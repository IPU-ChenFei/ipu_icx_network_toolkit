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

from src.lib import content_exceptions


class SerialLogVerifyCommon:
    """
    This Class is to verify the Os Log Error.
    1. BIOS Log Verification.
    """

    def __init__(self, log, os, cfg_opts, serial_bios_file_path):
        self._os = os
        self._log = log
        self._serial_bios_file_path = serial_bios_file_path
        self._cfg = cfg_opts

    def verify_bios_log_error_messages(self, passed_error_signature_list_to_parse, serial_bios_file_path=None):
        """
        verify error signatures are present for given error log and error type in the Bios Logs.

        :param passed_error_signature_list_to_parse: Error Signature-eg:["IEH CORRECT ERROR", "Sev: IEH CORRECT ERROR"]
        :param serial_bios_file_path: stored bios log file path
        :return True if signature found in Bios Log.
        :raise content_exceptions.
        """
        if not serial_bios_file_path:
            serial_bios_file_path = self._serial_bios_file_path

        with open(serial_bios_file_path, "r") as serial_log:
            full_serial_log = serial_log.read()
        found = 0
        for string_to_look in passed_error_signature_list_to_parse:
            self._log.info("Looking for [%s]", string_to_look)
            if re.findall(string_to_look, full_serial_log, re.IGNORECASE | re.MULTILINE):
                self._log.debug(" String found")
                found = found + 1
            else:
                self._log.debug(" String Not found")
        if found == len(passed_error_signature_list_to_parse):
            self._log.info("All String found in Serial Log")
        else:
            raise content_exceptions.TestFail("All String not found in Serial Log")
