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
import re

from dtaf_core.lib.dtaf_constants import Framework

from src.lib import content_exceptions
from src.power_management.pm.tests.intel_sst.intel_sst_common import IntelSSTCommon, IntelSSTConfig


class PowermanagementISSBiosCheckoutL(IntelSSTCommon):
    """
    This test case is used for Intel speed select feature validation.
    HPALM ID : H81614
    """
    TEST_CASE_ID = ["H81614", "PI_Powermanagement_ISS_BIOS_Checkout_L"]
    REGEX_SST_PP = r"Intel.*SST-PP.*is\ssupported"
    TDP_CONFIG = IntelSSTConfig.BASE
    TDP_LEVEL = '0'
    _BIOS_CONFIG_FILE = "power_management_iss_bios_checkout.cfg"
    PWRPL1_REGEX = "Pkg\sPower\sLimit1\(Watt\).*::\s+([0-9]+)"
    TJ_MAX_REGEX = "TJ-Max.*::\s+([0-9]+)"
    CPU_INFO = "lscpu"
    CORE_SOCKET = "Core\(s\)\sper socket:\s+([0-9]+)"
    SOCKET = "Socket\(s\):\s+([0-9]+)"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of PowermanagementISSTDPConfig1

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        self.bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self._BIOS_CONFIG_FILE)
        test_log.debug("Bios config file: %s", self.bios_config_file)
        super(PowermanagementISSBiosCheckoutL, self).__init__(test_log, arguments, cfg_opts,
                                                          bios_config_file_path=self.bios_config_file)

        self.check_is_iss_supported()

    def check_is_iss_supported(self):
        """
        This method is to check whether ISS support on SUT
        raise : raise exception if does not supports
        """
        intel_speed_select_info_cmd = "intel-speed-select -info"
        intel_speed_select_info_res_temp = self.os.execute(intel_speed_select_info_cmd, self._command_timeout)
        intel_speed_select_info_res = intel_speed_select_info_res_temp.stdout + "\n" + intel_speed_select_info_res_temp.stderr
        regex_res = re.findall(self.REGEX_SST_PP, intel_speed_select_info_res)
        if len(regex_res) == 0:
            raise content_exceptions.TestFail("SST PP does not supported in the SKU")

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(PowermanagementISSBiosCheckoutL, self).prepare()

    def execute(self):
        """test main logic to check the functionality"""
        errors = []
        tdp_config_value = self.get_tdp_config_value()
        if tdp_config_value not in self.TDP_CONFIG_DICT[self.TDP_CONFIG]:
            raise content_exceptions.TestFail("Intel SST config value is not set as expected")
        intel_sst_bios_details = self.get_intel_sst_info_bios(self.TDP_CONFIG)
        self._log.info("Intel ssp value from bios:{}".format(intel_sst_bios_details))
        intel_sst_pythonsv_details = self.get_intel_sst_info_pythonsv(self.TDP_CONFIG)

        self._log.info("PythonSV values from bios:{}".format(intel_sst_pythonsv_details))

        self._log.info("Verifying core count")
        if int(intel_sst_bios_details[self.TDP_LEVEL][self.IntelSSTTable.CORE_COUNT]) != int(intel_sst_pythonsv_details
                                                                                  [self.IntelSSTTable.CORE_COUNT]):
            errors.append("PythonSV(%s) and Bios(%s) core counts are not matching" % (intel_sst_pythonsv_details
                                                                                      [self.IntelSSTTable.CORE_COUNT],
                                                                                      intel_sst_bios_details[str(self.TDP_LEVEL)]
                                                                                      [self.IntelSSTTable.CORE_COUNT]))
        self._log.info("Verifying package TDP value")
        if int(intel_sst_bios_details[str(self.TDP_LEVEL)][self.IntelSSTTable.PACKAGE_TDP]) != int(intel_sst_pythonsv_details
                                                                                   [self.IntelSSTTable.PACKAGE_TDP]/8):
            errors.append("PythonSV(%s) and Bios(%s) package TDPs are not matching"
                          % (intel_sst_pythonsv_details[self.IntelSSTTable.PACKAGE_TDP],                             intel_sst_bios_details['3'][self.IntelSSTTable.PACKAGE_TDP]))
        self._log.info("Verifying P1 ratio value")
        if int(intel_sst_bios_details[str(self.TDP_LEVEL)][self.IntelSSTTable.P1_RATIO]) != int(
                intel_sst_pythonsv_details[self.IntelSSTTable.P1_RATIO]):
            errors.append("PythonSV(%s) and Bios(%s) P1 ratios are not matching" % (
                intel_sst_pythonsv_details[self.IntelSSTTable.P1_RATIO],
                intel_sst_bios_details[str(self.TDP_LEVEL)][self.IntelSSTTable.P1_RATIO]))

        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self._log.info("Waiting for system to boot up to os")
        self.os.wait_for_os(self.reboot_timeout)

        cpu_info_result = self._common_content_lib.execute_sut_cmd(self.CPU_INFO, self.CPU_INFO, self._command_timeout)
        self._log.debug("{} command result:{}".format(self.CPU_INFO, cpu_info_result))

        if not re.search(self.SOCKET, cpu_info_result):
            raise content_exceptions.TestFail("Failed to get socket info from Solar tool")

        socket = int(re.search(self.SOCKET, cpu_info_result).group(1))

        if not re.search(self.CORE_SOCKET, cpu_info_result):
            raise content_exceptions.TestFail("Failed to get core per socket info from Solar tool")
        core_socket = int(re.search(self.CORE_SOCKET, cpu_info_result).group(1))

        self._log.info("Core(s) per socket:{}".format(core_socket))
        self._log.info("Socket(s):{}".format(socket))

        if errors:
            raise content_exceptions.TestFail("\n".join(errors))

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PowermanagementISSBiosCheckoutL, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PowermanagementISSBiosCheckoutL.main() else Framework.TEST_RESULT_FAIL)
