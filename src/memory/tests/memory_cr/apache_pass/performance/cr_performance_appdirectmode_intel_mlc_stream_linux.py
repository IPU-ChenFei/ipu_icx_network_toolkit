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

from src.lib.bios_util import BiosUtil
from src.lib.test_content_logger import TestContentLogger
from src.memory.tests.memory_cr.apache_pass.provisioning.cr_provisioning_2lm_mixed_mode_50_50_interleaved_dax_linux \
    import CRProvisioning2LM50AppDirect50MemoryModeDaxLinux
from src.memory.tests.memory_cr.apache_pass.performance.cr_performance_common import CrPerformance
from src.provider.mlc_provider import MlcProvider
from src.provider.ipmctl_provider import IpmctlProvider
from src.manageability.lib.redfish_test_common import RedFishTestCommon


class CRPerformanceAppDirectModeIntelMLCStreamLinux(CrPerformance):
    """
    Glasgow ID: 57739.12

    1. Measure memory latencies and bandwidth using the MLC and Stream benchmarks in a Linux OS environment.
    2. The tests are executed on a system with DCPMM capacity configured in 1LM App Direct mode with specific
        platform BIOS settings.
    3. The results are compared with those from executing with only the DDR DIMMs present.
    4. Results are also taken with CPU prefetchers enabled and disabled.
    5. STREAM is the de facto industry standard benchmark for measuring sustained memory bandwidth in "MB/S".
    6. The Memory Latency Checker (MLC) test tool is now available externally and is method of measuring
        delay in the memory subsystem as a function of memory bandwidth.
    """

    BIOS_CONFIG_FILE_PREFETCHER_OFF = "cr_performance_appdirectmode_bios_knobs_prefetcher_off.cfg"
    BIOS_CONFIG_FILE_PREFETCHER_ON = "cr_performance_appdirectmode_bios_knobs_prefetcher_on.cfg"
    TEST_CASE_ID = "G57739"
    MLC_1LM_PREFETCH_OFF_LOG = "mlc_1lm_prefetch_off.log"
    MLC_LATENCY_MATRIX_OFF_LOG = "mlc_1lm_latency_matrix_off.log"
    MLC_IDLE_LATENCY_OFF_LOG = "mlc_idle_latency_off.log"
    MLC_LOADED_LATENCY_OFF_LOG = "mlc_loaded_latency_off.log"
    MLC_1LM_PREFETCH_ON_LOG = "mlc_1lm_prefetch_on.log"
    MLC_LATENCY_MATRIX_ON_LOG = "mlc_1lm_latency_matrix_on.log"
    MLC_IDLE_LATENCY_ON_LOG = "mlc_idle_latency_on.log"
    MLC_LOADED_LATENCY_ON_LOG = "mlc_loaded_latency_on.log"
    STREAM_1LM_PREFETCH_OFF_LOG = "stream_1lm_prefetch_off.log"
    STREAM_1LM_PREFETCH_ON_LOG = "stream_1lm_prefetch_on.log"
    STREAM_CMD = "./stream | tee -a {}"
    LOG_FOLDER = "msglogs"
    _stream_execute_path = None

    step_data_dict = {1: {'step_details': 'Setting & Verify BIOS knobs',
                          'expected_results': 'Successfully setup all BIOS knobs with updated knob values'
                                              ' & Verify the changes & Save'},
                      2: {'step_details': 'Installing stream tools in sut',
                          'expected_results': 'Successfully installed or not '},
                      3: {'step_details': 'Confirm that Persistent Memory Regions and Namespaces were '
                                          'provisioned prior to execute in this test case & clear var & dmesg logs',
                          'expected_results': 'Expected pmem device(s) & filesystems are present & '
                                              'clear var & dmesg logs'},
                      4: {'step_details': 'Load the msr driver to allow MLC to  read and write '
                                          'the model-specific registers (MSRs)',
                          'expected_results': 'msr installs properly & MLC benchmark installs without error'},
                      5: {'step_details': 'Executing MLC Tool related commands and collecting '
                                          'the outputs in particular log files (with prefetcher off) ',
                          'expected_results': 'Execute with out errors and collect the data into logs'},
                      6: {'step_details': 'Changing the prefetcher knob to Enable state',
                          'expected_results': 'Successfully Setup the prefetcer to Enable state & '
                                              'Verify the changes & Save'},
                      7: {'step_details': 'Executing MLC Tool related commands and collecting '
                                          'the outputs in particular log files (with prefetcher on) ',
                          'expected_results': 'Execute with out errors and collect the data into logs'},
                      8: {'step_details': 'Delete old log folder and Create new log folder &'
                                          'Copying MLC Log folder & Stream Log to Host',
                          'expected_results': 'Successfully delete & create a new log folder &'
                                              ' copied all logs into the host'},
                      9: {'step_details': 'Execute journalctl cmd & dmesg cmd & var log cmd & collect all logs '
                                          'and store in a folder',
                          'expected_results': 'Successfully execute all and copy that log folder to host'},
                      10: {'step_details': 'Verifying the collected log data of MLC & Stream tools',
                           'expected_results': 'Successfully the values should reach the expected values and return '
                                               'true'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new CRPerformanceAppDirectModeIntelMLCStreamLinux object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(CRPerformanceAppDirectModeIntelMLCStreamLinux, self).__init__(test_log, arguments, cfg_opts,
                                                                            self.BIOS_CONFIG_FILE_PREFETCHER_OFF)

        self._ipmctl_provider = IpmctlProvider.factory(test_log, self._os, execution_env="os", cfg_opts=cfg_opts)
        # Creating an object for bios config file for prefetcher on
        self._bios_util_prfetcher_on = BiosUtil(cfg_opts, self.BIOS_CONFIG_FILE_PREFETCHER_ON, self._bios, self._log,
                                                self._common_content_lib)

        #  Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

        # Creating an object for provisioning test case
        self._cr_provisioning_2lm_mixed_mode = CRProvisioning2LM50AppDirect50MemoryModeDaxLinux(self._log,
                                                                                                arguments, cfg_opts)
        self._log.info("Starting with cr provisioning 2LM 50% Mixed Mode dax Linux Provisioning TestCase. [Glasgow ID :"
                       "58172 ]")
        self._cr_provisioning_2lm_mixed_mode.prepare()
        self._cr_provisioning_result = self._cr_provisioning_2lm_mixed_mode.execute()

        if self._cr_provisioning_result:
            self._log.info("Provisioning 2LM 50% Mixed Mode dax Linux OS has been done successfully!")
        else:
            err_log = "Provisioning 2LM 50% Mixed Mode dax Linux is failed!"
            self._log.error(err_log)
            raise RuntimeError(err_log)

        self._log.info("Ended with cr provisioning 2LM 50% Mixed Mode dax Linux Provisioning TestCase. [Glasgow ID : "
                       "58172 ]")

        # Collecting mlc threshold values from config file
        self._idle_latency_threshold = self._common_content_configuration.memory_mlc_idle_lateny_threshold()
        self._peak_memory_bandwidth_threshold = self._common_content_configuration. \
            memory_mlc_peak_memory_bandwidth_threshold()
        self._memory_bandwidth_threshold = self._common_content_configuration.memory_mlc_memory_bandwidth_threshold()
        self._loaded_latency_threshold = self._common_content_configuration.memory_mlc_loaded_latency_threshold()
        self._mlc_provider = MlcProvider.factory(test_log, cfg_opts=cfg_opts, os_obj=self._os)
        self.obj_redfish = RedFishTestCommon(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        1. Set the bios knobs to its default mode.
        2. Set the bios knobs as per the test case.
        3. Reboot the SUT to apply the new bios settings.
        4. Verify the bios knobs that are set.
        5. To install perthreadfile.txt file
        6. To install Stream tool
        :return: None
        """

        self._test_content_logger.start_step_logger(1)  # Step logger start for Step 1
        self._common_content_lib.clear_all_os_log()  # To clear os logs
        self._common_content_lib.clear_dmesg_log()  # To clear dmesg logs
        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self.perform_os.reboot(int(self._reboot_timeout))  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.
        self._test_content_logger.end_step_logger(1, return_val=True)  # Step logger end for Step 1

        self._test_content_logger.start_step_logger(2)  # Step logger start for step 2

        # To clear SEL logs
        self.obj_redfish.clear_sel()

        # Copying gen_perthreadfile.sh to SUT and creating perthreadfile.txt
        self._install_collateral.install_perthread_sh_file(self._mlc_provider.mlc_path,
                                                           self._cr_provisioning_2lm_mixed_mode.mount_list)
        self._stream_execute_path = self._install_collateral.install_stream_tool()  # To install stream tool in SUT
        self._test_content_logger.end_step_logger(2, return_val=True)  # Step logger end for step 2

    def execute(self):
        """
        Function is responsible for the below tasks,

        1. Confirm the regions and collecting namespaces after provisioning
        2. Verifying pmem devices
        3. Clearing the os and dmesg logs
        4. Executing ipmctl command to collect dcpmm performance pre values
        5. Executing all mlc relating commands and collected into there particular logs
        6. Executing stream command and collected into particular log
        7. Executing ipmctl command to collect dcpmm performance post values
        8. Executing journalctl, var, dmesg commands to collect same logs
        9. Doing log parsing for all the collected logs

        :return: True, if the test case is successful.
        :raise: None
        """

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        # Collecting Persistent Memory Regions
        self._ipmctl_provider.dcpmm_get_pmem_unused_region()

        # Collecting Namespaces
        namespace_info = self._ipmctl_provider.dcpmm_get_disk_namespace()

        # Verifying  the the list of pmem devices
        self._cr_provisioning_2lm_mixed_mode.verify_pmem_device_presence_cap(namespace_info)

        # Clearing the os logs
        self._common_content_lib.clear_os_log()

        # Clearing the dmesg logs
        self._common_content_lib.clear_dmesg_log()

        # Step logger end for step 3
        self._test_content_logger.end_step_logger(3, return_val=True)

        # Collecting pre performance data
        pre_performance_data_frame = self.create_dimm_performance_result(mode="Pre")

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)

        # Loading modeprobe drive to allow MLC to read and write
        self._common_content_lib.execute_sut_cmd("modprobe msr", "Load msr", self._command_timeout, self.ROOT)

        # Clearing the os logs
        self._common_content_lib.clear_os_log()

        # Clearing the dmesg logs
        self._common_content_lib.clear_dmesg_log()

        # Step logger end for step 4
        self._test_content_logger.end_step_logger(4, return_val=True)

        # Step logger start for Step 5
        self._test_content_logger.start_step_logger(5)

        # Executing of MLC commands on sut linux os for prefetcher OFF
        self._mlc_provider.execute_mlc_test_with_2_greater_amp_1_error_param(" ", self.MLC_1LM_PREFETCH_OFF_LOG)

        # Executing the mlc latency matrix cmd
        self._mlc_provider.get_mlc_latency_info(" ", self.MLC_LATENCY_MATRIX_OFF_LOG)

        # Executing the mlc idle latency cmd
        self._mlc_provider.get_mlc_loaded_latency_info(" ", self.MLC_LOADED_LATENCY_OFF_LOG)

        # Executing the mlc loaded latency cmd
        self._mlc_provider.get_idle_latency(" ", self._cr_provisioning_2lm_mixed_mode.mount_list,
                                            self.MLC_IDLE_LATENCY_OFF_LOG)

        # Step logger end for step 5
        self._test_content_logger.end_step_logger(5, return_val=True)

        # Executing of stream commands on sut linux os for prefetcher OFF
        self.execute_stream_command(self.STREAM_CMD, self.STREAM_1LM_PREFETCH_OFF_LOG, self._stream_execute_path)

        # Step logger start for Step 6
        self._test_content_logger.start_step_logger(6)

        # Changing the prefether knob to enable
        self._bios_util_prfetcher_on.set_bios_knob()

        # Reboot the system
        self.perform_os.reboot(self._reboot_timeout)

        # Verifying the bios knob
        self._bios_util_prfetcher_on.verify_bios_knob()

        # Step logger end for step 6
        self._test_content_logger.end_step_logger(6, return_val=True)

        # Step logger start for Step 7
        self._test_content_logger.start_step_logger(7)

        # Executing of MLC commands on sut linux os for prefetcher On
        self._mlc_provider.execute_mlc_test_with_2_greater_amp_1_error_param("-e", self.MLC_1LM_PREFETCH_ON_LOG)

        # Executing the mlc latency matrix cmd
        self._mlc_provider.get_mlc_latency_info("-e", self.MLC_LATENCY_MATRIX_ON_LOG)

        # Executing the mlc idle latency cmd
        self._mlc_provider.get_mlc_loaded_latency_info("-e", self.MLC_LOADED_LATENCY_ON_LOG)

        # Executing the mlc loaded latency cmd
        self._mlc_provider.get_idle_latency("-e", self._cr_provisioning_2lm_mixed_mode.mount_list,
                                            self.MLC_IDLE_LATENCY_ON_LOG)

        # Step logger end for step 7
        self._test_content_logger.end_step_logger(7, return_val=True)

        # Executing stream command for prefetchers ON
        self.execute_stream_command(self.STREAM_CMD, self.STREAM_1LM_PREFETCH_ON_LOG, self._stream_execute_path)

        # Collecting the post performance data
        post_performance_data_frame = self.create_dimm_performance_result(mode="Post")

        # verify pre DCPMM performance and Post DCPMM performance
        self.verify_pre_post_stress_performance_result(pre_performance_data_frame,
                                                       post_performance_data_frame)

        # Step logger start for Step 8
        self._test_content_logger.start_step_logger(8)

        # Delete the test case id folder from our host if it is exists.
        self._common_content_lib.delete_testcaseid_folder_in_host(test_case_id=self.TEST_CASE_ID)

        # Copying mlc log files sut to host
        self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self._mlc_provider.mlc_path, extension=".log")

        # Copying stream log files sut to host
        log_path_to_parse = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self._stream_execute_path, extension=".log")

        # Step logger end for step 8
        self._test_content_logger.end_step_logger(8, log_path_to_parse)

        # Step logger start for Step 9
        self._test_content_logger.start_step_logger(9)

        # Removing if this folder is available in sut in ROOT path
        self._common_content_lib.execute_sut_cmd("rm -rf {}".format(self.LOG_FOLDER), "To delete log folder",
                                                 self._command_timeout, cmd_path=self.ROOT)

        # Creating a folder to collect all journalctl log var log and dmeg logs
        self._common_content_lib.execute_sut_cmd("mkdir {}".format(self.LOG_FOLDER), "create a log folder",
                                                 self._command_timeout, cmd_path=self.ROOT)

        # Adding journalctl log to log_folder in sut
        journalctl_log_path = Path(os.path.join(self.LOG_FOLDER, "journalctl.log")).as_posix()

        # Executing journalctl cmd to collect the log Check Machine Check Exception logging for mce hardware events
        self._common_content_lib.execute_sut_cmd("journalctl -u mcelog.service  > {}".format(journalctl_log_path),
                                                 "Journalctl command", self._command_timeout)

        # Adding var_log to log_folder in sut
        var_log_messages = Path(os.path.join(self.LOG_FOLDER, "var_log_messages.log")).as_posix()

        # Executing var log cmd to Check the OS logs and look for unexpected warnings and hardware errors
        # such as mcelog events
        self._common_content_lib.execute_sut_cmd("less /var/log/messages > {}".format(var_log_messages),
                                                 "var/log/messages ", self._command_timeout)

        # Adding dmesg log to log_folder in sut
        dmesg_log_path = Path(os.path.join(self.LOG_FOLDER, "dmesg.log")).as_posix()

        # Executing dmesg cmd
        self._common_content_lib.execute_sut_cmd("dmesg  > {}".format(dmesg_log_path), "dmesg log command",
                                                 self._command_timeout)

        # copy the log folder to host.
        log_path_to_parse = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self.LOG_FOLDER, extension=".log")

        # Step logger end for step 9
        self._test_content_logger.end_step_logger(9, log_path_to_parse)

        return self.log_parsing(log_path_to_parse)

    def log_parsing(self, log_file_path_host):
        """
        Verify All mlc and stream logs

        :param log_file_path_host: Host log file path

        :return: True if all log files parsed without any errors else False
        """
        # Step logger start for Step 10
        self._test_content_logger.start_step_logger(10)
        final_result = [
            self._mlc.verify_mlc_log(log_path=os.path.join(log_file_path_host, self.MLC_1LM_PREFETCH_OFF_LOG),
                                     idle_latency=self._idle_latency_threshold,
                                     peak_injection_memory_bandwidth=self._peak_memory_bandwidth_threshold,
                                     memory_bandwidth=self._memory_bandwidth_threshold),

            self._mlc.verify_mlc_log(log_path=os.path.join(log_file_path_host, self.MLC_1LM_PREFETCH_ON_LOG),
                                     idle_latency=self._idle_latency_threshold,
                                     peak_injection_memory_bandwidth=self._peak_memory_bandwidth_threshold,
                                     memory_bandwidth=self._memory_bandwidth_threshold),

            self._mlc.verify_mlc_latency_matrix(
                log_path=os.path.join(log_file_path_host, self.MLC_LATENCY_MATRIX_OFF_LOG),
                idle_latency_threshold_value=self._idle_latency_threshold),

            self._mlc.verify_mlc_latency_matrix(
                log_path=os.path.join(log_file_path_host, self.MLC_LATENCY_MATRIX_ON_LOG),
                idle_latency_threshold_value=self._idle_latency_threshold),

            self._mlc.verify_mlc_loaded_latency(
                log_path=os.path.join(log_file_path_host, self.MLC_LOADED_LATENCY_OFF_LOG),
                loaded_latency_threshold_value=self._loaded_latency_threshold),

            self._mlc.verify_mlc_loaded_latency(
                log_path=os.path.join(log_file_path_host, self.MLC_LOADED_LATENCY_ON_LOG),
                loaded_latency_threshold_value=self._loaded_latency_threshold),

            self._mlc.verify_idle_latency_mlc(log_path=os.path.join(log_file_path_host, self.MLC_IDLE_LATENCY_OFF_LOG),
                                              idle_latency_threshold_value=self._idle_latency_threshold),

            self._mlc.verify_idle_latency_mlc(log_path=os.path.join(log_file_path_host, self.MLC_IDLE_LATENCY_ON_LOG),
                                              idle_latency_threshold_value=self._idle_latency_threshold),

            self.verify_stream_data_linux(
                file_path=os.path.join(log_file_path_host, self.STREAM_1LM_PREFETCH_OFF_LOG)),

            self.verify_stream_data_linux(
                file_path=os.path.join(log_file_path_host, self.STREAM_1LM_PREFETCH_ON_LOG)),

            self._mem_parse_log.parse_log_for_error_patterns(log_path=os.path.join(log_file_path_host,
                                                                                   "journalctl.log")),
            self._mem_parse_log.parse_log_for_error_patterns(
                log_path=os.path.join(log_file_path_host, "var_log_messages.log"), encoding="UTF-8"),
            self._mem_parse_log.parse_log_for_error_patterns(log_path=os.path.join(log_file_path_host, "dmesg.log"))

        ]
        # Step logger end for step 10
        self._test_content_logger.end_step_logger(10, all(final_result))
        return all(final_result)

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(CRPerformanceAppDirectModeIntelMLCStreamLinux, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CRPerformanceAppDirectModeIntelMLCStreamLinux.main() else
             Framework.TEST_RESULT_FAIL)
