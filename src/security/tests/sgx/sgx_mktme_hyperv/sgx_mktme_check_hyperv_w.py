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

import sys
import os

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider

from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.provider.vm_provider import VMs
from src.provider.sgx_provider import SGXProvider
from src.virtualization.virtualization_common import VirtualizationCommon


class SGXMktmeCheckHyperV(VirtualizationCommon):
    """
    HPQC ID : H81549-PI_Security_SGX_MKTMEcheck_W, Phoenix ID : 18014075141
    Verify SGX enabled through bios and the register values
    """
    TEST_CASE_ID = ["H81549", "PI_Security_SGX_MKTMEcheck_W"]
    BIOS_CONFIG_FILE = "sgx_mktme_vm_bios_knobs.cfg"
    STEP_DATA_DICT = {1: {'step_details': 'Enable TME, MKTME and SGX Bios Knobs', 'expected_results': 'Verify TME, '
                          'MKTME and SGX Bios Knobs are Set'},
                      2: {'step_details': 'Execute sgx_test.exe', 'expected_results': 'Verity the app test'},
                      3: {'step_details': 'Create HyperV VM', 'expected_results': 'Verify the VM'},
                      4: {'step_details': 'After VM creation, execute sgx_test.exe', 'expected_results': 'Verity the '
                          'app test'}}
    NUMBER_OF_VMS = 1
    VM = [VMs.WINDOWS]
    VM_TYPE = "RS5"
    NETWORK_ASSIGNMENT_TYPE = "DDA"
    VSWITCH_NAME = "ExternalSwitch"
    ADAPTER_NAME = None

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SGXMktmeCheckHyperV

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(SGXMktmeCheckHyperV, self).__init__(test_log, arguments, cfg_opts)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.sgx_provider = SGXProvider.factory(self._log, cfg_opts, self.os, self.sdp)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(SGXMktmeCheckHyperV, self).prepare()

    def execute(self):
        """
        Test main logic to enable and check the bios knobs for SGX enable using ITP and execute Functional Validation
        Tool and verify SGX is Working as Expected.

        :raise: content_exceptions.TestFail if SGX capability not supported
        :return: True if test case executed successfully
        """
        self._test_content_logger.start_step_logger(1)
        self.bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self.bios_util.set_bios_knob(self.bios_config_file)  # To set the bios knob setting.
        self.perform_graceful_g3()  # To apply the new bios setting.
        self.bios_util.verify_bios_knob(self.bios_config_file)  # To verify the bios knob settings.
        self._test_content_logger.end_step_logger(1, True)
        self._test_content_logger.start_step_logger(2)
        self._log.info("SGX capability is supported")
        self.sgx_provider.check_sgx_tem_base_test()
        self._test_content_logger.end_step_logger(2, True)
        self._test_content_logger.start_step_logger(3)
        self._vm_provider.install_vm_tool()
        for index in range(self.NUMBER_OF_VMS):
            # Creates VM names dynamically according to the OS and its resources
            self._log.info("Creating VM on Hyper V")
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self.create_hyperv_vm(vm_name, self.VM_TYPE)  # Create VM function
            # Get Mac id flag from config to Assign the Mac id to Network
            mac_id_flag = self._common_content_configuration.enable_with_mac_id()
            self._log.info("Add MAC for VM from config is : {}".format(mac_id_flag))
            self._vm_provider.wait_for_vm(vm_name)  # Wait for VM to boot
            # Assign Network Adapter to VM using Direct Assignment method
            self._vm_provider.add_vm_network_adapter(self.NETWORK_ASSIGNMENT_TYPE, vm_name, self.ADAPTER_NAME,
                                                     self.VSWITCH_NAME, self.VM_TYPE, mac_id_flag)
            self.verify_hyperv_vm(vm_name, self.VM_TYPE)

        self._log.info("Hyper-v Basic functionality test successful")
        self._test_content_logger.end_step_logger(3, True)
        self._test_content_logger.start_step_logger(4)
        self.sgx_provider.load_sgx_properites()
        if not self.sgx_provider.run_sgx_app_test():
            raise content_exceptions.TestFail("{} have failures".format(self.SGX_TEST))
        self._test_content_logger.end_step_logger(4, True)

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(SGXMktmeCheckHyperV, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SGXMktmeCheckHyperV.main() else Framework.TEST_RESULT_FAIL)
