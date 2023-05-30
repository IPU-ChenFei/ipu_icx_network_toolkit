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
import datetime
import os
import platform
import re
from pathlib import Path
from shutil import copyfile

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.lib.content_configuration import ContentConfiguration
from src.lib.dmidecode_parser_lib import DmiDecodeParser
from src.lib.common_content_lib import CommonContentLib


class DmiDecodeVerificationLib(object):
    """
    Class to verify/ compare the dmidecode output from tool against the spec.
    """

    dmi_output = None

    smbios_config_file_per_platform_dict = {"PLY": r"neoncity_smbios_configuration.xml",
                                            "WLY": r"wilsoncity_smbios_configuration.xml",
                                            "EGS": r"archercity_smbios_configuration.xml"}

    def __init__(self, log, os_obj):
        self._log = log
        self._os = os_obj

        self._dmidecode_parser = DmiDecodeParser(self._log, self._os)
        self._common_content_lib = CommonContentLib(self._log, self._os, None)
        self._common_content_configuration = ContentConfiguration(self._log)

        self._command_timeout = self._common_content_configuration.get_command_timeout()

    def copy_smbios_config_file_if_not_exist(self, dmidecode_path):
        """
        To copy smbios config file into "C:\\Automation folder" if the file is not exists.

        :param dmidecode_path: If windows we need to have the tool path
        """

        exec_os = platform.system()
        platform_version = None
        try:
            cfg_file_default = Framework.CFG_BASE
        except KeyError:
            err_log = "Error - execution OS " + str(exec_os) + " not supported!"
            self._log.error(err_log)
            raise err_log

        # Get the Automation folder config file path based on OS.
        cfg_file_automation_path = cfg_file_default[exec_os] + "smbios_configuration.xml"

        # First check whether the config file exists in C:\Automation folder else files not exists
        if os.path.isfile(cfg_file_automation_path):
            self._log.info("Successfully verified the 'Smbios configuration.xml' file existence in the directory, "
                           "proceeding further..")
        else:
            if OperatingSystems.LINUX == self._os.os_type:
                platform_version = self._common_content_lib.execute_sut_cmd("dmidecode -t 0 | grep 'Version:'",
                                                                            "Get the platform name",
                                                                            self._command_timeout)
            elif OperatingSystems.WINDOWS == self._os.os_type:
                platform_version = self._common_content_lib.execute_sut_cmd('dmidecode --t 0 | FINDSTR "Version:"',
                                                                            "Get the platform name",
                                                                            self._command_timeout, dmidecode_path)

            version = platform_version.split(":")[1][0:4:].strip()
            smbios_config_file_path = self.smbios_config_file_per_platform_dict[version]

            config_file_src_path = None

            config_file_path = Path(os.path.dirname(os.path.realpath(__file__))).parent
            for root, dirs, files in os.walk(str(config_file_path)):
                for name in files:
                    if name.startswith(smbios_config_file_path) and name.endswith(".xml"):
                        config_file_src_path = os.path.join(root, name)

            if os.path.exists(config_file_src_path):
                if OperatingSystems.WINDOWS == self._os.os_type:
                    copyfile(config_file_src_path, cfg_file_automation_path)
                elif OperatingSystems.LINUX == self._os.os_type:
                    copyfile(Path(config_file_src_path).as_posix(), cfg_file_automation_path)
            else:
                raise RuntimeError("Smbios configuration file does not exists in the framework directory, "
                                   "please copy it before executing the test case..")

            self._log.info("Smbios configuration file does not exists in the directory, please wait while we copy it "
                           "for you..")

            self._log.info("Smbios configuration file has been copied under {}..".format(cfg_file_default[exec_os]))

    def verify_bios_information(self, dict_dmi_decode_from_tool, dict_dmi_decode_from_spec):
        """
        Function to verify the bios information against the spec.

        :param dict_dmi_decode_from_tool: Tool output of dmidecode as dictionary.
        :param dict_dmi_decode_from_spec: Spec information of dmidecode as dictionary.
        :return bios_info_compare_res: True if the verification is passed else false
        """
        bios_info_compare_res = True

        # Pattern to check the hex Handle of each DMI Type's
        handle_pattern = "[0-9A-F]*x[0-9A-F]*"

        # Pattern to check the Release date format
        date_pattern = r"[\d]{1,2}/[\d]{1,2}/[\d]{4,4}"
        for key in dict_dmi_decode_from_tool.keys():
            if dict_dmi_decode_from_tool[key]['DMIType'] == 0:
                date_pattern_check = re.search(date_pattern, dict_dmi_decode_from_tool[key]['Release Date'])
                release_date = datetime.datetime.strptime(dict_dmi_decode_from_tool[key]['Release Date'], "%m/%d/%Y")
                present_date = datetime.datetime.now()
                # Date one year back from current date.
                date_one_year_ago = present_date - datetime.timedelta(days=365)
                if not re.search(handle_pattern, key) or dict_dmi_decode_from_tool[key]['DMISize'] < 18 or \
                        dict_dmi_decode_from_tool[key]['Vendor'] != \
                        dict_dmi_decode_from_spec["BiosInformation"]['Vendor'] or \
                        dict_dmi_decode_from_tool[key]['Version'] != \
                        dict_dmi_decode_from_spec["BiosInformation"]['Version'] or not date_pattern_check or \
                        release_date.date() > present_date.date() or release_date.date() > date_one_year_ago.date() or \
                        not dict_dmi_decode_from_spec["BiosInformation"]["Address"] or \
                        not dict_dmi_decode_from_spec["BiosInformation"]["RuntimeSize"] or \
                        not dict_dmi_decode_from_spec["BiosInformation"]["RomSize"]:
                    bios_info_compare_res = False
                    self._log.error("DMI TYPE 0 information are not correct!")
                else:
                    self._log.info("DMI TYPE 0 information has been verified successfully!!")
        return bios_info_compare_res

    def verify_system_information(self, dict_dmi_decode_from_tool, dict_dmi_decode_from_spec):
        """
        Function to verify the system_information against the spec.

        :param dict_dmi_decode_from_tool: Tool output of dmidecode as dictionary.
        :param dict_dmi_decode_from_spec: Spec information of dmidecode as dictionary.
        :return sys_info_compare_res: True if the verification is passed else false
        """

        sys_info_compare_res = True
        num_dmi_type1 = 0
        # Pattern to check the hex Handle of each DMI Type's
        handle_pattern = "[0-9A-F]*x[0-9A-F]*"

        for key in dict_dmi_decode_from_tool.keys():
            if dict_dmi_decode_from_tool[key]['DMIType'] == 1:
                num_dmi_type1 = + 1
                if not re.search(handle_pattern, key) or dict_dmi_decode_from_tool[key]['DMISize'] < 27 or \
                        not dict_dmi_decode_from_tool[key]['Manufacturer'] or \
                        dict_dmi_decode_from_tool[key]['Product Name'] != \
                        dict_dmi_decode_from_spec['SystemInformation']['ProductName'] or \
                        (dict_dmi_decode_from_tool[key]["UUID"] == "00000000-0000-0000-0000-000000000000" or
                         dict_dmi_decode_from_tool[key]["UUID"] == "FFFFFFFF-FFFF-FFFF-FFFF-FFFFFFFFFFFF") or \
                        not dict_dmi_decode_from_tool[key]['Wake-up Type'] or \
                        not dict_dmi_decode_from_tool[key]['SKU Number'] or \
                        not dict_dmi_decode_from_tool[key]['Family']:
                    sys_info_compare_res = False
                    self._log.error("DMI TYPE 1 information are not correct!")
                else:
                    self._log.info("DMI TYPE 1 information has been verified successfully!")

        if num_dmi_type1 != 1:
            sys_info_compare_res = False
            self._log.error("DMI TYPE 1 has {} occurrence(s) which fails condition.".format(num_dmi_type1))
        else:
            self._log.info("DMI TYPE 1 is occurred {} time(s) in the entire smbios table.".format(num_dmi_type1))

        return sys_info_compare_res

    def verify_processor_information(self, dict_dmi_decode_from_tool, dict_dmi_decode_from_spec):
        """
        Function to verify the processor_information against the spec.

        :param dict_dmi_decode_from_tool: Tool output of dmidecode as dictionary.
        :param dict_dmi_decode_from_spec: Spec information of dmidecode as dictionary.
        :return processor_info_compare_res: True if the verification is passed else false
        """
        processor_info_compare_res = True
        num_sign_values = 0
        numeric_sign_values = 0
        socket = 0

        # Pattern to check the hex Handle of each DMI Type's
        handle_pattern = "[0-9A-F]*x[0-9A-F]*"

        # Pattern to check the processor ID format
        hexa_pattern = r"([0-9A-F])+\s([0-9fA-F])+\s([0-9A-F])+\s([0-9A-F])+\s([0-9A-F])+\s([0-9A-F])+" \
                       r"\s([0-9A-F])+\s([0-9A-F])"

        for key in dict_dmi_decode_from_tool.keys():
            if dict_dmi_decode_from_tool[key]['DMIName'] == 'Processor Information':
                socket = socket + 1
                processorsocket = "ProcessorInformation{}".format(socket)
                if 'ID' in dict_dmi_decode_from_tool[key]:
                    processor_id = dict_dmi_decode_from_tool[key]['ID']
                    hexa_pattern_match = re.search(hexa_pattern, processor_id)
                    if not hexa_pattern_match:
                        processor_info_compare_res = False
                        self._log.error("Processor ID on {} is not correct!".format(
                            dict_dmi_decode_from_tool[key]["Socket Designation"]))
                    else:
                        self._log.info("Processor ID on {} has been verified successfully!!".format(
                            dict_dmi_decode_from_tool[key]["Socket Designation"]))

                if 'Signature' in dict_dmi_decode_from_tool[key]:
                    for sign_keys in dict_dmi_decode_from_tool[key]['Signature'].split(','):
                        num_sign_values = num_sign_values + 1
                        for sign_value in sign_keys.split():
                            if sign_value.isdigit():
                                numeric_sign_values = numeric_sign_values + 1

                if numeric_sign_values != num_sign_values:
                    processor_info_compare_res = False
                    self._log.error("Numeric Values representing the 'Type', 'Family', 'Model', 'Stepping' are present"
                                    " in {} are not correct!".format(dict_dmi_decode_from_tool[key]["Socket "
                                                                                                    "Designation"]))
                else:
                    self._log.info("Numeric Values representing the 'Type', 'Family', 'Model', 'Stepping' are present"
                                   " in {} has been verified successfully!!".format(dict_dmi_decode_from_tool[key]
                                                                                    ["Socket Designation"]))

                if dict_dmi_decode_from_tool[key]['Version'] != \
                        dict_dmi_decode_from_spec["Sockets"][processorsocket]["Version"] or \
                        ((not dict_dmi_decode_from_tool[key]['Socket Designation'] and dict_dmi_decode_from_tool[key][
                            'Voltage'] >= 0) or (dict_dmi_decode_from_tool[key]['Socket Designation'] and
                                                 dict_dmi_decode_from_tool[key]['Voltage'] !=
                                                 dict_dmi_decode_from_spec["Sockets"][
                                                     processorsocket]['Voltage'])) or \
                        dict_dmi_decode_from_tool[key]['External Clock'] != dict_dmi_decode_from_spec[
                    "Sockets"][processorsocket]['ExternalClock'] or \
                        dict_dmi_decode_from_tool[key]['Max Speed'] != dict_dmi_decode_from_spec[
                    "Sockets"][processorsocket]['MaxSpeed'] or \
                        dict_dmi_decode_from_tool[key]['Max Speed'] == "FFh" or \
                        dict_dmi_decode_from_tool[key]['Max Speed'] == "00h" or \
                        dict_dmi_decode_from_tool[key]['Current Speed'] > dict_dmi_decode_from_spec[
                    "Sockets"][processorsocket]['MaxSpeed'] or \
                        dict_dmi_decode_from_tool[key]['Status'] != \
                        dict_dmi_decode_from_spec["Sockets"][processorsocket]['Status'] or \
                        not dict_dmi_decode_from_tool[key]['Upgrade'] or \
                        not dict_dmi_decode_from_tool[key]['L1 Cache Handle'] or \
                        not re.search(handle_pattern, dict_dmi_decode_from_tool[key]['L1 Cache Handle']) or \
                        not dict_dmi_decode_from_tool[key]['L2 Cache Handle'] or \
                        not re.search(handle_pattern, dict_dmi_decode_from_tool[key]['L2 Cache Handle']) or \
                        not dict_dmi_decode_from_tool[key]['L3 Cache Handle'] or \
                        not re.search(handle_pattern, dict_dmi_decode_from_tool[key]['L3 Cache Handle']) or \
                        not dict_dmi_decode_from_tool[key]['Core Count'] or \
                        dict_dmi_decode_from_tool[key]['Core Count'] != dict_dmi_decode_from_spec[
                    "Sockets"][processorsocket]['CoreCount'] or \
                        not dict_dmi_decode_from_tool[key]['Core Enabled'] or \
                        dict_dmi_decode_from_tool[key]['Core Enabled'] != dict_dmi_decode_from_spec[
                    "Sockets"][processorsocket]['CoreEnabled'] or \
                        not dict_dmi_decode_from_tool[key]['Thread Count'] or \
                        int(dict_dmi_decode_from_tool[key]['Thread Count']) != int(dict_dmi_decode_from_spec[
                                                                                       "Sockets"][processorsocket][
                                                                                       'CoreCount']) * 2:
                    processor_info_compare_res = False
                    self._log.error("Processor information on {} are not correct!".format(
                        dict_dmi_decode_from_tool[key]["Socket Designation"]))
                else:
                    self._log.info("Processor information on {} has been verified successfully!!".format(
                        dict_dmi_decode_from_tool[key]["Socket Designation"]))

        return processor_info_compare_res

    def verify_physical_memory_array(self, dict_dmi_decode_from_tool, dict_dmi_decode_from_spec):
        """
        Function to verify the physical_memory_array information against the spec.

        :param dict_dmi_decode_from_tool: Tool output of dmidecode as dictionary.
        :param dict_dmi_decode_from_spec: Spec information of dmidecode as dictionary.
        :return physical_mem_arr_compare_res: True if the verification is passed else false
        """

        # Pattern to check the hex Handle of each DMI Type's
        handle_pattern = "[0-9A-F]*x[0-9A-F]*"
        physical_mem_arr_compare_res = True
        for key in dict_dmi_decode_from_tool.keys():
            if dict_dmi_decode_from_tool[key]['DMIType'] == 16:
                if not re.search(handle_pattern, key) or dict_dmi_decode_from_tool[key]['Location'] != \
                        dict_dmi_decode_from_spec[
                            'PhysicalMemoryArray']['Location'] or \
                        dict_dmi_decode_from_tool[key]['Use'] != dict_dmi_decode_from_spec['PhysicalMemoryArray'][
                    'Use'] or \
                        (dict_dmi_decode_from_tool[key]['Error Correction Type'] != dict_dmi_decode_from_spec[
                            'PhysicalMemoryArray']['ErrorCorrectionType']) or \
                        dict_dmi_decode_from_tool[key]['Maximum Capacity'] != \
                        dict_dmi_decode_from_spec['PhysicalMemoryArray']['MaximumCapacity'] or \
                        int(dict_dmi_decode_from_tool[key]['Number Of Devices']) <= 0:
                    physical_mem_arr_compare_res = False
                    self._log.error("DMI TYPE 16 information are not correct!")
                else:
                    self._log.info("DMI TYPE 16 information has been verified successfully!")
        return physical_mem_arr_compare_res

    def verify_memory_device(self, dict_dmi_decode_from_tool, dict_dmi_decode_from_spec):
        """
        Function to verify the memory device information against the spec.

        :param dict_dmi_decode_from_tool: Tool output of dmidecode as dictionary.
        :param dict_dmi_decode_from_spec: Spec information of dmidecode as dictionary.
        :return memory_device_compare_res: True if the verification is passed else false
        """

        num_dmi_type17 = 0
        # Pattern to check hex value
        hexa_pattern_angle = "(0x[0-9A-F]+)"
        # Pattern to check the value is all F's
        pattern_all_f = "^[F+]$"
        # Pattern to check the hex Handle of each DMI Type's
        handle_pattern = "[0-9A-F]*x[0-9A-F]*"
        memory_device_compare_res = True

        for key in dict_dmi_decode_from_tool.keys():
            if dict_dmi_decode_from_tool[key]['DMIType'] == 17:
                num_dmi_type17 = num_dmi_type17 + 1
                memory_device_num = 'MemoryDevice{}'.format(num_dmi_type17)
                module_error = False

                if dict_dmi_decode_from_tool[key]['Size'] == "No Module Installed":
                    if dict_dmi_decode_from_tool[key]['Total Width'] != "Unknown" or \
                            dict_dmi_decode_from_tool[key]['Data Width'] != "Unknown" or \
                            dict_dmi_decode_from_tool[key]['Type'] != "Unknown":
                        module_error = True
                else:
                    if (dict_dmi_decode_from_tool[key]['Total Width'] != '72 bits' and
                        dict_dmi_decode_from_tool[key]['Total Width'] != '64 bits') or \
                            dict_dmi_decode_from_tool[key]['Data Width'] != "64 bits":
                        module_error = True

                self._log.info("{}".format(memory_device_num))

                self._log.info("OS reported Locator information - {} || Configuration file reported Locator "
                               "information  - {}"
                               .format(dict_dmi_decode_from_tool[key]['Locator'],
                                       dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['Locator']))

                self._log.info("OS reported Bank Locator information - {} || Configuration file reported "
                               "Bank Locator information - {}"
                               .format(dict_dmi_decode_from_tool[key]['Bank Locator'],
                                       dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['BankLocator']))

                self._log.info("OS reported Memory Type information - {} || Configuration file reported Memory Type "
                               "information - {}"
                               .format(dict_dmi_decode_from_tool[key]['Type'],
                                       dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['Type']))

                self._log.info("OS reported Memory Speed information - {} || Configuration file reported Memory Speed "
                               "information - {}"
                               .format(dict_dmi_decode_from_tool[key]['Speed'],
                                       dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['Speed']))

                if module_error or not re.search(handle_pattern, key) or \
                        not re.search(hexa_pattern_angle, dict_dmi_decode_from_tool[key]['Array Handle']) or \
                        dict_dmi_decode_from_tool[key]['Error Information Handle'] != \
                        dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['ErrorInformationHandle'] or \
                        dict_dmi_decode_from_tool[key]['Size'] != \
                        dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['Size'] or \
                        (dict_dmi_decode_from_tool[key]['Form Factor'] != 'DIMM' and
                         dict_dmi_decode_from_tool[key]['Form Factor'] != 'RIMM') or \
                        dict_dmi_decode_from_tool[key]['Set'] == 'FFh' or dict_dmi_decode_from_tool[key]['Locator'] != \
                        dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['Locator'] or \
                        dict_dmi_decode_from_tool[key]['Bank Locator'] != \
                        dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['BankLocator'] or \
                        (dict_dmi_decode_from_tool[key]['Type'] and dict_dmi_decode_from_tool[key]['Type'] !=
                         dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['Type']) or \
                        dict_dmi_decode_from_tool[key]['Type Detail'] != \
                        dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['TypeDetail'] or \
                        (dict_dmi_decode_from_tool[key]['Speed'] != 0 and
                         dict_dmi_decode_from_tool[key]['Speed'] != dict_dmi_decode_from_spec['MemoryDevices'][
                             memory_device_num]['Speed']) or \
                        (not dict_dmi_decode_from_tool[key]['Manufacturer'] or
                         re.search(pattern_all_f, dict_dmi_decode_from_tool[key]['Manufacturer'])) or \
                        (not dict_dmi_decode_from_tool[key]['Serial Number'] and
                         re.search(pattern_all_f, dict_dmi_decode_from_tool[key]['Serial Number'])) or \
                        not dict_dmi_decode_from_tool[key]['Part Number'] or \
                        dict_dmi_decode_from_tool[key]['Rank'] != dict_dmi_decode_from_spec['MemoryDevices'][
                    memory_device_num]['Rank'] or dict_dmi_decode_from_tool[key]['Configured Memory Speed'] != \
                        dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['ConfiguredClockSpeed'] or \
                        (dict_dmi_decode_from_tool[key]['Type'] == 'DDR4' and dict_dmi_decode_from_tool[key][
                            'Minimum Voltage'] != '1.2 V') or (dict_dmi_decode_from_tool[key]['Type'] == 'DDR5' and
                                                               dict_dmi_decode_from_tool[key][
                                                                   'Minimum Voltage'] != '1.1 V') or \
                        (dict_dmi_decode_from_tool[key]['Type'] == 'DDR4' and dict_dmi_decode_from_tool[key][
                            'Maximum Voltage'] != '1.2 V') or (dict_dmi_decode_from_tool[key]['Type'] == 'DDR5' and
                                                               dict_dmi_decode_from_tool[key][
                                                                   'Maximum Voltage'] != '1.1 V') or \
                        (dict_dmi_decode_from_tool[key]['Type'] == 'DDR4' and dict_dmi_decode_from_tool[key][
                            'Configured Voltage'] != '1.2 V') or (dict_dmi_decode_from_tool[key]['Type'] == 'DDR5' and
                                                                  dict_dmi_decode_from_tool[key][
                                                                      'Configured Voltage'] != '1.1 V'):
                    memory_device_compare_res = False

                    self._log.error("DMI TYPE 17 on {} information are not "
                                    "correct!".format(memory_device_num))
                else:
                    self._log.info("DMI TYPE 17 on {} information has been verified "
                                   "successfully!".format(memory_device_num))

        if num_dmi_type17 != int(dict_dmi_decode_from_spec['PhysicalMemoryArray']['NumberOfDevices']):
            memory_device_compare_res = False
            self._log.error("DMI TYPE 17 occurrence is {} and it is not equal to number of "
                            "devices".format(num_dmi_type17))
        else:
            self._log.info(
                "DMI TYPE 17 occurrence is {} and it is equal to number of devices".format(num_dmi_type17))

        return memory_device_compare_res

    def verify_diff_param_memory_device(self, dict_dmi_decode_from_tool, dict_dmi_decode_from_spec):
        """
        Function to verify the memory device information against the spec.

        :param dict_dmi_decode_from_tool: Tool output of dmidecode as dictionary.
        :param dict_dmi_decode_from_spec: Spec information of dmidecode as dictionary.
        :return diff_param_memory_device_compare_res: True if the verification is passed else false
        """

        num_dmi_type17 = 0

        diff_param_memory_device_compare_res = True
        # Pattern to check the hex Handle of each DMI Type's
        handle_pattern = "[0-9A-F]*x[0-9A-F]*"

        for key in dict_dmi_decode_from_tool.keys():
            if dict_dmi_decode_from_tool[key]['DMIType'] == 17:
                num_dmi_type17 = num_dmi_type17 + 1
                memory_device_num = 'MemoryDevice{}'.format(num_dmi_type17)
                if not re.search(handle_pattern, key) or \
                        dict_dmi_decode_from_tool[key]['Size'] != \
                        dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['Size'] or \
                        dict_dmi_decode_from_tool[key]['Locator'] != \
                        dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['Locator'] or \
                        dict_dmi_decode_from_tool[key]['Bank Locator'] != \
                        dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['BankLocator'] or \
                        (dict_dmi_decode_from_tool[key]['Type'] and dict_dmi_decode_from_tool[key]['Type'] !=
                         dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['Type']) or \
                        (dict_dmi_decode_from_tool[key]['Speed'] != 0 and
                         dict_dmi_decode_from_tool[key]['Speed'] != dict_dmi_decode_from_spec['MemoryDevices'][
                             memory_device_num]['Speed']) or \
                        dict_dmi_decode_from_tool[key]['Configured Memory Speed'] != \
                        dict_dmi_decode_from_spec['MemoryDevices'][memory_device_num]['ConfiguredClockSpeed']:
                    diff_param_memory_device_compare_res = False
                    self._log.error("DMI TYPE 17 on {} information are not "
                                    "correct!".format(memory_device_num))
                else:
                    self._log.info("DMI TYPE 17 on {} information has been verified "
                                   "successfully!".format(memory_device_num))
        return diff_param_memory_device_compare_res

    def verify_memory_array_mapped_address(self, dict_dmi_decode_from_tool):
        """
        Function to verify the memory array mapped address information.

        :param dict_dmi_decode_from_tool: Tool output of dmidecode as dictionary.
        :return memory_array_mapped_address_compare_res: True if the verification is passed else false
        """
        mem_arr_map_addresses = []
        # Pattern to check the hex Handle of each DMI Type's
        handle_pattern = "[0-9A-F]*x[0-9A-F]*"
        memory_array_mapped_address_compare_res = True
        num_dmi_type19 = 0
        for key in dict_dmi_decode_from_tool.keys():
            if dict_dmi_decode_from_tool[key]['DMIType'] == 19:
                num_dmi_type19 = num_dmi_type19 + 1
                dmi_wise_address = [dict_dmi_decode_from_tool[key]['Starting Address'],
                                    dict_dmi_decode_from_tool[key]['Ending Address']]
                mem_arr_map_addresses.append(dmi_wise_address)

                if not re.search(handle_pattern, key) or (dict_dmi_decode_from_tool[key]['DMISize'] != "1F" and
                                                          int(dict_dmi_decode_from_tool[key]['DMISize']) != 31) or \
                        int(dict_dmi_decode_from_tool[key]['Starting Address'], 16) >= \
                        int(dict_dmi_decode_from_tool[key]['Ending Address'], 16):
                    memory_array_mapped_address_compare_res = False
                    self._log.error("DMI TYPE 19 on Memory Array Mapped Address {} information are not "
                                    "correct!".format(num_dmi_type19))
                else:
                    self._log.info("DMI TYPE 19 on Memory Array Mapped Address {} information has been verified "
                                   "successfully!".format(num_dmi_type19))

        for index in range(0, len(mem_arr_map_addresses) - 1):
            if int(mem_arr_map_addresses[index][1], 16) >= int(mem_arr_map_addresses[index + 1][0], 16):
                memory_array_mapped_address_compare_res = False
                self._log.info("Failed - Ending address {} is greater than Starting address {} of "
                               "next DMI Type 19 block".format(mem_arr_map_addresses[index][1],
                                                               mem_arr_map_addresses[index + 1][0]))
            else:
                self._log.info("Successful - Ending address {} is less than Starting address {} of "
                               "next DMI Type 19 block".format(mem_arr_map_addresses[index][1],
                                                               mem_arr_map_addresses[index + 1][0]))

        if num_dmi_type19 <= 0:
            memory_array_mapped_address_compare_res = False
            self._log.error("DMI TYPE 19 has {} occurrence(s) in the entire smbios table.".format(num_dmi_type19))
        else:
            self._log.info("DMI TYPE 19 is occurred {} time(s) in the entire smbios table..".format(num_dmi_type19))

        return memory_array_mapped_address_compare_res

    def verify_memory_device_mapped_address(self, dict_dmi_decode_from_tool):
        """
        Function to verify the memory device mapped address information.

        :param dict_dmi_decode_from_tool: Tool output of dmidecode as dictionary.
        :return memory_device_mapped_address_compare_res: True if the verification is passed else false
        """
        num_dmi_type20 = 0
        # Pattern to check the hex Handle of each DMI Type's
        handle_pattern = "[0-9A-F]*x[0-9A-F]*"
        memory_device_mapped_address_compare_res = True

        for key in dict_dmi_decode_from_tool.keys():
            if dict_dmi_decode_from_tool[key]['DMIType'] == 20:
                num_dmi_type20 = num_dmi_type20 + 1
                if not re.search(handle_pattern, key) or dict_dmi_decode_from_tool[key]['DMISize'] < 35 or \
                        int(dict_dmi_decode_from_tool[key]['Starting Address'], 16) >= \
                        int(dict_dmi_decode_from_tool[key]['Ending Address'], 16):
                    memory_device_mapped_address_compare_res = False
                    self._log.error("DMI TYPE 20 on Memory Device Mapped Address {} information are not "
                                    "correct!".format(num_dmi_type20))
                else:
                    self._log.info("DMI TYPE 20 on Memory Device Mapped Address {} information has been verified "
                                   "successfully!".format(num_dmi_type20))

        if num_dmi_type20 <= 0:
            self._log.error("DMI TYPE 20 has {} occurrence(s) in the entire smbios table.".format(num_dmi_type20))
        else:
            self._log.info("DMI TYPE 20 has {} occurrence(s) in the entire smbios table..".format(num_dmi_type20))

        return memory_device_mapped_address_compare_res

    def verify_end_of_table(self, end_line):
        """
        Function to verify end of smbios table has correct information.

        :return end_of_table_compare_res: True if the verification is passed else false
        """
        end_of_table_compare_res = True

        if end_line != 'End Of Table':
            end_of_table_compare_res = False
            self._log.error("Unable to find the 'End Of Table'")
        else:
            self._log.info("Successfully verified that the last line of the dmidecode output is 'End Of Table'")

        return end_of_table_compare_res
