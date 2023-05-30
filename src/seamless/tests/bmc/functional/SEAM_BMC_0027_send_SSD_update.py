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
    :Seamless SSD update

    Attempts to send in an SSD FW use to initiate the seamless update
"""
import os
import random
import sys
import ntpath
import time

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.seamless.lib.ssd_common import SsdCommon
from src.seamless.tests.bmc.constants.ssd_constants import SsdWindows, TimeDelay

class SEAM_BMC_0027_send_SSD_update(SsdCommon):

    BIOS_CFG = r"..\configuration\\"

    def __init__(self, test_log, arguments, cfg_opts):
        super().__init__(test_log, arguments, cfg_opts)
        self.expected_ver = arguments.expected_ver
        self.warm_reset = arguments.warm_reset
        self.activation = False
        self.sps_mode = arguments.sps_mode
        self.update_type = None
        self.ssd_serial_number = self._common_content_configuration.get_ssd_serial_number()
        self.ssd_path = None
        self.ssd_part = None
        self.capsule_path = arguments.capsule_path
        self.expected_ver = arguments.expected_ver
        self.capsule_path2 = arguments.capsule_path2
        self.expected_ver2 = arguments.expected_ver2
        self.get_device_name_path()
        version = self.get_current_version()
        self._log.info(f"SSD version: {version}")
        self.fio = arguments.fio
        self.vm = arguments.vm
        self.fio_cmd = self._common_content_configuration.get_fio_cmd()
        self.bios_knob = arguments.bios_knob
        self.drive_letter = self._common_content_configuration.get_drive_letter()
        self.win_vm_name = self._common_content_configuration.get_win_vm_name()
        self.iometer_tool_path = self._common_content_configuration.get_iometer_tool_path()
        self.loop_count = arguments.loop
        self.iometer = arguments.iometer
        self.hyperv = arguments.hyperv
        self.seed_value = arguments.seed_value
        self.ptu = arguments.ptu
        self.socwatch = arguments.socwatch
        self.cc6_value = arguments.cc6_value
        self.c0_value = arguments.c0_value
        self.c6_value = arguments.c6_value
        self.ptu_cmd = arguments.ptu_cmd
        self.ptu_tool_lin = self._common_content_configuration.get_ptu_lin_tool_file_path()
        self.ptu_tool_win = self._common_content_configuration.get_ptu_win_tool_file_path()
        self.csv_file_path = os.path.join(self.log_dir, "PTU")
        os.makedirs(self.csv_file_path)

    @classmethod
    def add_arguments(cls, parser):
        parser.add_argument('--capsule_path', action='store',
                            help="Path to the capsule to be used for the update",
                            default="")
        parser.add_argument('--capsule_path2', action='store',
                            help="Path to the 2nd capsule to be used for the update",
                            default="")
        parser.add_argument('--expected_ver', action='store',
                            help="The version expected to be reported after update",
                            default="")
        parser.add_argument('--expected_ver2', action='store',
                            help="The version expected to be reported after update",
                            default="")
        parser.add_argument('--sps_mode', action='store_true',
                            help="Add argument to check sps mode")
        parser.add_argument('--warm_reset', action='store_true',
                            help="Add argument if warm reset to be performed")
        parser.add_argument('--fio', action='store_true',
                            help="Add argument if fio workload to be performed")
        parser.add_argument('--vm', action='store',
                            help="Add argument if VM workload to be performed with Vm name")
        parser.add_argument('--bios_knob', action='store',
                            help="Add argument if VM workload to be performed with Vm "
                                                              "name")
        parser.add_argument('--loop', type=int, default=1,
                            help="Add argument for # of loops")
        parser.add_argument('--iometer', action='store_true',
                            help="Add argument if iometer tool to be installed")
        parser.add_argument('--hyperv', action='store_true',
                            help="Add argument if hyperv to be created and running")
        parser.add_argument('--seed_value', type=int, default=None,
                            help="Add argument for seed value")
        parser.add_argument('--ptu', action='store_true',
                            help="Add argument if ptu tool to be run")
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
        """
        This function will get the current version of  SSD
        :return: ssd version
        """
        if self._os_type != OperatingSystems.LINUX:
            self._log.info("Get the Physical Disk Details")
            disk_details = self.run_ssh_command(SsdWindows.PHYSIVAL_DISK_CMD, log_output=False)
            self._log.info("Physical Disk details for {}".format(disk_details.stdout))
            if disk_details.stderr:
                raise RuntimeError("Unable to get the ssd firmware version")
            return disk_details.stdout
        else:
            cmd = r'smartctl -i {}'.format(self.device_path)
            result = self.run_ssh_command(cmd, log_output=False)
            for line in result.stdout.splitlines():
                if "Firmware Version:" in line:
                    version = line.split(":")
                    if len(version) > 1:
                        version = version[1].strip()
                    else:
                        raise RuntimeError(" Not able to detect ssd version")
                    return version
            raise RuntimeError(" Not able to detect ssd version")

    def prepare(self):
        """
        Prepare the setup
        """
        super().prepare()
        self.ssd_prepare(self.device_name, self.device_path, self.capsule_path)
        if self.bios_knob:
            bios_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                       self.BIOS_CFG + self.bios_knob)
            self.bios_knob_change(bios_enable)

    def execute(self):
        """
        This function will upgrade/downgrade the SSD FW and Create VM in Linux/Windows OS
        :return: True the test case is pass
        """
        result = None
        self._log.info("ssd_serial number: {}".format(self.ssd_serial_number))
        self.pre_update(self.device_name)
        for count in range(self.loop_count):
            self._log.info("Loop Number:{}".format(count))
            if self._os_type != OperatingSystems.WINDOWS:
                if self.capsule_path:
                    # Assumes NUC is Windows-based. Might be wise to check this.
                    filename = ntpath.basename(self.capsule_path)
                    result = self.update_ssd(self.device_name, "/root/" + filename,
                                             self.expected_ver)
                if self.capsule_path2:
                    # Assumes NUC is Windows-based. Might be wise to check this.
                    filename = ntpath.basename(self.capsule_path2)
                    result = self.update_ssd(self.device_name, "/root/" + filename,
                                             self.expected_ver2)
            else:
                if self.capsule_path:
                    result = self.update_ssd(self.device_name, self.capsule_path, self.expected_ver)
                if self.capsule_path2:
                    result = self.update_ssd(self.device_name, self.capsule_path2,
                                             self.expected_ver2)
        self.post_update()
        return result

    def cleanup(self, return_status):
        """
            This function will stop the VM and make default bios knob if it is set
        """
        super().cleanup(return_status)
        if self.vm:
            if self._os_type != OperatingSystems.WINDOWS:
                self.stop_vm_linux(self.vm)
            else:
                self.stop_hyperv_vm(self.win_vm_name)
        if self.bios_knob:
            self.bios_util.load_bios_defaults()
            self.sut_ssh.reboot(timeout=self.WARM_RESET_TIMEOUT)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SEAM_BMC_0027_send_SSD_update.main()
             else Framework.TEST_RESULT_FAIL)
