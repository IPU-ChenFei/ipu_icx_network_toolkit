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
import os

from dtaf_core.lib.dtaf_constants import Framework
from src.lib.bios_util import BiosUtil

from src.hsio.upi.hsio_upi_common import HsioUpiCommon


class UpiMaxLinkSpeed(HsioUpiCommon):
    """
    hsdes id: 22012841922 upi_max_linkspeed
    HSD ID: 1509819974 PI_upi_max_linkspeed
    This test modifies BIOS to ensure maximum UPI link speed is set and verifies through cscripts.
    """
    _BIOS_CONFIG_FILE = "upi_max_linkspeed_"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new UpiMaxLinkSpeed object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(UpiMaxLinkSpeed, self).__init__(
            test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)
        cpu_family = self._common_content_lib.get_platform_family().lower()
        self.bios_config_file_path = self._BIOS_CONFIG_FILE + cpu_family + ".cfg"
        self.bios_config_file_path = os.path.join(self.bios_dir_path, self.bios_config_file_path)

        self._log.info("Bios file selected: {}".format(self.bios_config_file_path))
        self.bios_util = BiosUtil(cfg_opts,
                                  bios_config_file=self.bios_config_file_path,
                                  bios_obj=self.bios, common_content_lib=self._common_content_lib,
                                  log=self._log)

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
        super(UpiMaxLinkSpeed, self).prepare()

    def execute(self):

        max_link_speed_set = self.verify_max_link_speed_set()
        if not max_link_speed_set:
            self.verify_no_upi_errors_indicated()
            return False

        return self.verify_no_upi_errors_indicated()


if __name__ == "__main__":

    sys.exit(Framework.TEST_RESULT_PASS if UpiMaxLinkSpeed.main()
             else Framework.TEST_RESULT_FAIL)
