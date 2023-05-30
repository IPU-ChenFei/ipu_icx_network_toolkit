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

    Attempts to send in an sps capsule use to initiate the seamless update
"""
import sys
import time
from datetime import datetime, timedelta
from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.seamless.lib.seamless_common import SeamlessBaseTest

class SEAMBMC0011sendssdupdate(SeamlessBaseTest):

    def __init__(self, test_log, arguments, cfg_opts):
        super(SEAMBMC0011sendssdupdate, self).__init__(test_log, arguments, cfg_opts)
        self.SSD_path = arguments.SSD_path
        self.expected_ver = arguments.expected_ver
        self.warm_reset = arguments.warm_reset
        self.fio = arguments.fio
        self.start_workload_command = self._workload_path + "StartWorkloads.ps1 " + self._powershell_credentials
        self.stop_workload_command = self._workload_path + "StopWorkloads.ps1 " + self._powershell_credentials
        self.drive = ''
        self.version = self.expected_ver[0:3]
        self.index = ''
        self.skip_reset = False
        self.activation = False
        self.sps_mode = arguments.sps_mode

    @classmethod
    def add_arguments(cls, parser):
        super(SEAMBMC0011sendssdupdate, cls).add_arguments(parser)
        parser.add_argument('--sps_mode', action='store_true', help="Add argument to check sps mode")
        parser.add_argument('--SSD_path', action='store', help="Path to the bin to be used for the update", default="")
        parser.add_argument('--expected_ver', action='store', help="The version expected to be reported after update", default="")
        parser.add_argument('--warm_reset', action='store_true', help="Add argument if warm reset to be performed")
        parser.add_argument('--fio', action='store', help="Add argument if workload need to be started", default="")

    def check_capsule_pre_conditions(self):
        #To-Do add capsule pre condition checks
        return True

    def evaluate_workload_output(self, output):
        #To-Do add workload output analysis
        return True

    def get_config(self):
        if self._os_type != OperatingSystems.LINUX:
            result = self.SSD_config()            
            for line in result.split('\n'):
                if "Index : " in line:
                    self.index = line.split(' : ')[1]
                    self._log.info("Index of device :" +str(self.index))
                    break
                if "DevicePath : " in line:
                    self.drive = line.split(' : ')[1]
                    self._log.info("DevicePath :" +str(self.drive))
        else :
            cmd = 'intelmas show -intelssd | grep -b2 -a2 '+ str(self.version)  
            result = self.run_ssh_command(cmd)
            for line in result.stdout.split('\n'):
                if "Index : " in line:
                    self.index = line.split(' : ')[1]
                    self._log.info("Index of device :" +str(self.index))
                    break
                if "DevicePath : " in line:
                    self.drive = line.split(' : ')[1]
                    self._log.info("DevicePath :" +str(self.drive))
        
    def get_current_version(self, echo_version=True):    
        if self._os_type != OperatingSystems.LINUX:
            result = self.run_powershell_command(command=self._workload_path+'SSD_Version.ps1 '+self._powershell_credentials+ " "+str(self.index), get_output=True)
            for line in result.split('\n'):
                if "Firmware : " in line:
                    version = line.split(' : ')[1]
                    self._log.info(version)
                    return version            
        else :
            cmd = 'intelmas show -intelssd | grep '+ str(self.version) 
            result = self.run_ssh_command(cmd)
            version = result.output.split('\n')[0].split(' ')
        if echo_version:
            self._log.info("Version detected: " + version[2])
            return version[2]

    def execute(self):
        self.get_config()
        return self.SSD_update(self.SSD_path,self.index,self.drive)

    def cleanup(self, return_status):
        super(SEAMBMC0011sendssdupdate, self).cleanup(return_status)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SEAMBMC0011sendssdupdate.main() else Framework.TEST_RESULT_FAIL)
