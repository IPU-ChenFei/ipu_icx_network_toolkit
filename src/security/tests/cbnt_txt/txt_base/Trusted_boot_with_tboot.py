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
from pathlib import Path
from dtaf_core.lib.dtaf_constants import Framework
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest
from src.lib.common_content_lib import CommonContentLib
from src.lib.test_content_logger import TestContentLogger
from src.lib import content_exceptions

local_path: Path = Path(__file__).parent.resolve()

class TrustedBootWithTboot(TxtBaseTest):
    """
       Glasgow ID : G58199.10 Trusted_Boot_with_tboot

       This Test case is used to get the pci/cpu/mem information before Tboot and after Tboot.
       The value of pci/cpu/mem are compared individually before Tboot and after Tboot and value should not change.
       pre-requisites:
       1.Ensure that the system is in sync with the latest BKC.
       2.Ensure that the platform has a TPM provisioned with ANY policy installed and active.
       3.Ensure that you have a Linux OS image or hard drive with Tboot installed
           and active
    """
    TEST_CASE_ID = ["G58199.10", "Trusted_Boot_with_tboot"]
    BIOS_CONFIG_FILE = Path.joinpath(local_path, "security_txt_bios_knobs_enable.cfg")
    PCI_CMD = "lspci"
    CPU_CMD = "lscpu"
    MEM_CMD = "lsmem"
    STEP_DATA_DICT = {1: {'step_details': 'Get result of lsmem/lscpu/lspci in normal boot',
                          'expected_results': 'lsmem/lscpu/lspci command output are logged successfully'},
                      2: {'step_details': 'Enable the Bios knobs for TXT',
                          'expected_results': 'All TXT knobs are enabled properly'},
                      3: {'step_details': 'Verify sut boot to trusted boot',
                          'expected_results': 'SUT booted trusted successfully'},
                      4: {'step_details': 'Get result of lsmem/lscpu/lspci in Trusted boot and compare with '
                                          'previous result',
                          'expected_results': 'Pre-tboot and post tboot lsmem/lscpu/lspci result are same'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of TrustedBootWithTboot

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(TrustedBootWithTboot, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._common_obj = CommonContentLib(self._log, self._os, cfg_opts)
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
        2. Load BIOS defaults settings.
        3. Sets the bios knobs according to configuration file and verifies if bios knobs sets successfully.
        """
        # get pre Tboot lsmem, lscpu and lspci data
        self.tboot_installation()
        self._test_content_logger.start_step_logger(1)
        self.pre_tboot_mem = self._common_obj.execute_sut_cmd(self.MEM_CMD, "details of mem", self._command_timeout)
        self._log.debug("Details of lsmem pre-tboot {}".format(self.pre_tboot_mem))
        self.pre_tboot_cpu = self._common_obj.execute_sut_cmd(self.CPU_CMD, "details of cpu", self._command_timeout)
        self._log.debug("Details of lscpu pre-tboot {}".format(self.pre_tboot_cpu))
        self.pre_tboot_pci = self._common_obj.execute_sut_cmd(self.PCI_CMD, "details of pci", self._command_timeout)
        self._log.debug("Details of lspci pre-tboot {}".format(self.pre_tboot_pci))
        self._test_content_logger.end_step_logger(1, return_val=True)
        self._test_content_logger.start_step_logger(2)
        self.enable_and_verify_bios_knob()  # enable and verify bios knobs
        self.tboot_index = self.get_tboot_boot_position()  # Get the Tboot_index from grub menu entry
        self.set_default_boot_entry(self.tboot_index)  # Set Tboot as default boot
        self.perform_graceful_g3()
        self._test_content_logger.end_step_logger(2, return_val=True)

    def execute(self):
        """
        This function is used to check SUT boot with Tboot and compare results of lsmem, lscpu and lspci after Tboot.

        :return: True if Test case pass
        :raise: content exception if the lsmem, lscpu or lspci comparision fails
        """
        # check if trusted boot
        self._test_content_logger.start_step_logger(3)
        self.verify_sut_booted_in_tboot_mode(self.tboot_index)  # verify if the system booted in Trusted mode.
        if not self.verify_trusted_boot():  # verify the sut boot with trusted env
            raise content_exceptions.TestFail("SUT did not boot to Trusted environment")
        self._log.info("SUT Booted to Trusted environment Successfully")

        self._test_content_logger.end_step_logger(3, return_val=True)
        # get post Tboot lsmem, lscpu and lspci data
        self._test_content_logger.start_step_logger(4)
        self.post_tboot_mem = self._common_obj.execute_sut_cmd(self.MEM_CMD, "details of mem", self._command_timeout)
        self._log.debug("Details of lsmem post-tboot {}".format(self.post_tboot_mem))
        self.post_tboot_cpu = self._common_obj.execute_sut_cmd(self.CPU_CMD, "details of cpu", self._command_timeout)
        self._log.debug("Details of lscpu post-tboot {}".format(self.post_tboot_cpu))
        self.post_tboot_pci = self._common_obj.execute_sut_cmd(self.PCI_CMD, "details of pci", self._command_timeout)
        self._log.debug("Details of lspci post-tboot {}".format(self.post_tboot_pci))
        # Compare results of lsmem, lscpu and lspci before and after Tboot
        if not self.compare_mem_cpu_pci_data(self.pre_tboot_pci, self.post_tboot_pci, self.pre_tboot_cpu,
                                             self.post_tboot_cpu, self.pre_tboot_mem, self.post_tboot_mem):
            raise content_exceptions.TestFail("Comparison of lscpu/lsmem/lspci is not same before and after tboot")
        self._log.info("Comparison of lscpu/lsmem/lspci is not same for linux os and tboot os")
        self._test_content_logger.end_step_logger(4, return_val=True)
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        """DTAF cleanup"""
        self.set_default_boot_entry(self._DEFAULT_ENTRY)  # Set system to default normal os boot
        self.perform_graceful_g3()
        super(TrustedBootWithTboot, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TrustedBootWithTboot.main() else Framework.TEST_RESULT_FAIL)
