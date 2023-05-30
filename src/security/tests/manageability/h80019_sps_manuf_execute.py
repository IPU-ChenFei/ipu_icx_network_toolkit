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
import shutil
import os

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.test_content_logger import TestContentLogger
from src.lib.content_base_test_case import ContentBaseTestCase
from src.provider.spsinfo_provider import SpsinfoProvider


class CheckSpsManuf(ContentBaseTestCase):
    """
    HPQC ID : "H80019-PI_Manageability_SPS_Tools_SPSManuf_O"

    The purpose of this test case is to verify Spstool folder to be copy on Windows sut and
    execute spsManufWin64.exe command and to check the spsmanuf test passed or not by providing the
    correct and wrong values for Runtime Image FW Version req value in spsManuf.cfg files.
    """
    TEST_CASE_ID = ["H80019-PI_Manageability_SPS_Tools_SPSManuf_O"]
    step_data_dict = {1: {'step_details': 'Check spstool copied on sut ',
                          'expected_results': 'Spstool prpare for unzip with two '
                                              'spsmanuf with correct and incorrect firmware version then'
                                              ' compress and copy to sut'},
                      2: {'step_details': 'Execute  spsManufWin64.exe -f spsManuf.cfg and '
                                          'spsManufWin64.exe -f spsManuf.cfg -verbose',
                          'expected_results': 'Check spsManuf Test Passed after executing the commands.'}
                      }
    SPSMANUF_WRONG_VERSION = "1.2.3.4"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of CheckSpsManuf

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(CheckSpsManuf, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self.sps_firmware_provider = SpsinfoProvider.factory(self._log, cfg_opts, self.os)  # type: SpsinfoProvider
        self.sps_tool_zip_file_path, self.sps_info_ver = self._common_content_configuration.get_sps_tool_info()
        self.sps_info_file_name = os.path.split(self.sps_tool_zip_file_path)[-1].strip()

    def prepare(self):
        # type: () -> None
        """
        Preparing sut with default setting

        :return: None
        """
        super(CheckSpsManuf, self).prepare()

    def execute(self):
        """
        This method unzip the Sps Manuf tool from the content configuration lib on host and modify spsManuf.cfg file
        copies Sps Manuf tool zip file to sut
        verifies successful test and verifies fail test.

        :return: True if success and fail tests executes as excepted.
        """
        self._test_content_logger.start_step_logger(1)
        self.modify_spsmanuf_config_archive()
        self.sut_folder_path = self.sps_firmware_provider.copy_spstool_sut(self.sps_tool_zip_file_path,
                                                                           self.sps_info_file_name)
        self._test_content_logger.end_step_logger(1, return_val=True)
        self._test_content_logger.start_step_logger(2)
        self.sps_firmware_provider.spsmanuf_tool_success_test(self.sut_folder_path)
        self.sps_firmware_provider.spsmanuf_tool_fail_test(self.sut_folder_path)
        self.sps_firmware_provider.spsmanuf_tool_success_test_verbose(self.sut_folder_path)
        self.sps_firmware_provider.spsmanuf_tool_fail_test_verbose(self.sut_folder_path)
        self._test_content_logger.end_step_logger(2, return_val=True)
        return True

    def modify_spsmanuf_config_archive(self):
        """
        Modifies the spsmanuf archive folder to create correct and wrong version of Image FW Version in
        SPS manuf conf files.
        """
        sps_tool_zip_file_host_path = os.path.splitext(self.sps_tool_zip_file_path)[0]
        self._common_content_lib.extract_zip_file_on_host(self.sps_tool_zip_file_path, sps_tool_zip_file_host_path)
        self.sps_firmware_provider.modify_cfg(sps_tool_zip_file_host_path, self.sps_info_ver,
                                              self.sps_firmware_provider.SPSMANUF_ACTUAL_CFG)
        self.sps_firmware_provider.modify_cfg(sps_tool_zip_file_host_path, self.SPSMANUF_WRONG_VERSION,
                                              self.sps_firmware_provider.SPSMANUF_WRONG_CFG)
        shutil.make_archive(os.path.splitext(self.sps_tool_zip_file_path)[0], 'zip', sps_tool_zip_file_host_path)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CheckSpsManuf.main() else Framework.TEST_RESULT_FAIL)
