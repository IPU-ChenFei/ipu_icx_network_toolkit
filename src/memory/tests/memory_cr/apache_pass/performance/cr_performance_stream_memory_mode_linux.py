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

from pathlib import Path

from dtaf_core.lib.dtaf_constants import Framework

from src.memory.tests.memory_cr.apache_pass.performance.cr_performance_common import CrPerformance
from src.memory.tests.memory_cr.apache_pass.provisioning.cr_provisioning_2lm_100_memory_mode_linux \
    import CRProvisioning2LM100MemoryModeLinux
from src.memory.lib.memory_common_lib import MemoryCommonLib
from src.lib.test_content_logger import TestContentLogger


class CRPerformanceStreamMemoryMode(CrPerformance):
    """
    Glasgow ID: 56974

    1. STREAM is the de facto industry standard benchmark for measuring sustained memory bandwidth in MB/S.
    2. This test can be utilized to test DCPMMs configured in memory mode or alternately to test
    system memory when the DCPMMs are configured in AppDirect mode.
    3. When run in 2LM 100% memory mode, the DCPMMs are used as system memory, DDR4 memory is utilized as cache.
    """

    BIOS_CONFIG_FILE = "cr_performance_stream_memory_mode_linux_56974.cfg"
    TEST_CASE_ID = "G56974"
    STREAM_LOG_FILE = "DCPMM_2LM_Stream.log"
    LOG_FOLDER = "logs"

    _ipmctl_execute_path = None
    _stream_extract_path = None
    step_data_dict = {1: {'step_details': 'Clear OS logs and Set & Verify BIOS knobs', 'expected_results':
                          'Clear ALL the system Os logs and BIOS setup options are updated with changes saved'},
                      2: {'step_details': 'Run IPMCTL command to get memory resources and install stream on SUT',
                          'expected_results': 'Memory allocation of 100% 2LM Memory Mode is configured and '
                                              'stream installed successfully'},
                      3: {'step_details': 'Run Stream command', 'expected_results':
                          'Stream execution completed without errors and a log file generated'},
                      4: {'step_details': 'Check Stream, var/log/messages, dmesg, journalctl logs',
                          'expected_results': 'No unexpected errors logged'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new Performance2LM100MemModeMLCStream object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling CRProvisioning2LM100MemoryModeLinux of Glasgow ID : 57092
        self._cr_provisioning_2lm_memory_mode = CRProvisioning2LM100MemoryModeLinux(test_log,
                                                                                    arguments, cfg_opts)

        self._cr_provisioning_2lm_memory_mode._log.info("Provisioning of DCPMM with 2LM 100%  Memory Mode "
                                                        "has been started.")
        self._cr_provisioning_2lm_memory_mode.prepare()
        self._cr_provisioning_result = self._cr_provisioning_2lm_memory_mode.execute()

        # calling cr performance init
        super(CRPerformanceStreamMemoryMode, self).__init__(test_log, arguments, cfg_opts,
                                                            self.BIOS_CONFIG_FILE)
        if self._cr_provisioning_result:
            self._log.info("Provisioning of DCPMM with 2LM 100% memory mode has been done successfully!")
        else:
            err_log = "Provisioning of DCPMM 2LM 100% memory mode is failed!"
            self._log.error(err_log)
            raise RuntimeError(err_log)
        #  Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._mem_parse_log = MemoryCommonLib(self._log, cfg_opts, self._os, 0)

    def prepare(self):
        # type: () -> None
        """
        1. Clear OS and dmesg logs
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs that are set.

        :return: None
        """

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        self._common_content_lib.clear_os_log()  # To clear os logs
        self._common_content_lib.clear_dmesg_log()  # To clear dmesg logs
        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.
        #  Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)
        self._ipmctl_execute_path = self.ROOT

    def execute(self):
        """
        1. To verify the memory resources
        2. To install stream tool and execute the stream commands.

        :return: True if no errors else False
        """
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        self._cr_provisioning_2lm_memory_mode.ipmctl_show_mem_resources(self._ipmctl_execute_path)

        #  Show System Memory info
        system_memory_data = self._cr_provisioning_2lm_memory_mode.show_system_memory_report_linux()

        #  Verify 2LM provisioning mode
        self._cr_provisioning_2lm_memory_mode.verify_lm_provisioning_configuration_linux(
            self._cr_provisioning_2lm_memory_mode.dcpmm_disk_goal, system_memory_data, mode="2LM")

        # install Stream tool
        self._stream_extract_path = self._install_collateral.install_stream_zip_file()

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, self._stream_extract_path)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        stream_command = "runme.sh >> {}".format(self.STREAM_LOG_FILE)

        self._log.info("Executing stream command : {}".format(stream_command))

        self._common_content_lib.execute_sut_cmd(stream_command, "Executing stream command",
                                                 self._command_timeout, self._stream_extract_path)
        #  Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)

        self._common_content_lib.execute_sut_cmd("rm -rf {}".format(self.LOG_FOLDER), "To delete log folder",
                                                 self._command_timeout, cmd_path=self.ROOT)
        self._common_content_lib.execute_sut_cmd("mkdir {}".format(self.LOG_FOLDER), "Create a log folder",
                                                 self._command_timeout, cmd_path=self.ROOT)
        var_log_messages = Path(os.path.join(self.LOG_FOLDER, "var_log_messages.log")).as_posix()
        self._common_content_lib.execute_sut_cmd("tail /var/log/messages > {}".format(var_log_messages),
                                                 "var/log/messages log", self._command_timeout)

        journalctl_log_path = Path(os.path.join(self.LOG_FOLDER, "journalctl.log")).as_posix()
        self._common_content_lib.execute_sut_cmd("journalctl -u mcelog.service  > {}".format(journalctl_log_path),
                                                 "Journalctl command", self._command_timeout)

        dmesg_log_path = Path(os.path.join(self.LOG_FOLDER, "dmesg.log")).as_posix()
        self._common_content_lib.execute_sut_cmd("dmesg  > {}".format(dmesg_log_path), "dmesg log command",
                                                 self._command_timeout)

        self._common_content_lib.delete_testcaseid_folder_in_host(test_case_id=self.TEST_CASE_ID)

        self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self._stream_extract_path, extension=".log")
        log_path_to_parse = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self.LOG_FOLDER, extension=".log")

        final_result = self.log_parsing(log_path_to_parse)
        #  Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, final_result)

        return final_result

    def log_parsing(self, log_file_path_host):
        """
        This function is used for the verification of logs.

        :param log_file_path_host: Log file path in the Host
        :return: True if all log files parsed without any errors else False
        """
        final_result = [
            self.verify_stream_data_linux(file_path=os.path.join(log_file_path_host,
                                                                 self.STREAM_LOG_FILE)),
            self._mem_parse_log.parse_log_for_error_patterns(log_path=os.path.join(log_file_path_host,
                                                                                     "dmesg.log")),
            self._mem_parse_log.parse_log_for_error_patterns(log_path=os.path.join(log_file_path_host,
                                                                                     "journalctl.log")),
            self._mem_parse_log.parse_log_for_error_patterns(
                log_path=os.path.join(log_file_path_host, "var_log_messages.log"), encoding="UTF-8")]
        return all(final_result)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CRPerformanceStreamMemoryMode.main() else Framework.TEST_RESULT_FAIL)
