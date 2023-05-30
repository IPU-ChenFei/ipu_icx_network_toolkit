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
import time

from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.ac_power import AcPowerControlProvider

from src.ras.tests.cr.thermal_alarm_check.thermal_alarm_check_common import ThermalAlarmCheckCommon


class ThermalEventCheck(ThermalAlarmCheckCommon):
    """
    Glasgow ID: 58848
    This TestCase is a Verification of DC Persistent Memory sensor reporting functionality
    at a platform level OS environment. Test case involves display of the Dual Inline Memory
    health info on one or more DC Persistent Memory present in a system when the DCPMM media
    temperature reporting is above threshold. Acceptable sensor readings are returned.
    Overall status is expected to reflect that the DC Persistent Memory(s) are healthy.
    Command line access to DC Persistent management functionality is available through the
    ipmctl component. The CLI utilities exposes available management features of the underlying DCPMMs.
    """
    _BIOS_CONFIG_FILE = "thermal_event_check_bios_knob.cfg"
    _AC_POWER_TIME_OUT = 3
    _AC_POWER_WAIT_TIME = 30

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new ThermalEventCheck object,

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :param arguments: None
        """
        super(ThermalEventCheck, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)
        ac_power_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac_power = ProviderFactory.create(ac_power_cfg, test_log)

    def prepare(self):
        # type: () -> None
        """
        1. Setting the bios knobs to its default mode.
        2. Setting the bios knobs as per the test case.
        3. Rebooting the SUT to apply the new bios settings.
        4. Verifying the bios knobs that are set.

        :return: None
        """

        self._log.info("Clearing all Linux OS logs...")
        self._common_content_lib.clear_all_os_error_logs()  # Clear all OS Log
        self._log.info("Setting the BIOS Knobs to default settings")
        self._bios_util.load_bios_defaults()  # loading the default BIOS Knobs
        self._log.info("Setting the Bios Knobs as per our Test Case Requirements")
        self._bios_util.set_bios_knob()  # Set the knobs as per TestCase
        self._log.info("Bios Knobs are Set as per our TestCase and Reboot in Progress to Apply the Settings")
        self._os.reboot(self._reboot_timeout)  # Rebooting the System
        self._bios_util.verify_bios_knob()  # Verify the BIOS Knob set properly

    def execute(self):
        """
        1. Check the dimm information like: status, topology, and manageability of dimm with
        populate_memory_dimm_information()
        2. Injecting the temperature error to dimm with calling the function inject_dual_inline_memory_temperature_error
        3. Checking the OS is alive or not.
        4. AC Power On.
        5. Checking the injected error is present or not and clearing it.
        6. Clearing all the Error Log and clear the Dimm History and reset the Target with log_dcpmm_error_detail.
        7. Collecting all logs with calling collect_all_logs()

        :return: None
        :raise: None
        """
        try:
            ret_val = False
            self.populate_memory_dimm_information()  # Call to check or get Dimm Information
            self.inject_dual_inline_memory_temperature_error()  # Call to inject the temperature on dimm

            if not self._os.is_alive():  # Check to OS is alive
                self._log.info("SUT got powered OFF after injecting error and perform power cycle to bring SUT UP..")
                if self._ac_power.ac_power_off(self._AC_POWER_TIME_OUT):
                    self._log.info("AC power supply has been removed")
                else:
                    log_error = "Failed to power-off SUT.."
                    self._log.error(log_error)
                    raise RuntimeError(log_error)
                time.sleep(self._AC_POWER_WAIT_TIME)
                if self._ac_power.ac_power_on(self._AC_POWER_TIME_OUT):
                    self._log.info("AC power supply has been connected")
                else:
                    log_error = "Failed to power-on SUT.."
                    self._log.error(log_error)
                    raise RuntimeError(log_error)
                self._os.wait_for_os(self._os_time_out_in_sec)  # Wait for System to come in OS State
            else:
                log_error = "SUT should not have been in OS after injecting thermal error..."
                raise RuntimeError(log_error)

            self.detected_injected_temp_error()  # Call a function to detect the injected temperature Error
            ret_val = True
        except Exception as ex:
            raise ex
        finally:
            self.clear_dcpmm_errors()  # Call a Function to Clear all error using itp command
            if not self._os.is_alive():
                self._os.wait_for_os(self._os_time_out_in_sec)
            self.collect_all_logs()  # Call to collect the all logs.

        return ret_val


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ThermalEventCheck.main()
             else Framework.TEST_RESULT_FAIL)

