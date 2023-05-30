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
import os
import sys

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.dtaf_content_constants import ErrorTypeAttribute
from src.lib import content_exceptions
from src.rdt.tests.rdt_l3_cdp.rdt_base import RdtBase


class TestId8UnusedClos(RdtBase):


    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new TestId8UnusedClos object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(TestId8UnusedClos, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):  # type: () -> None
        """
        To Setup prepare
        """
        super(TestId8UnusedClos, self).prepare()

    def execute(self):
        """
        1. check the content is present in SUT
        2. execute the content
        3. pull the results to host

        :raise : content_exceptions.TestFail
        :return : True on Success
        """
        return(super(TestId8UnusedClos, self).execute(script="testid_8", args=""))

    def cleanup(self, return_status):  # type: (bool) -> None
        """
        Test Cleanup
        """
        super(TestId8UnusedClos, self).cleanup(return_status)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TestId8UnusedClos.main()
             else Framework.TEST_RESULT_FAIL)
