
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


class QatUninstall(QatBaseTest):
    """
    HPQC ID : H79561
    This Test case execute qat status command, qat kernel module list and uninstall the QAT Tool
    """
    TEST_CASE_ID = ["H79561-PI_SPR_QAT_Uninstall_L"]

    step_data_dict = {1: {'step_details': 'Check device installation status',
                          'expected_results': 'Device should show 1 QAT Acceleratoin device'},
                      2: {'step_details': 'Finding the directory path of QAT',
                          'expected_results': 'QAT Tool directory path'},
                      3: {'step_details': 'Check the qat kernal modules using lsmod | grep "qat\|usdm" installation'
                                          'status', 'expected_results': 'Sut should show qat kernal modules'},
                      4: {'step_details': 'Uninstall the QAT tool',
                          'expected_results': 'Successfully uninstalled the QAT from the SUT'},
                      5: {'step_details': 'Check the qat kernal modules using lsmod | grep "qat\|usdm" after '
                                          'uninstalled the qat tool', 'expected_results': 'Sut should show qat kernal '
                                                                                          'modules without usdm_drv'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of QatUninstall

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(QatUninstall, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        Pre-validating if the sut is booted to RHEL Linux OS.
        """
        super(QatUninstall, self).prepare()

    def execute(self):
        """
        This function check qat device status and kernel modules.
        Uninstall the qat tool and check again the kernel modules

        :return: True if Test case pass else fail.
        :raise: Test case fail exception.
        """
        qat_dir_path = None
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        self.install_qat_tool()
        if not self.qat_device_status():
            raise content_exceptions.TestFail("QAT Tool does not supported in this system")
        #  Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        qat_dir_path = self.get_qat_dir()
        #  Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)
        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)
        self.check_lsmod_for_qat_installation()
        #  Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)
        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)
        self.uninstall_qat(qat_dir_path)
        #  Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=True)
        # Step logger start for Step 5
        self._test_content_logger.start_step_logger(5)
        self.check_lsmod_for_qat_uninstallation()
        #  Step logger end for Step 5
        self._test_content_logger.end_step_logger(5, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if QatUninstall.main() else Framework.TEST_RESULT_FAIL)
