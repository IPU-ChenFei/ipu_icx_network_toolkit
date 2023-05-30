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
    :TDX BIOS Knob Check:

    Verify TDX BIOS knob is not enabled/visible unless both TME and VMX are enabled.
"""
import sys
import os

from src.security.tests.tdx.tdx_common_linux import LinuxTdxBaseTest
from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from dtaf_core.lib.private.cl_utils.adapter import data_types


class TdxKnobCheck(LinuxTdxBaseTest):
    """
            This recipe tests BIOS knob enforcement and is compatible with most OSes.

            :Scenario: Verify TDX cannot be enabled if any of VMX, TME, or TME-MT are disabled. Enable VMX, TME, and
            TME-MT knobs and verify that TDX can be selected only when all three knobs are set to enabled.

            :Phoenix ID: 18014073289

            :Test steps:

                :1: Boot to BIOS menu.

                :2: Verify VMX knob is set to enable.

                :3: Verify TME knob is disabled.

                :4: Attempt to enable TDX in BIOS.  This should fail since TME is not enabled.

                :5: Enable TME knob in BIOS, disable TME-MT in BIOS.

                :6: Attempt to enable TDX in BIOS.  This should fail since TME-MT is not enabled.

                :7: Enable TME-MT in BIOS.

                :8: Attempt to enable TDX in BIOS.  This should be successful since TME-MT and TME are enabled.


            :Expected results: TDX can be enabled only in the case where TME-MT, TME, and VMX are all enabled.

            :Reported and fixed bugs:
                WW15.5:  SUT boots to OS before changing knobs with XMLCLI due to XMLCLI but when using ITP to change
                BIOS knobs from BIOS menu.

            :Test functions:

        """

    def prepare(self):
        self.bios_util.load_bios_defaults()
        self.reboot_sut()
        self._log.info("Setting BIOS knobs... this can take up to ten minutes.")
        if self.product == "SPR":  # 2LM and TDX are incompatible on SPR
            one_lm_knob_file = self.tdx_consts.KNOBS[f"{self.tdx_consts.LM_MODE}_1LM"]
            knob_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), f"../{one_lm_knob_file}")
            self.set_knobs(knob_file=knob_file, reboot_on_knob_set=False)
        self.serial_bios_util.navigate_bios_menu()

    def execute(self):
        self._log.info("Starting BIOS knob checkout.")

        # knob check
        self._log.info("Verifying VMX knob is enabled by default.")
        if not self.check_vmx_knobs(vmx_enabled=True, set_on_fail=False, reboot_on_knob_set=False):
            raise content_exceptions.TestFail("VMX is not enabled by default.")

        self._log.info("Checking TME knob is not enabled; if it is enabled, it will be disabled and SUT will be "
                       "rebooted.")
        # disable TME knob if it is enabled already
        self.check_tme_knobs(tme_enabled=False, set_on_fail=True, reboot_on_knob_set=False)

        self.boot_to_tdx_knob()
        self._log.debug("TME knob is disabled, trying to enable TDX without TME.  This should fail!")
        self.find_tdx_knob()
        self._log.info("Couldn't find TDX knob, as expected with TME disabled.  Rebooting to enable TME.")

        # enable TME, leave TME-MT disabled
        self.check_tme_knobs(tme_enabled=True, set_on_fail=True, reboot_on_knob_set=False)
        self.check_tmemt_knobs(tmemt_enabled=False, set_on_fail=True, reboot_on_knob_set=False)
        self._log.info("TME knob is enabled and TME-MT knob is disabled. Trying to enable TDX without TME-MT.  "
                       "This should fail!")
        self.boot_to_tdx_knob()
        self.find_tdx_knob()

        # enable TME-MT
        self.check_tmemt_knobs(tmemt_enabled=True, set_on_fail=True, reboot_on_knob_set=False)
        self.boot_to_tdx_knob()

        try:
            self.find_tdx_knob()
        except RuntimeError:  # TDX knob is selectable, catch error
            self._log.info("Can set TDX BIOS knob with TME and TME-MT enabled.")
        else:  # couldn't find the knob, raise error
            content_exceptions.TestFail("Couldn't select TDX knob with TME and TME-MT enabled.")

        return True  # made it this far, test is a pass

    def find_tdx_knob(self):
        """
        Find TDX knob in BIOS serial menu.  Raises error if TDX knob is selectable because this test has more negative
        checks than positive checks.  :)

        :raise RuntimeError: if TDX is selectable.
        """
        try:
            self.serial_bios_util.select_knob(self.tdx_consts.TDX_KNOB_LABEL, data_types.BIOS_UI_OPT_TYPE)
            raise RuntimeError("TDX knob is selectable.")
        except content_exceptions.TestFail:  # not being able to set knob is passing test
            self._log.info("Could not select TDX BIOS knob.")


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TdxKnobCheck.main() else Framework.TEST_RESULT_FAIL)

