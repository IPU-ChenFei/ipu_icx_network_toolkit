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
from src.memory.tests.memory_cr.apache_pass.provisioning.cr_provisioning_1lm_100_appdirectinterleaved_dax_windows \
    import CRProvisioning1LM100AppDirectInterleavedDax


class CRMLCPerformanceAppDirect(CrPerformance):
    """
    Glasgow ID: 57935
    1 . Measure memory latencies and bandwidth using MLC on a system with DCPMMs configured with Storage over AppDirect
    DAX partitions in a Microsoft Windows environment
    2 . The Intel® Memory Latency Checker (Intel® MLC) is a tool used to measure memory latencies and b/w with
    increasing load on the system.

    """

    BIOS_CONFIG_FILE = "cr_mlc_performance_appdirect_bios_knobs_57935.cfg"
    TEST_CASE_ID = "G57935"
    MLC_LOG_FOLDER = "MLC_LOGS"
    MLC_1LM_OUT_LOG_FILE_NAME = "1lm_mlc.log"

    _ipmctl_execute_path = None
    _mlc_execute_path = None

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new CRMLCPerformanceAppDirect object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling cr performance init
        super(CRMLCPerformanceAppDirect, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)
        self._cr_provisioning_app_direct_dax = CRProvisioning1LM100AppDirectInterleavedDax(self._log, arguments,
                                                                                           cfg_opts)
        # calling CRProvisioning1LM100AppDirectInterleavedDax
        self._cr_provisioning_app_direct_dax.prepare()
        self._cr_provisioning_app_direct_dax.execute()

        self._idle_latency_threshold = self._common_content_configuration.memory_mlc_idle_lateny_threshold()
        self._peak_memory_bandwidth_threshold = \
            self._common_content_configuration.memory_mlc_peak_memory_bandwidth_threshold()
        self._memory_bandwidth_threshold = self._common_content_configuration.memory_mlc_memory_bandwidth_threshold()

    def prepare(self):
        # type: () -> None
        """
        1. To clear the system event logs
        2. Set the bios knobs as per the test case.
        3. Reboot the SUT to apply the new bios settings.
        4. Verify the bios knobs that are set.
        5. Copy MLC tool to windows SUT.

        :return: None
        :raises: None
        """
        self._windows_event_log.clear_system_event_logs()  # To clear system event logs
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.
        self._ipmctl_execute_path = self._install_collateral.install_ipmctl()
        self._mlc_execute_path = self._install_collateral.install_mlc()

    def execute(self):
        """
        1. Confirm persistent memory regions are configured as expected.
        2. Performance metrics for each DCPMM DIMM.
        3. Run the MLC tool.
        4. Measure idle latency for the each DAX formatted persistent memory filesystem.

        :return: True, if the test case is successful else False.
        """
        final_result = []
        # Persistent memory Drive letters
        drive_letters_cr = self._cr_provisioning_app_direct_dax.store_generated_dcpmm_drive_letters
        # To delete log folder if exists
        self._common_content_lib.windows_sut_delete_folder(self.C_DRIVE_PATH, self.MLC_LOG_FOLDER)
        mlc_log_folder_path = os.path.join(self.C_DRIVE_PATH, self.MLC_LOG_FOLDER)  # Log folder path
        self._common_content_lib.execute_sut_cmd("mkdir {}".format(self.MLC_LOG_FOLDER), "making a directory",
                                                 self._command_timeout, self.C_DRIVE_PATH)
        # To get the DCPMM disk namespaces information.
        self._cr_provisioning_app_direct_dax.dcpmm_get_disk_namespace()

        # Pre DCPMM performance
        pre_stress_df = self.create_dimm_performance_result(mode="Pre")

        mlc_1lm_out_log_file_path = os.path.join(mlc_log_folder_path, self.MLC_1LM_OUT_LOG_FILE_NAME)
        # execute mlc
        command = "mlc.exe > {}".format(mlc_1lm_out_log_file_path)
        self._log.info("Executing mlc command : {}".format(command))
        self._common_content_lib.execute_sut_cmd(
            command, "mlc command", self._mlc_runtime, cmd_path=self._mlc_execute_path)

        # ideal latency for each persistent memory
        log_files_list = self.idle_latency_mlc(mlc_path=self._mlc_execute_path,
                                               mlc_log_folder_path=mlc_log_folder_path,
                                               drive_letters=drive_letters_cr)

        # Post DCPMM performance
        post_stress_df = self.create_dimm_performance_result(mode="Post")

        # verify pre DCPMM performance and Post DCPMM performance
        self.verify_pre_post_stress_performance_result(pre_stress_df, post_stress_df)

        whea_logs = self._windows_event_log.get_whea_error_event_logs()
        # check if there are any errors, warnings of category WHEA found
        if whea_logs is None or len(str(whea_logs)) == 0:
            self._log.info("No WHEA errors or warnings found in Windows System event log...")
            final_result.append(True)
        else:
            self._log.error("Found WHEA errors or warnings in Windows System event log...")
            self._log.error("WHEA error logs: \n" + str(whea_logs))
            final_result.append(False)

        # To get the list of DCPMM disks.
        disk_list = self._cr_provisioning_app_direct_dax.get_dcpmm_disk_list()
        self._cr_provisioning_app_direct_dax.verify_disk_partition(disk_lists=disk_list)  # to verify file systems

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

        self._common_content_lib.delete_testcaseid_folder_in_host(test_case_id=self.TEST_CASE_ID)

        # Copy log files to Host
        log_path_to_parse = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=mlc_log_folder_path, extension=".log")

        final_result.append(self.log_parsing(log_path_to_parse, log_files_list))

        return all(final_result)

    def log_parsing(self, log_path_to_parse, log_files_list):
        """
        This function is used for the verification og logs

        :param log_path_to_parse: Host Log Path
        :param log_files_list: idle latency log files for persistent memory

        return: True if all log files parsed without any errors else False
        """

        final_result = [self._mlc.verify_mlc_log(log_path=os.path.join(log_path_to_parse, "1lm_mlc.log"),
                                                 idle_latency=self._idle_latency_threshold,
                                                 peak_injection_memory_bandwidth=self._peak_memory_bandwidth_threshold,
                                                 memory_bandwidth=self._memory_bandwidth_threshold)]
        for each_log_file in log_files_list:
            each_log_file = os.path.join(log_path_to_parse, each_log_file)
            final_result.append(self._mlc.verify_idle_latency_mlc(
                each_log_file, idle_latency_threshold_value=self._idle_latency_threshold))

        return all(final_result)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CRMLCPerformanceAppDirect.main() else Framework.TEST_RESULT_FAIL)
