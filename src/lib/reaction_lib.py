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
import os
import six
import platform

from threading import Thread, Lock

from dtaf_core.lib.dtaf_constants import OperatingSystems


class ReactionLib(object):
    """
    Class which triggers events based on SUT log information over a COM/serial port.
    """

    def __init__(self, log, console_log, console_log_skip_to_end=False, daemon=True):
        self._console_log = console_log
        self._log = log
        # This below parameter should be True if to skip reading lines that was already in log,
        # And to consider any log details from now onwards
        self._console_log_skip_to_end = console_log_skip_to_end
        self._lock = Lock()
        self._daemon = daemon
        exec_os = platform.system()
        if OperatingSystems.WINDOWS in exec_os:
            self.new_line_pattern = "\r\n"
        elif OperatingSystems.LINUX in exec_os:
            self.new_line_pattern = "\n"
        else:
            self._log.error("Reaction lib is not supported in OS '{}'".format(exec_os))
            raise RuntimeError("Reaction lib is not supported in OS '{}'".format(exec_os))

    def __enter__(self):
        self._reactions = {}
        self._thread = Thread(target=self._reaction_thread)
        if self._daemon:
            self._thread.daemon = True
        self._log.debug("Reactionlib thread created, thread id {}".format(self._thread.name))
        self._run_thread = True
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._lock.acquire()
        self._log.debug("Exiting reactionlib thread id {}".format(self._thread.name))
        self._run_thread = False
        self._lock.release()

    def register_reaction(self, pattern, function_object):
        """
        Register an event so that the thread will call function_object whenever the event is triggered.

        Pattern is a string formatted per the Python re module's syntax that will be compiled and used to search on
        every line in the SUT's log output. Whenever there is a match, function_object will be called, passing in the
        match results as the first parameter.
        :param pattern: Regular expression string to trigger on.
        :param function_object: Function to execute whenever the event is triggered.
        :return: None
        """
        self._reactions[pattern] = (re.compile(pattern), function_object)

    def remove_reaction(self, pattern):
        """
        Function is removing string from watch list.

        """
        self._lock.acquire()
        try:
            self._reactions.pop(pattern)
        finally:
            self._lock.release()

    def _reaction_thread(self):
        """
        TODO: Once New Feature of Reaction provider is enabled we would test it.
        """
        console_log_file = open(self._console_log.log_file, 'r', newline="")

        # The below steps is to ensure the latest log information file
        if self._console_log_skip_to_end:
            console_log_file.seek(0, os.SEEK_END)
        actual_console_data = None
        prev_data = ""
        # run the thread in loop and exit once the flag is set
        while True and self._run_thread:
            self._lock.acquire()
            try:
                # The data which was coming from reading of serial log was distorted.
                # SO below logic is implemented to capture proper data and then comparing
                line = console_log_file.readline()
                if self.new_line_pattern not in line:
                    prev_data = prev_data + line
                else:
                    split_line = line.split(self.new_line_pattern)
                    prev_data = prev_data + split_line[0]
                    actual_console_data = prev_data
                    prev_data = self.new_line_pattern.join(split_line[1:])

                if actual_console_data is not None and actual_console_data != "":
                    for pattern, p_data in six.iteritems(self._reactions):
                        res = p_data[0].match(actual_console_data)
                        if res:
                            self._log.debug("Matched line: " + actual_console_data.strip())
                            p_data[1](res)  # Implement as subprocesses later for performance
            finally:
                self._lock.release()

        self._log.debug("Reactionlib thread is exiting from loop, thread id {}".format(self._thread.name))
