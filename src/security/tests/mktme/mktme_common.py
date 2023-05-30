#!/usr/bin/env python
##########################################################################
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and proprietary
# and confidential information of Intel Corporation and its suppliers and
# licensors, and is protected by worldwide copyright and trade secret laws and
# treaty provisions. No part of the Material may be used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or disclosed
# in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
##########################################################################
import re
import os

from typing import List, Union

from src.lib.platform_config import PlatformConfiguration
from dtaf_core.lib.silicon import CPUID
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.bios_menu import BiosBootMenuProvider
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib import content_exceptions
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral
from src.security.tests.mktme.mktme_constants import LinuxConst
from src.lib.uefi_util import UefiUtil


class MktmeBaseTest(ContentBaseTestCase):
    """
    Base class extension for MktmeBaseTest which holds common arguments
    and functions.
    """
    CPUID_EDX = 0x7
    CPUID_EAX = 0x1b
    CPUID_ECX = 0x7
    MSR_TME_ADDRESS = 0x982
    MSR_MKTME_VAL = "B"
    ENABLE_TME_MSR_VALUE = 0x100060000000B
    CSCRIPTS_FILE_NAME = "cscripts_log_file.log"
    CHOP_NAME_LCC = "Low Core Count"
    REGEX_CMD_FOR_MKTME = r"Max number of MK-TME Keys available for use:\s(.*)"
    MKTME_KNOB_NAME = "EnableMktme"
    MSR_WRITE_VAL = 0
    TME_KNOB_NAME = "EnableTme"
    WAIT_TIME_DELAY = 60
    MSR_TME_CAPABILITY_ADDRESS = 0x981
    MSR_TME_CAPABILITY_VALUE = 0x000007F780000003
    MSR_TME_EXCLUDE_MASK_ADDRESS = 0x983
    MSR_TME_EXCLUDE_MASK_VALUE = 0x0000000000000000
    MSR_TME_EXCLUDE_BASE_ADDRESS = 0x984
    MSR_TME_EXCLUDE_BASE_VALUE = 0x0000000000000000
    RDMSR_COMMAND = "rdmsr {}"
    MKTKE_KEY_ID_RE_EXP = "mktme: (.\d+)"
    MKTME_KEY_DMIDECODE = "dmesg | grep  -i 'x86/mktme: .* KeyID'"
    MKTME_KEY_ID = "63"
    UEFI_CONFIG_PATH = 'suts/sut/providers/uefi_shell'
    MKTME_RANDOM_KEY_CMD = r"MKTMETool.efi -k 1 random"
    MKTME_KEY_SUCCESS_TEXT = r"PCONFIG: PROG_SUCCESS"

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file_path=None):
        """
        Create an instance of sut silconprovider.

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(MktmeBaseTest, self).__init__(test_log, arguments, cfg_opts, bios_config_file_path)

        self._cfg = cfg_opts

        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.log_file_path = self.get_cscripts_log_file_path()
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self.platform_family = self._common_content_lib.get_platform_family()
        self.sut_os_type = self.os.os_type
        self.mktme_properties = self.load_mktme_content_config_properties()
        self.mktme_consts = LinuxConst(self.platform_family)
        self.uefi_util_obj = None
        self.initialize_sdp_objects()
        self.initialize_sv_objects()
        self.cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)


    def prepare(self):
        # type: () -> None
        """
        pre-checks if the sut is alive or not.
        """
        super(MktmeBaseTest, self).prepare()


    def verify_mktme_key_assignment(self, output):
        """
        This function checks for the add_key: Required key not available or keyctl retcode 1 is present in the output

        :param output: output of the key_assign_loop.sh file
        :raise: content_exception.TestFail if add_key: Required key not available or keyctl retcode 1 is present in the output
        """
        add_key = "add_key: Required key not available"
        keyctl_retcode = "keyctl retcode 1"

        if add_key in output or keyctl_retcode in output:
            self._log.error("MKTME key assignment is failed")
            raise content_exceptions.TestFail("MKTME key assignment is failed")
        self._log.info("MKTME key assignment is successful")

    def verify_mktme(self):
        """
        This function verifies is the system SUT's CPU SKU supports MKTME.

        :return: True if MKTME is supported, False otherwise.
        """
        self._log.info("Verifying MK-TME support")
        ret_val = [False, False, False]

        # Overriding common content lib object with cscripts,sdp and log file.
        self._common_content_lib = CommonContentLib(self._log, self.os, self._cfg)
        try:
            self.SDP.halt()
            support_chop_name = \
                self._common_content_lib.get_cpu_physical_chop_info(self.cscripts_obj, self.SDP, self.log_file_path)
            self._log.debug("chop name:{}".format(support_chop_name))
            if support_chop_name == self.CHOP_NAME_LCC:
                raise content_exceptions.TestNAError("This test case only applicable for core HCC, XCC")
            self._log.info("This CPU CORE will support for MKTME test cases")
            # Checking the CPU ID registry value for EDX, EAX and ECX
            itp_command_status = self.SDP.cpuid(CPUID.EDX, self.CPUID_EDX, 0, squash=True) & (1 << 18) != 0
            ret_val[0] = itp_command_status
            self._log.debug("ITP command cpuid for edx with registry value %x status is %s", self.CPUID_EDX,
                            itp_command_status)
            itp_command_status = self.SDP.cpuid(CPUID.EAX, self.CPUID_EAX, 0, squash=True) == 1
            ret_val[1] = itp_command_status
            self._log.debug("ITP command cpuid for eax with registry value %x status is %s", self.CPUID_EAX,
                            itp_command_status)
            itp_command_status = self.SDP.cpuid(CPUID.ECX, self.CPUID_ECX, 0, squash=True) & (1 << 13) != 0
            ret_val[2] = itp_command_status
            self._log.debug("ITP command cpuid for ecx with registry value %x status is %s", self.CPUID_ECX,
                            itp_command_status)
        except Exception as e:
            raise e
        finally:
            self.SDP.go()
        return all(ret_val)

    def msr_read_and_verify(self, msr_address, exp_msr_value, squash=True):
        """
        This function reads the msr address for the location and verify the
        expected value

        :return: True if getting the expected value else false
        """
        try:
            self._log.info("Verifying the MSR registers")
            self.SDP.halt()
            msr_values_list = self.SDP.msr_read(msr_address)
            hex_msr_list = [hex(msr_value) for msr_value in msr_values_list]
            self._log.debug("MSR values for all the threads {}".format(hex_msr_list))
            msr_values = self.SDP.msr_read(msr_address, squash=squash)
            if not squash:
                if len(set(msr_values)) != 1:
                    raise content_exceptions.TestFail("MSR (%s) value of all the cores are not same", msr_address)
                msr_value = msr_values[0]
            else:
                msr_value = msr_values
            self._log.debug("Expected TME and MKTME MSR Values {}".format(hex(msr_value)))
            if hex(msr_value) != hex(exp_msr_value):
                raise content_exceptions.TestFail("MSR value is not expected, Expected MSR value{} Acctual value {} "
                                                  "".format(hex(exp_msr_value), hex(msr_value)))
        except Exception as e:
            raise e
        finally:
            self.SDP.go()

    def get_cscripts_log_file_path(self):
        """
        # We are getting the Path for CPU CORE check log file

        :return: log_file_path
        """
        path = os.path.join(self.log_dir, self.CSCRIPTS_FILE_NAME)
        return path

    def msr_write_values(self, msr_address, msr_write_val):
        """
        This function writes the msr value to msr registers
        Throws exception if exception occurs while writing

        :param msr_address : msr register value e.g 0x982
        :param msr_write_val : Value to be written e.g 0
        """
        self._log.info("Verifying write value to the MSR registers")

        self.SDP.halt()
        try:
            self.SDP.msr_write(msr_address, msr_write_val, no_readback=True)
        except Exception as e:
            raise e
        finally:
            self.SDP.go()

    def verify_mktme_max_keys(self, serial_log_path):
        """
        This function find Max No of Keys in serial log and verify.

        :raise: content_exception.TestFail if unable to find MK-TME Max No of Keys
        """
        self._log.info("Check the Max No of Keys Value in serial log")
        with open(serial_log_path, 'r') as log_file:
            logfile_data = log_file.read()
            mktme_key_search = re.search(self.REGEX_CMD_FOR_MKTME, logfile_data)
            if not mktme_key_search:
                raise content_exceptions.TestFail("Failed to get the MK-TME Keys info")
            self._log.info(mktme_key_search.group())
        actual_keys = mktme_key_search.group(1)
        if PlatformConfiguration.MKTME_MAX_KEYS_DICT[self.platform_family] != actual_keys:
            raise content_exceptions.TestFail("Not getting MK-TME Max No of Keys, Expected MK-TME Max No of Keys {} "
                                              "Actual value {}".format(PlatformConfiguration.MKTME_MAX_KEYS_DICT[self.platform_family], actual_keys))

    def execute_cpuid(self, command):
        """
        This Method is Used to Execute CPUID Commands on SUT

        :return: cpuid_command_output
        """
        cpuid_command_output = self._common_content_lib.execute_sut_cmd(command, command, self._command_timeout)
        self._log.debug("CPUID Output for Command '{}' is '{}'".format(command, cpuid_command_output))
        return cpuid_command_output

    def verify_rdmsr_output(self, msr_address, expected_msr_value, rdmsr_cmd_output):
        """
        This Method is used to Verify rdmsr output is same as Expected Output.

        :param msr_address: msr address
        :param expected_msr_value: Expected Output of rdmsr Command
        :param rdmsr_cmd_output: rdmsr command output got from msr-tools.
        :raise content_exceptions.TestFail: if rdmsr command output is not as expected output
        """
        self._log.info("Verifying rdmsr address {} ".format(msr_address))
        if rdmsr_cmd_output.strip() != expected_msr_value.replace("0x", ""):
            raise content_exceptions.TestFail("Expected MSR Output for address '{}' is '{}' but Actual Output is '{}"
                                              .format(msr_address, expected_msr_value, rdmsr_cmd_output.strip()))
        self._log.debug("Msr Value for Command rdmsr '{}' is as Expected '{}'".
                        format(msr_address, rdmsr_cmd_output.strip()))

    def veriy_mktme_keyid(self):
        """
        This function check for the Excepted MKTME KeyID value
        :raise Exception:
        """
        output = self._common_content_lib.execute_sut_cmd(self.MKTME_KEY_DMIDECODE, self.MKTME_KEY_DMIDECODE, self._command_timeout)
        self._log.info(output.strip())
        output = re.findall(self.MKTKE_KEY_ID_RE_EXP, output.strip())
        if not output:
            raise content_exceptions.TestFail("Unable to ge the mktme keyid")
        if not output[0] == self.MKTME_KEY_ID:
            raise content_exceptions.TestFail(
                "MKTME Excepted value {} is not matching with current value {}".format(
                    self.MKTME_KEY_ID, output[0]))
        self._log.info(
            "MKTME Excepted value {} is matching with current value {}".format(self.MKTME_KEY_ID, output[0]))
        return True

    def load_mktme_content_config_properties(self) -> dict:
        """Loads the MKTME properties (MKTME VF paths, TD guest properties) from content_configuration.xml into a dict.
        :return: Dict of properties from content_configuration.xml file for MKTME """

        properties = self._common_content_configuration.get_security_mktme_params(self.sut_os_type)
        for key in properties.keys():
            # convert properties from str to bool
            if properties[key].lower() == "true":
                properties[key] = True
            elif properties[key].lower() == "false":
                properties[key] = False
            elif properties[key].isnumeric():
                properties[key] = int(properties[key])
        return properties

    def set_ipc_unlock_credentials(self, username: str, password: str) -> None:
        """Setting the credential to IPC to unlock the device.

        :param username: pythonsv checkout username
        :param password: pythonsv checkout password
        """
        import py2ipc
        authzservice = py2ipc.IPC_GetService("Authorization")
        authzservice.SetCredentials(username, password)

    def initialize_uefi_util_object(self):
        """This method is using to initialize the uefi util object.It has been using
        for the uefi based testing."""

        if self.uefi_util_obj is None:
            uefi_cfg = self._cfg.find(self.UEFI_CONFIG_PATH)
            uefi_obj = ProviderFactory.create(uefi_cfg, self._log)  # UefiShellProvider
            bios_boot_menu_cfg = self._cfg.find(BiosBootMenuProvider.DEFAULT_CONFIG_PATH)
            bios_boot_menu_obj = ProviderFactory.create(bios_boot_menu_cfg, self._log)  # BiosBootMenuProvider
            self.uefi_util_obj = UefiUtil(self._log,
                                          uefi_obj,
                                          bios_boot_menu_obj,
                                          self.ac_power,
                                          self._common_content_configuration,
                                          self.os,
                                          cfg_opts=self._cfg)

    def get_all_usb_drive_letter_in_sut(self) -> Union[List[str], Exception]:
        """Get all USB driver letter in Windows or get all root path to the usb block devices in Linux
        :return: all USB drive letter as list"""

        if self.sut_os_type == OperatingSystems.WINDOWS:
            windows_command = r"powershell.exe (get-volume ^| where drivetype -eq removable).driveletter"
            usb_drive_list_output = self._common_content_lib.execute_sut_cmd(windows_command,
                                                                             windows_command,
                                                                             self._command_timeout)

            self._log.info(f"usb drive list is :\n{usb_drive_list_output}")
            usb_drive_list = list()
            if len(usb_drive_list_output) > 0:
                lines = usb_drive_list_output.split('\n')
                for line in lines:
                    line = line.strip()
                    if len(line) > 0:
                        usb_drive_list.append(line.strip() + ':')

            return usb_drive_list
        else:
            # TBD linux version need to be implement later.
            return NotImplementedError("Must be implemented for Linux Version")

    def unlock_itp(self):
        """ Unlocking the itp"""

        self._log.info("running itp.unlock()")
        self.initialize_sdp_objects()
        if self.SDP:
            self.SDP.itp.unlock()
        else:
            raise content_exceptions.TestFail("SiliconDebugProvider is not initialized")

    def apply_uefi_random_key(self) -> None:
        """ apply the random key by executing MKTMETool.efi tool
        :return: raise content_exceptions.TestFail, if the tool failed to execute.
        """

        # Initialize the uefi util obj
        self.initialize_uefi_util_object()

        # Enter into the UEFI shell by reboot the SUT
        if not self.uefi_util_obj.enter_uefi_shell():
            raise content_exceptions.TestFail("Can't enter uefi shell to generate pcr list")

        # Get usb drive list by using uefi util object
        usb_drive_list = self.uefi_util_obj.get_usb_uefi_drive_list()

        # Apply the MKTMEtool.efi tool.
        self._log.info("Entering into the MKTMETool random key environment")
        if not self.uefi_util_obj.execute_efi_cmd(usb_drive_list, self.MKTME_RANDOM_KEY_CMD,
                                                  self.MKTME_KEY_SUCCESS_TEXT):
            self._log.info("System has not applied MKTMETool random key environment")
            raise content_exceptions.TestFail("System has not entered MKTMETool random key  environment")
        return

    def copy_mktme_tool_to_sut_usb_drives(self) -> None:
        """Copying the MkTmeTool.efi to the usb drives in the SUT"""

        # Get all usb drive letters connected in SUT
        usb_drive_list = self.get_all_usb_drive_letter_in_sut()
        if len(usb_drive_list) == 0:
            raise content_exceptions.TestFail("The SUT doesn't have any USB storage drives to copy the mktmetool.efi")

        # Get the MKTMETool.efi file path from host machine.
        host_src_file_name = self.mktme_properties[self.mktme_consts.XmlEntry.MKTME_TOOL_PATH_HOST]

        # There could be potential chance that all USB drives may not be enumerated in UEFI shell after reboot
        # Especially if the usb thumb drive connected to RSC2 or banino kind of hubs. So it is better to copy
        # the tools to all available usb drives in the SUT.
        for sut_dest_path in usb_drive_list:
            # copying tools to SUT's usb drives(at root path) from host machine
            self.os.copy_local_file_to_sut(host_src_file_name, sut_dest_path)
