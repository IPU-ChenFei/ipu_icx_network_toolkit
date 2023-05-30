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
from src.lib.content_base_test_case import ContentBaseTestCase
from src.provider.pcie_provider import PcieProvider
from src.pcie.lib.pcie_common_utils import PcieCommonUtil
from src.lib.dtaf_content_constants import IntelPcieDeviceId
from src.lib.dtaf_content_constants import PcieLinuxDriverNameConstant


class PcieKernelDriverCheckLinux(ContentBaseTestCase):
    """
    HPQALM ID : H79593

    This Testcase is used to check if a pcie Kernel driver.
    """
    TEST_CASE_ID = ["H79593"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a PcieKernelDriverCheckLinux object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PcieKernelDriverCheckLinux, self).__init__(test_log, arguments, cfg_opts)
        self._cfg = cfg_opts
        pcie_provider_obj = PcieProvider.factory(log=test_log, os_obj=self.os, cfg_opts=cfg_opts, execution_env='os',
                                                 uefi_obj=None)
        self.pcie_common_util_obj = PcieCommonUtil(test_log, self.os, self._common_content_configuration,
                                                   pcie_provider_obj, cfg_opts)
        self.product_family = self._common_content_lib.get_platform_family()
        if self._common_content_configuration.get_device_driver_from_config():
            IntelPcieDeviceId.CPU_ROOT_DEVICES[self.product_family] = self._common_content_configuration.get_cpu_device_id()
            IntelPcieDeviceId.PCH_ROOT_DEVICES[self.product_family] = self._common_content_configuration.get_pch_device_id()
            IntelPcieDeviceId.XHCI_DEVICE_ID[self.product_family] = self._common_content_configuration.get_xhci_device_id()
            IntelPcieDeviceId.SATA_DEVICE_ID[self.product_family] = self._common_content_configuration.get_sata_device_id()
            IntelPcieDeviceId.ME_DEVICE_ID[self.product_family] = self._common_content_configuration.get_me_device_id()
            IntelPcieDeviceId.LPC_ESPI_DEVICE_ID[self.product_family] = self._common_content_configuration.get_lpc_espi_device_id()
            IntelPcieDeviceId.SMBUS_DEVICE_ID[self.product_family] = self._common_content_configuration.get_smbus_device_id()
            IntelPcieDeviceId.SPI_DEVICE_ID[self.product_family] = self._common_content_configuration.get_spi_device_id()
            IntelPcieDeviceId.ETHERNET_DEVICE_ID[self.product_family] = self._common_content_configuration.get_ethernet_device_id()
            IntelPcieDeviceId.AHCI_DEVICE_ID[self.product_family] = self._common_content_configuration.get_ahci_device_id()
            PcieLinuxDriverNameConstant.KERNEL_DRIVER_ETHERNET = self._common_content_configuration.get_ethernet_kernel_driver()

    def execute(self):
        """
        This is Used to Verify if Pcie kernel driver is detected or not.

        :return: True or False
        """
        self.pcie_common_util_obj.check_pcie_kernel_driver(IntelPcieDeviceId.CPU_ROOT_DEVICES[self.product_family],
                                                           PcieLinuxDriverNameConstant.KERNEL_DRIVER_PCIE_PORT)

        if IntelPcieDeviceId.PCH_ROOT_DEVICES[self.product_family] != "None":
            self.pcie_common_util_obj.check_pcie_kernel_driver(IntelPcieDeviceId.PCH_ROOT_DEVICES[self.product_family],
                                                               PcieLinuxDriverNameConstant.KERNEL_DRIVER_PCIE_PORT)

        if IntelPcieDeviceId.SMBUS_DEVICE_ID[self.product_family] != "None":
            self.pcie_common_util_obj.check_pcie_kernel_driver(IntelPcieDeviceId.SMBUS_DEVICE_ID[self.product_family],
                                                               PcieLinuxDriverNameConstant.KERNEL_DRIVER_I801_SMBUS)

        if IntelPcieDeviceId.AHCI_DEVICE_ID[self.product_family] != "None":
            self.pcie_common_util_obj.check_pcie_kernel_driver(IntelPcieDeviceId.AHCI_DEVICE_ID[self.product_family],
                                                               PcieLinuxDriverNameConstant.KERNEL_DRIVER_AHCI)

        if IntelPcieDeviceId.XHCI_DEVICE_ID[self.product_family] != "None":
            self.pcie_common_util_obj.check_pcie_kernel_driver(IntelPcieDeviceId.XHCI_DEVICE_ID[self.product_family],
                                                               PcieLinuxDriverNameConstant.KERNEL_DRIVER_XHCI)

        if IntelPcieDeviceId.ETHERNET_DEVICE_ID[self.product_family] != "None":
            self.pcie_common_util_obj.check_pcie_kernel_driver(IntelPcieDeviceId.ETHERNET_DEVICE_ID[self.product_family],
                                                               PcieLinuxDriverNameConstant.KERNEL_DRIVER_ETHERNET)

        if IntelPcieDeviceId.SATA_DEVICE_ID[self.product_family] != "None":
            self.pcie_common_util_obj.check_pcie_kernel_driver(IntelPcieDeviceId.SATA_DEVICE_ID[self.product_family],
                                                               PcieLinuxDriverNameConstant.KERNEL_DRIVER_ME)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieKernelDriverCheckLinux.main() else Framework.TEST_RESULT_FAIL)
