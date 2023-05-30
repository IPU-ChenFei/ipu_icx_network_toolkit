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

from dtaf_core.lib.dtaf_constants import Framework
from src.ras.tests.pcie.pcie_cscripts_common import PcieCommon


class VerifyPcieCorrectedErrorThreshold(PcieCommon):
    """
    Glasgow ID: 59932

    This test case provides the validation plan and recipe for error reporting enhancement where corrected
    error reporting within the PCI Express module can be configured to only signal once a predetermined
    threshold is reached.

    """
    _BIOS_CONFIG_FILE = "pcie_corrected_error_threshold_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VerifyPcieCorrectedErrorThreshold object,

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :param arguments: None
        """
        super(VerifyPcieCorrectedErrorThreshold, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

    def prepare(self):
        """
        1. Set the bios knobs to its default mode.
        2. Set the bios knobs as per the test case.
        3. Reboot the SUT to apply the new bios settings.
        4. Verify the bios knobs that are set.

        :return: None
        """

        self._log.info("Clear all Linux OS logs...")
        self._common_content_lib.clear_all_os_error_logs()  # Clear all OS Log
        self._log.info("Set the BIOS Knobs to default settings")
        self._bios_util.load_bios_defaults()  # loading the default BIOS Knobs
        self._log.info("Set the Bios Knobs as per our Test Case Requirements")
        self._bios_util.set_bios_knob()  # Set the knobs as per TestCase
        self._log.info("Bios Knobs are Set as per our TestCase and Reboot in Progress to Apply the Settings")
        self._os.reboot(self._reboot_timeout)  # Rebooting the System
        self._bios_util.verify_bios_knob()  # Verify the BIOS Knob set properly

    def execute(self):
        """
        This test case provides the validation plan and recipe for error reporting enhancement where corrected
        error reporting within the PCI Express module can be configured to only signal once a predetermined
        threshold is reached.

        :return: True if passed else False
        :raise: None
        """
        ret_value = False
        self._log.info("Make sure that the UEFI-FW knobs are set correctly, check the  values of XPCORERRCOUNTER,"
                       " XPCORERRTHRESHOLD ")
        corerrthreshold_value = self.get_corrected_error_threshold()
        corerrcounter_value = self.get_corrected_error_counter()
        rootcon_seceen = self.get_rootcon_seceen_value()
        if corerrthreshold_value != self._PCIE_ERROR_COUNTER_VALUE[2] and \
                corerrcounter_value != self._PCIE_ERROR_COUNTER_VALUE[0] and \
                rootcon_seceen != self._PCIE_ERROR_COUNTER_VALUE[1]:
            self._log.error("UEFI knobs are not set Appropriately")
            raise RuntimeError("Failed to set UEFI Knobs!")
        self._log.info("Halt System to inject error..")
        self._sdp.halt()
        self._log.info("Inject PCIE Express Correctable Error")
        self.inject_and_verify_cscripts_pcie_errors()

        self._log.info("Bit [15:0] of XPCORERRCOUNTER is an error count which increments when an enabled"
                       "error is detected ")

        corerrcounter_value = self.get_corrected_error_counter()
        if corerrcounter_value != self._PCIE_ERROR_COUNTER_VALUE[1]:
            self._log.error("Bit [15:0] of XPCORERRCOUNTER is an error count which increments when an enabled"
                            "error is detected , error count is not incremented!")
            raise RuntimeError("XPCORERRCOUNTER not incremented!")

        self._log.info("Fetch the value of XPGLBERRSTS.pcie_aer_correctable_error")
        pcie_aer_correctable_error = self.obtain_xpglberrsts()
        if pcie_aer_correctable_error != self._PCIE_ERROR_COUNTER_VALUE[0]:
            self._log.error("XPGLBERRSTS.pcie_aer_correctable_error is not zero")
            raise RuntimeError("XPGLBERRSTS has to be zero until threshold has not reached 2")

        self._log.info("Inject PCIE Express Correctable Error Multiple times to reach threshold of 2")
        corerrcounter_value = self.get_corrected_error_counter()
        while corerrcounter_value != self._PCIE_ERROR_COUNTER_VALUE[2]:
            self.inject_and_verify_cscripts_pcie_errors()
            corerrcounter_value = self.get_corrected_error_counter()
            if corerrcounter_value == self._PCIE_ERROR_COUNTER_VALUE[2]:
                break

        # After injecting threshold number of errors, if xpglberrsts[2] = 0x1, it indicates a
        # receiver error escalation.  Since the errors that were injected are correctable errors (receiver errors),
        # then the value of xpglberrsts[2] = 0x1 (since bit[2] = pcie_aer_correctable_error).
        self._log("Check the value of xpglberrsts[2]")
        pcie_aer_correctable_error = self.obtain_xpglberrsts()
        if pcie_aer_correctable_error != self._PCIE_ERROR_COUNTER_VALUE[1]:
            self._log.error("XPGLBERRSTS.pcie_aer_correctable_error is not 1")
            raise RuntimeError("XPGLBERRSTS has to be 0x00000001 once threshold has reached 2")
        ret_value = True
        self._log.info("Collect dmesg logs!")
        self._common_content_lib.collect_dmesg_hardware_error_log()
        return ret_value


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VerifyPcieCorrectedErrorThreshold.main()
             else Framework.TEST_RESULT_FAIL)
