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

from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral
from src.provider.stressapp_provider import StressAppTestProvider
from src.storage.lib.storage_common import StorageCommon
from src.lib.test_content_logger import TestContentLogger


class U2NvmeStabilityAndStressBurninInWindows(ContentBaseTestCase):
    """
    Phoenix ID : 1509699166-U.2 NVME-Stability and Stress-Burnin in windows
               : 16013566695-M.2 NVME-Stability and Stress-Burnin in windows
    This Test case install BurnInTest tool and execute burnintest to stress in the u.2 device/M.2 device
    """
    TEST_CASE_ID = ["1509699166", "U2_Nvme_Stability_and_Stress_Burnin_in_Windows",
                    "16013566695", "M2_NVME_Stability_and_Stress_Burnin_in_Windows"]
    BURNING_WORKLOAD_CONFIG_FILE = "test_config_nvme_disk_test.bitcfg"
    STEP_DATA_DICT = {
        1: {'step_details': 'Boot to OS',
            'expected_results': 'System booted to OS'},
        2: {'step_details': 'Copy the burnin tool and install the tool on OS.',
            'expected_results': 'The tool should get installed on the OS.'},
        3: {'step_details': 'Mount the U.2/M.2 nvme drive .',
            'expected_results': 'The U.2/M.2 nvme should be mounted successfully.'},
        4: {'step_details': 'Start the burnin tool.',
            'expected_results': 'The tool should run successfully on the OS.'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of StabilityBurnInTest

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(U2NvmeStabilityAndStressBurninInWindows, self).__init__(test_log, arguments, cfg_opts)
        self.burnin_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                               self.BURNING_WORKLOAD_CONFIG_FILE)
        self.stress_app_provider = StressAppTestProvider.factory(test_log, os_obj=self.os, cfg_opts=cfg_opts)
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)
        self.storage_common_lib = StorageCommon(self._log, cfg_opts)
        # get the burnin tool run time in minutes from content_configuration.xml file
        self.burnin_execution_time = self._common_content_configuration.get_burnin_test_runtime()
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    def prepare(self):
        # type: () -> None
        """2
        This function load bios defaults to SUT
        """
        super(U2NvmeStabilityAndStressBurninInWindows, self).prepare()

    def execute(self):
        """
        This function install burnin tool, format the u.2 drive and execute burnin tool on the u.2 disk

        :return: True if test completed successfully, False otherwise.
        """
        # start of step 1
        self._test_content_logger.start_step_logger(1)
        self.os.is_alive()
        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, True)

        # start of step 2
        self._test_content_logger.start_step_logger(2)
        # install burnin tool
        bit_location = self.collateral_installer.install_burnintest()
        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, True)

        # start of step 3
        self._test_content_logger.start_step_logger(3)
        # formatting the u.2 nvme drive
        self.storage_common_lib.format_drive_win("nvme")
        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, True)

        # start of step 4
        self._test_content_logger.start_step_logger(4)
        self.stress_app_provider.execute_burnin_test(self.log_dir, self.burnin_execution_time, bit_location,
                                                     self.burnin_config_file)
        # Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if U2NvmeStabilityAndStressBurninInWindows.main() else Framework.TEST_RESULT_FAIL)
