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
    :iperf stress test on TD guest:

    Launch a given number of TD guests and run iperf stress test suite on each TD guest for prescribed amount
    of time.
"""
import sys
import time

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.security.tests.tdx.tdx_common_linux import LinuxTdxBaseTest


class TDGuestIperf(LinuxTdxBaseTest):
    """
            This recipe tests TD guest boot and requires the use of a OS supporting TD guest.  The parameters of this
            test can be customized by the settings in the content_configuration.xml.

            Change <TDX><num_of_vms> to control the number of TD guests that will be run.

            Change <security><iperf><running_time> to adjust iPerf run time; minimum enforced run time is 1 hr.

            :Scenario: Launch the number of TD guests prescribed, initiate iperf on each TD guest, run for the
            necessary time to complete the tests, then verify the SUT and the TD guests have not crashed.  TD guests
            will be tested serially instead of in parallel because iperf only allows one client to connect to the server
            at a time.

            :Phoenix IDs:  18014074829

            :Test steps:

                :1: Launch a TD guest.

                :2: On TD guest, launch iperf stress suite.

                :3: Repeat steps 1 and 2 for the prescribed number of TD guests.

                :4: Run until iperf suite tests complete.

            :Expected results: Each TD guest should boot and iperf suite should run to completion with no
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
        super(TDGuestIperf, self).__init__(test_log, arguments, cfg_opts)
        self.install_collateral.install_iperf()
        self._tool_name = self.tdx_consts.WorkloadToolNames.IPERF
        self._tool_run_time = self._common_content_configuration.security_iperf_running_time()
        if self._tool_run_time < self.tdx_consts.TimeConstants.HOUR_IN_SECONDS:
            self._log.warning("Time set in config file is less than an hour; setting run time to an hour.")
            self._tool_run_time = self.tdx_consts.TimeConstants.HOUR_IN_SECONDS
        self._tool_run_cmd = self.tdx_consts.IPERF_CLIENT_CMD

    def execute(self):
        sut_ip = self.os.execute("hostname -I", self.command_timeout).stdout.strip()
        self._tool_run_cmd = self._tool_run_cmd.format(sut_ip) + self.tdx_consts.IPERF_CLIENT_CMD_TIME
        num_vms = self.tdx_properties[self.tdx_consts.NUMBER_OF_VMS]
        self._log.info("Creating and launching {} VMs.".format(num_vms))

        try:
            self.os.execute_async(self.tdx_consts.IPERF_SERVER_CMD)
            iperf_host_pid = self.os.execute("pgrep {}".format(self._tool_name),
                                             self.command_timeout).stdout.strip()
            if iperf_host_pid == "":
                raise RuntimeError("{} failed to run on TDX host.".format(self._tool_name))
            self._log.debug("{} is listening on TDX host. PID: {}".format(self._tool_name, iperf_host_pid))
            for idx in range(0, num_vms):
                self._log.info("Starting TD guest {}.".format(idx))
                self.launch_vm(key=idx, tdvm=True)
                self._log.info("Attempting to execute SSH command to VM key {}.".format(idx))
                if not self.vm_is_alive(key=idx):
                    raise content_exceptions.TestFail("VM {} could not be reached after booting.".format(idx))
                self._log.debug("SSH was successful; VM {} is up.".format(idx))
                self.set_up_tool(idx=idx)
                self._log.info("Launching {} suite on VM {}.".format(self._tool_name, idx))
                log_file_name = "~/tdvm-{}-{}.txt".format(self._tool_name, idx)
                cmd = self._tool_run_cmd.format(self._tool_run_time) + log_file_name
                self._log.info("Running {} suite on VMs for {} seconds...".format(self._tool_name, self._tool_run_time))
                self.ssh_to_vm(key=idx, cmd=cmd, async_cmd=True)
                self.check_process_running(key=idx, process_name=self._tool_name)
                time.sleep(self._tool_run_time)
        finally:
            self._log.debug("Killing {} listening on TDX host.".format(self._tool_name))
            iperf_host_pid = self.os.execute("pgrep {}".format(self._tool_name),
                                             self.command_timeout).stdout.strip()
            self.os.execute("kill {}".format(iperf_host_pid), self.command_timeout)
        return True

    def cleanup(self, return_status):
        self._log.info("{} test is done.  Copying log files from VMs and shutting down VMs.".format(
            self._tool_name))
        for idx in range(0, self.tdx_properties[self.tdx_consts.NUMBER_OF_VMS]):
            log_file_name = "~/tdvm-{}-{}.txt".format(self._tool_name, idx)
            self.copy_file_between_sut_and_vm(idx, log_file_name, "/tdx/tdvm/logs/", to_vm=False)
            self.teardown_vm(key=idx)
        super(TDGuestIperf, self).cleanup(return_status)

    def set_up_tool(self, idx):
        self._log.debug("Copying and building {} from SUT to VM {}.".format(self._tool_name, idx))
        pkg_install_command = "yum -y install iperf3"
        result = self.ssh_to_vm(key=idx, cmd="{}".format(pkg_install_command))
        if "error" in result:
            raise content_exceptions.TestFail("Failed to install iperf on VM {}.  Error message: {}".format(idx,
                                                                                                            result))


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TDGuestIperf.main() else Framework.TEST_RESULT_FAIL)
