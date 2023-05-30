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
# property right is granted to or conferred upon you b.y disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
#################################################################################
import os
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


class VirtualizationSGXCoExistence(VirtualizationCommon):
    """
    This Test case verifies When SGX feature is enabled,  Windows Hyper-V,
    Linux KVM/Xen VMMs shouldn't have any issues with CPU and IO virtualization.
    """
    TEST_CASE_ID = "P18014074994"
    TEST_CASE_DETAILS = ["P18014074994",
                         "PI_Virtualization_SGX co-existence_L"]
    STEP_DATA_DICT = {
        1: {'step_details': "Install and verify Bios knobs for SGX",
            'expected_results': "Bios knobs installed and verified successfully'"},
        2: {'step_details': "",
            'expected_results': ""},
        3: {'step_details': "Create CentOS VM's VMM",
            'expected_results': "VM's Created Successfully"},
        4: {'step_details': "",
            'expected_results': ""}
    }

    BIOS_CONFIG_FILE = "pi_virtualization_sgx_co_existence_l.cfg"
    NUMBER_OF_VMS = [VMs.CENTOS] * 1
    VM_TYPE = "CENTOS"
    COMMON_TIMEOUT = 10
    VM=[VMs.CENTOS]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationSGXCoExistence object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(VirtualizationSGXCoExistence, self).__init__(test_log, arguments, cfg_opts)
        self._cfg_opts = cfg_opts
        self._log = test_log
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self._install_collateral = InstallCollateral(test_log, self.os, cfg_opts)

    def prepare(self):
        """
        This function sets the bios knob required for enabling SGX.
        """
        self._test_content_logger.start_step_logger(1)
        super(VirtualizationSGXCoExistence, self).prepare()
        sgx_bios_knobs = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   self.BIOS_CONFIG_FILE)
        self.set_and_verify_bios_knobs(sgx_bios_knobs)
        self._test_content_logger.end_step_logger(1, True)
        self._vm_provider.create_bridge_network("virbr0")

    def execute(self):
        """
        This function executes the following:
            1. Downloads sgx tool and sgx bin file from artifactory
            2. Installs the tools on SUT.
            3. Creates CEntos VM with SGX enabled
            4. Verifies if SGX is present on the VM.
        """
        sgx_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
            "sgx_rpm_local_repo.tgz")
        self.os.copy_local_file_to_sut(sgx_file_path, self.ROOT_PATH)
        sgx_bin_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
            "sgx_linux_x64_sdk_2.17.100.3.bin")
        self.os.copy_local_file_to_sut(sgx_bin_file_path, self.ROOT_PATH)
        self._install_collateral.yum_install("yum-utils.noarch")

        self._common_content_lib.execute_sut_cmd(f"tar -xzf /root/sgx_rpm_local_repo.tgz --directory "
                                                 f"/root", cmd_str="Executing untar",
                                                 execute_timeout=self.COMMON_TIMEOUT)
        self._common_content_lib.execute_sut_cmd(f"yum-config-manager --add-repo "
                                                 f"file:///root/sgx_rpm_local_repo/",
                                                 cmd_str="Executing yum-config-manager --add-repo "
                                                         f"file:///root/sgx_rpm_local_repo/",
                                                 execute_timeout=self.COMMON_TIMEOUT)
        self._install_collateral.yum_install(
            "libsgx-epid libsgx-uae-service libsgx-launch libsgx-urts" + " --nogpgcheck", cmd_path=f"/root")
        self._common_content_lib.execute_sut_cmd("chmod 777 /root/sgx_linux_x64_sdk_2.17.100.3.bin",
                                                 "chmod 777 /root/sgx_linux_x64_sdk_2.17.100.3.bin",
                                                 self._command_timeout)
        self._common_content_lib.execute_sut_cmd(f"./sgx_linux_x64_sdk_2.17.100.3.bin",
                                                 cmd_path=self.ROOT_PATH,
                                                 cmd_str="Executing sgx binary file",
                                                 execute_timeout=self._command_timeout)
        for index in range(len(self.NUMBER_OF_VMS)):
            # Creates VM names dynamically according to the OS and its resources
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self._log.info(" VM:{} on CentOS.".format(vm_name))
            # create with default values
            self._vm_provider.destroy_vm(vm_name)
            qemu_param = "-cpu host,+sgx-provisionkey -object memory-backend-epc,id=mem1,size=64M,prealloc=on " \
                         "-M sgx-epc.0.memdev=mem1,sgx-epc.0.node=0"
            dev_list = []
            dev_list_data = "qemuparam=={}".format(qemu_param)
            dev_list.append(dev_list_data)
            self.create_vm_qemu_generic(vm_name, self.VM_TYPE, vm_parallel=None, vm_create_async=True, mac_addr=True,
                                        pool_id=None,
                                        pool_vol_id=None, cpu_core_list=None, nw_bridge="bridge", devlist=dev_list)
            self._test_content_logger.end_step_logger(2, True)
            self._test_content_logger.start_step_logger(3)
            self.verify_vm_functionality(vm_name, self.VM_TYPE)
            vm_os_obj = self.create_vm_host(vm_name, self.VM_TYPE)
            common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            try:
                check_log_cmd = "dmesg | grep sgx"
                cmd_output = common_content_lib_vm_obj.execute_sut_cmd(check_log_cmd,check_log_cmd,
                                                                       execute_timeout=self._command_timeout,
                                                                       cmd_path=self.ROOT_PATH)
                if not (cmd_output is not None):
                    raise content_exceptions.TestFail(
                        "There are some dmesg log errors. Hence, test failed.")
            except Exception as e:
                self._log.error("Unable to check SGX log due to the error {} ".format(e))
                raise content_exceptions.TestFail("Cannot check SGX on VM.")
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationSGXCoExistence, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationSGXCoExistence.main()
             else Framework.TEST_RESULT_FAIL)
