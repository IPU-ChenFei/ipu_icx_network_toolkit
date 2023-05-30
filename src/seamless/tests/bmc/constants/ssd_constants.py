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


class SsdWindows:
    """
    This class having all the Windows OS Constants
    """
    GET_VM_CMD = r'powershell "Get-VM"'
    CREATE_VM_CMD = r'powershell SeamlessUpdateToolbox.ps1 -createVM -vmname {} -numvms 1 -vmtype "windows" -numvps 2 ' \
          r'-memory "4G" -vhd {} -vmswitch "vSwitch"'
    PHYSIVAL_DISK_CMD = 'powershell "Get-PhysicalDisk"'
    STORAGE_FW_VERSION = 'powershell "(Get-PhysicalDisk)[{}] | Get-StorageFirmwareInformation"'
    C_DRIVE_PATH = r"C:\\Tools\\"
    VM_FOLDER_PATH = r"C:\\VHDs"
    SSD_VM_FOLDER_PATH = r":\\VHDs\\"
    FW_UPDATE_CMD = 'powershell "(Get-PhysicalDisk)[{}] | Update-StorageFirmware -ImagePath {} -SlotNumber {}"'

    CLEAR_DISK_CMD = 'powershell "Get-Disk {} | Clear-Disk -RemoveData -A"'
    INITIALIZE_CMD = 'powershell "Initialize-Disk -Number {}"'
    PARTITION_CMD = r'powershell "New-Partition -DiskNumber {} -UseMaximumSize -DriveLetter {} | Format-Volume ' \
                    r'-FileSystem NTFS -NewFileSystemLabel NewVolume"'
    WMIC_GET_DEVICEID = "wmic diskdrive get caption, deviceid"
    VM_FILE_NAME = "VMPHU.vhdx"
    VM_SEAMLESS_FILE_NAME = "SeamlessUpdate_Linux_Guest.vhdx"
    PARTITION_DRIVE_CHECK = r'''powershell "Get-Partition -DiskNumber {} | Where-Object -FilterScript {{$_.DriveLetter -Eq '{}'}}"'''
    DRIVE_CHECK = r'powershell "Get-Partition -DriveLetter {}"'
    IOMETER_TOOL = "IOMeter.exe"
    EXECUTE_IOMETER_CMD = "IOmeter.exe /c configfile.icf /r result.csv"
    IOMETER_STATUS = r'TASKLIST /FI "IMAGENAME eq  IOmeter.exe"'
    IOMETER_KILL_CMD = r'TASKKILL /IM "IOmeter.exe" /F'
    GET_VM_STATE = r'powershell "Get-VM -name {}*"'
    START_VM_CMD = r'powershell "SeamlessUpdateToolbox.ps1 -startVM -vmname {}*"'
    STOP_VM_CMD = r'powershell "SeamlessUpdateToolbox.ps1 -stopVM -vmname {}*"'


class NvmeConstants:
    """
    This class having all NVME related constants
    """
    NVME_MIN_VERSION = 1.2
    NVME_LIST_CMD = "nvme list"


class ProxyConstants:
    """
    This class having all proxy related constants
    """
    PROXY_STR = r"proxy=http://proxy-chain.intel.com:911"
    EXPORT_HTTP = f"export http_proxy=http://proxy-chain.intel.com:911"
    EXPORT_HTTPS = f"export https_proxy=http://proxy-chain.intel.com:912"
    #UPDATE_YUM_FILE = f'echo {} >> /etc/yum.conf'


class TimeDelay:
    """
    This class having TimeDelay
    """
    VM_STABLE_TIMEOUT = 10
    DELAY_BW_UPDATE_L = 5
    DELAY_BW_UPDATE_U = 120

class LinuxPath:
    """
    This class having LinuxPath
    """
    ROOT_PATH = "/root"
    FIO_TABLE_INDEX = 4


class RandomSeed:
    """
        This class having Seed Value
    """
    SEED_VALUE = 1000
