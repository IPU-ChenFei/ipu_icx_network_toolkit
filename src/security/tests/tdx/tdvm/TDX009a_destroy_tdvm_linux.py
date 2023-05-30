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
    :TDX TDVM can be destroyed on top of TDX capable VMM in Linux:

    Verify TDVM can be destroyed on top of TDX capable VMM in Linux.
"""
import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.security.tests.tdx.tdx_common_linux import LinuxTdxBaseTest
from src.lib import content_exceptions


class TDVMTeardownLinux(LinuxTdxBaseTest):
    """
            This recipe tests TDVM and requires the use of a Linux distribution supporting TDVM.

            :Scenario: Shut down and destroy the TDVM.  Verify the TDVM can be deleted.

            :Phoenix ID: 18014073732

            :Test steps:

                With a TDVM created and launched, shutdown and destroy the TDVM.

            :Expected results: TDVM should succeed in being shut down and the OS should be able to destroy the VM.

            :Reported and fixed bugs:

            :Test functions:

        """

    def execute(self):
        key = 0
        self._log.info("Launched VM {}.".format(key))
        self.launch_vm(key=key, tdvm=True)
        self._log.info("Verifying VM has booted with SSH.")
        if self.vm_is_alive(key=key):
            self._log.info("VM is up.  Initiating shutdown of VM.")
        else:
            raise content_exceptions.TestFail("VM {} failed to boot.".format(key))

        self.teardown_vm(key=0, force=False)
        if not self.vm_is_alive(key=key):
            self._log.info("SSH attempt to VM {} failed.  VM successfully torn down.".format(key))
        else:
            raise content_exceptions.TestFail("VM {} failed to shut down.".format(key))

        return True  # made it this far, test is a pass


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TDVMTeardownLinux.main() else Framework.TEST_RESULT_FAIL)
