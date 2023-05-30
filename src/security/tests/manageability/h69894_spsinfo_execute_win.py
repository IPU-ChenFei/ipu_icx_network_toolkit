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
import os

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.test_content_logger import TestContentLogger
from src.lib.content_base_test_case import ContentBaseTestCase
from src.provider.spsinfo_provider import SpsinfoProvider
from src.lib import content_exceptions


class InstallSpsToolInfo(ContentBaseTestCase):
    """
    HPQC ID : "H69894"

    The purpose of this test case is to verify Spsinfo folder to be copy on Windows sut and
    execute Spsinfo command on SUT device collect the firmware version and verify
    with the configfile firm ware version.
    """
    TEST_CASE_ID = ["H69894"]
    step_data_dict = {1: {'step_details': 'Check spstool copied on sut based on os ',
                          'expected_results': 'copy spstool to sut collect folder path from sut'},
                      2: {'step_details': 'Execute  spsInfoWin64.exe on sut collect the firmware version ',
                          'expected_results': 'verify firmware version with content config file version'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of InstallSpsToolInfo

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(InstallSpsToolInfo, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self.sps_firmware_provider = SpsinfoProvider.factory(self._log, cfg_opts, self.os)  # type: SpsinfoProvider
        self.sps_tool_zip_file_path, self.sps_info_ver = self._common_content_configuration.get_sps_tool_info()
        self.sps_info_file_name = os.path.split(self.sps_tool_zip_file_path)[-1].strip()

    def prepare(self):
        # type: () -> None
        """
        preparing sut with default setting
        :return: None
        """
        super(InstallSpsToolInfo, self).prepare()

    def execute(self):
        """
        This method installs the Sps tool on sut and verify if it is installed properly.
        and also it verify the executed recovery firmware version number with the content configuration
        version.
        """
        self._test_content_logger.start_step_logger(1)
        self.sut_folder_path = self.sps_firmware_provider.copy_spstool_sut(self.sps_tool_zip_file_path,
                                                                           self.sps_info_file_name)
        self._test_content_logger.end_step_logger(1, return_val=True)
        self._test_content_logger.start_step_logger(2)
        actual_version = self.sps_firmware_provider.get_sps_version(self.sut_folder_path)
        if actual_version != self.sps_info_ver:
            raise content_exceptions.TestFail(" SPS Firmware version not matching, Actual Sps firmware version:{}, "
                                              "Expected Firmware version :{}".format(actual_version,
                                                                                     self.sps_info_ver))
        self._test_content_logger.end_step_logger(2, return_val=True)
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """Clean-up method called when a script ends"""
        if return_status:
            self._log.info(self._PASS_INFO)
        else:
            self._log.error(self._FAIL_INFO)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if InstallSpsToolInfo.main() else Framework.TEST_RESULT_FAIL)
