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

import os
import re
import sys

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.cbnt_constants import LinuxOsTypes
from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.virtualization.tests.dsa.dsa_common import DsaBaseTest


class SprIaxDMATesting(DsaBaseTest):
    """
    Phoenix ID : 16014809767-PI_SPR_IAX_Dma_Test_L

    This Test case is to Test the IAX DMA the Linux SUT
    """
    TEST_CASE_ID = ["16014809767", "PI_SPR_IAX_Dma_Test_L"]
    BIOS_CONFIG_FILE = "../vtd_bios_config.cfg"
    IAX_DMA_MODE_SCRIPT = "./setup_iax_DMA_mode.sh"
    EXEC_DMA_TEST_SCRIPT = "./Setup_Randomize_IAX_Conf.sh -i 100 -j 2"
    EXEC_DISABLE_WQ = "./Setup_Randomize_IAX_Conf.sh -d"
    TEST_CASE_CONTENT_PATH = "/root/pv-dsa-iax-bkc-tests/test_case_content"
    SPR_ACC_PATH = "/root/pv-dsa-iax-bkc-tests/spr-accelerators-random-config-and-test"
    STEP_DATA_DICT = {1: {'step_details': 'Enable Intel VT for Directed I/O (VT-d), Interrupt Remapping, PCIe ENQCMD '
                                          '/ENQCMDS, VMX Bios and reboot',
                          'expected_results': 'Verify the enabled BIOS'},
                      2: {'step_details': 'Install the dependency packages',
                          'expected_results': 'Installing the packages'},
                      3: {'step_details': 'download the git repo',
                          'expected_results': 'downloaded git repo successfully'},
                      4: {'step_details': 'Enable 2wq’s per device in kernel mode',
                          'expected_results': 'Enabled wqs successfully'},
                      5: {'step_details': 'Execute IAX DMA test with 2channels &100 iterations',
                          'expected_results': 'Executed IAX DMA Test successfully '},
                      6: {'step_details': 'Disable all wqs',
                          'expected_results': 'successfully disabled wqs'},
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of SprIaxDMATesting

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self._log = test_log
        self.dsa_bios_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(SprIaxDMATesting, self).__init__(test_log, arguments, cfg_opts, self.dsa_bios_enable)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self.update_git_proxy()
        if self.os.os_subtype.upper() != LinuxOsTypes.CENTOS:  # check if the Linux sub type is CentOS
            raise content_exceptions.TestFail("DSA DMA Testing not supported in the OS Type : {}".format(
                self.os.os_subtype))

    def prepare(self):
        # type: () -> None
        """
        preparing the setup by enabling VTd, Interrupt remapping, VMX, PCIe ENQCMD /ENQCMDS  and verify all kobs are
        enabled successfully
        """
        self._test_content_logger.start_step_logger(1)
        super(SprIaxDMATesting, self).prepare()
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This function execute
        1. Install dependency packages
        2. clone git repo
        3. Enable 2wq’s per device in kernel mode
        4. Execute DMA test with 2channels &100 iterations
        5. Disable all the wq's
        :raise: raise content exceptions
        :return: True if test case pass else fail
        """
        self._test_content_logger.start_step_logger(2)
        # Enabling the Intel iommu in kernel
        if not self.enable_intel_iommu_by_kernel():
            raise content_exceptions.TestFail("Unable to enable Intel IOMMU by kernel")
        # Installing the dependency packages
        self._log.info("Installing dependency package for CentOS: {}".format(self.INSTALL_DEPENDENCY_PACKAGE))
        for package in self.INSTALL_DEPENDENCY_PACKAGE:
            self._install_collateral.yum_install(package)
        self._test_content_logger.end_step_logger(2, return_val=True)
        # Cloning git repo
        self._test_content_logger.start_step_logger(3)
        self.clone_git_repo()
        self._test_content_logger.end_step_logger(3, return_val=True)

        # Enable 2wq’s per device in kernel mode
        self._test_content_logger.start_step_logger(4)
        result = self.execute_shell_script(self.IAX_DMA_MODE_SCRIPT, self.TEST_CASE_CONTENT_PATH)
        num_devices_enabled = len(re.findall(self.REGEX_VERIFY_ENABLE, result))
        self._log.debug("number of devices enabled {}".format(num_devices_enabled))
        if self.DSA_DEVICE_COUNT != num_devices_enabled:
            raise content_exceptions.TestFail("Failed to enable devices")
        self._test_content_logger.end_step_logger(4, return_val=True)

        # Execute IAX DMA test with 2channels &100 iterations
        self._test_content_logger.start_step_logger(5)
        result = self.execute_shell_script(self.EXEC_DMA_TEST_SCRIPT, self.SPR_ACC_PATH)
        total_threads = int(re.findall(self.REGEX_TOT_THREADS, result)[0])
        total_passed = int(re.findall(self.REGEX_THREADS_PASSED, result)[0])
        self._log.debug("Total number of Threads : {} Total Threads passed : {}".format(total_threads, total_passed))
        if total_threads != total_passed:
            raise content_exceptions.TestFail("DMA Test failed. Mismatch between Total Threads {} vs Threads passed"
                                              " {}".format(total_threads, total_passed))

        self._test_content_logger.end_step_logger(5, return_val=True)

        # Disable all the wq's
        self._test_content_logger.start_step_logger(6)
        result = self.execute_shell_script(self.EXEC_DISABLE_WQ, self.SPR_ACC_PATH)
        num_devices_disabled = len(re.findall(self.REGEX_VERIFY_DISABLE, result))
        self._log.debug("number of devices disabled {}".format(num_devices_disabled))
        if self.DSA_DEVICE_COUNT != num_devices_disabled:
            raise content_exceptions.TestFail("Failed to disable devices")
        self._test_content_logger.end_step_logger(6, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SprIaxDMATesting.main() else Framework.TEST_RESULT_FAIL)
