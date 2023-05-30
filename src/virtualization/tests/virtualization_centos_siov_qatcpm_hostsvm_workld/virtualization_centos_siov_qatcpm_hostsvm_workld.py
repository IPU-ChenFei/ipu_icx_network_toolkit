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
import sys
import time

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
#from src.virtualization.virtualization_common import VirtualizationCommon
from src.virtualization.base_qat_util import BaseQATUtil
from src.lib.install_collateral import InstallCollateral
from src.lib.common_content_lib import CommonContentLib
from src.provider.vm_provider import VMs

class VirtualizationSRIOVQATCpmHostSVMWorkload(BaseQATUtil):
    """
    Phoenix ID : 16012901366
    The purpose of this test case is to validate the SRIOV functionality using QAT device and configure the Host SVM.
    Then execute host workload inside host/guest
    """
    NUMBER_OF_VMS = 1
    VM = [VMs.CENTOS] * 1
    VM_TYPE = "CENTOS"
    TEST_CASE_ID = ["P16012901366", "VirtualizationSRIOVQATCpmHostSVMWorkload"]
    BIOS_CONFIG_FILE = "virt_siov_qatcpm_hostsvm_workld_biosknobs.cfg"
    STORAGE_VOLUME = ["/home"]
    QAT_LOAD_TEST_TIME = 7200
    STEP_DATA_DICT = {
        1: {'step_details': 'Install and verify Bios knobs for QAT',
            'expected_results': 'Bios knobs installed and verified successfully'},
        2: {'step_details': 'Get the CPU socket, core and threads per core info',
            'expected_results': 'CPU core information retrieved'},
        3: {'step_details': 'Install and configure the yum repo config file',
            'expected_results': 'Yum repo configured successfully'},
        4: {'step_details': 'Install the QAT depemdencies, may be kernel sources as well',
            'expected_results': 'All packages installed successfully'},
        5: {'step_details': 'Check and Install the QAT driver, Create VFs and get qat device details',
            'expected_results': 'QAT driver built and installed, VFs created successfully'},
        6: {'step_details': 'Restart by Stopping and Starting the QAT Services',
            'expected_results': 'QAT Services restarted successfully'},
        7: {'step_details': 'Create and check the qat VF devices',
            'expected_results': 'QAT VF devices created successfully'},
        8: {'step_details': 'Check dev_cfg of the VF to see if SVM is enabled successfully on the device',
            'expected_results': 'SVM is enabled successfully on the device'},
        9: {'step_details': 'Build the hash sample app',
            'expected_results': 'The hash sample app built successfully'},
        10: {'step_details': 'Run hash_sample application',
            'expected_results': 'hash_sample application run successfully'},
        11: {'step_details': 'Delete all VFs created',
            'expected_results': 'All VFs deleted successfully'},
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of TC Class, TestContentLogger and CommonContentLib

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.virt_siov_qatcpm_func_vmwl_biosknobs = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(VirtualizationSRIOVQATCpmHostSVMWorkload, self).__init__(test_log, arguments, cfg_opts, self.virt_siov_qatcpm_func_vmwl_biosknobs)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._common_content_lib = CommonContentLib(test_log, self.os, cfg_opts)
        self._cfg_opt = cfg_opts
        self._arg_tc = arguments
        self._test_log = test_log

    def prepare(self):
        # type: () -> None
        """Test preparation/setup """

        if self.os.os_type == OperatingSystems.LINUX:
            self._log.info("We have Linux OS for test case... proceeding further..")
        else:
            raise content_exceptions.TestFail("Target is not booted with Linux")

        self._test_content_logger.start_step_logger(1)
        super(VirtualizationSRIOVQATCpmHostSVMWorkload, self).prepare()
        self.set_and_verify_bios_knobs(bios_file_path=self.BIOS_CONFIG_FILE)
        self._vm_provider.create_bridge_network("virbr0")
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This validates the SIOV functionality using QAT device and configure the Host SVM.
        Then execute host workload inside host/guest

        :return: True if test case pass else fail
        """
        self._test_content_logger.start_step_logger(2)
        self.enable_intel_iommu_by_kernel()

        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        self.get_yum_repo_config(self.os, self._common_content_lib, os_type="centos")
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        qat_dependency_packages = "epel-release zlib-devel libnl3-devel boost-devel systemd-devel yasm lz4-devel " \
                "elfutils-libelf-devel zlib-devel libnl3-devel boost-devel systemd-devel yasm openssl-devel readline-devel"
        self._install_collateral.yum_install(package_name = qat_dependency_packages)
        self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        self.install_check_qat_status(qat_type="sriov", target_type="host",
                                      common_content_object=self._common_content_lib)
        self._test_content_logger.end_step_logger(5, return_val=True)

        self._test_content_logger.start_step_logger(6)
        self.stop_qat_service(self._common_content_lib)
        self.start_qat_service(self._common_content_lib)
        self._test_content_logger.end_step_logger(6, return_val=True)

        self._test_content_logger.start_step_logger(7)
        bdf_sym_asym_dc_dict = self.get_qat_device_details(self._common_content_lib)
        for index in range(len(bdf_sym_asym_dc_dict['bdf'])):
            self.create_accel_virtual_function(16, (bdf_sym_asym_dc_dict['bdf'])[index])

        self.qat_vf_device_presence()
        self.get_qat_device_status_adfctl(0, self._common_content_lib)
        self._test_content_logger.end_step_logger(7, return_val=True)
        self._test_content_logger.start_step_logger(8)
        self.qat_vf_file_presence()
        # for index in range(len(bdf_sym_asym_dc_dict['bdf'])):
        #     self.check_if_spr_svm_enabled((bdf_sym_asym_dc_dict['bdf'])[index], 16, self._common_content_lib)
        self._test_content_logger.end_step_logger(8, return_val=True)
        self._test_content_logger.start_step_logger(9)
        self.qat_build_hash_sample_workload_app(self._common_content_lib)
        self._test_content_logger.end_step_logger(9, return_val=True)

        self._test_content_logger.start_step_logger(10)
        start_time = time.time()
        seconds = self.QAT_LOAD_TEST_TIME
        while True:
            current_time = time.time()
            elapsed_time = current_time - start_time

            self.qat_run_hash_sample_workload(self._common_content_lib)

            if elapsed_time > seconds:
                self._log.info("Finished QAT load test after: " + str(int(elapsed_time)) + " seconds")
                break
        self._test_content_logger.end_step_logger(10, return_val=True)

        self._test_content_logger.start_step_logger(11)
        for index in range(len(bdf_sym_asym_dc_dict['bdf'])):
            self.delete_accel_virtual_function((bdf_sym_asym_dc_dict['bdf'])[index])
        self._test_content_logger.end_step_logger(11, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationSRIOVQATCpmHostSVMWorkload.main() else Framework.TEST_RESULT_FAIL)
