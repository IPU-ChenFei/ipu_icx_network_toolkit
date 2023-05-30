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


class UpiLlrSinglePortTransientErr(UpiLlrCrcCommon):
    """
    Glasgow_id : 58633
    H81571-UPI_LLR_Single_port_transient_fault_with_LLR_successful

    Intel UPI links are capable of detecting various types of correctable and uncorrected errors. Once an error is
    detected, it is reported (logged and signaled) using Intel UPI link MCA banks and platform specific log registers.
    """

    _BIOS_CONFIG_FILE = "upi_llr_16b_single_port_transient_bios_knobs.cfg"
    TEST_CASE_ID = ["H81571", "UPI_LLR_Single_port_transient_fault_with_LLR_successful"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new UpiLlrSinglePortTransientErr object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(UpiLlrSinglePortTransientErr, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

    def prepare(self):
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs that are set.

        :return: None
        """
        super(UpiLlrSinglePortTransientErr, self).prepare()
        self._common_content_lib.update_micro_code()

    def execute(self):
        """
        This method is used to execute inject_upi_port_test method to verify if Upi Llr rolling crc error is injected.

        :return: True or False based on the Output.
        """
        self._log.info("Setting date/time .......")
        self._common_content_lib.set_datetime_on_linux_sut()

        return self.inject_llr_upi_port_test(socket_to_test=0)

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(UpiLlrSinglePortTransientErr, self).cleanup(return_status)
        if self.os.is_alive():
            self._common_content_lib.delete_micro_code()
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if UpiLlrSinglePortTransientErr.main() else Framework.TEST_RESULT_FAIL)
