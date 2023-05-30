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

import re
import sys
import six
import time
import random
from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from dtaf_core.providers.console_log import ConsoleLogProvider
from dtaf_core.providers.provider_factory import ProviderFactory
from src.security.tests.cbnt_txt.txt_common import TxtBaseTest
from threading import Event
from abc import abstractmethod, ABCMeta
from src.lib.reaction_lib import ReactionLib


@six.add_metaclass(ABCMeta)
class SecretsBaseFlow(TxtBaseTest):

    SECRET = 0xdeadbeef
    INIT_BREAK_TIMEOUT = 400
    OS_CONTINUE_TIMEOUT = 400
    OS_BOOT_DELAY = 600
    SUT_SHUTDOWN_DELAY = 10.0
    AC_POWER_OFF_DELAY = 20.0
    RESET_BREAK_DELAY = 60.0
    INIT_BREAK_DELAY = 120.0
    LOG_FOLDER = "cscript"
    CSCRIPT_FILE_NAME = "cscript_log.txt"

    def __init__(self, test_log, arguments, cfg_opts, exec_platform):
        super(SecretsBaseFlow, self).__init__(test_log, arguments, cfg_opts, exec_platform)
        serial_log_cfg = cfg_opts.find(ConsoleLogProvider.DEFAULT_CONFIG_PATH)
        self._console_log = ProviderFactory.create(serial_log_cfg, test_log)
        if self._os.os_type != OperatingSystems.LINUX:
            raise ValueError("Secrets flow requires use of Linux and tboot.")
        self.secret_locations = []
        self.crystal_ridge = arguments.crystal_ridge
        self._init_break_event = Event()
        self._log_file_path = self._common_content_lib.get_log_file_path(self.LOG_FOLDER, self.CSCRIPT_FILE_NAME)

    @classmethod
    def add_arguments(cls, parser):
        super(SecretsBaseFlow, cls).add_arguments(parser)
        parser.add_argument('--crystal_ridge', action="store_true", default=False,
                            help="Set if using Crystal Ridge to bypass memory search step.")

    def execute(self):
        """
        1. This method parse e820 table
        2. write secrets to memory location
        3. DO surprise reset
        4. Wait for the init break trigger and halt cpu to check if serects are clear
        5. Verify trusted boot

        :return: Return true if boot trusted else it return False
        """
        result = False
        self._log.info("Parsing e820 table to get usable memory ranges.")
        memory_ranges = self.parse_e820_table()
        self._log.info("Writing secrets into memory.")
        self.write_secrets(memory_ranges)
        self._log.info("Executing surprise reset!")
        self.surprise_reset()  # Implementation varies based on child classes.
        self._log.info("Registering serial log trigger.")  # W/A for ITP-TXT interaction
        with ReactionLib(self._log, self._console_log) as reaction_engine:
            self._log.info("Waiting for init break.")
            reaction_engine.register_reaction(" Boot in Normal mode", self.init_break_trigger)
            if self._init_break_event.is_set():
                raise RuntimeError("Missed the INIT break trigger! Check for blocking tasks before this call.")
            if not self._init_break_event.wait(timeout=self.INIT_BREAK_TIMEOUT):
                raise RuntimeError("Did not get the INIT break trigger!")
            self._log.info("Got the init trigger event........")
            self._log.info("Halting cpu")
            self._sdp.start_log(self._log_file_path, "w")  # Starting CScripts Log
            self._sdp.halt()
            self._log.info("Checking for secrets.")
            try:
                result = self.check_for_secrets_clear()
            finally:
                self._sdp.go()
                self._sdp.stop_log()  # Stopping CScripts Log
                self.capture_cscript_log()  # Log the CScripts logs in log file

            if not result:
                self._log.error("Secrets still found in memory. Test failed.")
            else:
                self._log.info("Finished checking secrets! Waiting for OS to boot.")
        time.sleep(self._reboot_timeout)  # Waits until the system comes up
        trusted = self.check_txt_state()  # Confirm trusted recovery
        if not trusted:
            result = False
            self._log.error("SUT did not recover to the expected trusted state after reset. Test failed.")
        else:
            self._log.info("SUT recovered to the expected trusted state.")

        return result

    def execute_itp_only(self):
        """TODO: when the pve-common function will get complete, will update this function as well"""

        # Get memory ranges from the e820 table
        self._log.info("Parsing e820 table.")
        memory_ranges = self.parse_e820_table()

        self._log.info("Writing secrets into memory.")
        self.write_secrets(memory_ranges)

        self._log.info("Preparing ITP for surprise reset.")
        self._sdp.reset_break(True)

        self._log.info("Executing surprise reset and waiting for reset break!")
        self.secrets_reset()  # Implementation varies based on child classes.

        time.sleep(self.RESET_BREAK_DELAY)  # Dead reckoning rather than polling to avoid messing with the boot flow.
        if not self._sdp.is_halted():
            self._log.exception("Device did not enter reset break!")
            raise RuntimeError("Device did not enter reset break!")

        self._log.info("Set init break and continue.")
        self._sdp.reset_break(False)
        self._sdp.init_break(True)
        self._sdp.go()

        self._log.info("Waiting for init break.")
        time.sleep(self.INIT_BREAK_DELAY)
        if not self._sdp.is_halted():
            self._log.exception("Device did not enter init break!")
            raise RuntimeError("Device did not enter init break!")

        self._log.info("Checking for secrets.")
        try:
            result = self.check_for_secrets_clear()
        finally:
            self._sdp.init_break(False)
            self._sdp.go()

        if not result:
            self._log.error("Secrets still found in memory. Test failed.")
        else:
            self._log.info("Finished checking secrets! Waiting for OS to boot.")
            self._os.wait_for_boot()
            trusted = self.check_txt_state()  # Confirm trusted recovery
            if not trusted:
                result = False
                self._log.error("SUT did not recover to the expected trusted state after reset. Test failed.")
            else:
                self._log.info("SUT recovered to the expected trusted state.")

        return result

    def parse_e820_table(self):
        # Get e820-related messages
        e820_msgs = self._os.execute('dmesg | grep "BIOS-e820"', 10)

        # Regex for parsing e820 table
        e820_table_pat = "BIOS-e820: \[mem 0x([a-fA-F0-9]+)-0x([a-fA-F0-9]+)\] ([a-zA-Z ]+)$"
        self._log.debug("BIOS-e820 table")

        ranges = []
        for line in e820_msgs.stdout.split("\n"):
            self._log.debug(line)
            m = re.search(e820_table_pat, line)
            if m:
                # Line of the e820 table
                if m.group(3) == "usable":
                    ranges.append((int(m.group(1), 16), int(m.group(2), 16)))

        return ranges

    def get_open_word(self, memory_range):
        start = memory_range[0]
        if self.crystal_ridge:
            loc = hex(random.randint(memory_range[0], memory_range[1])).rstrip('L') + 'p'
            self._log.debug("Executing with Crystal Ridge; Bypassing memory search. Using " + str(loc))
            self._log.debug("Before writing secret, value = " + str(self._sdp.mem_read(loc, 8)))
        else:
            self._log.debug("Starting search for memory range " + str(memory_range) +
                            " at location " + hex(start).rstrip("L"))
            loc = None
        while start < memory_range[1] and loc is None:
            value = self._sdp.mem_read(hex(start).rstrip("L") + 'p', 8)
            self._log.debug("Memory location " + str(hex(start)) + "/" + str(memory_range[1]) + " = " + str(value))
            if int(value) == 0:
                loc = hex(start).rstrip('L') + 'p'
                self._log.debug("Found open word at " + str(loc) + " in range " + str(memory_range))
            start = start + 0x10
        if loc is None:
            self._log.debug("SUT has no unused memory in region " + str(memory_range))
            self._log.debug("Writing to random in-use memory address")
            loc = hex(random.randint(memory_range[0], memory_range[1])).rstrip('L') + 'p'
        return loc

    def write_secrets(self, memory_ranges):
        # Halt SUT
        self._sdp.halt()

        # Write secrets to memory
        try:
            for memory_range in memory_ranges:
                self._log.debug("Getting the first open word for memory range: " + str(memory_range))
                loc = self.get_open_word(memory_range)
                self._log.debug("Writing secret " + hex(self.SECRET).rstrip('L') + "... Don't tell anyone, ok?")
                self._sdp.mem_write(loc, 8, self.SECRET)
                self.secret_locations.append(loc)

            # Check that all secrets were set properly
            for loc in self.secret_locations:
                read_back = self._sdp.mem_read(loc, 8)
                self._log.debug("Read back " + str(read_back) + " from " + str(loc))
                if read_back != self.SECRET:
                    self._log.exception("Secret set failed at location " + loc)
                    raise RuntimeError("Secret set failed at location " + loc)
        finally:
            self._sdp.go()

    def check_txt_state(self):
        return self.verify_trusted_boot(expect_ltreset=True)

    @abstractmethod
    def surprise_reset(self):
        raise NotImplementedError("All child classes of SecretsBaseFlow must implement surprise reset")

    def check_for_secrets_clear(self):
        result = True
        for loc in self.secret_locations:
            val = self._sdp.mem_read(loc, 8)
            secret_cleared = val != self.SECRET
            self._log.debug("Read " + str(hex(val)) + " from location " + str(loc) +
                            ". Secret cleared: " + str(secret_cleared))
            if not secret_cleared:
                self._log.info("Secret was not cleared from location " + str(loc) + "!")
                result = False
        return result

    # noinspection PyUnusedLocal
    def init_break_trigger(self, match):
        self._log.debug("INIT break trigger received! Setting INIT break event.")
        self._init_break_event.set()

    def capture_cscript_log(self):
        """
        This function captures the cscript log when halting CPU after getting the init break trigger

        :raise : OSError, IOError Exception is raised if any error has occurred during reading the cscript log file
        :return: None
        """
        try:
            with open(self._log_file_path, "r") as log_file:  # Open the cscript log file
                log_details = log_file.read()
                # Capture the log information in test case log file
                self._log.info("Output of failed log is: '{}'".format(log_details))

        except (OSError, IOError) as e:
            self._log.error("Error in reading file due to exception '{}'".format(e))
            raise e


if __name__ == '__main__':
    print("This module does not have any tests to execute.")
    sys.exit(Framework.TEST_RESULT_FAIL)
