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
from src.ras.tests.einj_tests.einj_common import EinjCommon


class EinjMemCorrectable(EinjCommon):
    """
    Glasgow_id : 59255

    This test case: Injects memory correctable error: 0x08 and validate if the error is detected and corrected.
    """
    _bios_knobs_file = "einj_mem_biosknobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new EinjMemCorrectable object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(EinjMemCorrectable, self).__init__(test_log, arguments, cfg_opts, self._bios_knobs_file)

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
        # installing screen module to run the async commands
        self._install_collateral.screen_package_installation()
        super(EinjMemCorrectable, self).prepare()
        self._common_content_lib.update_micro_code()

    def execute(self):
        return self._ras_einj_obj.einj_inject_and_check(error_type=self._ras_einj_obj.EINJ_MEM_CORRECTABLE)

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(EinjMemCorrectable, self).cleanup(return_status)
        if self.os.is_alive():
            self._common_content_lib.delete_micro_code()
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if EinjMemCorrectable.main() else Framework.TEST_RESULT_FAIL)
