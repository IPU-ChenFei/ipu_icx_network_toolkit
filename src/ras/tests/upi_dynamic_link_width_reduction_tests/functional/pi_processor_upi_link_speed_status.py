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

from src.ras.tests.upi_dynamic_link_width_reduction_tests.upi_lane_failover_common import UpiLaneFailoverCommon


class VerifyUpiLinkSpeedStatus(UpiLaneFailoverCommon):
    """
    Testcase_id : H72507, H79581 (Linux) and H81722 (Windows)

    verify if UPI link speed is normal and same before and after executing stress tool.
    """

    STRESS_TIME = 20
    MINUTE = 60
    STRESS_COMMAND_DICT = {"prime95": "prime95.exe -t", "mprime": "./mprime -t"}
    TEST_CASE_ID = ["H72507 - PI_Processor_UPI_LinkSpeed_Status_L",
                    "H79581 - PI_Processor_UPI_LinkSpeed_Status_L",
                    "H81722 - PI_Processor_UPI_LinkSpeed_Status_W"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new VerifyUpiLinkSpeedStatus object

        :param test_log: Used for debug and info messages
        :param arguments: None
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(VerifyUpiLinkSpeedStatus, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        1. Copy mcelog.conf file to sut and reboot
        2. Clear All Os Logs before Starting the Test Case
        3. Set the bios knobs to its default mode.
        4. Set the bios knobs as per the test case.
        5. Reboot the SUT to apply the new bios settings.
        6. Verify the bios knobs whether they updated properly.

        :return: None
        """
        super(VerifyUpiLinkSpeedStatus, self).prepare()

    def execute(self):
        """
        This Method is Used to Verify Initial Upi Link Speed and execute one stress tool (Prime95) and check the Link
        Speed again and verify whether Link Speed is Downgraded after executing Stress Tool.

        :return: True or False based on the Output of inject_and_check_upi_link_width_change_failure
        """
        self.verify_upi_link_speed()
        command_result = self.os.execute("screen --version", self._command_timeout).stdout
        if "Screen version" not in command_result:
            self._install_collateral.screen_package_installation()

        self._log.info("Installing the stress test")
        stress_app_path, stress_tool_name = self._install_collateral.install_prime95(app_details=True)
        self._log.info("installed stress application")
        self._stress_provider.execute_async_stress_tool(self.STRESS_COMMAND_DICT[stress_tool_name], stress_tool_name,
                                                        stress_app_path)
        self._log.info("Stress test process has successfully started..")

        return self.verify_upi_link_speed(is_stress_tool_executed=True)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VerifyUpiLinkSpeedStatus.main() else Framework.TEST_RESULT_FAIL)
