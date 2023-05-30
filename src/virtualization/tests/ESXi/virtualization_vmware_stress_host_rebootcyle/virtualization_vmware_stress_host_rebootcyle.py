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

from dtaf_core.lib.dtaf_constants import Framework
import os
import time
import subprocess
import threading
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_exceptions import *
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger


class VirtualizationVmwareStresshostRebootCycles(VirtualizationCommon):
    """
    Phoenix ID: 16012889909
    Purpose of this test case is to continuously perform reboot cycles on host for Stress.
    1. Enable the VT-x and VT-d in BIOS ,  Full memory population
    2. Enable the ESXI shell and SSH. Edit the below file so that reboot script executes automatically on System reboot.
    4. Create the file cycle_number (initially echo 0 ).
    5. Run the reboot ESXI script
    """
    TEST_CASE_ID = ["P16012889909", "Virtualization_VMware_Stress_host_reboot_cycles"]
    LOCAL_FILE = "/etc/rc.local.d/local.sh"
    LOCAL_FILE_DATA = 'sh /vmfs/volumes/datastore1/reboot_esxi.sh & \n' \
                      'exit 0'
    DATASTORE_VMFS = "/vmfs/volumes/datastore1/"
    LOCAL_DIRECTORY = "/etc/rc.local.d/"
    cycle_file_path = "cycle_number"
    STEP_DATA_DICT = {
        1: {'step_details': "Enable the VT-x and VT-d in BIOS ,  Full memory population",
            'expected_results': "Bios knobs installed and verified successfully"},
        2: {'step_details': "Enable the ESXI shell and SSH. Edit the below file so that reboot script executes automatically on System reboot",
            'expected_results': "Should be successfull"},
        3: {'step_details': " Create the file cycle_number (initially echo 0 ).",
            'expected_results': "Creation should be successful"},
        4: {'step_details': "Run the reboot ESXI script",
            'expected_results': "Successfully verified Stress Reboot"},
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationVmwareStresshostRebootCycles object.
        """
        super(VirtualizationVmwareStresshostRebootCycles, self).__init__(test_log, arguments, cfg_opts)
        self.CYCLE_NUMBER = self.DATASTORE_VMFS + self.cycle_file_path
        self._cfg_opts = cfg_opts
        self._log = test_log
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)

    def prepare(self):
        # Need to implement bios configuration for ESXi SUT
        self._test_content_logger.start_step_logger(1)
        if self.os.os_type != OperatingSystems.ESXI:
            raise TestNotImplementedError("Not implemented for {} OS".format(self.os.os_type))
        self._log.info("VMWare ESXi SUT detected for the testcase")
        self._test_content_logger.end_step_logger(1, return_val=True)


    def execute(self):
        """
         1. Enable the VT-x and VT-d in BIOS ,  Full memory population
         2. Enable the ESXI shell and SSH. Edit the below file so that reboot script executes automatically on System reboot.
         3. Create the file cycle_number (initially echo 0 ).
         4. Run the reboot ESXI script
        """
        self._test_content_logger.start_step_logger(2)
        self._common_content_lib.execute_sut_cmd('sed -i "s/exit\s0//g" /etc/rc.local.d/local.sh', "remove exit 0 from local.sh script", self._command_timeout)
        self._common_content_lib.execute_sut_cmd('echo "{}">>{}'.format(self.LOCAL_FILE_DATA, self.LOCAL_FILE),
                                                     "Updating Local file contents", self._command_timeout)
        self.os.copy_local_file_to_sut(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                                    r"reboot_esxi.sh"), self.DATASTORE_VMFS)

        cmd = "chmod 777 reboot_esxi.sh"
        self._common_content_lib.execute_sut_cmd(cmd, "Change execute permission", self._command_timeout,
                                                 self.DATASTORE_VMFS)

        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        cycle_cmd = "echo 0 >{}"
        self._common_content_lib.execute_sut_cmd(cycle_cmd.format(self.CYCLE_NUMBER), "Adding initial value to cyle file",
                                                  self._command_timeout,self.DATASTORE_VMFS)
        self.os.copy_local_file_to_sut(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                                     r"reboot_esxi.sh"),self.DATASTORE_VMFS)

        cmd = "chmod 777 reboot_esxi.sh"
        self._common_content_lib.execute_sut_cmd(cmd, "Change execute permission", self._command_timeout, self.DATASTORE_VMFS)
        cmd2 = "chmod 777 {}"
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        self._common_content_lib.execute_sut_cmd(cmd2.format(self.LOCAL_FILE), "Change execute permission local script", self._command_timeout,
                                                  self.LOCAL_DIRECTORY)
        print("start reboot")
        self._common_content_lib.execute_sut_cmd("sh local.sh", "Running Reboot Test", self._command_timeout,cmd_path=self.LOCAL_DIRECTORY)
        time.sleep(10)
        number_of_cycles =0
        while number_of_cycles <= 1000:
            self.os.wait_for_os(300)
            if self.os.is_alive():
                cmd1 = "cat {}"
                number_of_cycles = self._common_content_lib.execute_sut_cmd(cmd1.format(self.CYCLE_NUMBER),
                                                                            "cat cmd",
                                                                            self._command_timeout,
                                                                            self.DATASTORE_VMFS)
                self._log.info("Os rebooted {} time".format(number_of_cycles))
                number_of_cycles = int(number_of_cycles)
                time.sleep(150)

            else:
                continue
        self._log.info("Reboot cycle worked as expected")

        return True

    def cleanup(self, return_status):
        super(VirtualizationVmwareStresshostRebootCycles, self).cleanup(return_status)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationVmwareStresshostRebootCycles.main()
             else Framework.TEST_RESULT_FAIL)
