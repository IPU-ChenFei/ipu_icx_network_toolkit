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
import subprocess
import time
from abc import ABCMeta, abstractmethod, ABC
from importlib import import_module
from xml.etree import ElementTree

from dtaf_core.providers.provider_factory import ProviderFactory
from six import add_metaclass

from dtaf_core.lib.dtaf_constants import OperatingSystems
from src.lib import content_exceptions
from src.lib.install_collateral import InstallCollateral
from src.provider.base_provider import BaseProvider
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib.common_content_lib import Sut2UserWin
from src.lib.common_content_lib import VmUserLin

@add_metaclass(ABCMeta)
class NetworkProvider(BaseProvider):
    """Network provider for Fetching Network Interface Name, System IP and Changing Network Adapter State"""

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new NetworkProvider object.

        :param os_obj: os object
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment
        :param log: Logger object to use for output messages
        """
        super(NetworkProvider, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj
        self._sut_os = self._os.os_type
        self._common_content_lib = CommonContentLib(log, os_obj, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)

    @staticmethod
    def factory(log, cfg_opts, os_obj):
        """
        To create a factory object based on the configuration xml file.

        :return: object
        """
        package = r"src.provider.network_provider"
        if OperatingSystems.WINDOWS == os_obj.os_type:
            mod_name = "WindowsNetworkProvider"
        elif OperatingSystems.LINUX == os_obj.os_type:
            mod_name = "LinuxNetworkProvider"
        else:
            raise NotImplementedError("Test is not implemented for %s" % os_obj.os_type)
        mod = import_module(package, mod_name)
        aclass = getattr(mod, mod_name)
        return aclass(cfg_opts=cfg_opts, log=log, os_obj=os_obj)

    @abstractmethod
    def get_network_interface_name(self):
        """
        This method is used to get network interface name.

        :raise: content_exceptions
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def change_network_adapter_status(self, status):
        """
        This Method is Used to Enable/Disable Network Adapter

        :param status: Enable/Disable
        :raise: content_exceptions
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def get_sut_ip(self):
        """
        This Method is Used to Get System IP.

        :raise: content_exceptions
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def is_sut_pingable(self):
        """
        This Method is Used to Verify the Connectivity of System Pinging Sut IP.

        :raise: content_exceptions
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def get_network_adapter_interfaces(self, assign_static_ip=False):
        """
        This Method is Used to Get Network Adapter Interface Dict which contains Interface Names as Keys and
        associated Ip Address as Values.

        :assign_static_ip: True if needs to assign static ip else False
        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def get_network_interface_ip_list(self):
        """
        This Method is Used to Get Network Adapter Interface IP's.

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def disable_network_adapter_and_ping(self, assign_static_ip=False):
        """
        This Method is Used to Disable Network Adapter and Ping Ip Address of Network Interface.

        :param assign_static_ip: If Flag is  set to True Static Ip will be assigned.
        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def enable_network_adapter_and_ping(self):
        """
        This Method is Used to Enable Network Adapter and Ping Ip Address of Network Interface after Enabling
        Network Adapter.

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def ping_network_adapter_ip(self, ip_address=None):
        """
        This Method is Used to Ping Network Adapter IP Address

        :ip_address: Ip Address of Network Adapter
        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def reset_virtual_network_adapters(self):
        """
        This Method is Used to Reset Virtual Network Adapters.

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def assign_static_ipv6_address_to_virtual_interfaces_and_ping(self):
        """
        This Method is Usd to Assign Static IPv6 Address to Virtual Network Interfaces and Ping

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def assign_static_ip_address_to_virtual_interfaces_and_ping(self):
        """
        This Method is used to assign static IP Address to Virtual Network Adapter and Ping.

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def generate_virtual_functions(self, num_of_adapters):
        """
        This Method is Used to Generate Virtual Network Adapters and Verify.

        :num_of_adapters: Number of virtual Adapters to be Generated.
        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def disable_foxville_port(self):
        """
        This Method is Used to Disable Foxville Port.

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def deallocate_static_ip(self):
        """
        This Method is Used to De Allocate Static Ip's assigned to Network Adapter Interfaces.

        :return: None
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def copy_iperf_to_sut1(self):
        """
        This Method is Used to Copy iperf to Sut1.

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def copy_iperf_to_sut2(self):
        """
        This Method is Used to Copy iperf to Sut1.

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def execute_sut1_as_iperf_client(self, exec_time):
        """
        This Method is Used to Copy iperf to Sut1.

        :param exec_time: Iperf Execution Time.
        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def execute_sut2_as_iperf_server(self, exec_time):
        """
        This Method is Used to Copy iperf to Sut1.

        :param exec_time: Iperf Execution Time
        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def create_sut2_os_obj(self):
        """
        This Method is Used to Copy iperf to Sut1.

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def get_sut1_interface_name(self):
        """
        This Method is Used to get Sut1 Interface Name.

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def get_sut2_interface_name(self):
        """
        This Method is Used to get Sut1 Interface Name.

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def assign_static_ipv6_to_sut1_interface(self):
        """
        This Method is Used to Assign Static Ipv6 address to Sut1 Interface.

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def assign_static_ipv6_to_sut2_interface(self):
        """
        This Method is Used to Assign Static Ipv6 address to Sut2 Interface.

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def de_allocate_static_ipv6_from_sut1(self):
        """
        This Method is Used to De Allocate Static IPv6 Address Assigned from Sut1 Interface.

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def de_allocate_static_ipv6_from_sut2(self):
        """
        This Method is Used to De Allocate Static IPv6 Address Assigned from Sut2 Interface.

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def ping_sut1_ipv6_from_sut2(self):
        """
        This Method is Used to Ping Sut1 IPv6 Address from Sut2.

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    @abstractmethod
    def ping_sut2_ipv6_from_sut1(self):
        """
        This Method is Used to Ping Sut2 IPv6 Address from Sut1.

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError


class WindowsNetworkProvider(NetworkProvider, ABC):
    """Windows Network provider object"""
    SYSTEM_IP_COMMAND = "ipconfig"
    REGEX_CMD_FOR_SYSTEM_IP = r"IPv4\sAddress.*:.*192.*"
    NETWORK_INTERFACE_COMMAND = "netsh interface show interface"
    REGEX_CMD_FOR_NETWORK_ADAPTER_NAME = r".*Connected.*"
    NETWORK_ADAPTER_COMMAND = 'netsh interface set interface "{}" {}'
    ENABLE = "Enable"
    DISABLE = "Disable"
    REGEX_CMD_FOR_SUT_PINGABLE = r"Reply\sfrom.*bytes.*time.*"
    REGEX_COMMAND_FOR_ADAPTER = r"Ethernet\sadapter.*"
    REGEX_CMD_FOR_NETWORK_ADAPTER_INTERFACE_IP = r"IPv4\sAddress.*:.*"
    WAITING_TIME_IN_SEC = 30
    ASSIGN_STATIC_IP_CMD = r'netsh interface ipv4 set address name="{}" static 10.10.10.1{} 255.255.255.0 10.10.10.1'
    STATIC_IP = "10.10.10.1{}"
    REMOVE_STATIC_IP_COMMAND = 'netsh interface ip set address "{}" dhcp'
    REGEX_FOR_DATA_LOSS = r".*sec.*0.00.*Bytes.*0.00.*bits.sec$"
    SUT2_CONFIG_FILE = """<?xml version="1.0" encoding="UTF-8"?>
            <sut_os name="Windows" subtype="Win" version="10" kernel="4.2">
                <shutdown_delay>5.0</shutdown_delay>
                <driver>
                    <ssh>
                        <credentials user="{}" password="{}"/>
                        <ipv4>{}</ipv4>
                    </ssh>
                </driver>
            </sut_os>
            """
    REGEX_CMD_FOR_SUT_IP = r"IPv4\sAddress.*{}"
    ASSIGN_STATIC_IPV6_ADDRESS = 'netsh interface ipv6 add address "{}" {}'
    REMOVE_STATIC_IPV6_ADDRESS = 'netsh interface ipv6 delete address "{}" {}'
    REGEX_CMD_FOR_IPv6_PINGABLE = r"Reply\sfrom.*time.*"

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new WindowsNetworkProvider object.

        :param os_obj: os object
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment
        :param log: Logger object to use for output messages
        """
        super(WindowsNetworkProvider, self).__init__(log, cfg_opts, os_obj)
        self._command_timeout = 30
        self.network_interface_name = self.get_network_interface_name()
        self.sut_ip = self.get_sut_ip()
        self.network_interface_dict = self.get_network_adapter_interfaces()
        self.install_collateral = InstallCollateral(self._log, os_obj, cfg_opts)
        self.cfg_opts = cfg_opts
        self.sut1_ip = self._common_content_configuration.get_sut1_ip()
        self.sut2_ip = self._common_content_configuration.get_sut2_ip()
        self.cmd_for_iperf_client = r"iperf3.exe -c {} -t {}"
        self.cmd_for_iperf_server = "iperf3.exe -s -1"
        self.sut_iperf_path = ""
        self.sut2_host_ip = self._common_content_configuration.get_sut2_usb_to_ethernet_ip()
        self.sut1_ipv6_address = self._common_content_configuration.get_sut1_ipv6_address()
        self.sut2_ipv6_address = self._common_content_configuration.get_sut2_ipv6_address()

    def get_network_interface_name(self):
        """
        This method is used to get network interface name.

        :return: network_interface_name
        """
        self._log.info("Fetching Network Interface Name")
        network_interface_cmd_output = self._common_content_lib. \
            execute_sut_cmd(self.SYSTEM_IP_COMMAND,
                            self.SYSTEM_IP_COMMAND,
                            self._command_timeout)
        network_interface_regex = re.compile(self.REGEX_CMD_FOR_SYSTEM_IP)
        network_interface_string = network_interface_regex.search(network_interface_cmd_output).group()
        ip_address_index = [index for index, line in enumerate(network_interface_cmd_output.split("\n"))
                            if network_interface_string in line][0]
        regex_for_adapter = re.compile(self.REGEX_COMMAND_FOR_ADAPTER)
        network_interface_log = network_interface_cmd_output.split("\n")[ip_address_index::-1]
        network_interface_value = regex_for_adapter.search("\n".join(network_interface_log)).group() \
            .strip(":").split(" ")
        network_interface_name = network_interface_value[-1] if "Ethernet" == network_interface_value[-1] else \
            "Ethernet {}".format(network_interface_value[-1].strip(":\r"))
        return network_interface_name

    def get_sut_ip(self):
        """
        This Method is Used to Get System Ip.

        :return: sys_ip_value
        """
        self._log.info("Fetching SUT Ip")
        sys_ip_cmd = self._common_content_lib.execute_sut_cmd(self.SYSTEM_IP_COMMAND, "SUT IP Command",
                                                              self._command_timeout)
        sys_ip_string = re.compile(self.REGEX_CMD_FOR_SYSTEM_IP)
        sys_ip_value = sys_ip_string.search(sys_ip_cmd).group().strip().split(":")[1].strip()
        self._log.debug("SUT IP is : {}".format(sys_ip_value))
        return sys_ip_value

    def change_network_adapter_status(self, status):
        """
        This Method is Used to Enable/Disable Network Adapter.

        :param status: Enable/Disable
        :return: None
        """
        self._log.info("{} the Network Adapter".format("Enabling" if status == self.ENABLE else "Disabling"))
        self._common_content_lib.execute_sut_cmd(self.NETWORK_ADAPTER_COMMAND.format(
            self.network_interface_name, status),
            "Change the Status of Network Adapter Command",
            self._command_timeout)
        self._log.info("Network Adapter is {} Successfully".format("Enabled" if status == self.ENABLE else "Disabled"))

    def is_sut_pingable(self):
        """
        This Method is Used to Verify the Connectivity of System Pinging Sut IP.

        :return: True or False
        """
        self._log.debug("Verify the Connectivity of the SUT by Pinging SUT Ip")
        ping_command = r"ping " + self.sut_ip
        result = self._os.execute(ping_command, self._command_timeout).stdout
        self._log.info("ping result for ip '{}' = {}".format(self.sut_ip, str(result)))
        if re.findall(self.REGEX_CMD_FOR_SUT_PINGABLE, "".join(result)):
            self._log.info("Sut is Pinging and Reachable")
            return True
        self._log.error("Error - ping " + self.sut_ip + " failed")
        return False

    def get_network_adapter_interfaces(self, assign_static_ip=False):
        """
        This Method is Used to Get Network Adapter Interface Dict which contains Interface Names as Keys and
        associated Ip Address as Values.

        :return: network_interface_dict
        """
        self._log.info("Fetching Network Adapter Interface Name")
        network_interface_cmd_output = self._common_content_lib.execute_sut_cmd(self.NETWORK_INTERFACE_COMMAND,
                                                                                self.NETWORK_INTERFACE_COMMAND,
                                                                                self._command_timeout)
        network_interface_string = re.compile(self.REGEX_CMD_FOR_NETWORK_ADAPTER_NAME)
        network_interface_value = network_interface_string.findall(network_interface_cmd_output)
        network_interface_list = [interface.split("  ")[-1] for interface in network_interface_value]
        if self.network_interface_name in network_interface_list:
            network_interface_list.remove(self.network_interface_name)
        network_interface_dict = {}
        if assign_static_ip:
            self._log.info("Assigning Static IP's to Network Adapter Interfaces.")
            for index in range(len(network_interface_list)):
                self._log.debug("Assigning IP {} to Interface {}".format(self.STATIC_IP.format(index),
                                                                         network_interface_list[index]))
                self._common_content_lib.execute_sut_cmd(self.ASSIGN_STATIC_IP_CMD.format(network_interface_list[index],
                                                                                          index),
                                                         "Assigning Static IP",
                                                         self._command_timeout)
                network_interface_dict[network_interface_list[index]] = self.STATIC_IP.format(index)
            self._log.info("Network Interface Dict after assigning static ip address is :{}"
                           .format(network_interface_dict))
            return network_interface_dict

        system_ip = self.get_network_interface_ip_list()
        for index in range(len(network_interface_list)):
            self._log.debug("Network Adapter Interface Name for IP {} is {}".format(system_ip,
                                                                                    network_interface_list[index]))
            network_interface_dict[network_interface_list[index]] = system_ip
        self._log.info("Network Interface Dict is {}".format(network_interface_dict))
        return network_interface_dict

    def ping_network_adapter_ip(self, ip_address=None):
        """
        This Method is Used to Ping Network Adapter IP Address

        :ip_address: Ip Address of Network Adapter
        :return: True or False
        """
        self._log.debug("Verify the Connectivity of the Network Adapter by Pinging Ip")
        adapter_ip = ip_address if ip_address else list(self.network_interface_dict.values())[0]
        ping_command = r"ping " + adapter_ip
        result = self._os.execute(ping_command, self._command_timeout).stdout
        self._log.info("ping result for ip '{}' = {}".format(adapter_ip, str(result)))
        if re.findall(self.REGEX_CMD_FOR_SUT_PINGABLE, "".join(result)):
            self._log.info("Network Adapter is Pinging and Reachable")
            return True
        self._log.error("Error - ping " + adapter_ip + " failed")
        return False

    def get_network_interface_ip_list(self):
        """
        This Method is Used to Get Network Adapter Interface IP's.

        :return: sys_ip_list
        """
        self._log.info("Get Network Adapter Interface Ip's")
        sys_ip_output = self._common_content_lib.execute_sut_cmd(self.SYSTEM_IP_COMMAND, self.SYSTEM_IP_COMMAND,
                                                                 self._command_timeout)

        ip_string = re.compile(self.REGEX_CMD_FOR_NETWORK_ADAPTER_INTERFACE_IP)
        ip_value = ip_string.findall(sys_ip_output)
        ip_list = [ip_address.split(":")[-1].strip() for ip_address in ip_value]
        if self.sut_ip in ip_list:
            ip_list.remove(self.sut_ip)
        self._log.debug("Adapter Ip is : {}".format(ip_list[0]))
        return ip_list[0]

    def disable_network_adapter_and_ping(self, assign_static_ip=False):
        """
        This Method is Used to Disable Network Adapter and Ping Ip Address of Network Interface.

        :param assign_static_ip: Raises Flag if static ip needs to set
        :return: None
        :raise content_exceptions.TestFail: if Ip Address is Pinging after Disabling Network Interface.
        """
        self._log.info("Disabling Network Adapter")
        if assign_static_ip:
            self.network_interface_dict = self.get_network_adapter_interfaces(assign_static_ip=True)
        network_interface = list(self.network_interface_dict.keys())[0]
        network_ip = self.network_interface_dict[network_interface]
        self._common_content_lib.execute_sut_cmd(self.NETWORK_ADAPTER_COMMAND.format(network_interface,
                                                                                     self.DISABLE),
                                                 "Disabling Network Adapter", self._command_timeout)
        self._log.debug("Network Adapter is Successfully Disabled")
        time.sleep(self.WAITING_TIME_IN_SEC)
        ping_command = r"ping " + network_ip
        result = self._os.execute(ping_command, self._command_timeout).stdout
        self._log.info("ping result for ip '{}' = {}".format(network_ip, str(result)))
        if re.findall(self.REGEX_CMD_FOR_SUT_PINGABLE, "".join(result)):
            raise content_exceptions.TestFail("System is Pinging Even After Disabling Network Adapter")
        self._log.info("System is Not Pinging as expected After Disabling Network Adapter")

    def enable_network_adapter_and_ping(self):
        """
        This Method is Used to Enable Network Adapter and Ping Ip Address of Network Interface after Enabling
        Network Adapter.

        :return: None
        :raise content_exceptions.TestFail: if unable to ping Ip Address after enabling Network Interface.
        """
        self._log.info("Enable Network Adapter")
        network_interface = list(self.network_interface_dict.keys())[0]
        network_ip = self.network_interface_dict[network_interface]
        self._common_content_lib.execute_sut_cmd(self.NETWORK_ADAPTER_COMMAND.format(network_interface,
                                                                                     self.ENABLE),
                                                 "Enabling Network Adapter", self._command_timeout)
        self._log.debug("Network Adapter is Successfully Enabled")
        time.sleep(self.WAITING_TIME_IN_SEC)
        ping_command = r"ping " + network_ip
        result = self._os.execute(ping_command, self._command_timeout).stdout
        self._log.info("ping result for ip '{}' = {}".format(network_ip, str(result)))
        if not re.findall(self.REGEX_CMD_FOR_SUT_PINGABLE, "".join(result)):
            raise content_exceptions.TestFail("System is Not Pinging Even After Enabling Network Adapter")
        self._log.info("System is Pinging as expected After Enabling Network Adapter")

    def reset_virtual_network_adapters(self):
        """
        This Method is Used to Reset Virtual Network Adapters.

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    def assign_static_ipv6_address_to_virtual_interfaces_and_ping(self):
        """
        This Method is Usd to Assign Static IPv6 Address to Virtual Network Interfaces and Ping

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    def assign_static_ip_address_to_virtual_interfaces_and_ping(self):
        """
        This Method is used to assign static IP Address to Virtual Network Adapter and Ping.

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    def generate_virtual_functions(self, num_of_adapters):
        """
        This Method is Used to Generate Virtual Network Adapters and Verify.

        :num_of_adapters: Number of virtual Adapters to be Generated.
        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    def copy_iperf_to_sut1(self):
        """
        This Method is Used to Copy iperf to Sut1.

        :raise: content_exceptions.TestNotImplementedError
        """
        self.sut_iperf_path = self.install_collateral.install_iperf_on_windows()

    def copy_iperf_to_sut2(self):
        """
        This Method is Used to Copy Iperf tool to Sut1.
        """
        self._log.info("Copying Iperf Tool to SUT2")
        sut2_os_obj = self.create_sut2_os_obj()
        sut2_install_collateral = InstallCollateral(self._log, sut2_os_obj, self.cfg_opts)
        sut2_common_content_lib = CommonContentLib(self._log, sut2_os_obj, self.cfg_opts)
        sut2_install_collateral.install_iperf_on_windows(common_content_lib=sut2_common_content_lib)

    def execute_sut1_as_iperf_client(self, exec_time):
        """
        This Method is Used to Execute Sut1 as a Iperf Client and Verify Whether there is any Data Loss at Client Side.

        :param exec_time: Iperf Execution Time.
        :raise content_exceptions.TestFail: If there is any Data Loss at Client Side.
        """
        self._log.info("Set Sut1 as Iperf Client")
        cmd_output = self._common_content_lib.execute_sut_cmd(self.cmd_for_iperf_client.format(self.sut2_ip, exec_time),
                                                              "Command for Iperf Client",
                                                              self._command_timeout+exec_time,
                                                              cmd_path=self.sut_iperf_path)
        self._log.debug("Sut1 is Successfully Set as Iperf Client and Iperf Response from Client is : {}".format(
            cmd_output))
        if re.search(self.REGEX_FOR_DATA_LOSS, cmd_output):
            raise content_exceptions.TestFail("Data Loss is Observed at Client Side")
        self._log.info("There is No Data Loss at Client Side")

    def execute_sut2_as_iperf_server(self, exec_time):
        """
        This Method is Used to execute Sut2 as Iperf Server and verify whether there is any Data Loss at Server Side.

        :param exec_time: Iperf Execution Time.
        :raise content_exceptions.TestFail: If there is any Data Loss at Server Side.
        """
        self._log.info("Set Sut2 as Iperf Server")
        sut2_os_obj = self.create_sut2_os_obj()
        sut2_common_content_lib = CommonContentLib(self._log, sut2_os_obj, self.cfg_opts)
        cmd_output = sut2_common_content_lib.execute_sut_cmd(self.cmd_for_iperf_server, self.cmd_for_iperf_server,
                                                             exec_time + self._command_timeout,
                                                             cmd_path=self.sut_iperf_path)
        self._log.debug("Sut2 is Successfully Set as Iperf Server and Iperf Response from Server is : {}".format(
            cmd_output))
        if re.search(self.REGEX_FOR_DATA_LOSS, cmd_output):
            raise content_exceptions.TestFail("Data Loss is Observed at Server Side")
        self._log.info("There is No Data Loss at Server Side")

    def create_sut2_os_obj(self):
        """
        This Method is Used to Create Sut2 Os Obj

        :return: sut2_os_obj
        """
        self._log.info("Creating Sut2 Os Object")
        sut2_cfg_opts = ElementTree.fromstring(self.SUT2_CONFIG_FILE.format(Sut2UserWin.USER, Sut2UserWin.PWD,
                                                                            self.sut2_host_ip))
        sut2_os_obj = ProviderFactory.create(sut2_cfg_opts, self._log)
        self._log.info("Sut2 Os object is Created Successfully.")
        return sut2_os_obj

    def disable_foxville_port(self):
        """
        This Method is Used to Disable Foxville Port.

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    def deallocate_static_ip(self):
        """
        This Method is Used to De Allocate Static Ip's assigned to Network Adapter Interfaces.

        :return: None
        """
        network_interface_list = list(self.network_interface_dict.keys())
        try:
            for interface in network_interface_list:
                self._log.info("De Allocating Static Ip to Interface {}".format(interface))
                self._common_content_lib.execute_sut_cmd(self.REMOVE_STATIC_IP_COMMAND.format(interface),
                                                         "De Allocating Static IP", self._command_timeout)
                self._log.info("Static Ip's are De Allocated Successfully")
        except RuntimeError:
            self._log.debug("There are No Static IP's allocated to these interfaces")

    def get_sut1_interface_name(self):
        """
        This Method is Used to get Sut1 Interface Name.

        :return network_interface_name: Interface Name of Sut1.
        """
        self._log.info("Fetching Sut1 Network Interface name")
        interface_cmd_output = self._common_content_lib.execute_sut_cmd(self.SYSTEM_IP_COMMAND,
                                                                        self.SYSTEM_IP_COMMAND, self._command_timeout)
        interface_cmd_value = re.search(self.REGEX_CMD_FOR_SUT_IP.format(self.sut1_ip), interface_cmd_output).group()
        ip_address_index = [index for index, line in enumerate(interface_cmd_output.split("\n"))
                            if interface_cmd_value in line][0]
        interface_log = interface_cmd_output.split("\n")[ip_address_index::-1]
        regex_for_adapter = re.compile(self.REGEX_COMMAND_FOR_ADAPTER)
        network_interface_value = regex_for_adapter.search("\n".join(interface_log)).group() \
            .strip(":").split(" ")
        network_interface_name = network_interface_value[-1] if "Ethernet" == network_interface_value[-1] else \
            "Ethernet {}".format(network_interface_value[-1].strip(":\r"))
        self._log.debug("Sut1 Network Interface Name is : '{}'".format(network_interface_name))
        return network_interface_name

    def get_sut2_interface_name(self):
        """
        This Method is used to get Sut2 Interface Name.

        :return network_interface_name: Interface Name of Sut2.
        """
        self._log.info("Fetching Sut2 Network Interface name")
        sut2_os_obj = self.create_sut2_os_obj()
        sut2_common_content_lib = CommonContentLib(self._log, sut2_os_obj, self.cfg_opts)
        interface_cmd_output = sut2_common_content_lib.execute_sut_cmd(self.SYSTEM_IP_COMMAND,
                                                                       self.SYSTEM_IP_COMMAND, self._command_timeout)
        interface_cmd_value = re.search(self.REGEX_CMD_FOR_SUT_IP.format(self.sut2_ip), interface_cmd_output).group()
        ip_address_index = [index for index, line in enumerate(interface_cmd_output.split("\n"))
                            if interface_cmd_value in line][0]
        interface_log = interface_cmd_output.split("\n")[ip_address_index::-1]
        regex_for_adapter = re.compile(self.REGEX_COMMAND_FOR_ADAPTER)
        network_interface_value = regex_for_adapter.search("\n".join(interface_log)).group() \
            .strip(":").split(" ")
        network_interface_name = network_interface_value[-1] if "Ethernet" == network_interface_value[-1] else \
            "Ethernet {}".format(network_interface_value[-1].strip(":\r"))
        self._log.debug("Sut2 Network Interface Name is : '{}'".format(network_interface_name))
        return network_interface_name

    def assign_static_ipv6_to_sut1_interface(self):
        """
        This Method is Used to Assign Static Ipv6 address to Sut1 Interface.
        """
        self._log.info("Assigning Static IPv6 Address to Sut1 Interface")
        sut1_interface = self.get_sut1_interface_name()
        self._common_content_lib.execute_sut_cmd(
            self.ASSIGN_STATIC_IPV6_ADDRESS.format(sut1_interface, self.sut1_ipv6_address),
            "CMD to Assign Static IPv6 on SUT1", self._command_timeout)
        self._log.debug("Static IPv6 Address '{}' is Assigned to Interface '{}'"
                        .format(self.sut1_ipv6_address, sut1_interface))

    def assign_static_ipv6_to_sut2_interface(self):
        """
        This Method is Used to assign Static IPv6 Address to Sut2 Interface.
        """
        self._log.info("Assigning Static IPv6 Address to Sut2 Interface")
        sut2_interface = self.get_sut2_interface_name()
        sut2_os_obj = self.create_sut2_os_obj()
        sut2_common_content_lib = CommonContentLib(self._log, sut2_os_obj, self.cfg_opts)
        sut2_common_content_lib.execute_sut_cmd(
            self.ASSIGN_STATIC_IPV6_ADDRESS.format(sut2_interface, self.sut2_ipv6_address),
            "CMD to Assign Static IPv6 on SUT2", self._command_timeout)
        self._log.debug("Static IPv6 Address '{}' is Assigned to Interface '{}'"
                        .format(self.sut2_ipv6_address, sut2_interface))

    def de_allocate_static_ipv6_from_sut1(self):
        """
        This Method is Used to De Allocate Static IPv6 Address Assigned from Sut1 Interface.
        """
        self._log.info("De Allocating Static IPv6 Address from Sut1 Interface")
        sut1_interface = self.get_sut1_interface_name()
        self._common_content_lib.execute_sut_cmd(
            self.REMOVE_STATIC_IPV6_ADDRESS.format(sut1_interface, self.sut1_ipv6_address),
            "CMD for De Allocating Static IPv6 Address", self._command_timeout)
        self._log.debug("Static IPv6 Address {} is de allocated from Interface {}"
                        .format(self.sut1_ipv6_address, sut1_interface))

    def de_allocate_static_ipv6_from_sut2(self):
        """
        This Method is Used to De Allocate Static IPv6 Address Assigned from Sut2 Interface.
        """
        self._log.info("De Allocating Static IPv6 Address from Sut2 Interface")
        sut2_os_obj = self.create_sut2_os_obj()
        sut2_common_content_lib = CommonContentLib(self._log, sut2_os_obj, self.cfg_opts)
        sut2_interface = self.get_sut2_interface_name()
        sut2_common_content_lib.execute_sut_cmd(
            self.REMOVE_STATIC_IPV6_ADDRESS.format(sut2_interface, self.sut2_ipv6_address),
            "CMD for De Allocating Static IPv6 Address", self._command_timeout)
        self._log.debug("Static IPv6 Address {} is de allocated from Interface {}"
                        .format(self.sut2_ipv6_address, sut2_interface))

    def ping_sut2_ipv6_from_sut1(self):
        """
        This Method is Used to Ping Sut2 IPv6 Address from Sut1.

        :return True: If Sut2 IPv6 is Pinging from Sut1 else False
        """
        self._log.info("Pinging Sut2 Ipv6 Address from Sut1")
        ping_command = r"ping " + self.sut2_ipv6_address
        result = self._os.execute(ping_command, self._command_timeout).stdout
        self._log.info("ping result for ip '{}' = {}".format(self.sut2_ipv6_address, str(result)))
        if re.findall(self.REGEX_CMD_FOR_IPv6_PINGABLE, "".join(result)):
            self._log.info("Sut2 IPv6 Address is Pinging and Reachable from Sut1")
            return True
        self._log.error("Error - ping " + self.sut2_ipv6_address + " failed")
        return False

    def ping_sut1_ipv6_from_sut2(self):
        """
        This Method is Used to Ping Sut1 IPv6 Address from Sut2.

        :return True: If Sut1 IPv6 is Pinging from Sut2 else False
        """
        self._log.info("Pinging Sut1 Ipv6 Address from Sut2")
        sut2_os_obj = self.create_sut2_os_obj()
        ping_command = r"ping " + self.sut1_ipv6_address
        result = sut2_os_obj.execute(ping_command, self._command_timeout).stdout
        self._log.info("ping result for ip '{}' = {}".format(self.sut1_ipv6_address, str(result)))
        if re.findall(self.REGEX_CMD_FOR_IPv6_PINGABLE, "".join(result)):
            self._log.info("Sut1 IPv6 Address is Pinging and Reachable from Sut2")
            return True
        self._log.error("Error - ping " + self.sut1_ipv6_address + " failed")
        return False


class LinuxNetworkProvider(NetworkProvider, ABC):
    """Linux Network provider object"""

    NETWORK_INTERFACE_COMMAND = "nmcli device status"
    REGEX_CMD_FOR_NETWORK_ADAPTER_NAME = r"ethernet\s.*\s.*"
    NETWORK_ADAPTER_COMMAND = "ifconfig {} {}"
    ENABLE = "up"
    DISABLE = "down"
    SYSTEM_IP_COMMAND = "ifconfig {}"
    REGEX_CMD_FOR_SYSTEM_IP = r"inet.*192.*"
    NETWORK_ADAPTER_INTERFACE_COMMAND = r"ip link show"
    REGEX_FOR_NETWORK_ADAPTER_INTERFACE = r".*ethernet.*\sconnected.*"
    DISABLE_NETWORK_INTERFACE_COMMAND = "nmcli device disconnect {}"
    REGEX_CMD_FOR_ADAPTER_IP_PINGABLE = r".*bytes\sfrom.*icmp_seq.*ttl.*time.*"
    ENABLE_NETWORK_ADAPTER_INTERFACE_COMMAND = "nmcli device connect {}"
    WAITING_TIME_IN_SEC = 30
    ASSIGN_STATIC_IP_COMMAND = r"ifconfig {} {}"
    STATIC_IP = "10.10.10.1{}"
    REMOVE_STATIC_IP_COMMAND = r"ifconfig {} 0.0.0.0"
    REGEX_CMD_FOR_ADAPTER_IP = r"inet.*netmask.*broadcast.*"
    GENERATING_VIRTUAL_ADAPTER_CMD = "echo {} > /sys/class/net/{}/device/sriov_numvfs"
    VERIFYING_VIRTUAL_ADAPTER_CMD = "lspci |grep net"
    REGEX_CMD_FOR_VERIFYING_VIRTUAL_ADAPTER = r".*Ethernet\scontroller.*Virtual\sFunction.*"
    STATIC_IP_FOR_VIRTUAL_ADAPTER = "20.20.20.2{}"
    ASSIGN_STATIC_IPV6_COMMAND = "/sbin/ifconfig {} inet6 add {}/16"
    RESET_VIRTUAL_ADAPTER_CMD = "echo 0 > /sys/class/net/{}/device/sriov_numvfs"
    GET_IPV6_ADDRESS_OF_DRIVER_CMD = "ifconfig {} | grep inet6"
    REGEX_CMD_FOR_IPV6 = "inet6.*"
    FOXVILLE_DEVICE_ID = "15f2"
    CMD_FOR_FOXVILLE_BDF = "lspci | grep {}".format(FOXVILLE_DEVICE_ID)
    CMD_FOR_FOXVILLE_INTERFACE = "lshw -c network -businfo | grep {}"
    REGEX_FOR_DATA_LOSS = r".*sec.*0.00.*Bytes.*0.00.*bits.sec$"
    SUT2_CONFIG_FILE = """<?xml version="1.0" encoding="UTF-8"?>
        <sut_os name="Linux" subtype="RHEL" version="10" kernel="4.2">
            <shutdown_delay>5.0</shutdown_delay>
            <driver>
                <ssh>
                    <credentials user="{}" password="{}"/>
                    <ipv4>{}</ipv4>
                </ssh>
            </driver>
        </sut_os>
        """

    def __init__(self, log, cfg_opts, os_obj):
        """
        Create a new LinuxNetworkProvider object.

        :param os_obj: os object
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment
        :param log: Logger object to use for output messages
        """
        super(LinuxNetworkProvider, self).__init__(log, cfg_opts, os_obj)
        self._command_timeout = 300
        self.network_interface_name = self.get_network_interface_name()
        self.sut_ip = self.get_sut_ip()
        self.network_interface_dict = self.get_network_adapter_interfaces()
        self.virtual_network_interface_list = []
        self.cmd_for_iperf_client = r"iperf3 -c {} -t {}"
        self.cmd_for_iperf_server = "iperf3 -s -1"
        self.sut1_ip = self._common_content_configuration.get_sut1_ip()
        self.sut2_ip = self._common_content_configuration.get_sut2_ip()
        self.install_collateral = InstallCollateral(self._log, os_obj, cfg_opts)
        self.cfg_opts = cfg_opts
        self.sut2_host_ip = self._common_content_configuration.get_sut2_usb_to_ethernet_ip()

    def get_network_interface_name(self):
        """
        This method is used to get network interface name by using nmcli device status command

        :return: network_interface_name
        """
        self._log.info("Fetching Network Interface Name")
        network_interface_cmd_output = self._common_content_lib. \
            execute_sut_cmd(self.NETWORK_INTERFACE_COMMAND,
                            self.NETWORK_INTERFACE_COMMAND,
                            self._command_timeout)
        network_interface_string = re.compile(self.REGEX_CMD_FOR_NETWORK_ADAPTER_NAME)
        network_interface_name = " ".join(network_interface_string.search(network_interface_cmd_output).group().strip()
                                          .split("\n")[0].strip().split()).split(" ")[2]
        self._log.debug("Network Interface name is {}".format(network_interface_name))
        return network_interface_name

    def change_network_adapter_status(self, status):
        """
        This Method is Used to Enable/Disable Network Adapter

        :param status: Enable/Disable
        """
        self._log.info("{} the Foxville Network Adapter".format("Enabling" if status == self.ENABLE else "Disabling"))
        self._common_content_lib.execute_sut_cmd(self.NETWORK_ADAPTER_COMMAND.format(
            self.network_interface_name, status),
            "Change the Status of Network Adapter Command",
            self._command_timeout)
        self._log.info("Network Adapter is {} Successfully".format("Enabled" if status == self.ENABLE else "Disabled"))

    def get_sut_ip(self):
        """
        This Method is Used to Get System Ip through Ifconfig Command.

        :return: sys_ip_value
        :raise content_exceptions.TestSetupError: If System is not Configured with 192 Series IP Address.
        """
        self._log.info("Fetching SUT Ip")
        interface_list = self.get_network_interfaces()
        for interface in interface_list:
            sys_ip_cmd = self._common_content_lib.execute_sut_cmd(
                self.SYSTEM_IP_COMMAND.format(interface), "SUT IP Command",
                self._command_timeout)
            sys_ip_string = re.compile(self.REGEX_CMD_FOR_SYSTEM_IP)
            if sys_ip_string.search(sys_ip_cmd):
                sys_ip_value = sys_ip_string.search(sys_ip_cmd).group().strip().split(" ")[1]
                self.network_interface_name = interface
                self._log.debug("Network Interface is {}".format(interface))
                self._log.debug("SUT IP is : {}".format(sys_ip_value))
                return sys_ip_value
        raise content_exceptions.TestSetupError("System does not have 192 Series Ip Address as part of P2P Connection")

    def is_sut_pingable(self):
        """
        This Method is Used to Verify the Connectivity of System Pinging Sut IP.

        :return: True or False
        """
        self._log.debug("Verify the Connectivity of the SUT by Pinging SUT Ip")
        ping_command = r"ping " + self.sut_ip
        result = subprocess.call(ping_command)
        self._log.info("ping result for ip '{}' = {}".format(self.sut_ip, str(result)))
        if result != 0:
            self._log.error("Error - ping " + self.sut_ip + " failed")
            return False
        self._log.info("Sut is Pinging and Reachable")
        return True

    def get_network_interfaces(self):
        """
        This Method is Used to Get Network Adapter Interface Names.

        :return: network_interfaces_list
        """
        self._log.info("Fetching Network Adapter Interface Name")
        network_interface_cmd_output = self._common_content_lib. \
            execute_sut_cmd(self.NETWORK_INTERFACE_COMMAND,
                            self.NETWORK_INTERFACE_COMMAND,
                            self._command_timeout)
        network_interface_regex = re.compile(self.REGEX_FOR_NETWORK_ADAPTER_INTERFACE)
        network_interface_string = network_interface_regex.findall(network_interface_cmd_output)
        network_interfaces_list = [line.split(" ")[0].strip() for line in network_interface_string]
        self._log.debug("Network Adapter Interface's are {}".format(", ".join(network_interfaces_list)))
        return network_interfaces_list

    def get_network_interface_ip_list(self):
        """
        This Method is Used to Get Network Adapter Interface IP's.

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    def disable_network_adapter_and_ping(self, assign_static_ip=False):
        """
        This Method is Used to Disable Network Adapter and Ping Ip Address of Network Interface.

        :param assign_static_ip: Will Assign Static Ip if flag set to True
        :return: None
        :raise content_exceptions.TestFail: if Ip Address is Pinging after disabling Network Interface.
        """
        if assign_static_ip:
            self.network_interface_dict = self.get_network_adapter_interfaces(assign_static_ip=True)
        network_interface = list(self.network_interface_dict.keys())[0]
        self._log.info(
            "Disabling the Network Adapter and ping ip address of Network Interface {}".format(network_interface))
        ip_address = self.network_interface_dict[network_interface]
        self._log.info("Disabling Network Adapter {}".format(network_interface))
        self._common_content_lib.execute_sut_cmd(self.DISABLE_NETWORK_INTERFACE_COMMAND.format(network_interface),
                                                 "Disabling Network Adapter", self._command_timeout)
        self._log.debug("Network Adapter Interface {} is Disabled".format(network_interface))
        time.sleep(self.WAITING_TIME_IN_SEC)
        self._log.info("Verify the Connectivity by Pinging Network Interface Ip")
        ping_command = r"ping " + ip_address + " -c 4"
        result = self._os.execute(ping_command, self._command_timeout).stdout
        self._log.info("ping result for Network Interface Ip '{}' = {}".format(ip_address, str(result)))
        if re.findall(self.REGEX_CMD_FOR_ADAPTER_IP_PINGABLE, "".join(result)):
            raise content_exceptions.TestFail("Ip is Pinging Even after Disabling Network Adapter")
        self._log.info("After Disabling Network Adapter Ip is Not Pinging as Expected")

    def enable_network_adapter_and_ping(self):
        """
        This Method is Used to Enable Network Adapter and Ping Ip Address of Network Interface.

        :return: None
        :raise content_exceptions.TestFail: if unable to ping Ip Address after enabling Network Interface.
        """
        network_interface = list(self.network_interface_dict.keys())[0]
        self._log.info("Enabling Network Adapter and ping IP address of Network Interface {}".format(network_interface))
        ip_address = self.network_interface_dict[network_interface]
        self._log.debug("Enabling Network Adapter Interface {}".format(network_interface))
        self._common_content_lib.execute_sut_cmd(
            self.ENABLE_NETWORK_ADAPTER_INTERFACE_COMMAND.format(network_interface),
            "Enabling Network Adapter Static Interface", self._command_timeout)
        self._log.debug("Network Adapter Interface {} is Enabled".format(network_interface))
        time.sleep(self.WAITING_TIME_IN_SEC)
        self._log.info("Verify the Connectivity by Pinging Interface Ip")
        ping_command = r"ping " + ip_address + " -c 4"
        result = self._os.execute(ping_command, self._command_timeout).stdout
        self._log.info("ping result for Static Ip '{}' = {}".format(ip_address, str(result)))
        if not re.findall(self.REGEX_CMD_FOR_ADAPTER_IP_PINGABLE, "".join(result)):
            raise content_exceptions.TestFail("Ip is Not Pinging Even after Enabling Network Adapter")
        self._log.info("After Enabling Network Adapter Ip is Pinging as Expected")

    def get_network_adapter_interfaces(self, assign_static_ip=False):
        """
        This Method is Used to Assign Static IP's to Network Adapter Interfaces and return dictionary of Interfaces
        and Ip Address as Keys and Values.

        :assign_static_ip: True if need to assign static ip else False
        :return: network_interface_dict
        """
        network_interface_list = self.get_network_interfaces()
        if self.network_interface_name in network_interface_list:
            network_interface_list.remove(self.network_interface_name)
        network_interface_dict = {}
        if assign_static_ip:
            for index in range(len(network_interface_list)):
                self._log.info("Assigning Static Ip {} to Interface {}".format(self.STATIC_IP.format(index),
                                                                               network_interface_list[index]))
                self._common_content_lib. \
                    execute_sut_cmd(self.ASSIGN_STATIC_IP_COMMAND.format(network_interface_list[index],
                                                                         self.STATIC_IP.format(index)),
                                    "Assigning Static IP", self._command_timeout)
                network_interface_dict[network_interface_list[index]] = self.STATIC_IP.format(index)
            self._log.info("Static IP's are Assigned to Network Interfaces Successfully")
            self._log.debug("Network Interface Dict is {}".format(network_interface_dict))
            return network_interface_dict
        for interface in network_interface_list:
            self._log.info("Get IP Address assigned to Interface {}".format(interface))
            address = self._common_content_lib.execute_sut_cmd(self.SYSTEM_IP_COMMAND.format(interface),
                                                               self.SYSTEM_IP_COMMAND,
                                                               self._command_timeout)
            ip_string = re.compile(self.REGEX_CMD_FOR_ADAPTER_IP)
            ip_value = ip_string.search(address).group().strip().split(" ")[1] if ip_string.search(address) else ""
            self._log.debug("IP Address for Interface {} is : {}".format(interface, ip_value))
            network_interface_dict[interface] = ip_value
        self._log.info("NetworkInterface Dict is {}".format(network_interface_dict))
        return network_interface_dict

    def deallocate_static_ip(self):
        """
        This Method is Used to De Allocate Static Ip's assigned to Network Adapter Interfaces.

        :return: None
        """
        network_interface_list = list(self.network_interface_dict.keys())
        for ip in network_interface_list:
            self._log.info("De Allocating Static Ip to Interface {}".format(ip))
            self._common_content_lib.execute_sut_cmd(self.REMOVE_STATIC_IP_COMMAND.format(ip),
                                                     "De Allocating Static IP", self._command_timeout)
        self._log.info("Static Ip's are De Allocated Successfully")

    def ping_network_adapter_ip(self, ip_address=None):
        """
        This Method is Used to Ping Network Adapter IP Address

        :ip_address: Ip Address of Network Adapter
        :return: True if Network Interface is pinging else False
        """
        self._log.info("Verify the Connectivity of the Network Adapter by Pinging Ip")
        adapter_ip = ip_address if ip_address else list(self.network_interface_dict.values())[0]
        ping_command = r"ping " + adapter_ip + " -c 4"
        result = self._os.execute(ping_command, self._command_timeout).stdout
        self._log.info("ping result for Network Interface Ip '{}' = {}".format(adapter_ip, str(result)))
        if not re.findall(self.REGEX_CMD_FOR_ADAPTER_IP_PINGABLE, "".join(result)):
            self._log.info("Error - ping " + adapter_ip + " failed")
            return False
        self._log.info("Network Adapter Interface is Pinging and Reachable")
        return True

    def generate_virtual_functions(self, num_of_adapters):
        """
        This Method is Used to Generate Virtual Network Adapters and Verify.

        :num_of_adapters: Number of virtual Adapters to be Generated.
        :raise content_exceptions.TestError: When Virtual Network Adapters are not Generated as Expected.
        """
        self._log.info("Generating {} Virtual Network Adapters".format(num_of_adapters))
        network_interface = list(self.network_interface_dict.keys())[0]
        self._common_content_lib.execute_sut_cmd(self.GENERATING_VIRTUAL_ADAPTER_CMD.
                                                 format(num_of_adapters, network_interface),
                                                 "Command to Generate Virtual Adapters", self._command_timeout)

        cmd_output = self._common_content_lib.execute_sut_cmd(self.VERIFYING_VIRTUAL_ADAPTER_CMD,
                                                              "Verification of Generating Virtual Adapters",
                                                              self._command_timeout)
        if not len(re.findall(self.REGEX_CMD_FOR_VERIFYING_VIRTUAL_ADAPTER, cmd_output)) == num_of_adapters:
            raise content_exceptions.TestError("Virtual Network Adapters are Not Generated as Expected")
        for index in reversed(range(num_of_adapters)):
            self.virtual_network_interface_list.append(network_interface + "v{}".format(index))
        self._log.debug("{} Virtual Network Adapters are Generated".format(num_of_adapters))

    def assign_static_ip_address_to_virtual_interfaces_and_ping(self):
        """
        This Method is used to assign static IP Address to Virtual Network Adapter and Ping.

        :raise content_exceptions.TestError: When Unable to ping Static Ip Address assigned to Virtual Network Adapter.
        """
        self._log.info("Assign Static IP Address to Virtual Network Adapter Interfaces and Ping Static Ip Address")
        time.sleep(self.WAITING_TIME_IN_SEC)
        for index in range(len(self.virtual_network_interface_list)):
            self._log.debug("Assigning Static IP {} to Interface {}"
                            .format(self.STATIC_IP_FOR_VIRTUAL_ADAPTER.format(index),
                                    self.virtual_network_interface_list[index]))
            self._common_content_lib.execute_sut_cmd(self.ASSIGN_STATIC_IP_COMMAND
                                                     .format(self.virtual_network_interface_list[index],
                                                             self.STATIC_IP_FOR_VIRTUAL_ADAPTER.format(index)),
                                                     "Assigning Static IP to Interface", self._command_timeout)
            self._log.debug("Pinging Static IP {} Assigned to Interface {}"
                            .format(self.STATIC_IP_FOR_VIRTUAL_ADAPTER.format(index),
                                    self.virtual_network_interface_list[index]))
            if not self.ping_network_adapter_ip(self.STATIC_IP_FOR_VIRTUAL_ADAPTER.format(index)):
                raise content_exceptions.TestError("Unable to Ping Static Ip Address {} assigned to Virtual "
                                                   "Interface {}".format(self.STATIC_IP_FOR_VIRTUAL_ADAPTER
                                                                         .format(index),
                                                                         self.virtual_network_interface_list[index]))
            self._log.debug("Virtual Network Adapter Interface {} is Pinging as Expected"
                            .format(self.virtual_network_interface_list[index]))

    def assign_static_ipv6_address_to_virtual_interfaces_and_ping(self):
        """
        This Method is Usd to Assign Static IPv6 Address to Virtual Network Interfaces and Ping

        :raise content_exceptions.TestError: When unable to Ping Static IPv6 Address assigned to Network Adapter.
        """
        self._log.info("Assign Static IPv6 Address to Virtual Network Adapter Interfaces and Ping Static IPv6 Address")
        ipv6_address = self.get_ipv6_address_of_driver()
        time.sleep(self.WAITING_TIME_IN_SEC)
        for index in range(len(self.virtual_network_interface_list)):
            self._log.debug("Assigning Static IPv6 {} to Interface {}"
                            .format(ipv6_address[:-1] + str(index),
                                    self.virtual_network_interface_list[index]))
            self._common_content_lib.execute_sut_cmd(self.ASSIGN_STATIC_IPV6_COMMAND
                                                     .format(self.virtual_network_interface_list[index],
                                                             ipv6_address[:-1] + str(index)),
                                                     "Assigning Static IPv6 to Interface", self._command_timeout)
            self._log.debug("Pinging Static IPv6 Address {} Assigned to Interface {}"
                            .format(ipv6_address[:-1] + str(index),
                                    self.virtual_network_interface_list[index]))
            if not self.ping_network_adapter_ip(ip_address=ipv6_address[:-1] + str(index)):
                raise content_exceptions.TestError("Unable to Ping Static IPv6 Address {} assigned to Virtual "
                                                   "Interface {}".format(ipv6_address[:-1] + str(index),
                                                                         self.virtual_network_interface_list[index]))
            self._log.debug("Virtual Network Adapter Interface {} is Pinging as Expected"
                            .format(self.virtual_network_interface_list[index]))

    def reset_virtual_network_adapters(self):
        """
        This Method is Used to Reset Virtual Network Adapters.

        :raise content_exceptions.TestError: When Unable to Reset Virtual Network Adapters to their Default
        """
        self._log.info("Resetting Virtual Network Adapters to there Default Value")
        network_interface = list(self.network_interface_dict.keys())[0]
        self._common_content_lib.execute_sut_cmd(self.RESET_VIRTUAL_ADAPTER_CMD.
                                                 format(network_interface),
                                                 "Command to Reset Virtual Adapters", self._command_timeout)
        cmd_output = self._common_content_lib.execute_sut_cmd(self.VERIFYING_VIRTUAL_ADAPTER_CMD,
                                                              "Verification of Virtual Adapters Count",
                                                              self._command_timeout)
        if re.findall(self.REGEX_CMD_FOR_VERIFYING_VIRTUAL_ADAPTER, cmd_output):
            raise content_exceptions.TestError("Virtual Network Adapters are Not Reset to there Default Value")
        self._log.info("Virtual Network Adapters are Reset to there Default Value")

    def get_ipv6_address_of_driver(self):
        """
        This Method is Used to Get IPv6 Address of Network Driver.

        :return ipv6_address: IPv6 Address of Network Driver.
        """
        self._log.info("Get IPv6 Address of Network Driver")
        interface = list(self.network_interface_dict.keys())[0]
        cmd_output = self._common_content_lib.execute_sut_cmd(self.GET_IPV6_ADDRESS_OF_DRIVER_CMD.format(interface),
                                                              self.GET_IPV6_ADDRESS_OF_DRIVER_CMD,
                                                              self._command_timeout)
        ipv6_address = re.search(self.REGEX_CMD_FOR_IPV6, cmd_output).group().split(" ")[1]
        self._log.debug("IPv6 Address of Network Driver is {}".format(ipv6_address))
        return ipv6_address

    def disable_foxville_port(self):
        """
        This Method is Used to Disable Foxville Port.
        """
        self._log.info("Disabling Foxville Port")
        try:
            foxville_port = self.get_foxville_port_interface()
            self._common_content_lib.execute_sut_cmd(self.DISABLE_NETWORK_INTERFACE_COMMAND.format(foxville_port),
                                                     "Disabling Foxville Port", self._command_timeout)
        except RuntimeError:
            self._log.debug("Foxville Port is Successfully Disabled")

    def get_foxville_bdf(self):
        """
        This Method is Used to get the Bus Device Function (BDF) of Foxville Port Interface.

        :return foxville_bdf: BDF Value of Foxville Port.
        """
        self._log.info("Getting Bdf of Foxville Port Interface")
        cmd_output = self._common_content_lib.execute_sut_cmd(self.CMD_FOR_FOXVILLE_BDF, self.CMD_FOR_FOXVILLE_BDF,
                                                              self._command_timeout)
        foxville_bdf = cmd_output.split(" ")[0]
        self._log.debug("Foxville port Bdf is {}".format(foxville_bdf))
        return foxville_bdf

    def get_foxville_port_interface(self):
        """
        This Method is Used to get the Foxville Port Interface from bdf value.

        :return foxville_interface: Interface of Foxville Port
        """
        self._log.info("Getting Foxville Interface through bdf value")
        bdf_value = self.get_foxville_bdf()
        cmd_output = self._common_content_lib.execute_sut_cmd(self.CMD_FOR_FOXVILLE_INTERFACE.format(bdf_value),
                                                              "CMD for Foxville Interface", self._command_timeout)
        foxville_interface = re.sub(" +", " ", cmd_output).split(" ")[1]
        self._log.debug("Foxville Port Interface is : {}".format(foxville_interface))
        return foxville_interface

    def copy_iperf_to_sut1(self):
        """
        This Method is Used to Copy Iperf tool to Sut1.

        :return iperf_path: Path of Iperf at Sut1.
        """
        self.install_collateral.install_iperf_on_linux()

    def create_sut2_os_obj(self):
        """
        This Method is Used to Create Sut2 Os Obj from Sut2 Credentials.

        :return sut2_os_obj: Os Object for Sut2
        """
        self._log.info("Creating Sut2 Os Object")
        sut2_cfg_opts = ElementTree.fromstring(self.SUT2_CONFIG_FILE.format(VmUserLin.USER, VmUserLin.PWD,
                                                                            self.sut2_host_ip))
        sut2_os_obj = ProviderFactory.create(sut2_cfg_opts, self._log)
        self._log.debug("Sut2 Os object is Created Successfully.")
        return sut2_os_obj

    def copy_iperf_to_sut2(self):
        """
        This Method is Used to Copy Iperf Tool to Sut2
        """
        self._log.info("Copying Iperf Tool to SUT2")
        sut2_os_obj = self.create_sut2_os_obj()
        sut2_install_collateral = InstallCollateral(self._log, sut2_os_obj, self.cfg_opts)
        sut2_install_collateral.install_iperf_on_linux()

    def execute_sut2_as_iperf_server(self, exec_time):
        """
        This Method is Used to Set Sut2 as Iperf Server and verify whether there is any data loss at server side..

        :param exec_time: Iperf Server Execution Time.
        :raise content_exceptions.TestFail: If there is any data loss at Server Side.
        """
        self._log.info("Set Sut2 as Iperf Server")
        sut2_os_obj = self.create_sut2_os_obj()
        sut2_common_content_lib = CommonContentLib(self._log, sut2_os_obj, self.cfg_opts)
        cmd_output = sut2_common_content_lib.execute_sut_cmd(self.cmd_for_iperf_server, self.cmd_for_iperf_server,
                                                             exec_time + self._command_timeout)
        self._log.debug("Sut2 is Successfully Set as Iperf Server and Iperf Response from Server is : {}".format(
            cmd_output))
        if re.search(self.REGEX_FOR_DATA_LOSS, cmd_output):
            raise content_exceptions.TestFail("Data Loss is Observed at Server Side")
        self._log.info("There is No Data Loss at Server Side")

    def execute_sut1_as_iperf_client(self, exec_time):
        """
        This Method is Used to Execute Sut1 as a Iperf Client and Verify Whether there is any Data Loss at Client Side.

        :param exec_time: Iperf Execution Time.
        :raise content_exceptions.TestFail: If there is any Data Loss at Client Side.
        """
        self._log.info("Set Sut1 as Iperf Client")
        cmd_output = self._common_content_lib.execute_sut_cmd(self.cmd_for_iperf_client.format(self.sut2_ip, exec_time),
                                                              self.cmd_for_iperf_client.format(self.sut2_ip, exec_time),
                                                              exec_time + self._command_timeout)
        self._log.debug("Sut1 is Successfully Set as Iperf Client and Iperf Response from Client is : {}".format(
            cmd_output))
        if re.search(self.REGEX_FOR_DATA_LOSS, cmd_output):
            raise content_exceptions.TestFail("Data Loss is Observed at Client Side")
        self._log.info("There is No Data Loss at Client Side")

    def get_sut1_interface_name(self):
        """
        This Method is Used to get Sut1 Interface Name.

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    def get_sut2_interface_name(self):
        """
        This Method is Used to get Sut1 Interface Name.

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    def assign_static_ipv6_to_sut1_interface(self):
        """
        This Method is Used to Assign Static Ipv6 address to Sut1 Interface.

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    def assign_static_ipv6_to_sut2_interface(self):
        """
        This Method is Used to Assign Static Ipv6 address to Sut2 Interface.

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    def de_allocate_static_ipv6_from_sut1(self):
        """
        This Method is Used to De Allocate Static IPv6 Address Assigned from Sut1 Interface.

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    def de_allocate_static_ipv6_from_sut2(self):
        """
        This Method is Used to De Allocate Static IPv6 Address Assigned from Sut2 Interface.

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    def ping_sut1_ipv6_from_sut2(self):
        """
        This Method is Used to Ping Sut1 IPv6 Address from Sut2.

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError

    def ping_sut2_ipv6_from_sut1(self):
        """
        This Method is Used to Ping Sut2 IPv6 Address from Sut1.

        :raise: content_exceptions.TestNotImplementedError
        """
        raise content_exceptions.TestNotImplementedError
