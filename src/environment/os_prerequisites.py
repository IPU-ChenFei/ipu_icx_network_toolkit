# !/usr/bin/env python
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
from pathlib import Path

from dtaf_core.lib.dtaf_constants import OperatingSystems, Framework
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.physical_control import PhysicalControlProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.uefi_shell import UefiShellProvider

try:
    from src.lib.bios_util import ItpXmlCli, BootOptions
    from src.lib.content_configuration import ContentConfiguration
except:
    pass

import re
import os
import platform
import subprocess
import time
import six

if six.PY2:
    import ConfigParser as config_parser
if six.PY3:
    import configparser as config_parser

from xml.etree import ElementTree
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

class OsPreRequisitesLib:
    C_DRIVE_PATH = "C:\\"
    SUT_INVENTORY_FILE_NAME = r"C:\Inventory\sut_inventory.cfg"

    def __init__(self, log, cfg_opts):
        """
        Create a new OsInstallationProvider object.

        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment
        :param log: Logger object to use for output messages
        """
        self._log = log
        self._cfg_opts = cfg_opts
        self._csp_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._folder_exists()

        try:
            phy_cfg = cfg_opts.find(
                PhysicalControlProvider.DEFAULT_CONFIG_PATH)
            self._phy = ProviderFactory.create(phy_cfg, self._log)  # type: PhysicalControlProvider
        except Exception as e:
            self._log.error("Looks like physical control provider not "
                            "supported. Error: %s", str(e))

        # Object creations of supporting classes
        try:
            self._common_content_configuration = ContentConfiguration(self._log)
        except:
            pass

        ac_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac = ProviderFactory.create(ac_cfg, self._log)  # type: AcPowerControlProvider

        uefi_cfg = cfg_opts.find(UefiShellProvider.DEFAULT_CONFIG_PATH)
        self._log.info("uefi_cfg created...")
        self._uefi = ProviderFactory.create(uefi_cfg, self._log)  # type: UefiShellProvider
        self._log.info("UEFI object created...")

        self._config_parser = config_parser.ConfigParser()

        self._platform_config_file_host_path = None

        if os.path.exists(self.SUT_INVENTORY_FILE_NAME):  # File already present
            self._config_parser.read(self.SUT_INVENTORY_FILE_NAME)
            list_sections = self._config_parser.sections()
            list_options = []
            cfg_values_list = []

            if len(list_sections) != 0:
                list_options = [options for options in self._config_parser[list_sections[0]]]
                itp_needed_auto = False
                for option in self._config_parser[list_sections[0]]:
                    cfg_values_list.append(self._config_parser.get(list_sections[0], option))
                    if self._config_parser.get(list_sections[0], option) == 'auto':
                        itp_needed_auto = True

                if itp_needed_auto:
                    self._platform_config_file_host_path = self._itp_initialization()
                    self.update_sut_inventory()

            if len(list_sections) == 0 or len(list_options) < 4 or len(set(cfg_values_list)) < 4 or \
                    len(list_options) != len(set(cfg_values_list)):
                self._log.info("There are no known sections in the configuration file, proceeding with auto "
                               "mode... ITP is initializing..")
                self._platform_config_file_host_path = self._itp_initialization()
                self.update_sut_inventory()
        else:
            self._sut_inventory_cfg_info = self._verify_sut_cfg_inventory_exists()
            self._platform_config_file_host_path = self._itp_initialization()
            self.update_sut_inventory()

    def get_sut_static_ip(self):
        exec_os = platform.system()
        try:
            cfg_file_default = Framework.CFG_BASE
        except KeyError:
            err_log = "Error - execution OS " + str(exec_os) + " not supported!"
            self._log.error(err_log)
            raise err_log

        # Get the Automation folder config file path based on OS.
        system_cfg_file_automation_path = cfg_file_default[exec_os] + "system_configuration.xml"
        tree = ElementTree.ElementTree()

        if os.path.exists(system_cfg_file_automation_path):
            tree.parse(system_cfg_file_automation_path)
        else:
            self._log.error("Unable to find system Configuration xml file under --> "
                            "{}".format(cfg_file_default[exec_os]))
            raise RuntimeError

        root = tree.getroot()
        return root.find(r".//ssh/ipv4").text.strip()

    def _folder_exists(self):
        dir_os_package = r"C:\os_package"
        if not os.path.exists(dir_os_package):
            os.makedirs(dir_os_package)
            self._log.info("os_package folder does not exists in C: drive, creating one now..")
        else:
            self._log.info("os_package folder exists in C: drive, proceeding further..")

    def _itp_initialization(self):
        """
        Function to initialize Itp object and get the platformconfig.xml file

        :return: path of xml file
        """
        platform_config_file_path = None
        self._csp = ProviderFactory.create(self._csp_cfg, self._log)  # type: SiliconRegProvider
        self.itp_xml_cli_util = ItpXmlCli(self._log, self._cfg_opts)
        try:
            self.itp_xml_cli_util.set_default_boot(BootOptions.UEFI)
        except Exception as ex:
            self._log.error("ITP has failed to initialize... Please check the platform for proper ITP connection, "
                            "Pythonsv and cscripts are configured..")

        self._log.info("Powering off and powering on SUT...")
        if self._ac.get_ac_power_state():
            no_attempts = 0
            while no_attempts < 3:
                self._log.info("Powering off SUT attempt no. '{}'".format(no_attempts))
                ret_val = self._ac.ac_power_off(10)
                self._log.info("SUT Power off status='{}'".format(ret_val))
                if ret_val or not self._ac.get_ac_power_state():
                    break
                no_attempts = no_attempts + 1

            time.sleep(10)
            ret_val = self._ac.ac_power_on(10)
            self._log.info("SUT Power on status='{}'".format(ret_val))
            time.sleep(20)

            if not ret_val:
                raise RuntimeError("SUT is not powered up..")

            try:
                self._uefi.wait_for_uefi(600)
            except:
                self._log.debug("SUT is in UEFI Shell..")
        else:
            self._log.info("Sut has AC power, proceeding further..")
        try:
            platform_config_file_path = self.itp_xml_cli_util.get_platform_config_file_path()
        except Exception as ex:
            self._log.error("ITP has failed to initialize... Please check the platform for proper ITP connection, "
                            "Pythonsv and cscripts are configured..")

        return platform_config_file_path

    def execute_cmd_on_host(self, cmd_line, cwd=None):
        """
        This function executes command line on HOST and returns the stdout.

        :param cmd_line: command line to execute

        :raises RunTimeError: if command line failed to execute or returns error
        :return: returns stdout of the command
        """
        if cwd:
            process_obj = subprocess.Popen(cmd_line, cwd=cwd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                           shell=True)
        else:
            process_obj = subprocess.Popen(cmd_line, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                           shell=True)
        stdout, stderr = process_obj.communicate()

        if process_obj.returncode != 0:
            log_error = "The command '{}' failed with error '{}' ...".format(cmd_line, stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        self._log.info("The command '{}' executed successfully..".format(cmd_line))
        return stdout

    def get_first_usb_size(self):
        """
        To get the usb size which is coming in first position on host.

        :return: USB size in GB
        """
        usb_size_gb = None
        usb_size = None

        if not self._phy.connect_usb_to_host(20):
            self._log.error("USB Switching To Host Failed")
            return False

        if platform.system() == OperatingSystems.WINDOWS:
            cmd_line = 'powershell "get-disk | where bustype -eq "USB" | Format-List | FINDSTR "^Size""'
            usb_size = self.execute_cmd_on_host(cmd_line)

            self._log.debug(usb_size)

            usb_size_gb = float(str(usb_size).split(":")[1].strip().split()[0])

        elif platform.system() == OperatingSystems.LINUX:
            cmd_line_get_size_list = 'lshw -class disk | grep -Ei "(size:)"'
            cmd_line_get_capabilities_list = 'lshw -class disk | grep -Ei "(capabilities)"'

            usb_cmd_size_list = list(self.execute_cmd_on_host(cmd_line_get_size_list))
            usb_cmd_capabilities_list = list(self.execute_cmd_on_host(cmd_line_get_capabilities_list))

            self._log.debug(usb_cmd_size_list)
            self._log.debug(usb_cmd_capabilities_list)

            for index, cap in enumerate(usb_cmd_capabilities_list):
                if "removable" in cap:
                    usb_size = usb_cmd_size_list[index]

            usb_size_with_gib = str(usb_size).split()[1].strip()
            usb_size_in_num = re.findall(r'\d+', usb_size_with_gib)
            usb_size_gb = map(float, usb_size_in_num)

        self._log.info("USB Device size: '{}'".format(usb_size_gb))

        if not self._phy.connect_usb_to_sut(5):
            self._log.error("USB Switching To Target Failed")
            return False

        rounded_usb_size = round(usb_size_gb)

        if rounded_usb_size in (7, 7.8, 7.5, 6, 6.5, 6.8):
            usb_size_gb = 8
        elif rounded_usb_size in (14, 14.5, 13, 12.5, 13.5):
            usb_size_gb = 16
        elif rounded_usb_size in (27, 27.5, 28, 28.5, 28.8, 28.7, 28.9, 29, 29.5):
            usb_size_gb = 32
        elif rounded_usb_size in (57, 57.5, 56, 56.5, 56.8, 57.8, 58, 58.5, 59.5):
            usb_size_gb = 64
        else:
            self._log.error(
                "Please Ensure that pendrive size is Correct and Connected To Host-Machine Supported "
                "size of USb 8,16,32,64gb..")
            raise RuntimeError

        return usb_size_gb

    def _verify_sut_cfg_inventory_exists(self):
        """
        Function to verify whether SUT inventory config is available in the C: drive

        :return: sut_inventory_cfg_path
        """
        dir_name = r"C:\Inventory"
        file_name = "sut_inventory.cfg"
        file_found = True
        sut_inventory_cfg_path = os.path.join(dir_name, file_name)

        if not os.path.exists(dir_name):
            self._log.info("SUT inventory folder does not exists, creating one now..")
            os.makedirs(os.path.join(dir_name))
        else:
            self._log.info("SUT inventory folder found, proceeding further..")

        if not os.path.exists(sut_inventory_cfg_path):
            self._log.info("SUT inventory configuration file does not exists, creating one now..")
            cfg_file_created = open(sut_inventory_cfg_path, "w")
            # Adding the section
            self._config_parser.add_section("sut_information")

            # Adding the section values
            self._config_parser.set("sut_information", "mode", "")
            self._config_parser.set("sut_information", "usb_name_1", "")
            self._config_parser.set("sut_information", "usb_size", "")
            self._config_parser.set("sut_information", "ssd_name_1", "")
            cfg_file_created.close()

            file_found = False
        else:
            self._log.info("SUT inventory configuration found, proceeding further..")

        return file_found, sut_inventory_cfg_path

    def get_all_uefi_names(self):
        uefi_line = []
        ssd_names = []
        with open(self._platform_config_file_host_path, "r") as fh_xml:
            for xml_line in fh_xml.readlines():
                if 'text="UEFI ' in xml_line:
                    only_name = xml_line.split('"')[1]
                    uefi_line.append(only_name.strip())

        uefi_lines = set(uefi_line)

        self._log.info("List of UEFI names in platform config file {}".format(uefi_lines))

        return uefi_lines

    def get_usb_names(self):

        usb_names = []
        uefi_line = []
        uefi_lines = self.get_all_uefi_names()

        for name in uefi_lines:
            if any(word.lower() in name.lower() for word in ["HP","SAMSUNG", "PNY", "TRANSCEND", "SANDISK", "KANGURU"]):
                if 'SSD' not in name:
                    usb_names.append(name)

        if len(usb_names) == 0:
            for name in uefi_line:
                if re.search(r"UEFI\s[A-Za-z].*\s*USB.*", name) and 'SSD' not in name:
                    usb_names.append(name)

        if len(usb_names) == 0:
            self._log.error("No USB names are found")
            raise RuntimeError
        # else:
        #     uefi_lines = list(set(uefi_lines) ^ set(usb_names))

        self._log.info("List of USB Names: {}".format(usb_names))

        return usb_names

    def get_ssd_names(self, usb_names):

        ssd_names = []
        uefi_lines = self.get_all_uefi_names()

        uefi_lines = list(set(uefi_lines) ^ set(usb_names))

        for name in uefi_lines:
            if any(word.lower() in name.lower() for word in ["UEFI INTEL", "UEFI KINGSTON", "UEFI SANDISK", "UEFI WDC",
                                                             "UEFI ADATA", "UEFI SAMSUNG", "UEFI SILICON POWER",
                                                             "UEFI CORSAIR FORCE", "UEFI WD BLACK", "UEFI CT",
                                                             "UEFI CRUCIAL", "UEFI ST500DM009"]):
                ssd_names.append(name)

        if len(ssd_names) == 0:
            self._log.error("No SSD names are found")
            raise RuntimeError

        self._log.info("List of SSD Names: {}".format(ssd_names))

        return ssd_names

    def get_ssd_names_config(self, os_name):
        """
        Function to get number of ssds connected to the SUT via sut_inventory config else from ITP.
        :param os_name: mentioned ssd name will be picked.
        :return number ssds
        """
        count = 0
        if os.path.exists(self.SUT_INVENTORY_FILE_NAME):  # File already present
            self._config_parser.read(self.SUT_INVENTORY_FILE_NAME)
            list_sections = self._config_parser.sections()
            list_options = [options for options in self._config_parser[list_sections[0]]]

            for ssds in list_options:
                if "ssd_name_{}".format(os_name) in ssds or "ssd_name_blank" in ssds:
                    count = count + 1

            if count == 0:
                for ssds in list_options:
                    if "ssd_name" in ssds or "ssd_name_blank" in ssds:
                        count = count + 1

        if count == 0:
            self._itp_initialization()
            ssd_names = []
            uefi_lines = self.get_all_uefi_names()

            for name in uefi_lines:
                if any(word.lower() in name.lower() for word in ["UEFI INTEL", "UEFI KINGSTON", "UEFI SANDISK",
                                                                 "UEFI WDC", "UEFI ADATA", "UEFI SAMSUNG",
                                                                 "UEFI SILICON POWER", "UEFI CORSAIR FORCE",
                                                                 "UEFI WD BLACK", "UEFI CT", "UEFI CRUCIAL",
                                                                 "UEFI ST500DM009"]):
                    ssd_names.append(name)

            count = len(ssd_names)

        return count

    def update_sut_inventory(self):
        """
        Function to update the inventory file with hard disk / usb name and usb size from platform config xml file.
        """
        ret_value = False
        if self._platform_config_file_host_path:
            if os.path.exists(self._platform_config_file_host_path):  # ITP working - Assume Auto mode
                if os.path.exists(self.SUT_INVENTORY_FILE_NAME):  # File already present
                    self._config_parser.read(self.SUT_INVENTORY_FILE_NAME)
                    usb_size = self.get_first_usb_size()

                    usb_names = self.get_usb_names()
                    ssd_names = self.get_ssd_names(usb_names)

                    self._config_parser.read(self.SUT_INVENTORY_FILE_NAME)

                    with open(self.SUT_INVENTORY_FILE_NAME, "w") as cfg_file:
                        cfg_file.seek(0)
                        cfg_file.truncate()
                    if len(self._config_parser.sections()) == 0:
                        self._config_parser.add_section("sut_information")

                    self._config_parser.set("sut_information", "mode", "auto")

                    for index_usb, name in enumerate(usb_names):
                        index_usb = index_usb + 1
                        self._config_parser.set("sut_information", "usb_name_{}".format(index_usb), str(name))

                    self._config_parser.set("sut_information", "usb_size", str(usb_size))

                    for index_ssd, name in enumerate(ssd_names):
                        index_ssd = index_ssd + 1
                        self._config_parser.set("sut_information", "ssd_name_{}".format(index_ssd), str(name))

                    with open(self.SUT_INVENTORY_FILE_NAME, "w") as cfg_file:
                        self._config_parser.write(cfg_file)
                    ret_value = True
            else:
                self._log.error("We are sorry that ITP seems malfunctioning, so the sut inventory config has not been "
                                "updated, please traverse to the path --> '{}' on your host and update the mode "
                                "of execution as manual".format(self._sut_inventory_cfg_info[1]))

        return ret_value

    def get_sut_inventory_data(self, os_name, inventory_filename=None):
        """
        Function to read the final usb, ssd names and sizes.

        :os_name: os name which need to be installed.
        :inventory_filename: path of the sut_inventory.cfg file
        :return: list of param values
        """
        list_values = []
        os_name_option_found = False
        ssd_name_found = False

        if os_name.lower() not in ["windows", "rhel", "esxi", "centos"]:
            self._log.error("Operating system name is not passed correctly.. please try again,...")
            raise RuntimeError

        if not inventory_filename:
            inventory_filename = self.SUT_INVENTORY_FILE_NAME

        if os.path.exists(inventory_filename):  # File already present
            self._config_parser.read(inventory_filename)
            list_sections = self._config_parser.sections()
            list_options = [options for options in self._config_parser[list_sections[0]]]

            if len(list_options) < 4:
                self._log.error("Unable to get all the parameter values for OS installation... Please make sure "
                                "the below options are available.. \n1. mode = auto / manual \n "
                                "2. usb_name_1 = UEFI hp x303w BC2B109BB177819C19 \n "
                                "3. usb_size = 32 \n 4. ssd_name_1 = UEFI KINGSTON SA400S37240G 50026B778345C1CD")
                raise RuntimeError
            self._log.debug("Searching for '{}' ssd name option in the sut inventory config file..".format(os_name))
            for option in self._config_parser[list_sections[0]]:
                if option != 'mode':
                    if os_name in option:
                        if not os_name_option_found:
                            value = self._config_parser.get(list_sections[0], option)
                            if not value:
                                self._log.error("Value is empty for the option - {}".format(option))
                                raise RuntimeError
                            os_name_option_found = True
                            list_values.append(value)
                        else:
                            self._log.info("OS SSD already picked..")
                    elif "usb" in option:
                        value = self._config_parser.get(list_sections[0], option)
                        if not value:
                            self._log.error("Value is empty for the option - {}".format(option))
                            raise RuntimeError
                        list_values.append(value)
                    else:
                        self._log.debug('Skipped the value of option --> "{}" which is not required..'.format(option))

            if not os_name_option_found:
                self._log.info("Search failed for '{}' ssd option in the sut_inventory.cfg file, so assuming this is "
                               "auto mode config generation, so proceeding with further search to find ssd name in "
                               "the file...".format(os_name))
                # considering maximum 4 SSDs connected on ths platform
                for no in range(1, 5):
                    os_name = "ssd_name_" + str(no)
                    if os_name in self._config_parser[list_sections[0]]:
                        ssd_name_found = True
                        value = self._config_parser.get(list_sections[0], os_name)
                        if value:
                            list_values.append(value)
                        else:
                            self._log.error("Value is empty for the option - {}".format(os_name))
                            raise RuntimeError
                        break
                    else:
                        self._log.debug("Failed to find the option 'ssd_name_{}', trying again..".format(no))

                if not ssd_name_found:
                    self._log.error("Failed to find any ssd name options, please update the config file correctly "
                                    "and try again..")
                    raise RuntimeError
        else:
            self._log.error("File does not exists..")
            raise RuntimeError
        self._log.debug("List of parameters that are need for Os installation are '{}'".format(list_values))

        return list_values
