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
import os
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider

from src.lib import content_base_test_case, content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.provider.sgx_provider import SGXProvider
from src.security.tests.cbnt_txt.txt_base.Trusted_boot_with_tboot import TrustedBootWithTboot
from src.security.tests.sgx.sgx_constant import SGXConstant

class VerifyMsmiDisabledForBank(content_base_test_case.ContentBaseTestCase):
    """
    Phoenix ID : P18015104723-Verify that MSMI is disabled for bank 0/1

    Verify that MSMI is not enabled in BIOS for MCA Bank 0 (IFU) and MCA Bank 1 (DCU). BIOS must not set mce_ctl bit in
    both IFU (MC0) and DCU (MC1) MCE_CTL when SGX MCA recovery is enabled. If BIOS does not do this, then SGX will be
    globally disabled for IFU and DCU recoverable poison.

    MSMI disable for bank 0, 1 when LMCE is enabled to support MCA-Recovery is specific for ICX server.   In SPR it is
    not required.   If BIOS setup says MSMI Enabled,  MSMI can be enabled for all the banks. So if eMCA G2 is enabled
    for SPR - we expect SPR to always keep MSMI signaling on in IFU/DCU (ICX was the exception).
    """
    TEST_CASE_ID = ["P18015104723", "Verify that MSMI is disabled for bank 0/1"]
    CMD_DCU = "cpu.cores.threads.dcu_cr_mc1_misc2.mce_ctl"
    CMD_IFU = "cpu.cores.threads.ifu_cr_mc0_misc2.mce_ctl"
    STEP_DATA_DICT = {1: {'step_details': 'Enable SGX Bios knobs and varify',
                          'expected_results': 'SGX Bios knobs enabled and verified'},
                      2: {'step_details': 'Check MSMI is enabled for all the banks through dcu and ifu cmd',
                          'expected_results': 'MSMI is enabled for all the banks'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of VerifyMsmiDisabledForBank

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.bios_config_file = SGXConstant(test_log).sgx_bios_knobs()
        super(VerifyMsmiDisabledForBank, self).__init__(test_log, arguments, cfg_opts, self.bios_config_file)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.sgx = SGXProvider.factory(test_log, cfg_opts, self.os, self.sdp)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    def prepare(self):
        # type: () -> None
        """
        This method executes the following steps:
        1. preparing the setup and setting knobs
        2. Enable and verify Sgx
        """
        self._test_content_logger.start_step_logger(1)
        super(VerifyMsmiDisabledForBank, self).prepare()
        self.sgx.check_sgx_enable()
        self._test_content_logger.end_step_logger(1, return_val=True)

    def unlock_svn(self):
        """
        This method creates cscript obj and pythonsv obj and Unlock to red access

        :return: None
        """
        self._log.info("Unlocking Red Access")
        self.initialize_sv_objects()
        self.initialize_sdp_objects()
        self.SDP.itp.unlock()

    def execute(self):
        """
        This method is used to execute the DCU and IFU cmd using debugger
        together

        :return: True if Test case pass
        :raise: content_exceptions.TestFail - if failed.
        """
        self._test_content_logger.start_step_logger(2)
        self.unlock_svn()
        msmi_dcu_ifu_cmd_output_data_false = []
        value_dcu = list(self.SV.get_by_path(self.SV.SOCKETS, self.CMD_DCU))
        self._log.info("DCU Pythonsv command {} value is :{}".format(self.CMD_DCU, value_dcu))
        value_ifu = list(self.SV.get_by_path(self.SV.SOCKETS, self.CMD_IFU))
        self._log.info("IFU Pythonsv command {} value is :{}".format(self.CMD_IFU, value_ifu))
        for msmi_dcu_cmd_output_data in value_dcu:
            self._log.info("msmi_dcu_cmd output : {}".format(msmi_dcu_cmd_output_data))
            if not self.sgx.verify_msmi_cmd_output(str(msmi_dcu_cmd_output_data)):
                msmi_dcu_ifu_cmd_output_data_false.append(msmi_dcu_cmd_output_data)
        for msmi_ifu_cmd_output_data in value_ifu:
            self._log.info("msmi_ifu_cmd output : {}".format(msmi_ifu_cmd_output_data))
            if not self.sgx.verify_msmi_cmd_output(str(msmi_ifu_cmd_output_data)):
                msmi_dcu_ifu_cmd_output_data_false.append(msmi_ifu_cmd_output_data)
        if msmi_dcu_ifu_cmd_output_data_false:
                self._log.error("One or more msmi_dcu_ifu_cmd output_data found false ! {}"
                                        .format(msmi_dcu_ifu_cmd_output_data_false))
                raise content_exceptions.TestFail("One or more msmi_dcu_ifu_cmd_output data found false !")
        self._log.info("All the msmi cmd output is True!")
        self._test_content_logger.end_step_logger(2, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VerifyMsmiDisabledForBank.main() else
             Framework.TEST_RESULT_FAIL)
