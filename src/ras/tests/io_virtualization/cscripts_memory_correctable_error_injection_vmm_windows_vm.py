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

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.dtaf_content_constants import ErrorTypeAttribute
from src.lib import content_exceptions
from src.ras.tests.io_virtualization.cscripts_pcie_error_injection_base_test import VmmCscriptsPcieErrorInjectionBaseTest


class VmmCscriptsMemoryCorrectableErrorInjectionVmmWindowsVm(VmmCscriptsPcieErrorInjectionBaseTest):
    """
    GLASGOW ID: G67988_W

    This test case walks you through how to do Memory error injection to the platform.
    This will require an OS with virtualization function enabled.
    """
    BIOS_CONFIG_FILE = "cscripts_memory_error_injection_bios_config_file.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VmmCscriptsMemoryCorrectableErrorInjectionVmmWindowsVm object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), self.BIOS_CONFIG_FILE)
        super(VmmCscriptsMemoryCorrectableErrorInjectionVmmWindowsVm, self).__init__(test_log, arguments, cfg_opts,
                                                                                 bios_config_file=bios_config_file
                                                                                 )
        self.num_vms = 1

    def prepare(self):  # type: () -> None
        """
        To Setup prepare
        """
        super(VmmCscriptsMemoryCorrectableErrorInjectionVmmWindowsVm, self).prepare()
        self._vm_provider_obj.install_vm_tool()

    def execute(self):
        """
        1. check available memory size
        2. Calculate the memory for the VM
        3. execute correctable memory test

        :raise : content_exceptions.TestFail
        :return : True on Success
        """
        memory_size = self._common_content_lib.get_os_available_memory()
        vm_memory = int(memory_size / 2)
        #  Observed an issue (Manually also), if we create VM with exact half memory size. So, reducing 2 gb.
        vm_memory_gb = int(vm_memory / 1024) - 2
        self._log.info("VM memory size - {} GB".format(vm_memory_gb))
        return self.cscripts_memory_error_injection_vmm_windows_vm(err_type=ErrorTypeAttribute.CORRECTABLE, vm_memory=vm_memory_gb)


    def cleanup(self, return_status):  # type: (bool) -> None
        """
        Test Cleanup
        1. Destroy Created VM.
        """

        super(VmmCscriptsMemoryCorrectableErrorInjectionVmmWindowsVm, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VmmCscriptsMemoryCorrectableErrorInjectionVmmWindowsVm.main()
             else Framework.TEST_RESULT_FAIL)
