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
from dtaf_core.providers.provider_factory import ProviderFactory

from src.lib.dtaf_content_constants import PcieSlotAttribute
from src.lib.test_content_logger import TestContentLogger
from src.pcie.tests.pi_pcie.pcie_common import PcieCommon
from src.lib import content_exceptions


class PcieModelAvailabilityOsGen4Windows(PcieCommon):
    """
    HPQC : 79612-PI_PCIe_PCIModelAvailability_OS_Gen4_RS5_W

    Verify PCI bus function: After populating add-in card, the SUT can enter OS correctly,
    the linkspeed is expected and the new Wake feature can work.
    """
    TEST_CASE_ID = ["H79612", "PI_PCIe_PCIModelAvailability_OS_Gen4_RS5_W"]

    _BIOS_CONFIG_FILE = "gen4_bios_knobs_config.cfg"
    step_data_dict = {
        1: {'step_details': 'To Check SUT is in OS or not',
            'expected_results': 'SUT should reach to OS'},
        2: {'step_details': 'Check MCE Error',
            'expected_results': 'No MCE Error should Capture in OS'},
        3: {'step_details': 'Check driver is installed or not',
            'expected_results': 'Driver should present'},
        4: {'step_details': 'Check LinkCap, LinkStat Speed and Width',
            'expected_results': 'LinkCap, LinkStat Speed and Width should match config details'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a PcieModelAvailabilityOsGen4Windows object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PcieModelAvailabilityOsGen4Windows, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)

    def execute(self):
        """
        This method is to execute:
        1. Check MCE Error.
        2. Check Driver is present or not.
        3. Check LinkCap, LinkStat Speed and Width.

        :return: True or False
        """
        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        self._test_content_logger.start_step_logger(1)
        if not self.os.is_alive():
            raise content_exceptions.TestFail("SUT is not alive")
        self._log.info("SUT is in OS as expected")
        self._test_content_logger.end_step_logger(1, True)
        self._test_content_logger.start_step_logger(2)
        mce_error = self._common_content_lib.check_if_mce_errors()
        if mce_error:
            raise content_exceptions.TestFail("MCE Error was captured in OS")
        self._log.info("No MCE Error was captured in OS Log")
        self._test_content_logger.end_step_logger(2, True)

        slot_list = self._common_content_configuration.get_pcie_slot_to_check()
        if any(item in PcieSlotAttribute.PCH_SLOT for item in slot_list):
            raise content_exceptions.TestFail("Please remove PCH slot for Gen5 test")
        pcie_slot_device_list = self._common_content_configuration.get_required_pcie_device_details(
            product_family=self._product_family, required_slot_list=slot_list)
        each_slot_in_list = []
        for each_slot in pcie_slot_device_list:
            each_slot_in_list.clear()
            each_slot_in_list.append(each_slot)
            pcie_device_info_dict = self.verify_required_slot_pcie_device(cscripts_obj=cscripts_obj,
                                                                          pcie_slot_device_list=each_slot_in_list,
                                                                          generation=4)
            self._test_content_logger.start_step_logger(3)

            for pcie_info_dict in pcie_device_info_dict:
                for bdf_key, pcie_device_details_value in pcie_info_dict.items():

                    if not self._pcie_provider.get_driver_status_by_bdf(bdf=bdf_key):
                        raise content_exceptions.TestFail("Device Driver is not available for slot: {} and "
                                                          "bdf: {}".format(each_slot, bdf_key))
                    break
            self._test_content_logger.end_step_logger(3, True)

            self._test_content_logger.start_step_logger(4)
            self.verify_required_slot_pcie_device(cscripts_obj=cscripts_obj,
                                                  pcie_slot_device_list=each_slot_in_list, lnk_cap_width_speed=True,
                                                  lnk_stat_width_speed=True, generation=4)
            self._test_content_logger.end_step_logger(4, True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieModelAvailabilityOsGen4Windows.main() else Framework.TEST_RESULT_FAIL)
