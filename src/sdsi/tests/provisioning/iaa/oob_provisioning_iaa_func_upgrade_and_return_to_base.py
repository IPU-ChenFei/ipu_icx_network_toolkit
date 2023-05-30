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
"""DEPRECATION WARNING - Not included in agent scripts/libraries, which will become the standard test scripts."""
import warnings
warnings.warn("This module is not included in agent scripts/libraries.", DeprecationWarning, stacklevel=2)
import sys

from dtaf_core.lib.dtaf_constants import Framework

from src.sdsi.tests.provisioning.iaa.ib_provisioning_iaa_func_upgrade_and_return_to_base import \
    InBandIAAFuncProvisionAndReturnToBase


class OutOfBandIAAFuncProvisionAndReturnToBase(InBandIAAFuncProvisionAndReturnToBase):
    """
    Glasgow_ID: 70170
    Phoenix_ID: 18014074695
    Expectation is that IAA devices should works only after applying the IAA4 licenses (except default devices)
    """
    def _get_common_lib(self):
        """
        Get the common library used for this test
        """
        self._log.info("Using Out of Band Common Library")
        from src.sdsi.lib.sdsi_common_lib import SDSICommonLib
        return SDSICommonLib(self._log, self.os, self._common_content_lib, self._common_content_configuration,
                             self._sdsi_installer, self.ac_power)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if OutOfBandIAAFuncProvisionAndReturnToBase.main()
             else Framework.TEST_RESULT_FAIL)