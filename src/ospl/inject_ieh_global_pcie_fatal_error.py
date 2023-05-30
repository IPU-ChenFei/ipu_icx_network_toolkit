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

from src.ras.tests.pcie.pcie_cscripts_common import PcieCommon


class InjectIehGlobalPcieFatalError(PcieCommon):
    """
    HPQC ID : H101104-PI_RAS_ieh_global_pcie_fatal_error
    Glasgow_id: G58515-PI_RAS_ieh_global_pcie_fatal_error
    This test injects a PCIE Fatal error and verifies the IEH global error status register is set appropriately.
    """
    TEST_CASE_ID = ["H101104", "PI_RAS_ieh_global_pcie_fatal_error", "G58515",
                    "PI_RAS_ieh_global_pcie_fatal_error"]
    _BIOS_CONFIG_FILE = "pcie_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new InjectIehGlobalPcieFatalError object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(InjectIehGlobalPcieFatalError, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

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
        super(InjectIehGlobalPcieFatalError,self).prepare()
        self._common_content_lib.update_micro_code()

    def execute(self):
        """
        This Method is used to execute verify_no_current_ieh_errors method and
        inject_and_verify_ieh_pcie_fatal_error method to verify if there are any previous errors and Inject the
        PCIE Fatal errors

        :return: True
        """
        self.verify_no_current_ieh_errors()
        return self.inject_and_verify_ieh_pcie_fatal_error_and_mask(mask=False)

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self.os.wait_for_os(self.reboot_timeout)
        super(InjectIehGlobalPcieFatalError, self).cleanup(return_status)
        if self.os.is_alive():
            self._common_content_lib.delete_micro_code()
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if InjectIehGlobalPcieFatalError.main() else Framework.TEST_RESULT_FAIL)
