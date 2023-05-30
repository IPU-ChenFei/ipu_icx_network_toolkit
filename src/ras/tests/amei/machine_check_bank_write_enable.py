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

from src.ras.tests.amei.amei_common import AmeiCommon


class MachineCheckBankWriteEnable(AmeiCommon):
    """
    Glasgow_id : G58299-_83_01_01_machine_check_bank_write_enabled

    Asynchronous Machine-check Error Injection (AMEI) provides capability to verify UEFI FW and SW based error
    handlers by implanting errors within the various machinecheck banks and then triggering
    CMCI/MCERR/MSMI/CSMI events.
    This test verifies Machine Check Bank Write is enabled.
    Test case flow:
    -Verify Machine Check Bank Write is enabled properly by writing 0x1E3 to 1 and reading the data back
    """
    TEST_CASE_ID = ["G58299", "_83_01_01_machine_check_bank_write_enabled"]
    _BIOS_CONFIG_FILE = "machine_check_bank_write_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new MachineCheckBankWriteEnable object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(MachineCheckBankWriteEnable, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs whether they updated properly.

        :return: None
        """
        super(MachineCheckBankWriteEnable, self).prepare()

    def execute(self):
        """
        executing check_machine_check_bank_write_enable method to verify whether machine check bank write is
        enabled or not.

        :return: True if check_machine_check_bank_write_enable method is executed Successfully.
        """
        return self.check_machine_check_bank_write_enable()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MachineCheckBankWriteEnable.main() else Framework.TEST_RESULT_FAIL)
