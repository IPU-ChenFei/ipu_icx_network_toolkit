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

import sys

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import ProductFamilies, OperatingSystems
from src.lib.content_base_test_case import ContentBaseTestCase
from src.provider.pcie_provider import PcieProvider
from src.pcie.lib.pcie_common_utils import PcieCommonUtil
from src.lib.dtaf_content_constants import IntelPcieDeviceId
from src.lib.dtaf_content_constants import PcieAttribute
from src.lib.dtaf_content_constants import PcieDeviceClassConstants
from src.lib import content_exceptions


class PcieConfigDisplay(ContentBaseTestCase):
    """
    HPQALM ID : H79592-PI_PCIe_Config_Display_L, H110750-PI_PCIe_Config_Display_W

    This Testcase is used to check if a pcie config display.
    """
    TEST_CASE_ID = ["H79592", "PI_PCIe_Config_Display_L", "H110750", "PI_PCIe_Config_Display_W"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a PcieConfigDisplay object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PcieConfigDisplay, self).__init__(test_log, arguments, cfg_opts)
        self._cfg = cfg_opts
        self.pcie_provider_obj = PcieProvider.factory(log=test_log, os_obj=self.os, cfg_opts=cfg_opts,
                                                      execution_env='os', uefi_obj=None)
        self.pcie_common_util_obj = PcieCommonUtil(test_log, self.os, self._common_content_configuration,
                                                   self.pcie_provider_obj, cfg_opts)
        self._expected_lnkcap_speed = self._common_content_configuration.get_pcie_cpu_root_linkcap_speed(
            self._common_content_lib.get_platform_family())
        self.product_family = self._common_content_lib.get_platform_family()
        if self._common_content_configuration.get_device_driver_from_config():
            IntelPcieDeviceId.PCH_ROOT_DEVICES[self.product_family] = self._common_content_configuration.get_pch_device_id()
            IntelPcieDeviceId.XHCI_DEVICE_ID[self.product_family] = self._common_content_configuration.get_xhci_device_id()
            IntelPcieDeviceId.SATA_DEVICE_ID[self.product_family] = self._common_content_configuration.get_sata_device_id()
            IntelPcieDeviceId.ME_DEVICE_ID[self.product_family] = self._common_content_configuration.get_me_device_id()
            IntelPcieDeviceId.LPC_ESPI_DEVICE_ID[self.product_family] = self._common_content_configuration.get_lpc_espi_device_id()
            IntelPcieDeviceId.SMBUS_DEVICE_ID[self.product_family] = self._common_content_configuration.get_smbus_device_id()
            IntelPcieDeviceId.SPI_DEVICE_ID[self.product_family] = self._common_content_configuration.get_spi_device_id()
            IntelPcieDeviceId.ETHERNET_DEVICE_ID[self.product_family] = self._common_content_configuration.get_ethernet_device_id()

    def execute(self):
        """
        This is Used to check pcie device exist or not.

        :return: True or False
        """

        unexpected_device_list = []
        product_family = self._common_content_lib.get_platform_family()
        if self.os.os_type.lower() == OperatingSystems.LINUX.lower():
            self.pcie_common_util_obj.check_memory_controller_error()

        # cpu root
        self._log.info("Checking CPU root port device")
        cpu_root_device_list = None
        if self.os.os_type.lower() == OperatingSystems.LINUX.lower():
            cpu_root_device_list = self.pcie_common_util_obj.get_cpu_root_device_details(
                PcieDeviceClassConstants.PCIE_BRIDGE)
        elif self.os.os_type.lower() == OperatingSystems.WINDOWS.lower():
            cpu_root_device_list = self.pcie_common_util_obj.get_cpu_root_device_details(
                PcieDeviceClassConstants.PCIE_BRIDGE_WINDOWS)
        self._log.info("CPU root device data : {}".format(cpu_root_device_list))
        if not cpu_root_device_list:
            raise content_exceptions.TestFail("No CPU root port exist")
        self._log.debug("CPU port root device exist on SUT")

        self._log.info("Checking Lnkcap speed for CPU port root")
        self._log.info("Expected link cap speed from config is :".format(self._expected_lnkcap_speed))
        for each_device in cpu_root_device_list:
            for each_bdf, device_details in each_device.items():
                if not device_details[PcieAttribute.LINKCAP_SPEED] == self._expected_lnkcap_speed:
                    unexpected_device_list.append(each_device)

        if not unexpected_device_list:
            self._log.debug("CPU root port has expected value for devices: {}".format(cpu_root_device_list))
        else:
            raise content_exceptions.TestFail(
                "CPU root Port not matched with the expected result : {} and CPU root port data is : {}".format(
                    self._expected_lnkcap_speed, cpu_root_device_list))
        self._log.info("CPU root device has expected value ...")
        # pch root
        if IntelPcieDeviceId.PCH_ROOT_DEVICES[self.product_family] != "None":
            self._log.info("Checking PCH root device")
            if self.os.os_type.lower() == OperatingSystems.LINUX.lower():
                self.pcie_common_util_obj.check_pci_device_exist(PcieDeviceClassConstants.PCIE_BRIDGE,
                                                                 IntelPcieDeviceId.PCH_ROOT_DEVICES[
                                                                     self.product_family])
            elif self.os.os_type.lower() == OperatingSystems.WINDOWS.lower():
                self.pcie_common_util_obj.check_pci_device_exist(PcieDeviceClassConstants.PCIE_BRIDGE_WINDOWS,
                                                                 IntelPcieDeviceId.PCH_ROOT_DEVICES[
                                                                     self.product_family])
        # usb
        if IntelPcieDeviceId.XHCI_DEVICE_ID[self.product_family] != "None":
            self._log.info("Checking USB device")
            if self.os.os_type.lower() == OperatingSystems.LINUX.lower():
                self.pcie_common_util_obj.check_pci_device_exist(PcieDeviceClassConstants.PCIE_USB,
                                                                 IntelPcieDeviceId.XHCI_DEVICE_ID[self.product_family])
            elif self.os.os_type.lower() == OperatingSystems.WINDOWS.lower():
                self.pcie_common_util_obj.check_pci_device_exist(PcieDeviceClassConstants.PCIE_USB_WINDOWS,
                                                                 IntelPcieDeviceId.XHCI_DEVICE_ID[self.product_family])
        # sata
        if IntelPcieDeviceId.SATA_DEVICE_ID[self.product_family] != "None":
            self._log.info("Checking SATA device")
            self.pcie_common_util_obj.check_pci_device_exist(PcieDeviceClassConstants.PCIE_SATA_CONTROLLER,
                                                             IntelPcieDeviceId.SATA_DEVICE_ID[self.product_family])

        # Me
        if IntelPcieDeviceId.ME_DEVICE_ID[self.product_family] != "None":
            self._log.info("Checking ME device")
            self.pcie_common_util_obj.check_pci_device_exist(PcieDeviceClassConstants.PCIE_ME,
                                                             IntelPcieDeviceId.ME_DEVICE_ID[self.product_family])
        # lpc espi
        if IntelPcieDeviceId.LPC_ESPI_DEVICE_ID[self.product_family] != "None":
            self._log.info("Checking lpc espi device")
            if self.os.os_type.lower() == OperatingSystems.LINUX.lower():
                self.pcie_common_util_obj.check_pci_device_exist(PcieDeviceClassConstants.PCIE_LPC_ESPI,
                                                                 IntelPcieDeviceId.LPC_ESPI_DEVICE_ID[
                                                                     self.product_family])
            elif self.os.os_type.lower() == OperatingSystems.WINDOWS.lower():
                self.pcie_common_util_obj.check_pci_device_exist(PcieDeviceClassConstants.PCIE_LPC_ESPI_WINDOWS,
                                                                 IntelPcieDeviceId.LPC_ESPI_DEVICE_ID[
                                                                     self.product_family])
        # smbus
        if IntelPcieDeviceId.SMBUS_DEVICE_ID[self.product_family] != "None":
            self._log.info("Checking SMBUS device")
            self.pcie_common_util_obj.check_pci_device_exist(PcieDeviceClassConstants.PCIE_SMBUS,
                                                             IntelPcieDeviceId.SMBUS_DEVICE_ID[self.product_family])
        # spi
        if IntelPcieDeviceId.SPI_DEVICE_ID[self.product_family] != "None":
            self._log.info("Checking SPI device")
            if self.os.os_type.lower() == OperatingSystems.LINUX.lower():
                self.pcie_common_util_obj.check_pci_device_exist(PcieDeviceClassConstants.PCIE_SPI,
                                                                 IntelPcieDeviceId.SPI_DEVICE_ID[self.product_family])
            elif self.os.os_type.lower() == OperatingSystems.WINDOWS.lower():
                self.pcie_common_util_obj.check_pci_device_exist(PcieDeviceClassConstants.PCIE_SPI_WINDOWS,
                                                                 IntelPcieDeviceId.SPI_DEVICE_ID[self.product_family])
        # ethernet
        if IntelPcieDeviceId.ETHERNET_DEVICE_ID[self.product_family] != "None":
            self._log.info("Checking Ethernet device")
            self.pcie_common_util_obj.check_pci_device_exist(PcieDeviceClassConstants.PCIE_ETHERNET_CONTROLLER,
                                                             IntelPcieDeviceId.ETHERNET_DEVICE_ID[self.product_family])
        if unexpected_device_list:
            raise content_exceptions.TestFail("Unexpected lnkcap speed found for devices: {}".format(
                unexpected_device_list))
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieConfigDisplay.main() else Framework.TEST_RESULT_FAIL)
