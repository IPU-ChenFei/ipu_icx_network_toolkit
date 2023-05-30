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
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.lib.content_exceptions import *
from src.provider.vm_provider import VMs
from src.provider.sgx_provider import SGXProvider
from src.virtualization.virtualization_common import VirtualizationCommon


class PiVirtualizationKvmMKTMEdisableSGXenL(VirtualizationCommon):
    """
    HPALM ID: 80048
    The purpose of this test case is making sure the creation of VMs guests on KVM using Virt-Manager.
    1. Create VM.
    2. Enable SGX Bios knobs.
    3. Disable MKTME Bios knobs.
    4. Start the VM.

    """
    VM = [VMs.RHEL]
    BIOS_CONFIG_FILE = "pi_virtualization_kvm_mktmedisable_sgxen_l_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiVirtualizationKvmMKTMEdisableSGXenL object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(PiVirtualizationKvmMKTMEdisableSGXenL, self).__init__(test_log, arguments, cfg_opts)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.sgx_provider = SGXProvider.factory(self._log, cfg_opts, self.os,
                                        self.sdp)
        self.sgx_bios_config_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        if self.os.os_type != OperatingSystems.LINUX:
            raise TestNotImplementedError("Not implemented for {} OS".format(self.os.os_type))

    def execute(self):
        """
        1. create VM
        2. check VM is functioning or not
        """
        for index in range(len(self.VM)):
            # create VM names dynamically according to the OS
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self.create_vm(vm_name, self.VM[index], mac_addr=True)
            self.verify_vm_functionality(vm_name, self.VM[index])
            # enable SGX and disable MKTME in BIOS
            self.bios_util.set_bios_knob(bios_config_file=self.sgx_bios_config_file_path)
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)
            self.bios_util.verify_bios_knob(bios_config_file=self.sgx_bios_config_file_path)
            self._log.info("SGX set successfully through bios")
            self.sgx_provider.check_sgx_enable()
            self.start_vm(vm_name)

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(PiVirtualizationKvmMKTMEdisableSGXenL, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiVirtualizationKvmMKTMEdisableSGXenL.main()
             else Framework.TEST_RESULT_FAIL)
