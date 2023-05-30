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
# otherwise. Any license under such intellectual property rights must be
# express and approved by Intel in writing.
###############################################################################
import platform
import re
import subprocess
import sys
from zipfile import ZipFile
import six
import os
import time
from ast import literal_eval
import xml.etree.ElementTree as ET
from imp import reload
from collections import OrderedDict
from importlib import import_module

if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path

if six.PY2:
    import ConfigParser as config_parser
if six.PY3:
    import configparser as config_parser

from dtaf_core.lib.dtaf_constants import OperatingSystems, Framework
from dtaf_core.lib.os_lib import LinuxDistributions
from src.lib.bios_constants import BiosSerialPathConstants
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.lib.private.cl_utils.adapter.data_types import RET_SUCCESS
from dtaf_core.lib.private.cl_utils.adapter import data_types
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
import src.lib.content_exceptions as content_exception
from src.bios_mapper.bios_mapper import BiosMapper
from src.lib.dtaf_content_constants import ProviderXmlConfigs
from src.lib.content_artifactory_utils import ContentArtifactoryUtils


class BiosUtil:
    """
    Class is used to fetch the bios knobs from config file which specific to test case and will be parsed to them
    to set / write the knobs and to verify that particular knob has been set as per the given config input.
    """
    _bios_obj = None
    _key_target = 'Target'
    _key_name = 'Name'

    def __init__(self, cfg_opts, bios_config_file=None, bios_obj=None, log=None, common_content_lib=None):
        self.bios_config_file = bios_config_file  # Assigning test config.cfg file to var
        self._bios_obj = bios_obj  # Assigning bios_obj
        self._log = log  # Assigning the object for log
        self._common_content_lib = common_content_lib
        self._cfg = cfg_opts
        self._product_family = common_content_lib.get_platform_family()
        self._bios_mapper = BiosMapper(self._product_family)

    def _populate_arguments(self, cp, list_sections):
        """
        Method to populate arguments for calling set_bios_knobs based on Name attribute.
        Go through each section, filter by Name attribute and creates the arguments list

        :param cp: config parser object
        :param list_sections: list of sections in config file

        :return: list of arguments with Name attribute
        :raise: RuntimeError - if section data is not correct.
        """
        try:
            list_args = []
            for section in list_sections:
                is_key_name_avail = cp.has_option(section, self._key_name)

                if not is_key_name_avail:
                    raise KeyError("The config file '{}' does not have 'Name' key, please "
                                   "add 'Name' Key..".format(self.bios_config_file))

                value_to_set = cp.get(section, self._key_target)
                name = cp.get(section, self._key_name)

                # get platform unique name if one exists
                unique_name = self._bios_mapper.get_bios_knob_name(name)
                if unique_name == BiosMapper.NOT_APPLICABLE:
                    self._log.info("The bios knob name '{}' is not applicable for product "
                                   "family '{}'".format(name, self._product_family))
                    continue

                list_args.append('"' + unique_name + '"')
                list_args.append(str(value_to_set))

            return list_args
        except Exception as ex:
            log_error = "Exception while reading bios config file '{}'".format(self.bios_config_file)
            self._log.error(log_error)
            raise ex

    def set_bios_knob(self, bios_config_file=None):
        """
        Method to set the bios knobs.
        1. Parsing through the cfg file to get the sections and its options.
        2. Set the bios knobs according to the cfg file options.

        :param bios_config_file: Bios configuration file
        :return: None
        :raise: RuntimeError - if failed to set the bios knob.
        """

        try:
            cp = config_parser.ConfigParser()
            if not bios_config_file:
                bios_config_file = self.bios_config_file
            cp.read(bios_config_file)
            list_sections = cp.sections()
            list_args = self._populate_arguments(cp, list_sections)

            if len(list_args) > 0:
                call_func_set_bios_knobs = "self._bios_obj.set_bios_knobs("
                for arg in list_args:
                    call_func_set_bios_knobs = call_func_set_bios_knobs + arg + ", "

                call_func_set_bios_knobs = call_func_set_bios_knobs + "overlap=True)"

                # call set_bios_knobs function now
                ret_value = eval(call_func_set_bios_knobs)

                if not ret_value[0]:
                    error_log = "Failed to set the bios knobs due to error '{}'".format(ret_value[1])
                    self._log.error(error_log)
                    raise RuntimeError(error_log)

                self._log.info("Bios knobs are set as per test case config..")
            else:
                self._log.warning("BIOS knob config file was blank, no BIOS knobs were changed.")

        except Exception as ex:
            self._log.error("Failed to set knob due to exception '{}'..".format(ex))
            raise ex

    # def verify_bios_knob(self):
    #     """
    #     Method to verify the bios knobs.
    #     1. Parsing through the cfg file to get the sections and its options for verification.
    #     2. Verifying the bios knobs against the cfg file option at the 0th index.
    #
    #     :return: None
    #     :raise: RuntimeError - if Failed to read the knob / Knob is not set correctly
    #     """
    #     try:
    #         cp = config_parser.ConfigParser()
    #         cp.read(self.bios_config_file)
    #         list_sections = cp.sections()
    #
    #         list_args= self._populate_arguments(cp, list_sections)
    #
    #         if len(list_args) > 0:
    #             call_func_read_bios_knobs = "self._bios_obj.read_bios_knobs("
    #             for arg in list_args:
    #                 call_func_read_bios_knobs = call_func_read_bios_knobs + arg + ", "
    #
    #             call_func_read_bios_knobs = call_func_read_bios_knobs + "hexa=True)"
    #
    #             # call set_bios_knobs function now
    #             eval(call_func_read_bios_knobs)
    #
    #     except Exception as ex:
    #         self._log.error("Error while reading the bios knob with exception = '{}'".format(ex))
    #         raise RuntimeError("Error while reading the bios knob with exception = '{}'".format(ex))

    def verify_bios_knob(self, bios_config_file=None):
        """
        Method to verify the bios knobs.
        1. Parsing through the cfg file to get the sections and its options for verification.
        2. Verifying the bios knobs against the cfg file option at the 0th index.

        :param bios_config_file: Bios configuration file
        :return: None
        :raise: RuntimeError - if Failed to read the knob / Knob is not set correctly
        """
        cp = config_parser.ConfigParser()
        if not bios_config_file:
            bios_config_file = self.bios_config_file
        cp.read(bios_config_file)
        list_sections = cp.sections()

        try:
            ret_val = True
            for section in list_sections:
                name = cp.get(section, self._key_name)
                # get platform unique name if one exists
                unique_name = self._bios_mapper.get_bios_knob_name(name)
                if unique_name == BiosMapper.NOT_APPLICABLE:
                    self._log.info("The bios knob name '{}' is not applicable for product "
                                   "family '{}'".format(name, self._product_family))
                    continue

                ret_value = self._bios_obj.read_bios_knobs(str(unique_name), hexa=True)

                self._log.info("Verifying the knob '{}'..".format(section))

                if not ret_value[0]:
                    error_log = "Failed to read knob '{}' value due to '{}'..".format(section, ret_value[1])
                    self._log.error(error_log)
                    ret_val = False
                    continue

                list_of_numbers = re.findall(r'0x[0-9A-F]+', (' '.join(map(str, ret_value[1]))), re.I)
                current_knob_value = ' '.join(map(str, list_of_numbers))
                current_knob_value = int(current_knob_value,0)

                knob_options = (cp.get(section, self._key_target))
                list_knob_options = str(knob_options).split(',')
                expected_knob_value = list_knob_options[0]
                # remove any quotes if present
                expected_knob_value = expected_knob_value.replace("\"", "")
                expected_knob_value = expected_knob_value.replace("\'", "")
                expected_knob_value = int(expected_knob_value,0)

                if current_knob_value == expected_knob_value:
                    self._log.info("The knob '{}' has been set with correct "
                                   "value '{}'".format(section, expected_knob_value))
                else:
                    self._log.error("The knob '{}' has not been set with correct "
                                    "value '{}'".format(section, expected_knob_value))
                    ret_val = False

            if not ret_val:
                log_error = "One or more Bios knob values are not set as per test case specification..."
                self._log.error(log_error)
                raise RuntimeError(log_error)

        except Exception as ex:
            self._log.error("Error while reading the bios knob with exception = '{}'".format(ex))
            raise RuntimeError("Error while reading the bios knob with exception = '{}'".format(ex))

    def load_bios_defaults(self):
        """
        This function will set the bios to its default settings.

        :return: None
        :raise: RuntimeError - if fails to load default settings
        """
        ret_val = self._bios_obj.default_bios_settings()
        if not ret_val[0]:
            error_log = "Load bios defaults: Failed due to '{}'..".format(ret_val[1])
            self._log.error(error_log)
            raise RuntimeError(error_log)
        self._log.info("Load bios defaults: Successful...")

    def get_max_bios_knob_option(self, prompt):
        """ Gets the maximum available option of the given bios knob

        :param prompt: Knob prompt
        :return: maximum value of bios knob name
        """
        status, message = self._bios_obj.get_knob_options(prompt)
        if not status:
            raise RuntimeError("Failed to get available knob options for " + prompt)
        self._log.debug(message)
        max_value = message.split(':')[-1].strip().split(",")[-1].strip()
        self._log.debug("Maximum value=%s", max_value)
        return max_value

    def set_single_bios_knob(self, name, value):
        """Sets the sing bios knob value at at time

        :param name: Knob name
        :param value: Knob value
        """
        self._bios_obj.set_bios_knobs(name, value, overlap=True)

    def get_bios_knob_current_value(self, name):
        """Reads the sing bios knob

        :param name: knob name
        :return: retunrs current value
        :raise: Raises the RuntimeError if any error
        """
        ret_value = self._bios_obj.read_bios_knobs(name, hexa=True)
        if not ret_value:
            raise RuntimeError("Could not find %s bios knob" % name)
        value = ret_value[1][0].split()[-1].strip()
        return value


class PlatformConfigReader(object):
    """Parser for PlatformConfig.xml"""
    _FRONTPAGE_TAG = "FrontPage"
    _PLATFORM_TAG = "PLATFORM"
    _BIOS_INFO = "BIOS"
    _TPM_REGEX = "Current TPM Device:\s(.*)"
    _KNOBS_FILE = os.path.dirname(os.path.abspath(__file__)) + "/" + "knobs.py"
    HIDDEN_KNOB_STATUS = "hidden"
    READONLY_KNOB_STATUS = "readonly"
    ACCESSIBLE_KNOB_STATUS = "accessible"
    MEMORY_FREQUENCY_XPATH = './/knob[@name="DdrFreqLimit"]'

    def __init__(self, xml_file, test_log):
        """Constructor of PlatformConfigReader

        @param xml_file: PlatforConfig.xml path to parse
        """
        self.xml_file = xml_file
        self._log = test_log
        parser = ET.parse(self.xml_file)
        self.root = parser.getroot()

    def update_xml_file(self, xml_file):
        """Reloads the parser

        @param xml_file: PlatforConfig.xml path to parse
        """
        self.xml_file = xml_file
        parser = ET.parse(self.xml_file)
        self.root = parser.getroot()

    def get_postpage_info(self):
        """Gets the bios post page info"""
        node = self.root.find(self._FRONTPAGE_TAG)
        info = {}
        for key, value in node.attrib.items():
            info[key] = value
        return info

    def get_bios_version_info(self):
        """Gets the bios info"""
        node = self.root.find(self._BIOS_INFO)
        info = {}
        for key, value in node.attrib.items():
            info[key] = value
        return info

    def get_platform_info(self):
        """Gets the platform info"""
        node = self.root.find(self._PLATFORM_TAG)
        info = {}
        for key, value in node.attrib.items():
            info[key] = value
        return info

    def get_hexadecimal_value(self, frequency_option):
        """Gets the hexadecimal value of option text

        @param : frequency option text
        @return : returns the hexadecimal value of option text
        """
        import lxml.etree as etree
        root = etree.parse(self.xml_file)
        memory_frequency_node = root.xpath(self.MEMORY_FREQUENCY_XPATH)
        options_node = memory_frequency_node[0].getchildren()
        frequency_option_nodes = options_node[0].getchildren()
        hexadecimal_of_frequency_option = ""
        for frequency_option_text in frequency_option_nodes:
            if frequency_option_text.attrib['text'] == frequency_option:
                hexadecimal_of_frequency_option = frequency_option_text.attrib['value']
                break
        return hexadecimal_of_frequency_option

    def get_post_page_memory_size(self):
        """Gets the post page memory size"""
        return self.get_postpage_info()["MemorySize"]

    def __read_commented_info(self):
        """Gets the readonly information which is in the form of text"""
        commented_info = []
        with open(self.xml_file) as f:
            for line in f:
                if line.strip().startswith("<!--"):
                    commented_info.append(
                        line.strip().strip("<!--").strip("-->").strip())
        return "\n".join(commented_info)

    def get_commented_info(self):
        """
        Gets the commented information

        :return: List of Values of the commented information in string type.
        """
        return self.__read_commented_info()

    def get_knobs_current_values(self, names):
        """Gets the knob current value

        @param names: Knob names
        @return: knob current value
        """
        knobs_values = {}
        for knob in self.root.iter("knob"):
            name = knob.get("name")
            if name in names:
                knobs_values[name] = knob.get("CurrentVal")
        return knobs_values

    def __get_all_knobs(self):
        """Gets the all knobs"""
        knobs_values = {}
        for knob in self.root.iter("knob"):
            name = knob.get("name")
            knobs_values[name] = literal_eval(knob.get("CurrentVal"))
        return knobs_values

    def __get_knob_depex(self, name):
        """Gets the knob depex

        @param name: Knob name
        @return: knob depex value
        """
        depex = "TRUE"
        for knob in self.root.iter("knob"):
            if knob.get("name").strip() == name:
                return knob.get("depex")
        return depex

    def __convert_to_py_cond(self, condition):
        """Converts the bios depex to python condition"""
        self._log.debug("Depex: %s", condition)
        condition = condition.replace("_EQU_", "==").replace("_OR_", "or").\
            replace("_NEQ_", "!=").replace("OR", "or").replace("AND", "and").\
            replace("_EQU_", "==").replace("Sif", "").replace("Gif", "")
        self._log.debug("PyCondition: %s", condition)
        return condition

    def get_knob_status(self, name):
        """Gets the knob status either hidden or readonly or accessible"""
        values = self.__get_all_knobs()
        self._log.debug(values)
        # Writing to a temp file
        with open(self._KNOBS_FILE, "w") as f:
            for knob, value in values.items():
                f.write(knob + "=" + str(value) + "\n")
        knobs_module = import_module("src.lib.knobs", "*")
        reload(knobs_module)
        # Making all the knobs vlaues as globals
        names = [x for x in knobs_module.__dict__ if not x.startswith("_")]
        globals().update({k: int(getattr(knobs_module, k)) for k in names})
        depex = self.__get_knob_depex(name)
        knob_status = "accessible"
        if depex.strip() != "TRUE":
            split_depex = depex.split("_AND_")
            sifs = [line.strip() for line in split_depex if
                    line.strip().startswith("Sif(")]
            gifs = [line.strip() for line in split_depex if
                    line.strip().startswith("Gif(")]
            sif_values = []
            gif_values = []
            for sif in sifs:
                sif_values.append(
                    str(eval(self.__convert_to_py_cond(sif))).capitalize())
            for gif in gifs:
                gif_values.append(
                    str(eval(self.__convert_to_py_cond(gif))).capitalize())
            self._log.debug("sif values {}".format(sif_values))
            self._log.debug("gif values {}".format(gif_values))
            is_suppressed = False
            if len(sif_values):
                is_suppressed = eval(" or ".join(sif_values))
                if is_suppressed:
                    knob_status = "hidden"
            if not is_suppressed:
                if len(gif_values):
                    if eval(" or ".join(gif_values)):
                        knob_status = "readonly"
        if os.path.exists(self._KNOBS_FILE):
            os.remove(self._KNOBS_FILE)
        return knob_status

    def filter_commented_info(self, string_pattern_to_search, commented_info):
        """
        This method searches the given string pattern from the commented information of platformconfig.xml

        :param string_pattern_to_search: pattern string to search
        :param commented_info: Gets the comment information from platformconfig.xml
        :return: return the regex search object
        """
        return re.search(string_pattern_to_search, commented_info)

    def get_current_tpm_device(self):
        """
        This method is to get the current TPM device information.

        :return: return the TPM device
        :raise: raises the content_exception.TestFail
        """
        tpm_device_info = self.filter_commented_info(self._TPM_REGEX, self.__read_commented_info())
        if not tpm_device_info:
            raise content_exception.TestFail("Fail to get the TPM Device info form using xmlcli")
        self._log.debug("{} Device is connected".format(tpm_device_info.group(1)))
        return tpm_device_info.group(1)

    def verify_tpm_is_disabled(self):
        """
        This method is to verify TPM device is disabled

        :return: return True if else false
        """
        self._log.info("verify the TPM is Disabled")
        tpm_device_info = self.filter_commented_info(self._TPM_REGEX, self.__read_commented_info())
        if not tpm_device_info:
            self._log.info("TPM is Disabled on the SUT")
            return True
        return False


class BootOptions(object):
    """
    This class defines the supported boot options to be set.
    """
    WINDOWS = OperatingSystems.WINDOWS
    FEDORA = LinuxDistributions.Fedora
    RHEL = LinuxDistributions.RHEL
    CLEARLINUX = LinuxDistributions.ClearLinux
    SLES = LinuxDistributions.SLES
    UBUNTU = LinuxDistributions.Ubuntu
    ESXI = OperatingSystems.ESXI
    UEFI = "UEFI Internal Shell"


class ChooseBoot:
    """
    This class allows the user to choose what to boot into using the boot menu.
    """
    SUPPORTED_BOOT_MENU_OPTIONS_DICT = {BootOptions.RHEL: "Red Hat Enterprise Linux",
                                        BootOptions.UEFI: "UEFI Internal Shell"}
    BIOS_UI = 'BIOS_UI_OPT_TYPE'

    def __init__(self, boot_menu_obj, common_content_configuration, log, ac_obj, os, cfg_opts):
        self._boot_menu_obj = boot_menu_obj
        self._ac_obj = ac_obj
        self._os = os
        self._common_content_configuration = common_content_configuration
        self._log = log
        self._press_f7_key = self._common_content_configuration.get_uefi_select_key()
        self._f7_key_wait_time = self._common_content_configuration.bios_boot_menu_select_time_in_sec()
        self._sut_shutdown_delay = self._common_content_configuration.sut_shutdown_delay()
        self._ac_timeout_delay_in_sec = self._common_content_configuration.ac_timeout_delay_in_sec()
        self._common_content_Lib = CommonContentLib(log, os, cfg_opts)

    def boot_choice(self, boot_option):
        """
        Allows the user to choose between different boot options based on the boot menu

        :param boot_option: boot option to be chosen for booting
        :return: None
        """
        return_val = False
        if boot_option not in self.SUPPORTED_BOOT_MENU_OPTIONS_DICT:
            raise content_exception.TestError("Desired boot option is not supported:" + boot_option)

        self._common_content_Lib.perform_graceful_ac_off_on(self._ac_obj)

        #if self.graceful_sut_ac_power_on():

        self._log.info("Waiting for menu entry...")
        self._boot_menu_obj.wait_for_entry_menu(
                int(self._common_content_configuration.bios_boot_menu_entry_wait_time()))
        self._log.info("Will press F7 now...")
        self._boot_menu_obj.press_key(str(self._press_f7_key))  # Pressing F7
        self._log.info("F7 pressed now...")
        time.sleep(int(self._f7_key_wait_time))
        self._boot_menu_obj.select(self.SUPPORTED_BOOT_MENU_OPTIONS_DICT[boot_option], self.BIOS_UI, int(
                                   self._f7_key_wait_time), False)
        return_val = self._boot_menu_obj.enter_selected_item(int(self._f7_key_wait_time), True)
        return return_val

    def graceful_sut_ac_power_on(self):
        """
        This function performs ac power off and then on.

        :return: return the power state True/False
        """
        ret_val = False
        if self._os.is_alive():
            self._os.shutdown(self._sut_shutdown_delay)
        if self._ac_obj.ac_power_off(self._ac_timeout_delay_in_sec):
            self._log.info("Ac power turned off")
        else:
            self._log.debug("Trying one more time to perform AC power off")
            if self._ac_obj.ac_power_off(self._ac_timeout_delay_in_sec):
                self._log.info("Ac power turned off")
            else:
                self._log.info("Unable to perform ac power off")
        if self._ac_obj.ac_power_on(self._ac_timeout_delay_in_sec):
            self._log.info("Ac power turned on")
            ret_val = True
        else:
            self._log.debug("Trying one more time to perform AC power on")
            if self._ac_obj.ac_power_on(self._ac_timeout_delay_in_sec):
                self._log.info("Ac power turned on")
                ret_val = True
            else:
                self._log.info("Unable to perform ac power on")
        return ret_val


class ItpXmlCli(object):
    """
    This class provides few out of band xmlcli API's to directly call from ITP host system.
    """
    PLATFORM_CONFIG_FILE = "PlatformConfig.xml"
    SUPPORTED_BOOT_OPTION_VALUE = [BootOptions.WINDOWS, LinuxDistributions.Fedora, LinuxDistributions.RHEL,
                                   LinuxDistributions.ClearLinux, LinuxDistributions.SLES,
                                   LinuxDistributions.Ubuntu, BootOptions.ESXI, BootOptions.UEFI]

    itp_xmlcli_constants = {"XMLCLI_ZIP_FILE": None, "XMLCLI_FOLDER_NAME": None}

    COLLATERAL_DIR_NAME = 'collateral'

    def __init__(self, log, cfg_opts=None):
        self._log = log
        self._log_dir = self.get_log_file_dir()
        self.cfg_opts = cfg_opts
        self._content_config = ContentConfiguration(self._log)
        self.install_itp_xmlcli()
        self._platform_config_file = None
        self._boot_order_xpath = './/knob[@name="BootOrder_0"]'
        self._sdp = None

        if self.cfg_opts:
            try:
                sdp_cfg = self.cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
                self._sdp = ProviderFactory.create(sdp_cfg, self._log)  # type: SiliconDebugProvider
                # set the debugport PrdyNotWired to True to avoid timeout error
                self._sdp.itp.config.debugport0.PlatformControl.PrdyNotWired = "True"
                self._log.info("The debugport 0 PlatformControl PrdyNotWired is set to True..")
            except Exception as ex:
                self._log.debug("Failed to set debug port0 PrdyNotWired to True due to exception='{}'".format(ex))

        try:
            import pysvtools.xmlcli.XmlCli as cli
            self._log.info("Setting AuthenticateXmlCliApis to True...")
            cli.clb.AuthenticateXmlCliApis = True
            self._cli = cli
        except Exception as ex:
            raise ImportError("Failed to import XmlCli due to exception = '{}',"
                              "Please check if CScripts or python-sv environment is setup correctly...".format(ex))

    def install_itp_xmlcli(self):
        """
        Copies the xmlcli package to use with itp interface to automation folder.
        :return: itp_xmlcli install path.
        :raises: RuntimeError - if any runtime error during copy to automation folder..
        """
        self._log.info("Installing ITP xmllci on host..")
        exec_os = platform.system()
        try:
            automation_folder = Framework.CFG_BASE[exec_os]
        except KeyError:
            err_log = "Error - execution OS " + str(exec_os) + " not supported!"
            self._log.error(err_log)
            raise KeyError(err_log)

        self.itp_xmlcli_constants["XMLCLI_ZIP_FILE"] = self._content_config.get_xmlcli_tools_name()
        self.itp_xmlcli_constants["XMLCLI_FOLDER_NAME"] = self._content_config.get_xmlcli_tools_name().split(".")[0]
        self._log.debug("Checking and downloading itp xmlcli version-{}  from Artifactory".format(
            self.itp_xmlcli_constants["XMLCLI_FOLDER_NAME"]))
        xmlcli_path = os.path.join(automation_folder, self.itp_xmlcli_constants["XMLCLI_FOLDER_NAME"])
        if not os.path.exists(xmlcli_path):
            artifactory_obj = ContentArtifactoryUtils(self._log, cfg_opts=self.cfg_opts)

            xmlcli_collateral_path = artifactory_obj.download_tool_to_automation_tool_folder(
                self.itp_xmlcli_constants["XMLCLI_ZIP_FILE"], exec_env="Uefi")
            self.extract_zip_file_on_host(xmlcli_collateral_path, automation_folder)
        try:
            import pysvtools.xmlcli.XmlCli as cli
            self._log.info("ITP xmllci installed on host and able to import it successfully..")
            self._log.info("Setting AuthenticateXmlCliApis to True...")
            cli.clb.AuthenticateXmlCliApis = True
        except Exception as ex:
            self._log.warning("Itp xmlcli is not installed, installing it")
            try:
                import threading
                start_thread = threading.Thread(target=self._execute_setup_file_for_xmlcli_host, args=(xmlcli_path,),
                                                daemon=True)
                start_thread.start()
                self._log.info("Threading has started for installing ITP-Xmlcli package.")
                # waiting for the installation process to complete
                time.sleep(15)
                import pysvtools.xmlcli.XmlCli as cli
                self._log.info("ITP xmllci installed on host and able to import it successfully..")
                self._log.info("Setting AuthenticateXmlCliApis to True...")
                cli.clb.AuthenticateXmlCliApis = True
            except Exception as ex:
                raise ("Exception occurred while installing itp xmlcli on HOST due to {}".format(ex))

    def _execute_setup_file_for_xmlcli_host(self, xmlcli_path):
        """
        This method is to install itp xmlcli python package on host

        :param xmlcli_path: folder path of the xmlcli pkg on HOST,
        :raise: RuntimeError
        """
        py_path = str(sys.executable)
        setup_path = os.path.join(xmlcli_path, "setup.py")
        command_line = py_path + " " + setup_path + " install"
        self._log.info("cmd {}".format(command_line))
        process_obj = subprocess.Popen(command_line, cwd=xmlcli_path, shell=True)
        process_obj.communicate()
        if process_obj.returncode != 0:
            log_error = "The command '{}' failed...".format(command_line)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        process_obj.kill()

    def extract_zip_file_on_host(self, zip_file_path, dest_path):
        """
        This method extracts the zip file on specified destination folder on HOST.

        :param zip_file_path: zip file with path to be extracted
        :param dest_path: destination folder where zip file to be extracted

        :raises: RuntimeError - if failed to extract the zip file.
        :return: None
        """
        try:
            self._log.info("Extracting zip file '{}' to destination folder '{}'..".format(zip_file_path, dest_path))
            with ZipFile(zip_file_path, 'r') as zp:
                zp.extractall(path=dest_path)
                self._log.info("Extract zip file: Successful..")
        except Exception as ex:
            log_error = "Extract zip file: Failed due to exception '{}'..".format(ex)
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def get_collateral_path(self):
        """
        Function to get the collateral directory path

        :return: collateral_path
        """
        try:
            parent_path = Path(os.path.dirname(os.path.realpath(__file__)))
            collateral_path = os.path.join(str(parent_path), self.COLLATERAL_DIR_NAME)
            return collateral_path
        except Exception as ex:
            self._log.error("Exception occurred while running running the 'get_collateral_path' function")
            raise ex

    def get_log_file_dir(self):
        """Gets the file handler from logger object"""
        for handler in self._log.handlers:
            if str(type(handler)) == "<class 'logging.FileHandler'>":
                return os.path.split(handler.baseFilename)[0]

    def get_platform_config_file_path(self):
        """
        This function saves the platform config file in test_log_file folder and returns the path to XML file

        :return: returns the PlatformConfig.xml file name along with path.
        """
        try:
            xml_platform_config_file = os.path.join(self._log_dir, self.PLATFORM_CONFIG_FILE)
            if os.path.exists(xml_platform_config_file):
                self._log.info("Removing the existing platform config file")
                os.remove(xml_platform_config_file)
            self._cli.savexml(filename=xml_platform_config_file)
            if not os.path.isfile(xml_platform_config_file):
                raise RuntimeError("Failed to get platform config XML file through ITP interface. "
                                   "Please check your PythonSV and CScript installation...")
            return xml_platform_config_file
        except Exception as ex:
            log_error = "Failed to get platform config file path due to exception '{}'".format(ex)
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def __get_current_boot_order(self):
        """
        This function parses the platform config file and gets the current boot order

        :return: returns the current boot order dictionary.
        """
        import lxml.etree as etree
        current_boot_order = {}
        self._platform_config_file = self.get_platform_config_file_path()
        root = etree.parse(self._platform_config_file)
        boot_order_node = root.xpath(self._boot_order_xpath)
        options_node = boot_order_node[0].getchildren()
        boot_option_nodes = options_node[0].getchildren()

        index = 0
        for boot_option_node in boot_option_nodes:
            key = boot_option_node.attrib['text'] + "-" + str(index)
            value = boot_option_node.attrib['value']
            current_boot_order[key] = value
            index += 1

        return current_boot_order

    def __get_boot_order_string(self, boot_option_value, current_boot_order):
        """
        This function finds if boot_option_value is present in current boot order, if yes
        creates the new boot order string by putting this as first boot value.

        :param: boot_option_value - boot option to be set as default
        :param: current_boot_order - current boot order dictionary
        :raises: TestNAError - if specified boot option value is not supported.

        :return: returns the new boot order string.
        """
        # find the key name of boot_option_value to be set as default
        key_name = None
        key_value = None
        for key, value in current_boot_order.items():
            if str(boot_option_value).lower() in str(key).lower():
                # we found the boot option
                key_name = key
                key_value = value
                break

        if not key_name:
            log_error = "Did not find the boot option for specified environment '{}".format(boot_option_value)
            self._log.error(log_error)
            raise content_exception.TestNAError(log_error)

        # form the boot order string
        boot_order_string = "%02s" % key_value
        for key, value in current_boot_order.items():
            if key == key_name:
                continue
            boot_order_string = boot_order_string + "-" + "%02s" % value

        return boot_order_string.replace("0x", "0")

    def set_default_boot(self, boot_option_value, boot_flag=True):
        """
        This function finds if boot_option_value is present in current boot order, if yes
        creates the new boot order string by putting this as first boot value. Then it calls
        SetBootOrder to make boot_option_value as default boot

        :param: boot_option_value - boot option to be set as default
        :param: boot_flag is set False if the Supported boot option check need to be skipped
        :raises: TestNAError - if specified boot option value is not supported.
        :raises: TestFail - iif failed to set boot order

        :return: None.
        """
        if boot_flag:
            if boot_option_value not in self.SUPPORTED_BOOT_OPTION_VALUE:
                raise content_exception.TestNAError("The boot option '{}' is not supported. Supported boot option "
                                                    "values are '{}'".format(boot_option_value, self.SUPPORTED_BOOT_OPTION_VALUE))

        current_boot_order = self.__get_current_boot_order()
        new_boot_order_string = self.__get_boot_order_string(boot_option_value, current_boot_order)

        self._log.info("The new boot order string: '{}'".format(new_boot_order_string))

        if self._cli.SetBootOrder(new_boot_order_string) != 0:
            log_error = "Setting the new boot order failed with default boot option as '{}' " \
                        "is failed..".format(boot_option_value)
            self._log.error(log_error)
            raise content_exception.TestFail(log_error)

        self._log.info("Setting the boot order with new default boot option as '{}' is "
                       "succeeded...".format(boot_option_value))

    def get_current_boot_order_string(self):
        """
        This function sets the current boot order string. User can store this string and can use this string
        to set back to this boot order.

        :return: None
        """
        self._platform_config_file = self.get_platform_config_file_path()
        current_boot_order = self.__get_current_boot_order()
        boot_option_value = next(iter(current_boot_order))
        current_boot_order_string = self.__get_boot_order_string(boot_option_value, current_boot_order)
        self._log.info("Current boor order string: '{}'".format(current_boot_order_string))
        return current_boot_order_string

    def set_boot_order(self, boot_order_string):
        """
        This function sets the boot order using string passed to this function.

        :param boot_order_string: boot order string e.g. "01-04-03-07-09"
        :raises: TestFail - if fails to set the boot order
        :return: None
        """
        self._log.info("Setting the boot order: '{}'".format(boot_order_string))
        if self._cli.SetBootOrder(boot_order_string) != 0:
            log_error = "Set boot order with value '{}' failed...".format(boot_order_string)
            self._log.error(log_error)
            raise content_exception.TestFail(log_error)

        self._log.info("Set boot order with value '{}' succeeded".format(boot_order_string))

    def perform_clear_cmos(self, sdp, os_obj, timeout):
        """
        This method clears the CMOS with ITP commands

        :param sdp: silicon debug provider object
        :param os_obj: os object
        :param timeout: reboot timeout
        :return: None
        """
        self._log.info("Performing clear cmos")
        try:
            self._log.info("Halting CPU")
            sdp.halt()
            self._log.info("Clearing CMOS")
            self._cli.clb.clearcmos()
        except Exception as e:
            raise e
        finally:
            sdp.go()
            self._log.info("Executing pulse power good for rebooting the platform")
            sdp.pulse_pwr_good()
            os_obj.wait_for_os(timeout)

    def _convert_bios_knob_file(self, knob_file):
        """
        type: (str) -> dict
        Function takes in a BIOS knob file in format for XmlCli use in OS and converts to a dict structure.
        :param knob_file: Input file for XmlCli through OS.
        :return: dict in format BIOS knob name from Platform_Configuration.xml file as key and setting as value."""
        knob_dict = {}
        with open(knob_file) as f:
            for line in f:
                if line != "":
                    split_line = line.split('=', 1)
                    if split_line[0].strip() == "Name":
                        key = split_line[1].strip()
                    elif split_line[0].strip() == "Target":
                        try:
                            knob_dict[key] = split_line[1].strip('"\n "')
                        except KeyError:
                            pass
        return knob_dict

    def set_bios_knobs(self, knob_file, restore_modify=False):
        """
        type: (str, bool) -> None
        Function takes in a BIOS knob file in format for XmlCli use in OS and converts to XmlCli through PythonSV
        format and then sets the BIOS knobs.
        :param knob_file: Input file for XmlCli through OS.
        :param restore_modify: Reset BIOS knobs to default before applying BIOS knob changes.
        :raise RuntimeError: If BIOS knobs fail to set with XmlCli."""
        cleaned_knob_file = self._convert_bios_knob_file(knob_file)
        knob_string = ""
        for knob in cleaned_knob_file.keys():
            knob_string = knob_string + "{}={},".format(knob, cleaned_knob_file[knob])
        knob_string = knob_string[:-1]  # cleave off last comma
        if restore_modify:
            self._log.debug("Restoring BIOS knobs to default. then applying BIOS knob changes.")
            if self._cli.CvRestoreModifyKnobs(knob_string) != 0:
                raise RuntimeError("Failed to set BIOS knobs: {}".format(knob_string))
        else:
            if self._cli.CvProgKnobs(knob_string) != 0:
                raise RuntimeError("Failed to set BIOS knobs: {}".format(knob_string))

    def verify_bios_knobs(self, knob_file):
        """ type: (str) -> None
        Function takes in a BIOS knob file in format for XmlCli use in OS and converts to XmlCli through PythonSV
        format and then checks the BIOS knobs.
        :param knob_file: Input file for XmlCli through OS.
        :raise RuntimeError: If BIOS knobs fail to set with XmlCli."""
        cleaned_knob_file = self._convert_bios_knob_file(knob_file)
        knob_string = ""
        for knob in cleaned_knob_file.keys():
            knob_string = knob_string + "{}={},".format(knob, cleaned_knob_file[knob])
        knob_string = knob_string[:-1]  # cleave off last comma
        if self._cli.CvReadKnobs(knob_string) != 0:
            raise RuntimeError("One or more of the BIOS knobs are not set as expected: {}".format(knob_string))


class SerialBiosUtil(object):
    """Serial Bios Util which navigates through the Bios menu UI"""

    _AC_TIMEOUT = 30
    _WAIT_FOR_ENTRY_MENU_TIMEOUT = 1200
    _WAIT_FOR_SETUP_MENU_TIMEOUT = 60
    _WAIT_FOR_SET_BIOS_KNOB = 60
    _PRESS_F2_KEY = "F2"
    _PRESS_F10_KEY = "F10"
    _PRESS_CONFIRM_KEY = "Y"
    _PRESS_ESC_KEY = data_types.BIOS_CMD_KEY_ESC
    _PRESS_RETURN_KEY = data_types.BIOS_CMD_KEY_ENTER
    _KNOB_ENABLED = "<Enable>"
    _KNOB_DISABLED = "<Disable>"
    BIOS_BOOTMENU_CONFIGPATH = "suts/sut/providers/bios_setupmenu"

    _EDKII_MENU = OrderedDict([(r"EDKII Menu", data_types.BIOS_UI_DIR_TYPE)])
    _CONTINUE = OrderedDict([(BiosSerialPathConstants.CONTINUE_KNOB, data_types.BIOS_UI_DIR_TYPE)])
    _RESET = OrderedDict([(BiosSerialPathConstants.RESET_KNOB, data_types.BIOS_UI_DIR_TYPE)])

    def __init__(self, ac, log, common_content_lib, cfg_opts):
        """Constructor"""
        self._ac = ac
        self._log = log
        self._common_content_lib = common_content_lib
        bios_set_menu_cfg = cfg_opts.find(self.BIOS_BOOTMENU_CONFIGPATH)
        self._bios_setup_menu_obj = ProviderFactory.create(bios_set_menu_cfg, self._log)  # type: # BiosSetupMenuProvider

    def press_key(self, key=None):
        """Send key press over serial.
        :param key: key press to be sent to serial
        :type: data_types.BIOS_CMD_KEY"""
        self._bios_setup_menu_obj.press_key(key,  True, self._WAIT_FOR_SET_BIOS_KNOB)

    def navigate_bios_menu(self):
        """
        This function navigates to Bios Menu.

        :return: True if the SUT navigates to Bios Menu
        """
        self._log.info("Waiting for menu entry...")
        self._common_content_lib.perform_graceful_ac_off_on(self._ac)
        if not self._bios_setup_menu_obj.wait_for_entry_menu(self._WAIT_FOR_ENTRY_MENU_TIMEOUT):
            return False, "Unable to navigate to Bios screen"
        self._log.debug('******* Press F2  *******')
        f2_state = self._bios_setup_menu_obj.press(self._PRESS_F2_KEY)
        if not f2_state:
            return False, "Unable to press F2 key"
        self._log.debug("Pressed F2 key")
        if not self._bios_setup_menu_obj.wait_for_bios_setup_menu(self._WAIT_FOR_SETUP_MENU_TIMEOUT) == RET_SUCCESS:
            return False, "Sut did not enter to Bios Screen mode"
        self._log.info("Sut booted in Bios screen mode")
        return True, RET_SUCCESS

    def select_enter_knob(self, knob_details):
        """ Select and press bios knob

        :param knob_details: knob details
        :return: None
        """
        for knob, knob_type in knob_details.items():
            self._log.debug("Navigating to %s -> %s", knob, knob_type)
            if self._bios_setup_menu_obj.select(knob, knob_type, self._WAIT_FOR_SET_BIOS_KNOB, True) != RET_SUCCESS:
                raise content_exception.TestFail("Failed to select Bios knob")
            if self._bios_setup_menu_obj.enter_selected_item(True, self._WAIT_FOR_SETUP_MENU_TIMEOUT) != RET_SUCCESS:
                raise content_exception.TestFail("Failed to press selected bios knob")
            self._log.debug("Navigated to %s -> %s", knob, knob_type)

    def set_bios_knob(self, knob, knob_type, setting):
        """Set BIOS knob provided to setting provided.
        :param knob: BIOS knob label.
        :param knob_type: BIOS knob type.
        :param setting: What to change the BIOS knob setting to."""
        self._log.debug("Navigating to %s -> %s", knob, knob_type)
        if self._bios_setup_menu_obj.select(knob, knob_type, self._WAIT_FOR_SET_BIOS_KNOB, True) != RET_SUCCESS:
            raise content_exception.TestFail("Failed to select Bios knob")
        self._log.debug("Setting BIOS knob {} to {}.".format(knob, setting))
        if self._bios_setup_menu_obj.select_from_popup(setting, False) != RET_SUCCESS:
            raise content_exception.TestFail("Failed to select BIOS knob option.")

    def save_bios_settings(self):
        """Press F10 to save BIOS settings."""
        if not self._bios_setup_menu_obj.press(self._PRESS_F10_KEY):
            return False, "Unable to press F10 key"
        self._log.debug("Pressed F10 key")
        time.sleep(self._WAIT_FOR_SET_BIOS_KNOB)
        self._log.info("Saving BIOS setting.")
        if not self._bios_setup_menu_obj.press_key(self._PRESS_CONFIRM_KEY, True, self._WAIT_FOR_SET_BIOS_KNOB):
            return False, "Unable to confirm key"
        time.sleep(self._WAIT_FOR_SET_BIOS_KNOB)

    def select_knob(self, knob, knob_type):
        """"""
        if self._bios_setup_menu_obj.select(knob, knob_type, self._WAIT_FOR_SET_BIOS_KNOB, True) != RET_SUCCESS:
            raise content_exception.TestFail("Failed to select Bios knob: %s" % knob)

    def get_page_information(self):
        """Gets the bios page information"""
        return self._bios_setup_menu_obj.get_page_information().result_value

    def get_current_screen_info(self):
        """Gets the current bios page info"""
        return self._bios_setup_menu_obj.get_current_screen_info().result_value

    def select_edkii_menu(self):
        """Enter into edkii menu"""
        success, msg = self.navigate_bios_menu()
        if not success:
            raise content_exception.TestFail(msg)
        self.select_enter_knob(self._EDKII_MENU)

    def go_back_a_screen(self):
        """Go back to the previous screen by pressing ESC."""
        esc_state = self._bios_setup_menu_obj.press_key(self._PRESS_ESC_KEY, True, self._WAIT_FOR_SET_BIOS_KNOB)
        if not esc_state:
            return False, "Unable to press ESC key"

    def read_item(self):
        """
        type: () -> str
        Reads currently selected BIOS knob.
        :return: tuple containing knob label, data_type of knob, knob description, and current knob status."""
        item = self._bios_setup_menu_obj.get_selected_item().result_value
        return item

    def check_current_item_status(self):
        """type: () -> bool
        Returns current knob setting for currently selected item.
        :return: True if knob is enabled, False if knob is disabled."""
        results = self.read_item()[-1]
        if results == self._KNOB_ENABLED:
            return True
        elif results == self._KNOB_DISABLED:
            return False
        else:
            self._log.error("Could not determine knob results, as check can only verify if knob is enabled.  Results "
                            "returned are {}.".format(results))

    def go_back_to_root(self):
        """Exit out of BIOS menu and continue to boot SUT."""
        self._bios_setup_menu_obj.back_to_root(self._WAIT_FOR_SETUP_MENU_TIMEOUT, False)

    def exit_out_bios_menu(self):
        """Exit out of BIOS menu and continue to boot SUT."""
        self._bios_setup_menu_obj.back_to_root(self._WAIT_FOR_SETUP_MENU_TIMEOUT, False)
        self.select_enter_knob(self._CONTINUE)

    def reset_sut(self):
        """Exit out of BIOS menu and continue to boot SUT."""
        self._bios_setup_menu_obj.back_to_root(self._WAIT_FOR_SETUP_MENU_TIMEOUT, False)
        self.select_enter_knob(self._RESET)

    def write_input_text(self, knob, knob_type, data):
        """Enter data, and press Enter to save.
        :param knob: Knob label in BIOS menu
        :param knob_type: one of the data_types from bios_util class
        :param data: Input to enter into BIOS text field."""
        if type(data) != str:
            data = str(data)
        if self._bios_setup_menu_obj.select(knob, knob_type, self._WAIT_FOR_SET_BIOS_KNOB, True) != RET_SUCCESS:
            raise content_exception.TestFail("Failed to select Bios knob")
        self._bios_setup_menu_obj.press_key(self._PRESS_RETURN_KEY, True, self._WAIT_FOR_SET_BIOS_KNOB)
        self._log.debug("Setting BIOS knob {} to {}.".format(knob, data))
        if self._bios_setup_menu_obj.input_text(text=data) != RET_SUCCESS:
            raise RuntimeError("Failed to write data into BIOS input field: {}".format(data))
        self._bios_setup_menu_obj.press_key(self._PRESS_RETURN_KEY, True, self._WAIT_FOR_SET_BIOS_KNOB)
