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

import os
import re
import io
import time
from typing import Dict, List
import ipccli
from pathlib import Path

from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.lib.dtaf_constants import OperatingSystems, ProductFamilies
from dtaf_core.providers.console_log import ConsoleLogProvider
from dtaf_core.providers.bios_provider import BiosProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.bios_menu import BiosBootMenuProvider
from dtaf_core.providers.uefi_shell import UefiShellProvider
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.lib.os_lib import OsCommandResult

from src.lib.bios_util import BiosUtil, ChooseBoot, BootOptions, SerialBiosUtil
from src.lib.bios_util import ItpXmlCli, PlatformConfigReader
from src.lib.uefi_util import UefiUtil
from src.lib.common_content_lib import CommonContentLib
from src.lib.os_lib import LinuxCommonLib
from src.lib.content_configuration import ContentConfiguration
from src.provider.copy_usb_provider import UsbRemovableDriveProvider
from src.lib.install_collateral import InstallCollateral
from src.provider.cpu_info_provider import CpuInfoProvider
from src.security.tests.cbnt_txt.txt_constants import TXT, Tpm2ToolCmds, TpmIndices, LCPPolicyElements, \
    Tpm2LcpCommands, Tpm2KeySignatures, Tpm2Drive, Tpm12Drive, Tpm12LcpCommands, Tboot, ArtifactoryToolPaths
from src.security.lib.pci_device_info import PciDeviceInfo
from src.security.lib.cpu_device_info import CpuDeviceInfo
from src.security.lib.mem_device_info import MemDeviceInfo
from src.lib.cbnt_constants import HashAlgorithms, CBnT, LinuxOsTypes, RedhatVersion, LcpPolicyVersion, TpmVersions
from src.lib import content_exceptions
from src.lib.grub_util import GrubUtil


class TxtBaseTest(BaseTestCase):
    """
    Base class extension for TXT which holds common arguments, functions.
    """
    _SIZE_OF_PCR_HEADER = 2
    _AC_TIMEOUT = _WAIT_TIME = 30
    _DEFAULT_ENTRY = 0
    _DEFAULT_BOOT_ORDER_FILE_PATH = "/boot/grub2/grubenv"
    _GRUB_CONFIG_FILE_PATH = "/boot/efi/EFI/{}/grub.cfg"
    UEFI_CONFIG_PATH = 'suts/sut/providers/uefi_shell'
    _GRUB_TBOOT_OPTION = "tboot"
    _GREP_MENU_ENTRY = 'grep {} {}'
    _VERIFY_TPM_CMD = "dmesg | grep -i TPM"
    _TPM_MOD_DETECT_AND_ENUMERATE_CMD = "ls /dev | grep -i tpm"
    _TPM_TOOL_ZIP_FILE = {"Tpm_Tools": "TPM_Tools.zip"}
    _TXT_ENTER_CMD = "getsec64-t1.efi -l SENTER -i"
    _TXT_ENTER_CMD_CBNT = "getsec64CBnT.efi -l SENTER -i"
    _TXT_ENTER_STR = "System is now in TXT Environment."
    _SERVER_TXT_INFO_CMD = "ServerTXTINFO.efi -c:a -a"
    _TXT_INFO_CMD = "TxtBtgInfo.efi -c brft -a"
    _TPM_PO_INDEX_ERASE_CMD = "TxtBtgInfo.efi -c t"
    _TXT_EXIT_CMD = "getsec64-t1.efi -l SEXIT -i"
    _TXT_EXIT_CMD_CBNT = "getsec64CBnT.efi -l SEXIT -i"
    _TXT_EXIT_STR = "System has exited TXT Environment."
    _TPM_DEVICE = "TPM 2.0"
    _SERVER_SECRET_ASSERT_CMD = "ServerSecrets.efi -s"
    _SERVER_SECRET_DE_ASSERT_CMD = "ServerSecrets.efi -n"
    _SERVER_SECRET_ASSERT_CMD_CBNT = "ServerSecretsCbnt.efi -s"
    _SERVER_SECRET_DE_ASSERT_CMD_CBNT = "ServerSecretsCbnt.efi -n"
    _SERVER_SECRET_ASSERT_SUCCESS_MSG = "Secrets bit is asserted"
    _SERVER_SECRET_DE_ASSERT_SUCCESS_MSG = "Secrets bit is de-asserted"
    _TPM2_MLE_HASH_CREATION_CMD = "--create -alg %s --cmdline \"logging=serial,memory\" /boot/tboot.gz > %s"
    _TPM2_MLE_ELEMENT_CREATION_CMD = "--create --type mle2 --minver %s --ctrl %s --out %s --alg %s %s"
    _TPM2_MLE_LEGACY_ELEMENT_CREATION_CMD = "--create --type mle --minver %s --ctrl %s --out %s %s"
    _TPM2_PCONF_ELEMENT_CREATION_CMD = "--create --type pconf2 --ctrl %s --out %s --alg %s --pcr%s %s"
    _TPM2_LCP_LIST_CREATION_CMD = " --create --out %s --listver %s "
    _TPM2_LCP_LIST_SIGN_CMD = " --sign --out %s --hashalg %s --rev %s --sigalg %s --priv %s --pub %s --out %s"
    _TPM2_POLICY_GENERATION_CMD = " --create --polver %s --type %s --ctrl %s --minver %s --pol %s --data %s " \
                                  "--rev %s --sign %s --alg %s"
    _NEGATIVE_TEST_CASE = "negative test case"
    _SERIAL_LOG_FILE = "serial_log.log"
    _PCR_PATH = "/tpm/tpm0/pcrs"
    _CMD_TO_GET_FILE_PATH = "find / -xdev -name {}"
    _TPM_COMMUNICATION_CMD = "tpm2-abrmd --allow-root"
    _PCRS_FIND_COMMAND = "find /sys/devices -name pcrs"
    TXT_BTG_INFO_COMMAND = "TxtBtgInfo.efi -a"

    _EXECUTE_SERVERPCRDUMP_TPM2 = "ServerPCRDumpTPM2.efi -v"
    EFI_FILE_PATH_ON_USB = None
    SUT_FILE_PATH = None
    USB_DRIVE_LIST = []
    HOST_OUTPUT_FILE_PATH = None
    ZIP_FILE_PATH = None
    # Algorithm, pcr file
    _PCR_GENERATION_EFI_DIR = "TPM PCR Tools"
    _LCP_IDEF_DATA_SIZE = 56
    _LCP_IDEF_POLICY_SIZE = [61, 68]
    _LCP_IDEF_POLICY_BUFFER = 69
    _LCP2_POLICY_TYPES = ["list", "any"]
    LCP_POLICY_CREATION_DICT = {LCPPolicyElements.MLE: _TPM2_MLE_ELEMENT_CREATION_CMD,
                                LCPPolicyElements.PCONF: _TPM2_PCONF_ELEMENT_CREATION_CMD,
                                LCPPolicyElements.MLE_LEGACY: _TPM2_MLE_LEGACY_ELEMENT_CREATION_CMD}
    HASH_ALGORITHM_HEX = {HashAlgorithms.SHA1: "0x4",
                          HashAlgorithms.SHA256: "0xB",
                          HashAlgorithms.SHA384: "0xC"}
    PCR_GENERATION_CHECK = {"0x4": "536",
                            "0xB": "824"}

    LCP_POLICY_VERSION_DICT = {
                               _NEGATIVE_TEST_CASE: "3.0",
                               ProductFamilies.CLX: "3.1",
                               ProductFamilies.CPX: "3.1",
                               ProductFamilies.ICX: "3.1",
                               ProductFamilies.SPR: "3.2"}
    LCP_LIST_VERSION_DICT = {
                             _NEGATIVE_TEST_CASE: "0x200",
                             ProductFamilies.CLX: "0x201",
                             ProductFamilies.CPX: "0x201",
                             ProductFamilies.ICX: "0x200",
                             ProductFamilies.SPR: "0x300"}
    PCR_STRING = "PCR "
    _PCR_DUMP_64_ZIP_FILE = {"pcrdump64": "pcrdump64.zip"}
    _EXECUTE_PCRDUMP_64 = "pcrdump64.efi -v"
    PCR_END_VALUE = 8
    _SIZE_OF_PCR_HASH = {
                            HashAlgorithms.SHA1: 20,
                            HashAlgorithms.SHA256: 32}
    _BYTE_SIZE_TO_WRITE = 8
    _VALUE_TO_WRITE = 1
    _BYTE_SIZE_TO_READ = 4
    _EXPECTED_E2STS_VAL = 0x0
    THREAD_INDEX = 0
    TBOOT_INSTALLATION_CMD = ["yum clean all", "yum update -y --nogpgcheck", "yum upgrade -y --nogpgcheck", "yum install trousers -y --nogpgcheck",
                              "yum install trousers-devel -y --nogpgcheck", "yum install tpm-tools -y --nogpgcheck", "yum install mercurial -y --nogpgcheck",
                              "yum remove libsafec-3.3-5.*.x86_64 -y --nogpgcheck",
                              "yum install libsafec-3.3-5.*.x86_64 -y --nogpgcheck",
                              "yum install tboot -y --nogpgcheck", "export http_proxy=http://proxy-chain.intel.com:911",
                              "export https_proxy=http://proxy-chain.intel.com:912"]
    TBOOT_MAKE_CMD = "make install"
    GRUB_CMD = ["grub2-mkconfig -o /boot/efi/EFI/{}/grub.cfg", "yum install grub2-efi-x64-modules -y"]
    EFI_FILEPATH = "/boot/efi/EFI/{}/x86_64-efi"
    COPY_MOD_FILE_CMD = ["cp /usr/lib/grub/x86_64-efi/relocator.mod /boot/efi/EFI/{}/x86_64-efi ",
                         "cp /usr/lib/grub/x86_64-efi/multiboot2.mod /boot/efi/EFI/{}/x86_64-efi"]
    SEARCH_STR_TBOOT = "insmod multiboot2"
    REPLACE_STR_TBOOT = r"\\tinsmod relocator"

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        """
        Create an instance of sut os provider, XmlcliBios provider, BIOS util and Config util
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        :param bios_config_file: Bios Configuration file name
        :return: None
        """
        super(TxtBaseTest, self).__init__(test_log, arguments, cfg_opts)

        self._cfg = cfg_opts

        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(
            sut_os_cfg, test_log)  # type: SutOsProvider
        self._common_content_lib = CommonContentLib(self._log, self._os, self._cfg)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac_obj = ProviderFactory.create(ac_cfg, test_log)  # type: AcPowerControlProvider

        self.GRUB_CMD = [f"grub2-mkconfig -o /boot/efi/EFI/{self._os.os_subtype.lower()}/grub.cfg",
                         "yum install grub2-efi-x64-modules -y"]
        self.EFI_FILEPATH = f"/boot/efi/EFI/{self._os.os_subtype.lower()}/x86_64-efi/"
        self.COPY_MOD_FILE_CMD = ["cp /usr/lib/grub/x86_64-efi/relocator.mod "
                                  f"{self.EFI_FILEPATH}",
                                  "cp /usr/lib/grub/x86_64-efi/multiboot2.mod "
                                  f"{self.EFI_FILEPATH}"]

        if not self._os.is_alive():
            self._log.error("System is not alive, wait for the sut online")
            self.perform_graceful_g3()  # To make the system alive

        if not self._os.is_alive():
            self._log.error("System is not alive")
            raise content_exceptions.TestFail("System is not alive")

        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        self._bios = ProviderFactory.create(
            bios_cfg, test_log)  # type: BiosProvider

        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._sdp = ProviderFactory.create(
            si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        cur_path = os.path.dirname(os.path.realpath(__file__))
        if bios_config_file:
            bios_config_file_path = self._common_content_lib.get_config_file_path(cur_path, bios_config_file)
            self._bios_util = BiosUtil(cfg_opts, bios_config_file_path, self._bios, self._log, self._common_content_lib)
        self.txt_consts = TXT.get_subtype_cls("TXT" + self._common_content_lib.get_platform_family(), False)
        self._install_collateral = InstallCollateral(self._log, self._os, self._cfg)
        self.txt_consts = TXT.get_subtype_cls(
            "TXT" + self._common_content_lib.get_platform_family(), False)
        self.tboot_data = Tboot
        self._prime_running_time = self._common_content_configuration.security_mprime_running_time()
        self._command_timeout = self._common_content_configuration.get_command_timeout()
        self._msr_time_sleep = self._common_content_configuration.get_msr_timeout()
        self.txt_msr_consts = TXT.MSR_PKG_C6_RESIDENCY
        uefi_cfg = cfg_opts.find(self.UEFI_CONFIG_PATH)
        self._uefi_obj = ProviderFactory.create(uefi_cfg, test_log)  # type: UefiShellProvider
        bios_boot_menu_cfg = cfg_opts.find(BiosBootMenuProvider.DEFAULT_CONFIG_PATH)
        self._bios_boot_menu_obj = ProviderFactory.create(bios_boot_menu_cfg, test_log)  # type: BiosBootMenuProvider
        self._uefi_util_obj = UefiUtil(
            self._log,
            self._uefi_obj,
            self._bios_boot_menu_obj,
            self._ac_obj,
            self._common_content_configuration, self._os, cfg_opts=self._cfg)
        self._copy_usb = UsbRemovableDriveProvider.factory(test_log, cfg_opts, self._os)
        self.platform_family = self._common_content_lib.get_platform_family()
        self._boot = ChooseBoot(self._bios_boot_menu_obj, self._common_content_configuration, test_log, self._ac_obj,
                                self._os, cfg_opts)
        self._serial_bios_util = SerialBiosUtil(self._ac_obj, test_log, self._common_content_lib, cfg_opts)
        self._linux_os = LinuxCommonLib(test_log, self._os)
        self._bios_boot_menu_entry_wait_time = self._common_content_configuration.bios_boot_menu_entry_wait_time()
        cng_cfg = cfg_opts.find(ConsoleLogProvider.DEFAULT_CONFIG_PATH)
        self.cng_log = ProviderFactory.create(cng_cfg, self._log)
        self.log_dir = self._common_content_lib.get_log_file_dir()
        self.itp = ipccli.baseaccess()
        self.serial_log_dir = os.path.join(self.log_dir, "serial_logs")
        if not os.path.exists(self.serial_log_dir):
            os.makedirs(self.serial_log_dir)
        self.cng_log.redirect(os.path.join(self.serial_log_dir,
                                           self._SERIAL_LOG_FILE))
        self._csp_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._csp = None
        self._cc_log_path = arguments.outputpath
        self.usb_set_time = self._common_content_configuration.get_usb_set_time_delay()
        self._common_content_lib.enable_network_manager_using_startup()
        self._cpu_provider = CpuInfoProvider.factory(self._log, cfg_opts, self._os)
        self.grub_util: GrubUtil = GrubUtil(self._log, self._common_content_configuration, self._common_content_lib)

    @classmethod
    def add_arguments(cls, parser):
        super(TxtBaseTest, cls).add_arguments(parser)
        # Use add_argument
        parser.add_argument('-o', '--outputpath', action="store", default="",
                            help="Log folder to copy log files to command center")

    def prepare(self):  # type: () -> None
        if not self._os.is_alive():
            self._log.info("System is not alive, making it alive")
            self.perform_graceful_g3()

    def copy_file(self, zip_file):
        """
        This function will copy zip files to sut
        """
        for folder_in_sut, file_name in zip_file.items():
            # Copy zip file to usb
            zip_file_path = self._install_collateral.download_and_copy_zip_to_sut(folder_in_sut, file_name)
            self._copy_usb.copy_file_from_sut_to_usb(self._common_content_lib, self._common_content_configuration,
                                                     zip_file_path)

    def enable_and_verify_bios_knob(self):
        """
        This method enable and verify the bios knobs

        :return: None
        """
        self._bios_util.load_bios_defaults()  # To set Bios knobs to default.
        self._bios_util.set_bios_knob()  # To set the bios knob setting
        self.perform_graceful_g3()
        self._bios_util.verify_bios_knob()  # To verify the Bios knob value set

    def validate_linux_mle(self, trusted=True):
        """
        This method runs txt-stat command and checks TXT measured launch and secrets flag set status
        :param trusted: True if trusted otherwise False
        :raise : RuntimeError if fail to execute txt-stat command
        :return: returns result as True or False
        """
        sut_val_cmd = "sudo /usr/sbin/txt-stat"
        expected_val_output = [
            'TXT measured launch: TRUE',
            'secrets flag set: TRUE'] if trusted else [
            'TXT measured launch: FALSE',
            'secrets flag set: FALSE']
        self._log.debug("Executing txt-stat.")
        cmd_result = self._os.execute(sut_val_cmd, self._command_timeout)
        self._log.debug(f"Output of txt-stat: {cmd_result.stdout}")
        result = cmd_result.cmd_passed()
        if result:
            for line in expected_val_output:
                if line not in cmd_result.stdout:
                    self._log.error(
                        "Did not find line " + line + " in txt-stat log!")
                    result = False
        else:
            raise RuntimeError("txt-stat failed to execute!")

        return result

    def _validate_txt_registers_trusted(self, expect_ltreset, mask_ltreset):
        """
        Read the registers value and comparing with the expected result
        :param expect_ltreset: Should be True if LT_RESET should be set (surprise reset occurred)
        :param mask_ltreset: If true, will ignore the status of the LT_RESET bit in E2STS
        :return: True if register values matches with expected value, else False
        """
        # Get expected values from txt_constants
        trusted_regs = self.txt_consts.TXT_TRUSTED_REGISTER_VALUES

        # Read each LT register and save the result
        register_values = {}
        try:
            self._sdp.halt()
            for register in self.txt_consts.TXT_REG_OFFSETS.keys():
                mmio_address = self.txt_consts.TXT_REG_PUBLIC_BASE + \
                               self.txt_consts.TXT_REG_OFFSETS[register]
                self._log.debug(
                    "Reading register " +
                    register +
                    " from address 0x%08x" %
                    mmio_address)
                reg_val = self._sdp.mem_read(
                    hex(mmio_address).rstrip('L') + 'p', 8)
                self._log.debug(register + "=" + str(hex(reg_val)))
                register_values[register] = reg_val
        finally:
            self._sdp.go()
        self._log.info("Register values are : {}".format(register_values))
        # Check each register to ensure that TXT environment is copacetic
        result = True

        for register in trusted_regs.keys():
            if register_values[register] != trusted_regs[register]:
                self._log.error(
                    "Register " +
                    register +
                    " did not have the right value!")
                self._log.error("Expected: " +
                                str(trusted_regs[register]) +
                                ", got: " +
                                str(register_values[register]))
                result = False

        # Special checks
        if int(register_values["LT_EXISTS"]) == 0:
            self._log.error(
                "LT_EXISTS register is 0. Platform may not be strapped for TXT.")
            result = False
        elif int(register_values["LT_EXISTS"]) != int(register_values["LT_JOINS"]):
            self._log.error(
                "LT_JOINS does not match LT_EXISTS. Not all CPUs joined the MLE!")
            result = False
        elif not mask_ltreset and not expect_ltreset and register_values["LT_E2STS"] != self.txt_consts.LT_E2STS_EXP:
            self._log.error(
                "LT_RESET bit is set when it shouldn't be! SUT may have gone through an ungraceful reset!")
            result = False
        elif not mask_ltreset and expect_ltreset and register_values["LT_E2STS"] != self.txt_consts.LT_E2STS_RESET_EXP:
            self._log.error(
                "LT_RESET bit isn't set, but it should be! SUT may have been gracefully reset when it" +
                "shouldn't have.")
            result = False
        elif mask_ltreset and not \
                (register_values["LT_E2STS"] == self.txt_consts.LT_E2STS_EXP or
                 register_values["LT_E2STS"] == self.txt_consts.LT_E2STS_RESET_EXP):
            self._log.error("LT_E2STS register was not set as expected!")
            result = False

        return result

    def verify_trusted_boot(self, expect_ltreset=False, mask_ltreset=False):
        # type: (bool, bool) -> bool
        """
        Validate if SUT booted trusted.
        :param expect_ltreset: Should be True if LT_RESET should be set (surprise reset occurred)
        :param mask_ltreset: If true, will ignore the status of the LT_RESET bit in E2STS
        :raise RuntimeError: If OS is not Linux
        :return: True if SUT booted trusted, False otherwise.
        """
        # Validate MLE setup
        if self._os.os_type == OperatingSystems.LINUX:
            mle_result = self.validate_linux_mle()
        else:
            raise RuntimeError("OS " +
                               str(self._os.os_type) +
                               " is not supported for TXT!")

        if not mle_result:
            self._log.error("SUT did not successfully launch the MLE!")
        self._log.info("SUT successfully launch the MLE!")

        # Validate TXT register status
        txt_result = self._validate_txt_registers_trusted(
            expect_ltreset, mask_ltreset)
        if not txt_result:
            self._log.error("TXT register checks were unsuccessful!")

        return txt_result and mle_result

    def verify_untrusted_boot(self):
        """
        Validate if SUT booted untrusted.
        :raise: RuntimeError: If OS is not Linux
        :raise: RuntimeError: If platform is not strapped for TXT
        :return: True if SUT booted untrusted, False otherwise.
        """
        # Validate MLE setup
        if self._os.os_type == OperatingSystems.LINUX:
            mle_result = self.validate_linux_mle(False)
        else:
            raise RuntimeError("OS " +
                               str(self._os.os_type) +
                               " is not supported for TXT!")

        if not mle_result:
            self._log.error(
                "MLE untrusted check failed! TXT seems to be enabled.")

        # Get TXT register status
        self._sdp.halt()
        lt_joins = self._sdp.mem_read(
            hex(
                self.txt_consts.TXT_REG_PUBLIC_BASE +
                self.txt_consts.TXT_REG_OFFSETS["LT_JOINS"]).rstrip('L') +
            'p',
            8)
        lt_exists = self._sdp.mem_read(
            hex(
                self.txt_consts.TXT_REG_PUBLIC_BASE +
                self.txt_consts.TXT_REG_OFFSETS["LT_EXISTS"]).rstrip('L') +
            'p',
            8)
        self._sdp.go()

        # Validate TXT register status
        if lt_exists == 0x0:
            log_error = "Platform is not strapped for TXT. Please check TXT_EN and TXT_AGENT settings."
            self._log.exception(log_error)
            raise RuntimeError(log_error)
        elif lt_joins != 0x0:
            self._log.error(
                "Platform reporting at least one socket entered MLE! Joins = " + str(hex(lt_joins)))

        return not lt_joins != 0x0

    def get_tboot_boot_position(self) -> str:
        """
        This extracts all available boot options in the grub configuration file and checks for tboot position
        This works only with EFI mode not on legacy mode

        :return: position of tboot in boot order
        :raise: NotImplementedError - if the the OS subtype is not RHEL
        """
        grub_file: str = self._GRUB_CONFIG_FILE_PATH.format(self._os.os_subtype.lower())
        grub_read_cmd: str = f"cat {grub_file}"
        self._log.info(f"Looking for tboot entries in {grub_file}")
        grub_read_res: OsCommandResult = self._os.execute(grub_read_cmd, timeout=self._command_timeout)
        if grub_read_res.cmd_failed():
            raise content_exceptions.TestSetupError(f"{grub_read_cmd} failed with return code {grub_read_res.return_code}.\nstderr:\n{grub_read_res.stderr}")
        else:
            grub_cfg: str = grub_read_res.stdout
            grub_dict: Dict = self.grub_util.get_entries(grub_cfg)
            grub_paths: List[str] = self.grub_util.dict_to_paths(grub_dict)
            tboot_paths: List[str] = list(filter(lambda p: p.lower().find("tboot")>=0, grub_paths))
            self._log.debug(f"Found {len(grub_paths)} entries in grub.cfg:\n{grub_paths}")
            if len(tboot_paths) == 1:
                return tboot_paths[0]
            elif len(tboot_paths) > 1:
                version: str = self.grub_util.get_current_kernel_version()
                versioned_paths: List[str] = list(filter(lambda p: p.lower().find(version)>=0, tboot_paths))
                if len(versioned_paths) != 1:
                    p = "\n".join(tboot_paths)
                    raise content_exceptions.TestSetupError(f"Found {len(versioned_paths)} suitable paths with kernel version {version} in paths:\n{p}")
                else:
                    return versioned_paths[0]
            else:
                raise content_exceptions.TestSetupError(f"Could not find any entries in {grub_file}. Please check its contents.")

    def verify_sut_booted_in_tboot_mode(self, expected_grub_index):
        """
        Verify if SUT booted with Tboot option after changing the grub option

        :param: expected_grub_index - expected grub index value for tboot.
        :raise: NotImplementedError - If the the OS subtype is not RHEL
        :raise: RuntimeError - If failed to execute the command (grep "saved_entry=" /boot/grub2/grubenv)
        :return: None
        """
        # we will execute below command get the default grub configuration
        # grep "saved_entry=" /boot/grub2/grubenv
        default_value_grub = "saved_entry="
        if self._os.os_subtype.upper() != LinuxOsTypes.RHEL and self._os.os_subtype.upper() != LinuxOsTypes.CENTOS:
            # TODO: Yet to implement getting default boot index and check
            log_debug = "Reading default grub index is not yet implemented for OS = '{}'".format(
                self._os.os_subtype)
            self._log.debug(log_debug)
            raise NotImplementedError(log_debug)

        self._log.info("getting the default value of grub configuration")
        if self._os.os_subtype.upper() == LinuxOsTypes.RHEL or self._os.os_subtype.upper() == LinuxOsTypes.CENTOS:
            command_line = self._GREP_MENU_ENTRY.format(default_value_grub, self._DEFAULT_BOOT_ORDER_FILE_PATH)
            command_result = self._common_content_lib.execute_sut_cmd(command_line, "grepsaved entry in grubenv",
                                                                      self._command_timeout)
            self._log.info("grub default boot command {} ".format(command_result))
            search_string = "saved_entry=" + str(expected_grub_index)
            if search_string in command_result or self._GRUB_TBOOT_OPTION in command_result:
                self._log.info("Sut is booted with tboot+linux")
            else:
                self._log.error("Sut is failed to boot with tboot+linux")
                raise RuntimeError("Sut is failed to boot with tboot+linux")

    def set_default_boot_entry(self, boot_index):
        self._log.info(f"Setting default boot entry to {boot_index}")
        if not self.grub_util.set_grub_boot_index(boot_index):
            raise content_exceptions.TestSetupError("Failed to set default boot index")

    def compare_mem_cpu_pci_data(
            self,
            pre_tboot_pci,
            post_tboot_pci,
            pre_tboot_cpu,
            post_tboot_cpu,
            pre_tboot_mem,
            post_tboot_mem):
        """
        This function is giving input for executed command output for parsing and comparing the both output
        if it is same it will return True/False

        :return If both results are equal it will true otherwise false
        """
        cpu_mem_pci_data_compare_result = []
        self._log.info("Parse the PCI command details of SUT...")
        parse_pci_data_src = PciDeviceInfo.parse_pci_output_data(
            pre_tboot_pci)
        parse_pci_data_dst = PciDeviceInfo.parse_pci_output_data(
            post_tboot_pci)
        pci_final_result = PciDeviceInfo.get_pci_data_diff(
            parse_pci_data_src, parse_pci_data_dst)
        self._log.info("PCI command results : {} ".format(pci_final_result))

        if not pci_final_result:
            cpu_mem_pci_data_compare_result.append(False)
            self._log.error("Comparison of the PCI command is Failed...")
        else:
            cpu_mem_pci_data_compare_result.append(True)
            self._log.info("Comparison of the PCI command is Passed...")

        self._log.info("Parse the CPU command details of SUT...")
        parse_cpu_data_src = CpuDeviceInfo.parse_cpu_output_data(
            pre_tboot_cpu)
        parse_cpu_data_dst = CpuDeviceInfo.parse_cpu_output_data(
            post_tboot_cpu)
        if parse_cpu_data_src["CPU MHz"] == parse_cpu_data_dst["CPU MHz"]:
            self._log.info("Both pre/pst tboot cpu info is same")
        else:
            self._log.info("pre tboot cpu mhz info {}".format(parse_cpu_data_src["CPU MHz"]))
            self._log.info("post tboot cpu mhz info {}".format(parse_cpu_data_dst["CPU MHz"]))
            # Delete the CPU MHZ results form dictionary
            del parse_cpu_data_src["CPU MHz"]
            del parse_cpu_data_dst["CPU MHz"]

        cpu_final_result = CpuDeviceInfo.get_cpu_data_diff(
            parse_cpu_data_src, parse_cpu_data_dst)
        self._log.info("CPU command results : {} ".format(cpu_final_result))
        if not cpu_final_result:
            cpu_mem_pci_data_compare_result.append(False)
            self._log.error("Comparison of the CPU command is Failed...")
        else:
            cpu_mem_pci_data_compare_result.append(True)
            self._log.info("Comparison of the CPU command is Passed...")

        self._log.info("Parse the mem command details of SUT...")
        parse_mem_data_src = MemDeviceInfo.parse_mem_output_data(
            pre_tboot_mem)
        parse_mem_data_dst = MemDeviceInfo.parse_mem_output_data(
            post_tboot_mem)

        mem_final_result = MemDeviceInfo.get_mem_data_diff(
            parse_mem_data_src, parse_mem_data_dst)
        self._log.info("MEM command results : {} ".format(mem_final_result))

        if not mem_final_result:
            cpu_mem_pci_data_compare_result.append(False)
            self._log.error("Comparison of the MEM command is Failed...")
        else:
            cpu_mem_pci_data_compare_result.append(True)
            self._log.info("Comparison of the MEM command is Passed...")

        return all(cpu_mem_pci_data_compare_result)

    def get_sdp_msr_values(self, msr_address):
        # type: (int) -> [list, int]
        """
        Read MSR values at the specified address across all threads.
        """
        self._sdp.halt()
        msr_val = self._sdp.msr_read(msr_address)
        self._sdp.go()

        return msr_val

    def check_sha256_enable(self, usb_drive_list):
        """
        Function checks if SHA256 is enabled in UEFI

        :param usb_drive_list: Takes the usb drive list as parameter to run command
        :return: returns True if SHA256 is enabled and False if not
        """
        run_txt_info = "ServerTXTINFO.efi -c:a -a"
        sha256_enable_kwd = "Hash Algorithm:       0xB"
        if self.platform_family in CBnT.CBNT_PRODUCT_FAMILIES:
            run_txt_info = "TxtBtgInfo.efi -c brft -a"

        if self._uefi_util_obj.execute_efi_cmd(usb_drive_list, run_txt_info, sha256_enable_kwd):
            return True

        return False

    def provision_tpm2(self, usb_drive_list, index=None, hashalg=None):
        """
        Provisions TPM 2.0 or PTT (fTPM)

        :param usb_drive_list: Takes the usb drive list as parameter to run command
        :param index: index to be provisioned; valid choices are SGX, PO, PS
        :param hashalg: hash algorithm to be used to provision
        :return: True if platform is provisioned successfully and False if not
        """

        ret_flag = False
        end_line = "Completed Successfully"
        success_provisioning = "Provisioning Completed Successfully"
        self._log.info("Provisioning TPM2 with hash algorithm:" + hashalg)
        if hashalg not in [HashAlgorithms.SHA256]:
            self._log.exception("Supplied algorithm not supported by provisioning tool!")
            raise ValueError("Supplied algorithm not supported by provisioning tool!")
        try:
            prov_cmd = Tpm2ToolCmds.PROV_CMDS[index]
        except KeyError:
            self._log.exception("Invalid index was provided to be provisioned!")
            raise KeyError("Invalid index was provided to be provisioned!")

        if self._uefi_util_obj.execute_efi_cmd(usb_drive_list, prov_cmd + " " + hashalg + " example",
                                               success_provisioning, end_line):
            ret_flag = True

        return ret_flag

    def reset_platform_auth(self, usb_drive_list: List, hashalg: str = None) -> None:
        """
        Reset PlatformAuth on TPM 2.0 or PTT (fTPM)

        :param usb_drive_list: Takes the usb drive list as parameter to run command
        :param hashalg: hash algorithm to be used to provision
        :return: True if platform is provisioned successfully and False if not
        """
        reset_platform_cmd = f"ResetPlatformAuth.nsh {hashalg} example"
        success_reset_platform = "Successfully set PlatformAuth to EMPTY"
        reset_platform_cmd_end_line = "EMPTY"

        if not self._uefi_util_obj.execute_efi_cmd(usb_drive_list, reset_platform_cmd, success_reset_platform,
                                                   reset_platform_cmd_end_line):
            raise content_exceptions.TestFail("Platform Reset Failed!")
        self._log.info("Platform Reset successfully")

    def provision_aux_index(self, usb_drive_list: List, hashalg: str = None) -> None:
        """
        Provisions TPM 2.0 or PTT (fTPM) AUX index

        :param usb_drive_list: Takes the usb drive list as parameter to run command
        :param hashalg: hash algorithm to be used to provision
        """

        end_line = "Completed Successfully"
        success_provisioning = "Provisioning Completed Successfully"
        index = "AUX"
        self.reset_platform_auth(usb_drive_list, hashalg=hashalg)
        self._log.info("Provisioning TPM2 AUX index with hash algorithm:" + hashalg)
        if hashalg not in [HashAlgorithms.SHA256]:
            self._log.exception("Supplied algorithm not supported by provisioning tool!")
            raise ValueError("Supplied algorithm not supported by provisioning tool!")
        try:
            prov_cmd = Tpm2ToolCmds.PROV_CMDS[index]
        except KeyError:
            self._log.exception("Invalid index was provided to be provisioned!")
            raise KeyError("Invalid index was provided to be provisioned!")

        if not self._uefi_util_obj.execute_efi_cmd(usb_drive_list, prov_cmd + " " + hashalg + " example",
                                               success_provisioning, end_line):
            raise content_exceptions.TestFail("Failed to provision AUX index!")

    def clear_tpm2_ownership(self, usb_drive_list):
        """
        Clears PO Ownership of a TPM2

        :param usb_drive_list: Takes the usb drive list as parameter to run command
        :return: None
        """

        SUCCESSFUL_CLEAR = "errorCode: 0"
        return self._uefi_util_obj.execute_efi_cmd(usb_drive_list, Tpm2ToolCmds.CLEAR_OWNERSHIP,
                                                   SUCCESSFUL_CLEAR)

    def verify_sha256_and_provision_tpm(self, usb_drive_list):
        """
        This method checks whether the system is enabled with SHA256 and Provision the TPM
        for CBnT and non- CBnT platforms

        :param usb_drive_list: Takes the usb drive list as parameter to run command
        :raise: content_exceptions if SHA256 is not enabled
        :raise: content_exceptions if Platform Reset Failed
        :raise: content_exceptions if Provisioning fails
        :return: None
        """

        # check if SHA256 is enabled in BIOS
        if not self.check_sha256_enable(usb_drive_list):
            raise content_exceptions.TestFail("SHA256 is not enabled")
        self._log.info("SHA256 is enabled")

        if self.platform_family in CBnT.CBNT_PRODUCT_FAMILIES:
            self._log.info("Looks like the platform is CBNT family, resetting the platform")
            self.reset_platform_auth(usb_drive_list, hashalg=HashAlgorithms.SHA256)

        # Provision the TPM2 PS indices; not needed for CBnT products
        if self.platform_family not in CBnT.CBNT_PRODUCT_FAMILIES:
            if not self.provision_tpm2(usb_drive_list, TpmIndices.PS, HashAlgorithms.SHA256):
                raise content_exceptions.TestFail("Provisioning for PS index has failed!")
            self._log.info("Provisioning is done for PS index Successfully")

        if self.platform_family in CBnT.CBNT_PRODUCT_FAMILIES:
            # Provision the TPM2 PO indices
            self._log.info("Looks like the platform is CBNT family, Provisioning PO index with SHA256")
            if not self.provision_tpm2(usb_drive_list, TpmIndices.PO, HashAlgorithms.SHA256):
                raise content_exceptions.TestFail("Provisioning for PO index has failed!")
            self._log.info("Successfully provisioned PO index")
            self.provision_aux_index(usb_drive_list, hashalg=HashAlgorithms.SHA256)

    def clear_po_index_tpm2(self, usb_drive_list):
        """
        Clears PO index of TPM2 device.
        :param usb_drive_list: Takes the usb drive list as parameter to run command
        :return:
        """
        self._log.info("Clearing PO index for TPM2")
        try:
            start_session_command = Tpm2ToolCmds.CLEAR_INDEX[TpmIndices.PO] + " StartSession EmptyAuthPWSession.sDef 1"
            clear_po_index = Tpm2ToolCmds.CLEAR_INDEX[TpmIndices.PO] + " NvUndefineSpace ExamplePO_Sha256.iDef 1"
            for usb_drive in usb_drive_list:
                self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(usb_drive, None)
            self._uefi_util_obj.uefi_navigate_to_usb(start_session_command)
            self._log.debug("Attempting to execute:" + start_session_command)
            self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(start_session_command, "errorCode: 0")
            self._uefi_util_obj.uefi_navigate_to_usb(clear_po_index)
            self._log.debug("Attempting to execute:" + clear_po_index)
            self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(clear_po_index, "errorCode: 0")
        except:
            raise content_exceptions.TestFail("Could not clear PO index in UEFI shell")

    def verifies_tpm2_active(self):
        """
        This method verifies tpm2 is recognized in os level

        :raise: content_exceptions if unable to recognise tpm2
        :return: None
        """
        tpm2_str = "TPM2"
        tpm_detect_str = "tpm0"
        output = self._common_content_lib.execute_sut_cmd(self._VERIFY_TPM_CMD, "Check TPM devices",
                                                          self._command_timeout)
        self._log.debug("Command '{}' output is '{}'".format(self._VERIFY_TPM_CMD, output))
        if not re.search(tpm2_str, output):
            raise content_exceptions.TestFail("Fail to recognise '{}'".format(tpm2_str))
        self._log.info("'{}' is recognised in os level".format(tpm2_str))
        output = self._common_content_lib.execute_sut_cmd(self._TPM_MOD_DETECT_AND_ENUMERATE_CMD,
                                                          "TPM module detect cmd", self._command_timeout)
        self._log.debug("Command '{}' output is '{}'".format(self._TPM_MOD_DETECT_AND_ENUMERATE_CMD, output))
        if not re.search(tpm_detect_str, output):
            raise content_exceptions.TestFail("Fail to detect TPM module")
        self._log.info("TPM module is detected in os level")

    def txt_check_info(self, usb_drive_list):
        """
        This method execute ServerTXTINFO or TxtBtgInfo efi file based on the CBnT platform in the shell
        and check any error in the results.

        :param usb_drive_list: Takes the usb drive list as parameter to run command
        :return: None
        """
        server_txt_cmd = self._TXT_INFO_CMD
        txt_info = None
        if self.platform_family not in CBnT.CBNT_PRODUCT_FAMILIES:
            # Executing ServerTXTinfo on non-CBnT platform
            self._log.info("Looks like the platform is CBNT family")
            server_txt_cmd = self._SERVER_TXT_INFO_CMD

        # Executing TxtBtgInfo or ServerTXTinfo based on platforms for checking error
        self._log.info("Executing '{}' command for checking errors".format(server_txt_cmd))
        for usb_drive in usb_drive_list:
            self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(usb_drive)
            txt_info = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(server_txt_cmd)
            self._log.debug(txt_info)
        # check any error in txt_info
        ret_val = ("\n".join(txt_info).lower()).find("error:") == -1
        if not ret_val:
            for error_line in txt_info:
                if "Error:" in error_line:
                    self._log.info("Error found {}".format(error_line))
                    raise content_exceptions.TestFail("Error found after running '{}' command".format(server_txt_cmd))
        self._log.info("Not found any error in {} command".format(server_txt_cmd))

    def execute_getsec_uefi_tool(self, usb_drive_list, exit_txt_env_flag=True):
        """
        This methods runs the getsec64 EFI tool and verify the system entered in TXT environment
        and if exit_flag is set then system should exit out from TXT environment successfully.

        :param usb_drive_list: List of usb device to search for the efi file and execute the command
        :param exit_txt_env_flag: set If want to come out of TXT environment
        :return: None
        """
        txt_enter_cmd = self._TXT_ENTER_CMD
        txt_exit_cmd = self._TXT_EXIT_CMD
        if self.platform_family in CBnT.CBNT_PRODUCT_FAMILIES:
            txt_enter_cmd = self._TXT_ENTER_CMD_CBNT
            txt_exit_cmd = self._TXT_EXIT_CMD_CBNT
        self._log.info("Entering into the TXT environment")
        if not self._uefi_util_obj.execute_efi_cmd(usb_drive_list, txt_enter_cmd, self._TXT_ENTER_STR):
            raise content_exceptions.TestFail("System has not entered TXT environment")
        self._log.info("System has entered TXT environment")
        if exit_txt_env_flag:
            if not self._uefi_util_obj.execute_efi_cmd(usb_drive_list, txt_exit_cmd, self._TXT_EXIT_STR):
                raise content_exceptions.TestFail("System has not exited TXT environment")
            self._log.info("System has exited TXT environment")

    def verify_secret_flag_de_assert(self, usb_drive_list):
        """
        This method checks if secret flag is de -asserted when the platform is in TXT environment by running
        Server Secrets64.efi -n

        :param usb_drive_list: List of usb device to search for the efi file and execute the command
        :raise: content_exception when fails to find the de-assert message
        :return: None
        """
        secret_bit_de_assert_cmd = self._SERVER_SECRET_DE_ASSERT_CMD
        if self.platform_family in CBnT.CBNT_PRODUCT_FAMILIES:
            secret_bit_de_assert_cmd = self._SERVER_SECRET_DE_ASSERT_CMD_CBNT
        self._log.info("Checking secret bit is de-asserted")
        if not self._uefi_util_obj.execute_efi_cmd(usb_drive_list, secret_bit_de_assert_cmd,
                                                   self._SERVER_SECRET_DE_ASSERT_SUCCESS_MSG):
            raise content_exceptions.TestFail("Fail to de-assert secret bit")
        self._log.info("Secret bit is de-asserted successfully")

    def verify_secret_flag_assert(self, usb_drive_list):
        """
        This method checks if secret flag is asserted when the platform is in TXT environment by running
        Server Secrets64.efi -s

        :param usb_drive_list: List of usb device to search for the efi file and execute the command
        :raise: content_exception when fails to find the assert message
        :return: None
        """
        secret_bit_assert_cmd = self._SERVER_SECRET_ASSERT_CMD
        if self.platform_family in CBnT.CBNT_PRODUCT_FAMILIES:
            secret_bit_assert_cmd = self._SERVER_SECRET_ASSERT_CMD_CBNT
        self._log.info("Checking secret bit is asserted")
        if not self._uefi_util_obj.execute_efi_cmd(usb_drive_list, secret_bit_assert_cmd,
                                                   self._SERVER_SECRET_ASSERT_SUCCESS_MSG):
            raise content_exceptions.TestFail("Fail to assert secret bit")
        self._log.info("Secret bit is asserted successfully")

    def generate_mle_hash(self, mle_hash, out):
        """
        Generates mle hash file for mle element creation

        :param mle_hash: hash algorithm for mle_hash
        :param out: name of file containing mle_hash
        """
        self._log.info("Generating mle hash with {} as the algorithm".format(mle_hash))
        self._os.execute(Tpm2LcpCommands.MLE_HASH + " " + self._TPM2_MLE_HASH_CREATION_CMD %
                         (mle_hash, out), self._command_timeout)

    def create_lcp_elt(self, elt_type, out, tpm_version, min_ver='0', ctrl='2', mle_hash=None, pcr_number=None, alg=None,
                       pcr_hash=None):      # type: (str,str,str,str,str,str,str,str,str) -> None
        """
        Creates a lcp element with flexibility of control, min_ver, tpm_version. The .elt file for the element is stored
        in the SUT's current working directory.

        :param elt_type: string from LCPPolicyElements representing Type of element for lcp list
        :param out:  name of element
        :param min_ver:  minimum version of element
        :param ctrl:  element control
        :param tpm_version: string from TXT constants representing tpm tools version for either legacy or tpm2
        :param mle_hash:  mle_hash_file for MLE element
        :param pcr_number: PCR number for PCR hash PCONF
        :param alg: algorithm type for element
        :param pcr_hash: PCR Hash of associated PCR number
        """

        self._log.info("Creating element of type:" + elt_type + " with min_ver:" + min_ver + " ctrl:" + ctrl)
        if mle_hash is not None and pcr_number is not None:
            raise content_exceptions.TestSetupError("Can't support both elements at once")
        if alg not in [HashAlgorithms.SHA1, HashAlgorithms.SHA256, HashAlgorithms.SHA384, HashAlgorithms.SHA512] \
                and alg is not None:
            raise content_exceptions.TestSetupError("Does not support provided algorithm:" + alg)
        elif mle_hash is not None and elt_type in [LCPPolicyElements.MLE, LCPPolicyElements.MLE_LEGACY]:
            if tpm_version == TXT.TPM_LEGACY:
                if elt_type == LCPPolicyElements.MLE_LEGACY:
                    self._os.execute(Tpm12LcpCommands.CREATE_ELEMENT + " " +
                                    (self.LCP_POLICY_CREATION_DICT[str(elt_type)] % (min_ver, ctrl, out, mle_hash)),
                                     self._command_timeout)
                else:
                    raise content_exceptions.TestSetupError(elt_type + " is not supported by legacy TPM")

            else:
                if elt_type == LCPPolicyElements.MLE_LEGACY:
                    self._os.execute(Tpm2LcpCommands.CREATE_ELEMENT + " " + (self.LCP_POLICY_CREATION_DICT[elt_type] %
                                                                             (min_ver, ctrl, out, mle_hash)),
                                     self._command_timeout)
                else:
                    self._os.execute(Tpm2LcpCommands.CREATE_ELEMENT + " " +
                                     (self.LCP_POLICY_CREATION_DICT[elt_type] % (min_ver, ctrl, out, alg, mle_hash)),
                                     self._command_timeout)

        elif pcr_number is not None and pcr_hash is not None and elt_type is LCPPolicyElements.PCONF:
            self._os.execute(Tpm2LcpCommands.CREATE_ELEMENT + " " + (self.LCP_POLICY_CREATION_DICT[elt_type]
                                                                     % (ctrl, out, alg, pcr_number,
                                                                        pcr_hash)),
                             self._command_timeout)
        else:
            raise content_exceptions.TestSetupError("Element type " + elt_type + " and arguments given do not match")

    def create_lcp2_list(self, out, elements, sig_alg, list_ver): # type: (str,list,str or None,str) -> None
        """
        Creates lcp2 list file with provided elements
        :param out: name of generated list
        :param sig_alg:  signing algorithm type
        :param list_ver:  platform being used to determine the list version
        :param elements: list of elements for the generated list
        :return: None
        """
        if list_ver not in self.LCP_LIST_VERSION_DICT:
            raise content_exceptions.TestSetupError(list_ver + " does not support lcp2 list version")
        list_cmd = Tpm2LcpCommands.CREATE_LIST + self._TPM2_LCP_LIST_CREATION_CMD % \
            (out, self.LCP_LIST_VERSION_DICT[list_ver])
        self._log.info("list_ver: " + self.LCP_LIST_VERSION_DICT[list_ver])
        if sig_alg is not None:
            list_cmd = list_cmd + " --sigalg " + sig_alg
            self._log.info("Signing algorithm type: " + sig_alg)
        if elements is not None:
            for element in elements:
                list_cmd = list_cmd + " " + element + " "
                self._log.info("list added element:" + element)
        self._os.execute(list_cmd, self._command_timeout)

    def sign_lcp2_list(self, out, rev, private_key, public_key, sig_alg='rsa', hash_alg=HashAlgorithms.SHA256):
        # type: (str,str,str,str,str or None,str) -> None
        """
        Signs an input lcp2 list file and generates a new list.

        :param out: name of outputted list
        :param hash_alg: hash algorithm for list
        :param rev: revocation counter
        :param sig_alg: signing algorithm type such as rsa
        :param private_key: private key
        :param public_key: public key
        """
        self._log.info("Signing lcp list with the following hash algorithm:" + hash_alg + ", revocation:" + rev +
                       ", signing algorithm:" + sig_alg + ", private and public key:" + private_key + " " + public_key)
        if hash_alg not in [HashAlgorithms.SHA1, HashAlgorithms.SHA256, HashAlgorithms.SHA384,
                            HashAlgorithms.SHA512, HashAlgorithms.SM2]:
            content_exceptions.TestSetupError("Signing algorithm provided: " + str(sig_alg) + " is not supported")
        self._os.execute(Tpm2LcpCommands.CREATE_LIST + self._TPM2_LCP_LIST_SIGN_CMD %
                         (out, hash_alg, rev, sig_alg, private_key, public_key, out), self._command_timeout)

    def create_policy(self, cbnt_product_version, pol, data, lcp2_lists, masks, policy_type='list', ctrl='2', rev='2',
                      alg=HashAlgorithms.SHA256, min_ver='0', sign=None):
        # type: (str,str,str,list,list,str,str,str,str,str,str) -> None
        """
        Creates a TPM2.0 policy from inputted LCP2 list, and allows for different signatures, revocation counter, masks,
         and control(reading and writing).

        :param cbnt_product_version: CBnT product version
        :param policy_type:  policy type, expecting list or any
        :param ctrl: sg the control over policy
        :param min_ver: expects a string for the minimum version of LCP_POLICY_2  for policy
        :param alg: Expecting a hash algorithm supported by TPM2.0 for policy
        :param pol:  policy file name
        :param data:  data file name
        :param lcp2_lists: input lcp list(s) in python list format
        :param rev:  revocation counter
        :param masks:  the supported hashes for each element in a python list
        :param sign:  the signature of policy such as rsa-3072
        """
        if cbnt_product_version not in CBnT.CBNT_PRODUCT_FAMILIES:
            content_exceptions.TestSetupError(str(cbnt_product_version) + " is not a supported product")
        if policy_type not in self._LCP2_POLICY_TYPES:
            content_exceptions.TestSetupError(str(policy_type) + " is not a supported policy type")
        if alg not in [HashAlgorithms.SHA1, HashAlgorithms.SHA256, HashAlgorithms.SHA384,
                       HashAlgorithms.SHA512, HashAlgorithms.SM2]:
            content_exceptions.TestSetupError(str(alg) + " is not a supported algorithm")
        if data is not None and lcp2_lists is None:
            content_exceptions.TestSetupError("Data file was provided when a list was not provided: " + str(data))
        self._log.info("type of policy:" + policy_type + " ctrl:" + ctrl
                       + " minver:" + min_ver + " revocation:" + rev + " and hash algorithm:" + alg +
                       " with pol and data file: " + pol)
        policy_cmd = Tpm2LcpCommands.CREATE_POLICY + self._TPM2_POLICY_GENERATION_CMD % \
                         (self.LCP_POLICY_VERSION_DICT[cbnt_product_version], policy_type, ctrl, min_ver, pol, data,
                          rev, sign, alg)
        if lcp2_lists is not None:
            for lcp2_list in lcp2_lists:
                policy_cmd = policy_cmd + " " + lcp2_list
            policy_cmd = policy_cmd + " --data " + data
        for mask in masks:
            if mask not in [HashAlgorithms.SHA1, HashAlgorithms.SHA256, HashAlgorithms.SHA384, HashAlgorithms.SHA512,
                            HashAlgorithms.SM2]:
                content_exceptions.TestSetupError(str(mask) + " is not a supported hash for an element in the list")
            policy_cmd = policy_cmd + " --mask " + mask
        self._log.info("command:" + policy_cmd)
        self._os.execute(policy_cmd, self._command_timeout)

    def generate_pcrs(self, alg, usb_drive_list, out): # type: (str,str,str) -> None
        """
        This method generates pcrs with the given algorithm.

        :param usb_drive_list: Takes the usb drive list as parameter to generate pcrs
        :param alg: algorithm used to generate PCRs
        :param out: output file name of pcr file
        :return: None
        """
        self._log.info("Generating pcrs list with hash algorithm:" + alg)
        if alg not in [HashAlgorithms.SHA1, HashAlgorithms.SHA256, HashAlgorithms.SHA384, HashAlgorithms.SHA512,
                       HashAlgorithms.SM2]:
            self._log.exception("Supplied algorithm not supported by pcr generation tool!")
            raise content_exceptions.TestSetupError("Supplied algorithm not supported by pcr generation tool!")
        try:
            pcr_command = Tpm2ToolCmds.PCR_GEN + " -a " + self.HASH_ALGORITHM_HEX[alg] + " -f pcrsForAutomation.pcr"
            for usb_drive in usb_drive_list:
                self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(usb_drive, None)
            self._uefi_util_obj.uefi_navigate_to_usb(pcr_command)
            self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(pcr_command, "INFO: " +
                                                    self.PCR_GENERATION_CHECK[self.HASH_ALGORITHM_HEX[alg]] +
                                                    " bytes written.")
            self._uefi_util_obj.execute_cmd_in_uefi_and_read_response("cp -q pcrsForAutomation.pcr* " + out, None)
            self._log.info("Cleaning up copied pcr file: pcrsForAutomation.pcr")
            self._uefi_util_obj.execute_cmd_in_uefi_and_read_response("rm pcrsForAutomation.pcr*", None)
        except:
            raise content_exceptions.TestFail("Couldn't execute: " + Tpm2ToolCmds.PCR_GEN + " -a " +
                                              self.HASH_ALGORITHM_HEX[alg] + " -f " + out +
                                              " Does your path have spaces?")

    def capture_pcr_hash(self, pcr_file, hash_alg, pcr_number=0):   # type: (str,str,int) -> str
        """
        This method captures the pcr hash associated with a given hashing algorithm and pcr number
        :param pcr_file: PCR file
        :param hash_alg: hash algorithm of PCR file
        :param pcr_number: The PCR number to obtain associated hash
        :return: PCR HASH of associated pcr_number in provided pcr_file
        """
        self._log.info("Capturing hash of pcr file: " + pcr_file + " for the " + str(pcr_number) + " PCR.")
        with open(pcr_file, 'rb') as fp:
            pcr_file_buffer = fp.read().hex()
            pcr2_header = pcr_file_buffer[0:8]
            algorithm_type = pcr_file_buffer[8:12]
            self._log.debug("PCR file header" + pcr2_header + ", PCR file reported algorithm type:" + algorithm_type )
            number_of_available_pcrs_list = list(pcr_file_buffer[12:16])
            temp = number_of_available_pcrs_list[0:2]
            number_of_available_pcrs_list[0:2] = number_of_available_pcrs_list[2:4]
            number_of_available_pcrs_list[2:4] = temp
            number_of_available_pcrs = ""
            if pcr_number > int(number_of_available_pcrs.join(number_of_available_pcrs_list), 16):
                content_exceptions.TestSetupError("Provided pcr number: " + str(pcr_number) +
                                                  " is larger than what the given pcr file: "
                                                  + pcr_file + " can provide.")
            self._log.debug("The given pcr file supports " + number_of_available_pcrs + " PCRs")
            upper = (16 + ((pcr_number+1)*(self._SIZE_OF_PCR_HASH[hash_alg] + self._SIZE_OF_PCR_HEADER) * 2))
            lower = (16 + (pcr_number*(self._SIZE_OF_PCR_HEADER + self._SIZE_OF_PCR_HASH[hash_alg]) +
                           self._SIZE_OF_PCR_HEADER) * 2)
            pcr_number_hash = pcr_file_buffer[lower:upper]
        return pcr_number_hash

    def generate_file_for_tpm2_provisioning(self, policy, original_idef_file, new_idef_file):
        """
        This method creates an index definition(idef) file for tpm2 provisioning.

        :param new_idef_file: the new idef file used for provisioning
        :param original_idef_file: original idef file used as a template for the new idef file
        :param policy: policy file to have copied into a buffer in idef file
        :return: None
        """
        count = 0
        self._log.info("Creating idef file:" + new_idef_file)

        with open(policy, 'rb') as fp:
            data_size = fp.read().hex()
            fp.close()
        fp = io.open(original_idef_file, 'r', encoding='utf-16-le')
        new_file = io.open(new_idef_file, 'w', encoding='utf-16-le')
        for line in fp:
            count = count + 1
            if count == self._LCP_IDEF_DATA_SIZE:
                new_file.write("dataSize: " + hex(len(data_size) // 2) + '\n')
            elif count in self._LCP_IDEF_POLICY_SIZE:
                new_file.write("size: " + hex(len(data_size) // 2) + '\n')
            elif count == self._LCP_IDEF_POLICY_BUFFER:
                new_file.write("buffer: " + data_size + '\n')
            else:
                new_file.write(line)
        new_file.close()

    def modify_linux_grub_file(self, targeted_phrase, deletion=False, path="/boot/efi/EFI/redhat/grub.cfg",
                               new_phase=None):     # type: (str,bool,str,str) -> None
        """
        Modifies grub file in linux OS.

        :param new_phase: new phrase meant to be inserted after the targeted phrase
        :param targeted_phrase: phrase in grub file that serves as a reference for the line of interest for a sed command
        :param deletion: boolean whether the targeted phrase needs to be removed or not
        :param path: path to the grub file
        :return:
        """
        path = f"/boot/efi/EFI/{self._os.os_subtype.lower()}/grub.cfg"
        if deletion:
            self._log.info("Deleting the policy from grub file")
            self._os.execute("sed -i '/" + targeted_phrase.replace("/", "\/") + "/d' " + path, self._command_timeout)
        else:
            self._os.execute("sed -i '/" + targeted_phrase.replace("/", "\/")+"/a " + new_phase.replace("/", "\/") + "' " +
                             path, self._command_timeout)

    def get_sinit_acm_minver(self, usb_drive_list):     # type: (str) -> str
        """
        Captures SINIT ACM version from TXTBtgInfo uefi script.
        :param usb_drive_list: Takes the usb drive list
        :return: returns interger of the ACM version, if fails, returns -1
        """
        for usb_drive in usb_drive_list:
            self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(usb_drive, None)
        self._uefi_util_obj.uefi_navigate_to_usb(self.TXT_BTG_INFO_COMMAND)
        efi_cmd_output = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.TXT_BTG_INFO_COMMAND,None)
        minver = False
        efi_cmd_output = efi_cmd_output
        for line in efi_cmd_output:
            line = line.strip('\r').strip(" ")
            if line == 'Chipset ACM Type                 = 0x1':
                minver = True
                continue
            if minver is True:
                return line.split('= ')[1]
        raise content_exceptions.TestFail("Couldn't find ACM version")

    def check_cleared_po_index_tpm2(self, usb_drive_list, nv_index):    # type: (str,str) -> bool
        """
        Checking if PO index at the specified nv index is cleared.
        :param usb_drive_list:
        :param nv_index: NV index to look up
        :return: True if nv index is not found (cleared), false otherwise.
        """
        self._log.info("Checking PO index is cleared using UEFI shell script")
        try:
            tpm_log = self._TPM_PO_INDEX_ERASE_CMD
            for usb_drive in usb_drive_list:
                self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(usb_drive, None)
            self._uefi_util_obj.uefi_navigate_to_usb(tpm_log)
            self._log.debug("Attempting to execute:" + tpm_log)
            tpm_log_data = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(tpm_log)
            cleared = True
            for line in tpm_log_data:
                if line == "NvIndex:          "+nv_index+'\r':
                    cleared = False
            return cleared
        except:
            content_exceptions.TestFail("Could not generate tpm2 log file")

    def boot_choice_selection(self, boot_option):   # type: (str) -> None
        """
        Chooses boot option off of the boot menu
        :param boot_option: boot option to attempt a successful boot
        :return: None
        """
        if self._boot.boot_choice(boot_option):
            self._log.info("Boot option: " + boot_option + " was selected successful.")
        else:
            raise content_exceptions.TestSetupError("Boot option: " + boot_option + "was not selected successfully.")

    def cleanup(self, return_status):  # type: (bool) -> None
        """Test Cleanup"""
        if not self._os.is_alive():
            self._log.info("SUT is down, applying power cycle to make the SUT up")
            self._log.info("AC Off")
            self._ac_obj.ac_power_off(self._AC_TIMEOUT)
            self._log.info("AC On")
            self._ac_obj.ac_power_on(self._AC_TIMEOUT)
            self._log.info("Waiting for OS")
            if self._common_content_lib.is_bootscript_required():
                self._common_content_lib.execute_boot_script()
            self._os.wait_for_os(self._reboot_timeout)
        else:
            self._log.info("Loading default bios settings")
            self._bios.default_bios_settings()
        # copy logs to CC folder
        self._log.info("Command center log folder='{}'".format(self._cc_log_path))
        self._common_content_lib.copy_log_files_to_cc(self._cc_log_path)
        super(TxtBaseTest, self).cleanup(return_status)

    def get_tpm_version(self):
        """
        This method gets the version of TPM installed in os level

        :raise: content_exceptions if unable to recognise tpm
        :return: TPM version
        """
        tpm_detect_str = "tpm0"
        tpm_cmd_output_string = self._common_content_lib.execute_sut_cmd(self._TPM_MOD_DETECT_AND_ENUMERATE_CMD,
                                                                         "TPM module detect cmd", self._command_timeout)
        self._log.debug(
            "Command '{}' output is '{}'".format(self._TPM_MOD_DETECT_AND_ENUMERATE_CMD, tpm_cmd_output_string))
        if not re.search(tpm_detect_str, tpm_cmd_output_string):
            raise content_exceptions.TestFail("Fail to detect TPM module")
        self._log.info("TPM module is detected in os level")
        verify_tpm_output_string = self._common_content_lib.execute_sut_cmd(self._VERIFY_TPM_CMD, "Check TPM devices",
                                                                            self._command_timeout)
        self._log.debug("Command '{}' output is '{}'".format(self._VERIFY_TPM_CMD, verify_tpm_output_string))
        if re.search(TpmVersions.TPM1P2, verify_tpm_output_string):
            self._log.info("Detected TPM1.2 Version")
            return TpmVersions.TPM1P2
        if re.search(TpmVersions.TPM2, verify_tpm_output_string):
            self._log.info("Detected TPM2 Version")
            return TpmVersions.TPM2

    def perform_graceful_g3(self):
        """Performs graceful shutdown"""
        self._log.info("Performs shutdown and boot the SUT")
        self._common_content_lib.perform_graceful_ac_off_on(self._ac_obj)
        self._os.wait_for_os(self._reboot_timeout)
        time.sleep(self._WAIT_TIME)

    def read_current_pcr_values(self, filename, tpm_version=TpmVersions.TPM2):
        """
        This Method Reads the contents of PCR and saves them to the SUT.

        :param filename: filename in string where the Read PCR values are saved into.
        :param tpm_version: Version of TPM to work on
         raise: content_exceptions.TestFail
        """
        command_to_get_path = self._CMD_TO_GET_FILE_PATH.format(filename)
        os_info = self._common_content_lib.get_linux_hostnamectl_info()
        if tpm_version == TpmVersions.TPM2:
            version_id = float(re.findall(r"\d+.\d+", os_info['operating system'])[0])
            if version_id > 8.2:
                tpm_read_pcr_cmd = "tpm2_pcrread > {}".format(filename)
            else :
                tpm_read_pcr_cmd = "tpm2_pcrlist > {}".format(filename)
            self._log.debug(
                "start the TPM communication service by executing the command : {}".format(self._TPM_COMMUNICATION_CMD))
            self._os.execute_async(self._TPM_COMMUNICATION_CMD)
        else:
            required_tpm_pcrs_path = ""
            output_string = self._common_content_lib.execute_sut_cmd(self._PCRS_FIND_COMMAND, self._PCRS_FIND_COMMAND,
                                                                     self._command_timeout)
            self._log.debug("{} command output : {}".format(self._PCRS_FIND_COMMAND, output_string))
            for each_path in output_string.split("\n"):
                if self._PCR_PATH in str(each_path):
                    required_tpm_pcrs_path = each_path
            if not required_tpm_pcrs_path:
                raise content_exceptions.TestFail("Fail to detect TPM PCRS Path in the SUT")
            tpm_read_pcr_cmd = "cat {} > {}".format(required_tpm_pcrs_path, filename)

        self._log.info("save the current values of the PCRs to the file {}".format(filename))
        self._log.debug("command : {}".format(tpm_read_pcr_cmd))
        self._common_content_lib.execute_sut_cmd(tpm_read_pcr_cmd, tpm_read_pcr_cmd, self._command_timeout)
        pcr_file_path = self._common_content_lib.execute_sut_cmd(command_to_get_path, command_to_get_path,
                                                                 self._command_timeout)
        if pcr_file_path == "":
            raise content_exceptions.TestFail("Failed to Read the contents of PCR and save them to the SUT.")
        return pcr_file_path

    def verify_tpm(self):
        """
        This function check TPM Device is present in the SUT or not

        raise: content_exceptions.TestFail
        """
        with ProviderFactory.create(self._csp_cfg, self._log) as self._csp:
            self.platform_file = ItpXmlCli(self._log, self._cfg)
            self.platform_read = PlatformConfigReader(self.platform_file.get_platform_config_file_path(),
                                                      test_log=self._log)
            self._log.info("verify the TPM 2.0")
            tpm_device = self.platform_read.get_current_tpm_device()
            if tpm_device != self._TPM_DEVICE:
                raise content_exceptions.TestFail("Failed to verify TPM Device, Expected={}, Actual={}".format(
                    self.TPM_DEVICE, tpm_device))

    def get_pcrdump_from_uefi(self, pcr_dump_cmd, pcr_dump_dir):
        """
        This Method boots to uefi shell and selects the usb drive where .efi files are present and then executes
        pcrdump command.

        :param pcr_dump_cmd: pcr command to execute
        :param pcr_dump_dir: directory name where efi file is present
        :raise: content exception if unable to get result after running pcr command
        :return: result of the pcrdump command
        """
        self._log.info("Collecting data from uefi shell by executing command {}".format(pcr_dump_cmd))
        usb_drive_list = self._uefi_util_obj.get_usb_uefi_drive_list()
        usb = self._uefi_util_obj.get_usb_folder_path(usb_drive_list, pcr_dump_dir)
        self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(usb)
        self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            self._uefi_util_obj.CWD + " " + pcr_dump_dir)
        self._log.info("Executing command {}".format(pcr_dump_cmd))
        efi_output = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(pcr_dump_cmd)
        if not efi_output:
            raise content_exceptions.TestFail("Unable to get output after running the "
                                              "command {}".format(pcr_dump_cmd))
        self._log.debug("Output of pcr command {} is {}".format(pcr_dump_cmd, efi_output))

        return efi_output

    def verify_pcr_values_equal(self, pcr_res_before, pcr_res_after, pcr_num):
        """
        This function compares the pcr values are equal or not with the given two result

        :param pcr_res_before: output generated by pcr efi command before
        :param pcr_res_after: output generated by pcr efi command after
        :param pcr_num: pcr value to be compared
        :return: return True if pcr value is equal else False
        """
        is_equal = True
        self._log.info("Comparing PCR value are same for the input pcr data")
        dict_pcr_before = {}
        dict_pcr_after = {}
        for line in pcr_res_before:
            if self.PCR_STRING in line:
                pcr_value = line.split(":")
                dict_pcr_before[pcr_value[0].strip()] = pcr_value[1].strip()
        self._log.debug("Before data PCR values: {}".format(dict_pcr_before))
        for line in pcr_res_after:
            if self.PCR_STRING in line:
                pcr_value = line.split(":")
                dict_pcr_after[pcr_value[0].strip()] = pcr_value[1].strip()
        self._log.debug("After data PCR values: {}".format(dict_pcr_after))
        if dict_pcr_before['{}'.format(pcr_num)] != dict_pcr_after['{}'.format(pcr_num)]:
            self._log.debug("Before reset:{} is different from PCR value after reset"
                            ":{} for {}".format(dict_pcr_before['{}'.format(pcr_num)],
                                                dict_pcr_after['{}'.format(pcr_num)], pcr_num))
            is_equal = False
        else:
            self._log.debug("Before reset:{} is same from PCR value after reset"
                            ":{} for {}".format(dict_pcr_before['{}'.format(pcr_num)],
                                                dict_pcr_after['{}'.format(pcr_num)], pcr_num))

        return is_equal

    def pcrdump64_data_formatting(self, pcrdump64_output):
        """
        This methods formats the output of pcrdump64.efi and returns a dictionary of all pcr values

        :param: output of pcrdump64.efi
        :raise: if unable to get pcr values
        :return: dictionary of pcr values from pcrdump64.efi output
        """
        self._log.info("Extracting output of PCR from pcrdump64 output")
        pcr_dump_list = []
        pcr_dump_dict = {}
        for each in pcrdump64_output:
            pcr_value = ''
            if re.search(self.PCR_STRING, each):
                index = pcrdump64_output.index(each)
                pcr_value_str = pcrdump64_output[index].strip() + ' ' + pcrdump64_output[index + 1].strip()
                if "  " in pcr_value_str:
                    pcr_value = " ".join(pcr_value_str.split("  "))
                pcr_dump_list.append(pcr_value)
        for element in pcr_dump_list[:self.PCR_END_VALUE]:
            pcr_dump_dict[element.split(":")[0].strip()] = element.split(":")[1].strip()
        if not pcr_dump_dict:
            raise content_exceptions.TestFail("Tpm is not enable, unable to fetch PCR value")
        self._log.debug("Output of pcrdump64 for all PCRs is {}".format(pcr_dump_dict))

        return pcr_dump_dict

    def compare_pcr_value(self, before_pcr, after_pcr, pcr_num=False):
        """
        This methods compares dictionary of pcr values of before and after reset
         and returns error dictionary of all unmatched pcr values

        :param: before reset pcr value
        :param: after reset pcr value
        :param: by default all pcr value from 0 to 7 will be compared, if single pcr value needs to compared,
            pcr_num="PCR 00" or "PCR 0" format can be fed
        :return: error dictionary of unmatched all pcr value
        """
        self._log.info("Comparing PCR values before and after reset")
        error_dict = {}
        if not pcr_num:
            for keys in before_pcr.keys():
                if before_pcr[keys] != after_pcr[keys]:
                    self._log.debug("Before reset:{} does not match with PCR value after reset"
                                    ":{} for {}".format(before_pcr[keys], after_pcr[keys], keys))
                    error_dict["before_reset_{}".format(keys)] = before_pcr[keys]
                    error_dict["after_reset_{}".format(keys)] = after_pcr[keys]
                else:
                    self._log.debug("Before reset:{} match with PCR value after reset"
                                    ":{} for {}".format(before_pcr[keys], after_pcr[keys], keys))
            error_list = list(error_dict.items())
        else:
            if before_pcr[pcr_num] != after_pcr[pcr_num]:
                error_dict["before_reset_{}".format(pcr_num)] = before_pcr[pcr_num]
                error_dict["after_reset_{}".format(pcr_num)] = after_pcr[pcr_num]
                self._log.debug("Before reset:{} does not match PCR value after reset"
                                    ":{} for {}".format(before_pcr[pcr_num], after_pcr[pcr_num], pcr_num))
            else:
                self._log.debug("Before reset:{} match with PCR value after reset"
                                ":{} for {}".format(before_pcr[pcr_num], after_pcr[pcr_num], pcr_num))
            error_list = list(error_dict.items())

        return error_list

    def copy_file_from_collateral_to_usb(self, phy, file_name, host_usb_provider):
        """
        Copy the  zip files from collateral to USB drive.

        :param phy: physical control provider object
        :param file_name: File name to copy
        :param host_usb_provider: Host usb provider object
        """
        self._log.info("Copying zip file to usb")
        usb_drive = host_usb_provider.get_hotplugged_usb_drive(phy)
        self._log.debug("Hot-plugged USB drive='{}'".format(usb_drive))
        usb_path = host_usb_provider.copy_collateral_to_usb_drive(file_name, usb_drive)  # Copying file to USB drive
        self._log.debug("The file is copied to USB folder '{}'".format(usb_path))
        phy.disconnect_usb(self.usb_set_time)  # USB disconnecting
        phy.connect_usb_to_sut(self.usb_set_time)  # USB connecting to SUT
        self._log.info("files copied successfully")

    def get_boot_order_xmlcli(self, itp_xml_cli_util):
        """
        This function get the current boot order using itp ipccli xmlcli
        :param itp_xml_cli_util: obj of itp_xml_cli
        :return: current boot-order present in xmlcli platform configuration file.
        """
        try:
            boot_order = itp_xml_cli_util.get_current_boot_order_string()
        except Exception as e:
            self._log.debug("Caught IPC_Error where IPC failed.  Attempting to initiate forcereconfig.  "
                            "Exception data: {}".format(e))
            self.itp.forcereconfig()
            boot_order = itp_xml_cli_util.get_current_boot_order_string()
        self._log.info("boot order {}".format(boot_order))
        return boot_order

    def set_uefi_shell_bootorder(self, itp_xml_cli_util):
        """
        This function set the boot order to UEFI shell using itp ipccli xmlcli
        :param itp_xml_cli_util: obj of itp_xml_cli
        """
        try:
            itp_xml_cli_util.set_default_boot(BootOptions.UEFI)
        except Exception as e:
            self._log.debug("Caught IPC_Error where IPC failed.  Attempting to initiate forcereconfig.  "
                            "Exception data: {}".format(e))
            self.itp.forcereconfig()
            itp_xml_cli_util.set_default_boot(BootOptions.UEFI)

    def set_boot_order(self, itp_xml_cli_util, boot_order):
        """
        This function sets the boot order which is passed as a parameter
        :param itp_xml_cli_util: obj of itp_xml_cli
        :param boot_order: boot order to be set
        """
        try:
            itp_xml_cli_util.set_boot_order(boot_order)
        except Exception as e:
            self._log.debug("Caught IPC_Error where IPC failed.  Attempting to initiate forcereconfig.  "
                            "Exception data: {}".format(e))
            self.itp.forcereconfig()
            itp_xml_cli_util.set_boot_order(boot_order)

    def clear_secret_flag(self):
        """
        This Function Clear secrets flag and verifies if the secret flag is cleared or not.

        :raise: content_exceptions Secret bit is not cleared
        :return: None
        """
        address_secret_flag = hex(self.txt_consts.TXT_REG_PRIVATE_BASE +
                                  self.txt_consts.TXT_REG_OFFSETS["SECRETS_PRIV"]).rstrip('L') + 'p'
        lt_e2sts_mem_address = hex(self.txt_consts.TXT_REG_PUBLIC_BASE +
                                   self.txt_consts.TXT_REG_OFFSETS["LT_E2STS"]).rstrip('L') + 'p'
        self._log.info(
            "Writing to memory location '{}' and value '{}' to clear the secret flag".format(address_secret_flag,
                                                                                             self._BYTE_SIZE_TO_READ))
        self._log.debug("Halting CPU")
        try:
            self._sdp.halt()
            self._sdp.itp.threads[self.THREAD_INDEX].mem(address_secret_flag, self._BYTE_SIZE_TO_WRITE,
                                                         self._VALUE_TO_WRITE)
            # Re-read E2STS to confirm secrets bit was cleared
            read_e2sts = self._sdp.mem_read(lt_e2sts_mem_address, self._BYTE_SIZE_TO_READ)
            self._log.info("Read back value at address '{}' is: {}".format(lt_e2sts_mem_address, hex(read_e2sts)))
        except Exception as e:
            self.itp.forcereconfig()
            self._sdp.halt()
            self._sdp.itp.threads[self.THREAD_INDEX].mem(address_secret_flag, self._BYTE_SIZE_TO_WRITE,
                                                         self._VALUE_TO_WRITE)
            # Re-read E2STS to confirm secrets bit was cleared
            read_e2sts = self._sdp.mem_read(lt_e2sts_mem_address, self._BYTE_SIZE_TO_READ)
            self._log.info("Read back value at address '{}' is: {}".format(lt_e2sts_mem_address, hex(read_e2sts)))
        finally:
            self._sdp.go()
        if not (hex(read_e2sts)) == hex(self._EXPECTED_E2STS_VAL):
            raise content_exceptions.TestFail("Secret bit is not cleared")
        self._log.info("Secret bit is cleared")

    def mle_launch_and_secret_bit_is_set(self):
        """
        This function checks if MLE is launch successfully and secret bit is set properly.

        :raise: content_exceptions if MLE is not launch successfully or secret bit is not set
        :return: None
        """
        # Verify if MLE is launched
        mle_res = self._validate_txt_registers_trusted(expect_ltreset=False, mask_ltreset=False)
        # verify secret bit is set
        self._sdp.halt()
        expected_lt_e2sts_val = self.txt_consts.LT_E2STS_EXP
        reg_lt_e2sts_add = hex(self.txt_consts.TXT_REG_PUBLIC_BASE +
                               self.txt_consts.TXT_REG_OFFSETS["LT_E2STS"]).rstrip('L') + 'p'
        self._log.debug("Reading the register '{}' value".format(self.txt_consts.LT_E2STS))
        read_e2sts = self._sdp.mem_read(reg_lt_e2sts_add, self._BYTE_SIZE_TO_READ)
        self._log.debug("Read back value for register '{}' is : '{}'"
                        .format(self.txt_consts.LT_E2STS, hex(read_e2sts)))
        self._sdp.go()
        if not mle_res and (hex(read_e2sts)) == hex(expected_lt_e2sts_val):
            raise content_exceptions.TestFail("MLE did not launched successfully or secret bit is not set")
        self._log.info("MLE launched successfully and secret bit is set")

    def get_core_uncore_value(self):
        """
        This function verifies core and uncore value.

        :raise: content_exceptions if unable to verify core and uncore value.
        """
        self._log.info("Verifying core and uncore value ")
        self._cpu_provider.populate_cpu_info()
        no_of_sockets_from_os = int(self._cpu_provider.get_number_of_sockets())
        family_name = self._common_content_lib.get_platform_family()
        no_of_cores_from_os = int(self._cpu_provider.get_number_of_cores())
        self._csp = ProviderFactory.create(self._csp_cfg, self._log)
        socket_core_count = {}
        try:
            self._csp.refresh()
            for each_socket in range(0, no_of_sockets_from_os):
                try:
                    socket_uncore = self.txt_consts.SOCKET_UNCORE_PCU_RESOLVED_CORES_CMD_STR.get(family_name)
                    self._log.info("executing itp command {}".format(socket_uncore))
                    get_reg_output = self._csp.get_by_path(self._csp.UNCORE, "punit.resolved_cores_cfg",
                                                           socket_index=each_socket)
                    count = [i for i in bin(get_reg_output) if i == "1"]
                    socket_core_count["CPU"+str(each_socket)] = len(count)
                    self._log.info("Registration output {}".format(get_reg_output))
                except Exception as e:
                    self._log.debug("Caught IPC_Error where IPC failed.  Attempting to initiate forcereconfig.  "
                                    "Exception data: {}".format(e))
                    get_reg_output = self._csp.get_by_path(self._csp.UNCORE, "punit.resolved_cores_cfg",
                                                           socket_index=each_socket)
                    self._log.info("Registration output {}".format(get_reg_output))
                    count = [i for i in bin(get_reg_output) if i == "1"]
                    socket_core_count["CPU"+str(each_socket)] = len(count)
        except Exception as e:
            raise content_exceptions.TestFail("Unable to Verifying core and uncore value with ITP command {}".format(e))
        self._log.info("Socket count {} using ITP ".format(socket_core_count))
        return socket_core_count

    def enable_and_verify_bios_knob_without_bios_default(self, bios_config_file):
        """
        This method enable and verify the bios knobs

        :param: bios_config_file: Config file path
        """
        self._bios_util.set_bios_knob(bios_config_file)  # To set the bios knob setting
        self.perform_graceful_g3()
        self._bios_util.verify_bios_knob(bios_config_file)  # To verify the Bios knob value set

    def tboot_installation(self):
        """
        This methods installs Tboot
        """
        for command in self.TBOOT_INSTALLATION_CMD:
            output: OsCommandResult = self._os.execute(command, self._command_timeout)
            if output.cmd_failed():
                raise content_exceptions.TestSetupError(f"{command} failed with return code {output.return_code}.\nstderr:\n{output.stderr}")
            self._log.debug("Output of command {} is {}".format(command, output))

        self._log.info("Copying tboot to sut and installing")
        tboot_zip_file, tboot_sinit_file = self._common_content_configuration.get_tboot_file_path()
        tboot_fn: str = os.path.splitext(os.path.basename(tboot_zip_file))[0]
        if tboot_fn.endswith(".tar"):
            tboot_fn = os.path.splitext(tboot_fn)[0]
        tboot_sut_path: str = Path(os.path.join(self._common_content_lib.ROOT_PATH, tboot_fn)).as_posix()
        tboot_path: str = self._install_collateral.download_and_copy_zip_to_sut(tboot_sut_path, tboot_zip_file)
        tboot_path = Path(os.path.join(tboot_path, tboot_fn)).as_posix()
        self._log.info("Tboot path is {}".format(tboot_path))
        self._log.info("Running make command")
        sut_cmd_result: OsCommandResult = self._os.execute(self.TBOOT_MAKE_CMD, self._command_timeout, tboot_path)
        if sut_cmd_result.cmd_failed():
            raise content_exceptions.TestSetupError(f"{self.TBOOT_MAKE_CMD} failed with return code {sut_cmd_result.return_code}.\nstderr:\n{sut_cmd_result.stderr}")

        tboot_sinit_sut_path: str = Path(os.path.join("/boot", os.path.basename(tboot_sinit_file))).as_posix()
        self._os.copy_local_file_to_sut(tboot_sinit_file, tboot_sinit_sut_path)

        for command in self.GRUB_CMD:
            command: str = command.format(self._os.os_subtype)
            output: OsCommandResult = self._os.execute(command, self._command_timeout)
            if output.cmd_failed():
                raise content_exceptions.TestSetupError(f"{command} failed with return code {output.return_code}.\nstderr:\n{output.stderr}")
            self._log.debug("Output of command {} is {}".format(command, output))

        efi_path: str = self.EFI_FILEPATH.format(self._os.os_subtype)
        chk_efi_res: OsCommandResult = self._os.execute(f"ls {efi_path}", timeout=self._command_timeout)
        if chk_efi_res.cmd_passed():
            self._common_content_lib.execute_sut_cmd(f"rm -rf {efi_path}", "To delete a folder",
                                                     self._command_timeout, self._common_content_lib.ROOT_PATH)

        self._common_content_lib.execute_sut_cmd(f"mkdir -p {efi_path}", "To Create a folder",
                                                 self._command_timeout, self._common_content_lib.ROOT_PATH)

        for command in self.COPY_MOD_FILE_CMD:
            command: str = command.format(self._os.os_subtype)
            output: OsCommandResult = self._os.execute(command, self._command_timeout)
            if output.cmd_failed():
                raise content_exceptions.TestSetupError(f"{command} failed with return code {output.return_code}.\nstderr:\n{output.stderr}")
            self._log.debug("Output of command {} is {}".format(command, output))

        self.modify_linux_grub_file(targeted_phrase=self.SEARCH_STR_TBOOT, new_phase=self.REPLACE_STR_TBOOT, path=efi_path)

    def install_tboot_mercurial(self):
        """Install tboot using mercurial from Intel SourceForge code repo."""
        self._log.debug("Remove old tboot install.")
        self._install_collateral.yum_remove("tboot")  # remove old install
        self._log.debug("Install mercurial and grub2 EFI tools.")
        self._install_collateral.yum_install("mercurial grub2-efi-x64-modules")
        tboot_dir = "/tmp/tboot"
        tboot_repo = self.tboot_data.LINK_TO_CLONE_LATEST_TBOOT
        self._log.debug(f"Cloning tboot source from Intel SourceForge {tboot_repo}.")
        result = self._os.execute(f"mkdir -p {tboot_dir}; cd {tboot_dir}; hg clone {tboot_repo}; cd code; "
                                  f"make && make install; grub2-mkconfig -o /boot/efi/EFI/{self._os.os_subtype}/grub.cfg",
                                  self._command_timeout)
        self._log.debug(f"Tboot install stdout: {result.stdout}\n\t"
                        f"Tboot install stderr: {result.stderr}")

        if not self._os.check_if_path_exists(self.EFI_FILEPATH, directory=True):
            self._os.execute(f"mkdir -p {self.EFI_FILEPATH}", self._command_timeout)
        for command in self.COPY_MOD_FILE_CMD:
            command: str = command.format(self._os.os_subtype)
            output: OsCommandResult = self._os.execute(command, self._command_timeout)
            if output.cmd_failed():
                raise content_exceptions.TestSetupError(f"{command} failed with return code {output.return_code}.\nstderr:\n{output.stderr}")
            self._log.debug("Output of command {} is {}".format(command, output))

