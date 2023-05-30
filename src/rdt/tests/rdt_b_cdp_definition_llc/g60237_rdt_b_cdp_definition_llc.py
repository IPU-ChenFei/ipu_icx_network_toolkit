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

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger
from src.lib import content_base_test_case
from src.provider.cpu_info_provider import CpuInfoProvider
from src.rdt.lib.rdt_utils import RdtUtils

from src.lib import content_exceptions


class RdtCDPDefinitionLlc(content_base_test_case.ContentBaseTestCase):
    """
    Glasgow ID : G60237.0-PI_RDT_B_CDPDefinition_LLC

    This test case aims to install RDT if it not installed and
    verify L3 CAT Set COS definition command/task and verify the cache allocation
    via rdtset tool when memtester is running

    """
    TEST_CASE_ID = ["G60237.0-PI_RDT_B_CDPDefinition_LLC"]
    COS_ARG_VALUE2 = "2"
    COS_ARG_VALUE3 = "3d"
    COS_VALUE3 = "3"
    COS_ARG_VALUE4 = "4c"
    COS_VALUE4 = "4"
    DATA_CODE_VALUE1 = "0xe"
    DATA_CODE_VALUE2 = "0xf"
    CDP_OFF = "off"
    L3_CDP_ENABLE = "pqos -R l3cdp-{} -v"
    L3_CDP_DISABLE = "pqos -R l3cdp-{} -v"
    L3_CAT_COS_CMD  = "pqos -e llc:{}={}"
    CHECK_L3_CAT_COS_DEFINITION_FOR_DATA_CODE = "L3CA COS{} => DATA {},CODE {}"
    CHECK_L3_CAT_COS_DEFINITION_FOR_CODE_ONLY = "L3CA COS{} => DATA \S+,CODE {}"
    CHECK_L3_CAT_COS_DEFINITION_FOR_DATA_ONLY = "L3CA COS{} => DATA {},CODE \S+"
    MIN_SOCKET = 2
    STEP_DATA_DICT = {
        1: {'step_details': 'Verify RDT is installed in sut',
            'expected_results': 'Installation od RDT is verified successfully'},
        2: {'step_details': 'Restore default monitoring',
            'expected_results': 'Restore to default monitoring is successful'},
        3: {'step_details': 'Verify L3 CDP capability is detected on platform',
            'expected_results': 'Successfully Verified L3 CDP capability is detected on platform '},
        4: {'step_details': 'Verify L3 CDP can be enabled on platform by running "pqos -R l3cdp-on -v" to enable L3 CDP',
            'expected_results': 'Sucessfully executed the command'},
        5: {'step_details': 'Verify that CDP was enabled with "pqos -s -V"',
            'expected_results': 'verified that CDP is enabled Successfully'},
        6: {'step_details': 'Verify L3 CDP can be disabled on platform by running "pqos -R l3cdp-off -v" to disable L3 CDP',
            'expected_results': 'Sucessfully executed the command'},
        7: {'step_details': 'Verify that CDP was disabled with "pqos -s -V"',
            'expected_results': 'verified that CDP is Disabled Successfully'},
        8: {'step_details': 'Verify L3 CAT COS definition can be set for Code and Data',
            'expected_results': 'L3 CAT COS definition set for Code and Data successfully'},
        9: {'step_details': 'Verify L3 CAT COS definition can be set for Code only',
            'expected_results': 'Verified that L3 CAT COS definition can be set for Data only'},
        10: {'step_details': 'Verify L3 CAT COS definition can be set for Data only',
             'expected_results': 'Verified that L3 CAT COS definition can be set for Data only '},
        11: {'step_details': 'Restore default monitoring',
             'expected_results': 'Restore to default monitoring is successful'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of RdtCDPDefinitionLlc

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(RdtCDPDefinitionLlc, self).__init__(test_log, arguments, cfg_opts)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._rdt = RdtUtils(self._log, self._common_content_lib, self._common_content_configuration, self.os, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("RDT installation is not implemented for the os: {}".format(
                self.os.os_type))
        self._cpu_info_provider = CpuInfoProvider.factory(self._log, cfg_opts, self.os)  # type: CpuInfoProvider
        self._cpu_info_provider.populate_cpu_info()
        self._num_sockets = int(self._cpu_info_provider.get_number_of_sockets())

    def prepare(self):  # type: () -> None
        """Test preparation/setup and install the stress tool to sut"""
        super(RdtCDPDefinitionLlc, self).prepare()

    def execute(self):
        """
        This method executes the below:
        1. Verify if RDT is installed, If not it will install
        2. Restore default monitoring: pqos -R
        3. Verify L3 CDP capability is detected on platform .
        4. Verify L3 CDP can be enabled on platform by running "pqos -R l3cdp-on -v" to enable L3 CDP
        5. Verify that CDP was enabled with "pqos -s -V"
        6. Verify L3 CDP can be disabled on platform by running "pqos -R l3cdp-off -v" to enable L3 CDP
        7. Verify that CDP was enabled with "pqos -s -V"
        8. Verify L3 CAT COS definition can be set for Code and Data
        9. Verify L3 CAT COS definition can be set for Code only
        10. Verify L3 CAT COS definition can be set for Dta only
        11. Restore default allocation:  pqos -R

        :return: True if test case pass
        """
        self._test_content_logger.start_step_logger(1)
        self._rdt.install_rdt()
        self._test_content_logger.end_step_logger(1, return_val=True)

        # Restore rdt monitor to default mode
        self._test_content_logger.start_step_logger(2)
        self._rdt.restore_default_rdt_monitor()
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Verify L3 CDP capability is detected on platform .
        self._test_content_logger.start_step_logger(3)
        self._rdt.verify_l3ca_capability(cdp_check=True)
        self._test_content_logger.end_step_logger(3, return_val=True)

        # Verify L3 CDP can be enabled on platform by running "pqos -R l3cdp-on -v" to enable L3 CDP
        self._test_content_logger.start_step_logger(4)
        self._rdt.set_platform_l3cdp()
        self._test_content_logger.end_step_logger(4, return_val=True)

        # Verify that CDP was enabled with "pqos -s -V"
        self._test_content_logger.start_step_logger(5)
        self._rdt.verify_l3ca_capability(cdp=self._rdt.CDP_ENABLED)
        self._test_content_logger.end_step_logger(5, return_val=True)

        # Verify L3 CDP can be disabled on platform by running "pqos -R l3cdp-off -v" to disable L3 CDP
        self._test_content_logger.start_step_logger(6)
        self._rdt.set_platform_l3cdp(enable=False)
        self._test_content_logger.end_step_logger(6, return_val=True)

        # Verify that CDP was disabled with "pqos -s -V"
        self._test_content_logger.start_step_logger(7)
        self._rdt.verify_l3ca_capability(cdp=self._rdt.CDP_DISABLED)
        self._test_content_logger.end_step_logger(7, return_val=True)

        # Verify L3 CAT COS definition can be set for Code and Data
        self._test_content_logger.start_step_logger(8)
        self._rdt.set_platform_l3cdp()
        l3_cdp_cmd = self.L3_CAT_COS_CMD.format(self.COS_ARG_VALUE2, self.DATA_CODE_VALUE1)
        expected_result = self.CHECK_L3_CAT_COS_DEFINITION_FOR_DATA_CODE.format(self.COS_ARG_VALUE2,
                                                                                self.DATA_CODE_VALUE1,
                                                                                self.DATA_CODE_VALUE1)
        self._rdt.verify_l3ca_cat_cos_definitions(l3_cdp_cmd, expected_result, self._num_sockets)
        self._test_content_logger.end_step_logger(8, return_val=True)

        # Verify L3 CAT COS definition can be set for Code only
        self._test_content_logger.start_step_logger(9)
        self._rdt.set_platform_l3cdp()
        l3_cdp_cmd = self.L3_CAT_COS_CMD.format(self.COS_ARG_VALUE4, self.DATA_CODE_VALUE2)
        expected_result = self.CHECK_L3_CAT_COS_DEFINITION_FOR_CODE_ONLY.format(self.COS_VALUE4,
                                                                                self.DATA_CODE_VALUE2)
        self._rdt.verify_l3ca_cat_cos_definitions(l3_cdp_cmd, expected_result, self._num_sockets)
        self._test_content_logger.end_step_logger(9, return_val=True)

        # Verify L3 CAT COS definition can be set for Data only
        self._test_content_logger.start_step_logger(10)
        self._rdt.set_platform_l3cdp()
        l3_cdp_cmd = self.L3_CAT_COS_CMD.format(self.COS_ARG_VALUE3, self.DATA_CODE_VALUE2)
        expected_result = self.CHECK_L3_CAT_COS_DEFINITION_FOR_DATA_ONLY.format(self.COS_VALUE3,
                                                                                self.DATA_CODE_VALUE2)
        self._rdt.verify_l3ca_cat_cos_definitions(l3_cdp_cmd, expected_result, self._num_sockets)
        self._test_content_logger.end_step_logger(10, return_val=True)

        # Restore rdt monitor to default mode
        self._test_content_logger.start_step_logger(11)
        self._rdt.restore_default_rdt_monitor()
        self._test_content_logger.end_step_logger(11, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RdtCDPDefinitionLlc.main() else Framework.TEST_RESULT_FAIL)
