#!/usr/bin/env python
#################################################################################
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
#################################################################################

import sys
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.bios_menu import BiosBootMenuProvider
from dtaf_core.providers.uefi_shell import UefiShellProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.lib import content_base_test_case
from src.security.tests.tpm.tpm_constants import TPM
from src.lib.uefi_util import UefiUtil
from src.lib.bios_util import ItpXmlCli
from src.lib.bios_util import BootOptions


class dtpmuefiregistercommands(content_base_test_case.ContentBaseTestCase):
    """
    Glasgow ID : 49323-TPM 2.0 - UEFI register commands
    This test case is to confirm DTPM is Established and memory mapped registry value is valid in uefi internal shell
    Using the UEFI built-in "mm" command to verify UEFI Vendor ID and Device ID reads.
    pre-requisites:
    Hardware
    1. One SUT platform with TPM 2.0 module installed or fTPM; supported CPU, Memory, and HDD.

    Software
    1. Latest BIOS that supports TPM or fTPM.

    Using TPM 2.0 (DTPM):
    1.	Turn AC off on the SUT and Install TPM 2.0 module unless fTPM is present on platform.
    2.	Setup Administrator Password in System Setup menu: "password" can be used but it will warn of weakness.
        NOTE: (For TPM 2.0 and further versions) There aren't any specific settings required to enable TPM 2.0;
    this is different from TPM 1.2, which required actions and settings to enable and activate.
    TPM 2.0 architecture doesn't require those steps related to TPM 1.2.

    Using fTPM 2.0:
    1.	Please complete TC "Enabling fTPM on a system" before running this test.
    """
    TEST_CASE_ID = ["G49323", "TPM 2.0 - UEFI register commands"]
    BIOS_BOOTMENU_CONFIGPATH = "suts/sut/providers/bios_bootmenu"
    UEFI_CONFIG_PATH = 'suts/sut/providers/uefi_shell'
    TPM_DID_VID = "Device ID/Vendor ID"
    ACCESS_BIT = "access bit"
    ACTIVE_LOCALITY = "active locality"
    REQUEST_USE = "request use"
    RELINQUICH = "relinquich"
    REQUEST_ACCESS = "request access"
    ACCESS_WIDTH = 1
    ACCESS_WIDTH_FOUR = 4
    BIT_VAL_ZERO = "0"
    BIT_VAL_TWENTY = "20"
    BIT_VAL_TWO = "2"
    BIT_VAL_ONE = "1"
    WAIT_TIME_OUT = 5

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of dtpm/ftpm established and checking the registry

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """

        super(dtpmuefiregistercommands, self).__init__(test_log, arguments, cfg_opts)
        uefi_cfg = cfg_opts.find(self.UEFI_CONFIG_PATH)
        self._uefi_obj = ProviderFactory.create(uefi_cfg, test_log)  # type: UefiShellProvider
        bios_boot_menu_cfg = cfg_opts.find(self.BIOS_BOOTMENU_CONFIGPATH)
        self._bios_boot_menu_obj = ProviderFactory.create(bios_boot_menu_cfg, test_log)  # type: BiosBootMenuProvider
        self.tpm_consts = TPM.get_subtype_cls(
            "TPM" + self._common_content_lib.get_platform_family(), False)
        self._uefi_util_obj = UefiUtil(
            self._log,
            self._uefi_obj,
            self._bios_boot_menu_obj,
            self.ac_power,
            self._common_content_configuration, self.os)
        self._bios_boot_menu_entry_wait_time = self._common_content_configuration.bios_boot_menu_entry_wait_time()
        self._csp_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._csp = None
        self.itp_xml_cli_util = None
        self.previous_boot_oder = None

    def prepare(self):
        # type: () -> None
        """
        Pre-validating whether sut is boot to uefi shell.

        :return: False if system did not boot to uefi shell.
        """
        super(dtpmuefiregistercommands, self).prepare()

    def get_memory_command(self, mem_address, access_width=1, noninteractive_mode=True, bit_val="10"):
        """
        get memory command on UEFI shell.
        :param mem_address: register address in hex
        :param access_width: how many bytes to read
        :param noninteractive_mode:
        :param bit_val: get clear/set the bit val
        :return: register contents
        """
        self._log.info("Memory address to read: " + mem_address)
        if access_width != 1 and noninteractive_mode:
            return "mm " + mem_address + " -w " + str(access_width) + " -n"
        elif noninteractive_mode:
            return "mm " + mem_address + " -n"
        else:
            return "mm " + mem_address + " " + bit_val

    def validate_memory_flag(self, registry_value, tpm_access_val, comment_str):
        """
        Get value from uefi shell and compared with the expected value

        :param registry_value: Expected registry value
        :param tpm_access_val: value which is retrived from uefi shell
        :param comment_str: registry string
        :return: return True if the value matches with expected value.
        """
        tpm_val_flag = False
        for value in tpm_access_val:
            if "MEM" in value:
                tpm_val = str(value.split(":")[-1]).strip()
                if registry_value == tpm_val:
                    self._log.info(
                        "Value of TPM {} Memory information is excepted value '{}'".format(
                            comment_str, tpm_val))
                    tpm_val_flag = True
                else:
                    self._log.error(
                        "Value of TPM {} Memory information is not excepted value '{}'".format(
                            comment_str, tpm_val))
        return tpm_val_flag

    def verify_dtpm_uefi_mm_registry(self):
        """
        This function compares registry value which is retrived from uefi using mm commands with the expected value.

        tpm access accepted value is "0xA1".
        activeLocality accepted value is "0x81".
        requestUse accepted value is "0xA1".

        :return: True if all the value matches are True
        """
        dtpm_val_flag = []
        dtpm_access_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            self.get_memory_command(
                self.tpm_consts.DTPM_ACCESS, self.ACCESS_WIDTH, True, self.BIT_VAL_ZERO))
        dtpm_val_flag.append(
            self.validate_memory_flag(
                self.tpm_consts.DTPM_MM_ACCESS_EXP_VAL,
                dtpm_access_val,
                self.ACCESS_BIT))

        self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            self.get_memory_command(
                self.tpm_consts.DTPM_ACCESS, self.ACCESS_WIDTH, False, self.BIT_VAL_TWENTY))
        dtpm_access_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            self.get_memory_command(
                self.tpm_consts.DTPM_ACCESS, self.ACCESS_WIDTH, True, self.BIT_VAL_ZERO))
        dtpm_val_flag.append(
            self.validate_memory_flag(
                self.tpm_consts.DTPM_MM_ACCESS_AL_EXP_VAL,
                dtpm_access_val,
                self.ACTIVE_LOCALITY))

        self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            self.get_memory_command(
                self.tpm_consts.DTPM_ACCESS, self.ACCESS_WIDTH, False, self.BIT_VAL_TWO))
        dtpm_access_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            self.get_memory_command(
                self.tpm_consts.DTPM_ACCESS, self.ACCESS_WIDTH, True, self.BIT_VAL_ZERO))
        dtpm_val_flag.append(
            self.validate_memory_flag(
                self.tpm_consts.DTPM_MM_ACCESS_EXP_VAL,
                dtpm_access_val,
                self.REQUEST_USE))

        return all(dtpm_val_flag)

    def verify_ftpm_uefi_mm_registry(self):
        """
        This function compares registry value which is retrived from uefi using mm commands with the expected value.

        tpm access accepted value is "0x83".
        activeLocality accepted value is "0x81".
        requestUse accepted value is "0x83".

        :return: True if all the value matches are True
        """
        ftpm_val_flag = []
        ftpm_access_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            self.get_memory_command(
                self.tpm_consts.FTPM_ACCESS, self.ACCESS_WIDTH, True, self.BIT_VAL_ZERO))
        ftpm_val_flag.append(self.validate_memory_flag(self.tpm_consts.FTPM_MM_ACCESS_EXP_VAL,
                                                       ftpm_access_val, self.ACCESS_BIT))

        self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            self.get_memory_command(
                self.tpm_consts.FTPM_ACCESS, self.ACCESS_WIDTH, True, self.BIT_VAL_TWO))
        ftpm_access_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            self.get_memory_command(
                self.tpm_consts.FTPM_ACCESS, self.ACCESS_WIDTH, True, self.BIT_VAL_ZERO))
        ftpm_val_flag.append(
            self.validate_memory_flag(
                self.tpm_consts.FTPM_MM_DID_VID_EXP_VAL,
                ftpm_access_val,
                self.RELINQUICH))
        self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.get_memory_command
                                                                  (self.tpm_consts.FTPM_ACCESS,
                                                                   self.ACCESS_WIDTH, True, self.BIT_VAL_ONE))
        ftpm_access_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            self.get_memory_command(self.tpm_consts.FTPM_ACCESS, self.ACCESS_WIDTH, True,
                                    self.BIT_VAL_ZERO))
        ftpm_val_flag.append(
            self.validate_memory_flag(
                self.tpm_consts.FTPM_MM_ACCESS_EXP_VAL,
                ftpm_access_val,
                self.REQUEST_ACCESS))
        return all(ftpm_val_flag)

    def execute(self):
        """
        This function will check DTPM/FTPM in UEFI registry commands.
        1. Verify Locality0 TPM_DID_VID_0 returns expected data of DTPM/FTPM
        2. DTPM: write 1 to locality 0 and verity the response using mm commands - bit 5 clear previous write
        3. FTPM: Relinquish locality - bit 2 clear the previous write

        return: True If the UEFI registry commands values are expected
        """
        self._csp = ProviderFactory.create(self._csp_cfg, self._log)  # type: SiliconRegProvider
        self.itp_xml_cli_util = ItpXmlCli(self._log, self._cfg)
        self.previous_boot_oder = self.itp_xml_cli_util.get_current_boot_order_string()
        self._log.info("Previous boot order {}".format(self.previous_boot_oder))
        self.itp_xml_cli_util.set_default_boot(BootOptions.UEFI)
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self._log.info("waiting for uefi shell..")
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        time.sleep(self.WAIT_TIME_OUT)
        # To check the SUT connected with DTPM/FTPM
        dtpm_access_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            self.get_memory_command(
                self.tpm_consts.DTPM_MM_DID_VID, self.ACCESS_WIDTH_FOUR, True, self.BIT_VAL_ZERO))
        dtpm_ret_flag = self.validate_memory_flag(
            self.tpm_consts.DTPM_MM_VID_EXP_VAL,
            dtpm_access_val,
            self.TPM_DID_VID)

        if dtpm_ret_flag:
            return self.verify_dtpm_uefi_mm_registry()
        else:
            ftpm_access_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(
                self.get_memory_command(
                    self.tpm_consts.FTPM_MM_DID_VID, self.ACCESS_WIDTH_FOUR, True, self.BIT_VAL_ZERO))
            ftpm_ret_flag = self.validate_memory_flag(self.tpm_consts.FTPM_MM_DID_VID_EXP_VAL, ftpm_access_val,
                                                      self.TPM_DID_VID)
            if ftpm_ret_flag:
                return self.verify_ftpm_uefi_mm_registry()
            else:
                return False

    def cleanup(self, return_status):  # type: (bool) -> None
        if self.itp_xml_cli_util is None:
            self.itp_xml_cli_util = ItpXmlCli(self._log, self._cfg)
        self.itp_xml_cli_util.set_boot_order(self.previous_boot_oder)
        self.perform_graceful_g3()
        super(dtpmuefiregistercommands, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if dtpmuefiregistercommands.main() else Framework.TEST_RESULT_FAIL)
