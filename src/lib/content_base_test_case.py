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

import os
import time
import datetime
from xml.etree import ElementTree

from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.physical_control import PhysicalControlProvider
from dtaf_core.providers.console_log import ConsoleLogProvider
from dtaf_core.providers.bios_provider import BiosProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.lib.dtaf_constants import DebuggerInterfaceTypes
from dtaf_core.lib.configuration import ConfigurationHelper
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider


from src.lib.bios_util import BiosUtil
from src.lib.content_configuration import ContentConfiguration
from src.lib.common_content_lib import CommonContentLib
from src.lib import content_exceptions
from src.lib.dtaf_content_constants import PhysicalProviderConstants
from src.lib.dtaf_content_constants import PlatformType
from src.lib.dtaf_content_constants import PlatformEnvironment
from src.lib.grub_util import GrubUtil
from src.lib.dtaf_content_constants import ProviderXmlConfigs
from src.lib.content_artifactory_utils import ContentArtifactoryUtils

from src.utils.telemetry import Telemetry


class ContentBaseTestCase(BaseTestCase):
    """ContentBaseTestCase is base test for all the dtaf content test cases"""

    AC_TIMEOUT = WAIT_TIME = 30
    _SERIAL_LOG_FILE = "serial_log.log"
    SV = None
    SDP = None

    def __init__(self, test_log, arguments, cfg_opts,
                 bios_config_file_path=None):
        """
        Create an instance of ContentBaseTestCase

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param bios_config_file_path: Bios config file
        :param arguments: None
        """
        self.bios_config_file_path = bios_config_file_path
        self.phy = None
        super(ContentBaseTestCase, self).__init__(test_log, arguments,
                                                  cfg_opts)
        try:
            self.reset_def = False if arguments.reset_defaults == "False" else True
        except AttributeError:
            self.reset_def = True
        self.sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self.os = ProviderFactory.create(self.sut_os_cfg, test_log)  # type: SutOsProvider

        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self.ac_power = ProviderFactory.create(ac_cfg, test_log)  # type: AcPowerControlProvider
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._artifactory_obj = ContentArtifactoryUtils(test_log, self.os, self._common_content_lib, cfg_opts)
        self.reboot_timeout = \
            self._common_content_configuration.get_reboot_timeout()
        try:
            self.test_prepare_disable = self._common_content_configuration.get_test_prepare_disable_value()
        except Exception as e:
            self._log.debug(e)
            self._log.info("test_prepare_disable not set in cfg file - setting to False as default")
            self.test_prepare_disable = False

        if self._common_content_configuration.get_telemetry_collector():
            self._telemetry_dict = {"test_name": "DTAF", "test_owner": "DTAF_AUTOMATION"}
            self.telemetry_obj = self.initialize_telemetry_object()

        self.bring_sut_up = self._common_content_configuration.get_bring_sut_up_value()

        # if windows OS, disable command prompt quick edit mode
        self._common_content_lib.disable_quick_edit_mode()

        if not self.os.is_alive():
            self._log.error("System is not alive, wait for the sut online")
            self.perform_graceful_g3()  # To make the system alive

        if not self.os.is_alive():
            self._log.error("System is not alive")
            raise content_exceptions.TestFail("System is not alive")

        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        self.bios = ProviderFactory.create(bios_cfg, test_log)  # type: BiosProvider

        # initialize PHY provider for SXSTATE, USBSWITCH and CMOS clear
        self.sut = ConfigurationHelper.get_sut_config(cfg_opts)

        try:
            id_value = '{}'.format(PhysicalProviderConstants.PHY_SX_STATE)
            phy_cfg = ConfigurationHelper.filter_provider_config(sut=self.sut,
                                                                 provider_name=r"physical_control",
                                                                 attrib=dict(id=id_value))
            phy_cfg1 = phy_cfg[0]
            self.phy = ProviderFactory.create(phy_cfg1, test_log)  # type: PhysicalControlProvider
        except Exception as e:
            self._log.error("Looks like physical control provider (CMOS, SX_State) not "
                            "supported. Error: %s", str(e))

        # initialize PHY provider for POSTCODE
        try:
            id_value = '{}'.format(PhysicalProviderConstants.PHY_POST_CODE)
            phy_cfg = ConfigurationHelper.filter_provider_config(sut=self.sut,
                                                                provider_name=r"physical_control",
                                                                attrib=dict(id=id_value))
            phy_cfg2 = phy_cfg[0]
            self.pc_phy = ProviderFactory.create(phy_cfg2, test_log)  # type: PhysicalControlProvider
        except Exception as e:
            self.pc_phy = None
            self._log.error("Looks like physical control provider not (postcode)"
                            "supported. Error: %s", str(e))

        self.log_dir = self._common_content_lib.get_log_file_dir()

        self._command_timeout = \
            self._common_content_configuration.get_command_timeout()

        self._sut_shutdown_delay = self._common_content_configuration. \
            sut_shutdown_delay()

        self._pretest_bios_knobs_file_path = self._common_content_configuration.get_pretest_bios_knobs_file_path()

        self.bios_util = BiosUtil(cfg_opts,
                                  bios_config_file=self.bios_config_file_path,
                                  bios_obj=self.bios, common_content_lib=self._common_content_lib,
                                  log=self._log)

        self.bios_util_pretest = BiosUtil(cfg_opts,
                                          bios_config_file=self._pretest_bios_knobs_file_path,
                                          bios_obj=self.bios, common_content_lib=self._common_content_lib,
                                          log=self._log)

        self.cng_cfg = cfg_opts.find(ConsoleLogProvider.DEFAULT_CONFIG_PATH)
        self.cng_log = ProviderFactory.create(self.cng_cfg, self._log)

        self.serial_log_dir = os.path.join(self.log_dir, "serial_logs")
        if not os.path.exists(self.serial_log_dir):
            os.makedirs(self.serial_log_dir)
        self.serial_log_path = os.path.join(self.serial_log_dir,
                                            self._SERIAL_LOG_FILE)
        self.cng_log.redirect(self.serial_log_path)
        if arguments is not None:
            self._cc_log_path = arguments.outputpath
        self._platform_type = self._common_content_lib.get_platform_type()
        self._platform_environment = self._common_content_lib.get_platform_environment()
        self._grub_obj = GrubUtil(self._log, self._common_content_configuration, self._common_content_lib)
        self._common_content_lib.enable_network_manager_using_startup()

        # terminate processes if requested by config
        process_list = self._common_content_configuration.get_process_terminate_list()
        if process_list:
            self._log.info("Process termination requested by config")
            for process in process_list:
                try:
                    self._log.info("Terminating %s" % process)
                    instances_pids = self._common_content_lib.get_running_process_instances_on_host(process)
                    self._common_content_lib.terminate_process_instances_on_host(instances_pids)
                except RuntimeError:
                    pass

    def perform_graceful_g3(self):
        """Performs graceful shutdown"""
        self._log.info("Performs shutdown and boot the SUT")
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self._common_content_lib.wait_for_os(self.reboot_timeout)
        time.sleep(self.WAIT_TIME)

    def prepare(self):
        # type: () -> None
        """Test preparation/setup """
        if not self.test_prepare_disable:
            try:
                # Add the common tag to the log file
                # To-Do: Content name, host_name, SUT OS, platform, silicon, bios, timestamp
                try:
                    self._log.info("#" * 20)
                    self._common_content_lib.get_sut_info()
                    self._common_content_lib.get_host_info()
                    self._log.info("#" * 20)
                except Exception as e:
                    self._log.debug(e)
                self._common_content_lib.clear_all_os_error_logs()
            except RuntimeError as e:
                self._log.error("failed to clear the logs, error is %s", str(e))

            if self.os.os_type.lower() == OperatingSystems.LINUX.lower():
                self.os.execute("rm -rf /var/log/*", self._command_timeout)
                self.os.execute("touch /var/log/messages", self._command_timeout)
                if not self._common_content_configuration.is_container_env():
                    # To change the kernel to +server in CentOS
                    self._grub_obj.set_default_boot_cent_os_server_kernel()

            if self._common_content_configuration.get_telemetry_collector() and hasattr(self.telemetry_obj, "tc"):
                today_date = datetime.date.today()
                year, week_num, day_of_week = today_date.isocalendar()
                self.telemetry_obj.start_telemetry(name=self._telemetry_dict["test_name"],
                                                   owner=self._telemetry_dict["test_owner"],
                                                   tag="{}WW{}".format(year, week_num))

            cscripts_debugger_interface_type = self._common_content_lib.get_cscripts_debugger_interface_type()
            # bios knobs changes will be supported only for intel reference RVP platform
            if self._platform_type == PlatformType.REFERENCE:
                # reset_def=True load bios defaults, inband cscripts is not capable of writing-only reading bios knobs
                if self.reset_def and cscripts_debugger_interface_type != DebuggerInterfaceTypes.INBAND:
                    if self._pretest_bios_knobs_file_path:
                        self._log.info("Loading bios defaults and setting pretest bios settings from {}"
                                       .format(self._pretest_bios_knobs_file_path))
                        self.bios_util_pretest.load_bios_defaults()
                        self.bios_util_pretest.set_bios_knob()
                    else:
                        self.bios_util.load_bios_defaults()

                if cscripts_debugger_interface_type != DebuggerInterfaceTypes.INBAND:
                    if self.bios_config_file_path:
                        self._log.info("Setting required bios settings")
                        self.bios_util.set_bios_knob()
                    if self._platform_environment == PlatformEnvironment.SIMICS:
                        self._common_content_lib.perform_os_reboot(self.reboot_timeout)
                    else:
                        self.perform_graceful_g3()

                if self.bios_config_file_path:
                    self._log.info("Verifying bios settings")
                    self.bios_util.verify_bios_knob()
            else:
                self._log.info("Platform type={}, settings bios KNOBS not supported.".format(self._platform_type))
        else:
            self._log.info("Skipping Test Prepare as designated in configuration file(test_prepare_disable) ")

    @classmethod
    def add_arguments(cls, parser):
        super(ContentBaseTestCase, cls).add_arguments(parser)
        # Use add_argument
        parser.add_argument('-o', '--outputpath', action="store", default="",
                            help="Log folder to copy log files to command center")

    def cleanup(self, return_status):
        """Test Cleanup"""
        try:
            content_verdict = {True: "PASS", False: "FAIL"}
            self._log.info("Parser_Tag: RESULT = {}".format(content_verdict[return_status]))
            parser_data_dict = self._common_content_lib.parse_dtaf_content_log()
            self._common_content_lib.write_parser_data_to_db(parser_data_dict)
        except Exception as e:
            self._log.debug(e)
        if self._common_content_configuration.get_telemetry_collector() and hasattr(self.telemetry_obj, "tc"):
            self.telemetry_obj.stop_telemetry()
        if not self.os.is_alive() and self.bring_sut_up and self.reset_def:
            self._log.info("SUT is down, applying power cycle to make the "
                           "SUT up")
            self._log.info("AC Off")
            self.ac_power.ac_power_off(self.AC_TIMEOUT)
            if self.phy:
                self._log.info("clearing cmos")
                try:
                    self.phy.set_clear_cmos(self.AC_TIMEOUT)
                except Exception as ex:
                    pass
            self._log.info("AC On")
            self.ac_power.ac_power_on(self.AC_TIMEOUT)
            self._log.info("Waiting for OS")
            if self._common_content_lib.is_bootscript_required():
                self._common_content_lib.execute_boot_script()
            try:
                self.os.wait_for_os(self.reboot_timeout)
            except Exception as ex:
                self._log.error("Cleanup: Failed to boot to OS with exception: '{}'.".format(ex))

        if self.os.is_alive():
            self._common_content_lib.store_os_logs(self.log_dir)
        # copy logs to CC folder
        self._log.info("Command center log folder='{}'".format(self._cc_log_path))
        self._common_content_lib.copy_log_files_to_cc(self._cc_log_path)
        super(ContentBaseTestCase, self).cleanup(return_status)

    def set_and_verify_bios_knobs(self, bios_file_path):
        """
        This method is to set the BIOS knob then reboot the SUT and verify it with the given bios config file

        :bios_file_path : Configuration file with the BIOS knob details
        :return : None
        """
        if self.reset_def:
            self.bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
            self.bios_util.set_bios_knob(bios_file_path)  # To set the bios knob setting.
            self.perform_graceful_g3()
            self.bios_util.verify_bios_knob(bios_file_path)  # To verify the bios knob settings.

    def initialize_sv_objects(self):
        """initialize sv, if not already initialized"""
        if self.SV is None:
            cpu = self._common_content_lib.get_platform_family()
            pch = self._common_content_lib.get_pch_family()
            sv_cfg = ElementTree.fromstring(ProviderXmlConfigs.PYTHON_SV_XML_CONFIG.format(cpu, pch))
            self.SV = ProviderFactory.create(sv_cfg, self._log)  # type: SiliconRegProvider

    def initialize_sdp_objects(self):
        """ initialize sdp, if not already initialized"""
        if self.SDP is None:
            si_cfg = ElementTree.fromstring(ProviderXmlConfigs.SDP_XML_CONFIG)
            self.SDP = ProviderFactory.create(si_cfg, self._log)  # type: SiliconDebugProvider

    def initialize_telemetry_object(self):
        """initialize the telemetry object"""
        cpu = self._common_content_lib.get_platform_family()
        telemetry_obj = Telemetry(cpu, self._log)
        return telemetry_obj

    def read_register_via_cscripts(self, socket, register):
        """
        Method to read value of the register.

        :param: register: register name
        :param: socket: socket number
        :return: value
        """
        value = self._cscripts.get_by_path(self._cscripts.UNCORE, register, socket_index=socket)
        return value

    def write_value_to_register_via_cscripts(self, socket, register, value):
        """
        Method to write value of the register.

        :param: socket: socket number
        :param: register: register name
        :param: value: register value
        :return: null
        """
        self._cscripts.get_by_path(self._cscripts.UNCORE, register, socket_index=socket).write(value)

    def write_value_list_to_register_list_via_cscripts(self, socket=0, registers=[], values=[]):
        """
        Method to adjust/assign values to the registers. Also print the initial and current values

        :param: registers: register list
        :param: values: register value list
        :param: socket: socket number
        :return: null
        """
        if not len(registers) == len(values):
            self._log.info("Mismatch in number of registers and number of values")
            raise ex

        self._log.info("Initial values of registers -")
        for register in registers:
            value = self.read_register_via_cscripts(socket, register)
            self._log.info("Value for {} - {}".format(register, value))

        self._log.info("Writing values to these registers")
        for i in range(len(registers)):
            self.write_value_to_register_via_cscripts(socket, registers[i], values[i])

        self._log.info("Verifying and printing the Updated values of registers -")
        for i in range(len(registers)):
            value = self.read_register_via_cscripts(socket, registers[i])
            if value == values[i]:
                self._log.info("New Value updated for {} - {}".format(registers[i], value))
            else:
                self._log.info("Value wrongly updated for {} as {}".format(registers[i], values[i]))
                raise ex