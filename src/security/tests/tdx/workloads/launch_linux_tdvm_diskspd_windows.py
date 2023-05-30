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
    :diskspd stress test on Linux TD guest:

    Launch a given number of Linux TD guests and run diskspd on each TD guest for prescribed amount of time.
"""

import sys

from dtaf_core.lib.dtaf_constants import Framework

from src.security.tests.tdx.workloads.tdvm_workload_base_test_windows import TDGuestWorkloadBaseTestWindows
from src.security.tests.common.common_windows import VmOS


class LinuxTDGuestDiskspdWindows(TDGuestWorkloadBaseTestWindows):
    """
            This recipe tests Linux TD guest boot and requires the use of a OS supporting TD guest.  The parameters of
            this test can be customized by the settings in the content_configuration.xml.

            Change <security><diskspd> to control the number of seconds that diskspd will be run for.

            :Scenario: Launch one TD guest, initiate diskspd on TD guest, run for the
             prescribed amount of time per above parameters, then verify the SUT and the TD guests have not crashed.

            :Phoenix ID: 14015392755

            :Test steps:

                :1: Launch a Linux TD guest.

                :2: On Linux TD guest, launch diskspd.

                :3: Run for prescribed amount of time (refer to beginning of this section for how to change the time).

            :Expected results: TD guest should boot and diskspd should run for the prescribed amount of time with
            no errors on the SUT or any of the Linux TD guests.

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
        super(LinuxTDGuestDiskspdWindows, self).__init__(test_log, arguments, cfg_opts)

        self._tools_destination_path_in_vm = r"/home/administrator"
        self._tool_name_in_artifactory = "diskspd-for-linux-master.zip"
        self._tool_base_loc_in_sut = r"C:\\"
        self._tool_process_name = "diskspd"
        self._tool_exe_name = "diskspd"
        self._tool_output_result_file_name = "diskspd-output.txt"
        self._tool_known_results_failures = ["error", "Error"]
        self._bios_log_known_errors_list = ["mcheck", "MCE"]
        self._vm_os = VmOS.LINUX
        self._tool_run_async = True
        self._host_tool_folder_path = self._artifactory_obj.download_tool_to_automation_tool_folder(self._tool_name_in_artifactory)
        self._tool_run_time = self._common_content_configuration.get_disk_spd_command_time_out()
        self._tool_run_command_in_vm = f'diskspd -c100M -t4 -Sh -d{self._tool_run_time}' \
                                       f' -w50 -L testfile > {self._tool_output_result_file_name}'
        self._software_pkg_lists = [f"echo {self.vm_user_pwd} | sudo -S apt-get install net-tools",
                                    f"echo {self.vm_user_pwd} | sudo -S apt-get update",
                                    f"echo {self.vm_user_pwd} | sudo -S apt-get install libaio-dev",
                                    f"echo {self.vm_user_pwd} | sudo -S apt install -y  build-essential",
                                    f"echo {self.vm_user_pwd} | sudo -S apt install make",
                                    f"echo {self.vm_user_pwd} | sudo -S apt install -y make-guile",
                                    ]
        command = f"cd /home/administrator/diskspd/diskspd-for-linux-master; echo {self.vm_user_pwd} | "\
                  f"sudo -S make && make install; echo {self.vm_user_pwd} | sudo -S cp bin/diskspd /usr/local/bin/"
        self._tool_source_code_bld_cmd_list.append(command)

    def execute(self):
        return super(LinuxTDGuestDiskspdWindows, self).execute()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if LinuxTDGuestDiskspdWindows.main() else Framework.TEST_RESULT_FAIL)
