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
    :TDX Key Split Check with TD guest launch:

    Verify available max keys are split between MKTME and TDX in BIOS and TD guest is able to boot.
"""
import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.security.tests.tdx.tdvm.TDX008a_launch_tdvm_linux import TDVMLaunchLinux


class TdxKeySplitTdGuest(TDVMLaunchLinux):
    """
            This recipe tests keys can be split between TME-MT and TDX.

            :Scenario: With TME-MT and TDX enabled the correct number of keys are divided to each feature.

            :Prerequisite:  SUT must be configured with the latest BKC applicable for the platform.

            :Phoenix ID: 22013238916

            :Test steps:

                :1: Boot to BIOS menu.

                :2: Verify TME-MT and TDX are enabled.

                :3: Check the TDX max keys in menu EDKII->Socket Configuration->Processor Configuration.

                :4: Set BIOS knob to divide the keys between TME-MT and TDX.

                :5: Reboot SUT.

                :6: Verify that the number of TDX keys + the number of TME-MT keys = the number of max keys.

                :7: Boot to OS and launch a TD guest to verify the TD guest can launch properly.

                :8: Repeat for each option in key split menu in BIOS.

            :Expected results: The number of TDX keys + the number of TME-MT keys = the number of max keys and a TD
            guest can launch properly.

            :Reported and fixed bugs:

            :Test functions:

        """

    def execute(self):
        max_keys = self.tdx_consts.MAX_KEYS
        for split in self.tdx_consts.KEY_IDX.keys():
            if split != 0:  # skip assigning zero keys, covered in another test case
                self._log.info("Setting split to {} TDX keys.".format(split))
                self.split_keys(split)
                tmemt_keys = self.get_keys(key_type="tme-mt")
                tdx_keys = self.get_keys(key_type="tdx")

                # check tdx key amount is correct
                if tdx_keys != split:
                    self._log.error("Unexpected number of TDX keys found.  Expected {}, "
                                    "actually got: {}".format(split, tdx_keys))
                    return False

                # check the number of tme-mt and tdx keys combined match max keys
                if tmemt_keys + tdx_keys != max_keys:
                    self._log.error("Number of TME-MT and TDX keys combined do not equal max keys!")
                    self._log.error("Keys do not add up.  TDX keys: {} TME keys: {} Max keys: {}".format(
                        tdx_keys, tmemt_keys, max_keys))
                    return False

                self._log.debug("Key split check passed.  Expected TDX keys: {}, actual TDX keys: {}, "
                                "TME-MT keys: {}".format(split, tdx_keys, tmemt_keys))

                if not super(TdxKeySplitTdGuest, self).execute():
                    raise content_exceptions.TestFail("TD guest failed to launch with {} TDX keys "
                                                      "assigned.".format(tmemt_keys, tdx_keys))
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TdxKeySplitTdGuest.main() else Framework.TEST_RESULT_FAIL)
