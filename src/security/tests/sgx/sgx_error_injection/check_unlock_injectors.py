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

from typing import List
import sys

from src.lib import content_base_test_case
from dtaf_core.lib.dtaf_constants import Framework
from pysvtools.fish_platform.platforms.EagleStream import _unlock_injectors as unlock_injectors


class CheckUnlockInjectors(content_base_test_case.ContentBaseTestCase):
    """
    Test ID: 18014073808
    Verify error injection capabilities for SGX and RAS InterOp
    """
    TEST_CASE_ID: List[str] = ["18014073808", "Verify error injection capabilities for SGX and RAS InterOp"]

    def execute(self) -> bool:
        unlock_injectors()
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CheckUnlockInjectors.main() else
             Framework.TEST_RESULT_FAIL)
