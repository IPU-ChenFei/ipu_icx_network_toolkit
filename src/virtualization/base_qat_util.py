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
import time

from dtaf_core.lib.dtaf_constants import ProductFamilies
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider

from src.lib import content_exceptions
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral
from src.virtualization.virtualization_common import VirtualizationCommon

class BaseQATUtil(VirtualizationCommon):
    """
    Base class extension for MktmeBaseTest which holds common functions.
    """
    QAT_DEVICE_NUM = 4
    DLB_DEVICE_NUM = 4
    DSA_DEVICE_NUM = 4
    IAX_DEVICE_NUM = 4
    DEVICE_ID = {
        'EGS': {
            'QAT_DEVICE_ID': '4940',
            'DLB_DEVICE_ID': '2710',
            'DSA_DEVICE_ID': '0b25',
            'IAX_DEVICE_ID': '0cfe',
            'QAT_VF_DEVICE_ID': '4941',
            'DLB_VF_DEVICE_ID': '2711',
            'DSA_MDEV_DEVICE_ID': '',
            'IAX_MDEV_DEVICE_ID': '',
            'QAT_MDEV_DEVICE_ID': '0da5',
            'DLB_MDEV_DEVICE_ID': '',
        },
        'BHS': {
            'QAT_DEVICE_ID': '4944',
            'DLB_DEVICE_ID': '2714',
            'DSA_DEVICE_ID': '0b25',
            'IAX_DEVICE_ID': '0cfe',
            'QAT_VF_DEVICE_ID': '4945',
            'DLB_VF_DEVICE_ID': '2715',
            'DSA_MDEV_DEVICE_ID': '',
            'IAX_MDEV_DEVICE_ID': '',
            'QAT_MDEV_DEVICE_ID': '0da5',
            'DLB_MDEV_DEVICE_ID': '',
        }
    }
    QAT_SERVICE_START = "qat_service start"
    QAT_SERVICE_STOP = "qat_service stop"
    QAT_SERVICE_RESTART = "qat_service restart"
    EXP_QAT_SERVICE_RESTART = "Restarting all devices"
    QAT_SERVICE_STATUS = "qat_service status"
    QAT_LSPCI = "lspci -vnd 8086:4940"
    QAT_LSPCI_VM = "lspci | grep 4941"
    QAT_VF_LSPCI = "lspci -vnd 8086:4941"

    LIST_QAT_KERNEL_MODULES = ['usdm_drv', 'intel_qat']
    SPR_QAT_KERNEL_MODULE = "qat_4xxx"
    UNINSTALL_QAT_KERNEL_MODULE = ['usdm_drv']
    QAT_KERNEL_MODULES = r"lsmod | grep 'qat\|usdm'"
    ZERO_QAT = 0
    REGEX_CMD = r"There is (\d+) QAT acceleration device"
    MAKE_UNINSTALL = "make uninstall"
    QAT_UNINSTALL_STR = "Acceleration Uninstall Complete"
    FIND_QAT_FOLDER_PATH = "find $(pwd) -type d -name 'QAT' 2>/dev/null"
    FIND_QAT_DEVICE_COUNT = "lspci -n | grep -i '8086:4940' | wc -l"
    FIND_QAT_DEVICE_COUNT_VM = "lspci | grep 4941 | wc -l"
    FIND_QAT_VF_DEVICE_COUNT = "lspci -n | grep -i '8086:4941' | wc -l"
    REGEX_FOR_CODE_COMPLETED_SUCCESSFULLY = r"Sample\scode\scompleted\ssuccessfully"
    REGEX_FOR_ERROR = r"Error"
    REGEX_FOR_ERR = r"ERR"
    REGEX_FOR_ERROR_CMD = r"error"

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file_path=None):
        """
        Create an instance of sut BaseQATUtil.

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(BaseQATUtil, self).__init__(test_log, arguments, cfg_opts, bios_config_file_path)
        self._cfg = cfg_opts
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._platform = self._common_content_lib.get_platform_family()

    def prepare(self):
        # type: () -> None
        """
        pre-checks if the sut is booted to RHEL Linux OS.
        """
        super(BaseQATUtil, self).prepare()
        # Setting date and time
        self._common_content_lib.set_datetime_on_linux_sut()
        self._install_collateral.install_kernel_rpm_on_linux()

    def get_qat_binary_path_linux(self, binary_name, common_content_object=None):
        """
        This functionis to get the explicit Path of given utility
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        find_binary_file_path = "find / -regex '.*\/build\/{}' -type f -name {} 2>/dev/null | grep *QAT*".format(
            binary_name,
            binary_name)
        binary_name_path = common_content_object.execute_sut_cmd_no_exception(find_binary_file_path,
                                                                           "run find command:{}".format(
                                                                               find_binary_file_path),
                                                                           self._command_timeout,
                                                                           "/root",
                                                                           ignore_result="ignore")
        binary_name_path = binary_name_path.strip()
        common_content_object.execute_sut_cmd_no_exception("chmod 777 {}".format(binary_name_path),
                                                           "enabling permission {}".format(
                                                               binary_name_path),
                                                           self._command_timeout,
                                                           "/root",
                                                           ignore_result="ignore")
        find_binary_file_path = "find / -regex '.*\/build\/{}' -perm /a=x -type f -name {} 2>/dev/null | grep *QAT*".format(
            binary_name,
            binary_name)
        binary_name_path = common_content_object.execute_sut_cmd_no_exception(find_binary_file_path,
                                                                           "run find command:{}".format(
                                                                               find_binary_file_path),
                                                                           self._command_timeout,
                                                                           "/root",
                                                                           ignore_result="ignore")
        binary_name_path = binary_name_path.strip()
        binary_path = "{}".format(os.path.dirname(binary_name_path))
        return binary_path

    def qat_device_status(self, common_content_object=None):
        """
        This function execute QAT service status command to get the QAT Device lists

        :return: True if it will get atleast 1 QAT device else fail
        :raise: content_exception.TestError if not getting the expected regular expression
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        self._log.info("Checking the QAT Device Status...")
        qat_service_path = self.get_qat_binary_path_linux("qat_service")
        ret_qat_status = common_content_object.execute_sut_cmd_no_exception("/{}/{}".format(
                                                                            qat_service_path,
                                                                            self.QAT_SERVICE_STATUS),
                                                                            "get QAT service status",
                                                                            self._command_timeout,
                                                                            cmd_path="{}".format(qat_service_path),
                                                                            ignore_result="ignore"
                                                                            )

        self._log.debug("QAT Tool supported device lists {}".format(ret_qat_status))
        if not ret_qat_status.strip():
            return False
        regex_search = re.search(self.REGEX_CMD, ret_qat_status, re.M)
        if not regex_search:
            raise content_exceptions.TestError("Could not get the info of QAT devices")
        qat_devices = int(regex_search.group(1))
        self._log.info("Number of QAT Acceleration devices are %d", qat_devices)
        if qat_devices == self.ZERO_QAT:
            return False

        return True

    def qat_vf_file_presence(self, common_content_object=None):
        """
        This function execute QAT service presence command to get the QAT Device lists

        :raise: content_exception.TestFail if not getting the expected true output
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib

        ret_qat_vf_file_status = common_content_object.execute_sut_cmd_no_exception("ls -la /etc/4xxxvf_dev*",
                                                                                    "get QAT VF files",
                                                                                    self._command_timeout,
                                                                                    cmd_path=self.ROOT_PATH,
                                                                                    ignore_result="ignore"
                                                                                )

        self._log.debug("QAT VF files list {}".format(ret_qat_vf_file_status))
        if not ret_qat_vf_file_status:
            return False
        regex_search = re.findall(".*/etc/4xxxvf_dev\d+.*", ret_qat_vf_file_status, re.M|re.I)
        if len(regex_search) <= 0:
            raise content_exceptions.TestError("Could not get the QAT VF files")

    def qat_vf_device_presence(self, common_content_object=None):
        """
        This function execute QAT service presence command to get the QAT Device lists

        :raise: content_exception.TestFail if not getting the expected true output
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib

        dev_size_32k = r"Memory at \w{12} " + re.escape("(64-bit, non-prefetchable) [virtual] [size=32K]")
        dev_size_8k = r"Memory at \w{12} " + re.escape("(64-bit, non-prefetchable) [virtual] [size=8K]")

        self._log.info("Checking the QAT Device Presence")
        ret_qat_presence = common_content_object.execute_sut_cmd(self.QAT_VF_LSPCI, "get QAT device presence",
                                                                    self._command_timeout)
        self._log.debug("Checking the total QAT Device Count {}".format(ret_qat_presence))
        total_device_cmd = common_content_object.execute_sut_cmd(self.FIND_QAT_VF_DEVICE_COUNT,
                                                                    "get count of total QAT device presence",
                                                                    self._command_timeout)
        self._log.debug("Total device count {}".format(total_device_cmd))
        total_device_count = int(total_device_cmd)

        dev_size_32k_count = int(len(re.findall(dev_size_32k, ret_qat_presence))/2)
        dev_size_8k_count = len(re.findall(dev_size_8k, ret_qat_presence))

        self._log.debug("dev_size_32k_count{}, dev_size_8k_count {}".format(dev_size_32k_count, dev_size_8k_count))

        if not (dev_size_32k_count == total_device_count and dev_size_8k_count == total_device_count ):
            raise content_exceptions.TestFail("Total number of device size count could not match total QAT VF devices "
                                              "count {}".format(total_device_count))
        self._log.info("QAT VF device list service is available")

    def qat_passthrough_device_presencein_vm(self, common_content_object=None):
        """
        This function execute QAT service presence command to get the QAT Device lists

        :raise: content_exception.TestFail if not getting the expected true output
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib

        self._log.info("Checking the QAT Device Presence")
        ret_qat_presence = common_content_object.execute_sut_cmd(self.QAT_LSPCI, "get QAT device presence",
                                                                    self._command_timeout)
        self._log.debug("Checking the total QAT Device Count {}".format(ret_qat_presence))
        if not "8086:4940" in ret_qat_presence:
            raise content_exceptions.TestFail("Checking the QAT Passthrough Device failed {}".format(ret_qat_presence))
        ret_qat_passthrough_presence = common_content_object.execute_sut_cmd(self.FIND_QAT_DEVICE_COUNT,
                                                                             "get QAT device presence",
                                                                             self._command_timeout)
        self._log.debug("Checking the total QAT Device Count {}".format(ret_qat_passthrough_presence))
        ret_qat_passthrough_presence = int(ret_qat_passthrough_presence)

        if ret_qat_passthrough_presence == 0:
            raise content_exceptions.TestFail("Total number of PT QAT devices count {}".format(ret_qat_passthrough_presence))
        self._log.info("QAT device count = {}".format(ret_qat_passthrough_presence))

    def qat_device_presencein_vm(self, common_content_object=None):
        """
        This function execute QAT service presence command to get the QAT Device lists

        :raise: content_exception.TestFail if not getting the expected true output
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib

        self._log.info("Checking the QAT Device Presence")
        ret_qat_passthrough_presence = common_content_object.execute_sut_cmd(self.FIND_QAT_DEVICE_COUNT, "get QAT device presence",
                                                                    self._command_timeout)
        self._log.debug("Checking the total QAT Device Count {}".format(ret_qat_passthrough_presence))
        ret_qat_passthrough_presence = int(ret_qat_passthrough_presence)
        total_device_cmd = common_content_object.execute_sut_cmd(self.FIND_QAT_DEVICE_COUNT_VM,
                                                                    "get count of total QAT device presence",
                                                                    self._command_timeout)
        self._log.debug("Total device count {}".format(total_device_cmd))
        total_device_count = int(total_device_cmd)

        if total_device_count == 0 and ret_qat_passthrough_presence == 0:
            raise content_exceptions.TestFail("Total number of QAT devices count {}".format(total_device_count))
        self._log.info("QAT device count {} are available in VM".format(total_device_count))

    def qat_device_presence(self, common_content_object=None):
        """
        This function execute QAT service presence command to get the QAT Device lists

        :raise: content_exception.TestFail if not getting the expected true output
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        dev_size_512k = r"Memory at \w{12} " + re.escape("(64-bit, non-prefetchable) [size=512K]")
        dev_size_8m = r"Memory at \w{12} " + re.escape("(64-bit, non-prefetchable) [size=8M]")
        dev_size_2m = r"Memory at \w{12} " + re.escape("(64-bit, non-prefetchable) [size=2M]")

        self._log.info("Checking the QAT Device Presence")
        ret_qat_presence = common_content_object.execute_sut_cmd(self.QAT_LSPCI, "get QAT device presence",
                                                                    self._command_timeout)
        self._log.debug("Checking the total QAT Device Count {}".format(ret_qat_presence))
        total_device_cmd = common_content_object.execute_sut_cmd(self.FIND_QAT_DEVICE_COUNT,
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

    def get_all_qat_device_bdf_value(self, common_content_object=None):
        """
          Purpose: To install QAT driver
          Args:
              No
          Returns:
              qat bdf value
          Example:
              Simplest usage: get QAT bdf value
                  get_qat_device_bdf_value
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        bdf_sym_asym_dc = {}
        bdf_sym_asym_dc['bdf'] = []
        cmand_qat_list = "lspci -D | grep 4940"
        qat_device_list_data = common_content_object.execute_sut_cmd(cmand_qat_list, "check qat in sut", 60)
        self._log.info(qat_device_list_data)
        # qat_bdf_value = (re.sub('\s\s+', '*', qat_device_list_data)).split('*')[index].split(" ")[0]
        if qat_device_list_data is not None:
            bdf_sym_asym_dc['bdf'] = re.findall(r'\b([0-9a-fA-F]{4}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}.\d{1}\s*)',
                                         qat_device_list_data)

            self._log.info(bdf_sym_asym_dc['bdf'])
        return bdf_sym_asym_dc

    def get_all_sriov_vf_qat_device_bdf_value(self, common_content_object=None):
        """
          Purpose: To install QAT driver
          Args:
              No
          Returns:
              qat bdf value
          Example:
              Simplest usage: get QAT bdf value
                  get_qat_device_bdf_value
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        bdf_sym_asym_dc = {}
        bdf_sym_asym_dc['bdf'] = []
        cmand_qat_list = "lspci -D | grep 4941"
        qat_device_list_data = common_content_object.execute_sut_cmd(cmand_qat_list, "check qat in sut", 60)
        self._log.info(qat_device_list_data)
        # qat_bdf_value = (re.sub('\s\s+', '*', qat_device_list_data)).split('*')[index].split(" ")[0]
        if qat_device_list_data is not None:
            bdf_sym_asym_dc['bdf'] = re.findall(r'\b([0-9a-fA-F]{4}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}.\d{1}\s*)',
                                         qat_device_list_data)

            self._log.info(bdf_sym_asym_dc['bdf'])
        return bdf_sym_asym_dc

    def check_lsmod_for_qat_installation(self, common_content_object=None):
        """
        This function execute lsmod grep command to get the QAT Kernel Modules from the sut

        :raise: content_exception.TestFail if not getting the expected qat kernel modules
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        no_kernel_modules = []
        self._log.info("Checking the QAT kernal modules in the sut...")
        grep_cmd_results = common_content_object.execute_sut_cmd(self.QAT_KERNEL_MODULES,
                                                                    "qat kernel modules", self._command_timeout)
        self._log.debug("QAT Tool kernel modules device lists: {}".format(grep_cmd_results))

        if self._platform == ProductFamilies.SPR:
            self.LIST_QAT_KERNEL_MODULES.append(self.SPR_QAT_KERNEL_MODULE)
        for module in self.LIST_QAT_KERNEL_MODULES:
            if module not in grep_cmd_results:
                no_kernel_modules.append(module)
        if no_kernel_modules:
            raise content_exceptions.TestFail("%s modules did not find", no_kernel_modules)

    def check_lsmod_for_qat_uninstallation(self, common_content_object=None):
        """
        This function execute lsmod grep command after uninstalled the qat tool and get the QAT Kernel Modules

        :raise: content_exception.TestFail if getting the usdm_drv kernel modules
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        no_kernel_modules = []
        self._log.info("Checking the QAT kernel modules in the sut after uninstall qat tool...")
        grep_cmd_results = common_content_object.execute_sut_cmd_no_exception(self.QAT_KERNEL_MODULES,
                                                                              "lsmod QAT Kernel modules",
                                                                              self._command_timeout,
                                                                              cmd_path="/root",
                                                                              ignore_result="ignore"
                                                                              )
        if grep_cmd_results:
            self._log.debug("QAT Tool kernel modules device lists: {}".format(grep_cmd_results))
            if self._platform == ProductFamilies.SPR:
                self.UNINSTALL_QAT_KERNEL_MODULE.append(self.SPR_QAT_KERNEL_MODULE)
            for module in self.UNINSTALL_QAT_KERNEL_MODULE:
                if module in grep_cmd_results:
                    no_kernel_modules.append(module)
            if no_kernel_modules:
                raise content_exceptions.TestFail("%s modules got found", no_kernel_modules)
        if grep_cmd_results:
            raise content_exceptions.TestFail("Failed to execut the command {} with error {}".format(
                self.QAT_KERNEL_MODULES, grep_cmd_results))
        else:
            self._log.debug("After uninstall the QAT not found any kernel modules")

    def install_check_qat_status(self, vm_name=None, os_obj=None, qat_type="siov", target_type="host",
                                 common_content_object=None, is_vm=None):
        """
        This function check QAT device status on SUT

        :return: True if get the QAT device status test case pass else fail
        """
        if is_vm != None:
            self._install_collateral.install_kernel_rpm_on_linux(os_obj=os_obj, common_content_lib=common_content_object, is_vm="yes")
        if common_content_object is None:
            common_content_object = self._common_content_lib
        if qat_type == "sriov":
            if target_type == "guest":
                self.install_qat_sriov_driver_tool_guest(configure_spr_cmd=None, common_content_object=common_content_object)
            else:
                self.install_qat_sriov_driver_tool_host(configure_spr_cmd=None, common_content_object=common_content_object)
        else:
            if target_type == "guest":
                self.install_qat_siov_driver_tool_guest(configure_spr_cmd=None, common_content_object=common_content_object)
            else:
                self.install_qat_siov_driver_tool(configure_spr_cmd=None, common_content_object=common_content_object)

        if target_type != "guest" or (vm_name is not None and "rhel" not in vm_name.lower()):
            try:
                # if target_type == "guest":
                #     self.reboot_linux_vm(vm_name)
                time.sleep(15)
                if not self.qat_device_status():
                    raise content_exceptions.TestFail("QAT does not support")
            except content_exceptions.TestError as ex:
                self._log.info("QAT status check failed, restarting the QAT Service...")
                qat_service_path = self.get_qat_binary_path_linux("qat_service")
                qat_service_restart_results = common_content_object.execute_sut_cmd("/{}/{}".format(
                                                                                qat_service_path,
                                                                                self.QAT_SERVICE_RESTART),
                                                                                "restart qat service",
                                                                                self._command_timeout,
                                                                                cmd_path="{}".format(qat_service_path))
                self._log.debug("Restarting the QAT Service in the SUT {}".format(qat_service_restart_results))
                if self.EXP_QAT_SERVICE_RESTART not in qat_service_restart_results:
                    raise content_exceptions.TestFail("Failed to Restart the QAT Services")

                if not self.qat_device_status():
                    raise content_exceptions.TestFail("QAT Tool does not supported in this system")

    def restart_qat_service(self, common_content_object=None):
        """
        This function check QAT device status on SUT
        :return: True if get the QAT device status test case pass else fail
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib

        self._log.info("Starting QAT service : to restart the QAT Service...")
        qat_service_path = self.get_qat_binary_path_linux("qat_service")
        qat_service_start_results = common_content_object.execute_sut_cmd_no_exception("/{}/{}".format(qat_service_path,
                                                                                                self.QAT_SERVICE_RESTART),
                                                                                       "run service qat_service restart",
                                                                                       self._command_timeout,
                                                                                       cmd_path="{}".format(
                                                                                           qat_service_path),
                                                                                       ignore_result="ignore")
        self._log.debug("Starting the QAT Service: {}".format(qat_service_start_results))
        if "Starting" not in qat_service_start_results:
            raise content_exceptions.TestFail("Failed to restart the QAT Services")

        if not self.qat_device_status(common_content_object):
            raise content_exceptions.TestFail("QAT Tool does not supported in this system")

    def start_qat_service(self, common_content_object=None):
        """
        This function check QAT device status on SUT

        :return: True if get the QAT device status test case pass else fail
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        qat_service_path = self.get_qat_binary_path_linux("qat_service")
        self._log.info("Starting QAT service : to restart the QAT Service...")
        qat_service_start_results = common_content_object.execute_sut_cmd_no_exception("/{}/{}".format(
                                                                                        qat_service_path,
                                                                                        self.QAT_SERVICE_START),
                                                                               "run service qat_service start",
                                                                                self._command_timeout,
                                                                                cmd_path="{}".format(qat_service_path),
                                                                                ignore_result="ignore")
        self._log.debug("Starting the QAT Service: {}".format(qat_service_start_results))
        if "Starting" not in qat_service_start_results:
            raise content_exceptions.TestFail("Failed to start the QAT Services")

        if not self.qat_device_status(common_content_object):
            raise content_exceptions.TestFail("QAT Tool does not supported in this system")

    def stop_qat_service(self, common_content_object=None):
        """
        This function check QAT device status on SUT

        :return: True if get the QAT device status test case pass else fail
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib

        qat_service_path = self.get_qat_binary_path_linux("qat_service")
        self._log.info("Stopping QAT service : to restart the QAT Service...")
        qat_service_stop_results = common_content_object.execute_sut_cmd_no_exception("/{}/{}".format(
                                                                                        qat_service_path,
                                                                                        self.QAT_SERVICE_STOP),
                                                                               "run service qat_service stop",
                                                                                self._command_timeout,
                                                                                cmd_path="{}".format(qat_service_path),
                                                                                ignore_result="ignore")
        self._log.debug("Stopping the QAT Service: {}".format(qat_service_stop_results))
        if "Stopping" not in qat_service_stop_results:
            raise content_exceptions.TestFail("Failed to stop the QAT Services")

        if not self.qat_device_status(common_content_object):
            raise content_exceptions.TestFail("QAT Tool does not supported in this system")

    def get_uuid_of_first_qat_device_instance(self, bdf_device, dev_type, common_content_object=None):
        """
        This method is to get the info about the QAT Device details and returns uuid of the first instance found for
        given device type "dev_type"
        :param bdf_device : BDF value as returned by get_qat_device_details()
        :param dev_type : device type such as "sym" or "dc" or "asym"
        :return uuid: None in case of no device
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        binary_name = "vqat_ctl"
        find_vqat_ctl_file_path = "find / -regex '.*\/build\/{}' -type f -name {} 2>/dev/null | grep *QAT*".format(binary_name,
                                                                                                       binary_name)
        vqat_ctl_path = common_content_object.execute_sut_cmd_no_exception(find_vqat_ctl_file_path,
                                                                           "run find command:{}".format(
                                                                               find_vqat_ctl_file_path),
                                                                           self._command_timeout,
                                                                           "/root",
                                                                           ignore_result="ignore")
        vqat_ctl_path = vqat_ctl_path.strip()
        common_content_object.execute_sut_cmd_no_exception("chmod 777 {}".format(vqat_ctl_path),
                                                           "enabling permission {}".format(
                                                               vqat_ctl_path),
                                                           self._command_timeout,
                                                           "/root",
                                                           ignore_result="ignore")
        find_vqat_ctl_file_path = "find / -regex '.*\/build\/{}' -perm /a=x -type f -name {} 2>/dev/null | grep *QAT*".format(binary_name,
                                                                                                                 binary_name)
        vqat_ctl_path = common_content_object.execute_sut_cmd_no_exception(find_vqat_ctl_file_path,
                                                                           "run find command:{}".format(
                                                                               find_vqat_ctl_file_path),
                                                                           self._command_timeout,
                                                                           "/root",
                                                                           ignore_result="ignore")
        vqat_ctl_path = vqat_ctl_path.strip()
        output = common_content_object.execute_sut_cmd_no_exception("/{} show".format(vqat_ctl_path),
                                                                    "run {} show command".format(
                                                                        vqat_ctl_path),
                                                                    self._command_timeout,
                                                                    "{}".format(os.path.dirname(vqat_ctl_path)),
                                                                    ignore_result="ignore")
        bdf_sym_asym_dc_list = output.split("\n")
        # initialize an empty string
        uuid = None
        max_index = len(bdf_sym_asym_dc_list)
        uuid_found = False
        for index, element in enumerate(bdf_sym_asym_dc_list):
            if uuid_found:
                break
            value = re.findall(r"BDF.*", element, re.M)
            if re.findall(r"BDF:\s+", element, re.M):
                bdf = value[0].split(": ")[1].strip()
                if bdf == bdf_device:
                    for idx in range(index + 1, max_index):
                        new_element = bdf_sym_asym_dc_list[idx]
                        if re.findall(r"BDF:\s+", new_element, re.M):
                            break
                        if re.findall(r"^\s+\d+\s+{}\s+.*".format(dev_type), new_element, re.M):
                            new_val = re.findall(r"^\s+\d+\s+{}\s+.*".format(dev_type), new_element, re.M)
                            uuid = new_val[0].split()[2]
                            uuid_found = True
                            break

        if uuid_found:
            self._log.info("uuid for device {} with BDF {}:\n{}".format(uuid, dev_type, bdf_device))
        else:
            self._log.error("Error:device {} with given bdf value {} not found\n".format(dev_type, bdf_device))

        return uuid

    def get_qat_device_details(self, common_content_object=None):
        """
        This method is to get the info about the QAT Device details

        :return bdf_sym_asym_dc: output of the "vqat_ctl show" command
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        binary_name = "vqat_ctl"
        find_vqat_ctl_file_path = "find / -regex '.*\/build\/{}' -type f -name {} 2>/dev/null | grep *QAT*".format(binary_name,
                                                                                                       binary_name)
        vqat_ctl_path = common_content_object.execute_sut_cmd_no_exception(find_vqat_ctl_file_path,
                                                                           "run find command:{}".format(
                                                                               find_vqat_ctl_file_path),
                                                                           self._command_timeout,
                                                                           "/root",
                                                                           ignore_result="ignore")
        vqat_ctl_path = vqat_ctl_path.strip()
        common_content_object.execute_sut_cmd_no_exception("chmod 777 {}".format(vqat_ctl_path),
                                                           "enabling permission {}".format(
                                                               vqat_ctl_path),
                                                           self._command_timeout,
                                                           "/root",
                                                           ignore_result="ignore")
        find_vqat_ctl_file_path = "find / -regex '.*\/build\/{}' -perm /a=x -type f -name {} 2>/dev/null | grep *QAT*".format(
            binary_name,binary_name)
        vqat_ctl_path = common_content_object.execute_sut_cmd_no_exception(find_vqat_ctl_file_path,
                                                                    "run find command:{}".format(find_vqat_ctl_file_path),
                                                                    self._command_timeout,
                                                                    self.ROOT_PATH,
                                                                    ignore_result="ignore")
        vqat_ctl_path = vqat_ctl_path.strip()
        output = common_content_object.execute_sut_cmd_no_exception("/{} show".format(vqat_ctl_path),
                                                                    "run {} show command".format(vqat_ctl_path),
                                                                    self._command_timeout,
                                                                    cmd_path="{}".format(os.path.dirname(vqat_ctl_path)),
                                                                    ignore_result="ignore")

        bdf_sym_asym_dc_list = output.split("\n")
        # initialize an empty string
        bdf_sym_asym_dc = {}
        bdf_sym_asym_dc['bdf']=[]
        bdf_sym_asym_dc['sym']=[]
        bdf_sym_asym_dc['asym']=[]
        bdf_sym_asym_dc['dc']=[]

        for index, element in enumerate(bdf_sym_asym_dc_list):
            value = re.findall(r"BDF.*|Available sym.*|Available asym.*|Available dc.*", element, re.M)
            if re.findall(r"BDF:\s+", element, re.M):
                bdf_sym_asym_dc['bdf'].append(value[0].split(": ")[1].strip())

            if re.findall(r"Available sym\s+:.*", element, re.M):
                bdf_sym_asym_dc['sym'].append(int(value[0].split(":")[1].strip()))

            if re.findall(r"Available asym\s+:.*", element, re.M):
                bdf_sym_asym_dc['asym'].append(int(value[0].split(":")[1].strip()))

            if re.findall(r"Available dc\s+:.*", element, re.M):
                bdf_sym_asym_dc['dc'].append(int(value[0].split(":")[1].strip()))

        # if system is not rebooted, VFs might be attached to vfio driver, in that case try lspci to get the details
        if len(bdf_sym_asym_dc['bdf']) == 0:
            dict_bdf_sym_asym_dc_list = self.get_all_qat_device_bdf_value(common_content_object=common_content_object)
            bdf_sym_asym_dc['bdf'] = dict_bdf_sym_asym_dc_list['bdf']

        self._log.info("bdf_sym_asym_dc:\n{}".format(bdf_sym_asym_dc))
        return bdf_sym_asym_dc

    def get_qat_vf_device_details(self, common_content_object=None):
        """
        This method is to get the info about the QAT Device details

        :return bdf_sym_asym_dc: output of the "vqat_ctl show" command
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        binary_name = "adf_ctl"
        find_adaf_ctl_file_path = r"find / -regex '.*\/build\/{}' -type f -name {} 2>/dev/null | grep *QAT*".format(binary_name,
                                                                                                       binary_name)

        adaf_ctl_path = common_content_object.execute_sut_cmd_no_exception(find_adaf_ctl_file_path,
                                                                           "run find command:{}".format(
                                                                               find_adaf_ctl_file_path),
                                                                           self._command_timeout,
                                                                           "/root",
                                                                           ignore_result="ignore")
        adaf_ctl_path = adaf_ctl_path.strip()
        common_content_object.execute_sut_cmd_no_exception("chmod 777 {}".format(adaf_ctl_path),
                                                           "enabling permission {}".format(
                                                               adaf_ctl_path),
                                                           self._command_timeout,
                                                           "/root",
                                                           ignore_result="ignore")
        find_adaf_ctl_file_path = "find / -regex '.*\/build\/{}' -perm /a=x -type f -name {} 2>/dev/null | grep *QAT*".format(
            binary_name,binary_name)
        adaf_ctl_path = common_content_object.execute_sut_cmd_no_exception(find_adaf_ctl_file_path,
                                                                    "run find command:{}".format(find_adaf_ctl_file_path),
                                                                    self._command_timeout,
                                                                    self.ROOT_PATH,
                                                                    ignore_result="ignore")
        adaf_ctl_path = adaf_ctl_path.strip()
        output = common_content_object.execute_sut_cmd_no_exception("/{} status".format(adaf_ctl_path),
                                                                    "run {} status command".format(adaf_ctl_path),
                                                                    self._command_timeout,
                                                                    cmd_path="{}".format(os.path.dirname(adaf_ctl_path)),
                                                                    ignore_result="ignore")

        dbdf_list_data = output.split("\n")
        # """
        # output will be as below ===>
        # Checking status of all devices.
        # There is 136 QAT acceleration device(s) in the system:
        # qat_dev7 - type: 4xxx,  inst_id: 7,  node_id: 1,  bsf: 0000:f7:00.0,  #accel: 1 #engines: 9 state: up
        # qat_dev8 - type: 4xxxvf,  inst_id: 0,  node_id: 0,  bsf: 0000:6b:00.1,  #accel: 1 #engines: 1 state: up
        # """
        # initialize an empty string
        dbdf_list = {}
        dbdf_list['bdf'] = []
        dbdf_list['dev_num'] = []
        dbdf_list['inst_id'] = []
        dbdf_list['node'] = []
        dbdf_list['accel'] = []
        dbdf_list['engines'] = []
        dbdf_list['state'] = []

        for index, element in enumerate(dbdf_list_data):
            if "qat_dev" in element:
                list_data = element.split(',')
                if "vf" in list_data[0]:
                    qat_vf_num_type = list_data[0].split('-')
                    dbdf_list['dev_num'].append(re.findall('[0-9]+', qat_vf_num_type[0])[0])
                    dbdf_list['inst_id'].append(list_data[1].split(':')[1].strip())
                    dbdf_list['node'].append(list_data[2].split(':')[1].strip())
                    dbdf_list['bdf'].append(
                        re.findall('.*bsf:\s+([0-9a-fA-F]{4}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}.\d{1}\S*)', list_data[3])[0])
                    dbdf_list['accel'].append(re.findall("#accel:\s+\d+", list_data[4])[0].split(':')[1].strip())
                    dbdf_list['engines'].append(re.findall("#engines:\s+\d+", list_data[4])[0].split(':')[1].strip())
                    dbdf_list['state'].append(
                        re.findall("\s+state:\s+[A-Za-z]+", list_data[4])[0].split(':')[1].strip())

        # if system is not rebooted, VFs might be attached to vfio driver, in that case try lspci to get the details
        if len(dbdf_list['bdf']) == 0:
            bdf_sym_asym_dc = self.get_all_sriov_vf_qat_device_bdf_value(common_content_object=common_content_object)
            dbdf_list['bdf'] = bdf_sym_asym_dc['bdf']
        self._log.info("bdf_sym_asym_dc:\n{}".format(dbdf_list))
        return dbdf_list

    def unload_vfio_driver(self, common_content_object=None):
        """
        This function will load vfio and vfio-pci driver
        [root@embargo QAT]# modprobe vfio
        [root@embargo QAT]# modprobe vfio-pci
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        # command = "modprobe -r -v vfio;modprobe -r -v vfio-pci;"
        command = "modprobe -r -v vfio-pci;"
        try:
            output = common_content_object.execute_sut_cmd_no_exception(command,
                                                                        "run command:{}".format(command),
                                                                        self._command_timeout,
                                                                        self.ROOT_PATH,
                                                                        ignore_result="ignore")
        except:
            pass
        output = output.strip()
        self._log.info("Result of the run {} command: {}".format(command, output))

    def load_vfio_driver(self, common_content_object=None):
        """
        This function will load vfio and vfio-pci driver
        [root@embargo QAT]# modprobe vfio
        [root@embargo QAT]# modprobe vfio-pci
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        command = "modprobe vfio;modprobe vfio-pci;"

        output = common_content_object.execute_sut_cmd_no_exception(command,
                                                                    "run command:{}".format(command),
                                                                    self._command_timeout,
                                                                    self.ROOT_PATH,
                                                                    ignore_result="ignore")
        output = output.strip()
        self._log.info("Result of the run {} command: {}".format(command, output))

    def create_accel_virtual_function(self, no_of_vf, dbsf_value):
        """
        This function will create virtual function of accelerator device
        [root@embargo QAT]# echo no_of_vf > /sys/bus/pci/devices/0000\:f8\:02.0/sriov_numvfs
        :param dbsf_value : Domain Bus Device Function of the VF Device e.g. 0000:AA:BB.C
        """
        domain_value = int(dbsf_value.split(":")[0].strip(), 16)
        bus_value = int(dbsf_value.split(":")[1].strip(), 16)
        slot_value = int(dbsf_value.split(":")[2].split(".")[0].strip(), 16)
        function_value = int(dbsf_value.split(":")[2].split(".")[1].strip(), 16)
        command = "echo {} > /sys/bus/pci/devices/{:04x}\:{:02x}\:{:02x}.{:01x}/sriov_numvfs".format(no_of_vf, domain_value,
                                                                                                  bus_value, slot_value,
                                                                                                  function_value)


        output = self._common_content_lib.execute_sut_cmd_no_exception(command,
                                                                    "run command:{}".format(command),
                                                                    self._command_timeout,
                                                                    self.ROOT_PATH,
                                                                    ignore_result="ignore")
        output = output.strip()
        self._log.info("Result of create VFs {} command: {}".format(command, output))

    def delete_accel_virtual_function(self, dbsf_value):
        """
        This function will delete virtual function of accelerator device
        [root@embargo QAT]# echo 0 > /sys/bus/pci/devices/0000\:f8\:02.0/sriov_numvfs
        :param dbsf_value : Domain Bus Device Function of the VF Device e.g. 0000:AA:BB.C
        """

        domain_value = int(dbsf_value.split(":")[0].strip(), 16)
        bus_value = int(dbsf_value.split(":")[1].strip(), 16)
        slot_value = int(dbsf_value.split(":")[2].split(".")[0].strip(), 16)
        function_value = int(dbsf_value.split(":")[2].split(".")[1].strip(), 16)
        command = "echo 0 > /sys/bus/pci/devices/{:04x}\:{:02x}\:{:02x}.{:01x}/sriov_numvfs".format( domain_value,
                                                                                                  bus_value, slot_value,
                                                                                                  function_value)


        output = self._common_content_lib.execute_sut_cmd_no_exception(command,
                                                                    "run command:{}".format(command),
                                                                    self._command_timeout,
                                                                    self.ROOT_PATH,
                                                                    ignore_result="ignore")
        output = output.strip()
        self._log.info("Result of delete VFs {} command: {}".format(command, output))

    def check_and_disbale_if_svm_enabled(self, file_path, common_content_object=None):
        """
        Check dev_cfg of the VF to see if SVM is enabled successfully on the device:
        [root@simics-craff home]# cat /etc/4xxx_dev<0,1,2,3,4...>.conf | grep -i SVMEnabled
        SvmEnabled = 1
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib

        command = "ls -la /etc/ | grep -i {} |grep -v grep".format(os.path.basename(file_path))

        output = common_content_object.execute_sut_cmd_no_exception(command,
                                                                    "run command:{}".format(command),
                                                                    self._command_timeout,
                                                                    "/etc/",
                                                                    ignore_result="ignore")

        if os.path.basename(file_path) not in output:
            self._log.info("File {} not found, command:{},o/p:{}".format(file_path, command, output))
            return

        command = "cat {} | grep -i SVMEnabled |" \
                  " grep -v grep".format(file_path)

        output = common_content_object.execute_sut_cmd_no_exception(command,
                                                                    "run command:{}".format(command),
                                                                    self._command_timeout,
                                                                    "/etc/",
                                                                    ignore_result="ignore")
        output = output.strip()
        self._log.info("Result of the run {} command: {}".format(command, output))

        output_list0 = re.findall(".*SVMEnabled = 1.*", output)
        output_list1 = re.findall(".*SVMEnabled=1.*", output)
        list0_len = len(output_list0)
        list1_len = len(output_list1)
        if list0_len == 0 and list1_len == 0:
            self._log.info("SVM Is NOT enabled")
            return
        else:
            self._log.info("SVM Is enabled")

        if list0_len == 1:
            self._log.info("SVM Is enabled, disabling now...")
            cmd = "fin = open(\"{}\", \"rt\"); data = fin.read();fin.close();" \
            "data = data.replace(\"SvmEnabled = 1\", \"SvmEnabled = 0\");" \
            "fin = open(\"{}\", \"wt\");fin.write(data);fin.close();exit();".format(file_path, file_path)
            try:
                common_content_object.execute_sut_cmd("python -c '{}'".format(cmd), "enable SIOV",
                                                    self._command_timeout, "/root")
            except:
                pass

        if list1_len == 1:
            cmd = "fin = open(\"{}\", \"rt\"); data = fin.read();fin.close();" \
                  "data = data.replace(\"SvmEnabled=1\", \"SvmEnabled=0\");" \
                  "fin = open(\"{}\", \"wt\");fin.write(data);fin.close();exit();".format(file_path, file_path)
            try:
                common_content_object.execute_sut_cmd("python -c '{}'".format(cmd), "enable SIOV",
                                                      self._command_timeout, "/root")
            except:
                pass

        self.restart_qat_service(common_content_object=common_content_object)

    def check_if_spr_svm_enabled(self, dbsf_value, no_of_vf, common_content_object=None):
        """
        Check dev_cfg of the VF to see if SVM is enabled successfully on the device:
        [root@simics-craff home]# cat /sys/kernel/debug/qat_4xxxvf_0000\:6b\:01.00/dev_cfg | grep -i SVMEnabled
        SvmEnabled = 1
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib

        domain_value = int(dbsf_value.split(":")[0].strip(), 16)
        bus_value = int(dbsf_value.split(":")[1].strip(), 16)
        slot_value = int(dbsf_value.split(":")[2].split(".")[0].strip(), 16)
        function_value = int(dbsf_value.split(":")[2].split(".")[1].strip(), 16)
        # For first slot_value, vf_value will start with 1 and go to max value of 7,
        # in further cycles for next slot value it will wrap to 0 and continue till 7
        vf_value = 1
        for index in range(0, no_of_vf):
            #vf_value as 0 means slot_number will be next for these VF and one slot can have max 8 VF
            if vf_value == 0:
                slot_value = slot_value + 1
            command = "cat /sys/kernel/debug/qat_4xxxvf_{:04x}\:{:02x}\:{:02x}.{:02x}/dev_cfg | grep -i SVMEnabled |" \
                      " grep -v grep".format(domain_value, bus_value, slot_value, vf_value)

            output = common_content_object.execute_sut_cmd_no_exception(command,
                                                                        "run command:{}".format(command),
                                                                        self._command_timeout,
                                                                        self.ROOT_PATH,
                                                                        ignore_result="ignore")
            output = output.strip()
            self._log.info("Result of the run {} command: {}".format(command, output))

            output_list = re.findall(".*SVMEnabled = 1.*", output)
            list_len = len(output_list)
            if list_len == 0:
                raise content_exceptions.TestFail("SVM Is Not enable in VFs")
            # wrap to 0 as max VF can be 7
            vf_value = ((vf_value + 1) % 8)
        self._log.info("Successfully verified VFs and SVM is enabled in the VFs {}".format(output))

    def host_vfio_driver_unbind(self, dbsf_value, common_content_object=None):
        """
        This function will unbind the host vfio driver
        [root@embargo QAT]# echo 0000:f8:02.0 > /sys/bus/pci/devices/0000\:f8\:02.0/driver/unbind
        :param dbsf_value : Domain Bus Device Function of the VF Device e.g. 0000:AA:BB.C
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib

        domain_value = int(dbsf_value.split(":")[0].strip(), 16)
        bus_value = int(dbsf_value.split(":")[1].strip(), 16)
        slot_value = int(dbsf_value.split(":")[2].split(".")[0].strip(), 16)
        function_value = int(dbsf_value.split(":")[2].split(".")[1].strip(), 16)
        command = "echo {} > /sys/bus/pci/devices/{:04x}\:{:02x}\:{:02x}.{:01x}/driver/unbind".format(dbsf_value, domain_value,
                                                                                                  bus_value, slot_value,
                                                                                                  function_value)
        try:
            output = common_content_object.execute_sut_cmd_no_exception(command,
                                                                    "run command:{}".format(command),
                                                                    self._command_timeout,
                                                                    self.ROOT_PATH,
                                                                    ignore_result="ignore")
        except:
            pass
        output = output.strip()
        self._log.info("Result of the run {} command: {}".format(command, output))

    def guest_vfio_pci_driver_bind(self, dbsf_value, accel_type=None, common_content_object=None):
        """
        This function will bind the guest vfio-pci driver
        :param dbsf_value : Domain Bus Device Function of the VF Device e.g. 0000:AA:BB.C
        [root@embargo QAT]# echo 8086 4941 > /sys/bus/pci/drivers/vfio-pci/new_id
        [root@embargo QAT]# lspci -s f8:02.0 -k
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        domain_value = int(dbsf_value.split(":")[0].strip(), 16)
        bus_value = int(dbsf_value.split(":")[1].strip(), 16)
        slot_value = int(dbsf_value.split(":")[2].split(".")[0].strip(), 16)
        function_value = int(dbsf_value.split(":")[2].split(".")[1].strip(), 16)
        if accel_type == "dsa":
            command = "echo 8086 0b25 > /sys/bus/pci/drivers/vfio-pci/new_id"
        elif accel_type == "qat":
            command = "echo 8086 4941 > /sys/bus/pci/drivers/vfio-pci/new_id"
        else:
            command = "echo 8086 1593 > /sys/bus/pci/drivers/vfio-pci/new_id"

        lspci_cmd = "lspci -s {} -k".format(dbsf_value)
        try:
            output = common_content_object.execute_sut_cmd_no_exception(command,
                                                                    "run command:{}".format(command),
                                                                    self._command_timeout,
                                                                    self.ROOT_PATH,
                                                                    ignore_result="ignore")
        except:
            pass
        output = output.strip()
        self._log.info("Result of the run {} command: {}".format(command, output))

        lspci_cmd_output = common_content_object.execute_sut_cmd_no_exception(lspci_cmd,
                                                                    "run command:{}".format(lspci_cmd),
                                                                    self._command_timeout,
                                                                    self.ROOT_PATH,
                                                                    ignore_result="ignore")
        lspci_cmd_output = lspci_cmd_output.strip()
        self._log.info("Result of the run {} command: {}".format(lspci_cmd, lspci_cmd_output))

    def host_vfio_driver_bind(self, dbsf_value, common_content_object=None):
        """
        This function will unbind the host vfio driver
        [root@embargo QAT]# echo 0000:f8:02.0 > /sys/bus/pci/devices/0000\:f8\:02.0/driver/unbind
        :param dbsf_value : Domain Bus Device Function of the VF Device e.g. 0000:AA:BB.C
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib

        domain_value = int(dbsf_value.split(":")[0].strip(), 16)
        bus_value = int(dbsf_value.split(":")[1].strip(), 16)
        slot_value = int(dbsf_value.split(":")[2].split(".")[0].strip(), 16)
        function_value = int(dbsf_value.split(":")[2].split(".")[1].strip(), 16)
        command = "echo {} > /sys/bus/pci/devices/{:04x}\:{:02x}\:{:02x}.{:01x}/driver/bind".format(dbsf_value, domain_value,
                                                                                                  bus_value, slot_value,
                                                                                                  function_value)

        try:
            output = common_content_object.execute_sut_cmd_no_exception(command,
                                                                    "run command:{}".format(command),
                                                                    self._command_timeout,
                                                                    self.ROOT_PATH,
                                                                    ignore_result="ignore")
        except:
            pass
        output = output.strip()
        self._log.info("Result of the run {} command: {}".format(command, output))

    def guest_vfio_pci_driver_unbind(self, dbsf_value, accel_type=None, common_content_object=None):
        """
        This function will bind the guest vfio-pci driver
        :param dbsf_value : Domain Bus Device Function of the VF Device e.g. 0000:AA:BB.C
        [root@embargo QAT]# echo 8086 4941 > /sys/bus/pci/drivers/vfio-pci/new_id
        [root@embargo QAT]# lspci -s f8:02.0 -k
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        domain_value = int(dbsf_value.split(":")[0].strip(), 16)
        bus_value = int(dbsf_value.split(":")[1].strip(), 16)
        slot_value = int(dbsf_value.split(":")[2].split(".")[0].strip(), 16)
        function_value = int(dbsf_value.split(":")[2].split(".")[1].strip(), 16)
        if accel_type == "dsa":
            command = "echo 8086 0b25 > /sys/bus/pci/drivers/vfio-pci/remove_id"
        elif accel_type == "qat":
            command = "echo 8086 4941 > /sys/bus/pci/drivers/vfio-pci/remove_id"
        else:
            command = "echo 8086 1593 > /sys/bus/pci/drivers/vfio-pci/remove_id"

        lspci_cmd = "lspci -s {} -k".format(dbsf_value)
        try:
            output = common_content_object.execute_sut_cmd_no_exception(command,
                                                                        "run command:{}".format(command),
                                                                        self._command_timeout,
                                                                        self.ROOT_PATH,
                                                                        ignore_result="ignore")
        except:
            pass
        output = output.strip()
        self._log.info("Result of the run {} command: {}".format(command, output))

        lspci_cmd_output = common_content_object.execute_sut_cmd_no_exception(lspci_cmd,
                                                                    "run command:{}".format(lspci_cmd),
                                                                    self._command_timeout,
                                                                    self.ROOT_PATH,
                                                                    ignore_result="ignore")
        lspci_cmd_output = lspci_cmd_output.strip()
        self._log.info("Result of the run {} command: {}".format(lspci_cmd, lspci_cmd_output))

    def run_qat_signoflife_workload(self, common_content_object=None):
        """
        This function runs the QAT workload on the system.
        """
        vqat_workload_cmd = "/{} signOfLife=1 runTests='1|2|4|8|16|32'"
        if common_content_object is None:
            common_content_object = self._common_content_lib
        binary_name = "cpa_sample_code"

        find_vqat_wl_file_path_cmd = "find / -regex '.*\/QAT\/build\/{}' -type f -name {} 2>/dev/null | grep *QAT*".format(binary_name,
                                                                                                       binary_name)

        find_vqat_wl_file_path = common_content_object.execute_sut_cmd_no_exception(find_vqat_wl_file_path_cmd,
                                                                               "run find command:{}".format(
                                                                                   find_vqat_wl_file_path_cmd),
                                                                               self._command_timeout,
                                                                               self.ROOT_PATH,
                                                                               ignore_result="ignore")

        find_vqat_wl_file_path = find_vqat_wl_file_path.strip()
        common_content_object.execute_sut_cmd_no_exception("chmod 777 {}".format(find_vqat_wl_file_path),
                                                           "enabling permission {}".format(
                                                               find_vqat_wl_file_path),
                                                           self._command_timeout,
                                                           "/root",
                                                           ignore_result="ignore")
        find_vqat_wl_file_path_cmd = "find / -regex '.*\/QAT\/build\/{}' -perm /a=x -type f -name {} 2>/dev/null | grep *QAT*".format(
            binary_name,binary_name)
        vqat_wl_file_path = common_content_object.execute_sut_cmd_no_exception(find_vqat_wl_file_path_cmd,
                                                                "run find command:{}".format(find_vqat_wl_file_path_cmd),
                                                                self._command_timeout,
                                                                self.ROOT_PATH,
                                                                ignore_result="ignore")
        vqat_wl_file_path = vqat_wl_file_path.strip()
        sample_code_results = common_content_object.execute_sut_cmd(vqat_workload_cmd.format(vqat_wl_file_path),
                                                    "run /{} signOfLife = 1 runTests = 1 | 2 | 4 | 8 | 16 | 32 command"
                                                    .format(vqat_wl_file_path),
                                                    self._command_timeout,
                                                    cmd_path="{}".format(os.path.dirname(vqat_wl_file_path)))

        self._log.info("VQAT Workload started: run [/{} signOfLife = 1 runTests = 1 | 2 | 4 | 8 | 16 | 32 command],"
                        " [O/P: {}]".format(vqat_wl_file_path, sample_code_results))

        self._log.debug("Cpa Sample code file execution output {}".format(sample_code_results))
        if not re.findall(self.REGEX_FOR_ERR, "".join(sample_code_results)) or re.findall(self.REGEX_FOR_ERROR, "".join(
                sample_code_results)) or re.findall(self.REGEX_FOR_ERROR_CMD, "".join(sample_code_results)):
            if re.findall(self.REGEX_FOR_CODE_COMPLETED_SUCCESSFULLY, "".join(sample_code_results)):
                self._log.info("Cpa Sample code run completed successfully without any error")
        else:
            raise content_exceptions.TestFail("cpa_sample_code execution is failed with error")

    def qat_build_hash_sample_workload_app(self, common_content_object=None):
        """
        Build hash_sample application
        #export ICP_ROOT=<QAT package location>
        #cd  $ICP_ROOT/quickassist/lookaside/access_layer/src/sample_code/functional
        #make all
        #./build/hash_sample
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        hash_sample_folder_name = "functional"
        find_hash_sample_file_path_cmd = \
            "find / -regex '.*\/quickassist\/lookaside\/access_layer\/.*' -type d -name {} 2>/dev/null".\
                                                                                    format(hash_sample_folder_name)

        find_hash_sample_file_path = common_content_object.execute_sut_cmd_no_exception(find_hash_sample_file_path_cmd,
                                                                               "run find command:{}".format(
                                                                                find_hash_sample_file_path_cmd),
                                                                                self._command_timeout,
                                                                                self.ROOT_PATH,
                                                                                ignore_result="ignore")

        icp_root_path = find_hash_sample_file_path.strip().split("quickassist")[0].strip()
        self._log.info("Hash Sample path {} ICP_ROOT Path : {}".format(find_hash_sample_file_path.strip(), icp_root_path))

        build_hash_sample_cmd = "export ICP_ROOT={};" \
                                "cd $ICP_ROOT/quickassist/lookaside/access_layer/src/sample_code/functional;" \
                                "make all;".format(icp_root_path)

        build_cmd_output = common_content_object.execute_sut_cmd(build_hash_sample_cmd,
                                                                              "run command:{}".format(build_hash_sample_cmd),
                                                                              self._command_timeout,
                                                                              self.ROOT_PATH)
        build_cmd_output = build_cmd_output.strip()
        self._log.info("Result of the run {} command: {}".format(build_hash_sample_cmd, build_cmd_output))

    def qat_run_hash_sample_workload(self, common_content_object=None):
        """
        Run usign SIOV QATDC virtual device e.g. qat-dc name = 092017ea-e613-4d63-8349-eb3f5d0d78a8

        Run hash_sample application
        #export ICP_ROOT=<QAT package location>
        #cd  $ICP_ROOT/quickassist/lookaside/access_layer/src/sample_code/functional
        #make all
        #./build/hash_sample
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        hash_sample_folder_name = "functional"
        find_hash_sample_file_path_cmd = \
            "find / -regex '.*\/quickassist\/lookaside\/access_layer\/.*' -type d -name {} 2>/dev/null".\
                                                                                    format(hash_sample_folder_name)

        find_hash_sample_file_path = common_content_object.execute_sut_cmd_no_exception(find_hash_sample_file_path_cmd,
                                                                               "run find command:{}".format(
                                                                                find_hash_sample_file_path_cmd),
                                                                                self._command_timeout,
                                                                                self.ROOT_PATH,
                                                                                ignore_result="ignore")

        icp_root_path = find_hash_sample_file_path.strip().split("quickassist")[0].strip()
        self._log.info("Hash Sample path {} ICP_ROOT Path : {}".format(find_hash_sample_file_path.strip(), icp_root_path))

        run_hash_sample_cmd = "export ICP_ROOT={};" \
                                "cd $ICP_ROOT/quickassist/lookaside/access_layer/src/sample_code/functional;" \
                                "./build/hash_sample;".format(icp_root_path)

        run_cmd_output = common_content_object.execute_sut_cmd(run_hash_sample_cmd,
                                                                              "run command:{}".format(run_hash_sample_cmd),
                                                                              self._command_timeout,
                                                                              self.ROOT_PATH)
        run_cmd_output = run_cmd_output.strip()
        self._log.info("Result of the run {} command: {}".format(run_hash_sample_cmd, run_cmd_output))
        # Add error checking using regex ???

        self._log.info("hash_sample command executed successfully {}".format(run_cmd_output))

    def run_qat_workload(self, common_content_object=None):
        """
        This function runs the QAT workload on the system.
        """
        vqat_workload_cmd = "/{}"
        if common_content_object is None:
            common_content_object = self._common_content_lib
        binary_name = "cpa_sample_code"
        find_vqat_wl_file_path = "find / -regex '.*\/build\/{}' -type f -name {} 2>/dev/null | grep *QAT*".format(binary_name,
                                                                                                       binary_name)
        vqat_ctl_path = common_content_object.execute_sut_cmd_no_exception(find_vqat_wl_file_path,
                                                                           "run find command:{}".format(
                                                                               find_vqat_wl_file_path),
                                                                           self._command_timeout,
                                                                           "/root",
                                                                           ignore_result="ignore")
        vqat_ctl_path = vqat_ctl_path.strip()
        common_content_object.execute_sut_cmd_no_exception("chmod 777 {}".format(vqat_ctl_path),
                                                           "enabling permission {}".format(
                                                               vqat_ctl_path),
                                                           self._command_timeout,
                                                           "/root",
                                                           ignore_result="ignore")
        find_vqat_wl_file_path = "find / -regex '.*\/build\/{}' -perm /a=x -type f -name {} 2>/dev/null | grep *QAT*".format(
            binary_name,binary_name)
        vqat_wl_file_path = common_content_object.execute_sut_cmd_no_exception(find_vqat_wl_file_path,
                                                                "run find command:{}".format(find_vqat_wl_file_path),
                                                                self._command_timeout,
                                                                self.ROOT_PATH,
                                                                ignore_result="ignore")
        vqat_wl_file_path = vqat_wl_file_path.strip()
        sample_code_results = common_content_object.execute_sut_cmd(vqat_workload_cmd.format(vqat_wl_file_path),
                                                    "run /{} command"
                                                    .format(vqat_wl_file_path),
                                                    self._command_timeout,
                                                    self.ROOT_PATH)

        self._log.info("VQAT Workload started: run [/{} command],"
                        " [O/P: {}]".format(vqat_wl_file_path, sample_code_results))

        self._log.debug("Cpa Sample code file execution output {}".format(sample_code_results))
        if not re.findall(self.REGEX_FOR_ERR, "".join(sample_code_results)) or re.findall(self.REGEX_FOR_ERROR, "".join(
                sample_code_results)) or re.findall(self.REGEX_FOR_ERROR_CMD, "".join(sample_code_results)):
            if re.findall(self.REGEX_FOR_CODE_COMPLETED_SUCCESSFULLY, "".join(sample_code_results)):
                self._log.info("Cpa Sample code run completed successfully without any error")
        else:
            raise content_exceptions.TestFail("cpa_sample_code execution is failed with error")

    def run_qat_stress_workload(self, common_content_object=None):
        """
        This function runs the QAT workload on the system.
        """
        vqat_workload_cmd = "/{} runTests=1 cyNumBuffers=20 cySymLoops=30"
        if common_content_object is None:
            common_content_object = self._common_content_lib
        binary_name = "cpa_sample_code"
        find_vqat_wl_file_path = "find / -regex '.*\/build\/{}' -type f -name {} 2>/dev/null | grep *QAT*".format(binary_name,
                                                                                                       binary_name)
        vqat_wl_file_path = common_content_object.execute_sut_cmd_no_exception(find_vqat_wl_file_path,
                                                                               "run find command:{}".format(
                                                                                   find_vqat_wl_file_path),
                                                                               self._command_timeout,
                                                                               self.ROOT_PATH,
                                                                               ignore_result="ignore")

        vqat_wl_file_path = vqat_wl_file_path.strip()
        common_content_object.execute_sut_cmd_no_exception("chmod 777 {}".format(vqat_wl_file_path),
                                                           "enabling permission {}".format(
                                                               vqat_wl_file_path),
                                                           self._command_timeout,
                                                           "/root",
                                                           ignore_result="ignore")
        find_vqat_wl_file_path = "find / -regex '.*\/build\/{}' -perm /a=x -type f -name {} 2>/dev/null | grep *QAT*".format(
            binary_name,binary_name)
        vqat_wl_file_path = common_content_object.execute_sut_cmd_no_exception(find_vqat_wl_file_path,
                                                                "run find command:{}".format(find_vqat_wl_file_path),
                                                                self._command_timeout,
                                                                self.ROOT_PATH,
                                                                ignore_result="ignore")

        vqat_wl_file_path = vqat_wl_file_path.strip()
        sample_code_results = common_content_object.execute_sut_cmd(vqat_workload_cmd.format(vqat_wl_file_path),
                                                    "run /{} runTests=1 cyNumBuffers=20 cySymLoops=30 command"
                                                    .format(vqat_wl_file_path),
                                                    self._command_timeout,
                                                    self.ROOT_PATH)

        self._log.info("VQAT Workload started: run [/{} command],"
                        " [O/P: {}]".format(vqat_wl_file_path, sample_code_results))

        self._log.debug("Cpa Sample code file execution output {}".format(sample_code_results))
        if not re.findall(self.REGEX_FOR_ERR, "".join(sample_code_results)) or re.findall(self.REGEX_FOR_ERROR, "".join(
                sample_code_results)) or re.findall(self.REGEX_FOR_ERROR_CMD, "".join(sample_code_results)):
            if re.findall(self.REGEX_FOR_CODE_COMPLETED_SUCCESSFULLY, "".join(sample_code_results)):
                self._log.info("Cpa Sample code run completed successfully without any error")
        else:
            raise content_exceptions.TestFail("cpa_sample_code execution is failed with error")

    def set_qat_device_up_adfctl(self, index, common_content_object=None):
        """
        This function makes the qat device up using "adf_ctl"
        adf_ctl qat_dev0 up
        """

        if common_content_object is None:
            common_content_object = self._common_content_lib
        binary_name = "adf_ctl"
        cmd_adf_ctl_up = "/{} qat_dev{} up"
        find_adf_ctl_file_path = "find / -regex '.*\/build\/{}' -type f -name {} 2>/dev/null | grep *QAT*".format(binary_name,
                                                                                                       binary_name)
        adf_ctl_path = common_content_object.execute_sut_cmd_no_exception(find_adf_ctl_file_path,
                                                                          "run find command:{}".format(
                                                                              find_adf_ctl_file_path),
                                                                          self._command_timeout,
                                                                          self.ROOT_PATH,
                                                                          ignore_result="ignore")
        adf_ctl_path = adf_ctl_path.strip()
        common_content_object.execute_sut_cmd_no_exception("chmod 777 {}".format(adf_ctl_path),
                                                           "enabling permission {}".format(
                                                               adf_ctl_path),
                                                           self._command_timeout,
                                                           "/root",
                                                           ignore_result="ignore")
        find_adf_ctl_file_path = "find / -regex '.*\/build\/{}' -perm /a=x -type f -name {} 2>/dev/null | grep *QAT*".format(
            binary_name,binary_name)
        adf_ctl_path = common_content_object.execute_sut_cmd_no_exception(find_adf_ctl_file_path,
                                                                    "run find command:{}".format(find_adf_ctl_file_path),
                                                                    self._command_timeout,
                                                                    self.ROOT_PATH,
                                                                    ignore_result="ignore")
        adf_ctl_path = adf_ctl_path.strip()
        output = common_content_object.execute_sut_cmd_no_exception(cmd_adf_ctl_up.format(adf_ctl_path, index),
                                                                    "run {} qat_dev{} up command".format(
                                                                        adf_ctl_path, index),
                                                                    self._command_timeout,
                                                                    cmd_path="{}".format(os.path.dirname(adf_ctl_path)),
                                                                    ignore_result="ignore")

        self._log.info("Result of the run {} qat_dev{} up command: {}".format(adf_ctl_path, index, output))
        return output

    def get_qat_device_status_adfctl(self, index, common_content_object=None):
        """
        This function gets the status of vqat device using "adf_ctl"
        lspci -vd :0da5
	    run adf_ctl status
	    """
        cmd_adf_ctl = "/{} status"

        if common_content_object is None:
            common_content_object = self._common_content_lib
        binary_name = "adf_ctl"
        find_adf_ctl_file_path = "find / -regex '.*\/build\/{}' -type f -name {} 2>/dev/null | grep *QAT*".format(binary_name,
                                                                                                       binary_name)
        adf_ctl_path = common_content_object.execute_sut_cmd_no_exception(find_adf_ctl_file_path,
                                                                          "run find command:{}".format(
                                                                              find_adf_ctl_file_path),
                                                                          self._command_timeout,
                                                                          self.ROOT_PATH,
                                                                          ignore_result="ignore")
        adf_ctl_path = adf_ctl_path.strip()
        common_content_object.execute_sut_cmd_no_exception("chmod 777 {}".format(adf_ctl_path),
                                                           "enabling permission {}".format(
                                                               adf_ctl_path),
                                                           self._command_timeout,
                                                           "/root",
                                                           ignore_result="ignore")
        find_adf_ctl_file_path = "find / -regex '.*\/build\/{}' -perm /a=x -type f -name {} 2>/dev/null | grep *QAT*".format(
            binary_name,binary_name)

        adf_ctl_path = common_content_object.execute_sut_cmd_no_exception(find_adf_ctl_file_path,
                                                                    "run find command:{}".format(find_adf_ctl_file_path),
                                                                    self._command_timeout,
                                                                    self.ROOT_PATH,
                                                                    ignore_result="ignore")
        adf_ctl_path = adf_ctl_path.strip()
        output = common_content_object.execute_sut_cmd_no_exception(cmd_adf_ctl.format(adf_ctl_path),
                                                                    "run {} status command".format(
                                                                        adf_ctl_path),
                                                                    self._command_timeout,
                                                                    cmd_path="{}".format(os.path.dirname(adf_ctl_path)),
                                                                    ignore_result="ignore")

        if output is None or output == "":
            raise content_exceptions.TestFail("No QAT device found on system o/p = {}".format(output))

        self._log.info("Result of the adf_ctl {}".format(output))
        return output

    def check_vqat_dev_type_attached_to_vm(self, common_content_object=None):
        """
        first check devices assigned (e.g.)
        # lspci -vnd:4941 => cpm2.0 VF
        Vqats share same device ID in guest, you can distinguish them by subsystem ID ‘SDevice’.
        # lspci -vnd:4941 -> cpm2.0 VF
        # lspci -vnd:b058 ->cpm2.0 sym vqat
        # lspci -vnd:b059 ->cpm2.0 asym vqat
        # lspci -vnd:b05a ->cpm2.0 dc vqat
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib

        cmd_check_vqat = " lspci -vnd:4941 | grep 4941| wc -l"
        cmd_check_vqat_sym = "lspci -vnd:b058"
        cmd_check_vqat_asym = "lspci -vnd:b059"
        cmd_check_vqat_dc = "lspci -vnd:b05a"

        sym_d = None
        asym_d = None
        dc_d = None

        result_lspci = common_content_object.execute_sut_cmd_no_exception(cmd_check_vqat,
                                                                    "run find command:{}".format(cmd_check_vqat),
                                                                    self._command_timeout,
                                                                    self.ROOT_PATH,
                                                                    ignore_result="ignore")
        if result_lspci == 0:
            raise content_exceptions.TestFail("No VQAT VFs found on VM")

        result_lspci = common_content_object.execute_sut_cmd_no_exception(cmd_check_vqat_sym,
                                                                    "run {} command".format(
                                                                        cmd_check_vqat_sym),
                                                                    self._command_timeout,
                                                                    self.ROOT_PATH,
                                                                    ignore_result="ignore")

        self._log.debug("Result of the lspci for sym {}".format(result_lspci))
        if result_lspci is not None:
            sym_d = "sym"

        result_lspci = common_content_object.execute_sut_cmd_no_exception(cmd_check_vqat_asym,
                                                                    "run {} command".format(
                                                                        cmd_check_vqat_asym),
                                                                    self._command_timeout,
                                                                    self.ROOT_PATH,
                                                                    ignore_result="ignore")

        self._log.debug("Result of the lspci for asym {}".format(result_lspci))
        if result_lspci is not None:
            asym_d = "asym"

        result_lspci = common_content_object.execute_sut_cmd_no_exception(cmd_check_vqat_dc,
                                                                    "run {} command".format(
                                                                        cmd_check_vqat_dc),
                                                                    self._command_timeout,
                                                                    self.ROOT_PATH,
                                                                    ignore_result="ignore")

        self._log.debug("Result of the lspci for dc {}".format(result_lspci))
        if result_lspci is not None:
            dc_d = "dc"

        return sym_d, asym_d, dc_d

    def check_vqat_device_type_attached(self, common_content_object=None):
        """
        first check devices assigned (e.g.)
        # lspci -vnd:4941 => cpm2.0 VF
        Vqats share same device ID in guest, you can distinguish them by subsystem ID ‘SDevice’.
        # lspci -v -d 8086:0da5 -vmm | grep -E 'SDevice | 0000' => cpm2.0 sym vqat
        # lspci -v -d 8086:0da5 -vmm | grep -E 'SDevice | 0001' => cpm2.0 asym vqat
        # lspci -v -d 8086:0da5 -vmm | grep -E 'SDevice | 0002' => cpm2.0 dc vqat
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib

        cmd_check_vqat = " lspci -vnd:4941 | grep 4941| wc -l"
        cmd_check_vqat_sym = "lspci -v -d 8086:0da5 -vmm | grep -E 'SDevice | 0000'"
        cmd_check_vqat_asym = "lspci -v -d 8086:0da5 -vmm | grep -E 'SDevice | 0001'"
        cmd_check_vqat_dc = "lspci -v -d 8086:0da5 -vmm | grep -E 'SDevice | 0002'"

        sym_d = None
        asym_d = None
        dc_d = None

        result_lspci = common_content_object.execute_sut_cmd_no_exception(cmd_check_vqat,
                                                                          "run find command:{}".format(cmd_check_vqat),
                                                                          self._command_timeout,
                                                                          self.ROOT_PATH,
                                                                          ignore_result="ignore")
        if result_lspci == 0:
            raise content_exceptions.TestFail("No VQAT VFs found on VM")

        result_lspci = common_content_object.execute_sut_cmd_no_exception(cmd_check_vqat_sym,
                                                                    "run {} command".format(
                                                                        cmd_check_vqat_sym),
                                                                    self._command_timeout,
                                                                    self.ROOT_PATH,
                                                                    ignore_result="ignore")

        self._log.debug("Result of the lspci for sym {}".format(result_lspci))
        if result_lspci is not None:
            sym_d = "sym"

        result_lspci = common_content_object.execute_sut_cmd_no_exception(cmd_check_vqat_asym,
                                                                    "run {} command".format(
                                                                        cmd_check_vqat_asym),
                                                                    self._command_timeout,
                                                                    self.ROOT_PATH,
                                                                    ignore_result="ignore")

        self._log.debug("Result of the lspci for asym {}".format(result_lspci))
        if result_lspci is not None:
            asym_d = "asym"

        result_lspci = common_content_object.execute_sut_cmd_no_exception(cmd_check_vqat_dc,
                                                                    "run {} command".format(
                                                                        cmd_check_vqat_dc),
                                                                    self._command_timeout,
                                                                    self.ROOT_PATH,
                                                                    ignore_result="ignore")

        self._log.debug("Result of the lspci for dc {}".format(result_lspci))
        if result_lspci is not None:
            dc_d = "dc"

        return sym_d, asym_d, dc_d

    def remove_qat_devices(self, dev_uuid, common_content_object=None):
        """
        This method is to delete the QAT Device
        :param dev_uuid : uuid of the vqat device to be deleted
        :param dev_type : device type such as "sym" or "dc" or "asym"
        :return
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        binary_name = "vqat_ctl"
        find_vqat_ctl_file_path = "find / -regex '.*\/build\/{}' -type f -name {} 2>/dev/null  | grep *QAT*".format(binary_name,
                                                                                                       binary_name)
        vqat_ctl_path = common_content_object.execute_sut_cmd_no_exception(find_vqat_ctl_file_path,
                                                                           "run find command:{}".format(
                                                                               find_vqat_ctl_file_path),
                                                                           self._command_timeout,
                                                                           self.ROOT_PATH,
                                                                           ignore_result="ignore")
        vqat_ctl_path = vqat_ctl_path.strip()
        common_content_object.execute_sut_cmd_no_exception("chmod 777 {}".format(vqat_ctl_path),
                                                           "enabling permission {}".format(
                                                               vqat_ctl_path),
                                                           self._command_timeout,
                                                           "/root",
                                                           ignore_result="ignore")
        find_vqat_ctl_file_path = "find / -regex '.*\/build\/{}' -perm /a=x -type f -name {} 2>/dev/null | grep *QAT*".format(
            binary_name,binary_name)
        vqat_ctl_path = common_content_object.execute_sut_cmd_no_exception(find_vqat_ctl_file_path,
                                                                    "run find command:{}".format(find_vqat_ctl_file_path),
                                                                    self._command_timeout,
                                                                    self.ROOT_PATH,
                                                                    ignore_result="ignore")
        vqat_ctl_path = vqat_ctl_path.strip()
        result_remove_op = common_content_object.execute_sut_cmd_no_exception("/{} remove {}".format(
                                                                    vqat_ctl_path, dev_uuid),
                                                                    "run {} remove {} command".format(
                                                                        vqat_ctl_path, dev_uuid),
                                                                    self._command_timeout,
                                                                    "{}".format(os.path.dirname(vqat_ctl_path)),
                                                                    ignore_result="ignore")

        self._log.debug("Result of the QAT Device {} remove {}".format(dev_uuid, result_remove_op))

    def create_qat_devices(self, bdf_device, no_of_vqat_dev_available, dev_type, common_content_object=None):
        """
        This method is to create the QAT Device
        :param bdf_device : BDF value as returned by get_qat_device_details()
        :param no_of_vqat_dev_available : max number of  free qat available devices for which vqat can be created for
         given type
        :param dev_type : device type such as "sym" or "dc" or "asym"
        :return
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        binary_name = "vqat_ctl"
        find_vqat_ctl_file_path = "find / -regex '.*\/build\/{}' -type f -name {} 2>/dev/null  | grep *QAT*".format(binary_name,
                                                                                                       binary_name)
        vqat_ctl_path = common_content_object.execute_sut_cmd_no_exception(find_vqat_ctl_file_path,
                                                                           "run find command:{}".format(
                                                                               find_vqat_ctl_file_path),
                                                                           self._command_timeout,
                                                                           self.ROOT_PATH,
                                                                           ignore_result="ignore")
        vqat_ctl_path = vqat_ctl_path.strip()
        common_content_object.execute_sut_cmd_no_exception("chmod 777 {}".format(vqat_ctl_path),
                                                           "enabling permission {}".format(
                                                               vqat_ctl_path),
                                                           self._command_timeout,
                                                           "/root",
                                                           ignore_result="ignore")
        find_vqat_ctl_file_path = "find / -regex '.*\/build\/{}' -perm /a=x -type f -name {} 2>/dev/null | grep *QAT*".format(
            binary_name,binary_name)
        vqat_ctl_path = common_content_object.execute_sut_cmd_no_exception(find_vqat_ctl_file_path,
                                                                    "run find command:{}".format(find_vqat_ctl_file_path),
                                                                    self._command_timeout,
                                                                    self.ROOT_PATH,
                                                                    ignore_result="ignore")
        vqat_ctl_path = vqat_ctl_path.strip()
        dev_uuid_list = []
        no_of_new_vqat = 0
        for index in range(no_of_vqat_dev_available):
            result_create_op = common_content_object.execute_sut_cmd("/{} create {} {}".format(
                                                                        vqat_ctl_path, bdf_device, dev_type),
                                                                        "run {} create {} {} command".format(
                                                                            vqat_ctl_path, bdf_device, dev_type),
                                                                        self._command_timeout,
                                                                        "{}".format(os.path.dirname(vqat_ctl_path)))

            self._log.debug("Result of the QAT {} Device create {}".format(dev_type, result_create_op))
            regex_failed_check = ".*Failed to create QAT-{}.*".format(dev_type)
            result_create_failed = re.search(regex_failed_check, result_create_op, re.MULTILINE)
            if result_create_failed:
                break
            # dev_uuid_new = result_create_op.split("=")[1].strip()
            # dev_uuid[dev_type].append(dev_uuid_new)
            no_of_new_vqat = no_of_new_vqat + 1

        if no_of_new_vqat > 0:
            self._log.info("New vqat created on the system".format(no_of_new_vqat))

        # repopulate all device using vqat_ctl show for the given dbdf
        number_of_dev, dev_uuid_list = self.get_uuid_list_of_all_vqat_devices(bdf_device, dev_type,
                                                                    common_content_object)

        return number_of_dev, dev_uuid_list

    def get_uuid_list_of_all_vqat_devices(self, bdf_device, dev_type, common_content_object=None):
        """
                This method is to get the info about all VQAT Device and returns uuid of the all instances found for
                given device type "dev_type"
                :param bdf_device : BDF value as returned by get_qat_device_details()
                :param dev_type : device type such as "sym" or "dc" or "asym"
                :return uuid: None in case of no device
                """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        binary_name = "vqat_ctl"
        find_vqat_ctl_file_path = "find / -regex '.*\/build\/{}' -type f -name {} 2>/dev/null | grep *QAT*".format(binary_name,
                                                                                                     binary_name)
        vqat_ctl_path = common_content_object.execute_sut_cmd_no_exception(find_vqat_ctl_file_path,
                                                                           "run find command:{}".format(
                                                                               find_vqat_ctl_file_path),
                                                                           self._command_timeout,
                                                                           "/root",
                                                                           ignore_result="ignore")
        vqat_ctl_path = vqat_ctl_path.strip()
        common_content_object.execute_sut_cmd_no_exception("chmod 777 {}".format(vqat_ctl_path),
                                                           "enabling permission {}".format(
                                                               vqat_ctl_path),
                                                           self._command_timeout,
                                                           "/root",
                                                           ignore_result="ignore")
        find_vqat_ctl_file_path = "find / -regex '.*\/build\/{}' -perm /a=x -type f -name {} 2>/dev/null | grep *QAT*".format(
            binary_name,binary_name)
        vqat_ctl_path = common_content_object.execute_sut_cmd_no_exception(find_vqat_ctl_file_path,
                                                                           "run find command:{}".format(
                                                                               find_vqat_ctl_file_path),
                                                                           self._command_timeout,
                                                                           "/root",
                                                                           ignore_result="ignore")
        vqat_ctl_path = vqat_ctl_path.strip()

        output_data = common_content_object.execute_sut_cmd_no_exception("/{} show".format(vqat_ctl_path),
                                                                    "run {} show command".format(
                                                                        vqat_ctl_path),
                                                                    self._command_timeout,
                                                                    "{}".format(os.path.dirname(vqat_ctl_path)),
                                                                    ignore_result="ignore")


        bdf_val = bdf_device
        bdf_data_blocks = output_data.split('BDF:')
        uuid_list = []
        uuid_collected = 0
        if dev_type == "sym":
            regex_dev_uuid = ".*\d+\s+(sym\s+.*[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\s+\w+.*"
        if dev_type == "asym":
            regex_dev_uuid = ".*\d+\s+(asym\s+.*[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\s+\w+.*"
        if dev_type == "dc":
            regex_dev_uuid = ".*\d+\s+(dc\s+.*[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12})\s+\w+.*"

        if len(bdf_data_blocks) > 0:
            for index in range(len(bdf_data_blocks)):
                bdf_data_block_elem = bdf_data_blocks[index]
                bdf_block_data_lines = bdf_data_block_elem.split('\n')
                index = 0
                if bdf_val in bdf_block_data_lines[index]:

                    dev_data_list = re.findall(regex_dev_uuid, bdf_data_block_elem, re.M)

                    regex_uuid = ".*([0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}).*"
                    for uuid_index in range(len(dev_data_list)):
                        uuid_data_match = re.search(regex_uuid, dev_data_list[uuid_index], re.M)
                        uuid_data = uuid_data_match.group(1).strip()
                        uuid_list.append(uuid_data)
                        uuid_collected = uuid_collected + 1

        self._log.info("Total vqat found on the system {} for DBDF {}".format(uuid_collected, bdf_device))

        return uuid_collected, uuid_list

    def spr_qat_installation(self, qat_folder_path, configure_spr_cmd=None, common_content_object=None):
        """
        This function execute SPR QAT Tool installation

        :param: qat_folder_path get the QAT folder path
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        if configure_spr_cmd:
            configure_cmd = configure_spr_cmd
        else:
            configure_cmd = r"./configure && make uninstall"
        make_cmd = "make -s -j install"
        make_install_samples = "make -s -j samples-install"
        find_cpa_sample_code_file = "find $(pwd) -type f -name 'cpa_sample_code' 2>/dev/null"
        qat_dependency_packages = "echo y | yum install boost-build boost-devel boost-doc boost-examples " \
                                  "libnl3-devel libnl3-doc yasm openssl-devel"
        spr_work_around_cmd = ["export EXTRA_CXXFLAGS=-Wno-stringop-truncation",
                               "echo '/usr/local/lib' | sudo tee -a /etc/ld.so.conf", "mkdir -p /etc/default",
                               "mkdir -p /etc/udev/rules.d/", "mkdir -p /etc/ld.so.conf.d"]

        self._log.info("QAT Installtion in SPR platfrom")
        # Configuring the work around for SPR platform
        for cmd_item in spr_work_around_cmd:
            self._log.info("Executing work around command '{}' for QAT installation".format(cmd_item))
            common_content_object.execute_sut_cmd(cmd_item, cmd_item, self._command_timeout)

        # Installing dependency packates
        command_result = common_content_object.execute_sut_cmd(qat_dependency_packages,
                                                                  "Dependency package installation",
                                                                  self._command_timeout)
        self._log.debug("Dependency packages are installed sucessfully {}".format(command_result))

        # Configuring the QAT Tool if installed already uninstall
        command_result = common_content_object.execute_sut_cmd(configure_cmd, "run configure command",
                                                                  self._command_timeout, qat_folder_path)
        self._log.debug(
            "Configuring and Uninstall QAT Tool successfully if already installed {}".format(command_result))

        # make install  the QAT Tool
        command_result = common_content_object.execute_sut_cmd(make_cmd, "run make install command",
                                                                  self._command_timeout, qat_folder_path)
        self._log.debug("Install the QAT Tool in SUT {}".format(command_result))
        # make install samples the QAT Tool
        command_result = common_content_object.execute_sut_cmd(make_install_samples, "run make install command",
                                                                  self._command_timeout, qat_folder_path)
        self._log.debug("Install the Samples Tool with QAT {}".format(command_result))
        # find cpa_sample_code file from the build folder
        cpa_sample_file = common_content_object.execute_sut_cmd(find_cpa_sample_code_file,
                                                                   "find the cpa_sample_code file in build path",
                                                                   self._command_timeout, qat_folder_path + "/build")
        self._log.debug("Found cpa_sample_code file from build folder {} ".format(cpa_sample_file))
        if not cpa_sample_file:
            raise content_exceptions.TestFail("cpa_sample code file not found from build folder")
        self._log.info("QAT Tool installed successfully")

    def install_qat(self, qat_type, target_type=None, configure_spr_cmd=None, common_content_object=None):
        """
        This method installs QAT on sut by running below commands:
        1. tar -xvf ./QAT1.7.L.4.9.0-00008.tar.gz
        2. ./configure
        3. make
        4. make install
        5. make samples-install

        :return: None
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        self._log.info("Installing QAT")
        self._log.info("Enabling Proxy")
        self.enable_proxy(common_content_object)
        packges_required = "epel-release zlib-devel libnl3-devel boost-devel systemd-devel yasm lz4-devel elfutils-libelf-devel openssl-devel readline-devel"
        if target_type == "guest":
            qat_file_name = os.path.split(self._install_collateral.vm_qat_file_path)[-1].strip()
        else:
            qat_file_name = os.path.split(self._install_collateral.qat_file_path)[-1].strip()
        cmd_to_install_dep_pack = "yum -y install elfutils-libelf-devel libudev-devel --allowerasing --nobest --skip-broken"
        cmd_to_install_dev_tools = 'yum -y group install "Development Tools" --allowerasing'
        qat_folder_name = "QAT"
        if qat_type == "sriov":
            configure_cmd = "./configure --enable-icp-sriov={}".format(target_type)
        else:
            # configure_cmd = "./configure"
            configure_cmd = "./configure --enable-icp-sriov={}".format(target_type)

        make_command = "make; sync;"
        make_install_cmd = "make install; sync;"
        make_samples_install_cmd = "make samples-install; sync;"

        artifactory_name = qat_file_name
        qat_host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
        qat_host_path = qat_host_path.strip()
        # Copy the QAT file to SUT
        sut_folder_path = common_content_object.copy_zip_file_to_linux_sut(qat_folder_name, qat_host_path)
        sut_folder_path = sut_folder_path.strip()
        self._log.info("QAT file is extracted and copied to SUT path {}".format(sut_folder_path))

        # Install packages required for QAT
        # Installing Development tools
        command_result = common_content_object.execute_sut_cmd(cmd_to_install_dev_tools,
                                                               "Install development tools",
                                                               self._command_timeout)
        self._log.debug("Installation of 'Development Tools' is done successfully with output '{}'"
                        .format(command_result))

        # Install other packages required for QAT
        self.yum_virt_install(package_group=packges_required,
                              common_content_lib=common_content_object, flags="--nobest --skip-broken")

        # Install more packages required for QAT
        command_result = common_content_object.execute_sut_cmd(cmd_to_install_dep_pack, "Install require tools",
                                                                  self._command_timeout)
        self._log.debug("Installation of dependency packages is done successfully with output '{}'"
                        .format(command_result))

        # "and configure_spr_cmd is not None" ==> Added in below condition to ignore specific build method for SPR as issue fixed
        if self._platform == ProductFamilies.SPR and configure_spr_cmd is not None:
            self.spr_qat_installation(sut_folder_path, configure_spr_cmd=configure_spr_cmd,
                                      common_content_object=common_content_object)
        else:
            # Installing QAT Tool for other platforms
            # Configuring the QAT Tool
            command_result = common_content_object.execute_sut_cmd(configure_cmd, "run configure command",
                                                                      self._command_timeout, sut_folder_path)
            self._log.debug("Configuring the QAT Tool file successfully {}".format(command_result))
            # make and compiling the files in QAT Tool folder
            command_result = common_content_object.execute_sut_cmd(make_command, "run make command",
                                                                      self._command_timeout, sut_folder_path)
            self._log.debug("make and compiling the files QAT Tool folder {}".format(command_result))
            # make install command
            command_result = common_content_object.execute_sut_cmd(make_install_cmd, "run make Install command",
                                                                      self._command_timeout, sut_folder_path)
            self._log.debug("Installation of QAT make install is done successfully {}".format(command_result))

            # make samples-install command
            command_result = common_content_object.execute_sut_cmd(make_samples_install_cmd, "run make samples-Install command",
                                                                   self._command_timeout, sut_folder_path)
            self._log.debug("Installation of QAT make samples-install is done successfully {}".format(command_result))

    def install_qat_sriov_driver_tool_host(self, configure_spr_cmd=None, common_content_object=None):
        """
        This function installing the qat tool in sut
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        self.install_qat(qat_type="sriov", target_type="host", configure_spr_cmd=configure_spr_cmd, common_content_object=common_content_object)

    def install_qat_sriov_driver_tool_guest(self, configure_spr_cmd=None, common_content_object=None):
        """
        This function installing the qat tool in sut
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        self.install_qat(qat_type="sriov", target_type="guest", configure_spr_cmd=configure_spr_cmd, common_content_object=common_content_object)

    def install_qat_siov_driver_tool(self, configure_spr_cmd=None, common_content_object=None):
        """
        This function installing the qat tool in sut
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        self.install_qat(qat_type="siov", target_type="host", configure_spr_cmd=configure_spr_cmd, common_content_object=common_content_object)

    def install_qat_siov_driver_tool_guest(self, configure_spr_cmd=None, common_content_object=None):
        """
        This function installing the qat tool in sut
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        self.install_qat(qat_type="siov", target_type="guest", configure_spr_cmd=configure_spr_cmd, common_content_object=common_content_object)

    def get_qat_dir(self, common_content_object=None):
        """
        This function get the QAT tool installed directory path

        :return: The QAT directory path
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        self._log.info("Finding the QAT tool installed directory...")
        qat_dir = common_content_object.execute_sut_cmd(self.FIND_QAT_FOLDER_PATH, "find QAT path",
                                                           self._command_timeout).strip()
        self._log.debug("QAT Tool directory path '{}'".format(qat_dir))
        return qat_dir

    def uninstall_qat(self, qat_dir_path, common_content_object=None):
        """
        This function uninstall the QAT from the sut

        :raise: content_exception.TestFail if not uninstalled properly
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        self._log.info("Uninstalling the QAT Tool..")
        ret_qat_status = common_content_object.execute_sut_cmd(self.MAKE_UNINSTALL, "make uninstall cmd",
                                                                  self._command_timeout, qat_dir_path)
        self._log.debug("QAT Tool Uninstalled command results {}".format(ret_qat_status))
        if self.QAT_UNINSTALL_STR not in ret_qat_status:
            raise content_exceptions.TestFail("Failed to uninstall QAT tool")
        self._log.info("QAT is uninstalled")

    def spr_cpa_sample_code_workaround(self, common_content_object=None):
        """
        This function execute command in cscript command for SPR platform as workaround
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
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

    def execute_cpa_sample_code(self, cpa_sample_command, common_content_object=None):
        """
        This function execute the cpa_sample_code file to get the data movement in the sut

        :raise: raise content_exceptions.TestFail if not getting the file or getting error
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        find_cpa_sample_code_file = "find $(pwd) -type f -name 'cpa_sample_code' 2>/dev/null | grep QAT/build"
        self._log.info("Execute the command {}".format(cpa_sample_command))
        # While executing SPR Platform run the workaround
        try:
            if "esxi" not in self.os.os_type.lower():
                if self._platform == ProductFamilies.SPR:
                    self.spr_cpa_sample_code_workaround(common_content_object)
        except:
            pass
        # find cpa_sample_code file from the build folder
        cpa_sample_file_path = common_content_object.execute_sut_cmd(find_cpa_sample_code_file,
                                                                        "find the cpa_sample_code file in build path",
                                                                        self._command_timeout)
        self._log.info("Found cpa_sample_code file from build folder {} ".format(cpa_sample_file_path))
        if not cpa_sample_file_path:
            raise content_exceptions.TestFail("cpa_sample code file not found from build folder")
        build_path = os.path.split(cpa_sample_file_path)[:-1][0]
        self._log.info("Found cpa_sample_code file from build path {} ".format(build_path))
        sample_code_results = common_content_object.execute_sut_cmd(cpa_sample_command,
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

################################################From PRC team#########################################################
    def check_acce_device_esxi(self, acce_module_name, cpu_num, device_id, common_content_object=None,
                               is_driver_installed=False):
        """
         Purpose: Check accelerator device status
         Args:
             common_content_object object to common content class
             acce_module_name: this is accelerator device name, eg: 'qat', 'dlb', 'iadx'
             is_driver_installed: check driver installed or not
         Returns:
             No
         Raises:
             RuntimeError: If any errors
         Example:
             Simplest usage: Get CPU number in BIOS serial log
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        output = common_content_object.execute_sut_cmd("lspci -p | grep 8086:{}".format(device_id),
                                              "Execute lspci -p | grep 8086:{}".format(device_id),
                                              self._command_timeout,
                                              self.ROOT_PATH)
        if acce_module_name == 'qat':
            self.__detect_device_type_in_esxi(output, ['device_id', 'V'], 'qat', cpu_num)
            if is_driver_installed:
                self.__detect_device_type_in_esxi(output, ['device_id', 'V', 'qat'], 'qat', cpu_num)
        elif acce_module_name == 'dlb':
            self.__detect_device_type_in_esxi(output, ['device_id', 'V'], 'dlb', cpu_num)
            if is_driver_installed:
                self.__detect_device_type_in_esxi(output, ['device_id', 'V', 'dlb'], 'dlb', cpu_num)
        elif acce_module_name == 'iadx':
            self.__detect_device_type_in_esxi(output, ['device_id', 'V'], 'dsa', cpu_num)
            if is_driver_installed:
                self.__detect_device_type_in_esxi(output, ['device_id', 'V', 'iadx'], 'dsa', cpu_num)

    def qat_driver_install_esxi(self, common_content_object=None):
        """
          Purpose: To install QAT driver
          Args:
              No
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Install QAT driver
                  qat_driver_install_esxi
        """
        qat_folder_name = "QAT"
        if common_content_object is None:
            common_content_object = self._common_content_lib
        command_result = common_content_object.execute_sut_cmd("rm -rf /vmfs/volumes/datastore1/{}".format(qat_folder_name),
                                                               "Install development tools",
                                                               self._command_timeout)
        qat_file_name = os.path.split(self._install_collateral.qat_file_path_esxi)[-1].strip()
        qat_host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(qat_file_name)
        qat_host_path = qat_host_path.strip()
        # Copy the QAT file to SUT

        sut_folder_path = common_content_object.copy_zip_file_to_esxi(qat_folder_name, qat_host_path)
        sut_folder_path = sut_folder_path.strip()
        self._log.info("QAT file is extracted and copied to SUT path {}".format(sut_folder_path))

        # Install packages required for QAT
        # Installing Development tools
        try:
            cmand_out = "esxcfg-module -u qat"
            self._common_content_lib.execute_sut_cmd(cmand_out, "verify qat", 60)
        except:
            pass

        command_result = common_content_object.execute_sut_cmd(
                "esxcli software vib install -v /vmfs/volumes/datastore1/{}/vib20/qat/INT*.vib --no-sig-check ".format(qat_folder_name),
                "Installed: Intel-qat",
                self._command_timeout)
        if command_result is not None:
            self._log.info("Installed: Intel-qat Operation finished successfully with output '{}'"
                       .format(command_result))
        else:
            self._log.info("QAT driver install failed with output '{}'"
                            .format(command_result))
        cmand_reboot = "reboot"
        self._common_content_lib.execute_sut_cmd(cmand_reboot, "reboot the sut", 60)
        time.sleep(300)
        self.load_driver_esxi()
        self.check_acce_driver_esxi('qat')

    def get_qat_device_bdf_value(self, index):
        """
          Purpose: To install QAT driver
          Args:
              No
          Returns:
              qat bdf value
          Example:
              Simplest usage: get QAT bdf value
                  get_qat_device_bdf_value
        """
        qat_bdf_value = ""
        cmand_qat_list = "lspci -p | grep 8086:4940"
        qat_device_list_data = self._common_content_lib.execute_sut_cmd(cmand_qat_list, "check qat in sut", 60)
        self._log.info(qat_device_list_data)
        # qat_bdf_value = (re.sub('\s\s+', '*', qat_device_list_data)).split('*')[index].split(" ")[0]
        if qat_device_list_data is not None:
            qat_device_list = re.findall(r'\b([0-9a-fA-F]{4}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}.\d{1}\s*)',
                                         qat_device_list_data)
            qat_bdf_value = qat_device_list[index].strip()
            self._log.info(qat_bdf_value)
        return qat_bdf_value

    def uninstall_driver_esxi(self, acce_module_name, common_content_object=None):
        """
              Purpose: To uninstall accelerator device driver
              Args:
                  acce_module_name: this is accelerator device name, eg: 'qat', 'dlb', 'iadx'
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Uninstall accelerator device driver
                      uninstall_driver_esxi()
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib

        if acce_module_name == 'qat':
            try:
                command_result = common_content_object.execute_sut_cmd(
                    "esxcfg-module -u {}".format(acce_module_name),
                    "uninstall the module",
                    self._command_timeout)
                self._log.debug("Uninstalled module successfully with output '{}'".format(command_result))
            except:
                pass

            try:
                command_result = common_content_object.execute_sut_cmd(
                    "esxcli software vib remove -n {}".format(acce_module_name),
                    "uninstall the module",
                    self._command_timeout)
                self._log.debug("Uninstalled module successfully with output '{}'".format(command_result))
            except:
                pass

        elif acce_module_name == 'dlb':
            try:
                command_result = common_content_object.execute_sut_cmd("esxcfg-module -u dlb", "check for the driver",
                                                                       60)
                self._log.debug("Uninstalled module successfully with output '{}'".format(command_result))
            except:
                pass

            try:
                command_result = common_content_object.execute_sut_cmd("esxcli software component remove -n Intel-dlb",
                                                                       "uninstall driver", 60)
                self._log.debug("Uninstalled module successfully with output '{}'".format(command_result))
            except:
                pass


        elif acce_module_name == 'iadx':
            try:
                command_result = common_content_object.execute_sut_cmd(
                    "vmkload_mod --unload {}".format(acce_module_name),
                    "uninstall the module",
                    self._command_timeout)
                self._log.debug("Uninstalled module successfully with output '{}'".format(command_result))
            except:
                pass

            try:
                command_result = common_content_object.execute_sut_cmd(
                    "esxcli software vib remove --maintenance-mode -n {}".format(acce_module_name),
                    "remove the software componenet of the module",
                    self._command_timeout)
                self._log.debug("Uninstalled module successfully with output '{}'".format(command_result))
            except:
                pass

        cmand_reboot = "reboot;"
        self._common_content_lib.execute_sut_cmd(cmand_reboot, "reboot the sut", 60)
        time.sleep(300)
        self._log.info("Removed the {} driver of the module from sut successfully".format(acce_module_name))

    #############################################################################################################

    def __cc6_value_check(self, out):
        cpu_num = self.get_cpu_num()
        core_num = self.__get_core_num()
        line_list = out.strip().split('CC6')
        cc6_line_list = line_list[1].split('Core C-State Summary: Entry Counts')
        word_list = cc6_line_list[0].strip().split(',')
        value_list = []
        for word in word_list:
            value_list.append(word.strip())
        less_100_value_list = []
        for word in value_list:
            if word != '' and float(word) <= 100.00:
                less_100_value_list.append(word)
        cc6_num = 0
        for word in less_100_value_list:
            if float(word) >= 70:
                cc6_num += 1
        if cc6_num != cpu_num * core_num:
            self._log.err('Not all core CC6 Residency value more than 70%')
            raise Exception('Not all core CC6 Residency value more than 70%')

    def __check_all_device_wq(self, cpu_num, device_num, out):
        line_list = out.strip().split('\n')
        dsa_enable_num = 0
        for line in line_list:
            if '"state":"enabled"' in line:
                dsa_enable_num += 1
        if dsa_enable_num != cpu_num * device_num * 9:
            self._log.err('Not all dsa grouped_workqueues are enabled')
            raise Exception('Not all dsa grouped_workqueues are enabled')

    def __check_enabled_wq_num(self, out):
        line_list = out.strip().split('Enabling')
        work_queues_list = line_list[2].split('enabled')
        queues_word_list = work_queues_list[1].strip().split(' ')
        return queues_word_list[0]

    def __check_error(self, err):
        if err != '':
            self._log.err(err)
            raise Exception(err)

    def __check_device_in_vm(self, out, vf_num, check_key):
        dev_num = 0
        line_list = out.strip().split('\n')
        for line in line_list:
            if check_key in line:
                dev_num += 1
        if dev_num != vf_num:
            self._log.err("Can't detact attached device")
            raise Exception("Can't detact attached device")

    def __cpu_idle_value_check(self, out):
        thread_num = self.__get_thread_num()
        line_list = out.strip().split('CPU Idle')
        cpu_idle_list = line_list[1].split('CPU P-State/Frequency Summary: Total Samples Received')
        cpu_idle_list = cpu_idle_list[0].strip().split(',')
        word_list = []
        for word in cpu_idle_list:
            word_list.append(word.strip())
        print(word_list)
        cpu_idle_value_less_100_list = []
        for word in word_list:
            if word != '' and float(word) <= 100.00:
                cpu_idle_value_less_100_list.append(word)
        cpu_idle_num = 0
        for word in cpu_idle_value_less_100_list:
            if float(word) >= 70:
                cpu_idle_num += 1
        if cpu_idle_num != thread_num:
            self._log.err('Not all thread cpu idle value more than 70%')
            raise Exception('Not all thread cpu idle value more than 70%')

    def __check_driver_installed_in_esxi(self, acce_module_name, common_content_object=None):
        """
        To check if driver is loaded
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        if acce_module_name == "qat":
            cmd = "vmkload_mod --list | grep {}".format(acce_module_name)
            #output will be "qat_dvx                    9     4024"

            command_result = common_content_object.execute_sut_cmd(
                cmd, "check for the accelerator driver",
                self._command_timeout)
            regex_search = re.search(r"qat_dvx\s+\d+\s+\d+", command_result, re.M)
            if not regex_search:
                raise content_exceptions.TestError("Could not get the info of QAT driver")
            self._log.debug("Driver found successfully with output '{}'"
                            .format(regex_search))

    def __detect_device_type_in_esxi(self, out, key_list, acce_ip, cpu_num):
        qat_line_list = out.strip().split('\n')
        for key in key_list:
            key_num = 0
            for line in qat_line_list:
                if key in line:
                    key_num += 1
            if acce_ip == 'qat':
                if key_num != cpu_num * self.QAT_DEVICE_NUM:
                    self._log.err('Not all device are recognized')
                    raise Exception('Not all device are recognized')
            elif acce_ip == 'dlb':
                if key_num != cpu_num * self.DLB_DEVICE_NUM:
                    self._log.err('Not all device are recognized')
                    raise Exception('Not all device are recognized')
            elif acce_ip == 'dsa':
                if key_num != cpu_num * self.DSA_DEVICE_NUM:
                    self._log.err('Not all device are recognized')
                    raise Exception('Not all device are recognized')

    def __get_core_num(self, common_content_object=None):
        """
              Purpose: Get current SUT core numbers
              Args:
                  No
              Returns:
                  Yes: return core numbers
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Get current SUT core numbers
                        __get_core_num()
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        command_result = common_content_object.execute_sut_cmd(
            "lscpu",
            "lscpu",
            self._command_timeout)
        line_list = command_result.strip().split('\n')
        for line in line_list:
            word_list = line.split()
            if word_list[0] == 'Core(s)':
                core_num = int(word_list[3])
                return core_num

    def __get_qat_pci_id(self, dev_id):
        """
              Purpose: Modify the format of QAT device ID
              Args:
                  dev_id : QAT device ID -->'0000:6d:00.0'
              Returns:
                  Yes  --> '0000_6b_00_1'
              Example:
                  Simplest usage: Modify the format of QAT device ID
                        __get_qat_pci_id(0000:6d:00.0)
                        return '0000_6b_00_1'
        """
        change_li = []
        word_list_split = dev_id.split(':')  # [' 0000', '6b', '00.1']
        word_list_change = word_list_split[2].split('.')  # ['00', '1']
        change_li.append(word_list_split[0])  # [' 0000]
        change_li.append(word_list_split[1])  # [' 0000', '6b']
        change_li.append(word_list_change[0])  # [' 0000', '6b','00']
        change_li.append(word_list_change[1])  # [' 0000', '6b','00', '1']
        i = 1
        while i < len(change_li):
            change_li.insert(i, '_')  # [' 0000', '_', '6b', '_', '00', '_', '1']
            i += 2
        change_str = ''.join(change_li)  # ' 0000_6b_00_1'
        change_str = change_str.strip()  # '0000_6b_00_1'
        return change_str

    def __get_qat_unbind_path(self, dev_id):
        """
              Purpose: Modify the format of QAT device ID
              Args:
                  dev_id : QAT device ID -->'0000:6d:00.0'
              Returns:
                  Yes  --> '0000\:6b\:00.0'
              Example:
                  Simplest usage: Modify the format of QAT device ID
                        __get_qat_unbind_path(0000:6d:00.0)
                        return '0000\:6b\:00.0'
        """
        word_split = dev_id.split(':')  # [' 0000', '6b', '00.0']
        i = 1
        while i < len(word_split):
            word_split.insert(i, '\\:')  # [' 0000', '\\:', '6b', '\\:', '00.0']
            i += 2
        change_word = "".join(word_split)  # ' 0000\:6b\:00.0'
        change_word = change_word.strip()  # '0000\:6b\:00.0'
        return change_word

    def __get_thread_num(self, common_content_object=None):
        """
              Purpose: Get current SUT core numbers
              Args:
                  No
              Returns:
                  Yes: return core numbers
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Get current SUT core numbers
                        __get_core_num()
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        command_result = common_content_object.execute_sut_cmd(
            "lscpu",
            "lscpu",
            self._command_timeout)

        line_list = command_result.strip().split('\n')
        for line in line_list:
            word_list = line.split()
            if word_list[0] == 'CPU(s):':
                thread_num = int(word_list[1])
                return thread_num

    def __qat_asym_config(self, common_content_object=None):
        """
              Purpose: Modify QAT asymmetric encrypted files config
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Modify QAT asym metric encrypted files config
                        __qat_asym_config()
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        cpu_num = self.get_cpu_num()
        for i in range(cpu_num*self.QAT_DEVICE_NUM):
            command_result = common_content_object.execute_sut_cmd(
                "sed -i 's/ServicesEnabled.*/ServicesEnabled = asym;dc/g' /etc/4xxx_dev{}.conf".format(i),
                "sed -i 's/ServicesEnabled.*/ServicesEnabled = asym;dc/g' /etc/4xxx_dev{}.conf".format(i),
                self._command_timeout)
            self._log.debug("command_result for qat asym config  {}".format(command_result))
        self.restart_qat_service()

    def __qat_asym_config_clr(self, common_content_object=None):
        """
              Purpose: Clear QAT asymmetric encrypted config files
              Args:
                  No
              Returns:
                  No
              Example:
                  Simplest usage: Clear QAT asymmetric encrypted config files
                        __qat_asym_config_clr()
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        cpu_num = self.get_cpu_num()
        for i in range(cpu_num*self.QAT_DEVICE_NUM):
            command_result = common_content_object.execute_sut_cmd(
                "sed -i 's/ServicesEnabled = asym;dc/ServicesEnabled = sym;dc/g' /etc/4xxx_dev{}.conf".format(i),
                "sed -i 's/ServicesEnabled = asym;dc/ServicesEnabled = sym;dc/g' /etc/4xxx_dev{}.conf".format(i),
                self._command_timeout)
            self._log.debug("command_result for qat asym config  {}".format(command_result))

        self.restart_qat_service()

    def __qat_mdev_config(self, common_content_object=None):
        """
              Purpose: Modify QAT SIOV config files
              Args:
                  No
              Returns:
                  No
              Example:
                  Simplest usage: Modify QAT SIOV config files
                        __qat_mdev_config()
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        cpu_num = self.get_cpu_num()
        for i in range(cpu_num*self.QAT_DEVICE_NUM):
            command_result = common_content_object.execute_sut_cmd(
                "sed -i 's/NumberAdis = 0/NumberAdis = 16/g' /etc/4xxx_dev{}.conf".format(i),
                "sed -i 's/NumberAdis = 0/NumberAdis = 16/g' /etc/4xxx_dev{}.conf".format(i),
                self._command_timeout)
            self._log.debug("command_result for qat mdev config  {}".format(command_result))
        self.qat_service_stop_start()

    def __qat_mdev_config_clr(self, common_content_object=None):
        """
              Purpose: Clear QAT SIOV config files
              Args:
                  No
              Returns:
                  No
              Example:
                  Simplest usage: Clear QAT SIOV config files
                        __qat_mdev_config_clr()
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        cpu_num = self.get_cpu_num()
        for i in range(cpu_num*self.QAT_DEVICE_NUM):
            command_result = common_content_object.execute_sut_cmd(
                "sed -i 's/NumberAdis = 16/NumberAdis = 0/g' /etc/4xxx_dev{}.conf".format(i),
                "sed -i 's/NumberAdis = 16/NumberAdis = 0/g' /etc/4xxx_dev{}.conf".format(i),
                self._command_timeout)
        self.restart_qat_service()

    def __qat_shim_config(self, common_content_object=None):
        """
              Purpose: Modify QAT SSL config files
              Args:
                  No
              Returns:
                  No
              Example:
                  Simplest usage: Modify QAT SSL config files
                        __qat_shim_config()
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        cpu_num = self.get_cpu_num()
        for i in range(cpu_num*self.QAT_DEVICE_NUM):
            command_result = common_content_object.execute_sut_cmd(
                "sed -i 's/\[SSL\]/\[SHIM\]/g' /etc/4xxx_dev{}.conf".format(i),
                "sed -i 's/\[SSL\]/\[SHIM\]/g'/etc/4xxx_dev{}.conf".format(i),
                self._command_timeout)
            self._log.debug("command_result {}".format(command_result))
            command_result = common_content_object.execute_sut_cmd(
                "sed -i 's/NumberCyInstances = 3/NumberCyInstances = 1/g' /etc/4xxx_dev{}.conf".format(i),
                "sed -i 's/NumberCyInstances = 3/NumberCyInstances = 1/g' /etc/4xxx_dev{}.conf".format(i),
                self._command_timeout)
            self._log.debug("command_result {}".format(command_result))
            command_result = common_content_object.execute_sut_cmd(
                "sed -i 's/NumberDcInstances = 2/NumberDcInstances = 1/g' /etc/4xxx_dev{}.conf".format(i),
                "sed -i 's/NumberDcInstances = 2/NumberDcInstances = 1/g' /etc/4xxx_dev{}.conf".format(i),
                self._command_timeout)
            self._log.debug("command_result {}".format(command_result))
            command_result = common_content_object.execute_sut_cmd(
                "sed -i 's/NumProcesses = 1/NumProcesses = 16/g' /etc/4xxx_dev{}.conf".format(i),
                "sed -i 's/NumProcesses = 1/NumProcesses = 16/g' /etc/4xxx_dev{}.conf".format(i),
                self._command_timeout)
            self._log.debug("command_result {}".format(command_result))
            command_result = common_content_object.execute_sut_cmd(
                "sed -i 's/LimitDevAccess = 0/LimitDevAccess = 1/g' /etc/4xxx_dev{}.conf".format(i),
                "sed -i 's/LimitDevAccess = 0/LimitDevAccess = 1/g' /etc/4xxx_dev{}.conf".format(i),
                self._command_timeout)
            self._log.debug("command_result {}".format(command_result))
        self.restart_qat_service()

    def __qat_shim_config_clr(self, common_content_object=None):
        """
              Purpose: Clear QAT SSL config files
              Args:
                  No
              Returns:
                  No
              Example:
                  Simplest usage: Clear QAT SSL config files
                        __qat_shim_config_clr()
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        cpu_num = self.get_cpu_num()
        for i in range(cpu_num*self.QAT_DEVICE_NUM):
            command_result = common_content_object.execute_sut_cmd(
                "sed -i 's/ServicesEnabled = asym;dc/ServicesEnabled = sym;dc/g' /etc/4xxx_dev{}.conf".format(i),
                "sed -i 's/ServicesEnabled = asym;dc/ServicesEnabled = sym;dc/g' /etc/4xxx_dev{}.conf".format(i),
                self._command_timeout)
            self._log.debug("command_result for qat asym config  {}".format(command_result))
            self.sut.execute_shell_cmd(f'sed -i "s/\[SHIM\]/\[SSL\]/g" /etc/4xxx_dev{i}.conf', timeout=60)
            self.sut.execute_shell_cmd(f'sed -i "s/NumberCyInstances = 1/NumberCyInstances = 3/g" /etc/4xxx_dev{i}.conf',
                                  timeout=60)
            self.sut.execute_shell_cmd(f'sed -i "s/NumberDcInstances = 1/NumberDcInstances = 2/g" /etc/4xxx_dev{i}.conf',
                                  timeout=60)
            self.sut.execute_shell_cmd(f'sed -i "s/NumProcesses*/NumProcesses = 1/g" /etc/4xxx_dev{i}.conf', timeout=60)
            self.sut.execute_shell_cmd(f'sed -i "s/LimitDevAccess = 1/LimitDevAccess = 0/g" /etc/4xxx_dev{i}.conf',
                                  timeout=60)
        self.restart_qat_service()

################################################From PRC team#########################################################
