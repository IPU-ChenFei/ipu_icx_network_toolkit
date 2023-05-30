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
from dtaf_core.lib.base_test_case import BaseTestCase

from src.lib.redfish_common import RedFishCommon


class ExampleRedfishCommon(BaseTestCase):

    def __init__(self, test_log, arguments, cfg_opts):
        super(ExampleRedfishCommon, self).__init__(test_log, arguments, cfg_opts)
        self._cfg_opts = cfg_opts

    def execute(self):
        rf_common = RedFishCommon(self._log, self._cfg_opts)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ExampleRedfishCommon.main() else Framework.TEST_RESULT_FAIL)

