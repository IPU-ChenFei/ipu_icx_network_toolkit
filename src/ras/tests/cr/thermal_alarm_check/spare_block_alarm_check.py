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
import src.lib.content_exceptions as content_exception

from dtaf_core.lib.dtaf_constants import Framework

from src.ras.tests.cr.thermal_alarm_check.thermal_alarm_check_common import ThermalAlarmCheckCommon
from src.memory.tests.memory_cr.apache_pass.provisioning.cr_provisioning_1lm_100_appdirect_interleaved_block \
    import CRProvisioning1LM100AppDirectInterLeavedBlockLinux


class SpareBlockAlarmCheck(ThermalAlarmCheckCommon):

    """
    Glasgow_id : 59282
    This Test the correct behavior of the alarms when the Temperature value or the Threshold value is modified.
    DCPMMs are provisioned as 1LM, 100% AppDirect Interleaved or Not-Interleaved.

    sbe: Spare Block Enable
    sbt: Spare Block Threshold

    Test Case Flow:
    Bios knobs
    Check DIMM Health
    Set alarms and thresholds
    Check alarm reporting with remaining percentage in Th+1, Th and Th-1
    Check alarm reporting with threshold in Current remaining percentage -x, Current remaining percentage ,
    Current remaining percentage +x
    """
    _BIOS_CONFIG_FILE = "spare_block_alarm_check_bios_knobs.cfg"
    _SPARE_BLOCK_THRESHOLD_IN_PERCENTAGE = 50
    _OS_LOG_SIG_LIST = ["Hardware error", "Thermal Alarm Trip"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new ThermalAlarmCheck object
        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(SpareBlockAlarmCheck, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)
        self._provisioning_obj = CRProvisioning1LM100AppDirectInterLeavedBlockLinux(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        1. 1LM Provisioning
        2. Clear All Os Logs before Starting the Test Case
        3. Setting the bios knobs to its default mode.
        4. Setting the bios knobs as per the test case.
        5. Rebooting the SUT to apply the new bios settings.
        6. Verifying the bios knobs that are set.
        :return: None
        """
        self._provisioning_obj.prepare()
        if self._provisioning_obj.execute():
            self._log.info("System is provisioned as per Test Case")
        else:
            log_err = "Please check the system configuration and Provision"
            self._log.error(log_err)
            raise content_exception.TestSetupError("SUT is not provisioned as per Test Case Requirement")

        self._common_content_lib.clear_all_os_error_logs()
        self._log.info("Set and Verify the bios knobs")
        self._bios_util.set_bios_knob()
        self._sdp.pulse_pwr_good()
        self._os.wait_for_os(self._reboot_timeout)
        self._bios_util.verify_bios_knob()

    def execute(self):
        """
        1. Check the dimm information like: status, topology, and manageability of dimm with
        populate_memory_dimm_information()
        2. Set the DCPMM ACCESS PATH TO AUTO and Refresh topology
        3. Obtain the list of DCPMM.
        4. Identify target DCPMM.
        5. Check DCPMM health.
        6. Check alarm Current State.
        7. Set percentage alarm threshold and verify it.
        8. Os Log Verification.
        """
        self._ipmctl_provider.get_memory_dimm_information()
        self._ipmctl_provider.get_list_of_dimms_which_are_healthy_and_manageable()
        self.set_dcpmm_access_path_to_auto_and_refresh_topology()
        self.obtaining_list_of_dcpmm_dimms()
        self.identifying_target_dcpmm()
        self.checking_dcpmms_health()
        self.checking_alarms_current_state()
        # Enable Alarm and set threshold to 50
        self.set_percentage_alarm_thresholds_and_verify(spare_block_threshold=self._SPARE_BLOCK_THRESHOLD_IN_PERCENTAGE,
                                                        expected_tripped_state="False", alarm_spares_state="False",
                                                        package_sparing_has_happened=False)
        # Set the DIMM remaining percentage value to threshold+2 in C-Scripts
        self.set_dimm_percentage_and_verify(spare_block_threshold=self._SPARE_BLOCK_THRESHOLD_IN_PERCENTAGE+2,
                                            expected_tripped_state="False", alarm_spares_state=False,
                                            package_sparing_has_happened=False)
        # Set the DIMM remaining percentage value to match the threshold in C-Scripts
        self.set_percentage_alarm_thresholds_and_verify(spare_block_threshold=self._SPARE_BLOCK_THRESHOLD_IN_PERCENTAGE,
                                                        expected_tripped_state="False", alarm_spares_state=False,
                                                        package_sparing_has_happened=False)
        # Set the DIMM remaining percentage value to "threshold-2" in C-Scripts
        self.set_dimm_percentage_and_verify(spare_block_threshold=self._SPARE_BLOCK_THRESHOLD_IN_PERCENTAGE-2,
                                            expected_tripped_state="True", alarm_spares_state=True,
                                            package_sparing_has_happened=False)
        # Set threshold to CurrPercentRemain-3 in C-Scripts
        self.set_percentage_alarm_thresholds_and_verify(spare_block_threshold=self._SPARE_BLOCK_THRESHOLD_IN_PERCENTAGE
                                                        -5, expected_tripped_state=False, alarm_spares_state=False,
                                                        flag=3, package_sparing_has_happened=False)
        # Set threshold to match the CurrPercentRemain in C-Scripts
        self.set_percentage_alarm_thresholds_and_verify(spare_block_threshold=self._SPARE_BLOCK_THRESHOLD_IN_PERCENTAGE
                                                        -2, expected_tripped_state=False, alarm_spares_state=False,
                                                        flag=2, package_sparing_has_happened=False)
        # Set threshold to CurrPercentRemain+1 using C-SCripts
        self.set_percentage_alarm_thresholds_and_verify(spare_block_threshold=self._SPARE_BLOCK_THRESHOLD_IN_PERCENTAGE
                                                        +1, expected_tripped_state=True, alarm_spares_state=True,
                                                        sw_tr_flag=True, flag=-1, package_sparing_has_happened=False)

        # Set threshold to CurrPercentRemain-1 in C-Scripts
        self.set_percentage_alarm_thresholds_and_verify(spare_block_threshold=self._SPARE_BLOCK_THRESHOLD_IN_PERCENTAGE
                                                        -1, expected_tripped_state=False, alarm_spares_state=False,
                                                        package_sparing_has_happened=False, flag=1)
        self.clear_dcpmm_errors()
        if not self._os.is_alive():
            self._sdp.pulse_pwr_good()
            self._os.wait_for_os(self._reboot_timeout)
        self._log.info("Verify Os Log")
        ret_val = self._os_log_obj.verify_os_log_error_messages(__file__, self._os_log_obj.DUT_DMESG_FILE_NAME,
                                                                self._OS_LOG_SIG_LIST, check_error_not_found_flag=True)
        if ret_val:
            self._log.info("No unexpected OS error logs indicated")
        else:
            log_err = "Unexpected OS error logs was indicated"
            self._log.error(log_err)
            raise content_exception.TestFail(log_err)

        ret_val = self._os_log_obj.verify_os_log_error_messages(__file__, self._os_log_obj.DUT_MESSAGES_FILE_NAME,
                                                                self._OS_LOG_SIG_LIST, check_error_not_found_flag=True)
        if ret_val:
            self._log.info("No unexpected OS error logs indicated")
        else:
            log_err = "Unexpected OS error logs was indicated"
            self._log.error(log_err)
            raise content_exception.TestFail(log_err)

        ret_val = self._os_log_obj.verify_os_log_error_messages(__file__, self._os_log_obj.DUT_JOURNALCTL_FILE_NAME,
                                                                self._OS_LOG_SIG_LIST, check_error_not_found_flag=True)
        if ret_val:
            self._log.info("No unexpected OS error logs indicated")
        else:
            log_err = "Unexpected OS error logs was indicated"
            self._log.error(log_err)
            raise content_exception.TestFail(log_err)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SpareBlockAlarmCheck.main() else Framework.TEST_RESULT_FAIL)

