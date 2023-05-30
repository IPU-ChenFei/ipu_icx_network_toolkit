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
from src.hsio.pcie.stress.ptg_stress_variable_rd import PtgVarRd


class PtgVarWr(PtgVarRd):
    """
    Phoenix ID: 15011118747
    Gen5_MSB_Stress_write_Variable_Packet_Transaction

    Test requires a FastPath image!

    Stress_PCIe__Gen5_MSB_wr_Variable_Packet_Transaction_VT-d_On
    """
    TEST_CASE_ID = ["15011118747", "Gen5_MSB_Stress_write_Variable_Packet_Transaction"]

    def __init__(self, test_log, arguments, cfg_opts):
        super(PtgVarWr, self).__init__(test_log, arguments, cfg_opts)
        self.test_patterns = "wr8,wr96,wr256,wr512"
        self.test_type = "wr"

    def prepare(self):
        """
        Prepare
        """
        super(PtgVarWr, self).prepare()

    def execute(self):
        """
        Runs different read patterns -
            wr8,wr96,wr256,wr512
        Each test pattern is run for 10 seconds.
        """
        super(PtgVarWr, self).execute()

    def cleanup(self, return_status):
        """
        Copy logs from SUT to Host
        """
        super(PtgVarWr, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PtgVarWr.main() else Framework.TEST_RESULT_FAIL)
