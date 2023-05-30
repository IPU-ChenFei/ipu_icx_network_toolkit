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

from src.lib.test_content_logger import TestContentLogger
from src.pcie.tests.pi_pcie.pcie_common import PcieCommon


class PCIExpressPcieGen3LinkWidthVerification(PcieCommon):
    """
    Glasgow : 29886-PCI_Express_PCIe_Gen3_Link_Width_verification

    To verify that each Gen3 PCI express slot in the system can link a Gen3 adapter at all supported link widths.

    """
    TEST_CASE_ID = ["G29886", "PCIExpressPCIeGen3LinkWidthVerification"]

    step_data_dict = {
        1: {'step_details': 'Check require PCIe slot is populated or not',
            'expected_results': 'Required PCIe slot is populated as Expected'},
        2: {'step_details': 'Check Populated PCIe Card has Gen3 Link speed and width',
            'expected_results': 'Populated PCIe Card has Gen3 Link speed and Width as expected'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a PCIExpressPcieGen3LinkWidthVerification object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PCIExpressPcieGen3LinkWidthVerification, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):  # type: () -> None
        """
        This method is to execute prepare.
        """
        super(PCIExpressPcieGen3LinkWidthVerification, self).prepare()

    def execute(self):
        """
        This method is to execute:
        1. Get PCI Device Details from Config File.
        2. Check require slot is populated or not.
        3. Check Populated Gen3 PCIe slot has Gen3 Link Stat speed and Width.

        :return: True or False
        """
        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)

        self._test_content_logger.start_step_logger(1)
        # Getting populated slot list from config file.
        slot_list = self._common_content_configuration.get_pcie_slot_to_check()
        # Getting the populated slot info from config file.
        pcie_slot_device_list = self._common_content_configuration.get_required_pcie_device_details(
            product_family=self._product_family, required_slot_list=slot_list)
        self._test_content_logger.end_step_logger(1, True)

        self._test_content_logger.start_step_logger(2)
        # Verifying Link status speed for populated speed
        each_slot_in_list = []
        for each_slot in pcie_slot_device_list:
            each_slot_in_list.clear()
            each_slot_in_list.append(each_slot)
            self.verify_required_slot_pcie_device(cscripts_obj=cscripts_obj, pcie_slot_device_list=each_slot_in_list,
                                                  lnk_stat_width_speed=True, generation=5)
        self._test_content_logger.end_step_logger(2, True)
        return True

    def cleanup(self, return_status):
        super(PCIExpressPcieGen3LinkWidthVerification, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PCIExpressPcieGen3LinkWidthVerification.main() else
             Framework.TEST_RESULT_FAIL)
