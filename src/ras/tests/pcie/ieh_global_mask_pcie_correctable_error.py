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


class IehGlobalMaskPcieCorrectableError(PcieCommon):
    """
    Glasgow_id : 58516
    This test injects a PCIE Correctable Error and verifies the IEH global error status register if error is masked.
    """
    _BIOS_CONFIG_FILE = "pcie_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new IehGlobalMaskPcieCorrectableError object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(IehGlobalMaskPcieCorrectableError, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

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
        if self._cscripts.silicon_cpu_family in self._common_content_lib.SILICON_10NM_CPU:
            self._pcie_telemetry.collect_io_telemetry_to_csv("IehGlobalMaskPcieCorrectableError", 0)
            super(IehGlobalMaskPcieCorrectableError, self).prepare()
        else:
            log_error = "Not Implemented for other than 10nm"
            self._log.error(log_error)
            raise NotImplementedError(log_error)

    def execute(self):
        """
        1. verify_no_current_ieh_errors - To check if there are any Previous Errors
        2. enable_ieh_mask - Enabling the Mask by Changing the Register Access and Reverting the Access after Enabling.
        3. inject_ieh_global_mask_pcie_correctable_error - Inject Pcie Correctable Error and Check if the
         Error is Masked

        :return: True or False
        """
        self.verify_no_current_ieh_errors()
        self.enable_ieh_mask(error_type="correctable")
        return self.inject_ieh_global_mask_pcie_correctable_error()

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        self._pcie_telemetry.collect_io_telemetry_to_csv("IehGlobalMaskPcieCorrectableError", 1)
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self.os.wait_for_os(self.reboot_timeout)
        super(IehGlobalMaskPcieCorrectableError, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if IehGlobalMaskPcieCorrectableError.main() else Framework.TEST_RESULT_FAIL)
