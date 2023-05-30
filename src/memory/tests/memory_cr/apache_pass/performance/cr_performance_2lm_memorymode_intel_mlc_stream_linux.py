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
from src.lib.bios_util import BiosUtil
from src.lib.test_content_logger import TestContentLogger


class CRPerformance2LM100MemModeMLCStream(CrPerformance):
    """
    Glasgow ID: 57076

    1. Measure memory latencies and bandwidth using the MLC and Stream benchmarks in a Linux OS environment.
    2. The tests is executed on a system configured in 2LM mode with DCPMMs and with DDR DIMMs only with
    specific platform BIOS settings.
    3. Results are also taken with CPU prefetchers enabled and disabled.
    4. STREAM is the de facto industry standard benchmark for measuring sustained memory bandwidth in MB/S.
    5.The Memory Latency Checker (MLC) test tool is now available externally and is method of measuring delay
    in the memory subsystem as a function of memory bandwidth.
    """

    PREFETCHERS_DISABLED_BIOS_CONFIG_FILE = \
        "cr_performance_2lm_memorymode_intel_mlc_stream_prefetchers_disabled_57076.cfg"
    PREFETCHERS_ENABLED_BIOS_CONFIG_FILE = \
        "cr_performane_2lm_memorymode_intel_mlc_stream_prefetchers_enabled_57076.cfg"
    TEST_CASE_ID = "G57076"
    MLC_COMMAND = "./mlc -Z 2>&1 | tee -a {}"
    STREAM_COMMAND = "./stream| tee -a {}"
    MLC_PREFETCH_OFF_LOG_FILE = "2lm_prefetchoff_mlc.log"
    STREAM_PREFETCH_OFF_LOG_FILE = "2lm_prefetchoff_stream.log"
    MLC_PREFETCH_ON_LOG_FILE = "2lm_prefetchon_mlc.log"
    STREAM_PREFETCH_ON_LOG_FILE = "2lm_prefetchon_stream.log"
    LOG_FOLDER = "logs"

    _ipmctl_execute_path = None
    _mlc_execute_path = None
    _stream_extract_path = None

    step_data_dict = {1: {'step_details': 'Clear OS logs and Set & Verify BIOS knobs', 'expected_results':
                          'Clear ALL the system Os logs and BIOS setup options are updated with changes saved'},
                      2: {'step_details': 'Run IPMCTL command to get memory resources', 'expected_results':
                          'Memory allocation of 100% 2LM Memory Mode is configured'},
                      3: {'step_details': 'Run IPMCTL command to get DCPMM pre performance', 'expected_results':
                          'A table with these DCPMM performance metrics should be generated'},
                      4: {'step_details': 'Assigning executable privileges to MLC', 'expected_results':
                          'MLC benchmark installs without errors'},
                      5: {'step_details': 'Run MLC command for prefetch off', 'expected_results':
                          'Verify that the command completes successfully and log file is generated'},
                      6: {'step_details': 'Run Stream command for prefetch off', 'expected_results':
                          'Verify that the command completes successfully and log file is generated'},
                      7: {'step_details': 'Update the BIOS settings for all prefetchers enabled', 'expected_results':
                          'BIOS setup options are updated with changes saved'},
                      8: {'step_details': 'Load msr driver and Run MLC command for prefetch ON', 'expected_results':
                          'msr driver installs properly,  MLC command completes successfully and a file is generated'},
                      9: {'step_details': 'Run Stream command for prefetch ON', 'expected_results':
                          'Verify that the command completes successfully and log file is generated'},
                      10: {'step_details': 'Run IPMCTL command to get DCPMM post performance', 'expected_results':
                           'Each of the values for each DimmID are expected to greater than those '
                           'logged prior to test'},
                      11: {'step_details': 'check MLC, Stream, var/log/messages, dmesg, journalctl logs',
                           'expected_results': 'No unexpected errors logged'}
                      }

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
        super(CRPerformance2LM100MemModeMLCStream, self).__init__(test_log, arguments, cfg_opts,
                                                                  self.PREFETCHERS_DISABLED_BIOS_CONFIG_FILE)
        #  Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

        if self._cr_provisioning_result:
            self._log.info("Provisioning of DCPMM with 2LM 100% memory mode has been done successfully!")
        else:
            err_log = "Provisioning of DCPMM 2LM 100% memory mode is failed!"
            self._log.error(err_log)
            raise RuntimeError(err_log)

        self.bios_config_prefetcher_enable_obj = BiosUtil(cfg_opts, self.PREFETCHERS_ENABLED_BIOS_CONFIG_FILE, self._bios,
                                                          self._log, self._common_content_lib)

        self._idle_latency_threshold = self._common_content_configuration.memory_mlc_idle_lateny_threshold()
        self._peak_memory_bandwidth_threshold = \
            self._common_content_configuration.memory_mlc_peak_memory_bandwidth_threshold()
        self._memory_bandwidth_threshold = self._common_content_configuration.memory_mlc_memory_bandwidth_threshold()
        self._mem_parse_log = MemoryCommonLib(self._log, cfg_opts, self._os, 0)

    def prepare(self):
        # type: () -> None
        """

        1. To Clear OS and dmesg logs.
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case for the prefetchers disabled.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs that are set.
        6. To install mlc tool.
        7. To install stream tool.

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
        self._mlc_execute_path = self._install_collateral.install_mlc()  # To install MLC tool in SUT
        self._stream_extract_path = self._install_collateral.install_stream_tool()  # To install Stream tool in SUT

    def execute(self):
        """
        1. To verify the provisioning of DCPMM with 2LM 100%  Memory Mode.
        2. To set the Bios knobs for the prefetchers enabled.
        3. Reboot the SUT to apply the new bios settings.
        4. Verify the bios knobs that are set.
        5. To verify the DCPMM performance for pre and post values.
        6. To execute MLC and Stream commands with Prefetchers OFF and ON.
        7. To verify the MLC and Stream logs.

        :return: True if no errors else False
        """

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        self._cr_provisioning_2lm_memory_mode.ipmctl_show_mem_resources(self._ipmctl_execute_path)

        #  Show System Memory info
        system_memory_data = self._cr_provisioning_2lm_memory_mode.show_system_memory_report_linux()

        #  Verify 2LM provisioning mode
        verify_provisioning_status = self._cr_provisioning_2lm_memory_mode.verify_lm_provisioning_configuration_linux(
            self._cr_provisioning_2lm_memory_mode.dcpmm_disk_goal, system_memory_data, mode="2LM")

        # Step Logger end for Step 2
        self._test_content_logger.end_step_logger(2, verify_provisioning_status)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        # Pre DCPMM performance
        pre_stress_df = self.create_dimm_performance_result(mode="Pre")

        self._common_content_lib.clear_os_log()  # To clear os logs
        self._common_content_lib.clear_dmesg_log()  # To clear dmesg logs

        # Step Logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)

        self._common_content_lib.execute_sut_cmd("chmod +x mlc", "Assigning executable privledges",
                                                 self._command_timeout, self._mlc_execute_path)

        self._common_content_lib.execute_sut_cmd("modprobe msr", "Load msr driver", self._command_timeout)

        # Step Logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=True)

        # Step logger start for Step 5
        self._test_content_logger.start_step_logger(5)

        cmd_result = self.execute_mlc_command(self.MLC_COMMAND, self.MLC_PREFETCH_OFF_LOG_FILE, self._mlc_execute_path)

        # Step Logger end for Step 5
        self._test_content_logger.end_step_logger(5, return_val=cmd_result)

        # Step logger start for Step 6
        self._test_content_logger.start_step_logger(6)

        cmd_result = self.execute_stream_command(self.STREAM_COMMAND, self.STREAM_PREFETCH_OFF_LOG_FILE,
                                                 self._stream_extract_path)

        # Step Logger end for Step 6
        self._test_content_logger.end_step_logger(6, return_val=cmd_result)

        # Step logger start for Step 7
        self._test_content_logger.start_step_logger(7)

        #  To set the bios knobs for the prefetchers Enabled
        self.bios_config_prefetcher_enable_obj.set_bios_knob()
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
        self.bios_config_prefetcher_enable_obj.verify_bios_knob()  # To verify the bios knob settings.

        # Step Logger end for Step 7
        self._test_content_logger.end_step_logger(7, return_val=True)

        # Step logger start for Step 8
        self._test_content_logger.start_step_logger(8)

        self._common_content_lib.execute_sut_cmd("modprobe msr", "Load msr driver", self._command_timeout)
        cmd_result = self.execute_mlc_command(self.MLC_COMMAND, self.MLC_PREFETCH_ON_LOG_FILE, self._mlc_execute_path)

        # Step Logger end for Step 8
        self._test_content_logger.end_step_logger(8, return_val=cmd_result)

        # Step logger start for Step 9
        self._test_content_logger.start_step_logger(9)
        cmd_result = self.execute_stream_command(self.STREAM_COMMAND, self.STREAM_PREFETCH_ON_LOG_FILE,
                                                 self._stream_extract_path)

        # Step Logger end for Step 9
        self._test_content_logger.end_step_logger(9, return_val=cmd_result)

        # Step logger start for Step 10
        self._test_content_logger.start_step_logger(10)

        # Post DCPMM performance
        post_stress_df = self.create_dimm_performance_result(mode="Post")

        # verify pre DCPMM performance and Post DCPMM performance
        performance_status = self.verify_pre_post_stress_performance_result(pre_stress_df, post_stress_df)

        # Step Logger end for Step 10
        self._test_content_logger.end_step_logger(10, performance_status)

        # Step logger start for Step 11
        self._test_content_logger.start_step_logger(11)

        self._common_content_lib.execute_sut_cmd("rm -rf {}".format(self.LOG_FOLDER), "To delete log folder",
                                                 self._command_timeout, cmd_path=self.ROOT)
        self._common_content_lib.execute_sut_cmd("mkdir {}".format(self.LOG_FOLDER), "create a log folder",
                                                 self._command_timeout, cmd_path=self.ROOT)

        var_log_messages = Path(os.path.join(self.LOG_FOLDER, "var_log_messages.log")).as_posix()
        self._common_content_lib.execute_sut_cmd("less /var/log/messages > {}".format(var_log_messages),
                                                 "var/log/messages ", self._command_timeout)

        journalctl_log_path = Path(os.path.join(self.LOG_FOLDER, "journalctl.log")).as_posix()
        self._common_content_lib.execute_sut_cmd("journalctl -u mcelog.service  > {}".format(journalctl_log_path),
                                                 "Journalctl command", self._command_timeout)

        dmesg_log_path = Path(os.path.join(self.LOG_FOLDER, "dmesg.log")).as_posix()
        self._common_content_lib.execute_sut_cmd("dmesg  > {}".format(dmesg_log_path), "dmesg log command",
                                                 self._command_timeout)

        self._common_content_lib.delete_testcaseid_folder_in_host(test_case_id=self.TEST_CASE_ID)

        self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self.LOG_FOLDER, extension=".log")

        self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self._stream_extract_path, extension=".log")

        log_path_to_parse = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self._mlc_execute_path, extension=".log")

        self._common_content_lib.execute_sut_cmd("rm -rf {}".format(self.LOG_FOLDER), "To delete log folder",
                                                 self._command_timeout, cmd_path=self.ROOT)

        final_result = self.log_parsing(log_path_to_parse)

        # Step Logger end for Step 11
        self._test_content_logger.end_step_logger(11, final_result)

        return final_result

    def log_parsing(self, log_file_path_host):
        """
        This function is used for the verification of logs.

        :param log_file_path_host: Log file path in the Host
        :return: True if all log files parsed without any errors else False
        """
        final_result = [
            self._mlc.verify_mlc_log(log_path=os.path.join(log_file_path_host, self.MLC_PREFETCH_OFF_LOG_FILE),
                                     idle_latency=self._idle_latency_threshold,
                                     peak_injection_memory_bandwidth=self._peak_memory_bandwidth_threshold,
                                     memory_bandwidth=self._memory_bandwidth_threshold),
            self.verify_stream_data_linux(file_path=os.path.join(
                log_file_path_host, self.STREAM_PREFETCH_OFF_LOG_FILE)),
            self._mlc.verify_mlc_log(log_path=os.path.join(log_file_path_host, self.MLC_PREFETCH_ON_LOG_FILE),
                                     idle_latency=self._idle_latency_threshold,
                                     peak_injection_memory_bandwidth=self._peak_memory_bandwidth_threshold,
                                     memory_bandwidth=self._memory_bandwidth_threshold),
            self.verify_stream_data_linux(file_path=os.path.join(
                log_file_path_host, self.STREAM_PREFETCH_ON_LOG_FILE)),
            self._mem_parse_log.parse_log_for_error_patterns(log_path=os.path.join(log_file_path_host, "dmesg.log")),
            self._mem_parse_log.parse_log_for_error_patterns(
                log_path=os.path.join(log_file_path_host, "journalctl.log")),
            self._mem_parse_log.parse_log_for_error_patterns(
                log_path=os.path.join(log_file_path_host, "var_log_messages.log"), encoding="UTF-8")]

        return all(final_result)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CRPerformance2LM100MemModeMLCStream.main() else Framework.TEST_RESULT_FAIL)
