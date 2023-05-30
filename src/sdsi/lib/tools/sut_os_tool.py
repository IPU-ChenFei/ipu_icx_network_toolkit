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
"""Tool which provides functionality to interact with SUT Operating System.

    Typical usage example:
        self._sut_os_tool.perform_reboot()
        cpu_info_list = self._sut_os_tool.execute_cmd("lscpu").strip().split("\n")
"""
from logging import Logger

from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.lib.exceptions import OsCommandException
from dtaf_core.lib.os_lib import OsCommandResult
from dtaf_core.providers.sut_os_provider import SutOsProvider

class SutOsTool:
    """Class to perform SUT OS operations."""

    def __init__(self, log: Logger, sut_os: SutOsProvider) -> None:
        """Initialize the SutOsTool.

        Args:
            log: logger to use for test logging.
            sut_os: OS provider used for test content to interact with SUT.
        """
        self._log = log
        self._os = sut_os

    def execute_cmd(self, command: str, path: str = '', timeout: int = 1200) -> str:
        """Execute a command on the SUT

        Args:
            command: The command to execute on the SUT
            path: The SUT path to execute the command
            timeout: The number of seconds to wait before timing out.

        Return:
            str: The stdout result of the os command.

        Raise:
            OsCommandException: If the command fails.
        """
        res: OsCommandResult = self._os.execute(command, timeout, path) if path else self._os.execute(command, timeout)

        if res.cmd_failed():
            error_msg = f"Failed to run '{command}' with status code:'{res.return_code}' and stderr:'{res.stderr}'"
            self._log.error(error_msg)
            raise OsCommandException(error_msg)
        return str(res.stdout)

    def wait_for_os(self, timeout: int = 1800) -> None:
        """Sleep until the OS can be reached

        Args:
            timeout: The number of seconds to wait before timing out.
        """
        self._os.wait_for_os(timeout)

    def perform_reboot(self, timeout: int = 1800) -> None:
        """Perform an OS reboot

        Args:
            timeout: The number of seconds to wait before timing out.
        """
        self._os.reboot(timeout)

    def copy_local_file_to_sut(self, host_path: str, sut_path: str) -> None:
        """Copy files from the host to the SUT.

        Args:
            host_path: The path of the file on the host to transfer.
            sut_path: The directory on the SUT to transfer the file to.
        """
        self._os.copy_local_file_to_sut(host_path, sut_path)

    def clear_os_error_logs(self) -> None:
        """Copy OS error logs from the SUT."""
        self._log.info("Clearing of OS Logs Initiated ...")
        if OperatingSystems.LINUX in self._os.os_type:
            clear_cmds = [r"sudo dmesg --clear",
                          r"sudo chmod 777 /var/log/messages",
                          r"sudo echo \"\" > /var/log/messages",
                          r"sudo find /var/log/journal -type f -name *.journal* -exec rm  {} \;"]
            [self.execute_cmd(cmd) for cmd in clear_cmds]
        elif OperatingSystems.WINDOWS in self._os.os_type:
            self.execute_cmd("PowerShell Clear-EventLog -LogName System")
        else:
            self._log.warning(f'Unsupported OS: {self._os.os_type}, failed to clear os logs.')
            return
        self._log.info("OS Logs are Cleared Successfully")
