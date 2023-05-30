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
from dtaf_core.lib.dtaf_constants import ProductFamilies
import os


class HostOs:
    """This Class is for Host Operating OS type Attribute"""
    Linux = "Linux"
    Windows = "Windows"


class SysUser:
    """
    Store the test user credentials username and password
    this is quick fix to unbreak existing scripts and not expose
    the password in clear text
    """
    # force key error, ensure the upper CI layers handle
    # setting up of the environment variables.
    USER = os.environ['sys_user']
    PWD = os.environ['sys_pwd']
    ATF = os.environ['atf_api']

    def __init__(self):
        # support ability to read secrets from cred management
        self.user = SysUser.USER
        self.pwd = SysUser.PWD
        self.atf = SysUser.ATF


class ArtifactoryFolderNames:
    """Constant for Artifactory Folders Name"""
    LINUX = "Linux"
    Windows = "Windows"
    ESXI = "ESXi"
    UEFI = "Uefi"


class Artifactory:
    """Constant for Artifactory"""

    Artifactory_Path = {
        ArtifactoryFolderNames.LINUX: "Automation_Tools/{}/Linux/{}",
        ArtifactoryFolderNames.Windows: "Automation_Tools/{}/Windows/{}",
        ArtifactoryFolderNames.UEFI: "Automation_Tools/{}/Uefi/{}",
        ArtifactoryFolderNames.ESXI: "Automation_Tools/{}/Esxi/{}"
    }

    Host_Tool_Path = {
        HostOs.Windows: {
            ArtifactoryFolderNames.LINUX: "C:\\Automation\\Tools\\{}\\Linux\\",
            # eg. C:\\Automation\\Tools\\SPR\\Linux\\solar.zip
            ArtifactoryFolderNames.Windows: "C:\\Automation\\Tools\\{}\\Windows\\",
            ArtifactoryFolderNames.ESXI: "C:\\Automation\\Tools\\{}\\Esxi\\",
            ArtifactoryFolderNames.UEFI: "C:\\Automation\\Tools\\{}\\Uefi\\"
        },
        HostOs.Linux: {
            ArtifactoryFolderNames.LINUX: "/opt/Automation/Tools/{}/Linux/{}",
            # eg. /opt/Automation/Tools/SPR/Linux/solar.zip
            ArtifactoryFolderNames.Windows: "/opt/Automation/Tools/{}/Windows/{}",
            ArtifactoryFolderNames.ESXI: "/opt/Automation/Tools/{}/Esxi/{}",
            ArtifactoryFolderNames.UEFI: "/opt/Automation/Tools/{}/Uefi/{}"
        }
    }
    CURL_CMD = f"curl -f -u {SysUser.USER}:{SysUser.PWD} "
    DOWNLOADING_CMD = CURL_CMD + r" -X GET https://ubit-artifactory-ba.intel.com/artifactory/list/dcg-dea-srvplat-local/{} --output {}"


class ArtifactoryTools:
    PRIME95_ZIP_FILE = "PRIME95_ZIP_FILE"
    SVM_ZIP_FILE = "SVM_ZIP_FILE"
    STRESS_NG = "STRESS_NG"
    PM_UTILITY = "PM_UTILITY"
    PLATFORM_STRESS_CYCLER_LINUX = "PLATFORM_STRESS_CYCLER_LINUX"
    FIO = "FIO"
    MLC_FOLDER_NAME = "MLC_FOLDER_NAME"
    SEL_VIEWER = "SEL_VIEWER"
    MEM_REBOOTER = "MEM_REBOOTER"
    PLATFORM_CYCLER = "PLATFORM_CYCLER"
    PLATFORM_STRESS_CYCLER_WINDOWS = "PLATFORM_STRESS_CYCLER_WINDOWS"
    FIO_MSI_INSTALLER = "FIO_MSI_INSTALLER"
    INTEL_OPTANE_PMEM_MGMT_FILE_NAME = "INTEL_OPTANE_PMEM_MGMT_FILE_NAME"
    PLATFORM_STRESS_LINUX_FILE = "PLATFORM_STRESS_LINUX_FILE"
    STRESS_MPRIME_LINUX_FILE = "STRESS_MPRIME_LINUX_FILE"
    STRESS_CV_CLI_LINUX_FILE = "STRESS_CV_CLI_LINUX_FILE"
    MLC_INSTALLER = "MLC_INSTALLER"
    MLC_INTERNAL_INSTALLER = "MLC_INTERNAL_INSTALLER"
    MLC_EXE_INSTALLER = "MLC_EXE_INSTALLER"
    RAS_TOOLS_PATH = "RAS_TOOLS_PATH"
    NTTTCP_LINUX_ZIP_FILE = "ntttcp_linux_zip_file"
    DISK_SPD_ZIP_FILE = "disk_spd_zip_file"
    DISK_SPD_LINUX_ZIP_FILE = "disk_spd_linux_zip_file"
    STREAM_WIN_FILE = "STREAM_WIN_FILE"
    STREAM_LINUX_FILE = "STREAM_LINUX_FILE"
    MCE_LOG_CONFIG_FILE_NAME = "mcelog_conf_file_name"
    DCPMM_PLATFORM_CYCLER_FILE = "DCPMM_PLATFORM_CYCLER_FILE"
    STREAM_ZIP_FILE = "STREAM_ZIP_FILE"
    DPDK_FILE_NAME = "dpdk_file_name"
    XMLCLI_ZIP_FILE = "XMLCLI_ZIP_FILE"
    RDT_FILE_NAME = "rdt_file_name"
    QAT_FILE_NAME = "qat_file_name"
    SMART_CTL = "smartctl_win32_setup.exe"
    IWVSS_EXE_INSTALLER = "IWVSS_EXE_INSTALLER"
    TURBOSTAT_TOOL_NAME = "TURBOSTAT_TOOL_NAME"
    SW_TRACE_C_FILENAME = "sw_trace_c_filename"
    SOCWATCH_ZIP_FILE = "socwatch_zip_file"
    RUNNER_HOST_FOLDER_NAME = "RUNNER_HOST_FOLDER_NAME"
    SCP_GO_LINUX_FILE = "SCP_GO_LINUX_FILE"
    SCP_GO_WINDOWS_FILE = "SCP_GO_WINDOWS_FILE"
    FIO_ZIP_FILE = "fio_zip_file"
    SOLAR_HOST_FOLDER_NAME = "SOLAR_HOST_FOLDER_NAME"
    ACPICA_TAR_FILE_NAME = "acpica_tar_file_name"
    CYCLING_HOST_FOLDER_NAME = "CYCLING_HOST_FOLDER_NAME"
    PLATFORM_STRESS_CYCLER_WINDOWS_FILE = "PLATFORM_STRESS_CYCLER_WINDOWS_FILE"
    RAS_RUNNER_TOOL_NAME = "RAS_RUNNER_TOOL_NAME"
    MULTICHASE_TOOL_FILE = "MULTICHASE_TOOL_FILE"
    KVM_UNIT_TEST_FILE = "KVM_UNIT_TEST_FILE"
    SMM_UPDATE_ZIP = "SMM_UPDATE_ZIP"
    TEST_REPO = "TEST_REPO"
    WIN_KICKSTART_ISO_LINUX_FILE = "WIN_KICKSTART_ISO_LINUX_FILE"
    INTEL_LAN_V26_4 = "intel_lan_v26"
    CORE_INFO = "CORE_INFO"
    CTG_EXE_INSTALLER = "CTG_EXE_INSTALLER"
    CTG_LIB = "CTG_LIB_PACKAGE"
    VROC_ZIP_FILE = "VROC_ZIP_FILE"
    TESTER_TOOL = "tester"
    MLC_EXE_NEW = "mlc_new_win"
    PTG = "ptg"

class ArtifactoryName:
    """
    Example:
        1. DictLinuxTools["Sut_Folder_Name]="Zip_File_name"
        2. DictLinuxTools["prime95"]="prime95.tar.gz"

        3. DictWindowsTools["prime95"]="prime95.zip"
    """
    DictLinuxTools = {
        ArtifactoryTools.STRESS_MPRIME_LINUX_FILE: "prime95.tar.gz",
        ArtifactoryTools.STRESS_CV_CLI_LINUX_FILE: "CXL_CV_APP_07.tar.gz",
        ArtifactoryTools.STRESS_NG: "stress-ng-0.12.04.tar.xz",
        ArtifactoryTools.PM_UTILITY: "pm_utility-master.zip",
        ArtifactoryTools.PLATFORM_CYCLER: "platform_cycler_linux.tgz",
        ArtifactoryTools.FIO: "fio-master.zip",
        ArtifactoryTools.PLATFORM_STRESS_LINUX_FILE: "stressapptest",
        ArtifactoryTools.MLC_INSTALLER: "mlc_v3.9a.tgz",
        ArtifactoryTools.RAS_TOOLS_PATH: "ras_tools.tar",
        ArtifactoryTools.MLC_INTERNAL_INSTALLER: "mlc_v3.9a_internal.tgz",
        ArtifactoryTools.NTTTCP_LINUX_ZIP_FILE: "ntttcp-for-linux-master.zip",
        ArtifactoryTools.DISK_SPD_LINUX_ZIP_FILE: "diskspd-for-linux-master.zip",
        ArtifactoryTools.STREAM_LINUX_FILE: "stream.tgz",
        ArtifactoryTools.MCE_LOG_CONFIG_FILE_NAME: "mcelog.conf",
        ArtifactoryTools.DCPMM_PLATFORM_CYCLER_FILE: "dcpmm_platform_cycler_linux.tgz",
        ArtifactoryTools.STREAM_ZIP_FILE: "stream.zip",
        ArtifactoryTools.DPDK_FILE_NAME: "dpdk-19.08.tar.xz",
        ArtifactoryTools.XMLCLI_ZIP_FILE: "xmlcli_1_2_15.zip",
        ArtifactoryTools.RDT_FILE_NAME: "eaglestream-bkc-rdt-4.1.0_v2.zip",
        ArtifactoryTools.QAT_FILE_NAME: "QAT20.L.0.5.1-00003.tar.gz",
        ArtifactoryTools.TURBOSTAT_TOOL_NAME: "turbostat.tar.gz",
        ArtifactoryTools.SW_TRACE_C_FILENAME: "sw_trace_notifier_provider.c",
        ArtifactoryTools.SOCWATCH_ZIP_FILE: "socwatch_chrome_linux_INTERNAL_v2021.1.1_x86_64.tar.gz",
        ArtifactoryTools.RUNNER_HOST_FOLDER_NAME: "validation_runner.zip",
        ArtifactoryTools.SCP_GO_LINUX_FILE: "go_scp",
        ArtifactoryTools.FIO_ZIP_FILE: "fio-master.zip",
        ArtifactoryTools.SOLAR_HOST_FOLDER_NAME: "Solar.tar.gz",
        ArtifactoryTools.ACPICA_TAR_FILE_NAME: "acpica-unix.tar.gz",
        ArtifactoryTools.CYCLING_HOST_FOLDER_NAME: "LinuxCycling.zip",
        ArtifactoryTools.PLATFORM_STRESS_CYCLER_LINUX: "platform_cycler_linux.tgz",
        ArtifactoryTools.PLATFORM_STRESS_CYCLER_WINDOWS_FILE: "platform_cycler_windows.zip",
        ArtifactoryTools.RAS_RUNNER_TOOL_NAME: "runner.zip",
        ArtifactoryTools.MULTICHASE_TOOL_FILE: "multichase-master.zip",
        ArtifactoryTools.KVM_UNIT_TEST_FILE:"kvm-unit-tests-master.tar",
        ArtifactoryTools.SMM_UPDATE_ZIP: "smm_update.zip",
        ArtifactoryTools.TEST_REPO: "test.repo",
        ArtifactoryTools.WIN_KICKSTART_ISO_LINUX_FILE: "win_kickstart_iso.iso",
        ArtifactoryTools.INTEL_LAN_V26_4: "intel_lan_v26.zip",
        ArtifactoryTools.CTG_EXE_INSTALLER: "ctg-master.zip",
        ArtifactoryTools.CTG_LIB: "ctg_lib.zip",
        ArtifactoryTools.TESTER_TOOL: "tester",
        ArtifactoryTools.PTG: "PTG-BKM.zip",
    }
    DictWindowsTools = {
        ArtifactoryTools.PRIME95_ZIP_FILE: "prime95.zip",
        ArtifactoryTools.SVM_ZIP_FILE: "GFX_nVidia_SVM.zip",
        ArtifactoryTools.SEL_VIEWER: "SELViewer.zip",
        ArtifactoryTools.MEM_REBOOTER: "mem_rebooter_installer_win-20190206.zip",
        ArtifactoryTools.PLATFORM_CYCLER: "platform_cycler_win-20191115.zip",
        ArtifactoryTools.PLATFORM_STRESS_CYCLER_WINDOWS: "platform_cycler_windows.zip",
        ArtifactoryTools.INTEL_OPTANE_PMEM_MGMT_FILE_NAME: "cr_mgmt_03.00.00.0329_centos_8.2.zip",
        ArtifactoryTools.FIO_MSI_INSTALLER: "fio-3.9-x64.zip",
        ArtifactoryTools.MLC_EXE_INSTALLER: "mlc_v3.8.tgz",
        ArtifactoryTools.DISK_SPD_ZIP_FILE: "diskspd.zip",
        ArtifactoryTools.STREAM_WIN_FILE: "Stream_MP.zip",
        ArtifactoryTools.XMLCLI_ZIP_FILE: "xmlcli_1_2_15.zip",
        ArtifactoryTools.SMART_CTL: "smartctl_win32_setup.exe",
        ArtifactoryTools.IWVSS_EXE_INSTALLER: "iwVSS_2_8_3.zip",
        ArtifactoryTools.SCP_GO_WINDOWS_FILE: "go_scp.exe",
        ArtifactoryTools.CORE_INFO: "Coreinfo.exe",
        ArtifactoryTools.MLC_EXE_NEW: "mlc_new_win.zip"

    }
    DictUEFITools = {
        ArtifactoryTools.VROC_ZIP_FILE: "vroc_uefi_egs.zip"
    }
