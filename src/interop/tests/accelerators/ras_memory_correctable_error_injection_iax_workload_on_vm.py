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

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.provider.vm_provider import VMs
from src.interop.lib.common_library import CommonLibrary
from src.lib.content_base_test_case import ContentBaseTestCase


class RasMemoryCorrectableErrorInjectionWithIAXWorkloadVM(ContentBaseTestCase):
    """
    Phoenix ID : 16014312671 - RAS_Memory_Correctable_Error_Injection_with_IAX_Workload_VM
    The purpose of this test case is to validate the IAX fisher execution on guest VM and run workload.
    """
    NUMBER_OF_VMS = 1
    VM = [VMs.CENTOS] * 1
    TEST_CASE_ID = ["16014312671", "RAS_Memory_Correctable_Error_Injection_with_IAX_Workload_VM"]
    BIOS_CONFIG_FILE = "accelerator_config.cfg"
    GRUB_CMD = "intel_iommu=on,sm_on iommu=on no5lvl --update-kernel=ALL"

    STEP_DATA_DICT = {1: {'step_details': 'BIOS Settings as per TC and update grub configs',
                          'expected_results': 'BIOS settings and gurb config setting are updated successfully'},
                      2: {'step_details': 'Unbind the IAX device and attach and create VM..',
                          'expected_results': 'VM to be created successful with IAX device attached'},
                      3: {'step_details': 'IAX to run on VM',
                          'expected_results': 'IAX to be successfully run in VM'},
                      4: {'step_details': 'Run fisher tool and collect the results',
                          'expected_results': 'Fisher tool to be executed successfully'}
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
        super(RasMemoryCorrectableErrorInjectionWithIAXWorkloadVM, self).__init__(test_log, arguments, cfg_opts,
                                                                                  self.accelerator_bios_knobs)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._common_lib_acc = CommonLibrary(test_log, self.os, cfg_opts, arguments)
        self.port_number = self._common_content_configuration.get_port_number_for_vm()

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
        This Method validates the IAX fisher for guest VM and run workload.
        :return: True if test case pass else fail
        """
        index = 0
        device_cmd = '-device intel-iommu,caching-mode=on,dma-drain=on,x-scalable-mode="modern",' \
                     'device-iotlb=on,aw-bits=48 -device vfio-pci,sysfsdev=/sys/bus/mdev/devices/{}'
        self._test_content_logger.start_step_logger(2)
        vm_name = self.VM[index] + "_" + str(index)
        uuid = self._common_lib_acc.get_uuid("IAX")
        self._common_lib_acc.create_qemu_vm(vm_name, self.port_number, [device_cmd.format(uuid)])
        self._common_lib_acc.update_kernel_args_and_reboot_on_vm(vm_name, [self.GRUB_CMD], self.port_number)
        self._test_content_logger.end_step_logger(2, True)

        self._test_content_logger.start_step_logger(3)
        self._common_lib_acc.run_mdev_workload_on_vm("IAX", "-uc", "-r",  port_number=self.port_number)
        self._common_lib_acc.run_mdev_workload_on_vm("IAX", "-kc", "-i 100 -j 2", port_number=self.port_number)
        self._test_content_logger.end_step_logger(3, True)

        self._test_content_logger.start_step_logger(4)
        self._common_lib_acc.run_fisher_tool_on_vm(self.port_number, type_of_error="correctable", workload="IAX")
        self._test_content_logger.end_step_logger(4, True)
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        """
        To clean the system after execution
        """
        self._common_lib_acc.execute_ssh_on_vm("rm -rf {}".format(self._common_lib_acc.ACCEL_RANDOM_CONFIG_PATH.format
                                                                  ("fisher_*")), "removing fisher output",
                                               self.port_number, self._command_timeout)
        super(RasMemoryCorrectableErrorInjectionWithIAXWorkloadVM, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if RasMemoryCorrectableErrorInjectionWithIAXWorkloadVM.main() else
        Framework.TEST_RESULT_FAIL)
