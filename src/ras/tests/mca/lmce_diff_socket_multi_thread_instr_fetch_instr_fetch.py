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


class LmceDiffSocketMultiThreadInstrFetchInstrFetch(McaCommon):
    """
    Glasgow_id : 63082
    MCA Recovery Execution Path
    Software layer assisted recovery from uncorrectable data errors. Enables software layers
    (OS, VMM, DBMS, Application) to assist in system recovery from errors that are not correctable at
    the hardware level and marked as corrupted data by the CPU.

    This test injects and consumes memory poison error in Data Load Unit in windows SUT/Linux SUT
    """
    _BIOS_CONFIG_FILE = "lmce_data_access_bios_knobs.cfg"
    TEST_CASE_ID = ["G63082.0 - lmce_diff_socket_multi_thread_instr_fetch_instr_fetch"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new LmceDiffSocketMultiThreadInstrFetchInstrFetch object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(LmceDiffSocketMultiThreadInstrFetchInstrFetch, self).__init__(test_log, arguments, cfg_opts,
                                                                            self._BIOS_CONFIG_FILE)

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
        super(LmceDiffSocketMultiThreadInstrFetchInstrFetch, self).prepare()

    def execute(self):
        """
        executing mca_inject_and_check method from ras_mca_common to inject lmce different socket multiple Instruction
        Fetch errors using Ras Tools and verify the error in Os Logs.

        Test case flow:

        -Clear all OS error logs
        -Install plugin required to inject Instruction Fetch errors
        -Inject memory poison error
        -Delay for core to consume the error
        -Obtain OS error logs and parse them

        :return: True or False
        """
        return self._mca_common.mca_inject_and_check(self._mca_common.RAS_LMCE_EXE_INSTR_INSTR_ACCESS_PATH)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if LmceDiffSocketMultiThreadInstrFetchInstrFetch.main() else
             Framework.TEST_RESULT_FAIL)
