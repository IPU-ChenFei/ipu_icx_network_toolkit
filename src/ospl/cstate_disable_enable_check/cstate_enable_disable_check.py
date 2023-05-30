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
import os

from dtaf_core.lib.dtaf_constants import Framework

from src.power_management.socwatch_common import SocWatchBaseTest
from src.provider.socwatch_provider import CoreCStates


class CStateEnableDisableCheck(SocWatchBaseTest):
    """
    HPQC ID : H82176-PI_Powermanagement_Power_Cstate_Disable-enable_check_SoCwatch_L
    This Test case install SocWatch Tool in the SUT and Execute the Socwatch command
    Verify the Package C-State and Core C-state residency values
    """
    TEST_CASE_ID = ["H82176", "PI_Powermanagement_Power_Cstate_Disable-enable_check_SoCwatch_L"]
    BIOS_CONFIG_FILE_ENABLE = "power_cstate_enable_bios_knobs.cfg"
    BIOS_CONFIG_FILE_DISABLE = "power_cstate_disable_bios_knobs.cfg"
    SOCWATCH_RUN_TIME = 900
    SOCWATCH_RUN_TIME_CSTATE_DISABLE = 600
    SYSTEM_IDLE_TIME = 300  # system idle time in seconds
    CC6_CSTATE_ENABLE_THRESHOLD = 70
    CC6_CSTATE_DISABLE_THRESHOLD = 20
    CC0_CC1_CSTATE_DISABLE_THRESHOLD = 70

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of CStateEnableDisableCheck

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.cstate_bios_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                               self.BIOS_CONFIG_FILE_ENABLE)
        super(CStateEnableDisableCheck, self).__init__(test_log, arguments, cfg_opts, self.cstate_bios_enable)
        self.cstate_bios_disable = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                self.BIOS_CONFIG_FILE_DISABLE)

    def prepare(self):
        # type: () -> None
        """
        This function will Clear the mce errors and load bios defaults to SUT
        """
        super(CStateEnableDisableCheck, self).prepare()
        self._common_content_lib.update_micro_code()

    def execute(self):
        """
        This function install socwatch and execute socwatch
        Copy CSV file to host, read and verify the C-state values
        Setting the C-state bios to disable and repeat the same steps twice

        :return: True if test completed successfully, False otherwise.
        """
        self.execute_socwatch_tool(socwatch_runtime=self.SOCWATCH_RUN_TIME, system_idle_timeout=self.SYSTEM_IDLE_TIME,
                                   execute_stress=False)
        # Verify the Core/Package C-state residency values
        self._log.info("Verify Core C-State residency percentage for CC1/CC6")
        self.csv_reader_obj.verify_core_c_state_residency(CoreCStates.CORE_C_STATE_CC6, "%s > %d" % (
            CoreCStates.CORE_C_STATE_CC6, self.CC6_CSTATE_ENABLE_THRESHOLD))

        # Step2: Disable the C-state bios
        self.set_verify_bios_knobs(self.cstate_bios_disable)

        self.execute_socwatch_tool(socwatch_runtime=self.SOCWATCH_RUN_TIME_CSTATE_DISABLE,
                                   execute_stress=False)

        # Verify Core C-State residency values
        try:
            self._log.info("Verify Core C-State residency percentage CC0")
            self.csv_reader_obj.verify_core_c_state_residency(CoreCStates.CORE_C_STATE_CC0,
                                                              "%s > %d" % (CoreCStates.CORE_C_STATE_CC0,
                                                                           self.CC0_CC1_CSTATE_DISABLE_THRESHOLD))
        except Exception as e:
            self._log.debug("Verification for CC0 got failed due to exception {}".format(e))
            self._log.info("Verify Core C-State residency percentage CC1")
            self.csv_reader_obj.verify_core_c_state_residency(CoreCStates.CORE_C_STATE_CC1,
                                                              "%s > %d" % (CoreCStates.CORE_C_STATE_CC1,
                                                                           self.CC0_CC1_CSTATE_DISABLE_THRESHOLD))
        self._log.info("Verify Core C-State residency percentage CC6")
        self.csv_reader_obj.verify_core_c_state_residency(CoreCStates.CORE_C_STATE_CC6,
                                                          "%s < %d" % (CoreCStates.CORE_C_STATE_CC6,
                                                                       self.CC6_CSTATE_DISABLE_THRESHOLD))
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(CStateEnableDisableCheck, self).cleanup(return_status)
        if self.os.is_alive():
            self._common_content_lib.delete_micro_code()
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CStateEnableDisableCheck.main() else Framework.TEST_RESULT_FAIL)
