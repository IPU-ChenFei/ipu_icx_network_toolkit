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
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon
from src.ras.lib.ras_upi_util import RasUpiUtil
from src.lib.common_content_lib import CommonContentLib
from src.ras.tests.io_virtualization.vm_upi_lane_failover_base_test import VmUpiLaneFailOverBaseTest
from src.lib import content_exceptions


class UpiLaneFailOverForSingleGuestOs(VmUpiLaneFailOverBaseTest):
    """
    GLASGOW ID: G67425

    While running stress on Single VMs,  Cause a UPI lane failover
    Verify VM is still functional
    """
    BIOS_CONFIG_FILE = "upi_lane_failover_bios_knobs.cfg"
    TEST_CASE_ID = ["G67425", "Upi_Lane_FailOver_For_Single_Guest_Os_With_Vm_Cpu_Workloads"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new UpiLaneFailOverForSingleGuestOs object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        super(UpiLaneFailOverForSingleGuestOs, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE
                                                                             )
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.virtualization_obj = VirtualizationCommon(self._log, arguments, cfg_opts)

    def prepare(self):  # type: () -> None
        """
        To Setup prepare
        """
        super(UpiLaneFailOverForSingleGuestOs, self).prepare()

    def execute(self, num_of_vms=None):
        """
        1. create one VM.
        2. check VM is functioning or not.
        3. Run crunch stress tool on VM.
        4. Run Upi Lane Failover Test.
        5. Check VM still working or not.

        :raise : content_exceptions.TestFail
        :return : True on Success
        """
        super(UpiLaneFailOverForSingleGuestOs, self).execute(
            num_of_vms=1)
        return True

    def cleanup(self, return_status, num_of_vms=None):  # type: (bool) -> None
        """
        Test Cleanup
        1. Destroy Created VM.
        """
        super(UpiLaneFailOverForSingleGuestOs, self).cleanup(return_status, 1)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if UpiLaneFailOverForSingleGuestOs.main()
             else Framework.TEST_RESULT_FAIL)
