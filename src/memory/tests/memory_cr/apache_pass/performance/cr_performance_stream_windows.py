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
from src.memory.tests.memory_cr.apache_pass.performance.cr_performance_common import CrPerformance
from src.memory.tests.memory_cr.apache_pass.provisioning.cr_provisioning_2lm_100_memory_mode \
    import CRProvisioning2LM100MemoryMode


class CRPerformanceStreamWindows(CrPerformance):
    """
    Glasgow ID: 57936
    1. Usage & Benchmark testing as part of the (SAT) System Acceptance Testing on a Microsoft Windows OS.
    2. STREAM is the de facto industry standard benchmark for measuring sustained memory bandwidth in MB\S.
    3. This test can be applied to both memory mode and AppDirect mode. When run in 2LM 100% memory mode, the DCPMMs
    are used for memory.

    """

    BIOS_CONFIG_FILE = "cr_performance_stream_windows.cfg"
    TEST_CASE_ID = "G57936"
    STREAM_OPT_FILES = ["aa_stream_duv.out",
                        "aa_stream_v2.out"]

    _ipmctl_execute_path = None
    _stream_execute_path = None

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new CRMLCPerformanceAppDirect object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling cr performance init
        super(CRPerformanceStreamWindows, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)

        # calling CRProvisioning2LM100MemoryMode
        self._cr_provisioning_memory_mode = CRProvisioning2LM100MemoryMode(self._log, arguments, cfg_opts)
        self._log.info("Start of 2LM 100% Memory Mode Windows Provisioning TestCase. [Glasgow ID: 57207]")
        self._cr_provisioning_memory_mode.prepare()
        self._cr_provisioning_memory_mode.execute()
        self._log.info("End of 2LM 100% Memory Mode Windows Provisioning TestCase. [Glasgow ID: 57207]")

    def prepare(self):
        # type: () -> None
        """
        1. To clear the system event logs
        2. Set the bios knobs as per the test case.
        3. Reboot the SUT to apply the new bios settings.
        4. Verify the bios knobs that are set.
        5. Copy IPMCTL tool to Windows SUT.
        5. Copy Stream tool to windows SUT.

        :return: None
        :raises: None
        """
        self._windows_event_log.clear_system_event_logs()  # To clear system event logs
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.
        self._ipmctl_execute_path = self._install_collateral.install_ipmctl()  # To install IPMCTL tool in SUT
        self._stream_execute_path = self._install_collateral.install_stream_tool()  # To install Stream_MP tool in SUT

    def execute(self):
        """
        1. Run Stream_MP tool
        2. Verify the Stream Output logs.
        3. Verify EventViewer for Errors
        4. Check for Thermal and Media errors

        :return: True, if the test case is successful else False.
        """
        final_result = []

        #  Execute supporting files for Stream_MP
        self.execute_stream_supported_files_win(self._stream_execute_path)

        # Execute Stream_MP test tool
        final_result.append(self.execute_stream_mp_tool_win(self._stream_execute_path))

        # Delete the if existing TestCaseID folder is present in HOST
        self._common_content_lib.delete_testcaseid_folder_in_host(test_case_id=self.TEST_CASE_ID)

        # Copy log files to Host
        log_path_to_parse = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self._stream_execute_path, extension=".out")

        # Verify Stream_Mp logs
        for stream_opt_file in self.STREAM_OPT_FILES:
            log_file_path_to_parse = os.path.join(log_path_to_parse, stream_opt_file)
            final_result.append(self.verify_stream_opt_logs(log_file_path_to_parse))

        # Creating a data frame with dimm information and adding extra columns as per our test case need.
        dimm_show = self._cr_provisioning_memory_mode.populate_memory_dimm_information(self._ipmctl_executer_path)

        # Get the list of dimms which are healthy and log them.
        self._cr_provisioning_memory_mode.get_list_of_dimms_which_are_healthy()

        # Verify the list of dimms which are healthy are matching with the pmem disk output.
        self._cr_provisioning_memory_mode.verify_all_dcpmm_dimm_healthy()

        # Verify the firmware version of each dimms are matching with the pmem disk output.
        self._cr_provisioning_memory_mode.verify_dimms_firmware_version()

        # Verify the device location of each dimms are matching with the pmem disk output.
        self._cr_provisioning_memory_mode.verify_dimms_device_locator()

        # Verify event viewer logs
        whea_logs = self._windows_event_log.get_whea_error_event_logs()
        # check if there are any errors, warnings of category WHEA found
        if whea_logs is None or len(str(whea_logs)) == 0:
            self._log.info("No WHEA errors or warnings found in Windows System event log...")
            final_result.append(True)
        else:
            self._log.error("Found WHEA errors or warnings in Windows System event log...")
            self._log.error("WHEA error logs: \n" + str(whea_logs))
            final_result.append(False)

        # To display thermal errors
        thermal_error_data = self._common_content_lib.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_ERROR_THERMAL, "To display thermal errors",
            self._command_timeout, self._ipmctl_execute_path)
        self._log.info("Thermal error data \n{}".format(thermal_error_data))

        # To display media errors
        media_error_data = self._common_content_lib.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_ERROR_MEDIA, "To display Media errors",
            self._command_timeout, self._ipmctl_execute_path)
        self._log.info("Media error data \n{}".format(media_error_data))

        return all(final_result)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CRPerformanceStreamWindows.main() else Framework.TEST_RESULT_FAIL)
