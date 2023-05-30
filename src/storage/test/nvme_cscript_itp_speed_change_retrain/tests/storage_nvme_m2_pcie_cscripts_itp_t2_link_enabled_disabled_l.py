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
from src.lib.install_collateral import InstallCollateral
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.test_content_logger import TestContentLogger
from src.lib.dtaf_content_constants import PcieAttribute
from src.provider.pcie_provider import PcieProvider
from src.provider.pcie_ltssm_provider import PcieLtssmToolProvider
from src.lib import content_exceptions


class StorageNvmeM2PcieCScriptsItpT2LinkDisableLinux(ContentBaseTestCase):
    """
    Glasgow ID : G56606- NVMe_M.2_PCIe_CScripts_ITP_T2_Link Enabled - Disabled
    The purpose of this Test Case is to verify the functionality of all supported M.2 nvme link state transition
    for a specific adapter in all slot of the system.
    """
    TEST_CASE_ID = ["G56606", "NVMe_M.2_PCIe_CScripts_ITP_T2_Link Enabled - Disabled"]
    LTSSM_TEST_NAME = "linkDisable"
    step_data_dict = {
        1: {'step_details': 'Install the Ltssm tool on SUT',
            'expected_results': 'Ltssm tool installed successfully'},
        2: {'step_details': 'To get the bus id',
            'expected_results': 'Fetched bus id'},
        3: {'step_details': 'Check NVME device Link speed, Width and run the Ltssm Test',
            'expected_results': 'NVME Link speed and width speed as Expected and passed Ltssm Test'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a StorageNvmeM2PcieCScriptsItpT2LinkDisableLinux object
        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(StorageNvmeM2PcieCScriptsItpT2LinkDisableLinux, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)
        self.install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._product_family = self._common_content_lib.get_platform_family()
        self._pcie_provider = PcieProvider.factory(self._log, self.os, cfg_opts, "os", uefi_obj=None)
        self._pcie_ltssm_provider = PcieLtssmToolProvider.factory(log=self._log, cfg_opts=cfg_opts,
                                                                  os_obj=self.os, pcie_provider_obj=self._pcie_provider)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(StorageNvmeM2PcieCScriptsItpT2LinkDisableLinux, self).prepare()

    def execute(self):
        """
        This method is to execute:
        1. Install LTSSM Tools.
        2. To Get Bus id.
        3. Check Link Width, Speed and Test LTSSM Tool execution and Check Errors.
        :return: True or False
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        sut_folder_path = self.install_collateral.install_ltssm_tool()
        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        slot_info = self._common_content_configuration.get_pch_slot_nvme_m2_info(self._product_family)
        bus_output = slot_info['bus']
        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)
        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)
        device_details = self._pcie_provider.get_device_details_with_bus(bus_output)
        if len(device_details) < 1:
            raise content_exceptions.TestFail("Device Details are not Captured, Please Verify Configuration, "
                                              "VMD-Disable Mode and try again")
        for bdf_value in device_details.keys():
            self._pcie_ltssm_provider.run_ltssm_tool(test_name=self.LTSSM_TEST_NAME,
                                                     device_id=device_details[bdf_value][PcieAttribute.DEVICE_ID],
                                                     cmd_path=sut_folder_path, bdf=bdf_value, disable_kernel_driver=False)
            break
        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(StorageNvmeM2PcieCScriptsItpT2LinkDisableLinux, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StorageNvmeM2PcieCScriptsItpT2LinkDisableLinux.main() else Framework.TEST_RESULT_FAIL)
