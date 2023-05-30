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
    :TD Workload Base Test Case:

    Launch a given number of TD guests and run a specific workload or stress test suite on each TD guest for prescribed
    amount of time.
"""
import time
import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.security.tests.tdx.tdx_common_linux import LinuxTdxBaseTest


class TDGuestWorkloadBaseTest(LinuxTdxBaseTest):
    """
           This is a base test for workload testing with TD guests as part of the TDX feature.

           The following parameters in the content_configuration.xml file should be populated before running a test.

            Change <TDX><num_of_vms> to control the number of TD guests that will be run in parallel.
            Each test will have its own parameter to adjust for run time; this should be explained in the individual
            test case.

            :Scenario: Launch the number of TD guests prescribed, initiate the workload on each TD guest, run for the
            necessary time to complete the tests, then verify the SUT and the TD guests have not crashed.

            :Phoenix IDs:

            :Test steps:

                :1: Launch a TD guest.

                :2: On TD guest, launch a stress suite or workload.

                :3: Repeat steps 1 and 2 for the prescribed number of TD guests.

                :4: Run until workload tests complete.

            :Expected results: Each TD guest should boot and the workload suite should run to completion with no
            errors on the SUT or any of the TD guests.

            :Reported and fixed bugs:

            :Test functions:

        """

    def execute(self):
        run_exceptions = [self.tdx_consts.WorkloadToolNames.DISKSPD, self.tdx_consts.WorkloadToolNames.NTTTCP,
                          self.tdx_consts.WorkloadToolNames.STRESSNG]
        num_vms = int(self.tdx_properties[self.tdx_consts.NUMBER_OF_VMS])
        self._log.info(f"Creating and launching {num_vms} VMs.")
        for idx in range(0, num_vms):
            self._log.info(f"Starting TD guest {idx}.")
            self.launch_vm(key=idx, tdvm=True)
            self.set_yum_proxy_on_vm(key=idx)  # verify yum proxy exists on VM
            self.set_up_tool(idx=idx)
            self._log.info(f"Launching {self._tool_name} suite on VM {idx}.")
            log_file_name = f"{self._tool_sut_folder_path}tdvm-{self._tool_name}-{idx}.txt"
            if self._tool_name in run_exceptions:
                cmd = self._tool_run_cmd.format(self._tool_run_time) + log_file_name
            else:
                cmd = self._tool_sut_folder_path + "/" + self._tool_run_cmd.format(self._tool_run_time) + log_file_name
            self.ssh_to_vm(key=idx, cmd=cmd, async_cmd=True)
            self.check_process_running(key=idx, process_name=self._tool_name)
        self._log.info(f"Running {self._tool_name} suite on VMs for {self._tool_run_time} seconds...")
        time.sleep(self._tool_run_time)

        self._log.info("{} test is done.  Copying log files from VMs and shutting down VMs.".format(
            self._tool_name))
        for idx in range(0, num_vms):
            log_file_name = f"tdvm-{self._tool_name}-{idx}.txt"
            file_path_on_vm = self.find_file_on_vm(key=idx, file_name=log_file_name)
            self.copy_file_between_sut_and_vm(idx, file_path_on_vm, "/tdx/tdvm/logs/", to_vm=False)
            if not self.os.check_if_path_exists(f"/tdx/tdvm/logs/{log_file_name}"):
                raise content_exceptions.TestFail(f"Log file {log_file_name} could not be found on VM!  Double check "
                                                  f"there is space on the device!")
            self._log.debug("Removing log file from VM.")
            self.ssh_to_vm(key=idx, cmd=f"rm -f {file_path_on_vm}")
            if self.tdx_consts.WorkloadToolNames.DISKSPD == self._tool_name:
                self._log.debug(f"Cleaning up testfile from {self._tool_name} test.")
                self.ssh_to_vm(key=idx, cmd="rm -f testfile")
            self.teardown_vm(key=idx)

        return True

    def log_file_check(self, log_file_name: str, idx: int) -> None:
        """Sanity check log files by verifying file is not empty and no errors are found.

        :param log_file_name: name of the log file on the VM.
        :param idx: key identifier of the VM
        """
        file_size_check = self.execute_os_cmd(f"wc -l {log_file_name} | grep ^0")
        error_search = self.execute_os_cmd(f"grep -i error /tdx/tdvm/logs/{log_file_name}")
        self._log.debug(f"Sanity checking log file {log_file_name}")
        if file_size_check != "":
            raise content_exceptions.TestFail(f"Log file {log_file_name} is empty. It appears there was a problem "
                                              f"running {self._tool_name} on VM {idx}")
        self._log.debug("Log file is not empty.  Checking for error content")

        if error_search == "":
            self._log.debug(f"No errors found for VM {idx}.  Checking file is not empty.")
        else:
            self.workload_error_handler(error_search, log_file_name)

        self._log.info("All log sanity checks PASSED; check all log files in dtaf_log directory to "
                       "verify no extraneous results are found.")

    def workload_error_handler(self, error_search, log_file_name):
        """Call workload specific error handler here, otherwise just raise exception."""
        raise content_exceptions.TestFail(f"Error found in {self._tool_name} test log. Found "
                                          f"string: {error_search}")

    def set_up_tool(self, idx: int) -> None:
        """Set up workload tool on VM.
        :param idx: VM key identifier.
        :raise content_exceptions.TestFail: raised if VM image does not have enough disk space to install workload."""

        self._log.debug(f"Removing old workload install on VM {idx} at {self._tool_sut_folder_path}.")
        self.ssh_to_vm(key=idx, cmd=f"rm -rf {self._tool_sut_folder_path}")
        self._log.debug(f"Copying and building {self._tool_name} from SUT to VM {idx}.")
        self.copy_file_between_sut_and_vm(idx, self._tool_sut_folder_path, self._tool_sut_folder_path)
        pkg_install_command = f"yum -y install libaio-devel; yum -y groupinstall \'Development Tools\'; " \
                              f"cd {self._tool_sut_folder_path};"
        result = self.ssh_to_vm(key=idx, cmd=f"{pkg_install_command} {self._tool_build_cmd}")
        if "space" in result:
            raise content_exceptions.TestFail(f"VM does not have enough space to install {self._tool_name}")


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TDGuestWorkloadBaseTest.main() else Framework.TEST_RESULT_FAIL)
