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

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.test_content_logger import TestContentLogger
from src.pcie.tests.pi_pcie.pcie_common import PcieCommon
from src.lib.dtaf_content_constants import LinuxCyclingToolConstant, PcieAttribute
from src.lib import content_exceptions


class PcieSlotCEndPointLtssmTesting(PcieCommon):
    """
    HPQC : PI_PCH_SlotC_LTSSM_Endpoint_Testing_L
    GLASGOW ID : 10527.12

    The purpose of this Test Case is to verify the functionality of all supported pcie link state transition
    for a specific adapter in all slot of the system.
    """
    TEST_CASE_ID = ["H89967", "PI_PCH_SlotC_LTSSM_Endpoint_Testing_L"]

    step_data_dict = {
        1: {'step_details': 'Check PCIe device Link speed and Width speed',
            'expected_results': 'PCIe Link speed and width speed as Expected'},
        2: {'step_details': 'Disable the driver and run the ltssm test',
            'expected_results': 'Device driver disabled successfully and passed ltssm Test'},
        3: {'step_details': 'Check MCE Error',
            'expected_results': 'No MCE Error Captured'},
        4: {'step_details': 'Boot the SUT',
            'expected_results': 'SUT booted Successfully'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a PcieSlotCEndPointLtssmTesting object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PcieSlotCEndPointLtssmTesting, self).__init__(test_log, arguments, cfg_opts)
        self._cfg = cfg_opts
        self._sut_path = self._pcie_ltssm_provider.install_ltssm_tool()
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)
        self.LTSSM_TEST_NAME_LIST = self._common_content_configuration.get_ltssm_test_list()

    def execute(self):
        """
        This method is to execute:
        1. Check Link and Width Speed.
        2. Test LTSSM Tool execution
        3. Check MCE Log in OS Log.

        :return: True or False
        """
        summary_status_dict = {}
        test_status_list = []
        product_family = self._common_content_lib.get_platform_family()
        slot_info = self._common_content_configuration.get_pch_slot_c_info(self._product_family)
        self._test_content_logger.start_step_logger(1)
        bus_output = slot_info['bus']
        device_details = self._pcie_provider.get_device_details_with_bus(bus_output)
        if len(device_details) < 1:
            raise content_exceptions.TestFail("Device Details are not Captured, Please Verify Configuration, "
                                              "VMD-Disable Mode and try again")
        self._test_content_logger.end_step_logger(1, True)

        for bdf_value in device_details.keys():
            self._test_content_logger.start_step_logger(2)
            for each_test in self.LTSSM_TEST_NAME_LIST:
                if self._pcie_ltssm_provider.run_ltssm_tool(test_name=each_test,
                                                         device_id=device_details[bdf_value][PcieAttribute.DEVICE_ID],
                                                         cmd_path=self._sut_path, bdf=bdf_value,skip_errors_on_failures=True):
                    summary_status_dict[each_test] = "Passed"
                    test_status_list.append(True)
                else:
                    summary_status_dict[each_test] = "Failed"
                    test_status_list.append(False)

            self._test_content_logger.end_step_logger(2, True)
            self._test_content_logger.start_step_logger(3)
            mce_error = self._common_content_lib.check_if_mce_errors()
            if mce_error:
                raise content_exceptions.TestFail("MCE error was Captured in Log.")
            self._log.debug("No MCE error was Captured in Os Log")
            self._test_content_logger.end_step_logger(3, True)
            self._test_content_logger.start_step_logger(4)
            self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
            self.os.wait_for_os(self.reboot_timeout)
            self._test_content_logger.end_step_logger(4, True)
            break
        if not bool(test_status_list):
            raise content_exceptions.TestFail("Test is Failed. Test Summary: {}".format(summary_status_dict))
        self._log.info("Test Passed Summary: {}".format(summary_status_dict))

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieSlotCEndPointLtssmTesting.main() else Framework.TEST_RESULT_FAIL)
