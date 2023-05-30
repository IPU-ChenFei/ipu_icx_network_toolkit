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

from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.security.tests.qat.qat_common import QatBaseTest


class QatStatusCheck(QatBaseTest):
    """
    HPQC ID : H79559
    This Test case execute command to check QAT Status
    """
    QAT_SERVICE_RESTART = "service qat_service restart"
    EXP_QAT_SERVICE_RESTART = "Restarting all devices"
    TEST_CASE_ID = ["H79559-PI_SPR_QAT_StatusCheck_L"]

    step_data_dict = {1: {'step_details': 'Check device installation status',
                          'expected_results': 'Device should show 1 QAT Acceleration device'},
                      2: {'step_details': 'if step1 fails restart the device', 'expected_results':
                          'Stop all devices and Start all devices'},
                      3: {'step_details': 'Check device installation status',
                          'expected_results': 'Device should show 1 QAT Acceleration device'},
                      4: {'step_details': 'Reboot and check device status',
                          'expected_results': 'Device should show 1 QAT Acceleration device'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of QatStatusCheck

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(QatStatusCheck, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        Pre-checks if the sut is alive or not.
        """
        super(QatStatusCheck, self).prepare()

    def execute(self):
        """
        This function check QAT device status on SUT

        :return: True if get the QAT device status test case pass else fail
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        self.install_qat_tool()
        try:
            if not self.qat_device_status():
                raise content_exceptions.TestFail("QAT does not support")
        except content_exceptions.TestError as ex:
            #  Step logger end for Step 1
            self._test_content_logger.end_step_logger(1, return_val=True)
            # Step logger start for Step 2
            self._test_content_logger.start_step_logger(2)
            self._log.info("QAT status check failed, restarting the QAT Service...")
            qat_service_restart_results = self._common_content_lib.execute_sut_cmd(self.QAT_SERVICE_RESTART,
                                                                                   "get qat status", self._command_timeout)
            self._log.debug("Restarting the QAT Service in the SUT {}".format(qat_service_restart_results))
            if self.EXP_QAT_SERVICE_RESTART not in qat_service_restart_results:
                raise content_exceptions.TestFail("Failed to Restart the QAT Services")
            #  Step logger end for Step 2
            self._test_content_logger.end_step_logger(2, return_val=True)
            # Step logger start for Step 3
            self._test_content_logger.start_step_logger(3)
            if not self.qat_device_status():
                raise content_exceptions.TestFail("QAT Tool does not supported in this system")
            #  Step logger end for Step 3
            self._test_content_logger.end_step_logger(3, return_val=True)
        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)
        # Performs graceful shutdown
        self.perform_graceful_g3()
        if not self.qat_device_status():
            raise content_exceptions.TestFail("QAT Tool does not supported in this system")
        self._test_content_logger.end_step_logger(4, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if QatStatusCheck.main() else Framework.TEST_RESULT_FAIL)
