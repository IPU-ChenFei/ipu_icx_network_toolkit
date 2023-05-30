#!/usr/bin/env python
##########################################################################
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
##########################################################################
"""
    :TDX TDVM can be paused and resumed with TDX capable Linux VMM:

    Verify TDVM can be paused and resumed with TDX capable Linux VMM.
"""

import sys
import time

from dtaf_core.lib.dtaf_constants import Framework

from src.security.tests.tdx.tdx_common_linux import LinuxTdxBaseTest
from src.lib import content_exceptions


class TDVMEnterExitLinux(LinuxTdxBaseTest):
    """
            This recipe tests TDVM boot and requires the use of a Linux supporting TDVM.

            :Scenario: Pause and resume TDVM.

            :Phoenix ID: 18014073991

            :Test steps:

                With a TDVM created and launched (from TDX007a_install_tdvm_linux and TDX008a_launch_tdvm_linux),
                verify the TDVM can be paused and resumed.

            :Expected results: TDVM be paused and resumed.

            :Reported and fixed bugs:

            :Test functions:

        """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of test case.
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        :return: None
        """
        super(TDVMEnterExitLinux, self).__init__(test_log, arguments, cfg_opts)
        self.BUFFER_TIME = 5.0

    def execute(self):
        key = 0
        self.launch_vm(key=key, tdvm=True)
        self._log.info("VM is alive after launching.")
        self._log.info("Pausing VM {}.".format(key))
        self.pause_vm(key)
        time.sleep(self.BUFFER_TIME)
        if self.vm_is_alive(key=key):
            raise content_exceptions.TestFail("VM could still be accessed while paused.")
        self._log.info("Could not ssh to VM while it was paused.")

        self._log.info("Resuming VM {}.".format(key))
        self.resume_vm(key)
        time.sleep(self.BUFFER_TIME)
        if not self.vm_is_alive(key=key):
            raise content_exceptions.TestFail("VM could not be accessed with SSH after resuming.")
        self._log.info("Could ssh to VM when it was resumed after pausing.")

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TDVMEnterExitLinux.main() else Framework.TEST_RESULT_FAIL)
