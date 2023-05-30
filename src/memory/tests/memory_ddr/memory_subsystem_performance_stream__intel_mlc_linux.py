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
import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.memory.tests.memory_ddr.ddr_common import DDRCommon
from src.lib.bios_util import BiosUtil


class MemorySubsystemPerformanceMlcStreamLinux(DDRCommon):
    """
    Glasgow ID: 63300
    This Test Case is to Measure memory latencies and bandwidth using the MLC and Stream benchmarks.
    1. The tests are executed on a system configured with DDR DIMMs with specific platform BIOS settings.
    2. Results are also taken with CPU prefetchers enabled and disabled.
    3. STREAM is the de facto industry standard benchmark for measuring sustained memory bandwidth in MB.
    4.The Memory Latency Checker (MLC) test tool is now available externally and is method of measuring delay
        in the memory subsystem as a function of memory bandwidth.
    """
    _bios_config_file = "memory_bios_knobs_subsystem_prefetchers_disabled.cfg"
    _prefetcher_bios_config_file = "memory_bios_knobs_subsytem_prefetchers_enabled.cfg"
    TEST_CASE_ID = "G63300"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new StressTestRebootFastBootEn object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(MemorySubsystemPerformanceMlcStreamLinux, self).__init__(test_log, arguments, cfg_opts,
                                                                       self._bios_config_file)

        bios_config_file_path = self.get_bios_config_file_path(self._prefetcher_bios_config_file)
        self._new_bios_config_file = BiosUtil(cfg_opts, bios_config_file_path, self._bios, self._log, self._common_content_lib)

    def prepare(self):
        # type: () -> None
        """
        1. Setting the bios knobs to its default mode.
        2. Setting the bios knobs as per the test case.
        3. Rebooting the SUT to apply the new bios settings.
        4. Verifying the bios knobs that are set.
        5. Clear os and dmesg logs

        :return: None
        """
        self._bios.default_bios_settings()  # To set the Bios Knobs to its default mode.
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.
        self._common_content_lib.clear_os_log()  # To clear os logs
        self._common_content_lib.clear_dmesg_log()  # To clear dmesg logs
        self.mlc_read_write_register()  # Load msr driver to read specific register

    def execute(self):
        """
        1. Install mlc  and stream tool
        1. Run mlc tool and verify mlc logs with prefetcher disabled bios knobs
        2. Run Stream and verify stream logs with prefetcher disabled bios knobs
        3. create dmesg and mce logs
        3. Log parsing to verify error

        :return: True if all log files parsed without any errors else false
        """
        return_value = []
        # To install mlc tool in SUT
        self._mlc_extract_path = self._install_collateral.install_mlc()
        self._common_content_lib.execute_sut_cmd("chmod +x mlc", "Assigning executable privledges ",
                                                 self._command_timeout, self._mlc_extract_path)

        #  Run MLC Tool in SUT
        self.execute_mlc_test_linux(self._mlc_extract_path)
        self._common_content_lib.delete_testcaseid_folder_in_host(test_case_id=self.TEST_CASE_ID)
        log_path_to_parse = self._common_content_lib.copy_log_files_to_host(test_case_id=self.TEST_CASE_ID,
                                                                            sut_log_files_path=self._mlc_extract_path,
                                                                            extension=".log")

        mlc_log_path = os.path.join(log_path_to_parse, "ddr4_prefetch_mlc.log")

        #  Verify mlc log data
        return_value.append(self._mlc_utils.verify_mlc_log_with_template_data(mlc_log_path))

        # To install Stream tool in SUT
        self._stream_extract_path = self._install_collateral.install_stream_tool()

        #  To run Stream file in SUT
        self.execute_stream_test_linux(self._stream_extract_path)
        self._common_content_lib.delete_testcaseid_folder_in_host(test_case_id=self.TEST_CASE_ID)
        log_path_to_parse = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self._stream_extract_path, extension=".log")

        stream_log_path = os.path.join(log_path_to_parse, "ddr4_prefetch_stream.log")

        #  To verify Stream data
        self.verify_stream_data(stream_log_path)

        #  To apply prefetcher enabled bios settings
        self._bios.default_bios_settings()  # To set the Bios Knobs to its default mode.
        self._new_bios_config_file.set_bios_knob()  # To set the  new bios knob setting.
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
        self._new_bios_config_file.verify_bios_knob()  # To verify the bios knob settings.
        self.mlc_read_write_register()

        #  Run MLC Tool in SUT
        self.execute_mlc_test_linux(self._mlc_extract_path)
        self._common_content_lib.delete_testcaseid_folder_in_host(test_case_id=self.TEST_CASE_ID)
        log_path_to_parse = self._common_content_lib.copy_log_files_to_host(test_case_id=self.TEST_CASE_ID,
                                                                            sut_log_files_path=self._mlc_extract_path,
                                                                            extension=".log")
        mlc_log_path = os.path.join(log_path_to_parse, "ddr4_prefetch_mlc.log")

        #  Verify mlc log data
        return_value.append(self._mlc_utils.verify_mlc_log_with_template_data(mlc_log_path))

        #  To Run Stream file in SUT
        self.execute_stream_test_linux(self._stream_extract_path)

        self._common_content_lib.delete_testcaseid_folder_in_host(test_case_id=self.TEST_CASE_ID)
        log_path_to_parse = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self._stream_extract_path, extension=".log")
        stream_log_path = os.path.join(log_path_to_parse, "ddr4_prefetch_stream.log")

        #  To verify Stream data
        self.verify_stream_data(stream_log_path)

        self._common_content_lib.create_dmesg_log()
        self._common_content_lib.create_mce_log()
        self._common_content_lib.delete_testcaseid_folder_in_host(test_case_id=self.TEST_CASE_ID)
        log_path_to_parse = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self.LINUX_USR_ROOT_PATH, extension=".log")

        return self.log_parsing_stream_mlc_app_test(log_file_path=log_path_to_parse)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MemorySubsystemPerformanceMlcStreamLinux.main() else
             Framework.TEST_RESULT_FAIL)
