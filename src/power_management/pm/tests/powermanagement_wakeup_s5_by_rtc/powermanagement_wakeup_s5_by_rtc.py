#!/usr/bin/env python
###############################################################################
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
###############################################################################
import sys
import os
import time
from datetime import datetime, timedelta

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.bios_menu import BiosBootMenuProvider
from dtaf_core.providers.uefi_shell import UefiShellProvider
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.lib import content_exceptions
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.bios_util import ItpXmlCli
from src.lib.bios_util import BootOptions
from src.lib.install_collateral import InstallCollateral
from src.lib.uefi_util import UefiUtil


class PowerManagementWakeUpS5ByRtc(ContentBaseTestCase):
    """
    HPQC ID : H81606-PI_PowerManagement_WakeUpS5_By_RTC_L, H87934-PI_Powermanagement_WakeupS5ByRTC_W

    This test case rtc wake up s5 enable knob and checking No MCE or OS error
    shutdown os successfully and wakeup with out issues
    """
    TEST_CASE_ID = ["H81606", "PI_PowerManagement_WakeUpS5_By_RTC_L", "H87934", "PI_Powermanagement_WakeupS5ByRTC_W"]
    SHUTDOWN_CMD = 'shutdown -t 0'
    BIOS_CONFIG_FILE = "rtc_wake_system_from_s5.cfg"
    TIME_DELAY_IN_SEC = 120
    RTC_HOUR_KNOB_NAME = "RTCWakeupTimeHour"
    RTC_MINUTE_KNOB_NAME = "RTCWakeupTimeMinute"
    FOURTYFIVE_MINUTS = 45
    TEST_FILE_NAME = "C:\\test_file.txt"
    STR_HELLO_WORLD = "Hello World"
    TIME_CMD = "time"
    WAIT_TIME_OUT = 5

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of PowerManagementWakeUpS5ByRtc

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        self.rtc_wakeup_bios_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(PowerManagementWakeUpS5ByRtc, self).__init__(test_log, arguments, cfg_opts,
                                                           self.rtc_wakeup_bios_enable)
        self.install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        uefi_cfg = cfg_opts.find(UefiShellProvider.DEFAULT_CONFIG_PATH)
        self._uefi_obj = ProviderFactory.create(uefi_cfg, test_log)  # type: UefiShellProvider
        bios_boot_menu_cfg = cfg_opts.find(BiosBootMenuProvider.DEFAULT_CONFIG_PATH)
        self._bios_boot_menu_obj = ProviderFactory.create(bios_boot_menu_cfg,
                                                          test_log)  # type: BiosBootMenuProvider
        self._uefi_util_obj = UefiUtil(
            self._log,
            self._uefi_obj,
            self._bios_boot_menu_obj,
            self.ac_power,
            self._common_content_configuration, self.os)
        self.previous_boot_oder = None
        self.current_boot_order = None
        self._bios_boot_menu_entry_wait_time = self._common_content_configuration.bios_boot_menu_entry_wait_time()
        self._csp_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        csp = ProviderFactory.create(self._csp_cfg, self._log)  # type: SiliconRegProvider
        self.itp_xml_cli_util = ItpXmlCli(self._log, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Setting the Date and Time in SUT
        4. Adding 15 minutes to the current time and convert 24 hr format
        5. Set the bios knobs as per the test case.
        6. Reboot the SUT to apply the new bios settings.
        7. Verify the bios knobs whether they updated properly.
        """
        super(PowerManagementWakeUpS5ByRtc, self).prepare()

    def get_uefi_time(self):
        """
        This method will change boot order to uefi and revert back to previous boot order after getting uefi time

        :return: UEFI Time
        """
        self._log.info("Getting current boot order")
        self.previous_boot_oder = self.itp_xml_cli_util.get_current_boot_order_string()
        self._log.info("Current boot order {}".format(self.previous_boot_oder))
        self._log.info("Setting the default boot order to {}".format(BootOptions.UEFI))
        self.itp_xml_cli_util.set_default_boot(BootOptions.UEFI)
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self._log.info("waiting for UEFI shell")
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        time.sleep(self.WAIT_TIME_OUT)
        uefi_time_cmd_output = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.TIME_CMD)
        self._log.debug("uefi time command output:{}".format(uefi_time_cmd_output))
        self.itp_xml_cli_util.set_boot_order(self.previous_boot_oder)
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self._log.info("waiting for os to be alive")
        self.os.wait_for_os(self.reboot_timeout)
        self.current_boot_order = self.itp_xml_cli_util.get_current_boot_order_string()
        # capturing current time from uefi_time_cmd_output : ['time\r', '05:24:51 (LOCAL)\r', 'Shell> ']
        current_time = uefi_time_cmd_output[1].split(' ')[0]
        current_time = datetime.strptime(current_time, '%H:%M:%S')
        return current_time

    def set_rtc_wakeup_bios_time(self, current_time):
        """
        This method will add plus 45 minutes to current time and set RTC wake up time.

        :return: None
        """
        # Adding 45 minutes to the current time
        current_plus_45 = current_time + timedelta(minutes=self.FOURTYFIVE_MINUTS)
        # converting 24hr time format
        current_plus_45 = current_plus_45.strftime("%H:%M")
        self._log.info("Current time plus 45: {}".format(current_plus_45))
        # converting hours and minutes into hexa values
        current_hour = hex(int(current_plus_45.split(':')[0]))
        current_minutes = hex(int(current_plus_45.split(':')[1]))
        self.bios.set_bios_knobs(self.RTC_HOUR_KNOB_NAME, current_hour, overlap=True)
        self.bios.set_bios_knobs(self.RTC_MINUTE_KNOB_NAME, current_minutes, overlap=True)
        # Setting RTC wake up hours and minutes bios knobs
        self._common_content_lib.perform_os_reboot(self.reboot_timeout)
        actual_current_value = self.bios_util.get_bios_knob_current_value(self.RTC_HOUR_KNOB_NAME).strip(r"\r\n\t ")
        self._log.info("Actual current value of the %s bios knob is %s", self.RTC_HOUR_KNOB_NAME, actual_current_value)
        if eval(actual_current_value) != eval(str(current_hour)):
            raise content_exceptions.TestFail("%s value is not set" % self.RTC_HOUR_KNOB_NAME)
        actual_current_value = self.bios_util.get_bios_knob_current_value(self.RTC_MINUTE_KNOB_NAME).strip(r"\r\n\t ")
        self._log.info("Actual current value of the %s bios knob is %s", self.RTC_MINUTE_KNOB_NAME,
                       actual_current_value)
        if eval(actual_current_value) != eval(str(current_minutes)):
            raise content_exceptions.TestFail("%s value is not set" % self.RTC_MINUTE_KNOB_NAME)
        self._log.info("System wake up time is successfully set at {}".format(current_plus_45))

    def execute(self):
        """

        This method is Execute shutdown -t 0, wake up RTC  and check clear mce logs.

        :return: True or False
        :raise: content_exceptions.TestFail
        """
        current_time = self.get_uefi_time()
        self.set_rtc_wakeup_bios_time(current_time)
        self._common_content_lib.clear_mce_errors()
        if OperatingSystems.WINDOWS == self.os.os_type:
            self._log.info("Creating the Text file")
            self._common_content_lib.execute_sut_cmd('echo "{}">{}'.format(self.STR_HELLO_WORLD, self.TEST_FILE_NAME),
                                                     "Creating the Test file", self._command_timeout)
            result = self._common_content_lib.execute_sut_cmd("more {}".format(self.TEST_FILE_NAME),
                                                              "getting content output", self._command_timeout)
            self._log.debug("Text contains of {} file:\n{}".format(self.TEST_FILE_NAME, result))
            self._log.info("Executing shutdown")
            try:
                self.os.shutdown(self._sut_shutdown_delay)
            except Exception as ex:
                self._log.error("Paramiko throws error sometime if OS is not alive. Ignoring this "
                                "exception '{}'...".format(ex))
        elif OperatingSystems.LINUX == self.os.os_type:
            self._log.info("Executing shutdown :{}".format(self.SHUTDOWN_CMD))
            self.os.execute_async(self.SHUTDOWN_CMD)
        else:
            raise content_exceptions.TestFail("This testcase is not implemented for: {}".format(self.os.os_type))
        time.sleep(self.TIME_DELAY_IN_SEC)
        if self.os.is_alive():
            raise content_exceptions.TestFail("Could not shutdown the SUT with command :{}".format(self.SHUTDOWN_CMD))
        self.os.wait_for_os(self.reboot_timeout + (self.FOURTYFIVE_MINUTS*60))
        self._log.info("RTC Wakeup happened successfully ")
        if OperatingSystems.WINDOWS == self.os.os_type:
            result = self._common_content_lib.execute_sut_cmd("more {}".format(self.TEST_FILE_NAME),
                                                              "getting content output", self._command_timeout)
            self._log.debug("Text contains of {} file:\n{}".format(self.TEST_FILE_NAME, result))
            if self.STR_HELLO_WORLD not in result:
                raise content_exceptions.TestFail("File content is not present after RTC wakeup")
            self._log.info("Successfully verified File content is present on SUT after RTC wakeup")
        errors = self._common_content_lib.check_if_mce_errors()
        self._log.debug("MCE errors: %s", errors)
        if errors:
            raise content_exceptions.TestFail("There are MCE errors after Wakeup by RTC: %s", errors)
        self._log.info("Test has been completed successfully!")

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        if str(self.current_boot_order) != str(self.previous_boot_oder):
            self.itp_xml_cli_util.set_boot_order(self.previous_boot_oder)
            self.perform_graceful_g3()
        super(PowerManagementWakeUpS5ByRtc, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PowerManagementWakeUpS5ByRtc.main()
             else Framework.TEST_RESULT_FAIL)
