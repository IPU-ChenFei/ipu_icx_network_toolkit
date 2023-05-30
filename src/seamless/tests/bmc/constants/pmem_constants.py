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


class PmemLinux:
    """
    This class having all the Linux OS Constants
    """
    SHOW_DIMM = r'ipmctl show -dimm'
    SHOW_TOPOLOGY = r'ipmctl show -topology'
    SHOW_MEMORYRESOURCES = r'ipmctl show -memoryresources'
    APPDIRECT_CMD = r'ipmctl create -f -goal persistentmemorytype=appdirect'
    UPDATE_FW_CMD = r'ndctl update-firmware all -f {} -A -v'
    UPFATE_FW_DIMM_CMD = r'ndctl update-firmware {} -f {} -A -v'
    ACTIVATE_CMD = r'ndctl activate-firmware ACPI.NFIT --no-idle --force'
    FW_DEBUG_LOG_CMD = r'ipmctl dump -destination {} -dict {} -debug -dimm'
    NLOG_CMD = r"cd {} && ipmctl dump -destination {} -dict nlog_dict.{}.txt -debug -dimm"
    VM_WAIT_TIME = 120
    FILE_PREFIX = "file_prefix"
    KPI_VALUE = 150000
    EZFIO_FILE = "ezfio.py"
    EZFIO_FOLDER = "/root/ezfio-master"
    NAMESPACE_LIST = "ndctl list"
    CREATE_NAMESPACE = "ndctl create-namespace"
    KILL_FIO = "killall fio"
    KILL_EZFIO = "killall ezfio"
    RUNNING_ACTIVITY = "pgrep -l ezfio"
    DELETE_NAMESPACE = "ndctl destroy-namespace all -f"
    HARD_DISK_LIST = "fdisk -l"
    FIO_TOOL_CONTENT = ["combine.py", "COPYING", "ezFIO User Guide.pdf", "ezfio.bat", "ezfio.ps1", "ezfio.py", "original.ods", "original.ods" ]
    TIMEOUT = 30


class PmemWindows:
    """
    This class having all the Linux OS Constants
    """

    CMD = r"{}\nvdimmutil.exe -fwUpdate {} 1 {}"
    CMD1 = r"{}\nvdimmutil.exe -setRuntimeFwActivationArmState all 1"
    CMD2 = r"{}\pmemutil.exe -activateruntimefirmware"
    FW_TOOL_FILES = ["nvdimmutil.exe", "pmemutil.exe", "nvmvalidate.exe"]
    ACTIVATION_TOOLS = "Activation_Tools"
