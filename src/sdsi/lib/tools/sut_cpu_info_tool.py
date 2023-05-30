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
"""Tool which provides functionality to fetch information about the SUT CPU.

    Typical usage example:
        self.platform_info_tool: SutCpuInfoTool = SutCpuInfoTool.factory(self._log, self.os, config)
        self.num_sockets = self.platform_info_tool.get_number_of_sockets()
"""
from abc import ABCMeta, abstractmethod
from logging import Logger
from typing import Dict
from xml.etree.ElementTree import Element

from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.providers.sut_os_provider import SutOsProvider

from src.sdsi.lib.tools.sut_os_tool import SutOsTool


class SutCpuInfoTool(metaclass=ABCMeta):
    """
    Class to provide information about the SUT CPU.
    This Class is an abstract base class which cannot be initialized, but provides an interface for subclasses for
    OS-specific implementation. Subclasses are dynamic, and initialized with SutCpuInfoTool.factory
    """

    def __init__(self, log: Logger, sut_os: SutOsProvider, config: Element) -> None:
        """Initialize the Cpu Info tool.

        Args:
            log: logger to use for test logging.
            sut_os: OS provider used for test content to interact with SUT.
            config: configuration options for test content.
        """
        self._log = log
        self._os = sut_os
        self._config = config
        self._sut_os_tool: SutOsTool = SutOsTool(log, sut_os)

    @staticmethod
    def factory(log: Logger, sut_os: SutOsProvider, config: Element):
        """Factory method to dynamically create corresponding CpuInfoTool object based on the platform type.

        Args:
            log: logger to use for test logging.
            sut_os: OS provider used for test content to interact with SUT.
            config: configuration options for test content.

        Return:
            PlatformInfoTool: Subclass specific to the SUT platform OS.
        """
        if OperatingSystems.LINUX == sut_os.os_type: return SutCpuInfoToolLinux(log, sut_os, config)
        # TODO - Implement tool for Windows SUT OS
        raise NotImplementedError

    @abstractmethod
    def get_max_cpu_frequency(self) -> float:
        """Abstract method for fetching the max cpu frequency from the SUT."""

    @abstractmethod
    def get_current_cpu_frequency(self) -> float:
        """Abstract method for fetching the current cpu frequency from the SUT."""

    @abstractmethod
    def get_min_cpu_frequency(self) -> float:
        """Abstract method for fetching the min cpu frequency from the SUT."""

    @abstractmethod
    def get_logical_processors(self) -> int:
        """Abstract method for fetching the number of logical processors from the SUT."""

    @abstractmethod
    def get_number_of_sockets(self) -> int:
        """Abstract method for fetching the number of sockets from the SUT."""

    @abstractmethod
    def get_number_of_cores(self) -> int:
        """Abstract method for fetching the total number of cores from the SUT."""

    @abstractmethod
    def get_number_of_cores_per_socket(self) -> int:
        """Abstract method for fetching the number of cores per socket from the SUT."""

    @abstractmethod
    def get_number_of_threads(self) -> int:
        """Abstract method for fetching the number of threads from the SUT."""

    @abstractmethod
    def get_l1d_cache_size(self) -> str:
        """Abstract method for fetching the l1d cache size from the SUT."""

    @abstractmethod
    def get_l1i_cache_size(self) -> str:
        """Abstract method for fetching the l1i cache size from the SUT."""

    @abstractmethod
    def get_l2_cache_size(self) -> str:
        """Abstract method for fetching the l2 cache size from the SUT."""

    @abstractmethod
    def get_l3_cache_size(self) -> str:
        """Abstract method for fetching the l3 cache size from the SUT."""

    @abstractmethod
    def get_virtualization_data(self) -> str:
        """Abstract method for fetching virtualization data from the SUT."""

    @abstractmethod
    def get_numa_node(self) -> int:
        """Abstract method for fetching numa node from the SUT."""

    @abstractmethod
    def get_cpu_stepping(self) -> int:
        """Abstract method for fetching the cpu stepping from the SUT."""


class SutCpuInfoToolLinux(SutCpuInfoTool):
    """Linux-Implementation of a class to provide information about the SUT CPU."""

    def _get_cpu_info(self) -> Dict[str, str]:
        """Run a command to fetch cpu info from the Linux Os.

        Returns:
            Dict[str, str]: CPU Information {info_key: info_value}
        """
        cpu_info_list = self._sut_os_tool.execute_cmd("lscpu").strip().split("\n")
        cpu_info = {i.split(":")[0].strip(): i.split(":")[1].strip() for i in cpu_info_list}
        return cpu_info

    def get_max_cpu_frequency(self) -> float:
        """Get the maximum cpu frequency from the SUT.

        Returns:
            float: maximum cpu frequency in MHz.
        """
        return float(self._get_cpu_info()['CPU max MHz'])

    def get_current_cpu_frequency(self) -> float:
        """Get the current cpu frequency from the SUT.

        Returns:
            float: current cpu frequency in MHz.
        """
        return float(self._get_cpu_info()['CPU MHz'])

    def get_min_cpu_frequency(self) -> float:
        """Get the minimum cpu frequency from the SUT.

        Returns:
            float: minimum cpu frequency in MHz.
        """
        return float(self._get_cpu_info()['CPU min MHz'])

    def get_logical_processors(self) -> int:
        """Get the number of logical processors in system.

        Returns:
            int: Logical processor count
        """
        return int(self._get_cpu_info()['CPU(s)'])

    def get_number_of_sockets(self) -> int:
        """Get the number of sockets on the system.

        Returns:
            int: Socket count
        """
        return int(self._get_cpu_info()['Socket(s)'])

    def get_number_of_cores(self) -> int:
        """Get the number of cores on the system.

        Returns:
            int: Core count
        """
        return int(self.get_number_of_sockets() * self.get_number_of_cores_per_socket())

    def get_number_of_cores_per_socket(self) -> int:
        """Get the number of cores per sockets on the system.

        Returns:
            int: Core count per socket
        """
        return int(self._get_cpu_info()['Core(s) per socket'])

    def get_number_of_threads(self) -> int:
        """Get the number of threads on the system.

        Returns:
            int: numbers of threads on the system
        """
        info = self._get_cpu_info()
        return int(info['Thread(s) per core']) * self.get_number_of_cores_per_socket() * self.get_number_of_sockets()

    def get_l1d_cache_size(self) -> str:
        """Get the L1d cache size on the SUT.

        Returns:
            str: The l1d cache size, Ex format: 48K
        """
        return self._get_cpu_info()['L1d cache']

    def get_l1i_cache_size(self) -> str:
        """Get the L1i cache size on the SUT.

        Returns:
            str: The l1i cache size, Ex format: 32K
        """
        return self._get_cpu_info()['L1i cache']

    def get_l2_cache_size(self) -> str:
        """Get the l2 cache size on the SUT.

        Returns:
            str: The l2 cache size, Ex format: 2048K
        """
        return self._get_cpu_info()['L2 cache']

    def get_l3_cache_size(self) -> str:
        """Get the l3 cache size on the SUT.

        Returns:
            str: The l3 cache size, Ex format: 107520K
        """
        return self._get_cpu_info()['L3 cache']

    def get_virtualization_data(self) -> str:
        """Get the virtualization data from the SUT.

        Returns:
            str: The virtualization data, Ex format: VT-x
        """
        return self._get_cpu_info()['Virtualization']

    def get_numa_node(self) -> int:
        """Get the numa node number from the SUT.

        Returns:
            int: The numa node number
        """
        return int(self._get_cpu_info()['NUMA node(s)'])

    def get_cpu_stepping(self) -> int:
        """Get the CPU stepping of the system

        Returns:
            int: The CPU stepping of the system
        """
        return int(self._get_cpu_info()['Stepping'])
