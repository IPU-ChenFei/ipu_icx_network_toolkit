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

import src.lib.content_exceptions as content_exceptions
from src.power_management.lib.reset_base_test import ResetBaseTest
from src.storage.test.storage_common import StorageCommon
from src.lib.install_collateral import InstallCollateral


class SATARebootCycles(ResetBaseTest):
    """
    PHONEIX ID : 16013590666 - U.2 NVMe- Reboot cycling at OS

    This TestCase is Used to Verify MCE Logged Status by Performing Warm Reset Cycles and verifying the status of u.2
     NVME in Every Cycle.
    """
    TEST_CASE_ID = ["16013560988", "SATA-6 GBPS- Reboot cycling at OS- use mix of all SATASSD",
                    "16013587551", "SATA- OS reboot Os to OS(win)",
                    "16013589417", "SATA- OS reboot Os to OS(linux)"
                    "16015362946","EDSFF OS reboot OS to OS"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new PowerManagementRebootCycles object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(SATARebootCycles, self).__init__(test_log, arguments, cfg_opts)
        self._storage_common = StorageCommon(test_log, arguments, cfg_opts)
        self.install_collateral_obj = InstallCollateral(self._log, self.os, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        1. Copy mcelog.conf file to sut and reboot
        2. Clear All Os Logs before Starting the Test Case
        3. Reboot the SUT to apply the new bios settings.

        :return: None
        """
        self.install_collateral_obj.copy_smartctl_exe_file_to_sut()
        super(SATARebootCycles, self).prepare()

    def execute(self):
        """
        This Method is Used to verify status of MCE in Every Warm Reset of 10 Cycles'

        :return: True or False
        """
        for cycle_number in range(self._common_content_configuration.get_num_of_reboot_cycles()):
            before_reboot_device_list = self._storage_common.get_smartctl_drive_list()
            self.warm_reset()
            after_reboot_device_list = self._storage_common.get_smartctl_drive_list()
            if before_reboot_device_list != after_reboot_device_list:
                raise content_exceptions.TestFail("Before reboot and After reboot SATA device list is not same")
            self._log.info("Before reboot and after reboot SATA devices are same")
            if self._common_content_lib.check_if_mce_errors():
                log_error = "Machine Check errors are Logged in Warm Reset Cycle '{}'".format(cycle_number)
                self._log.error(log_error)
                raise content_exceptions.TestFail(log_error)
            self._log.info("No Machine Check Errors are Logged in Warm Reset Cycle '{}'".format(cycle_number))
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SATARebootCycles.main() else Framework.TEST_RESULT_FAIL)
