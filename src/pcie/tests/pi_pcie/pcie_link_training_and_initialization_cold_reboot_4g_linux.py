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
import os

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions

from src.lib.test_content_logger import TestContentLogger
from src.pcie.tests.pi_pcie.pcie_common import PcieCommon
from dtaf_core.providers.provider_factory import ProviderFactory
from src.lib.dtaf_content_constants import LinuxCyclingToolConstant, PcieSlotAttribute


class PcieLinkTrainingAndInitializationColdReboot4gLinux(PcieCommon):
    """
    HPQC ID : H89961-PI_PCIe_Link_training_and_Initialization_Overnight_AC_cycling_Gen4_L

    This Testcase is used to check the pcie link train and initialize proper after Cold reboot.
    """
    BIOS_CONFIG_FILE = "gen4_bios_knobs_config.cfg"
    TEST_CASE_ID = ["H89961", "PI_PCIe_Link_training_and_Initialization_Overnight_AC_cycling_Gen4_L"]

    SCRIPT_FILE_NAME = LinuxCyclingToolConstant.CYCLING_SCRIPTS_FILE_NAME

    ARGUMENTS = {"ex: sda sdb sdc sdd hda hdb": "1",
                 "ex: 13.4.1.1 13.4.2.1 13.4.3.1 13.4.4.1 12.8.1.1 12.8.2.1": "1",
                 "ex: init 6 or shutdown -r now": "init 0"}

    step_data_dict = {
        1: {'step_details': 'Check the required PCIe Slot Device is Populated and Verify LnkCap Speed and Width',
            'expected_results': 'Required PCIe Slot device should populate and LnkCap Speed and Width should be '
                                'as Expected'},
        2: {'step_details': 'Execute Cycle Tool and perform Cold reboot',
            'expected_results': 'After Cold Reboot SUT should boot to OS and should visible all '
                                'populated slot'},
        3: {'step_details': 'Verify the Cycling Log',
            'expected_results': 'No Error should Capture'},
        4: {'step_details': 'Check LnkCap Speed and Width after Cycling Completed',
            'expected_results': 'LnkCap Speed and Width should be an Expected'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a PcieLinkTrainingAndInitializationColdReboot4gLinux object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PcieLinkTrainingAndInitializationColdReboot4gLinux, self).__init__(test_log, arguments, cfg_opts,
                                                                                   self.BIOS_CONFIG_FILE)

        self._cycling_tool_sut_folder_path = self._install_collateral.install_cycling_tool_to_sut()
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):  # type: () -> None
        """
        This method is used to copy collateral scripts to SUT.
        """
        self._install_collateral.copy_collateral_script(self.SCRIPT_FILE_NAME,
                                                        self._cycling_tool_sut_folder_path.strip())
        super(PcieLinkTrainingAndInitializationColdReboot4gLinux, self).prepare()

    def execute(self):
        """
        This is Used to check the stability of SUT after cold reboot cycle.

        :return: True or False
        """
        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        slot_list = self._common_content_configuration.get_pcie_slot_to_check()
        if any(item in PcieSlotAttribute.PCH_SLOT for item in slot_list):
            raise content_exceptions.TestFail("Please remove PCH slot for Gen4 test")
        pcie_slot_device_list = self._common_content_configuration.get_required_pcie_device_details(
            product_family=self._product_family, required_slot_list=slot_list)
        each_slot_in_list = []

        self._test_content_logger.start_step_logger(1)
        # Check LnkCap speed and Width before Cycling.
        for each_slot in pcie_slot_device_list:
            each_slot_in_list.clear()
            each_slot_in_list.append(each_slot)
            self.verify_required_slot_pcie_device(cscripts_obj=cscripts_obj, pcie_slot_device_list=each_slot_in_list,
                                                  lnk_cap_width_speed=True, lnk_stat_width_speed=False, generation=4)
        self._test_content_logger.end_step_logger(1, True)

        self._test_content_logger.start_step_logger(2)
        # Execute Cycling Tool and Perform Cold reboot.
        self.execute_the_cycling_tool(
            arguments=self.ARGUMENTS, directory_path=self._cycling_tool_sut_folder_path.strip(), boot_type="ac_cycle")
        self._test_content_logger.end_step_logger(2, True)

        self._test_content_logger.start_step_logger(3)
        # Verify the Cycling Log
        self.verify_cycling_log()
        self._test_content_logger.end_step_logger(3, True)

        self._test_content_logger.start_step_logger(4)
        # Check LnkCap Speed and Width after cycle.
        for each_slot in pcie_slot_device_list:
            each_slot_in_list.clear()
            each_slot_in_list.append(each_slot)
            self.verify_required_slot_pcie_device(cscripts_obj=cscripts_obj, pcie_slot_device_list=each_slot_in_list,
                                                  lnk_cap_width_speed=True, lnk_stat_width_speed=False, generation=4)
            self._test_content_logger.end_step_logger(4, True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieLinkTrainingAndInitializationColdReboot4gLinux.main()
             else Framework.TEST_RESULT_FAIL)
