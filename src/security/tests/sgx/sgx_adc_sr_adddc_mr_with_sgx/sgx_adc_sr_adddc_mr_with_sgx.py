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

from src.lib.dtaf_content_constants import TimeConstants
from src.lib import content_exceptions
from src.security.tests.sgx.sgx_common import SgxCommon
from src.security.tests.sgx.sgx_constant import SGXConstant


class SGXAdcSrAdddcMrWithSgx(SgxCommon):
    """
    Glasgow ID : G64020.2-No ADC(SR) or ADDDC(MR) with SGX
    Phoneix ID : 18014073497-SGX InterOp with ADC(SR) or ADDDC(MR)
    From SPR onwards, SGX can co-exist with ADC(SR) or ADDDC(MR)
    """
    TEST_CASE_ID = ["G64020 - No ADC(SR) or ADDDC(MR) with SGX", "P18014073497-SGX InterOp with ADC(SR) or ADDDC(MR)"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SGXAdcSrAdddcMrWithSgx

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        bios_config_file_path = SgxCommon.get_bios_knob_cfg_complete_path(
            SGXConstant.BIOS_CONFIG_FILE_SGX_ADDDC_CONFIG_FILE, cfg_opts)
        super(SGXAdcSrAdddcMrWithSgx, self).__init__(test_log, arguments, cfg_opts,
                                                     bios_config_file_path=bios_config_file_path)

    def prepare(self):
        # type: () -> None
        """preparing the setup and setting knobs"""
        super(SGXAdcSrAdddcMrWithSgx, self).prepare()

    def execute(self):
        """
        This method executes the following steps:
        1. Enabled ADDDC knob and verify it is Enabled.
        2. Verify SGX knob is Enabled when ADDDC Sparing  knob is Enabled.
        3. Verify SGX msr value matches the excepted value.
        4. Run Hydra test for one Hour

        :raise: content exception SGX Bios knob is not Enabled.
        :return: True if Test case pass
        """
        if not self.bios_util.get_bios_knob_current_value(
                self.sgx_provider.SGX_KNOB_NAME) == SGXConstant.SGX_ENABLE_KNOB_VALUE:
            raise content_exceptions.TestFail("SGX Bios knob is not Enabled when ADDDC Sparing knob is enabled")
        self._log.info("SGX Bios knob is Enabled when ADDDC Sparing knob is enabled")
        self.sgx_provider.check_sgx_enable()
        self.sgx_provider.run_hydra_test(test_duration=TimeConstants.ONE_HOUR_IN_SEC)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SGXAdcSrAdddcMrWithSgx.main() else
             Framework.TEST_RESULT_FAIL)
