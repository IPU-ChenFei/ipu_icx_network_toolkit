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
import time
import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.lib.test_content_logger import TestContentLogger
from src.memory.tests.memory_ddr.ddr_common import DDRCommon
from src.manageability.lib.redfish_test_common import RedFishTestCommon
from src.lib import content_exceptions


class IlvssMemoryStress(DDRCommon):
    """
    Glasgow ID: 63293

    This test case is to demonstrate ilVSS Memory Stress.
    This testing covers the below tasks..
    1. Verify platform functional reliability with the a memory configuration as spec defined without unexpected errors
       under heavy stress with data integrity checking.
    2. Configure the ilVSS Data Integrity & Stress application for the platform.
    3. Execute memory focused stress for specified period of time.
    4. Check basic platform functionality while under stress.
    5. Verify no unexpected errors were logged while executing stress.
    """

    _bios_config_file = "ilvss_memory_stress.cfg"
    TEST_CASE_ID = "G63293"
    OPT_IVLSS = "/opt/ilvss.0"
    VAR_LOG = "/var"
    VAR_LOG_MSG_CMD = "cat /var/log/messages >& message.log"
    JOURNAL_CTL_CMD = "journalctl -u mcelog.service >& journalctl.log"
    LIST_PROCESSES = "texec"
    return_value = []
    result_value = "True"
    dmi_cmd = "dmidecode > dmi.txt"
    step_data_dict = {1: {'step_details': 'Set and verify BIOS knobs and verify the Total memory before and after '
                                          '    BIOS knobs setting',

                          'expected_results': 'BIOS setup options are updated with changes saved and the memory '
                                              'reported by OS is consistent '},

                      2: {'step_details': 'Clear OS logs  and execute the top command and  verify that the three values'
                                          'displayed for "Load Average" is closer to zero ',

                          'expected_results': 'Cleared  OS system logs and Load Average readings are closer to zero '},

                      3: {'step_details': 'Copy ilvss package to SUT and Install the latest version  of ilvss and'
                                          'if ilvss is already installed, delete the existing log files ',

                          'expected_results': 'Successfully Installed the ilVSS tool/package.'
                                              'and Pre-existing ilvss logs are deleted (If present) '},

                      4: {'step_details': 'Set current date and time on SUT and copy stress pkg on SUT , execute ilvss'
                                          'to complete a full test loop ',
                          'expected_results': 'Date and time is updated ,stress pkg copied successfully ,ilvss is '
                                              'executed for complete full test'},

                      5: {'step_details': 'Execute the top command after system is under stress and Load Average" value'
                                          ' should be around 50 or greater',
                          'expected_results': 'Load Average  reported by "top" is significantly greater after VSS'
                                              ' begins execution '},

                      6: {'step_details': ' Copy vss log from Sut to Host and parse the vss log for unexpected error ',

                          'expected_results': 'Verified, there are no memory errors reported from VSS logs '},

                      7: {'step_details': 'Parse the /var/log/messages and journalctl logs for any unexpected errors '
                                          'and warnings ',
                          'expected_results': 'No unexpected errors were logged during stress test in /varlog/messages'
                                              ' and journalctl '},
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new ilVSS Memory Stress object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """

        #  Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        # calling base class init

        super(IlvssMemoryStress, self).__init__(test_log, arguments, cfg_opts, self._bios_config_file)
        self.obj_redfish = RedFishTestCommon(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        1. Setting the bios knobs to its default mode.
        2. Setting the bios knobs as per the test case.
        3. Rebooting the SUT to apply the new bios settings.
        4. Verifying the bios knobs that are set.

        :return: None
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        total_memory_before_bios = self.get_total_memory()
        self._log.info(total_memory_before_bios)
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.
        total_memory_after_bios = self.get_total_memory()
        self._log.info(total_memory_after_bios)
        total_memory_variance = \
            self._post_mem_capacity_config - (self._post_mem_capacity_config * self._variance_percent)

        total_dram_memory = int(self.get_total_memory().split()[0]) / (1024 * 1024)
        if total_dram_memory < int(total_memory_variance) or total_dram_memory > self._post_mem_capacity_config:
            raise content_exceptions.TestFail("Total Installed DDR Capacity is not same as configuration.")

        self._log.info("Total Installed DDR memory Capacity is same as configuration.")

        #  Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Function is responsible for the below tasks,

        1. Clear dmeg log.
        2. Clear OS logs and verify the load average value.
        3. Install ilvss tool.
        4. Verify no unexpected errors were logged while executing stress under the specified conditions.
        5. Verify the load average after the ilvss stress.
        6. Copy log files to Host
        7. Verify no unexpected errors were logged in /var/log/messages.
        8. Verify no unexpected errors were logged in journal ctl.

        :return: True, if the test case is successful else false
        :raise: Runtime error
        """
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        # To clear the os logs ,/var/log/messages
        self._common_content_lib.clear_os_log()
        self.obj_redfish.check_sel()
        self.obj_redfish.clear_sel()

        # Clear dmesg logs
        self._common_content_lib.clear_dmesg_log()

        # Load average before system under stress
        load_avg_value = self.get_load_average()
        max_load_avg = self.get_max_load_average(load_avg_value)
        self._log.info("Correct load average value {}".format(max_load_avg))
        if float(max_load_avg) <= self.CMP_LOAD_AVERAGE_BEFORE_STRESSAPP:
            self._log.info("Success as maximum value of load average value is less than threshold value")
        else:
            log_err = "Failed as maximum value of load average value more than threshold value"
            self._log.error(log_err)
            raise RuntimeError(log_err)

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        # Install latest version of ilvss
        self._install_collateral.install_ilvss()

        #  Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)

        product_info = self._common_content_lib.execute_sut_cmd("sudo dmidecode -s system-product-name",
                                                                "Product information", self._command_timeout,
                                                                self.LINUX_USR_ROOT_PATH)
        product_info = product_info.split('\n')[0]

        # Execute ilvss configuration for stress
        self.configure_ilvss_stress()

        self._os.execute_async(r"./t /pkg /opt/ilvss.0/packages/{} /reconfig /pc {} /flow "
                               r"S145 /run /minutes {} /RR ilvss_log.log".
                               format(self.dict_package_info[product_info],
                                      self.dict_product_info[product_info],
                                      self._ilvss_runtime), cwd=self.OPT_IVLSS)
        time.sleep(600)
        #  Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=True)

        # Step logger start for Step 5
        self._test_content_logger.start_step_logger(5)

        # To check max load avg after stress
        load_avg_value = self.get_load_average()
        max_load_avg = self.get_max_load_average(load_avg_value)
        self._log.info("Collected load average value {}".format(max_load_avg))
        if float(max_load_avg) >= self.CMP_LOAD_AVERAGE_AFTER_STRESSAPP:
            self._log.info("Correct load average value")
        else:
            log_error = "Incorrect load average value"
            self._log.error(log_error)
            raise RuntimeError(log_error)

        # Waiting for half of the execution time, so that we can validate the platform responsiveness
        time.sleep(float((self._command_timeout * self._ilvss_runtime) * self._script_sleep_time_percent))

        # Check responsiveness of the platform by creating a text file with some content.
        self._common_content_lib.execute_sut_cmd("echo testing the platform response > test.txt", "Creating a file",
                                                 self._command_timeout)
        #  Step logger end for Step 5
        self._test_content_logger.end_step_logger(5, return_val=True)

        # Step logger start for Step 6
        self._test_content_logger.start_step_logger(6)

        # It will make this script wait till the process completes it's execution on the SUT
        self.wait_for_ilvss_process_finish(self.LIST_PROCESSES)

        # Copy VSS logs from SUT to Host
        self._common_content_lib.delete_testcaseid_folder_in_host(test_case_id=self.TEST_CASE_ID)
        log_file_path_host = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self.OPT_IVLSS, extension=".log")

        # Parsing ilvss log
        self.return_value.append(self._memory_common_lib.parse_log_for_error_patterns
                                 (log_path=os.path.join(log_file_path_host, "ilvss_log.log")))

        #  Step logger end for Step 6
        self._test_content_logger.end_step_logger(6, return_val=all(self.return_value))

        # Step logger start for Step 7
        self._test_content_logger.start_step_logger(7)

        # Copy /var/log/messages logs from SUT to Host and parse to check error/warning
        self._common_content_lib.execute_sut_cmd(self.VAR_LOG_MSG_CMD,
                                                 "redirect /var/log/messages to message.log ",
                                                 self._command_timeout, self.VAR_LOG)

        file_path_host = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self.VAR_LOG, extension=".log")

        self.return_value.append(self._memory_common_lib.parse_log_for_error_patterns
                                 (log_path=os.path.join(file_path_host, "message.log")))

        # Execute journalctl command and copy logs from SUT to Host and parse to check error/warning
        self._common_content_lib.execute_sut_cmd(self.JOURNAL_CTL_CMD,
                                                 "To execute journalctl command ",
                                                 self._command_timeout, self.LINUX_USR_ROOT_PATH)

        file_path_host = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self.LINUX_USR_ROOT_PATH, extension=".log")

        self.return_value.append(self._memory_common_lib.parse_log_for_error_patterns
                                 (log_path=os.path.join(file_path_host, "journalctl.log"),))

        #  Step logger end for Step 7
        self._test_content_logger.end_step_logger(7, return_val=all(self.return_value))

        return all(self.return_value)

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(IlvssMemoryStress, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if IlvssMemoryStress.main() else Framework.TEST_RESULT_FAIL)
