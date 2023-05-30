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
TIMEOUT = 10
COMMAND_TIMEOUT = 120
p_state_core_frequency = 3000
uncore_frequency = 2200
TIMEOUT_SEC = 2


class PMWindows:
    """
    This class having all the Windows OS Constants
    """
    PTU_CMD = "PTU.exe -ct 1 -mt 3 -b 0 -ts -l 2 -log -logdir {}  -csv"
    EXECUTOR_PATH = "C:\Program Files\Intel\Power Thermal Utility - Server Edition 3.4.0"
    PTU_TOOL_SUT_PATH = r"C:\Tools"
    PTU_TOOL_ZIP_FILE_NAME = "PTU.zip"
    PTU_TOOL_FOLDER_NAME = "PTU"
    PTU_TOOL_FILE_NAME = "Power Thermal Utility - Server Edition 3.4.0.exe"
    PTU_XPPTMEM_FILE = "xpptumem"
    PTU_TOOL_SUT_FOR_INSTALLING = r"C:\Tools\PTU"


class PMLinux:
    """
    This class having all the Linux OS constants
    """
    PTU_CMD = "./ptu -y -ct 4 -mt 3 -b 1 -ts -l 2 -log -logdir . -logname xyz -csv"
    EXECUTOR_PATH = "/root/PTU_Linux"
    PTU_TOOL_SUT_PATH_LINUX = "/root"
    PTU_TOOL_FOLDER_NAME = "PTU_Linux"
    PTU_TOOL_CONTENT = ["ptu_usage.txt", "README.txt", "ptu", "driver", "coremask.sh", "killptu.sh"]
    PTU_TOOL_FILE_NAME = "ptu"
    PTU_CSV_FILE_PATH_SUT = "/root/PTU_Linux"
    KILL_PTU_CMD = "sh killptu.sh"
    PTU_APP_NAME = "./ptu"


class SocwatchWindows:
    """
    This class having all the Windows OS Constants
    """
    SOCWATCH_CMD = "socwatch.exe -m -f sys -o {} -t 600"
    SOCWATCH_EXECUTOR_PATH = r"C:\Tools\socwatch_windows_INTERNAL_v2021.3\64"
    SOCWATCH_TOOL_SUT_PATH = r"C:\Tools"
    SOCWATCH_TOOL_FOLDER_NAME = "socwatch_windows_INTERNAL_v2021.3"
    SOCWATCH_TOOL_CONTENT = ["EULA.txt", "third-party-programs.txt"]
    SOCWATCH_TOOL_NAME = "C:\Socwatch"
    SOCWATCH_TOOL_FOLDER_NAME_WINDOWS = "socwatch"

class SocwatchLinux:
    """
    This class having all the Linux OS Constants
    """
    SOCWATCH_CMD_LINUX = "./socwatch -m -f sys -o {} -t 600"
    SOCWATCH_EXECUTOR_PATH_LINUX = "/root/socwatch"
    SOCWATCH_TOOL_FOLDER_NAME_LINUX = "socwatch"
    SOCWATCH_TOOL_CONTENT_LINUX = ["setup_socwatch_env.sh", "socwatch_chrome_create_install_package.sh",
                                   "third-party-programs.txt", "build_drivers.sh"]
    SOCWATCH_TOOL_SUT_PATH_LINUX = "/root"
    SOCWATCH_CHECKING_FILE_CONTENT_LINUX = "socwatch_chrome_linux_INTERNAL_v2021.3_x86_64"

class SocwatchConstants:
    """
    This class having all the common constants for both OS
    """
    CPU_P_STATE_FREQUENCY = "CPU P-State Average Frequency (excluding CPU idle time)"
    CORE_C_STATE_RESIDENCY_TIME = "Core C-State Summary: Residency (Percentage and Time)"
    RESIDENCY_PERCENT_MATCH = "Residency (%)"
    CORE_FREQUENCY_MIN_VALUE = 800


class CoreCStates:
    """
    Core C-State Constant Variables
    """
    CORE_C_STATE_CC0 = "CC0"
    CORE_C_STATE_CC1 = "CC1"
    CORE_C_STATE_CC6 = "CC6"
    CORE_C_STATE_CC0_CC1 = "CC0+CC1"
