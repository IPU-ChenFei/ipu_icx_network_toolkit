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
from dtaf_core.providers.provider_factory import ProviderFactory

from src.ras.tests.upi_llr.upi_llr_common import UpiLlrCrcCommon
from src.ras.lib.ras_upi_util import RasUpiUtil
from dtaf_core.lib.dtaf_constants import ProductFamilies
from src.lib.common_content_lib import CommonContentLib
import xml
from xml.etree.ElementTree import Element, tostring
import xmltodict


class StressUpiLlrTransientFaultThreshold(UpiLlrCrcCommon):
    """
    Glasgow_id : 69328
    Stress UPI LLR-transient fault threshold

    Intel UPI links are capable of detecting various types of correctable and uncorrected errors.
    Once an error is detected, it is reported (logged and signaled) using Intel UPI link MCA banks and
    platform specific log registers.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new StressUpiLlrTransientFaultThreshold object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        # xml location-> suts/sut/silicon/cpu/family"
        cfg_dict = []
        cpu_family_location = CommonContentLib.PLATFORM_CPU_FAMILY
        cpu_family = cfg_opts.find(cpu_family_location)
        if xml.etree.ElementTree.iselement(cpu_family):
            cfg_dict = xmltodict.parse(tostring(cpu_family))
        product_family_name = cfg_dict["family"]

        # SPR- When MCA banks got merged -UPI threshold registers are not used - update BIOS knob EmcaCsmiThreshold
        _BIOS_CONFIG_FILE_DICT = {
            ProductFamilies.ICX: "stress_upi_llr_transient_fault_threshold.cfg",
            ProductFamilies.SPR: "stress_upi_llr_transient_fault_threshold_SPR.cfg"
        }
        self._BIOS_CONFIG_FILE = _BIOS_CONFIG_FILE_DICT[product_family_name]

        super(StressUpiLlrTransientFaultThreshold, self).__init__(
            test_log,
            arguments,
            cfg_opts,
            self._BIOS_CONFIG_FILE)

        self._upi_utils_obj = RasUpiUtil(self.os, self._log, cfg_opts, self._common_content_lib, arguments)

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
        super(StressUpiLlrTransientFaultThreshold, self).prepare()

    def execute(self):
        """
        This method is used to execute:
        1. Run stress tools and verify tool is running or not.
        2. Set the error threshold.
        3. Inject the UPI error.
        4. Verify Os log.

        :return: True or False based on Test Case fail or pass.
        """
        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        sdp_obj = ProviderFactory.create(self.si_dbg_cfg, self._log)
        # threshold_value=0x8014- Last bit should high to set threshold and 0x0014 to set threshold to 20.
        # Note: SPR is set in BIOS knobs - and is hardcoded currently to 0x8014 in bios cfg file
        return self.inject_upi_threshold_test(csp=cscripts_obj, sdp=sdp_obj, stress_test=True, threshold_value=0x8014)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StressUpiLlrTransientFaultThreshold.main() else Framework.TEST_RESULT_FAIL)
