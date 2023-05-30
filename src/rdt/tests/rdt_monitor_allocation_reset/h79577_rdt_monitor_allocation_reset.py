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

from src.power_management.lib.reset_base_test import ResetBaseTest
from src.lib import content_base_test_case
from src.rdt.lib.rdt_utils import RdtUtils
from src.lib import content_exceptions


class RdtMonitorAllocationReset(content_base_test_case.ContentBaseTestCase):
    """
    HPQC ID : H79577-PI_RDT_A_Monitor_Allocation_reset_L, H55148-PI_RDT_A_Monitor&Allocation_reset

    This test case aims to install RDT if it not installed and Check possibility of associating
    classes to cores via pqos -a.
    """
    TEST_CASE_ID = ["H79577", "PI_RDT_A_Monitor_Allocation_reset_L", "H55148", "PI_RDT_A_Monitor&Allocation_reset"]
    VAL_OF_CORE = "3"
    CORE = "Core {}".format(VAL_OF_CORE)
    DEFAULT_COS_VAL = "COS0"
    ALLOCATED_COS_VAL = "COS1"
    ALLOCATE_L3CACHE_TO_CORE_CMD = "pqos -a 'llc:1={}'".format(VAL_OF_CORE)

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of RdtMonitorAllocationReset

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(RdtMonitorAllocationReset, self).__init__(test_log, arguments, cfg_opts)
        self._reset_obj = ResetBaseTest(test_log, arguments, cfg_opts)
        self._rdt = RdtUtils(self._log, self._common_content_lib, self._common_content_configuration, self.os, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("RDT installation is not implemented for the os: {}".format(
                self.os.os_type))

    def prepare(self):
        # type: () -> None
        """Test preparation/setup """
        if not self.os.is_alive():
            self._log.error("System is not alive")
            self.perform_graceful_g3()  # To make the system alive

    def alter_and_verify_core_allocation(self):
        """
        This method Check actual L3CA COS definitions, Allocate L3 cache memory for particular core
        and again Check L3CA COS definitions is changed accordingly.

        :raise: Content_exception if unable to allocate L3 cache to core
        """
        # Check actual L3CA COS definitions and core information: pqos -s
        self._rdt.check_l3ca_core_definitions(self._rdt.CHECK_L3CA_CMD, self.CORE, self.DEFAULT_COS_VAL)
        # Allocate L3 cache memory for core 3 to COS1: pqos -a 'llc:1=3'
        self._log.info("Allocating L3 cache memory for '{}' to '{}'".format(self.CORE, self.ALLOCATED_COS_VAL))
        unmatched_value = self._common_content_lib.execute_cmd_and_get_unmatched_result(
            self.ALLOCATE_L3CACHE_TO_CORE_CMD, self._rdt.ALLOCATE_L3CACHE_INFO, self._rdt.ALLOCATION_SUCCESSFUL_INFO,
            self._command_timeout)
        if unmatched_value:
            raise content_exceptions.TestFail("{} did not find in the {} output".
                                              format(unmatched_value, self.ALLOCATE_L3CACHE_TO_CORE_CMD))
        # Check L3CA COS definitions after changes: pqos -s
        self._rdt.check_l3ca_core_definitions(self._rdt.CHECK_L3CA_CMD, self.CORE, self.ALLOCATED_COS_VAL)

    def execute(self):
        """
        This method executes the below:
        1. Verify if RDT is installed, If not it will install
        2. Restore default monitoring: pqos -R
        3. Turn on RDT monitoring to view the core status: 'pqos -m 'all:0,1,2,3' -t 10'
        4. Check actual L3CA COS definitions and core information: pqos -s
        5. Allocate L3 cache memory for core 3 to COS1: pqos -a 'llc:1=3'
        6. Check L3CA COS definitions after changes: pqos -s
        7. Reboot the platform
        8. Check L3CA COS definitions after changes: pqos -s
        9. Turn on RDT monitoring to view the core status: 'pqos -m 'all:0,1,2,3' -t 10'
        10. Repeat step 4-7
        11. Shutdown and perform dc reset
        12. Check L3CA COS definitions after changes: pqos -s
        13. Turn on RDT monitoring to view the core status: 'pqos -m 'all:0,1,2,3' -t 10'
        14. Repeat step 4-7
        15. Shutdown and perform ac reset
        16. Check L3CA COS definitions after changes: pqos -s
        17. Turn on RDT monitoring to view the core status: 'pqos -m 'all:0,1,2,3' -t 10'

        :return: True if test case pass
        """
        # Verify if RDT is installed, If not it will install
        self._rdt.install_rdt()
        # Restore default monitoring: pqos -R
        self._rdt.restore_default_rdt_monitor()
        # Turn on RDT monitoring to view the core status: 'pqos -m 'all:0,1,2,3' -t 10'
        self._rdt.turn_on_rdt_monitoring()
        # Alter and verify core allocation
        self.alter_and_verify_core_allocation()
        self._log.info("Performing reboot")
        self._reset_obj.warm_reset()
        # Check L3CA COS definitions: pqos -s
        self._rdt.check_l3ca_core_definitions(self._rdt.CHECK_L3CA_CMD, self.CORE, self.DEFAULT_COS_VAL)
        # Turn on RDT monitoring to view the core status: 'pqos -m 'all:0,1,2,3' -t 10'
        self._rdt.turn_on_rdt_monitoring()
        # Alter and verify core allocation
        self.alter_and_verify_core_allocation()
        self._log.info("Performing shutdown and DC power reset")
        if self._reset_obj.graceful_s5() != 0:
            raise content_exceptions.TestFail("Failed in performing graceful in s5 state")
        # Check L3CA COS definitions: pqos -s
        self._rdt.check_l3ca_core_definitions(self._rdt.CHECK_L3CA_CMD, self.CORE, self.DEFAULT_COS_VAL)
        # Turn on RDT monitoring to view the core status: 'pqos -m 'all:0,1,2,3' -t 10'
        self._rdt.turn_on_rdt_monitoring()
        # Alter and verify core allocation
        self.alter_and_verify_core_allocation()
        self._log.info("Performing shutdown and AC power reset")
        self.perform_graceful_g3()
        # Check L3CA COS definitions: pqos -s
        self._rdt.check_l3ca_core_definitions(self._rdt.CHECK_L3CA_CMD, self.CORE, self.DEFAULT_COS_VAL)
        # Turn on RDT monitoring to view the core status: 'pqos -m 'all:0,1,2,3' -t 10'
        self._rdt.turn_on_rdt_monitoring()

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RdtMonitorAllocationReset.main() else Framework.TEST_RESULT_FAIL)
