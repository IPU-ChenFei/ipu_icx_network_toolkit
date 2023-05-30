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


class McaRecovExePathSrarEinjMemUcIfu(McaCommon):
    """
    Glasgow_id : 63077
    MCA Recovery Execution Path
    Software layer assisted recovery from uncorrectable data errors. Enables software layers (OS, VMM, DBMS,
    Application) to assist in system recovery from errors that are not correctable at the hardware level and marked as
    corrupted data by the CPU.

    This test injects and consumes memory poison error in Data Load Unit in windows SUT
    """
    _BIOS_CONFIG_FILE = "mca_recovery_exe_srar_bios_knobs.cfg"
    TEST_CASE_ID = ["G63077.0 - mca_recovery_exe_path_srar_einj_mem_uc_ifu"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new McaRecovExePathSrarEinjMemUcIfu object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(McaRecovExePathSrarEinjMemUcIfu, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs whether they updated properly.

        :return: None
        """
        super(McaRecovExePathSrarEinjMemUcIfu, self).prepare()

    def execute(self):
        """
        executing mca_inject_and_check method from ras_mca_common to inject mca error using Ras Tools and verify the
        error in Os Logs.

        :return: True or False
        """
        return self._mca_common.mca_inject_and_check(self._mca_common.RAS_MCA_EXE_INSTR_PATH)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if McaRecovExePathSrarEinjMemUcIfu.main() else Framework.TEST_RESULT_FAIL)
