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

from src.ras.tests.cr.thermal_alarm_check.thermal_alarm_check_common import ThermalAlarmCheckCommon


class ThermalAlarmCheck(ThermalAlarmCheckCommon):
    """
        Glasgow_id : 59281
        This TestCase is a Verification of DCPMM sensor reporting functionality at a platform level OS environment.
        Test case involves display of the DIMM health info on one or more DCPMM present in a system when the DCPMM media
        temperature reporting is above threshold, same as threshold and less than threshold and Threshold Value is Same
        as Current Dimm Temperature , Less than Dimm Temperature and More than Dimm Temperature.
    """
    _BIOS_CONFIG_FILE = "thermal_alarm_check_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new ThermalAlarmCheck object
        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(ThermalAlarmCheck, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Setting the bios knobs to its default mode.
        3. Setting the bios knobs as per the test case.
        4. Rebooting the SUT to apply the new bios settings.
        5. Verifying the bios knobs that are set.
        :return: None
        """
        self._common_content_lib.clear_all_os_error_logs()
        self._log.info("Setting the Bios Knobs to Default Settings")
        self._bios.default_bios_settings()  # To set the Bios Knobs to its default mode.
        self._log.info("Setting the Bios Knobs as per our Test Case Requirements")
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._log.info("Bios Knobs are Set as per our TestCase and Reboot in Progress to Apply the Settings")
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.

    def execute(self):
        self.populate_memory_dimm_information()
        self.get_list_of_dimms_which_are_healthy_and_manageable()
        self.set_dcpmm_access_path_to_auto_and_refresh_topology()
        self.obtaining_list_of_dcpmm_dimms()
        self.identifying_target_dcpmm()
        self.checking_dcpmms_health()
        self.checking_alarms_current_state()

        # first set alarms for threshold media temperatures
        self.set_alarm_thresholds_and_verify(self._MEDIA_DIMM_THRESHOLD_VALUE,
                                             self._REGEX_CMD_FOR_MEDIA_TEMP_THRESHOLD,
                                             False
                                             )
        # set media temperature values to different threshold values and verify
        # set to threshold value + 1 and verify it trips
        self.set_dimm_temperature_and_verify(self._MEDIA_DIMM_THRESHOLD_VALUE + 1,
                                             self._REGEX_CMD_FOR_MEDIA_TEMP_TRIP,
                                             self._REGEX_CMD_FOR_MEDIA_TEMP_VALUE,
                                             True)  # should be in tripped state
        # set to threshold value and verify it trips
        self.set_dimm_temperature_and_verify(self._MEDIA_DIMM_THRESHOLD_VALUE,
                                             self._REGEX_CMD_FOR_MEDIA_TEMP_TRIP,
                                             self._REGEX_CMD_FOR_MEDIA_TEMP_VALUE,
                                             True)  # should be in tripped state
        # set to threshold value -1 and verify it does not trips
        self.set_dimm_temperature_and_verify(self._MEDIA_DIMM_THRESHOLD_VALUE - 1,
                                             self._REGEX_CMD_FOR_MEDIA_TEMP_NOT_TRIP,
                                             self._REGEX_CMD_FOR_MEDIA_TEMP_VALUE,
                                             False)  # should not be in tripped state
        # set threshold temperature value to current dimm temperature -1 and verify it trips
        self.set_alarm_thresholds_and_verify(self._MEDIA_DIMM_THRESHOLD_VALUE - 2,
                                             self._REGEX_CMD_FOR_MEDIA_TEMP_THRESHOLD,
                                             True,
                                             self._REGEX_CMD_FOR_MEDIA_TEMP_TRIP)  # should be in tripped state
        # set threshold temperature value to current dimm temperature and verify it trips
        self.set_alarm_thresholds_and_verify(self._MEDIA_DIMM_THRESHOLD_VALUE - 1,
                                             self._REGEX_CMD_FOR_MEDIA_TEMP_THRESHOLD,
                                             True,
                                             self._REGEX_CMD_FOR_MEDIA_TEMP_TRIP)  # should be in tripped state
        # set threshold temperature value to current dimm temperature +1 and verify it does not trips
        self.set_alarm_thresholds_and_verify(self._MEDIA_DIMM_THRESHOLD_VALUE,
                                             self._REGEX_CMD_FOR_MEDIA_TEMP_THRESHOLD,
                                             False,
                                             self._REGEX_CMD_FOR_MEDIA_TEMP_NOT_TRIP)  # should be in tripped state
        self.clear_dcpmm_errors()
        self.reset_all_dcpmm_thresholds()
        self.collect_all_logs()
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ThermalAlarmCheck.main() else Framework.TEST_RESULT_FAIL)
