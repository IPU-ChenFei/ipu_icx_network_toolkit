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
from src.lib.content_configuration import ContentConfiguration
import src.lib.content_exceptions as content_exceptions


class WindowsEventLog(object):
    """
    Utility class to interface with windows event log
    """

    REGISTERED_EVENT_SOURCES = 'wmic PATH Win32_NtEventLogFile Where "LogFileName=\'%s\'" get sources  /format:list'
    EVENT_LOG_WITH_SOURCES = 'powershell.exe "Get-EventLog -LogName %s -Source %s -EntryType Error,Warning| ' \
                             'Format-Table -AutoSize"'
    EVENT_LOG_WITHOUT_SOURCES = 'powershell.exe "Get-EventLog -LogName %s -EntryType Error |' \
                                ' Format-Table -AutoSize"'

    def __init__(self, log_obj, sut_os_obj):
        """
        :param log_obj: log object
        :param sut_os_obj: sut os object
        """
        self._log_obj = log_obj
        self._sut_os_obj = sut_os_obj

        self._common_content_configuration = ContentConfiguration(self._log_obj)
        self._command_timeout = self._common_content_configuration.get_command_timeout()

    def clear_system_event_logs(self):
        """
        This function is used to clear the windows system logs
        :return: None
        :raise: RuntimeError if failed to run powershell command to clear system event logs
        """
        self._log_obj.debug("Clearing system event logs...")
        command_line = "PowerShell Clear-EventLog -LogName System"
        command_result = self._sut_os_obj.execute(command_line, self._command_timeout)
        self._log_obj.debug(command_result.stdout.strip())
        self._log_obj.error(command_result.stderr.strip())
        if command_result.cmd_failed():
            log_error = "Failed to clear the system event log with error code = '{}' and " \
                        "std_error='{}'".format(command_result.return_code, command_result.stderr)
            self._log_obj.error(log_error)
            raise RuntimeError(log_error)

    def clear_hardware_event_logs(self):
        """
        This function is used to clear the Hardware event logs
        :return: None
        :raise: RuntimeError if failed to run powershell command to clear hardware event logs
        """
        self._log_obj.debug("Clearing Hardware event logs...")
        command_line = "PowerShell Clear-EventLog -LogName HardwareEvents"
        command_result = self._sut_os_obj.execute(command_line, self._command_timeout)
        self._log_obj.debug(command_result.stdout.strip())
        self._log_obj.error(command_result.stderr.strip())
        if command_result.cmd_failed():
            log_error = "Failed to clear the hardware event log with error code = '{}' and " \
                        "std_error='{}'".format(command_result.return_code, command_result.stderr)
            self._log_obj.error(log_error)
            raise RuntimeError(log_error)

    def get_registered_event_sources(self, logname):
        """
        This function provides all sources available for that particular log name
        :return: list of sources
        """
        self._log_obj.debug("Getting registered event sources for %s", logname)
        sources = set()
        no_instance = 'No Instance(s) Available'
        command_result = self._sut_os_obj.execute(self.REGISTERED_EVENT_SOURCES % logname, self._command_timeout)
        self._log_obj.debug("CLI CMD output: %s", command_result.stdout.strip())
        self._log_obj.error("CLI CMD Error: %s", command_result.stderr.strip())
        if no_instance.lower() in command_result.stderr.strip().lower():
            return sources
        sources = eval(command_result.stdout.strip().split("=")[-1].strip())
        # removing the log name
        if logname in sources:
            sources.remove(logname)
        return list(sources)

    def get_event_logs(self, logname, sources=[]):
        """
        This function is used to get event logs for the particular log name and source
        :return: Error logs if logged
        """
        self._log_obj.debug("Getting event logs for %s logname and %s sources", logname, sources)
        cmd = self.EVENT_LOG_WITHOUT_SOURCES % logname
        if sources:
            cmd = self.EVENT_LOG_WITH_SOURCES % (logname, ','.join(sources))
        command_result = self._sut_os_obj.execute(cmd, self._command_timeout)
        self._log_obj.debug("CLI CMD output: %s", command_result.stdout.strip())
        self._log_obj.error("CLI CMD Error: %s", command_result.stderr.strip())
        return command_result.stdout.strip()

    def check_windows_mce_logs(self):
        """
        This function is used to check for registered sources and get logs for registered sources
        :return: logs for registered sources
       """
        sources_found = []
        err_logs = []
        mce_logs = ""
        ignore_items = ["OpenSSH SSH Server service", "------", "EntryType Source"]
        # Get Ignore mce error boolean value from content configuration.xml
        ignore_mce_error = self._common_content_configuration.get_ignore_mce_errors_value()
        available_hw_sources = self.get_registered_event_sources("HardwareEvents")
        self._log_obj.debug("Available hardware event sources %s", available_hw_sources)
        if available_hw_sources:
            sources_found.append(True)
            mce_logs = mce_logs + "\n" + self.get_event_logs("HardwareEvents", available_hw_sources)

        available_whea_sources = [log for log in self.get_registered_event_sources("System") if "-WHEA" in log]
        self._log_obj.debug("Available WHEA event sources %s", available_whea_sources)
        if available_whea_sources:
            sources_found.append(True)
            mce_logs = mce_logs + "\n" + self.get_event_logs("System", available_whea_sources)
        if not any(sources_found):
            raise content_exceptions.TestFail("Could not find Windows MCE event sources")
        mce_logs = mce_logs + "\n" + self.get_event_logs("System")
        mce_logs = mce_logs.split('\n')
        for error in mce_logs:
            if not any(item in error for item in ignore_items):
                err_logs.append(error)
        mce_logs = '\n'.join(err_logs)
        if not ignore_mce_error:
            return mce_logs.strip("\r\n\t ")
        else:
            self._log_obj.error("MCE ERRORS:{}\n".format(mce_logs.strip("\r\n\t ")))
            return

    def get_whea_error_event_logs(self):

        """
        This function is used to get whea error and warning logs from windows system event log
        :return: the whea error/warning logs
        :raise: RuntimeError if failed to run powershell command to get whea error logs from system event logs
        """
        whea_logs = None
        command_line = 'powershell.exe "Get-EventLog -LogName System -Source \'Microsoft-Windows-WHEA-Logger\'' \
                       ' -EntryType Error,Warning"'

        command_result = self._sut_os_obj.execute(command_line, self._command_timeout)
        self._log_obj.debug("CLI CMD output: %s", command_result.stdout.strip())
        self._log_obj.error("CLI CMD Error: %s", command_result.stderr.strip())
        if command_result.cmd_failed():
            # powershell command returns non zero value, if no logs found
            self._log_obj.info("WHEA log Not found in the System event logs...")
        elif command_result.return_code == 0:
            whea_logs = command_result.stdout

        return whea_logs

    def clear_application_logs(self):
        """
        This function is used to clear the windows Application log
        :return: None
        :raise: RuntimeError if failed to run powershell command to clear application log
        """
        command_line = "PowerShell Clear-EventLog -LogName Application"
        command_result = self._sut_os_obj.execute(command_line, self._command_timeout)

        if command_result.cmd_failed():
            log_error = "Failed to clear the system event log with error code = '{}' and " \
                        "std_error='{}'".format(command_result.return_code, command_result.stderr)
            self._log_obj.error(log_error)
            raise RuntimeError(log_error)

        self._log_obj.info("The Application log entries are cleared...")

    def get_application_event_error_logs(self, cmd_str):
        """
        This function is used to get error and warning logs from Application log

        :return: the error/warning logs
        :raise: RuntimeError if failed to run powershell command
        """
        application_log = None
        command_line = 'powershell.exe "Get-EventLog -LogName Application {}"'.format(cmd_str)
        command_result = self._sut_os_obj.execute(command_line, self._command_timeout)
        if command_result.cmd_failed():
            # powershell command returns non zero value, if no logs found
            self._log_obj.info("There are no matches found for Application log in the system...")
        elif command_result.return_code == 0:
            application_log = command_result.stdout

        return application_log
