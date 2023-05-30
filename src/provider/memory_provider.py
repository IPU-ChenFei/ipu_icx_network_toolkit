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
import os
from abc import ABCMeta, abstractmethod
from importlib import import_module

import string
from dtaf_core.lib.dtaf_constants import OperatingSystems, ProductFamilies
from six import add_metaclass

from src.lib import content_exceptions
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib.install_collateral import InstallCollateral
from src.provider.base_provider import BaseProvider
from src.lib.os_lib import WindowsCommonLib
from src.lib.dmidecode_parser_lib import DmiDecodeParser
from src.lib import dtaf_content_constants
from src.lib.dtaf_content_constants import RootDirectoriesConstants
from src.lib.memory_constants import MemoryClusterConstants
from src.provider.cpu_info_provider import CpuInfoProvider
from src.lib.content_artifactory_utils import ContentArtifactoryUtils
from src.lib.tools_constants import ArtifactoryName, ArtifactoryTools
from src.lib.memory_constants import PlatformMode


@add_metaclass(ABCMeta)
class MemoryProvider(BaseProvider):
    """ Class to provide Linux windows to get total system memory, populated memory slots functionalities """

    LINUX_USR_ROOT_PATH = "/root"
    C_DRIVE_PATH = "C:\\"
    #  Need /accepteula for accepting end user license agreement via command line
    CORE_INFO_CMD = "Coreinfo.exe -n /accepteula"
    REGEX_FOR_NUMA_NODE = r"NUMA.*Node\s\d+"
    DDR_STRING = "None"
    CR_STRING = "None"
    NON_VOLATILE = "non-volatile"
    INTEL_PERSISTENT_MEMORY = "Intel persistent memory"
    DDR5_STRING = "DDR5"
    DDR4_STRING = "DDR4"

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new MemoryProvider object.

        :param log: Logger object to use for output messages
        :param os_obj: OS object
        """
        super(MemoryProvider, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._os = os_obj
        self._sut_os = self._os.os_type

        self._common_content_lib_obj = CommonContentLib(self._log, self._os, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._command_timeout = self._common_content_configuration.get_command_timeout()
        self._windows_common_lib = WindowsCommonLib(self._log, self._os)
        self._dmidecode_parser = DmiDecodeParser(self._log, self._os)
        self.config = dtaf_content_constants.ChannelConfigConstant.CHANNEL_CONFIG_1
        self._product_family = self._common_content_lib_obj.get_platform_family()
        self._cpu_info_provider = CpuInfoProvider.factory(self._log, cfg_opts, self._os)
        self._artifactory_obj = ContentArtifactoryUtils(self._log, self._os, self._common_content_lib_obj, cfg_opts)

    @staticmethod
    def factory(log, cfg_opts, os_obj):
        """
        To create a factory object.

        :param log: Logger object to use for output messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :param os_obj: OS object
        :return: object
        """
        package = r"src.provider.memory_provider"
        if OperatingSystems.WINDOWS == os_obj.os_type:
            mod_name = "MemoryWindowsProvider"
        elif OperatingSystems.LINUX == os_obj.os_type:
            mod_name = "MemoryLinuxProvider"
        else:
            raise NotImplementedError("Test is not implemented for %s" % os_obj.os_type)

        mod = import_module(package, mod_name)
        aclass = getattr(mod, mod_name)
        return aclass(log=log, cfg_opts=cfg_opts, os_obj=os_obj)

    @abstractmethod
    def re_initialize_memory_provider(self):
        """
        This function is used to reinitialise the memory provider.
        """
        raise NotImplementedError

    @abstractmethod
    def get_total_system_memory(self):
        """
        This function is used to get the total system memory

       :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_total_memory_slots(self):
        """
        This function returns number of memory slots in system.

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_populated_memory_slots(self):
        """
        This function is used to get the populated memory locator information in the SUT

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_locator_info(self, mem_info, locator):
        """
        This function is used to return the information of the DIMM based on the mem_info like Size, Speed, FormFactor.

        :param mem_info: memory information like Size, Speed, FormFactor.
        :param locator: Device Locator of the DIMM.
        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_memory_slots_details(self):
        """
        This function is used to get dmidecode command in linux, wmic command data in windows for all memory slots.

        :return:
        """
        raise NotImplementedError

    @abstractmethod
    def get_snc_node_info(self):
        """
        This function is used to get snc node information

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_dict_off_loc_size(self):
        """
        Function to get the dictionary of all the dimm locations and it's sizes.

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_list_off_locators(self, hbm=False):
        """
        Function to get the list of all the dimm locations.

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_populated_channel_configuration(self, new_locator_size_dict, locator_list):
        """
        Function to get populated dimm information channel wise in a dictionary

        :param new_locator_size_dict: populated dimm location and its sizes in a dict
        :param locator_list: populated dimm locations in a list
        :raise: NotImplementedError
        """
        raise NotImplementedError

    def get_channel_configuration_list(self):
        """
        Function to get channel list that matches the number of configuration channels.

        :return: list_config_population
        """
        channel_config_count = 1
        list_config_population = []
        for letter in string.ascii_uppercase:
            new_key = "CHANNEL {}".format(letter)
            list_config_population.append(new_key)
            if len(self.config) == channel_config_count:
                break
            channel_config_count = channel_config_count + 1

        channel_config1 = dtaf_content_constants.ChannelConfigConstant.CHANNEL_CONFIG_1.split("-")
        channel_config2 = dtaf_content_constants.ChannelConfigConstant.CHANNEL_CONFIG_2.split("-")
        channel_config3 = dtaf_content_constants.ChannelConfigConstant.CHANNEL_CONFIG_3.split("-")
        channel_config4 = dtaf_content_constants.ChannelConfigConstant.CHANNEL_CONFIG_4.split("-")

        dict_config1_channel_population = dict(zip(list_config_population, channel_config1))
        dict_config2_channel_population = dict(zip(list_config_population, channel_config2))
        dict_config3_channel_population = dict(zip(list_config_population, channel_config3))
        dict_config4_channel_population = dict(zip(list_config_population, channel_config4))

        return dict_config1_channel_population, dict_config2_channel_population, \
               dict_config3_channel_population, dict_config4_channel_population

    def get_egs_channel_configuration(self):
        """
        Function to get channel list that matches the number of configuration channels.

        :return: list_config_population
        """
        channel_config_count = 1
        list_config_population = []
        for letter in string.ascii_uppercase:
            new_key = "CHANNEL {}".format(letter)
            list_config_population.append(new_key)
            if len(self.config) == channel_config_count:
                break
            channel_config_count = channel_config_count + 1

        channel_config1 = dtaf_content_constants.ChannelConfigConstant.CHANNEL_CONFIG_5.split("-")

        dict_config1_channel_population = dict(zip(list_config_population, channel_config1))

        return dict_config1_channel_population

    def get_1_dpc_channel_configuration(self):
        """
        Function to get channel list that matches the number of configuration channels.

        :return: config_population
        """
        channel_config_count = 1
        list_config_population = []
        for letter in string.ascii_uppercase:
            new_key = "CHANNEL {}".format(letter)
            list_config_population.append(new_key)
            if len(self.config) == channel_config_count:
                break
            channel_config_count = channel_config_count + 1

        channel_config = dtaf_content_constants.ChannelConfigConstant.CHANNEL_CONFIG_2.split("-")

        dict_config_channel_population = dict(zip(list_config_population, channel_config))
        self._log.debug("channel configuration in dictionary : {}".format(dict_config_channel_population))
        return dict_config_channel_population

    def get_1_dps_channel_configuration(self):
        """
        Function to get channel list that matches the number of configuration channels.

        :return: config_population
        """
        channel_config_count = 1
        list_config_population = []
        for letter in string.ascii_uppercase:
            new_key = "CHANNEL {}".format(letter)
            list_config_population.append(new_key)
            if len(self.config) == channel_config_count:
                break
            channel_config_count = channel_config_count + 1

        channel_config = self._common_content_configuration.get_dimm_population_for_1dps().split("-")

        dict_config_channel_population = dict(zip(list_config_population, channel_config))
        self._log.debug("channel configuration in dictionary : {}".format(dict_config_channel_population))
        return dict_config_channel_population

    def get_2_dpc_channel_configuration(self):
        """
        Function to get channel list that matches the number of configuration channels.

        :return: config_population
        """
        channel_config_count = 1
        list_config_population = []
        for letter in string.ascii_uppercase:
            new_key = "CHANNEL {}".format(letter)
            list_config_population.append(new_key)
            if len(self.config) == channel_config_count:
                break
            channel_config_count = channel_config_count + 1

        channel_config = dtaf_content_constants.ChannelConfigConstant.CHANNEL_CONFIG_4.split("-")

        dict_config_channel_population = dict(zip(list_config_population, channel_config))
        self._log.debug("channel configuration in dictionary : {}".format(dict_config_channel_population))
        return dict_config_channel_population

    def no_dpc_channel_configuration(self):
        """
        Function to get channel list that matches the number of configuration channels.

        :return: config_population
        """
        channel_config_count = 1
        list_config_population = []
        for letter in string.ascii_uppercase:
            new_key = "CHANNEL {}".format(letter)
            list_config_population.append(new_key)
            if len(self.config) == channel_config_count:
                break
            channel_config_count = channel_config_count + 1

        channel_config = dtaf_content_constants.ChannelConfigConstant.CHANNEL_CONFIG_6.split("-")

        dict_config_channel_population = dict(zip(list_config_population, channel_config))
        self._log.debug("channel configuration in dictionary : {}".format(dict_config_channel_population))
        return dict_config_channel_population

    @abstractmethod
    def verify_channel_population(self, dict_config_channel_population):
        """
        Function to verify the pre-condition supported, whether the dimm population is as per the configuration.

        :param dict_config_channel_population: configuration to verify the dimm population
        :raise: NotImplementedError
        """
        raise NotImplementedError

    def get_slot_configuration_list(self):
        """
        Function to get channel list that matches the number of configuration channels.

        :return: list_config_population
        """
        new_locator_size_dict = self.get_dict_off_loc_size_mem_type()
        list_slot_config_population = []

        for dict_slot_keys in new_locator_size_dict:
            list_slot_config_population.append("_".join(dict_slot_keys.split("_")[1::]))

        slot_config1 = dtaf_content_constants.SlotConfigConstant.SLOT_CONFIG_8_by_4.split("-")
        slot_config2 = dtaf_content_constants.SlotConfigConstant.SLOT_CONFIG_8_by_8.split("-")

        dict_config1_slot_population = dict(zip(list_slot_config_population, slot_config1))
        dict_config2_slot_population = dict(zip(list_slot_config_population, slot_config2))

        return dict_config1_slot_population, dict_config2_slot_population

    @abstractmethod
    def get_dict_off_loc_size_mem_type(self):
        """
        Function to get the dictionary of all the dimm locations and it's sizes.

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_populated_slot_configuration(self, new_locator_size_dict, locator_list):
        """
        Function to get populated dimm information channel wise in a dictionary

        :param new_locator_size_dict: populated dimm location and its sizes in a dict
        :param locator_list: populated dimm locations in a list
        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def verify_slot_population(self, dict_config_slot_population):
        """
        Function to verify the pre-condition supported, whether the dimm population is as per the configuration.

        :param dict_config_slot_population: configuration to verify the dimm population
        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def verify_populated_memory_type(self, memory_type):
        """
        verifies the slots are populated with input memory type

        :raise: Exception : Content Exceptions if sut is not populated with input memory type
        """

        raise NotImplementedError

    @abstractmethod
    def get_dram_memory_size_list(self):
        """
        Function to get the list of all the dimm sizes.

        :raise: NotImplementedError
        """

        raise NotImplementedError

    def get_speed_of_installed_dimm(self):
        """
        Function to get all the installed dimm and it's speed.

        :raise: NotImplementedError
        """
        raise NotImplementedError

    def get_configured_memory_speed_of_installed_dimm(self):
        """
        Function to get all the installed dimm and it's configured memory speed.

        :raise: NotImplementedError
        """
        raise NotImplementedError

    def get_installed_hardware_component_information(self, hardware_item):
        """
        Function to get all the installed dimm and it's configured memory speed.

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def verify_dmidecode_installed_or_not(self):
        """
        Function to verify dmidecode tool has been installed on the SUT. If not installed in the SUT ,to install
        dmidecode tool in the SUT.

        :raise: NotImplementedError
        """
        raise NotImplementedError

    def update_ddr_from_dmidecode(self, dict_dmi_decode_from_tool):
        """
        Function is used to update the DDR data based on the manufacturer

        :param dict_dmi_decode_from_tool: dmi decode data in the from of dictionary
        :return: dict_dmi_decode_from_tool
        """
        if OperatingSystems.WINDOWS == self._os.os_type:
            for dict_keys in dict_dmi_decode_from_tool.keys():
                if dict_dmi_decode_from_tool[dict_keys]['DMIType'] == 17:
                    if "No Module Installed" not in dict_dmi_decode_from_tool[dict_keys]["Size"]:
                        if "Intel" in dict_dmi_decode_from_tool[dict_keys]["Manufacturer"]:
                            memory_type = "Intel persistent memory"
                        else:
                            if ProductFamilies.SPR in self._product_family:
                                memory_type = "DDR5"
                            else:
                                memory_type = "DDR4"
                        dict_dmi_decode_from_tool[dict_keys]['Type'] = memory_type

            return dict_dmi_decode_from_tool
        elif OperatingSystems.LINUX == self._os.os_type:
            return dict_dmi_decode_from_tool

    def initialize_ddr_cr_strings(self, dict_dmi_decode_from_tool):
        """
        This function is used to update DDR and CR type names

        :param dict_dmi_decode_from_tool:
        :return:
        """
        for dict_keys in dict_dmi_decode_from_tool.keys():
            if dict_dmi_decode_from_tool[dict_keys]['DMIType'] == 17:
                if "No Module Installed" not in dict_dmi_decode_from_tool[dict_keys]["Size"]:
                    if "Intel" in dict_dmi_decode_from_tool[dict_keys]["Manufacturer"]:
                        if ProductFamilies.SPR in self._product_family:
                            self.CR_STRING = self.NON_VOLATILE
                        else:
                            self.CR_STRING = self.INTEL_PERSISTENT_MEMORY
                    else:
                        if ProductFamilies.SPR in self._product_family:
                            self.DDR_STRING = "DDR5"
                        else:
                            self.DDR_STRING = "DDR4"

    def verify_8_plus_1_population(self):
        """
        Function to get the population of DDR and CR.

        :return: if DDR and CR has 8+1 config
        """
        raise NotImplementedError

    def verify_8_plus_8_population(self):
        """
        Function to get the population of DDR and CR.

        :return: if DDR and CR has 8+8 config
        """
        raise NotImplementedError

    def verify_8_plus_4_population(self):
        """
        Function to get the population of DDR and CR.

        :return: if DDR and CR has 8+4 config
        """
        raise NotImplementedError

    def verify_4_plus_4_population(self):
        """
        Function to get the population of DDR and CR.

        :return: if DDR and CR has 4+4 config
        """
        raise NotImplementedError

    @abstractmethod
    def get_available_disk_space(self):
        """
        This method is to get teh Available Disk Space.

        :return available space
        """
        raise NotImplementedError

    @abstractmethod
    def verify_1dpc_or_2dpc_memory_configuration(self):
        """
        Function to verify SUT has 1DPC or 2DPC memory configuration
        """
        raise NotImplementedError

    @abstractmethod
    def verify_only_hbm_memory_configuration(self):
        """
        Function to verify SUT has 1DPC or 2DPC memory configuration
        """
        raise NotImplementedError

    @abstractmethod
    def get_node_memory_list(self):
        """
        This function is used to get the node memory size
        """
        raise NotImplementedError

    @abstractmethod
    def verify_cache_mode_memory_hbm(self, cluster_mode):
        """
        This method is used to verify Cache mode (2LM) for HBM

        :param cluster_mode : like Quad, SNC4
        """
        raise NotImplementedError

    @abstractmethod
    def verify_flat_mode_memory_hbm(self, cluster_mode):
        """
        This method is used to verify Flat mode (1LM) for HBM

        :param cluster_mode : like Quad, SNC4
        """
        raise NotImplementedError

    @abstractmethod
    def verify_hbm_mode_memory(self, cluster_mode, platform_mode=None):
        """
        This method is used to verify HBM mode

        :param cluster_mode : like Quad, SNC4
        :param platform_mode: Like HBM, FLAT, CACHE
        """
        raise NotImplementedError


class MemoryInfo(object):
    SYSTEM_INFO = "Systeminfo"
    SIZE = "Size"
    SPEED = "Speed"
    FORM_FACTOR = "FormFactor"
    BANK_LABEL = "BankLabel"
    ALL = "All"
    MEMORY_CONFIGURED_SPEED = "Configured Memory Speed"
    MEMORY_CLOCK_SPEED = "Configured Clock Speed"
    LOCATOR = "Locator"


class MemoryWindowsProvider(MemoryProvider):
    """
    Class to provide get total system memory, populated memory slots, locator information functionality
    for windows platform
    """

    def __init__(self, log, cfg_opts, os_obj):
        super(MemoryWindowsProvider, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._os = os_obj
        self._install_collateral = InstallCollateral(log, os_obj, cfg_opts)
        self._dmidecode_path = self._install_collateral.install_dmidecode()

        self.dict_dmi_decode_data = self.get_memory_slots_details()
        self.dict_dmi_decode_data = self.update_ddr_from_dmidecode(self.dict_dmi_decode_data)


    def factory(self, log, cfg_opts, os_obj):
        pass

    def re_initialize_memory_provider(self):
        self.dict_dmi_decode_data = self.get_memory_slots_details()
        self.dict_dmi_decode_data = self.update_ddr_from_dmidecode(self.dict_dmi_decode_data)

    def get_total_system_memory(self):
        """
        This function is used to get the total system memory

        :return system_info_list: total physical memory and available physical memory
        :raise: Runtime error if Total Physical Memory, Available Physical Memory not present in the Systeminfo.
        """
        cmd_result = self._common_content_lib_obj.execute_sut_cmd(MemoryInfo.SYSTEM_INFO, "To get system info",
                                                                  self._command_timeout)

        memory_total_value = re.findall("Total Physical Memory:.*", cmd_result)
        if not memory_total_value:
            raise RuntimeError("Failed to get the Total Memory Value from System Info")
        self._log.info("The Amount of Memory reported by the OS is : {}".format(memory_total_value[0].strip()))

        memory_free_value = re.findall("Available Physical Memory:.*", cmd_result)
        if not memory_free_value:
            raise RuntimeError("Failed to get the Available Physical Memory Value from System Info")
        self._log.info("The Amount of Available Physical Memory reported by the OS is : {}"
                       .format(memory_free_value[0].strip()))
        system_info_list = [memory_total_value[0].strip(), memory_free_value[0].strip()]
        return system_info_list

    def get_total_memory_slots(self):
        """
        This function returns number of memory slots in system.

        :return total_memory_slots: total number of memory slots
        """
        # To get the total number of memory devices in the SUT
        total_memory_slots = int(self._common_content_lib_obj.execute_sut_cmd(
            'dmidecode -t 16 | findstr "Number Of Devices"', "command to get Memory devices count",
            self._command_timeout).split(":")[1].strip(), self._dmidecode_path)

        self._log.info("Total number of memory slots in the SUT are {}".format(total_memory_slots))
        return total_memory_slots

    def get_populated_memory_slots(self):
        """
        This function is used to get the populated memory locator information in the SUT.

        :return dram_memory_location_list: The installed memory locators in the SUT.
        """
        # To get the install DIMM locator in the SUT
        dict_dmi_decode_data = self.get_memory_slots_details()

        dram_memory_location_list = []
        for key in dict_dmi_decode_data.keys():
            if dict_dmi_decode_data[key]['Size'] != "No Module Installed":
                dram_memory_location_list.append(dict_dmi_decode_data[key]['Locator'])

        self._log.info("The populated memory locators in the SUT are : {}".format(dram_memory_location_list))
        return dram_memory_location_list

    def get_memory_slots_details(self):
        """
        This function is used to get the wmic command data in the form of a dictionary

        :return wmic_dict: wmic data in the form of a dictionary
        """

        dmi_cmd = "dmidecode -t 17 > dmi.txt"
        dmi_decode_folder = "dmidecode"
        self._common_content_lib_obj.execute_sut_cmd(dmi_cmd, "get dmi dmidecode -t 17 type output",
                                                     self._command_timeout, cmd_path=self._dmidecode_path)

        self._common_content_lib_obj.delete_testcaseid_folder_in_host(test_case_id=dmi_decode_folder)

        log_path_to_parse = self._common_content_lib_obj.copy_log_files_to_host(
            test_case_id=dmi_decode_folder, sut_log_files_path=self._dmidecode_path, extension=".txt")

        # Check whether the dmi.txt exists in the folder has been done inside the "dmidecode_parser" function.
        dict_dmi_decode_from_tool = self._dmidecode_parser.dmidecode_parser(log_path_to_parse)

        return dict_dmi_decode_from_tool

    def get_locator_info(self, mem_info, locator):
        """
        This function is used to return the information of the DIMM based on the mem_info like Size, Speed, FormFactor.

        :param mem_info: memory information like Size, Speed, FormFactor.
        :param locator: Device Locator of the DIMM.
        :return memory_info_data_dict: based on mem_info it will return the information.
        """
        memory_info_data_dict = {}
        for key in self.dict_dmi_decode_data.keys():
            if self.dict_dmi_decode_data[key]['Size'] != "No Module Installed":
                if self.dict_dmi_decode_data[key]['Locator'] == locator:
                    if mem_info == MemoryInfo.SIZE:
                        memory_info_data_dict[MemoryInfo.SIZE] = self.dict_dmi_decode_data[key]['Size']
                    elif mem_info == MemoryInfo.SPEED:
                        memory_info_data_dict[MemoryInfo.SPEED] = self.dict_dmi_decode_data[key]['Speed']
                    elif mem_info == MemoryInfo.FORM_FACTOR:
                        memory_info_data_dict[MemoryInfo.FORM_FACTOR] = self.dict_dmi_decode_data[key]['Form Factor']
                    elif mem_info == MemoryInfo.BANK_LABEL:
                        memory_info_data_dict['Bank Locator'] = self.dict_dmi_decode_data[key]['Bank Locator']
                    elif mem_info == MemoryInfo.ALL:
                        memory_info_data_dict[MemoryInfo.SIZE] = self.dict_dmi_decode_data[key]['Size']
                        memory_info_data_dict[MemoryInfo.SPEED] = self.dict_dmi_decode_data[key]['Speed']
                        memory_info_data_dict[MemoryInfo.FORM_FACTOR] = self.dict_dmi_decode_data[key]['Form Factor']
                        memory_info_data_dict['Bank Locator'] = self.dict_dmi_decode_data[key]['Bank Locator']
        return memory_info_data_dict

    def get_snc_node_info(self):
        """
        This function is used to get snc node information

        :raise TestNotImplementedError
        """
        if OperatingSystems.WINDOWS == self._os.os_type:
            artifactory_name = ArtifactoryName.DictWindowsTools[ArtifactoryTools.CORE_INFO]
            core_info_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
            if not os.path.isfile(core_info_path):
                log_error = "{} does not exists".format(core_info_path)
                self._log.error(log_error)
                raise IOError(log_error)
            # copying file to Windows SUT in C:\\ from host
            self._os.copy_local_file_to_sut(core_info_path, self.C_DRIVE_PATH)

            command_output = self._common_content_lib_obj.execute_sut_cmd(sut_cmd=self.CORE_INFO_CMD,
                                                                          cmd_str=self.CORE_INFO_CMD,
                                                                          execute_timeout=self._command_timeout,
                                                                          cmd_path=self.C_DRIVE_PATH)
            node_list = re.findall(self.REGEX_FOR_NUMA_NODE,command_output)
        else:
            raise content_exceptions.TestFail("Not implemeted for the OS {}".format(self._os.os_type))
        return node_list

    def get_dict_off_loc_size(self):
        """
        Function to get the dictionary of all the dimm locations and it's sizes.

        :return: new_locator_size_dict
        """
        self.dict_dmi_decode_data = self.get_memory_slots_details()
        new_locator_size_dict = {}
        locator_list = []
        for dict_keys in self.dict_dmi_decode_data.keys():
            new_locator_size_dict[self.dict_dmi_decode_data[dict_keys]["Locator"]] = \
                self.dict_dmi_decode_data[dict_keys]["Size"]
            locator_list.append(self.dict_dmi_decode_data[dict_keys]["Locator"])

        return new_locator_size_dict

    def get_list_off_locators(self, hbm=False):
        """
        Function to get the list of all the dimm locations.

        :return: locator_list
        """
        locator_list = []
        if hbm:
            for dict_keys in self.dict_dmi_decode_data.keys():
                locator_list.append(self.dict_dmi_decode_data[dict_keys]["Locator"])
            self._log.debug("Locators list :{}".format(locator_list))
        else:
            for dict_keys in self.dict_dmi_decode_data.keys():
                if PlatformMode.HBM_MODE not in self.dict_dmi_decode_data[dict_keys]["Locator"]:
                    locator_list.append(self.dict_dmi_decode_data[dict_keys]["Locator"])
        return locator_list

    def get_populated_channel_configuration(self, new_locator_size_dict, locator_list):
        """
        Function to get populated dimm information channel wise in a dictionary

        :param new_locator_size_dict: populated dimm location and its sizes in a dict
        :param locator_list: populated dimm locations in a list
        :return: new_channel_info_dict
        """

        new_channel_info_dict = {}
        cpu_list = []
        for dict_slot_keys in new_locator_size_dict:
            if dict_slot_keys in locator_list:
                new_key = dict_slot_keys.split("_")[-1]
                cpu_list.append(dict_slot_keys.split("_")[0])
                cpu_socket_number = dict_slot_keys.split("_")[0]
                new_key = "CHANNEL " + ''.join([channel for channel in new_key if not channel.isdigit()])
                new_channel_info_dict.setdefault(cpu_socket_number, dict())
                if new_locator_size_dict[dict_slot_keys] != "No Module Installed":
                    new_channel_info_dict[cpu_socket_number][new_key] = \
                        new_channel_info_dict[cpu_socket_number].setdefault(new_key, 0) + 1

                else:
                    new_channel_info_dict[cpu_socket_number][new_key] = \
                        new_channel_info_dict[cpu_socket_number].setdefault(new_key, 0) + 0
        return new_channel_info_dict

    def verify_channel_population(self, dict_config_channel_population):
        """
        Function to verify the pre-condition supported, whether the dimm population is as per the configuration.

        :param dict_config_channel_population: configuration to verify the dimm population
        :return: true if verification is successfull else false
        """

        new_locator_size_dict = self.get_dict_off_loc_size()
        locator_list = self.get_list_off_locators()

        new_channel_info_dict = self.get_populated_channel_configuration(new_locator_size_dict, locator_list)

        dict_config_match = []

        for dic_cpu in new_channel_info_dict:
            for dic_channel in new_channel_info_dict[dic_cpu]:
                if new_channel_info_dict[dic_cpu][dic_channel] != int(dict_config_channel_population[dic_channel]):
                    dict_config_match.append(False)
                else:
                    dict_config_match.append(True)

        if all(dict_config_match):
            self._log.info("The configuration that matches this platform is : {}".
                           format("-".join(dict_config_channel_population.values())))
            self._log.info(
                "Successfully verified the platform configuration for this test case... proceeding further..")

        return all(dict_config_match)

    def get_dict_off_loc_size_mem_type(self):
        """
        Function to get the dictionary of all the dimm locations and it's sizes.

        :return: new_locator_size_mem_type_dict
        """
        self.dict_dmi_decode_data = self.get_memory_slots_details()
        new_locator_size_mem_type_dict = {}
        locator_list = []
        self.initialize_ddr_cr_strings(self.dict_dmi_decode_data)
        for dict_keys in self.dict_dmi_decode_data.keys():
            if "No Module Installed" not in self.dict_dmi_decode_data[dict_keys]["Size"]:
                if "Intel" in self.dict_dmi_decode_data[dict_keys]["Manufacturer"]:
                    memory_type = self.CR_STRING
                else:
                    memory_type = self.DDR_STRING
                new_locator_size_mem_type_dict[self.dict_dmi_decode_data[dict_keys]["Locator"]] = \
                    str(self.dict_dmi_decode_data[dict_keys]["Size"]) + \
                    str("-" + memory_type)
            else:
                new_locator_size_mem_type_dict[self.dict_dmi_decode_data[dict_keys]["Locator"]] = \
                    str(self.dict_dmi_decode_data[dict_keys]["Size"]) + \
                    str("-" + self.dict_dmi_decode_data[dict_keys]["Type"])

            locator_list.append(self.dict_dmi_decode_data[dict_keys]["Locator"])
        self._log.info("Locator, size, memory Type Dictionary ; {}".format(new_locator_size_mem_type_dict))
        return new_locator_size_mem_type_dict

    def get_populated_slot_configuration(self, new_locator_size_dict, locator_list):
        """
        Function to get populated dimm information channel wise in a dictionary

        :param new_locator_size_dict: populated dimm location and its sizes in a dict
        :param locator_list: populated dimm locations in a list
        :return: new_cpu_wise_slot_info_dict_cr_ddr
        """

        new_cpu_wise_slot_info_dict = {}
        new_cpu_wise_slot_info_dict_cr_ddr = {}
        cpu_list = []
        self.initialize_ddr_cr_strings(self.dict_dmi_decode_data)
        for dict_slot_keys in new_locator_size_dict:
            if dict_slot_keys in locator_list:
                cpu_list.append(dict_slot_keys.split("_")[0])
                cpu_socket_number = dict_slot_keys.split("_")[0]
                new_key = "_".join(dict_slot_keys.split("_")[1::])
                new_cpu_wise_slot_info_dict.setdefault(cpu_socket_number, dict())
                new_cpu_wise_slot_info_dict[cpu_socket_number][new_key] = \
                    new_locator_size_dict[dict_slot_keys]

        for dict_cpu in new_cpu_wise_slot_info_dict:
            for new_dict_keys in new_cpu_wise_slot_info_dict[dict_cpu]:
                new_cpu_wise_slot_info_dict_cr_ddr.setdefault(dict_cpu, dict())
                if "No Module Installed" in new_cpu_wise_slot_info_dict[dict_cpu][new_dict_keys]:
                    new_cpu_wise_slot_info_dict_cr_ddr[dict_cpu][new_dict_keys] = \
                        str(new_cpu_wise_slot_info_dict_cr_ddr[dict_cpu].setdefault(new_dict_keys, "")) + "0"
                elif self.DDR_STRING in new_cpu_wise_slot_info_dict[dict_cpu][new_dict_keys]:
                    new_cpu_wise_slot_info_dict_cr_ddr[dict_cpu][new_dict_keys] = \
                        str(new_cpu_wise_slot_info_dict_cr_ddr[dict_cpu].setdefault(new_dict_keys, "")) + "DDR"
                elif self.CR_STRING in new_cpu_wise_slot_info_dict[dict_cpu][new_dict_keys]:
                    new_cpu_wise_slot_info_dict_cr_ddr[dict_cpu][new_dict_keys] = \
                        str(new_cpu_wise_slot_info_dict_cr_ddr[dict_cpu].setdefault(new_dict_keys, "")) + "CR"
        self._log.info("DIMM information : {}".format(new_cpu_wise_slot_info_dict_cr_ddr))
        return new_cpu_wise_slot_info_dict_cr_ddr

    def verify_slot_population(self, dict_config_slot_population):
        """
        Function to verify the pre-condition supported, whether the dimm population is as per the configuration.

        :param dict_config_slot_population: configuration to verify the dimm population
        :return: true if verification is successful else false
        """

        get_dict_off_loc_size_mem_type = self.get_dict_off_loc_size_mem_type()
        locator_list = self.get_list_off_locators()

        new_slot_info_dict = self.get_populated_slot_configuration(get_dict_off_loc_size_mem_type, locator_list)

        config_match_list = {err_type: [] for err_type in new_slot_info_dict.keys()}

        for cpu_socket in new_slot_info_dict:
            for mem_slot in new_slot_info_dict[cpu_socket]:
                if new_slot_info_dict[cpu_socket][mem_slot] != dict_config_slot_population[mem_slot]:
                    config_match_list[cpu_socket].append(False)
                else:
                    config_match_list[cpu_socket].append(True)

        final_match_list = []

        for cpu_socket in config_match_list:

            if all(config_match_list[cpu_socket]):
                final_match_list.append(True)
                self._log.debug("The configuration on {} matches this platform is : {}".
                                format(cpu_socket, "-".join(dict_config_slot_population.values())))
            elif not any(config_match_list[cpu_socket]):
                self._log.debug("{} does not have any DIMM population..".format(cpu_socket))
            else:
                final_match_list.append(False)

        if all(final_match_list):
            self._log.info(
                "Successfully verified the platform slot population for this test case... proceeding further..")

        return all(final_match_list)

    def get_speed_of_installed_dimm(self):
        """
        Function to get all the installed dimm and it's speed.

        :return : speed dictionary
        """
        return self.get_installed_hardware_component_information(MemoryInfo.SPEED)

    def get_configured_memory_speed_of_installed_dimm(self):
        """
        Function to get all the installed dimm and it's configured memory speed.

        :return : Configured Clock Speed dictionary
        """
        return self.get_installed_hardware_component_information(MemoryInfo.MEMORY_CLOCK_SPEED)

    def get_installed_hardware_component_information(self, hardware_component):
        """
        Function to get the hardware information for the installed dimms

        :param: hardware_component
        :return: installed dimm location and hardware_component details
        """
        memory_slot_info_dict = self.get_memory_slots_details()
        hardware_component_info_dict = {}
        for dict_keys in memory_slot_info_dict.keys():
            if memory_slot_info_dict[dict_keys][MemoryInfo.SIZE] != "No Module Installed":
                hardware_component_info_dict[memory_slot_info_dict[dict_keys][MemoryInfo.LOCATOR]] = \
                    memory_slot_info_dict[dict_keys][hardware_component].split()[0]
        self._log.info("Details: {} :\n{}".format(hardware_component, hardware_component_info_dict))
        return hardware_component_info_dict

    def verify_populated_memory_type(self, memory_type):
        """
        verifies the slots are populated with input memory type

        :raise: NotImplementedError
        """

        raise NotImplementedError

    def verify_dmidecode_installed_or_not(self):
        """
        Function to verify dmidecode tool has been installed on the SUT. If not installed in the SUT ,to install
        dmidecode tool in the SUT.

        :return: True
        """
        dmi_decode_exe = "dmidecode.exe"
        dmi_decode_find_command = r"where /R C:\\ " + dmi_decode_exe
        cmd_result = self._os.execute(dmi_decode_find_command, self._command_timeout)
        self._log.debug(cmd_result.stdout)
        self._log.debug(cmd_result.stderr)
        if not cmd_result.stdout:
            self._install_collateral.install_dmidecode()
        else:
            self._log.info("dmidecode already installed in SUT")
        return True

    def get_dram_memory_size_list(self):
        """
        Function to get the list of all the dimm sizes.

        :return: dram_memory_size_list
        """
        self.dict_dmi_decode_data = self.update_ddr_from_dmidecode(self.dict_dmi_decode_data)
        dram_memory_size_list_with_units = []
        dram_memory_size_list = []
        dram_memory_location_list = []
        for key in self.dict_dmi_decode_data.keys():
            if self.dict_dmi_decode_data[key]['Size'] != "No Module Installed":
                if "DDR" in self.dict_dmi_decode_data[key]['Type']:
                    dram_memory_size_list_with_units.append(self.dict_dmi_decode_data[key]['Size'])
                    dram_memory_location_list.append(self.dict_dmi_decode_data[key]['Locator'])

                    self._log.info("The size of DRAM is {} located at {}".format(
                        self.dict_dmi_decode_data[key]['Size'], self.dict_dmi_decode_data[key]['Locator']))
        for each in dram_memory_size_list_with_units:
            if "MB" in each:
                dram_memory_size_list.append(int(int(each.split()[0]) / 1024))
            else:
                dram_memory_size_list.append(int(each.split()[0]))

        self._log.info("DDR Size list in GB : {}".format(dram_memory_size_list))
        return dram_memory_size_list

    def verify_8_plus_1_population(self):
        """
        Function to verify the population of DDR and CR.

        :return: if DDR and CR has 8+1 config
        """
        new_locator_size_dict = self.get_dict_off_loc_size_mem_type()
        list_slot_config_population = []

        for dict_slot_keys in new_locator_size_dict:
            list_slot_config_population.append("_".join(dict_slot_keys.split("_")[1::]))

        slot_config = dtaf_content_constants.SlotConfigConstant.SLOT_CONFIG_8_by_1.split("-")
        self._log.debug("SLOT config : {}".format(slot_config))
        dict_config_slot_population = dict(zip(list_slot_config_population, slot_config))
        self._log.debug("dictionary SLOT config : {}".format(dict_config_slot_population))

        dict_config_match = self.verify_slot_population(dict_config_slot_population)
        if not dict_config_match:
            raise content_exceptions.TestSetupError("System is not have 8 + 1 configuration ..")
        self._log.info("The CPU has the expected 8+1 Configuration ..")
        return True

    def verify_8_plus_8_population(self):
        """
        Function to verify the population of DDR and CR.

        :return: if DDR and CR has 8 + 8 config
        """
        new_locator_size_dict = self.get_dict_off_loc_size_mem_type()
        list_slot_config_population = []

        for dict_slot_keys in new_locator_size_dict:
            list_slot_config_population.append("_".join(dict_slot_keys.split("_")[1::]))

        slot_config = dtaf_content_constants.SlotConfigConstant.SLOT_CONFIG_8_by_8.split("-")
        self._log.info("SLOT config : {}".format(slot_config))
        dict_config_slot_population = dict(zip(list_slot_config_population, slot_config))
        self._log.info("Dict slot Config population : {}".format(dict_config_slot_population))
        dict_config_match = self.verify_slot_population(dict_config_slot_population)
        if not dict_config_match:
            raise content_exceptions.TestSetupError("System does not have 8 + 8 configuration ..")
        self._log.info("The CPU has the expected 8+8 Configuration ..")
        return True

    def verify_8_plus_4_population(self):
        """
        Function to verify the population of DDR and CR.

        :return: if DDR and CR has 8 + 4 config
        """
        new_locator_size_dict = self.get_dict_off_loc_size_mem_type()
        list_slot_config_population = []

        for dict_slot_keys in new_locator_size_dict:
            list_slot_config_population.append("_".join(dict_slot_keys.split("_")[1::]))

        slot_config = dtaf_content_constants.SlotConfigConstant.SLOT_CONFIG_8_by_4.split("-")
        self._log.info("SLOT config : {}".format(slot_config))
        dict_config_slot_population = dict(zip(list_slot_config_population, slot_config))
        self._log.info("Dict slot Config population : {}".format(dict_config_slot_population))
        dict_config_match = self.verify_slot_population(dict_config_slot_population)
        if not dict_config_match:
            raise content_exceptions.TestSetupError("System does not have 8 + 4 configuration ..")
        self._log.info("The CPU has the expected 8+4 Configuration ..")
        return True

    def verify_4_plus_4_population(self):
        """
        Function to verify the population of DDR and CR.

        :return: if DDR and CR has 4 + 4 config
        """
        new_locator_size_dict = self.get_dict_off_loc_size_mem_type()
        list_slot_config_population = []

        for dict_slot_keys in new_locator_size_dict:
            list_slot_config_population.append("_".join(dict_slot_keys.split("_")[1::]))

        slot_config = dtaf_content_constants.SlotConfigConstant.SLOT_CONFIG_4_by_4.split("-")
        self._log.info("SLOT config : {}".format(slot_config))
        dict_config_slot_population = dict(zip(list_slot_config_population, slot_config))
        self._log.info("Dict slot Config population : {}".format(dict_config_slot_population))
        dict_config_match = self.verify_slot_population(dict_config_slot_population)
        if not dict_config_match:
            raise content_exceptions.TestSetupError("System does not have 4 + 4 configuration ..")
        self._log.info("The CPU has the expected 4+4 Configuration ..")
        return True

    def verify_1dpc_or_2dpc_memory_configuration(self):
        """
        Function to verify SUT has 1DPC or 2DPC memory configuration
        """
        dict_config_channel_population = self.get_1_dpc_channel_configuration()

        # Verification between platform configuration and golden configuration info.
        dict_config_match = self.verify_channel_population(dict_config_channel_population)

        if not dict_config_match:
            self._log.info("SUT do not have 1DPC memory configuration, check for 2DPC ...")
            dict_config_channel_population = self.get_2_dpc_channel_configuration()

            # Verification between platform configuration and golden configuration info.
            config_match = self.verify_channel_population(dict_config_channel_population)
            if not config_match:
                raise content_exceptions.TestFail("System do not have 1DPC or 2DPC memory configuration ..")
            self._log.info("SUT has 2DPC memory configuration ...")
            return True
        self._log.info("SUT has 1 DPC memory configuration ...")
        return True

    def verify_only_hbm_memory_configuration(self):
        """
        Function to verify SUT has 1DPC or 2DPC memory configuration
        """
        dict_config_channel_population = self.no_dpc_channel_configuration()

        # Verification between platform configuration and golden configuration info.
        dict_config_match = self.verify_channel_population(dict_config_channel_population)

        if not dict_config_match:
            raise content_exceptions.TestFail("SUT does have DRR memory configuration, Please remove "
                                              "all the DDR memory for HBM mode ...")
        return True

    def get_node_memory_list(self, platform_mode=None):
        """
        This function is used to get the node memory size
        :param platform_mode: Like HBM, FLAT, CACHE
        :return node_memory_info dict
        """
        install_memory = self._windows_common_lib.task_manager_wmic_mem_get(task_option="BankLabel,Capacity",
                                                                            list_option=True)
        node_mem_info = {}
        cnt = 0
        if platform_mode == PlatformMode.HBM_MODE:
            for item in install_memory:
                if item.lower().startswith('bank'):
                    value = item.split()[-1]
                    if value.isdigit():
                        node = item.split()[0] + str(cnt)
                        if node not in node_mem_info:
                            node_mem_info[node] = (int(value) / (1024 * 1024 * 1024))
                        else:
                            node_mem_info[node] += (int(value) / (1024 * 1024 * 1024))
                        cnt += 1
        else:
            for item in install_memory:
                if item.lower().startswith('node'):
                    value = item.split()[-1]
                    if value.isdigit():
                        node = item.split()[0] + " " + item.split()[1]
                        if node not in node_mem_info:
                            node_mem_info[node] = (int(value) / (1024 * 1024 * 1024))
                        else:
                            node_mem_info[node] += (int(value) / (1024 * 1024 * 1024))
        return node_mem_info

    def verify_cache_mode_memory_hbm(self, cluster_mode):
        """
        This method is used to verify Cache mode (2LM) for HBM

        :param cluster_mode : like Quad, SNC4
        """
        ddr_memory_config = self._common_content_configuration.memory_bios_post_memory_capacity()
        self._log.info("DDR memory from config xml is : {} GB".format(ddr_memory_config))
        variance = float(self._common_content_configuration.get_memory_variance_percent())
        self._log.info("Variance from config xml is : {}".format(variance))
        self._cpu_info_provider.populate_cpu_info()
        socket_present = int(self._cpu_info_provider.get_number_of_sockets())
        self._log.info("Sockets in the SUT : {}".format(socket_present))
        node_memory_list_gb = self.get_node_memory_list()
        self._log.info("Node Memory list in GB is : {}".format(node_memory_list_gb))

        ddr_memory_config_variance = ddr_memory_config - (ddr_memory_config * variance)
        self._log.info("DDR memory with Variance : {} GB".format(ddr_memory_config_variance))
        # DDR connected to one socket
        one_socket_memory_config = float(ddr_memory_config / socket_present)
        self._log.info("DDR connected to 1 socket from config is : {}".format(one_socket_memory_config))
        one_node_memory_variance = None
        one_node_memory_config = None
        if cluster_mode == MemoryClusterConstants.QUAD_STRING:
            # For Cache mode (2LM), Quad, DDR for each node is : memory populated per socket
            one_node_memory_config = one_socket_memory_config
            one_node_memory_variance = one_node_memory_config - (one_node_memory_config * variance)

        elif cluster_mode == MemoryClusterConstants.SNC4_STRING:
            # For Cache mode (2LM), SNC4 DDR for each node is : 1/4 of memory populated per socket
            one_node_memory_config = (1 / 4) * one_socket_memory_config
            one_node_memory_variance = one_node_memory_config - (one_node_memory_config * variance)

        self._log.info("Node memory from config for Cache (2LM) with {} is : {}".format(cluster_mode,
                                                                                        one_node_memory_config))
        self._log.info("Node memory from config for Cache (2LM) with {} with variance is : {}".format(
            cluster_mode, one_node_memory_variance))
        for each_node_memory_gb in node_memory_list_gb.values():
            if each_node_memory_gb < one_node_memory_variance or each_node_memory_gb > one_node_memory_config:
                raise content_exceptions.TestFail(
                    "Node memory from OS is : {} and Node memory from config with "
                    "variance is : {}".format(each_node_memory_gb, one_node_memory_variance))

        self._log.info("Node memory matched for Cache (2LM) with {}".format(cluster_mode))

    def verify_flat_mode_memory_hbm(self, cluster_mode):
        """
        This method is used to verify Flat mode (1LM) for HBM

        :param cluster_mode : like Quad, SNC4
        """
        ddr_memory_config = self._common_content_configuration.memory_bios_post_memory_capacity()
        self._log.info("DDR memory from config xml is : {} GB".format(ddr_memory_config))
        variance = float(self._common_content_configuration.get_memory_variance_percent())
        self._log.info("Variance from config xml is : {}".format(variance))
        self._cpu_info_provider.populate_cpu_info()
        socket_present = int(self._cpu_info_provider.get_number_of_sockets())
        self._log.info("Sockets in the SUT : {}".format(socket_present))
        node_memory_list_gb = self.get_node_memory_list()
        self._log.info("Node Memory list in GB is : {}".format(node_memory_list_gb))

        ddr_memory_config_variance = ddr_memory_config - (ddr_memory_config * variance)
        self._log.info("DDR memory with Variance : {} GB".format(ddr_memory_config_variance))
        # DDR connected to one socket
        one_socket_memory_config = float(ddr_memory_config / socket_present)
        self._log.info("DDR connected to 1 socket from config is : {}".format(one_socket_memory_config))
        one_node_memory_variance = None
        one_node_memory_config = None
        if cluster_mode == MemoryClusterConstants.QUAD_STRING:
            # For Flat mode (1LM), Quad, DDR for each node is : memory populated per socket
            one_node_memory_config = one_socket_memory_config
            one_node_memory_variance = one_node_memory_config - (one_node_memory_config * variance)

        elif cluster_mode == MemoryClusterConstants.SNC4_STRING:
            # For Flat mode (1LM), SNC4 DDR for each node is : 1/4 of memory populated per socket
            one_node_memory_config = (1 / 4) * one_socket_memory_config
            one_node_memory_variance = one_node_memory_config - (one_node_memory_config * variance)

        self._log.info("Node memory from config for Flat (1LM) with {} is : {}".format(cluster_mode,
                                                                                        one_node_memory_config))
        self._log.info("Node memory from config for Flat (1LM) with {} with variance is : {}".format(
            cluster_mode, one_node_memory_variance))
        for each_node_memory_gb in node_memory_list_gb.values():
            if each_node_memory_gb < one_node_memory_variance or each_node_memory_gb > one_node_memory_config:
                raise content_exceptions.TestFail(
                    "Node memory from OS is : {} and Node memory from config with "
                    "variance is : {}".format(each_node_memory_gb, one_node_memory_variance))

        self._log.info("Node memory matched for Flat (1LM) with {}".format(cluster_mode))

    def verify_hbm_mode_memory(self, cluster_mode, platform_mode=None):
        """
        This method is used to verify HBM mode

        :param cluster_mode : like Quad, SNC4
        :param platform_mode: Like HBM, FLAT, CACHE
        """
        node_memory_list_gb = self.get_node_memory_list(platform_mode)
        self._log.info("Node Memory list in GB is : {}".format(node_memory_list_gb))
        variance = float(self._common_content_configuration.get_memory_variance_percent())
        self._log.info("Variance from config xml is : {}".format(variance))
        self._cpu_info_provider.populate_cpu_info()
        socket_present = int(self._cpu_info_provider.get_number_of_sockets())
        self._log.info("Sockets in the SUT : {}".format(socket_present))
        one_node_hbm_memory_variance = None
        one_node_hbm_memory_config = None

        if platform_mode == PlatformMode.HBM_MODE and cluster_mode == MemoryClusterConstants.QUAD_STRING:
            # For hbm mode (1LM)
            one_node_hbm_memory_config = self._common_content_configuration.get_hbm_memory_per_socket_config()
            one_node_hbm_memory_variance = one_node_hbm_memory_config - (one_node_hbm_memory_config * variance)
        elif platform_mode == PlatformMode.HBM_MODE and cluster_mode == MemoryClusterConstants.SNC4_STRING:
            one_node_hbm_memory_config = int(self._common_content_configuration.get_hbm_memory_per_socket_config() / 4)
            one_node_hbm_memory_variance = int(one_node_hbm_memory_config - (one_node_hbm_memory_config * variance))
        elif cluster_mode == MemoryClusterConstants.QUAD_STRING:
            one_node_hbm_memory_config = self._common_content_configuration.get_hbm_memory_per_socket_config()
            one_node_hbm_memory_variance = int(one_node_hbm_memory_config - (one_node_hbm_memory_config * variance))
        elif cluster_mode == MemoryClusterConstants.SNC4_STRING:
            # For hbm mode (1LM)
            one_node_hbm_memory_config = self._common_content_configuration.get_hbm_memory_per_socket_config()
            one_node_hbm_memory_variance = int(one_node_hbm_memory_config - (one_node_hbm_memory_config * variance))
        else:
            raise content_exceptions.TestFail("None of the configuration is matched.. exiting.. Please check the "
                                              "mode placed")

        # To check HBM Nodes Size
        for each_hbm_node_gb in node_memory_list_gb.values():
            if each_hbm_node_gb < one_node_hbm_memory_variance or each_hbm_node_gb > one_node_hbm_memory_config:
                raise content_exceptions.TestFail("Node memory from OS is : {} and Node memory from config with "
                                                  "variance is : {}".format(each_hbm_node_gb,
                                                                            one_node_hbm_memory_variance))
        self._log.info("Node memory matched for HBM (1LM) with {}".format(cluster_mode))

    def get_available_disk_space(self):
        """
        This method is to get teh Available Disk Space.

        :return available space
        """
        raise NotImplementedError

    class MemoryInfo(object):
        SYSTEM_INFO = "Systeminfo"
        SIZE = "Size"
        SPEED = "Speed"
        FORM_FACTOR = "FormFactor"
        BANK_LABEL = "BankLabel"
        ALL = "All"
        MEMORY_CONFIGURED_SPEED = "Configured Memory Speed"
        MEMORY_CLOCK_SPEED = "Configured Clock Speed"
        LOCATOR = "Locator"


class MemoryLinuxProvider(MemoryProvider):
    """
    Class to provide get total system memory, populated memory slots, locator information functionality
    for linux platform
    """

    MEM_REGEX = r"Mem:\s*[0-9]*"
    PACKAGE_NUMACTL = "numactl"
    PACKAGE_DAXCTL = "daxctl"

    def __init__(self, log, cfg_opts, os_obj):
        super(MemoryLinuxProvider, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._os = os_obj
        self._install_collateral = InstallCollateral(log, os_obj, cfg_opts)
        self.dict_dmi_decode_data = self.get_memory_slots_details()

    def factory(self, log, cfg_opts, os_obj):
        pass

    def re_initialize_memory_provider(self):
        """
        This method is to re-initialise the memory provider.
        """
        self.dict_dmi_decode_data = self.get_memory_slots_details()

    def get_total_system_memory(self):
        """
        This function is used to get the total system memory

        :return mem_total_val: total system memory
        :raise : RuntimeError
        """
        get_memory_info = self._common_content_lib_obj.execute_sut_cmd("free -m", "System Information",
                                                                       self._command_timeout, self.LINUX_USR_ROOT_PATH)
        if get_memory_info != "":
            self._log.info("Displaying System Memory information... \n {}".format(get_memory_info))

        mem_total_val = None
        if re.search(self.MEM_REGEX, get_memory_info):
            mem_match_data = re.findall(self.MEM_REGEX, get_memory_info)
            mem_total_val = mem_match_data[0].split(":")[1].strip()
        if not mem_total_val:
            err_msg = "Fail to fetch the total memory value"
            self._log.error(err_msg)
            raise RuntimeError(err_msg)
        self._log.info("Successfully got the total memory value from OS: {} MB".format(mem_total_val))
        return float(mem_total_val)

    def get_total_memory_slots(self):
        """
        This function returns number of memory slots in system.

        :return total_memory_slots: total number of memory slots
        """
        command_number_of_devices = "dmidecode -t 16 | grep 'Number Of Devices'"
        cmd_res = self._common_content_lib_obj.execute_sut_cmd(
            command_number_of_devices, "command to get number of devices",
            self._command_timeout, self.LINUX_USR_ROOT_PATH)

        total_memory_slots = int(cmd_res.split(':')[1])
        self._log.info("Total number of memory slots in the SUT are {}".format(total_memory_slots))
        return total_memory_slots

    def get_populated_memory_slots(self):
        """
        This function is used to get the populated memory locator information in the SUT

        :return dram_memory_location_list: The installed memory locators in the SUT.
        """
        dram_memory_location_list = []
        for key in self.dict_dmi_decode_data.keys():
            if self.dict_dmi_decode_data[key]['Size'] != "No Module Installed":
                dram_memory_location_list.append(self.dict_dmi_decode_data[key]['Locator'])

        self._log.info("The populated memory locators in the SUT are : {}".format(dram_memory_location_list))
        return dram_memory_location_list

    def get_locator_info(self, mem_info, locator):
        """
        This function is used to return the information of the DIMM based on the mem_info like Size, Speed, FormFactor.

        :param mem_info: memory information like Size, Speed, FormFactor.
        :param locator: Device Locator of the DIMM
        :return memory_info_data_dict: based on mem_info it will return the information.
        """

        memory_info_data_dict = {}
        for key in self.dict_dmi_decode_data.keys():
            if self.dict_dmi_decode_data[key]['Size'] != "No Module Installed":
                if self.dict_dmi_decode_data[key]['Locator'] == locator:
                    if mem_info == MemoryInfo.SIZE:
                        memory_info_data_dict[MemoryInfo.SIZE] = self.dict_dmi_decode_data[key]['Size']
                    elif mem_info == MemoryInfo.SPEED:
                        memory_info_data_dict[MemoryInfo.SPEED] = self.dict_dmi_decode_data[key]['Speed']
                    elif mem_info == MemoryInfo.FORM_FACTOR:
                        memory_info_data_dict[MemoryInfo.FORM_FACTOR] = self.dict_dmi_decode_data[key]['Form Factor']
                    elif mem_info == MemoryInfo.BANK_LABEL:
                        memory_info_data_dict['Bank Locator'] = self.dict_dmi_decode_data[key]['Bank Locator']
                    elif mem_info == MemoryInfo.ALL:
                        memory_info_data_dict[MemoryInfo.SIZE] = self.dict_dmi_decode_data[key]['Size']
                        memory_info_data_dict[MemoryInfo.SPEED] = self.dict_dmi_decode_data[key]['Speed']
                        memory_info_data_dict[MemoryInfo.FORM_FACTOR] = self.dict_dmi_decode_data[key]['Form Factor']
                        memory_info_data_dict['Bank Locator'] = self.dict_dmi_decode_data[key]['Bank Locator']
        return memory_info_data_dict

    def get_memory_slots_details(self):
        """
         This function is used to get the dmidecode command data in the form of a dictionary

        :return dict_dmi_decode_from_tool: dmi decode data in the from of dictionary
        """
        dmi_cmd = "dmidecode -t 17 > dmi.txt"
        dmi_decode_folder = "dmidecode"
        self._common_content_lib_obj.execute_sut_cmd(dmi_cmd, "get dmi dmidecode -t 17 type output",
                                                     self._command_timeout, cmd_path=self.LINUX_USR_ROOT_PATH)

        self._common_content_lib_obj.delete_testcaseid_folder_in_host(test_case_id=dmi_decode_folder)

        log_path_to_parse = self._common_content_lib_obj.copy_log_files_to_host(
            test_case_id=dmi_decode_folder, sut_log_files_path=self.LINUX_USR_ROOT_PATH, extension=".txt")

        # Check whether the dmi.txt exists in the folder has been done inside the "dmidecode_parser" function.
        dict_dmi_decode_from_tool = self._dmidecode_parser.dmidecode_parser(log_path_to_parse)

        return dict_dmi_decode_from_tool

    def get_snc_node_info(self):
        """
        This function is used to get snc node information.

        :return node_list
        """

        node_list = self._common_content_lib_obj.execute_sut_cmd("ls -d /sys/devices/system/node/node*",
                                                                 "Fetch number of nodes", self._command_timeout). \
            strip().split("\n")

        self._log.debug("The node list : {}".format(node_list))

        return node_list

    def get_dict_off_loc_size(self):
        """
        Function to get the dictionary of all the dimm locations and it's sizes.

        :return: new_locator_size_dict
        """
        new_locator_size_dict = {}
        locator_list = []
        for dict_keys in self.dict_dmi_decode_data.keys():
            new_locator_size_dict[self.dict_dmi_decode_data[dict_keys]["Locator"]] = \
                self.dict_dmi_decode_data[dict_keys]["Size"]
            locator_list.append(self.dict_dmi_decode_data[dict_keys]["Locator"])
        self._log.debug("Dictionary of locator and size : {}".format(new_locator_size_dict))
        return new_locator_size_dict

    def get_list_off_locators(self, hbm=False):
        """
        Function to get the list of all the dimm locations.

        :return: locator_list
        """
        locator_list = []
        if hbm:
            for dict_keys in self.dict_dmi_decode_data.keys():
                locator_list.append(self.dict_dmi_decode_data[dict_keys]["Locator"])
            self._log.debug("Locators list :{}".format(locator_list))
        else:
            for dict_keys in self.dict_dmi_decode_data.keys():
                if PlatformMode.HBM_MODE not in self.dict_dmi_decode_data[dict_keys]["Locator"]:
                    locator_list.append(self.dict_dmi_decode_data[dict_keys]["Locator"])
        return locator_list

    def get_populated_channel_configuration(self, new_locator_size_dict, locator_list):
        """
        Function to get populated dimm information channel wise in a dictionary

        :param new_locator_size_dict: populated dimm location and its sizes in a dict
        :param locator_list: populated dimm locations in a list
        :return: new_channel_info_dict
        """

        new_channel_info_dict = {}
        cpu_list = []
        for dict_slot_keys in new_locator_size_dict:
            if dict_slot_keys in locator_list:
                new_key = dict_slot_keys.split("_")[-1]
                cpu_list.append(dict_slot_keys.split("_")[0])
                cpu_socket_number = dict_slot_keys.split("_")[0]
                new_key = "CHANNEL " + ''.join([channel for channel in new_key if not channel.isdigit()])
                new_channel_info_dict.setdefault(cpu_socket_number, dict())
                if new_locator_size_dict[dict_slot_keys] != "No Module Installed":
                    new_channel_info_dict[cpu_socket_number][new_key] = \
                        new_channel_info_dict[cpu_socket_number].setdefault(new_key, 0) + 1

                else:
                    new_channel_info_dict[cpu_socket_number][new_key] = \
                        new_channel_info_dict[cpu_socket_number].setdefault(new_key, 0) + 0
        self._log.debug("channel information : {}".format(new_channel_info_dict))
        return new_channel_info_dict

    def verify_channel_population(self, dict_config_channel_population):
        """
        Function to verify the pre-condition supported, whether the dimm population is as per the configuration.

        :param dict_config_channel_population: configuration to verify the dimm population
        :return: true if verification is successful else false
        """

        new_locator_size_dict = self.get_dict_off_loc_size()

        locator_list = self.get_list_off_locators()

        new_channel_info_dict = self.get_populated_channel_configuration(new_locator_size_dict, locator_list)

        dict_config_match = []

        for dic_cpu in new_channel_info_dict:
            for dic_channel in new_channel_info_dict[dic_cpu]:
                if new_channel_info_dict[dic_cpu][dic_channel] != int(dict_config_channel_population[dic_channel]):
                    dict_config_match.append(False)
                else:
                    dict_config_match.append(True)

        if all(dict_config_match):
            self._log.info("The configuration that matches this platform is : {}".
                           format("-".join(dict_config_channel_population.values())))
            self._log.info(
                "Successfully verified the platform configuration for this test case... proceeding further..")

        return all(dict_config_match)

    def get_dict_off_loc_size_mem_type(self):
        """
        Function to get the dictionary of all the dimm locations and it's sizes.

        :return: new_locator_size_mem_type_dict
        """
        new_locator_size_mem_type_dict = {}
        locator_list = []
        for dict_keys in self.dict_dmi_decode_data.keys():
            new_locator_size_mem_type_dict[self.dict_dmi_decode_data[dict_keys]["Locator"]] = \
                str(self.dict_dmi_decode_data[dict_keys]["Size"]) + \
                str("-" + self.dict_dmi_decode_data[dict_keys]["Type"])
            locator_list.append(self.dict_dmi_decode_data[dict_keys]["Locator"])

        return new_locator_size_mem_type_dict

    def get_populated_slot_configuration(self, new_locator_size_dict, locator_list):
        """
        Function to get populated dimm information channel wise in a dictionary

        :param new_locator_size_dict: populated dimm location and its sizes in a dict
        :param locator_list: populated dimm locations in a list
        :return: new_cpu_wise_slot_info_dict_cr_ddr
        """

        new_cpu_wise_slot_info_dict = {}
        new_cpu_wise_slot_info_dict_cr_ddr = {}
        cpu_list = []
        self.initialize_ddr_cr_strings(self.dict_dmi_decode_data)
        for dict_slot_keys in new_locator_size_dict:
            if dict_slot_keys in locator_list:
                cpu_list.append(dict_slot_keys.split("_")[0])
                cpu_socket_number = dict_slot_keys.split("_")[0]
                new_key = "_".join(dict_slot_keys.split("_")[1::])
                new_cpu_wise_slot_info_dict.setdefault(cpu_socket_number, dict())
                new_cpu_wise_slot_info_dict[cpu_socket_number][new_key] = \
                    new_locator_size_dict[dict_slot_keys]

        for dict_cpu in new_cpu_wise_slot_info_dict:
            for new_dict_keys in new_cpu_wise_slot_info_dict[dict_cpu]:
                new_cpu_wise_slot_info_dict_cr_ddr.setdefault(dict_cpu, dict())
                if "No Module Installed" in new_cpu_wise_slot_info_dict[dict_cpu][new_dict_keys]:
                    new_cpu_wise_slot_info_dict_cr_ddr[dict_cpu][new_dict_keys] = \
                        str(new_cpu_wise_slot_info_dict_cr_ddr[dict_cpu].setdefault(new_dict_keys, "")) + "0"
                elif self.DDR_STRING in new_cpu_wise_slot_info_dict[dict_cpu][new_dict_keys]:
                    new_cpu_wise_slot_info_dict_cr_ddr[dict_cpu][new_dict_keys] = \
                        str(new_cpu_wise_slot_info_dict_cr_ddr[dict_cpu].setdefault(new_dict_keys, "")) + "DDR"
                elif self.CR_STRING in new_cpu_wise_slot_info_dict[dict_cpu][new_dict_keys]:
                    new_cpu_wise_slot_info_dict_cr_ddr[dict_cpu][new_dict_keys] = \
                        str(new_cpu_wise_slot_info_dict_cr_ddr[dict_cpu].setdefault(new_dict_keys, "")) + "CR"
        self._log.info("DIMM information : {}".format(new_cpu_wise_slot_info_dict_cr_ddr))
        return new_cpu_wise_slot_info_dict_cr_ddr

    def verify_slot_population(self, dict_config_slot_population):
        """
        Function to verify the pre-condition supported, whether the dimm population is as per the configuration.

        :param dict_config_slot_population: configuration to verify the dimm population
        :return: true if verification is successful else false
        """

        get_dict_off_loc_size_mem_type = self.get_dict_off_loc_size_mem_type()
        locator_list = self.get_list_off_locators()

        new_slot_info_dict = self.get_populated_slot_configuration(get_dict_off_loc_size_mem_type, locator_list)

        config_match_list = {err_type: [] for err_type in new_slot_info_dict.keys()}

        for cpu_socket in new_slot_info_dict:
            for mem_slot in new_slot_info_dict[cpu_socket]:
                if new_slot_info_dict[cpu_socket][mem_slot] != dict_config_slot_population[mem_slot]:
                    config_match_list[cpu_socket].append(False)
                else:
                    config_match_list[cpu_socket].append(True)

        final_match_list = []

        for cpu_socket in config_match_list:

            if all(config_match_list[cpu_socket]):
                final_match_list.append(True)
                self._log.debug("The configuration on {} matches this platform is : {}".
                                format(cpu_socket, "-".join(dict_config_slot_population.values())))
            elif not any(config_match_list[cpu_socket]):
                self._log.debug("{} does not have any DIMM population..".format(cpu_socket))
            else:
                final_match_list.append(False)

        if all(final_match_list):
            self._log.info(
                "Successfully verified the platform slot population for this test case... proceeding further..")

        return all(final_match_list)

    def get_speed_of_installed_dimm(self):
        """
        Function to get all the installed dimm and it's speed.

        :return: speed_dict
        """
        return self.get_installed_hardware_component_information(MemoryInfo.SPEED)

    def get_configured_memory_speed_of_installed_dimm(self):
        """
        Function to get all the installed dimm locations and it's configured memory speed.

        :return: configured_memory_speed_dict
        """
        return self.get_installed_hardware_component_information(MemoryInfo.MEMORY_CONFIGURED_SPEED)

    def get_installed_hardware_component_information(self, hardware_component):
        """
        Function to get the hardware information for the installed dimms

        :param: hardware_component
        :return: installed dimm location and hardware_component details
        """
        memory_slot_info_dict = self.get_memory_slots_details()
        hardware_component_info_dict = {}
        for dict_keys in memory_slot_info_dict.keys():
            if memory_slot_info_dict[dict_keys][MemoryInfo.SIZE] != "No Module Installed":
                hardware_component_info_dict[memory_slot_info_dict[dict_keys][MemoryInfo.LOCATOR]] = \
                    memory_slot_info_dict[dict_keys][hardware_component].split()[0]
        self._log.info("Details: {} :\n{}".format(hardware_component, hardware_component_info_dict))
        return hardware_component_info_dict

    def verify_dmidecode_installed_or_not(self):
        """
        Function to verify dmidecode tool has been installed on the SUT. If not installed in the SUT ,to install
        dmidecode tool in the SUT.

        :return: True
        """
        dmi_decode_install_cmd = "yum install -y dmidecode"
        dmi_decode_cmd_result = self._os.execute("dmidecode", self._command_timeout)
        if dmi_decode_cmd_result.cmd_failed():
            self._log.info("dmidecode not installed in SUT")
            self._common_content_lib_obj.execute_sut_cmd(
                dmi_decode_install_cmd, "dmi decode installations ", self._command_timeout,
                cmd_path=self.LINUX_USR_ROOT_PATH)
        else:
            self._log.info("dmidecode already installed in SUT")
        return True

    def verify_populated_memory_type(self, memory_type):
        """
        verifies the slots are populated with input memory type

        :raise: Exception : Content Exceptions if sut is not populated with input memory type
        """
        memory_count = 0
        type_str = "Type"
        self._log.info("Verify all the slot of the sut is connected with {}".format(memory_type))
        memory_slot_details = self.get_memory_slots_details()
        self._log.debug("memory slot details {}".format(memory_slot_details))
        for key_tag, mem_type in memory_slot_details.items():
            if mem_type.get(type_str) == memory_type:
                memory_count += 1
        if memory_count != len(memory_slot_details):
            raise content_exceptions.TestFail("All the slots of the sut memory is not connected "
                                              "with {}".format(memory_type))
        self._log.info("All the slots of the sut memory is connected with {}".format(memory_type))

    def get_dram_memory_size_list(self):
        """
        Function to get the list of all the dimm sizes.

        :return: dram_memory_size_list
        """
        dram_memory_size_list_with_gb = []
        dram_memory_location_list = []
        for key in self.dict_dmi_decode_data.keys():
            if self.dict_dmi_decode_data[key]['Size'] != "No Module Installed":
                if self.dict_dmi_decode_data[key]['Memory Technology'] == "DRAM":
                    dram_memory_size_list_with_gb.append(self.dict_dmi_decode_data[key]['Volatile Size'])
                    dram_memory_location_list.append(self.dict_dmi_decode_data[key]['Locator'])

                    self._log.info("The size of DRAM is {} located at {}".format(
                        self.dict_dmi_decode_data[key]['Volatile Size'], self.dict_dmi_decode_data[key]['Locator']))

        # Remove the GB and take only numeric value (size) of dram
        dram_memory_size_list = list(map(lambda sub: int(''.join([ele for ele in sub if ele.isnumeric()])),
                                         dram_memory_size_list_with_gb))

        return dram_memory_size_list

    def verify_8_plus_1_population(self):
        """
        Function to get the population of DDR and CR.

        :return: if DDR and CR has 8+1 config
        """

        new_locator_size_dict = self.get_dict_off_loc_size_mem_type()
        list_slot_config_population = []

        for dict_slot_keys in new_locator_size_dict:
            list_slot_config_population.append("_".join(dict_slot_keys.split("_")[1::]))

        slot_config = dtaf_content_constants.SlotConfigConstant.SLOT_CONFIG_8_by_1.split("-")
        self._log.debug("SLOT config : {}".format(slot_config))
        dict_config_slot_population = dict(zip(list_slot_config_population, slot_config))
        self._log.debug("dictionary SLOT config : {}".format(dict_config_slot_population))

        dict_config_match = self.verify_slot_population(dict_config_slot_population)
        if not dict_config_match:
            raise content_exceptions.TestSetupError("System is not have 8 + 1 configuration ..")
        self._log.info("The CPU has the expected 8+1 Configuration ..")
        return True

    def verify_8_plus_8_population(self):
        """
        Function to verify the population of DDR and CR.

        :return: if DDR and CR has 8 + 8 config
        """
        new_locator_size_dict = self.get_dict_off_loc_size_mem_type()
        list_slot_config_population = []

        for dict_slot_keys in new_locator_size_dict:
            list_slot_config_population.append("_".join(dict_slot_keys.split("_")[1::]))

        slot_config = dtaf_content_constants.SlotConfigConstant.SLOT_CONFIG_8_by_8.split("-")
        self._log.info("SLOT config : {}".format(slot_config))
        dict_config_slot_population = dict(zip(list_slot_config_population, slot_config))
        self._log.info("Dict slot Config population : {}".format(dict_config_slot_population))
        dict_config_match = self.verify_slot_population(dict_config_slot_population)
        if not dict_config_match:
            raise content_exceptions.TestSetupError("System does not have 8 + 8 configuration ..")
        self._log.info("The CPU has the expected 8+8 memory Configuration ..")
        return True

    def verify_8_plus_4_population(self):
        """
        Function to verify the population of DDR and CR.

        :return: if DDR and CR has 8 + 4 config
        """
        new_locator_size_dict = self.get_dict_off_loc_size_mem_type()
        list_slot_config_population = []

        for dict_slot_keys in new_locator_size_dict:
            list_slot_config_population.append("_".join(dict_slot_keys.split("_")[1::]))

        slot_config = dtaf_content_constants.SlotConfigConstant.SLOT_CONFIG_8_by_4.split("-")
        self._log.info("SLOT config : {}".format(slot_config))
        dict_config_slot_population = dict(zip(list_slot_config_population, slot_config))
        self._log.info("Dict slot Config population : {}".format(dict_config_slot_population))
        dict_config_match = self.verify_slot_population(dict_config_slot_population)
        if not dict_config_match:
            raise content_exceptions.TestSetupError("System does not have 8 + 4 configuration ..")
        self._log.info("The CPU has the expected 8+4 memory Configuration ..")
        return True

    def verify_4_plus_4_population(self):
        """
        Function to verify the population of DDR and CR.

        :return: if DDR and CR has 4 + 4 config
        """
        new_locator_size_dict = self.get_dict_off_loc_size_mem_type()
        list_slot_config_population = []

        for dict_slot_keys in new_locator_size_dict:
            list_slot_config_population.append("_".join(dict_slot_keys.split("_")[1::]))

        slot_config = dtaf_content_constants.SlotConfigConstant.SLOT_CONFIG_4_by_4.split("-")
        self._log.info("SLOT config : {}".format(slot_config))
        dict_config_slot_population = dict(zip(list_slot_config_population, slot_config))
        self._log.info("Dict slot Config population : {}".format(dict_config_slot_population))
        dict_config_match = self.verify_slot_population(dict_config_slot_population)
        if not dict_config_match:
            raise content_exceptions.TestSetupError("System does not have 4 + 4 configuration ..")
        self._log.info("The CPU has the expected 4+4 memory Configuration ..")
        return True

    def verify_1dpc_or_2dpc_memory_configuration(self):
        """
        Function to verify SUT has 1DPC or 2DPC memory configuration

        return : True if SUT has 1DPC or 2DPC memory configuration.
        """
        dict_config_channel_population = self.get_1_dpc_channel_configuration()

        # Verification between platform configuration and golden configuration info.
        dict_config_match = self.verify_channel_population(dict_config_channel_population)

        if not dict_config_match:
            self._log.info("SUT do not have 1DPC memory configuration, check for 2DPC ...")
            dict_config_channel_population = self.get_2_dpc_channel_configuration()

            # Verification between platform configuration and golden configuration info.
            config_match = self.verify_channel_population(dict_config_channel_population)
            if not config_match:
                raise content_exceptions.TestFail("System do not have 1DPC or 2DPC memory configuration ..")
            self._log.info("SUT has 2DPC memory configuration ...")
            return True
        self._log.info("SUT has 1 DPC memory configuration ...")
        return True

    def verify_only_hbm_memory_configuration(self):
        """
        Function to verify SUT has no DDR memory configuration (HBM mode)

        return : True if SUT has no DDR memory configuration (HBM mode).
        """
        dict_config_channel_population = self.no_dpc_channel_configuration()

        # Verification between platform configuration and golden configuration info.
        dict_config_match = self.verify_channel_population(dict_config_channel_population)

        if not dict_config_match:
            raise content_exceptions.TestFail("SUT does have DRR memory configuration, Please remove "
                                              "all the DDR memory for HBM mode ...")
        return True

    def get_node_memory_list(self):
        """
        This function is used to get the node memory size from the numactl --hardware command

        return : node_memory_list_in_gb
        """
        numactl_size_command = "numactl --hardware | grep -i 'size'"
        self._install_collateral.yum_install(self.PACKAGE_NUMACTL)
        cmd_res = self._common_content_lib_obj.execute_sut_cmd(
            numactl_size_command, numactl_size_command, self._command_timeout, RootDirectoriesConstants.LINUX_ROOT_DIR)
        self._log.info("command : {} result is : {}".format(numactl_size_command, cmd_res))

        cmd_res = cmd_res.strip().split("\n")
        node_memory_list_in_gb = []
        for each in cmd_res:
            if "MB" in each:
                node_memory_list_in_gb.append(int(int(each.split(":")[1].strip("MB").strip()) / 1024))
        return node_memory_list_in_gb

    def verify_cache_mode_memory_hbm(self, cluster_mode):
        """
        This method is used to verify Cache mode (2LM) for HBM

        :param cluster_mode : like Quad, SNC4
        """
        ddr_memory_config = self._common_content_configuration.memory_bios_post_memory_capacity()
        self._log.info("DDR memory from config xml is : {} GB".format(ddr_memory_config))
        variance = float(self._common_content_configuration.get_memory_variance_percent())
        self._log.info("Variance from config xml is : {}".format(variance))
        self._cpu_info_provider.populate_cpu_info()
        socket_present = int(self._cpu_info_provider.get_number_of_sockets())
        self._log.info("Sockets in the SUT : {}".format(socket_present))
        node_memory_list_gb = self.get_node_memory_list()
        self._log.info("Node Memory list in GB is : {}".format(node_memory_list_gb))

        ddr_memory_config_variance = ddr_memory_config - (ddr_memory_config * variance)
        self._log.info("DDR memory with Variance : {} GB".format(ddr_memory_config_variance))
        # DDR connected to one socket
        one_socket_memory_config = int(ddr_memory_config / socket_present)
        self._log.info("DDR connected to 1 socket from config is : {}".format(one_socket_memory_config))
        one_node_memory_variance = None
        one_node_memory_config = None
        if cluster_mode == MemoryClusterConstants.QUAD_STRING:
            # For Cache mode (2LM), Quad, DDR for each node is : memory populated per socket
            one_node_memory_config = one_socket_memory_config
            one_node_memory_variance = int(one_node_memory_config - (one_node_memory_config * variance))

        elif cluster_mode == MemoryClusterConstants.SNC4_STRING:
            # For Cache mode (2LM), SNC4 DDR for each node is : 1/4 of memory populated per socket
            one_node_memory_config = int((1 / 4) * one_socket_memory_config)
            one_node_memory_variance = int(one_node_memory_config - (one_node_memory_config * variance))

        self._log.info("Node memory from config for Cache (2LM) w   ith {} is : {}".format(cluster_mode,
                                                                                        one_node_memory_config))
        self._log.info("Node memory from config for Cache (2LM) with {} with variance is : {}".format(
            cluster_mode, one_node_memory_variance))
        for each_node_memory_gb in node_memory_list_gb:
            if each_node_memory_gb < one_node_memory_variance or each_node_memory_gb > one_node_memory_config:
                raise content_exceptions.TestFail(
                    "Node memory from OS is : {} and Node memory from config with "
                    "variance is : {}".format(each_node_memory_gb, one_node_memory_variance))

        self._log.info("Node memory matched for Cache (2LM) with {}".format(cluster_mode))

    def verify_flat_mode_memory_hbm(self, cluster_mode):
        """
        This method is used to verify Flat mode (1LM) for HBM

        :param cluster_mode : like Quad, SNC4
        """
        ls_dax_command = "ls /dev/dax*"
        reconfigure_daxctl_cmd = "daxctl reconfigure-device -m system-ram {}"
        self._install_collateral.yum_install(self.PACKAGE_DAXCTL)
        cmd_output = self._common_content_lib_obj.execute_sut_cmd(ls_dax_command, ls_dax_command, self._command_timeout,
                                                                  RootDirectoriesConstants.LINUX_ROOT_DIR)
        cmd_output = cmd_output.strip().split("\n")
        self._log.info("command {} output is : {}".format(ls_dax_command, cmd_output))
        for each in cmd_output:
            dax_value = each.split("/")[-1]
            reconfigure_daxctl = reconfigure_daxctl_cmd.format(dax_value)
            res = self._common_content_lib_obj.execute_sut_cmd(
                reconfigure_daxctl, reconfigure_daxctl, self._command_timeout, RootDirectoriesConstants.LINUX_ROOT_DIR)
            self._log.info("command '{}' output is : {}".format(reconfigure_daxctl_cmd, res))

        node_memory_list_gb = self.get_node_memory_list()
        self._log.info("Node Memory list in GB is : {}".format(node_memory_list_gb))
        ddr_memory_config = self._common_content_configuration.memory_bios_post_memory_capacity()
        variance = float(self._common_content_configuration.get_memory_variance_percent())
        self._log.info("Variance from config xml is : {}".format(variance))
        ddr_nodes_list_gb = None
        hbm_nodes_list_gb = None
        ddr_memory_config_variance = ddr_memory_config - (ddr_memory_config * variance)
        self._log.info("DDR memory with Variance : {} GB".format(ddr_memory_config_variance))
        self._cpu_info_provider.populate_cpu_info()
        socket_present = int(self._cpu_info_provider.get_number_of_sockets())
        self._log.info("Sockets in the SUT : {}".format(socket_present))
        # DDR connected to one socket
        one_socket_memory_config = float(ddr_memory_config / socket_present)
        self._log.info("DDR connected to 1 socket from config is : {}".format(one_socket_memory_config))
        one_node_ddr_memory_variance = None
        one_node_ddr_memory_config = None
        one_node_hbm_memory_variance = None
        one_node_hbm_memory_config = None

        if cluster_mode == MemoryClusterConstants.QUAD_STRING:
            hbm_index = socket_present
            ddr_nodes_list_gb = node_memory_list_gb[0:hbm_index]
            hbm_nodes_list_gb = node_memory_list_gb[hbm_index:]
            one_node_ddr_memory_config = one_socket_memory_config
            one_node_hbm_memory_config = self._common_content_configuration.get_hbm_memory_per_socket_config()
            one_node_ddr_memory_variance = one_node_ddr_memory_config - (one_node_ddr_memory_config * variance)
            one_node_hbm_memory_variance = one_node_hbm_memory_config - (one_node_hbm_memory_config * variance)
        elif cluster_mode == MemoryClusterConstants.SNC4_STRING:
            hbm_index = socket_present * 4
            ddr_nodes_list_gb = node_memory_list_gb[0:hbm_index]
            self._log.info("DDR nodes list in GB is : {}".format(ddr_nodes_list_gb))
            hbm_nodes_list_gb = node_memory_list_gb[hbm_index:]
            self._log.info("HBM nodes list in GB is : {}".format(hbm_nodes_list_gb))
            # For Cache mode (2LM), SNC4 DDR for each node is 1/4 (memory populated) / socket
            one_socket_memory_config = one_socket_memory_config - self._common_content_configuration.\
                get_hbm_memory_per_socket_config()
            one_node_ddr_memory_config = (1 / 4) * one_socket_memory_config
            one_node_hbm_memory_config = (1 / 4) * self._common_content_configuration.get_hbm_memory_per_socket_config()
            one_node_ddr_memory_variance = one_node_ddr_memory_config - (one_node_ddr_memory_config * variance)
            one_node_hbm_memory_variance = one_node_hbm_memory_config - (one_node_hbm_memory_config * variance)

        self._log.info("Node memory from config for Cache (1LM) with {} is : {}".format(cluster_mode,
                                                                                        one_node_ddr_memory_config))
        self._log.debug("Node memory from config for Cache (1LM) with {} with variance is : {}".format(
            cluster_mode, one_node_ddr_memory_variance))
        # To check DDR Nodes Size
        for each_node_memory_gb in ddr_nodes_list_gb:
            if each_node_memory_gb < one_node_ddr_memory_variance or each_node_memory_gb > one_node_ddr_memory_config:
                raise content_exceptions.TestFail(
                    "Node memory from OS is : {} and Node memory from config with "
                    "variance is : {}".format(each_node_memory_gb, one_node_ddr_memory_variance))
        # To check HBM Nodes Size
        for each_hbm_node_gb in hbm_nodes_list_gb:
            if each_hbm_node_gb < one_node_hbm_memory_variance or each_hbm_node_gb > one_node_hbm_memory_config:
                raise content_exceptions.TestFail("Node memory from OS is : {} and Node memory from config with "
                                                  "variance is : {}".format(each_hbm_node_gb,
                                                                            one_node_hbm_memory_variance))
        self._log.info("Node memory matched for Flat (1LM) with {}".format(cluster_mode))

    def verify_hbm_mode_memory(self, cluster_mode, platform_mode=None):
        """
        This method is used to verify HBM mode

        :param cluster_mode : like Quad, SNC4
        :param platform_mode: Like HBM, FLAT, CACHE
        """

        node_memory_list_gb = self.get_node_memory_list()
        self._log.info("Node Memory list in GB is : {}".format(node_memory_list_gb))
        variance = float(self._common_content_configuration.get_memory_variance_percent())
        self._log.info("Variance from config xml is : {}".format(variance))
        hbm_nodes_list_gb = None
        self._cpu_info_provider.populate_cpu_info()
        socket_present = int(self._cpu_info_provider.get_number_of_sockets())
        self._log.info("Sockets in the SUT : {}".format(socket_present))
        one_node_hbm_memory_variance = None
        one_node_hbm_memory_config = None

        if platform_mode == PlatformMode.HBM_MODE and cluster_mode == MemoryClusterConstants.QUAD_STRING:
            hbm_index = 0
            hbm_nodes_list_gb = node_memory_list_gb[hbm_index:]
            self._log.info("HBM nodes list in GB is : {}".format(hbm_nodes_list_gb))
            # For hbm mode (1LM)
            one_node_hbm_memory_config = self._common_content_configuration.get_hbm_memory_per_socket_config()
            one_node_hbm_memory_variance = one_node_hbm_memory_config - (one_node_hbm_memory_config * variance)
        elif platform_mode == PlatformMode.HBM_MODE and cluster_mode == MemoryClusterConstants.SNC4_STRING:
            hbm_index = 0
            hbm_nodes_list_gb = node_memory_list_gb[hbm_index:]
            self._log.info("HBM nodes list in GB is : {}".format(hbm_nodes_list_gb))
            # For hbm mode (1LM)
            one_node_hbm_memory_config = int(self._common_content_configuration.get_hbm_memory_per_socket_config() / 4)
            one_node_hbm_memory_variance = int(one_node_hbm_memory_config - (one_node_hbm_memory_config * variance))
        elif cluster_mode == MemoryClusterConstants.QUAD_STRING:
            hbm_index = socket_present
            hbm_nodes_list_gb = node_memory_list_gb[hbm_index:]
            one_node_hbm_memory_config = self._common_content_configuration.get_hbm_memory_per_socket_config()
            one_node_hbm_memory_variance = int(one_node_hbm_memory_config - (one_node_hbm_memory_config * variance))
        elif cluster_mode == MemoryClusterConstants.SNC4_STRING:
            hbm_index = socket_present * 4
            hbm_nodes_list_gb = node_memory_list_gb[hbm_index:]
            self._log.info("HBM nodes list in GB is : {}".format(hbm_nodes_list_gb))
            # For hbm mode (1LM)
            one_node_hbm_memory_config = self._common_content_configuration.get_hbm_memory_per_socket_config()
            one_node_hbm_memory_variance = int(one_node_hbm_memory_config - (one_node_hbm_memory_config * variance))
        else:
            raise content_exceptions.TestFail("None of the configuration is matched.. exiting.. Please check the "
                                              "mode placed")

        # To check HBM Nodes Size
        for each_hbm_node_gb in hbm_nodes_list_gb:
            if each_hbm_node_gb < one_node_hbm_memory_variance or each_hbm_node_gb > one_node_hbm_memory_config:
                raise content_exceptions.TestFail("Node memory from OS is : {} and Node memory from config with "
                                                  "variance is : {}".format(each_hbm_node_gb,
                                                                            one_node_hbm_memory_variance))
        self._log.info("Node memory matched for HBM (1LM) with {}".format(cluster_mode))

    def get_available_disk_space(self):
        """
        This method is to get teh Available Disk Space.

        :return available space
        """
        available_output = self._common_content_lib_obj.execute_sut_cmd(sut_cmd="df -h --output=avail /| grep -v Avail",
                                                                    cmd_str="disk space check command",
                                                                    execute_timeout=self._command_timeout)
        self._log.info("Available Disk Space is - {}".format(available_output))
        return available_output.strip()
