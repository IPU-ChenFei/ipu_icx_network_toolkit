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

from src.lib.dtaf_content_constants import ErrorTypeAttribute

from src.lib.os_lib import WindowsCommonLib
from src.provider.vm_provider import VMs
from src.ras.tests.io_virtualization.virtualization_hyper_v_numa_affinity_setup import VirtualizationHyperNumaAffinitySetup


class VirtualizationHyperVRedHatVmsSubNumaAffinitySetupMemCeInjection(VirtualizationHyperNumaAffinitySetup):
    """
    GLASGOW ID: G68644_W

    This test cases will help put a virtual machine on a Numa node and another virtual machine on another.
    Test case can divide the numa nodes further into sub-numa nodes in 2-cluster(SNC2)  and 4 cluster (SNC4) mode
    with Mem CE.
    """
    BIOS_CONFIG_FILE = "vm_hyperv_subnuma_memory_inject_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationHyperVRedHatVmsSubNumaAffinitySetupMemCeInjection object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(VirtualizationHyperVRedHatVmsSubNumaAffinitySetupMemCeInjection, self).__init__(test_log, arguments, cfg_opts,
                                                                                self.BIOS_CONFIG_FILE)
        self._windows_common_lib = WindowsCommonLib(self._log, self.os)

    def prepare(self):  # type: () -> None
        """
        To Setup prepare
        """
        super(VirtualizationHyperVRedHatVmsSubNumaAffinitySetupMemCeInjection, self).prepare(
            vm_os_type=OperatingSystems.LINUX)

    def execute(self):
        """
        1. Execute VirtualizationHyperNumaAffinitySetup Test
        2. Inject Mem Error
        3. Verify in OS

        :return : True on Success
        """
        super(VirtualizationHyperVRedHatVmsSubNumaAffinitySetupMemCeInjection, self).execute()

        self.inject_and_verify_mem_error(ErrorTypeAttribute.CORRECTABLE)
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        """
        Test Cleanup
        1. Destroy Created VM.
        """
        super(VirtualizationHyperVRedHatVmsSubNumaAffinitySetupMemCeInjection, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationHyperVRedHatVmsSubNumaAffinitySetupMemCeInjection.main()
             else Framework.TEST_RESULT_FAIL)
