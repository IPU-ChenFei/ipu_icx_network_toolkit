#!/usr/bin/env python
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
from src.hsio.cxl.cxl_ctg_base_test import CxlCtgCommon


class CxlVersionModeNegotiationAPNCscriptsVerification(CxlCtgCommon):
    """
    hsdes_id :  22015202045 CXL Version Mode Negotiation - Cscripts verification.

    As defined in the CXL 2.0 spec below, a CXL device is required to support both 1.1 and 2.0 modes
    (this is the 2.0 spec so 1.1 does not have this requirement)
    This test verifies compliance with this requirement without the use of a protocol analyzer.
    """

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        """
        Create an instance of CxlVersionModeNegotiationAPNCscriptsVerification.

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(CxlVersionModeNegotiationAPNCscriptsVerification, self).__init__(test_log, arguments, cfg_opts, bios_config_file)

    def prepare(self):
        """
        To check whether the host is alive or not.
        """
        super(CxlVersionModeNegotiationAPNCscriptsVerification, self).prepare(self.sdp)

    def execute(self):
        """
        This method is to execute.
        1. Get the specs of CXL device.
        2. Verify specs through cscripts
        3. repeat with cold reboot
        4. repeat with warm reboot
        """
        inventory_input_flag = self._common_content_configuration.get_user_inputs_for_cxl_flag
        if inventory_input_flag:
            self._log.info("Running via inventory inputs")
        else:
            self._log.info("Running via user inputs")
        self.cxl_enumerate_and_discover(inventory_input=inventory_input_flag)
        self.cxl_enumerate_and_discover(reboot="ac_cycle", inventory_input=inventory_input_flag)
        self.cxl_enumerate_and_discover(reboot="warm_reboot", inventory_input=inventory_input_flag)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CxlVersionModeNegotiationAPNCscriptsVerification.main() else Framework.TEST_RESULT_FAIL)
