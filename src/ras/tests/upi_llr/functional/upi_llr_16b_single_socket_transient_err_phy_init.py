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

from src.ras.tests.upi_llr.upi_llr_common import UpiLlrCrcCommon


class UpiLlrSinglePortTransientErrPhyInit(UpiLlrCrcCommon):
    """
    Glasgow_id : 58634
    HPQALM : "H81569-PI_RAS_UPI_LLR_Single_port_transient_fault_with_LLR_failure_requiring_PHY_re_INIT"

    Intel UPI links are capable of detecting various types of correctable and uncorrected errors. Once an error is
    detected, it is reported (logged and signaled) using Intel UPI link MCA banks and platform specific log registers.
    This test case injects corrected UPI CRC error, checks PythonSV logs and error logged by Windows target.

    """
    _BIOS_CONFIG_FILE = "upi_llr_16b_transient_err_bios_knob.cfg"
    TEST_CASE_ID = ["H81569-PI_RAS_UPI_LLR_Single_port_transient_fault_with_LLR_failure_requiring_PHY_re_INIT"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new UpiLlrSinglePortTransientErrPhyInit object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(UpiLlrSinglePortTransientErrPhyInit, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

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
        super(UpiLlrSinglePortTransientErrPhyInit, self).prepare()

    def execute(self):
        """
        This method is used to execute inject_upi_port_test method to Inject an error

        :return: True or False based on the Output of inject_upi_port_test.
        """
        self._log.info("Setting date/time .......")
        self._common_content_lib.set_datetime_on_linux_sut()

        return self.inject_llr_upi_port_test(init=True, socket_to_test=0)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if UpiLlrSinglePortTransientErrPhyInit.main() else Framework.TEST_RESULT_FAIL)
