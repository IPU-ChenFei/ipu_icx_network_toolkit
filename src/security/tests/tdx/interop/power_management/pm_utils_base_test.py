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
    :PM Utils + TDX Base Test:

    Launch a given number of TD guests and run pm_utis test suite on the SUT for prescribed amount of time."""

import sys
import os

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems
from src.lib import content_exceptions
from src.security.tests.tdx.tdx_common_linux import LinuxTdxBaseTest


class TdxPmUtilsBaseTest(LinuxTdxBaseTest):
    """
           This is a base test for testing with pm_utils suite with TD guests as part of the TDX feature.

           The following parameters in the content_configuration.xml file should be populated before running a test.

            Change <TDX><num_of_vms> to control the number of TD guests that will be run in parallel.

            :Scenario: Launch the number of TD guests prescribed, initiate pm_utils on the SUT, run pm_utils for the
            necessary time to complete the tests, then verify the SUT and the TD guests have not crashed.

            :Phoenix IDs:

            :Test steps:

                :1: Launch a TD guest.

                :2: On SUT, build and launch pm_utils tst suite/

                :3: Run until workload tests complete.

            :Expected results: Each TD guest should boot and the pm_utils test suite should run to completion with no
            errors on the SUT or any of the TD guests.

            :Reported and fixed bugs:

            :Test functions:

        """

    _BIOS_CONFIG_FILE_CSTATE_AUTO = "collateral/cstate_auto_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new object for TdxPmUtilsBaseTest

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(TdxPmUtilsBaseTest, self).__init__(test_log, arguments, cfg_opts)
        self.pm_util_cmd = ""  # command
        self.pm_util_timeout = ""
        self._pm_install_dir = self.install_collateral.install_pmutility().strip()
        self.cstate_auto_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                             self._BIOS_CONFIG_FILE_CSTATE_AUTO)

    def prepare(self):
        self._log.info("Checking OS is Linux.")
        if self.sut_os != OperatingSystems.LINUX:
            raise content_exceptions.TestSetupError("PM utils tests only support Linux distributions; OS {} is not "
                                                    "supported. ")
        self._log.info("Checking Cstate knob is set to Auto.")
        self.check_knobs(knob_file=self.cstate_auto_file, set_on_fail=True)
        self._log.info("Setting date and time.")
        self._common_content_lib.set_datetime_on_linux_sut()
        self._log.info("Verifying idle driver is supported by OS.")
        driver_result = self.execute_os_cmd("cat /sys/devices/system/cpu/cpuidle/current_driver")
        if not ("intel_idle" in driver_result or "acpi_idle" in driver_result):
            raise content_exceptions.TestSetupError("SUT does not support idle driver needed by PM utils.")
        super(TdxPmUtilsBaseTest, self).prepare()

    def execute(self):
        num_vms = self.tdx_properties[self.tdx_consts.NUMBER_OF_VMS]
        self._log.info("Creating and launching {} VMs.".format(num_vms))
        for idx in range(0, num_vms):
            self._log.info("Starting TD guest {}.".format(idx))
            self.launch_vm(key=idx, tdvm=True)
            self._log.info("Attempting to execute SSH command to VM key {}.".format(idx))
            if not self.vm_is_alive(key=idx):
                raise content_exceptions.TestFail("VM {} could not be reached after booting.".format(idx))
            self._log.debug("SSH was successful; VM {} is up.".format(idx))

        self._log.info("VMs are up; setting up pm_utils on SUT.")
        if self.pm_util_cmd == "" or self.pm_util_timeout == "":  # pm util command was not defined
            raise content_exceptions.TestError("Missing or undefined pm util parameter.! PM util command: {}, PM util "
                                               "timeout: {}".format(self.pm_util_cmd, self.pm_util_timeout))
        run_cmd = "{}/{}".format(self._pm_install_dir, self.pm_util_cmd)
        time_in_seconds = float((int(self.pm_util_timeout) + 1) * 60)
        run_results = self.execute_os_cmd(run_cmd, time_in_seconds)  # pmutils timeout is in minutes, converting to seconds
        if run_results == "":  # no results were returned,  something has gone wrong
            raise content_exceptions.TestError("Got no results when running PM utils command; please check set up.")
        self._log.info("Output from executing Cstate harasser: {}".format(run_results))
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TdxPmUtilsBaseTest.main() else Framework.TEST_RESULT_FAIL)
