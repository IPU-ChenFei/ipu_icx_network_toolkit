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
from src.memory.tests.memory_ddr.ddr_common import DDRCommon


class MemorySubsystemPerformanceIntelMLCWindows(DDRCommon):
    """
    Glasgow ID: 63299
    This Test Case is to measure memory latencies and bandwidth using the MLC benchmark...
    1. The tests are executed on a system configured with DDR DIMMs only with specific platform BIOS settings.
    2. The Memory Latency Checker (MLC) test tool is now available externally and is method of measuring delay in the
    memory subsystem as a function of memory bandwidth.
    3. The MLC tool disables the CPU prefetchers during execution.
    """
    _bios_config_file = "memory_bios_knobs_subsystem_performance.cfg"
    TEST_CASE_ID = "G63299"
    MLC_OUT_LOG_FILE_NAME = "ddr4_mlc.log"
    _mlc_execute_path = None

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new StressTestRebootFastBootEn object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(MemorySubsystemPerformanceIntelMLCWindows, self).__init__(test_log, arguments, cfg_opts,
                                                                        self._bios_config_file)

    def prepare(self):
        # type: () -> None
        """
        1. Setting the bios knobs to its default mode.
        2. Setting the bios knobs as per the test case.
        3. Rebooting the SUT to apply the new bios settings.
        4. Verifying the bios knobs that are set.

        :return: None
        """
        pre_bios_memory_value = self.get_total_memory_win()  # To get the Pre Bios Total Memory
        self._windows_event_log.clear_system_event_logs()  # To clear system event logs
        self._bios_util.load_bios_defaults()  # # To set the Bios Knobs to its default mode
        self._bios_util.set_bios_knob()  # To set the bios knob setting
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the Bios knob value set
        post_bios_memory_value = self.get_total_memory_win()  # To get the Post Bios Total Memory
        self.compare_memtotal(pre_bios_memory_value, post_bios_memory_value)  # To compare Pre and Post Bios MemTotal
        self._mlc_execute_path = self._install_collateral.install_mlc()

    def execute(self):
        """
        Run the MLC tool and get the Log file and compare the data with the Template log file

        :return: True, if the test case is successful.
        """
        final_result = []

        #  To delete Test Case ID folder if exists
        self._common_content_lib.delete_testcaseid_folder_in_host(test_case_id=self.TEST_CASE_ID)

        #  Run MLC Tool
        final_result.append(self.run_mlc_windows(self._mlc_execute_path))

        mlc_log_folder_path = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self._mlc_execute_path, extension=".log")

        #  Verify MLC Log file
        final_result.append(self.verify_mlc_log(os.path.join(mlc_log_folder_path, self.MLC_OUT_LOG_FILE_NAME)))

        whea_logs = self._windows_event_log.get_whea_error_event_logs()
        # check if there are any errors, warnings of category WHEA found
        if whea_logs is None or len(str(whea_logs)) == 0:
            self._log.info("No WHEA errors or warnings found in Windows System event log...")
            final_result.append(True)
        else:
            self._log.error("Found WHEA errors or warnings in Windows System event log...")
            self._log.error("WHEA error logs: \n" + str(whea_logs))
            final_result.append(False)

        return all(final_result)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MemorySubsystemPerformanceIntelMLCWindows.main() else
             Framework.TEST_RESULT_FAIL)
