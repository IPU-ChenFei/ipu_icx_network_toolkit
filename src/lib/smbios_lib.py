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

from src.lib.content_configuration import ContentConfiguration
from src.lib.smbios_configuration import SMBiosConfiguration


class SMBiosLib(object):
    """
    This class implements common smbios functions which can used across all test cases.
    """

    def __init__(self, log, os_obj):
        self._log = log
        self._os = os_obj
        self.sut_os = self._os.os_type

        self._common_smbios_configuration = SMBiosConfiguration(self._log)
        self._dict_output = self._common_smbios_configuration.get_smbios_table_dict()

        self._common_content_configuration = ContentConfiguration(self._log)
        self._command_timeout = self._common_content_configuration.get_command_timeout()  # command timeout in seconds

    def get_bios_information(self):
        """
        Function to fetch the bios information from the configuration dictionary.

        :return - bios information as dict
        """
        return self._dict_output["BiosInformation"]

    def get_system_information(self):
        """
        Function to fetch the system information from the configuration dictionary.

        :return - system information as dict
        """
        return self._dict_output["SystemInformation"]

    def get_number_of_sockets(self):
        """
        Function to fetch the number of sockets from the configuration dictionary.

        :return - number of socket present on the board as int
        """
        return self._dict_output["Sockets"]["NumberOfSockets"]

    def get_socket_information(self, socket_index):
        """
        Function to get_socket_information from the configuration dictionary.

        :param socket_index: socket index will be passed to get the specific processor information
        :return - Processor Information of the specific index
        """
        return self._dict_output["Sockets"]["ProcessorInformation{}".format(socket_index)]

    def get_physical_memory_array_information(self):
        """
        Function to get_physical_memory_array_information from the configuration dictionary.

        :return - physical memory array information as dict
        """
        return self._dict_output["PhysicalMemoryArray"]

    def get_number_of_memory_devices(self):
        """
        Function to get_number_of_memory_devices from the configuration dictionary.

        :return - number of memory devices present on the board as int
        """
        return self._dict_output["MemoryDevices"]["NumberOfDevices"]

    def get_memory_device_information(self, memory_index):
        """
        Function to get_memory_device_information from the configuration dictionary.

        :param memory_index: memory index will be passed to get the specific memory device information
        :return - Memory device Information of the specific index
        """
        return self._dict_output["MemoryDevices"]["MemoryDevice{}".format(memory_index)]

    def get_number_of_memory_mapped_addresses(self):
        """
        Function to get_number_of_memory_mapped_addresses from the configuration dictionary.

        :return - number of memory mapped devices present on the board as int
        """
        return self._dict_output["MemoryMappedAdresses"]["NumberOfDevices"]

    def get_memory_mapped_address_information(self, memory_map_index):
        """
        Function to get_memory_mapped_address_information from the configuration dictionary.

        :param memory_map_index: memory mapped index will be passed to get the specific memory mapped device information
        :return - Memory mapped addresses Information of the specific index
        """
        return self._dict_output["MemoryMappedAdresses"]["MemoryMappedAddress{}".format(memory_map_index)]

    def get_number_of_memory_device_mapped_addresses(self):
        """
        Function to get_number_of_memory_device_mapped_addresses from the configuration dictionary.

        :return - number of memory device mapped addresses present on the board as int
        """
        return self._dict_output["MemoryDeviceMappedAddresses"]["NumberOfDevices"]

    def get_memory_device_mapped_address_information(self, memory_device_index):
        """
        Function to get_memory_device_mapped_address_information from the configuration dictionary.

        :param memory_device_index: memory device index will be passed to get the specific memory device mapped
        address information
        :return - Memory device mapped addresses Information of the specific index
        """
        return self._dict_output["MemoryMappedAdresses"]["MemoryDeviceMappedAddress{}".format(memory_device_index)]
