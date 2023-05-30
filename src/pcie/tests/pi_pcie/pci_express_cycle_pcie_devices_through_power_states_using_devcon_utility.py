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
from src.pcie.tests.pi_pcie.pcie_common import PcieCommon
from src.lib import content_exceptions


class PciExpressCyclePcieDevicesThroughPowerStatesUsingDevconUtility(PcieCommon):
    """
    GLASGOW ID : G56022.0

    The purpose of this Test Case is use the Devcon utility to exercize the power state switching capabilities of a
    system chipset and attached devices.
    """
    TEST_CASE_ID = ["G56022.0-PCI_Express_Cycle_PCIe_Devices_Through_Power_States_Using_Devcon_Utility"]

    step_data_dict = {
        1: {'step_details': 'Copy the file "DriverCycleWin.zip" from host to the SUT, Extract the zip file',
            'expected_results': 'Copied and extracted the file "DriverCycleWin.zip" from host to the SUT'},
        2: {'step_details': 'Start the devcon test to enable and disable the desired PCIe devices in the SUT',
            'expected_results': 'Successfully executed the devcon test to enable and disable the desired PCIe '
                                'devices in the SUT'},
        3: {'step_details': 'Check MCE Error',
            'expected_results': 'No MCE Error Captured'},
        4: {'step_details': 'Boot the SUT',
            'expected_results': 'SUT booted Successfully'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a PciExpressCyclePcieDevicesThroughPowerStatesUsingDevconUtility object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PciExpressCyclePcieDevicesThroughPowerStatesUsingDevconUtility, self).__init__(test_log,
                                                                                             arguments, cfg_opts)

        #  Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)

        # Step logger start for Step 1
        self._test_content_logger.end_step_logger(1, True)

        # Copying and installing "DriverCycleWin.zip" to the SUT
        self._sut_path = self._install_collateral.install_driver_cycle()

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, True)

    def execute(self):
        """
        This method is to execute:
        1. Start the devcon test
        2. Check the SEL and the Windows System Log for errors.

        :return: True, if the test case is successful.
        :raise: None
        """

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        device_id_list = self._common_content_configuration.get_device_id_list()

        # Executing devcon test for number of cycles
        device_flag = True
        device_id_list = self._common_content_configuration.get_device_id_list()

        for each_cycle in range(0, int(self._no_of_cycle_for_devcon_utility_test)):
            for device_id in device_id_list:
                if not self._pcie_provider.get_device_details_by_device_id(device_id):
                    device_flag = False
                    self._log.info("Device with device id: '{}' is not available on SUT. So, Can not proceed testing "
                                   "for this device".format(device_id))
                else:
                    self._pcie_provider.set_kernel_driver(device_id, "enable")
                    self._pcie_provider.set_kernel_driver(device_id, "disable")
        if not device_flag:
            raise content_exceptions.TestFail("No PCIe device found to run devcon utility test")

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, True)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        # Checking for SEL and Windows System log
        mce_errors = self._common_content_lib.check_if_mce_errors()
        if mce_errors:
            raise content_exceptions.TestFail("MCE error was Captured in Log.")
        self._log.debug("No MCE error was Captured in Os Log")

        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, True)

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)

        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self.os.wait_for_os(self.reboot_timeout)

        # Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, True)

        return True


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if PciExpressCyclePcieDevicesThroughPowerStatesUsingDevconUtility.main() else
        Framework.TEST_RESULT_FAIL)
