#!/usr/bin/env python
# coding=utf-8
##########################################################################
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
##########################################################################

import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.ras.tests.cloaking.cloaking_common import CloakingCommon


class CloakingEinjMemoryCorrectableError(CloakingCommon):
    """
    Glasgow iD : 60305
    Cloaking refers to allowing UEFI-FW/SMM to mask corrected and UCNA errors from OS/SW visibility.

    MCA Bank Error Control Enabling Registers:
    CMCI_DISABLEWhen set to 1, disables corrected machine check interrupt entirely, cleared upon each reset.
    CERR_RD_STATUS_IN_SMM_ONLY default value is '0', which is the legacy behavior. When set to 1, an rdmsr to any
    MCi_STATUS register will return 0 while a corrected error is logged in the register unless the processor is in
    SMM mode.
    UCNA_RD_STATUS_IN_SMM_ONLY default value is '0', which is the legacy behavior. When set to 1, an rdmsr to any
    MCi_STATUS register will return 0 while a UCNA error is logged in the register unless the processor is in SMM mode
    KTICERRLOGCTRL Dis_ ce_log bit 0. When set, Corrected errors will not be logged in Intel® UPI MCA bank status
    registers (IA32_MCi_STATUS). It will still be logged in BIOS_KTI_ERR_ST registers.
    KTICORERRCNTDIS Corerrcnt_mask bits 9:0. Intel® UPI Error count disable mask. NOTE: This has no effect on the
    KTIERRCNT0/1/2_CNTR error counters. If bit is set to 1 it disables incrementing of Intel® UPI MCA banks status
    register (IA32_MCi_STATUS.cor_err_cnt and/or BIOS_KTI_ERR_ST.cor_err_cnt for a given error code).

    Once this feature is enabled, only SMM and PECI will have access to such error logs.
    """

    BIOS_CONFIG_FILE = "cloaking_mem_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new CloakingEinjMemoryCorrectableError object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(CloakingEinjMemoryCorrectableError, self).__init__(test_log, arguments, cfg_opts,
                                                                 self.BIOS_CONFIG_FILE)

    def prepare(self):

        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs that are set.

        :return: None
        """
        self._install_collateral.copy_mcelog_conf_to_sut()
        self._einj_corr_obj.prepare()  # Calling prepare of object for Glasgow ID: 59255

    def execute(self):
        """
        Injecting the EinjMemoryCorrectableError and validating the error log

        :return result: True if error detected else False
        """
        ret_val = self.cloaking_injecting_memory_correctable_error()
        return ret_val


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CloakingEinjMemoryCorrectableError.main() else
             Framework.TEST_RESULT_FAIL)
