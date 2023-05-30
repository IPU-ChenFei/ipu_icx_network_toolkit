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

from src.lib.test_content_logger import TestContentLogger
from src.pcie.tests.pi_pcie.pcie_common import PcieCommon, PxpInventory
from src.lib import content_exceptions
from dtaf_core.providers.provider_factory import ProviderFactory


class PcieAdapterIoBusCheck(PcieCommon):
    """
    HPQC ID : H82172, H82173
    GLASGOW : 10473.6, 16400

    This Testcase is used to check the io adapter function in each supported slot.
    """
    TEST_CASE_ID = ["H82172", "PI_PCIe_Adapter_I0_Bus_Check_L", "H82173", "PI_PCIe_Adapter_IO_Bus_Check_W",
                    "G10473", "PCI_Express_PCIe_Adapter_IO_Bus_Check",
                    "G16400", "PCI_Express_PCIe_Subsytem_IO_Bus_Check"]
    step_data_dict = {
        1: {'step_details': 'Check SUT is alive or not',
            'expected_results': 'SUT should be in OS'},
        2: {'step_details': 'Check driver for PCIe Device',
            'expected_results': 'Driver should be visible'},
        3: {'step_details': 'Check PCIe Device LnkCap Speed and Width is correct or not',
            'expected_results': 'PCIe Device LnkCap Speed and Width should be as Expected'},
        4: {'step_details': 'Check PCIe Error',
            'expected_results': 'No PCIe Error Captured in WHEA Error'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a PcieAdapterIoBusCheck object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PcieAdapterIoBusCheck, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)

    def execute(self):
        """
        This is Used to check pcie adapter io bus.
        1. Check SUT is in OS or not.
        2. Check Kernel Driver
        3. Check LnkCap Speed and Width.

        :return: True or False
        """
        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        self._test_content_logger.start_step_logger(1)
        if not self.os.is_alive():
            raise content_exceptions.TestFail("SUT is not Alive")
        self._test_content_logger.end_step_logger(1, True)

        slot_list = self._common_content_configuration.get_pcie_slot_to_check()
        pcie_slot_device_list = self._common_content_configuration.get_required_pcie_device_details(
            product_family=self._product_family, required_slot_list=slot_list)
        each_slot_in_list = []
        for each_slot in pcie_slot_device_list:
            each_slot_in_list.clear()
            each_slot_in_list.append(each_slot)
            pcie_device_info_dict = self.verify_required_slot_pcie_device(cscripts_obj=cscripts_obj,
                                                                          pcie_slot_device_list=each_slot_in_list,
                                                                          generation=5)
            self._test_content_logger.start_step_logger(2)

            for pcie_info_dict in pcie_device_info_dict:
                for bdf_key, pcie_device_details_value in pcie_info_dict.items():

                    if not self._pcie_provider.get_driver_status_by_bdf(bdf=bdf_key):
                        raise content_exceptions.TestFail("Device Driver is not available for slot: {} and "
                                                          "bdf: {}".format(each_slot, bdf_key))
                    break
            self._test_content_logger.end_step_logger(2, True)

            self._test_content_logger.start_step_logger(3)
            self.verify_required_slot_pcie_device(cscripts_obj=cscripts_obj,
                                                  pcie_slot_device_list=each_slot_in_list, lnk_cap_width_speed=False,
                                                  lnk_stat_width_speed=True, generation=self.get_pcie_controller_gen(
                    PxpInventory.PCIeLinkSpeed.GEN5))
            self._test_content_logger.end_step_logger(3, True)

        self._test_content_logger.start_step_logger(4)
        self._pcie_util_obj.check_memory_controller_error()
        self._log.info('No PCIe Error was Captured')
        self._test_content_logger.end_step_logger(4, True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieAdapterIoBusCheck.main() else Framework.TEST_RESULT_FAIL)
