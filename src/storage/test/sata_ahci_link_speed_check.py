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
from src.storage.test.storage_common import StorageCommon


class SataLinkSpeed(StorageCommon):
    """
    Glasgow_id : 44210
    HPALM : 80245
    Validate and Check of SATA drive Link Speed.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new SataLinkSpeed object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(SataLinkSpeed, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        1. Copy Smart exe File to SUT.

        :return: None
        """
        self._install_collateral_obj.copy_smartctl_exe_file_to_sut()

    def execute(self):
        """
        1. Call storage provider method check ahci link speed to Test the link speed.

        :return: True or False
        """
        self.check_ahci_link_speed()
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SataLinkSpeed.main() else Framework.TEST_RESULT_FAIL)
