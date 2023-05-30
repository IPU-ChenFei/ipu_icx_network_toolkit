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
import time
import os

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.install_collateral import InstallCollateral
from src.lib.dtaf_content_constants import IOmeterToolConstants, TimeConstants
from src.storage.test.storage_common import StorageCommon
from src.provider.socwatch_provider import SocWatchCSVReader
from src.lib.test_content_logger import TestContentLogger
from src.lib import content_exceptions


class StorageIOStressSataWindows(StorageCommon):
    """
    HPALM : H80007-PI_Storage_StressIO_SATA_W, H82235-PI_Storage_StressIO_SATA_W
    Drive stress IO on all the drives for one hour:
    1. On Windows SUT, run 'iometer.exe' under cmd shell for one hour
    """
    TEST_CASE_ID = ["H80007", "PI_Storage_StressIO_SATA_W", "H82235", "PI_Storage_StressIO_SATA_W"]

    step_data_dict = {1: {'step_details': 'Check all the drives in This Computer-->Manage-->Disk Management',
                          'expected_results': 'Collected and verified os booted from SATA or not'},
                      2: {'step_details': 'IDrive stress IO on all the drives for one hour using Iometer tool command '
                                          'run-iometer -t 1:00:0',
                          'expected_results': 'IOMeter tool installed and executed successfully without any errors'}}
    CSV_FILE = "result.csv"
    DEVICE_TYPE = "SATA"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new StorageIOStressWindows object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(StorageIOStressSataWindows, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        csv_file_path = os.path.join(self.log_dir, self.CSV_FILE)
        self.csv_reader_obj = SocWatchCSVReader(self._log, csv_file_path)

    def prepare(self):
        """
        # type: () -> None
        Executing the prepare.
        """
        super(StorageIOStressSataWindows, self).prepare()

    def execute_iometer(self, sut_folder_path):
        """
        1. Run execute_iometer.reg file in SUT machine to Once run.
        2. IOmeter will run for one hour
        3. Perform an reboot and checks iometer in task manager

        :raise: content_exceptions.TestFail
        :return: None
        """
        # Adding iometer command to regedit
        self._log.info("Executing {} command".format(IOmeterToolConstants.ADD_IOMETER_REG))
        self._common_content_lib.execute_sut_cmd(IOmeterToolConstants.ADD_IOMETER_REG,
                                                 IOmeterToolConstants.ADD_IOMETER_REG, self._command_timeout,
                                                 sut_folder_path)
        # Adding Autologon command to regedit
        self._log.info("Executing {} command".format(IOmeterToolConstants.EXECUTE_AUTOLOGON_REG))
        self._common_content_lib.execute_sut_cmd(IOmeterToolConstants.EXECUTE_AUTOLOGON_REG,
                                                 IOmeterToolConstants.EXECUTE_AUTOLOGON_REG, self._command_timeout,
                                                 sut_folder_path)
        self._common_content_lib.perform_os_reboot(self.reboot_timeout)
        time.sleep(TimeConstants.ONE_MIN_IN_SEC)
        process_running = self.os.execute(IOmeterToolConstants.TASKFIND_CMD.format("Iometer"),
                                          self._command_timeout)

        self._log.info("Task list output: {}".format(process_running.stdout))
        if process_running.return_code:
            raise content_exceptions.TestFail("IOMeter stress tool is not running")
        self._log.info("Successfully launched IOmeter tool and execute iometer stress for {}secs"
                       .format(TimeConstants.ONE_HOUR_IN_SEC))
        time.sleep(TimeConstants.ONE_HOUR_IN_SEC + TimeConstants.ONE_MIN_IN_SEC)
        process_running = self.os.execute(
            IOmeterToolConstants.TASKFIND_CMD.format("Iometer"),
            self._command_timeout)
        if not process_running.return_code:
            raise content_exceptions.TestFail("IOMeter stress tool is failed to close still running")
        self._log.info("Successfully launched and Ended IOmeter tool")

    def execute(self):
        """
        1. Check OS is booted from SATA or not
        2. Copy IOMeter tool into Windows target SUT.
        3. Run iometer.reg file in Host machine to accept Intel Open Source License.
        4. On Windows SUT, run EXECUTE_IOMETER_CMD

        :raise: content_exceptions.TestFail
        :return: True or False
        """
        self._test_content_logger.start_step_logger(1)
        self.verify_os_device_info(self.DEVICE_TYPE)
        self._log.info("OS Successfully booted from {}".format(self.DEVICE_TYPE))
        self._test_content_logger.end_step_logger(1, True)
        self._test_content_logger.start_step_logger(2)
        sut_folder_path = self._install_collateral.install_iometer_tool_windows()
        self.execute_iometer(sut_folder_path)
        # Copy Csv file from host to sut
        self.copy_csv_file_from_sut_to_host(self.log_dir, sut_folder_path, self.CSV_FILE)
        # Update the csv file to the csv reader provider
        self.csv_reader_obj.update_csv_file(os.path.join(self.log_dir, self.CSV_FILE))
        absolute_log_path = self.log_dir + os.sep + self.CSV_FILE
        read_errors_values = self.get_column_data(IOmeterToolConstants.READ_ERROR, absolute_log_path)
        self._log.info("Iometer {} values :{}".format(IOmeterToolConstants.READ_ERROR, read_errors_values))

        write_errors_values = self.get_column_data(IOmeterToolConstants.WRITE_ERROR, absolute_log_path)
        self._log.info("Iometer {} values :{}".format(IOmeterToolConstants.WRITE_ERROR, write_errors_values))
        read_errors_values = [float(value) for value in read_errors_values if
                              float(value) > float(IOmeterToolConstants.ERROR_LIMIT)]
        errors = []
        if read_errors_values:
            errors.append("Few {} values are greater than {}".format(IOmeterToolConstants.READ_ERROR,
                                                                     IOmeterToolConstants.ERROR_LIMIT))
        write_errors_values = [float(value) for value in write_errors_values if
                               float(value) > float(IOmeterToolConstants.ERROR_LIMIT)]
        if write_errors_values:
            errors.append("Few {} values are greater than {}".format(IOmeterToolConstants.WRITE_ERROR,
                                                                     IOmeterToolConstants.ERROR_LIMIT))

        if errors:
            raise content_exceptions.TestFail("\n".join(errors))
        self._test_content_logger.end_step_logger(2, True)

        return True

    def cleanup(self, return_status):
        """
        # type: (bool) -> None
        Executing the cleanup.
        """
        super(StorageIOStressSataWindows, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StorageIOStressSataWindows.main() else Framework.TEST_RESULT_FAIL)
