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

from src.ras.tests.mca.mca_common import McaCommon


class McaRecoveryNonExecutionPath(McaCommon):
    """
    Glasgow_id : 59495
    Hpalm_id : 81552
    MCA Recovery Non Execution Path
    Software layer assisted recovery from uncorrectable data errors. Enables software layers (OS, VMM, DBMS,
    Application) to assist in system recovery from errors that are not correctable at the hardware level and marked as
    corrupted data by the CPU.
    """
    _BIOS_CONFIG_FILE = "mca_non_exe_bios_knobs.cfg"
    TEST_CASE_ID = ["G59495.0 - mca_recovery_non_exe_path", "H81552-PI_RAS_CPU_mca_recovery_non_exe_path"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new McaRecoveryNonExecutionPath object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(McaRecoveryNonExecutionPath, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Copy mcelog.conf file to sut and reboot
        2. Clear All Os Logs before Starting the Test Case
        3. Set the bios knobs to its default mode.
        4. Set the bios knobs as per the test case.
        5. Reboot the SUT to apply the new bios settings.
        6. Verify the bios knobs whether they updated properly.

        :return: None
        """
        super(McaRecoveryNonExecutionPath, self).prepare()
        self._common_content_lib.update_micro_code()

    def execute(self):
        """
        executing mca_inject_and_check method from ras_mca_common to inject mca error using Ras Tools and verify the
        error in Os Logs.

        :return: True or False
        """
        return self._mca_common.mca_inject_and_check(self._mca_common.RAS_MCA_NON_EXE_PATH)

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(McaRecoveryNonExecutionPath, self).cleanup(return_status)
        if self.os.is_alive():
            self._common_content_lib.delete_micro_code()
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if McaRecoveryNonExecutionPath.main() else Framework.TEST_RESULT_FAIL)
