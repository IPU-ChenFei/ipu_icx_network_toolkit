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
import sys

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.cbnt_constants import LinuxOsTypes
from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.virtualization.tests.dsa.dsa_common import DsaBaseTest


class DsaLibInstall(DsaBaseTest):
    """
    HPQC ID : H87919-PI_DSA_Lib_install_L

    This Test case DSA Library install in the Linux SUT
    """
    TEST_CASE_ID = ["H87919", "PI_DSA_Lib_install_L"]
    BIOS_CONFIG_FILE = "../vtd_bios_config.cfg"
    STEP_DATA_DICT = {1: {'step_details': 'Enable Intel VT for Directed I/O (VT-d), Interrupt Remapping, PCIe ENQCMD '
                                          '/ENQCMDS, VMX Bios and reboot',
                          'expected_results': 'Verify the enabled BIOS'},
                      2: {'step_details': 'Install the dependency packages', 'expected_results': 'Installing the '
                                                                                                 'packages'},
                      3: {'step_details': 'Determine the devices state', 'expected_results': 'Fail if not found the '
                                                                                             'devices'},
                      4: {'step_details': 'Driver basic check', 'expected_results': 'Fail if any error found'},
                      5: {'step_details': 'DCheck the driver file system', 'expected_results': 'Verify DSA devices '
                          'should be dsa0 to dsa7 devices should be available'},
                      6: {'step_details': 'Verify accel config tool', 'expected_results': 'Run unit test to verify '
                          'libaccfg APIs'},
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of DsaLibInstall

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.dsa_bios_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(DsaLibInstall, self).__init__(test_log, arguments, cfg_opts, self.dsa_bios_enable)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        if self.os.os_subtype.upper() != LinuxOsTypes.CENTOS:  # check if the Linux sub type is CentOS
            raise content_exceptions.TestFail("DSA Lib Install is not supported in the OS Type : {}".format(
                self.os.os_subtype))

    def prepare(self):
        # type: () -> None
        """
        preparing the setup by enabling VTd, Interrupt remapping, VMX, PCIe ENQCMD /ENQCMDS  and verify all kobs are
        enabled successfully
        """
        self._test_content_logger.start_step_logger(1)
        super(DsaLibInstall, self).prepare()
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This function execute
        1. Install dependency packages
        2. Determine the dsa device state
        3. Dsa driver basic check
        4. Verify the Dsa driver files
        5. Install the dsa accel config tool

        :raise: raise content exceptions if kernal file is not updated
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
        self._test_content_logger.start_step_logger(3)
        # lsmod grep command for idxd device
        self.check_idxd_device()
        # Determine the dsa device state
        self.determine_device_state()
        self._test_content_logger.end_step_logger(3, return_val=True)
        self._test_content_logger.start_step_logger(4)
        # lsmod grep command for idxd device
        self.check_idxd_device()
        # DSA device basic check
        self.driver_basic_check()
        self._test_content_logger.end_step_logger(4, return_val=True)
        self._test_content_logger.start_step_logger(5)
        # Check DSA devices
        self.verify_dsa_driver_directory()
        self._test_content_logger.end_step_logger(5, return_val=True)
        self._test_content_logger.start_step_logger(6)
        # Install accel config tool
        self._install_collateral.install_verify_accel_config()
        self._test_content_logger.end_step_logger(6, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if DsaLibInstall.main() else Framework.TEST_RESULT_FAIL)
