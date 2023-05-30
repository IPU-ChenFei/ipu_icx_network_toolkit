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
from dtaf_core.lib.configuration import ConfigurationHelper
from dtaf_core.providers.provider_factory import ProviderFactory

from src.lib import content_exceptions
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral
from src.lib.dtaf_content_constants import TimeConstants, CpuFanSpeedConstants


class PiPowerManagementCheckCPUCoresTemperatureLinux(ContentBaseTestCase):
    """
    Pheonix ID : 18016909531-PI_Powermanagement_Check_CPU_PCH_temperature_L

    To Check and verify CPU cores temperature
    """
    TEST_CASE_ID = ["18016909531", "PI_Powermanagement_Check_CPU_PCH_temperature_L"]
    IPMI_CMD = "ipmitool sensor list | grep 'Core.* CPU'"
    TEMPERATURE_LIMIT = 70.0

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of PiPowerManagementCheckCPUCoresTemperatureLinux

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        super(PiPowerManagementCheckCPUCoresTemperatureLinux, self).__init__(test_log, arguments, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise NotImplementedError("Not implemented for {} OS".format(self.os.os_type))

        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        bmc_console_cfg = ConfigurationHelper.filter_provider_config(sut=self.sut, provider_name=r"console",
                                                                     attrib=dict(id="BMC"))
        bmc_console_cfg = bmc_console_cfg[0]
        self._bmc_console = ProviderFactory.create(bmc_console_cfg, test_log)
        self._speed = CpuFanSpeedConstants.FAN_SPEED_100_PERCENT

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(PiPowerManagementCheckCPUCoresTemperatureLinux, self).prepare()
        self._install_collateral.install_ipmitool()

        self._common_content_lib.set_and_verify_cpu_fan_speed(self._bmc_console, self._speed)
        self._log.info("CPU Fan running at 100% RPM ....")

    def _get_cpu_core_temperature_values(self, ipmi_sensor_list):
        """
        This method will add CPU core as a key and temperature value as value into a dictionary

        :param ipmi_sensor_list: command output
        :return: CPU values
        """
        cpu_cores_info = {}
        # From ipmitool sensor list | grep 'Core.* CPU' and store in cpu cores info in a dictionary
        for line in ipmi_sensor_list.strip().split("\n"):
            cpu_cores_info[line.split("|")[0].strip()] = line.split("|")[1].strip()
        self._log.info("CPU Cores information : \n{}".format(cpu_cores_info))
        return cpu_cores_info

    def execute(self):
        """test main logic to check the cpu cores temperature
        :return: True if cpu values are less than 70
        """

        invalid_matches = []
        self._log.info("Making system idle for {} sec".format(TimeConstants.FIFTEEN_IN_SEC))
        time.sleep(TimeConstants.FIFTEEN_IN_SEC)
        self._log.info("Executing ipmitool sensor list command for CPU cores : {}".format(self.IPMI_CMD))
        command_result = self._common_content_lib.execute_sut_cmd(
            self.IPMI_CMD, "ipmi sensor status list for CPU cores", self._command_timeout)
        self._log.debug("command {} result:\n {}".format(self.IPMI_CMD, command_result))
        cpu_info = self._get_cpu_core_temperature_values(command_result)
        # Comparing each value of cpu is less that 70 or not
        for key, value in cpu_info.items():
            if float(value) > self.TEMPERATURE_LIMIT:
                invalid_matches.append((key, value))
        if invalid_matches:
            raise content_exceptions.TestFail("Temperature: {} which greater than {} degrees C".
                                              format(invalid_matches, self.TEMPERATURE_LIMIT))

        self._log.info("All CPU Cores temperature is **lesser** than {} degrees C".format(self.TEMPERATURE_LIMIT))

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PiPowerManagementCheckCPUCoresTemperatureLinux, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS
             if PiPowerManagementCheckCPUCoresTemperatureLinux.main() else Framework.TEST_RESULT_FAIL)
