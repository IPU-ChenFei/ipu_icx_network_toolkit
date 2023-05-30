#!/usr/bin/env python
##########################################################################
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
##########################################################################
"""
    :diskspd stress test on TD guest:

    Launch a given number of TD guests and run diskspd on each TD guest for prescribed amount of time.
"""

import sys

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.tools_constants import ArtifactoryName, ArtifactoryTools
from src.security.tests.tdx.workloads.tdvm_workload_base_test_windows import TDGuestWorkloadBaseTestWindows
from src.security.tests.common.common_windows import VmOS


class TDGuestDiskspdWindows(TDGuestWorkloadBaseTestWindows):
    """
            This recipe tests TD guest boot and requires the use of a OS supporting TD guest.  The parameters of this
            test can be customized by the settings in the content_configuration.xml.

            Change <memory><diskspd><disk_spd_run_time> to adjust DiskSpd run time.

            :Scenario: Launch one TD guests, initiate DiskSpd on TD guest, run for the
            necessary time to complete the tests, then verify the SUT and the TD guest have not crashed.

            :Phoenix IDs:  22013223688

            :Test steps:

                :1: Launch a TD guest.

                :2: On TD guest, launch DiskSpd.

                :3: Run until DiskSpd tests complete.

            :Expected results: TD guest should boot and DiskSpd test should run to completion with no
            errors on the SUT or TD guest.

            :Reported and fixed bugs:

            :Test functions:

        """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of test case.
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        :return: None
        """
        super(TDGuestDiskspdWindows, self).__init__(test_log, arguments, cfg_opts)

        self._tools_destination_path_in_vm = self.tdx_properties[self.tdx_consts.VM_TOOLS_BASE_LOC]
        self._tool_name_in_artifactory = ArtifactoryName.DictWindowsTools[ArtifactoryTools.DISK_SPD_ZIP_FILE]
        self._tool_base_loc_in_sut = r"C:\\"
        self._tool_process_name = "diskspd"
        self._tool_exe_name = "diskspd.exe"
        self._tool_output_result_file_name = "diskspd-output.txt"
        self._tool_known_results_failures = ["error", "Error"]
        self._bios_log_known_errors_list = ["mcheck", "MCE"]
        self._vm_os = VmOS.WINDOWS
        self._host_tool_folder_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
            self._tool_name_in_artifactory)
        self._tool_run_time = self._common_content_configuration.get_disk_spd_command_time_out()
        self._tool_run_command_in_vm = f'diskspd.exe -c100M -t4 -Sh -d{self._tool_run_time}' \
                                       f' -w50 -L testfile ">" {self._tool_output_result_file_name}'

    def execute(self):
        return super(TDGuestDiskspdWindows, self).execute()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TDGuestDiskspdWindows.main() else Framework.TEST_RESULT_FAIL)
