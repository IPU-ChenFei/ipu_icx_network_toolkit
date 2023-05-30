#!/usr/bin/env python
###############################################################################
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
###############################################################################

import re
import sys

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger
from src.lib.dtaf_content_constants import TimeConstants
from src.lib.platform_config import PlatformConfiguration
from src.lib import content_exceptions
from src.provider.ptu_provider import PTUProvider
from src.provider.socwatch_provider import CoreCStates
from src.power_management.socwatch_common import SocWatchBaseTest


class PiPowermanagementCStateWithACPLinux(SocWatchBaseTest):
    """
    HPALM ID : H103084-PI_Powermanagement_C_State_With_ACP_L
    This function will install ptu and mlc checks the dimms temperatures
    """

    TEST_CASE_ID = ["H103084", "PI_Powermanagement_C_State_With_ACP_L"]
    SOCWATCH_RUN_TIME = TimeConstants.FIVE_MIN_IN_SEC
    SOCWATCH_PTU_RUN_TIME = TimeConstants.FIFTEEN_IN_SEC
    PTU_CMD = "./ptu -ct 3 -y -t {}".format(SOCWATCH_PTU_RUN_TIME)
    CC0_CC1_THRESHOLD_IDLE = CC6_THRESHOLD_STRESS = 15
    CC6_THRESHOLD_IDLE = CC0_CC1_THRESHOLD_STRESS = 85
    CC0_CC1_CONDITION_IDLE = "%s <" + str(CC0_CC1_THRESHOLD_IDLE)
    CC6_CONDITION_IDLE = "%s > " + str(CC6_THRESHOLD_IDLE)
    CC0_CC1_CONDITION_STRESS = "%s > " + str(CC0_CC1_THRESHOLD_STRESS)
    CC6_CONDITION_STRESS = "%s < " + str(CC6_THRESHOLD_STRESS)
    ACPI_EXPECTED_VALUE = 1
    step_data_dict = {1: {'step_details': 'To check ACPI enabled or not by using Python SV ',
                          'expected_results': 'ACPI Enabled in SUT ...'},
                      2: {'step_details': 'Keep the system idle for 5 minutes and run SOCWatch tool to check '
                                          'values for CC0+CC1 < 15 and CC6 > 85.',
                          'expected_results': 'Soc watch tool ran successfully and CC0+CC1 < 15% and CC6 > 85%'},
                      3: {'step_details': 'Install ptu tool and run monitor for 600s',
                          'expected_results': 'Ptu tool should run without any error'},
                      4: {'step_details': 'To verify CC0+CC1 > 85 and CC6 < 15',
                          'expected_results': 'Successfully verified CC0+CC1 > 85 and CC6 < 15'},
                      5: {'step_details': 'Keep the system idle for 5 minutes and run SOCWatch tool to check '
                                          'values for CC0+CC1 < 15 and CC6 > 85.',
                          'expected_results': 'Soc watch tool ran successfully and CC0+CC1 < 15% and CC6 > 85%'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of PiPowermanagementCStateWithACPLinux

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        super(PiPowermanagementCStateWithACPLinux, self).__init__(test_log, arguments, cfg_opts)

        if self.os.os_type != OperatingSystems.LINUX:
            raise NotImplementedError("Not implemented for {} OS".format(self.os.os_type))
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)
        self._ptu_provider = PTUProvider.factory(test_log, cfg_opts=cfg_opts, os_obj=self.os)
        self._silicon_family = self._common_content_lib.get_platform_family()

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(PiPowermanagementCStateWithACPLinux, self).prepare()

    def execute(self):
        """
        This function used to check ACPI enabled or not and to install ptu tool and Socwatch tool and CC0, CC1,
        CC6 values validation.

        :return: True if test completed successfully, False otherwise.
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        self.initialize_sv_objects()
        self.initialize_sdp_objects()
        self.SDP.itp.unlock()
        sockets_count = self.SV.get_socket_count()
        self._log.info("Socket count : {}".format(sockets_count))
        ltssm_obj = self.SV.get_ltssm_object()
        ltssm_obj.sls()
        acpi_list = list()
        for each_socket in range(0, sockets_count):
            acp_value = self.SV.get_by_path(
                scope=self.SV.UNCORE, reg_path=PlatformConfiguration.CHECK_ACPI_ENABLE[self._silicon_family],
                socket_index=each_socket)
            self._log.info("ACPI Values for Socket : {} are {}:".format(each_socket, acp_value))
            acpi_list.append(str(acp_value))

        acpi_hex_values = re.findall("0x.*", acpi_list[0])
        self._log.info("ACPI Core values in hexa decimal are : {}".format(acpi_hex_values))
        acpi_values = [int(i, 16) for i in acpi_hex_values]
        acpi_integer_values = list(map(int, acpi_values))
        self._log.info("ACPI Core values with integers are : {}".format(acpi_integer_values))
        if self.ACPI_EXPECTED_VALUE not in acpi_integer_values:
            raise content_exceptions.TestFail("ACPI not enabled because all cores has value 0...")
        self._log.info("ACPI Enabled ...")

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        self.execute_socwatch_tool(socwatch_runtime=self.SOCWATCH_RUN_TIME,
                                   system_idle_timeout=TimeConstants.FIVE_MIN_IN_SEC, execute_stress=False)

        # Verify CC0+CC1 package
        self._log.info("Verify Core C-State residency percentage CC0 and CC1 > {}".format(self.CC0_CC1_THRESHOLD_IDLE))
        self.csv_reader_obj.verify_core_c_state_residency(
            core_c_state=CoreCStates.CORE_C_STATE_CC0_CC1,
            condition=self.CC0_CC1_CONDITION_IDLE % CoreCStates.CORE_C_STATE_CC0_CC1, cc0_cc1_sum=True)

        # Verify CC6 package
        self._log.info("Verify Core C-State residency percentage CC6 > {}".format(self.CC6_THRESHOLD_IDLE))
        self.csv_reader_obj.verify_core_c_state_residency(CoreCStates.CORE_C_STATE_CC6,
                                                          self.CC6_CONDITION_IDLE % CoreCStates.CORE_C_STATE_CC6)

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)
        # Stress
        ptu_tool_path = self._ptu_provider.install_ptu()
        self._install_collateral.screen_package_installation()
        self._log.info("Executing the command : {}".format(self.PTU_CMD))
        self.os.execute_async(cmd=self.PTU_CMD, cwd=ptu_tool_path)
        self.execute_socwatch_tool(socwatch_runtime=self.SOCWATCH_PTU_RUN_TIME, execute_stress=False)
        self._ptu_provider.kill_ptu_tool()

        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)

        # Verify CC0+CC1 package
        self._log.info("Verify Core C-State residency percentage CC0 and CC1 > {} %".format(
            self.CC0_CC1_THRESHOLD_STRESS))
        self.csv_reader_obj.verify_core_c_state_residency(
            core_c_state=CoreCStates.CORE_C_STATE_CC0_CC1,
            condition=self.CC0_CC1_CONDITION_STRESS % CoreCStates.CORE_C_STATE_CC0_CC1, cc0_cc1_sum=True)

        # Verify CC6 package
        self._log.info("Verify Core C-State residency percentage CC6 < {} %".format(self.CC6_THRESHOLD_STRESS))
        self.csv_reader_obj.verify_core_c_state_residency(CoreCStates.CORE_C_STATE_CC6,
                                                          self.CC6_CONDITION_STRESS % CoreCStates.CORE_C_STATE_CC6)

        # Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=True)

        # Step logger start for Step 5
        self._test_content_logger.start_step_logger(5)

        # For Idle state
        self.execute_socwatch_tool(socwatch_runtime=self.SOCWATCH_RUN_TIME,
                                   system_idle_timeout=TimeConstants.TEN_MIN_IN_SEC, execute_stress=False)

        # Verify CC0+CC1 package
        self._log.info("Verify Core C-State residency percentage CC0 and CC1 > {}".format(self.CC0_CC1_THRESHOLD_IDLE))
        self.csv_reader_obj.verify_core_c_state_residency(
            core_c_state=CoreCStates.CORE_C_STATE_CC0_CC1,
            condition=self.CC0_CC1_CONDITION_IDLE % CoreCStates.CORE_C_STATE_CC0_CC1, cc0_cc1_sum=True)

        # Verify CC6 package
        self._log.info("Verify Core C-State residency percentage CC6 > {}".format(self.CC6_THRESHOLD_IDLE))
        self.csv_reader_obj.verify_core_c_state_residency(CoreCStates.CORE_C_STATE_CC6,
                                                          self.CC6_CONDITION_IDLE % CoreCStates.CORE_C_STATE_CC6)

        # Step logger end for Step 5
        self._test_content_logger.end_step_logger(5, return_val=True)

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PiPowermanagementCStateWithACPLinux, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiPowermanagementCStateWithACPLinux.main() else Framework.TEST_RESULT_FAIL)
