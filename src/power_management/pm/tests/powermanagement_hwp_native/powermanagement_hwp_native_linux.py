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
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.dtaf_content_constants import TimeConstants


class PowerManagementHWPNativeLinux(ContentBaseTestCase):
    """
    HPALM ID : H81627-PI_Powermanagement_HWP_Native_L
    Install Solar HWP Native and run the tool
    """
    TEST_CASE_ID = ["H81627", "PI_Powermanagement_HWP_Native_L"]
    _BIOS_CONFIG_FILE = "pm_hwp_native.cfg"
    HOST_XML_FILE_NAME = "P0_PN.xml"
    EXECUTE_SOLAR = "./solar.sh /cfg {}".format(HOST_XML_FILE_NAME)
    SOLAR_PASS_FLOW = ["Solar Exiting. All flows Passing.", "HWP finished: PASS"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of PowerManagementHWPNativeLinux

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        super(PowerManagementHWPNativeLinux, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)
        if self.os.os_type != OperatingSystems.LINUX:
            raise NotImplementedError("Not implemented for {} OS".format(self.os.os_type))

        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(PowerManagementHWPNativeLinux, self).prepare()

    def execute(self):
        """
        test main logic to copy solar toot to sut and install it and also check and clear mce and dmesg logs.
        """
        # Copy solar.tar file to sut.
        sut_folder_path = self._install_collateral.install_solar_hwp_native()
        # Copy P0_PN.xml file into  solar folder in sut.
        host_folder_path = self._install_collateral.download_tool_to_host(self.HOST_XML_FILE_NAME)
        self.os.copy_local_file_to_sut(host_folder_path, sut_folder_path)

        self._log.info("Copied {} file into sut under path :{}".format(self.HOST_XML_FILE_NAME, sut_folder_path))

        # Run solar using the command ./solar.sh /cfg P0_PN.xml
        self._log.info("Executing solar HWP native command:{}".format(self.EXECUTE_SOLAR))
        command_result = self._common_content_lib.execute_sut_cmd(self.EXECUTE_SOLAR, self.EXECUTE_SOLAR,
                                                                  TimeConstants.ONE_HOUR_IN_SEC,
                                                                  sut_folder_path)
        self._log.debug("Successfully ran Solar HWP result: \n{}".format(command_result))
        # Checking for pass info in command result
        for pass_info in self.SOLAR_PASS_FLOW:
            if pass_info not in command_result:
                raise content_exceptions.TestFail("Solar execution failed")

        errors = self._common_content_lib.check_if_mce_errors()
        self._log.debug("MCE errors: %s", errors)
        if errors:
            raise content_exceptions.TestFail("There are MCE errors after "
                                              "Solar HWP Native execution: %s" % errors)

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PowerManagementHWPNativeLinux, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PowerManagementHWPNativeLinux.main() else Framework.TEST_RESULT_FAIL)
