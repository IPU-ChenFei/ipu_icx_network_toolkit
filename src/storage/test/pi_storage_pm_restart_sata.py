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
from src.lib import content_exceptions
from src.provider.storage_provider import StorageProvider
from src.lib.install_collateral import  InstallCollateral
from dtaf_core.lib.dtaf_constants import OperatingSystems


class PiStoragePMRestartSata(StorageCommon):
    """
    HPALM : H80005-PI_Storage_PMRestart_SATA_W
    Check the storage work fine after restart boot.
    """
    TEST_CASE_ID = ["H80005-PI_Storage_PMRestart_SATA_W"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new PiStoragePMRestartWindows object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PiStoragePMRestartSata, self).__init__(test_log, arguments, cfg_opts)
        self._install_collateral_obj = InstallCollateral(self._log,self.os, cfg_opts)
        self._storage_provider = StorageProvider.factory(test_log, self.os, cfg_opts, "os")

    def prepare(self):
        # type: () -> None
        """
        :return None
        """
        super(PiStoragePMRestartSata, self).prepare()
        self._install_collateral_obj.copy_smartctl_exe_file_to_sut()

    def execute(self):
        """
        This method Checking Disk size and dirve info  before restart, Checking Disk size,Disk drive info after restart
        Verify the drive size before and after restart,check the link speed for SATA disk
        Copied a text file to all the sata device

        :return: True or False
        :raise: content_exceptions.TestNotImplementedError
        """
        if self.os.os_type == OperatingSystems.WINDOWS:
            self.check_storage_drive_before_after_restart()
        else:
            raise content_exceptions.TestNotImplementedError("This Function is not implemented for Linux")

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiStoragePMRestartSata.main() else Framework.TEST_RESULT_FAIL)
