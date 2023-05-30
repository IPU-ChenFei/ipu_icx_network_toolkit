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

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.provider.sgx_provider import SGXProvider
from src.lib import content_base_test_case
from src.lib import content_exceptions


class SGXMaxPRMRRSize(content_base_test_case.ContentBaseTestCase):
    """
    HPALM ID : H78279/H81533
    Enable SGX
    EDKII -> Socket Configuration -> Processor Configuration -> PRMRR Size = max size
    Save and boot to OS.
    """
    BIOS_CONFIG_FILE = "../sgx_enable_through_bios.cfg"
    PRMRR_KNOB_PROMPT = "PRMRR Size"
    PRMRR_KNOB_NAME = "PrmrrSize"
    TEST_CASE_ID = ["H78279-PI_Security_SGX_MAX_RegionSize_L",
                    "H81533-PI_Security_SGX_PRMRR_Configuration_Max_Regions_W"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SGXMaxPMRRSize

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
                __file__)), self.BIOS_CONFIG_FILE)

        super(SGXMaxPRMRRSize, self).__init__(
                test_log, arguments, cfg_opts,
                bios_config_file_path=bios_config_file)
        self._log.debug("Bios config file: %s", bios_config_file)
        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.srp = ProviderFactory.create(sil_cfg, test_log)  # type: SiliconRegProvider
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.sgx = SGXProvider.factory(test_log, cfg_opts, self.os, self.sdp)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(SGXMaxPRMRRSize, self).prepare()

    def execute(self):
        """Check for SGX PSW Installation"""
        self._log.info("SGX set successfully")
        self.sgx.check_sgx_enable()
        max_value = self.bios_util.get_max_bios_knob_option(
                self.PRMRR_KNOB_PROMPT)
        self._log.info("Maximum size=%s", max_value)
        value = '0x00'
        # Converting into hexadecimal
        if max_value.endswith("G"):
            value = hex(int(max_value.replace('G', ''))*1024*1024*1024)
        elif max_value.endswith("M"):
            value = hex(int(max_value.replace('M', ''))*1024*1024)
        else:
            raise content_exceptions.TestFail("Unknown %s size to convert "
                                              "into hexadecimal" % max_value)
        self._log.info("Max PRMRR Size: %s", value)
        self.bios.set_bios_knobs(self.PRMRR_KNOB_NAME, value, overlap=True)
        self.perform_graceful_g3()
        self.sgx.check_sgx_enable()
        actual_current_value = self.bios_util.get_bios_knob_current_value(
                self.PRMRR_KNOB_NAME)
        self._log.info("Actual current value of the %s bios knob is %s",
                       self.PRMRR_KNOB_NAME, actual_current_value)
        if eval((actual_current_value.strip("\\r"))) != eval(str(value)):
            raise content_exceptions.TestFail("%s value is not set" %
                                              self.PRMRR_KNOB_NAME)
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(SGXMaxPRMRRSize, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SGXMaxPRMRRSize.main() else
             Framework.TEST_RESULT_FAIL)
