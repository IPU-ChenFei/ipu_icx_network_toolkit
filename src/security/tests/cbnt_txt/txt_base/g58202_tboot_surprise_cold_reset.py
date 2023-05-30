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
# treaty provisions0. No part of the Material may be used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or disclosed
# in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
##########################################################################

import sys
import time

from dtaf_core.lib.dtaf_constants import Framework

from src.security.tests.cbnt_txt.txt_common import TxtBaseTest
from src.lib.common_content_lib import CommonContentLib
from src.lib.test_content_logger import TestContentLogger


class TbootSurpriseColdReset(TxtBaseTest):
    """
    Glasgow ID : 58202
    This Test case execute AC power OFF/ON and Check SUT is in Trusted Boot
    pre-requisites:
    TXT should be enabled and boot trusted.
    """
    BIOS_CONFIG_FILE = "txt_base/security_txt_bios_knobs_enable.cfg"
    PCI_CMD = "lspci"
    CPU_CMD = "lscpu"
    MEM_CMD = "lsmem"
    TEST_CASE_ID = "G58202"

    step_data_dict = {1: {'step_details': 'Executing lsmem/lscpu/lspci command, enabling TXT BIOS Knobs'
                          'and Booting to tboot', 'expected_results': 'Verifying TXT BIOS Knobs and verifying'
                          'SUT entered to Tboot and comparing the lsmem/lscpu/lspci results'},
                      2: {'step_details': 'AC power OFF and ON', 'expected_results': 'SUT should boot'},
                      3: {'step_details': 'Verify to SUT is entered to TBOOT',
                          'expected_results': 'SUT should entered to TBOOT'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of TbootSurpriseColdReset

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(TbootSurpriseColdReset, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)
        self._common_obj = CommonContentLib(self._log, self._os)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._ac_power_off_wait_time = self._common_content_configuration.ac_power_off_wait_time()
        self.pre_tboot_pci = None
        self.pre_tboot_cpu = None
        self.pre_tboot_mem = None
        self.post_tboot_pci = None
        self.post_tboot_cpu = None
        self.post_tboot_mem = None
        self.tboot_index = None

    def prepare(self):
        # type: () -> None
        """
        1. Execute OS commands before the Tboot set.
        3. Pre-validate whether sut is configured with Tboot by get the Tboot index in OS boot order.
        4. Load BIOS defaults settings.
        5. Sets the bios knobs according to configuration file and verifies if bios knobs sets successfully.
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

    def execute(self):
        """
        This function is used to check SUT boot with Tboot and compare results of lsmem, lscpu and lspci after Tboot.
        After entered to Tboot, AC Power OFF for 20 seconds and AC Power ON check the SUT should be in Tboot

        :return: True if SUT in tboot Test case pass else fail
        """

        # check if trusted boot
        self.verify_sut_booted_in_tboot_mode(self.tboot_index)  # verify if the system booted in Trusted mode.
        self._os.reboot(self._reboot_timeout)
        if self.verify_trusted_boot():  # verify the sut boot with trusted env
            self._log.info("SUT Booted to Trusted environment Successfully")
        else:
            return False

        # get post Tboot lsmem, lscpu and lspci data
        self.post_tboot_mem = self._common_obj.execute_sut_cmd(
            self.MEM_CMD, "details of mem", self._command_timeout)
        self.post_tboot_cpu = self._common_obj.execute_sut_cmd(
            self.CPU_CMD, "details of cpu", self._command_timeout)
        self.post_tboot_pci = self._common_obj.execute_sut_cmd(
            self.PCI_CMD, "details of pci", self._command_timeout)

        # Compare results of lsmem, lscpu and lspci before and after Tboot
        ret_val = False
        if self.compare_mem_cpu_pci_data(
                self.pre_tboot_pci,
                self.post_tboot_pci,
                self.pre_tboot_cpu,
                self.post_tboot_cpu,
                self.pre_tboot_mem,
                self.post_tboot_mem):
            self._log.info("Comparison of lscpu/lsmem/lspci is same before and after tboot")
        else:
            self._log.info("Comparison of lscpu/lsmem/lspci is not same before and after tboot")
            return ret_val
        #  Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        # Surprise AC power OFF/ON
        self._log.info("Removing power from the SUT")
        self._ac_obj.ac_power_off()
        self._log.info("SUT AC Power OFF")
        time.sleep(self._ac_power_off_wait_time)
        self._ac_obj.ac_power_on()
        self._log.info(" AC Power ON")
        #  Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)
        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)
        self._os.wait_for_os(self._reboot_timeout)
        # check if SUT is in trusted boot
        self.verify_sut_booted_in_tboot_mode(self.tboot_index)  # verify if the system booted in Trusted mode.
        if self.verify_trusted_boot():  # verify the sut boot with trusted env
            self._log.info("SUT Booted to Trusted environment Successfully")
            ret_val = True
        else:
            if self.verify_trusted_boot(expect_ltreset=True):  # verify the sut boot with trusted environment
                self._log.info("SUT Booted to Trusted environment Successfully")
                ret_val = True
            else:
                self._log.error("SUT did not Boot into Trusted environment")
        #  Step logger end for Step 1
        self._test_content_logger.end_step_logger(3, ret_val)
        return ret_val


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TbootSurpriseColdReset.main() else Framework.TEST_RESULT_FAIL)
