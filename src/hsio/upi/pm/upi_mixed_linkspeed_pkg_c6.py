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
import time

from dtaf_core.lib.dtaf_constants import Framework
from src.lib.bios_util import BiosUtil

from src.hsio.upi.hsio_upi_common import HsioUpiCommon
from src.ras.tests.io_power_management.io_power_management_common import IoPmCommon


class UpiMixedLinkSpeedPkgC6(HsioUpiCommon, IoPmCommon):
    """
    hsdes id: 22013008131 upi_non_ras_mixed_linkspeed with package C6
    This test modifies BIOS to ensure mixed UPI link speeds is set with package C6 state enabled
    and verifies through cscripts at idle

    This test assumes that number of sockets was provided in the system_configuration.xml.
    i.e. system_configuration.xml must have a new value: /suts/sut/silicon/cpu/num_of_sockets
    """
    _BIOS_CONFIG_FILE = "upi_mixed_linkspeed_"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new UpiMixedLinkSpeedPkgC6 object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(UpiMixedLinkSpeedPkgC6, self).__init__(
            test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)
        socket_num = self._common_content_lib.get_platform_number_of_sockets()
        cpu_family = self._common_content_lib.get_platform_family().lower()
        self.bios_config_file_path = self._BIOS_CONFIG_FILE + cpu_family + "_" \
                                     + str(socket_num) + "s_pkg_c6.cfg"
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
        super(UpiMixedLinkSpeedPkgC6, self).prepare()

    def execute(self):

        self.install_ptu_on_sut_linux()
        time.sleep(self.PACKAGE_C6_STATE_DELAY_SEC)
        if not self.ptu_check_c6_state_linux():
            self._log.error("System not in c6 state!")
            return False

        self.print_upi_topology()

        return self.run_upi_package_c6_test(self._upi_checks.MIXED_LINK_SPEED,
                                            test_duration_sec=self.C6_STATE_TEST_RUNTIME_SEC)


if __name__ == "__main__":

    sys.exit(Framework.TEST_RESULT_PASS if UpiMixedLinkSpeedPkgC6.main()
             else Framework.TEST_RESULT_FAIL)
