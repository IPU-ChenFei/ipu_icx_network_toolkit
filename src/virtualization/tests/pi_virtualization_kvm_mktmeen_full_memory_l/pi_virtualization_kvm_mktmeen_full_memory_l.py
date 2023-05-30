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
from dtaf_core.lib.dtaf_constants import OperatingSystems

from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider

from src.lib.content_exceptions import *
from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon
from src.security.tests.mktme.mktme_common import MktmeBaseTest
from src.lib.bios_util import ItpXmlCli
from src.lib.install_collateral import InstallCollateral


class PiVirtualizationKvmMKTMEenFullMemoryL(VirtualizationCommon, MktmeBaseTest):
    """
    HPALM ID: 80050
    The purpose of this test case is making sure the creation of VMs guests on KVM using Virt-Manager.
    1. Enable Max Memory in BIOS
    2. Create VM.
    3. Disable SGX Bios knobs.
    4. Enable MKTME Bios knobs.
    5. Start the VM.

    """
    TC_ID = ["H80050-PI_Virtualization_KVM_MKTMEen_full_memory_L"]
    VM = [VMs.RHEL]
    BIOS_CONFIG_FILE = "pi_virtualization_kvm_mktmeen_full_memory_l_bios_knobs.cfg"
    MAX_MEM_BIOS_CONFIG_FILE = "pi_virtualization_kvm_enable_full_memory_l_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiVirtualizationKvmMKTMEenFullMemoryL object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(PiVirtualizationKvmMKTMEenFullMemoryL, self).__init__(test_log, arguments, cfg_opts)
        self.mktme_bios_config_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                        self.BIOS_CONFIG_FILE)
        self.max_mem_bios_config_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                          self.MAX_MEM_BIOS_CONFIG_FILE)

        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self.itp_xml_cli_util = ItpXmlCli(self._log, self._cfg)

        if self.os.os_type != OperatingSystems.LINUX:
            raise TestNotImplementedError("Not implemented for {} OS".format(self.os.os_type))
        self.high_memory_error = False

    def prepare(self):
        """
        Verify if th SUT is MKTME supported or not
        """
        if not self.verify_mktme():
            raise TestSetupError("Fail to verify SUT is MKTME supported or not")
        # enable maximum memory
        try:
            self.bios_util.set_bios_knob(bios_config_file=self.max_mem_bios_config_file_path)
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)
            self.bios_util.verify_bios_knob(bios_config_file=self.max_mem_bios_config_file_path)
        except Exception as ex:
            self.high_memory_error = True
            self.itp_xml_cli_util.perform_clear_cmos(self._sdp, self.os, self.reboot_timeout)
            self.sdp.reset_target()
            self.os.wait_for_os(self.reboot_timeout)

    def verify_vm_after_enable_mktme(self, vm_name, vm_type):
        """
        This method is to verify VM and MKTME

        :param vm_name:Name of the VM.
        :param vm_type: Type of the VM. ex:RHEL
        """
        self.verify_vm_functionality(vm_name, vm_type)
        # disable SGX and enable MKTME in BIOS
        self.bios_util.set_bios_knob(bios_config_file=self.mktme_bios_config_file_path)
        self._common_content_lib.perform_os_reboot(self.reboot_timeout)
        self.bios_util.verify_bios_knob(bios_config_file=self.mktme_bios_config_file_path)
        self._log.info("MKTME set successfully through bios")
        self.msr_read_and_verify(self.MSR_TME_ADDRESS, self.MSR_MKTME_VAL)
        self._log.info("Successfully verified MKTME register value")
        self.start_vm(vm_name)

    def execute(self):
        """
        1. create VM
        2. check VM is functioning or not
        3. Enable MKTME and verify
        """
        self._vm_provider.create_bridge_network()
        try:
            if self.high_memory_error:
                raise RuntimeError("System is not booting with High Memory Bios settings")
            for index in range(len(self.VM)):
                # create VM names dynamically according to the OS
                vm_name = self.VM[index] + "_" + str(index)
                self.LIST_OF_VM_NAMES.append(vm_name)
                self.create_vm(vm_name, self.VM[index], mac_addr=True)
                self.verify_vm_after_enable_mktme(vm_name, self.VM[index])

        except Exception as ex:
            self._log.error("Fail to create VM with High Memory. Creating with the default memory settings")
            try:
                for vm_name in self.LIST_OF_VM_NAMES:
                    self._vm_provider.destroy_vm(vm_name)
            except Exception as ex:
                raise ("Unable to Destroy the VM due to {}".format(ex))
            self.bios_util.load_bios_defaults()
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)
            for index in range(len(self.VM)):
                # create VM names dynamically according to the OS
                vm_name = self.VM[index] + "_" + str(index)
                self.LIST_OF_VM_NAMES.append(vm_name)
                self.create_vm(vm_name, self.VM[index], mac_addr=True)
                self.verify_vm_after_enable_mktme(vm_name, self.VM[index])
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(PiVirtualizationKvmMKTMEenFullMemoryL, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiVirtualizationKvmMKTMEenFullMemoryL.main()
             else Framework.TEST_RESULT_FAIL)
