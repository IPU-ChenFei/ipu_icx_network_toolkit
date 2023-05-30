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
    :NTttcp stress test on TD guest:

    Launch a given number of TD guests and run DiskSpd stress test suite on each TD guest for prescribed amount
    of time.
"""
import sys
import time

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.security.tests.tdx.tdx_common_linux import LinuxTdxBaseTest


class TDGuestNtttcp(LinuxTdxBaseTest):
    """
            This recipe tests TD guest boot and requires the use of a OS supporting TD guest.  The parameters of this
            test can be customized by the settings in the content_configuration.xml.

            Change <TDX><num_of_vms> to control the number of TD guests that will be run.

            Change <security><ntttcp><running_time> to adjust NTttcp run time; minimum enforced run time is 1 hr.

            :Scenario: Launch the number of TD guests prescribed, initiate Ntttcp on each TD guest, run for the
            necessary time to complete the tests, then verify the SUT and the TD guests have not crashed.  TD guests
            will be tested serially instead of in parallel because ntttcp only allows one client to connect to the
            server at a time.

            :Phoenix IDs:  18014073914

            :Test steps:

                :1: On TDX host, launch ntttcp receiver.

                :2: Launch a TD guest.

                :3: On TD guest, launch stress-ng CPU stress suite.

                :4: Run until ntttcp test completes on TD guest.

                :5: Repeat steps 1 through 4 for the prescribed number of TD guests.

            :Expected results: Each TD guest should boot and ntttcp test should run to completion with no
            errors on the SUT or any of the TD guests.

            :Reported and fixed bugs:

            :Test functions:

        """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new object for TDGuestNtttcp

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(TDGuestNtttcp, self).__init__(test_log, arguments, cfg_opts)
        self._tool_sut_folder_path = self.install_collateral.install_ntttcp().strip() + "/"
        self._tool_name = self.tdx_consts.WorkloadToolNames.NTTTCP
        self._tool_run_time = self._common_content_configuration.security_ntttcp_running_time()
        if self._tool_run_time < self.tdx_consts.TimeConstants.HOUR_IN_SECONDS:
            self._log.warning("Time set in config file is less than an hour; setting run time to an hour.")
            self._tool_run_time = self.tdx_consts.TimeConstants.HOUR_IN_SECONDS
        self._tool_run_cmd = self.tdx_consts.NTTTCP_CLIENT_CMD
        self._tool_build_cmd = "cd src; make && make install"

    def execute(self):
        sut_ip = self.os.execute("hostname -I", self.command_timeout).stdout.strip()
        self._tool_run_cmd = self._tool_run_cmd.format(sut_ip) + self.tdx_consts.NTTTCP_CLIENT_CMD_TIME
        num_vms = self.tdx_properties[self.tdx_consts.NUMBER_OF_VMS]
        self._log.info("Creating and launching {} VMs.".format(num_vms))

        try:
            for idx in range(0, num_vms):
                self.check_ntttcp_process()
                self._log.debug("Starting listening ntttcp connection on TDX host.")
                self.os.execute_async(self.tdx_consts.NTTTCP_SERVER_CMD)
                ntttcp_host_pid = self.os.execute("pgrep {}".format(self._tool_name),
                                                  self.command_timeout).stdout.strip()
                if ntttcp_host_pid == "":
                    raise RuntimeError("{} failed to run on TDX host.".format(self._tool_name))
                else:
                    self._log.debug("Current ntttcp pid is {}.".format(ntttcp_host_pid))
                self._log.debug("{} is listening on TDX host. PID: {}".format(self._tool_name, ntttcp_host_pid))
                self._log.info("Starting TD guest {}.".format(idx))
                self.launch_vm(key=idx, tdvm=True)
                self._log.debug("Attempting to execute SSH command to VM key {}.".format(idx))
                if not self.vm_is_alive(key=idx):
                    raise content_exceptions.TestFail("VM {} could not be reached after booting.".format(idx))
                self._log.debug("SSH was successful; VM {} is up.".format(idx))
                self.set_up_tool(idx=idx)
                self._log.info("Launching {} suite on VM {}.".format(self._tool_name, idx))
                log_file_name = "{}/tdvm-{}-{}.txt".format(self._tool_sut_folder_path, self._tool_name, idx)
                cmd = self._tool_run_cmd.format(self._tool_run_time) + log_file_name
                self._log.info("Running {} suite on VMs for {} seconds...".format(self._tool_name, self._tool_run_time))
                self.ssh_to_vm(key=idx, cmd=cmd, async_cmd=True)
                self.check_process_running(key=idx, process_name=self._tool_name)
                time.sleep(self._tool_run_time)
        finally:
            try:
                self.check_ntttcp_process()
            except content_exceptions.TestFail:
                self._log.warning("Caught error when waiting for ntttcp process to end on TDX host.")
                self._log.debug("Killing {} listening on TDX host.".format(self._tool_name))
                ntttcp_host_pid = self.os.execute("pgrep {}".format(self._tool_name),
                                                  self.command_timeout).stdout.strip()
                self.os.execute("kill {}".format(ntttcp_host_pid),
                                self.command_timeout)
                ntttcp_host_pid = self.os.execute("pgrep {}".format(self._tool_name),
                                                  self.command_timeout).stdout.strip()
                if ntttcp_host_pid != "":
                    self._log.error("Failed to kill ntttcp process on TDX host.  PID found: {}".format(ntttcp_host_pid))
        self._log.info("{} test is done.  Copying log files from VMs and doing basic error check.".format(
            self._tool_name))
        for idx in range(0, self.tdx_properties[self.tdx_consts.NUMBER_OF_VMS]):
            file_name = "tdvm-{}-{}.txt".format(self._tool_name, idx)
            log_file_name = self.find_file_on_vm(key=idx, file_name=file_name)
            self.copy_file_between_sut_and_vm(idx, log_file_name, "/tdx/tdvm/logs/", to_vm=False)
            file_size_check = self.execute_os_cmd("wc -l {} | grep ^0".format(log_file_name))
            error_search = self.execute_os_cmd("grep -i error /tdx/tdvm/logs/{}".format(file_name))
            self._log.debug("Sanity checking log file {}".format(log_file_name))
            if error_search != "":
                raise content_exceptions.TestFail("Error found in ntttcp test log. Found "
                                                  "string: {}".format(error_search))
            self._log.debug("No errors found.  Checking file is not empty.")
            if file_size_check != "":
                raise content_exceptions.TestFail("Log file {} is empty. It appears there was a problem running "
                                                  "ntttcp on VM {}".format(log_file_name, idx))
            self._log.debug("Log file is not empty.")
        self._log.info("All log sanity checks PASSED; check all ntttcp log files in dtaf_log directory to "
                       "verify no extraneous results are found.")
        return True

    def cleanup(self, return_status):
        self._log.info("Shutting down VMs.")
        self.kill_all_running_vms()
        super(TDGuestNtttcp, self).cleanup(return_status)

    def check_ntttcp_process(self):
        timer = 0
        sleep_interval = 5.0
        ntttcp_host_pid = self.os.execute("pgrep {}".format(self._tool_name),
                                          self.command_timeout).stdout.strip()
        while ntttcp_host_pid != "":
            self._log.debug("{} is still running on host, waiting for process to "
                            "finish...".format(self._tool_name))
            ntttcp_host_pid = self.os.execute("pgrep {}".format(self._tool_name),
                                              self.command_timeout).stdout.strip()
            time.sleep(sleep_interval)
            timer = sleep_interval + timer
            if timer > self.command_timeout:
                raise content_exceptions.TestFail("{} process has not ended on TDX host in timeout period.  "
                                                  "Process might be stuck or process never ran on TD "
                                                  "guest.".format(self._tool_name))

    def set_up_tool(self, idx):
        self._log.debug("Copying and building {} from SUT to VM {}.".format(self._tool_name, idx))
        self.copy_file_between_sut_and_vm(idx, self._tool_sut_folder_path, self._tool_sut_folder_path)
        pkg_install_command = "yum -y install libaio-devel; yum -y groupinstall \'Development Tools\'; cd {};".format(
            self._tool_sut_folder_path)
        result = self.ssh_to_vm(key=idx, cmd="{} {}".format(pkg_install_command, self._tool_build_cmd))
        if "error" in result:
            raise content_exceptions.TestFail("Failed to install ntttcp on VM {}.  Error message: {}".format(idx,
                                                                                                             result))


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TDGuestNtttcp.main() else Framework.TEST_RESULT_FAIL)
