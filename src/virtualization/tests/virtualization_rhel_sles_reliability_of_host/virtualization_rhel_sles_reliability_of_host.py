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
# treaty provisions. No part of the Material may Ibe used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or disclosed
# in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
#################################################################################

import sys
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_exceptions import *
from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger
from src.lib import content_exceptions
from src.lib.content_artifactory_utils import ContentArtifactoryUtils
from src.lib.mlc_utils import MlcUtils
from src.ras.lib.ras_upi_util import RasUpiUtil


class VirtualizationRhelSlesReliabilityOfHost(VirtualizationCommon):
    """
    Phoenix ID: 18014073847
    The purpose of this test case is making sure the creation of VMs guests on KVM using Virt-Manager.
    1. Install virt-install if not present.
    2. Copy RHEL ISO image to SUT under '/var/lib/libvirt/images'.
    4. Create VM.
    5. Verify VM is running.
    """
    TEST_CASE_ID = ["p18014073847", "Virtualization_Rhel_Sles_Reliability_Of_Host"]
    STORAGE_VOLUME = ["/home"]
    STEP_DATA_DICT = {
        1: {'step_details': "Create the VM machine names.",
            'expected_results': "VM machine names created successfully"},
        2: {'step_details': "Install stress Tool on SUT(Libquantum, Crunch, Phoronix).",
            'expected_results': "Stress Tool Installed on SUT successfully"},
        3: {'step_details': "Create thread to execute stress Test on VM(Libquantum, Crunch, Phoronix)",
            'expected_results': " Stress Test on VM started successfully"},
        4: {'step_details': "Check if VM is alive",
            'expected_results': "VM OS is working fine and stable"},
        5: {'step_details': "Check if SUT is alive",
            'expected_results': "SUT OS is working fine and stable"},
        }
    BIOS_CONFIG_FILE = "virtualization_rhel_sles_reliability_of_host.cfg"
    NUMBER_OF_VMS = [VMs.RHEL] * 8
    VM_TYPE = "RHEL"
    TEST_RUN_TIME = 7200
    CMD_TO_START_CRUNCH_STRESS_ON_SUT = "./crunch-static-102 -e 0 -e 1 -e 2 -e 8 -e 9 -e 11 -e 13 -e 14 -e 16 -e " \
                                        "23 -e 25 -e 26 -e 28 -e 29 -e 30"
    LIST_OF_PHORONIX_DEPENDENCY_PKG = ["php*", "mpich", "mpich-*", "openmpi", "openmpi-devel", "libgfortran", "gcc-gfortran",
                                       "compat-*", "php-json", "expect"]
    LIST_OF_PHORONIX_DEPENDENCY_TOOL = ["gcc", "gcc-c++", "make", "autoconf", "automake", "glibc-*", "patch"]
    LIST_OF_PHORONIX_WORKLOAD_TOOL = ["bzip2", "php-cli", "php-pecl-*", "php-pdo", "php-xml"]
    WAIT_TIME_FOR_TOOL_RUN_SEC = 10
    PHORONIX_FILE_NAME = r"phoronix-test-suite-7.6.0.tar.gz"
    PHORONIX_PATH = r"phoronix-test-suite/"
    CMD_TO_CHECK_RUNNING_TOOL = "ps -ef| grep {}"
    WAIT_TIME_FOR_TOOL = 200
    PHORONIX_EXEC_CMD = "FORCE_TIMES_TO_RUN=20 phoronix-test-suite batch-benchmark pts/npb-1.2.4"
    CRUNCH_STR = "crunch"
    PHORONIX_STR = "phoronix"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationCentOsKvmScalableIovGen4NicStress2Vm object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(VirtualizationRhelSlesReliabilityOfHost, self).__init__(test_log, arguments, cfg_opts)
        self._cfg_opts = cfg_opts
        self._log = test_log
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        if self.os.os_type != OperatingSystems.LINUX:
            raise TestNotImplementedError("Not implemented for {} OS".format(self.os.os_type))
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self._install_collateral = InstallCollateral(test_log, self.os, cfg_opts)
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)
        self._mlc_runtime = self._common_content_configuration.memory_mlc_run_time()
        self._mlc_utils = MlcUtils(self._log)
        self._artifactory_obj = ContentArtifactoryUtils(self._log, self.os, self._common_content_lib, cfg_opts)

    def prepare(self):

        self.bios_util.load_bios_defaults()
        self.bios_util.set_bios_knob(bios_config_file=self.BIOS_CONFIG_FILE)
        self._common_content_lib.perform_os_reboot(self.reboot_timeout)
        self.bios_util.verify_bios_knob(bios_config_file=self.BIOS_CONFIG_FILE)
        self._vm_provider.create_bridge_network("virbr0")

    def execute(self):
        #  To check and enable intel_iommu by using grub menu
        if not self.enable_intel_iommu_by_kernel():
            raise content_exceptions.TestFail("Unable to enable Intel IOMMU by kernel")
        self._install_collateral.screen_package_installation()
        socket, core_socket, threads_per_core = self.get_cpu_core_info()
        total_cpus = socket * core_socket * threads_per_core
        cpus_per_vm = int(total_cpus / len(self.NUMBER_OF_VMS))
        for index in range(len(self.STORAGE_VOLUME)):
            pool_id = "Storage" + "_" + str(index)
            self.LIST_OF_POOL.append(pool_id)
            mount_dev = self.STORAGE_VOLUME[index]
            self.LIST_OF_MOUNT_DEVICE.append(mount_dev)
            if self._vm_provider.find_if_storage_pool_exist(pool_id):
                self._vm_provider.delete_storage_pool(pool_id)
            self._vm_provider.create_storage_pool(pool_id, mount_dev)
        self._test_content_logger.start_step_logger(1)
        for index in range(len(self.NUMBER_OF_VMS)):
            vm_name = self.NUMBER_OF_VMS[index] + "_" + str(index)
            self._log.info(" Creating VM:{} on CentOS".format(vm_name))
            self._vm_provider.destroy_vm(vm_name)
            self.LIST_OF_VM_NAMES.append(vm_name)
            free_storage_pool = self._vm_provider.find_available_storage_pool(self.LIST_OF_POOL, self.VM_TYPE)
            end_index = (total_cpus - 1) - (index * cpus_per_vm)
            # start_index = end_index - ((vm_index + 1) * cpus_per_vm) + 1
            start_index = end_index - cpus_per_vm + 1
            cpu_list = "{}-{}".format(start_index, end_index)
            self.create_vm_generic(vm_name, self.VM_TYPE, vm_parallel="yes", vm_create_async=True,
                                   mac_addr=True, pool_id=free_storage_pool, pool_vol_id=None,
                                   cpu_core_list=cpu_list, nw_bridge="virbr0")
        self._test_content_logger.end_step_logger(1, return_val=True)
        self.create_vm_wait()
        time.sleep(self.VM_WAIT_TIME)
        for index in range(len(self.NUMBER_OF_VMS)):
            vm_name = self.NUMBER_OF_VMS[index] + "_" + str(index)
            self.verify_vm_functionality(vm_name, self.NUMBER_OF_VMS[index])
            vm_os_obj = self.create_vm_host(vm_name, self.NUMBER_OF_VMS[index])
            common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            install_collateral_vm_obj = InstallCollateral(self._log, vm_os_obj, self._cfg_opts)
            repo_folder_path = self._common_content_configuration.get_yum_repo_name(self._sut_os, self.VM_TYPE)
            self._enable_yum_repo_in_vm(vm_os_obj, repo_folder_path)
            vm_ras_util = RasUpiUtil(vm_os_obj, self._log, self._cfg, common_content_lib_vm_obj)
            self.get_yum_repo_config(vm_os_obj, common_content_lib_vm_obj, os_type="centos",machine_type="vm")
            install_collateral_vm_obj.screen_package_installation()
            self._test_content_logger.start_step_logger(2)
            self._log.info("Install Crunch tool on VM:{}".format(vm_name))
            crunch_tool_path = install_collateral_vm_obj.install_crunch_tool()
            self._log.info("Install Libquantum tool on VM:{}".format(vm_name))
            libqunatum_tool_path = vm_ras_util.install_libquantum_tool()
            self._log.info("Installing phoronix dependency packages: {} /n {}".format(
                self.LIST_OF_PHORONIX_DEPENDENCY_PKG, self.LIST_OF_PHORONIX_DEPENDENCY_TOOL))
            for package in self.LIST_OF_PHORONIX_DEPENDENCY_PKG:
                common_content_lib_vm_obj.execute_sut_cmd("yum install -y {};echo y".format(package),
                                                          "installaing phoronix dependency pkg", self._command_timeout)
            for tool in self.LIST_OF_PHORONIX_DEPENDENCY_TOOL:
                common_content_lib_vm_obj.execute_sut_cmd("yum install -y {};echo y".format(tool),
                                                          "installaing phoronix dependency tool", self._command_timeout)
            self.install_phoronix_tool_on_vm(vm_name, vm_os_obj)
            self.configure_phoronix_on_vm(vm_name, vm_os_obj, common_content_lib_vm_obj)
            self._test_content_logger.end_step_logger(2, return_val=True)
            self._test_content_logger.start_step_logger(3)
            vm_ras_util.execute_libquantum_tool(libqunatum_tool_path)
            self.execute_crunch_tool(vm_os_obj, crunch_tool_path, common_content_lib_vm_obj)
            self.execute_phoronix_on_vm(vm_os_obj, common_content_lib_vm_obj)
            self._test_content_logger.end_step_logger(3, return_val=True)
        time.sleep(self.TEST_RUN_TIME)
        self._test_content_logger.start_step_logger(4)
        for index in range(len(self.NUMBER_OF_VMS)):
            self._log.info("Verifying VM after stress test completed")
            vm_name = self.NUMBER_OF_VMS[index] + "_" + str(index)
            self.verify_vm_functionality(vm_name, self.NUMBER_OF_VMS[index])
        self._test_content_logger.end_step_logger(4, return_val=True)
        self._test_content_logger.start_step_logger(5)
        if not self.os.is_alive():
            self._log.error("System is not alive")
            raise content_exceptions.TestFail("System is not alive")
        self._test_content_logger.end_step_logger(5, return_val=True)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationRhelSlesReliabilityOfHost, self).cleanup(return_status)

    def execute_crunch_tool(self, vm_os_obj, tool_path, common_content_lib_vm):
        """
        This Method to install crunch tool and execute it.

        :raise content_exception.
        """
        self._log.info("Crunch tool path: {}".format(tool_path))
        vm_os_obj.execute_async(self.CMD_TO_START_CRUNCH_STRESS_ON_SUT, tool_path)

        # Wait time for tool run
        time.sleep(self.WAIT_TIME_FOR_TOOL_RUN_SEC)

        crunch_stress_output = common_content_lib_vm.execute_sut_cmd(
            sut_cmd=self.CMD_TO_CHECK_RUNNING_TOOL.format(self.CRUNCH_STR),
            cmd_str=self.CMD_TO_CHECK_RUNNING_TOOL.format(self.CRUNCH_STR), execute_timeout=self._command_timeout)
        self._log.info("{} output to check crunch tool is running or not : {}".format(
            self.CMD_TO_CHECK_RUNNING_TOOL.format(self.CRUNCH_STR), crunch_stress_output))
        if self.CRUNCH_STR not in crunch_stress_output:
            raise content_exceptions.TestFail("Crunch tool is not executing")
        self._log.info("Crunch Tool Successfully Started")

    def install_phoronix_tool_on_vm(self, vm_name, vm_os_obj):
        """
        This Method to install phoronix tool on vm.

        :raise content_exception.
        """

        self._log.info("Install Phoronix tool to the VM:{}".format(vm_name))
        host_folder_path = self._artifactory_obj.download_tool_to_automation_tool_folder(self.PHORONIX_FILE_NAME)
        path = vm_os_obj.copy_local_file_to_sut(source_path=host_folder_path, destination_path=self.ROOT_PATH)
        vm_os_obj.execute("tar xvzf {}".format(self.PHORONIX_FILE_NAME), self._command_timeout, cwd=self.ROOT_PATH)
        self._log.info("PHORONIX tool Successfully Installed")
        return path

    def configure_phoronix_on_vm(self, vm_name, vm_os_obj, common_content_lib_vm):
        """
        This Method to configure phoronix tool on vm.

        :raise content_exception.
        """
        phoronix_npb_cmds = ["phoronix-test-suite install-dependencies pts/npb-1.2.4",
                             "phoronix-test-suite batch-install pts/npb-1.2.4",
                             "phoronix-test-suite validate-test-suite pts/npb-1.2.4"]
        self._log.info("Configuring Phoronix suite on VM:{}".format(vm_name))
        self._log.info("Installing phoronix package: {}".format(self.LIST_OF_PHORONIX_WORKLOAD_TOOL))
        for tool in self.LIST_OF_PHORONIX_WORKLOAD_TOOL:
            common_content_lib_vm.execute_sut_cmd("yum install -y {};echo y".format(tool),
                                                  "installaing phoronix dependency tool", self._command_timeout)
        common_content_lib_vm.execute_sut_cmd("tar -xzf ./mpi.tar.gz -C /", "command to unzip mpi tar",
                                              self._command_timeout, cmd_path=self.PHORONIX_PATH)
        common_content_lib_vm.execute_sut_cmd("echo 'export PATH=$PATH:/nfs/mpich3/bin' >> ~/.bashrc",
                                              "command to export path to mpi",
                                              self._command_timeout)
        common_content_lib_vm.execute_sut_cmd("./install-sh", "installing phoronix tool",
                                              self._command_timeout, cmd_path=self.PHORONIX_PATH)
        self._log.info("Executing Phoronix Network Setup")
        host_folder_path = self._artifactory_obj.download_tool_to_automation_tool_folder("phoronix_network_setup.sh")
        vm_os_obj.copy_local_file_to_sut(source_path=host_folder_path, destination_path=self.ROOT_PATH)
        common_content_lib_vm.execute_sut_cmd("chmod 777 phoronix_network_setup.sh",
                                              "change permissions for phoronix network mode file",
                                              self._command_timeout)
        common_content_lib_vm.execute_sut_cmd("./phoronix_network_setup.sh", "executing network mode",
                                              self._command_timeout)
        time.sleep(self.WAIT_TIME_FOR_TOOL)
        common_content_lib_vm.execute_sut_cmd("rm -rf /var/lib/phoronix-test-suite",
                                              "executing rm -rf /var/lib/phoronix-test-suite",
                                              self._command_timeout)
        common_content_lib_vm.execute_sut_cmd("tar -xvf home.phoronix-test-suite.tar -C /root/",
                                              "executing tar -xvf home.phoronix-test-suite.tar -C /root/",
                                              self._command_timeout, cmd_path=self.PHORONIX_PATH)
        common_content_lib_vm.execute_sut_cmd("tar -xvf home.phoronix-test-suite.tar -C /var/lib/",
                                              "executing tar -xvf home.phoronix-test-suite.tar -C /var/lib/",
                                              self._command_timeout, cmd_path=self.PHORONIX_PATH)
        common_content_lib_vm.execute_sut_cmd("mv /var/lib/.phoronix-test-suite /var/lib/phoronix-test-suite",
                                              "executing mv /var/lib/.phoronix-test-suite /var/lib/phoronix-test-suite",
                                              self._command_timeout)
        common_content_lib_vm.execute_sut_cmd("phoronix-test-suite enterprise-setup",
                                              "executing phoronix-test-suite enterprise-setup",
                                              self._command_timeout)
        self._log.info("Set phoronix in batch-mode")
        host_folder_path = self._artifactory_obj.download_tool_to_automation_tool_folder("phoronix_batch_mode.sh")
        vm_os_obj.copy_local_file_to_sut(source_path=host_folder_path, destination_path=self.ROOT_PATH)
        common_content_lib_vm.execute_sut_cmd("chmod 777 phoronix_batch_mode.sh",
                                              "change permissions for phoronix batch mode file",
                                              self._command_timeout)
        common_content_lib_vm.execute_sut_cmd("./phoronix_batch_mode.sh", "executing ./phoronix_batch_mode.sh",
                                              self._command_timeout)
        time.sleep(self.WAIT_TIME_FOR_TOOL)
        # Validating Phoronix nbp test suite
        for cmd in phoronix_npb_cmds:
            common_content_lib_vm.execute_sut_cmd(cmd, "executing {}".format(cmd), self._command_timeout)
        self._log.info("Successfully configured Phoronix test suite on VM:{}".format(vm_name))

    def execute_phoronix_on_vm(self, vm_os_obj, common_content_lib_vm):
        """
        This Method to execute phoronix tool on vm.

        :raise content_exception.
        """
        self._log.info("Phoronix tool path: {}".format(self.PHORONIX_PATH))
        vm_os_obj.execute_async(self.PHORONIX_EXEC_CMD, self.ROOT_PATH)
        # Wait time for tool run
        time.sleep(self.WAIT_TIME_FOR_TOOL_RUN_SEC)
        phoronix_stress_output = common_content_lib_vm.execute_sut_cmd(
            sut_cmd=self.CMD_TO_CHECK_RUNNING_TOOL.format(self.PHORONIX_STR),
            cmd_str=self.CMD_TO_CHECK_RUNNING_TOOL.format(self.PHORONIX_STR), execute_timeout=self._command_timeout)
        self._log.info("{} output to check crunch tool is running or not : {}".format(
            self.CMD_TO_CHECK_RUNNING_TOOL.format(self.PHORONIX_STR), phoronix_stress_output))
        if self.PHORONIX_STR not in phoronix_stress_output:
            raise content_exceptions.TestFail("Phoronix tool is not executing")
        self._log.info("Phoronix Tool Successfully Started")


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationRhelSlesReliabilityOfHost.main()
             else Framework.TEST_RESULT_FAIL)
