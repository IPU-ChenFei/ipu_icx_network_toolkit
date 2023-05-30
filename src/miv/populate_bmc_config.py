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
import os
import socket
import shutil
import platform
from configobj import ConfigObj
import six
if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.uefi_shell import UefiShellProvider
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.physical_control import PhysicalControlProvider
from dtaf_core.providers.bios_menu import BiosBootMenuProvider
from dtaf_core.providers.console_log import ConsoleLogProvider

from src.lib.uefi_cmdtool_lib import UefiCmdtoolLib
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib.uefi_util import UefiUtil
from src.provider.copy_usb_provider import UsbRemovableDriveProvider
from src.collaterals.collateral_constants import CollateralConstants
from src.lib.install_collateral import InstallCollateral
from src.lib.bios_util import ItpXmlCli
from src.lib.bios_util import BootOptions
from src.lib.bios_util import ChooseBoot
import src.lib.content_exceptions as content_exceptions
from src.provider.host_usb_drive_provider import HostUsbDriveProvider

import montana as montana


class PopulateBmcConfig(BaseTestCase):
    """
        1. Interacts with BMC Serial
    """
    # Relative path for miv configuration folder
    MIV_CONFIG_RELATIVE_PATH = "configuration"
    BMC_OPEN = "open"   # OpenBMC with NM bridging to PCH
    BMC_OPENNM_IPMI = "OpenNM_IPMI"  # Ignition FW stack using IPMI with no NM bridging
    BMC_OPENNM_REDFISH = "OpenNM_Redfish"  # Ignition FW stack using Redfish to the BMC
    _SERIAL_LOG_FILE = "serial_log.log"

    use_itp_xmlcli = False

    def __init__(self, test_log, arguments, cfg_opts):
        """
        This class populates the Montana BMC Configuration file.

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        super(PopulateBmcConfig, self).__init__(test_log, arguments, cfg_opts)

        self._cfg = cfg_opts

        uefi_cfg = cfg_opts.find(UefiShellProvider.DEFAULT_CONFIG_PATH)
        self._uefi = ProviderFactory.create(uefi_cfg, test_log)  # type: UefiShellProvider
        self._log.info("UEFI Shell provider object created..")

        os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(os_cfg, test_log)  # type: SutOsProvider

        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac = ProviderFactory.create(ac_cfg, test_log)  # type: AcPowerControlProvider

        bios_boot_menu_cfg = cfg_opts.find(BiosBootMenuProvider.DEFAULT_CONFIG_PATH)
        self._bios_boot_menu = ProviderFactory.create(bios_boot_menu_cfg, test_log)

        self._common_content_lib = CommonContentLib(test_log, self._os, cfg_opts)
        self._miv_config_abs_path = os.path.join(self.get_montana_path, self.MIV_CONFIG_RELATIVE_PATH)
        self._content_config = ContentConfiguration(test_log)
        self._reboot_timeout = self._content_config.get_reboot_timeout()
        self._install_collateral = InstallCollateral(test_log, self._os, cfg_opts)

        self._uefi_util = UefiUtil(test_log, self._uefi, self._bios_boot_menu, self._ac, self._content_config, self._os)
        self._choose_boot = ChooseBoot(self._bios_boot_menu, self._content_config, test_log, self._ac, self._os, cfg_opts)

        console_cfg = cfg_opts.find(ConsoleLogProvider.DEFAULT_CONFIG_PATH)
        self._console_log = ProviderFactory.create(console_cfg, test_log)

        try:
            phy_cfg = cfg_opts.find(PhysicalControlProvider.DEFAULT_CONFIG_PATH)
            self._phy = ProviderFactory.create(phy_cfg, test_log)  # type: PhysicalControlProvider
        except Exception as ex:
            self._log.error("Physical controller configuration not populated in System_Configuration.xml...")
            raise content_exceptions.TestSetupError(ex)

        self._itp_xmlcli = None
        if self.use_itp_xmlcli:
            self._itp_xmlcli = ItpXmlCli(test_log, cfg_opts)  # type: ItpXmlCli
        self._default_boot_order_string = None

        self._usb_copy_provider = UsbRemovableDriveProvider.factory(test_log, cfg_opts, self._os)
        self._host_usb_provider = HostUsbDriveProvider.factory(test_log, cfg_opts, self._os)  # type: HostUsbDriveProvider

        self.log_dir = self._common_content_lib.get_log_file_dir()

        self._cc_log_path = arguments.outputpath
        self._config_files_path = arguments.configfilespath  # config files path with comma separated

        self.serial_log_dir = os.path.join(self.log_dir, "serial_logs")
        if not os.path.exists(self.serial_log_dir):
            os.makedirs(self.serial_log_dir)
        self._console_log.redirect(os.path.join(self.serial_log_dir,self._SERIAL_LOG_FILE))

        if not self._os.is_alive():
            self._log.error("System is not alive, wait for the sut online")
            self._common_content_lib.perform_graceful_ac_off_on(self._ac)
            try:
                self._os.wait_for_os(self._reboot_timeout)
            except Exception as ex:
                self._log.error("System is not alive, exception='{}'".format(ex))
                raise content_exceptions.TestFail("System is not alive")

    @classmethod
    def add_arguments(cls, parser):
        super(PopulateBmcConfig, cls).add_arguments(parser)
        # Use add_argument

        # output log file path to copy logs for command center consumption
        parser.add_argument('-o', '--outputpath', action="store", default="",
                            help="Log folder to copy log files to command center")

        # configuration files
        parser.add_argument('-c', '--configfilespath', action="store", default="",
                            help="Config files")

    @property
    def get_montana_path(self):
        try:
            montana_path = Path(montana.__file__).parent
            self._log.info("Montana Framework Path='{}'".format(montana_path))
            return montana_path
        except Exception as ex:
            log_error = "Unable to get path to Montana framework due to exception = '{}'.Check if you have populated" \
                        " the 'PYTHONPATH' with correct path to Montana framework"
            self._log.error(log_error)
            raise ex

    def boot_to_uefi_using_itp_xmlcli(self):
        # store the initial default boot order string
        self._default_boot_order_string = self._itp_xmlcli.get_current_boot_order_string()

        # make UEFI as default boot
        self._itp_xmlcli.set_default_boot(BootOptions.UEFI)
        # perform G3 to boot to UEFI shell
        self._common_content_lib.perform_graceful_ac_off_on(self._ac)
        self._log.info("Waiting for boot into UEFI shell...")
        self._uefi.wait_for_uefi(self._reboot_timeout)
        self._log.info("SUT booted to UEFI...")

    def boot_to_os_using_itp_xmlcli(self):
        # Set the boot order back to original
        self._itp_xmlcli.set_boot_order(self._default_boot_order_string)
        self._log.info("Performing graceful G3 to boot to OS...")
        # perform G3 to go back to OS
        self._common_content_lib.perform_graceful_ac_off_on(self._ac)
        self._os.wait_for_os(self._reboot_timeout)
        self._log.info("SUT booted to OS...")

    def boot_to_uefi_using_serial(self):
        self._choose_boot.boot_choice(BootOptions.UEFI)
        self._log.info("Waiting to boot to UEFI...")
        self._uefi.wait_for_uefi(self._content_config.get_reboot_timeout())
        self._log.info("SUT booted to UEFI...")

    def boot_to_os_using_serial(self):
        self._log.info("Performing graceful G3 to boot to OS...")
        self._common_content_lib.perform_graceful_ac_off_on(self._ac)
        self._os.wait_for_os(self._content_config.get_reboot_timeout())
        self._log.info("SUT booted to OS...")

    def boot_to_efi(self):
        if self.use_itp_xmlcli:
            self.boot_to_uefi_using_itp_xmlcli()
        else:
            self.boot_to_uefi_using_serial()

    def boot_to_os(self):
        if self.use_itp_xmlcli:
            self.boot_to_os_using_itp_xmlcli()
        else:
            self.boot_to_os_using_serial()

    def execute(self):
        """
        This TestCase performs below.
        1. Get the BMC IP address and SUT IP
        2. Create debuguser and enable admin access to channel 1 and 3
        3. Updates the MIV Config file with above details

        :return: True if passed else False
        :raise: None
        """
        ret_val = False
        try:
            # check if we have hot-pluggable USB drive (connected to either Banino, RSC2 or PI)
            usb_drive = self._host_usb_provider.get_hotplugged_usb_drive(self._phy)
            if usb_drive is None:
                self._log.error("Usb pen drive not connected to physical controller (Banino/RSC2/PI/SoundWave)..")
                raise content_exceptions.TestSetupError

            # copy cmdtool collateral to USB
            cmdtool = CollateralConstants.COLLATERAL_CMDTOOL
            self._log.info("Copying cmdtool to USB drive..")
            usb_path = self._host_usb_provider.copy_collateral_to_usb_drive(cmdtool, usb_drive)
            self._log.info("The cmdtool is copied to USB folder '{}'".format(usb_path))

            sut_ip_address = self._common_content_lib.get_sut_ip()
            self._log.info("SUT IP Address='{}'".format(sut_ip_address))

            self.boot_to_efi()

            # switch the USB to SUT
            self._phy.connect_usb_to_sut(10)

            list_usb_devices = self._uefi_util.get_usb_uefi_drive_list()
            if len(list_usb_devices) == 0:
                self.boot_to_os()
                raise content_exceptions.TestFail("USB thumb drive not found in UEFI ...")

            usb_map = list_usb_devices[0]
            uefi_cmdtool = UefiCmdtoolLib(self._uefi, self._log, usb_map, cmdtool)
            bmc_ip_address = uefi_cmdtool.get_bmc_ip()
            self._log.info("Successfully retrieved the BMC IP Address = '{}'".format(bmc_ip_address))

            # create debuguser and enable admin access
            uefi_cmdtool.create_and_enable_debuguser()

            self.boot_to_os()

            # ping both BMC and SUT IP
            self.ping_ip(bmc_ip_address)
            self.ping_ip(sut_ip_address)

            self.create_miv_config_file(bmc_ip_address, sut_ip_address)
            ret_val = True
        except Exception as ex:
            log_error = "Failed to populate BMC Configuration due to exception='{}'".format(ex)
            self._log.error(log_error)

        return ret_val

    def cleanup(self, return_status):
        """Test Cleanup"""
        is_os_alive = True
        if not self._os.is_alive():
            self._log.info("SUT is down, applying power cycle to make the "
                           "SUT up")
            try:
                self.boot_to_os()
            except Exception as ex:
                is_os_alive = False
                self._log.error("SUT did not boot into OS, even after G3 with exception='{}'..".format(ex))

        self._common_content_lib.store_os_logs(self.log_dir)
        # copy logs to CC folder if provided
        if self._cc_log_path:
            self._log.info("Command center log folder='{}'".format(self._cc_log_path))
            self._common_content_lib.copy_log_files_to_cc(self._cc_log_path)

        super(PopulateBmcConfig, self).cleanup(return_status)

    def ping_ip(self, ip_addr):
        if OperatingSystems.WINDOWS in platform.system():
            ping_cmd = "ping -n 4 {}".format(ip_addr)
        elif OperatingSystems.LINUX in platform.system():
            ping_cmd = "ping -c 4 {}".format(ip_addr)

        response = os.system(ping_cmd)
        if 0 == response:
            self._log.info("Ping successful with IP address '{}...".format(ip_addr))
        else:
            self._log.info("Ping failed with IP address '{}...".format(ip_addr))

    def create_miv_config_file(self, bmc_ip, sut_ip):
        template_config_file_path = os.path.join(self._common_content_lib.get_project_src_path(),
                                                 r"src\configuration\miv_config.cfg")

        host_name = socket.gethostname()
        config_file_name = host_name + ".cfg"
        miv_config_file_path = os.path.join(self._miv_config_abs_path, config_file_name)

        # copy config file to miv config folder
        shutil.copyfile(template_config_file_path, miv_config_file_path)
        cpu_family = self._common_content_lib.get_platform_family()

        cp = ConfigObj(miv_config_file_path)
        cp["Section0"]["bmcver"] = self.BMC_OPEN
        cp["Section0"]["ipaddress"] = bmc_ip
        cp["Section0"]["osip"] = sut_ip
        cp["Section0"]["cpuname"] = str(cpu_family).lower()
        cp.write()
        self._log.info("The MIV Configuration file '{}' populated successfully..".format(miv_config_file_path))
        # copy config file Automation folder as well
        exec_os = platform.system()
        def_miv_cfg_file_path = os.path.join(Framework.CFG_BASE[exec_os], config_file_name)
        shutil.copyfile(miv_config_file_path, def_miv_cfg_file_path)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PopulateBmcConfig.main() else Framework.TEST_RESULT_FAIL)

