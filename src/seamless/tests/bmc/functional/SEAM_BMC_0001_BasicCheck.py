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
    :Seamless BMC hello world test:

    Checks that BMC connections are possible and the framework is ok.
"""
import sys
from datetime import datetime, timedelta
from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.seamless.lib.seamless_common import SeamlessBaseTest


class SEAM_BMC_0001_BasicCheck(SeamlessBaseTest):
    def __init__(self, test_log, arguments, cfg_opts):
        super(SEAM_BMC_0001_BasicCheck, self).__init__(test_log, arguments, cfg_opts)
        self.warm_reset = False
        
    def check_capsule_pre_conditions(self):
        pass

    def get_current_version(self, echo_version=True):
        fw_inv = self._bmc_redfish.get_firmwareinventory()
        for each in fw_inv:
            if each['Id'] == 'bmc_active':
                version = each['Version']
                print(each)
        return version

    def examine_post_update_conditions(self):
        pass

    def evaluate_workload_output(self, output):
        pass

    def block_until_complete(self, pre_version):
        pass

    def prepare(self):
        self.time_start_test = datetime.now()

    def execute(self):
        
        version = self.get_current_version()
        self._log.info("BMC version = " + str(version))
        final_result = True
        return final_result

    def cleanup(self, return_status):
        super(SEAM_BMC_0001_BasicCheck, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SEAM_BMC_0001_BasicCheck.main() else Framework.TEST_RESULT_FAIL)
