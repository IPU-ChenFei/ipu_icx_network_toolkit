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

from src.ras.tests.pcie.pcie_cscripts_common import PcieCommon


class IehGlobalMaskPcieFatalError(PcieCommon):
    """
    Glasgow_id : 58518
    This test injects a PCIE Fatal Error and verifies the IEH global error status register if error is masked.
    """
    _BIOS_CONFIG_FILE = "pcie_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new IehGlobalMaskPcieFatalError object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(IehGlobalMaskPcieFatalError, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs whether they updated properly.

        :return: None
        """
        if self._cscripts.silicon_cpu_family in self._common_content_lib.SILICON_10NM_CPU:
            self._pcie_telemetry.collect_io_telemetry_to_csv("IehGlobalMaskPcieFatalError", 0)
            self._common_content_lib.clear_all_os_error_logs()  # This Method is used to Clear All OS Logs.
            self.verify_injection_port_address() #This Method is used to verify injection port address
            self._log.info("Set the Bios Knobs to Default Settings")
            self._bios.default_bios_settings()  # To set the Bios Knobs to its default mode.
            self._log.info("Set the Bios Knobs as per our Test Case Requirements")
            self._bios_util.set_bios_knob()  # To set the bios knob setting.
            self._log.info("Bios Knobs are Set as per our TestCase and Reboot to Apply the Settings")
            self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
            self._bios_util.verify_bios_knob()  # To verify the bios knob settings.
        else:
            log_error = "Not Implemented for other than 10nm"
            self._log.error(log_error)
            raise NotImplementedError(log_error)

    def execute(self):
        """
        1. verify_if_any_previous_correctable_errors - To check if there are any Previous Errors
        2. enabling_ieh_mask - Enabling the Mask by Changing the Register Access and
         Reverting the Access after Enabling.
        3. injecting_pcie_fatal_error_and_mask - Inject Pcie Fatal Error and Check if the Error is Masked

        :return: True or False
        """
        self.verify_no_current_ieh_errors()
        self.enable_ieh_mask(error_type="fatal")
        return self.inject_and_verify_ieh_pcie_fatal_error_and_mask()

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        self._pcie_telemetry.collect_io_telemetry_to_csv("IehGlobalMaskPcieFatalError", 1)
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self.os.wait_for_os(self.reboot_timeout)
        super(IehGlobalMaskPcieFatalError, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if IehGlobalMaskPcieFatalError.main() else Framework.TEST_RESULT_FAIL)
