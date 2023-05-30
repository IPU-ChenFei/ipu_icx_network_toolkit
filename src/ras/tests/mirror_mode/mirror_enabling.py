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

from src.ras.tests.mirror_mode.mirror_mode_common import MirrorModeCommon


class MirrorEnabling(MirrorModeCommon):
    """
    Glasgow_id : 59860

    Memory Mirroring is a method of keeping a duplicate (secondary or mirrored) copy of the contents of memory as a
    redundant backup for use if the primary memory fails. The mirrored copy of the memory is stored in memory of the
    same processor socket. Dynamic (without reboot) fail-over to the mirrored DIMMs is transparent to the OS and
    applications.

    Primary usage model for this feature is to provide more reliable memory. Such memory space will be fault tolerant
     in case of single bit, multi-bit, single device, multi-device faults.
    """
    _BIOS_CONFIG_FILE = "mirror_mode_common_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new MirrorEnabling object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(MirrorEnabling, self).__init__(test_log, arguments, cfg_opts,
                                             self._BIOS_CONFIG_FILE)

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
        self._common_content_lib.clear_all_os_error_logs()  # This Method is used to Clear All OS Logs.
        self._log.info("Set the Bios Knobs to Default Settings")
        self._bios.default_bios_settings()  # To set the Bios Knobs to its default mode.
        self._log.info("Set the Bios Knobs as per our Test Case Requirements")
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._log.info("Bios Knobs are Set as per our TestCase and Reboot to Apply the Settings")
        self._os.reboot(int(self._reboot_timeout_in_sec))  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.

    def execute(self):
        """
        This Method is used to execute verify_whether_mirror_mode_enabled to verify if mirror mode is successfully
        Enabled or not by Enabling the Bios Knob.

        :return: True if verify_whether_mirror_mode_enabled method is executed Successfully.
        """
        return self.verify_whether_mirror_mode_enabled()

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MirrorEnabling.main() else Framework.TEST_RESULT_FAIL)
