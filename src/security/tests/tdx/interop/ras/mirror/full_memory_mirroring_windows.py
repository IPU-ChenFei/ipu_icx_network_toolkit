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
    :No Full Memory Mirroring:

    Verify TDX cannot be enabled with full memory mirroring.
"""
import sys

from dtaf_core.lib.private.cl_utils.adapter import data_types
from dtaf_core.lib.dtaf_constants import Framework
from src.security.tests.tdx.tdx_common_windows import WindowsTdxBaseTest
from src.lib import content_exceptions


class TDXFullMemoryMirroringWindows(WindowsTdxBaseTest):
    """
            This recipe tests compatibility with full memory mirroring feature and is compatible with most TDX
            supporting OSs.  The SUT must be populated with at least one memory channel pair that supports a mirror
            configuration.

            :Scenario: Verify TDX cannot be enabled with full memory mirroring enabled.  Ensure that if memory mirroring
            is disabled, TDX can be enabled.

            :Phoenix ID: 22014296926

            :Test steps:

                :1: Boot to BIOS menu.

                :2: Enable TDX knobs.  Refer to Glasgow ID 69627 for steps.

                :3: Enable Full Memory Mirroring BIOS knob (EDKII -> Socket Configuration -> Memory Configuration ->
                Memory RAS Configuration -> Mirror Mode -> Full Mirror Mode.

                :4: Go back to TDX BIOS knob and verify it is greyed out/cannot be selected.

                :5: Go back to Mirror Mode BIOS knob in step 3 and set Mirror Mode BIOS knob to "Disable".

                :6: Go back to TDX BIOS knob and verify it can be selected again.

                :7: Repeat step 3, save BIOS settings, and reboot SUT to OS.

                :8: Verify that TDX is not enabled through enumeration check.

            :Expected results: TDX is not enabled while full mirror mode is enabled and TDX enumeration check fails.

            :Reported and fixed bugs:

            :Test functions:

        """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create test instance.
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        :return: None
        """
        super(TDXFullMemoryMirroringWindows, self).__init__(test_log, arguments, cfg_opts)
        self.mirror_mode_knob_name = 'MirrorMode'
        self.full_mirror_mode_value = "0x1"
        self.current_mirror_mode_value = ""

    def execute(self):
        # get current memory mode
        self.current_mirror_mode_value = self.bios_util.get_bios_knob_current_value(self.mirror_mode_knob_name)
        self.current_mirror_mode_value = self.current_mirror_mode_value.replace("\\", "")
        self.current_mirror_mode_value = self.current_mirror_mode_value.replace("r", "")
        # change memory mode into full memory mirror mode.
        self.bios_util.set_single_bios_knob(self.mirror_mode_knob_name, self.full_mirror_mode_value)
        self.reboot_sut()

        # reboot and get into bios menu
        self.serial_bios_util.navigate_bios_menu()

        # check TDX knob is not accessible
        self._log.info("Checking TDX knob is not accessible.")
        self.serial_bios_util.select_enter_knob(self.tdx_consts.PROC_BIOS_PATH)
        try:
            self.serial_bios_util.select_knob(self.tdx_consts.TDX_KNOB_LABEL, data_types.BIOS_UI_OPT_TYPE)
        except content_exceptions.TestFail:
            self._log.info("TDX knob could not be selected as expected; this is because Full Memory Mirror is enabled.")
        else:
            raise RuntimeError("TDX knob could be set with Full Memory Mirroring enabled.")

        # disabling full memory mirroring
        self._log.info("Disabling Full Mirror Mode.")
        self.serial_bios_util.go_back_to_root()
        self.serial_bios_util.select_enter_knob(self.tdx_consts.RAS_BIOS_PATH)
        self.serial_bios_util.set_bios_knob(self.tdx_consts.MIRROR_MODE_LABEL, data_types.BIOS_UI_OPT_TYPE,
                                            "Disable")
        self.serial_bios_util.save_bios_settings()
        self.serial_bios_util.go_back_to_root()

        # check TDX knob is accessible
        self._log.info("Checking TDX knob is accessible with memory mirroring disabled.")
        self.serial_bios_util.select_enter_knob(self.tdx_consts.PROC_BIOS_PATH)
        try:
            self.serial_bios_util.select_knob(self.tdx_consts.TDX_KNOB_LABEL, data_types.BIOS_UI_OPT_TYPE)
        except content_exceptions.TestFail:
            self._log.error("TDX knob could not be selected with disabled Memory Mirroring.")
            raise RuntimeError("TDX knob could not be set with disabled Memory Mirroring.")
        else:
            self._log.info("Found TDX knob and could select it.")

        # reboot SUT and set Memory mode to 'Full mirror mode'
        self.reboot_sut()
        self.bios_util.set_single_bios_knob(self.mirror_mode_knob_name, self.full_mirror_mode_value)
        self.reboot_sut()
        # check TDX is enumerated or not
        if self.verify_tdx_enumeration():
            raise content_exceptions.TestFail("TDX enumerated successfully, but it was not expected at 'Full mirror mode'")
        else:
            self._log.info("TDX enumeration failed.")

        return True


    def cleanup(self, return_status: bool) -> None:
        self.bios_util.set_single_bios_knob(self.mirror_mode_knob_name, self.current_mirror_mode_value)
        self.reboot_sut()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TDXFullMemoryMirroringWindows.main() else Framework.TEST_RESULT_FAIL)
