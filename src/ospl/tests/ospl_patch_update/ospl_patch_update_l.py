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
from src.lib.content_base_test_case import ContentBaseTestCase


class OsplPatchUpdate(ContentBaseTestCase):
    """
    Phoenix ID: 16014810854 - PI_OSPL_Patch_update_L
    This test case is to update the OSPL patch micro code
    """
    TEST_CASE_ID = ["16014810854", "PI_OSPL_Patch_update_L"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new OsplPatchUpdate object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(OsplPatchUpdate, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        :return: None
        """
        super(OsplPatchUpdate, self).prepare()

    def execute(self):
        """
        1. get the current microcode version
            cat /proc/cpuinfo | grep micro
        2. put the new microcode (pdb file) to the ucode folder
        3. Issue OS patch load
            echo 1 > /sys/devices/system/cpu/microcode/reload

        :return: True, if the test case is successful
        """
        # call installer reboot stress test
        self._common_content_lib.update_micro_code()
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if OsplPatchUpdate.main() else Framework.TEST_RESULT_FAIL)
