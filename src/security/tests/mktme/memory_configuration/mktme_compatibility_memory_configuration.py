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
import sys
import os

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.security.tests.mktme.mktme_common_windows import WindowsMktmeBase


class MktmeMemCompatibilityNUMASNCWindows(WindowsMktmeBase):
    """
        Phoenix ID : 18014071067	Verify MKTME compatibility in the the 1-0-0-0 memory configuration - NUMA_on-SNC_off
        Phoenix ID : 18014070632	Verify MKTME compatibility in the the 4-4-4-4 memory configuration - NUMA_on-SNC_off
        Phoenix ID : 18014070756	Verify MKTME compatibility in the the 4-4-4-4 memory configuration - NUMA_on-SNC_on
        Phoenix ID : 18014070902	Verify MKTME compatibility in the the 1-1-1-1 memory configuration - NUMA_on-SNC_on
        Phoenix ID : 18014071044	Verify MKTME compatibility in the the 1-1-1-1 memory configuration - NUMA_on-SNC_off
    """
    TEST_CASE_ID = ["18014071067 - Verify MKTME compatibility in the the 1-0-0-0 memory configuration - NUMA_on-SNC_off",
                    "18014070632 - Verify MKTME compatibility in the the 4-4-4-4 memory configuration - NUMA_on-SNC_off",
                    "18014070756 - Verify MKTME compatibility in the the 4-4-4-4 memory configuration - NUMA_on-SNC_on",
                    "18014070902 - Verify MKTME compatibility in the the 1-1-1-1 memory configuration - NUMA_on-SNC_on",
                    "18014071044 - Verify MKTME compatibility in the the 1-1-1-1 memory configuration - NUMA_on-SNC_off"]
    MIN_NUMA_COUNT_EXPECTED = 1

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of test case.
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        :return: None
        """
        super(MktmeMemCompatibilityNUMASNCWindows, self).__init__(test_log, arguments, cfg_opts)
        self.SNC_MODE = arguments.SNC_MODE
        self._NUMA_SNC2_KNOB_ON = "../collateral/numa_snc2_en_reference_knob.cfg"
        self._NUMA_SNC2_KNOB_OFF = "../collateral/numa_snc2_dis_reference_knob.cfg"
        self._TME_TMEMT_ON = "../collateral/tme_and_tme_mt_enable_knob.cfg"

    @classmethod
    def add_arguments(cls, parser):
        """
        :param parser: argument parser
        :return: None
        """
        super(MktmeMemCompatibilityNUMASNCWindows, cls).add_arguments(parser)
        parser.add_argument("-snc", "--SNC_MODE", action="store", dest="SNC_MODE", default="ON")

    def execute(self):
        """
        1. Set SNC to SNC ON/OFF
        2. Check NUMA Node list values
        3. Enable TME, MK-TME,
        4. Run mktmetool.efi -u 1 random
        """

        # Preprocess input parameter for SNC value
        if self.SNC_MODE.upper() == "ON":
            self._log.info("Enabling SNC2 and NUMA ON")
            bios_knob_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self._NUMA_SNC2_KNOB_ON)
        elif self.SNC_MODE.upper() == "OFF":
            bios_knob_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self._NUMA_SNC2_KNOB_OFF)
            self._log.info("Disabling SNC2 and NUMA ON")
        else:
            raise content_exceptions.TestFail(f"Unknown input parameter '{self.SNC_MODE}' identified")

        # Copy the mktme value to at least one USB drive attached to SUT.
        self.copy_mktme_tool_to_sut_usb_drives()

        # apply NUMA ON SNC ON/OFF knob values.
        self.check_knobs(bios_knob_file, set_on_fail=True)

        # check NUMA configuration node count.
        numa_group_count_host = self.get_numa_host_numa_node_values_windows()
        if numa_group_count_host <= self.MIN_NUMA_COUNT_EXPECTED:
            raise content_exceptions.TestFail(f"Numa Count '{numa_group_count_host}' should be greater than"
                                              f" {self.MIN_NUMA_COUNT_EXPECTED}")

        # Enabling  TME & TME-MT bios values.
        bios_knob_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self._TME_TMEMT_ON)
        self.check_knobs(bios_knob_file, set_on_fail=True)

        # Enter into UEFI Shell command to run MKTMETool.efi
        self.apply_uefi_random_key()
        # Now the SUT is in BIOS menu, reboot the SUT to enter into OS mode.
        self.reboot_sut()

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MktmeMemCompatibilityNUMASNCWindows.main() else Framework.TEST_RESULT_FAIL)
