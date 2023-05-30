#!/usr/bin/env python
##########################################################################
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
##########################################################################
import re
import os

from dtaf_core.lib.dtaf_constants import ProductFamilies
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.lib import content_exceptions
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral


class QatBaseTest(ContentBaseTestCase):
    """
    Base class extension for MktmeBaseTest which holds common functions.
    """
    QAT_SERVICE_STATUS = "service qat_service status"
    QAT_LSPCI = "lspci -vnd 8086:4940"
    LIST_QAT_KERNEL_MODULES = ['usdm_drv', 'intel_qat']
    SPR_QAT_KERNEL_MODULE = "qat_4xxx"
    UNINSTALL_QAT_KERNEL_MODULE = ['usdm_drv']
    QAT_KERNEL_MODULES = r"lsmod | grep 'qat\|usdm'"
    ZERO_QAT = 0
    REGEX_CMD = r"There is (\d+) QAT acceleration device"
    MAKE_UNINSTALL = "make uninstall"
    QAT_UNINSTALL_STR = "Acceleration Uninstall Complete"
    FIND_QAT_FOLDER_PATH = "find $(pwd) -type d -name 'QAT'"
    FIND_QAT_DEVICE_COUNT = "lspci -n | grep -i '8086:4940' | wc -l"
    REGEX_FOR_CODE_COMPLETED_SUCCESSFULLY = r"Sample\scode\scompleted\ssuccessfully"
    REGEX_FOR_ERROR = r"Error"
    REGEX_FOR_ERR = r"ERR"
    REGEX_FOR_ERROR_CMD = r"error"

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file_path=None):
        """
        Create an instance of sut QatBaseTest.

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(QatBaseTest, self).__init__(test_log, arguments, cfg_opts, bios_config_file_path)
        self._cfg = cfg_opts
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._platform = self._common_content_lib.get_platform_family()
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)

    def prepare(self):
        # type: () -> None
        """
        pre-checks if the sut is booted to RHEL Linux OS.
        """
        super(QatBaseTest, self).prepare()
        # Setting date and time
        self._common_content_lib.set_datetime_on_linux_sut()

    def qat_device_status(self):
        """
        This function execute QAT service status command to get the QAT Device lists

        :return: True if it will get atleast 1 QAT device else fail
        :raise: content_exception.TestError if not getting the expected regular expression
        """
        self._log.info("Checking the QAT Device Status...")
        ret_qat_status = self.os.execute(self.QAT_SERVICE_STATUS, self._command_timeout)

        self._log.debug("QAT Tool supported device lists {}".format(ret_qat_status.stdout))
        if not ret_qat_status.stdout.strip():
            return False
        regex_search = re.search(self.REGEX_CMD, ret_qat_status.stdout, re.M)
        if not regex_search:
            raise content_exceptions.TestError("Could not get the info of QAT devices")
        qat_devices = int(regex_search.group(1))
        self._log.info("Number of QAT Acceleration devices are %d", qat_devices)
        if qat_devices == self.ZERO_QAT:
            return False

        return True

    def qat_device_presence(self):
        """
        This function execute QAT service presence command to get the QAT Device lists

        :raise: content_exception.TestFail if not getting the expected true output
        """
        dev_size_512k = r"Memory at \w{12} " + re.escape("(64-bit, non-prefetchable) [size=512K]")
        dev_size_8m = r"Memory at \w{12} " + re.escape("(64-bit, non-prefetchable) [size=8M]")
        dev_size_2m = r"Memory at \w{12} " + re.escape("(64-bit, non-prefetchable) [size=2M]")

        self._log.info("Checking the QAT Device Presence")
        ret_qat_presence = self._common_content_lib.execute_sut_cmd(self.QAT_LSPCI, "get QAT device presence",
                                                                    self._command_timeout)
        self._log.debug("Checking the total QAT Device Count {}".format(ret_qat_presence))
        total_device_cmd = self._common_content_lib.execute_sut_cmd(self.FIND_QAT_DEVICE_COUNT,
                                                                    "get count of total QAT device presence",
                                                                    self._command_timeout)
        self._log.debug("Total device count {}".format(total_device_cmd))
        total_device_count = int(total_device_cmd)
        dev_size_512k_count = len(re.findall(dev_size_512k, ret_qat_presence))
        dev_size_8m_count = len(re.findall(dev_size_8m, ret_qat_presence))
        dev_size_2m_count = len(re.findall(dev_size_2m, ret_qat_presence))
        self._log.debug("dev_size_512K_count {}, dev_size_8M_count {}, dev_size_2M_count {}".format(
            dev_size_512k_count, dev_size_8m_count, dev_size_2m_count))

        if not (dev_size_512k_count == total_device_count and dev_size_8m_count == total_device_count and
                dev_size_2m_count == total_device_count):
            raise content_exceptions.TestFail("Total number of device size count could not match total QAT devices "
                                              "count {}".format(total_device_count))
        self._log.info("QAT device list service is available")

    def check_lsmod_for_qat_installation(self):
        """
        This function execute lsmod grep command to get the QAT Kernel Modules from the sut

        :raise: content_exception.TestFail if not getting the expected qat kernel modules
        """
        no_kernel_modules = []
        self._log.info("Checking the QAT kernal modules in the sut...")
        grep_cmd_results = self._common_content_lib.execute_sut_cmd(self.QAT_KERNEL_MODULES,
                                                                    "qat kernel modules", self._command_timeout)
        self._log.debug("QAT Tool kernel modules device lists: {}".format(grep_cmd_results))

        if self._platform == ProductFamilies.SPR:
            self.LIST_QAT_KERNEL_MODULES.append(self.SPR_QAT_KERNEL_MODULE)
        for module in self.LIST_QAT_KERNEL_MODULES:
            if module not in grep_cmd_results:
                no_kernel_modules.append(module)
        if no_kernel_modules:
            raise content_exceptions.TestFail("%s modules did not find", no_kernel_modules)

    def check_lsmod_for_qat_uninstallation(self):
        """
        This function execute lsmod grep command after uninstalled the qat tool and get the QAT Kernel Modules

        :raise: content_exception.TestFail if getting the usdm_drv kernel modules
        """
        no_kernel_modules = []
        self._log.info("Checking the QAT kernel modules in the sut after uninstall qat tool...")
        grep_cmd_results = self.os.execute(self.QAT_KERNEL_MODULES, self._command_timeout)
        if grep_cmd_results.stdout:
            self._log.debug("QAT Tool kernel modules device lists: {}".format(grep_cmd_results.stdout))
            if self._platform == ProductFamilies.SPR:
                self.UNINSTALL_QAT_KERNEL_MODULE.append(self.SPR_QAT_KERNEL_MODULE)
            for module in self.UNINSTALL_QAT_KERNEL_MODULE:
                if module in grep_cmd_results.stdout:
                    no_kernel_modules.append(module)
            if no_kernel_modules:
                raise content_exceptions.TestFail("%s modules got found", no_kernel_modules)
        if grep_cmd_results.stderr:
            raise content_exceptions.TestFail("Failed to execut the command {} with error {}".format(
                self.QAT_KERNEL_MODULES, grep_cmd_results.stderr))
        else:
            self._log.debug("After uninstall the QAT not found any kernel modules")

    def install_qat_tool(self, configure_spr_cmd=None):
        """
        This function installing the qat tool in sut
        """
        self._install_collateral.install_qat(configure_spr_cmd)

    def get_qat_dir(self):
        """
        This function get the QAT tool installed directory path

        :return: The QAT directory path
        """
        self._log.info("Finding the QAT tool installed directory...")
        qat_dir = self._common_content_lib.execute_sut_cmd(self.FIND_QAT_FOLDER_PATH, "find QAT path",
                                                           self._command_timeout).strip()
        self._log.debug("QAT Tool directory path '{}'".format(qat_dir))
        return qat_dir

    def uninstall_qat(self, qat_dir_path):
        """
        This function uninstall the QAT from the sut

        :raise: content_exception.TestFail if not uninstalled properly
        """
        self._log.info("Uninstalling the QAT Tool..")
        ret_qat_status = self._common_content_lib.execute_sut_cmd(self.MAKE_UNINSTALL, "make uninstall cmd",
                                                                  self._command_timeout, qat_dir_path)
        self._log.debug("QAT Tool Uninstalled command results {}".format(ret_qat_status))
        if self.QAT_UNINSTALL_STR not in ret_qat_status:
            raise content_exceptions.TestFail("Failed to uninstall QAT tool")
        self._log.info("QAT is uninstalled")

    def spr_cpa_sample_code_workaround(self):
        """
        This function execute command in cscript command for SPR platform as workaround
        """
        self._cscripts = ProviderFactory.create(self.sil_cfg, self._log)  # type: SiliconRegProvider
        self._sv = self._cscripts.get_cscripts_utils().getSVComponent()
        self._sv.refresh()
        self._log.info("Executing the workaround command for SPR Platform")
        available_socket = self._cscripts.get_socket_count()
        self._log.info("Available socket in the sut {}".format(available_socket))
        for socket in range(0, available_socket):
            self._cscripts.get_sockets()[socket].uncore.m2iosf8.vtuncerrmsk_cfg.pmr_check_abort = 1
            self._cscripts.get_sockets()[socket].uncore.m2iosf8.vtuncerrmsk_cfg.gpa_overflow = 1
            self._cscripts.get_sockets()[socket].uncore.m2iosf8.vtuncerrmsk_cfg.iommu_mem_resp_abort = 1
            self._cscripts.get_sockets()[socket].uncore.m2iosf8.vtuncerrmsk_cfg.illegal_msi = 1
            cmd_results = self._cscripts.get_sockets()[socket].uncore.m2iosf8.vtuncerrmsk_cfg.show()
            self._log.debug("SPR Platform availabel socket id {} with {}".format(socket, cmd_results))

    def execute_cpa_sample_code(self, cpa_sample_command):
        """
        This function execute the cpa_sample_code file to get the data movement in the sut

        :raise: raise content_exceptions.TestFail if not getting the file or getting error
        """
        find_cpa_sample_code_file = "find $(pwd) -type f -name 'cpa_sample_code' | grep QAT/build"
        self._log.info("Execute the command {}".format(cpa_sample_command))
        # While executing SPR Platform run the workaround
        if self._platform == ProductFamilies.SPR:
            self.spr_cpa_sample_code_workaround()
        # find cpa_sample_code file from the build folder
        cpa_sample_file_path = self._common_content_lib.execute_sut_cmd(find_cpa_sample_code_file,
                                                                        "find the cpa_sample_code file in build path",
                                                                        self._command_timeout)
        self._log.info("Found cpa_sample_code file from build folder {} ".format(cpa_sample_file_path))
        if not cpa_sample_file_path:
            raise content_exceptions.TestFail("cpa_sample code file not found from build folder")
        build_path = os.path.split(cpa_sample_file_path)[:-1][0]
        self._log.info("Found cpa_sample_code file from build path {} ".format(build_path))
        sample_code_results = self._common_content_lib.execute_sut_cmd(cpa_sample_command,
                                                                       "Execute cpa_sample_code file",
                                                                       self._command_timeout,
                                                                       build_path)
        self._log.debug("Cpa Sample code file execution output {}".format(sample_code_results))
        if not re.findall(self.REGEX_FOR_ERR, "".join(sample_code_results)) or re.findall(self.REGEX_FOR_ERROR, "".join(
                sample_code_results)) or re.findall(self.REGEX_FOR_ERROR_CMD, "".join(sample_code_results)):
            if re.findall(self.REGEX_FOR_CODE_COMPLETED_SUCCESSFULLY, "".join(sample_code_results)):
                self._log.info("Cpa Sample code run completed successfully without any error")
        else:
            raise content_exceptions.TestFail("cpa_sample_code execution is failed with error")

