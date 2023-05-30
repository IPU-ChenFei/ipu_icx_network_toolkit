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

from dtaf_core.lib.dtaf_constants import Framework

from src.virtualization.virtualization_common import VirtualizationCommon


class VirtualizationHyperVInstallHypervisor(VirtualizationCommon):
    """
    HPALM ID: H80294_Virtualization - Hyper-V - Install Hypervisor
    Glasgow ID: 33669.3
    Microsoft Hyper-V, codenamed Viridian, formerly known as Windows Server Virtualization, is a native hypervisor;
    it can create virtual machines on x86-64 systems running Windows.
    """
    TESTCASE_ID = ["H80294", "Virtualization_Hyper_V_Install_Hypervisor"]
    bios_file = "virtualization_hyper_v_install_hypervisor_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationHyperVInstallHypervisor object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(VirtualizationHyperVInstallHypervisor, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):  # type: () -> None
        self.set_and_verify_bios_knobs(bios_file_path=self.bios_file)

    def execute(self):
        """
        1. install Hyper-V on SUT
        """
        self._vm_provider.install_vm_tool()
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationCommon, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationHyperVInstallHypervisor.main()
             else Framework.TEST_RESULT_FAIL)
