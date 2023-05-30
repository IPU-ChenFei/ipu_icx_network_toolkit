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
import os

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems
from src.lib import content_exceptions
from src.lib.content_base_test_case import ContentBaseTestCase
from src.provider.solar_provider import SolarProvider
from src.lib.dtaf_content_constants import SolarHwpConstants


class PowerManagementPowerLegacyPstateAllSolarWindows(ContentBaseTestCase):
    """
    HPALM ID : H87937
    Install Solar tool and run the tool
    """
    TEST_CASE_ID = ["H87937", "PI_Powermanagement_Power_Legacy_Pstate_All_Solar_W"]

    SOLAR_PASS_FLOW = ["Solar Exiting. All flows Passing.", "PSTATES finished: PASS",
                       "PSTATES:  Failing Iterations: 0 (Tolerance: 20)."]
    BIOS_CONFIG_FILE_NAME = "pm_hwp_disable.cfg"
    HOST_XML_FILE_NAME = "Pstate_All.xml"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of PowerManagementPowerLegacyPstateAllSolarWindows

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        self.hwp_disable_bios = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                             self.BIOS_CONFIG_FILE_NAME)
        super(PowerManagementPowerLegacyPstateAllSolarWindows, self).__init__(test_log, arguments, cfg_opts,
                                                                              self.hwp_disable_bios)
        if self.os.os_type != OperatingSystems.WINDOWS:
            raise NotImplementedError("This Test is Supported only on Windows")
        self._solar_provider = SolarProvider.factory(test_log, cfg_opts, self.os)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(PowerManagementPowerLegacyPstateAllSolarWindows, self).prepare()

    def execute(self):
        """
        test main logic to copy solar tool to sut and install it and check whea logs.
        """

        # To clear mce error logs
        self._log.debug("Cleare MCE Logs")
        self._common_content_lib.clear_mce_errors()

        sut_folder_path = self._solar_provider.install_solar_tool()

        result = self._solar_provider.execute_installer_solar_test(xml_file_name=self.HOST_XML_FILE_NAME,
                                                                   sut_folder_path=sut_folder_path,
                                                                   command=SolarHwpConstants.SOLAR_WINDOWS_COMMAND)

        self._solar_provider.verify_solar_tool_output(result, self.SOLAR_PASS_FLOW)

        errors = self._common_content_lib.check_if_mce_errors()
        self._log.debug("MCE errors: %s", errors)
        if errors:
            raise content_exceptions.TestFail("There are MCE errors after "
                                              "Solar execution: %s" % errors)

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PowerManagementPowerLegacyPstateAllSolarWindows, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PowerManagementPowerLegacyPstateAllSolarWindows.main()
             else Framework.TEST_RESULT_FAIL)
