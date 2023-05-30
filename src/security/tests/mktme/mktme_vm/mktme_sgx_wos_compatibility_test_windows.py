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
import sys
import os
import argparse
import logging
from xml.etree import ElementTree

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.security.tests.mktme.mktme_common_windows import WindowsMktmeBase


class MktmeSGXVMCompatibilityWindows(WindowsMktmeBase):
    """
        Phoenix id: 18014070937

        This test is targeting to
        - Enable MKTME setting as well as SGX
        - Run sgx_test.exe -auto mode.
        - Launch  a MKTME enabled VM in host machine
        - Encrypt the VM memory
        - Run for few minutes
        - Run the sgx_test.exe -auto mode once again.
        - Shutdown
    """

    _BIOS_CONFIG_FILE_TME_SGX_ENABLE = r"..\collateral\sgx_mktme_vm_bios_knobs.cfg"
    _BIOS_CONFIG_FILE_TME_SGX_DISABLE = r"..\collateral\sgx_disable_bios_knobs.cfg"

    def __init__(self, test_log: logging.Logger, arguments: argparse.Namespace, cfg_opts: ElementTree) -> None:
        """Create an instance of MktmeSaveRestoreVMWindows.

        :param test_log: Logger object
        :param arguments: arguments as Namespace
        :param cfg_opts: Configuration object.
        :return: None
        """
        super(MktmeSGXVMCompatibilityWindows, self).__init__(test_log, arguments, cfg_opts)
        self.tme_sgx_bios_enable_cfg_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                         self._BIOS_CONFIG_FILE_TME_SGX_ENABLE)
        self.tme_sgx_bios_disable_cfg_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                          self._BIOS_CONFIG_FILE_TME_SGX_DISABLE)

    def prepare(self):
        self.clean_all_vms_from_hyper_v()
        super(MktmeSGXVMCompatibilityWindows, self).prepare()
        self.check_knobs(knob_file=self.tme_sgx_bios_enable_cfg_file, set_on_fail=True)
        self.verify_mktme()
        self.setup_sgx_packages()

    def run_sgx_test(self):
        """Run the sgx_test.exe"""

        self._log.info("Starting the sgx_test.exe")
        if not self.sgx_provider.run_sgx_app_test():
            raise content_exceptions.TestFail("sgx_test.exe have failures")
        self._log.info("Successfully completed the sgx_test.ext")

    def cleanup(self, return_status) -> None:
        """cleanup SGX bios settings and other items."""

        super(MktmeSGXVMCompatibilityWindows, self).cleanup(return_status)

    def execute(self):
        legacy = False
        enable_ethernet = True
        key = 0

        # run sgx test before launching the MKTME VM
        self.run_sgx_test()

        key, vm_name = self.create_vm_name(key, legacy)
        self.launch_vm(key, vm_name, legacy, enable_ethernet)
        self._log.info("VM is alive after launching.")

        # applying memory encryption to VM
        self._log.info(f"applying memory encryption settings on VM {vm_name}")
        ret_val = self.apply_memory_encryption_on_vm(vm_name, self.vm_reboot_timeout)
        if not ret_val:
            raise content_exceptions.TestFail("Memory encryption is not applied to the VM")
        self._log.info(f"Verify  VM is running. {vm_name}")
        ret_val = self.test_vm_folder_accessible(vm_name)
        if ret_val is True:
            self._log.info("VM is accessible")
        else:
            raise content_exceptions.TestFail("VM is not accessible after applying memory encryption")

        # run sgxtest after launching the MKTME VM
        self.run_sgx_test()

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MktmeSGXVMCompatibilityWindows.main() else Framework.TEST_RESULT_FAIL)
