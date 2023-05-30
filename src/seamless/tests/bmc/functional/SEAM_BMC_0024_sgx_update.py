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
    :Seamless BMC capsule stage test
    Attempts to send in a SGX ucode patch use to initiate the seamless update
"""


import sys
import time
import os
from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from datetime import datetime, timedelta 
from src.seamless.lib.seamless_common import SeamlessBaseTest

from src.seamless.lib.sgx_common import SgxCommon
from src.seamless.tests.bmc.constants.sgx_constants import SGXConstants


class SEAM_BMC_0024_sgx_update(SgxCommon):

    BIOS_CFG = r"..\configuration\\"

    def __init__(self, test_log, arguments, cfg_opts):
        super(SEAM_BMC_0024_sgx_update, self).__init__(test_log, arguments, cfg_opts)
        self.expected_ver = ""
        self.expected_ucode = arguments.expected_ucode
        self.expected_ucode2 = arguments.expected_ucode2
        self.expected_ucode3 = arguments.expected_ucode3
        self.expected_ucode4 = arguments.expected_ucode4
        self.expected_ucodebase = arguments.expected_ucodebase
        self.expected_svn = arguments.expected_svn
        self.expected_svn2 = arguments.expected_svn2
        self.expected_svn3 = arguments.expected_svn3
        self.expected_svn4 = arguments.expected_svn4
        self.expected_svnbase = arguments.expected_svnbase
        self.capsule = arguments.capsule
        self.capsule2 = arguments.capsule2
        self.capsule3 = arguments.capsule3
        self.capsule4 = arguments.capsule4
        self.sgx_command = arguments.sgx_command
        self.loop_count = arguments.loop
        self.vm_count = arguments.vm_count
        self.sgx_count = arguments.sgx_count
        self.sgx_ucode_patch_count = arguments.patch_count
        self.start_workload = arguments.start_workload
        self.warm_reset = arguments.warm_reset
        self.dc_cycle = arguments.dc_cycle
        self.update_type = arguments.update_type
        self.target_msr = arguments.target_msr
        self.msr_update_value = arguments.msr_update_value
        self.bios_knob = arguments.bios_knob
        self.multi_step_patch = arguments.multi_step_patch
        self.patch_FMS_name = arguments.patch_FMS_name

        
    @classmethod
    def add_arguments(cls, parser):
        super(SEAM_BMC_0024_sgx_update, cls).add_arguments(parser)
        parser.add_argument('--expected_ucode', action='store', help="The ucode version expected to be reported after update", default="")
        parser.add_argument('--expected_svn', action='store', help="The svn version expected to be reported after update", default="")
        parser.add_argument('--expected_ucode2', action='store', help="The ucode version expected to be reported after update", default="")
        parser.add_argument('--expected_svn2', action='store', help="The svn version expected to be reported after update", default="")
        parser.add_argument('--expected_ucode3', action='store', help="The ucode version expected to be reported after update", default="")
        parser.add_argument('--expected_svn3', action='store', help="The svn version expected to be reported after update", default="")
        parser.add_argument('--expected_ucode4', action='store', help="The ucode version expected to be reported after update", default="")
        parser.add_argument('--expected_svn4', action='store', help="The svn version expected to be reported after update", default="")
        parser.add_argument('--expected_ucodebase', action='store', help="The ucode version expected to be reported after update", default="")
        parser.add_argument('--expected_svnbase', action='store', help="The svn version expected to be reported after update", default="") 
        parser.add_argument('--capsule', action='store', help='The path for ucode update patch')
        parser.add_argument('--capsule2', action='store', help='The path for ucode update patch')
        parser.add_argument('--capsule3', action='store', help='The path for ucode update patch')
        parser.add_argument('--capsule4', action='store', help='The path for ucode update patch')
        parser.add_argument('--sgx_command', action='store', help="The sgx cmd to be executed:svn_ver, sgx_update, sgx_checkupdate, sgx_svnupdate, sgx_rollback, launch_sgx_workload, launch_sgx_vm", default="svn_ver")
        parser.add_argument('--loop', type=int, default=1,help="Add argument for # of loops")
        parser.add_argument('--vm_count', type=int, default=1, help="Add argument for # VM's")
        parser.add_argument('--sgx_count', type=int, default=1, help="Add argument for # SGX's")
        parser.add_argument('--patch_count', type=int, default=1, help="Add argument for # ucode patches")
        parser.add_argument('--dc_cycle', action='store_true', help="Add argument if dc cycle to be performed")
        parser.add_argument('--warm_reset', action='store_true', help="Add argument if warm reset to be performed")
        parser.add_argument('--start_workload', action='store_true', help="Add argument if workload need to be started")
        parser.add_argument('--update_type', action='store', help="Specify if efi utility, fit ucode, inband", default="fit_ucode")
        parser.add_argument('--target_msr', type=int, default=1024, help="Add argument for msr to be updated")
        parser.add_argument('--msr_update_value', type=int, default=4094, help="Add argument for msr update value")
        parser.add_argument('--bios_knob', action='store', help="Add argument if BIOS knobs needs to be configured")
        parser.add_argument('--multi_step_patch', action='store_true', help="Add argument if multi stepping patch is used for update")
        parser.add_argument('--patch_FMS_name', action='store', help='The FMS name for ucode update patch')

    def check_capsule_pre_conditions(self):
        # To-Do add capsule pre condition checks
        return True

    def evaluate_workload_output(self, output):
       # To-Do add workload output analysis
        return True;

    def get_current_version(self, echo_version=True):
    # To-Do add workload output analysis
        return True;

    def prepare(self):
        """
        Prepare the setup
        """
        # To-Do add BIOS Knob changes for SGX
        super().prepare()
        if self.bios_knob:
            bios_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CFG + self.bios_knob)
            self.bios_knob_change(bios_enable)
    
    
    def execute(self):
        """
        This function will upgrade/downgrade Ucode patch perform SVN updates in Linux/Windows OS
        :return: True the test case is pass
        """

        result = self.perform_sgx_tcb_recovery()
        return result

    def cleanup(self, return_status):
        """
            This function will stop the VM and make default bios knob if it is set
        """
        super().cleanup(return_status)
 
if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SEAM_BMC_0024_sgx_update.main() else Framework.TEST_RESULT_FAIL)
