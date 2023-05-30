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
    :TDX Base Cycle Test Case:

    Base test case for TDX power cycling.
"""

import sys
import time
import os
import logging
import argparse
from xml.etree import ElementTree

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.lib.exceptions import OsCommandException

from src.power_management.lib.reset_base_test import ResetBaseTest
from src.security.tests.tdx.tdvm.TDX050_launch_multiple_tdvm_linux import MultipleTDVMLaunch
from src.lib import content_exceptions


class TdxCycleTest(ResetBaseTest):
    """
            This test is to serve as a base cycle test for TDX power cycle testing.

            :Scenario: Boot to an OS with a TDX enabled VMM and launch a TD guest VM.  Power cycle the system (as
            defined in power_cycle, verify that TD guest is not up,  and relaunch the TD guest.  Repeat for given
            number of cycles. power_cycle must be overridden in the inheriting class.

            :Phoenix ID: N/A

            :Test steps:

                :1: Boot to an OS with a TDX enabled VMM.

                :2: Launch a TD guest VM.

                :3: Power cycle the system.

                :4: Verify TD guest is not booted when system boots to OS.

                :5: Repeat steps 1-4 for given number of cycles.

            :Expected results: Each time after a reset, the SUT should boot to the OS.  Each time a TD guest is
            attempted to be launched should be successful.

            :Reported and fixed bugs:

            :Test functions:

        """

    def __init__(self, test_log: logging.Logger, arguments: argparse.Namespace, cfg_opts: ElementTree) -> None:
        """
        Create an instance of test case.
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(TdxCycleTest, self).__init__(test_log, arguments, cfg_opts)
        self.failed_iterations = []
        self.multiple_tdvms = MultipleTDVMLaunch(test_log, arguments, cfg_opts)
        self.cycle_test_type = None
        self.command_timeout = self.multiple_tdvms.command_timeout
        self.tdx_consts = self.multiple_tdvms.tdx_consts
        self.tdx_properties = self.multiple_tdvms.tdx_properties
        self.sut_os = self.multiple_tdvms.sut_os
        try:
            self.tdx_properties[self.tdx_consts.MEM_INTEGRITY_MODE] = arguments.INTEGRITY_MODE.upper()
        except AttributeError:  # no argument given for memory integrity
            self._log.debug("No memory integrity setting given, leaving knob alone.")
            self.tdx_properties[self.tdx_consts.MEM_INTEGRITY_MODE] = None

    @classmethod
    def add_arguments(cls, parser):
        """
        :param parser: argument parser
        :return: None
        """
        super(TdxCycleTest, cls).add_arguments(parser)
        parser.add_argument("--integrity-mode", "--im", action="store", dest="INTEGRITY_MODE", default=None)

    def prepare(self) -> None:
        self.multiple_tdvms.os_preparation()  # verify python softlink is installed in OS
        super(TdxCycleTest, self).prepare()
        self.multiple_tdvms.prepare()
        self.multiple_tdvms.install_collateral.yum_install("gnome-settings-daemon gnome-session")
        if self.cycle_test_type == "Redfish" or self.cycle_test_type == "IPMI":
            for command in [self.tdx_consts.POWER_BUTTON_SHUTDOWN_SET_CMD, self.tdx_consts.DISABLE_LOGIN_TIMER_CMD]:
                result = self.os.execute(command, self.command_timeout)
                if result.stderr != "":
                    raise content_exceptions.TestSetupError(f"Failed to set power button shut down behaviour in OS. "
                                                            f"Stdout: {result.stdout}\nStderr: {result.stderr}")

    def execute(self) -> bool:
        ignore_mce_error = self._common_content_configuration.get_ignore_mce_errors_value()

        self._log.info(f"Number of {self.cycle_test_type} cycles to be executed: {self.total_cycles}")
        if self.health_check:
            self.baseline_pcie_health_check()

        self.cng_log.__exit__(None, None, None)
        for cycle_number in range(1, self.total_cycles + 1):
            self._log.info(f"******* Cycle number {cycle_number} started *******")
            self._failed_pc = None
            self._boot_flow = None
            if not ignore_mce_error:
                self._log.info("Clearing MCE logs")
                self._common_content_lib.clear_mce_errors()
            start_time = time.time()
            serial_log_file = os.path.join(self.serial_log_dir, f"serial_log_iteration_{cycle_number}.log")
            with ProviderFactory.create(self.cng_cfg, self._log) as cng_log:
                cng_log.redirect(serial_log_file)
                cycle_status = self.power_cycle()
                end_time = time.time()
                boot_time = int(end_time - start_time)
                self._log.info(f"Cycle #{cycle_number} completed with status code {cycle_status}. Boot time for the "
                               f"cycle is {boot_time} seconds.")
                if cycle_status != 0:
                    if cycle_status in self.reset_handlers.keys():
                        handler = self.reset_handlers[cycle_status]
                        ret_val = handler(cycle_number)
                    else:
                        ret_val = self.default_reset_handler(cycle_number)
                    cng_log.__exit__(None, None, None)
                    if not ret_val:
                        self._log.error(f"Terminating the {self.cycle_test_type} cycling test..")
                        break
                self.during_cycle(cycle_number)

            # end of cycle test for loop

        # print test summary here
        test_status = True
        if self._number_of_failures > 0 or len(self.failed_iterations) > 0:
            test_status = False
        self.print_result_summary()

        return test_status

    def power_cycle(self) -> None:
        """Power cycle the system and wait for boot."""
        raise NotImplementedError("power_cycle method must be overridden at the test level!")

    def during_cycle(self, cycle_number: int) -> None:
        """Action to take on SUT after booted but before power_cycle.
        :param cycle_number: number of current cycle; provided for use with log files."""
        # system booted, so attempt to boot TD guest
        try:
            self.multiple_tdvms.execute()
        except (content_exceptions.TestFail, content_exceptions.TestError) as e:
            log_error = f"Cycle #{cycle_number}: Failed to boot TD guest.  Exception data: {e}"
            self.failed_iterations.append(log_error)
        try:
            self.multiple_tdvms.rename_vm_log_files(file_rename=f"-cycle-{cycle_number}")
        except content_exceptions.TestError:
            self._log.warning(f"Could not save VM serial logs for cycle {cycle_number} as SUT did not appear "
                              f"to be up.")

    def print_result_summary(self) -> None:
        """Print the result summary at the end of the test."""
        self._log.info("******************* Start Summary of Cycling test *************************")
        self._log.info(f"Number of cycles succeeded = {self.total_cycles - self._number_of_failures} and failed "
                       f"= {self._number_of_failures}.")
        if self._number_of_failures > 0:
            self._log.error("\n".join(self._list_failures))
        if len(self.failed_iterations) != 0:
            self._log.info(f"Number of cycles TD guest failed to boot:  {len(self.failed_iterations)}.")
            self._log.error("\n".join(self.failed_iterations))
        else:
            self._log.info("No TD guest boot failures found.")
        self._log.info("******************* End Summary of Cycling test *************************")

    def cleanup(self, return_status: bool) -> None:
        """Save log files and close any remaining processes related to test.
        :param return_status: True if test passed, False if test failed."""
        self._log.debug("Running cleanup for Multiple TD guest launch test case.")
        if self.os.is_alive():
            self._log.info("OS is up, cleaning up open VMs and saving log files.")
            # teardown running VMs
            self._log.info("Killing remaining running VMs.")
            self.multiple_tdvms.kill_all_running_vms()
            self._log.info("Copying log files to log directory on SUT at {}.".format(self.log_dir))
            td_guest_zip = self.multiple_tdvms.tdx_consts.ZIPPED_TDVM_FILES
            zipped_vm_logs = self.multiple_tdvms.compress_vm_log_files()
            try:
                self.os.copy_file_from_sut_to_local(zipped_vm_logs, f"{self.log_dir}\\{td_guest_zip}")
            except (FileNotFoundError, IOError, OsCommandException):
                self._log.warning("Caught exception when attempting to copy VM log files from SUT... likely no VMs "
                                  "successfully launched.")
            self._log.info("Clearing log files from VM directory on SUT.")
            self.multiple_tdvms.execute_os_cmd(f"rm -rf {self.tdx_consts.TD_GUEST_LOG_PATH_LINUX}/*")
        else:
            self._log.warning("OS does not appear to be up - failed to collect VM log files.  Please verify system "
                              "health and save the log files from {} on the SUT OS with the test logs.".format(
                self.tdx_consts.TD_GUEST_LOG_PATH_LINUX))
        self._log.debug("Launching cleanup for TdxCycleTest class.")
        if self.cycle_test_type == "Redfish" or self.cycle_test_type == "IPMI":
            result = self.os.execute(self.tdx_consts.POWER_BUTTON_SUSPEND_SET_CMD, self.command_timeout)
            if result.stderr != "":
                raise content_exceptions.TestSetupError(f"Failed to set power button shut down behaviour in OS. "
                                                        f"Stdout: {result.stdout}\nStderr: {result.stderr}")
        super(TdxCycleTest, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TdxCycleTest.main() else Framework.TEST_RESULT_FAIL)
