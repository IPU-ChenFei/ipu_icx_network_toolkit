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
import time

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.security.tests.cbnt_txt.txt_common import TxtBaseTest


class SystemIdleTestWithMLE(TxtBaseTest):
    """
    Glasgow ID : 58226
    Phoenix ID : 18014070554
    This Test case is to demonstrate Trusted boot With TXT enabled by selecting trusted OS and running stress
    tool Prime95 and ensuring that the boot is Trusted even after stress test
    pre-requisites:
    1.Ensure that the system is in sync with the BKC.
    2.Ensure that you have a Linux OS image or hard drive with tboot installed.
    3.Ensure that the platform has a TPM provisioned with an ANY policy installed
        and active
    """
    _MPRIME_FOLDER_NAME = "Prime95"
    _COLLATERAL_DIR_NAME = "collateral"
    _STRESS_MPRIME_LINUX_FILE = "prime95.tar.gz"
    _BIOS_CONFIG_FILE = "txt_base/security_txt_bios_knobs_enable.cfg"
    _MPRIME_PATH = "/root/Prime95/"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(SystemIdleTestWithMLE, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)
        self.tboot_index = None

    def prepare(self):
        # type: () -> None
        """
        Pre-validating whether sut is configured with tboot by getting the tboot index in OS boot order.
        Loading BIOS defaults settings.
        Sets the bios knobs according to configuration file and verifies if bios knobs sets successfully.
        Copy Prime95 tool tar file to Linux SUT Unzip tar file under user home folder of SUT.
        """

        # get the tboot_index from grub menu entry
        self.tboot_index = self.get_tboot_boot_position()
        # set tboot as default boot
        self.set_default_boot_entry(self.tboot_index)
        self._bios_util.load_bios_defaults()  # To set Bios knobs to default.
        self._bios_util.set_bios_knob()  # To set the bios knob setting
        self._os.reboot(self._reboot_timeout)  # To apply Bios changes
        self._bios_util.verify_bios_knob()  # To verify the Bios knob value set
        self._install_collateral.install_prime95()  # to copy Prime95 tool to sut

    def execute_mprime(self):
        """
        Executing prime95 stress tool for configured timeout value
        :raise: RuntimeError - Raised when Mprime process is not started
        :return: None
        """
        command_line = "./mprime -t"
        try:
            # running the command to start 'mprime' tool
            self._log.info("Starting the command mprime command '{}' to start torture test".format(command_line))
            self._log.info("The mprime command will run from directory '{}' and duration '{}'"
                           .format(self._MPRIME_PATH, self._prime_running_time))
            self._os.execute_async(command_line, cwd=self._MPRIME_PATH)
            cmd_result = self._os.execute("ps -ef |grep mprime", self._command_timeout)
            if cmd_result.cmd_failed():
                self._log.error("Failed to execute command line '{}'".format("ps -ef |grep mprime"))

            if command_line in cmd_result.stdout:
                self._log.info("Mprime process successfully started and process "
                               "details = '{}'".format(cmd_result.stdout))
            else:
                log_error = "Mprime process did not started successfully..."
                self._log.info(log_error)
                raise RuntimeError(log_error)
        except Exception as ex:
            log_error = "Exception :'{}' occurred during the execution of command '{}'".format(str(ex), command_line)
            self._log.error(log_error)
            raise log_error

    def terminate_mprime(self):
        """
        Terminate the mprime process after running for configured time.
        :return: None
        :raise: Raise user defined Exception if failed to kill the mprime process
        """
        command_line = "pkill -INT mprime"
        try:
            # We will wait little longer as mprime take more time to respond
            command_result = self._os.execute(command_line, self._command_timeout)
            if command_result.cmd_failed():
                log_error = "Failed to kill the mprime application with return value = '{}' and " \
                            "std_error = '{}'..".format(command_result.return_code, command_result.stderr)
                self._log.error(log_error)
            else:
                self._log.info("mprime process is killed successfully")
        except Exception as ex:
            log_error = "Failed to kill the mprime due to exception {}".format(ex)
            self._log.error(log_error)
            raise log_error

    def execute(self):
        """
        This function is used to check SUT should be boot in trusted environment
        :return: True if Test case pass else fail
        """
        # set the os boot order to tboot as default
        ret_val = False

        self.verify_sut_booted_in_tboot_mode(self.tboot_index)
        if not self.verify_trusted_boot():  # verify the sut boot with trusted env
            self._log.info("SUT did not Boot into Trusted environment")
            return ret_val

        self.execute_mprime()  # to execute prime95 tool

        # wait for configured amount of time
        time.sleep(self._prime_running_time)  # sleep for duration of mprime timeout

        self.terminate_mprime()

        # check if trusted boot is still enabled after stress test
        ret_val = self.verify_trusted_boot()  # verify the sut boot with trusted env
        if ret_val:
            self._log.info("SUT Booted to Trusted environment Successfully")
        else:
            self._log.error("SUT did not Boot into Trusted environment")
        return ret_val


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SystemIdleTestWithMLE.main() else Framework.TEST_RESULT_FAIL)
