"""
!/usr/bin/env python
################################################################################
INTEL CONFIDENTIAL
Copyright Intel Corporation All Rights Reserved.

The source code contained or described herein and all documents related to
the source code ("Material") are owned by Intel Corporation or its suppliers
or licensors. Title to the Material remains with Intel Corporation or its
suppliers and licensors. The Material may contain trade secrets and proprietary
and confidential information of Intel Corporation and its suppliers and
licensors, and is protected by worldwide copyright and trade secret laws and
treaty provisions. No part of the Material may be used, copied, reproduced,
modified, published, uploaded, posted, transmitted, distributed, or disclosed
in any way without Intel's prior express written permission.

No license under any patent, copyright, trade secret or other intellectual
property right is granted to or conferred upon you by disclosure or delivery
of the Materials, either expressly, by implication, inducement, estoppel or
otherwise. Any license under such intellectual property rights must be express
and approved by Intel in writing.
#################################################################################
"""


class RasWindows:
    """
    This class contains all RAS Constants for windows os
    """
    WHEAHCT_TOOL_HOST_PATH = r"C:\Automation\tools\WHEAHCT_Tool.zip"
    WHEAHCT_TOOL_SUT_PATH_WINDOWS = r"c:\tools"
    WHEAHCT_TOOL_ZIP_FILE_NAME = "WHEAHCT_Tool.zip"
    WHEAHCT_TOOL_FOLDER_NAME = "WHEAHCT_Tool"
    WHEAHCT_TOOL_CONTENT = ["cap.txt", "Clear_whea_evts.cmd", "dumprec.exe", "installPlugin.bat", "memce.cmd",
                            "memuce.cmd", "plugin.sys", "whea.vbs", "wheahct.exe", "WHEAHCT.wtl",
                            "wheahct_help.txt", "WTTlog.dll"]
    WHEAHCT_TOOL_FILE_NAME = "wheahct.exe"
    ERR_INJ_CMD_NON_FATAL = "/err 16 /param1 2 /param2 0x1000000 /param3 0x40 /param4 0"
    ERR_INJ_CMD_FATAL = "/err 32 /param1 2 /param2 0x1000000 /param3 0x40 /param4 0"
    CRT_ERR_INJ_CMD = "/err 8 /param1 2 /param2 0x1000000 /param3 0x40 /param4 0"
    UNCRT_ERR_INJ_CMD = "/err 32 /param1 2 /param2 0x1000000 /param3 0x40 /param4 0"
    ERROR_MESSAGE = ["hardware error", "Component: Memory", "PhysicalAddress: 0x1000000"]
    WINDOWS_WHEA_LOG = "Windows whea"


class RasLinux:
    """
    This class contains all RAS constants for Linux os
    """
    ERR_INJ_NON_FATAL_CMD_LINUX = ["cd /sys/kernel/debug/apei/einj",
                                   "echo 0x000040002000 > param1",
                                   "echo 0xfffffffffffff000 > param2",
                                   "echo 0x10 > error_type",
                                   "echo 0 > notrigger",
                                   "echo 1 > error_inject"]
    ERR_INJ_FATAL_CMD_LINUX = ["cd /sys/kernel/debug/apei/einj",
                               "echo 0x000040003000 > param1",
                               "echo 0xfffffffffffff000 > param2",
                               "echo 0x20 > error_type",
                               "echo 0 > notrigger",
                               "echo 1 > error_inject"]
    CRT_ERR_INJ_CMD_LINUX = ["cd /sys/kernel/debug/apei/einj",
                             "echo 0x000040001000 > param1",
                             "echo 0xfffffffffffff000 > param2",
                             "echo 0x8 > error_type",
                             "echo 0> notrigger",
                             "echo 1 > error_inject"]
    LINUX_ERROR_LOG = "dmesg"
    UNCORRECT_NON_FATAL_ERR_LIN = ["Hardware Error", "uncorrected",
                                   "physical_address: 0x0000000040002000"]
    UNCORRECT_FATAL_ERR_LIN = ["Hardware Error", "uncorrected",
                               "physical_address: 0x0000000040003000"]
    CORRECT_ERR_LIN = ["Hardware Error", "uncorrected",
                       "physical_address: 0x0000000040001000"]


class RasConstants:
    """
    This class contains Common RAS Constants for both OS
    """
    TIME_OUT_SEC = 2
    TIMEOUT_SEC = 1
    TIMEOUT = 5
    COMMAND_TIMEOUT_SEC = 30








