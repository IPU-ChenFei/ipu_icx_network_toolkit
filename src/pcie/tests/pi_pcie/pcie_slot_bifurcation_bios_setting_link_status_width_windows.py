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


class PcieSlotBifurcationBiosSettingLinkStatusWidthWindows(PcieCommon):
    """
    HPQC : H89970-PI_PCIe_Slot_Bifurcation_Bios_Setting_Link_Status_Width_W

    Verify Bifurcation bios setting in sls and Verify width and speed
    """
    TEST_CASE_ID = ["H89970", "PI_PCIe_Slot_Bifurcation_Bios_Setting_Link_Status_Width_W"]

    _BIOS_CONFIG_FILE = "bifurcation_by_four_bios_knobs.cfg"
    step_data_dict = {
        1: {'step_details': 'Check Bifurcation in pcie.sls',
            'expected_results': 'Bifurcation should be as Expected'},
        2: {'step_details': 'Check Width and Speed in OS',
            'expected_results': 'Configuration Width and Speed should match with OS '}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a PcieSlotBifurcationBiosSettingLinkStatusWidthLinux object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PcieSlotBifurcationBiosSettingLinkStatusWidthWindows, self).__init__(test_log, arguments, cfg_opts,
                                                                                   self._BIOS_CONFIG_FILE)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):  # type: () -> None
        """
        This method is to execute prepare.
        """
        super(PcieSlotBifurcationBiosSettingLinkStatusWidthWindows, self).prepare()

    def execute(self):
        """
        This method is to execute:
        1. Verify Bifurcation in pcie.sls.
        2. Check LinkStat Speed and Width.

        :return: True or False
        """
        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        sdp_obj = ProviderFactory.create(self.sdp_cfg, self._log)

        # Verify bifurcation in pcie.sls
        self._test_content_logger.start_step_logger(1)
        self.verify_bifurcation_status_in_sls(csp=cscripts_obj, sdp=sdp_obj)
        self._test_content_logger.end_step_logger(1, True)

        # Verify Speed and Width
        self._test_content_logger.start_step_logger(2)
        slot_list = self._common_content_configuration.get_bifurcation_pcie_slot_to_check()
        other_slot_list = self._common_content_configuration.get_pcie_slot_to_check()
        # To check the valid slot for bifurcation test
        for each_slot in slot_list:
            if each_slot not in PcieSlotAttribute.BIFURCATION_SLOTS:
                self._log.error("This test is valid for only slot e and slot b bifurcation")
                raise content_exceptions.TestFail("Please remove slot: {} from config for bifurcation "
                                                  "test".format(each_slot))
        for each_other_slot in other_slot_list:
            if each_other_slot in PcieSlotAttribute.BIFURCATION_SLOT_NAME:
                raise content_exceptions.TestFail("Please remove the slot_e and slot_b from select_slot")

        pcie_slot_device_list = self._common_content_configuration.get_required_pcie_device_details(
            product_family=self._product_family, required_slot_list=slot_list)
        each_slot_in_list = []
        for each_slot in pcie_slot_device_list:
            each_slot_in_list.clear()
            each_slot_in_list.append(each_slot)

            self.verify_required_slot_pcie_device(cscripts_obj=cscripts_obj,
                                                  pcie_slot_device_list=each_slot_in_list, lnk_cap_width_speed=False,
                                                  lnk_stat_width_speed=True, generation=5)
        self._test_content_logger.end_step_logger(2, True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieSlotBifurcationBiosSettingLinkStatusWidthWindows.main() else Framework.TEST_RESULT_FAIL)
