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
import ast

import os
import re
import ast

from importlib import import_module
from abc import ABCMeta, abstractmethod
from six import add_metaclass

from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib import content_exceptions
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib.install_collateral import InstallCollateral
from src.provider.base_provider import BaseProvider
from src.lib.dtaf_content_constants import PcieAttribute, WindowsMemrwToolConstant
from src.lib.dtaf_content_constants import ExecutionEnv
from src.lib.install_collateral import InstallCollateral
from src.lib import content_exceptions


@add_metaclass(ABCMeta)
class PcieProvider(BaseProvider):

    def __init__(self, log, os_obj, uefi_util_obj=None, cfg_opts=None):
        """
        Create a new PcieProvider object.

        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment
        :param log: Logger object to use for output messages
        """
        super(PcieProvider, self).__init__(log, cfg_opts, os_obj)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj
        self._sut_os = self._os.os_type
        self._common_content_config = ContentConfiguration(self._log)
        self._common_content_lib = CommonContentLib(self._log, self._os, self._cfg_opts)
        self._cmd_time_out_in_sec = self._common_content_config.get_command_timeout()
        self._reboot_time_out_in_sec = self._common_content_config.get_reboot_timeout()

    @staticmethod
    def factory(log, os_obj, cfg_opts=None, execution_env=None, uefi_obj=None):
        """
        To create a factory object based on the configuration xml file.

        :return: object
        """
        package = r"src.provider.pcie_provider"
        if execution_env and execution_env not in {ExecutionEnv.OS, ExecutionEnv.ITP, ExecutionEnv.UEFI}:
            raise ValueError("Invalid value has been provided for "
                             "argument 'execution_env'. it should be 'os', 'uefi' or 'itp'")

        #   Getting the required module name
        if execution_env == ExecutionEnv.ITP:
            mod_name = "PcieProviderItp"
        elif execution_env == ExecutionEnv.UEFI:
            if uefi_obj is None:
                raise ValueError('uefi util object can not be empty')

            mod_name = "PcieProviderUefi"
        else:
            if ExecutionEnv.OS == execution_env:
                execution_env = os_obj.os_type.lower()
            if OperatingSystems.WINDOWS == os_obj.os_type:
                mod_name = "PcieProviderWindows"
            elif OperatingSystems.LINUX == os_obj.os_type:
                mod_name = "PcieProviderLinux"
            else:
                raise NotImplementedError("PCIe is not implemented for "
                                          "specified OS '{}'".format(os_obj.os_type))

        mod = import_module(package, mod_name)
        aclass = getattr(mod, mod_name)
        return aclass(cfg_opts=cfg_opts, log=log, os_obj=os_obj, uefi_util_obj=uefi_obj)

    @abstractmethod
    def get_pcie_devices(self, re_enumerate=False):
        """
        This method is to get the pcie devices.

        :param re_enumerate - If true enumerates the PCI devices again
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_device_details_by_device_id(self, device_id):
        """
        This method is to get device details by device id.

        :param device_id
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_device_details_by_device_class(self, class_id):
        """
        This method is to get device details by class.

        :param class_id
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_linkcap_speed(self, device_id):
        """
        This method is to get the lincap speed.

        :param device_id
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_linkstatus_width(self, device_id):
        """
        This method is to get the linkstatus width.

        :param device_id
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_device_bus(self, bdf):
        """
        This method is to get the device bus.

        :param bdf
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def disable_kernel_driver(self, device_id):
        """
        This method is to disable the kernel driver.

        :param device_id
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_driver_status(self, device_id):
        """
        This method will give the status of driver in device manager.

        :param device_id
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def set_kernel_driver(self, device_id, status):
        """
        This method is to enable/disable the kernel driver..

        :param device_id
        :param status: enable/disable
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_device_details_with_bus(self, bus):
        """
        This method is to get the pcie device details with bus.

        :param bus
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_link_cap_speed_by_bdf(self, bdf):
        """
        This method is to get the link cap speed by bdf.

        :param bdf
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_link_cap_width_by_bdf(self, bdf):
        """
        This method is to get the link cap width by bdf.

        :param bdf
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_link_status_width_by_bdf(self, bdf=None):
        """
        This method is to get the link status width by bdf.

        :param bdf
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_link_status_speed_by_bdf(self, bdf=None):
        """
        This method is to get the link status speed by bdf.

        :param bdf
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_pcie_driver_name_by_bdf(self, bdf=None):
        """
        This method is to get the pcie driver name by bdf.

        :param bdf
        :raise NotImplementedError
        """
        raise NotImplementedError


class PcieProviderLinux(PcieProvider):
    """
    This Class is having the method of storage functionality based on Linux.

    :raise None
    """
    LSPCI_MM_CMD = "lspci -mm"
    LSPCI_MN_CMD = "lspci -mn"
    LSPCI_DRIVER_CMD = "lspci -v -d {}:{}"
    KERNEL_DRIVER_REGEX = r'Kernel\sdriver\sin\suse\S\s(\S+)'
    LINCAP_REGEX = r"LnkCap:\sPort\s\S+\sSpeed\s(\S+)"
    LINCAP_WIDTH_REGEX = r"LnkCap:.*Width\s(\S+)"
    LNKCAP_SPEED = "lspci -s {} -vvv"
    LINK_STATUS_WIDTH_REGEX = r"LnkSta:\sSpeed.*Width\s(\S+)"
    LINK_STATUS_SPEED = r"LnkSta:\sSpeed\s(\S+)"
    CXL_TYPE_REGEX = r"CXLCap:\tCache[+-]\sIO[+]\sMem[+-]"
    ROOT_COMPLEX_STR = "Root Complex Integrated Endpoint"
    CXL_VENDOR_ID_REGEX = r"Designated Vendor-Specific: Vendor=(.*):\sCXL"

    def __init__(self, log, os_obj, cfg_opts=None, uefi_util_obj=None):
        super(PcieProviderLinux, self).__init__(log, os_obj, cfg_opts, uefi_util_obj)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj
        self.__dict_pci_device_dict = {}
        self.__bdf_device_class_dict = {}
        self._pcie_device_dict = self.__enumerate_pcie_devices()
        self.cxl_type_dict = {"Cache- IO+ Mem+": "Type 3", "Cache+ IO+ Mem-": "Type 1", "Cache+ IO+ Mem+": "Type 2"}

    def factory(log, os_obj, cfg_opts=None, execution_env=None, uefi_obj=None):
        pass

    def __enumerate_pcie_devices(self):
        """
        This method is to enumerate the pcie devices.

        :return pcie devices in dictionary form eg:- {'00:01.7': {'vendor_id': '8086', 'device_id': '0b00',
        'device_driver': 'ioatdma', 'device_class': 'System peripheral'}, '00:02.0': {'vendor_id': '8086',
        'device_id': '09a6', 'device_driver': None, 'device_class': 'System peripheral'},...}.
        """
        command_output = self._common_content_lib.execute_sut_cmd(sut_cmd=self.LSPCI_MM_CMD, cmd_str=
        self.LSPCI_MM_CMD, execute_timeout=
                                                                  self._cmd_time_out_in_sec)
        pcie_bdf_device_class_info_list = command_output.split('\n')[:-1]
        for each_line in pcie_bdf_device_class_info_list:
            each_line_list = each_line.split('"')
            bdf_value = each_line_list[0][:-1]
            self.__bdf_device_class_dict[bdf_value] = each_line_list[1]
        command_output = self._common_content_lib.execute_sut_cmd(sut_cmd=self.LSPCI_MN_CMD, cmd_str=
        self.LSPCI_MN_CMD, execute_timeout=
                                                                  self._cmd_time_out_in_sec)
        pcie_device_info_list = command_output.split('\n')[:-1]
        for each_line in pcie_device_info_list:
            each_device_info_dict = {}
            each_line_list = each_line.split(' ')
            each_device_info_dict[PcieAttribute.VENDOR_ID] = each_line_list[2][1:-1]
            each_device_info_dict[PcieAttribute.DEVICE_ID] = each_line_list[3][1:-1]
            command_output = self._common_content_lib.execute_sut_cmd(sut_cmd=self.LSPCI_DRIVER_CMD.format(
                each_line_list[2][1:-1], each_line_list[3][1:-1]), cmd_str=self.LSPCI_DRIVER_CMD.format(
                each_line_list[2][1:-1], each_line_list[3][1:-1]), execute_timeout=self._cmd_time_out_in_sec)
            regex_out_put = re.findall(self.KERNEL_DRIVER_REGEX, command_output)
            if len(regex_out_put):
                each_device_info_dict[PcieAttribute.DEVICE_DRIVER] = regex_out_put[0]
            else:
                each_device_info_dict[PcieAttribute.DEVICE_DRIVER] = None
            each_device_info_dict[PcieAttribute.DEVICE_CLASS] = self.__bdf_device_class_dict[each_line_list[0]]

            self.__dict_pci_device_dict[each_line_list[0]] = each_device_info_dict
        return self.__dict_pci_device_dict

    def get_pcie_devices(self, re_enumerate=False):
        """
        This method is to get the pcie devices.

        :param re_enumerate - If true enumerates the PCI devices again

        :return pcie devices in dictionary form eg:- {'00:01.7': {'vendor_id': '8086', 'device_id': '0b00',
        'device_driver': 'ioatdma', 'device_class': 'System peripheral'}, '00:02.0': {'vendor_id': '8086',
        'device_id': '09a6', 'device_driver': None, 'device_class': 'System peripheral'},...}.
        """
        if re_enumerate:
            self._pcie_device_dict = self.__enumerate_pcie_devices()
        return self._pcie_device_dict

    def get_device_details_by_device_id(self, device_id):
        """
        This method is to get device details by device id.

        :param device_id
        :return [{'00:02.0': {'vendor_id': '8086', 'device_id': '09a6', 'device_driver': None,
        'device_class': 'System peripheral'}}, {'80:02.0': {'vendor_id': '8086', 'device_id': '09a6',
        'device_driver': None, 'device_class': 'System peripheral'}}]
        """
        device_detail_list = []
        all_device_info_dict = self._pcie_device_dict
        for bdf_key, bdf_value in all_device_info_dict.items():
            each_device_dict = {}
            if bdf_value[PcieAttribute.DEVICE_ID] == device_id:
                each_device_dict[bdf_key] = bdf_value
                device_detail_list.append(each_device_dict)
        self._log.debug("Device details searched by device id:  {}".format(device_detail_list))
        return device_detail_list

    def get_device_details_by_device_class(self, class_id):
        """
        This Method is to get device details by class id.

        :param class_id
        :return: [{'00:00.0': {'vendor_id': '8086', 'device_id': '09a2', 'device_driver': None, 'device_class':
        'System peripheral'}}, {'00:00.1': {'vendor_id': '8086', 'device_id': '09a4', 'device_driver': None,
        'device_class': 'System peripheral'}}, ...]
        """
        device_detail_list = []
        all_device_info_dict = self._pcie_device_dict
        for bdf_key, bdf_value in all_device_info_dict.items():
            each_device_dict = {}
            if class_id in bdf_value[PcieAttribute.DEVICE_CLASS]:
                each_device_dict[bdf_key] = bdf_value
                device_detail_list.append(each_device_dict)
        self._log.debug("Device Detail List searched with class:  {}".format(device_detail_list))
        return device_detail_list

    def get_linkcap_speed(self, device_id):
        """
        This method is to get the lincap speed.

        :param device_id
        :return linkspeed
        """
        linkcap_speed = ""
        for bdf_key, device_details in self._pcie_device_dict.items():
            if device_details[PcieAttribute.DEVICE_ID] == device_id:
                if PcieAttribute.LINKCAP_SPEED in device_details.keys():
                    linkcap_speed = device_details[PcieAttribute.LINKCAP_SPEED]
                else:
                    cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=self.LNKCAP_SPEED.format(bdf_key),
                                                                          cmd_str=self.LNKCAP_SPEED.format(bdf_key),
                                                                          execute_timeout=self._cmd_time_out_in_sec)
                    regex_output = re.findall(self.LINCAP_REGEX, cmd_output)
                    linkcap_speed = regex_output[0].replace(',', '')
                    device_details[PcieAttribute.LINKCAP_SPEED] = linkcap_speed

        return linkcap_speed

    def get_linkcap_width(self, device_id):
        """
        This method is to get the lincap width.

        :param device_id
        :return width
        """
        linkcap_width = ""
        for bdf_key, device_details in self._pcie_device_dict.items():
            if device_details[PcieAttribute.DEVICE_ID] == device_id:
                if PcieAttribute.LINKCAP_WIDTH in device_details.keys():
                    linkcap_width = device_details[PcieAttribute.LINKCAP_WIDTH]
                else:
                    cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=self.LNKCAP_SPEED.format(bdf_key),
                                                                          cmd_str=self.LNKCAP_SPEED.format(bdf_key),
                                                                          execute_timeout=self._cmd_time_out_in_sec)
                    regex_output = re.findall(self.LINCAP_WIDTH_REGEX, cmd_output)
                    linkcap_width = regex_output[0].replace(',', '')
                    device_details[PcieAttribute.LINKCAP_WIDTH] = linkcap_width
        return linkcap_width

    def get_link_cap_width_by_bdf(self, bdf):
        """
        This method is to get the link cap width by bdf.

        :param bdf
        :return width
        :raise content_exceptions
        """
        lspci_output = self._common_content_lib.execute_sut_cmd(sut_cmd=self.LNKCAP_SPEED.format(bdf),
                                                                cmd_str=self.LNKCAP_SPEED.format(bdf),
                                                                execute_timeout=self._cmd_time_out_in_sec)
        regex_output = re.findall(self.LINCAP_WIDTH_REGEX, lspci_output)
        if not regex_output:
            raise content_exceptions.TestFail("Link Cap Width was not captured in OS for bdf: {}".format(bdf))
        linkcap_width = regex_output[0].replace(',', '')
        return linkcap_width

    def get_link_cap_speed_by_bdf(self, bdf):
        """
        This method is to get the link cap speed by bdf.

        :param bdf
        :return speed
        :raise content_exceptions
        """
        lspci_output = self._common_content_lib.execute_sut_cmd(sut_cmd=self.LNKCAP_SPEED.format(bdf),
                                                                cmd_str=self.LNKCAP_SPEED.format(bdf),
                                                                execute_timeout=self._cmd_time_out_in_sec)
        regex_output = re.findall(self.LINCAP_REGEX, lspci_output)
        if not regex_output:
            raise content_exceptions.TestFail("Link Cap Speed was not captured in OS for bdf: {}".format(bdf))
        linkcap_speed = regex_output[0].replace(',', '')
        return linkcap_speed

    def get_link_status_speed_by_bdf(self, bdf=None):
        """
        This method is to get the link status speed.

        :param bdf
        :return link_status_speed
        :raise content_exceptions
        """
        if not bdf:
            raise content_exceptions.TestFail("Please pass bdf as an Arguments")
        else:
            cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=self.LNKCAP_SPEED.format(bdf),
                                                                  cmd_str=self.LNKCAP_SPEED.format(bdf),
                                                                  execute_timeout=self._cmd_time_out_in_sec)
            regex_output = re.findall(self.LINK_STATUS_SPEED, cmd_output)
            if not regex_output:
                raise content_exceptions.TestFail("Link Status speed was not captured in OS for bdf: {}".format(bdf))
            link_status_speed = regex_output[0].replace(',', '')
        return link_status_speed

    def get_link_status_width_by_bdf(self, bdf=None):
        """
        This method is to return link status width for required bdf.

        :param bdf
        :return link_status_width
        :raise content_exceptions
        """
        if not bdf:
            raise content_exceptions.TestFail("Please pass bdf as an Arguments")
        else:
            cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=self.LNKCAP_SPEED.format(bdf),
                                                                  cmd_str=self.LNKCAP_SPEED.format(bdf),
                                                                  execute_timeout=self._cmd_time_out_in_sec)
            regex_output = re.findall(self.LINK_STATUS_WIDTH_REGEX, cmd_output)
            if not regex_output:
                raise content_exceptions.TestFail("Link Status Width was not captured in OS for bdf: {}".format(bdf))
            link_status_width = regex_output[0].replace(',', '')
        return link_status_width

    def get_linkstatus_width(self, device_id):
        """
        This method is to get linkstatus width.

        :param device_id
        :return width
        """
        link_status_width = ""
        for bdf_key, device_details in self._pcie_device_dict.items():
            if device_details[PcieAttribute.DEVICE_ID] == device_id:
                if PcieAttribute.LINKSTATUS_WIDTH in device_details.keys():
                    link_status_width = device_details[PcieAttribute.LINKSTATUS_WIDTH]
                else:
                    cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=self.LNKCAP_SPEED.format(bdf_key),
                                                                          cmd_str=self.LNKCAP_SPEED.format(bdf_key),
                                                                          execute_timeout=self._cmd_time_out_in_sec)
                    regex_output = re.findall(self.LINK_STATUS_WIDTH_REGEX, cmd_output)
                    link_status_width = regex_output[0].replace(',', '')
                    device_details[PcieAttribute.LINKCAP_WIDTH] = link_status_width
        return link_status_width

    def get_device_bus(self, bdf=None, device_id=None):
        """
        This method is to get the bus id of device.

        :return bus_id
        :raise RunTimeError
        """
        if bdf:
            return bdf.split(':')[0]
        elif device_id:
            all_device_info_dict = self._pcie_device_dict
            for bdf_key, bdf_value in all_device_info_dict.items():
                if bdf_value[PcieAttribute.DEVICE_ID] == device_id:
                    return bdf_key.split(':')[0]
            else:
                raise RuntimeError("Device id: {} has no bdf value".format(device_id))

    def disable_kernel_driver(self, device_id):
        """
        This method is to disable the kernel driver.

        :return None
        """
        cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=self.LSPCI_DRIVER_CMD.format('8086', device_id),
                                                              cmd_str="kernel driver command execution",
                                                              execute_timeout=
                                                              self._cmd_time_out_in_sec)
        regex_out_put = re.findall(self.KERNEL_DRIVER_REGEX, cmd_output)
        if regex_out_put:
            self._common_content_lib.execute_sut_cmd("modprobe -r {}".format(regex_out_put[0]), cmd_str="driver disable"
                                                     , execute_timeout=self._cmd_time_out_in_sec)
            self._log.debug("Kernel driver for device id: {} is now disable".format(device_id))
        self._log.debug("Kernel driver for device id: {} is already disable".format(device_id))

    def get_driver_status(self, device_id):
        """
        This method will give the status of driver in device manager.

        :param device_id
        :raise NotImplementedError
        """
        raise NotImplementedError("This method is not Implemented for Linux")

    def get_driver_status_by_bdf(self, bdf=None):
        """
        This method is to provide kernel driver status by bdf.

        :param bdf
        :return True or False
        """
        if not bdf:
            raise content_exceptions.TestFail("No bdf was found to search...Please pass bdf value as parameter")
        lspci_out_put = self._common_content_lib.execute_sut_cmd(sut_cmd=self.LNKCAP_SPEED.format(bdf), cmd_str=
        self.LNKCAP_SPEED.format(bdf), execute_timeout=self._cmd_time_out_in_sec)
        device_driver_name = re.findall(self.KERNEL_DRIVER_REGEX, lspci_out_put)
        if device_driver_name:
            self._log.debug("Device driver for bdf: {} is visible is OS: {}".format(bdf, device_driver_name))
            return True
        else:
            return False

    def set_kernel_driver(self, device_id, status):
        """
        This method is to enable/disable the kernel driver.

        :param device_id
        :param status: enable/disable
        :raise NotImplementedError
        """
        raise NotImplementedError("This method is not Implemented for Linux")

    def get_device_details_with_bus(self, bus):
        """
        This method is to get the device info with bus.

        :param bus
        :return pcie_device_info
        """
        each_device_dict = {}
        all_device_info_dict = self._pcie_device_dict
        for bdf_key, bdf_value in all_device_info_dict.items():
            each_device_dict = {}
            self._log.debug("bdf_key value : {}".format(bdf_key))
            self._log.debug("Bus value : {}".format(bdf_value))
            if bdf_key.startswith(bus):
                each_device_dict[bdf_key] = bdf_value
                cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=self.LNKCAP_SPEED.format(bdf_key), cmd_str=
                             self.LNKCAP_SPEED.format(bdf_key), execute_timeout=self._cmd_time_out_in_sec)
                regex_output = re.findall(self.CXL_TYPE_REGEX, cmd_output)
                if regex_output:
                    each_device_dict[bdf_key]["cxl_device_type"] = self.cxl_type_dict[regex_output[0][-15:]]
                else:
                    each_device_dict[bdf_key]["cxl_device_type"] = "NA"
                if self.ROOT_COMPLEX_STR in str(cmd_output):
                    each_device_dict[bdf_key]["root_complex"] = True
                else:
                    each_device_dict[bdf_key]["root_complex"] = False
                regex_output = re.findall(self.CXL_VENDOR_ID_REGEX, cmd_output)
                if regex_output:
                    each_device_dict[bdf_key]["vendor_id"] = regex_output[0].split()[0]
                break
        self._log.debug("Device details {} for bus:  {}".format(each_device_dict, bus))
        return each_device_dict

    def get_pcie_driver_name_by_bdf(self, bdf=None):
        """
        This method is to get the driver name of PCIe device.

        :param bdf
        :return pcie driver name
        """
        if not bdf:
            raise content_exceptions.TestFail("Please send bdf as an Argument")
        cmd_out_put = self._common_content_lib.execute_sut_cmd(sut_cmd=self.LNKCAP_SPEED.format(bdf),
                                                               cmd_str="command to get driver",
                                                               execute_timeout=self._cmd_time_out_in_sec)
        driver_name = re.findall(self.KERNEL_DRIVER_REGEX, cmd_out_put)
        if driver_name:
            driver_name = driver_name[0]
        self._log.debug("Driver name for bdf: {} is : {}".format(bdf, driver_name))
        return driver_name


class PcieProviderWindows(PcieProvider):
    """
    This Class has different method of PCIe on Windows Platform

    :raise None
    """
    DEV_ADD = "DEV_ADD"
    VID_DID = "VID_DID"
    SVID_DID = "SVID_DID"
    CLASS = "CLASS:"
    LINK = "LINK:"
    REGEX_FOR_LINK_SPEED_AND_WIDTH = r"LINK:\s+(\S+)\s\S+\s(\S+)\scapable\S\s(\S+)\sat\s(\S+)"

    def __init__(self, log, os_obj, cfg_opts=None, uefi_util_obj=None):
        super(PcieProviderWindows, self).__init__(log, os_obj, cfg_opts, uefi_util_obj)
        self._log = log
        self._cfg_opts = cfg_opts
        self._os = os_obj
        self._device_stacklist_sut_path = ""
        self._install_collateral = InstallCollateral(self._log, self._os, cfg_opts)
        self._memrw_folder_path = self._install_collateral.download_and_copy_zip_to_sut(
            WindowsMemrwToolConstant.MEMRW_FOLDER_NAME, WindowsMemrwToolConstant.HOST_ZIP_FILE_NAME)
        self._all_device_details_dict = self.__enumerate_pcie_devices()
        self._cycle_tool_sut_folder_path = self._install_collateral.install_driver_cycle()
        path = self._install_collateral.install_ccb_package_on_sut()
        self._install_collateral.install_ccb_wheel_package(["DeviceStackList"], path)
        self._device_list = self.__get_device_list()

    def factory(log, os_obj, cfg_opts=None, execution_env=None, uefi_obj=None):
        pass

    def __enumerate_pcie_devices(self):
        """
        This method is to enumerate the pcie devices.

        :return device detail dict:{'S0:B0:D0:F0': {'vendor_id': '8086', 'device_id': '09a2', 'device_class':
        'BASE_SYSTEM_DEV, System peripheral', 'linkcap_width': 'x0', 'linkcap_speed': '0.0Gb'},
        'S0:B0:D0:F1': {'vendor_id': '8086', 'device_id': '09a4', 'device_class':
        'BASE_SYSTEM_DEV, System peripheral', 'linkcap_width': 'x0', 'linkcap_speed': '0.0Gb'}}
        """
        bdf_key = ""
        cmd_output = self._common_content_lib.execute_sut_cmd(
            sut_cmd=WindowsMemrwToolConstant.MEMRW_CMD_TO_GET_PCIE_INFO, cmd_str="memrw tool execution", execute_timeout
            =self._cmd_time_out_in_sec, cmd_path=self._memrw_folder_path)

        devices_info_dict = {}
        each_device_info_dict = {}
        for each_line in cmd_output.split('\n'):
            if self.DEV_ADD in each_line:
                if bool(each_device_info_dict):
                    devices_info_dict[bdf_key] = each_device_info_dict
                    each_device_info_dict = {}
                bdf_key = each_line.split(':', 1)[1].strip(' ').split(' ')[0]

            elif self.VID_DID in each_line and self.SVID_DID not in each_line:
                id = each_line.split(':')[1].strip(' ')
                each_device_info_dict[PcieAttribute.VENDOR_ID] = id[:4]
                each_device_info_dict[PcieAttribute.DEVICE_ID] = id[4:8] # device id will be of 4 digit

            elif self.CLASS in each_line:
                each_device_info_dict[PcieAttribute.DEVICE_CLASS] = each_line.split(":")[1].strip(' ')

            elif self.LINK in each_line:
                regex_output = re.findall(self.REGEX_FOR_LINK_SPEED_AND_WIDTH, each_line)
                if regex_output:
                    each_device_info_dict[PcieAttribute.LINKCAP_WIDTH] = regex_output[0][0]
                    each_device_info_dict[PcieAttribute.LINKCAP_SPEED] = regex_output[0][1][:-1] + 'T/s'
                    each_device_info_dict[PcieAttribute.LINKSTATUS_WIDTH] = regex_output[0][2]
                    each_device_info_dict[PcieAttribute.LINKSTATUS_SPEED] = regex_output[0][3][:-1] + 'T/s'
        devices_info_dict[bdf_key] = each_device_info_dict
        return devices_info_dict

    def __get_device_list(self):
        """
        This method is get the device list info.

        :return list of dict
        """
        cmd_line = WindowsMemrwToolConstant.CMD_FOR_SUT_HOME_PATH
        collateral_script = "windows_device_stacklist.py"
        sut_home_path = self._common_content_lib.execute_sut_cmd(cmd_line, cmd_line, self._cmd_time_out_in_sec)
        sut_home_path = str(sut_home_path).strip().strip("\\n")
        self._device_stacklist_sut_path = os.path.join(sut_home_path, collateral_script)
        self._install_collateral.copy_collateral_script(collateral_script, sut_home_path)

        cmd_line = "python {} dsl_get_device_list".format(self._device_stacklist_sut_path)
        driver_dict = self._common_content_lib.execute_sut_cmd(cmd_line, cmd_line, self._cmd_time_out_in_sec)
        dict_storage_disks = ast.literal_eval(driver_dict)

        return dict_storage_disks

    def get_pcie_devices(self, re_enumerate=False):
        """
        This method is to get the pcie devices.

        :param re_enumerate - If true enumerates the PCI devices again

        :return device detail dict:{'S0:B0:D0:F0': {'vendor_id': '8086', 'device_id': '09a2', 'device_class':
        'BASE_SYSTEM_DEV, System peripheral', 'linkcap_width': 'x0', 'linkcap_speed': '0.0Gb'},
        'S0:B0:D0:F1': {'vendor_id': '8086', 'device_id': '09a4', 'device_class':
        'BASE_SYSTEM_DEV, System peripheral', 'linkcap_width': 'x0', 'linkcap_speed': '0.0Gb'}}
        """
        if re_enumerate:
            self._all_device_details_dict = self.__enumerate_pcie_devices()
        return self._all_device_details_dict

    def get_device_details_by_device_id(self, device_id):
        """
        This method is to get device details by device id.

        :param device_id
        :return [{'S0:B0:D28:F0': {'vendor_id': '8086', 'device_id': 'a194', 'device_class':
        'BRIDGE_DEV, PCI, Normal decode', 'linkcap_width': 'x1', 'linkcap_speed': '8.0Gb'}}]
        """
        device_detail_list = []
        all_device_info_dict = self._all_device_details_dict
        for bdf_key, bdf_value in all_device_info_dict.items():
            each_device_dict = {}
            if bdf_value[PcieAttribute.DEVICE_ID] == device_id:
                each_device_dict[bdf_key] = bdf_value
                device_detail_list.append(each_device_dict)
        self._log.debug("Device details searched by device id:  {}".format(device_detail_list))
        return device_detail_list

    def get_device_details_by_device_class(self, class_id):
        """
        This method is to get device details by class.

        :param class_id
        :return device details dict: [{'S0:B0:D0:F0': {'vendor_id': '8086', 'device_id': '09a2', 'device_class':
        'BASE_SYSTEM_DEV, System peripheral', 'linkcap_width': 'x0', 'linkcap_speed': '0.0Gb'}}, {'S0:B0:D0:F1':
        {'vendor_id': '8086', 'device_id': '09a4', 'device_class': 'BASE_SYSTEM_DEV, System peripheral', 'linkcap_width'
        : 'x0', 'linkcap_speed': '0.0Gb'}}
        """
        device_detail_list = []
        all_device_info_dict = self._all_device_details_dict
        for bdf_key, bdf_value in all_device_info_dict.items():
            each_device_dict = {}
            if class_id in bdf_value[PcieAttribute.DEVICE_CLASS]:
                each_device_dict[bdf_key] = bdf_value
                device_detail_list.append(each_device_dict)
        self._log.debug("Device Detail List searched with class:  {}".format(device_detail_list))
        return device_detail_list

    def get_linkcap_speed(self, device_id):
        """
        This method is to get linkcap speed.

        :param device_id
        :return linkcap speed
        """
        linkcap_speed = ""
        try:
            for bdf_key, device_details in self._all_device_details_dict.items():
                if device_details[PcieAttribute.DEVICE_ID] == device_id:
                    if PcieAttribute.LINKCAP_SPEED in device_details.keys():
                        linkcap_speed = device_details[PcieAttribute.LINKCAP_SPEED]
                        break

            return linkcap_speed
        except Exception as ex:
            raise content_exceptions.TestFail("Exception Occurred during finding linkcap speed: {}".format(ex))

    def get_linkcap_width(self, device_id):
        """
        This method is to get the lincap width.

        :param device_id
        :return width
        """
        linkcap_width = ""
        try:
            for bdf_key, device_details in self._all_device_details_dict.items():
                if device_details[PcieAttribute.DEVICE_ID] == device_id:
                    if PcieAttribute.LINKCAP_WIDTH in device_details.keys():
                        linkcap_width = device_details[PcieAttribute.LINKCAP_WIDTH]
                        break
            return linkcap_width
        except Exception as ex:
            raise content_exceptions.TestFail("Exception occurred during finding linkcap width: {}".format(ex))

    def get_linkstatus_width(self, device_id):
        """
        This method is to get linkstatus width.

        :param device_id
        :return width
        """
        link_status_width = ""
        for bdf_key, device_details in self._all_device_details_dict.items():
            if device_details[PcieAttribute.DEVICE_ID] == device_id:
                if PcieAttribute.LINKSTATUS_WIDTH in device_details.keys():
                    link_status_width = device_details[PcieAttribute.LINKSTATUS_WIDTH]

        return link_status_width

    def get_device_bus(self, bdf=None, device_id=None):
        """
        This method is to get the bus id of device.

        :return bus_id
        :raise RunTimeError
        """
        if bdf:
            return bdf.split(':')[1][1:]
        elif device_id:
            all_device_info_dict = self._all_device_details_dict
            for bdf_key, bdf_value in all_device_info_dict.items():
                if bdf_value[PcieAttribute.DEVICE_ID] == device_id:
                    return bdf_key.split(':')[1][1:]
            else:
                raise RuntimeError("Device id: {} has no bdf value".format(device_id))

    def disable_kernel_driver(self, device_id):
        """
        This method is to disable the kernel driver.

        :return None
        """
        cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd="devcon disable *DEV_{}".format(device_id),
                                                              cmd_str="kernel driver command execution", execute_timeout
                                                              =self._cmd_time_out_in_sec,
                                                              cmd_path=self._cycle_tool_sut_folder_path)

        self._log.debug("Kernel driver for device id: {} is : {}".format(device_id, cmd_output))
        if re.findall("Enable failed", cmd_output):
            raise content_exceptions.TestFail(
                "Couldn't Enable the kernel driver for the device id: {}".format(device_id))

    def get_driver_status_by_bdf(self, bdf=None):
        """
        This method is to get status by bdf.

        :param bdf
        """
        device_id = None
        vendor_id = None
        if not bdf:
            raise content_exceptions.TestFail("Please send bdf as an Argument")
        else:
            for bdf_key, value in self._all_device_details_dict.items():
                if bdf_key == bdf:
                    device_id = value[PcieAttribute.DEVICE_ID]
                    vendor_id = value[PcieAttribute.VENDOR_ID]
                    break
            if not device_id:
                raise content_exceptions.TestFail("Device id was not found for bdf: {}".format(bdf))
            return self.get_driver_status(device_id=device_id, vendor_id=vendor_id)  # Sending vendor id to remove
            # hard coding

    def get_driver_status(self, device_id, vendor_id="8086"):  # Intel Device by default: 8086
        """
        This method will give the status of driver in device manager.

        :param device_id
        :return True or False
        """
        for each_device in self._device_list:
            dev_id = each_device[PcieAttribute.FULL_DEVICE_ID]
            if isinstance(dev_id, bytes):
                dev_id = dev_id.decode('utf-8')
            if "VEN_{}&DEV_{}".format(str(vendor_id).upper(), str(device_id).upper()) in dev_id:  # Using Dynamically
                # Vendor id to remove hard coding.
                self._log.info("VEN_{}&DEV_{}".format(str(vendor_id).upper(), str(device_id).upper()))
                if isinstance(each_device[PcieAttribute.DEVICE_NAME], bytes):
                    each_device_name = each_device[PcieAttribute.DEVICE_NAME].decode('utf-8')
                else:
                    each_device_name = each_device[PcieAttribute.DEVICE_NAME]
                break
        cmd_line = "python {} dsl_checkforYellowBang \"{}\" \"0\"".format(self._device_stacklist_sut_path,
                                                                          each_device_name)
        self._log.debug("cmd_line of checkforYellowBang: {}".format(cmd_line))
        driver_status = self._common_content_lib.execute_sut_cmd(cmd_line, cmd_line, self._cmd_time_out_in_sec)
        return not int(driver_status)

    def set_kernel_driver(self, device_id, status):
        """
        This method is to enable/disable the kernel driver.

        :param device_id: id of the PCIE device
        :param status: status enable/disable
        :return None
        """
        cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd="devcon {} *DEV_{}".format(status, device_id),
                                                              cmd_str="kernel driver command execution",
                                                              execute_timeout=self._cmd_time_out_in_sec,
                                                              cmd_path=self._cycle_tool_sut_folder_path)
        self._log.debug("Kernel driver for device id: {} is : {}".format(device_id, cmd_output))
        if re.findall(status.capitalize() + " failed", cmd_output):
            self._log.error(status.capitalize() + " failed")
            raise content_exceptions.TestFail("Couldn't {} the kernel driver for device id: {}".
                                              format(status, device_id))

    def get_device_details_with_bus(self, bus):
        """
        This method is to get device info of dedicated bus.

        :param bus
        :return dict
        """
        device_info_dict = {}
        self._log.info("Searching the device info with bus")
        for bdf, value in self._all_device_details_dict.items():
            if ":B{}".format(bus) in bdf:
                device_info_dict[bdf] = value
        self._log.info("The device with this bdf is: {}".format(device_info_dict))
        return device_info_dict

    def get_link_status_speed_by_bdf(self, bdf=None):
        """
        This method is to get linkstatus speed by bdf

        :param: bdf
        :return link_status_speed
        """
        link_status_speed = None
        if not bdf:
            raise content_exceptions.TestFail("Please pass bdf as an argument")
        for bdf_key, value in self._all_device_details_dict.items():
            if bdf_key == bdf:
                link_status_speed = value[PcieAttribute.LINKSTATUS_SPEED]

        return link_status_speed

    def get_link_status_width_by_bdf(self, bdf=None):
        """
        This method is to get link status width by bdf.

        :param: bdf
        :return link_status_speed
        """
        link_status_width = None
        if not bdf:
            raise content_exceptions.TestFail("Please pass bdf as an Argument")
        for bdf_key, value in self._all_device_details_dict.items():
            if bdf_key == bdf:
                link_status_width = value[PcieAttribute.LINKSTATUS_WIDTH]

        return link_status_width

    def get_link_cap_width_by_bdf(self, bdf):
        """
        This method is to get link cap width by bdf.

        :param bdf
        :raise NotImplementedError
        """
        raise NotImplementedError("Still Not Implemented for Windows")

    def get_pcie_driver_name_by_bdf(self, bdf=None):
        """
        This method is to get driver name by bdf.

        :param bdf
        :raise NotImplementedError
        """
        raise NotImplementedError("Still Not Implemented For Windows")

    def get_link_cap_speed_by_bdf(self, bdf):
        """
        This method is to get link cap speed by bdf.

        :param bdf
        :raise NotImplementedError
        """
        raise NotImplementedError("Still Not implemented for Windows")


class PcieProviderItp(PcieProvider):
    """
    This Class have different method of Pcie functionality with itp environment

    :raise None
    """

    def __init__(self, log, os_obj, cfg_opts=None, uefi_util_obj=None):
        super(PcieProviderItp, self).__init__(log, os_obj, cfg_opts, uefi_util_obj)
        self._log = log
        self._os = os_obj

    def factory(log, os_obj, cfg_opts=None, execution_env=None, uefi_obj=None):
        pass

    def get_pcie_devices(self, re_enumerate=False):
        """
        This method is to get the pcie devices.

        :param re_enumerate - If true enumerates the PCI devices again

        :raise NotImplementedError
        """
        raise NotImplementedError("This get_pcie_devices method is not implemented for itp environment")

    def get_device_details_by_device_id(self, device_id):
        """
        This method is to get device details by device id.

        :param device_id
        :raise NotImplementedError
        """
        raise NotImplementedError("This get_device_details_by_device_id method is not implemented "
                                  "for itp environment")

    def get_device_details_by_device_class(self, class_id):
        """
        This method is to get device details by class.

        :param class_id
        :raise NotImplementedError
        """
        raise NotImplementedError("This get_device_details_by_device_class method is not implemented "
                                  "for itp environment")

    def get_linkcap_speed(self, device_id):
        """
        This method is to get linkcap speed.

        :param device_id
        :raise NotImplementedError
        """
        raise NotImplementedError("This get_device_details_by_device_class method is not implemented "
                                  "for itp")


class PcieProviderUefi(PcieProvider):
    """
    This Class have different method of Pcie functionality with uefi environment

    :raise None
    """

    def __init__(self, log, os_obj, cfg_opts=None, uefi_util_obj=None):
        super(PcieProviderUefi, self).__init__(log, os_obj, cfg_opts, uefi_util_obj)
        self._log = log
        self._os = os_obj

    def factory(log, os_obj, cfg_opts=None, execution_env=None, uefi_obj=None):
        pass

    def get_pcie_devices(self, re_enumerate=False):
        """
        This method is to get the pcie devices.

        :param re_enumerate - If true enumerates the PCI devices again

        :raise NotImplementedError
        """
        raise NotImplementedError("This get_pcie_devices method is not implemented for uefi environment")

    def get_device_details_by_device_id(self, device_id):
        """
        This method is to get device details by device id.

        :param device_id
        :raise NotImplementedError
        """
        raise NotImplementedError("This get_device_details_by_device_id method is not implemented "
                                  "for uefi environment")

    def get_device_details_by_device_class(self, class_id):
        """
        This method is to get device details by class.

        :param class_id
        :raise NotImplementedError
        """
        raise NotImplementedError("This get_device_details_by_device_class method is not implemented "
                                  "for uefi environment")

    def get_linkcap_speed(self, device_id):
        """
        This method is to get linkcap speed.

        :param device_id
        :raise NotImplementedError
        """
        raise NotImplementedError("This get_device_details_by_device_class method is not implemented "
                                  "for uefi")
