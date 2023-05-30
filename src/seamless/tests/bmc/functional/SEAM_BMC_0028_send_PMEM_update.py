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
"""
    :Seamless PMEM update

    Attempts to send in an PMEM FW use to initiate the seamless update
"""
import os
import sys
import time

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.seamless.lib.pmem_common import PmemCommon

class SEAM_BMC_0028_send_PMEM_update(PmemCommon):

    BIOS_CFG = r"..\configuration\\"

    def __init__(self, test_log, arguments, cfg_opts):
        super().__init__(test_log, arguments, cfg_opts)
        self.expected_ver = arguments.expected_ver
        self.warm_reset = arguments.warm_reset
        self.dc_reset = arguments.dc_cycle
        self.ac_reset = arguments.ac_cycle
        self.activation = False
        self.sps_mode = arguments.sps_mode
        self.update_type = None
        self.capsule_name = arguments.capsule_name
        self.expected_ver = arguments.expected_ver
        self.capsule_name2 = arguments.capsule_name2
        self.expected_ver2 = arguments.expected_ver2
        self.bios_knob = arguments.bios_knob
        self.fio = arguments.fio
        self.loop_count = arguments.loop
        self.ipmctl_centos_zip = self._common_content_configuration.get_ipmctl_tool_path_centos_zip()
        self.vm = arguments.vm
        self.hyperv = arguments.hyperv
        self.ipmctl_windows_zip = self._common_content_configuration.get_ipmctl_tool_path_windows_zip()
        self.nvdimmutil_windows_zip = self._common_content_configuration.get_nvdimmutil_tool_path_windows_zip()
        self.windows_sut_root_path = self._common_content_configuration.get_windows_sut_root_path()
        self.win_vm_name = self._common_content_configuration.get_win_vm_name()
        self.ipmctl_tool_file = self._common_content_configuration.get_ipmctl_tool_file()
        self.dsaworkload = arguments.dsa
        self.ptu = arguments.ptu
        self.socwatch = arguments.socwatch
        self.cc6_value = arguments.cc6_value
        self.c0_value = arguments.c0_value
        self.c6_value = arguments.c6_value
        self.ptu_cmd = arguments.ptu_cmd
        self.ptu_tool_lin = self._common_content_configuration.get_ptu_lin_tool_file_path()
        self.ptu_tool_win = self._common_content_configuration.get_ptu_win_tool_file_path()
        self.socwatch_tool_lin = self._common_content_configuration.get_socwatch_lin_tool_file_path()
        self.socwatch_tool_win = self._common_content_configuration.get_socwatch_win_tool_file_path()
        self.csv_file_path = os.path.join(self.log_dir, "PTU")
        os.makedirs(self.csv_file_path)
        self.ezfio_tool_path = self._common_content_configuration.get_ezfio_tool_path()
        self.dsa_windows_zip = self._common_content_configuration.get_dsa_tool_file_path()
        self.dsa_sut_path = self._common_content_configuration.get_sut_path_linux()
        self.dsa_file_name_pmem = self._common_content_configuration.get_dsa_file_name_pmem()
        # self.timeout.dsa = self._common_content_configuration.get_dsa_timeout()

    @classmethod
    def add_arguments(cls, parser):
        super(SEAM_BMC_0028_send_PMEM_update, cls).add_arguments(parser)
        parser.add_argument('--capsule_name', action='store', help="Path to the capsule to be used for the update",
                            default="")
        parser.add_argument('--capsule_name2', action='store', help="Path to the 2nd capsule to be used for the update",
                            default="")
        parser.add_argument('--expected_ver', action='store', help="The version expected to be reported after update",
                            default="")
        parser.add_argument('--expected_ver2', action='store', help="The version expected to be reported after update",
                            default="")
        parser.add_argument('--sps_mode', action='store_true', help="Add argument to check sps mode")
        parser.add_argument('--warm_reset', action='store_true', help="Add argument if warm reset to be performed")
        parser.add_argument('--dc_cycle', action='store_true', help="Add argument if dc cycle to be performed")
        parser.add_argument('--ac_cycle', action='store_true', help="Add argument if ac cycle to be performed")
        parser.add_argument('--bios_knob', action='store', help="Add argument if VM workload to be performed with Vm "
                                                              "name")
        parser.add_argument('--loop', type=int, default=1, help="Add argument for # of loops")
        parser.add_argument('--fio', action='store_true', help="Add argument if fio workload to be performed")
        parser.add_argument('--vm', action='store', help="Add argument if VM workload to be performed with Vm name")
        parser.add_argument('--hyperv', action='store_true', help="Add argument if hyperv to be created and running")
        parser.add_argument('--dsa', action='store_true', help="Add argument if dsa workload to be created and running")
        parser.add_argument('--ptu', action='store_true', help="Add argument if ptu stress to be performed")
        parser.add_argument('--socwatch', action='store_true', help="Add argument if socwatch workload to be performed")
        parser.add_argument('--cc6_value', action='store', help="Add argument if cc6 workload to be performed")
        parser.add_argument('--c0_value', action='store', help="Add argument if c0  workload to be performed")
        parser.add_argument('--c6_value', action='store', help="Add argument if c6  workload to be performed")
        parser.add_argument('--ptu_cmd', action='store', help="Add argument if ptu  stress to be performed")

    def check_capsule_pre_conditions(self):
        # To-Do add capsule pre condition checks
        return True

    def evaluate_workload_output(self, output):
        # To-Do add workload output analysis
        return True

    def get_current_version(self, echo_version=True):
        pass

    def prepare(self):
        """
        Prepare the setup
        """
        super().prepare()
        if self.bios_knob:
            bios_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CFG + self.bios_knob)
            self.bios_knob_change(bios_enable)
        self.pmem_prepare()

    def execute(self):
        """
        This function will upgrade/downgrade the PMEM FW and Create VM in Linux/Windows OS
        :return: True the test case is pass
        """
        result = None
        self.pmem_pre_update()
        for count in range(self.loop_count):
            self._log.info("Loop Number:{}".format(count))
            if self.capsule_name:
                result = self.pmem_execute(self.file_sut_path, self.expected_ver)
            if self.capsule_name2:
                result = self.pmem_execute(self.file_sut_path2, self.expected_ver2)
        self.pmem_post_update()
        return result

    def cleanup(self, return_status):
        super().cleanup(return_status)
        if self.vm:
            if self._os_type != OperatingSystems.WINDOWS:
                self.stop_vm_linux(self.vm)
        if self.hyperv:
            self.stop_hyperv_vm(self.win_vm_name)
        if self.fio:
            self.stop_workloads_lin()
            self.kill_fio()

        if self.bios_knob:
            self.bios_util.load_bios_defaults()
            self.sut_ssh.reboot(timeout=self.WARM_RESET_TIMEOUT)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SEAM_BMC_0028_send_PMEM_update.main() else Framework.TEST_RESULT_FAIL)
