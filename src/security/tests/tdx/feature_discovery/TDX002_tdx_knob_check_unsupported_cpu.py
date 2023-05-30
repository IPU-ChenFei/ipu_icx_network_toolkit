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
    :TDX BIOS Knob Check with Unsupported CPU:

    Verify TDX knob is greyed out when CPU does not support TDX.
"""
import sys

from src.security.tests.tdx.tdx_common_linux import LinuxTdxBaseTest
from src.security.tests.tdx.feature_discovery.TDX010_tdx_enumeration import TdxEnumeration
from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from dtaf_core.lib.private.cl_utils.adapter import data_types


class TdxCpuUnsupported(LinuxTdxBaseTest):
    """
            This recipe tests TDX cannot be enabled when CPU is not supported.

            :Scenario: With a CPU that does not support TDX, check that TDX cannot be enabled, even with TME and VMX
            enabled.

            :Prerequisites:  SUT must be configured with the latest BKC applicable for the platform.  No CPU on SUT
            should support TDX.

            :Phoenix ID: 18014075421

            :Test steps:

                :1: Boot to BIOS menu.

                :2: Attempt to enable TDX.

            :Expected results: TDX should fail to enable.

            :Reported and fixed bugs:

            :Test functions:

        """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of sut os provider, XmlcliBios provider, BIOS util and Config util
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        :return: None
        """
        super(TdxCpuUnsupported, self).__init__(test_log, arguments, cfg_opts)
        self.enumeration_test = TdxEnumeration(test_log, arguments, cfg_opts)

    def prepare(self):
        if self.enumeration_test.execute():
            raise content_exceptions.TestSetupError("Fuses on CPU are enabled for TDX; please replace with a CPU which "
                                                    "does not have fusing enabled for TDX for this test.")
        # set VMX and TME knobs if not already set
        try:
            self.check_vmx_knobs(set_on_fail=False)
        except RuntimeError:
            raise RuntimeError("VMX knob was not set by default!")
        self.check_tme_knobs(tme_enabled=True, set_on_fail=True)
        self.check_tmemt_knobs(tmemt_enabled=True, set_on_fail=True)

    def execute(self):
        # boot to BIOS menu
        self._log.info("Starting BIOS knob checkout, booting to BIOS menu.")
        self.boot_to_tdx_knob()

        # attempt to set TDX knob
        try:
            self.serial_bios_util.select_knob(self.tdx_consts.TDX_KNOB_LABEL, data_types.BIOS_UI_OPT_TYPE)
            raise RuntimeError("TDX knob is selectable with CPU SKU that does not support TDX.")
        except content_exceptions.TestFail:  # not being able to set knob is passing test
            self._log.info("Could not set TDX BIOS knob with CPU SKU that does not support TDX.")

        # exit BIOS menu and boot to OS
        self._log.info("Reboot and boot to OS.")
        self.reboot_sut()

        # attempt to set TDX knob with OS tool
        try:
            self.check_tdx_knobs(set_on_fail=True)
            self.reboot_sut()
            self.check_tdx_knobs()
        except RuntimeError:
            self._log.debug("TDX knob failed to be set as expected.")
            return True
        else:
            self._log.error("TDX knob was able to be set!")
            return False


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TdxCpuUnsupported.main() else Framework.TEST_RESULT_FAIL)
