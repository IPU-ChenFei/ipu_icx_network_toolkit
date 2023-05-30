#!/usr/bin/env python
##########################################################################
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
##########################################################################
"""
    :Stress-ng memory stress test on TD guest:

    Launch a given number of TD guests and run stress-ng memory stress test suite on each TD guest for prescribed amount
    of time.
"""
import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.security.tests.tdx.workloads.tdvm_workload_base_test import TDGuestWorkloadBaseTest


class TDGuestStressngMemory(TDGuestWorkloadBaseTest):
    """
            This recipe tests TD guest boot and requires the use of a OS supporting TD guest.  The parameters of this
            test can be customized by the settings in the content_configuration.xml.

            Change <TDX><num_of_vms> to control the number of TD guests that will be run in parallel.

            Change <security><stressng><running_time> to adjust stress-ng run time; minimum enforced run time is 1 hr.

            :Scenario: Launch the number of TD guests prescribed and, initiate stress-ng memory test suite on each TD
            guest, run for the necessary time to complete the tests, then verify the SUT and the TD guests
            have not crashed.

            :Phoenix IDs:  18014072035

            :Test steps:

                :1: Launch a TD guest.

                :2: On TD guest, launch stress-ng memory stress suite.

                :3: Repeat steps 1 and 2 for the prescribed number of TD guests.

                :4: Run until stress-ng memory suite tests complete.

            :Expected results: Each TD guest should boot and stress-ng memory suite should run to completion with no
            errors on the SUT or any of the TD guests.

            :Reported and fixed bugs:

            :Test functions:

        """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new object for StressWithPrime95AndFio

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(TDGuestStressngMemory, self).__init__(test_log, arguments, cfg_opts)
        self._tool_name = self.tdx_consts.WorkloadToolNames.STRESSNG
        self._tool_sut_folder_path = ""
        self.install_collateral.yum_install(self._tool_name)
        self._tool_run_time = self._common_content_configuration.security_stressng_running_time()
        if self._tool_run_time < self.tdx_consts.TimeConstants.HOUR_IN_SECONDS:
            self._log.warning("Time set in config file is less than an hour; setting run time to an hour.")
            self._tool_run_time = self.tdx_consts.TimeConstants.HOUR_IN_SECONDS
        self._tool_run_cmd = self.tdx_consts.STRESSNG_MEMORY_CMD.format(self._tool_run_time)

    def execute(self):
        return super(TDGuestStressngMemory, self).execute()

    def set_up_tool(self, idx: int) -> None:
        """Set up stress-ng tool on VM.
        :param idx: VM key identifier.
        :raise content_exceptions.TestFail: raised if VM image does not have enough disk space to install workload."""
        self._log.debug(f"Copying and building {self._tool_name} from SUT to VM {idx}.")
        pkg_install_command = "yum -y install libatomic stress-ng"
        result = self.ssh_to_vm(key=idx, cmd=f"{pkg_install_command}")
        if "error" in result:
            raise content_exceptions.TestFail(f"Failed to install stress-ng on VM {idx}.  Error message: {result}")

    def workload_error_handler(self, error_search: str, log_file_name: str) -> None:
        """Workload specific error checking.
        :param error_search: error string found by top level script check.
        :param log_file_name: path to workload log file
        :raise content_exceptions.TestFail: raised if expected success strings are not found in log file."""
        if "out of resources" in error_search:
            self._log.debug("stress-ng ran out of system resources when running test.  As long as the VM did not crash, "
                            "this should be OK.")
        raise_exception = False
        for message in self.tdx_consts.STRESSNG_COMPLETED_SUCCESSFULLY:
            success_string = self.execute_os_cmd(f"grep {message} {log_file_name}")
            if success_string == "":
                self._log.error(f"Missing success string \"{message}\" in stress-ng log file.")
                raise_exception = True
        if raise_exception:
            raise content_exceptions.TestFail("Some checks failed for test log verification.  Please check test log for "
                                              "details.")


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TDGuestStressngMemory.main() else Framework.TEST_RESULT_FAIL)
