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

from src.ras.tests.sddc.sddc_common import SddcCommon
import src.ras.lib.sddc_util as SddcUtil


class SddcEnable(SddcCommon):
    """
    Glasgow_id : 63036
    ECC (Error-Correcting Code)
    MCA (Machine Check Architecture)
    SDDC (Single Device Data Correction)

    SDDC refers to the ability of the error correction code to correct errors resulting from the failure of a single
    DRAM device. Single Device Data Correction (SDDC) is supported on Standard RAS.

    Feature description
    SDDC provides error checking and correction that protects against a single x4 DRAM device failure (hard-errors)
    as well as multi-bit faults in any portion of a single DRAM device on a DIMM Skylake processor uses a new
    ECC algorithm to improve the coverage.
    For X4 DRAM based DIMM in 1LM/2LM: In case of a device hard failure affecting all 16 banks it
    implements a new algorithm based on 'device sparing on to the ECC device'.
    After device sparing event subsequent single errors will be detected but not corrected and
    will trigger fatal MCERR.
    For X8 DRAM based DIMMs in 1LM SDDC is carried out within a static virtual lockstep pair
    configured at the memory initialization time. A static virtual lockstep pair is confined
    within the same channel thus improving the throughput. Lockstep across two channels required by the
    Broadwell architecture is no longer applicable. NOTE: Static virtual lockstep was selected as the most design
    friendly lockstep.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new MemSmbusRecovery object
        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(SddcEnable, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Setting the bios knobs to its default mode.
        3. Setting the bios knobs as per the test case.
        4. Rebooting the SUT to apply the new bios settings.
        5. Verifying the bios knobs that are set.
        :return: None
        """
        super(SddcEnable, self).prepare()

    def execute(self):
        return SddcUtil.get_ecc_status(self._cscripts, self._sdp, self._common_content_lib, self._log)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SddcEnable.main() else Framework.TEST_RESULT_FAIL)