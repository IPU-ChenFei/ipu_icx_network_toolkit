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

import os
import re
import time

import src.lib.content_exceptions as content_exception
from dtaf_core.providers.bios_provider import BiosProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.console_log import ConsoleLogProvider
from src.provider.ipmctl_provider import IpmctlProvider

from src.lib.bios_util import BiosUtil
from src.lib.common_content_lib import CommonContentLib
from src.lib.memory_dimm_info_lib import MemoryDimmInfo
from src.lib.content_configuration import ContentConfiguration
from src.ras.lib.ras_common_utils import RasCommonUtil
from src.lib.install_collateral import InstallCollateral
from src.ras.lib.os_log_verification import OsLogVerifyCommon
from src.lib.content_base_test_case import ContentBaseTestCase


class ThermalAlarmCheckCommon(ContentBaseTestCase):
    """
    This Class is Used as Common Class For all the Thermal Alarm Check Functionality Test Cases
    """
    _IPMCTL_SHOW_TOPOLOGY_CMD = "ipmctl show -topology"
    _IPMCTL_SHOW_DIMM_CMD = "ipmctl show -dimm"
    _IPMCTL_SHOW_MANAGEABILTY_CMD = "ipmctl show -d ManageabilityState -dimm"
    _IPMCTL_SHUTDOWN_STATUS_CMD = "ipmctl show -d HealthState,LatchedLastShutdownStatus,UnlatchedLastShutdownStatus" \
                                  " -dimm {}"
    _IPMCTL_SHOW_SENSOR_DATA_CMD = "ipmctl show -sensor -dimm {}"
    _IPMCTL_CMD_FOR_LISTING_EXISTING_DCPMM_ERRORS = "ipmctl show -error Media -dimm {}"
    _IPMCTL_CMD_FOR_TRIGGERING_DIRTY_SHUTDOWN = r"ipmctl set -dimm {} DirtyShutdown=1"
    _FILE_NAME = "thermal_alarm_check_log.txt"
    _HEALTH_STATUS = "Health Status (HS)"
    _NORMAL = "Normal"
    _REXEX_FOR_FINDING_RANGE = r"([0-9].*)-([0-9a-zA-z].*)*\s:"
    _REGEX_FOR_RANK = r"Rank\sAddr_*\s=\s*0x([0-9a-zA-Z_]+).*"
    _REGEX_FOR_SOCKET = r"Socket_*\s=\s([0-9])"
    _REGEG_FOR_MC = r"Mc_*\s=\s([0-9])"
    _REGEX_FOR_CHANNEL = r"Ch_*\s=\s([0-9])"
    _REGEX_FOR_SOC_CH_MC = r"\s[0-9]\s*\|\s*dimm{}*\s*\|\s*([0-9])\s*\|\s*([0-9])\s*\|\s*([0-9])\s*"
    _NDCTL_LIST_CMD = "ndctl list --dimm=nmem0 -H"
    _REGEX_CMD_FOR_NDCTL_LIST = r".*alarm_spares.*\:{}"
    _REGEX_CMD_FOR_PERCENTAGE_REMAINING_ENABLE = r"\s*Percentage\sRemaining\s\:\sEnable"
    _REGEX_CMD_FOR_HEALTH_STATUS = r"Health\sStatus\s*\(HS\)\s*\:\sNormal"
    _REGEX_CMD_FOR_MEDIA_TEMPERATURE = r"Media Temperature\s:\sEnable"
    _REGEX_CMD_FOR_MEDIA_TEMP_TRIP = r"Media\sTemperature\sTrip\s\:\s*Tripped"
    _REGEX_CMD_FOR_MEDIA_TEMP_NOT_TRIP = r"Media\sTemperature\sTrip\s\:\s*Not tripped"
    _REGEX_CMD_FOR_MEDIA_TEMP_VALUE = r"Media\sTemperature\s\(MTP\)\s*\:\s*{}"
    _REGEX_CMD_FOR_MEDIA_TEMP_THRESHOLD = r"Media\sTemperature\sThreshold\s*\(MTT\)\s*:\s\D*{}"
    _REGEX_CMD_FOR_ACCESS_MODE_AUTO = r"New\sAccess\sMode\s:\sauto"
    _REGEX_CMD_FOR_LATCHED_DIRTY_SHUTDOWN_COUNT = r".*LatchedDirtyShutdownCount.*"
    _REGEX_CMD_FOR_UNLATCHED_DIRTY_SHUTDOWN_COUNT = r".*UnlatchedDirtyShutdownCount.*"
    _REGEX_CMD_FOR_PERSISTENT_MEMORY = r".*Persistent\sMemory"
    _REGEX_CMD_FOR_LATCH_SYSTEM_SHUTDOWN_STATE = r"Latch\sSystem\sShutdown\sState.*Enable"
    _REGEX_CMD_FOR_LAST_SHUTDOWN_STATUS = r"Latched\sLast\sShutdown\sStatus\s\(LSS\).*Dirty\sShutdown"
    _REGEX_CMD_FOR_MEDIA_USER_DATA_ACCESS = r"Media\sDisabled\s:\s\S+\sUser\sData\sis\saccessible"
    _REGEX_CMD_FOR_MEDIA_USER_NO_DATA_ACCESS = r"Media\sDisabled\s:\s\S+\sUser\sData\sis\snot\saccessible"
    _REGEX_CMD_DIMM_HEALTH_NORMAL = r"Health\sStatus\s\(HS\)\s+:\s+Normal\s\(no\sissues\sdetected\)"
    _REGEX_CMD_DIMM_HEALTH_FATAL = r"Health\sStatus\s\(HS\)\s+:\s+Fatal\(data\sloss\shas\soccurred\sor\sis\simminent\)"
    _REGEX_CMD_FOR_HEALTH_STATUS_CHANGE_ERROR = r"Error\sType\s+:\s+\S+\s-\sSmart\sHealth\sStatus\sChange"
    _REGEX_FOR_SET_POISON_BIT = r"Poison\serror\ssuccessfully\sinje.*"
    _REGEX_FOR_CHECKING_ERROR = r"The\snumber\sof\serrors\sfound\sduring\sthe\srange\sscrub\s:\s0x01"
    _ADDR_LIST = [0x4080000000, 0x9080000000, 0x9090000000, 0x9100000000, 0x9200000000, 0x9300000000, 0x9400000000,
                  0x9500000000, 0x9600000000, 0xa000000000, 0xb000000000, 0xc000000000, 0xd000000000]
    _REGEX_CMD_FOR_PERCENTAGE_REMAINING_VALUE = r"\sPercentage\sRemaining\s\(PR\)\s:\s{}.*"

    _MEDIA_DIMM_THRESHOLD_VALUE = 82
    _PERCENTAGE_REMAINING_TRIGGER = 8
    _PACKAGING_SPARING_TRIGGER = 1
    _SDP_LOG_FILE_NAME = "cscripts_temp.log"
    _MIN_TEMP = 50
    _MAX_TEMP = 98
    _START_LIMIT_ADDR = 0x10000000
    _END_LIMIT_ADDR = 0x50000000
    _START_LIMIT = 0x10000000
    _LAST_LIMIT = 0x40000000
    _LIST_OF_COLLECT_OS_LOGS_COMMANDS = ["dmesg",
                                         "cat /var/log/messages",
                                         "journalctl -u mcelog"]
    _CMD_FOR_PERSISTENT_MEMORY = r"cat /proc/iomem | grep Persistent"
    _MESSAGE_LOG_FOR_THRESHOLD_PER = ["Set of Dimm Percentage Remaining Value found as expected",
                                      "Percentage Remaining Trip found as expected",
                                      "Package Sparing register status found as expected"]
    _UNEXPECTED_MESSAGE_LOG_FOR_THRESHOLD_PER = ["Set of Dimm Percentage Remaining Value found was Unexpected",
                                                 r"Percentage Remaining Trip found was Unexpected",
                                                 "Package Sparing register status found was Unexpected"]
    _REGEX_CMD_FOR_PERCENTAGE_THRESHOLD = [r"\sPercentage\sRemaining\s\(PR\)\s:\s{}.*",
                                           r"\sPercentage\sRemaining\sTrip\s:\s{}",
                                           r"\sPackage\sSparing\shas\shappened\s:\s{}"]

    def __init__(
            self,
            test_log,
            arguments,
            cfg_opts,
            bios_config_file
    ):
        """
        Create an instance of sut os provider, XmlcliBios provider, SiliconDebugProvider, SiliconRegProvider
         BIOS util and Config util,
        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(
            ThermalAlarmCheckCommon,
            self).__init__(
            test_log,
            arguments,
            cfg_opts)
        self._cfg = cfg_opts
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(
            sut_os_cfg, test_log)  # type: SutOsProvider
        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        self._bios = ProviderFactory.create(
            bios_cfg, test_log)  # type: BiosProvider
        bios_config_file_path = self.get_bios_config_file_path(
            bios_config_file)
        error_conf_bios = "fatal_media_error_clear_bios_knob.cfg"
        bios_config_file_path_for_error_clear = self.get_bios_config_file_path(error_conf_bios)

        self._common_content_lib = CommonContentLib(self._log, self._os, self._cfg)
        self._bios_util = BiosUtil(cfg_opts,
            bios_config_file_path,
            self._bios,
            self._log,
            self._common_content_lib)
        self._error_clear_bios_util = BiosUtil(cfg_opts,
            bios_config_file_path_for_error_clear,
            self._bios,
            self._log,
            self._common_content_lib)
        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._cscripts = ProviderFactory.create(
            sil_cfg, test_log)  # type: SiliconRegProvider
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._sdp = ProviderFactory.create(
            si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        serial_log_cfg = cfg_opts.find(ConsoleLogProvider.DEFAULT_CONFIG_PATH)
        self._slog = ProviderFactory.create(serial_log_cfg, test_log)  # type: ConsoleLogProvider
        self._nvd = self._cscripts.get_cscripts_nvd_object()
        self._sv = self._cscripts.get_cscripts_utils().getSVComponent()
        self.dimm_healthy_and_manageable_list = []

        self.log_file_path = self.get_thermal_alarm_check_log_path()
        self._common_content_configuration = ContentConfiguration(self._log)
        self._ipmctl_provider = IpmctlProvider.factory(test_log, self._os, execution_env="os", cfg_opts=cfg_opts)
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        self._command_timeout = self._common_content_configuration.get_command_timeout()
        self._os_time_out_in_sec = self._common_content_configuration.os_full_ac_cycle_time_out()
        self._time_stamp = ""
        self.latched_dirty_shutdown_value = None
        self.unlatched_dirty_shutdown_value = None
        ac_power_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac_power = ProviderFactory.create(ac_power_cfg, test_log)
        self._ras_common_obj = RasCommonUtil(self._log, self._os, cfg_opts, self._common_content_configuration, self._bios_util,
                                             self._cscripts, self._sdp)
        self._mce_obj = InstallCollateral(self._log, self._os, self._cfg)
        self._os_log_obj = OsLogVerifyCommon(self._log, self._os, self._common_content_configuration,
                                             self._common_content_lib)
        self._LOWER_LIMIT = 0x0
        self._UPPER_LIMIT = 0x1
        self._os_log_obj = OsLogVerifyCommon(self._log, self._os, self._common_content_configuration,
                                             self._common_content_lib)
        self._ipmctl_executer_path = "/root"

    def get_bios_config_file_path(self, bios_config_file):
        """
        getting the bios config file path

        :param : This will take the bios config file
        :raise : IOError - If BIOS config file is not found
        :return: This will return the complete Bios config file path
        """
        cur_path = os.path.dirname(os.path.realpath(__file__))
        bios_config_file_path = os.path.join(cur_path, bios_config_file)
        if not os.path.isfile(bios_config_file_path):
            self._log.error("The bios config file '%s' does not exists." % bios_config_file)
            raise IOError("The bios config file '%s' does not exists." % bios_config_file)

        return bios_config_file_path

    def get_thermal_alarm_check_log_path(self):
        """
        # We are getting the Path for thermal alarm check log file

        :return: log_file_path
        """
        cur_path = os.path.dirname(os.path.realpath(__file__))
        path = os.path.join(cur_path, self._FILE_NAME)
        return path

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs that are set.

        :return: None
        """
        self._common_content_lib.clear_all_os_error_logs()
        self._log.info("Set the Bios Knobs to Default Settings")
        self._bios.default_bios_settings()  # To set the Bios Knobs to its default mode.
        self._log.info("Set the Bios Knobs as per our Test Case Requirements")
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._log.info("Bios Knobs are Set as per our TestCase and Reboot in Progress to Apply the Settings")
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.

    def populate_memory_dimm_information(self):
        """
        This Function populated memory dimm information by running below ipmctl commands on SUT
        - ipmctl show -topology
        - ipmctl show -dimm
        - ipmctl show -d ManageabilityState -dimm
        Finally it will create object of class MemoryDimmInfo.

        :return: None
        :raise: RuntimeError for any error during ipmctl command execution or parsing error.
        """
        try:
            self._log.info("Checking the Topology to Identify the DIMM Socket Locations ")

            # Get dimm topology output using ipmctl command
            command_result = self._os.execute(self._IPMCTL_SHOW_TOPOLOGY_CMD, self._command_timeout)
            if command_result.cmd_failed():
                log_error = "Failed to run ipmctl show -topology command with return value = '{}' and " \
                            "std_error='{}'..".format(command_result.return_code, command_result.stderr)
                self._log.error(log_error)
                raise RuntimeError(log_error)

            show_topology_output = command_result.stdout.split(",")[0]

            # Get show dimm output using ipmctl command
            command_result = self._os.execute(
                self._IPMCTL_SHOW_DIMM_CMD, self._command_timeout)
            if command_result.cmd_failed():
                log_error = "Failed to run ipmctl show -dimm command with return value = '{}' and " \
                            "std_error='{}'..".format(command_result.return_code, command_result.stderr)
                self._log.error(log_error)
                raise RuntimeError(log_error)
            show_dimm_command_output = command_result.stdout.split(",")[0]

            # Get manageability output using ipmctl command
            command_result = self._os.execute(self._IPMCTL_SHOW_MANAGEABILTY_CMD, self._command_timeout)
            if command_result.cmd_failed():
                log_error = "Failed to run ManageabilityState command with return value = '{}' and " \
                            "std_error='{}'..".format(command_result.return_code, command_result.stderr)
                self._log.error(log_error)
                raise RuntimeError(log_error)

            manageability_state_command_output = command_result.stdout.split(',')[0]

            # Object creation.
            memory_info_obj = MemoryDimmInfo(show_topology_output, show_dimm=show_dimm_command_output,
                                             manageability=manageability_state_command_output)

            self.dimm_healthy_and_manageable_list = memory_info_obj.get_dimm_info_healthy_manageable()

        except Exception as ex:
            log_error = "Unable to Execute IPMCTL Commands on SUT {}".format(ex)
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def get_list_of_dimms_which_are_healthy_and_manageable(self):
        """
        This Method is Used to Fetch List of All the Healthy and Manageable Dimm's and raise the RunTimeError if
        there are no Healthy and Manageable Dimms.

        :return: None
        :raise: RuntimeError if there are no Healthy and Manageable Dimm's
        """
        if len(self.dimm_healthy_and_manageable_list) > 0:
            for dimm in self.dimm_healthy_and_manageable_list:
                self._log.info("Dimm{} is Healthy and Manageable".format(dimm))
        else:
            log_error = "We don't have Dimm's which are Healthy and Manageable"
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def set_dcpmm_access_path_to_auto_and_refresh_topology(self):
        """
        This Method is Used to Set the Access Path to Auto Mode and Refreshing the DCPMM Topology.

        :return None
        :raise RunTimeError if there is any error in setting the Access Mode
        """
        try:
            self._log.info("Setting the Access to Auto Mode")
            self._sdp.start_log(
                self.log_file_path, "w")  # Opening CScripts Log File
            # Setting the DCPMM Access Path to Auto Mode
            self._nvd.set_access('auto')
            self._sv.refresh()
            self._sdp.stop_log()  # CLosing the Cscripts Log File
            with open(self.log_file_path, "r") as log_file:
                log_file_list = log_file.readlines()
                regex_out = re.findall(self._REGEX_CMD_FOR_ACCESS_MODE_AUTO, "\n".join(log_file_list))
                if len(regex_out) != 0:
                    self._log.info("Setting the Access to Auto Mode is Successful and Refreshing the DCPMM Topology")
                self._log.info("".join(log_file_list))
            self._nvd.refresh()  # Refreshing the DCPMM Topology
            self._log.info("Listing the Platform Devices")
            self._log.info(self._sdp.itp.devicelist)
            self._log.info("Devices Listing Successful")
        except Exception as ex:
            log_error = "Unable to set the Access Mode to Auto due to the Exception '{}'".format(ex)
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def obtaining_list_of_dcpmm_dimms(self, get_dimm_config_flag = False):
        """ This Function is Used to Populate the List of DCPMM DIMM's and check whether DCPMM Dimm's are
        Enabled or Not. and also to get the socket, channel amd mc of dedicated dimm based on flag get dimm config flag.

        :param get_dimm_config_flag to decide for getting ch, mc, socket.
        :return None if get_dimm_config_flag is false else return tupple having info of socket, mc, ch.
        :raise RuntimeError if Dimm is not enabled
        """
        self._log.info("Obtaining the List of DCPMM DIMM's")
        # Reopening the Cscripts Log File and Appending the Data
        self._sdp.start_log(self.log_file_path, "w")
        self._nvd.show_list()  # Obtaining the List of DCPMM Dimm's with the Current Media State
        self._sdp.stop_log()  # Closing Cscripts Log
        # Opening the Cscripts Log File to Check Whether Dimm is Enabled or Not
        with open(self.log_file_path, "r") as log_file:
            log_file_list = log_file.readlines()
            log_file.seek(0, 0)
            regex_file_log = log_file.read()
            self._log.info("List of DCPMM Dimm Data is {}".format("".join(log_file_list)))
            for dimm_id in self.dimm_healthy_and_manageable_list:
                for line in log_file_list:
                    if "dimm{}".format(dimm_id[2:]) in line:
                        if "Enabled" in line:
                            self._log.info("Dimm {} is Enabled".format(dimm_id))
                        else:
                            self._log.error("Dimm {} is Not Enabled".format(dimm_id))
        self._log.info("List of DCPMM Dimm's is Populated Successfully")

        if get_dimm_config_flag:
            dimm_id = self._ipmctl_provider.dimm_healthy_and_manageable_list[0]
            regex = self._REGEX_FOR_SOC_CH_MC.format(dimm_id[2:])
            ret_val = re.findall(regex, regex_file_log)
            return ret_val

    def identifying_target_dcpmm(self):
        """ This Function is Used to Identify Target DIMM and list the details of our Targetted Dimm

         :return None
         :raise RunTimeError if there is any error occurred while identifying Targetted Dcpmm.
         """
        try:
            self._log.info("Identifying the Target DCPMM")
            self._sdp.start_log(
                self.log_file_path, "w")  # Reopening the Cscripts File
            for dimm in range(len(self.dimm_healthy_and_manageable_list)):  # Identifying the Target DCPMM's from
                # our Dimm List
                self._nvd.dimms[dimm].identify_dimm()
            self._sdp.stop_log()
            with open(self.log_file_path, "r") as log_file:
                self._log.info(log_file.read())
            self._log.info("Target DCPMM has been Identified")
        except Exception as ex:
            log_error = "Unable to Identify Target Dcpmm due to the exception '{}'".format(ex)
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def checking_dcpmms_health(self):
        """ This Function is Used to Identify the Health Status of Targeted DCPMM Dimm and Check whether
        Health Status of our Targeted Dimm is Normal or Not.

        :return None
        """
        self._log.info("Checking Targeted DCPMM's Health Status")
        # Reopening the Cscripts File and Appending the File
        self._sdp.start_log(self.log_file_path, "w")
        self._nvd.dimms[0].get_smart_info()  # Checking DCPMM's Health
        self._sdp.stop_log()  # Closing Cscripts Log File
        # Opening Cscripts File to Check Whether Health Status is Normal or Not
        with open(self.log_file_path, "r") as log_file:
            log_file_list = log_file.readlines()
            self._log.info("DCPMM Data is {}".format("".join(log_file_list)))
            regex_out = re.findall(self._REGEX_CMD_FOR_HEALTH_STATUS, "\n".join(log_file_list))
            if len(regex_out) != 0:
                self._log.info("Health Status is Normal")
            else:
                self._log.error("Health Status is Not Normal")

    def checking_alarms_current_state(self):
        """
        This Function is Used to Check the Alarm's Current State and Alarm's Threshold Values,
        By Default Current Status of Alarm's will be in Disable State.

        :return None
        :raise RuntimeError if we are unable to get the current alarm status
        """
        try:
            self._log.info("Checking the Current State of the Alarms ")
            self._sdp.start_log(
                self.log_file_path, "w")  # Reopening Cscripts Log File
            # Checking Alarm's Current State
            self._nvd.dimms[0].get_alarm_thresholds()
            self._sdp.stop_log()
            with open(self.log_file_path, "r") as log_file:
                self._log.info("Alarms Current status is {}".format(log_file.read()))
        except Exception as ex:
            log_error = "Unable to get the Current Status of Alarm's due to '{}'".format(ex)
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def set_alarm_thresholds_and_verify(self, threshold_temperature,
                                        regex_media_threshold_value,
                                        expected_tripped_state,
                                        regex_media_trip_state=None):
        """
        By Default Alarm's might be disabled and by using this Method we will enable the Alarm's
        and Set the Threshold Values for Alarm and verify whether Alarm's are enabled or not and modify the
        Threshold Value of Media Temperature with respect to Media Dimm Temperature to check whether Media Temperature
         Trip is in Tripped State or Not .

        :param: threshold_temperature - threshold value for media temperature
        :param: regex_media_threshold_value - Regular Expression to verify Threshold Value of Media Temperature
        which we are Passing
        :param: expected_tripped_state - Specifies whether media should be in tripped state or not
        :param: regex_media_trip_state - Regular Expression to check Media Temperature Trip State
        :return None
        :raise RuntimeError if Alarm's are Not Enabled Properly
        :raise RuntimeError if trip state not set as expected
        """
        _PERCENTAGE_REMAINING_ENABLE = 1  # this should be enabled
        _MEDIA_TEMPERATURE_ENABLE = 1  # this should be enabled
        _CORE_TEMPERATURE_ENABLE = 0  # this should be disabled
        self._log.info("Enabling the Alarm's and Setting the Threshold Values for Alarm")
        # Start logging cscripts command output to log file
        self._sdp.start_log(self.log_file_path, "w")
        # Enabling the Alarm's and Setting Threshold Values for Alarm's
        self._nvd.dimms[0].set_alarm_thresholds(_PERCENTAGE_REMAINING_ENABLE,
                                                _MEDIA_TEMPERATURE_ENABLE,
                                                _CORE_TEMPERATURE_ENABLE,
                                                self._MIN_TEMP,
                                                threshold_temperature,
                                                self._MAX_TEMP)
        self._nvd.dimms[0].get_smart_info()
        self._sdp.stop_log()  # Closing Cscripts Log File
        # Opening Cscripts Log File to Check whether Media Temperature is set correctly
        with open(self.log_file_path, "r") as log_file:
            self._log.info(
                "Beginning of set_alarm_thresholds_and_verify Output with Threshold Value of '{}'".format(
                    threshold_temperature))
            log_file_list = log_file.readlines()
            self._log.info("".join(log_file_list))
            self._log.info(
                "set_alarm_thresholds_and_verify Functionality Output with Threshold Value of '{}'"
                " is Completed".format(threshold_temperature))
            if regex_media_trip_state:
                regex_trip_value_output = re.findall(regex_media_trip_state, "\n".join(log_file_list))
                regex_temp_value_output = re.findall(regex_media_threshold_value.format(threshold_temperature),
                                                     "\n".join(log_file_list))
                if len(regex_trip_value_output) != 0 and len(regex_temp_value_output) != 0:
                    self._log.info(
                        "Setting of Dimm Temperature Threshold Value to '{}' is successful ".format(
                            threshold_temperature))
                    if expected_tripped_state:
                        self._log.info("Media Temperature Trip is in Tripped State")
                    else:
                        self._log.info("Media Temperature Trip is in Not tripped State")
                else:
                    self._log.error("Unable to Set the Alarm Thresholds and Media Temperature Threshold is not set to "
                                    "'{}'".format(threshold_temperature))
            else:
                regex_out = re.findall(self._REGEX_CMD_FOR_MEDIA_TEMPERATURE, "\n".join(log_file_list))
                if len(regex_out) != 0:
                    self._log.info("Alarm's are Enabled and Threshold Values are Set to '{}' and "
                                   "Media Temperature is Successfully Enabled".format(threshold_temperature))
                else:
                    log_error = "Unable to set threshold temperature values.. to '{}'".format(threshold_temperature)
                    self._log.error(log_error)
                    raise RuntimeError(log_error)

    def set_dimm_temperature_and_verify(self,
                                        dimm_temperature,
                                        reg_expr_media_temp,
                                        reg_expr_media_temp_value,
                                        is_tripped_state):
        """
        This Method is Used to Set the Dimm Media Temperature to Threshold Value minus one and Check the Thermal
         Trip Status and Media Temperature Trip is in Tripped State or Not

        :param: dimm_temperature - dime temperature to set
        :param: reg_expr_media_temp - regular expression to parse if media temperature is in trip state
        :param: reg_expr_media_temp_value - regular expression to parse media temperature value
        :param: expected_tripped_state - specifies whether dimm should go to tripped state or not
        :return None
        :raise RuntimeError if there is any error in Setting the Dimm Temperature to Threshold value minus one
        """
        try:
            self._log.info("Setting the Dimm Temperature to '{}'..".format(dimm_temperature))

            # Reopening the Cscripts Log File
            self._sdp.start_log(self.log_file_path, "w")
            self._nvd.dimms[0].inject_temperature_error(1, dimm_temperature, 0)
            self._nvd.dimms[0].get_smart_info()  # Checking the Health Status
            self._sdp.stop_log()  # Closing Cscripts log File

            # Reopening Cscripts Log File to Check whether
            with open(self.log_file_path, "r") as log_file:
                self._log.info("Beginning of log with media temperature value '{}'".format(dimm_temperature))
                log_file_list = log_file.readlines()
                self._log.info("".join(log_file_list))
                self._log.info("End of log with media temperature value '{}".format(dimm_temperature))

                regex_trip_output = re.findall(reg_expr_media_temp, "\n".join(log_file_list))
                regex_temp_value_output = re.findall(reg_expr_media_temp_value.format(dimm_temperature),
                                                     "\n".join(log_file_list))

                if len(regex_temp_value_output) != 0 and len(regex_trip_output) != 0:
                    self._log.info("Dimm Temperature is set to '{}'..".format(dimm_temperature))
                    if is_tripped_state:
                        self._log.info("Media Temperature Trip state is set to tripped state..")
                    else:
                        self._log.info("Media Temperature Trip state is set to Not tripped state..")
                else:
                    log_error = "Unable to set the value of Dimm Temperature to '{}'..".format(dimm_temperature)
                    self._log.error(log_error)
                    raise RuntimeError(log_error)
        except Exception as ex:
            log_error = "Unable to set the value of Dimm Temperature to '{}' one due to" \
                        " exception '{}'".format(dimm_temperature, ex)
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def clear_dcpmm_errors(self):
        """
        This Method is Used to Check the DCPMM Error Log and clear the Dimm History and reset the Target.

        :return None
        :raise RunTimeError if there is any issue while checking and clearing the error logs
        """
        try:
            self._log.info("Checking the Error Log of DCPMM")
            # Reopening the Cscripts Log File
            self._sdp.start_log(self.log_file_path, "w")
            self._nvd.dimms[0].error_log()  # Checking the Cscripts Error Log
            self._sdp.stop_log()  # Closing Cscripts log File
            with open(self.log_file_path) as log_file:
                self._log.info(
                    "Checking DCPMM Error Log Output is {}".format(
                        log_file.read()))
            self._sdp.reset_break = 1
            self._sdp.reset_target()
            self._nvd.dimms[0].clear_history()
            self._sdp.reset_break = 0
            self._sdp.reset_target()
            self._log.info("Cleared all the error Logs of DCPMM")
        except Exception as ex:
            log_error = "Unable to check and clear the error logs of DCPMM due to exception '{}'".format(
                ex)
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def reset_all_dcpmm_thresholds(self):
        """ This Method is Used to Set All the DCPMM Thresholds to it's Default Values

        :return None
        :raise RunTimeError if there is any error in resetting dcpmm thresholds
        """
        try:
            self._log.info(
                "Resetting all the DCPMM Thresholds to its Default Values")
            # Resetting all the Thresholds Applied to Default
            self._nvd.dimms[0].reset_all_thresholds_and_policies()
            self._log.info(
                "The applied DCPMM thresholds were reset to default values")
            self._os.wait_for_os(int(self._reboot_timeout))
        except Exception as ex:
            log_error = "Unable to Reset DCPMM Thresholds to it's default values due to exception '{}'".format(
                ex)
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def collect_all_logs(self):
        """
        This Method is used to collect all the OS Level Logs.

        :return None
        :raise RuntimeError if there is any error while collecting the logs
        """
        try:
            self._os.wait_for_os(int(self._reboot_timeout))
            for command_line in self._LIST_OF_COLLECT_OS_LOGS_COMMANDS:
                cmd_result = self._os.execute(command_line, self._command_timeout)
                if cmd_result.cmd_failed():
                    log_error = "Failed to run command '{}' with " \
                                "return value = '{}' and " \
                                "std_error='{}'..".format(command_line, cmd_result.return_code, cmd_result.stderr)
                    self._log.error(log_error)
                    raise RuntimeError(log_error)
                else:
                    self._log.info("The command '{}' executed successfully.. and Output of '{}' log is {}"
                                   u''.format(command_line, command_line, cmd_result.stdout.strip()))
        except Exception as ex:
            log_error = "Unable to Collect OS Logs due to exception '{}'".format(ex)
            self._log.error(log_error)

    def inject_dual_inline_memory_temperature_error(self):
        """
        This Function inject temperature error by running below ipmctl commands on SUT
        - ipmctl show set -dimm 0xXXXX Temperature=100

        :return: None
        :raise: RuntimeError for any error during ipmctl command execution or parsing error.
        """
        self._log.info("Checking the dimms are healthy and manageable:")
        self.get_list_of_dimms_which_are_healthy_and_manageable()
        self._log.info("Setting the Temperature")
        # Inject the Temperature on dimm
        command_to_set_temp = "date -u;ipmctl set -dimm {} Temperature=100".format(
            self.dimm_healthy_and_manageable_list[0])
        set_temperature = self._os.execute(command_to_set_temp, self._command_timeout)

        if set_temperature.cmd_failed():
            log_error = "Failed to run ipmctl set -dimm temperature command with return value = " \
                        "'{}' and std_error='{}'..".format(set_temperature.return_code, set_temperature.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        self._time_stamp = set_temperature.stdout.strip().split('\n')[0]
        self._log.info("Set Temperature is : {}".format(set_temperature.stdout.strip().split('\n')))

        return True

    def detected_injected_temp_error(self):
        """
        This Function detect the injected temperature error by running below ipmctl commands on SUT
        - ipmctl show -error Thermal -dimm 0xXXXX

        :return: None
        :raise: RuntimeError for any error during ipmctl command execution or parsing error.
        """
        try:
            self._log.info("Detected the injected temperature error from the DCPMM:")
            # show the Thermal Error on dimm
            thermal_error_cmd = "ipmctl show -error Thermal -dimm {}".format(self.dimm_healthy_and_manageable_list[0])
            error_inj_error = self._os.execute(thermal_error_cmd, self._command_timeout)

            if error_inj_error.cmd_failed():
                log_error = "Failed to run ipmctl show -error Thermal command with return value = '{}' and " \
                            "std_error='{}'..".format(error_inj_error.return_code,
                                                      error_inj_error.stderr)
                self._log.error(log_error)
                raise RuntimeError(log_error)

            self.verify_temperature_error_accuracy(error_inj_error.stdout.strip())
            self._log.info("Injected Error are now {}".format(error_inj_error.stdout.strip()))

            if "Thermal Error" in error_inj_error.stdout.strip().split("\n")[0]:
                self._log.info("Thermal Error found on dimm")
            else:
                self._log.error("Thermal Error is not found on dimm, Error is not injected")
                raise RuntimeError("Thermal Error is not found on dimm, Error is not injected")

            clr_temp_error = "ipmctl set -dimm {} Clear=1 Temperature=1".format(
                self.dimm_healthy_and_manageable_list[0])

            # Clearing the dimm error
            command_result = self._os.execute(clr_temp_error, self._command_timeout)

            if command_result.cmd_failed():
                log_error = "Failed to run clear the dimm error command with return value = '{}' and " \
                            "std_error='{}'..".format(command_result.return_code,
                                                      command_result.stderr)
                self._log.error(log_error)
                raise RuntimeError(log_error)

            self._log.info("Cleared Injected Error {}".format(command_result.stdout.strip()))
        except Exception as ex:
            raise ("Command execution error on SUT: {}".format(ex))

    def verify_temperature_error_accuracy(self, temperature_error):
        """
        This Function to validate the temperature error, system time stamp, temperature type

        :param: temperature error log to validate
        :return: None
        :raise: RuntimeError for any error during execution.
        """
        try:
            regex_code = r'\s*(.*)\s\:\s(.*)'
            temperature_error_log = re.findall(regex_code, temperature_error)
            self._log.info("Error Details : {}".format(temperature_error_log))
            time_stamp = []
            temperature_accuracy = []
            temperature_type = []
            for error_log_param in temperature_error_log:
                if error_log_param[0] == 'System Timestamp':
                    time_stamp.append(error_log_param[1])
                elif error_log_param[0] == 'Temperature':
                    temperature_accuracy.append(error_log_param[1])
                elif error_log_param[0] == 'Temperature Type':
                    temperature_type.append(error_log_param[1])

            regex_code = ".*:"
            time_stamp_formated = self._time_stamp.replace("  ", " 0")
            error_log_param = [time_stamp.index(i) for i in time_stamp if re.search('^' +
                                                                                    re.findall(regex_code,
                                                                                               time_stamp_formated)[0],
                                                                                    i)]
            self._log.info("System Time Stamp : {}".format(time_stamp[error_log_param[0]]))
            if temperature_accuracy[error_log_param[0]] == '100C':
                self._log.info("Temperature set found : {}".format(temperature_accuracy[error_log_param[0]]))
            else:
                self._log.error("Injected Temperature Found Wrong : {}".format(temperature_accuracy[error_log_param[
                    0]]))

            if temperature_type[error_log_param[0]] == '0 - Media Temperature':
                self._log.info('Temperature Type found : {}'.format(temperature_type[error_log_param[0]]))
            else:
                self._log.error("Temperature Type Found Wrong : {}".format(temperature_type[error_log_param[0]]))

        except Exception as ex:
            log_error = "An exception occurred : {}".format(str(ex))
            self._log.error(log_error)
            raise ex

    def verify_shutdown_sensor_status_and_current_value(self, is_dirty_shutdown_triggered=False,
                                                        is_system_rebooted=False):
        """
        This Method is used to verify Shutdown Sensor Status and Current Value of Latched Shutdown and UnLatched
        Shutdown Count Initially and after Triggering the Dirty Shutdown on Dimm and After Rebooting the Sut and
        Comparing these Values with Initial Values.

        :return:
        """
        command_result = self._os.execute(
            self._IPMCTL_SHUTDOWN_STATUS_CMD.format(self.dimm_healthy_and_manageable_list[0]),
            self._command_timeout)
        if command_result.cmd_failed():
            log_error = "Failed to run {} command with return value = '{}' and " \
                        "std_error='{}'..".format(self._IPMCTL_SHUTDOWN_STATUS_CMD, command_result.return_code,
                                                  command_result.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        dimm_shutdown_status_cmd_output = command_result.stdout.split(",")[0]
        self._log.info(dimm_shutdown_status_cmd_output)
        if "HealthState=Healthy" in dimm_shutdown_status_cmd_output and "LatchedLastShutdownStatus" != "Unknown":
            self._log.info("Health State of dimm is Normal and Shutdown Status is not Unknown")
        else:
            log_error = "Dimms Health status is not Normal"
            self._log.error(log_error)
            raise RuntimeError(log_error)

        command_result = self._os.execute(
            self._IPMCTL_SHOW_SENSOR_DATA_CMD.format(self.dimm_healthy_and_manageable_list[0]),
            self._command_timeout)
        if command_result.cmd_failed():
            log_error = "Failed to run {} command with return value = '{}' and " \
                        "std_error='{}'..".format(self._IPMCTL_SHOW_SENSOR_DATA_CMD, command_result.return_code,
                                                  command_result.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        dimm_sensor_data_output = command_result.stdout.strip().split(",")[0]
        self._log.info(dimm_sensor_data_output)
        latched_shutdown_string = re.compile(self._REGEX_CMD_FOR_LATCHED_DIRTY_SHUTDOWN_COUNT)
        unlatched_shutdown_string = re.compile(self._REGEX_CMD_FOR_UNLATCHED_DIRTY_SHUTDOWN_COUNT)
        latched_dirty_shutdown_value = \
            int(latched_shutdown_string.search(dimm_sensor_data_output).group().strip().split("|")[2])
        unlatched_dirty_shutdown_value = \
            int(unlatched_shutdown_string.search(dimm_sensor_data_output).group().strip().split("|")[2])
        if is_dirty_shutdown_triggered:
            if is_system_rebooted:
                if latched_dirty_shutdown_value == self.latched_dirty_shutdown_value + 1 and \
                        unlatched_dirty_shutdown_value == self.unlatched_dirty_shutdown_value + 1:
                    self._log.info(
                        "Latched Dirty Shut Down value and Un latched Dirty Shut Down Value are Increased after "
                        "dirty shutdown is Triggered and System is Rebooted")
                else:
                    log_error = "Latched Dirty Shut Down value and Un latched Dirty Shut Down Value are Not Increased" \
                                " after dirty shutdown is Triggered and System is Rebooted"
                    self._log.error(log_error)
                    raise RuntimeError(log_error)
            else:
                if latched_dirty_shutdown_value == self.latched_dirty_shutdown_value and \
                        unlatched_dirty_shutdown_value == self.unlatched_dirty_shutdown_value:
                    self._log.info("Latched Dirty Shut Down value and Un latched Dirty Shut Down Value are same even "
                                   "after dirty shutdown is Triggered")
                else:
                    log_error = "Latched Dirty Shut Down value and Un latched Dirty Shut Down Value are Not same " \
                                "after dirty shutdown is Triggered"
                    self._log.error(log_error)
                    raise RuntimeError(log_error)
        else:
            self.latched_dirty_shutdown_value = latched_dirty_shutdown_value
            self._log.info("Initial Latched Dirty Shutdown Count is '{}'".format(self.latched_dirty_shutdown_value))
            self.unlatched_dirty_shutdown_value = unlatched_dirty_shutdown_value
            self._log.info("Initial Unlatched Dirty Shutdown Count is '{}'".format(self.unlatched_dirty_shutdown_value))

    def verify_dcpmms_are_configured_in_1lm_mode(self):
        """
        This Method is Used to Verify if DCPMM Dimms are Configured in 1 LM Mode.

        :return:
        :raise: RuntimeError if Dcpmm's are not configured in 1 LM Mode
        """
        command_result = self._os.execute(self._CMD_FOR_PERSISTENT_MEMORY, self._command_timeout)
        if command_result.cmd_failed():
            log_error = "Failed to run {} command with return value = '{}' and " \
                        "std_error='{}'..".format(self._CMD_FOR_PERSISTENT_MEMORY, command_result.return_code,
                                                  command_result.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        persistent_memory_cmd_output = command_result.stdout.split(",")[0]
        self._log.info(persistent_memory_cmd_output)
        regex_output = re.findall(self._REXEX_FOR_FINDING_RANGE, persistent_memory_cmd_output)
        self._LOWER_LIMIT = int("0x"+regex_output[0][0], 16)
        self._UPPER_LIMIT = int("0x"+regex_output[0][1], 16)
        regex_out = re.findall(self._REGEX_CMD_FOR_PERSISTENT_MEMORY, persistent_memory_cmd_output)
        if len(regex_out) != 0:
            self._log.info("DCPMM's are Configured in 1LM Mode")
        else:
            log_error = "DCPMM's are Not configured in 1LM Mode"
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def list_dcpmm_existing_error_logs(self):
        """
        This Method is Used to List the Existing DCPMM Error Logs.

        :return:
        """
        command_result = self._os.execute(self._IPMCTL_CMD_FOR_LISTING_EXISTING_DCPMM_ERRORS.
                                          format(self.dimm_healthy_and_manageable_list[0]), self._command_timeout)
        if command_result.cmd_failed():
            log_error = "Failed to run {} command with return value = '{}' and " \
                        "std_error='{}'..".format(self._IPMCTL_CMD_FOR_LISTING_EXISTING_DCPMM_ERRORS,
                                                  command_result.return_code, command_result.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        dcpmm_existing_errors_cmd_output = command_result.stdout.strip()
        self._log.info(dcpmm_existing_errors_cmd_output)

    def trigger_dirty_shutdown_on_dcpmm_dimm(self):
        """
        This Method triggers an artificial ADR failure on all manageable DCPMM s resulting in a dirty shutdown on each
        DCPMM on the next reboot.

        :return:
        :raise: RuntimeError if Dirty Shutdown is Not Triggered.
        """
        command_result = self._os.execute(self._IPMCTL_CMD_FOR_TRIGGERING_DIRTY_SHUTDOWN.
                                          format(self.dimm_healthy_and_manageable_list[0]), self._command_timeout)
        if command_result.cmd_failed():
            log_error = "Failed to run {} command with return value = '{}' and " \
                        "std_error='{}'..".format(self._IPMCTL_CMD_FOR_TRIGGERING_DIRTY_SHUTDOWN,
                                                  command_result.return_code, command_result.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        trigger_dirty_shutdown_cmd_output = command_result.stdout.strip()
        if "Trigger a dirty shut down on DIMM {}: Success".format(self.dimm_healthy_and_manageable_list)[0] in \
                trigger_dirty_shutdown_cmd_output:
            self._log.info("Dirty Shutdown is Triggered on Dimm '{}' Successfully".
                           format(self.dimm_healthy_and_manageable_list)[0])
        else:
            log_error = "Dirty Shutdown is Not triggered on Dimm '{}'".format(self.dimm_healthy_and_manageable_list)[0]
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def verify_latch_system_state(self):
        """
        This Method is Used to verify if LSS is Enabled , with the Help of CSCRIPTS.

        :return:
        :raise: RunTimeError if LSS is not Enabled.
        """
        self._log.info("Verifying Latch Systems State with the help of Cscripts")
        self._sdp.start_log(self.log_file_path, "w")
        self._nvd.dimms[0].get_latch_system_shutdown_state()
        self._sdp.stop_log()
        with open(self.log_file_path, "r") as log_file:
            log_file_list = log_file.readlines()
            self._log.info("".join(log_file_list))
            regex_out = re.findall(self._REGEX_CMD_FOR_LATCH_SYSTEM_SHUTDOWN_STATE, "".join(log_file_list))
            if len(regex_out) != 0:
                self._log.info("Latch System Shutdown is in Enable State")
            else:
                log_error = "Latch System Shutdown is Not in Enable State"
                self._log.error(log_error)
                raise RuntimeError(log_error)

    def verify_dcpmm_latch_last_shutdown_status(self):
        """
        This Method is used to Verify if DCPMM Dimm Latched System Shutdown State(LSS) is Mentioned as  Dirty Shutdown.

        :return:
        :raise: RunTimeError if LSS is not Mentioned as Dirty ShutDown.
        """
        self._log.info("Verify whether Latched Last Shutdown Status (LSS) is mentioned as Dirty Shutdown")
        self._sdp.start_log(self.log_file_path, "w")
        self._sdp.halt()
        self._nvd.dimms[0].get_smart_info()
        self._sdp.stop_log()
        with open(self.log_file_path, "r") as log_file:
            log_file_list = log_file.readlines()
            self._log.info("".join(log_file_list))
            regex_out = re.findall(self._REGEX_CMD_FOR_LAST_SHUTDOWN_STATUS, "".join(log_file_list))
            if len(regex_out) != 0:
                self._log.info("Latched Last System Shutdown is Dirty Shutdown")
            else:
                log_error = "Latched Last System Shutdown is Not Dirty Shutdown"
                self._log.error(log_error)
                raise RuntimeError(log_error)

    def rebooting_the_sut(self):
        """
        This Method is used to Reboot the Sut to Verify the Latched Shutdown Status is Enabled after Reboot and Verify
         if DCPMM Dimm Latched System Shutdown State is Dirty Shutdown and Latched Shutdown and Un Latched Shutdown
         Count is Increased from Previous Count.

        :return:
        """
        self._log.info("Reboot the Sut to verify Latched Shutdown Status")
        self._ac_power.ac_power_off(self._common_content_configuration.ac_timeout_delay_in_sec())
        time.sleep(self._common_content_configuration.itp_halt_time_in_sec())
        self._ac_power.ac_power_on(self._common_content_configuration.ac_timeout_delay_in_sec())
        self._os.wait_for_os(int(self._reboot_timeout))
        self._log.info("Rebooting of Sut is Completed")

    def verify_dimm_health_status(self, status="NORMAL"):
        """
        This method captures cscripts log by executing get_smart_info() and returns the viral interrupt
        and viral status by parsing the log file

        :return: Viral_interrupt value
        """
        health_status = False
        self._sdp.start_log(self._SDP_LOG_FILE_NAME)
        self._nvd.dimms[0].get_smart_info()
        self._sdp.stop_log()
        logfile = os.path.abspath(self._SDP_LOG_FILE_NAME)
        file_header = open(logfile, "r")
        dimm_health = file_header.readlines()
        if status == "NORMAL":
            regex = self._REGEX_CMD_DIMM_HEALTH_NORMAL
        else:
            regex = self._REGEX_CMD_DIMM_HEALTH_FATAL
        for each in dimm_health:
            if re.match(regex, each.strip()):
                self._log.info(each.strip())
                health_status = True
        file_header.close()
        os.remove(logfile)
        if not health_status:
            self._log.error("Unable to get health status of DIMMs")
            raise RuntimeError("Failed to run get_smart_info() in cscripts")
        return health_status

    def verify_media_user_data_access(self, access=True):
        """
        This method captures cscripts log by executing get_smart_info() and returns the viral interrupt
        and viral status by parsing the log file

        :return: Viral_interrupt value
        """
        regex = ""
        bsr_flag = False
        self._sdp.start_log(self._SDP_LOG_FILE_NAME)
        self._nvd.dimms[0].show_bsr()
        self._sdp.stop_log()
        logfile = os.path.abspath(self._SDP_LOG_FILE_NAME)
        file_header = open(logfile, "r")
        show_bsr_data = file_header.readlines()
        if access:
            regex = self._REGEX_CMD_FOR_MEDIA_USER_DATA_ACCESS
        else:
            regex = self._REGEX_CMD_FOR_MEDIA_USER_NO_DATA_ACCESS
        for each in show_bsr_data:
            if re.match(regex, each.strip()):
                self._log.info(each.strip())
                bsr_flag = True
        file_header.close()
        os.remove(logfile)
        if not bsr_flag:
            self._log.error("Unable to get show_bsr() info")
            raise RuntimeError("Failed to run show_bsr() in cscripts")
        return bsr_flag

    def inject_and_verify_fatal_media_error(self):
        """
        This test injects a Fatal Media error and checks if the system detects and responds to the error in a 1LM configuration.

        :returns: Boolean
        :raises: RuntimeError
        """
        try:
            inject_fatal_media_error_success = True
            target_dimm_id = self._ipmctl_provider.dimm_healthy_and_manageable_list[0]
            self._log.info("Halt the System!")
            self._sdp.halt()
            self._log.info("Set the DCPMM access path to auto and Refresh the DCPMM topology!")
            self.set_dcpmm_access_path_to_auto_and_refresh_topology()
            self._log.info("Unhalt the CPU!")
            self._sdp.go()
            self._log.info("Verify DCPMMs are Healthy and Manageable")
            if target_dimm_id not in self._ipmctl_provider.dimm_healthy_and_manageable_list:
                self._log.error("Target DIMM that we are testing on is not Healthy and Manageable!")
                raise RuntimeError("DCPMMs are not Healthy and Manageable")
            self._ipmctl_provider.get_list_of_dimms_which_are_healthy_and_manageable()
            self._log.info("Clear OS logs and dmesg logs!")
            self._common_content_lib.clear_os_log()
            self._common_content_lib.clear_dmesg_log()
            self._log.info("Verify the Media is enabled and Verify user data is accessible using C-Scripts")
            self.verify_media_user_data_access()
            self._log.info("Check DIMM Health Status!")
            self.verify_dimm_health_status()
            self._log.info("Inject a Fatal Media Error to DCPMM media")
            self._ipmctl_provider.inject_fatal_media_error()
            self._ipmctl_provider.populate_memory_dimm_information()
            if target_dimm_id in self._ipmctl_provider.dimm_healthy_and_manageable_list:
                self._log.error("Target DIMM that we are testing should not be Healthy and Manageable!")
                raise RuntimeError("DCPMMs are Healthy and Manageable after error injection!")
            self._log.info("Verify user data is not accessible using C-Scripts")
            self.verify_media_user_data_access(access=False)
            self._log.info("Verify the Health Status is Fatal using C-Script")
            self.verify_dimm_health_status(status="FATAL")
            self._log.info("Change Bios Configuration for error clearing")
            self._error_clear_bios_util.set_bios_knob()  # To set the bios knob setting.
            self._log.info("Bios Knobs are Set as per our TestCase and Reboot in Progress to Apply the Settings")
            self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
            self._error_clear_bios_util.verify_bios_knob()
            self._log.info("After rebooting the SUT, clear the errors using C-Scripts.")
            self._nvd.dimms[0].set_software_triggers(4, 0)
            self._os.wait_for_os(self._os_time_out_in_sec)
            self._ipmctl_provider.populate_memory_dimm_information()
            if target_dimm_id not in self._ipmctl_provider.dimm_healthy_and_manageable_list:
                self._log.error("Target DIMM that we are testing on is not Healthy and Manageable!")
                raise RuntimeError("DCPMMs are not Healthy and Manageable")
            self._ipmctl_provider.get_list_of_dimms_which_are_healthy_and_manageable()
            self._log.info("Check DCPMMs status with ipmctl")
            self.verify_dimm_health_status()
            self._log.info("Using CScripts, verify the Media State is Enabled")
            self.obtaining_list_of_dcpmm_dimms()
            self._log.info("Check if error was logged with ipmctl and clear injected Poison")
            error_logs = self._ipmctl_provider.list_dcpmm_existing_error_logs()
            dcpmm_existing_errors_cmd_output = error_logs.split("\n")
            smart_health_status_change = False
            for each in dcpmm_existing_errors_cmd_output:
                if re.match(self._REGEX_CMD_FOR_HEALTH_STATUS_CHANGE_ERROR, each.strip()):
                    smart_health_status_change = True
            if not smart_health_status_change:
                raise RuntimeError("DCPMMs Health Status Not Changed in error Logs!")
            self._sdp.start_log(self.log_file_path, "w")
            self._ipmctl_provider.list_dcpmm_existing_error_logs()
            self._log.info("Checking the Error Log of DCPMM")
            self._nvd.dimms[0].error_log()  # Checking the Cscripts Error Log
            self._sdp.stop_log()  # Closing Cscripts log File
            with open(self.log_file_path) as log_file:
                self._log.info(
                    "Checking DCPMM Error Log Output is {}".format(
                        log_file.read()))
            self._ipmctl_provider.clear_fatal_media_error()
            self._log.info("Clear all the error Logs of DCPMM")
            self._sdp.reset_break = 1
            self._sdp.reset_target()
            self._nvd.dimms[0].clear_history()
            self._sdp.reset_break = 0
            self._sdp.reset_target()
            self._os.wait_for_os(self._os_time_out_in_sec)
            self._log.info("Collect all logs for evidence!")
            self.collect_all_logs()
            return inject_fatal_media_error_success
        except Exception as ex:
            log_error = "Unable to inject and verify fatal media error due to exception '{}'" \
                .format(ex)
            self._log.error(log_error)
            raise ex

    def obtain_target_address(self, soc_ket=0, m_c=0, chan_nel=0):
        """
        This method is to find the target address using addtran object.

        param: soc_ket- use for socket number
        param: m_c- use for mc number
        param: chan_nel- use for channel number
        return: rank address and system address
        raise: Exception
        """
        try:
            flag = 0
            addr_tran = 0
            self._sdp.halt()
            product = self._common_content_lib.get_platform_family()
            if product in self._common_content_lib.SILICON_10NM_CPU:
                add_tran_obj = self._cscripts.get_add_tran_obj()
                self._log.info("Search the target Address")
                ti = add_tran_obj.TranslationInfo()
                addr_tran = self._LOWER_LIMIT
                while addr_tran < self._UPPER_LIMIT:
                    ti.core_addr = addr_tran
                    self._sdp.start_log(self.log_file_path, "w")
                    add_tran_obj.core_address_to_dram_address(ti, verbose=1)
                    ti.show_results()
                    self._sdp.stop_log()
                    with open(self.log_file_path, 'r') as mirroring_log:
                        add_mapped_log = mirroring_log.read()
                        self._log.info(add_mapped_log)
                        rank_value = re.findall(self._REGEX_FOR_RANK, add_mapped_log)
                        sok = re.findall(self._REGEX_FOR_SOCKET, add_mapped_log)
                        mc = re.findall(self._REGEG_FOR_MC, add_mapped_log)
                        ch = re.findall(self._REGEX_FOR_CHANNEL, add_mapped_log)
                        if sok[0] == soc_ket and mc[0] == m_c and chan_nel == ch[0]:
                            rank_value_in_str = "0x"+rank_value[0].replace('_', '')
                            rank_value_in_int = int(rank_value_in_str, 16)
                            rank_value_in_hex = hex(rank_value_in_int)
                            if self._START_LIMIT <= rank_value_in_int <= self._LAST_LIMIT:
                                addr_tran = addr_tran + self._LAST_LIMIT
                                continue
                            else:
                                flag = 1
                                break
                        addr_tran = addr_tran + 0x10000
                if flag:
                    self._log.debug("Rank Address : {}".format(rank_value_in_hex))
                    self._log.debug("Channel Number : {}".format(ch))
                    self._log.debug("Socket Number : {}".format(sok))
                    self._log.debug("Machine Number : {}".format(mc))
                else:
                    log_err = "An exception Occurred : Rank address was not found"
                    self._log.error(log_err)
                    raise log_err
        except Exception as ex:
            raise ex
        return rank_value_in_hex, hex(addr_tran)

    def set_poison_bit_at_valid_device(self, addr):
        """
        This method is to set the poison bit at valid address.

        param: addr - rank address to inject the error
        raise: Exception if bit is fail to poison.
        """
        try:
            self._sdp.halt()
            self._log.info("Inject the poison Error")
            self._sdp.start_log(self.log_file_path, "w")
            self._nvd.dimms[0].inject_poison_error(0x2, addr)
            self._sdp.stop_log()
            with open(self.log_file_path, "r") as inject_log:
                read_inject_log = inject_log.read()
                self._log.info(read_inject_log)
                status = re.findall(self._REGEX_FOR_SET_POISON_BIT, read_inject_log, re.IGNORECASE | re.MULTILINE)
                if status:
                    self._log.info("Bit is poisoned successfully as expected")
                else:
                    log_err = "Bit was not poisoned successfully"
                    raise log_err
        except Exception as ex:
            raise ex
        finally:
            self._sdp.go()

    def set_address_range_scrubber_to_inject_scrub_poison(self, regex, rank_addr):
        """
        The method to set address range scrubber for injecting scrub poison

        return: True if error is captured in Log else False.
        raise: Exception ex
        """
        try:
            ret_val = []
            self._sdp.halt()
            self._sdp.start_log(self.log_file_path, "w")
            self._nvd.dimms[0].set_address_range_scrub(1, self._START_LIMIT_ADDR, self._END_LIMIT_ADDR+int(rank_addr,
                                                                                                           16))
            self._nvd.dimms[0].get_long_operation_status()
            self._sdp.stop_log()
            with open(self.log_file_path, "r") as inject_log:
                read_inject_log = inject_log.read()
                self._log.info(read_inject_log)
                ret_val.append(re.findall(regex, read_inject_log))
                regex_out_put = re.findall(r"DPA\sError\sAddresses\s\S+\s:\s(\S+)", read_inject_log)
                for addr in regex_out_put:
                    if int(rank_addr, 16) == int(addr, 16):
                        ret_val.append(True)
                        return all(ret_val)
            return False

        except Exception as ex:
            raise ex

        finally:
            self._sdp.go()

    def check_dpa_error_in_log(self, rank_addr):
        """
        This method is to check dpa error in  log.

        :raise Exception
        """
        try:
            ret_val = False
            self._sdp.halt()
            self._sdp.start_log(self.log_file_path, "w")
            self._nvd.error_log()
            self._sdp.stop_log()
            with open(self.log_file_path, "r") as inject_log:
                read_inject_log = inject_log.read()
                self._log.info(read_inject_log)
                regex_out_put = re.findall(r"DPA\s:\s(\S+)", read_inject_log)
                for addr in regex_out_put:
                    if int(rank_addr, 16) == int(addr, 16):
                        ret_val = True
                        return ret_val

            return ret_val
        except Exception as ex:
            log_err = "Unable to execute the error log itp command: {}".format(ex)
            self._log.error(log_err)
            raise log_err

    def check_viral_policy(self):
        """
        This method is to validate viral status policy is False or not.
        """
        viral_status_and_policy = [r'Viral\sStatus\s:\sFalse', r'Viral\sPolicy\s:\sEnabled']
        self._sdp.start_log(self.log_file_path, "w")
        self._nvd.dimms[0].get_viral_policy()
        self._sdp.stop_log()
        with open(self.log_file_path, "r") as viral_log:
            read_viral_log = viral_log.read()
            self._log.info(read_viral_log)
            regex_out_put = self._common_content_lib.extract_regex_matches_from_file(read_viral_log,
                                                                                     viral_status_and_policy)
            if regex_out_put:
                self._log.info("Viral Status is False and Viral policy is Enabled as Expected")
            else:
                log_err = r"Unexpected Value found for Viral status and policy"
                raise log_err

    def verify_os_log(self, journalctl_sig_list, dmesg_sig_list, var_log_message_list):
        """
        Verify the Os Log

        :param journalctl_sig_list
        :param dmesg_sig_list
        :param var_log_message_list
        """
        journal_ctl = self._os_log_obj.verify_os_log_error_messages(__file__,
                                                                    self._os_log_obj.DUT_JOURNALCTL_FILE_NAME,
                                                                    journalctl_sig_list, check_error_not_found_flag=
                                                                    True)
        dmesg = self._os_log_obj.verify_os_log_error_messages(__file__, self._os_log_obj.DUT_DMESG_FILE_NAME,
                                                              dmesg_sig_list, check_error_not_found_flag=True)
        var_log_message = self._os_log_obj.verify_os_log_error_messages(
            __file__, self._os_log_obj.DUT_MESSAGES_FILE_NAME, var_log_message_list, check_error_not_found_flag=True)
        return journal_ctl and dmesg and var_log_message

    def set_percentage_alarm_thresholds_and_verify(self, spare_block_threshold, expected_tripped_state,
                                                   alarm_spares_state, package_sparing_has_happened, flag=0,
                                                   sw_tr_flag=False):
        """
        By Default Alarm's might be disabled and by using this Method we will enable the Alarm's
        and Set the Threshold Values for Alarm and verify whether Alarm's are enabled or not and modify the
        Threshold Value of Percentage remaining  to check whether Percentage remaining Trip is in Tripped State or Not
        and Checking whether the Alarm Spare state is in false state or in True State.

        :param spare_block_threshold: threshold value for Percentage remaining
        :param expected_tripped_state: Specifies whether Percentage Remaining should be in tripped state or not
        :param alarm_spares_state: Specifies whether Alarm Spares State should be in True or False
        :param package_sparing_has_happened: Specifies whether package_sparing_has_happened is true or not.
        :param flag: use for validate
        :param sw_tr_flag: Specifies whether to call set trigger software funtion
        :return None
        :raise RuntimeError if Alarm's are Not Enabled Properly
        :raise RuntimeError if trip state not set as expected
        """
        try:
            percent_remaining_enable = 1  # this should be enabled
            media_temperature_enable = 1  # this should be enabled
            core_temperature_enable = 0  # this should be disabled
            self._log.info("Enabling the Alarm's and Setting the Threshold Values for Alarm")
            # Start logging cscripts command output to log file
            self._sdp.start_log(self.log_file_path, "w")
            # Enabling the Alarm's and Setting Threshold Values for Alarm's
            self._nvd.dimms[0].set_alarm_thresholds(percent_remaining_enable,
                                                    media_temperature_enable,
                                                    core_temperature_enable,
                                                    spare_block_threshold,
                                                    self._MEDIA_DIMM_THRESHOLD_VALUE,
                                                    self._MAX_TEMP)
            if not sw_tr_flag:
                self._nvd.dimms[0].set_software_triggers(self._PERCENTAGE_REMAINING_TRIGGER,
                                                         self._PACKAGING_SPARING_TRIGGER,
                                                         spare_block_threshold + flag)

            self._nvd.dimms[0].get_smart_info()
            self._sdp.stop_log()  # Closing Cscripts Log File
            self._log.info(
                "Beginning of set_percentage_alarm_thresholds_and_verify Output with Percentage Threshold Value of '{}'"
                    .format(spare_block_threshold))
            # Opening Cscripts Log File and Validating
            self.validate_cscripts_logs(spare_block_threshold=spare_block_threshold + flag, alarm_spares_state=
            alarm_spares_state, expected_tripped_state=expected_tripped_state,
                                        package_sparing_has_happened=package_sparing_has_happened)
            self._log.info(
                "set_percentage_alarm_thresholds_and_verify Functionality Output with Threshold Value of '{}'"
                " is Completed".format(spare_block_threshold))
        except Exception as ex:
            log_error = "Unable to set the Threshold Values for Percentage Alarm due to exception '{}'".format(ex)
            self._log.error(log_error)
            raise content_exception.TestFail(log_error)

    def set_dimm_percentage_and_verify(self, spare_block_threshold, expected_tripped_state, alarm_spares_state,
                                       package_sparing_has_happened):
        """
        This Method is Used to modify the Dimm Percentage with respective to Threshold Value and Check the Percentage
         Remaining Value and Checking the Percentage Remaining is in Tripped State or Not and Checking the Alarm
         Spare state is in False state or True state.

        :param: spare_block_threshold - dimm percentage to set.
        :param: expected_tripped_state - specifies whether dimm should go to tripped state or not.
        :param: alarm_spares_state - specifis whether alarm spare state is true or not.
        :param: package_sparing_has_happened - specifies whether package sparing has happened true or not.

        :return None
        :raise RuntimeError if there is any error in Setting the Dimm Percentage to Threshold value minus one
        """
        try:
            self._log.info("Set the Dimm percentage to '{}'..".format(spare_block_threshold))
            # Reopening the Cscripts Log File
            self._sdp.start_log(self.log_file_path, "w")
            self._nvd.dimms[0].set_software_triggers(self._PERCENTAGE_REMAINING_TRIGGER,
                                                     self._PACKAGING_SPARING_TRIGGER,
                                                     spare_block_threshold)
            self._nvd.dimms[0].get_smart_info()  # Checking the Health Status
            self._sdp.stop_log()  # Closing Cscripts log File
            # Reopening Cscripts Log File to Check whether
            self._log.info("Beginning of log with percentage remaining value '{}'".format(spare_block_threshold))
            # Validating outputs of Cscripts Log file
            self.validate_cscripts_logs(spare_block_threshold=spare_block_threshold, expected_tripped_state=
            expected_tripped_state, alarm_spares_state=alarm_spares_state,
                                        package_sparing_has_happened=package_sparing_has_happened)
            self._log.info("End of log with percentage remaining value '{}".format(spare_block_threshold))

        except Exception as ex:
            log_error = "Unable to set the value of Dimm Percentage to '{}' one due to" \
                        " exception '{}'".format(spare_block_threshold, ex)
            self._log.error(log_error)
            raise content_exception.TestFail(log_error)

    def validate_cscripts_logs(self, spare_block_threshold, alarm_spares_state, expected_tripped_state,
                               package_sparing_has_happened):
        """
         This Method is used to Validate the Cscripts Log to Check the Percentage
         Remaining Value and Checking the Percentage Remaining is in Tripped State or Not and Checking the Alarm
         Spare state is in False state or True state and Checking the Percentage Remaining Spare Capacity.

         :param spare_block_threshold: dimm percentage to set
         :param alarm_spares_state: specifies whether alarm spares state should be True or False
         :param expected_tripped_state:specifies whether dimm should go to tripped state or not
         :param package_sparing_has_happened:specifies whether package sparing should be True or False.
         :return:None
         :raise RuntimeError if there is any error in Setting the Dimm Percentage to Threshold
         :raise RuntimeError if there is any error in Setting the Dimm Percentage Remaining Threshold Value
         """
        try:
            validating_list = [spare_block_threshold, expected_tripped_state, package_sparing_has_happened]
            ndctl_cmd_result = self._os.execute(self._NDCTL_LIST_CMD, self._command_timeout)
            if ndctl_cmd_result.cmd_failed():
                log_error = "Failed to run command '{}' with " \
                            "return value = '{}' and " \
                            "std_error='{}'..".format(self._NDCTL_LIST_CMD, ndctl_cmd_result.return_code,
                                                      ndctl_cmd_result.stderr)
                self._log.error(log_error)

            with open(self.log_file_path, "r") as log_file:
                log_file_list = log_file.readlines()
                self._log.info("".join(log_file_list))

                for index in range(0, 3):
                    regex_out_put = re.findall(self._REGEX_CMD_FOR_PERCENTAGE_THRESHOLD[index].format(
                        validating_list[index]), "\n".join(log_file_list))
                    if len(regex_out_put) > 0:
                        self._log.info("{} is : {}".format(self._MESSAGE_LOG_FOR_THRESHOLD_PER[index],
                                                           validating_list[index]))
                    else:
                        log_error = self._UNEXPECTED_MESSAGE_LOG_FOR_THRESHOLD_PER[index]
                        raise content_exception.TestFail(log_error)
                regex_alarm_spare_state = re.findall(self._REGEX_CMD_FOR_NDCTL_LIST.format(alarm_spares_state),
                                                     "\n".join(
                                                         ndctl_cmd_result.stdout.strip().split(",")), re.IGNORECASE)
                if regex_alarm_spare_state:
                    self._log.info("Alarm Spare State is in {} state".format(alarm_spares_state))
                else:
                    log_error = "Alarm Spare State was not found as expected: {}".format(alarm_spares_state)
                    raise content_exception.TestFail(log_error)
        except Exception as ex:
            log_err = "An exception Occurred: {}".format(ex)
            raise content_exception.TestFail(log_err)
