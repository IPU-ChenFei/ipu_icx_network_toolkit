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
import time

from dtaf_core.lib.dtaf_constants import OperatingSystems
from src.lib.common_content_lib import CommonContentLib
from src.lib.dtaf_content_constants import PcieAttribute, IntelPcieDeviceId
import src.lib.content_exceptions as content_exceptions

from dtaf_core.lib.dtaf_constants import OperatingSystems
from src.lib.dtaf_content_constants import IntelPcieDeviceId
from src.lib.install_collateral import InstallCollateral
from src.lib.dtaf_content_constants import LinuxCyclingToolConstant
from src.lib.dtaf_content_constants import TimeConstants


class PcieCommonUtil:
    """
    This class is for pcie common util.
    """
    LSPCI_CMD = 'lspci | grep -i ERROR'
    SLEEP_TIME = 20
    RESTART = "./restart.sh"
    SUT_WINDOWS_WHEA_LOG = """powershell.exe "$a=(get-WinEvent @{logname='system'; ProviderName='*WHEA*'})[0]; """\
                           """'id: '+$a.Id; 'TimeCreated: '+$a.TimeCreated; $a.Message;"""\
                           """([xml]$a.ToXml()).Event.EventData.ChildNodes | foreach {$_.Name + ': ' + $_.'#Text'}" """
    CORR_UNCORR_SIGN = ["UncorrectableErrorStatus: 0x0", "CorrectableErrorStatus: 0x0"]

    def __init__(self, log, os, common_content_config, pcie_provider_obj, cfg_opts):
        self._log = log
        self._os = os
        self._cfg = cfg_opts
        self._pcie_provider_obj = pcie_provider_obj
        self._common_content_config = common_content_config
        self._common_content_lib = CommonContentLib(self._log, self._os, self._cfg)
        self._cmd_time_out = self._common_content_config.get_command_timeout()
        self._install_collateral = InstallCollateral(self._log, self._os, self._cfg)

    def check_pcie_kernel_driver(self, device_id, expected_kernel_driver):
        """
        This method is to validate kernel driver.

        :param device_id
        :param expected_kernel_driver
        :raise content_exception
        """
        ret_val = False
        pcie_device_dict = self._pcie_provider_obj.get_pcie_devices()
        for key, value in pcie_device_dict.items():
            if self._os.os_type == OperatingSystems.LINUX:
                if value[PcieAttribute.DEVICE_ID] == device_id and value[PcieAttribute.DEVICE_DRIVER] == \
                        expected_kernel_driver:
                    self._log.debug(
                        "Kernel driver found as expected: '{}' for device id: '{}'".format(expected_kernel_driver,
                                                                                           device_id))
                    ret_val = True
                    break
            else:
                if self._pcie_provider_obj.get_driver_status(device_id):
                    self._log.debug("Kernel driver for device id: {} was reflected in device manager".format(device_id))
                    ret_val = True
                    break
        if ret_val:
            self._log.debug("Kernel driver for device id: '{}' reflecting in OS as expected".format(device_id))
        else:
            raise content_exceptions.TestFail("Kernel driver for device id: '{}' was not reflected in OS".format(
                device_id))

    def check_memory_controller_error(self):
        """
        This method is to check the controller error.

        :raise: content_exception
        """
        if self._os.os_type == OperatingSystems.LINUX:
            cmd_output = self._os.execute(self.LSPCI_CMD, self._cmd_time_out).stdout.strip()
            if cmd_output:
                raise content_exceptions.TestFail('Error captured in lspci command output')
            self._log.debug("No Error is Captured in lspci output Log")
        elif self._os.os_type == OperatingSystems.WINDOWS:
            cmd_output = self._os.execute(self.SUT_WINDOWS_WHEA_LOG, self._cmd_time_out).stdout.strip()
            self._log.info("WHEA Error command output: {}".format(cmd_output))

            out_put = re.findall(pattern="Component: PCI Express Root Complex Event Collector", string=cmd_output)
            self._log.info("Regex Out Put: {}".format(out_put))
            if out_put:
                for each_type_error in self.CORR_UNCORR_SIGN:
                    if each_type_error not in cmd_output:
                        self._log.error("Error type: {} was captured in WHEA error".format(each_type_error))
                raise content_exceptions.TestFail("PCIe Error was Captured in WHEA Error")
            self._log.debug("No PCIe Error was Captured in WHEA Error")
        else:
            raise content_exceptions.TestFail("Not Implemented for OS type: {}".format(self._os.os_type))

    def check_pci_device_exist(self, class_name, expected_device_id):
        """
        This method is to check the pci device exist.

        :param expected_device_id
        :param class_name
        :raise content_exception
        """
        device_id_list = []
        device_detail_of_all_same_class = self._pcie_provider_obj.get_device_details_by_device_class(class_name)
        self._log.info("Device info the class name : {} is {}".format(class_name, device_detail_of_all_same_class))
        for each_device_details in device_detail_of_all_same_class:
            for bdf_value, value in each_device_details.items():
                device_id_list.append(value[PcieAttribute.DEVICE_ID])
        if expected_device_id not in device_id_list:
            raise content_exceptions.TestFail('PCIe device is not captured of device id : {} and class name is : {}'.
                                              format(expected_device_id, class_name))
        self._log.debug("PCIe Device of class name: '{}' and device id: '{}' exist".format(class_name,
                                                                                          expected_device_id))

    def validate_installed_pcie_link_width_speed(self, device_id, expected_lnk_speed=None, expected_lnk_width=None):
        """
        This method is to validate the pcie link width and speed.

        :param expected_lnk_speed
        :param expected_lnk_width
        :param device_id
        """
        product_family = self._common_content_lib.get_platform_family()
        linkcap_speed = self._pcie_provider_obj.get_linkcap_speed(device_id)
        linkcap_speed = linkcap_speed.replace('.0', '')  # Making compatible for both Linux and Windows
        if not expected_lnk_speed:
            expected_lnk_speed = IntelPcieDeviceId.PCIE_LINK_SPEED_WIDTH_DICT[product_family] \
                [device_id][PcieAttribute.LINKCAP_SPEED]
        if not expected_lnk_width:
            expected_lnk_width = IntelPcieDeviceId.PCIE_LINK_SPEED_WIDTH_DICT[product_family] \
                [device_id][PcieAttribute.LINKCAP_WIDTH]
        if linkcap_speed not in expected_lnk_speed:
            raise content_exceptions.TestFail("LinkCap Speed for device id: {} is found as :{}, which is not an"
                                              "Expected Speed".format(device_id, linkcap_speed))

        self._log.info("LinkCap Speed for device id: {} is {}".format(device_id, linkcap_speed))
        linkcap_width = self._pcie_provider_obj.get_linkcap_width(device_id)
        if linkcap_width not in expected_lnk_width:
            raise content_exceptions.TestFail("LinkCap Width for device id: {} is found as :{}, which is not an"
                                              "Expected Width".format(device_id, linkcap_width))

        self._log.info("LinkCap Width for device id: {} is {}".format(device_id, linkcap_width))

    def get_cpu_root_device_details(self, device_id_class):
        """
        This method is to get the cpu root device details.

        :param device_id_class
        :return list of dict having cpu root details
        """
        cpu_root_port_device_list = []
        platform_stepping = self._common_content_lib.get_platform_stepping()
        if platform_stepping.startswith("A"):
            device_id = ['347a', '347c']
        else:
            device_id = ['352a', '352c']

        cpu_root_device_details = self._pcie_provider_obj.get_device_details_by_device_class(device_id_class)
        for each_device_details in cpu_root_device_details:
            for bdf_key, device_details in each_device_details.items():
                if device_details[PcieAttribute.DEVICE_ID] in device_id:
                    self._log.info("CPU port root device for bdf value : {} and device id : {} is availble".format(
                        bdf_key, device_details[PcieAttribute.DEVICE_ID]))
                    cpu_root_port_device_list.append(each_device_details)
                    linkcap_speed = self._pcie_provider_obj.get_linkcap_speed(device_details[PcieAttribute.DEVICE_ID])
                    device_details[PcieAttribute.LINKCAP_SPEED] = linkcap_speed

        return cpu_root_port_device_list
