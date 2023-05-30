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


class SataStabilityAndStressIometerAhciMode(StorageCommon):
    """
    Phoenix 1509354438: SATA-Stability and Stress- IOMeter in AHCI Mode

    Trigger iometer stress testcase on the SATA SSD on both U.2 and M.2  in AHCI mode
    """
    TEST_CASE_ID = ["1509354438", "SATA-Stability and Stress- IOMeter in AHCI Mode"]

    step_data_dict = {1: {'step_details': 'Copy and install the iometer to the system.',
                          'expected_results': 'IOMeter tool installed and executed successfully without any errors'},
                      2: {'step_details': 'Create simple volume for all the SATA SSD both U.2 and M.2.',
                          'expected_results': 'SSD formatted and simple volume created.'},
                      3: {'step_details': 'Trigger the iometer on the SATA SSD with IO operations sequential read , '
                                          'sequential write , random read and random write.',
                          'expected_results': 'IOMeter tool triggered and executed successfully without any errors'}
                      }
    CSV_FILE = "result.csv"
    DEVICE_TYPE = "SATA"
    ADD_IOMETER_REG = "reg import execute_storage_iometer.reg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new StorageIOStressWindows object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(SataStabilityAndStressIometerAhciMode, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        csv_file_path = os.path.join(self.log_dir, self.CSV_FILE)
        self.csv_reader_obj = SocWatchCSVReader(self._log, csv_file_path)

    def prepare(self):
        """
        # type: () -> None
        Executing the prepare.
        """
        super(SataStabilityAndStressIometerAhciMode, self).prepare()
        self._test_content_logger.start_step_logger(1)
        self.sut_folder_path = self._install_collateral.install_iometer_tool_windows()
        self._log.info("OS IOmeter tool installed successfully in SUT path {}".format(self.sut_folder_path))

        self._test_content_logger.end_step_logger(1, True)

    def execute_iometer(self, sut_folder_path):
        """
        1. Run execute_storage_iometer.reg file in SUT machine to Once run.
        2. IOmeter will run for one hour
        3. Perform an reboot and checks iometer in task manager

        :raise: content_exceptions.TestFail
        :return: None
        """
        # Adding iometer command to regedit
        self._log.info("Executing {} command".format(self.ADD_IOMETER_REG))
        self._common_content_lib.execute_sut_cmd(self.ADD_IOMETER_REG,
                                                 self.ADD_IOMETER_REG, self._command_timeout,
                                                 sut_folder_path)
        # Adding Autologon command to regedit
        self._log.info("Executing {} command".format(IOmeterToolConstants.EXECUTE_AUTOLOGON_REG))
        self._common_content_lib.execute_sut_cmd(IOmeterToolConstants.EXECUTE_AUTOLOGON_REG,
                                                 IOmeterToolConstants.EXECUTE_AUTOLOGON_REG, self._command_timeout,
                                                 sut_folder_path)
        self._common_content_lib.perform_os_reboot(self.reboot_timeout)
        time.sleep(TimeConstants.ONE_MIN_IN_SEC / 2)
        self.verify_iometer_running()

    def verify_iometer_running(self):
        """
        Function to verify that the process is running in the background on SUT.

        :raise: RuntimeError if IOmeter is not launched in background
        """
        process_name = "IOmeter.exe"
        ret_code = self.__verify_process_running(process_name)

        if ret_code == 0:
            self._log.info("{} has been started to execute in the background..".format(process_name))
        else:
            raise RuntimeError("{} is not launched in the background..".format(process_name))

    def __verify_process_running(self, str_process_name):
        """
        Function to find the process running on the SUT.

        :param str_process_name: name of the process to be found
        :return 0 if process is found in the task list else 1
        """
        process_running = self.os.execute('TASKLIST | FINDSTR /I "{}"'.format(str_process_name),
                                          self._command_timeout)
        return process_running.return_code

    def wait_for_iometer_to_complete(self):
        """
        Function verify and hold until background process finish running on the SUT.
        """
        process_running = True
        self.process_name = "IOmeter.exe"

        while process_running:
            ret_code = self.__verify_process_running(self.process_name)

            if ret_code == 0:
                self._log.info("IOmeter is still running in the background..")
                self._log.info("Waiting for the IOmeter execution to complete..")
                time.sleep(TimeConstants.FIVE_MIN_IN_SEC)
            else:
                process_running = False

                self._log.info("IOmeter execution has been completed successfully..")
                self._log.info("{} has been started to execute in the background..".format(self.process_name))

    def verify_iometer_logs(self, sut_folder_path):
        """
        To verify the vss logs post execution

        :param sut_folder_path: path where log file resides in the SUT.
        :return: true if log has no errors else fail
        """
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

    def execute(self):
        """
        1. Create simple volume for all the SATA SSD both U.2 and M.2.
        2. Trigger the iometer on the SATA SSD with IO operations sequential read , sequential write ,
        random read and random write.

        :return: True or False
        """
        self._test_content_logger.start_step_logger(2)
        self.format_drive_win(self.DEVICE_TYPE)
        self._test_content_logger.end_step_logger(2, True)

        self._test_content_logger.start_step_logger(2)
        self.execute_iometer(self.sut_folder_path)
        # wait for the iometer to complete
        self.wait_for_iometer_to_complete()
        # Parsing iometer log
        self.verify_iometer_logs(self.sut_folder_path)
        self._test_content_logger.end_step_logger(2, True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SataStabilityAndStressIometerAhciMode.main() else Framework.TEST_RESULT_FAIL)
