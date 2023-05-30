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
    :TD Guest and SGX Enclave Coexistence with High and Low PRM:

    With lowest PRM setting and TD guest launched, launch SGX enclave and verify TD guest is alive.  Set PRM to highest
    setting and launch TD guest, then launch SGX enclave.
"""
import sys
import os

from dtaf_core.lib.dtaf_constants import Framework
from src.lib.content_exceptions import TestFail
from src.security.tests.tdx.interop.security.sgx_enclave_coexistance import SgxEnclaveTdGuest


class SgxEnclaveTdGuestPrmCheck(SgxEnclaveTdGuest):
    """
            This test verifies the coexistence of an SGX enclave and a TD guest on the SUT.  Paths to SGX PSW and FVT
            packages from BKC must be updated in content_configuration.xml file.  These are between the
            <SGX_APP><LINUX><RHEL_BASE_KERNEL><PSW_ZIP> and <SGX_APP><LINUX><RHEL_BASE_KERNEL><SGX_FVT_ZIP> tags.

            :Scenario: Launch a TD guest and an SGX enclave on the SUT.  Verify system and TD guest are alive.

            :Phoenix ID: 22015382158

            :Test steps:

                :1:  Enable TDX and SGX.

                :2:  Set the PRM to the lowest size.

                :3:  Install SGX SW collateral (PSW and FVT stacks).

                :4:  Create and launch a TD guest.

                :5:  Launch SGX sample enclave.

                :6:  Verify TD guest is still alive.

                :7:  Set the PRM to the highest size.

                :8:  Repeat steps 4 through 6.

            :Expected results: TD guest and SUT should be alive.

            :Reported and fixed bugs:

            :Test functions:

        """

    def prepare(self) -> None:
        super(SgxEnclaveTdGuestPrmCheck, self).prepare()
        self.launch_vms.prepare()

    def execute(self) -> bool:
        smallest_prm_value = min(self.launch_vms.tdx_consts.PRM_KNOB_VALUES.values())
        largest_prm_value = max(self.launch_vms.tdx_consts.PRM_KNOB_VALUES.values())
        for value in [largest_prm_value, smallest_prm_value]:
            self._log.info(f"Setting PRM size to {hex(value)}")
            self.set_prm_knob(hex(value))
            self._log.info("Launching TD VMs.")
            self.launch_vms.execute()
            self._log.info("Setting up SGX sample enclave.")
            super(SgxEnclaveTdGuestPrmCheck, self).execute()
            self._log.info("SGX sample enclave launched, checking VM health.")
            for key, vm in enumerate(self.launch_vms.tdvms):
                if not self.launch_vms.vm_is_alive(key=key):
                    raise TestFail(f"VM {key} no longer alive after launching SGX enclave.")
            self._log.info("TD guests are alive after launching SGX enclave.")
        return True

    def cleanup(self, return_status: bool) -> None:
        self.launch_vms.cleanup(return_status)  # override SGX clean up for TD guest clean up method

    def set_prm_knob(self, prm_size: str):
        """Set knob file for PRM size.
        :return: path to knob file"""
        temp_file = "prm_knob_file.cfg"
        knob_file = self.launch_vms.tdx_consts.BiosKnobFiles.BIOS_CONFIG_FILE_SGX_PRM_KNOB_SIZE
        knob_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"../../{knob_file}")
        with open(knob_file) as in_file:
            with open(temp_file, "w") as out_file:
                for line in in_file:
                    if "{}" in line:
                        line = line.format(prm_size)
                    out_file.write(line)
        self.launch_vms.set_knobs(temp_file)
        os.remove(temp_file)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SgxEnclaveTdGuestPrmCheck.main() else Framework.TEST_RESULT_FAIL)
