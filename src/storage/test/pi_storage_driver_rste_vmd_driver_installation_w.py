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

from src.lib.test_content_logger import TestContentLogger
from src.storage.test.storage_common import StorageCommon
from src.storage.test.pi_storage_rste_driver_installation_w import PiStorageRSTeDriverInstallationW


class PiRsteVmdDriverInstallationWindows(StorageCommon):
    """
    HPQC : 80275-PI_Storage_Driver_RSTeVMDDriver_Installation_W
    This Class is Used to Enable Vmd Bios Knobs and Install and Verify Vroc Tool on Windows Os
    """
    TEST_CASE_ID = ["H80275", "PI_Storage_Driver_RSTeVMDDriver_Installation_W"]

    step_data_dict = {1: {'step_details': 'Enable Vmd Bios Knobs and Verify',
                          'expected_results': 'Vmd Bios Knobs are Enabled and Verified'},
                      2: {'step_details': 'Install the Windows driver run VROCSetup.exe -s.'
                                          'Reboot and Verify driver installed correctly using any method like checking'
                                          ' in control panel or driver queries.',
                          'expected_results': 'The driver was installed and verified successfully'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new PiRsteVmdDriverInstallationWindows object

        :param test_log: Used for debug and info messages
        :param arguments: None
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PiRsteVmdDriverInstallationWindows, self).__init__(test_log, arguments, cfg_opts)
        if self.os.os_type != OperatingSystems.WINDOWS:
            raise NotImplementedError("This Test is Supported only on Windows")
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self.vroc_obj = PiStorageRSTeDriverInstallationW(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        :return None
        """
        super(PiRsteVmdDriverInstallationWindows, self).prepare()

    def execute(self):
        """
        Enable Vmd Bios Knobs and install and verify Vroc Tool

        :return: True
        """
        self._test_content_logger.start_step_logger(1)
        self.enable_vmd_bios_knobs()
        self._test_content_logger.end_step_logger(1, True)

        self._test_content_logger.start_step_logger(2)
        return_value = self.vroc_obj.execute()
        self._test_content_logger.end_step_logger(2, return_value)
        return return_value

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PiRsteVmdDriverInstallationWindows, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiRsteVmdDriverInstallationWindows.main() else Framework.TEST_RESULT_FAIL)
