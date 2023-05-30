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


class WindowsVMProviderBasicFunctionality(VirtualizationCommon):
    """
    Test to check the functionality for Windows VM Provider
    """
    bios_file = "virtualization_hyper_v_install_hypervisor_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new WindowsVMProviderBasicFunctionality object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(WindowsVMProviderBasicFunctionality, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):  # type: () -> None
        self.set_and_verify_bios_knobs(bios_file_path=self.bios_file)

    def execute(self):
        """
        1. create VM from template
        2. get VM info
        """
        try:
            self._vm_provider.create_vm_from_template("windows_VM1", 2)
            self._vm_provider.get_vm_info("windows_VM1")
            self._vm_provider.create_vm_from_template("linux_VM1", 2)
            self._vm_provider.get_vm_info("linux_VM1")
            self._vm_provider.create_vm("windows_iso", 1, 2, 50, 10)
            self._vm_provider.get_vm_info("windows_iso")
            self._vm_provider.create_vm("linux_iso", 1, 2, 50, 10)
            self._vm_provider.get_vm_info("linux_iso")
            return True
        except RuntimeError:
            return False

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationCommon, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if WindowsVMProviderBasicFunctionality.main()
             else Framework.TEST_RESULT_FAIL)
