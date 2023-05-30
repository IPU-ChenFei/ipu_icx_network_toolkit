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
import time
from dtaf_core.lib.dtaf_constants import OperatingSystems
from src.lib.content_configuration import ContentConfiguration


class SleepStateExecutor(object):
    """Contains functions related to executing SUT sleep cycles."""

    S3 = "S3"
    S4 = "S4"

    # Default sleep times
    DEFAULT_SLEEP_TIMES = {S3: 120, S4: 300}

    # Linux sleep commands
    LINUX_SLEEP_COMMANDS = {S3: "rtcwake -m mem -s %d", S4: "rtcwake -m disk -s %d"}

    # Linux AWK and grep methods for truncating and searching the dmesg log (Thanks to the Runner team!)
    DMESG_AWK_PROGRAM = " { if (flag>0) { print; } }  /%s/ { print; flag=1; } "
    DMESG_FULL_CMD = 'dmesg | awk "' + DMESG_AWK_PROGRAM + \
                     '" | grep "ACPI: Waking up from system sleep state" | tail -1 | awk \'{ print $NF }\''

    # Linux dmesg sleep state names
    DMESG_SLEEP_NAMES = {S3: "S3", S4: "S4"}

    def __init__(self, log, os):
        """
        Creates a New SleepStateExecutor Object

        :param log: Log Object to Log the data
        :param os: Os Object to Perform any Os Level Operations
        """
        self._log = log
        self._os = os
        self._content_config = ContentConfiguration(self._log)
        self._execute_command_timeout = self._content_config.get_command_timeout()

    def validate_linux_acpi_log(self, last_acpi_str, sleep_state, desired_sleep_time, actual_sleep_time):
        """
        This Method is Used to Validate Linux Acpi Log

        :param last_acpi_str: Last Acpi String
        :param sleep_state: Time in seconds to stay in the sleep state
        :param desired_sleep_time: Expected Sleep Time
        :param actual_sleep_time: Actual Sleep Time
        :return:
        """
        self._log.info("Validating last ACPI state...")
        self._log.info("Last ACPI string = " + str(last_acpi_str))
        acpi_valid = last_acpi_str == self.DMESG_SLEEP_NAMES[sleep_state]
        if not acpi_valid:
            self._log.error("System did not resume from ACPI " + str(sleep_state) +
                            " properly! Actual last state = " + str(last_acpi_str))
            result = False
        else:
            self._log.info("Validating sleep time...")
            result = actual_sleep_time >= desired_sleep_time
            if not result:
                self._log.error("Time to sleep was shorter than expected! Expected %d, Actual %d"
                               % (desired_sleep_time, actual_sleep_time))
                return False
        return result

    def linux_sleep_cycle(self, sx_state, sleep_time):
        """
        Executes one Linux Sleep Cycle

        :param sx_state: S3 or S4 State
        :param sleep_time: Time in seconds to stay in the sleep state
        :return: True or False
        """
        self._log.info("Injecting marker into the dmesg log")
        marker_ts = int(round(time.time()))
        marker = "PTV" + sx_state + "cycle" + str(marker_ts)
        self._os.execute("echo " + marker + " > /dev/kmsg", self._execute_command_timeout)

        self._log.info("Sending SUT into " + sx_state)
        result = self._os.execute(self.LINUX_SLEEP_COMMANDS[sx_state] % sleep_time)
        valid = result.cmd_passed()

        if valid:
            self._log.info("Getting dmesg log from SUT")
            last_acpi_str = self._os.execute(self.DMESG_FULL_CMD % marker, self._execute_command_timeout)
            if last_acpi_str.cmd_failed() or len(last_acpi_str.output) == 0:
                self._log.error("Failed to get ACPI state from log. Output (if any): " + str(last_acpi_str.output))
                valid = False
            else:
                self._log.info("Validating SUT wakeup")
                last_acpi_str = last_acpi_str.output.rstrip()
                valid = self.validate_linux_acpi_log(last_acpi_str, sx_state, sleep_time,
                                                     int(round(time.time())) - marker_ts)
            if not valid:
                self._log.error("SUT did not enter or resume from " + str(sx_state) + " properly!")
        else:
            self._log.error("Sleep state command failed! Command output: " + str(result.output))

        return valid

    def sleep_cycle(self, sx_state, sleep_time=None):
        """
        Execute one sleep cycle on the SUT.

        :param sx_state: Sleep state to use in the cycle, specified by a power_state_utils.SleepStates constant.
        :param sleep_time: Time in seconds to stay in the sleep state.
                If None, the sleep time will be the default stored in this class.
        :return: True if cycling was successful, False otherwise
        """
        if sleep_time is None:
            sleep_time = self.DEFAULT_SLEEP_TIMES[sx_state]
        if self._os.os_type == OperatingSystems.LINUX:
            result = self.linux_sleep_cycle(sx_state, sleep_time)
        else:
            raise RuntimeError("OS " + self._os.os_type + " not supported by the sleep_cycle function!")
        return result
