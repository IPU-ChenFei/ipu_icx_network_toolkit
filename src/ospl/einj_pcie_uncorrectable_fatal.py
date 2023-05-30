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
from src.ras.tests.einj_tests.einj_common import EinjCommon


class EinjPcieUncorrectableFatalError(EinjCommon):
    """
    TEST_CASE_ID = ["G59259-PI_RAS_PCIE_einj_pcie_uncorrectable_fatal"] --
    TEST_CASE_ID = ["H81555-PI_RAS_PCIE_einj_pcie_uncorrectable_fatal"] --
    This TestCase Injects a PcieUncorrectableFatalError and Validate if the error is detected.
    """
    _BIOS_CONFIG_FILE = "einj_pcie_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new EinjPcieUncorrectableFatalError object

        :param test_log: Used for debug and info messages
        :param arguments: None
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(EinjPcieUncorrectableFatalError, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

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
        super(EinjPcieUncorrectableFatalError, self).prepare()
        self._common_content_lib.update_micro_code()

    def execute(self):
        """
        Inject the PcieUnCorrectableFatal Error and validate the error log

        :return : True if error detected else False
        """
        return self._ras_einj_obj.einj_inject_and_check(self._ras_einj_obj.EINJ_PCIE_UNCORRECTABLE_FATAL)

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(EinjPcieUncorrectableFatalError, self).cleanup(return_status)
        if self.os.is_alive():
            self._common_content_lib.delete_micro_code()
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if EinjPcieUncorrectableFatalError.main() else Framework.TEST_RESULT_FAIL)
