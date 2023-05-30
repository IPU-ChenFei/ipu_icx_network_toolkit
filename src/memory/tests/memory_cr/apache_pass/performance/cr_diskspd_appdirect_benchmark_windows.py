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
from src.memory.tests.memory_cr.apache_pass.performance.cr_performance_common import CrPerformance
from src.memory.tests.memory_cr.apache_pass.provisioning.cr_provisioning_common import CrProvisioningTestCommon
from src.memory.tests.memory_cr.apache_pass.provisioning.cr_provisioning_2lm_mixed_mode_25_75_interleaved_block import \
    CRProvisioning2LM25AppDirect75MemoryMode


class CrDiskSpdAppDirectBenchmarkWindows(CrPerformance):
    """
    Glasgow ID: 57908
    Verification of the platform supported DCPMM Peformance capabilities by using DiskSpd tool in a Microsoft Windows OS
    environment.

    1. Configure platform with CPUs, Memory and MS Windows OS.
    2. Configure and execute DskSpd for 15 minutes on each DCPMM file system.
    3. Collect and analyze log output files to confirm performance is as per established expectations.
    4. Verify no unexpected errors were logged while executing tool.

    """

    BIOS_CONFIG_FILE = "cr_diskspd_appdirect_benchmark_windows_bios_knobs.cfg"
    TEST_CASE_ID = "G57908"

    _disk_spd_file_path = None
    _ipmctl_execute_path = None

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new CrDiskSpdAppDirectBenchmarkWindows object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(CrDiskSpdAppDirectBenchmarkWindows, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)

        # calling CRProvisioning2LM25AppDirect75MemoryMode
        self._cr_provisioning_25appdirect = CRProvisioning2LM25AppDirect75MemoryMode(self._log, arguments, cfg_opts)
        self._cr_provisioning_25appdirect.prepare()
        self._cr_provisioning_25appdirect.execute()

    def prepare(self):
        # type: () -> None
        """
        1. Setting the bios knobs to its default mode.
        2. Setting the bios knobs as per the test case.
        3. Rebooting the SUT to apply the new bios settings.
        4. Verifying the bios knobs that are set.
        5. Copy zipped DiskSpd Tool to SUT
        6. Unzip it.

        :return: None
        """

        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.
        self._disk_spd_file_path = self._install_collateral.install_disk_spd()  # To install DiskSpd tool

    def execute(self):
        """
        Function is responsible for the below tasks,

        1. Confirm persistent memory regions are configured as expected.
        2. Performance metrics for each DCPMM DIMM.
        3. Execute DiskSpd as specified in the test case.
        4. Check OS application and system event logs for unexpected errors.
        5. Check Thermal and Media errors on the dimms.

        :return: True, if the test case is successful else false
        :raise: None
        """

        return_value = []

        #  To get the DCPMM disk namespaces information.
        self._cr_provisioning_25appdirect.dcpmm_get_disk_namespace()

        disk_list = self._cr_provisioning_25appdirect.get_dcpmm_disk_list()

        self._log.info("{} DCPMM device(s) attached to this system board {}.".format(len(disk_list), disk_list))

        #  Pre DCPMM performance
        pre_stress_df = self.create_dimm_performance_result(mode="Pre")

        #  Persistent memory Drive letters
        drive_letter_list = self._cr_provisioning_25appdirect.store_generated_dcpmm_drive_letters

        #  Execute DiskSpd command for each Persistent Memory Drives
        disk_spd_log_file_list = []
        for letter in drive_letter_list:
            status, result_file = self.execute_disk_spd_command(letter, self._disk_spd_file_path)
            if status:
                return_value.append(status)
                disk_spd_log_file_list.append(result_file)

        #  delete the TC automation folder
        self._common_content_lib.delete_testcaseid_folder_in_host(test_case_id=self.TEST_CASE_ID)

        #  copy files DiskSpd log files to SUT
        for file in disk_spd_log_file_list:
            disk_spd_host_folder_path = self._common_content_lib.copy_log_files_to_host(
                test_case_id=self.TEST_CASE_ID, sut_log_files_path=self._disk_spd_file_path, extension=".txt")
            disk_spd_host_file_path = os.path.join(disk_spd_host_folder_path, file)
            #  Verify the DiskSpd log file for each drive with the base one
            return_value.append(self.verify_disk_spd_data(disk_spd_host_file_path))

        #  Pre DCPMM performance
        post_stress_df = self.create_dimm_performance_result(mode="Post")

        #  verify pre DCPMM performance and Post DCPMM performance
        return_value.append(self.verify_pre_post_stress_performance_result(pre_stress_df, post_stress_df))

        whea_logs = self._windows_event_log.get_whea_error_event_logs()
        #  check if there are any errors, warnings of category WHEA found
        if whea_logs is None or len(str(whea_logs)) == 0:
            self._log.info("No WHEA errors or warnings found in Windows System event log...")
            return_value.append(True)
        else:
            self._log.error("Found WHEA errors or warnings in Windows System event log...")
            self._log.error("WHEA error logs: \n" + str(whea_logs))
            return_value.append(False)

        #  To get the list of DCPMM disks.
        disk_list = self._cr_provisioning_25appdirect.get_dcpmm_disk_list()
        self._cr_provisioning_25appdirect.verify_disk_partition(disk_lists=disk_list)  # to verify file systems

        #  To display thermal errors
        thermal_error_data = self._common_content_lib.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_ERROR_THERMAL, "To display thermal errors",
            self._command_timeout, self._ipmctl_execute_path)
        self._log.info("Thermal error data \n{}".format(thermal_error_data))

        #  To display media errors
        media_error_data = self._common_content_lib.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_ERROR_MEDIA, "To display Media errors",
            self._command_timeout, self._ipmctl_execute_path)
        self._log.info("Media error data \n{}".format(media_error_data))

        return all(return_value)


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if CrDiskSpdAppDirectBenchmarkWindows.main() else Framework.TEST_RESULT_FAIL)
