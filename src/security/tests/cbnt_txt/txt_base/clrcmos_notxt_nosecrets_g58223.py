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
from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.physical_control import PhysicalControlProvider

from src.security.tests.cbnt_txt.txt_common import TxtBaseTest
from src.lib.common_content_lib import CommonContentLib
from src.lib.test_content_logger import TestContentLogger


class ClrCMOSNoTXTNoSecrets(TxtBaseTest):
    """
    Glasgow ID : 58223
    Boot trusted, clear secrets flag, verifies secrets are cleared from memory, and does a surprise AC off.
    CMOS clear and Remove battery for at least 1 minute and Wait till system comes up,
    sets TXT enabled, and then verifies that the SUT boots trusted.
    pre-requisites:
    1.Ensure that the system is in sync with the BKC.
    2.Ensure that you have a Linux OS image or hard drive with tboot installed.
    3.Ensure that the platform has a TPM provisioned with an ANY policy installed
        and active
    """
    BIOS_CONFIG_FILE = "txt_base/security_txt_bios_knobs_enable.cfg"
    PCI_CMD = "lspci"
    CPU_CMD = "lscpu"
    MEM_CMD = "lsmem"
    TEST_CASE_ID = "G58223"
    BYTE_SIZE_TO_WRITE = 8
    VALUE_TO_WRITE = 1
    BYTE_SIZE_TO_READ = 4
    THREAD_INDEX = 0
    EXPECTED_E2STS_VAL = 0x0
    CMOS_CLEAR_INP = 1
    EXPECTED_USER_INP = "1"

    step_data_dict = {1: {'step_details': 'Executing lsmem/lscpu/lspci command, enabling TXT BIOS Knobs'
                                          'and Booting to tboot',
                          'expected_results': 'Verifying TXT BIOS Knobs and verifying'
                                              'SUT entered to Tboot and comparing the lsmem/lscpu/lspci results'},
                      2: {'step_details': 'verify that the MLE is launched and the secrets bit has been set',
                          'expected_results': 'MLE launch successfully and the secrets bit has been set'},
                      3: {'step_details': 'Clear secret flag',
                          'expected_results': 'Secret flag is cleared successfully'},
                      4: {'step_details': 'AC power off, Physically remove battery/clear CMOS  and AC power on',
                          'expected_results': 'AC power off successfully, Physically battery removed and '
                                              'cmos clear done and AC power on successfully'},
                      5: {'step_details': 'Executing lsmem/lscpu/lspci command, enabling TXT BIOS Knobs'
                                          'and Booting to tboot',
                          'expected_results': 'Verifying TXT BIOS Knobs and verifying'
                                              'SUT entered to Tboot and comparing the lsmem/lscpu/lspci results'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(ClrCMOSNoTXTNoSecrets, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self.tboot_index = None
        self._common_obj = CommonContentLib(self._log, self._os)
        self.pre_tboot_pci = None
        self.pre_tboot_cpu = None
        self.pre_tboot_mem = None
        self.post_tboot_pci = None
        self.post_tboot_cpu = None
        self.post_tboot_mem = None
        self.tboot_index = None
        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac = ProviderFactory.create(ac_cfg, test_log)  # type: AcPowerControlProvider
        phy_cfg = cfg_opts.find(PhysicalControlProvider.DEFAULT_CONFIG_PATH)
        self._phy = ProviderFactory.create(phy_cfg, test_log)  # type: PhysicalControlProvider
        self._ac_power_off_wait_time = self._common_content_configuration.ac_power_off_wait_time()

    def prepare(self):
        # type: () -> None
        """
        Pre-validating whether sut is configured with tboot by getting the tboot index in OS boot order.
        Loading BIOS defaults settings.
        Sets the bios knobs according to configuration file and verifies if bios knobs sets successfully.
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        # get pre Tboot lsmem, lscpu and lspci data
        self.pre_tboot_mem = self._common_obj.execute_sut_cmd(
            self.MEM_CMD, "details of mem", self._command_timeout)
        self.pre_tboot_cpu = self._common_obj.execute_sut_cmd(
            self.CPU_CMD, "details of cpu", self._command_timeout)
        self.pre_tboot_pci = self._common_obj.execute_sut_cmd(
            self.PCI_CMD, "details of pci", self._command_timeout)

        self.tboot_index = self.get_tboot_boot_position()  # Get the Tboot_index from grub menu entry
        self.set_default_boot_entry(self.tboot_index)  # Set Tboot as default boot
        self._bios_util.load_bios_defaults()  # To set Bios knobs to default.
        self._bios_util.set_bios_knob()  # To set the bios knob
        self._os.reboot(self._reboot_timeout)
        self._bios_util.verify_bios_knob()  # To verify the Bios knob value set
        self.verify_sut_booted_in_tboot_mode(self.tboot_index)  # verify if grub is set to tboot

    def ungraceful_g3(self):
        """
        This function performs the ungraceful reset and also performs the clear CMOS/Battery removal operation

        :raise: RuntimeError: If Fail to perform AC power off
        :raise: RuntimeError: If Fail to perform clear CMOS
        :return: None
        """

        if self._ac.ac_power_off(self._ac_power_off_wait_time):  # To perform a Ungraceful Shutdown
            self._log.info("AC power is turned OFF")
        else:
            self._log.error("AC power is not turned OFF")
            raise RuntimeError("AC power is not turned OFF")
        if self._phy.set_clear_cmos(self._ac_power_off_wait_time):  # Clears CMOS value
            self._log.info("Clear CMOS is done successfully")
        else:
            self._log.error("Clear CMOS is not done successfully")
            raise RuntimeError("Clear CMOS is not done successfully")
        self._log.info("Physically Remove the battery for at least 1 minute and press key '1' to continue if "
                       "CMOS battery has been removed")
        input_value = sys.stdin.read(self.CMOS_CLEAR_INP)  # Requires 1 as a input from the user if battery is removed
        if input_value == self.EXPECTED_USER_INP:
            self._log.info("CMOS battery is removed for 1 minute and placed back successfully, Power on the system")
        else:
            raise RuntimeError("Did not receive any input from user...")
        if self._ac.ac_power_on(self._ac_power_off_wait_time):
            self._log.info("AC power is turned ON")
        else:
            self._log.error("AC power is not turned ON")
            raise RuntimeError("AC power is not turned ON")

    def mle_launch_and_secret_bit_is_set(self):
        """
        This function checks if MLE is launch successfully and secret bit is set properly.

        :raise: RuntimeError if MLE is not launch successfully or secret bit is not set
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
        read_e2sts = self._sdp.mem_read(reg_lt_e2sts_add, self.BYTE_SIZE_TO_READ)
        self._log.debug("Read back value for register '{}' is : '{}'"
                        .format(self.txt_consts.LT_E2STS, hex(read_e2sts)))
        self._sdp.go()
        if mle_res and (hex(read_e2sts)) == hex(expected_lt_e2sts_val):
            self._log.info("MLE launched successfully and secret bit is set")
        else:
            self._log.info("MLE did not launched successfully or secret bit is not set")
            raise RuntimeError("MLE did not launched successfully or secret bit is not set")

    def execute(self):
        """
        This function is used to check SUT should be boot in trusted environment
        :return: True if Test case pass else fail
        """
        ret_val = False
        if self.verify_trusted_boot():  # verify the sut boot with trusted env
            self._log.info("SUT Booted to Trusted environment Successfully")
        else:
            self._log.info("SUT did not Booted to Trusted environment...")
            return False

        # get post Tboot lsmem, lscpu and lspci data
        self.post_tboot_mem = self._common_obj.execute_sut_cmd(self.MEM_CMD, "details of mem", self._command_timeout)
        self.post_tboot_cpu = self._common_obj.execute_sut_cmd(self.CPU_CMD, "details of cpu", self._command_timeout)
        self.post_tboot_pci = self._common_obj.execute_sut_cmd(self.PCI_CMD, "details of pci", self._command_timeout)

        # Compare results of lsmem, lscpu and lspci before and after Tboot
        if self.compare_mem_cpu_pci_data(self.pre_tboot_pci, self.post_tboot_pci, self.pre_tboot_cpu,
                                         self.post_tboot_cpu, self.pre_tboot_mem, self.post_tboot_mem):
            self._log.info("Comparison of lscpu/lsmem/lspci is same before and after tboot")
        else:
            self._log.info("Comparison of lscpu/lsmem/lspci is not same before and after tboot")
            return ret_val
        #  Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        self.mle_launch_and_secret_bit_is_set()
        #  Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)
        # Clear secrets flag
        address_secret_flag = hex(self.txt_consts.TXT_REG_PRIVATE_BASE +
                                  self.txt_consts.TXT_REG_OFFSETS["SECRETS_PRIV"]).rstrip('L') + 'p'
        lt_e2sts_mem_address = hex(self.txt_consts.TXT_REG_PUBLIC_BASE +
                                   self.txt_consts.TXT_REG_OFFSETS["LT_E2STS"]).rstrip('L') + 'p'
        self._log.debug("Halting CPU.")
        self._sdp.halt()
        self._log.info("Writing to memory location '{}' to clear the secret flag".format(address_secret_flag))
        self._sdp.itp.threads[self.THREAD_INDEX].mem(address_secret_flag, self.BYTE_SIZE_TO_WRITE, self.VALUE_TO_WRITE)

        # Re-read E2STS to confirm secrets bit was cleared
        read_e2sts = self._sdp.mem_read(lt_e2sts_mem_address, self.BYTE_SIZE_TO_READ)
        self._log.info("Read back value at address '{}' is: {}".format(lt_e2sts_mem_address, hex(read_e2sts)))
        self._sdp.go()
        if (hex(read_e2sts)) == hex(self.EXPECTED_E2STS_VAL):
            self._log.info("secret bit is cleared")
        else:
            self._log.error("secret bit is not cleared")
            raise RuntimeError("secret bit is not cleared")
        #  Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)
        self.ungraceful_g3()
        #  Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=True)

        # Step logger start for Step 5
        self._test_content_logger.start_step_logger(5)
        self._os.wait_for_os(self._reboot_timeout)  # Waits until the system comes up
        # get pre Tboot lsmem, lscpu and lspci data
        self.pre_tboot_mem = self._common_obj.execute_sut_cmd(
            self.MEM_CMD, "details of mem", self._command_timeout)
        self.pre_tboot_cpu = self._common_obj.execute_sut_cmd(
            self.CPU_CMD, "details of cpu", self._command_timeout)
        self.pre_tboot_pci = self._common_obj.execute_sut_cmd(
            self.PCI_CMD, "details of pci", self._command_timeout)

        self.tboot_index = self.get_tboot_boot_position()  # Get the Tboot_index from grub menu entry
        self.set_default_boot_entry(self.tboot_index)  # Set Tboot as default boot
        self._bios_util.load_bios_defaults()  # To set Bios knobs to default.
        self._bios_util.set_bios_knob()  # To set the bios knob
        self._os.reboot(self._reboot_timeout)
        self._bios_util.verify_bios_knob()  # To verify the Bios knob value set
        self.verify_sut_booted_in_tboot_mode(self.tboot_index)  # verify if grub is set to tboot
        if self.verify_trusted_boot():  # verify the sut boot with trusted environment
            self._log.info("SUT Booted to Trusted environment Successfully")
        else:
            if self.verify_trusted_boot(expect_ltreset=True):  # verify the sut boot with trusted environment
                self._log.info("SUT Booted to Trusted environment Successfully")
            else:
                self._log.error("SUT did not Boot into Trusted environment")
                return False

        # get post Tboot lsmem, lscpu and lspci data
        self.post_tboot_mem = self._common_obj.execute_sut_cmd(self.MEM_CMD, "details of mem", self._command_timeout)
        self.post_tboot_cpu = self._common_obj.execute_sut_cmd(self.CPU_CMD, "details of cpu", self._command_timeout)
        self.post_tboot_pci = self._common_obj.execute_sut_cmd(self.PCI_CMD, "details of pci", self._command_timeout)

        # Compare results of lsmem, lscpu and lspci before and after Tboot
        if self.compare_mem_cpu_pci_data(self.pre_tboot_pci, self.post_tboot_pci, self.pre_tboot_cpu,
                                         self.post_tboot_cpu, self.pre_tboot_mem, self.post_tboot_mem):
            self._log.info("Comparison of lscpu/lsmem/lspci is same before and after tboot")
            ret_val = True
        else:
            self._log.info("Comparison of lscpu/lsmem/lspci is not same before and after tboot")
        #  Step logger end for Step 5
        self._test_content_logger.end_step_logger(5, return_val=ret_val)

        return ret_val

    def cleanup(self, return_status):
        # type: (bool) -> None
        """Clean-up method called when a script ends"""
        # stopping serial driver
        self._uefi_obj.serial._release()
        super(ClrCMOSNoTXTNoSecrets, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ClrCMOSNoTXTNoSecrets.main() else Framework.TEST_RESULT_FAIL)
