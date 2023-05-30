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

from src.lib.test_content_logger import TestContentLogger
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral
from src.provider.vss_provider import VssProvider


class MemoryDdrIwvssWindows(ContentBaseTestCase):
    """
    HPQC ID: 102741-PI_Memory_DDR5_IWVSS_W, Pheonix ID : 18016909599

    Running iwvss tool for memory stress for 6 hours.
    """

    TEST_CASE_ID = ["H102741", "PI_Memory_DDR5_IWVSS_W"]
    PROCESS_NAME = "mem64.exe"
    LOG_NAME = "iwvss_log.log"

    step_data_dict = {1: {'step_details': 'To clear OS logs and load default bios settings ...',
                          'expected_results': 'Cleared OS logs and default bios settings done ...'},
                      2: {'step_details': 'Select package in IWVSS and run memory workload for 6 hrs',
                          'expected_results': 'No errors should be reported'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance MemoryDdrIwvssWindows

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None 
        """
        # calling base class init
        super(MemoryDdrIwvssWindows, self).__init__(test_log, arguments, cfg_opts)

        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

        self._vss_provider_obj = VssProvider.factory(self._log, cfg_opts=cfg_opts, os_obj=self.os)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        To clear OS logs and load default bios settings.

        :return: None
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        super(MemoryDdrIwvssWindows, self).prepare()

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        1.Select package in IWVSS and run memory workload for 6 hrs

        :return: True, if the test case is successful.
        """

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        # TODO : For iwvss 2.9.2 we are using this work around
        self._install_collateral.install_vc_redist()

        self._log.info("Executing the iwvss ...")
        # To copy the package and Execute iwvss configuration for stress
        self._vss_provider_obj.execute_vss_memory_test_package(flow_tree="Mem")

        # wait for the iwvss to complete
        self._vss_provider_obj.wait_for_vss_to_complete(self.PROCESS_NAME)

        # Parsing iwvss log
        return_value = self._vss_provider_obj.verify_vss_logs(self.LOG_NAME)

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=return_value)

        return return_value

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(MemoryDdrIwvssWindows, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MemoryDdrIwvssWindows.main() else Framework.TEST_RESULT_FAIL)
