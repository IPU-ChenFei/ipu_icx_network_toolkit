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
"""DEPRECATION WARNING - Not included in agent scripts/libraries, which will become the standard test scripts."""
import warnings
warnings.warn("This module is not included in agent scripts/libraries.", DeprecationWarning, stacklevel=2)
import sys

from dtaf_core.lib.dtaf_constants import Framework

from src.sdsi.lib.sdsi_common_lib import SDSICommonLib
from src.sdsi.tests.provisioning.dlb.dlb_base_test_case import SDSI_DLB_Base_Class


class OutOfBandDLBProvisionAndReturnToBaseTwoDlbInst(SDSI_DLB_Base_Class):
    """
    Glasgow_ID: 74255
    Phoenix_ID: 22013943597
    Expectation is that DLB/HQM devices should works only after applying the HQM2 licenses.
    """
    # HQM payload should not be higher than that of maximum supported devices. So the payload name
    # can be lesser or equal as that of HQM_Count per CPU
    HQM_PAYLOAD_NAME_TO_ENABLE = "HQM2"

    # socket_0_din0, socket_0_din3, socket_1_din0, socket_1_din3
    dlb_pcie_device_ids_list = ["6d:00.0","7c:00.0","ea:00.0","f9:00.0"]
    hqm_bios_name_list = ["HqmEn_0", "HqmEn_3","HqmEn_4", "HqmEn_7"]


    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of OutOfBandDLBProvisionAndReturnToBaseFourDlbInst

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super().__init__(test_log, arguments, cfg_opts)

        self._sdsi_obj = SDSICommonLib(self._log, self.os, self._common_content_lib,
                                       self._common_content_configuration, self._sdsi_installer, self.ac_power,
                                       cfg_opts)

        cpu_count = self._sdsi_obj.number_of_cpu

        #make en explicit call to super class's Initialize() method.
        super().Initialize(self._sdsi_obj, self.HQM_PAYLOAD_NAME_TO_ENABLE,
                           self.dlb_pcie_device_ids_list, self.hqm_bios_name_list)


    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        self._log.info("OutOfBandDLBProvisionAndReturnToBaseTwoDlbInst::prepare")
        super().prepare()




    def execute(self):
        """
            Test case steps.
            pre: apply license, clear NVRAM.
            #3  Update HqM bios settings
            #4  check SDsI installer is working(covered by initialization)
            #5  verifying any dlb devices enumerated without HQM licence
            #6  Removing the default dlb2 driver
            #7  Apply HQm4 payload licence
            #8  Enable VTD and Interrupt Mapping bios settings.
            #9  verifying all

        """
        retval = super().execute()
        return retval


    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        self._log.info("Perform graceful G3 for resetting the counters after test irrespective of pass/fail.")
        self.perform_graceful_g3()
        super().cleanup(return_status)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if OutOfBandDLBProvisionAndReturnToBaseTwoDlbInst.main()
             else Framework.TEST_RESULT_FAIL)
