#!/usr/bin/env python
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and propri-
# etary and confidential information of Intel Corporation and its suppliers and
# licensors, and is protected by worldwide copyright and trade secret laws and
# treaty provisions. No part of the Material may be used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or disclosed
# in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be ex-
# press and approved by Intel in writing.

import datetime
import os
import re
import sys
import time
from ast import literal_eval

from src.lib import redfish_common, content_exceptions
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral


class RedFishTestCommon(ContentBaseTestCase):
    """
    This class is used to verify whether the user is able to turn Off/on/Restart the server on via the ResetType@Redfish command

    """
    _REDFISH_BASIC_URL = "/redfish/v1/"
    _REDFISH_AUTHENTICATION_URL = "/redfish/v1/Systems"
    _REDFISH_SYSTEM_URL = "/redfish/v1/Systems/system"
    _REDFISH_SYSTEM_RESET_URL = "/redfish/v1/Systems/system/Actions/ComputerSystem.Reset"
    _REDFISH_UPDATE_FIRMWARE_URL = "/redfish/v1/UpdateService"
    _REDFISH_FILE_UPLOAD_CMD = " --data-binary @{}"
    _REDFISH_GRACEFULSHUTDOWN_JSON = r"{\"ResetType\": \"GracefulShutdown\"}"
    _REDFISH_GRACEFUL_RESTART_JSON = r"{\"ResetType\": \"GracefulRestart\"}"
    _REDFISH_FORCEOFF_JSON = r"{\"ResetType\": \"ForceOff\"}"
    _REDFISH_POWERON_JSON = r"{\"ResetType\": \"On\"}"
    _REDFISH_FORCEON_JSON = r"{\"ResetType\": \"ForceOn\"}"
    _REDFISH_FORCE_RESTART_JSON = r"{\"ResetType\": \"ForceRestart\"}"
    _REDFISH_UNCHECK_FORCE_ENTER_BIOS_SETUP = r"{\"Boot\":{\"BootSourceOverrideEnabled\":\"Disabled\",\"BootSourceOverrideTarget\":\"None\"}}"
    _REDFISH_CHECK_FORCE_ENTER_BIOS_SETUP = r"{\"Boot\":{\"BootSourceOverrideEnabled\":\"Continuous\",\"BootSourceOverrideTarget\":\"BiosSetup\"}}"
    _SUCCESS_RESPONSE_STRING = "Successfully Completed Request"
    _FIRMWARE_UPDATE_CHECK_SUCCESS = "ServiceEnabled\": true"
    _FIRMWARE_UPDATE_TASK_STATUS = "Running"
    _204_RESPONSE_CODE = "204 No Content"
    _BMC_INFO_CMD = "ipmitool bmc info"
    _REGEX_FIRMWARE = r"Firmware Revision\s+:\s(\d+.\d+)"
    _REDFISH_SEL_ENTRIES_URL = "/redfish/v1/Systems/system/LogServices/EventLog/Entries"
    _REDFISH_SEL_CLEAR_ENTRIES_URL = "/redfish/v1/Systems/system/LogServices/EventLog/Actions/LogService.ClearLog"
    _POWER_BUTTON_POWER_OFF = "gsettings set org.gnome.settings-daemon.plugins.power power-button-action interactive"
    _SYSTEMCTL_RESTART_CMD = "systemctl restart systemd-logind"
    _SYSTEMCTL_MASK_CMD = "systemctl {} sleep.target suspend.target hibernate.target hybrid-sleep.target"
    _MASK = "mask"
    _UNMASK = "unmask"
    _SYSTEMD_LOGIN_FILE = "/etc/systemd/logind.conf"
    _SED_CMD_TO_CHANGE_PWR_SETTING = "sed -i -e 's/{}/{}/g' {}"
    _LOGIN_SETTING_KEY = "HandlePowerKey"
    _HASH = "#"
    _SEL_KEY_SEVERITY = 'Severity'
    _SEL_KEY_CREATED = 'Created'
    _SEL_SEVERITY_WARNING = "Warning"
    _SEL_SEVERITY_CRITICAL = "Critical"
    _SEL_KEY_MESSAGE = 'Message'
    _SEL_KEY_MEMBERS = 'Members'

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of RedFishCommon

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        super(RedFishTestCommon, self).__init__(test_log, arguments, cfg_opts)
        self._redfish_obj = redfish_common.RedFishCommon(test_log, cfg_opts)
        self.wait_time_for_graceful_shutdown = int(self._common_content_configuration.memory_next_reboot_wait_time())*2
        self.wait_time_for_reboot = self._common_content_configuration.get_reboot_timeout()
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        call base class prepare function

        :return: None
        """
        # we do not need to set any bios knobs, we will not call base prepare function
        pass

    def check_redfish_basic_authentication(self):
        """
        Remote Access (Redfish) - To check the  access via RedFish API

        :returns : boolean
        """
        ret_value = True
        json_response_data = self._redfish_obj.curl_get(self._REDFISH_BASIC_URL)
        if self._REDFISH_AUTHENTICATION_URL not in str(json_response_data):
            log_error = "Error - Redfish URL : {} is not Correct - {}".format(self._REDFISH_BASIC_URL,
                                                                              json_response_data)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        self._log.info("Successfully tested the Redfish API without Errors!")

        json_response_data = self._redfish_obj.curl_get(self._REDFISH_AUTHENTICATION_URL)
        if self._REDFISH_SYSTEM_URL not in str(json_response_data):
            log_error = "Error - Redfish URL : {} is not Correct - {}".format(self._REDFISH_AUTHENTICATION_URL,
                                                                              json_response_data)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        self._log.info("Successfully tested the Redfish API for Basic Authentication without Errors!")
        return ret_value

    def check_sel(self):
        """
        This Method checks for unexpected SEL events!

        :returns : boolean
        """
        ret_value = True
        json_response_data = self._redfish_obj.curl_get(self._REDFISH_SEL_ENTRIES_URL)
        sel_entries_dict = literal_eval(json_response_data.decode('utf8').strip("\r\n"))
        self._log.info("check the SEL for any unexpected events!")
        for each_sel_entry in sel_entries_dict[self._SEL_KEY_MEMBERS]:
            if each_sel_entry:
                if str(datetime.datetime.now().date()) == each_sel_entry[self._SEL_KEY_CREATED].split("T")[0]:
                    if each_sel_entry[self._SEL_KEY_SEVERITY] == self._SEL_SEVERITY_CRITICAL:
                        ret_value = False
                        self._log.info("Severity : {}".format(each_sel_entry[self._SEL_KEY_SEVERITY]))
                        self._log.info("Time Stamp : {}".format(each_sel_entry[self._SEL_KEY_CREATED]))
                        self._log.info("Description : {}".format(each_sel_entry[self._SEL_KEY_MESSAGE]))
        if ret_value:
            self._log.info("Unexpected SEL critical events not found!")
        return ret_value

    def redfish_force_off(self):
        """
        This Method Force off the System using Redfish API.

        :raises: RuntimeError
        """
        json_response_data = self._redfish_obj.curl_post(self._REDFISH_SYSTEM_RESET_URL,
                                                         request_body=self._REDFISH_FORCEOFF_JSON)
        if self._SUCCESS_RESPONSE_STRING not in str(json_response_data):
            log_error = "Error - Redfish URL : {} is not Correct - {}".format(self._REDFISH_SYSTEM_RESET_URL,
                                                                              json_response_data)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        time.sleep(self._common_content_configuration.ac_power_off_wait_time())
        if not self.os.is_alive():
            self._log.info("System turned Off through RedFish POST without errors!")
        else:
            log_error = "System failed to turn Off through RedFish POST!"
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def redfish_force_on(self):
        """
        This Method Force off the System using Redfish API.

        :raises: RuntimeError
        """
        json_response_data = self._redfish_obj.curl_post(self._REDFISH_SYSTEM_RESET_URL,
                                                         request_body=self._REDFISH_FORCEON_JSON)
        if self._SUCCESS_RESPONSE_STRING not in str(json_response_data):
            log_error = "Error - Redfish URL : {} is not Correct - {}".format(self._REDFISH_SYSTEM_RESET_URL,
                                                                              json_response_data)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        self.os.wait_for_os(self._common_content_configuration.get_reboot_timeout())
        self._log.info("System Forced On and booted through RedFish POST without errors!")

    def redfish_power_on(self):
        """
        This Method Force off the System using Redfish API.

        :raises: RuntimeError
        """
        time.sleep(self.wait_time_for_graceful_shutdown)
        json_response_data = self._redfish_obj.curl_post(self._REDFISH_SYSTEM_RESET_URL,
                                                         request_body=self._REDFISH_POWERON_JSON)

        if self._SUCCESS_RESPONSE_STRING not in str(json_response_data):
            log_error = "Error - Redfish URL : {} is not Correct - {}".format(self._REDFISH_SYSTEM_RESET_URL,
                                                                              json_response_data)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        self.os.wait_for_os(self._common_content_configuration.get_reboot_timeout())
        self._log.info("System turned On and booted through RedFish POST without errors!")
        time.sleep(self.wait_time_for_graceful_shutdown)

    def redfish_graceful_shutdown(self):
        """
        This Method Shuts down the System Gracefully using Redfish API.

        :raises: RuntimeError
        """
        json_response_data = self._redfish_obj.curl_post(self._REDFISH_SYSTEM_RESET_URL,
                                                         request_body=self._REDFISH_GRACEFULSHUTDOWN_JSON)

        if self._SUCCESS_RESPONSE_STRING not in str(json_response_data):
            log_error = "Error - Redfish URL : {} is not Correct - {}".format(self._REDFISH_SYSTEM_RESET_URL,
                                                                              json_response_data)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        nowtime = datetime.datetime.now()
        time.sleep(self.wait_time_for_graceful_shutdown)
        while (datetime.datetime.now() - nowtime).seconds < int(self.wait_time_for_graceful_shutdown):
            if not self.os.is_alive():
                self._log.info("System is not Alive")
                break
            else:
                self._log.debug("System is Alive yet waiting for some more time")
        if self.os.is_alive():
            log_error = "System failed to Shutdown Gracefully through RedFish POST!"
            self._log.error(log_error)
            raise RuntimeError(log_error)
        self._log.info("System Shutdown Gracefully through RedFish POST!")
        time.sleep(self.wait_time_for_graceful_shutdown)

    def redfish_force_restart(self):
        """
        This Method force restarts the System using Redfish API

        :return: None
        """
        json_response_data = self._redfish_obj.curl_post(self._REDFISH_SYSTEM_RESET_URL,
                                                         request_body=self._REDFISH_FORCE_RESTART_JSON)
        if self._SUCCESS_RESPONSE_STRING not in str(json_response_data):
            log_error = "Error - Redfish URL : {} is not Correct - {}".format(self._REDFISH_SYSTEM_RESET_URL,
                                                                              json_response_data)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        self._log.info("The force restart redfish command sent successfully..")
        self._log.info("Waiting for system to boot to OS...")
        self.os.wait_for_os(self._common_content_configuration.get_reboot_timeout())
        self._log.info("System turned On and booted through RedFish POST without errors!")

    def system_forceon_async(self):
        """
        This Method force restarts the System using Redfish API without waiting for OS to boot up

        :return: None
        """
        json_response_data = self._redfish_obj.curl_post(self._REDFISH_SYSTEM_RESET_URL,
                                                         request_body=self._REDFISH_FORCEON_JSON)
        if self._SUCCESS_RESPONSE_STRING not in str(json_response_data):
            log_error = "Error - Redfish URL : {} is not Correct - {}".format(self._REDFISH_SYSTEM_RESET_URL,
                                                                              json_response_data)
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def redfish_check_uncheck_force_enter_bios_setup(self, check=False):
        """
        This Method checks/unchecks the "Force enter BIOS Setup" Option in WebGUI based on check parameter passed.

        :return: None
        """
        if check:
            json_response_data = self._redfish_obj.curl_patch(self._REDFISH_SYSTEM_URL,
                                                             request_body=self._REDFISH_CHECK_FORCE_ENTER_BIOS_SETUP)
        else:
            json_response_data = self._redfish_obj.curl_patch(self._REDFISH_SYSTEM_URL,
                                                              request_body=self._REDFISH_UNCHECK_FORCE_ENTER_BIOS_SETUP)

        if self._204_RESPONSE_CODE not in str(json_response_data):
            log_error = "Error - Redfish URL : {} is not Correct - {}".format(self._REDFISH_SYSTEM_RESET_URL,
                                                                              json_response_data)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        if check:
            self._log.info("Force Enter BIOS Setup Option Checked Successfully without errors!")
        else:
            self._log.info("Force Enter BIOS Setup Option Unchecked Successfully without errors!")

    def redfish_graceful_restart(self):
        """
        This Method Restarts the System Gracefully using Redfish API.

        :raises: RuntimeError
        """
        json_response_data = self._redfish_obj.curl_post(self._REDFISH_SYSTEM_RESET_URL,
                                                         request_body=self._REDFISH_GRACEFUL_RESTART_JSON)

        if self._SUCCESS_RESPONSE_STRING not in str(json_response_data):
            log_error = "Error - Redfish URL : {} is not Correct - {}".format(self._REDFISH_SYSTEM_RESET_URL,
                                                                              json_response_data)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        self.os.wait_for_os(self.wait_time_for_reboot)
        self._log.info("System Graceful Restart Successful!")

    def clear_sel(self):
        """
        This Method clears SEL events!

        :returns : boolean
        """
        ret_value = True
        json_response_data = self._redfish_obj.curl_post(self._REDFISH_SEL_CLEAR_ENTRIES_URL)

        if self._SUCCESS_RESPONSE_STRING not in str(json_response_data):
            log_error = "Error - Redfish URL : {} is not Correct - {}".format(self._REDFISH_SYSTEM_RESET_URL,
                                                                              json_response_data)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        self._log.info("System Event Logs Cleared Successfully!")
        return ret_value

    def redfish_firmware_update(self, bmc_fw_path):
        """
        This Method Updates the BMC firmware using Redfish API

        :raise:  ContentException.TestError
        :return: True if BMC is updated elseFfalse
        """
        json_response_data = self._redfish_obj.curl_get(self._REDFISH_UPDATE_FIRMWARE_URL)
        if self._FIRMWARE_UPDATE_CHECK_SUCCESS not in str(json_response_data):
            log_error = "Error - Redfish URL : {} is not Correct - {}".format(self._REDFISH_UPDATE_FIRMWARE_URL,
                                                                              json_response_data)
            self._log.error(log_error)
            raise content_exceptions.TestError(log_error)
        self._log.info("Successfully tested the Redfish firmware update API for Basic Authentication without Errors!")

        curl_command = self._REDFISH_UPDATE_FIRMWARE_URL+ self._REDFISH_FILE_UPLOAD_CMD.format(bmc_fw_path)
        json_response_data = self._redfish_obj.curl_post(curl_command)
        if self._FIRMWARE_UPDATE_TASK_STATUS not in str(json_response_data):
            log_error = "Error - Redfish URL : {} is not Correct - {}".format(self._REDFISH_SYSTEM_RESET_URL,
                                                                              json_response_data)
            self._log.error(log_error)
            raise content_exceptions.TestError(log_error)

        self._log.info("The BMC Firmware update command sent successfully..")
        self._log.info("Waiting for bmc to reboot...")
        time.sleep(self._common_content_configuration.get_msr_timeout())
        return True

    def get_bmc_version(self):
        """
        This Method is used to get current BMC Firmware version.

        :raise:  ContentException.TestError
        :return: Firmware Revised version number
        """
        self._install_collateral.install_ipmitool()
        command_result = self._common_content_lib.execute_sut_cmd(self._BMC_INFO_CMD, self._BMC_INFO_CMD,
                                                                  self._command_timeout)
        self._log.debug("command {} result:\n {}".format(self._BMC_INFO_CMD, command_result))
        if re.findall(self._REGEX_FIRMWARE, command_result):
            return re.findall(self._REGEX_FIRMWARE, command_result)[0]
        else:
            log_error = "Could not fetch the BMC Version"
            self._log.error(log_error)
            raise content_exceptions.TestError(log_error)

    def change_power_setting_for_redfish(self, mask=False):
        """
        This Method changes the power switch setting from suspend state to power off state.

        :param mask: boolean value , if True the method masks the power action else unmasks the power action
        :raise:  ContentException.TestError
        """
        self._log.info("Change the power button action to power off from suspend mode")
        self._common_content_lib.execute_sut_cmd(self._POWER_BUTTON_POWER_OFF, self._POWER_BUTTON_POWER_OFF,
                                                 self._command_timeout)
        mask_cmd = self._SYSTEMCTL_MASK_CMD.format(self._UNMASK)
        sed_cmd = self._SED_CMD_TO_CHANGE_PWR_SETTING.format(self._LOGIN_SETTING_KEY,
                                                             self._HASH + self._LOGIN_SETTING_KEY,
                                                             self._SYSTEMD_LOGIN_FILE)
        if mask :
            mask_cmd = self._SYSTEMCTL_MASK_CMD.format(self._MASK)
            sed_cmd = self._SED_CMD_TO_CHANGE_PWR_SETTING.format(self._HASH + self._LOGIN_SETTING_KEY,
                                                                 self._LOGIN_SETTING_KEY,
                                                                 self._SYSTEMD_LOGIN_FILE)

        self._common_content_lib.execute_sut_cmd(mask_cmd, mask_cmd, self._command_timeout)
        self._common_content_lib.execute_sut_cmd(sed_cmd, sed_cmd, self._command_timeout)
        self._log.debug("Executed command {} successfully".format(sed_cmd))
        self._common_content_lib.execute_sut_cmd(self._SYSTEMCTL_RESTART_CMD, self._SYSTEMCTL_RESTART_CMD,
                                                 self._command_timeout)
        self._log.info("successfully Changed the power button action.")
