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
import re

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.test_content_logger import TestContentLogger
from src.security.tests.qat.qat_common import QatBaseTest
from src.provider.cpu_info_provider import CpuInfoProvider
from src.lib import content_exceptions


class QatPcieDeviceEnumeration(QatBaseTest):
    """
    HPQC ID : H79963
    This Test case verify QAT PCIe device enumeration in the SUT
    """
    TEST_CASE_ID = ["H79963"]
    LSPCI_COMMAND = "lspci -nd '8086:4940'"
    RE_EXP_FORMAT = ":[0-9][0-9]+.[0-9]\s0b40:[\s]8086:4940"
    NO_OF_DEVICES_PER_SOCKET = 4

    step_data_dict = {1: {'step_details': 'QAT Pcie device enumeration',
                          'expected_results': 'Verify Pcie devices'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of QatPcieDeviceEnumeration

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(QatPcieDeviceEnumeration, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._cpu_info_provider = CpuInfoProvider.factory(self._log, cfg_opts, self.os)  # type: CpuInfoProvider

    def prepare(self):
        # type: () -> None
        """
        Pre-checks if the test case is applicable for RHEL Linux OS.
        """
        super(QatPcieDeviceEnumeration, self).prepare()
        # Setting date and time
        self._common_content_lib.set_datetime_on_linux_sut()

    def execute(self):
        """
        This function check qat installation if not install the qat
        Collect available socket from the sut and execute lspci command to get pcie devices
        Verify pcie devices count.

        :return: True if pcie devices matches with the socket else false
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        # Check QAT is installed in the SUT if not install the QAT
        if not self.qat_device_status():
            self.install_qat_tool()
        # Get available sockets in the EGS SUTs
        self._cpu_info_provider.populate_cpu_info()
        socket_present_in_sut = int(self._cpu_info_provider.get_number_of_sockets())
        self._log.info("Available sockets in the sut: {}".format(socket_present_in_sut))
        ret_qat_devices = self._common_content_lib.execute_sut_cmd(self.LSPCI_COMMAND, "run lspci command to get "
                                                                                      "devices", self._command_timeout)
        self._log.info("lspci QAT pcie devices info {}".format(ret_qat_devices))
        ret_device_count = re.findall(self.RE_EXP_FORMAT, ret_qat_devices)
        self._log.info("device count {}".format(len(ret_device_count)))
        if not ret_device_count:
            raise content_exceptions.TestFail("Not found the QAT Pcie devices in the sut")
        if socket_present_in_sut * self.NO_OF_DEVICES_PER_SOCKET != len(ret_device_count):
            raise content_exceptions.TestFail("%s QAT Pcie devices are not matching with present sockets ",
                                              ret_device_count)
        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if QatPcieDeviceEnumeration.main() else Framework.TEST_RESULT_FAIL)
