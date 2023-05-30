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
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.storage.test.storage_common import StorageCommon
from src.power_management.lib.reset_base_test import ResetBaseTest
from src.lib import content_exceptions


class CheckStorageAfterS5(StorageCommon):
    """
    HPQC ID : H80006_PI_Storage_PMS5_SATA_W
    HPALM : H80243-PI_Storage_PMS5_L
    Check the storage work fine after s5 boot.
    """
    TEST_CASE_ID = ["H80006_PI_Storage_PMS5_SATA_W", "H80243-PI_Storage_PMS5_L"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new CheckStorageAfterS5 object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(CheckStorageAfterS5, self).__init__(test_log, arguments, cfg_opts)
        if self.os.os_type == OperatingSystems.WINDOWS:
            self._reset_base_test = ResetBaseTest(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        :return None
        """

    def check_storage_device_info_before_after_s5(self):
        before_s5 = self._storage_provider.enumerator_storage_device()

        self._log.debug("DiskDrive Information before S5 shutdown \n:{}".format(before_s5))
        if not self.os.is_alive():
            raise content_exceptions.TestFail("SUT is not alive")

        self._reset_base_test.surprise_s5()

        after_s5 = self._storage_provider.enumerator_storage_device()

        self._log.debug("DiskDrive Information after S5 shutdown \n:{}".format(after_s5))
        if before_s5 != after_s5:
            raise content_exceptions.TestFail("DiskDrive Information is not same after S5 shutdown")

    def execute(self):
        """
        1. Call Function to check the storage after s5 boot.

        :return: True or False
        """
        if self.os.os_type == OperatingSystems.LINUX:
            self.check_storage_device_work_fine_after_boot(boot_option="s5")
        elif self.os.os_type == OperatingSystems.WINDOWS:
            self.check_storage_device_info_before_after_s5()
            self.copy_text_file_to_all_sata_drives()
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CheckStorageAfterS5.main() else Framework.TEST_RESULT_FAIL)
