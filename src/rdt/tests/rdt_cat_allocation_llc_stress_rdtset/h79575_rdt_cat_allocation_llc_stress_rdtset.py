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

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.lib.test_content_logger import TestContentLogger
from src.lib import content_base_test_case
from src.rdt.lib.rdt_utils import RdtUtils
from src.lib import content_exceptions
from src.lib.install_collateral import InstallCollateral


class RdtAllocationLlcStressRdtset(content_base_test_case.ContentBaseTestCase):
    """
    HPQC ID : H79575-PI_RDT_A_CATAllocation_LLC_stress_rdtset_L, H55281-PI_RDT_A_CATAllocation_LLC_stress_rdtset

    This test case aims to install RDT if it not installed and Check the RDT cache allocation functionality
    via rdtset command when stress tool is running.
    """

    TEST_CASE_ID = ["H79575", "PI_RDT_A_CATAllocation_LLC_stress_rdtset_L",
                    "H55281", "PI_RDT_A_CATAllocation_LLC_stress_rdtset"]
    CORE = "11"
    ALLOC_VAL = "0xf"
    RDT_MONITOR_CMD = "pqos -m 'all:{}' -t 10".format(CORE)
    PARAMETERS_LIST_CHECK = ["IPC", "MISSES", "LLC[KB]", "MBL[MB/s]"]
    RDTSET_CMD = 'rdtset -t "l3={};cpu={}" -c {} -k stress -m 10 -c 10'.format(ALLOC_VAL, CORE, CORE)
    STEP_DATA_DICT = {
        1: {'step_details': 'Verify if RDT is installed sut',
            'expected_results': 'Verified installation'},
        2: {'step_details': 'Restore RDT to default monitoring',
            'expected_results': 'Restore RDT to default monitoring is successful'},
        3: {'step_details': 'Turn on RDT monitoring for CPU core {}'.format(CORE),
            'expected_results': 'RDT monitoring is turned on successfully'},
        4: {'step_details': 'Set cache allocation with rdtset for core {}, and run stress on this core'.format(CORE),
            'expected_results': 'Setting Cache allocation is successful'},
        5: {'step_details': 'Turn on RDT monitoring for CPU core {} and compare results'.format(CORE),
            'expected_results': 'RDT monitoring is turned on and observed event values are increased after running '
                                'stress'},
        6: {'step_details': 'Check actual RDT setup',
            'expected_results': 'Configuration set with rdtset is displayed for core {}'
                                ' Expected value is {} for selected core'.format(CORE, ALLOC_VAL)},
        7: {'step_details': 'Terminate stress process then check actual RDT setup',
            'expected_results': 'CAT is return to default COS settings for core {}'
                                'Expected values is default COS value for selected core'.format(CORE)}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of RdtAllocationLlcStressRdtset

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(RdtAllocationLlcStressRdtset, self).__init__(test_log, arguments, cfg_opts)
        self._rdt = RdtUtils(self._log, self._common_content_lib, self._common_content_configuration, self.os, cfg_opts)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("RDT installation is not implemented for the os: {}".format(
                self.os.os_type))

    def prepare(self):  # type: () -> None
        """Test preparation/setup and install the stress tool to sut"""
        super(RdtAllocationLlcStressRdtset, self).prepare()
        self._install_collateral.install_stress_tool_to_sut()

    def check_configuration_set(self, expected_mask_val):
        """
        This method checks the Configuration set with rdtset, is displayed for the core
        and checks the expected value for selected core is matching.

        :param expected_mask_val: expected Mask values
        :raise: Content_exception if unable to get the regex pattern
        :return: None
        """
        core_regex = "Core {}.* => (COS\d+).*".format(self.CORE)
        self._log.info("Checking configuration changes which is done with rdtset")
        l3ca_cmd_result = self._common_content_lib.execute_sut_cmd(
            self._rdt.CHECK_L3CA_CMD, self._rdt.CHECK_L3CA_CMD, self._command_timeout)
        self._log.debug("Result of command {} is {}".format(self._rdt.CHECK_L3CA_CMD, l3ca_cmd_result))
        get_cos = re.search(core_regex, l3ca_cmd_result)
        if not get_cos:
            raise content_exceptions.TestFail("Unable to get the pattern".format(core_regex))
        self._log.debug("Core {} COS definition is {}".format(self.CORE, get_cos.group(1)))
        mask_pattern = ".*{} =>.*{}$".format(get_cos.group(1), expected_mask_val)
        mask_val = [i for i in l3ca_cmd_result.split("\n") if re.search(mask_pattern, i)]
        if not mask_val:
            raise content_exceptions.TestFail("Unable to get pattern {}".format(mask_val))
        self._log.info("All configuration changes which is done with rdtset is verified successfully and able to "
                       "find pattern {}".format(mask_val[0]))

    def execute_rdt_cat_allocation_llc_stress_rdtset(self):
        """
        This method executes the below:
        1. Verify if RDT is installed, If not it will install
        2. Restore default monitoring: pqos -R
        3. Turn on RDT monitoring for selected CPU core (11): 'pqos -m 'all:11' -t 10'
        4. Set cache allocation with rdtset for core 11, and  run stress on this core:
            rdtset -t 'l3=0xf;cpu=11' -c 11 -k stress -m 10 -c 10
        5. Turn on RDT monitoring and check that there is a significant increase of IPC, LLC MISSES, LLC and MBL
        6. Check actual RDT setup when stress is running
        7. Stops the Stress and checks the RDT setup returned to default COS

        """
        self._test_content_logger.start_step_logger(1)
        self._rdt.install_rdt()
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        self._rdt.restore_default_rdt_monitor()
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        without_stress_event_values = self._rdt.collect_rdt_monitored_events(pqos_cmd= self.RDT_MONITOR_CMD)
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        self._log.info("Setting cache allocation with rdtset for core {}, "
                       "and run stress on this core".format(self.CORE))
        self.os.execute_async(self.RDTSET_CMD)
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        with_stress_event_values = self._rdt.collect_rdt_monitored_events(pqos_cmd=self.RDT_MONITOR_CMD, stress=True)
        self._rdt.check_rdt_event_statistics_increased(without_stress_event_values, with_stress_event_values)
        self._test_content_logger.end_step_logger(5, return_val=True)

        self._test_content_logger.start_step_logger(6)
        self.check_configuration_set(self.ALLOC_VAL)
        self._test_content_logger.end_step_logger(6, return_val=True)

        self._test_content_logger.start_step_logger(7)
        if not self._rdt.is_stress_running():
            raise content_exceptions.TestFail("Stress Tool not running is system")
        self._rdt.stop_stress_tool()
        self.check_configuration_set(self._rdt.default_cos_val)
        self._test_content_logger.end_step_logger(7, return_val=True)

    def execute(self):
        """
        This method executes the test case with given number of iterations

        :return: True if test case pass
        """
        test_case_status = False
        for index in range(self._rdt.ITERATION):
            try:
                self._log.info("Iteration {}".format(index))
                self.execute_rdt_cat_allocation_llc_stress_rdtset()
                test_case_status = True
                break
            except Exception as e:
                self._log.error("Attempt number {} failed due to {}".format(index, e))
            finally:
                if self._rdt.is_stress_running():
                    self._rdt.stop_stress_tool()

        return test_case_status

    def cleanup(self, return_status):
        """Test Cleanup"""
        if self._rdt.is_stress_running():
            self._rdt.stop_stress_tool()
        super(RdtAllocationLlcStressRdtset, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RdtAllocationLlcStressRdtset.main() else Framework.TEST_RESULT_FAIL)
