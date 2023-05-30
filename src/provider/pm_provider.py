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
import re
from importlib import import_module
from abc import ABCMeta, abstractmethod
from six import add_metaclass

from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.provider.base_provider import BaseProvider
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration


@add_metaclass(ABCMeta)
class PmProvider(BaseProvider):
    """
    This power management provider is implemented for both linux and windows to perform management activities.
    """

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new pm provider object.

        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :param log: Logger object to use for output message.
        :param os_obj: OS object.
        """
        super(PmProvider, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj
        self._sut_os = self._os.os_type

        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        self._content_config_obj = ContentConfiguration(self._log)
        self._command_timeout = self._content_config_obj.get_command_timeout()

    @staticmethod
    def factory(log, cfg_opts, os_obj):
        """
        To create a factory object based on the configuration xml file.

        :return: object
        :Raise: NotImplementedError
        """
        package = r"src.provider.pm_provider"
        if OperatingSystems.WINDOWS == os_obj.os_type:
            mod_name = "PmProviderWindows"
        elif OperatingSystems.LINUX == os_obj.os_type:
            mod_name = "PmProviderLinux"
        else:
            raise NotImplementedError

        mod = import_module(package, mod_name)
        aclass = getattr(mod, mod_name)
        return aclass(cfg_opts=cfg_opts, log=log, os_obj=os_obj)

    @abstractmethod
    def set_display_timeout(self, timeout):
        """
        Set screen display timeout.
        :param timeout: timeout value in seconds.

        :return: None.
        :Raise: NotImplementedError.
        """
        raise NotImplementedError

    @abstractmethod
    def set_sleep_timeout(self, timeout):
        """
        Set screen sleep timeout time.

        :param timeout: timeout value in seconds.
        :return: None.
        :Raise: NotImplementedError.
        """
        raise NotImplementedError

    @abstractmethod
    def set_screen_saver_blank(self, timeout):
        """
        set screen to blank

        :param timeout: timeout value in seconds.
        :return: None.
        :Raise: NotImplementedError.
        """
        raise NotImplementedError

    @abstractmethod
    def set_power_scheme(self):
        """
        Set power scheme
        """
        raise NotImplementedError


class PmProviderLinux(PmProvider):
    """
    This provider is implemented for linux environment to set screensaver blank and screen idle.
    """

    __IDLE_DELAY_SET_CMD = "dbus-launch gsettings set org.gnome.desktop.session idle-delay %d"
    __IDLE_DELAY_GET_CMD = "dbus-launch gsettings get org.gnome.desktop.session idle-delay"

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new PmProviderLinux object.

        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :param log: Logger object to use for output message.
        :param os_obj: OS object.
        """
        super(PmProviderLinux, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj

    def set_display_timeout(self, timeout):
        """
        Sets the timeout for Power saving > Blank Screen
        Timeout Range : 0 to 9999

        :param timeout: timeout value in seconds.
        :return: None.
        :Raise: RuntimeError.
        """
        self._log.info("Setting the 'Display timeout' power option")
        if not timeout:
            screen_saver_settings = ["dbus-launch gsettings set org.gnome.settings-daemon.plugins.power idle-dim false",
                                     self.__IDLE_DELAY_SET_CMD % timeout]
        else:
            screen_saver_settings = ["dbus-launch gsettings set org.gnome.settings-daemon.plugins.power idle-dim true",
                                     self.__IDLE_DELAY_SET_CMD % timeout]

        for setting in screen_saver_settings:
            self._log.debug("Setting %s" % setting)
            self._common_content_lib.execute_sut_cmd(setting, setting, self._command_timeout)
        output = self._common_content_lib.execute_sut_cmd(self.__IDLE_DELAY_GET_CMD, self.__IDLE_DELAY_GET_CMD,
                                                          self._command_timeout, cmd_path="/root")
        self._log.debug("Output of power settings: %s" % output)
        if output == "":
            raise RuntimeError("linux power settings(%s) failed" % (self.__IDLE_DELAY_SET_CMD % timeout))
        if int(output.strip().split()[-1].strip()) != timeout:
            raise RuntimeError("Could not set linux power settings(%s)", (self.__IDLE_DELAY_SET_CMD % timeout))

    def set_sleep_timeout(self, timeout=120):
        """
        Set screen timeout time.
        dbus-launch is used to launch dbus and execute the command with the help of dbus.

        :param timeout: timeout value in seconds.
        :return: None.
        :Raise: RuntimeError.
        """
        self._log.info("Setting the 'Sleep timeout' power option")
        awake_settings = ["dbus-launch gsettings set org.gnome.settings-daemon.plugins.power "
                          "sleep-inactive-ac-timeout {}", "dbus-launch gsettings set org.gnome.settings-daemon.plugins."
                                                          "power sleep-inactive-battery-timeout {}"]

        get_awake_setting = ["dbus-launch gsettings get org.gnome.settings-daemon.plugins.power sleep-inactive-battery"
                             "-timeout", "dbus-launch gsettings get org.gnome.settings-daemon.plugins.power "
                                         "sleep-inactive-ac-timeout"]

        for setting in awake_settings:
            self._log.debug("Setting %s", setting)
            self._common_content_lib.execute_sut_cmd(setting.format(str(timeout)), setting, self._command_timeout)

        for get_value in get_awake_setting:
            output = self._common_content_lib.execute_sut_cmd(get_value, get_value, self._command_timeout)
            self._log.debug("Output of power settings: %s", output)
            if output == "":
                raise RuntimeError("linux power settings(%s) failed" % (get_value % timeout))
            if int(output.strip()) != timeout:
                raise RuntimeError("Could not set linux power settings(%s)", (get_value % timeout))

    def set_screen_saver_blank(self, timeout):
        """
        Set screen Blank.

        :param timeout: timeout value in seconds.
        :return: None.
        :Raise: RuntimeError
        """
        self._log.info("Setting screen to Blank")
        self._common_content_lib.execute_sut_cmd('setterm -term xterm -blank {}'.format(timeout),
                                                 "Blank Screen", self._command_timeout)
        self._log.debug("Screen saver value is set to: %s", timeout)

    def set_power_scheme(self, option=None):
        """
        It is applicable only for windows not for linux

        :return: None.
        :Raise: None
        """

        pass


class PmProviderWindows(PmProvider):
    """
    This provider is implemented for windows environment to set screensaver blank and screen idle.
    """

    AC_REGEX_PATTERN = "Current AC Power Setting Index:\s+(\S+)"
    DC_REGEX_PATTERN = "Current DC Power Setting Index:\s+(\S+)"
    _BLANCED_GUID = "381b4222-f694-41f0-9685-ff5bb260df2e"
    _DISPLAY_GUID = "7516b95f-f776-4464-8c53-06167f40cc99"
    _DISPLAY_OFF_GUID = "3c0bc021-c8a8-4e07-a973-6b14cbcb2b7e"
    _SLEEP_GUID = "238c9fa8-0aad-41ed-83f4-97be242c8f20"
    _SLEEP_AFTER_GUID = "29f6c1db-86da-48c5-9fdb-f2b67b1f44da"
    INT_16 = 16
    SECONDS = 60

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new PmProviderWindows object.

        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :param log: Logger object to use for output message.
        :param os_obj: OS object.
        """
        super(PmProviderWindows, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj

    def _powercfg_query(self, balanced_guid, group_guid, sub_group_guid):
        """
        This Method execute powercfg query command with required GUID's and returns AC and DC value

        :param balanced_guid: Take balanced_guid value
        :param group_guid: Take group_guid value
        :param sub_group_guid: Take sun_group_guid value

        :return: Returns's AC and DC value
        """

        command_line = "powercfg /query {} {} {}".format(balanced_guid, group_guid, sub_group_guid)
        command_line_result = self._common_content_lib.execute_sut_cmd(command_line, "Current timeout value",
                                                                       self._command_timeout)

        return int(re.findall(self.AC_REGEX_PATTERN, command_line_result)[0], self.INT_16), \
               int(re.findall(self.DC_REGEX_PATTERN, command_line_result)[0], self.INT_16)

    def set_display_timeout(self, timeout):
        """
          Sets the timeout for Power saving > Blank Screen
          Timeout Range : 0 to 9999

          :param timeout: timeout value in seconds.
          :return: None.
          :Raise: None.
          """
        self._log.info("Converting timeout seconds value into minutes")
        timeout_minutes = timeout // self.SECONDS  # Converting to minutes since commands takes values in minutes
        self._log.info("Setting the 'Turn off Display' power option")

        list_awake_setting = ["powercfg -change -monitor-timeout-dc {}", "powercfg -change -monitor-timeout-ac {}"]

        for power_option in list_awake_setting:
            self._common_content_lib.execute_sut_cmd(power_option.format(timeout_minutes),
                                                     "Setting display state value to %d" % timeout,
                                                     self._command_timeout)

        ac_display_timeout, dc_display_timeout = self._powercfg_query(self._BLANCED_GUID, self._DISPLAY_GUID,
                                                                      self._DISPLAY_OFF_GUID)
        if ac_display_timeout != timeout:
            raise RuntimeError("Could not set AC display timeout to {}".format(timeout))
        if dc_display_timeout != timeout:
            raise RuntimeError("Could not set DC display timeout to {}".format(timeout))

        self._log.debug("Successfully set Display Timeout AC and DC Power Value to: {} and {} seconds"
                        .format(ac_display_timeout, dc_display_timeout))

    def set_sleep_timeout(self, timeout=120):
        """
        Set sleeping timeout value.

        :param timeout: timeout value in seconds.
        :return: None.
        :Raise: None.
        """
        self._log.info("Converting timeout value into minutes")
        timeout_minutes = timeout // self.SECONDS  # Converting to minutes since commands takes values in minutes
        self._log.info("Setting the 'Sleep timeout' power option")

        list_awake_setting = ["powercfg -change -standby-timeout-dc {}", "powercfg -change -standby-timeout-ac {}"]

        for power_option in list_awake_setting:
            self._common_content_lib.execute_sut_cmd(power_option.format(timeout_minutes),
                                                     "Setting sleep state value to %d" % timeout,
                                                     self._command_timeout)

        ac_sleep_timeout, dc_sleep_timeout = self._powercfg_query(self._BLANCED_GUID, self._SLEEP_GUID,
                                                                  self._SLEEP_AFTER_GUID)
        if ac_sleep_timeout != timeout:
            raise RuntimeError("Could not set AC sleep timeout to {}".format(timeout))
        if dc_sleep_timeout != timeout:
            raise RuntimeError("Could not set DC sleep timeout to {}".format(timeout))

        self._log.debug("Successfully set Sleep Timeout AC and DC Power Value to: {} and {} seconds"
                        .format(ac_sleep_timeout, dc_sleep_timeout))

    def set_power_scheme(self, option=None):
        """
        This function is used to check the current power scheme and can set to required scheme.

        :param option: takes the power option to set.
        :return: true if power scheme is set as expected else false.
        :raise: RunTimeError
        """
        command_line = "powercfg /getactivescheme"
        command_line_result = self._common_content_lib.execute_sut_cmd(command_line, "Power Scheme",
                                                                       self._command_timeout)
        power_value = False
        hp_option = None
        self._log.info("Setting the 'Power scheme' option")
        pwr_list_options = self._common_content_lib.execute_sut_cmd("powercfg -list", "power options",
                                                                    self._command_timeout)
        pwr_list = pwr_list_options.strip().split("\n")

        re_pwr_pattern = "(.*){}(.*)".format(option)

        for line_pwr_options in pwr_list:
            if re.search(re_pwr_pattern, line_pwr_options, re.IGNORECASE):
                hp_option = line_pwr_options.split(":")[1].split()[0].strip()

        self._common_content_lib.execute_sut_cmd("powercfg -setactive {}".format(hp_option),
                                                 "power option set", self._command_timeout)

        pwr_result = self._common_content_lib.execute_sut_cmd("powercfg /getactivescheme",
                                                              "get current power scheme", self._command_timeout)

        self._log.debug("The current {}".format(pwr_result))

        if re.search(re_pwr_pattern, pwr_result, re.IGNORECASE):
            power_value = True

        if not power_value:
            err_log = "Power scheme has not been set correctly"
            self._log.error(err_log)
            raise RuntimeError(err_log)
        return power_value

    def set_screen_saver_blank(self, timeout):
        """Set screen Blank.

        :param timeout: timeout value in minutes.
        :return: None.
        :Raise: None
        """
        self._log.info("Setting screensaver to Blank")
        self._common_content_lib.execute_sut_cmd('reg add "HKEY_CURRENT_USER\Control Panel\Desktop" /v SCRNSAVE.EXE /t '
                                                 'REG_SZ /d C:\Windows\system32\scrnsave.scr /f',
                                                 "Blank Screen", self._command_timeout)
