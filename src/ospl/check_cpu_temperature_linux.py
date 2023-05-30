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
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib import content_exceptions
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral
from src.lib.dtaf_content_constants import TimeConstants


class CheckAndVerifyCPUTemperatureLinux(ContentBaseTestCase):
    """
    HPALM ID : H81603-PI_Powermanagement_Check_CPU_temperature_L
    Check and verify DTS CPU and Die CPU temperature
    """
    TEST_CASE_ID = ["H81603", "PI_Powermanagement_Check_CPU_temperature_L"]
    IPMI_CMD = "ipmitool sensor list | grep 'degrees C'"
    TEMPERATURE_LIMIT = 50.0

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of CheckAndVerifyCPUTemperatureLinux

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        super(CheckAndVerifyCPUTemperatureLinux, self).__init__(test_log, arguments, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise NotImplementedError("Not implemented for {} OS".format(self.os.os_type))

        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(CheckAndVerifyCPUTemperatureLinux, self).prepare()
        self._common_content_lib.update_micro_code()
        self._install_collateral.install_ipmitool()

    def _get_cpu_temperature_values(self, ipmi_sensor_list):
        """
        This method will add CPU as key and temperature value as value into a dictionary

        :param ipmi_sensor_list: command output
        :return: CPU values
        """
        cpu_info = {}
        # Find CPU from ipmi_sensor_list and store in cpu_info dictionary
        for line in ipmi_sensor_list.strip().split("\n"):
            if "DTS CPU" in line or "Die CPU" in line:
                cpu_info[line.split("|")[0].strip()] = line.split("|")[1].strip()
        self._log.info("CPU info: \n{}".format(cpu_info))
        return cpu_info

    def execute(self):
        """test main logic to check the cpu temperature
        :return: True if cpu values are less than 50
        """

        invalid_matches = []
        self._log.info("Making system idle for {} sec".format(TimeConstants.FIFTEEN_IN_SEC))
        time.sleep(TimeConstants.FIFTEEN_IN_SEC)
        self._log.info("Executing ipmi sensor list command: {}".format(self.IPMI_CMD))
        command_result = self._common_content_lib.execute_sut_cmd(self.IPMI_CMD, "ipmi sensor status list",
                                                                  self._command_timeout)
        self._log.debug("command {} result:\n {}".format(self.IPMI_CMD, command_result))
        cpu_info = self._get_cpu_temperature_values(command_result)
        # Comparing each value of cpu is less that 50 or not
        for key, value in cpu_info.items():
            if float(value) > self.TEMPERATURE_LIMIT:
                invalid_matches.append((key, value))
        if invalid_matches:
            raise content_exceptions.TestFail("Temperature: {} which greater than {} degrees C".
                                              format(invalid_matches, self.TEMPERATURE_LIMIT))

        self._log.info("All CPU temperature is **lesser** than {} degrees C".format(self.TEMPERATURE_LIMIT))

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(CheckAndVerifyCPUTemperatureLinux, self).cleanup(return_status)
        if self.os.is_alive():
            self._common_content_lib.delete_micro_code()
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CheckAndVerifyCPUTemperatureLinux.main() else Framework.TEST_RESULT_FAIL)
