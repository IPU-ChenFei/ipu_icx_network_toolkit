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
    :TDX TDVM can be created on top of TDX capable VMM:

    Verify TDVM can be created on top of TDX capable VMM.
"""

import sys
import time

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.security.tests.tdx.tdvm.TDX050_launch_multiple_tdvm_linux import MultipleTDVMLaunch


class RebootTdvmLinux(MultipleTDVMLaunch):
    """
            This recipe tests TD guest boot and requires the use of an OS supporting TD guest.

            :Scenario: Launch the TD guest created and verify the VM can boot.

            :Phoenix IDs: 22014697232

            :Test steps:

                :1: With a TD guest created (from TDX007_TDVM_Build), launch TD guest.

                :2: For each TD guest booted, reboot the TD guest.

            :Expected results: Each TD guest rebooted should boot back up successfully.  The TD guests and the SUT
            should be alive.

            :Reported and fixed bugs:

            :Test functions:

        """

    def execute(self):
        try:
            num_cycles = self.tdx_properties[self.tdx_consts.TD_GUEST_REBOOT_CYCLES]
        except KeyError:
            raise content_exceptions.TestError(f"Could not find number of cycles defined in content_configuration.xml "
                                               f"file!  Please update field to the number of cycles necessary in "
                                               f"<TDX><LINUX><cycling><td_guest_reboot_cycles>.")
        super(RebootTdvmLinux, self).execute()  # boot all necessary VMs
        for cycle in range(0, num_cycles):
            self._log.info(f"Starting reboot iteration {cycle + 1} of {num_cycles}.")
            for key, vm in enumerate(self.tdvms):
                self.reboot_vm(key=key)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RebootTdvmLinux.main() else Framework.TEST_RESULT_FAIL)
