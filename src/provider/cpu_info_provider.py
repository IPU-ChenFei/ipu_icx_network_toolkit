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
import re
from importlib import import_module
from abc import ABCMeta, abstractmethod
from six import add_metaclass

from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.provider.base_provider import BaseProvider
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration


@add_metaclass(ABCMeta)
class CpuInfoProvider(BaseProvider):

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new CPU Util object.

        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment
        :param log: Logger object to use for output messages
        """
        super(CpuInfoProvider, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj
        self._sut_os = self._os.os_type

        self._common_content_obj = CommonContentLib(self._log, self._os, self._cfg_opts)
        self._content_config_obj = ContentConfiguration(self._log)
        self._command_time_out = self._content_config_obj.get_command_timeout()

    @staticmethod
    def factory(log, cfg_opts, os_obj):
        """
        To create a factory object based on the configuration xml file.

        :return: object
        """
        package = r"src.provider.cpu_info_provider"
        if OperatingSystems.WINDOWS == os_obj.os_type:
            mod_name = "CpuInfoProviderWindows"
        elif OperatingSystems.LINUX == os_obj.os_type:
            mod_name = "CpuInfoProviderLinux"
        else:
            raise NotImplementedError

        mod = import_module(package, mod_name)
        aclass = getattr(mod, mod_name)
        return aclass(cfg_opts=cfg_opts, log=log, os_obj=os_obj)

    @abstractmethod
    def populate_cpu_info(self):
        """
        Calls OS APIs to populate the CPU information.

        :return: None
        """
        raise NotImplementedError

    @abstractmethod
    def get_max_cpu_frequency(self):
        """
        To get the current frequency of CPU in Hertz.

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_current_cpu_frequency(self):
        """
        To get the current frequency of CPU in Hertz.

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_min_cpu_frequency(self):
        """
        To get the current frequency of CPU in Hertz.

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_logical_processors(self):
        """
        To get no of Logical Processors in the system.

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_number_of_sockets(self):
        """
        To get the Number of Sockets in system

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_number_of_cores(self):
        """
        To get the Number of Sockets in system

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_number_of_cores_per_socket(self):
        """
        To get the Number of Cores/Socket in system
        
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_l1d_cache_size(self):
        """
        To get the L1d Cache Size in system

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_l1i_cache_size(self):
        """
        To get the L1i Cache Size in system

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_l2_cache_size(self):
        """
        To get the L2 Cache Size in system

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_l3_cache_size(self):
        """
        To get the L3 Cache Size in system

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_virtualization_data(self):
        """
        To get Information about Virtualization in the system

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_numa_node(self):
        return NotImplementedError

    @abstractmethod
    def get_number_of_threads(self):
        return NotImplementedError


class CpuInfoProviderLinux(CpuInfoProvider):
    _LSCPU_COMMAND = "lscpu"
    _KEY_CPU_MAX_FREQUENCY_LIMIT = 'CPU max MHz'
    _KEY_CPU_CURRENT_FREQUENCY = 'CPU MHz'
    _KEY_CPU_MIN_FREQUENCY_LIMIT = 'CPU min MHz'
    _KEY_NUMA_NODES = "NUMA node(s)"
    _NUMBER_OF_THREADS = "Thread(s) per core"
    _KEY_NO_OF_LOGICAL_PROCESSORS = 'CPU(s)'
    _KEY_NO_OF_SOCKETS = 'Socket(s)'
    _KEY_NO_OF_CORES = 'Core(s) per socket'
    _KEY_L1D_CACHE_SIZE = 'L1d cache'
    _KEY_L1I_CACHE_SIZE = 'L1i cache'
    _KEY_L2_CACHE_SIZE = 'L2 cache'
    _KEY_L3_CACHE_SIZE = 'L3 cache'
    _KEY_VIRTUALIZATION = 'Virtualization'
    VIRTUALIZATION = 'virtualization_data'

    def __init__(self, log, cfg_opts, os_obj):
        super(CpuInfoProviderLinux, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj
        self._dict_cpu_info = {}

    def populate_cpu_info(self):
        """
        Calls OS APIs to populate the CPU information.

        :return: None
        """
        # clear exis
        self._dict_cpu_info.clear()
        self.__populate_cpu_info()

    def __populate_cpu_info(self):
        """
        To populate cpu information into a dictionary
        :return: None
        """
        try:
            # execute lscpu command on SUT
            result = self._common_content_obj.execute_sut_cmd(self._LSCPU_COMMAND, "exec lscpu command",
                                                              self._command_time_out)

            cpu_info_list = result.strip().split("\n")
            self._log.debug(cpu_info_list)
            for each_item in cpu_info_list:
                if each_item:
                    list_info = each_item.split(":")
                    if len(list_info) > 1:
                        self._dict_cpu_info[list_info[0].strip()] = list_info[1].strip()
            self._log.debug(self._dict_cpu_info)
        except Exception as ex:
            self._log.error("Populating cpu info failed due to Exception'{}'...".format(ex))
            raise ex

    def get_max_cpu_frequency(self):
        """
        To get the current frequency of CPU in Hertz.
        sample output string : CPU max MHz:3200.0000

        :return: current frequency
        """
        return self._dict_cpu_info[self._KEY_CPU_MAX_FREQUENCY_LIMIT]

    def get_numa_node(self):
        return self._dict_cpu_info[self._KEY_NUMA_NODES]

    def get_number_of_threads(self):
        return int(self._dict_cpu_info[self._NUMBER_OF_THREADS]) * int(self._dict_cpu_info[self._KEY_NO_OF_CORES])\
                                                                     * int(self._dict_cpu_info[self._KEY_NO_OF_SOCKETS])

    def get_min_cpu_frequency(self):
        """
        To get the minimum CPU frequency limit of system
        sample output string : CPU min MHz:800.0000

        :return: min cpu frequency
        """
        return self._dict_cpu_info[self._KEY_CPU_MIN_FREQUENCY_LIMIT]

    def get_current_cpu_frequency(self):
        """
        To get the current frequency of CPU in Hertz.
        example string :  CPU MHz:800.148

        :return: current frequency
        """
        return self._dict_cpu_info[self._KEY_CPU_CURRENT_FREQUENCY]

    def get_logical_processors(self):
        """
        To get No of Logical Processors in system
        example string :  CPU(s):48

        :return: Logical processor count
        """
        return self._dict_cpu_info[self._KEY_NO_OF_LOGICAL_PROCESSORS]

    def get_number_of_sockets(self):
        """
        To get the Number of Sockets in system
        example string :  Socket(s): 2

        :return: Number of Sockets
        """
        return self._dict_cpu_info[self._KEY_NO_OF_SOCKETS]

    def get_number_of_cores(self):
        """
        To get the Number of Sockets in system
        example string : Core(s) per socket: 12

        :return: Number of cores
        """
        number_of_cores = int(self.get_number_of_sockets()) * int(self._dict_cpu_info[self._KEY_NO_OF_CORES])
        return str(number_of_cores)

    def get_number_of_cores_per_socket(self):
        """
        To get the Number of Cores per Socket in system
        example string : Core(s) per socket: 12

        :return: Number of cores
        """
        return self._dict_cpu_info[self._KEY_NO_OF_CORES]

    def get_l1d_cache_size(self):
        """
        To get the L1d Cache Size in system
        example string : L1d cache: 1.1 MiB

        :return: L1d cache Size
        """
        return self._dict_cpu_info[self._KEY_L1D_CACHE_SIZE]

    def get_l1i_cache_size(self):
        """
        To get the L1i Cache Size in system
        example string : L1i cache: 768 KiB

        :return: L1i cache Size
        """
        return self._dict_cpu_info[self._KEY_L1I_CACHE_SIZE]

    def get_l2_cache_size(self):
        """
        To get the L2 Cache Size in system
        example string : L2 cache: 30 MiB

        :return: L2 cache Size
        """
        l2_cache_size = self._dict_cpu_info[self._KEY_L2_CACHE_SIZE]
        l2_cache = int(re.sub('\D', '', l2_cache_size))
        if "K" in l2_cache_size:
            l2_cache_size = l2_cache / 1024
        else:
            l2_cache_size = l2_cache
        return l2_cache_size

    def get_l3_cache_size(self):
        """
        To get the L3 Cache Size in system
        example string :L3 cache: 36 MiB


        :return: L3 cache Size
        """
        l3_cache_size = self._dict_cpu_info[self._KEY_L3_CACHE_SIZE]
        l3_cache = int(re.sub('\D', '', l3_cache_size))
        if "K" in l3_cache_size:
            l3_cache_size = l3_cache / 1024
        else:
            l3_cache_size = l3_cache
        return l3_cache_size

    def get_virtualization_data(self):
        """
        to get information about virtualization in the system
        example string: Virtualization:VT-x

        :return: string that contains virtualization info
        """
        return self._dict_cpu_info[self._KEY_VIRTUALIZATION]


class CpuInfoProviderWindows(CpuInfoProvider):
    _WINDOWS_CMD_NUMBER_OF_SOCKETS = "wmic cpu get SocketDesignation /format:list"
    _WINDOWS_CMD_FOR_CPU_SOCKET_INFO = "wmic cpu where \"SocketDesignation='{}'\" get * /format:list"
    _COUNTER_PROPERTY = r"'\Processor Information(0,0)\% of Maximum Frequency'"
    _WINDOWS_CMD_CURRENT_FREQUENCY = r'PowerShell "(Get-Counter -Counter {}).CounterSamples.CookedValue"'

    _KEY_MAXCLOCK_SPEED = "MaxClockSpeed"
    _KEY_CURRENT_CLOCKSPEED = "CurrentClockSpeed"
    _KEY_NO_OF_LOGICAL_PROCESSORS = "NumberOfLogicalProcessors"
    _KEY_NO_OF_SOCKETS = 'SocketDesignation'
    _KEY_NO_OF_CORES = 'NumberOfCores'
    _KEY_L2_CACHE_SIZE = 'L2CacheSize'
    _KEY_L3_CACHE_SIZE = 'L3CacheSize'
    _KEY_VIRTUALIZATION = 'VirtualizationFirmwareEnabled'

    _WINDOWS_VIRTUALIZATION_ENABLED_VALUE = 'TRUE'
    _VIRTUALIZATION_ENABLED_DATA = 'VT-x'
    VIRTUALIZATION = 'virtualization_data'

    def __init__(self, log, cfg_opts, os_obj):
        super(CpuInfoProviderWindows, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj
        self._list_cpu_info_dict = []

    def populate_cpu_info(self):
        """
        Calls OS APIs to populate the CPU information.

        :return: None
        """
        self._list_cpu_info_dict.clear()
        self.__populate_cpu_info()

    def __populate_cpu_socket_info(self, cpu_id):
        wmic_query = self._WINDOWS_CMD_FOR_CPU_SOCKET_INFO.format(cpu_id)
        result = self._common_content_obj.execute_sut_cmd(wmic_query, wmic_query,self._command_time_out)
        cpu_info_list = result.strip().split("\n")

        dict_cpu_socket_info = {}
        for cpu_info in cpu_info_list:
            if cpu_info:
                list_cpu_info = cpu_info.split("=")
                if len(list_cpu_info) > 1:
                    dict_cpu_socket_info[list_cpu_info[0]] = str(list_cpu_info[1])

        self._list_cpu_info_dict.append(dict_cpu_socket_info)

    def __get_percent_max_clock_frequency(self):
        # get the current frequency
        cmd_line = self._WINDOWS_CMD_CURRENT_FREQUENCY.format(self._COUNTER_PROPERTY)
        self._log.info("Executing command line '{}'".format(cmd_line))
        ret_val = self._os.execute(cmd_line, 10)
        if ret_val.cmd_failed():
            raise RuntimeError("Failed to get % of max frequency value due to '{}'".format(ret_val.stderr))

        self._log.info("% of maximum frequency value is '{}'".format(ret_val.stdout))
        return ret_val.stdout

    def __populate_cpu_info(self):
        """
        To populate cpu information into a dictionary
        :return: None
        """
        # first get number of sockets
        result = self._common_content_obj.execute_sut_cmd(self._WINDOWS_CMD_NUMBER_OF_SOCKETS,
                                                          self._WINDOWS_CMD_NUMBER_OF_SOCKETS,
                                                          self._command_time_out)
        number_of_sockets = result.strip().split("\n")
        list_socket_id = []
        for socket in number_of_sockets:
            if socket:
                socket_info = socket.split("=")
                if len(socket_info) > 1:
                    list_socket_id.append(socket_info[1])

        self._log.info("Socket ID details: {}".format(list_socket_id))

        for cpu_id in list_socket_id:
            self.__populate_cpu_socket_info(cpu_id)

        self._percent_max_freq = self.__get_percent_max_clock_frequency()

    def get_max_cpu_frequency(self):
        """
        To get the current frequency of CPU in Hertz.
        example string : MaxClockSpeed=2195

        :return: current frequency
        """
        max_freq = 0
        for cpu_socket_dict in self._list_cpu_info_dict:
            if int(cpu_socket_dict[self._KEY_MAXCLOCK_SPEED]) > max_freq:
                max_freq = int(cpu_socket_dict[self._KEY_MAXCLOCK_SPEED])
        return str(max_freq)

    def get_current_cpu_frequency(self):
        """
        To get the current frequency of CPU in Hertz.
        example string :  CurrentClockSpeed=2195

        :return: current frequency
        """
        max_clock_speed = self.get_max_cpu_frequency()
        current_clock_speed = int(max_clock_speed) * int(self._percent_max_freq) / 100
        return current_clock_speed

    def get_logical_processors(self):
        """
        To get the Count of Logical Processors in the system
        example string : NumberOfLogicalProcessors=12
                         NumberOfLogicalProcessors=12

        :return : logical processor count
        """
        logical_processor_count = 0
        for cpu_socket_dict in self._list_cpu_info_dict:
            logical_processor_count = logical_processor_count + \
                                       int(cpu_socket_dict[self._KEY_NO_OF_LOGICAL_PROCESSORS])
        return str(logical_processor_count)

    def get_min_cpu_frequency(self):
        """
        To get the minimum cpu frequency in system
        example string :

        :raise NotImplementedError
        """
        # TODO: Windows does not expose minimum frequency, hence returning current frequency
        max_clock_speed = self.get_max_cpu_frequency()
        current_clock_speed = int(max_clock_speed) * int(self._percent_max_freq) / 100
        return current_clock_speed

    def get_number_of_sockets(self):
        """
        To get the Number of Sockets in system
        example string : SocketDesignation=CPU Socket - U3E1
                         SocketDesignation=CPU Socket - U3E2

        :return: Number of Sockets
        """
        return len(self._list_cpu_info_dict)

    def get_numa_node(self):
        return NotImplementedError

    def get_number_of_threads(self):
        return NotImplementedError

    def get_number_of_cores(self):
        """
        To get the Number of cores in system
        example string : NumberOfCores=2
                         NumberOfCores=2

        :return: Number of cores
        """
        total_no_of_cores = 0
        for cpu_socket_dict in self._list_cpu_info_dict:
            total_no_of_cores = total_no_of_cores + \
                                      int(cpu_socket_dict[self._KEY_NO_OF_CORES])
        return str(total_no_of_cores)

    def get_l1d_cache_size(self):
        """
        To get the L1d Cache Size in system

        :raise NotImplementedError
        """
        raise NotImplementedError

    def get_l1i_cache_size(self):
        """
        To get the L1i Cache Size in system

        :raise NotImplementedError
        """
        raise NotImplementedError

    def get_l2_cache_size(self):
        """
        To get the L2 Cache Size in system
        example string : L2CacheSize=278

        :return: L2 cache Size
        """
        l2cachesize = 0
        for cpu_socket_dict in self._list_cpu_info_dict:
            l2cachesize = l2cachesize + \
                                int(cpu_socket_dict[self._KEY_L2_CACHE_SIZE])
        # convert to MB
        l2cachesize = int(l2cachesize)/1024
        return str(l2cachesize)

    def get_l3_cache_size(self):
        """
        To get the L3 Cache Size in system
        example string : L3CacheSize=3072

        :return: L3 cache Size
        """
        l3cachesize = 0
        for cpu_socket_dict in self._list_cpu_info_dict:
            l3cachesize = l3cachesize + \
                          int(cpu_socket_dict[self._KEY_L3_CACHE_SIZE])
        # convert to MB
        l3cachesize = int(l3cachesize)/1024
        return str(l3cachesize)

    def get_virtualization_data(self):
        """
        To get information about virtualization in the system
        example string : VirtualizationFirmwareEnabled=FALSE

        :return: string that contains the virtualization data
        """
        virtualization_data = self._list_cpu_info_dict[0][self._KEY_VIRTUALIZATION]
        if virtualization_data == self._WINDOWS_VIRTUALIZATION_ENABLED_VALUE:
            virtualization_data = self._VIRTUALIZATION_ENABLED_DATA

        return virtualization_data

    def get_number_of_cores_per_socket(self):
        """
        To get the Number of Cores per Socket in system
        example string : Core(s) per socket: 12

        :return: Number of cores
        """
        raise NotImplementedError
