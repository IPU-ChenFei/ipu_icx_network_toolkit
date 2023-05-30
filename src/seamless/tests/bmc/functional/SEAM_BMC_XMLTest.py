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
    :Seamless Inventory XML Generation Test:

    Just a test version of BMC_0001 to get XML building up and running.
"""
import os
import sys
from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.seamless.lib.seamless_common import SeamlessBaseTest


class SEAM_BMC_XMLTest(SeamlessBaseTest):

    def __init__(self, test_log, arguments, cfg_opts):
        super(SEAM_BMC_XMLTest, self).__init__(test_log, arguments, cfg_opts)
        self.capsule_path = arguments.capsule_path
        self.expected_ver = arguments.expected_ver
        self.warm_reset = arguments.warm_reset
        self.start_workload = arguments.start_workload
        self.capsule_type = arguments.capsule_type
        self.sut_mode = arguments.sut_mode
        self.start_workload_command = self._workload_path + "StartWorkloads.ps1 " + self._powershell_credentials
        self.stop_workload_command = self._workload_path + "StopWorkloads.ps1 " + self._powershell_credentials
        self.get_sps_command = self._workload_path + "GetSPSVersion.ps1 " + self._powershell_credentials
        self.regionName = ""
        self.skip_reset = False
        self.sps_mode = arguments.sps_mode

    @classmethod
    def add_arguments(cls, parser):
        super(SEAM_BMC_XMLTest, cls).add_arguments(parser)
        parser.add_argument('--sps_mode', action='store_true', help="Add argument to check sps mode")
        parser.add_argument('--capsule_path', action='store', help="Path to the capsule to be used for the update",
                            default="")
        parser.add_argument('--expected_ver', action='store', help="The version expected to be reported after update",
                            default="")
        parser.add_argument('--warm_reset', action='store_true', help="Add argument if warm reset to be performed")
        parser.add_argument('--start_workload', action='store_true', help="Add argument if workload need to be started")
        parser.add_argument('--sut_mode', action='store', help="State if SUT is in UEFI mode or DC power off mode",
                            default="")
        parser.add_argument('--capsule_type', action='store', help="Add type of update capsule", default="")

    def get_current_version(self, echo_version=True):
        return self.get_sps_ver(False)

    def check_capsule_pre_conditions(self):
        # To-Do add capsule pre condition checks
        return True

    def evaluate_workload_output(self, output):
        # To-Do add workload output analysis
        return True

    def execute(self):
        xml_bmc = self.get_inventory_xml_bmc()
        xml_os = self.get_inventory_xml_os()
        capsule_xml_path = "C:\\Orchestrator\\XMLFiles\\capsule-modded.xml"  # Replace with actual Capsule XML when we get one.

        f = open("bmc.xml", "w")
        f.write(xml_bmc)
        bmc_xml_path = os.path.realpath(f.name)
        f.close()

        f = open("os.xml", "w")
        f.write(xml_os)
        os_xml_path = os.path.realpath(f.name)
        f.close()

        return self.validate_for_orchestrator(capsule_xml_path, bmc_xml_path, os_xml_path)

    def cleanup(self, return_status):
        super(SEAM_BMC_XMLTest, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SEAM_BMC_XMLTest.main() else Framework.TEST_RESULT_FAIL)
