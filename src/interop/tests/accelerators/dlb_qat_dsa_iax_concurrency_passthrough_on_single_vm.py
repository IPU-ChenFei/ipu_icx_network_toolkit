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
import threading

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.provider.vm_provider import VMs
from src.security.tests.hqm.hqm_common import HqmBaseTest
from src.interop.lib.common_library import CommonLibrary


class DlbQatDsaIaxConcurrencyPassthroughSingleVm(HqmBaseTest):
    """
    Phoenix ID : 16014303183 - DLB_QAT_DSA_IAX_Concurrency_Passthrough_on_single_VM
    The purpose of this test case is to validate the DSA passthrough for guest VM and run workload.
    """
    NUMBER_OF_VMS = 1
    VM = [VMs.CENTOS] * 1
    TEST_CASE_ID = ["16014303183", "DLB_QAT_DSA_IAX_Concurrency_Passthrough_on_single_VM"]
    BIOS_CONFIG_FILE = "accelerator_config.cfg"
    ACC_DEVICES = ["QAT", "DLB", "DSA", "IAX"]
    ACC_DEVICE_CODE = ["4940", "2710", "0b25", "0cfe"]
    CPA_SAMPLE_CODE = r"./cpa_sample_code"
    GRUB_CMD = "intel_iommu=on,sm_on iommu=on no5lvl --update-kernel=ALL"

    STEP_DATA_DICT = {1: {'step_details': 'BIOS Settings as per TC and update grub configs',
                          'expected_results': 'BIOS settings and gurb config setting are updated successfully'},
                      2: {'step_details': 'Install DLB in SUT and unbind the device update the grub in VM..',
                          'expected_results': 'Installation of DLB and unbind device grub update to be successful'},
                      3: {'step_details': 'Create VM with the device that are unbinded',
                          'expected_results': 'VM to be created to successfully'},
                      4: {'step_details': 'Install QAT in VM',
                          'expected_results': 'QAT to be installed successfully'},
                      5: {'step_details': 'Install DLB in VM',
                          'expected_results': 'DLBto be installed successfully in VM'},
                      6: {'step_details': 'QAT, DLB, DSA, IAX to run Concurrently on VM',
                          'expected_results': 'Concurrent execution of QAT, DLB, DSA, IAX to be successfully in VM'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of TC Class, TestContentLogger and CommonContentLib

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.accelerator_bios_knobs = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                                   self.BIOS_CONFIG_FILE)
        super(DlbQatDsaIaxConcurrencyPassthroughSingleVm, self).__init__(test_log, arguments, cfg_opts,
                                                                         self.accelerator_bios_knobs)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._common_lib_acc = CommonLibrary(test_log, self.os, cfg_opts, arguments)

    def prepare(self):
        # type: () -> None
        """Test preparation/setup """
        self._test_content_logger.start_step_logger(1)
        if self.os.os_type == OperatingSystems.LINUX:
            self._log.info("We have Linux OS for test case... proceeding further..")
        else:
            raise content_exceptions.TestFail("This TC is implement for Linux OS")
        self.set_and_verify_bios_knobs(bios_file_path=self.accelerator_bios_knobs)
        self._common_lib_acc.update_kernel_args_and_reboot([self.GRUB_CMD])
        self._test_content_logger.end_step_logger(1, True)

    def execute(self):
        """
        This Method validates the DSA passthrough for guest VM and run workload.
        :return: True if test case pass else fail
        """
        index = 0
        self._test_content_logger.start_step_logger(2)
        self.install_hqm_driver_libaray()
        port_number = self._common_content_configuration.get_port_number_for_vm()
        vm_name = self.VM[index] + "_" + str(index)
        self._log.info("unbinding devices to be connected to VM")
        for device in self.ACC_DEVICES:
            self._common_lib_acc.unbind_devices(device=device)
        self._log.info("Getting Devices to attach to VM")
        acc_dev = self._common_lib_acc.get_vfio_devices_vm(self.ACC_DEVICE_CODE, 1)
        self._log.info("Updating Grub in VM")
        self._common_lib_acc.update_kernel_args_and_reboot_on_vm(vm_name, [self.GRUB_CMD], port_number)
        self._test_content_logger.end_step_logger(2, True)

        self._test_content_logger.start_step_logger(3)
        self._common_lib_acc.create_qemu_vm(vm_name, port_number, acc_dev)
        self._test_content_logger.end_step_logger(3, True)

        self._test_content_logger.start_step_logger(4)
        self._common_lib_acc.install_qat_on_vm(port_number, configure_spr_cmd='./configure')
        self._test_content_logger.end_step_logger(4, True)

        self._test_content_logger.start_step_logger(5)
        self._common_lib_acc.install_hqm_driver_on_vm(port_number)
        self._test_content_logger.end_step_logger(5, True)

        self._test_content_logger.start_step_logger(6)
        qat_workload_thread = threading.Thread(target=self._common_lib_acc.execute_cpa_sample,
                                               args=(port_number, self.CPA_SAMPLE_CODE,))
        dlb_workload_thread = threading.Thread(target=self._common_lib_acc.execute_dlb, args=(port_number,))
        dsa_workload_thread = threading.Thread(target=self._common_lib_acc.run_dsa_workload_on_vm,
                                               args=("DSA", port_number,))
        iax_workload_thread = threading.Thread(target=self._common_lib_acc.run_dsa_workload_on_vm,
                                               args=("IAX", port_number,))
        qat_workload_thread.start()
        dlb_workload_thread.start()
        dsa_workload_thread.start()
        iax_workload_thread.start()

        qat_workload_thread.join()
        dlb_workload_thread.join()
        dsa_workload_thread.join()
        iax_workload_thread.join()

        self._test_content_logger.end_step_logger(6, True)
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(DlbQatDsaIaxConcurrencyPassthroughSingleVm, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if DlbQatDsaIaxConcurrencyPassthroughSingleVm.main() else Framework.TEST_RESULT_FAIL)
