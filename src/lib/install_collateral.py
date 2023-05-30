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

import os
import subprocess
import sys
import six
import time
import threading
import re
from shutil import copy
import shutil

import platform

from dtaf_core.lib.exceptions import OsCommandException, OsCommandTimeoutException
# from importlib_metadata import FileNotFoundError

from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import ProductFamilies
from dtaf_core.lib.os_lib import LinuxDistributions

from src.lib.common_content_lib import CommonContentLib
from src.lib.content_artifactory_utils import ContentArtifactoryUtils
from src.lib.content_configuration import ContentConfiguration
from src.lib.dtaf_content_constants import BonnieTool, LttsmToolConstant, CcbPackageConstants, RasPcieAer, \
    PcmToolConstants, PcmMemoryConstants

from src.lib import content_exceptions
from src.lib.dtaf_content_constants import TurboStatConstants, RDTConstants, VROCConstants, RasRunnerToolConstant
from src.lib.dtaf_content_constants import CommonConstants
from src.lib.dtaf_content_constants import SolarHwpConstants
from src.lib.dtaf_content_constants import AcpicaToolConstants
from src.lib.dtaf_content_constants import LinuxCyclingToolConstant, DriverCycleToolConstant
from src.lib.dtaf_content_constants import IntelSsdDcToolConstants, LinPackToolConstant

from src.lib.dtaf_content_constants import WindowsMemrwToolConstant, StressCrunchTool, StressMprimeTool,\
    StressLibquantumTool
from src.lib.dtaf_content_constants import BurnInConstants, SgxHydraToolConstants

from src.lib.dtaf_content_constants import DynamoToolConstants, IOmeterToolConstants, TimeConstants

from src.lib.os_lib import WindowsCommonLib
from src.collaterals.collateral_constants import CollateralConstants
from src.lib.dtaf_content_constants import PTUToolConstants
from src.lib.tools_constants import ArtifactoryName, ArtifactoryTools
from src.lib.grub_util import GrubUtil

if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path


class InstallCollateral(object):
    """
        This class implements installation of all tools which can be used across all test cases.
    """
    platform_stress_constants = {
        "PLATFORM_STRESS_CYCLER_LINUX_FILE": "platform_cycler_linux.tgz",
        "PLATFORM_STRESS_CYCLER_WINDOWS_FILE": "platform_cycler_windows.zip",
        "PLATFORM_STRESS_LINUX_FILE": "stressapptest"
    }

    platform_cycler_constants = {
        "PLATFORM_CYCLER_FOLDER_NAME": "platform_cycler",
        "PLATFORM_CYCLER_EXTRACT_FOLDER_NAME": "platform_cycler_linux_installer",

        "WINDOWS_PLATFORM_CYCLER_LOG_FOLDER": r"platform_cycler\logs",
        "WINDOWS_PLATFORM_CYCLER_FOLDER": "platform_cycler_win",
        "WINDOWS_PLATFORM_CYCLER_ZIP_FILE": "platform_cycler_win-20191115.zip",

        "LINUX_PLATFORM_CYCLER_LOG_FOLDER": "/platform_rebooter/",
        "LINUX_PLATFORM_DC_CYCLER_LOG_PATH": "/platform_dc_graceful/logs/",
        "LINUX_PLATFORM_REBOOTER_LOG_PATH": "/platform_rebooter/logs/"
    }

    prime_tool_constants = {
        "PRIME95_ZIP_FILE": "prime95.zip",
        "MPRIME_FOLDER_NAME": "Prime95",
        "STRESS_MPRIME_LINUX_FILE": "prime95.tar.gz"
    }

    util_constants = {
        "COLLATERAL_DIR_NAME": 'collateral',
        "LINUX_USR_SBIN_PATH": "/usr/sbin",
        "SEL_ZIP_FILE": "SELViewer.zip",
        "WINDOWS_MEM_REBOOTER_ZIP_FILE": "mem_rebooter_installer_win-20190206.zip",
        "LINUX_USR_ROOT_PATH": "/root",
        "LINUX_VAR_LIB_IMG_PATH": "/var/lib/libvirt/images"
    }

    ipmctl_constants = {"LINUX_USR_ROOT_PATH": "/root", "IPMCTL_USR_BIN_PATH": "/usr/bin/ipmctl"}

    fio_constants = {
        "FIO_MSI_INSTALLER": "fio-3.9-x64.zip"
    }

    mlc_constants = {"MLC_INSTALLER": "mlc.tgz", "MLC_EXE_INSTALLER": "mlc_v3.8.tgz", "MLC_FOLDER_NAME": "MLC"}

    disk_spd_constants = {"disk_spd_zip_file": "diskspd.zip", "disk_spd_linux_zip_file": "diskspd-for-linux-master.zip"}

    ntttcp_constants = {"ntttcp_linux_zip_file": "ntttcp-for-linux-master.zip"}

    stressng_constants = {"STRESSNG_LINUX_FILE": "stress-ng-0.12.04.tar.xz",
                          "STRESSNG_FOLDER_NAME": "stress-ng-0.12.04"}

    stream_constants = {"STREAM_LINUX_FILE": "stream.tgz", "STREAM_FOLDER_NAME": "stream",
                        "STREAM_WIN_FILE": "Stream_MP.zip"}
    stream_zip_constants = {"STREAM_ZIP_FILE": "stream.zip", "stream_omp_NTW_FILE": "stream_omp_NTW",
                            "stream_omp_RFO_FILE": "stream_omp_RFO", "STREAM_FOLDER_NAME": "stream"}

    pmutils_constants = {"PMUTILS_LINUX_FILE": "pm_utility-master.zip", "PMUTILS_LINUX_FOLDER": "pm_utility-master"}

    TOLERANT_FILE = "update_linux_tolerant.py"

    pnpwls = {"pnp_workload": "pnpwls-master.tar.gz", "stream_folder_name": "stream"}

    platform_cycler_extract_path = None
    mlc_extract_path = None

    ras_tool_constants = {
        "RAS_TOOLS_PATH": "ras_tools.tar",
        "RAS_TOOLS_FOLDER_NAME": "ras_tools"
    }

    MCELOG_CONSTANTS = {
        "mcelog_conf_file_name": "mcelog.conf"
    }
    FIO_CONSTANTS = {"fio_zip_file": "fio-master.zip", "fio_folder_name": "fio-master"}
    MESH_CONSTANTS = {"mesh_zip_file": "dm_xprod.zip", "mesh_folder_name": "dm_xprod"}
    DOCKER_REPO = "https://download.docker.com/linux/centos/docker-ce.repo"
    CPANM_MODULE = "Data::Validate::IP Net::OpenSSH Net::Ping IO::Pty"

    dcpmm_platform_cycler_constant = {"DCPMM_PLATFORM_CYCLER_FILE": "dcpmm_platform_cycler_linux.tgz"}
    PERTHREAD_FILE_NAME = "gen_perthreadfile.sh"
    BURNIN_FILE_ZIP = "burnintest.zip"
    BURNIN_FILE_ZIP_WIN = "burnintest_win.zip"
    BURNIN_DIR_SUT = "Burnintest"
    dpdk_properties = {
        "DPDK_FOLDER_PATH": "/usr/src",
        "DPDK_FOLDER_NAME": "DPDK"
    }
    vm_create_thread_list = []
    DPDK_PATCH_NAME = "dpdk_dlb_v20.11_200b584_diff.patch"
    SUCCESS_DPDK_INSTALL = "Installation in dpdk-install/ complete"

    itp_xmlcli_constants = {"XMLCLI_ZIP_FILE": "xmlcli_1_2_15.zip", "XMLCLI_FOLDER_NAME": "xmlcli_1_2_15"}

    ILVSS_CONSTANTS = {"VSS_FILE": "VSS.zip", "OPT_PATH": "/opt", "OPT_IVLSS": "/opt/ilvss.0"}

    CPUID_CONSTANTS = {"CPUID_ZIP_FILE": "CPUID.zip", "CPUID_FOLDER_NAME": "CPUID"}

    rdt_stress_constants = {"STRESS_DIR": "STRESS", "STRESS_TAR_FILE": "stress-1.0.4.tar.gz"}

    RDT_FOLDER = "RDT"
    C_DRIVE_PATH = "C:\\"
    SMART_CTL = r"smartctl.exe"
    IWVSS_CONSTANTS = {"IWVSS_SUT_FOLDER_NAME": "iwVSS"}
    IOMETER_CONSTANTS = {"IOMETER_SUT_FOLDER_NAME": "iometer"}

    RUNNER_SUT_FOLDER_NAME = "runner"
    RUNNER_HOST_FOLDER_NAME = "validation_runner.zip"
    SCP_GO_LINUX_FILE = "go_scp"
    SCP_GO_WINDOWS_FILE = "go_scp.exe"

    DOWNLOAD_PIP = "wget https://bootstrap.pypa.io/get-pip.py --no-check-certificate"
    OPT = "/opt"
    RAS_RUNNER_HOST_FOLDER_NAME = "runner.zip"
    RAS_RUNNER_SUT_FOLDER_NAME = "runner"
    RAS_RUNNER_FOLDER_INSTALLATION_PATH = "/runner"

    dmidecode_constants = {
        "DMIDECODE_EXE_INSTALLER": "dmidecode.zip", "DMIDECODE_MASTER_LINUX": "dmidecode-master.zip"}
    DMIDECODE_WINDOWS_INSTALLED_PATH = r"C:\\dmidecode"
    SEMT_CONSTANTS = {
        "SEMT_FOLDER_NAME": "semt_ver0.3a.tgz"
    }

    STREAM_APP_CONSTANT_WINDOWS = {
        "STREAM_APP_CONSTANT_WINDOWS": "ACORE-StreamApp_Arr_40M_SGX.zip"
    }
    MSR_TOOLS_PATH = "msr-tools-1.3-12.el8.x86_64.rpm"
    MSR_TOOLS_INSTALLATION_CMD = "echo y | yum install msr-tools*"

    CCBSDK_WINDOWS_FILE = r"IntelCCBSDK_Internal.exe"
    CCBHWAPI_WINDOWS_FILE = r"ccbhwapi-1.0.0.5-py2-none-any.whl"
    USBTREEVIEW = "UsbTreeView"
    USBTREEVIEW_ZIP_FILE = "usbtreeview.zip"
    DEVCON_FILE = "devcon.exe"
    WINDOWS_USER_ADMIN_PATH = r"C:\Users\Administrator"
    REGX_LIB_IPMCTL = "libipmctl\d+-\d+.\d+.\d+.\d+-\d+\.el\d+.x86_64.rpm"
    DEFAULT_DIRECTORY_ESXI = "/vmfs/volumes/datastore1"
    REGX_IPMCTL = "ipmctl-\d.*"
    ROOT_PATH = "/root"
    MAKE = "make"
    MAKE_INSTALL = "make install"
    IO_PORT = "ioport-1.2-22.fc33.x86_64.rpm"
    IO_PORT_ZIP_FILE = "ioport.zip"
    PCIERRPOLL_TAR_FILE = "PCIERRPOLL.tar"
    PCIERRPOLL_FILE = "PCIERRpoll"
    IPMCTL_VERSION_COMMAND = "ipmctl version"
    DMA_TEST_SCRIPT = "dma_test.sh"
    IPERF_FOLDER_PATH = "C:\\Iperf"
    BURNIN_TOOL_SUT_ZIP_PATH = "C:\\burnintest.zip"
    BURNIN_TOOL_FOLDER_PATH = "C:\\burnin_tool"


    WIN_KICKSTART_ISO_LINUX_FILE_NAME = "win_kickstart_iso.iso"

    EMBARGO_REPO = "/etc/yum.repos.d/Intel-Embargo.repo"

    SCREEN_ZIP_NAME = "screen.zip"
    SCREEN_RPM_NAME = "screen-4.1.0-0.25.20120314git3c2946.el7.x86_64.rpm"
    VC_REDIST_EXE_FILE_NAME = "VC_redist.x64.exe"
    IPERF_TOOL = "iperf3-3.1.3.rpm"
    IPERF_TOOL_ESXI = "iperf-2.0.5-1-offline_bundle.zip"
    IPERF_TOOL_INSTALLATION_CMD = "echo y | yum install {}".format(IPERF_TOOL)
    IPERF_TOOL_INSTALLATION_CMD_ESXI = "esxcli software component apply -d vmfs/volumes/datastore1/{} --no-sig-check".format(IPERF_TOOL_ESXI)
    # IPERF_TOOL_INSTALLATION_CMD_ESXI = "esxcli software component apply -d /vmfs/volumes/datastore1/iperf-2.0.5-1-offline_bundle.zip --no-sig-check"
    IPERF_TOOL_INSTALLATION_CMD_RPM = "rpm -ivh {}".format(IPERF_TOOL)
    IPERF_TOOL_WINDOWS = "iperf-3.1.3-win64.zip"
    ROOT = "/root"
    LDB_TRAFFIC_FILE_CMD = r"ldb_traffic -n 1024 -w poll"
    LDB_REGEX_TX = r"Sent\s(\d+)\sevents"
    LDB_REGEX_RX = r"Received\s(\d+)\sevents"
    MAXKEYASSIGNMENTMKTME = {
        "MKTMEKEYASSIGNMENTMAXZIPFILE": "mktmekeyassignmentmax.zip"
        }
    SGXHYDRAEXFIRST = {
        "SGXHYDRAEXFIRSTZIPFILE": "SGXHydraEx-FIRST.zip",
        "Hydradllfiles": ["msvcp140.dll", "vcruntime140.dll", "vcruntime140_1.dll"]
        }
    DMSETOOL_PATH = "dmsetool.rpm"
    DMSE_TOOLS_INSTALLATION_CMD = "echo y | yum install dmsetool*"
    CENTOS_STREAM = "CentOS Stream"
    CXL_CV_CLI_FOLDER_PATH = "cxl_cv-0.1.0-Linux"
    CXL_CV_CLI_FILE_NAME = "CXL_CV_APP_07.tar.gz"
    WINDOWS_SYSTEM32 = "%SystemRoot%\system32"

    def __init__(self, log, os_obj, cfg_opts):
        self._log = log
        self._os = os_obj
        self.sut_os = self._os.os_type
        self._cfg = cfg_opts
        self._common_content_lib = CommonContentLib(self._log, self._os, self._cfg)
        self._common_content_configuration = ContentConfiguration(self._log)

        self._command_timeout = self._common_content_configuration.get_command_timeout()
        self._os_time_out_in_sec = self._common_content_configuration.os_full_ac_cycle_time_out()
        self._reboot_time_out = self._common_content_configuration.get_reboot_timeout()
        self.sut_ras_tools_path = None
        self.sut_viral_injector_path = None
        self.dpdk_file_path = self._common_content_configuration.get_dpdk_file()
        self.dpdk_file_name = os.path.split(self.dpdk_file_path)[-1].strip()
        self.dpdk_patch_file_name = self._common_content_configuration.get_dpdk_patch_file()
        self.kernel_dsa_rpm_file_name = self._common_content_configuration.get_kernel_dsa_rpm_file()
        self.rdt_file_path = self._common_content_configuration.get_rdt_file()
        self.kernel_rpm_file_name = self._common_content_configuration.get_kernel_rpm_file()
        self.vm_kernel_rpm_file_name = self._common_content_configuration.get_vm_kernel_rpm_file()
        self.qat_file_path = self._common_content_configuration.get_qat_file()
        self.vm_qat_file_path = self._common_content_configuration.get_vm_qat_file()
        self.vm_hqm_file_path = self._common_content_configuration.get_vm_hqm_file()
        self.vm_dpdk_file_path = self._common_content_configuration.get_vm_dpdk_file()
        self.vm_dpdk_file_name = os.path.split(self.vm_dpdk_file_path)[-1].strip()
        self.vm_dpdk_patch_file_name = self._common_content_configuration.get_vm_dpdk_patch_file()
        self.vm_kernel_dsa_rpm_file_name = self._common_content_configuration.get_vm_kernel_dsa_rpm_file()
        self.qat_file_path_esxi = self._common_content_configuration.get_qat_file_esxi()
        self.dlb_file_path_esxi = self._common_content_configuration.get_dlb_file_esxi()
        self.hqm_file_path = self._common_content_configuration.get_hqm_file()
        self.vcenter_esxi_file_path = self._common_content_configuration.get_vcenter_esxi_file()
        self.vcenter_json_file_path = self._common_content_configuration.get_vcenter_json_file()
        self.accel_file_path = self._common_content_configuration.get_idx_file()
        self.vm_accel_file_path = self._common_content_configuration.get_vm_idx_file()
        self.spr_file_path = self._common_content_configuration.get_spr_file()
        self.nvme_file_path = self._common_content_configuration.get_nvme_file()
        self._ldb_traffic_data = self._common_content_configuration.get_hqm_ldb_traffic_data()
        self._platform = self._common_content_lib.get_platform_family()
        self._os_lib = WindowsCommonLib(self._log, os_obj)
        self.ROOT = "/root"
        self._artifactory_obj = ContentArtifactoryUtils(self._log, self._os, self._common_content_lib, cfg_opts)
        self._grub_obj = GrubUtil(self._log, self._common_content_configuration, self._common_content_lib)

    def install_prime95(self, app_details=False):
        """
        Prime95 installer.
        1. Copy the file to SUT and installed it.

        :Param: app_details contains path and name of the application
        :return: application path , name and copy method
        """
        if OperatingSystems.WINDOWS == self.sut_os:
            artifactory_name = ArtifactoryName.DictWindowsTools[ArtifactoryTools.PRIME95_ZIP_FILE]
            zip_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
            if app_details:
                prime_path = self._common_content_lib.copy_zip_file_to_sut("prime95", zip_file_path)
                return prime_path, "prime95"
            return self._common_content_lib.copy_zip_file_to_sut("prime95", zip_file_path)
        elif OperatingSystems.LINUX == self.sut_os:
            if app_details:
                path = self.copy_mprime_file_to_sut()
                return path, "mprime"
            return self.copy_mprime_file_to_sut()
        else:
            self._log.error("Prime95 is not supported on OS '%s'" % self._os.sut_os)
            raise NotImplementedError("Prime95 is not supported on OS '%s'" % self._os.sut_os)

    def install_svm_tool(self):
        """
        Download and Copy GFX_nVidia_SVM.zip to SUT, and extract it.
        1. Copy the file to SUT and installed it.

        :return: application path
        """
        if OperatingSystems.WINDOWS == self.sut_os:
            artifactory_name = ArtifactoryName.DictWindowsTools[ArtifactoryTools.SVM_ZIP_FILE]
            zip_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
            return self._common_content_lib.copy_zip_file_to_sut("SVM", zip_file_path)
        else:
            self._log.error("SVM is not supported on OS '%s'" % self._os.sut_os)
            raise NotImplementedError("SVM is not supported on OS '%s'" % self._os.sut_os)

    def install_stressng(self):
        """
        Stress-ng installer.
        Copy the file to SUT and build it.

        :return: application path , name and copy method
        """
        if OperatingSystems.LINUX == self.sut_os:
            artifactory_name = ArtifactoryName.DictLinuxTools[ArtifactoryTools.STRESS_NG]
            zip_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
            sut_path = self._common_content_lib.copy_zip_file_to_linux_sut(
                self.stressng_constants["STRESSNG_FOLDER_NAME"], zip_file_path)
            # stress-ng is within its own folder, so fix folder structure
            embedded_directory = "{}/{}/*".format(sut_path, self.stressng_constants["STRESSNG_FOLDER_NAME"])
            self._os.execute("mv {} {}".format(embedded_directory, sut_path), self._command_timeout)
            self.yum_install("libaio-devel")
            self.yum_install("\"Development Tools\"", group=True)
            result = self._os.execute("cd {}; make".format(sut_path), self._command_timeout)
            if result.stderr:
                raise RuntimeError("Failed to make stress-ng.  Failure message: {}".format(result.stderr))
            self._log.debug("Successfully built stress-ng.")
            return sut_path
        else:
            self._log.error("Stress-ng is not supported on OS {}".format(self._os.sut_os))
            raise NotImplementedError("Stress-ng is not supported on OS {}".format(self._os.sut_os))

    def install_pmutility(self):
        """
        pmutility installer.
        Copy the file to SUT and build it.

        :return: application path , name and copy method
        """
        if OperatingSystems.LINUX == self.sut_os:
            artifactory_name = ArtifactoryName.DictLinuxTools[ArtifactoryTools.PM_UTILITY]
            zip_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
            sut_path = self._common_content_lib.copy_zip_file_to_linux_sut(
                self.pmutils_constants["PMUTILS_LINUX_FOLDER"], zip_file_path)
            # pmutils is within its own folder, so fix folder structure
            embedded_directory = "{}/{}/*".format(sut_path, self.pmutils_constants["PMUTILS_LINUX_FOLDER"])
            self._os.execute("mv {} {}".format(embedded_directory, sut_path), self._command_timeout)
            self.yum_install("\"Development Tools\"", group=True)
            result = self._os.execute("cd {}; make all".format(sut_path), self._command_timeout)
            if result.stderr:
                raise RuntimeError("Failed to make pmutil.  Failure message: {}".format(result.stderr))
            self._log.debug("Successfully built pmutil.")
            return sut_path
        else:
            self._log.error("pmutility is not supported on OS {}".format(self._os.sut_os))
            raise NotImplementedError("pmutility is not supported on OS {}".format(self._os.sut_os))

    def install_iperf(self):
        """iperf3 installer.
        Run package installer to install iperf3."""
        if OperatingSystems.LINUX == self.sut_os:
            self.yum_install("iperf3")
        else:
            self._log.error("iperf is not supported on OS {}".format(self._os.sut_os))
            raise NotImplementedError("iperf is not supported on OS {}".format(self._os.sut_os))

    def install_ptg(self):
        """
        Downloads PTG files to SUT.
        """
        if OperatingSystems.LINUX == self.sut_os:
            zip_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
                ArtifactoryName.DictLinuxTools["ptg"])
            # Return SUT path
            return self._common_content_lib.copy_zip_file_to_linux_sut(ArtifactoryTools.PTG, zip_file_path)
        else:
            self._log.error("PTG is not supported on OS {}".format(self._os.sut_os))
            raise NotImplementedError("PTG is not supported on OS {}".format(self._os.sut_os))

    def install_selviewer(self):
        """
        SELViewer installer.
        1. Copy the file to SUT and installed it.

        :return: None
        """
        if OperatingSystems.WINDOWS == self.sut_os:
            artifactory_name = ArtifactoryName.DictWindowsTools[ArtifactoryTools.SEL_VIEWER]
            zip_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
            self._common_content_lib.copy_zip_file_to_sut(self.util_constants["SEL_ZIP_FILE"].split(".")[0],
                                                          zip_file_path)
        elif OperatingSystems.LINUX == self.sut_os:
            # TODO: need add code for SELViewer for linux
            raise NotImplementedError
        else:
            self._log.error("SELViewer is not supported on OS '%s'" % self._os.sut_os)
            raise NotImplementedError("SELViewer is not supported on OS '%s'" % self._os.sut_os)

    def install_mem_rebooter(self):
        """
        Mem Rebooter installer.
        1. Copy the file to SUT and installed it.

        :return: None
        """
        if OperatingSystems.WINDOWS == self.sut_os:
            artifactory_name = ArtifactoryName.DictWindowsTools[ArtifactoryTools.MEM_REBOOTER]
            zip_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
            self._common_content_lib.copy_zip_file_to_sut(
                self.util_constants["WINDOWS_MEM_REBOOTER_ZIP_FILE"].split(".")[0],
                zip_file_path)
        elif OperatingSystems.LINUX == self.sut_os:
            # TODO: need add code for MemRebooter for linux
            raise NotImplementedError
        else:
            self._log.error("MemRebooter is not supported on OS '%s'" % self._os.sut_os)
            raise NotImplementedError("MemRebooter is not supported on OS '%s'" % self._os.sut_os)

    def install_platform_cycler(self):
        """
        Platform cycler installer.
        1. Copy the file to SUT and installed it.

        :return: None
        """
        if OperatingSystems.WINDOWS == self.sut_os:
            artifactory_name = ArtifactoryName.DictWindowsTools[ArtifactoryTools.PLATFORM_CYCLER]
            zip_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
            return self._common_content_lib.copy_zip_file_to_sut(self.platform_cycler_constants
                                                                 ["WINDOWS_PLATFORM_CYCLER_ZIP_FILE"].split(".")[0],
                                                                 zip_file_path)
        elif OperatingSystems.LINUX == self.sut_os:
            return self.install_platform_cycler_linux()
        else:
            self._log.error("Platform cycler is not supported on OS '%s'" % self._os.sut_os)
            raise NotImplementedError("Platform cycler is not supported on OS '%s'" % self._os.sut_os)

    def get_stress_test_tools_file_path(self):
        """
        Function to get platform cycler path and stress app test tools path.

        :param: os_type: Linux or Windows.
        :return: platform cycler path and stress app test file path.
        :raise: NotImplementedError: For OS other than Windows and Linux this exception will raise.
        :raise: FileNotFoundError: Will raise when the specified file is not existed in the path.
        """

        platform_cycler_path = None
        platform_stressapp_path = None

        if OperatingSystems.WINDOWS == self.sut_os:
            artifactory_name = ArtifactoryName.DictWindowsTools[ArtifactoryTools.PLATFORM_STRESS_CYCLER_WINDOWS]
            platform_cycler_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
            # TODO: need add code for stressapptest for windows
        elif OperatingSystems.LINUX == self.sut_os:
            artifactory_name = ArtifactoryName.DictLinuxTools[ArtifactoryTools.PLATFORM_STRESS_CYCLER_LINUX]
            platform_cycler_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
            artifactory_name = ArtifactoryName.DictLinuxTools[ArtifactoryTools.PLATFORM_STRESS_LINUX_FILE]
            platform_stressapp_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)

        else:
            self._log.error("Memory stress test not supported on OS '%s'" % self._os.sut_os)
            raise NotImplementedError("Memory stress test not supported on OS '%s'" % self._os.sut_os)

        if not os.path.isfile(platform_cycler_path):
            self._log.error("Platform cycler script '%s' does not exists" % str(platform_cycler_path))
            raise FileNotFoundError("Platform cycler script '%s' does not exists" % str(platform_cycler_path))

        if not os.path.isfile(platform_stressapp_path):
            self._log.error("Stressapptest script '%s' does not exists" % str(platform_stressapp_path))
            raise FileNotFoundError("Stressapptest script '%s' does not exists" % str(platform_stressapp_path))

        return platform_cycler_path, platform_stressapp_path

    def install_platform_cycler_linux(self):
        """
        Linux environment platform cycler installer.
        1. Copy platform cycler tool tar file to Linux SUT.
        2. Decompress tar file under user home folder.

        :return: None
        """
        self._log.info("Copying platform cycler tar file to SUT under home folder...")

        # get Linux SUT home folder name
        ret_val = self._os.execute("echo $HOME", self._command_timeout)
        if ret_val.cmd_failed():
            self._log.error("Failed to execute the command {}".format(ret_val))
            raise RuntimeError("Failed to execute the command {} and the "
                               "error is {}..".format(ret_val, ret_val.stderr))
        home_folder = str(ret_val.stdout).strip('\n')
        sut_platform_cycler_path = Path(os.path.join(home_folder, self.platform_cycler_constants[
            "PLATFORM_CYCLER_FOLDER_NAME"])).as_posix()

        # delete the folder in SUT if exists
        verify_rm_cmd = self._os.execute("rm -rf {}".format(sut_platform_cycler_path), self._command_timeout)

        if verify_rm_cmd.cmd_failed():
            self._log.error("Failed to execute the command {}".format(verify_rm_cmd))
            raise RuntimeError("Failed to execute the command {} and the "
                               "error is {}..".format(verify_rm_cmd, verify_rm_cmd.stderr))

        # create platform_cycler folder
        verify_mkdir_cmd = self._os.execute("mkdir {}".format(sut_platform_cycler_path), self._command_timeout)

        if verify_mkdir_cmd.cmd_failed():
            self._log.error("Failed to execute the command {}".format(verify_mkdir_cmd))
            raise RuntimeError("Failed to execute the command {} and the "
                               "error is {}..".format(verify_mkdir_cmd, verify_mkdir_cmd.stderr))

        # delete log folder as well
        verify_rm_rf_cmd = self._os.execute("rm -rf {}".format(self.platform_cycler_constants[
                                                                   "LINUX_PLATFORM_CYCLER_LOG_FOLDER"]),
                                            self._command_timeout)

        if verify_rm_rf_cmd.cmd_failed():
            self._log.error("Failed to execute the command {}".format(verify_rm_rf_cmd))
            raise RuntimeError("Failed to execute the command {} and the "
                               "error is {}..".format(verify_rm_rf_cmd, verify_rm_rf_cmd.stderr))
        # copy tar file to SUT
        host_platform_cycler_path, host_platform_stressapp_path = \
            self.get_stress_test_tools_file_path()

        parent_path = Path(os.path.dirname(os.path.realpath(__file__)))
        self._collateral_path = os.path.join(parent_path, self.util_constants["COLLATERAL_DIR_NAME"])

        self._os.copy_local_file_to_sut(host_platform_cycler_path, sut_platform_cycler_path)
        self._os.copy_local_file_to_sut(host_platform_stressapp_path, self.util_constants["LINUX_USR_SBIN_PATH"])

        # extract platform cycler tar file
        verify_untar_cmd = self._os.execute("tar xvzf {}".format(self.platform_stress_constants[
                                                                     "PLATFORM_STRESS_CYCLER_LINUX_FILE"]),
                                            self._command_timeout, cwd=sut_platform_cycler_path)

        if verify_untar_cmd.cmd_failed():
            self._log.error("Failed to execute the command {}".format(verify_untar_cmd))
            raise RuntimeError("Failed to execute the command {} and the "
                               "error is {}..".format(verify_untar_cmd, verify_untar_cmd.stderr))
        self._log.info("The file '{}' has been decompressed "
                       "successfully ..".format(self.platform_stress_constants["PLATFORM_STRESS_CYCLER_LINUX_FILE"]))

        self.platform_cycler_extract_path = Path(os.path.join(sut_platform_cycler_path,
                                                              self.platform_cycler_constants[
                                                                  "PLATFORM_CYCLER_EXTRACT_FOLDER_NAME"])).as_posix()
        return self.platform_cycler_extract_path

    def copy_mprime_file_to_sut(self):
        """
        This method copy the Prime95 tool from host machine to sut

        :raise: RuntimeError - If execute method fails to run the commands
        :return:None
        """

        self._log.info("Copying Prime95 tar file to SUT under home folder")
        # get Linux SUT home folder name
        ret_val = self._os.execute("echo $HOME", self._command_timeout)
        if ret_val.cmd_failed():
            log_error = "Failed to run 'echo $HOME' command with return value = '{}' and " \
                        "std_error='{}'..".format(ret_val.return_code, ret_val.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        home_folder = str(ret_val.stdout).strip('\n')
        sut_mprime_path = Path(os.path.join(home_folder, self.prime_tool_constants["MPRIME_FOLDER_NAME"])).as_posix()

        # delete the folder in SUT if exists
        command__remove_dir = "rm -rf {}".format(sut_mprime_path)
        command_result = self._os.execute(command__remove_dir, self._command_timeout)
        if command_result.cmd_failed():
            log_error = "Failed to run command '{}' with return value = '{}' and std_error='{}'..".format(
                command__remove_dir, command_result.return_code, command_result.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        # create Prime95 folder in sut
        command_make_dir = "mkdir {}".format(sut_mprime_path)
        command_result = self._os.execute(command_make_dir, self._command_timeout)
        if command_result.cmd_failed():
            log_error = "Failed to run command '{}' with return value = '{}' and std_error='{}'.." \
                .format(command_make_dir, command_result.return_code, command_result.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        # copy Prime95 tar file to SUT
        host_platform_mprime_path = self.get_mprime_file_path()
        self._os.copy_local_file_to_sut(host_platform_mprime_path, sut_mprime_path)

        # extract prime95 tar file
        command_extract_tar_file = "tar xvzf {}".format(self.prime_tool_constants["STRESS_MPRIME_LINUX_FILE"])
        command_result = self._os.execute(command_extract_tar_file, self._command_timeout, cwd=sut_mprime_path)
        if command_result.cmd_failed():
            log_error = "Failed to run {} command with return value = '{}' and std_error='{}'.." \
                .format(command_extract_tar_file, command_result.return_code, command_result.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        self._log.info("The file '{}' has been decompressed "
                       "successfully ..".format(self.prime_tool_constants["STRESS_MPRIME_LINUX_FILE"]))

        return sut_mprime_path

    def get_mprime_file_path(self):
        """
        Function to get Prime95 tool path
        :return: Prime95 path.
        :raise: RuntimeError: will raise specified os does not support the mprime test
        :raise: IOError: Will raise when the specified file is not existed in the path.
        """
        if OperatingSystems.LINUX == self._os.os_type:
            artifactory_name = ArtifactoryName.DictLinuxTools[ArtifactoryTools.STRESS_MPRIME_LINUX_FILE]
            mprime_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
        else:
            log_error = "Prime95 test not supported on OS '%s'" % str(self._os.os_type)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        if not os.path.isfile(mprime_path):
            log_error = "Prime95 script '%s' does not exists" % str(mprime_path)
            self._log.error(log_error)
            raise IOError(log_error)
        return mprime_path

    def copy_cv_cli_file_to_sut(self):
        """
        This method copy the cv_cli tool from host machine to sut

        :raise: RuntimeError - If execute method fails to run the commands
        :return:None
        """

        self._log.info("Copying cv_cli tar file to SUT under home folder")
        # get Linux SUT home folder name
        ret_val = self._os.execute("echo $HOME", self._command_timeout)
        if ret_val.cmd_failed():
            log_error = "Failed to run 'echo $HOME' command with return value = '{}' and " \
                        "std_error='{}'..".format(ret_val.return_code, ret_val.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        home_folder = str(ret_val.stdout).strip('\n')
        sut_cv_cli_path = Path(os.path.join(home_folder, self.CXL_CV_CLI_FOLDER_PATH)).as_posix()

        # delete the folder in SUT if exists
        command__remove_dir = "rm -rf {}".format(sut_cv_cli_path)
        command_result = self._os.execute(command__remove_dir, self._command_timeout)
        if command_result.cmd_failed():
            log_error = "Failed to run command '{}' with return value = '{}' and std_error='{}'..".format(
                command__remove_dir, command_result.return_code, command_result.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        # create cv_cli folder in sut
        command_make_dir = "mkdir {}".format(sut_cv_cli_path)
        command_result = self._os.execute(command_make_dir, self._command_timeout)
        if command_result.cmd_failed():
            log_error = "Failed to run command '{}' with return value = '{}' and std_error='{}'.." \
                .format(command_make_dir, command_result.return_code, command_result.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        # copy cv_cli tar file to SUT
        artifactory_name = ArtifactoryName.DictLinuxTools[ArtifactoryTools.STRESS_CV_CLI_LINUX_FILE]
        host_platform_cv_cli_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
        self._os.copy_local_file_to_sut(host_platform_cv_cli_path, sut_cv_cli_path)

        # extract cv_cli tar file
        command_extract_tar_file = "tar xvzf {}".format(self.CXL_CV_CLI_FILE_NAME)
        command_result = self._os.execute(command_extract_tar_file, self._command_timeout, cwd=sut_cv_cli_path)
        if command_result.cmd_failed():
            log_error = "Failed to run {} command with return value = '{}' and std_error='{}'.." \
                .format(command_extract_tar_file, command_result.return_code, command_result.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        self._log.info("The file '{}' has been decompressed "
                       "successfully ..".format(self.CXL_CV_CLI_FILE_NAME))

        return sut_cv_cli_path

    def install_ipmctl(self):
        """
        IPMCTL installer.
        1. Copy the file to SUT and installed it.

        :return: None
        """
        if OperatingSystems.WINDOWS == self.sut_os:
            intel_optane_exe = None
            installed_version = None
            file_name = self._common_content_configuration.get_intel_optane_pmem_mgmt_file()
            zip_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder(file_name)
            regx_for_version = "Command\sLine\sInterface\sVersion\s\d+.\d+.\d+.\d+"
            self._log.info("executing the command : {}".format(self.IPMCTL_VERSION_COMMAND))
            version_result = self._os.execute(self.IPMCTL_VERSION_COMMAND, self._command_timeout)
            self._log.info(version_result.stdout)
            self._log.error(version_result.stdout)
            if not version_result.cmd_failed():
                if version_result.stdout:
                    version_result_list = version_result.stdout.split('\n')
                    for each_line in version_result_list:
                        installed_version = re.findall(regx_for_version, each_line)[0].split(' ')[-1]
                        self._log.info("Installed ipmctl version in the SUT is : {}".format(installed_version))
                        break
            ipmctl_executer_path = self._common_content_lib.copy_zip_file_to_sut(file_name.split("_")[0], zip_file_path)
            list_exe_files = self._common_content_lib.execute_sut_cmd(r"dir *.exe", "Find the path of ipmctl",
                                                                      self._command_timeout, ipmctl_executer_path)
            for line in list_exe_files.split("\n"):
                if ".exe" in line:
                    intel_optane_exe = line.split()[-1]
                    break
            if version_result.cmd_failed() or (installed_version not in intel_optane_exe):

                self._common_content_lib.execute_sut_cmd('"{}" /S'.format(intel_optane_exe), "Install ipmctl",
                                                         self._command_timeout, ipmctl_executer_path)

                self._log.info("Latest version of Intel Optane Pmem Mgmt tool has been installed".format(
                    intel_optane_exe))
                self._common_content_lib.perform_os_reboot(self._reboot_time_out)
            else:
                self._log.info("Ipmctl tool already installed with the version {}".format(intel_optane_exe))

        elif OperatingSystems.LINUX == self.sut_os:
            rpm_find_libipmctl_command = "rpm -qa | grep libipmctl.*"
            self._log.info("Executing the command : {}".format(rpm_find_libipmctl_command))
            result = self._os.execute(rpm_find_libipmctl_command, self._command_timeout,
                                      self.util_constants["LINUX_USR_ROOT_PATH"])
            self._log.info("std out : {}".format(result.stdout))
            self._log.info("std error: {}".format(result.stderr))
            rpm_files_list = None
            if result:
                rpm_files_list = result.stdout.strip().split("\n")
                self._log.info("RPM Files list : {}".format(rpm_files_list))
            which_ipmctl_command = "which ipmctl"
            file_name = self._common_content_configuration.get_intel_optane_pmem_mgmt_file()
            ipmctl_tool_path_host = self._artifactory_obj.download_tool_to_automation_tool_folder(file_name)
            folder_path_sut = self._common_content_lib.copy_zip_file_to_linux_sut(file_name.split("_")[0],
                                                                                  ipmctl_tool_path_host)

            self._log.info("Executing the command : ls *.rpm ")
            rpm_files = self._common_content_lib.execute_sut_cmd("ls *.rpm", "To get list of rpm files",
                                                                 self._command_timeout, folder_path_sut)
            self._log.info("rpm files list in intel_optane_pmem_mgmt_file_name : \n{} ".format(rpm_files))
            libipmctl_rpm_file_name = re.findall(pattern=self.REGX_LIB_IPMCTL, string=rpm_files)
            self._log.info("libipmctl rpm file name : {}".format(libipmctl_rpm_file_name))
            ipmctl_rpm_file_name = re.findall(pattern=self.REGX_IPMCTL, string=rpm_files)
            self._log.info("ipmctl rpm file name : {}".format(ipmctl_rpm_file_name))

            # condition to check both the versions equal
            if str(libipmctl_rpm_file_name[0].strip().split(".rpm")[0]) in rpm_files_list:
                self._log.info("ipmctl already installed in SUT")
            # condition to check both the versions not equal
            elif str(libipmctl_rpm_file_name[0].strip().split(".rpm")[0]) not in rpm_files_list:
                for each_rpm in rpm_files_list:
                    self.yum_remove(each_rpm.strip())
                self.yum_remove("ipmctl")

                install_libipmctl_command = "rpm -ivh {}".format(libipmctl_rpm_file_name[0])
                install_ipmctl_command = "rpm -ivh {}".format(ipmctl_rpm_file_name[0])

                self._log.info("Executing command : {}".format(install_libipmctl_command))
                self._os.execute(install_libipmctl_command, self._command_timeout, folder_path_sut)
                self._os.execute(install_ipmctl_command, self._command_timeout, folder_path_sut)

                self._log.info("Executing the command: {} ".format(which_ipmctl_command))
                which_ipmctl_cmd_result = self._os.execute(which_ipmctl_command, self._command_timeout,
                                                           self.util_constants["LINUX_USR_ROOT_PATH"])
                self._log.info("std out {}".format(which_ipmctl_cmd_result.stdout))
                self._log.info("std error : {}".format(which_ipmctl_cmd_result.stderr))

                if self.ipmctl_constants["IPMCTL_USR_BIN_PATH"] in which_ipmctl_cmd_result.stdout:
                    self._log.info("IPMCTL tool installed in the SUT ...")
                else:
                    error_msg = "failed to install ipmctl tool in SUT"
                    raise content_exceptions.TestFail(error_msg)
        else:
            self._log.error("IPMCTL is not supported on OS '%s'" % self.sut_os)
            raise NotImplementedError("IPMCTL is not supported on OS '%s'" % self.sut_os)

    def install_fio(self, install_fio_package=False):
        """
        To install fio tool

        :param: install_fio_linux
        :return: None
        """
        if OperatingSystems.WINDOWS == self.sut_os:
            artifactory_name = ArtifactoryName.DictWindowsTools[ArtifactoryTools.FIO_MSI_INSTALLER]
            zip_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
            ipmctl_executer_path = self._common_content_lib.copy_zip_file_to_sut(self.fio_constants[
                                                                                     "FIO_MSI_INSTALLER"].
                                                                                 split(".")[0], zip_file_path)
            self._common_content_lib.execute_sut_cmd('msiexec /i "fio-3.9-x64.msi" /quiet', "Install fio",
                                                     self._command_timeout, ipmctl_executer_path)
            return ipmctl_executer_path
        elif OperatingSystems.LINUX == self.sut_os:
            self.install_fio_linux(yum_install_fio=install_fio_package)
        else:
            log_error = "FIO is not supported on OS '{}'".format(self._os.sut_os)
            self._log.error(log_error)
            raise NotImplementedError(log_error)

    def copy_win_kickstart_iso(self):
        """
        FUnction to install WIN_KICKSTART_ISO_LINUX_FILE on SUT
        1. Copy the file to SUT.

        :return: installed tool path
        """
        if OperatingSystems.WINDOWS == self.sut_os:
            # TODO: need add code for StressTestApp for Windows
            raise NotImplementedError

        elif OperatingSystems.LINUX == self.sut_os:
            artifactory_name = ArtifactoryName.DictLinuxTools[ArtifactoryTools.WIN_KICKSTART_ISO_LINUX_FILE]
            host_platform_win_kickstart_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
                artifactory_name)
            self._os.copy_local_file_to_sut(host_platform_win_kickstart_file_path,
                                            self.util_constants["LINUX_USR_ROOT_PATH"])
            platform_win_ks_file_path = Path(os.path.join(self.util_constants["LINUX_USR_ROOT_PATH"],
                                                         self.WIN_KICKSTART_ISO_LINUX_FILE_NAME)).as_posix()

            command_line = self._os.execute("chmod 777 {}".format(platform_win_ks_file_path), 0.5)

            if command_line.cmd_failed():
                log_error = "Failed to run command '{}' with return value = '{}' and std_error='{}'..". \
                    format(command_line, command_line.return_code, command_line.stderr)
                self._log.error(log_error)
                raise RuntimeError(log_error)
            self._os.execute("cp {} {}".format(platform_win_ks_file_path,
                                               self.util_constants["LINUX_VAR_LIB_IMG_PATH"]),
                             self._command_timeout)
            return platform_win_ks_file_path

        else:
            self._log.error("Kickstart file is not supported on OS '%s'" % self._os.sut_os)
            raise NotImplementedError("Kickstart file is not supported on OS '%s'" % self._os.sut_os)

    def install_stress_test_app(self):
        """
        FUnction to install StressTestApp tool on SUT
        1. Copy the file to SUT and installed it.

            :return: installed tool path
        """
        if OperatingSystems.WINDOWS == self.sut_os:
            # TODO: need add code for StressTestApp for Windows
            raise NotImplementedError

        elif OperatingSystems.LINUX == self.sut_os:
            artifactory_name = ArtifactoryName.DictLinuxTools[ArtifactoryTools.PLATFORM_STRESS_LINUX_FILE]
            host_platform_stressapp_test_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
                artifactory_name)
            self._os.copy_local_file_to_sut(host_platform_stressapp_test_path,
                                            self.util_constants["LINUX_USR_ROOT_PATH"])
            platform_stress_app_path = Path(os.path.join(self.util_constants["LINUX_USR_ROOT_PATH"],
                                                         self.platform_stress_constants
                                                         ["PLATFORM_STRESS_LINUX_FILE"])).as_posix()

            command_line = self._os.execute("chmod 777 {}".format(platform_stress_app_path), 0.5)

            if command_line.cmd_failed():
                log_error = "Failed to run command '{}' with return value = '{}' and std_error='{}'..". \
                    format(command_line, command_line.return_code, command_line.stderr)
                self._log.error(log_error)
                raise RuntimeError(log_error)
            self._os.execute("cp {} {}".format(platform_stress_app_path,
                                               self.util_constants["LINUX_USR_SBIN_PATH"]),
                             self._command_timeout)
            return platform_stress_app_path

        else:
            self._log.error("StressTestApp  is not supported on OS '%s'" % self._os.sut_os)
            raise NotImplementedError("StressTestApp is not supported on OS '%s'" % self._os.sut_os)

    def install_mlc_internal_linux(self, force_install=True):
        """
        Linux environment mlc installer.
        Note: Container environment can not use artifactory
        1. Copy mlc tool zip file to Linux SUT.
        2. Decompress zip file under mlc folder.
        :param force_install:  True to force install - this would be default
        :return: None
        """
        artifactory_name = ArtifactoryName.DictLinuxTools[ArtifactoryTools.MLC_INTERNAL_INSTALLER]
        sut_mlc_path = Path(os.path.join(self.util_constants["LINUX_USR_ROOT_PATH"],
                                         artifactory_name.split(".")[0])).as_posix()

        check_mlc_dir_exists = self._os.execute("test -d {}".format(sut_mlc_path), self._command_timeout,
                                                self.util_constants["LINUX_USR_ROOT_PATH"])
        # container environment can not install from artifactory
        if self._common_content_configuration.is_container_env() or \
                (not check_mlc_dir_exists.cmd_failed() and not force_install):
            self.mlc_extract_path = Path(os.path.join(sut_mlc_path, "Linux")).as_posix()
            self._log.info("Found MLC Path in SUT: {}, force install skipped".format(self.mlc_extract_path))
            return self.mlc_extract_path

        self._log.info("Copying mlc tar file to SUT ...")

        # delete the folder in SUT if exists
        remove_command = "rm -rf {}".format(sut_mlc_path)
        verify_rm_cmd = self._os.execute(remove_command, self._command_timeout)

        if verify_rm_cmd.cmd_failed():
            self._log.error("Failed to execute the command {}".format(remove_command))
            raise RuntimeError("Failed to execute the command {} and the "
                               "error is {}..".format(remove_command, verify_rm_cmd.stderr))

        # create mlc folder
        self._common_content_lib.execute_sut_cmd("mkdir {}".format(sut_mlc_path), "create folder",
                                                 self._command_timeout, self.util_constants["LINUX_USR_ROOT_PATH"])

        host_mlc_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)

        mlc_tool_path = self._common_content_lib.copy_zip_file_to_linux_sut("mlc", host_mlc_path)

        return mlc_tool_path

    def install_mlc_linux(self, force_install=True):
        """
        Linux environment mlc installer.
        Note: Container environment can not use artifactory
        1. Copy mlc tool tar file to Linux SUT.
        2. Decompress tar file under mlc folder.

        :param force_install:  True to force install - this would be default
        :return: None
        """
        artifactory_name = ArtifactoryName.DictLinuxTools[ArtifactoryTools.MLC_INSTALLER]
        sut_mlc_path = Path(os.path.join(self.util_constants["LINUX_USR_ROOT_PATH"],
                                         artifactory_name.split(".")[0])).as_posix()

        check_mlc_dir_exists = self._os.execute("test -d {}".format(sut_mlc_path), self._command_timeout,
                                                self.util_constants["LINUX_USR_ROOT_PATH"])
        # container environment can not install from artifactory
        if self._common_content_configuration.is_container_env() or \
                (not check_mlc_dir_exists.cmd_failed() and not force_install):
            self.mlc_extract_path = Path(os.path.join(sut_mlc_path, "Linux")).as_posix()
            self._log.info("Found MLC Path in SUT: {}, force install skipped".format(self.mlc_extract_path))
            return self.mlc_extract_path

        self._log.info("Copying mlc tar file to SUT ...")

        # delete the folder in SUT if exists
        remove_command = "rm -rf {}".format(sut_mlc_path)
        verify_rm_cmd = self._os.execute(remove_command, self._command_timeout)

        if verify_rm_cmd.cmd_failed():
            self._log.error("Failed to execute the command {}".format(remove_command))
            raise RuntimeError("Failed to execute the command {} and the "
                               "error is {}..".format(remove_command, verify_rm_cmd.stderr))

        # create mlc folder
        self._common_content_lib.execute_sut_cmd("mkdir {}".format(sut_mlc_path), "create folder",
                                                 self._command_timeout, self.util_constants["LINUX_USR_ROOT_PATH"])

        host_mlc_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
        # copy tar file to SUT
        self._os.copy_local_file_to_sut(host_mlc_path, sut_mlc_path)

        # extract mlc tar file
        tar_command = "tar xvf {}".format(artifactory_name)
        self._common_content_lib.execute_sut_cmd(tar_command, "Tar Command", self._command_timeout, sut_mlc_path)
        self._log.info("The file '{}' has been decompressed successfully ..".format(artifactory_name))

        self.mlc_extract_path = Path(os.path.join(sut_mlc_path, "Linux")).as_posix()
        self._log.info("MLC Path in SUT : {}".format(self.mlc_extract_path))
        return self.mlc_extract_path

    def install_mlc(self):
        """
        MLC installer.
        1. Copy the file to SUT and installed it.

        :return: mlc installed tool path
        """
        if OperatingSystems.WINDOWS == self.sut_os:
            artifactory_name = ArtifactoryName.DictWindowsTools[ArtifactoryTools.MLC_EXE_INSTALLER]
            host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
            mlc_path = self._common_content_lib.copy_zip_file_to_sut(
                self.mlc_constants["MLC_FOLDER_NAME"], host_path)
            mlc_windows_path = os.path.join(mlc_path, "Windows")

            return mlc_windows_path
        elif OperatingSystems.LINUX == self.sut_os:
            return self.install_mlc_linux()
        else:
            log_error = "MLC is not supported on OS '{}'".format(self._os.sut_os)
            self._log.error(log_error)
            raise NotImplementedError(log_error)

    def copy_ras_tools_to_linux(self):
        """
        This Method is used to Copy Ras_tools.tar file to sut
        """
        self._log.info("Copying Ras Tools tar file to SUT under tools folder...")

        # get Linux SUT home folder name
        ras_tools_dir = "/etc/tools"
        ret_val = self._os.execute("cd /etc/tools/", self._command_timeout)
        if ret_val.cmd_failed():
            self._log.error("Failed to execute the command {}".format(ret_val))
            raise RuntimeError("Failed to execute the command {} and the "
                               "error is {}..".format(ret_val, ret_val.stderr))
        self.sut_ras_tools_path = Path(os.path.join(ras_tools_dir, self.ras_tool_constants[
            "RAS_TOOLS_FOLDER_NAME"])).as_posix()
        # delete the folder in SUT if exists
        verify_rm_cmd = self._os.execute("rm -rf {}".format(self.sut_ras_tools_path), self._command_timeout)

        if verify_rm_cmd.cmd_failed():
            self._log.error("Failed to execute the command {}".format(verify_rm_cmd))
            raise RuntimeError("Failed to execute the command {} and the "
                               "error is {}..".format(verify_rm_cmd, verify_rm_cmd.stderr))

        # create platform_cycler folder
        verify_mkdir_cmd = self._os.execute("mkdir {}".format(self.sut_ras_tools_path), self._command_timeout)

        if verify_mkdir_cmd.cmd_failed():
            self._log.error("Failed to execute the command {}".format(verify_mkdir_cmd))
            raise RuntimeError("Failed to execute the command {} and the "
                               "error is {}..".format(verify_mkdir_cmd, verify_mkdir_cmd.stderr))

        # copy tar file to SUT
        host_ras_tools_path = self.get_ras_tools_file_path()

        self._os.copy_local_file_to_sut(host_ras_tools_path, self.sut_ras_tools_path)

    def install_linux_ras_tools(self):
        """
        Linux environment Ras Tools installer.
        1. Copy Ras Tools tar file to Linux SUT.
        2. Decompress tar file under user /etc/tools folder.

        :return: None
        """
        self.copy_ras_tools_to_linux()

        # extract Ras Tools tar file
        verify_untar_cmd = self._os.execute("tar -xvf {}".format(self.ras_tool_constants["RAS_TOOLS_PATH"]),
                                            self._command_timeout, cwd=self.sut_ras_tools_path)

        if verify_untar_cmd.cmd_failed():
            self._log.error("Failed to execute the command {}".format(verify_untar_cmd))
            raise RuntimeError("Failed to execute the command {} and the "
                               "error is {}..".format(verify_untar_cmd, verify_untar_cmd.stderr))

        self._log.info("The file '{}' has been decompressed "
                       "successfully ..".format(self.ras_tool_constants["RAS_TOOLS_PATH"]))

        ras_tools_make_cmd = self._os.execute("make",
                                              self._command_timeout,
                                              cwd=self.sut_ras_tools_path)
        if ras_tools_make_cmd.cmd_failed():
            self._log.error("Failed to execute the command {}".format(ras_tools_make_cmd))
            raise RuntimeError("Failed to execute the command {} and the "
                               "error is {}..".format(ras_tools_make_cmd, ras_tools_make_cmd.stderr))

        if ras_tools_make_cmd.return_code != 0:
            self._log.error("Ras Tool installation failed on SUT")
        else:
            self._log.info("Ras Tool Installed Successfully")

        self.ras_tools_extract_path = Path(os.path.join(self.sut_ras_tools_path,
                                                        self.ras_tool_constants["RAS_TOOLS_PATH"])).as_posix()

        return ras_tools_make_cmd.return_code

    def get_ras_tools_file_path(self):
        """
        Function to get Ras Tools path.

        :return: ras_tools_path.
        :raise: NotImplementedError: For OS other than Linux this exception will raise.
        :raise: IOError: Will raise when the specified file is not existed in the path.
        """

        ras_tools_path = None

        if OperatingSystems.WINDOWS == self.sut_os:
            log_error = "Ras tools has no implemented support on Windows SUT"
            self._log.error(log_error)
            raise NotImplementedError(log_error)
        elif OperatingSystems.LINUX == self.sut_os:
            artifactory_name = ArtifactoryName.DictLinuxTools[ArtifactoryTools.RAS_TOOLS_PATH]
            ras_tools_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)

        else:
            self._log.error("Ras Tools Installation is not supported on OS '%s'" % self._os.sut_os)
            raise NotImplementedError("Ras Tools Installation is not supported on OS '%s'" % self._os.sut_os)

        if not os.path.isfile(ras_tools_path):
            self._log.error("Ras Tools script '%s' does not exists" % str(ras_tools_path))
            raise IOError("Ras Tools script '%s' does not exists" % str(ras_tools_path))

        return ras_tools_path

    def install_ntttcp(self):
        """
        ntttcp installer.
        1. Copy the file to SUT and installed it.

        :return: Path to installed ntttcp
        """
        if OperatingSystems.LINUX == self.sut_os:
            artifactory_name = ArtifactoryName.DictLinuxTools[ArtifactoryTools.NTTTCP_LINUX_ZIP_FILE]
            zip_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
            sut_path = self._common_content_lib.copy_zip_file_to_linux_sut(self.ntttcp_constants[
                                                                    "ntttcp_linux_zip_file"].split(".")[0],
                                                                zip_path)

            # ntttcp for linux is within its own folder, so fix folder structure
            embedded_directory = "{}/{}/*".format(sut_path,
                                                  self.ntttcp_constants["ntttcp_linux_zip_file"].split(".")[0])
            self._os.execute("mv {} {}".format(embedded_directory, sut_path), self._command_timeout)
            self.yum_install("libaio-devel")
            self.yum_install("\"Development Tools\"", group=True)
            result = self._os.execute("cd {}/src; make && make install".format(sut_path), self._command_timeout)
            if "error" in result.stderr:
                raise RuntimeError("Failed to make ntttcp.  Failure message: {}".format(result.stderr))
            if "No space left on device" in result.stdout:
                raise RuntimeError("No space on SUT to install ntttcp.  Failure message: {}".format(result.stdout))
            self._log.debug("Successfully built ntttcp.")
            return sut_path

        else:
            self._log.error("Ntttcp Tool is not supported on OS '%s'" % self._os.sut_os)
            raise NotImplementedError("Ntttcp Tool is not supported on OS '%s'" % self._os.sut_os)

    def install_disk_spd(self):
        """
        disk_spd installer.
        1. Copy the file to SUT and installed it.

        :return: None
        """
        if OperatingSystems.WINDOWS == self.sut_os:
            artifactory_name = ArtifactoryName.DictWindowsTools[ArtifactoryTools.DISK_SPD_ZIP_FILE]
            zip_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
            return self._common_content_lib.copy_zip_file_to_sut(self.disk_spd_constants["disk_spd_zip_file"].
                                                                 split(".")[0], zip_file_path)
        elif OperatingSystems.LINUX == self.sut_os:
            artifactory_name = ArtifactoryName.DictLinuxTools[ArtifactoryTools.DISK_SPD_LINUX_ZIP_FILE]
            zip_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
            sut_path = self._common_content_lib.copy_zip_file_to_linux_sut(self.disk_spd_constants[
                                                                    "disk_spd_linux_zip_file"].split(".")[0],
                                                                zip_file_path)

            # diskspd for linux is within its own folder, so fix folder structure
            embedded_directory = "{}/{}/*".format(sut_path,
                                                  self.disk_spd_constants["disk_spd_linux_zip_file"].split(".")[0])
            self._os.execute("mv {} {}".format(embedded_directory, sut_path), self._command_timeout)
            self.yum_install("libaio-devel")
            self.yum_install("\"Development Tools\"", group=True)
            result = self._os.execute("cd {}; make && make install".format(sut_path), self._command_timeout)
            if "error" in result.stderr:
                raise RuntimeError("Failed to make diskspd.  Failure message: {}".format(result.stderr))
            self._log.debug("Successfully built diskspd.")
            return sut_path

        else:
            self._log.error("DiskSpd Tool is not supported on OS '%s'" % self._os.sut_os)
            raise NotImplementedError("DiskSpd Tool is not supported on OS '%s'" % self._os.sut_os)

    def install_stream_tool(self):
        """
         This method copy the Stream tool from host machine to sut
         :raise: RuntimeError - If execute method fails to run the commands
         :return: Installed stream tool path
         """
        if OperatingSystems.WINDOWS == self.sut_os:
            artifactory_name = ArtifactoryName.DictWindowsTools[ArtifactoryTools.STREAM_WIN_FILE]
            tool_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
            # Copy stream zip file to sut and unzip it
            return self._common_content_lib.copy_zip_file_to_sut(self.stream_constants["STREAM_WIN_FILE"].split('.')[
                                                                     0], tool_path)

        elif OperatingSystems.LINUX == self.sut_os:
            # get Linux SUT home folder name
            ret_val = self._os.execute("echo $HOME", self._command_timeout)
            if ret_val.cmd_failed():
                log_error = "Failed to run 'echo $HOME' command with return value = '{}' and " \
                            "std_error='{}'..".format(ret_val.return_code, ret_val.stderr)
                self._log.error(log_error)
                raise RuntimeError(log_error)

            home_folder = str(ret_val.stdout).strip('\n')
            sut_stream_path = Path(os.path.join(home_folder, self.stream_constants["STREAM_FOLDER_NAME"])).as_posix()

            # delete the folder in SUT if exists
            command_remove_dir = "rm -rf {}".format(sut_stream_path)
            command_result = self._os.execute(command_remove_dir, self._command_timeout)
            if command_result.cmd_failed():
                log_error = "Failed to run command '{}' with return value = '{}' and std_error='{}'..".format(
                    command_remove_dir, command_result.return_code, command_result.stderr)
                self._log.error(log_error)
                raise RuntimeError(log_error)

            # create Stream folder in sut
            command_make_dir = "mkdir {}".format(sut_stream_path)
            command_result = self._os.execute(command_make_dir, self._command_timeout)
            if command_result.cmd_failed():
                log_error = "Failed to run command '{}' with return value = '{}' and std_error='{}'.." \
                    .format(command_make_dir, command_result.return_code, command_result.stderr)
                self._log.error(log_error)
                raise RuntimeError(log_error)

            # copy Stream tar file to SUT
            host_platform_stream_path = self.get_stream_file_path()
            self._os.copy_local_file_to_sut(host_platform_stream_path, sut_stream_path)

            # extract stream tar file
            command_extract_tar_file = "tar xvzf {}".format(self.stream_constants["STREAM_LINUX_FILE"])
            command_result = self._os.execute(command_extract_tar_file, self._command_timeout, cwd=sut_stream_path)
            if command_result.cmd_failed():
                log_error = "Failed to run {} command with return value = '{}' and std_error='{}'.." \
                    .format(command_extract_tar_file, command_result.return_code, command_result.stderr)
                self._log.error(log_error)
                raise RuntimeError(log_error)

            self._log.info("The file '{}' has been decompressed "
                           "successfully ..".format(self.stream_constants["STREAM_LINUX_FILE"]))
            return sut_stream_path

        else:
            self._log.error("Stream tool  is not supported on OS '%s'" % self._os.sut_os)
            raise NotImplementedError("Stream tool is not supported on OS '%s'" % self._os.sut_os)

    def get_stream_file_path(self):
        """
        Function to get Stream tool path
        :return: Stream tool path.
        :raise: RuntimeError: will raise specified os does not support the Stream test
        :raise: IOError: Will raise when the specified file is not existed in the path.
        """
        if OperatingSystems.LINUX == self._os.os_type:
            artifactory_name = ArtifactoryName.DictLinuxTools[ArtifactoryTools.STREAM_LINUX_FILE]
            stream_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
        else:
            log_error = "Stream tool not supported on OS '%s'" % str(self._os.os_type)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        if not os.path.isfile(stream_path):
            log_error = "Stream tool  '%s' does not exists" % str(stream_path)
            self._log.error(log_error)
            raise IOError(log_error)
        return stream_path

    def copy_mcelog_binary_to_sut(self):
        """
        This method is to copy mcelog binary file to SUT
        """
        if self._os.os_type == OperatingSystems.WINDOWS or self._common_content_lib.get_platform_family() != \
                ProductFamilies.SPR:
            return
        else:
            host_folder_path = self._artifactory_obj.download_tool_to_automation_tool_folder(tool_name="mcelog")
            self._os.execute("mv /usr/sbin/mcelog /usr/sbin/mcelog.old", self._command_timeout)
            self._os.copy_local_file_to_sut(host_folder_path, "/usr/sbin/")
            self._os.execute("chmod +777 mcelog", self._command_timeout, "/usr/sbin/")

    def get_mcelog_conf_file_path(self):
        """
        Function to get Mcelog Conf path.

        :param: os_type: Linux.
        :return: mcelog_conf_file_path.
        :raise: NotImplementedError: For OS other than Linux this exception will raise.
        :raise: IOError: Will raise when the specified file is not existed in the path.
        """

        if OperatingSystems.WINDOWS == self.sut_os:
            log_error = "Not Implemeted Installation of MceLog conf on Windows Sut"
            self._log.error(log_error)
            raise NotImplementedError(log_error)
        elif OperatingSystems.LINUX == self.sut_os:
            artifactory_name = ArtifactoryName.DictLinuxTools[ArtifactoryTools.MCE_LOG_CONFIG_FILE_NAME]
            mcelog_conf_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)

        else:
            self._log.error("Mcelog.conf is not supported on OS '%s'" % self._os.sut_os)
            raise NotImplementedError("Mcelog.conf is not supported on OS '%s'" % self._os.sut_os)

        if not os.path.isfile(mcelog_conf_file_path):
            self._log.error("Mcelog.conf script '%s' does not exists" % str(mcelog_conf_file_path))
            raise IOError("Mcelog.conf script '%s' does not exists" % str(mcelog_conf_file_path))

        return mcelog_conf_file_path

    def copy_mcelog_conf_to_sut(self):
        """
        Copy Mcelog.conf file to sut

        :return: None
        """
        if OperatingSystems.LINUX != self._os.os_type:
            return

        self._log.info("Copying mcelog.conf file to SUT under /etc/mcelog folder...")

        # get Linux SUT home folder name
        dir = "/etc/mcelog"
        ret_val = self._os.execute("cd /etc/mcelog", self._command_timeout)
        if ret_val.cmd_failed():
            self._log.error("Failed to execute the command {}".format(ret_val))
            raise RuntimeError("Failed to execute the command {} and the "
                               "error is {}..".format(ret_val, ret_val.stderr))
        sut_mcelog_path = Path(os.path.join(dir, self.MCELOG_CONSTANTS[
            "mcelog_conf_file_name"])).as_posix()

        # copy tar file to SUT
        host_ras_tools_path = self.get_mcelog_conf_file_path()

        self._os.copy_local_file_to_sut(host_ras_tools_path, sut_mcelog_path)
        self._log.info("mcelog.conf file has been copied to sut Successfully")

    def install_dcpmm_platform_cycler_linux(self):
        """
        Linux environment dcpmm platform cycler installer.
        1. Copy dcpmm platform cycler tool tar file to Linux SUT.
        2. Decompress tar file under user home folder.

        :return: None
        """
        self._log.info("Copying platform cycler tar file to SUT under home folder...")

        # get Linux SUT home folder name
        ret_val = self._os.execute("echo $HOME", self._command_timeout)
        if ret_val.cmd_failed():
            self._log.error("Failed to execute the command {}".format(ret_val))
            raise RuntimeError("Failed to execute the command {} and the "
                               "error is {}..".format(ret_val, ret_val.stderr))
        home_folder = str(ret_val.stdout).strip('\n')
        sut_platform_cycler_path = Path(os.path.join(home_folder, self.platform_cycler_constants[
            "PLATFORM_CYCLER_FOLDER_NAME"])).as_posix()

        # delete the folder in SUT if exists
        verify_rm_cmd = self._os.execute("rm -rf {}".format(sut_platform_cycler_path), self._command_timeout)

        if verify_rm_cmd.cmd_failed():
            self._log.error("Failed to execute the command {}".format(verify_rm_cmd))
            raise RuntimeError("Failed to execute the command {} and the "
                               "error is {}..".format(verify_rm_cmd, verify_rm_cmd.stderr))

        # create platform_cycler folder
        verify_mkdir_cmd = self._os.execute("mkdir {}".format(sut_platform_cycler_path), self._command_timeout)

        if verify_mkdir_cmd.cmd_failed():
            self._log.error("Failed to execute the command {}".format(verify_mkdir_cmd))
            raise RuntimeError("Failed to execute the command {} and the "
                               "error is {}..".format(verify_mkdir_cmd, verify_mkdir_cmd.stderr))

        # delete log folder as well
        verify_rm_rf_cmd = self._os.execute("rm -rf {}".format(self.platform_cycler_constants[
                                                                   "LINUX_PLATFORM_CYCLER_LOG_FOLDER"]),
                                            self._command_timeout)

        if verify_rm_rf_cmd.cmd_failed():
            self._log.error("Failed to execute the command {}".format(verify_rm_rf_cmd))
            raise RuntimeError("Failed to execute the command {} and the "
                               "error is {}..".format(verify_rm_rf_cmd, verify_rm_rf_cmd.stderr))
        # copy tar file to SUT
        host_platform_cycler_path = self.get_dcpmm_cycler_tools_file_path()

        self._os.copy_local_file_to_sut(host_platform_cycler_path, sut_platform_cycler_path)

        # extract platform cycler tar file
        verify_untar_cmd = self._os.execute("tar xvzf {}".format(self.dcpmm_platform_cycler_constant[
                                                                     "DCPMM_PLATFORM_CYCLER_FILE"]),
                                            self._command_timeout, cwd=sut_platform_cycler_path)

        if verify_untar_cmd.cmd_failed():
            self._log.error("Failed to execute the command {}".format(verify_untar_cmd))
            raise RuntimeError("Failed to execute the command {} and the "
                               "error is {}..".format(verify_untar_cmd, verify_untar_cmd.stderr))
        self._log.info("The file '{}' has been decompressed "
                       "successfully ..".format(self.dcpmm_platform_cycler_constant["DCPMM_PLATFORM_CYCLER_FILE"]))

        self.platform_cycler_extract_path = Path(os.path.join(sut_platform_cycler_path,
                                                              self.platform_cycler_constants[
                                                                  "PLATFORM_CYCLER_EXTRACT_FOLDER_NAME"])).as_posix()
        return self.platform_cycler_extract_path

    def install_dcpmm_platform_cycler(self):
        """
        DCPMM Platform cycler installer.
        1. Copy the file to SUT and installed it.

        :return: dcpmm platform cycler path.
        :raise: NotImplementedError: For OS other than Linux this exception will raise.
        """
        if OperatingSystems.WINDOWS == self.sut_os:
            # TODO
            raise NotImplementedError
        elif OperatingSystems.LINUX == self.sut_os:
            return self.install_dcpmm_platform_cycler_linux()
        else:
            self._log.error("Platform cycler is not supported on OS '%s'" % self._os.sut_os)
            raise NotImplementedError("Platform cycler is not supported on OS '%s'" % self._os.sut_os)

    def get_dcpmm_cycler_tools_file_path(self):
        """
        Function to get dcpmm platform cycler path .

        :param: os_type: Windows.
        :return: dcpmm platform cycler path.
        :raise: NotImplementedError: For OS other than Linux this exception will raise.
        """

        if OperatingSystems.WINDOWS == self.sut_os:
            # TODO: need add code for windows
            raise NotImplementedError
        elif OperatingSystems.LINUX == self.sut_os:
            artifactory_name = ArtifactoryName.DictLinuxTools[ArtifactoryTools.DCPMM_PLATFORM_CYCLER_FILE]
            dcpmm_platform_cycler_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
        else:
            self._log.error("DCPMM cycler tool not supported on OS '%s'" % self._os.sut_os)
            raise NotImplementedError("DCPMM cycler tool not supported on OS '%s'" % self._os.sut_os)
        return dcpmm_platform_cycler_path

    def install_stream_zip_file(self):
        """
        This function is used to install runme.sh file in stream.zip file and giving chmod permissions to
         runme.sh, stream_omp_NTW, stream_omp_RFO

        :return: tool_path: stream installed path
        """
        tool_path = None
        try:
            artifactory_name = ArtifactoryName.DictLinuxTools[ArtifactoryTools.STREAM_ZIP_FILE]
            host_tool_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
            tool_path = self._common_content_lib.copy_zip_file_to_linux_sut(
                self.stream_zip_constants["STREAM_ZIP_FILE"].split('.')[0],
                host_tool_path)
            self._common_content_lib.execute_sut_cmd("chmod +x runme.sh", "Giving executable permissions",
                                                     self._command_timeout, cmd_path=tool_path)
            self._common_content_lib.execute_sut_cmd("sed -i 's/\r//' runme.sh", "To remove ^M errors",
                                                     self._command_timeout, cmd_path=tool_path)
            self._common_content_lib.execute_sut_cmd(
                "chmod +x {}".format(self.stream_zip_constants["stream_omp_NTW_FILE"]),
                "Giving executable permissions", self._command_timeout,
                cmd_path=tool_path)
            self._common_content_lib.execute_sut_cmd(
                "chmod +x {}".format(self.stream_zip_constants["stream_omp_RFO_FILE"]),
                "Giving executable permissions", self._command_timeout,
                cmd_path=tool_path)
        except Exception as ex:
            log_error = "error in executing te function install_stream_zip_file"
            self._log.error(log_error)
            RuntimeError(ex)

        return tool_path

    def install_burnintest(self):
        """Installs the BIT"""
        if self.sut_os == OperatingSystems.LINUX:
            return self.install_burnin_linux()
        elif self._os.os_type == OperatingSystems.WINDOWS:
            return self.install_burnin_windows()
        else:
            raise NotImplementedError("BurnInTest is not implemented for %s"
                                      % self.sut_os)

    def install_dpdk(self):
        """
        This method installs dpdk on sut by running below commands:
        1. export RTE_SDK=/usr/src/(check where dpdk is extracted)
        2. export RTE_TARGET=x86_64-native-linuxapp-gcc
        3. find -exec touch \{\} \;
        4. make install DESTDIR=dpdk-install T=x86_64-native-linuxapp-gcc

        :return: returns Path where dpdk is installed
        """
        find_cmd = "find $(pwd) -type d -name 'dpdk-*'"
        yum_package_list = ["elfutils-libelf-devel", "numactl-devel"]
        set_rte_target_var = "export RTE_TARGET=x86_64-native-linuxapp-gcc"
        make_command = "make install DESTDIR=dpdk-install T=x86_64-native-linuxapp-gcc"
        exec_touch_cmd = "find -exec touch \{\} \;"

        artifactory_name = self.dpdk_file_name
        host_tool_name = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)

        # Copy the DPDK file to SUT
        sut_folder_path = self._common_content_lib.copy_zip_file_to_linux_sut(self.dpdk_properties["DPDK_FOLDER_NAME"],
                                                                              host_tool_name)
        dpdk_dir_path = self._common_content_lib.execute_sut_cmd(find_cmd, "find dpdk dir path",
                                                                 self._command_timeout, sut_folder_path)
        dpdk_dir_name = os.path.split(dpdk_dir_path)[-1].strip()
        self._log.debug("DPDK directory name is '{}'".format(dpdk_dir_name))
        self._common_content_lib.execute_sut_cmd("cp -RTf {} {}".format(str(sut_folder_path),
                                                                        str(self.dpdk_properties["DPDK_FOLDER_PATH"])),
                                                 "copy file", self._command_timeout)
        self._log.info("DPDK file is extracted and copied to '{}' folder successfully".
                       format(self.dpdk_properties["DPDK_FOLDER_PATH"]))
        # Installing dependency packages
        for each_package in yum_package_list:
            self.yum_install(each_package)
        # Installing Development tools
        self.install_development_tool_linux()
        # Dpdk path in sut
        dpdk_path = Path(os.path.join(self.dpdk_properties["DPDK_FOLDER_PATH"], dpdk_dir_name)).as_posix()
        set_rte_sdk_var = "export RTE_SDK={}".format(dpdk_path)
        # Set environment variables
        self._common_content_lib.execute_sut_cmd(set_rte_sdk_var, "Set Env variable",
                                                 self._command_timeout,
                                                 cmd_path=dpdk_path)
        self._log.debug("Environment variable RTE_SDK is set successfully ")

        self._common_content_lib.execute_sut_cmd(set_rte_target_var, "Set Env variable",
                                                 self._command_timeout,
                                                 cmd_path=dpdk_path)
        self._log.debug("Environment variable RTE_TARGET is set successfully ")
        self._common_content_lib.execute_sut_cmd(exec_touch_cmd, "touch cmd",
                                                 self._command_timeout,
                                                 cmd_path=dpdk_path)
        self._log.debug("Touch command executed successfully ")
        # Make install command
        command_result = self._common_content_lib.execute_sut_cmd(make_command, "make install",
                                                                  2 * self._command_timeout, cmd_path=dpdk_path)
        self._log.debug("Make command output is '{}'".format(command_result))

        if self.SUCCESS_DPDK_INSTALL not in command_result:
            raise RuntimeError("Installation of DPDK failed...")

        self._log.info("Installation of DPDK is done successfully ")

        return dpdk_path

    def install_itp_xmlcli(self):
        """
        Copies the xmlcli package to use with itp interface to automation folder.
        :return: itp_xmlcli install path.
        :raises: RuntimeError - if any runtime error during copy to automation folder..
        """
        self._log.info("Installing ITP xmllci on host..")
        exec_os = platform.system()
        try:
            automation_folder = Framework.CFG_BASE[exec_os]
        except KeyError:
            err_log = "Error - execution OS " + str(exec_os) + " not supported!"
            self._log.error(err_log)
            raise KeyError(err_log)

        xmlcli_path = os.path.join(automation_folder,
                                   self._common_content_configuration.get_xmlcli_tools_name().split('.')[0])
        self._log.debug("Checking and downloading itp xmlcli version- {} from Artifactory".format(
            self._common_content_configuration.get_xmlcli_tools_name().split('.')[0]))
        if not os.path.exists(xmlcli_path):
            artifactory_name = self._common_content_configuration.get_xmlcli_tools_name()
            host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
            self._common_content_lib.extract_zip_file_on_host(host_path, automation_folder)

        try:
            import pysvtools.xmlcli.XmlCli as cli
            self._log.info("ITP xmllci already installed on host..")
            self._log.info("Setting AuthenticateXmlCliApis to True...")
            cli.clb.AuthenticateXmlCliApis = True
        except ImportError:
            # install xmlcli
            py_path = str(sys.executable)
            setup_path = os.path.join(xmlcli_path, "setup.py")
            command_line = py_path + " " + setup_path + " install"
            process_obj = subprocess.Popen(command_line, cwd=xmlcli_path, stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, shell=True)
            stdout, stderr = process_obj.communicate()
            self._log.info(stdout)

            if process_obj.returncode != 0:
                log_error = "The command '{}' failed with error '{}' ...".format(command_line, stderr)
                self._log.error(log_error)
                raise RuntimeError(log_error)
            self._log.info("XmlCli package '{}' installed successfully...".format(xmlcli_path))
            import pysvtools.xmlcli.XmlCli as cli
            self._log.info("Setting AuthenticateXmlCliApis to True...")
            cli.clb.AuthenticateXmlCliApis = True

    def install_rdt(self):
        """
        This function installs the RDT tool in sut
        1. Copy intel-cmt-cat-master to SUT
        2. find . -type f | xargs -n 5 touch
        3. make clean
        4. make uninstall
        5. make
        6. make install
        7. echo /usr/local/lib > /etc/ld.so.conf.d/kernel-3.10.0-957.el7.x86_64.conf
        8. ldconfig

        :return: None
        """
        rdt_file_name = os.path.split(self.rdt_file_path)[-1].strip()
        echo_cmd = "echo /usr/local/lib > /etc/ld.so.conf.d/kernel-*.conf"
        cmd_to_install_dev_tools = 'echo y | yum group install -y "Development Tools"'
        find_cmd = "find $(pwd) -type d -name 'intel-cmt-*'"
        make_cmd = "make"
        make_install_cmd = "make install"
        ldconfig_cmd = "ldconfig"
        make_clean_cmd = "make clean"
        make_uninstall_cmd = "make uninstall"
        clock_align_cmd = "find . -type f | xargs -n 5 touch"
        modprobe_cmd = "modprobe msr"

        self._log.info("Installing RDT on sut")

        def extract_rdt_tool():
            """
            This local method extracts the rdt tool zip file and install Development tools

            :return:  intel-cmt-cat-master folder path
            """
            # Copy file from C:/Automation/BKC/Tools to src/lib/collateral folder
            collateral_path = self._common_content_lib.get_collateral_path()
            copy(self.rdt_file_path, collateral_path)

            # Copy the RDT file to SUT
            sut_folder_path = self._common_content_lib.copy_zip_file_to_linux_sut(RDTConstants.RDT_FOLDER,
                                                                                  self.rdt_file_path)

            rdt_folder_loc = self._common_content_lib.execute_sut_cmd(find_cmd, "find command",
                                                                      self._command_timeout, cmd_path=sut_folder_path)
            self._log.debug("Intel-cmt-cat location output is '{}'".format(rdt_folder_loc))

            # Installing Development tools
            if LinuxDistributions.Cnos.lower() not in [self._os.os_subtype.lower()]:
                command_result = self._common_content_lib.execute_sut_cmd(cmd_to_install_dev_tools,
                                                                          "Install development tools",
                                                                          self._command_timeout)
                self._log.debug("Installation of 'Development Tools' is done successfully with output '{}'"
                                .format(command_result))

            self._log.debug("RDT installed folder  :{}".format(rdt_folder_loc.strip()))
            return rdt_folder_loc.strip()

        def uninstall_rdt_tool(rdt_folder_loc):
            """
            This method aligns the clock and do uninstall rdt

            :param rdt_folder_loc: intel-cmt-cat-master folder path
            :return: None
            """

            command_result = self._common_content_lib.execute_sut_cmd(clock_align_cmd,
                                                                      "rdt clock align cmd", self._command_timeout,
                                                                      cmd_path=rdt_folder_loc)
            self._log.debug("Clock align command output is :'{}'".format(command_result))

            command_result = self._common_content_lib.execute_sut_cmd(make_clean_cmd, "rdt make clean",
                                                                      self._command_timeout, cmd_path=rdt_folder_loc)
            self._log.debug("Make clean command output is :'{}'".format(command_result))

            command_result = self._common_content_lib.execute_sut_cmd(make_uninstall_cmd, "rdt make uninstall",
                                                                      self._command_timeout, cmd_path=rdt_folder_loc)
            self._log.debug("Make uninstall command output is :'{}'".format(command_result))

        def install_rdt_tool(rdt_folder_loc):
            """
            This method installs the rdt tool

            :param rdt_folder_loc: intel-cmt-cat-master folder path
            :return: None
            """

            command_result = self._common_content_lib.execute_sut_cmd(make_cmd, "rdt make cmd", self._command_timeout,
                                                                      cmd_path=rdt_folder_loc)
            self._log.debug("Make command output is :'{}'".format(command_result))

            command_result = self._common_content_lib.execute_sut_cmd(make_install_cmd, "rdt make install cmd",
                                                                      self._command_timeout, cmd_path=rdt_folder_loc)
            self._log.debug("Make install command output is :'{}'".format(command_result))

            self._common_content_lib.execute_sut_cmd(echo_cmd, "rdt {} cmd".format(echo_cmd), self._command_timeout,
                                                     cmd_path=rdt_folder_loc)

            self._common_content_lib.execute_sut_cmd(ldconfig_cmd, "rdt ldconfig cmd", self._command_timeout,
                                                     cmd_path=rdt_folder_loc)

            self._common_content_lib.execute_sut_cmd(modprobe_cmd, "modprobe cmd", self._command_timeout)

        rdt_folder_path = extract_rdt_tool()
        uninstall_rdt_tool(rdt_folder_path)
        install_rdt_tool(rdt_folder_path)

    def install_qat(self, configure_spr_cmd=None):
        """
        This method installs QAT on sut by running below commands:
        1. tar -xvf ./QAT1.7.L.4.9.0-00008.tar.gz
        2. ./configure
        3. make
        4. make install

        :return: None
        """
        self._log.info("Installing QAT")
        qat_file_name = os.path.split(self.qat_file_path)[-1].strip()
        cmd_to_install_dep_pack = "echo y | yum install -y elfutils-libelf-devel libudev-devel"
        cmd_to_install_dev_tools = 'echo y | yum group install "Development Tools"'
        qat_folder_name = "QAT"
        configure_cmd = "./configure"
        make_command = "make"
        make_install_cmd = "make install"

        artifactory_name = qat_file_name
        qat_host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
        # Copy the QAT file to SUT
        sut_folder_path = self._common_content_lib.copy_zip_file_to_linux_sut(qat_folder_name, qat_host_path)
        self._log.info("QAT file is extracted and copied to SUT path {}".format(sut_folder_path))
        # Install QAT tool in EGS Platform
        command_result = self._common_content_lib.execute_sut_cmd(cmd_to_install_dep_pack, "Install require tools",
                                                                  self._command_timeout)
        self._log.debug("Installation of dependency packages is done successfully with output '{}'"
                        .format(command_result))
        if self._platform == ProductFamilies.SPR:
            self.spr_qat_installation(sut_folder_path, configure_spr_cmd=configure_spr_cmd)
        else:
            # Installing QAT Tool for other platforms
            # Installing Development tools
            command_result = self._common_content_lib.execute_sut_cmd(cmd_to_install_dev_tools,
                                                                      "Install development tools",
                                                                      self._command_timeout)
            self._log.debug("Installation of 'Development Tools' is done successfully with output '{}'"
                            .format(command_result))
            # Configuring the QAT Tool
            command_result = self._common_content_lib.execute_sut_cmd(configure_cmd, "run configure command",
                                                                      self._command_timeout, sut_folder_path)
            self._log.debug("Configuring the QAT Tool file successfully {}".format(command_result))
            # make and compiling the files in QAT Tool folder
            command_result = self._common_content_lib.execute_sut_cmd(make_command, "run make command",
                                                                      self._command_timeout, sut_folder_path)
            self._log.debug("make and compiling the files QAT Tool folder {}".format(command_result))
            # make install command
            command_result = self._common_content_lib.execute_sut_cmd(make_install_cmd, "run make Install command",
                                                                      self._command_timeout, sut_folder_path)
            self._log.debug("Installation of QAT is done successfully {}".format(command_result))

    def copy_collateral_script(self, script_name, sut_path):
        host_script_path = os.path.join(self._common_content_lib.get_project_src_path(),
                                        r"src\collateral_scripts", script_name)
        self._log.info("Copying the collateral script '{}' from host to SUT "
                       "path '{}'..".format(host_script_path, sut_path))
        self._os.copy_local_file_to_sut(host_script_path, sut_path)

    def copy_smartctl_exe_file_to_sut(self):
        """
        This Function is to copy the smartctl exe file to sut(Only For Windows)

        :raise: IOError- if exe file is not available
        """
        if OperatingSystems.WINDOWS == self._os.os_type:
            artifactory_name = ArtifactoryName.DictWindowsTools[ArtifactoryTools.SMART_CTL]
            smartctl_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
            if not os.path.isfile(smartctl_path):
                log_error = "{} does not exists".format(smartctl_path)
                self._log.error(log_error)
                raise IOError(log_error)
            # copying file to windows SUT in C:\\ from host
            self._os.copy_local_file_to_sut(smartctl_path, self.C_DRIVE_PATH)
            smart_tools_folder = "smart_tools"
            if not self._os.check_if_path_exists(smart_tools_folder):
                self._common_content_lib.execute_sut_cmd("smartctl_win32_setup.exe /S /D=" +
                                                     self.C_DRIVE_PATH + smart_tools_folder, "install systemctl tool",
                                                     self._command_timeout, self.C_DRIVE_PATH)
                self._log.info("{} successfully installed.".format((smart_tools_folder)))
            self._log.info("{} already exists.".format((smart_tools_folder)))

    def install_iwvss(self):
        """
        To install iwVSS tool

        :return: iwvss_installed_path
        """
        if OperatingSystems.WINDOWS == self.sut_os:
            iwvss_exe_file_name, licence_key_file_name = \
                self._common_content_configuration.get_iwvss_exe_licence_file_name()
            self._log.info("iwVSS tool exe file name from the configuration xml is : {}".format(iwvss_exe_file_name))
            host_iwvss_path = self._artifactory_obj.download_tool_to_automation_tool_folder(iwvss_exe_file_name)
            self._log.info("iwVSS tool path in host is : {}".format(host_iwvss_path))

            # delete the folder in Window SUT
            self._common_content_lib.windows_sut_delete_folder(self.C_DRIVE_PATH,
                                                               self.IWVSS_CONSTANTS["IWVSS_SUT_FOLDER_NAME"])

            self._common_content_lib.execute_sut_cmd(
                "mkdir {}".format(self.IWVSS_CONSTANTS["IWVSS_SUT_FOLDER_NAME"]), "create folder",
                self._command_timeout, self.C_DRIVE_PATH)

            iwvss_executer_path = Path(
                os.path.join(self.C_DRIVE_PATH, self.IWVSS_CONSTANTS["IWVSS_SUT_FOLDER_NAME"])).as_posix()

            # To copy exe file to SUT
            self._os.copy_local_file_to_sut(source_path=host_iwvss_path, destination_path=iwvss_executer_path)

            self._common_content_lib.execute_sut_cmd('"{}" /S'.format(iwvss_exe_file_name), "Install iwVSS",
                                                     self._command_timeout, iwvss_executer_path)
            iwvss_installed_path = self._common_content_lib.execute_sut_cmd(r"where /R C:\ ctc.exe", "Find the path of "
                                                                                                     "iwVSS",
                                                                            self._command_timeout, iwvss_executer_path)

            iwvss_installed_path = Path(iwvss_installed_path).parent
            self._log.info("iwVSS tool has been successfully installed under '{}'".format(iwvss_installed_path))

            self._log.info("Licence key file name from the configuration xml is : {}".format(licence_key_file_name))
            host_licence_key_path = self._artifactory_obj.download_tool_to_automation_tool_folder(licence_key_file_name)
            self._log.info("Licence key path in host is : {}".format(host_licence_key_path))

            # To copy licence key to SUT
            self._os.copy_local_file_to_sut(source_path=host_licence_key_path, destination_path=iwvss_installed_path)
            return iwvss_installed_path
        else:
            log_error = "iwVSS is not supported on OS '{}'".format(self._os.sut_os)
            self._log.error(log_error)
            raise NotImplementedError(log_error)

    def install_turbo_stat_tool_linux(self):
        """
        This method installs TurboStat tool on sut by running below commands:
        1. tar -xvf ./turbostat.tar.gz

        :return: None
        """
        self._log.info("Installing TurboStat tool")
        # Copy the stress tool file to SUT
        artifactory_name = ArtifactoryName.DictLinuxTools[ArtifactoryTools.TURBOSTAT_TOOL_NAME]
        tool_name = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
        sut_folder_path = self._common_content_lib.copy_zip_file_to_linux_sut(TurboStatConstants.
                                                                              TURBOSTAT_TOOL_FOLDER_NAME,
                                                                              tool_name)
        self._log.info("TurboStat tool file is extracted and copied to SUT path {}".format(sut_folder_path))
        executable_path = sut_folder_path + TurboStatConstants.COMPLETE_TURBOSTAT_TOOL_PATH
        return executable_path

    def yum_verify_package(self, package_name):
        """
        This method verifies if the linux package is present in the yum installed list
        :return : True if package is already installed
        :raise content_exceptions.TestSetupError if package verification is  unsuccessful
        """
        cmd_line = "yum list installed {}".format(package_name)
        cmd_result = self._os.execute(cmd_line, self._command_timeout)
        self._log.debug(cmd_result)
        if cmd_result.cmd_passed():
            if str(package_name).lower() in str(cmd_result.stdout).lower():
                self._log.info("The package '{}' verification is successfully".format(package_name))
                return True
            raise content_exceptions.TestSetupError("The package '{}' verification is unsuccessful".format(package_name))

    def yum_reinstall(self, package_name, flags=None, cmd_path=None):
        """
        This method will reinstall the given linux package

        :param package_name: name of the linux package to be installed
        :param flags: flags that will apply when installing the package, except '-y'
        :param cmd_path: path of the execute command
        :type: bool
        :return : Function returns if package is already installed
        :raise : raise: contents_exception.TestSetupError If unable to install yum packages
        """
        max_attempts = 5
        is_yum_success = 0
        wait_delay = 5
        # check if package already installed
        cmd_line = "yum list installed {}".format(package_name)
        cmd_result = self._os.execute(cmd_line, self._command_timeout)
        if cmd_result.cmd_passed():
            if str(package_name).lower() in str(cmd_result.stdout).lower():
                self._log.info("The package '{}' is already installed.".format(package_name))
                return

        self._log.debug("reInstalling the {} package".format(package_name))

        cmd_result = self._common_content_lib.execute_sut_cmd("rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY*",
                                                              "Importing rpm key", self._command_timeout)
        self._log.debug(cmd_result)
        if flags is not None:
            package_name = package_name + " " + flags
        for no_attempts in range(max_attempts):
            try:
                self._log.debug("Running yum command for attempt {}".format(no_attempts + 1))

                install_result = self._common_content_lib.execute_sut_cmd("yum -y reinstall {} --allowerasing".format(package_name),
                                                                          "yum reinstall cmd", self._command_timeout,
                                                                          cmd_path)

                self._log.debug("Yum reinstallation output is: {}".format(install_result))
                is_yum_success = 1
                break
            except Exception as ex:
                self._log.error("Error: {} for attempt {}, trying once again for command: {}".
                                format(ex, no_attempts + 1, package_name))
            time.sleep(wait_delay)
        if not is_yum_success:
            raise content_exceptions.TestSetupError("Command {} execution failed after {} attempts".format(
                package_name, max_attempts))
        self._log.info("Successfully reinstalled the {} package".format(package_name))

    def yum_install(self, package_name, flags=None, cmd_path=None, group=False):
        """
        This method will install the given linux package

        :param package_name: name of the linux package to be installed
        :param flags: flags that will apply when installing the package, except '-y'
        :param cmd_path: path of the execute command
        :param group: if pkg name is a group install (such as Development Tools)
        :type: bool
        :return : Function returns if package is already installed
        :raise : raise: contents_exception.TestSetupError If unable to install yum packages
        """
        max_attempts = 5
        is_yum_success = 0
        wait_delay = 5
        if self._os.os_subtype.upper() in ["SLES", "CNOS"]:
            install_cmd = "zypper --non-interactive install {}".format(package_name)
            cmd_result = self._os.execute(install_cmd, self._command_timeout)
            self._log.debug("Yum installation stdout is: {}".format(cmd_result.stdout))
            self._log.error("Yum installation stderr is: {}".format(cmd_result.stderr))
            if cmd_result.cmd_failed():
                raise content_exceptions.TestSetupError("failed to install the package {}".format(package_name))
            self._log.info("The package '{}' is successfully installed.".format(package_name))
            return True
        else:
            # check if package already installed
            cmd_line = "yum list installed {}".format(package_name)
            cmd_result = self._os.execute(cmd_line, self._command_timeout)
            if cmd_result.cmd_passed():
                if str(package_name).lower() in str(cmd_result.stdout).lower():
                    self._log.info("The package '{}' is already installed.".format(package_name))
                    return

            self._log.debug("Installing the {} package".format(package_name))

            cmd_result = self._common_content_lib.execute_sut_cmd("rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY*",
                                                                  "Importing rpm key", self._command_timeout)
            self._log.debug(cmd_result)
            if flags is not None:
                package_name = package_name + " " + flags
            for no_attempts in range(max_attempts):
                try:
                    self._log.debug("Running yum command for attempt {}".format(no_attempts + 1))
                    if not group:
                        install_result = self._common_content_lib.execute_sut_cmd("yum -y install {} --allowerasing".format(package_name),
                                                                                  "yum install cmd", self._command_timeout,
                                                                                  cmd_path)
                    else:
                        install_result = self._common_content_lib.execute_sut_cmd(
                            "yum -y groupinstall {} --allowerasing".format(package_name),
                            "yum install cmd", self._command_timeout,
                            cmd_path)
                    self._log.debug("Yum installation output is: {}".format(install_result))
                    is_yum_success = 1
                    break
                except Exception as ex:
                    self._log.error("Error: {} for attempt {}, trying once again for command: {}".
                                    format(ex, no_attempts + 1, package_name))
                time.sleep(wait_delay)
            if not is_yum_success:
                raise content_exceptions.TestSetupError("Command {} execution failed after {} attempts".format(
                    package_name, max_attempts))
            self._log.info("Successfully installed the {} package".format(package_name))

    def yum_remove(self, package_name):
        """
        This method will uninstall/remove the given linux package

        :param package_name: name of the linux package to be removed
        :return : None
        :raise : None
        """
        if self._os.os_subtype.upper() == "SLES":
            cmd = "zypper --non-interactive remove {}".format(package_name)
        else:
            cmd = "yum -y remove {}".format(package_name)
        self._log.info("Removing the {} package".format(package_name))
        uninstall_result = self._common_content_lib.execute_sut_cmd(cmd, "remove {}".format(package_name),
                                                                    self._command_timeout)
        self._log.debug(uninstall_result)
        self._log.info("Successfully removed the {} package".format(package_name))

    def install_socwatch(self):
        """
        This method installs SOCWATCH on sut by running below commands:
        1. make socwatch directory in home path
        2. copy socwatch_chrome_linux_INTERNAL.tar.gz to home/socwatch path
        3. Unzip tar -xf socwatch_chrome_linux_INTERNAL.tar.gz
        4. Goto socwatch_chrome_linux_INTERNAL
        5. Build Drivers running script  sh ./build_drivers.sh -l
        6. Goto drivers folder build the socperf1_2.ko and socwatch2_1.ko files
        7. Setup the collection environment

        :return: return socwatch directory path
        """
        find_drivers = "find $(pwd) -type d -name 'drivers'"
        build_drivers = 'sh ./build_drivers.sh -l'
        socwatch_env_cmd = 'source ./setup_socwatch_env.sh'
        list_drivers_files = 'ls *.ko'
        find_cmd = "find $(pwd) -type d -name 'socwatch_chrome_linux*'"
        find_src_folder = "find $(pwd) -type d -name 'src'"
        #sw_trace_c_file_path_sut = "socwatch_driver/src/"
        sw_trace_c_filename = "sw_trace_notifier_provider.c"
        artifactory_file_name = \
            self._common_content_configuration.get_socwatch_tool_name_config(self._os.os_type.lower())
        self._log.info("Soc watch tool name from the config xml is : {}".format(artifactory_file_name))
        sut_folder_name = artifactory_file_name.split("_")[0]
        no_driver_files_str = "No such file or directory"
        dnf_update_command = "dnf update -y --allowerasing"
        dnf_kernel_next_command = "dnf install https://emb-pub.ostc.intel.com/overlay/centos/8/202111012334/repo/x86_64/kernel-next-server-devel-5.12.0-2021.05.07_49.el8.x86_64.rpm -y"
        yum_commands_list = ["gcc", "gcc-c++", "libelf*", "elfutils-libelf-devel"]
        sed_update_command_config = self._common_content_configuration.get_sed_update_soc_watch().split(r'/')
        self._log.info("sed Update command from config is : {}".format(sed_update_command_config))
        sed_command = "sed -i 's/{}/{}/' {}".format(sed_update_command_config[0], sed_update_command_config[1],
                                                    self.EMBARGO_REPO)
        self._log.info("Installing SOCWATCH Tool")
        artifacotry_name = ArtifactoryName.DictLinuxTools[ArtifactoryTools.SOCWATCH_ZIP_FILE]
        socwatch_zip_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_file_name)
        # Copy the socwatch file to SUT
        sut_folder_path = self._common_content_lib.copy_zip_file_to_linux_sut(sut_folder_name, socwatch_zip_file_path)
        self._log.info("Socwatch file is extracted and copied to SUT path {}".format(sut_folder_path))
        # find socwatch folder path
        dir_name = self._common_content_lib.execute_sut_cmd(find_cmd, "find the socwatch file path",
                                                            self._command_timeout, sut_folder_path).split()[0]
        self._log.debug("Socwatch directory name {}".format(dir_name))

        if self._os.os_subtype.lower() == LinuxDistributions.CentOS.lower():
            sed_update_command_config = self._common_content_configuration.get_sed_update_soc_watch().split(r'/')
            self._log.info("sed Update command from config is : {}".format(sed_update_command_config))
            sed_command = "sed -i 's/{}/{}/' {}".format(sed_update_command_config[0], sed_update_command_config[1],
                                                        self.EMBARGO_REPO)
            repo_result = self._os.execute("cat {}".format(self.EMBARGO_REPO), self._command_timeout)
            self._log.debug(repo_result.stdout)
            self._log.debug(repo_result.stderr)

            # if latest word is there it will replace with the number in /etc/yum.repos.d/Intel-Embargo.repo
            if sed_update_command_config[0] in repo_result.stdout:
                cmd_result = self._os.execute(sed_command, self._command_timeout)
                self._log.debug(cmd_result.stdout)
                self._log.debug(cmd_result.stderr)

        if self._os.os_subtype.lower() == LinuxDistributions.CentOS.lower():
            os_name = self._grub_obj.get_linux_name()
            if self.CENTOS_STREAM in os_name:
                kernel_version_in_sut = self._common_content_lib.execute_sut_cmd("uname -r", "get kernel version",
                                                                                 self._command_timeout)
                kernels_avail = self._common_content_lib.execute_sut_cmd("ls /usr/src/kernels/", "Getting the kernels",
                                                                         self._command_timeout)
                if kernel_version_in_sut in kernels_avail:
                    self._log.info("SUT has CENTOS Stream, so do not required to install devel packages... "
                                   "comes with built in OS.")
            else:
                self._common_content_lib.execute_sut_cmd(
                    dnf_kernel_next_command, "Executing {}".format(dnf_kernel_next_command),
                    TimeConstants.ONE_HOUR_IN_SEC)

        # To install packages
        for each_command in yum_commands_list:
            self.yum_install(each_command)

        sw_trace_c_file_path_host = self._artifactory_obj.download_tool_to_automation_tool_folder(sw_trace_c_filename)
        src_folder_path_sut = self._common_content_lib.execute_sut_cmd(
            find_src_folder, find_src_folder, self._command_timeout, sut_folder_path)
        sw_trace_c_file_path_sut = Path(os.path.join(src_folder_path_sut.strip(), sw_trace_c_filename)).as_posix()
        self._log.info("Sw Trace C file Path in Host is : {}".format(sw_trace_c_file_path_host))
        self._log.info("Sw Trace C file Path in SUT is : \n{}".format(sw_trace_c_file_path_sut))
        # copying .c file to the SUT.
        self._os.copy_local_file_to_sut(source_path=sw_trace_c_file_path_host,
                                        destination_path=sw_trace_c_file_path_sut)

        # To Build the Intel SoC Watch driver
        cmd_output = self._os.execute(build_drivers, self._command_timeout,
                                      dir_name)  # "run sh ./build_drivers.sh -l command",
        self._log.debug("Socwatch build command output :\n{}".format(cmd_output.stdout))
        self._log.error("Socwatch build command output :\n{}".format(cmd_output.stderr))
        driver_path = self._common_content_lib.execute_sut_cmd(find_drivers, "find the drivers path",
                                                               self._command_timeout, sut_folder_path).split()[0]
        self._log.debug("Socwatch drivers path {}".format(driver_path))
        file_list = self._common_content_lib.execute_sut_cmd(list_drivers_files, "list of drivers inside files",
                                                             self._command_timeout, driver_path).split()
        self._log.info("Drivers file list {}".format(file_list))
        if not file_list:
            raise content_exceptions.TestError("Failed to install socwatch drivers")
        # To install Intel Soc Watch Drivers
        for file in file_list:
            sut_cmd = self._os.execute('insmod ' + driver_path + "/" + file, self._command_timeout, driver_path)
            self._log.debug("Socwatch drivers in insmod {}".format(sut_cmd.stdout))
            if no_driver_files_str in sut_cmd.stderr:
                raise content_exceptions.TestFail("% driver not found to install socwatch" % file)
        # To setup collection environment
        self._common_content_lib.execute_sut_cmd(socwatch_env_cmd, "run {} command".format(socwatch_env_cmd),
                                                 self._command_timeout, dir_name)
        self._log.debug("Socwatch installation is completed successfully in this SUT path {}".format(dir_name))
        return dir_name

    def install_validation_runner_linux(self):
        """
        This install thread runner method will copy the application folder to sut and install it

        :raise: If installation failed raise content_exceptions.TestError
        """
        unzip_command = "unzip runner_files.zip"
        install_cmd = "./install.sh"
        find_folder_name = "validation_runner"
        find_install_path = "find $(pwd) -type d -name '%s'" % find_folder_name
        success_installation = "INSTALLATION HAS COMPLETED SUCCESSFULLY"
        tool_path = self._artifactory_obj.download_tool_to_automation_tool_folder(self.RUNNER_HOST_FOLDER_NAME)
        self._log.info("Installing validation Runner application")
        sut_folder_path = self._common_content_lib.copy_zip_file_to_linux_sut(self.RUNNER_SUT_FOLDER_NAME,
                                                                              tool_path)
        self._log.debug("runner file is extracted and copied to SUT path {}".format(sut_folder_path))
        install_path = self._common_content_lib.execute_sut_cmd(find_install_path, "finding path",
                                                                self._command_timeout, "/root/runner")
        self._log.debug("Validation Runner tool path to install {}".format(install_path))
        command_result = self._common_content_lib.execute_sut_cmd(install_cmd, install_cmd, self._command_timeout,
                                                                  install_path.strip() + "/")
        self._log.debug("Validation runner installation result: {}".format(command_result))
        if success_installation not in command_result:
            raise content_exceptions.TestFail("Failed to install validation runner")

        self._log.info("Successfully installed validation runner")
        self._common_content_lib.execute_sut_cmd(unzip_command, unzip_command, self._command_timeout,
                                                 install_path.strip() + "/")
        self._log.debug("%s executed", unzip_command)

    def install_validation_runner(self):
        """
        This install thread runner method will copy the application folder to sut and install it

        :raise: If installation failed raise content_exceptions.TestError
        """
        if OperatingSystems.WINDOWS == self._os.os_type:
            raise self.install_validation_runner_windows()
        elif OperatingSystems.LINUX == self._os.os_type:
            return self.install_validation_runner_linux()

    def copy_to_collateral(self, source_path):
        """
        This method is to copy files to collateral.

        :param source_path
        :raise None
        """
        file_name = os.path.split(source_path)[-1].strip()
        try:
            collateral_path = os.path.join(self._common_content_lib.get_collateral_path(), self._os.os_type.lower())
            copy(source_path, collateral_path)
        except Exception as ex:
            raise ex
        else:
            self._log.info("Successfully copied {} file to '{}' directory...".format(file_name, collateral_path))
        return file_name

    def copy_scp_go_to_sut(self):
        """This method is to copy the scp_go executable file to SUT

        return Tuple: location of the file and the scp_go executable file name
        """
        scp_go_file_path = None
        scp_go_file_name = None
        tool_sut_locaton = None
        if OperatingSystems.WINDOWS == self.sut_os:
            scp_go_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder(self.SCP_GO_WINDOWS_FILE)
            tool_sut_locaton = self.C_DRIVE_PATH
            scp_go_file_name = self.SCP_GO_WINDOWS_FILE
        elif OperatingSystems.LINUX == self.sut_os:
            scp_go_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder(self.SCP_GO_LINUX_FILE)
            tool_sut_locaton = self.util_constants["LINUX_USR_ROOT_PATH"]
            scp_go_file_name = self.SCP_GO_LINUX_FILE
        else:
            raise NotImplementedError("SCP_GO tool not supported on OS '%s'" % self._os.sut_os)
        self._log.info("Copying {} file to SUT".format(scp_go_file_name))
        self._os.copy_local_file_to_sut(scp_go_file_path, tool_sut_locaton)
        self._log.info("Successfully copied the {} file under {}".format(scp_go_file_name, tool_sut_locaton))
        return tool_sut_locaton, scp_go_file_name

    def install_cpuid(self):
        """
        Install cpuid package in the linux sut
        """
        self._log.info("copy and install cpuid tool")
        find_file_name = "cpuid*"
        root_folder = "/root/"
        find_install_path = "find $(pwd) -type f -name '%s'" % find_file_name
        tool_path = self._artifactory_obj.download_tool_to_automation_tool_folder(self.CPUID_CONSTANTS["CPUID_ZIP_FILE"])
        sut_folder_path = self._common_content_lib.copy_zip_file_to_linux_sut(self.CPUID_CONSTANTS["CPUID_FOLDER_NAME"],
                                                                              tool_path)
        self._log.debug("Cpuid file is extracted and copied to SUT path {}".format(sut_folder_path))
        install_path = self._common_content_lib.execute_sut_cmd(find_install_path, "finding path",
                                                                self._command_timeout,
                                                                root_folder + self.CPUID_CONSTANTS[
                                                                    "CPUID_FOLDER_NAME"])
        self._log.debug("Cpuid tool path to install {}".format(install_path))
        if not install_path.strip():
            raise content_exceptions.TestFail("Unable to find the cpuid file")
        cpu_id = os.path.basename(install_path.strip())
        self.yum_install(cpu_id, flags=None, cmd_path = root_folder + self.CPUID_CONSTANTS["CPUID_FOLDER_NAME"])

    def install_bonnie_to_sut(self):
        """
        This method is to install the bonnie stress tool to SUT.

        return: install path
        raise: None
        """
        self._log.info("Installing bonnie to SUT")
        host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(BonnieTool.BONNIE_HOST_FOLDER_NAME)
        sut_folder_path = self._common_content_lib.copy_zip_file_to_linux_sut(BonnieTool.BONNIE_SUT_FOLDER_NAME,
                                                                              host_path)
        self._log.debug("bonnie file is extracted and copied to SUT path {}".format(sut_folder_path))
        install_path = self._common_content_lib.execute_sut_cmd(BonnieTool.FIND_INSTALL_PATH, "finding path",
                                                                self._command_timeout,
                                                                BonnieTool.BONNIE_HOST_FOLDER_PATH)
        return install_path

    def install_stress_tool_to_sut(self):
        """
        This method installs the stress tool to sut.

        :return: None
        """
        find_stress_dir = "find $(pwd) -type d -name 'stress*'"
        cmd_to_install_stress = "./configure && make && sudo make install"

        self._log.info("Installing stress tool to sut")
        if LinuxDistributions.Cnos.lower() not in [self._os.os_subtype.lower()]:
            self.install_development_tool_linux()

        host_tool_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
            RDTConstants.RDT_STRESS_CONSTANTS["STRESS_TAR_FILE"])
        # Copy stress tool tar file to sut
        stress_tool_dir_path = self._common_content_lib.copy_zip_file_to_linux_sut(
            RDTConstants.RDT_STRESS_CONSTANTS["STRESS_DIR"], host_tool_path)
        self._log.debug("Stress tool path in sut is '{}'".format(stress_tool_dir_path))

        stress_tool_path = (self._common_content_lib.execute_sut_cmd(find_stress_dir, find_stress_dir,
                                                                     self._command_timeout,
                                                                     cmd_path=stress_tool_dir_path)).strip()
        self._log.debug("Stress tool executable path in sut is '{}'".format(stress_tool_path))
        install_cmd_res = self._common_content_lib.execute_sut_cmd(
            cmd_to_install_stress, cmd_to_install_stress, self._command_timeout, stress_tool_path)
        self._log.debug("Stress tool installation is successful and command output is '{}'".format(install_cmd_res))

    def get_proxy_cmd(self):
        """Get proxy command with command separator"""
        command = ""
        command_separator = ";"
        env_set_cmd = 'export'
        if self._os.os_type == OperatingSystems.WINDOWS:
            command_separator = "&"
            location = self.C_DRIVE_PATH
            env_set_cmd = 'set'
        self._log.info("http_proxy=%s", CommonConstants.HTTP_PROXY)
        self._log.info("https_proxy=%s", CommonConstants.HTTPS_PROXY)
        if CommonConstants.HTTP_PROXY:
            command = command + ("%s http_proxy=%s" % (env_set_cmd, CommonConstants.HTTP_PROXY)) + command_separator
        if CommonConstants.HTTPS_PROXY:
            command = command + ("%s https_proxy=%s" % (env_set_cmd, CommonConstants.HTTPS_PROXY)) + command_separator
        return command

    def install_pip(self):
        """Install Pip"""
        command_separator = ";"
        install_pip_command = "python3 get-pip.py --trusted-host files.pythonhosted.org --trusted-host pypi.org"
        location = self.util_constants["LINUX_USR_ROOT_PATH"]
        proxy_command = self.get_proxy_cmd()
        self._log.info("Installing Pip")
        self.yum_install("wget")
        self._log.info("Downloading pip: %s", (proxy_command + self.DOWNLOAD_PIP))
        wget_output = self._common_content_lib.execute_sut_cmd(proxy_command + self.DOWNLOAD_PIP, "Download pip",
                                                               self._command_timeout, location)
        self._log.info("Download pip output:%s", wget_output)
        self._log.info("Installing pip")
        install_pip_output = self._common_content_lib.execute_sut_cmd(proxy_command + install_pip_command,
                                                                      "Install pip", self._command_timeout, location)
        self._log.debug("Install pip output:%s", install_pip_output)
        check_pip_version = self._common_content_lib.execute_sut_cmd(proxy_command + "pip --version", "check pip",
                                                                     self._command_timeout, location)
        self._log.info(check_pip_version)

    def install_python_package(self, package, trusted_hosts=["files.pythonhosted.org", "pypi.org"]):
        """Installs the python package

        param package: python package
        :return: None
        """
        self.install_pip()
        proxy_command = self.get_proxy_cmd()
        trusted_hosts_format = " --trusted-host " + " --trusted-host ".join(trusted_hosts)
        package_install_output = self._common_content_lib.execute_sut_cmd(proxy_command + "pip install %s %s" % (
            package, trusted_hosts_format), "check pip",
                                                                          self._command_timeout)
        self._log.info(package_install_output)

    def install_fio_linux(self, yum_install_fio=False):
        """
        This method is to install the fio tools on SUT.

        :param fio_package_flag
        """
        if not yum_install_fio:

            self._common_content_lib.set_datetime_on_sut()
            fio_host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(self.FIO_CONSTANTS["fio_zip_file"])
            sut_folder_path = self._common_content_lib.copy_zip_file_to_linux_sut("FIO",
                                                                                  fio_host_path)
            sut_folder_path = Path(os.path.join(sut_folder_path, self.FIO_CONSTANTS["fio_folder_name"])).as_posix()

            self._log.info("Executing 'configure' command ...")
            self._common_content_lib.execute_sut_cmd(
                "./configure", "run configure command", self._command_timeout, cmd_path=sut_folder_path)
            self._log.info("Executing 'make' command ...")
            self._common_content_lib.execute_sut_cmd(
                "make", "run make command", self._command_timeout, sut_folder_path)
            self._log.info("Executing 'make install' command ...")
            self._common_content_lib.execute_sut_cmd(
                "make install", "run make install", self._command_timeout, sut_folder_path)
        else:
            self.yum_install('fio')

    def install_ipmitool(self):
        """
        This method will install ipmitool in sut

        :raise: If installation failed raise content_exceptions.TestError
        """
        if OperatingSystems.WINDOWS == self._os.os_type:
            raise NotImplementedError
        elif OperatingSystems.LINUX == self._os.os_type:
            self.yum_install("ipmitool")

    def install_solar_hwp_native_linux(self):
        """
        This method will copy and install solar application into sut

        """
        install_pre_requisite = ["kernel-tools", "elfutils-libelf-devel"]
        self._log.info("Installing solar tool")
        solar_tool_name_config = self._common_content_configuration.get_solar_tool_name(self._os.os_type.lower())
        host_tool_path = self._artifactory_obj.download_tool_to_automation_tool_folder(solar_tool_name_config)
        sut_folder_path = self._common_content_lib.copy_zip_file_to_linux_sut(SolarHwpConstants.SOLAR_SUT_FOLDER_NAME,
                                                                              host_tool_path)
        self._log.debug("Solar file is extracted and copied to SUT path {}".format(sut_folder_path))

        # Install pre-requirements before installing ./SolarSetup.sh
        self._log.info("Installing pre-requirements list: {}".format(install_pre_requisite))
        for package in install_pre_requisite:
            self.yum_install(package)

        # Install solar tool cmd: ./SolarSetup.sh
        self._log.info("Installing Solar HWP Native Command: {}".format(SolarHwpConstants.SOLAR_SETUP))
        install_cmd_result = self._common_content_lib.execute_sut_cmd(SolarHwpConstants.SOLAR_SETUP,
                                                                      SolarHwpConstants.SOLAR_SETUP,
                                                                      self._command_timeout, sut_folder_path)
        self._log.debug("Installed Solar HWP Native:\n{}".format(install_cmd_result))

        return sut_folder_path

    def install_solar_hwp_native(self):
        """
        This install solar hwp native method will copy the application folder to sut and install it
        """
        if OperatingSystems.WINDOWS == self._os.os_type:
            return self.install_solar_hwp_native_windows()
        elif OperatingSystems.LINUX == self._os.os_type:
            return self.install_solar_hwp_native_linux()

    def install_development_tool_linux(self):
        """
        This method will install 'Development Tools' on linux SUT

        :return : Function returns if package is already installed
        :raise: contents_exception.TestSetupError If unable to install Development Tools
        """
        # check if development tools already installed
        max_attempts = 5
        is_tool_installed = 0
        wait_delay = 5
        cmd_line = 'yum grouplist "Development Tools"'
        cmd_result = self._os.execute(cmd_line, self._command_timeout)
        if cmd_result.cmd_passed():
            if "Development Tools" in cmd_result.stdout:
                self._log.info("Development Tools already installed.")
                return
        com_to_install_dev_tools = 'sudo yum -y group install "Development Tools"'
        self._log.info("Installing Development Tools")
        for no_attempts in range(max_attempts):
            try:
                install_result = self._common_content_lib.execute_sut_cmd(com_to_install_dev_tools,
                                                                          "Installing Development "
                                                                          "Tools",
                                                                          self._command_timeout)
                self._log.debug("Install Development Tools output:\n{}".format(install_result))
                is_tool_installed = 1
                break
            except Exception as ex:
                self._log.error("Error: {} for attempt {}, trying once again for command: {}".
                                format(ex, no_attempts + 1, com_to_install_dev_tools))
            time.sleep(wait_delay)

        if not is_tool_installed:
            raise content_exceptions.TestSetupError("Command {} execution failed after {} attempts".format(
                com_to_install_dev_tools, max_attempts))
        self._log.info("Successfully installed Development Tools")

    def install_hqm_driver(self, common_content_lib=None, is_vm=None):
        """
        HQM Driver Installation
        1. Copy the .txz file to sut and extract it
        2. Use make command to compile in dlb folder
        3. Use make command to compile in libdlb folder
        4. insmod the dlb2.ko file

        raise: contents_exception.TestFail if dlb2.ko kernel file not available
        """
        if common_content_lib is None:
            common_content_lib = self._common_content_lib
        self._log.info("Install HQM Driver on the SUT")
        if is_vm is not None:
            hqm_file_name = os.path.split(self.vm_hqm_file_path)[-1].strip()
        else:
            hqm_file_name = os.path.split(self.hqm_file_path)[-1].strip()
        hqm_folder_name = "HQM"
        if is_vm is not None:
            dpdk_file_name = os.path.split(self.vm_dpdk_file_path)[-1].strip()
        else:
            dpdk_file_name = os.path.split(self.dpdk_file_path)[-1].strip()
        dpdk_name, version = self.get_name_version(dpdk_file_name)
        dpdk_full_folder_name = dpdk_name + '-' + 'stable' + '-' + version
        dpdk_folder_name = "HQM/dpdk"
        make_command = "make"
        find_dlb2_kernel_file = "find $(pwd) -type f -name 'dlb2.ko' 2>/dev/null"
        find_dlb_dir_path = "find $(pwd) -type d -name 'dlb2' 2>/dev/null | grep 'driver/dlb2'"
        find_libdlb_dir_path = "find $(pwd) -type d -name 'libdlb' 2>/dev/null"
        grep_dlb_driver = "lsmod | grep dlb"
        expected_dlb_val = "dlb2"
        insmod_cmd = "insmod"
        rmmod_cmd = "rmmod"

        if is_vm is not None:
            patch_file = self.vm_dpdk_patch_file_name
        else:
            patch_file = self.dpdk_patch_file_name
        patch_cmd = "cd /root/HQM/dpdk/{};patch -Np1 < /root/HQM/dpdk/{};".format(dpdk_full_folder_name,
                                                                                  patch_file)
        dos_2_unix_cmd = "dos2unix /root/HQM/dpdk/{}".format(patch_file)
        export_cmd = "cd /root/HQM/dpdk/{};" \
                     "echo y | yum install -y meson;" \
                     "export DPDK_DIR=/root/HQM/dpdk/{}/;" \
                     "export RTE_SDK=$DPDK_DIR;" \
                     "export RTE_TARGET=installdir;" \
                     "meson setup --prefix $RTE_SDK/$RTE_TARGET builddir;" \
                     "ninja -C builddir install".format(dpdk_full_folder_name, dpdk_full_folder_name)

        build_dlb2_driver_cmd = "cd /root/HQM/driver/dlb2; make;"
        build_libdlb_cmd = "cd /root/HQM/libdlb; make;"

        hqm_host_file_path = (self._artifactory_obj.download_tool_to_automation_tool_folder(hqm_file_name)).strip()
        dpdk_host_file_path = (self._artifactory_obj.download_tool_to_automation_tool_folder(dpdk_file_name)).strip()

        common_content_lib.execute_sut_cmd_no_exception("whoami;sync;",
                                                        "executing sync command",
                                                        self._command_timeout,
                                                        cmd_path=self.ROOT,
                                                        ignore_result="ignore")
        # Remove HQM file if it already exists.
        common_content_lib.execute_sut_cmd_no_exception("find / -type f -name HQM 2>/dev/null -exec rm {} \;",
                                                        "Removing the HQM file",
                                                        self._command_timeout,
                                                        cmd_path=self.ROOT_PATH, ignore_result="ignore")
        common_content_lib.execute_sut_cmd_no_exception("find / -type d -name HQM 2>/dev/null -exec rm -r {} \;",
                                                        "Removing the HQM file",
                                                        self._command_timeout,
                                                        cmd_path=self.ROOT_PATH, ignore_result="ignore")
        common_content_lib.execute_sut_cmd_no_exception("mkdir -p '{}'".format(hqm_folder_name),
                                                        "To Create a HQM folder",
                                                        self._command_timeout,
                                                        cmd_path=self.ROOT_PATH, ignore_result="ignore")
        # Copy the HQM file to SUT
        sut_folder_path = common_content_lib.copy_zip_file_to_linux_sut(hqm_folder_name, hqm_host_file_path,
                                                                        dont_delete="True")
        sut_folder_path = sut_folder_path.strip()
        self._log.debug("HQM file is extracted and copied to SUT path {}".format(sut_folder_path))
        common_content_lib.execute_sut_cmd_no_exception("sync",
                                                        "executing sync command",
                                                        self._command_timeout,
                                                        cmd_path=self.ROOT,
                                                        ignore_result="ignore")
        # Copy the dpdk file to SUT
        dpdk_folder_path = common_content_lib.copy_zip_file_to_linux_sut(dpdk_folder_name, dpdk_host_file_path,
                                                                        dont_delete="True")
        dpdk_folder_path = dpdk_folder_path.strip()
        self._log.debug("dpdk file is extracted and copied to dpdk path in HQM {}".format(dpdk_folder_path))
        self._log.info("dpdk installed successfully")

        # execute dos2unix to patch cmd
        dos2unix_result = common_content_lib.execute_sut_cmd_no_exception(dos_2_unix_cmd,
                                                                          "executing dos2unix command to patch",
                                                                          self._command_timeout,
                                                                          cmd_path=dpdk_folder_path,
                                                                          ignore_result="ignore")
        self._log.debug("Dos2unix to patch {}".format(dos2unix_result))
        common_content_lib.execute_sut_cmd_no_exception("sync",
                                                        "executing sync command",
                                                        self._command_timeout,
                                                        cmd_path=self.ROOT,
                                                        ignore_result="ignore")
        # execute patch cmd
        hqm_driver_dpdk_path = common_content_lib.execute_sut_cmd_no_exception(patch_cmd, "executing patch command",
                                                                               self._command_timeout,
                                                                               cmd_path=dpdk_folder_path,
                                                                               ignore_result="ignore")
        hqm_driver_dpdk_path = hqm_driver_dpdk_path.strip()
        self._log.debug("HQM drivers dlb path {}".format(hqm_driver_dpdk_path))
        # export cmd
        hqm_driver_dpdk_path = common_content_lib.execute_sut_cmd_no_exception(export_cmd, "executing export command",
                                                                               self._command_timeout,
                                                                               cmd_path=dpdk_folder_path,
                                                                               ignore_result="ignore")
        hqm_driver_dpdk_path = hqm_driver_dpdk_path.strip()
        self._log.debug("HQM drivers dlb path {}".format(hqm_driver_dpdk_path))

        # build_dlb2_driver_cmd
        driver_build_result = common_content_lib.execute_sut_cmd(build_dlb2_driver_cmd,
                                                                 "executing make command for dlb",
                                                                 self._command_timeout, cmd_path=dpdk_folder_path)
        self._log.debug("HQM drivers build result {}".format(driver_build_result))

        # build_libdlb_cmd
        libdlb_build_result = common_content_lib.execute_sut_cmd(build_libdlb_cmd, "executing make command for libdlb",
                                                                 self._command_timeout, cmd_path=dpdk_folder_path)
        self._log.debug("HQM libdlb build result {}".format(libdlb_build_result))

        # Search dlb folder
        hqm_driver_dlb_path = common_content_lib.execute_sut_cmd_no_exception(find_dlb_dir_path, "find the driver path",
                                                                              self._command_timeout,
                                                                              cmd_path=self.ROOT_PATH,
                                                                              ignore_result="ignore")
        self._log.debug("HQM drivers dlb path {}".format(hqm_driver_dlb_path))
        # make and compiling the files in HQM Driver folder
        command_result = common_content_lib.execute_sut_cmd(make_command, "run make command on dlb folder",
                                                            self._command_timeout, hqm_driver_dlb_path.strip())
        self._log.debug("Make and compiling the files HQM driver folder {}".format(command_result))
        # find libdlb folder
        hqm_driver_libdlb_path = common_content_lib.execute_sut_cmd_no_exception(find_libdlb_dir_path,
                                                                          "find the libdlb path",
                                                                          self._command_timeout,
                                                                          cmd_path=self.ROOT_PATH,
                                                                          ignore_result="ignore")
        self._log.debug("HQM user libdlb path {}".format(hqm_driver_libdlb_path))
        # make and compiling the files in HQM libdlb folder
        command_result = common_content_lib.execute_sut_cmd(make_command, "run make command in libdlb",
                                                                  self._command_timeout, hqm_driver_libdlb_path.strip())
        self._log.debug("Make and compiling the files HQM libdlb follder {}".format(command_result))
        # find dlb2 kernel file
        hqm_driver_kernel_file_path = common_content_lib.execute_sut_cmd(find_dlb2_kernel_file,
                                                                               "find the dlb2 kernel file",
                                                                               self._command_timeout,
                                                                               cmd_path=self.ROOT_PATH)
        self._log.debug("HQM driver kernel file {}".format(hqm_driver_kernel_file_path))
        # rmmod and insmod on dlb2.ko kernel file
        # cmd_output = self._os.execute(insmod_cmd + " " + hqm_driver_kernel_file_path.strip(), self._command_timeout,
        #                               sut_folder_path)
        driver_load_status = common_content_lib.execute_sut_cmd_no_exception(grep_dlb_driver, "grep the dlb2 kernel file",
                                                               self._command_timeout, cmd_path=sut_folder_path,
                                                               ignore_result="ignore")
        self._log.debug("Installed HQM driver info {}".format(driver_load_status))

        if expected_dlb_val in driver_load_status.strip():
            cmd_output1 = common_content_lib.execute_sut_cmd_no_exception("{} {}".format(rmmod_cmd, hqm_driver_kernel_file_path.strip()),
                                                             "rmmod the dlb2 driver",
                                                             self._command_timeout,
                                                             cmd_path=sut_folder_path, ignore_result="ignore")
            self._log.debug(cmd_output1)

        common_content_lib.execute_sut_cmd_no_exception("sync",
                                                        "executing sync command",
                                                        self._command_timeout,
                                                        cmd_path=self.ROOT,
                                                        ignore_result="ignore")

        cmd_output2 = common_content_lib.execute_sut_cmd("{} {}".format(insmod_cmd, hqm_driver_kernel_file_path.strip()),
                                                        "insmod the dlb2 driver",
                                                        self._command_timeout,
                                                        cmd_path=sut_folder_path)
        self._log.debug(cmd_output2)
        # grep dlb driver file
        hqm_driver_kernel = common_content_lib.execute_sut_cmd_no_exception(grep_dlb_driver,
                                                                            "grep the dlb2 kernel file",
                                                                            self._command_timeout,
                                                                            cmd_path=sut_folder_path,
                                                                            ignore_result="ignore")

        self._log.debug("Installed HQM driver info {}".format(hqm_driver_kernel))
        common_content_lib.execute_sut_cmd_no_exception("sync",
                                                        "executing sync command",
                                                        self._command_timeout,
                                                        cmd_path=self.ROOT,
                                                        ignore_result="ignore")
        if expected_dlb_val not in hqm_driver_kernel.strip():
            raise content_exceptions.TestFail("HQM Driver installation failed")
        self._log.info("HQM driver installed successfully")

    def get_name_version(self, path):
        """
        Extracts the file name base name and version string
        :param path : path to file
        """
        file_name = os.path.basename(path)
        separator_index = file_name.index('.tar')
        base_name = file_name[:separator_index]
        name, version = base_name.split('-')
        return name, version

    def run_dpdk_workload(self, vm_name = None, common_content_lib = None):
        """
        Run the dpdk workload
        """
        if common_content_lib is None:
            common_content_lib = self._common_content_lib
        dpdk_file_name = os.path.split(self.dpdk_file_path)[-1].strip()
        dpdk_name, version = self.get_name_version(dpdk_file_name)
        dpdk_full_folder_name = dpdk_name + '-' + 'stable' + '-' + version
        test_cmd1 = "cd /root/HQM/dpdk/{};" \
                   "ninja -C builddir;" \
                   "mkdir -p /mnt/hugepages;" \
                   "mount -t hugetlbfs nodev /mnt/hugepages;" \
                   "echo 2048 > /proc/sys/vm/nr_hugepages;".format(dpdk_full_folder_name)
        test_cmd2 = "cd /root/HQM/dpdk/{};" \
                    "ninja -C builddir;" \
                    "mkdir -p /mnt/hugepages;" \
                   "mount -t hugetlbfs nodev /mnt/hugepages;" \
                   "echo 2048 > /proc/sys/vm/nr_hugepages;" \
                   "cd builddir/app;" \
                   "./dpdk-test-eventdev -c 0x0f --vdev=dlb2_event -- --test=order_queue --plcores=1 " \
                   "--wlcore=2,3 --nb_flows=64 --nb_pkts=100000000;".format(dpdk_full_folder_name)

        self._log.info("Execute dpdk workload command for dpdk-test-eventdev")

        # executing dpdk workload
        dpdk_path = common_content_lib.execute_sut_cmd_no_exception(test_cmd1, "executing dpdk workload command1",
                                                                        self._command_timeout, cmd_path=self.ROOT,
                                                                    ignore_result="ignore")
        self._log.info("HQM drivers dlb path {}".format(dpdk_path))
        # if vm_name is not None:
        #     reboot_cmd = self._common_content_lib.execute_sut_cmd_no_exception("virsh reboot {}".format(vm_name),
        #                                                                        "executing reboot vm",
        #                                                             self._command_timeout, cmd_path=self.ROOT,
        #                                                             ignore_result="ignore")
        #     self._log.debug("reboot vm {} {}".format(vm_name, reboot_cmd))
        # else:
        #     self._common_content_lib.perform_os_reboot(self._common_content_lib._reboot_timeout)

        time.sleep(10)
        dpdk_wrkload_run_result = common_content_lib.execute_sut_cmd(test_cmd2, "executing dpdk workload command2",
                                                                        self._command_timeout, cmd_path=self.ROOT)
        self._log.debug("DPDK Workload executed successfully : {}".format(dpdk_wrkload_run_result))
        self._log.info("DPDK Workload executed successfully : {}".format(dpdk_wrkload_run_result))

    def run_dlb_workload(self, vm_name = None, common_content_lib = None):
        """
        Run the dlb workload
        """
        if common_content_lib is None:
            common_content_lib = self._common_content_lib
        dpdk_file_name = os.path.split(self.dpdk_file_path)[-1].strip()
        dpdk_name, version = self.get_name_version(dpdk_file_name)
        dpdk_full_folder_name = dpdk_name + '-' + 'stable' + '-' + version
        dlb_cmd = "cd /root/HQM/dpdk/{}/builddir/app;" \
                  "export LD_LIBRARY_PATH=/root/HQM/libdlb/;" \
                  "/root/HQM/libdlb/examples/dir_traffic -n 1024 -w poll".format(dpdk_full_folder_name)
        self._log.info("Execute dlb_traffic workload command")

    #    if vm_name is not None:
    #        reboot_cmd = self._common_content_lib.execute_sut_cmd_no_exception("virsh reboot {}".format(vm_name),
    #                                                                           "executing reboot vm",
    #                                                                           self._command_timeout, cmd_path=self.ROOT,
    #                                                                           ignore_result="ignore")
    #        self._log.debug("reboot vm {} {}".format(vm_name, reboot_cmd))
    #    else:
    #        self._common_content_lib.perform_os_reboot(self._common_content_lib._reboot_timeout)

        time.sleep(10)
        # execute dlb workload
        ldb_traffic_result = common_content_lib.execute_sut_cmd(dlb_cmd, "executing dlb workload command",
                                                                        self._command_timeout, cmd_path=self.ROOT)

        self._log.debug("ldb traffic command results {}".format(ldb_traffic_result))
        ldb_tx_traffic = re.search(self.LDB_REGEX_TX, ldb_traffic_result)
        ldb_rx_traffic = re.search(self.LDB_REGEX_RX, ldb_traffic_result)
        if not (ldb_tx_traffic and ldb_rx_traffic):
            raise content_exceptions.TestFail("Failed to get the TX/RX data events")
        if (ldb_tx_traffic.group(1) != self._ldb_traffic_data) and (ldb_rx_traffic.group(1) != self._ldb_traffic_data):
            raise content_exceptions.TestFail("Failed to get the ldb_traffi TX/RX data events")
        self._log.debug("The ldb traffic run successfully without any errors")
        self._log.info("The ldb traffic run successfully without any errors")

    def __run_dlb_workload_vmware(self, vm_name = None, vm_parallel = None, common_content_lib = None, runtime = 7200):
        """
        Run the dlb workload
        """
        if common_content_lib is None:
            common_content_lib = self._common_content_lib
        dlb_cmd = "export TOP=/root/HQM/dlb;" \
                  "export LD_LIBRARY_PATH=$TOP/libdlb;" \
                  "end=$((SECONDS+{}));" \
                  "while [ $SECONDS -lt $end ];" \
                  "do $LD_LIBRARY_PATH/examples/ldb_traffic -n 1024 -w poll ;done ".format(runtime)
        self._log.info("Execute dlb_traffic workload command")
        time.sleep(30)
        # execute dlb workload
        ldb_traffic_result = common_content_lib.execute_sut_cmd(dlb_cmd, "executing dlb workload command",
                                                                             self._command_timeout, cmd_path=self.ROOT)

        self._log.debug("ldb traffic command results {}".format(ldb_traffic_result))
        ldb_tx_traffic = re.search(self.LDB_REGEX_TX, ldb_traffic_result)
        ldb_rx_traffic = re.search(self.LDB_REGEX_RX, ldb_traffic_result)
        if not (ldb_tx_traffic and ldb_rx_traffic):
            raise content_exceptions.TestFail("Failed to get the TX/RX data events")
        if (ldb_tx_traffic.group(1) != self._ldb_traffic_data) and (ldb_rx_traffic.group(1) != self._ldb_traffic_data):
            raise content_exceptions.TestFail("Failed to get the ldb_traffi TX/RX data events")
        self._log.debug("The ldb traffic run successfully without any errors")
        self._log.info("The ldb traffic run successfully without any errors")

    def run_dlb_workload_vmware(self, vm_name = None, vm_parallel = None, common_content_lib = None, runtime=7200):

        vm_thread = None
        if vm_parallel is not None:
            # Trigger dlb workload in a thread for vm
            vm_thread = threading.Thread(target=self.__run_dlb_workload_vmware,
                                         args=(vm_name, vm_parallel, common_content_lib, runtime))
            vm_thread.start()
            self._log.info(" Started VM creation thread for VM:{}.".format(vm_name))
            self.vm_create_thread_list.append(vm_thread)
        else:
            # Trigger VM creation in sequential manner
            self.__run_dlb_workload_vmware(vm_name = vm_name, vm_parallel = vm_parallel, common_content_lib = common_content_lib, runtime = runtime)

        return vm_thread

    def install_hqm_dpdk_driver(self, common_content_lib = None,is_vm = None):
        """
        HQM driver and DPDK Installation
        1. Copy the .txz file of HQM to sut and extract it
        2. Copy the .txz file of DPDK to sut and extract it
        3. Run dpdk workload
        4. Run dlb workload

        """
        if common_content_lib is None:
            common_content_lib = self._common_content_lib
        self._log.info("Install HQM Driver on the SUT")
        if is_vm is not None:
            hqm_file_name = os.path.split(self.vm_hqm_file_path)[-1].strip()
        else:
            hqm_file_name = os.path.split(self.hqm_file_path)[-1].strip()

        if is_vm is not None:
            dpdk_file_name = os.path.split(self.vm_dpdk_file_path)[-1].strip()
        else:
            dpdk_file_name = os.path.split(self.dpdk_file_path)[-1].strip()

        hqm_folder_name = "HQM"
        dpdk_name, version = self.get_name_version(dpdk_file_name)
        dpdk_full_folder_name = dpdk_name + '-' + 'stable' + '-' + version
        dpdk_folder_name = "HQM/dpdk"
        find_dlb2_kernel_file = "find $(pwd) -type f -name 'dlb2.ko' 2>/dev/null"
        find_dlb_dir_path = "find $(pwd) -type d -name 'dlb2' 2>/dev/null | grep 'driver/dlb2'"
        find_libdlb_dir_path = "find $(pwd) -type d -name 'libdlb' 2>/dev/null"
        grep_dlb_driver = "lsmod | grep dlb"
        expected_dlb_val = "dlb2"
        insmod_cmd = "insmod"
        rmmod_cmd = "rmmod"
        make_command = "make"

        if is_vm is not None:
            patch_file = self.vm_dpdk_patch_file_name
        else:
            patch_file = self.dpdk_patch_file_name
        patch_cmd = "cd /root/HQM/dpdk/{};patch -Np1 < /root/HQM/dpdk/{};".format(dpdk_full_folder_name,
                                                                                  patch_file)
        dos_2_unix_cmd = "dos2unix /root/HQM/dpdk/{}".format(patch_file)
        export_cmd = "cd /root/HQM/dpdk/{};" \
                     "export DPDK_DIR=/root/HQM/dpdk/{}/;" \
                     "export RTE_SDK=$DPDK_DIR;" \
                     "export RTE_TARGET=installdir;" \
                     "meson setup --prefix $RTE_SDK/$RTE_TARGET builddir;" \
                     "ninja -C builddir install".format(dpdk_full_folder_name, dpdk_full_folder_name)

        build_dlb2_driver_cmd = "cd /root/HQM/driver/dlb2; make;"
        build_libdlb_cmd = "cd /root/HQM/libdlb; make;"

        hqm_host_file_path = (self._artifactory_obj.download_tool_to_automation_tool_folder(hqm_file_name)).strip()
        dpdk_host_file_path = (self._artifactory_obj.download_tool_to_automation_tool_folder(dpdk_file_name)).strip()

        # Copy the HQM file to SUT
        sut_folder_path = common_content_lib.copy_zip_file_to_linux_sut(hqm_folder_name, hqm_host_file_path,
                                                                        dont_delete="True")
        sut_folder_path = sut_folder_path.strip()
        self._log.debug("HQM file is extracted and copied to SUT path {}".format(sut_folder_path))
        self._log.info("HQM driver installed successfully")
        common_content_lib.execute_sut_cmd_no_exception("whoami;sync;",
                                                        "executing sync command",
                                                        self._command_timeout,
                                                        cmd_path=self.ROOT,
                                                        ignore_result="ignore")
        # Copy the dpdk file to SUT
        sut_folder_path = common_content_lib.copy_zip_file_to_linux_sut(dpdk_folder_name, dpdk_host_file_path,
                                                                              dont_delete="True")
        sut_folder_path = sut_folder_path.strip()
        self._log.debug("dpdk file is extracted and copied to dpdk path in HQM {}".format(sut_folder_path))
        self._log.info("dpdk installed successfully")
        common_content_lib.execute_sut_cmd_no_exception("whoami;sync;",
                                                        "executing sync command",
                                                        self._command_timeout,
                                                        cmd_path=self.ROOT,
                                                        ignore_result="ignore")
        # execute dos2unix to patch cmd
        dos2unix_result = common_content_lib.execute_sut_cmd_no_exception(dos_2_unix_cmd,
                                                                               "executing dos2unix command to patch",
                                                                                self._command_timeout,
                                                                                cmd_path=sut_folder_path,
                                                                                ignore_result="ignore")
        self._log.debug("Dos2unix to patch {}".format(dos2unix_result))

        # execute patch cmd
        hqm_driver_dpdk_path = common_content_lib.execute_sut_cmd_no_exception(patch_cmd, "executing patch command",
                                                                        self._command_timeout, cmd_path=sut_folder_path,
                                                                          ignore_result="ignore")
        self._log.debug("HQM drivers dlb path {}".format(hqm_driver_dpdk_path.strip()))
        # export cmd
        hqm_driver_dpdk_path = common_content_lib.execute_sut_cmd_no_exception(export_cmd, "executing export command",
                                                                        self._command_timeout, cmd_path=sut_folder_path,
                                                                          ignore_result="ignore")
        self._log.debug("HQM drivers dlb path {}".format(hqm_driver_dpdk_path.strip()))

        # build_dlb2_driver_cmd
        driver_build_result = common_content_lib.execute_sut_cmd(build_dlb2_driver_cmd, "executing make command for dlb",
                                                                        self._command_timeout, cmd_path=sut_folder_path)
        self._log.debug("HQM drivers build result {}".format(driver_build_result))

        # build_libdlb_cmd
        libdlb_build_result = common_content_lib.execute_sut_cmd(build_libdlb_cmd, "executing make command for libdlb",
                                                                        self._command_timeout, cmd_path=sut_folder_path)
        self._log.debug("HQM libdlb build result {}".format(libdlb_build_result))

        # Search dlb folder
        hqm_driver_dlb_path = common_content_lib.execute_sut_cmd_no_exception(find_dlb_dir_path, "find the driver path",
                                                                              self._command_timeout,
                                                                              cmd_path=self.ROOT_PATH,
                                                                              ignore_result="ignore")
        self._log.debug("HQM drivers dlb path {}".format(hqm_driver_dlb_path))
        # make and compiling the files in HQM Driver folder
        command_result = common_content_lib.execute_sut_cmd(make_command, "run make command on dlb folder",
                                                            self._command_timeout, hqm_driver_dlb_path.strip())
        self._log.debug("Make and compiling the files HQM driver folder {}".format(command_result))
        # find libdlb folder
        hqm_driver_libdlb_path = common_content_lib.execute_sut_cmd_no_exception(find_libdlb_dir_path,
                                                                          "find the libdlb path",
                                                                          self._command_timeout,
                                                                          cmd_path=self.ROOT_PATH,
                                                                          ignore_result="ignore")
        self._log.debug("HQM user libdlb path {}".format(hqm_driver_libdlb_path))
        # make and compiling the files in HQM libdlb folder
        command_result = common_content_lib.execute_sut_cmd(make_command, "run make command in libdlb",
                                                                  self._command_timeout, hqm_driver_libdlb_path.strip())
        self._log.debug("Make and compiling the files HQM libdlb follder {}".format(command_result))
        # find dlb2 kernel file
        hqm_driver_kernel_file_path = common_content_lib.execute_sut_cmd(find_dlb2_kernel_file,
                                                                               "find the dlb2 kernel file",
                                                                               self._command_timeout,
                                                                               cmd_path=self.ROOT_PATH)
        self._log.debug("HQM driver kernel file {}".format(hqm_driver_kernel_file_path))
        # rmmod and insmod on dlb2.ko kernel file
        # cmd_output = self._os.execute(insmod_cmd + " " + hqm_driver_kernel_file_path.strip(), self._command_timeout,
        #                               sut_folder_path)
        driver_load_status = common_content_lib.execute_sut_cmd_no_exception(grep_dlb_driver, "grep the dlb2 kernel file",
                                                               self._command_timeout, cmd_path=self.ROOT_PATH,
                                                               ignore_result="ignore")
        self._log.debug("Installed HQM driver info {}".format(driver_load_status))

        if expected_dlb_val in driver_load_status.strip():
            cmd_output1 = common_content_lib.execute_sut_cmd_no_exception("{} {}".format(rmmod_cmd, hqm_driver_kernel_file_path.strip()),
                                                             "rmmod the dlb2 driver",
                                                             self._command_timeout,
                                                             cmd_path=self.ROOT_PATH, ignore_result="ignore")
            self._log.debug(cmd_output1)

        common_content_lib.execute_sut_cmd_no_exception("sync",
                                                        "executing sync command",
                                                        self._command_timeout,
                                                        cmd_path=self.ROOT,
                                                        ignore_result="ignore")

        cmd_output2 = common_content_lib.execute_sut_cmd("{} {}".format(insmod_cmd, hqm_driver_kernel_file_path.strip()),
                                                        "insmod the dlb2 driver",
                                                        self._command_timeout,
                                                        cmd_path=self.ROOT_PATH)
        self._log.debug(cmd_output2)
        # grep dlb driver file
        hqm_driver_kernel = common_content_lib.execute_sut_cmd_no_exception(grep_dlb_driver,
                                                                            "grep the dlb2 kernel file",
                                                                            self._command_timeout,
                                                                            cmd_path=self.ROOT_PATH,
                                                                            ignore_result="ignore")

        self._log.debug("Installed HQM driver info {}".format(hqm_driver_kernel))
        common_content_lib.execute_sut_cmd_no_exception("sync",
                                                        "executing sync command",
                                                        self._command_timeout,
                                                        cmd_path=self.ROOT,
                                                        ignore_result="ignore")
        if expected_dlb_val not in hqm_driver_kernel.strip():
            raise content_exceptions.TestFail("HQM Driver installation failed")
        self._log.info("HQM driver installed successfully")

    def download_vcenter_file_for_esxi(self):
        """
        This method is to install the vcenter esxi to host
        """
        self._log.info("Download Vcenter Esxi on the host")
        vcenter_esxi_file_name = os.path.split(self.vcenter_esxi_file_path)[-1].strip()
        vcenter_esxi_host_file_path = (self._artifactory_obj.download_tool_to_automation_tool_folder(vcenter_esxi_file_name)).strip()
        return vcenter_esxi_file_name, vcenter_esxi_host_file_path

    def download_json_for_esxi(self):
        """
        This method is to install the vcenter esxi to host
        """
        self._log.info("Download Vcenter json Esxi on the host")
        vcenter_json_file_name = os.path.split(self.vcenter_json_file_path)[-1].strip()
        vcenter_json_host_file_path = (self._artifactory_obj.download_tool_to_automation_tool_folder(vcenter_json_file_name)).strip()
        return vcenter_json_file_name

    def install_acpica_tool_linux(self):
        """
        This method is to install the acpi tool to linux SUT
        """

        install_command_list = ["make clean", "make", "make install"]
        host_tool_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
            AcpicaToolConstants.acpica_tar_file_name)
        tool_sut_path = self._common_content_lib.copy_zip_file_to_linux_sut(AcpicaToolConstants.acpic_tool_name,
                                                                            host_tool_path)
        tool_complete_path = tool_sut_path + "/" + AcpicaToolConstants.acpic_folder_name
        self._log.info("Installing {} tool".format(AcpicaToolConstants.acpic_tool_name))
        for command in install_command_list:
            cmd_result = self._common_content_lib.execute_sut_cmd(command, "run {}".format(command),
                                                                  self._command_timeout, cmd_path=tool_complete_path)
            self._log.debug("{} command stdout:\n{}".format(command, cmd_result))
        self._log.info("Successfully installed the {} tool".format(AcpicaToolConstants.acpic_tool_name))
        return tool_complete_path

    def spr_qat_installation(self, qat_folder_path, configure_spr_cmd=None):
        """
        This function execute SPR QAT Tool installation

        :param: qat_folder_path get the QAT folder path
        """
        if configure_spr_cmd:
            configure_cmd = configure_spr_cmd
        else:
            configure_cmd = r"./configure && make uninstall"
        make_cmd = "make -s -j install"
        make_install_samples = "make -s -j samples-install"
        find_cpa_sample_code_file = "find $(pwd) -type f -name 'cpa_sample_code'"
        qat_dependency_packages = "echo y | yum install boost-build boost-devel boost-doc boost-examples " \
                                  "libnl3-devel libnl3-doc yasm openssl-devel"
        spr_work_around_cmd = ["export EXTRA_CXXFLAGS=-Wno-stringop-truncation",
                               "echo '/usr/local/lib' | sudo tee -a /etc/ld.so.conf", "mkdir -p /etc/default",
                               "mkdir -p /etc/udev/rules.d/", "mkdir -p /etc/ld.so.conf.d"]

        self._log.info("QAT Installtion in SPR platfrom")
        # Configuring the work around for SPR platform
        for cmd_item in spr_work_around_cmd:
            self._log.info("Executing work around command '{}' for QAT installation".format(cmd_item))
            self._common_content_lib.execute_sut_cmd(cmd_item, cmd_item, self._command_timeout)

        # Installing dependency packates
        command_result = self._common_content_lib.execute_sut_cmd(qat_dependency_packages,
                                                                  "Dependency package installation",
                                                                  self._command_timeout)
        self._log.debug("Dependency packages are installed sucessfully {}".format(command_result))

        # Configuring the QAT Tool if installed already uninstall
        command_result = self._common_content_lib.execute_sut_cmd(configure_cmd, "run configure command",
                                                                  self._command_timeout, qat_folder_path)
        self._log.debug(
            "Configuring and Uninstall QAT Tool successfully if already installed {}".format(command_result))

        # make install  the QAT Tool
        command_result = self._common_content_lib.execute_sut_cmd(make_cmd, "run make install command",
                                                                  self._command_timeout, qat_folder_path)
        self._log.debug("Install the QAT Tool in SUT {}".format(command_result))
        # make install samples the QAT Tool
        command_result = self._common_content_lib.execute_sut_cmd(make_install_samples, "run make install command",
                                                                  self._command_timeout, qat_folder_path)
        self._log.debug("Install the Samples Tool with QAT {}".format(command_result))
        # find cpa_sample_code file from the build folder
        cpa_sample_file = self._common_content_lib.execute_sut_cmd(find_cpa_sample_code_file,
                                                                   "find the cpa_sample_code file in build path",
                                                                   self._command_timeout, qat_folder_path + "/build")
        self._log.debug("Found cpa_sample_code file from build folder {} ".format(cpa_sample_file))
        if not cpa_sample_file:
            raise content_exceptions.TestFail("cpa_sample code file not found from build folder")
        self._log.info("QAT Tool installed successfully")

    def install_cycling_tool_to_sut_linux(self):
        """
        This method is to install the cycling tool to SUT.

        return: install path
        raise: None
        """
        self._log.info("Installing cycling to SUT")
        host_folder_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
            LinuxCyclingToolConstant.CYCLING_HOST_FOLDER_NAME)
        sut_folder_path = self._common_content_lib.copy_zip_file_to_linux_sut(
            LinuxCyclingToolConstant.CYCLING_SUT_FOLDER_NAME, host_folder_path)
        self._log.debug("cycling tool file is extracted and copied to SUT path {}".format(sut_folder_path))

        install_path = self._common_content_lib.execute_sut_cmd(LinuxCyclingToolConstant.FIND_INSTALL_PATH,
                                                                "finding path", self._command_timeout,
                                                                LinuxCyclingToolConstant.CYCLING_HOST_FOLDER_PATH)
        return install_path

    def install_mesh_stress(self):
        """
        This method will copy and install mesh stress into sut.
        """
        self.install_stress_test_app()
        install_pre_requisite = ["cpanminus", "fio", "stress-ng", "p7zip", "numactl", "htop"]
        self._os.execute("dnf config-manager --add-repo={}".format(self.DOCKER_REPO),
                         self._command_timeout)
        for package in install_pre_requisite:
            try:
                self.yum_install(package)
            except Exception as ex:
                self._log.error("Failed to install package '{}' due to exception:'{}'".format(package, ex))
        try:
            self.yum_install(package_name="docker-ce", flags="--nobest --allowerasing")
        except Exception as ex:
            self._log.error("Failed to install package 'docker-ce' due to exception:'{}'".format(ex))

        self._os.execute("cpanm -n {}".format(self.CPANM_MODULE), self._command_timeout)

        host_tool_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
            self.MESH_CONSTANTS["mesh_zip_file"])

        sut_folder_path = self._common_content_lib.copy_zip_file_to_linux_sut(self.MESH_CONSTANTS["mesh_folder_name"],
                                                                              host_tool_path)
        self._log.debug("mesh files have been extracted and copied to SUT path {}".format(sut_folder_path))

        return sut_folder_path

    def install_ptu_linux(self, sut_folder_name, installer_name):
        """
        This method will copy and install ptu application into sut

        """
        install_pre_requisite = ["kernel-tools", "kernel-devel", "elfutils-libelf-devel"]
        self._log.info("Installing ptu tool")
        host_folder_path = self._artifactory_obj.download_tool_to_automation_tool_folder(installer_name)
        sut_folder_path = self._common_content_lib.copy_zip_file_to_linux_sut(sut_folder_name, host_folder_path)
        self._log.debug("PTU file is extracted and copied to SUT path {}".format(sut_folder_path))
        self.install_development_tool_linux()
        # Install pre-requirements before installing ./ptu
        self._log.info("Installing pre-requirements list: {}".format(install_pre_requisite))
        for package in install_pre_requisite:
            try:
                self.yum_install(package)
            except Exception as ex:
                self._log.error("Failed to install package '{}' due to exception:'{}'".format(package, ex))

        return sut_folder_path

    def install_ptu_windows(self, sut_folder_name, installer_name):
        """
        This install thread runner method will copy the application folder to sut and install it

        :raise: If installation failed raise content_exceptions.TestError
        """
        host_tool_path = self._artifactory_obj.download_tool_to_automation_tool_folder(installer_name)
        self._log.info("Installing the PTU tool")

        sut_folder_path = self._common_content_lib.copy_zip_file_to_sut(sut_folder_name, host_tool_path)

        cmd_ptu = "dir | FINDSTR .exe"

        ptu_installer_name = self._os.execute(cmd_ptu, self._command_timeout, sut_folder_path)

        installer_name = ("Power" + ptu_installer_name.stdout.split("Power")[-1]).replace("\n", " ")

        self._common_content_lib.execute_sut_cmd('"{}" -s'.format(installer_name), "cmd",
                                                 self._command_timeout, sut_folder_path)
        self._log.info("Installed PTU tool successfully %s", sut_folder_path)

        return sut_folder_path

    def install_ptu(self, sut_folder_name, installer_name):
        """
        This install ptu method will copy the application folder to sut and install it
        """
        if OperatingSystems.WINDOWS == self._os.os_type:
            return self.install_ptu_windows(sut_folder_name, installer_name)
        elif OperatingSystems.LINUX == self._os.os_type:
            return self.install_ptu_linux(sut_folder_name, installer_name)

    def install_solar_hwp_native_windows(self):
        """
        This method will copy and install solar application into sut

        :return installed_path : solar tool installed path
        """
        solar_regx = "Solar-(.*)"

        solar_host_folder_name_windows = { OperatingSystems.LINUX: "solar.tar.gz", OperatingSystems.WINDOWS: "solar.zip"}
        tool_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
            solar_host_folder_name_windows[self._os.os_type])
        sut_folder_path = self._common_content_lib.copy_zip_file_to_sut(
            SolarHwpConstants.SOLAR_SUT_FOLDER_NAME, tool_path)
        self._log.debug("Solar file is extracted and copied to SUT path {}".format(sut_folder_path))

        dir_result = self._common_content_lib.execute_sut_cmd("dir", "Dir command",
                                                              self._command_timeout, sut_folder_path)

        # To get the exe file name version
        exe_name = re.search(solar_regx, dir_result).group(1)
        if not exe_name:
            raise content_exceptions.TestError("Failed to find the solar tool")

        self._common_content_lib.execute_sut_cmd("Solar-{} --mode unattended".format(exe_name), "install solar tool",
                                                 self._command_timeout, sut_folder_path)
        installed_path = os.path.join(self.C_DRIVE_PATH, "Solar")

        return installed_path

    def install_validation_runner_windows(self):
        """
        This install thread runner method will copy the application folder to sut and install it

        :raise: If installation failed raise content_exceptions.TestError
        """
        exe_file = None
        file_name = "validation_runner.zip"
        host_tool_path = self._artifactory_obj.download_tool_to_automation_tool_folder(file_name)
        self._log.info("{} has started copying into SUT..".format(file_name))
        runner_tool_path_sut = self._common_content_lib.copy_zip_file_to_sut(file_name.split(".")[0], host_tool_path)
        self._log.info("File successfully copied into SUT under {}..".format(runner_tool_path_sut))
        list_exe_files = self._common_content_lib.execute_sut_cmd(r"dir *.exe", "Find the path of runner tool",
                                                                  self._command_timeout, runner_tool_path_sut)
        for line in list_exe_files.split("\n"):
            if ".exe" in line:
                exe_file = line.split()[-1]
                break

        self._log.info("{} has started Installing in SUT..".format(exe_file))
        self._common_content_lib.execute_sut_cmd('"{}" /S'.format(exe_file), "Install validation runner",
                                                 self._command_timeout, runner_tool_path_sut)

        self._log.info("Latest version of validation runner tool has been installed successfully..")

    def install_ilvss(self):
        """
        To Install ilvss tool

        :return: None
        """
        if OperatingSystems.LINUX == self._os.os_type:
            # To set the current date and time on SUT
            self._common_content_lib.set_datetime_on_sut()
            ilvss_file_name, ilvss_license_key_file_name = \
                self._common_content_configuration.get_ilvss_file_name_license_name()
            self._log.info("ilvss man file name from config is : {}".format(ilvss_file_name))
            self._log.info("ilvss licence key file name from config is : {}".format(ilvss_license_key_file_name))
            ilvss_file_path_host = self._artifactory_obj.download_tool_to_automation_tool_folder(ilvss_file_name)
            self._log.info("ilvss file path in Host : {}".format(ilvss_file_path_host))
            ilvss_license_key_path_host = self._artifactory_obj.download_tool_to_automation_tool_folder(
                ilvss_license_key_file_name)
            self._log.info("ilvss licence key path in Host : {}".format(ilvss_license_key_path_host))
            # To delete existing ilvss tool
            self._common_content_lib.execute_sut_cmd("rm -rf {}".format(ilvss_file_name),
                                                     "To delete tool", self._command_timeout)
            self._log.info("Copying {} file to SUT ....".format(ilvss_file_name))
            self._os.copy_local_file_to_sut(source_path=ilvss_file_path_host,
                                            destination_path=self.util_constants["LINUX_USR_ROOT_PATH"])

            # To give chmod permission
            self._common_content_lib.execute_sut_cmd(
                sut_cmd="chmod +x {}".format(ilvss_file_name), cmd_str="To give chmod permission",
                execute_timeout=self._command_timeout, cmd_path=self.util_constants["LINUX_USR_ROOT_PATH"])
            # Remove the existing installed ilvss tool
            self._common_content_lib.execute_sut_cmd(
                "rm -rf ilvss.* *.log", "Removing the existing installed ilvss tool", self._command_timeout, self.OPT)

            self._log.info("Existing ilvss logs has been deleted")
            self._log.info("Installing ilvss tool in the SUT ...")
            # To install ilvss
            self._common_content_lib.execute_sut_cmd("VSS=I ./{}".format(ilvss_file_name), "To install ilvss tool",
                                                     self._command_timeout, self.util_constants["LINUX_USR_ROOT_PATH"])
            self._log.info("ILVSS tool has been installed successfully")

            self._log.info("Copying licence key : {} to SUT ....".format(self.ILVSS_CONSTANTS['OPT_IVLSS']))
            # To copy license key
            self._os.copy_local_file_to_sut(source_path=ilvss_license_key_path_host,
                                            destination_path=self.ILVSS_CONSTANTS['OPT_IVLSS'])
        else:
            self._log.error("ILVSS is not supported on OS '%s'" % self._os.sut_os)
            raise NotImplementedError("ILVSS is not supported on OS '%s'" % self._os.sut_os)

    def install_cycling_tool_to_sut(self):
        """
        This method is to install cycling tool.

        :return tool path
        """
        if self._os.os_type == OperatingSystems.LINUX:
            return self.install_cycling_tool_to_sut_linux()
        else:
            host_folder_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
                WindowsMemrwToolConstant.CYCLING_HOST_FOLDER_NAME)

            if not os.path.isfile(host_folder_path):
                raise IOError("{} does not found".format(host_folder_path))

            # copying file to windows SUT in C:\\ from host
            self._os.copy_local_file_to_sut(host_folder_path, self._common_content_lib.C_DRIVE_PATH)

            return self._common_content_lib.C_DRIVE_PATH

    def install_dmidecode(self):
        """
        This function is used to copy dmidecode.exe.

        :raise: If installation failed raise content_exceptions.TestError
        """
        if OperatingSystems.WINDOWS == self._os.os_type:

            res = self._os.execute("dmidecode -t 17", timeout=self._command_timeout,
                                   cwd=self.DMIDECODE_WINDOWS_INSTALLED_PATH)
            if res.cmd_failed():
                host_folder_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
                    self.dmidecode_constants["DMIDECODE_EXE_INSTALLER"])
                return self._common_content_lib.copy_zip_file_to_sut(
                    self.dmidecode_constants["DMIDECODE_EXE_INSTALLER"].split(".")[0],
                    host_folder_path)
            else:
                return self.DMIDECODE_WINDOWS_INSTALLED_PATH
        elif OperatingSystems.LINUX == self._os.os_type:
            dmidecode_version_command = "dmidecode --v"
            dmidecode_version = self._common_content_lib.execute_sut_cmd(
                dmidecode_version_command, "To get dmidecode version", self._command_timeout)
            self._log.info("dmidecode version is : {}".format(dmidecode_version))
            if float(dmidecode_version) != 3.3:
                find_cmd = "find $(pwd) -type f -name 'Makefile'"
                self._log.info("copying dmidecode zip file to SUT ...")
                host_folder_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
                    self.dmidecode_constants["DMIDECODE_MASTER_LINUX"])
                zip_file_path = self._common_content_lib.copy_zip_file_to_linux_sut(
                    self.dmidecode_constants["DMIDECODE_MASTER_LINUX"].split(".")[0],
                    host_folder_path)
                dir_name = self._common_content_lib.execute_sut_cmd(find_cmd, "find the autogen.sh file path",
                                                                    self._command_timeout, zip_file_path).split()[-1]
                dir_path = os.path.dirname(dir_name)
                self._log.info("Executing the command : {}".format(self.MAKE))
                self._common_content_lib.execute_sut_cmd(self.MAKE, "Executing Make Command", self._command_timeout,
                                                         dir_path)
                self._log.info("Executing the command : {}".format(self.MAKE_INSTALL))
                self._common_content_lib.execute_sut_cmd(self.MAKE_INSTALL, "Executing Make Install",
                                                         self._command_timeout, dir_path)
            return self.util_constants["LINUX_USR_ROOT_PATH"]

    def install_socwatch_windows(self):
        """
        To install SocWatch tool in windows SUT

        :return:soc_exe_path: exe file path of socwatch
        """
        folder_name = "64"
        soc_watch_zip_fie = "socwatch_windows.zip"
        sut_folder_name = "socwatch"
        host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(soc_watch_zip_fie)
        sut_folder_path = self._common_content_lib.copy_zip_file_to_sut(sut_folder_name, host_path)
        soc_exe_path = sut_folder_path + os.sep + folder_name
        return soc_exe_path

    def install_burnin_linux(self, common_content_lib=None, os_obj=None):
        """
        To install burnin tool for linux

        :return: bit_location
        """
        if os_obj is None:
            os_obj = self._os
        if common_content_lib is None:
            common_content_lib = self._common_content_lib
        host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(self.BURNIN_FILE_ZIP)
        bit_location = \
            common_content_lib.copy_zip_file_to_linux_sut(
                self.BURNIN_DIR_SUT, host_path)
        sut_cmd = os_obj.execute("echo y | yum install "
                                 "ncurses-compat-libs;echo y | yum install ncurses;yum -y install alsa-lib-devel; yum -y install libncurses",
                                 self._command_timeout)
        self._log.debug(sut_cmd.stdout.strip())
        self._log.debug(sut_cmd.stderr.strip())
        return bit_location

    def install_burnin_windows(self, common_content_lib=None, os_obj=None):
        """
        To install burnin tool for windows

        :return: bit installed path
        """
        if os_obj is None:
            os_obj = self._os
        if common_content_lib is None:
            common_content_lib = self._common_content_lib

        # path = "C:\\Automation\\burner\\BIT_*"
        # powershell_cmd = "powershell rm {}".format(path)
        # command_result = self._os.execute(powershell_cmd, timeout=self._command_timeout, cwd=self.C_DRIVE_PATH)

        bit_find_command = r"where /R C:\\ " + BurnInConstants.BIT_EXE_FILE_NAME_WINDOWS
        print(bit_find_command)
        cmd_result = self._os.execute(bit_find_command, self._command_timeout)
        self._log.debug(cmd_result.stdout)
        self._log.debug(cmd_result.stderr)
        if not cmd_result.stdout:
            host_folder_path = self._artifactory_obj.download_tool_to_automation_tool_folder(self.BURNIN_FILE_ZIP_WIN)

            bit_extracted_path = common_content_lib.copy_zip_file_to_sut(
                self.BURNIN_DIR_SUT, host_folder_path)
            self._log.debug("BIT Extracted path : {}".format(bit_extracted_path))

            self._os.execute("rmdir /Q/S {}".format(BurnInConstants.BIT_INSTALLED_PATH_WINDOWS),
                             self._command_timeout)
            common_content_lib.execute_sut_cmd(
                BurnInConstants.BIT_INSTALL_COMMAND_WINDOWS, "silent installation", self._command_timeout,
                bit_extracted_path)

            bit_key = os.path.join(bit_extracted_path, BurnInConstants.BIT_KEY_WINDOWS_VM)
            self._log.debug("copying the licence key ...")
            print("################", bit_key, BurnInConstants.BIT_INSTALLED_PATH_WINDOWS)
            # common_content_lib.execute_sut_cmd(
            #   'copy {} "{}"'.format(bit_key, BurnInConstants.BIT_INSTALLED_PATH_WINDOWS), "copy key fie, ",
            #  self._command_timeout)

        return BurnInConstants.BIT_INSTALLED_PATH_WINDOWS

    def install_perthread_sh_file(self, mlc_execute_path, mount_list):
        """
        Function to install perthreadfile.txt in mlc tool folder
        Copying the gen_perthread_file.sh file to sut in mlc folder

        :param mlc_execute_path: path of the root path
        :param mount_list: contains mount points to check weather it present or not in pertherad file

        :raise: RuntimeError: if chmod permission was not given.
        """
        try:
            sh_file_host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(self.PERTHREAD_FILE_NAME)
            self._os.copy_local_file_to_sut(sh_file_host_path, mlc_execute_path)
            self._log.info("The file gen_perthreadfile.sh copied to SUT ")
            self._common_content_lib.execute_sut_cmd("chmod +x {}".format(self.PERTHREAD_FILE_NAME),
                                                     "Giving chmod permissions", self._command_timeout,
                                                     cmd_path=mlc_execute_path)
            self._common_content_lib.execute_sut_cmd("sed -i 's/\r//' {}".format(self.PERTHREAD_FILE_NAME),
                                                     "To remove ^M errors", self._command_timeout,
                                                     cmd_path=mlc_execute_path)
            txt_file = self._common_content_lib.execute_sut_cmd("./gen_perthreadfile.sh",
                                                                "Executing gen_perthread_file.sh",
                                                                self._command_timeout, cmd_path=mlc_execute_path)
            self._log.info("Perthread file installed in {}".format(mlc_execute_path))
            for each_mount_list in mount_list:
                match = re.findall(each_mount_list, txt_file)
                if match:
                    self._log.info("The mount point {} is present in perthreadfile.txt ".format(each_mount_list))
                else:
                    error_log = "The mount point {} is not present in perthreadfile.txt .".format(each_mount_list)
                    self._log.error(error_log)
                    raise IOError(error_log)
        except Exception as ex:
            log_error = "An exception occurred:\n{}".format(str(ex))
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def install_intel_ssd_dc_windows(self):
        """
        To install Intel SSD Data Center tool in windows SUT

        :return: intel_ssd_tool_path_sut
        """
        exe_file = None
        os_architecture = "wmic os get osarchitecture"
        intel_ssd_dict = {"64-bit": IntelSsdDcToolConstants.INTEL_SSD_DC_TOOL_64,
                          "32-bit": IntelSsdDcToolConstants.INTEL_SSD_DC_TOOL_32}

        file_name = self._common_content_configuration.get_intelssd_location(self._os.os_type.lower())
        host_folder_path = self._artifactory_obj.download_tool_to_automation_tool_folder(file_name)
        self._log.info("{} has started copying into SUT..".format(file_name))
        intel_ssd_tool_path_sut = self._common_content_lib.copy_zip_file_to_sut(file_name.split(".")[0], host_folder_path)
        self._log.info("File successfully copied into SUT under {}..".format(intel_ssd_tool_path_sut))
        list_exe_files = self._common_content_lib.execute_sut_cmd(r"dir *.exe", "Find the path of intel ssd dc tool",
                                                                  self._command_timeout, intel_ssd_tool_path_sut)

        for line in list_exe_files.split("\n"):
            if ".exe" in line:
                exe_file = line.split()[-1]
                break
        os_architecture = self._common_content_lib.execute_sut_cmd(os_architecture, os_architecture,
                                                                   self._command_timeout,
                                                                   intel_ssd_tool_path_sut).split()[-1]
        self._log.info("SUT is running :{} windows os".format(os_architecture))

        self._log.info("{}{} has started Installing in SUT..".format(intel_ssd_dict[os_architecture], exe_file))
        self._common_content_lib.execute_sut_cmd('"{}{}" -s'.format(intel_ssd_dict[os_architecture], exe_file),
                                                 "Install intel ssd data center tool",
                                                 self._command_timeout, intel_ssd_tool_path_sut)
        self._log.info("Latest version of  Intel SSD DC Tool has been installed successfully..")

        return intel_ssd_tool_path_sut

    def install_ltssm_tool(self):
        """
        This method is to install the lttsm tool on SUT.

        :return sut_ltssm_tool folder path
        """
        if self._os.os_type == OperatingSystems.LINUX:
            host_folder_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
                LttsmToolConstant.LTSSM_TOOL_HOST_FILE_NAME_LINUX)
            sut_folder_path = self._common_content_lib.copy_zip_file_to_linux_sut(
                LttsmToolConstant.LTSSM_TOOL_SUT_FOLDER_NAME_LINUX, host_folder_path)

            self._common_content_lib.execute_sut_cmd(sut_cmd="chmod +777 *", cmd_str="set permission",
                                                     execute_timeout=self._command_timeout, cmd_path=
                                                     sut_folder_path)
            return sut_folder_path
        else:
            host_folder_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
                LttsmToolConstant.LTSSM_TOOL_HOST_FILE_NAME_WINDOWS
            )
            sut_folder_path = self._common_content_lib.copy_zip_file_to_sut(
                LttsmToolConstant.LTSSM_TOOL_SUT_FOLDER_NAME_WINDOWS,
                host_folder_path)
            return sut_folder_path

    def install_driver_cycle(self):
        """
        This method is to install drver cycle for win.

        :return sut_path
        """
        if self._os.os_type == OperatingSystems.WINDOWS:
            host_folder_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
                DriverCycleToolConstant.DRIVER_CYCLE_TOOL_HOST_FILE_NAME)
            sut_folder_path = self._common_content_lib.copy_zip_file_to_sut(
                DriverCycleToolConstant.DRIVER_CYCLE_TOOL_SUT_FOLDER_NAME,
                host_folder_path)
            return sut_folder_path.strip()
        elif self._os.os_type == OperatingSystems.LINUX:
            host_folder_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
                DriverCycleToolConstant.DRIVER_TOOL_NAME_LINUX)
            self._os.copy_local_file_to_sut(host_folder_path, self._common_content_lib.ROOT_PATH)
            self._os.execute("chmod +777 {}".format(DriverCycleToolConstant.DRIVER_TOOL_NAME_LINUX),
                             self._command_timeout,
                             self._common_content_lib.ROOT_PATH)
            return self._common_content_lib.ROOT_PATH
        else:
            raise NotImplementedError("Not Implemented for OS type: {}".format(self._os.os_type))

    def install_ccb_package_on_sut(self):
        """
        This method is to install the ccb package on SUT.

        :return wheel package folder path
        """
        if self._os.os_type == OperatingSystems.WINDOWS:
            host_folder_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
                CcbPackageConstants.HOST_FOLDER_NAME)
            sut_folder_name = self._common_content_lib.copy_zip_file_to_sut(CcbPackageConstants.SUT_FOLDER_NAME,
                                                                            host_folder_path)
            self._log.debug(sut_folder_name)
            sut_folder_name = sut_folder_name.strip() + "\\" + CcbPackageConstants.SUT_FOLDER_NAME
            self._common_content_lib.execute_sut_cmd(sut_cmd="Setup.exe -s", cmd_str="install",
                                                     cmd_path=sut_folder_name.strip(),
                                                     execute_timeout=self._command_timeout)
            return sut_folder_name + "\\" + CcbPackageConstants.WHL_PACKAGE_FOLDER_NAME
        else:
            raise NotImplementedError("Not implemented for Os type: {}".format(self._os.os_type))

    def install_ccb_wheel_package(self, whl_package_list=[], cmd_path=None):
        """
        This method is to install the whl package on SUT.

        :param whl_package_list
        :param cmd_path
        """
        general_proxy = "http://proxy01.iind.intel.com:911"
        chain_proxy = "http://proxy-chain.intel.com:911"
        cmd_output = self._os.execute("python -V", self._command_timeout)
        if cmd_output.cmd_failed():
            raise content_exceptions.TestFail("Failed to execute the command 'python -V'")
        self._log.debug(cmd_output.stderr)
        if re.findall("Python 2", cmd_output.stderr, re.IGNORECASE | re.MULTILINE):
            python_dependency = "py2"
        else:
            python_dependency = "py3"

        for each_pkg in whl_package_list:
            cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd="dir |FINDSTR /I {}".format(each_pkg),
                                                                  cmd_str="find wheel pkg", execute_timeout=
                                                                  self._command_timeout,
                                                                  cmd_path=cmd_path.strip()).strip()
            self._log.debug("whl packages of {} are: {}".format(each_pkg, cmd_output))
            for whl_pkg in cmd_output.split():
                if python_dependency in whl_pkg:
                    pkg = whl_pkg.strip()
                    self._log.debug("Selected package for python version: {} is {}".format(python_dependency,
                                                                                           pkg))
            cmd = "python -m pip install --proxy {} {}"
            command_output = self._os.execute(cmd.format(general_proxy, pkg), self._command_timeout,
                                              cmd_path.strip())
            self._log.debug(command_output.stdout)
            if command_output.return_code != 0:
                self._os.execute(cmd.format(chain_proxy, pkg), self._command_timeout,
                                 cmd_path.strip())

    def install_pip_package(self, pkg):
        """
        This method is to install pip package on Windows SUT.

        :return None
        """
        general_proxy = "http://proxy01.iind.intel.com:911"
        chain_proxy = "http://proxy-chain.intel.com:911"
        cmd = "python -m pip install --proxy {} {}"
        command_output = self._os.execute(cmd.format(general_proxy, pkg), self._command_timeout)
        self._log.debug(command_output.stdout)
        if command_output.return_code != 0:
            self._os.execute(cmd.format(chain_proxy, pkg), self._command_timeout)

    def copy_semt_files_to_sut(self):
        """
        This method copies semt files from host to sut

        :return semt app folder path
        """
        # Copy the semt_files file to SUT
        host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
            self.SEMT_CONSTANTS["SEMT_FOLDER_NAME"])
        return self._common_content_lib.copy_zip_file_to_linux_sut(
            self.SEMT_CONSTANTS["SEMT_FOLDER_NAME"].split(".")[0],
            host_path)

    def copy_sgx_stream_tool_windows(self):
        """
        This method copies sgx stream app files from artifactory to sut

        :return sgx stream app folder path
        """
        host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
            self.STREAM_APP_CONSTANT_WINDOWS["STREAM_APP_CONSTANT_WINDOWS"])
        return self._common_content_lib.copy_zip_file_to_sut(
            self.STREAM_APP_CONSTANT_WINDOWS["STREAM_APP_CONSTANT_WINDOWS"].split(".")[0],
            host_path)

    def install_msr_tools_linux(self):
        """
        This Method is Used to Install Msr tools
        """
        self._log.info("Installing msr-tool")

        msr_tools_path = self._artifactory_obj.download_tool_to_automation_tool_folder(self.MSR_TOOLS_PATH)
        sut_path = self.util_constants["LINUX_USR_ROOT_PATH"]
        self._os.copy_local_file_to_sut(msr_tools_path, sut_path)
        self._log.debug("MSR Tools File is Successfully Copied to SUT")
        msr_tool_cmd_output = self._common_content_lib.execute_sut_cmd(self.MSR_TOOLS_INSTALLATION_CMD,
                                                                       self.MSR_TOOLS_INSTALLATION_CMD,
                                                                       self._command_timeout)
        self._log.debug("Msr Tools is Successfully Installed on SUT {}".format(msr_tool_cmd_output))

    def install_ccbsdk_in_sut(self):
        """
        This Method is used to Install CCB SDK on Sut by executing ccbsdk.exe

        :raise content_exceptions.TestError: if unable to Install CCBSDK Package on SUT.
        """
        ccbsdk_cmd = r'dir "Intel(R)CCBSDK" /s'
        self._log.info("Installing ccbsdk")
        system_scope_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder(self.CCBSDK_WINDOWS_FILE)
        self._log.debug("Copying {} file to SUT".format(self.CCBSDK_WINDOWS_FILE))
        self._os.copy_local_file_to_sut(system_scope_file_path, self.C_DRIVE_PATH)
        self._log.debug("Successfully copied the {} file under {}".format(self.CCBSDK_WINDOWS_FILE, self.C_DRIVE_PATH))
        self._common_content_lib.execute_sut_cmd('"{}" /S'.format(self.CCBSDK_WINDOWS_FILE), "Install CCBSDK",
                                                 self._command_timeout, self.C_DRIVE_PATH)
        if not self._common_content_lib.execute_sut_cmd(ccbsdk_cmd, "Find the path of System Scope Tool",
                                                        self._command_timeout, self.C_DRIVE_PATH):
            raise content_exceptions.TestError("CCBSDK Tool is Not Installed")
        self._log.info("CCBSDK Tool has been installed successfully")

    def install_ccbhwapi_in_sut(self):
        """
        This Method is Used to Install CCB Hardware API to Interact and Provide Hardware Details.
        """
        # Installing ccbsdk tool
        self.install_ccbsdk_in_sut()
        system_scope_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
            self.CCBHWAPI_WINDOWS_FILE)
        self._log.debug("Copying {} file to SUT".format(self.CCBHWAPI_WINDOWS_FILE))
        self._os.copy_local_file_to_sut(system_scope_file_path, self.C_DRIVE_PATH)
        self._log.debug("Successfully copied the {} file under {}".format(self.CCBHWAPI_WINDOWS_FILE,
                                                                          self.C_DRIVE_PATH))
        self._common_content_lib.execute_sut_cmd(r"pip install {}".format(self.CCBHWAPI_WINDOWS_FILE),
                                                 "Pip Install CCBHWAPI Module",
                                                 self._command_timeout, cmd_path=self.C_DRIVE_PATH)
        self._log.info("CCB hardware api is installed successfully")

    def get_memtester_dir_path(self):
        """
        This method returns the dir path where memtester tool is installed.

        :return: memtester tool path on SUT
        """
        find_memtester_dir = "find $(pwd) -type d -name 'memtester*'"
        # Copy memtester tool tar file to sut
        self._log.info("Copying memtester tool to SUT and installing")

        host_folder_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
            RDTConstants.RDT_MEMTESTER_CONSTANTS["MEMTESTER_TAR_FILE"])
        memtester_tool_dir_path = self._common_content_lib.copy_zip_file_to_linux_sut(
            RDTConstants.RDT_MEMTESTER_CONSTANTS["MEMTESTER_DIR"],
            host_folder_path)

        self._log.debug("Memtester tool path in sut is '{}'".format(memtester_tool_dir_path))

        memtester_tool_path = (self._common_content_lib.execute_sut_cmd(find_memtester_dir, find_memtester_dir,
                                                                        self._command_timeout,
                                                                        cmd_path=memtester_tool_dir_path)).strip()
        self._log.debug("Memtester tool executable path in sut is '{}'".format(memtester_tool_path))
        return memtester_tool_path

    def install_memtester_tool_to_sut(self):
        """
        This method installs the memtester tool to sut.

        :return: None
        """
        memtester_tool_path = self.get_memtester_dir_path()
        cmd_to_install_memtester = "make install"
        self._log.info("Installing memtester tool to sut")
        install_cmd_res = self._common_content_lib.execute_sut_cmd(
            cmd_to_install_memtester, "Install Memtester", self._command_timeout, memtester_tool_path)
        self._log.debug("Memtester tool installation is successful and command output is '{}'".format(install_cmd_res))

    def __copy_collateral_to_linux_sut(self, collateral_name, dict_collateral, host_collateral_path):
        """

        :param: collateral_name - collateral name
        :param: dict_collateral - dict which contains collateral details
        :param: host_collateral_path - host path where collateral file exists

        :raise: RuntimeError - if any runtime error occurs

        :return: returns the path where archive file copied/extracted to SUT
        """
        # archive extract command
        dict_archive_extract_cmd = {
            CollateralConstants.ZIP: "unzip {}",
            CollateralConstants.TAR: "tar zxvf {}",
            CollateralConstants.TGZ: "tar xvzf {}",
            CollateralConstants.TAR_GZ: "tar xvzf {}"
        }

        sut_home_path = self._common_content_lib.get_sut_home_path()
        sut_collateral_path = Path(os.path.join(sut_home_path, collateral_name)).as_posix()

        # delete the folder if already exists
        cmd_line = "rm -rf {}".format(sut_collateral_path)
        self._os.execute(cmd_line, self._command_timeout)

        archive_type = dict_collateral[CollateralConstants.TYPE]
        archive_name = dict_collateral[CollateralConstants.FILE_NAME]
        if archive_type in dict_archive_extract_cmd:
            # extract the folder in SUT if it is archive
            extract_cmd = dict_archive_extract_cmd[archive_type]
            sut_archive_file_path = Path(os.path.join(sut_home_path, archive_name)).as_posix()
            # copy collateral to SUT
            self._log.info("Copying from host '{}' to SUT '{}".format(host_collateral_path, sut_archive_file_path))
            self._os.copy_local_file_to_sut(host_collateral_path, sut_archive_file_path)
            cmd_line = extract_cmd.format(sut_archive_file_path)
            self._common_content_lib.execute_sut_cmd(cmd_line, cmd_line, self._command_timeout)
            # delete the archive file, as we extracted already
            cmd_line = "rm -f {}".format(sut_archive_file_path)
            self._common_content_lib.execute_sut_cmd(cmd_line, cmd_line, self._command_timeout)
        else:
            # nothing to extract, just create the folder and copy the file
            cmd_line = "mkdir {}".format(sut_collateral_path)
            self._common_content_lib.execute_sut_cmd(cmd_line, cmd_line, self._command_timeout)
            # copy collateral to SUT
            sut_collateral_file_path = os.path.join(sut_collateral_path, archive_name)
            self._os.copy_local_file_to_sut(host_collateral_path, sut_collateral_file_path)

        # check if copied folder exists
        cmd_line = "ls -l {}".format(sut_collateral_path)
        self._common_content_lib.execute_sut_cmd(cmd_line, cmd_line, self._command_timeout)

        return sut_collateral_path

    def __copy_collateral_to_windows_sut(self, collateral_name, dict_collateral, host_collateral_path):
        """
        :param: collateral_name - collateral name
        :param: dict_collateral - dict which contains collateral details
        :param: host_collateral_path - host path where collateral file exists

        :raise: RuntimeError - if any runtime error occurs

        :return: returns the path where archive file copied/extracted to SUT
        """
        # archive extract command
        dict_archive_extract_cmd = {
            CollateralConstants.ZIP: "tar -cf {}",
        }

        sut_home_path = self._common_content_lib.get_sut_home_path()
        sut_collateral_path = os.path.join(sut_home_path, collateral_name)

        # delete the folder if already exists
        cmd_line = "rmdir /S /Q  {}".format(sut_collateral_path)
        self._os.execute(cmd_line, self._command_timeout)

        archive_type = dict_collateral[CollateralConstants.TYPE]
        archive_name = dict_collateral[CollateralConstants.FILE_NAME]
        if archive_type in dict_archive_extract_cmd:
            # extract the archive to folder in SUT if it is archive
            extract_cmd = dict_archive_extract_cmd[archive_type]
            sut_archive_file_path = os.path.join(sut_home_path, archive_name)
            # copy collateral to SUT
            self._os.copy_local_file_to_sut(host_collateral_path, sut_archive_file_path)
            cmd_line = extract_cmd.format(sut_archive_file_path)
            self._common_content_lib.execute_sut_cmd(cmd_line, cmd_line, self._command_timeout)
            # delete the archive file, as we extracted already
            cmd_line = "del /Q sut_archive_file_path"
            self._common_content_lib.execute_sut_cmd(cmd_line, cmd_line, self._command_timeout)
        else:
            # nothing to extract just, create the folder and copy the file
            cmd_line = "mkdir {}".format(sut_collateral_path)
            self._common_content_lib.execute_sut_cmd(cmd_line, cmd_line, self._command_timeout)
            # copy collateral to SUT
            sut_collateral_file_path = os.path.join(sut_collateral_path, archive_name)
            self._os.copy_local_file_to_sut(host_collateral_path, sut_collateral_file_path)

        # check if copied folder exists
        cmd_line = "dir /s {}".format(sut_collateral_path)
        self._common_content_lib.execute_sut_cmd(cmd_line, cmd_line, self._command_timeout)

        return sut_collateral_path

    def copy_collateral_to_sut(self, collateral_name):
        """
        This method will copy the collateral binary to SUT home path
        :param: key_collateral - key to collateral dict
        :raise: RuntimeError for any failures

        :return: path where binary copied to SUT
        """
        dict_copy_function = {OperatingSystems.LINUX: self.__copy_collateral_to_linux_sut,
                              OperatingSystems.WINDOWS: self.__copy_collateral_to_windows_sut}

        proj_src_path = self._common_content_lib.get_project_src_path()
        dict_collateral = CollateralConstants.dict_collaterals[collateral_name]

        archive_relative_path = dict_collateral[CollateralConstants.RELATIVE_PATH]
        archive_file_name = dict_collateral[CollateralConstants.FILE_NAME]
        host_collateral_path = os.path.join(proj_src_path, r"src\collaterals", archive_relative_path, archive_file_name)
        if not os.path.exists(host_collateral_path):
            log_error = "The collateral archive '{}' does not exists..".format(host_collateral_path)
            self._log.error(log_error)
            raise FileNotFoundError(log_error)

        if self._os.os_type not in dict_collateral[CollateralConstants.SUPP_OS]:
            log_error = "This functionality is not supported for the OS '{}'..".format(self._os.os_type)
            self._log.error(log_error)
            raise NotImplementedError(log_error)

        copy_sut_function = dict_copy_function[self._os.os_type]
        sut_folder_path = copy_sut_function(collateral_name, dict_collateral, host_collateral_path)
        return sut_folder_path

    def install_linpack_mpi(self):
        """
        This method is to install the linpack mpi tool to SUT.

        :return path
        """
        self._log.info("Copying tool to SUT is in progress...")
        host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(LinPackToolConstant.HOST_FOLDER_NAME)
        sut_folder_path = self._common_content_lib.copy_zip_file_to_linux_sut(LinPackToolConstant.SUT_FOLDER_NAME,
                                                                              host_path)
        self._log.info("SUT folder path name: {}".format(sut_folder_path))
        mpi_file_path = sut_folder_path.strip() + "/" + LinPackToolConstant.SUT_MPI_FOLDER_NAME
        self._common_content_lib.execute_sut_cmd(sut_cmd="tar xzvf {}".format(LinPackToolConstant.MKLB_FILE_NAME),
                                                 cmd_str=
                                                 "extracting file: {}".format(LinPackToolConstant.MKLB_FILE_NAME),
                                                 execute_timeout=self._command_timeout,
                                                 cmd_path=sut_folder_path.strip() + "/")
        self._common_content_lib.execute_sut_cmd(sut_cmd="tar xzvf {}".format(LinPackToolConstant.MPI_FILE_NAME),
                                                 cmd_str="extracting the file: {}".format(
                                                     LinPackToolConstant.MPI_FILE_NAME),
                                                 execute_timeout=self._command_timeout,
                                                 cmd_path=sut_folder_path.strip() + "/")
        self._log.info("Uninstalling the Linpack Application")
        command_to_update_config_file = "sed 's/PSET_MODE=install/PSET_MODE=uninstall/g' silent.cfg > silent.org ; " \
                                        "mv -f silent.org silent.cfg; chmod +777 silent.cfg"

        self._common_content_lib.execute_sut_cmd(sut_cmd=command_to_update_config_file,
                                                 cmd_str=command_to_update_config_file, execute_timeout=
                                                 self._command_timeout, cmd_path=mpi_file_path + "/")
        cmd_output = self._os.execute(LinPackToolConstant.COMMAND_TO_INSTALL, self._command_timeout,
                                      mpi_file_path + "/")
        self._log.info("Uninstall the Application: {}".format(cmd_output.stdout))
        self._log.info("Installing the Linpack Application")
        command_to_update_config_file = "sed 's/PSET_MODE=uninstall/PSET_MODE=install/g' silent.cfg > silent.org ;" \
                                        " mv -f silent.org silent.cfg; chmod +777 silent.cfg"
        self._common_content_lib.execute_sut_cmd(sut_cmd=command_to_update_config_file,
                                                 cmd_str=command_to_update_config_file,
                                                 execute_timeout=self._command_timeout, cmd_path=mpi_file_path + "/")
        command_to_update_config_file = "sed 's/ACCEPT_EULA=decline/ACCEPT_EULA=accept/g' silent.cfg > silent.org ;" \
                                        " mv -f silent.org silent.cfg; chmod +777 silent.cfg"
        self._common_content_lib.execute_sut_cmd(sut_cmd=command_to_update_config_file,
                                                 cmd_str=command_to_update_config_file,
                                                 execute_timeout=self._command_timeout, cmd_path=mpi_file_path + "/")
        cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=LinPackToolConstant.COMMAND_TO_INSTALL
                                                              , cmd_str=LinPackToolConstant.COMMAND_TO_INSTALL,
                                                              execute_timeout=
                                                              self._command_timeout, cmd_path=mpi_file_path + "/")
        self._log.info("Installation Output: {}".format(cmd_output))

        return sut_folder_path.strip()

    def install_abrt_cli_in_linux(self):
        """Installs abrt-cli in linux"""
        self._log.debug("Installing abrt-cli")
        if not self._os.check_if_path_exists(
                os.path.join(self._common_content_lib._LINUX_BIN_LOCATION,
                             "abrt-cli").replace("/", os.path.sep),
                directory=False):
            sut_cmd = self._os.execute("rpm --import "
                                       "/etc/pki/rpm-gpg/RPM-GPG-KEY*",
                                       self._command_timeout)
            self._log.debug(sut_cmd.stdout)
            self._log.debug(sut_cmd.stderr)
            self.yum_install("abrt-tui")
        sut_cmd = self._os.execute('abrt-auto-reporting enabled',
                                   self._command_timeout)
        self._log.debug(sut_cmd.stdout)
        self._log.debug(sut_cmd.stderr)

    def install_vroc_tool_windows(self):
        """
        This install thread VROC tool method will copy the application folder to sut and install it

        :raise: If installation failed raise content_exceptions.TestFail
        """

        file_name = "vroc.zip"

        host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(file_name)

        self._log.info("{} has started copying into SUT..".format(file_name))
        sut_folder_path = self._common_content_lib.copy_zip_file_to_sut(file_name.split(".")[0], host_path)

        self._log.info("File successfully copied into SUT under {}".format(sut_folder_path))

        # Using where command find's the path of SetupVROC.exe file.
        setup_path = self._common_content_lib.execute_sut_cmd(VROCConstants.SETUP_FILE_WHERE_CMD, VROCConstants.
                                                              SETUP_FILE_WHERE_CMD, self._command_timeout,
                                                              sut_folder_path)
        setup_path = Path(setup_path).parent

        # Execute's SetupVROC.exe file
        self._log.info("Executing {} command under {}".format(VROCConstants.SETUP_CMD, setup_path))
        vroc_cmd_output = self._os.execute(cmd=VROCConstants.SETUP_CMD, timeout=self._command_timeout,
                                           cwd=str(setup_path))
        self._log.debug("Std error : {}".format(vroc_cmd_output.stderr))
        self._log.debug("Stdout : {}".format(vroc_cmd_output.stdout))

        time.sleep(10)  # Wait time to install VROC Tool
        self._log.debug("{} command output:{}".format(VROCConstants.SETUP_CMD, vroc_cmd_output.stdout))

        # Performing an reboot to verify tool installation
        self._log.info("Successfully executed {} performing an reboot".format(VROCConstants.SETUP_CMD))
        self._common_content_lib.perform_os_reboot(self._reboot_time_out)
        verify_output = self._common_content_lib.execute_sut_cmd(VROCConstants.VERIFY_VROC_CMD,
                                                                 VROCConstants.VERIFY_VROC_CMD, self._command_timeout)
        self._log.debug("Verify command:{} output:{}".format(VROCConstants.VERIFY_VROC_CMD, verify_output))
        # Verifying the tool in control panel
        if VROCConstants.TOOL_NAME not in verify_output:
            raise content_exceptions.TestFail("Failed to install VROC tool")
        self._log.info("Successfully installed {}".format(VROCConstants.TOOL_NAME))

    def install_dynamo_tool_linux(self):
        """
        This method will copy and install dynamo application into sut

        """
        self._log.info("Installing dynamo tool")
        tool_name = "dynamo.tar"
        host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(tool_name)
        sut_folder_path = self._common_content_lib.copy_zip_file_to_linux_sut(
            DynamoToolConstants.DYNAMO_SUT_FOLDER_NAME,
            host_path)

        return sut_folder_path

    def install_dynamo_tool_esxi(self):
        """
        This method will copy and install dynamo application into sut

        """
        self._log.info("Installing dynamo tool")
        tool_name = "dynamo.tar"
        host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(tool_name)
        sut_folder_path = self._common_content_lib.copy_zip_file_to_esxi_sut(
            DynamoToolConstants.DYNAMO_SUT_FOLDER_NAME,
            host_path)

        return sut_folder_path

    def install_iometer_tool_on_host_esxi(self, common_content_lib=None):
        """
        This method will copy and install dynamo application into sut

        """
        if common_content_lib is None:
            common_content_lib = self._common_content_lib

        self._log.info("Downloading iometer tool")
        tool_name = "iometer_tool.zip"
        host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(tool_name)
        vm_folder_name = "Iometer"
        VM_FOLDER_PATH = common_content_lib.copy_zip_file_to_sut(vm_folder_name, host_path)

        # sut_folder_path = self._common_content_lib.copy_zip_file_to_linux_sut(
        #     IOmeterToolConstants.ZIP_FILE_NAME,
        #     host_path)

        return VM_FOLDER_PATH

    def iometer_reg_add_esxi(self, common_content_lib=None):
        """
        This method will add iometer.reg file to get the registry entry added
        """
        if common_content_lib is None:
            common_content_lib = self._common_content_lib

        cmd ="$HKCU_IOMETER='HKCU:\Software\iometer.org';" \
             "Remove-Item -Path $HKCU_IOMETER -Confirm:$false -recurse;" \
             "$HKCU_IOMETER= 'HKCU:\Software';" \
             "New-Item -Path $HKCU_IOMETER -Name iometer.org -Confirm:$false;" \
             "$HKCU_IOMETER= 'HKCU:\Software\iometer.org';" \
             "New-Item -Path $HKCU_IOMETER -Name Iometer -Confirm:$false;" \
             "$HKCU_IOMETER= 'HKCU:\Software\iometer.org\Iometer';" \
             "New-Item -Path $HKCU_IOMETER -Name Settings -Confirm:$false;" \
             "New-ItemProperty -Path $HKCU_IOMETER\Settings -Name 'Version' -Value '1.1.0'  -PropertyType 'String' -Confirm:$false;"

        try:
            command_result = common_content_lib.execute_sut_cmd(
                "powershell.exe $progressPreference = 'silentlyContinue'; {}".format(cmd),
                "executing {}".format(cmd), self._command_timeout)
            self._log.debug(command_result)
            self._log.info(command_result)

        except:
            pass

    def install_iometer_tool_on_host_win(self):
        """
        This method will copy and install iometer application into host

        """
        self._log.info("Downloading iometer tool")
        tool_name = "iometer_tool.zip"
        tool_path = self._artifactory_obj.download_tool_to_automation_tool_folder(tool_name)

        # Uncompress the file
        host_path = tool_path.split(".")[0]
        os.system("powershell.exe Expand-Archive -Path '{}' -DestinationPath '{}'".format(tool_path,
                                                                                    os.path.dirname(tool_path)))

        config_file_name = self._common_content_configuration.get_iometer_tool_config_file_name()
        config_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder(config_file_name)

        return host_path, config_file_path


    def install_aer_inject_tool(self):
        """
        This method is to install AER inject tool.

        :return sut_folder path
        """
        self._log.info("Copy AER inject to SUT")
        host_folder_path = self._artifactory_obj.download_tool_to_automation_tool_folder(RasPcieAer.HOST_FOLDER_NAME)
        sut_folder_path = self._common_content_lib.copy_zip_file_to_linux_sut(RasPcieAer.SUT_FOLDER_NAME,
                                                                              host_folder_path) + "/" + \
                          RasPcieAer.SUT_TOOL_FOLDER_NAME
        self._log.info("SUT folder path is: {}".format(sut_folder_path))
        self._log.info("Execute make command")
        self._common_content_lib.execute_sut_cmd(sut_cmd="make", cmd_str="make", execute_timeout=self._command_timeout,
                                                 cmd_path=sut_folder_path)

        make_install_output = self._common_content_lib.execute_sut_cmd(sut_cmd="make install", cmd_str="make install",
                                                                       execute_timeout=self._command_timeout,
                                                                       cmd_path=sut_folder_path)
        self._log.info("Make Install Output: {}".format(make_install_output))
        self._log.info("AER tool successfully installed")
        self._log.info("Copy ras-util file to SUT")
        host_tool_path = self._artifactory_obj.download_tool_to_automation_tool_folder(RasPcieAer.RAS_UTILS_HOST_FOLDER_NAME)
        self._os.copy_local_file_to_sut(host_tool_path, sut_folder_path)
        self._common_content_lib.execute_sut_cmd(sut_cmd="chmod +777 {}".format(RasPcieAer.RAS_UTILS_HOST_FOLDER_NAME),
                                                 cmd_str="giving Permissions", cmd_path=sut_folder_path,
                                                 execute_timeout=self._command_timeout)
        ras_utils_output = self._common_content_lib.execute_sut_cmd(sut_cmd=RasPcieAer.INSTALL_RAS_UTILS,
                                                                    cmd_str=RasPcieAer.INSTALL_RAS_UTILS,
                                                                    execute_timeout=self._command_timeout,
                                                                    cmd_path=sut_folder_path)
        self._log.info("Install output: {}".format(ras_utils_output))
        self.yum_install("kernel-modules-extra")
        return sut_folder_path


    def install_crunch_tool(self):
        """
        This method is to install crunch tool.

        :return tool path
        """
        self._log.info("Move crunch tool to the SUT")
        host_folder_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
            StressCrunchTool.HOST_FOLDER_NAME)
        path = self._common_content_lib.copy_zip_file_to_linux_sut(StressCrunchTool.SUT_FOLDER_NAME,
                                                                   host_folder_path)
        path = Path(os.path.join(path, StressCrunchTool.SUT_FOLDER_NAME)).as_posix().strip()
        self._log.info("Crunch tool Successfully Installed")
        return path

    def install_libquantum_tool(self):
        """
        This method is to install libquantum tool.

        :return tool path
        """
        self._log.info("Move libquantum tool to the SUT")
        host_folder_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
            StressLibquantumTool.HOST_FILE_NAME)
        path = self._common_content_lib.copy_zip_file_to_linux_sut(StressLibquantumTool.SUT_FOLDER_NAME,
                                                                   host_folder_path)
        path = Path(os.path.join(path, StressLibquantumTool.SUT_FOLDER_NAME)).as_posix().strip()
        self._log.info("Libquantum tool Successfully Installed")
        return path

    def install_mprime_tool(self):
        """
        This method is to install mprime tool.

        :return tool path
        """
        self._log.info("Move mprime tool to the SUT")
        host_folder_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
            StressMprimeTool.HOST_FILE_NAME)
        path = self._common_content_lib.copy_zip_file_to_linux_sut(StressMprimeTool.SUT_FOLDER_NAME,
                                                                   host_folder_path)
        self._log.info("Mprime tool Successfully Installed")
        return path

    def install_iometer_tool_windows(self):
        """
        This install iometer tool method will zip and copy the application folder to sut and install it

        :raise: If installation failed raise content_exceptions.TestFail
        :return sut_folder path
        """
        # Get iometer_tool folder path
        iometer_tool_path = os.path.join(self._common_content_lib.get_collateral_path(),
                                         IOmeterToolConstants.IOMETER_TOOL_FOLDER)
        self._log.debug("IOMeter tool path in collateral: {}".format(iometer_tool_path))
        # Copying config file to collateral iometer tool path
        bkc_config_file_path = self._common_content_configuration.get_iometer_tool_config_file()
        copy(bkc_config_file_path, iometer_tool_path)
        self._log.info("Getting SUT username and password from system configuration file")
        username, password = self._common_content_lib.get_sut_crediantials(self._cfg)
        IOmeterToolConstants.ADD_AUTOLOGON_REG.append(IOmeterToolConstants.DEFAULT_USER.format(username))
        IOmeterToolConstants.ADD_AUTOLOGON_REG.append(IOmeterToolConstants.DEFAULT_PASSWORD.format(password))
        abs_file_path = os.path.join(iometer_tool_path, IOmeterToolConstants.AUTO_LOGON_REG_FILE_NAME)
        with open(abs_file_path, "w", encoding='utf-16') as f:
            f.writelines(IOmeterToolConstants.ADD_AUTOLOGON_REG)
        self._log.info("Successfully created {} auto logon registry file"
                       .format(IOmeterToolConstants.AUTO_LOGON_REG_FILE_NAME))
        self._log.info("Executing compress command: {} under path: {} "
                       .format(IOmeterToolConstants.ZIP_CMD.format(IOmeterToolConstants.ZIP_FILE_NAME),
                               iometer_tool_path))
        host_folder_path = os.path.join(self._common_content_lib.get_collateral_path(),
                                        IOmeterToolConstants.ZIP_FILE_NAME)
        # Executing compress command: Powershell Compress-Archive *.* iometer_tool.zip
        if os.path.isfile(host_folder_path):
            os.remove(host_folder_path)
        self._common_content_lib.execute_cmd_on_host \
            (IOmeterToolConstants.ZIP_CMD.format(host_folder_path), iometer_tool_path)

        # Copying zip file to SUT
        if os.path.isfile(os.path.join(self.C_DRIVE_PATH, IOmeterToolConstants.IOMETER_TOOL_FOLDER)):
            self._common_content_lib.windows_sut_delete_folder(self.C_DRIVE_PATH,
                                                               IOmeterToolConstants.IOMETER_TOOL_FOLDER)

        sut_folder_path = self._common_content_lib.copy_zip_file_to_sut(IOmeterToolConstants.IOMETER_TOOL_FOLDER,
                                                                        host_folder_path)

        self._log.info("File successfully copied into SUT under {}".format(sut_folder_path))

        # Executing import iometer.reg command
        reg_output = self._common_content_lib.execute_sut_cmd(IOmeterToolConstants.REG_CMD, IOmeterToolConstants.REG_CMD
                                                              , self._command_timeout, sut_folder_path)
        self._log.debug("Successfully run iometer org file: {}".format(reg_output))

        return sut_folder_path

    def copy_and_install_hydra_tool(self):
        """
        This method copy and install sgx hydra tool from host to sut

        :return hydra tool folder path
        """
        make_cmd = "make SGX_PRERELEASE=1 SGX_DEBUG=0"
        sgxhydra_str = "/SGXHydra"
        self._log.info("Copying and installing SGX Hydra tool")
        hydra_tool_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
            SgxHydraToolConstants.HYDRA_TOOL)
        # copy and install sgx hydra tool to SUT
        hydra_path = self._common_content_lib.copy_zip_file_to_linux_sut(SgxHydraToolConstants.HYDRA_TEST_DIR,
                                                                         hydra_tool_path) + \
                     sgxhydra_str
        make_output = self._common_content_lib.execute_sut_cmd(make_cmd, make_cmd, self._command_timeout, hydra_path)
        self._log.debug("Make output is :{}".format(make_output))
        return hydra_path

    def copy_sgx_hydra_windows(self):
        """
        This method copy sgx hydra tool from host to windows sut

        :return: hydra tool folder path
        """
        self._log.info("Copy sgx hydra tool")
        self._log.info("Copying the zip files from {}".format(SgxHydraToolConstants.HYDRA_TOOL_WINDOWS))
        tool_path =self._artifactory_obj.download_tool_to_automation_tool_folder(
            SgxHydraToolConstants.HYDRA_TOOL_WINDOWS)
        hydra_path = self._common_content_lib.copy_zip_file_to_sut(SgxHydraToolConstants.HYDRA_TEST_DIR,
                                                                   tool_path)
        self.copy_hydra_dll_files(hydra_path)
        return hydra_path

    def copy_devcon_to_sut(self):
        """
        This Method is Used to Copy Devcon.exe from Collateral to Sut.

        :return:None
        """
        self._log.info("Copying {} file to SUT".format(self.DEVCON_FILE))
        devcon_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder(self.DEVCON_FILE)
        self._os.copy_local_file_to_sut(devcon_file_path, self.WINDOWS_USER_ADMIN_PATH)
        self._log.debug("Successfully copied the {} file under {}".format(self.DEVCON_FILE,
                                                                          self.WINDOWS_USER_ADMIN_PATH))

    def run_dsa_workload_on_all_wq_in_vm(self, spr_file_path,common_content_lib_vm,vm_obj):
        """
        This function runs workload on VM using Guest_Passthru_Randomize_DSA_Conf.sh.

        :param : spr_file_path : Scripts file path
        :param : common_content_lib_vm : Common content object
        :param : vm_os_obj : VM OS object
        :return: None
        """
        self._log.info("Running Guest_Passthru_Randomize_DSA_Conf test")
        configure_wq = "./Guest_Passthru_Randomize_DSA_Conf.sh -cu"
        cmd_output = common_content_lib_vm.execute_sut_cmd(sut_cmd=configure_wq,cmd_str=configure_wq,
                                                           execute_timeout=self._command_timeout,
                                                           cmd_path=spr_file_path)
        self._log.info("Configuring workqueues {}".format(cmd_output))
        cmd_dma = "./Guest_Passthru_Randomize_DSA_Conf.sh -o 0x3"
        cmd_output = common_content_lib_vm.execute_sut_cmd(sut_cmd=cmd_dma,cmd_str=cmd_dma,
                                                           execute_timeout=self._command_timeout,
                                                           cmd_path=spr_file_path)
        self._log.info("Running DSA workload on vm and output is {}".format(cmd_output))

        cmd_check_error = "journalctl --dmesg | grep error"
        cmd_opt = vm_obj.execute(cmd_check_error, self._command_timeout)
        if len(cmd_opt.stdout) == 0:
            self._log.info("No errors found")
        else:
            raise RuntimeError("Errors found after running workload")

    def install_verify_accel_config_no_idxd_reload(self, iax=False):
        """
        Install and verify accel config tool
        1. Copy to SUT
        2. Build the accel config tool
        3. Check the accel config basic command
        4. Show accel config components list
        5. accel config test unit test for libaccfg API's

        :raise: If installation/build failed raise content_exceptions.TestFail
        """
        self._log.info("Download and build accel config tool")
        accel_config_list_cmd = r"accel-config --list-cmds"
        grep_cmd = "grep 'test-libaccfg: PASS' temp.txt"
        accel_config_list_commands = ["version", "list", "load-config", "save-config", "help",
                                      "disable-device", "enable-device", "disable-wq", "enable-wq",
                                      "config-device", "config-group", "config-wq", "config-engine",
                                      "create-mdev", "remove-mdev"]
        cmd_not_present = []
        find_cmd = "find $(pwd) -type f -name 'autogen.sh'"
        cat_cmd = "cat temp.txt"
        dsa_accel_folder = "DSA_ACCEL"
        self._log.info("Accelerator tool path from the configuration file is : {}".format(self.accel_file_path))
        # Downloading the accel tool from artifactory
        self._log.info("Downloading Accel config tool")
        host_tool_path = self._artifactory_obj.download_tool_to_automation_tool_folder(self.accel_file_path)
        # Copy the DSA file to SUT
        sut_folder_path = self._common_content_lib.copy_zip_file_to_linux_sut(dsa_accel_folder, host_tool_path)
        self._log.debug("DSA Accel config file folder path {}".format(sut_folder_path))
        # Find autogen.sh file in sut_folder_path
        accel_dir_name = self._common_content_lib.execute_sut_cmd(find_cmd, "find the autogen.sh file path",
                                                                  self._command_timeout, sut_folder_path).split()[-1]
        self._log.debug("DSA accel config directory name {}".format(accel_dir_name))
        if not accel_dir_name:
            raise content_exceptions.TestFail("DSA accel config directory not found")
        accel_dir_path = os.path.split(accel_dir_name)[:-1][0]
        self._log.info("DSA accel config directory path {}".format(accel_dir_path))
        # Build accel config tool
        self.build_accel_config_tool(accel_dir_path)
        # verify the accel-config basic commands
        cmd_output = self._common_content_lib.execute_sut_cmd(accel_config_list_cmd, accel_config_list_cmd,
                                                              self._command_timeout, accel_dir_path)
        self._log.debug("accel-config basic commands list supported by the tool {}".format(cmd_output))
        for cmd_item in accel_config_list_commands:
            if cmd_item not in cmd_output.split():
                cmd_not_present.append(cmd_item)
        if cmd_not_present:
            raise content_exceptions.TestFail("These accel-config basic command are not present {}".format(
                cmd_not_present))
        # Verify accel config list of devices
        if iax:
            self.verify_iax_accel_config_list_devices()
        else:
            self.verify_accel_config_list_devices()

    def install_verify_accel_config(self, iax=False):
        """
        Install and verify accel config tool
        1. Copy to SUT
        2. Build the accel config tool
        3. Check the accel config basic command
        4. Show accel config components list
        5. accel config test unit test for libaccfg API's

        :raise: If installation/build failed raise content_exceptions.TestFail
        """
        self._log.info("Verify accel config tool")
        accel_config_list_cmd = r"accel-config --list-cmds"
        accel_config_test = r"accel-config test"
        accel_config_version = r"accel-config --version"
        success_string = "SUCCESS"
        version = self._common_content_configuration.get_accel_config_version()
        grep_cmd = "grep 'test-libaccfg: PASS' temp.txt"
        accel_config_list_commands = ["version", "list", "load-config", "save-config", "help",
                                      "disable-device", "enable-device", "disable-wq", "enable-wq",
                                      "config-device", "config-group", "config-wq", "config-engine",
                                      "create-mdev", "remove-mdev"]
        cmd_not_present = []
        self._log.info("Accelerator tool path from the configuration file is : {}".format(self.accel_file_path))
        # Downloading the accel tool from artifactory
        self._log.info("Downloading Accel config tool")
        host_tool_path = self._artifactory_obj.download_tool_to_automation_tool_folder(self.accel_file_path)
        dsa_accel_folder = "DSA_ACCEL"
        find_cmd = "find $(pwd) -type f -name 'autogen.sh'"
        # Copy the DSA file to SUT
        sut_folder_path = self._common_content_lib.copy_zip_file_to_linux_sut(dsa_accel_folder, host_tool_path)
        self._log.debug("DSA Accel config file folder path {}".format(sut_folder_path))
        # Find autogen.sh file in sut_folder_path
        accel_dir_name = self._common_content_lib.execute_sut_cmd(find_cmd, "find the autogen.sh file path",
                                                                  self._command_timeout, sut_folder_path).split()[-1]
        self._log.debug("DSA accel config directory name {}".format(accel_dir_name))

        if not accel_dir_name:
            raise content_exceptions.TestFail("DSA accel config directory not found")
        accel_dir_path = os.path.split(accel_dir_name)[:-1][0]
        self._log.info("DSA accel config directory path {}".format(accel_dir_path))
        # Build accel config tool
        self.build_accel_config_tool(accel_dir_path)
        # verify the accel-config basic commands
        cmd_output = self._common_content_lib.execute_sut_cmd(accel_config_list_cmd, accel_config_list_cmd,
                                                              self._command_timeout, accel_dir_path)
        self._log.debug("accel-config basic commands list supported by the tool {}".format(cmd_output))
        for cmd_item in accel_config_list_commands:
            if cmd_item not in cmd_output.split():
                cmd_not_present.append(cmd_item)
        if cmd_not_present:
            raise content_exceptions.TestFail("These accel-config basic command are not present {}".format(
                cmd_not_present))

        # Verify accel config list of devices
        if iax:
            self.verify_iax_accel_config_list_devices()
        else:
            self.verify_accel_config_list_devices()

        # Verify accel config test
        cmd_output = self._common_content_lib.execute_sut_cmd(accel_config_test, accel_config_test,
                                                              self._command_timeout)
        self._log.debug("accel-config test command output {}".format(cmd_output))
        if success_string not in cmd_output:
            raise content_exceptions.TestFail("The accel-config test failed, {} not in {}".format(
                success_string,cmd_output))
        self._log.info("Successfully tested the libaccfg APIs by running {}".format(accel_config_test))

        # Verify accel config version
        cmd_output = self._common_content_lib.execute_sut_cmd(accel_config_version, accel_config_version,
                                                              self._command_timeout)
        self._log.debug("accel-config version command output {}".format(cmd_output))
        if version not in cmd_output:
            raise content_exceptions.TestFail("The accel-config version failed, {} not in {}".format(
                version, cmd_output))
        self._log.info("Accel-config version : {}".format(version))

        self._log.info("Reload idxd module.")
        self._common_content_lib.execute_sut_cmd("modprobe idxd", "modprobe idxd", self._command_timeout)

    def setup_spr_on_vm(self, common_content_lib_vm):
        """
        This function setup SPR on VM.

        :param : install_collateral_vm_obj : install_collateral vm_obj

        :return: None
        """
        self._log.info("Copying SPR to VM from SUT")
        spr_folder = "SPR"
        self.spr_file_path = self._common_content_configuration.get_spr_file()
        host_tool_path = self._artifactory_obj.download_tool_to_automation_tool_folder(self.spr_file_path)
        sut_folder_path = common_content_lib_vm.copy_zip_file_to_linux_sut(spr_folder, host_tool_path)

    def run_workload_on_vm(self, spr_file_path,common_content_lib_vm,vm_obj):
        """
        This function runs workload on VM.

        :param : vm_os_obj : VM OS object

        :return: None
        """
        self._log.info("Running DMA test")
        configure_wq = "./Guest_Mdev_Randomize_DSA_Conf.sh -k"
        cmd_output = common_content_lib_vm.execute_sut_cmd(sut_cmd=configure_wq,cmd_str=configure_wq,
                                                           execute_timeout=self._command_timeout,
                                                           cmd_path=spr_file_path)
        self._log.info("Configuring workqueues {}".format(cmd_output))
        cmd_dma = "./Guest_Mdev_Randomize_DSA_Conf.sh -i 1000 -j 10"
        cmd_output = common_content_lib_vm.execute_sut_cmd(sut_cmd=cmd_dma,cmd_str=cmd_dma,
                                                           execute_timeout=self._command_timeout,
                                                           cmd_path=spr_file_path)
        self._log.info("Running DSA workload on vm and output is {}".format(cmd_output))

        cmd_check_error = "journalctl --dmesg | grep error"
        cmd_opt = vm_obj.execute(cmd_check_error, self._command_timeout)
        if len(cmd_opt.stdout) == 0:
            self._log.info("No errors found")
        else:
            raise RuntimeError("Errors found after running workload")

    def run_iax_workload_on_vm(self, spr_file_path, common_content_lib_vm, vm_obj, i_value=1000, j_value=10):
        """
        This function runs IAX workload on VM.

        :param : vm_os_obj : VM OS object

        :return: None
        """
        self._log.info("Running DMA test")
        configure_wq = "./Guest_Mdev_Randomize_IAX_Conf.sh -k"
        cmd_output = common_content_lib_vm.execute_sut_cmd(sut_cmd=configure_wq, cmd_str=configure_wq,
                                                           execute_timeout=self._command_timeout,
                                                           cmd_path=spr_file_path)
        self._log.info("Configuring workqueues {}".format(cmd_output))
        cmd_dma = "./Guest_Mdev_Randomize_IAX_Conf.sh -i {} -j {}".format(i_value, j_value)
        cmd_output = common_content_lib_vm.execute_sut_cmd(sut_cmd=cmd_dma, cmd_str=cmd_dma,
                                                           execute_timeout=self._command_timeout,
                                                           cmd_path=spr_file_path)
        self._log.info("Running IAX workload on vm and output is {}".format(cmd_output))

        cmd_check_error = "journalctl --dmesg | grep error"
        cmd_opt = vm_obj.execute(cmd_check_error, self._command_timeout)
        if len(cmd_opt.stdout) == 0:
            self._log.info("No errors found")
        else:
            raise RuntimeError("Errors found after running workload")

    def run_dsa_workload_on_vm(self, spr_file_path, common_content_lib_vm, vm_obj):
        """
        This function runs IAX workload on VM.

        :param : vm_os_obj : VM OS object

        :return: None
        """
        self._log.info("Running DMA test")
        configure_wq = "./Guest_Mdev_Randomize_DSA_Conf.sh -k"
        cmd_output = common_content_lib_vm.execute_sut_cmd(sut_cmd=configure_wq,cmd_str=configure_wq,
                                                           execute_timeout=self._command_timeout,
                                                           cmd_path=spr_file_path)
        self._log.info("Configuring workqueues {}".format(cmd_output))
        cmd_dma = "./Guest_Mdev_Randomize_DSA_Conf.sh -i 100 -j 2"
        cmd_output = common_content_lib_vm.execute_sut_cmd(sut_cmd=cmd_dma,cmd_str=cmd_dma,
                                                           execute_timeout=self._command_timeout,
                                                           cmd_path=spr_file_path)
        self._log.info("Running DSA workload on vm and output is {}".format(cmd_output))
        cmd_check_error = "journalctl --dmesg | grep error"
        cmd_opt = vm_obj.execute(cmd_check_error, self._command_timeout)
        if len(cmd_opt.stdout) == 0:
            self._log.info("No errors found")
        else:
            raise RuntimeError("Errors found after running workload")

    def install_and_verify_accel_config_vm(self, common_content_lib_vm):
        """
        Install and verify accel config tool
        1. Copy to SUT
        2. Build the accel config tool
        3. Check the accel config basic command
        4. Show accel config components list
        5. accel config test unit test for libaccfg API's

        :raise: If installation/build failed raise content_exceptions.TestFail
        """
        self._log.info("Download and build accel config tool")
        accel_config_list_cmd = r"accel-config --list-cmds"
        find_cmd = "find $(pwd) -type f -name 'autogen.sh'"
        dsa_accel_folder = "DSA_ACCEL"

        host_tool_path = self._artifactory_obj.download_tool_to_automation_tool_folder(self.accel_file_path)
        # Copy the DSA file to SUT
        sut_folder_path = common_content_lib_vm.copy_zip_file_to_linux_sut(dsa_accel_folder, host_tool_path)
        self._log.debug("DSA Accel config file folder path {}".format(sut_folder_path))
        accel_dir_name = common_content_lib_vm.execute_sut_cmd(find_cmd, "find the autogen.sh file path",
                                                               self._command_timeout, self.ROOT_PATH)
        if not accel_dir_name:
            raise content_exceptions.TestFail("DSA accel config directory not found")
        accel_dir_path = os.path.split(accel_dir_name)[:-1][0]
        self._log.info("DSA accel config directory path {}".format(accel_dir_path))

        cmd_autogen = "./autogen.sh -v"
        cmd_configure = "./configure CFLAGS='-g -O2' --prefix=/usr --sysconfdir=/etc --libdir=/usr/lib64 " \
                        "--enable-test=yes --enable-debug=yes"
        cmd_make_all = "make all"

        cmd_output = common_content_lib_vm.execute_sut_cmd(cmd_autogen, cmd_autogen, self._command_timeout,
                                                              accel_dir_path)
        self._log.info("Autogen output on VM {}".format(cmd_output))

        cmd_output1 = common_content_lib_vm.execute_sut_cmd(cmd_configure, cmd_configure, self._command_timeout,
                                                           accel_dir_path)
        self._log.info("Configure output on VM {}".format(cmd_output1))

        cmd_output2 = common_content_lib_vm.execute_sut_cmd(cmd_make_all, cmd_make_all, self._command_timeout,
                                                            accel_dir_path)
        self._log.info("Make command output {}".format(cmd_output2))

    def build_accel_config_tool(self, accel_dir_path):
        """
        This  function build the accel config tool
        1../autogen.sh -v
        2. ./configure CFLAGS='-g -O2' --prefix=/usr --sysconfdir=/etc --libdir=/usr/lib64 " \
                       "--enable-test=yes --enable-debug=yes
        3. make all
        4. sudo make install

        :param accel_dir_path: accel config folder path
        :raise: raise content exceptions if not build accel config tool
        """
        cmd_autogen = "./autogen.sh -v"
        cmd_configure = "./configure CFLAGS='-g -O2' --prefix=/usr --sysconfdir=/etc --libdir=/usr/lib64 " \
                        "--enable-test=yes --enable-debug=yes"
        cmd_make_all = "make all"
        cmd_make_install = "sudo make install"
        autogen_regex = r"./configure CFLAGS='-g -O2' --prefix=/usr --sysconfdir=/etc --libdir=/usr/lib64"

        self._log.info("Build the accel config tool")
        # Build accel config autogen.sh command
        cmd_output = self._common_content_lib.execute_sut_cmd(cmd_autogen, cmd_autogen, self._command_timeout,
                                                              accel_dir_path)
        self._log.debug("accel config autogen command output {}".format(cmd_output))
        autogen_output = re.search(autogen_regex, cmd_output)
        if not autogen_output:
            raise content_exceptions.TestFail("Accel config build got failed")
        # Configure accel config tool
        cmd_output = self._common_content_lib.execute_sut_cmd(cmd_configure, cmd_configure, self._command_timeout,
                                                              accel_dir_path)
        self._log.debug("accel config configure output {}".format(cmd_output))
        # make all command for accel config
        cmd_output = self._common_content_lib.execute_sut_cmd(cmd_make_all, cmd_make_all, self._command_timeout,
                                                              accel_dir_path)
        self._log.debug("accel config tool make all output {}".format(cmd_output))
        # sudo make install command for accel config tool
        cmd_output = self._common_content_lib.execute_sut_cmd(cmd_make_install, cmd_make_install, self._command_timeout,
                                                              accel_dir_path)
        self._log.debug("accel config tool sudo make install output {}".format(cmd_output))

    def verify_accel_config_list_devices(self):
        """
        This function verify accel config tool list of devices

        :param accel_dir_path: accel config folder path
        :raise: raise content exception if not found 8 dsa devices
        """
        accel_cofnig_list = r"accel-config list -i"
        regex_dsa = "dsa(\d+)"
        dsa_device_list = []
        dsa_device_count = 8
        self._log.info("Verify accel config dsa devices")
        # verify the accel-config components
        cmd_output = self._common_content_lib.execute_sut_cmd(accel_cofnig_list, accel_cofnig_list,
                                                              self._command_timeout)
        self._log.debug("accel-config components in json format {}".format(cmd_output))
        import ast
        dsa_list_dict = [item for item in ast.literal_eval(cmd_output)]
        for item in range(len(dsa_list_dict)):
            if re.search(regex_dsa, dsa_list_dict[item]["dev"]):
                dsa_device_list.append(dsa_list_dict[item]["dev"])
        self._log.debug("List of dsa devices {}".format(dsa_device_list))
        if len(dsa_device_list) != dsa_device_count:
            raise content_exceptions.TestFail("8 DSA devices not found")
        self._log.info("Found all dsa devices from dsa0 to dsa7")

    def install_kernel_dsa_rpm_on_linux(self, is_vm=None):
        """
               This Method is Used to Install Kernal rpm on Linux Sut, by copying Kernal Rpm file from Collateral to Sut.

               """
        self._log.info(
            "Installing Kernel rpm on Sut")  # rpm file name-kernel-next-server-devel-5.12.0-2021.05.07_49.el8.x86_64.rpm
        kernel_rpm_file = self.kernel_dsa_rpm_file_name
        if is_vm != None:
            kernel_rpm_file = self.vm_kernel_dsa_rpm_file_name
        else:
            kernel_rpm_file = self.kernel_dsa_rpm_file_name
        cmd_to_install_kernel_rpm = "rpm -ivh --nodeps --force {}".format(kernel_rpm_file)
        kernel_rpm_tool_path = self._artifactory_obj.download_tool_to_automation_tool_folder(kernel_rpm_file)
        sut_path = self.util_constants["LINUX_USR_ROOT_PATH"]
        self._os.copy_local_file_to_sut(kernel_rpm_tool_path, sut_path)
        self._log.debug("Kernel Rpm File is Successfully Copied to SUT")
        kernel_rpm_cmd_output = self._common_content_lib.execute_sut_cmd_no_exception(cmd_to_install_kernel_rpm,
                                                                                      "Installing rpm",
                                                                                      self._command_timeout)
        self._log.info("Kernel rpm is Successfully Installed on SUT {}".format(kernel_rpm_cmd_output))

    def install_rdt_stream_tool_to_sut(self):
        """
        This method installs the stream tool to sut.
        :return: stream_tool_path
        """
        stream_tool_path = self.get_stream_dir_path()
        cmd_to_install_stream = "gcc -O -DSTREAM_ARRAY_SIZE=100000000 -DNTIMES=12000 stream.c -o stream"
        self._log.info("Installing stream tool to sut")
        install_cmd_res = self._common_content_lib.execute_sut_cmd(
            cmd_to_install_stream, "Install stream", self._command_timeout, stream_tool_path)
        self._log.info("stream tool installation is successful and command output is '{}'".format(install_cmd_res))
        return stream_tool_path

    def get_stream_dir_path(self):
        """
        This method returns the dir path where stream tool is installed.
        :return: stream tool path on SUT
        """
        find_stream_dir = "find $(pwd) -type d -name 'stream*'"
        # Copy stream tool tar file to sut
        self._log.info("Copying stream tool to SUT and installing")
        host_tool_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
            RDTConstants.RDT_STREAM_CONSTANTS["STREAM_LINUX_FILE"])
        stream_tool_dir_path = self._common_content_lib.copy_zip_file_to_linux_sut(
            RDTConstants.RDT_STREAM_CONSTANTS["STREAM_DIR"], host_tool_path)
        self._log.debug("Stream tool path in sut is '{}'".format(stream_tool_dir_path))
        stream_tool_path = self._common_content_lib.execute_sut_cmd(find_stream_dir, find_stream_dir,
                                                                    self._command_timeout,
                                                                    cmd_path=stream_tool_dir_path).strip()
        self._log.debug("stream tool executable path in sut is '{}'".format(stream_tool_path))
        return stream_tool_path

    def install_pcm_tool(self):
        """
        This method installs pcm tool on the Linux SUT

        :return: the installed tool path on SUT
        """
        # copy the PCM tool from collateral to SUT
        pcm_sut_folder_name = PcmToolConstants.PCM_TOOL_ZIP_FILE.split(".")[-2]
        host_foldr_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
            PcmToolConstants.PCM_TOOL_ZIP_FILE)
        self._log.debug("Copy the {} to sut".format(PcmToolConstants.PCM_TOOL_ZIP_FILE))
        pcm_extracted_folder_path_in_sut = self._common_content_lib.copy_zip_file_to_linux_sut(
            pcm_sut_folder_name, host_foldr_path)
        pcm_extracted_folder_path_in_sut = pcm_extracted_folder_path_in_sut + "/" + \
                                           pcm_extracted_folder_path_in_sut.split("/")[-1]

        # run make command to install the tool
        self._log.debug("Run make command")
        self._common_content_lib.execute_sut_cmd("make", "make", self._command_timeout,
                                                 cmd_path=pcm_extracted_folder_path_in_sut)
        return pcm_extracted_folder_path_in_sut

    def install_ioport(self):
        """
        This function is to install ioport in linux sut

        :raise: Raise error if not installed
        """

        if OperatingSystems.LINUX == self.sut_os:
            self._log.info("Installing IOPort rpm package")
            host_folder_path = self._artifactory_obj.download_tool_to_automation_tool_folder(self.IO_PORT_ZIP_FILE)
            sut_folder_path = self._common_content_lib.copy_zip_file_to_linux_sut(
                sut_folder_name=self.IO_PORT.split('-')[0], host_zip_file_path=host_folder_path)
            self._log.info("IOport path in SUT is : {}".format(sut_folder_path))
            self.yum_install(package_name=self.IO_PORT, cmd_path=sut_folder_path)
            self._log.info("Successfully installed IOPort tool in SUT")
        elif OperatingSystems.WINDOWS == self.sut_os:
            self._log.info("IOPort tool not applicable for windows ...")
        else:
            log_error = "IOPort is not supported on OS '{}'".format(self._os.sut_os)
            self._log.error(log_error)
            raise NotImplementedError(log_error)

    def install_pcm_memory_tool(self):
        """
        This method installs pcm memory tool on the Linux SUT

        :return: the installed tool path on SUT
        """
        # copy the PCM tool from collateral to SUT

        self._log.debug("Copy the {} to sut".format(PcmMemoryConstants.PCM_TOOL_FILE))

        host_folder_path = self._artifactory_obj.download_tool_to_automation_tool_folder(PcmMemoryConstants.PCM_TOOL_FILE)
        self._os.copy_local_file_to_sut(host_folder_path, self._common_content_lib.ROOT_PATH)
        self._os.execute("chmod +777 {}".format(PcmMemoryConstants.PCM_TOOL_FILE), self._command_timeout,
                         self._common_content_lib.ROOT_PATH)
        return self._common_content_lib.ROOT_PATH

    def roll_back_embargo_repo(self):
        """
        This function is used to roll back the embargo repos
        """
        if self._os.os_subtype.lower() == LinuxDistributions.CentOS.lower():
            sed_update_config = self._common_content_configuration.get_sed_update_soc_watch().split(r'/')
            self._log.info("sed Update command from config is : {}".format(sed_update_config))
            sed_command = "sed -i 's/{}/{}/' {}".format(sed_update_config[1], sed_update_config[0], self.EMBARGO_REPO)
            repo_result = self._os.execute("cat {}".format(self.EMBARGO_REPO), self._command_timeout)
            self._log.debug(repo_result.stdout)
            self._log.debug(repo_result.stderr)
            # To replace number with latest
            if sed_update_config[0] not in repo_result.stdout:
                self._log.info("Executing the command : {}".format(sed_command))
                self._os.execute(sed_command, self._command_timeout)
        else:
            self._log.info("Changing repos to normal not required in OS : {}".format(self._os.os_subtype))

    def load_intel_e810_network_adapter(self):
        """
        This method load Intel Network Adapter Driver for E810 Series Devices

        """
        self._log.info("Load Intel E810 network adapter driver")
        if OperatingSystems.LINUX == self._os.os_type:
            network_adapter_driver = self._common_content_configuration.get_e810_network_adapter_driver()
            adapter_driver_name = os.path.split(network_adapter_driver)[-1].strip()
            adapter_folder_name = adapter_driver_name.split('.tar')[0]
            adapter_host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(adapter_driver_name)
            driver_executer_path = self._common_content_lib.copy_zip_file_to_linux_sut("E810_driver", adapter_host_path)

            driver_path = Path(os.path.join(driver_executer_path, adapter_folder_name)).as_posix()
            driver_actual_path = Path(os.path.join(driver_path, "src")).as_posix()
            make_cmd = "make -j"
            install_pre_requisite = self._common_content_configuration.get_pre_requisite_packages()
            for package in install_pre_requisite:
                try:
                    self.yum_install(package)
                except Exception as ex:
                    self._log.error("Failed to install package '{}' due to exception:'{}'".format(package, ex))

            # load the E810 driver
            command_result = self._common_content_lib.execute_sut_cmd(make_cmd, "run make command to build driver",
                                                                      self._command_timeout, driver_actual_path)
            self._log.debug("Building E810 driver output \n {}".format(command_result))

            # Enable the driver
            self._common_content_lib.execute_sut_cmd("insmod ice.ko", "run ice driver load command",
                                                     self._command_timeout, driver_actual_path)
        else:
            raise NotImplementedError(
                "Loading Intel E810 network driver is not implemented in {} os".format(self._os.os_type))

    def copy_and_execute_tolerant_script(self):
        """
        This Method is to copy the update_linux_tolerant.py to SUT, which inturn Change values to 3 from 1 for
        all machinechecks.

        :return:
        """
        host_tolerant_path = self._artifactory_obj.download_tool_to_automation_tool_folder(self.TOLERANT_FILE)

        self._log.info("Copying update_linux_tolerant.py to SUT")
        self._os.copy_local_file_to_sut(host_tolerant_path, self.util_constants["LINUX_USR_ROOT_PATH"])
        self._log.info("Running update_linux_tolerant.py on SUT side")
        self._os.execute("python {}".format(self.TOLERANT_FILE), self._common_content_configuration.
                         get_command_timeout(), self.util_constants["LINUX_USR_ROOT_PATH"])

    def install_run_stream(self):
        """
        This method is used to check the pnpwls existance and upload the pnpwls from the host machine to SUT

        return: Path where the run_stream.sh is available on SUT
        raise: ImplementationError
        """
        self._log.info("Load pnp workload run_stream to SUT")
        if OperatingSystems.LINUX == self._os.os_type:
            default_path = "/root/stress/pnpwls-master/stream"
            stream_path = Path(os.path.join(default_path, "run_stream.sh")).as_posix()
            if not self._os.check_if_path_exists(stream_path):
                host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(self.pnpwls["pnp_workload"])
                pnpwls_path = self._common_content_lib.copy_zip_file_to_linux_sut("stress", host_path)
                workload = self.pnpwls["pnp_workload"].split(".tar.gz")
                pnpwls_actual_path = Path(os.path.join(pnpwls_path, workload[0])).as_posix()
                pnpwls_stream_path = Path(
                    os.path.join(pnpwls_actual_path, self.pnpwls["stream_folder_name"])).as_posix()
                return pnpwls_stream_path
            else:
                return default_path
        else:
            raise NotImplementedError(
                "Install run stream is not implemented in {} os".format(self._os.os_type))

    def install_runner_tool(self):
        """
            This method installs the ras runner tool by copying the ras runner cmds in runner folder
        """
        self._log.info("Installing ras runner tool")
        artifactory_name = ArtifactoryName.DictLinuxTools[ArtifactoryTools.RAS_RUNNER_TOOL_NAME]
        host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
        sut_runner_path = self._common_content_lib.copy_zip_file_to_linux_sut(self.RAS_RUNNER_SUT_FOLDER_NAME,
                                                                              host_path)
        self._log.info("runner file is extracted and copied to SUT path {}".format(sut_runner_path))
        remove_runner = "rm -rf {}".format(self.RAS_RUNNER_FOLDER_INSTALLATION_PATH)
        self._common_content_lib.execute_sut_cmd(remove_runner, remove_runner, self._command_timeout, cmd_path="/")
        cmd_line = "mkdir {}".format(self.RAS_RUNNER_SUT_FOLDER_NAME)
        self._common_content_lib.execute_sut_cmd(cmd_line, cmd_line, self._command_timeout, cmd_path="/")
        self._common_content_lib.execute_sut_cmd(RasRunnerToolConstant.RUNNER_FOLDER_PATH,
                                                 "runner_copy_cmd", self._command_timeout)
        self._common_content_lib.execute_sut_cmd("unzip runner_files.zip", "unzip_runner_file", self._command_timeout,
                                                 "/runner")
        for each_cp_cmd in range(len(RasRunnerToolConstant.RUNNER_CMD_DICT)):
            self._common_content_lib.execute_sut_cmd(RasRunnerToolConstant.RUNNER_CMD_DICT[each_cp_cmd], "Copy files",
                                                     self._command_timeout)
        self._log.info("Successfully Installed ras runner tool")

    def screen_package_installation(self, vm_os_linux=False):
        """
        Installs screen rpm

        :param vm_os_linux - Install screen package on Linux VM.
        """
        if self._os.os_type.lower() == OperatingSystems.LINUX.lower() or vm_os_linux == True:
            res = self._os.execute("screen --version", self._command_timeout)

            if "Screen version" not in res.stdout:

                host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(self.SCREEN_ZIP_NAME)
                path_screen = self._common_content_lib.copy_zip_file_to_linux_sut(self.SCREEN_ZIP_NAME.split(".")[0],
                                                                                  host_path)
                path_screen_rpm = Path(
                    os.path.join(path_screen, self.SCREEN_RPM_NAME)).as_posix()
                self._log.info("Screen folder path -- {}".format(path_screen_rpm))

                self._log.info("Screen package is not installed on this SUT, proceeding further to install ..")
                res_screen = self._os.execute("yum install {} -y".format(path_screen_rpm), self._command_timeout)

                if res_screen.cmd_failed():
                    self._log.debug("Screen package installation failed, please check necessary repos are "
                                    "enabled and try again..")
                else:
                    self._log.info("Screen package installation successful.")
            else:
                self._log.info("{} already installed..".format(res.stdout.strip()))

    def install_kernel_rpm_on_linux(self, os_obj=None, common_content_lib=None, is_vm=None):
        """
        This Method is Used to Install Kernal rpm on Linux Sut, by copying Kernal Rpm file from Collateral to Sut.

        """
        self._log.info("Installing Kernel rpm on Sut") #rpm file name-kernel-next-server-devel-5.12.0-2021.05.07_49.el8.x86_64.rpm
        if os_obj == None:
            os_obj = self._os
        if common_content_lib == None:
            common_content_lib = self._common_content_lib
        kernel_rpm_file = self.kernel_rpm_file_name
        if is_vm != None:
            kernel_rpm_file = self.vm_kernel_rpm_file_name
        else:
            kernel_rpm_file = self.kernel_rpm_file_name
        cmd_to_install_kernel_rpm = "rpm -ivh --nodeps --force {}".format(kernel_rpm_file)
        kernel_rpm_tool_path = self._artifactory_obj.download_tool_to_automation_tool_folder(kernel_rpm_file)
        sut_path = self.util_constants["LINUX_USR_ROOT_PATH"]
        os_obj.copy_local_file_to_sut(kernel_rpm_tool_path, sut_path)
        self._log.debug("Kernel Rpm File is Successfully Copied to SUT")
        kernel_rpm_cmd_output = common_content_lib.execute_sut_cmd_no_exception(cmd_to_install_kernel_rpm,
                                                                                      "Installing rpm",
                                                                                      self._command_timeout)
        self._log.info("Kernel rpm is Successfully Installed on SUT {}".format(kernel_rpm_cmd_output))

    def download_and_copy_zip_to_sut(self, sut_folder_name, tool_file_name):
        """
        This method is to download the tool from Artifactory and copy to SUT.

        :param sut_folder_name
        :param tool_file_name
        """
        tool_path = self._artifactory_obj.download_tool_to_automation_tool_folder(tool_file_name)
        if self._os.os_type == OperatingSystems.LINUX:
            zip_file_path = self._common_content_lib.copy_zip_file_to_linux_sut(sut_folder_name, tool_path)
        else:
            zip_file_path = self._common_content_lib.copy_zip_file_to_sut(sut_folder_name, tool_path)

        return zip_file_path

    def download_tool_to_host(self, tool_name, exec_env=None):
        """
        This method is to dowload the tool to Host from Artifactory.

        :param tool_name
        :param exec_env
        :return tool_path
        """
        return self._artifactory_obj.download_tool_to_automation_tool_folder(tool_name, exec_env)

    def install_iperf_on_linux(self, common_content_lib=None):
        """
        This Method is Used to Install Iperf Tool on Linux Sut, by copying Iperf Rpm file from Collateral to Sut.

        :param common_content_lib: Sut2 Common Content Lib object if passed else it will take self._common_content_lib
        """
        self._log.info("Copying Iperf Tool to Sut")
        iperf_tool_path = self._artifactory_obj.download_tool_to_automation_tool_folder(self.IPERF_TOOL)
        sut_path = self.util_constants["LINUX_USR_ROOT_PATH"]
        self._os.copy_local_file_to_sut(iperf_tool_path, sut_path)
        self._log.debug("Iperf Tools Rpm File is Successfully Copied to SUT")
        common_content_lib = common_content_lib if common_content_lib else self._common_content_lib
        iperf_tool_cmd_output = common_content_lib.execute_sut_cmd(self.IPERF_TOOL_INSTALLATION_CMD,
                                                                   self.IPERF_TOOL_INSTALLATION_CMD,
                                                                   self._command_timeout)
        self._log.info("Iperf Tool is Successfully Installed on SUT {}".format(iperf_tool_cmd_output))

    def install_iperf_on_linux_rpm_cmd(self, common_content_lib=None, os_obj=None):
        """
        This Method is Used to Install Iperf Tool on Linux Sut, by copying Iperf Rpm file from Collateral to Sut.

        :param common_content_lib: Sut2 Common Content Lib object if passed else it will take self._common_content_lib
        """
        if os_obj is None:
            os_obj = self._os
        if common_content_lib is None:
            common_content_lib = self._common_content_lib

        self._log.info("Copying Iperf Tool to Sut")
        iperf_tool_path = self._artifactory_obj.download_tool_to_automation_tool_folder(self.IPERF_TOOL)
        sut_path = self.util_constants["LINUX_USR_ROOT_PATH"]
        os_obj.copy_local_file_to_sut(iperf_tool_path, sut_path)
        self._log.debug("Iperf Tools Rpm File is Successfully Copied to SUT")
        common_content_lib = common_content_lib if common_content_lib else self._common_content_lib
        self.disable_firewall_in_linux(common_content_lib)
        time.sleep(2)
        common_content_lib.execute_sut_cmd("chmod 777 {}".format(self.IPERF_TOOL),
                                           "chmod 777 {}".format(self.IPERF_TOOL),
                                           self._command_timeout)
        time.sleep(1)
        iperf_tool_cmd_output = common_content_lib.execute_sut_cmd(self.IPERF_TOOL_INSTALLATION_CMD_RPM,
                                                                   self.IPERF_TOOL_INSTALLATION_CMD_RPM,
                                                                   self._command_timeout)
        self._log.info("Iperf Tool is Successfully Installed on SUT {}".format(iperf_tool_cmd_output))

    def disable_firewall_in_linux(self, common_content_lib):
        common_content_lib.execute_sut_cmd("systemctl disable firewalld",
                                           "systemctl disable firewalld",
                                           self._command_timeout)

    def install_iperf_on_esxi(self, common_content_lib=None):
        """
        This Method is Used to Install Iperf Tool on Linux Sut, by copying Iperf Rpm file from Collateral to Sut.

        :param common_content_lib: Sut2 Common Content Lib object if passed else it will take self._common_content_lib
        """
        if common_content_lib is None:
            common_content_lib = self._common_content_lib

        self._log.info("Copying Iperf Tool to Sut")
        iperf_tool_path = self._artifactory_obj.download_tool_to_automation_tool_folder(self.IPERF_TOOL_ESXI)
        sut_path = self.util_constants["ESXI_USR_ROOT_PATH"]
        self._os.copy_local_file_to_sut(iperf_tool_path, sut_path)
        self._log.debug("Iperf Tools Rpm File is Successfully Copied to SUT")
        common_content_lib = common_content_lib if common_content_lib else self._common_content_lib
        self.disable_firewall_in_esxi(common_content_lib)
        time.sleep(2)
        iperf_tool_cmd_output = common_content_lib.execute_sut_cmd(self.IPERF_TOOL_INSTALLATION_CMD_ESXI,
                                                                   self.IPERF_TOOL_INSTALLATION_CMD_ESXI,
                                                                   self._command_timeout)
        self._log.info("Iperf Tool is Successfully Installed on SUT {}".format(iperf_tool_cmd_output))

    def disable_firewall_in_esxi(self, common_content_lib):
        cmd_get="esxcli network firewall get"
        common_content_lib.execute_sut_cmd(cmd_get,"get_firewall_status",self._command_timeout)
        cmd="esxcli network firewall set --enabled false"
        common_content_lib.execute_sut_cmd(cmd,
                                           "esxcli network firewall set –-enabled false",
                                           self._command_timeout)

    def install_iperf_on_windows(self, common_content_lib=None):
        """
        This Method is Used to Install Iperf Tool on Windows Sut, by copying Iperf Zip file from Collateral to Sut.

        :return sut_iperf_path: Iperf Tool Path in SUT.
        """
        self._log.info("Copying Iperf Tool to SUT")
        common_content_lib = common_content_lib if common_content_lib else self._common_content_lib
        host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(self.IPERF_TOOL_WINDOWS)
        # copying file to windows SUT in C:\\ from host
        self._os.copy_local_file_to_sut(host_path, self.C_DRIVE_PATH)

        # delete the folder in Window SUT
        common_content_lib.windows_sut_delete_folder(self.C_DRIVE_PATH, "Iperf")

        cmd_to_extract = "powershell Expand-Archive -Path '{}' -DestinationPath '{}'".format(
            os.path.join(self.C_DRIVE_PATH, self.IPERF_TOOL_WINDOWS), self.IPERF_FOLDER_PATH)

        # creating the folder and extract the zip file
        command_result = self._os.execute(cmd_to_extract, timeout=self._command_timeout, cwd=self.C_DRIVE_PATH)
        if command_result.cmd_failed():
            log_error = "failed to run the command '{}' with return value = '{}' and " \
                        "std error = '{}' ..".format(cmd_to_extract, command_result.return_code, command_result.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        sut_path_sut = os.path.join(self.C_DRIVE_PATH, "Iperf")

        self._log.info("The file '{}' has been unzipped successfully ..".format(self.IPERF_TOOL_WINDOWS))
        iperf_path = os.path.join(sut_path_sut, self.IPERF_TOOL_WINDOWS)
        self._log.info("Iperf folder is Copied Successfully to path {}".format(iperf_path))
        sut_iperf_path = iperf_path.replace(".zip", "")
        self._log.info("Iperf Path in Sut is : '{}'".format(sut_iperf_path))
        return sut_iperf_path

    def install_iperf_on_vm(self):
        """
        This method is to install iperf on VM.
        """
        if self._os.os_type == OperatingSystems.LINUX:
            return self.install_iperf_on_linux()
        elif self._os.os_type == OperatingSystems.WINDOWS:
            return self.install_iperf_on_windows()
        elif self._os.os_type == OperatingSystems.ESXI:
            return self.install_iperf_on_esxi()
        else:
            raise content_exceptions.TestFail("Not Implemented for OS type- {}".format(self._os.os_type))

    def install_burnin_tool_on_windows(self):
        """
        To install burnin tool for windows
        :return: bit installed path
        """
        bit_find_command = r"where /R C:\\ " + BurnInConstants.BIT_EXE_FILE_NAME_WINDOWS
        cmd_result = self._os.execute(bit_find_command, self._command_timeout)
        self._log.debug(cmd_result.stdout)
        self._log.debug(cmd_result.stderr)
        if not cmd_result.stdout:
            host_folder_path = self._artifactory_obj.download_tool_to_automation_tool_folder(self.BURNIN_FILE_ZIP)
            zip_file = os.path.basename(host_folder_path)
            if not os.path.isfile(host_folder_path):
                raise IOError("{} does not found".format(host_folder_path))

            # copying file to windows SUT in C:\\ from host
            self._os.copy_local_file_to_sut(host_folder_path, self.C_DRIVE_PATH)

            # delete the folder in Window SUT
            self._common_content_lib.windows_sut_delete_folder(self.C_DRIVE_PATH, "burnin_tool")

            powershell_cmd = "powershell Expand-Archive -Path '{}' -DestinationPath '{}'".format(
                self.BURNIN_TOOL_SUT_ZIP_PATH, self.BURNIN_TOOL_FOLDER_PATH)
            # creating the folder and extract the zip file
            command_result = self._os.execute(powershell_cmd, timeout=self._command_timeout, cwd=self.C_DRIVE_PATH)
            if command_result.cmd_failed():
                log_error = "failed to run the command 'mkdir && tar' with return value = '{}' and " \
                            "std error = '{}' ..".format(command_result.return_code, command_result.stderr)
                self._log.error(log_error)
                raise RuntimeError(log_error)

            bit_extracted_path = os.path.join(self.C_DRIVE_PATH, "burnin_tool")

            self._log.info("The file '{}' has been unzipped successfully ..".format(zip_file))

            self._log.debug("BIT Extracted path : {}".format(bit_extracted_path))

            self._os.execute("rmdir /Q/S {}".format(BurnInConstants.BIT_INSTALLED_PATH_WINDOWS),
                             self._command_timeout)
            BIT_INSTALL_COMMAND_WINDOWS = 'bitpro.exe /VERYSILENT /DIR={}'.format(
                BurnInConstants.BIT_INSTALLED_PATH_WINDOWS)
            self._common_content_lib.execute_sut_cmd(
                BIT_INSTALL_COMMAND_WINDOWS, "silent installation", self._command_timeout,
                bit_extracted_path)

            bit_key = os.path.join(bit_extracted_path, BurnInConstants.BIT_KEY_WINDOWS)
            self._log.debug("copying the licence key ...")
            self._common_content_lib.execute_sut_cmd(
                'copy {} "{}"'.format(bit_key, BurnInConstants.BIT_INSTALLED_PATH_WINDOWS), "copy key fie, ",
                self._command_timeout)

        return BurnInConstants.BIT_INSTALLED_PATH_WINDOWS

    def copy_network_drivers_to_sut(self):
        """
        This method is to copy the Network driver fron Host to SUT.

        :return the path
        """
        zip_file_name = "intel_lan_v25_5.zip"
        host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(zip_file_name)
        sut_path = self._common_content_lib.copy_zip_file_to_sut("intel_driver", host_path)
        return sut_path

    def install_driver_on_windows(self, inf_file_list=None, device_id_list=None):
        """
        This method is to install driver on SUT or VM.

        :param inf_file_list
        :param device_id_list
        """
        sut_driver_folder_path = self.copy_network_drivers_to_sut()
        REGEX_TO_FIND_HWID = r".*VEN_[\S+].*\\"
        if not inf_file_list:
            raise content_exceptions.TestFail("Please pass argument in list for eg. ['icea68.inf']")
        self.copy_devcon_to_sut()
        inf_device_id_zip = zip(inf_file_list, device_id_list)
        for each_device in inf_device_id_zip:
            cmd = "powershell.exe Get-CimInstance -ClassName Win32_PNPEntity ^| Select-Object -Property DeviceID ^|" \
                  " findstr '{}'".format(each_device[1])
            hw_ids = self._common_content_lib.execute_sut_cmd(sut_cmd=cmd, cmd_str=cmd, execute_timeout=
            self._command_timeout).strip()
            hw_id_list = re.findall(REGEX_TO_FIND_HWID, hw_ids)
            if not hw_id_list:
                raise content_exceptions.TestFail("No Device HwId found with Device id - {}".format(each_device[1]))
            hw_id = hw_id_list[0]
            cmd_to_get_inf_full_path = "powershell.exe (get-childitem '{}' -File '*{}'-recurse).fullname".format(
                sut_driver_folder_path, each_device[0])
            inf_file = self._common_content_lib.execute_sut_cmd(cmd_to_get_inf_full_path, cmd_to_get_inf_full_path,
                                                     self._command_timeout).strip()
            driver_installation_cmd = '''devcon.exe update "%s" "%s''' % (inf_file, hw_id[:-1])
            try:
                installation_output = self._common_content_lib.execute_sut_cmd(driver_installation_cmd,
                                                                               driver_installation_cmd,
                                                                               self._command_timeout,
                                                                               self.WINDOWS_USER_ADMIN_PATH)
                self._log.info(installation_output)
            except:
                self._log.error("Driver installation Failed")

    def install_vc_redist(self):
        """
        To install vc_redist.exe in SUT.

        :return: None
        """
        host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(self.VC_REDIST_EXE_FILE_NAME)
        self._log.info("{} path in host is : {}".format(self.VC_REDIST_EXE_FILE_NAME, host_path))
        self._os.copy_local_file_to_sut(source_path=host_path, destination_path=self.C_DRIVE_PATH)
        install_command = "{} /install /quiet".format(self.VC_REDIST_EXE_FILE_NAME)
        self._common_content_lib.execute_sut_cmd(install_command, "Install {}".format(self.VC_REDIST_EXE_FILE_NAME),
                                                 self._command_timeout, self.C_DRIVE_PATH)

    def get_spr_path(self, common_content=None):
        """
        Get the spr directory path from SUT

        :return: spr_dir_path
        """
        spr_dir_path = None
        if common_content is None:
            common_content = self._common_content_lib
        spr_folder = "SPR_FOLDER"
        try:
            self._log.info("Downloading the SPR config to SUT")
            host_tool_path_spr = self._artifactory_obj.download_tool_to_automation_tool_folder(self.spr_file_path)
            # Copy the SPR file to SUT
            self._log.info("Copy the SPR config to Linux SUT")
            sut_folder_path = common_content.copy_zip_file_to_linux_sut(spr_folder, host_tool_path_spr)
            self._log.debug("spr file folder path {}".format(sut_folder_path))
            find_spr_cmd = "find $(pwd) -type f -name 'Setup_Randomize_DSA_Conf.sh'"
            spr_folder = self._spr_folder = \
                common_content.execute_sut_cmd(find_spr_cmd, "find the Setup_Randomize_DSA_Conf.sh file path",
                                                         self._command_timeout, sut_folder_path)
            self._log.info("SPR directory name {}".format(spr_folder))
            if not spr_folder:
                raise content_exceptions.TestFail("SPR directory not found")
            spr_dir_path = os.path.split(spr_folder)[:-1][0]
            self._log.info("SPR  config directory name {}".format(spr_dir_path))
        except Exception as ex:
            log_error = "error in executing te function get_spr_path"
            self._log.error(log_error)
            RuntimeError(ex)

        return spr_dir_path

    def configure_dsa_ca(self, spr_dir_path):
        """
        Configure DSA

        :return: None
        """
        # Define the output file
        log_file_launch = "/root/launch"
        try:
            self._log.info("Running SetupRandomise script")
            cmd_output = self._common_content_lib.execute_sut_cmd(
                sut_cmd='./Setup_Randomize_DSA_Conf.sh -ca > {}'.format(log_file_launch),
                cmd_str='./Setup_Randomize_DSA_Conf.sh -ca > {}'.format(log_file_launch),
                execute_timeout=self._command_timeout,
                cmd_path=spr_dir_path)
            self._log.info("The output of DSA setup {}".format(cmd_output))
            cmd = "./Guest_Mdev_Randomize_DSA_Conf.sh -k"
            cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=cmd, cmd_str=cmd,
                                                                  execute_timeout=self._command_timeout,
                                                                  cmd_path=spr_dir_path)
            self._log.info("Configuring workqueues {}".format(cmd_output))
        except Exception as ex:
            log_error = "error in configuring DSA"
            self._log.error(log_error)
            RuntimeError(ex)

    def configure_dsa(self, spr_dir_path):
        """
        Configure DSA

        :return: None
        """
        # Define the output file
        log_file_launch = "/root/launch"
        log_file_launch1 = "/root/launch1"

        try:
            self._log.info("Running SetupRandomise script")

            cmd_output = self._common_content_lib.execute_sut_cmd(
                sut_cmd='./Setup_Randomize_DSA_Conf.sh -d > {}'.format(log_file_launch1),
                cmd_str='./Setup_Randomize_DSA_Conf.sh -d > {}'.format(log_file_launch1),
                execute_timeout=self._command_timeout,
                cmd_path=spr_dir_path)
            cmd_output = self._common_content_lib.execute_sut_cmd(
                sut_cmd='./Setup_Randomize_DSA_Conf.sh -maM > {}'.format(log_file_launch),
                cmd_str='./Setup_Randomize_DSA_Conf.sh -maM > {}'.format(log_file_launch),
                execute_timeout=self._command_timeout,
                cmd_path=spr_dir_path)
            self._log.info("The output of DSA setup {}".format(cmd_output))
        except Exception as ex:
            log_error = "error in configuring DSA"
            self._log.error(log_error)
            RuntimeError(ex)

    def configure_dsa_devices(self, spr_dir_path):
        """
        Configure DSA

        :return: None
        """
        # Define the output file
        log_file_launch = "/root/launch"
        cmd = "./Guest_Mdev_Randomize_DSA_Conf.sh -c > {}".format(log_file_launch)
        cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=cmd, cmd_str=cmd,
                                                              execute_timeout=self._command_timeout,
                                                              cmd_path=spr_dir_path)
        self._log.info("Configuring workqueues {}".format(cmd_output))
        try:
            self._log.info("Running SetupRandomise script")
            cmd_output = self._common_content_lib.execute_sut_cmd(
                sut_cmd='./Setup_Randomize_DSA_Conf.sh -maM > {}'.format(log_file_launch),
                cmd_str='./Setup_Randomize_DSA_Conf.sh -maM > {}'.format(log_file_launch),
                execute_timeout=self._command_timeout,
                cmd_path=spr_dir_path)
            self._log.info("The output of DSA setup {}".format(cmd_output))
        except Exception as ex:
            log_error = "error in configuring DSA"
            self._log.error(log_error)
            RuntimeError(ex)

    def configure_iax(self, spr_dir_path):
        """
        Configure IAX

        :return: None
        """
        # Define the output file
        log_file_launch = "/root/launch_aix"
        log_file_launch1 = "/root/launch_aix1"
        cmd_output = self._common_content_lib.execute_sut_cmd(
            sut_cmd='./Setup_Randomize_IAX_Conf.sh -d > {}'.format(log_file_launch1),
            cmd_str='./Setup_Randomize_IAX_Conf.sh -d > {}'.format(log_file_launch1),
            execute_timeout=self._command_timeout,
            cmd_path=spr_dir_path)
        self._log.info("The output of IAX disable {}".format(cmd_output))
        try:
            self._log.info("Running SetupRandomise script")
            cmd_output = self._common_content_lib.execute_sut_cmd(
                sut_cmd='./Setup_Randomize_IAX_Conf.sh -maM > {}'.format(log_file_launch),
                cmd_str='./Setup_Randomize_IAX_Conf.sh -maM > {}'.format(log_file_launch),
                execute_timeout=self._command_timeout,
                cmd_path=spr_dir_path)
            self._log.info("The output of IAX setup {}".format(cmd_output))

        except Exception as ex:
            log_error = "error in configuring IAX"
            self._log.error(log_error)
            RuntimeError(ex)

    def get_mdev_id(self, index):
        """
        Get the mdev device ID

        :return: mdev device id
        """
        try:
            cmd_list_mdev = "ls /sys/bus/mdev/devices/"
            self._log.info("Get the mdev device id")
            vfio_device_list = self._common_content_lib.execute_sut_cmd(sut_cmd=cmd_list_mdev, cmd_str=cmd_list_mdev,
                                                                        execute_timeout=self._command_timeout,
                                                                        cmd_path=self.ROOT)
            vfio_list = vfio_device_list.split('\n')
            return vfio_list[index]
        except Exception as ex:
            log_error = "error in getting mdev id"
            self._log.error(log_error)
            RuntimeError(ex)

    def build_accel_config_tool_vm(self, accel_dir_path, common_content_lib_vm):
        """
        This  function build the accel config tool
        1../autogen.sh -v
        2. ./configure CFLAGS='-g -O2' --prefix=/usr --sysconfdir=/etc --libdir=/usr/lib64 " \
                     "--enable-test=yes --enable-debug=yes
        3. make all
        4. sudo make install
        :param accel_dir_path: accel config folder path
        :raise: raise content exceptions if not build accel config tool
         """
        cmd_autogen = "./autogen.sh -v"
        cmd_configure = "./configure CFLAGS='-g -O2' --prefix=/usr --sysconfdir=/etc --libdir=/usr/lib64 " \
                        "--enable-test=yes --enable-debug=yes"
        cmd_make_all = "make all"
        cmd_make_install = "sudo make install"
        autogen_regex = r"./configure CFLAGS='-g -O2' --prefix=/usr --sysconfdir=/etc --libdir=/usr/lib64"
        self._log.info("Build the accel config tool")
        try:
            # Build accel config autogen.sh command
            cmd_output = common_content_lib_vm.execute_sut_cmd(cmd_autogen, cmd_autogen, self._command_timeout,
                                                               accel_dir_path)
            self._log.info("accel config autogen command output {}".format(cmd_output))
            autogen_output = re.search(autogen_regex, cmd_output)
            if not autogen_output:
                raise content_exceptions.TestFail("Accel config build got failed")
            # Configure accel config tool
            cmd_output = common_content_lib_vm.execute_sut_cmd(cmd_configure, cmd_configure, self._command_timeout,
                                                               accel_dir_path)
            self._log.info("accel config configure output {}".format(cmd_output))
            # make all command for accel config
            cmd_output = common_content_lib_vm.execute_sut_cmd(cmd_make_all, cmd_make_all, self._command_timeout,
                                                               accel_dir_path)
            self._log.info("accel config tool make all output {}".format(cmd_output))
            # sudo make install command for accel config tool
            cmd_output = common_content_lib_vm.execute_sut_cmd(cmd_make_install, cmd_make_install, self._command_timeout,
                                                           accel_dir_path)

            self._log.info("accel config tool sudo make install output {}".format(cmd_output))
        except Exception as ex:
            log_error = "error in building accel"
            self._log.error(log_error)
            RuntimeError(ex)

    def run_dma_test(self,common_content_lib=None ,os_obj=None):
        """
        This method is to run DMA Test

        :param common_content_lib: Common content lib object of the VM or host
        :param os_obj : Object of a host or VM
        raise: raise content exceptions if the test fails
        """

        if os_obj is None:
            os_obj = self._os
        if common_content_lib is None:
            common_content_lib = self._common_content_lib
        os_obj.copy_local_file_to_sut(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                                   r"virtualization\tests\dma_test.sh"), self.ROOT)
        cmd = "chmod 777 dma_test.sh"
        common_content_lib.execute_sut_cmd(cmd,"Change execute permission",self._command_timeout,cmd_path=self.ROOT)
        common_content_lib.execute_sut_cmd("./dma_test.sh","Running DMA Test", self._command_timeout,cmd_path=self.ROOT)
        cmd_check_dma_error = "journalctl --dmesg  | grep result #1000: 'test passed'"
        dma_test_error = os_obj.execute(cmd_check_dma_error, self._command_timeout)
        if len(dma_test_error.stdout) == 0:
            raise RuntimeError("Errors found after running workload")
        else:
            self._log.info("No errors found")


    def install_pcierrpoll(self):
        """
        This method install PCIERRPoll tool on the sut.

        :return: Path where the tool is installed
        """
        if OperatingSystems.LINUX == self.sut_os:
            self._log.info("Installing PCIERRPoll tool")
            zip_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder(self.PCIERRPOLL_TAR_FILE)
            tool_path = self._common_content_lib.copy_zip_file_to_linux_sut(
                sut_folder_name=self.PCIERRPOLL_TAR_FILE.split('.')[0], host_zip_file_path=zip_file_path)
            command = "chmod +x {}".format(self.PCIERRPOLL_FILE)
            self._common_content_lib.execute_sut_cmd(command, command, self._command_timeout, cmd_path=tool_path)
            self._log.info("Successfully installed PCIERRPoll tool in SUT")
            return tool_path
        elif OperatingSystems.WINDOWS == self.sut_os:
            sut_folder_name = "PCIERR"
            artifactory_name = "PCIERRpoll_debug.exe"
            exe_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
            path_in_sut = Path(os.path.join(self.C_DRIVE_PATH, sut_folder_name)).as_posix().strip()
            self._os.execute("rmdir /Q /S {}".format(sut_folder_name), self._command_timeout, self.C_DRIVE_PATH)
            self._os.execute("mkdir {}".format(sut_folder_name), self._command_timeout, self.C_DRIVE_PATH)
            self._os.copy_local_file_to_sut(source_path=exe_file_path, destination_path=path_in_sut)
            self._log.info("SUT tool path in SUT is : {}".format(path_in_sut))
            self._log.info("Successfully installed PCIERRPoll tool in SUT")
            return path_in_sut
        else:
            log_error = "PCIERRPoll tool is not supported on OS '{}'".format(self._os.sut_os)
            self._log.error(log_error)
            raise NotImplementedError(log_error)

    def copy_maxkeymktme(self):
        """
        This Method is Used to copy maxkeymktme tool from artifactory to SUT

        :return: Tool path
        """
        host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
            self.MAXKEYASSIGNMENTMKTME["MKTMEKEYASSIGNMENTMAXZIPFILE"])
        return self._common_content_lib.copy_zip_file_to_linux_sut(
            self.MAXKEYASSIGNMENTMKTME["MKTMEKEYASSIGNMENTMAXZIPFILE"].split(".")[0],
            host_path)

    def copy_sgxhydra_first_tool(self):
        """
        This Method is Used to copy sgxhydra_first tool from artifactory to SUT

        :return: Tool path
        """
        host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
            self.SGXHYDRAEXFIRST["SGXHYDRAEXFIRSTZIPFILE"])
        return self._common_content_lib.copy_zip_file_to_linux_sut(
            self.SGXHYDRAEXFIRST["SGXHYDRAEXFIRSTZIPFILE"].split(".")[0],
            host_path)

    def copy_and_install_mem_tool(self):
        """
        This Method is Used to copy and install the mem rpm tool from artifactory to SUT
        """
        dmse_tool_path = self._artifactory_obj.download_tool_to_automation_tool_folder(self.DMSETOOL_PATH)
        sut_path = self.util_constants["LINUX_USR_ROOT_PATH"]
        self._os.copy_local_file_to_sut(dmse_tool_path, sut_path)
        self._log.debug("DMSE Tools File is Successfully Copied to SUT")
        dmse_tool_cmd_output = self._common_content_lib.execute_sut_cmd(self.DMSE_TOOLS_INSTALLATION_CMD,
                                                                        self.DMSE_TOOLS_INSTALLATION_CMD,
                                                                        self._command_timeout)
        self._log.debug("Dmse Tools is Successfully Installed on SUT {}".format(dmse_tool_cmd_output))

    def verify_iax_accel_config_list_devices(self):
        """
        This function verifies iax devices in accel config tool list of devices

        :param accel_dir_path: accel config folder path
        :raise: raise content exception if not found 8 iax devices
        """
        accel_cofnig_list = r"accel-config list -i"
        regex_iax = "iax(\d+)"
        iax_device_list = []
        iax_device_count = 8
        self._log.info("Verify accel config iax devices")
        # verify the accel-config components
        cmd_output = self._common_content_lib.execute_sut_cmd(accel_cofnig_list, accel_cofnig_list,
                                                              self._command_timeout)
        self._log.debug("accel-config components in json format {}".format(cmd_output))
        import ast
        iax_list_dict = [item for item in ast.literal_eval(cmd_output)]
        for item in range(len(iax_list_dict)):
            if re.search(regex_iax, iax_list_dict[item]["dev"]):
                iax_device_list.append(iax_list_dict[item]["dev"])
        self._log.debug("List of iax devices {}".format(iax_device_list))
        if len(iax_device_list) != iax_device_count:
            raise content_exceptions.TestFail("8 iax devices not found")
        self._log.info("Found all 8 iax devices")

    def run_iax_dma_test(self, common_content_lib=None, os_obj=None):
        """
        This method is to run IAX DMA Test

        :param common_content_lib: Common content lib object of the VM or host
        :param os_obj : Object of a host or VM
        raise: raise content exceptions if the test fails
        """
        if os_obj is None:
            os_obj = self._os
        if common_content_lib is None:
            common_content_lib = self._common_content_lib
        os_obj.copy_local_file_to_sut("iax_vm_dma_mdev.sh", self.ROOT)
        cmd = "chmod 777 iax_vm_dma_mdev.sh"
        common_content_lib.execute_sut_cmd(cmd, "Change execute permission", self._command_timeout, cmd_path=self.ROOT)
        common_content_lib.execute_sut_cmd("./iax_vm_dma_mdev.sh", "Running IAX DMA Test", self._command_timeout,
                                           cmd_path=self.ROOT)
        cmd_check_dma_error = "journalctl --dmesg  | grep result #100: 'test passed'"
        dma_test_error = os_obj.execute(cmd_check_dma_error, self._command_timeout)
        if len(dma_test_error.stdout) == 0:
            raise RuntimeError("Errors found after running workload")
        else:
            self._log.info("No errors found")

    def install_ctg_tool(self):
        """
        This method is to install the CTG tool on SUT.
        """
        ctg_tool_host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(tool_name=r"ctg_tool.zip")
        ctg_sut_path = Path(os.path.join(self._common_content_lib.copy_zip_file_to_linux_sut(
            "ctg_tool", ctg_tool_host_path), "ctg-master")).as_posix()

        ctg_lib_host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(tool_name=r"ctg_lib.zip")

        ctg_lib_sut_path = Path(os.path.join(
            self._common_content_lib.copy_zip_file_to_linux_sut("ctg_lib", ctg_lib_host_path), "lib")).as_posix()

        cores, ret = self._common_content_lib.get_core_count_from_os()
        cmd_to_change_core_thread = "sed 's/#define MAX_NUM_CPU_THREADS 128/#define MAX_NUM_CPU_THREADS {}/g' ctg.h > " \
                                    "ctg_dummy.h ; mv -f ctg_dummy.h ctg.h; " \
                                    "chmod +777 ctg.h".format(int(cores))
        self._log.info(cmd_to_change_core_thread)
        self._os.execute(cmd_to_change_core_thread, self._command_timeout, ctg_sut_path)

        self._os.execute("cp -r {} {}".format(ctg_lib_sut_path, ctg_sut_path), 200)

        self._os.execute("chmod 777 lib", 200, ctg_sut_path)
        self._os.execute("make clean", 200, ctg_sut_path)
        result = self._os.execute("make", 200, ctg_sut_path)
        self._log.info("make output- {}".format(result.stdout))
        return ctg_sut_path

    def get_nvme(self):
        """
        This function Get the NVME vib driver.

        :return: The vib file for installing NVME driver.
        """
        nvme_folder = "NVME"
        if self.nvme_file_path == "":
            raise content_exceptions.TestFail("Please add the 'nvme_file_name' tag details and rerun")
        else:
            host_tool_path_nvme = self._artifactory_obj.download_tool_to_automation_tool_folder(self.nvme_file_path)
            print(self.nvme_file_path)
            print(host_tool_path_nvme)
            sut_folder_path = self._common_content_lib.copy_zip_file_to_esxi(nvme_folder, host_tool_path_nvme)
            self._log.info("The path on ESXI to copy zip file is {}".format(sut_folder_path))
            find_nvme = "find $pwd -type f -name 'VMW-esx-*'"
            nvme_folder = self._nvme_folder = \
                self._common_content_lib.execute_sut_cmd(find_nvme, "find the find_nvme file path",
                                                         self._command_timeout, self.DEFAULT_DIRECTORY_ESXI)
            self._log.info("NVME DIRECTORY ZIP  name {}".format(nvme_folder))
            nvme_folder_path = nvme_folder.replace('./', '')
            nvme_dir_path_vib_zip = os.path.split(nvme_folder)[:-1][0]
            zip_dir_name = self.DEFAULT_DIRECTORY_ESXI + nvme_dir_path_vib_zip.replace('.', '')
            file_zip = self.DEFAULT_DIRECTORY_ESXI + "/" + nvme_folder_path
            cmd = "unzip {}"
            directory_name_vib = os.path.split(file_zip)[:-1][0]

            self._common_content_lib.execute_sut_cmd(cmd.format(file_zip), "unzip the vib file", self._command_timeout,
                                                     zip_dir_name)
            find_nvme_vib = "find iavmd-*.vib -type f -name 'iavmd-*.vib'"
            nvme_vib = self.nvme_vib = \
                self._common_content_lib.execute_sut_cmd(find_nvme_vib, "find the find_nvme vib file path",
                                                         self._command_timeout, zip_dir_name)
            self._log.info("NVME VIB  name {}".format(nvme_vib))
            return (nvme_vib, zip_dir_name)


    def vib_install_software(self, vib_file, path_full):
        """
        This function install the NVME vib driver.

        :return: status of the installation.
        """
        cp_cmd = "cp {} {}"
        tmp_dir = "/var/tmp/"
        self._os.execute("cp {} {}".format(path_full, tmp_dir), self._command_timeout)

        vib_file1 = tmp_dir + vib_file

        cmd2 = "esxcli software vib install -v {}"
        self._common_content_lib.execute_sut_cmd(cmd2.format(vib_file1), "software vib", self._command_timeout,
                                                 tmp_dir)

        cmd_reboot = "reboot"
        self._common_content_lib.execute_sut_cmd(cmd_reboot, "Reboot", self._command_timeout,
                                                 self.DEFAULT_DIRECTORY_ESXI)
        time.sleep(2500)
        cmd4 = "esxcfg-scsidevs -a"
        output = self._common_content_lib.execute_sut_cmd(cmd4, "list software vibdev", self._command_timeout,
                                                          self.DEFAULT_DIRECTORY_ESXI)

        driver_version_check = "esxcli software vib list | grep vmd"
        output = self._common_content_lib.execute_sut_cmd(driver_version_check, "Driver version check",
                                                          self._command_timeout,
                                                          self.DEFAULT_DIRECTORY_ESXI)

        if 'iavmd' in output:
            self._log.info("Software Vib listed successfully")
        else:
            raise RuntimeError("Software Vib  fail to list")

    def vib_remove_software(self):
        """
        This function remove the NVME vib driver.

        :return: status of the removal.
        """
        cmd_to_remove = "esxcli software vib remove -n iavmd"
        self._common_content_lib.execute_sut_cmd(cmd_to_remove, "Driver version check",
                                                 self._command_timeout,
                                                 self.DEFAULT_DIRECTORY_ESXI)
        cmd_reboot = "reboot"
        self._common_content_lib.execute_sut_cmd(cmd_reboot, "Reboot", self._command_timeout,
                                                 self.DEFAULT_DIRECTORY_ESXI)
        time.sleep(2500)
        cmd_check_after_removal = "esxcfg-scsidevs -a"
        output = self._common_content_lib.execute_sut_cmd(cmd_check_after_removal, "list software vibdev",
                                                          self._command_timeout,
                                                          self.DEFAULT_DIRECTORY_ESXI)
        if 'iavmd' not in output:
            self._log.info("Software Vib removed successfully")
        else:
            raise RuntimeError("Software Vib  fail to remove")

    def install_sgx_sdk_installer(self, sdk_full_name) -> None:
        """Download and install the SGX SDK installer from artifactory
        :param sdk_full_name: sgx sdk installer file name in the artifactory"""

        if OperatingSystems.WINDOWS != self.sut_os:
            self._log.error(f"{sdk_full_name}  not supported in {self._os.sut_os}")
            raise NotImplementedError(f"{sdk_full_name} not supported in {self._os.sut_os}")

        host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(sdk_full_name)
        self._log.info(f"{sdk_full_name} path in host is : {host_path}")
        self._os.copy_local_file_to_sut(source_path=host_path, destination_path=self.C_DRIVE_PATH)
        install_command = f"{sdk_full_name} --a install --output=sgx_install_output.txt --eula=accept"
        self._common_content_lib.execute_sut_cmd(install_command, f"Install {install_command}",
                                                 self._command_timeout, self.C_DRIVE_PATH)

    def install_tester_tool(self):
        """
        Download and Copy tester app to SUT.
        1. Copy the file to SUT and change the permission .
        :return: application path
        """
        tester_path = ''
        if OperatingSystems.LINUX == self.sut_os:
            tester_path = self.download_and_copy_zip_to_sut(
                self.TESTER_TOOL_ZIP["TESTER_TOOL_ZIP_FILE"].split(".")[0].strip(),
                self.TESTER_TOOL_ZIP["TESTER_TOOL_ZIP_FILE"])

            self._common_content_lib.execute_sut_cmd(sut_cmd="chmod u+x tester",
                                                    cmd_str="change tester app permission",
                                                    execute_timeout=5)

        else:
            self._log.error("TESTER Tool is not supported on OS '%s'" % self._os.sut_os)
            raise NotImplementedError("Tester Tool is not supported on OS '%s'" % self._os.sut_os)

        return tester_path

    def install_new_mlc_w(self):
        """
        This method is to copy the MLC internal tool into SUT
        """
        artifactory_name = ArtifactoryName.DictWindowsTools[ArtifactoryTools.MLC_EXE_NEW]
        host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
        mlc_path = self._common_content_lib.copy_zip_file_to_sut(
            self.mlc_constants["MLC_FOLDER_NAME"], host_path)
        mlc_windows_path = os.path.join(mlc_path, "Windows")
        return mlc_windows_path

    def copy_hydra_dll_files(self, hydra_path: str) -> None:
        """
        Copies the Hydra Dll file to Windows system32 folder from Hydra folder in the sut.

        :param hydra_path: Hydra folder path in the sut
        :raise: content_exception.TestFail if the Hydra dll files are not present in hydra folder in sut.
        :return: None
        """
        self._log.info("Copying Hydra dll files from HydraFolder to Windows system32 location if required.")
        for dllfile in self.SGXHYDRAEXFIRST.get("Hydradllfiles"):
            if not self._common_content_lib.search_windows_file(self.WINDOWS_SYSTEM32, dllfile):
                self._log.debug("Copying Hydra dll files {} to system32 path".format(dllfile))
                source_path = self._common_content_lib.search_windows_file(hydra_path, dllfile)
                self._log.info("Source path {}".format(source_path))
                if source_path:
                    self._common_content_lib.copy_windows_file_in_sut(source_path, self.WINDOWS_SYSTEM32)
                    self._log.debug("Copying of Hydra dll file {} to windows system32 is successfully".format(dllfile))
                else:
                    raise content_exceptions.TestFail("Hydra dll files is not present in the Hydra folder in sut")
            else:
                self._log.debug("Hydra dll files {} is already present in the system32 location, copying not required"
                                .format(dllfile))
        self._log.info("All Hydra dll files are present in windows system32 location")
