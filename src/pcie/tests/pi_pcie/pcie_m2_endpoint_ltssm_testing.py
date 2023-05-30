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
from src.lib.dtaf_content_constants import LinuxCyclingToolConstant, IntelPcieDeviceId
from src.lib import content_exceptions


class PcieEndPointM2LtssmTesting(PcieCommon):
    """
    HPQALM ID : H89962-PI_PCH_M.2_Slot_LTSSM_Endpoint_Testing_L

    The purpose of this Test Case is to verify the functionality of all supported pcie link state transition
    for a specific adapter in all slot of the system.
    """
    TEST_CASE_ID = ["PI_PCH_M.2_Slot_LTSSM_Endpoint_Testing_L"]

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
        Creates a PcieEndPointM2LtssmTesting object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PcieEndPointM2LtssmTesting, self).__init__(test_log, arguments, cfg_opts)
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

        # getting the device id of PCIe card
        nvme_device_id = IntelPcieDeviceId.PCIE_NVME_M2_DEVICE_ID[eval("self._product_family")]

        # getting the details of device id to check, it is available or not
        if not self._pcie_provider.get_device_details_by_device_id(nvme_device_id):
            self._log.debug("Device with device id: '{}' is not available on SUT. So, Can not proceed testing for "
                            "this device".format(nvme_device_id))
            raise content_exceptions.TestFail("NVMe device is not detected")
        else:
            self._test_content_logger.start_step_logger(1)
            # Validating the link speed and width
            self._pcie_util_obj.validate_installed_pcie_link_width_speed(nvme_device_id)
            self._test_content_logger.end_step_logger(1, True)

            self._test_content_logger.start_step_logger(2)
            self._log.debug("Testing for the device id: '{}' is in progress".format(nvme_device_id))
            for each_test in self.LTSSM_TEST_NAME_LIST:
                # calling method to validate each testing one by one.
                self._pcie_ltssm_provider.run_ltssm_tool(test_name=each_test, device_id=nvme_device_id
                                                         , cmd_path=self._sut_path)
            self._test_content_logger.end_step_logger(2, True)
        self._test_content_logger.start_step_logger(3)
        # Checking MCE Error after Testing
        mce_error = self._common_content_lib.check_if_mce_errors()
        if mce_error:
            raise content_exceptions.TestFail("MCE error was Captured in Log.")
        self._log.debug("No MCE error was Captured in Os Log")
        self._test_content_logger.end_step_logger(3, True)
        self._test_content_logger.start_step_logger(4)
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self.os.wait_for_os(self.reboot_timeout)
        self._test_content_logger.end_step_logger(4, True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieEndPointM2LtssmTesting.main() else Framework.TEST_RESULT_FAIL)
