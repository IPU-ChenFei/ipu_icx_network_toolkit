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
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.test_content_logger import TestContentLogger
from src.lib import content_exceptions


class PiRSTeVMDDriverInstallationCheckL(ContentBaseTestCase):
    """
    HPQC : 80276-PI_PCIeSSD - RSTe VMD Driver Installation Check_L
    This test case functionality is to Check if the RSTe VMD driver is preinstalled along with Linux OS
    """
    TEST_CASE_ID = ["H80276", "PI_PCIeSSD - RSTe VMD Driver Installation Check_L"]

    step_data_dict = {1: {'step_details': 'Check if the RSTe VMD driver is preinstalled along with Linux OS.',
                          'expected_results': 'RSTe driver should be present'}}
    LEDMON = "ledmon"
    MDADM = "mdadm"
    RPM_LEDMON_CMD = "rpm -qa | grep {}".format(LEDMON)
    RPM_MDADM_CMD = "rpm -qa | grep {}".format(MDADM)

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new PiRSTeVMDDriverInstallationCheckL object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PiRSTeVMDDriverInstallationCheckL, self).__init__(test_log, arguments, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise NotImplementedError("This Test is Supported only on Linux")
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        :return None
        """
        super(PiRSTeVMDDriverInstallationCheckL, self).prepare()

    def execute(self):
        """
        Check if the RSTe VMD driver is preinstalled along with Linux OS

        :return: True
        :raise: If driver verification failed raise content_exceptions.TestFail
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        self._log.info("Executing {} command".format(self.RPM_LEDMON_CMD))
        ledmon_output = self._common_content_lib.execute_sut_cmd(self.RPM_LEDMON_CMD, self.RPM_LEDMON_CMD,
                                                                 self._command_timeout)
        self._log.debug("{} Command output:{}".format(self.RPM_LEDMON_CMD, ledmon_output))
        if self.LEDMON not in ledmon_output:
            raise content_exceptions.TestFail("Failed to verify {} command".format(self.RPM_LEDMON_CMD))

        self._log.info("Executing {} command".format(self.RPM_MDADM_CMD))
        mdadm_output = self._common_content_lib.execute_sut_cmd(self.RPM_MDADM_CMD, self.RPM_MDADM_CMD,
                                                                self._command_timeout)
        self._log.debug("{} Command output:{}".format(self.RPM_MDADM_CMD, mdadm_output))
        if self.MDADM not in mdadm_output:
            raise content_exceptions.TestFail("Failed to verify {} command".format(self.RPM_MDADM_CMD))
        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""

        super(PiRSTeVMDDriverInstallationCheckL, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiRSTeVMDDriverInstallationCheckL.main() else Framework.TEST_RESULT_FAIL)
