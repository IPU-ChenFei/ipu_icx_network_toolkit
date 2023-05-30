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

from src.virtualization.virtualization_common import VirtualizationCommon


class VirtualizationGenericVTBiosSetup(VirtualizationCommon):
    """
    Glasgow ID: 56228

    Generic Virtualization configuring VT features in the setup menu (BIOS)
    """
    TC_ID = ["H56228", "Virtualization_Generic_BIOS_VT_setup"]
    BIOS_CONFIG_FILE = "virtualization_generic_vt_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationGenericVTBiosSetup object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        self.bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(VirtualizationGenericVTBiosSetup, self).__init__(test_log, arguments, cfg_opts, self.bios_config_file)


    def prepare(self):  # type: () -> None
        super(VirtualizationGenericVTBiosSetup, self).prepare()

    def execute(self):
        """

        Install Hypervisor on SUT, Either Windows or Linux os type is supported.
        Note:
        If SUT os type is Windows install Hyper-V hypervisor.
        If SUT os type is Linux / RHEL install KVM based hypervisor.
        """
        self._vm_provider.install_vm_tool()

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationCommon, self).cleanup(return_status)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationGenericVTBiosSetup.main()
             else Framework.TEST_RESULT_FAIL)
