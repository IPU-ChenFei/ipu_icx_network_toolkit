#!/usr/bin/env python
###############################################################################
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
###############################################################################

import sys

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.lib import content_exceptions
from src.lib.bios_util import SerialBiosUtil, ItpXmlCli
from src.lib.content_base_test_case import ContentBaseTestCase


class ResetFromBiosSetupPageLinux(ContentBaseTestCase):
    """
    HPALM ID : H92436-PI_RESET_From_Bios_Setup_Page_L
    PHOENIX ID : 18016909529-PI_RESET_From_Bios_Setup_Page_L

    Enter into BIOS Page and Do a Reset from BIOS and Verify.
    """
    TEST_CASE_ID = ["H92436","PI_RESET_From_Bios_Setup_Page_L"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of ResetFromBiosSetupPageLinux

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        super(ResetFromBiosSetupPageLinux, self).__init__(test_log, arguments, cfg_opts)
        self._serial_bios_util = SerialBiosUtil(self.ac_power, test_log, self._common_content_lib, cfg_opts)
        self._csp_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(ResetFromBiosSetupPageLinux, self).prepare()

    def execute(self):
        """test main logic to check the functionality"""
        # Check current boot order
        self._csp = ProviderFactory.create(self._csp_cfg, self._log)
        self.itp_xml_cli_util = ItpXmlCli(self._log, self._cfg)
        self.previous_boot_oder = self.itp_xml_cli_util.get_current_boot_order_string()
        self._log.info("Boot Order before Reset : {}".format(self.previous_boot_oder))
        self._log.info("Boot to BIOS")
        success, msg = self._serial_bios_util.navigate_bios_menu()
        if not success:
            raise content_exceptions.TestFail("SUT Failed to boot to BIOS!")
        else:
            self._serial_bios_util.reset_sut()
        self.os.wait_for_os(self.reboot_timeout)
        self.current_boot_order = self.itp_xml_cli_util.get_current_boot_order_string()
        self._log.info("Boot Order after Reset : {}".format(self.current_boot_order))
        if str(self.current_boot_order) != str(self.previous_boot_oder):
            raise content_exceptions.TestFail("The Boot order before Reset is different from the current Boot order!")

        self._log.info("Test has been completed successfully!")
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(ResetFromBiosSetupPageLinux, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ResetFromBiosSetupPageLinux.main() else Framework.TEST_RESULT_FAIL)
