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

from src.lib.os_lib import WindowsCommonLib
from src.ras.tests.io_virtualization.virtualization_hyper_v_numa_affinity_setup import VirtualizationHyperNumaAffinitySetup


class VirtualizationHyperSubNumaAffinitySetup(VirtualizationHyperNumaAffinitySetup):
    """
    GLASGOW ID: G68117_W

    This test cases will help put a virtual machine on a Numa node and another virtual machine on another.
    Test case can divide the numa nodes further into sub-numa nodes in 2-cluster(SNC2)  and 4 cluster (SNC4) mode.
    """
    BIOS_CONFIG_FILE = "virtualisation_hyperv_subnuma_affinity_setup.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationHyperSubNumaAffinitySetup object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), self.BIOS_CONFIG_FILE)
        super(VirtualizationHyperSubNumaAffinitySetup, self).__init__(test_log, arguments, cfg_opts,
                                                                      bios_config=bios_config_file)
        self._windows_common_lib = WindowsCommonLib(self._log, self.os)

    def prepare(self):  # type: () -> None
        """
        To Setup prepare
        """
        super(VirtualizationHyperSubNumaAffinitySetup, self).prepare()

    def execute(self):
        """
        1. Execute VirtualizationHyperNumaAffinitySetup Test

        :return : True on Success
        """
        super(VirtualizationHyperSubNumaAffinitySetup, self).execute()
        return True


    def cleanup(self, return_status):  # type: (bool) -> None
        """
        Test Cleanup
        1. Destroy Created VM.
        """
        super(VirtualizationHyperSubNumaAffinitySetup, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationHyperSubNumaAffinitySetup.main()
             else Framework.TEST_RESULT_FAIL)
