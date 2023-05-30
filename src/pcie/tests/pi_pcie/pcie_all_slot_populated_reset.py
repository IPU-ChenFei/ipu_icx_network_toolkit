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
import time

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from src.pcie.tests.pi_pcie.pcie_common import PcieCommon
from dtaf_core.providers.provider_factory import ProviderFactory
from src.lib.test_content_logger import TestContentLogger


class PcieAllSlotPopulatedReset(PcieCommon):
    """
    HPQC : H92895, H92894

    This Testcase is used to check the stability of Machine after populating all slot with Warm reboot.
    """
    TEST_CASE_ID = ["H92895", "PI_PCIE_All_Slot_Populated_Reset_W"]
    SLEEP_TIME = 60
    step_data_dict = {
        1: {'step_details': 'Check the required PCIe Slot Device is Populated',
            'expected_results': 'Required PCIe Slot device should populate'},
        2: {'step_details': 'Apply Warm Reboot',
            'expected_results': 'After Warm Reboot SUT should boot to OS and should visible all '
                                'populated slot'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a PcieAllSlotPopulatedReset object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PcieAllSlotPopulatedReset, self).__init__(test_log, arguments, cfg_opts)
        if self.os.os_type == OperatingSystems.LINUX:
            self.TEST_CASE_ID = ["H92894", "PI_PCIE_All_Slot_Populated_Reset_L"]
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):  # type: () -> None
        """
        This method to execute prepare.
        """
        super(PcieAllSlotPopulatedReset, self).prepare()

    def execute(self):
        """
        This is Used to check pcie adapter io bus.
        1. Validate the required Slot is available and Validate Speed and Width for All Slot.
        2. Perform OS reboot 5 time.

        :return: True or False
        """
        self._test_content_logger.start_step_logger(1)
        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        slot_list = self._common_content_configuration.get_pcie_slot_to_check()
        pcie_slot_device_list = self._common_content_configuration.get_required_pcie_device_details(
            product_family=self._product_family, required_slot_list=slot_list)
        self.verify_required_slot_pcie_device(cscripts_obj=cscripts_obj, pcie_slot_device_list=pcie_slot_device_list,
                                              generation=5, lnk_cap_width_speed=False, lnk_stat_width_speed=False)
        self._test_content_logger.end_step_logger(1, True)

        self._test_content_logger.start_step_logger(2)
        for iteration_time in range(0, 5):
            time.sleep(self.SLEEP_TIME)
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)
            self._log.info("Reboot cycle  # {} completed and SUT booted to OS Successfully".format(iteration_time + 1))
            time.sleep(self.SLEEP_TIME)
            self.verify_required_slot_pcie_device(cscripts_obj=cscripts_obj,
                                                  pcie_slot_device_list=pcie_slot_device_list,
                                                  generation=5, lnk_cap_width_speed=False, lnk_stat_width_speed=False)
        self._test_content_logger.end_step_logger(2, True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieAllSlotPopulatedReset.main() else Framework.TEST_RESULT_FAIL)
