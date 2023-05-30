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
import re
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral
from src.lib.os_lib import WindowsCommonLib
from src.provider.stressapp_provider import StressAppTestProvider
from src.lib.dtaf_content_constants import TimeConstants
from src.lib.dtaf_content_constants import Mprime95ToolConstant
from src.lib import content_exceptions


class StressWithPrime95OnWin(ContentBaseTestCase):
    """
    HPQALM ID : H81724
    This class to verify stress and stability after running Prime95 stress tool
    """
    STRESS_COMMAND_DICT = {"prime95": "prime95.exe -t"}
    MEMORY_CHECK_TIME_GAP = 5.0

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new object for StressWithPrime95OnWin

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(StressWithPrime95OnWin, self).__init__(test_log, arguments, cfg_opts)

        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._stress_provider = StressAppTestProvider.factory(test_log, cfg_opts, self.os)
        self._log.info("Installing the stress test")
        self._stress_app_path, self._stress_tool_name = self._install_collateral.install_prime95(app_details=True)

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
        super(StressWithPrime95OnWin, self).prepare()

    def execute(self):
        """
        This method install and validate prime95 stress windows

        :return: True or False
        :raise: if non zero errors raise content_exceptions.TestFail
        """
        windows_common_lib = WindowsCommonLib(self._log, self.os)

        # The amount of "Total Physical Memory" reported by System Information utility
        system_memory_info = windows_common_lib.get_system_memory()
        prime95_run_time = self._common_content_configuration.get_memory_prime95_running_time()

        total_memory_data_win = [int(system_memory_info[0].split(":")[1].strip("MB").strip().replace(",", ""))]

        preference_prime_params = ["V24OptionsConverted=1\n", "StressTester=1\n", "UsePrimenet=0\n",
                                   "TortureMem={}\n".format(total_memory_data_win),
                                   "TortureTime=6\n", "TortureWeak=0\n", "[PrimeNet]\n", "Debug=0"]

        self._common_content_lib.create_prime95_preference_txt_file(self._stress_app_path, preference_prime_params)
        self._log.info("installed stress application")
        self._stress_provider.execute_async_stress_tool(self.STRESS_COMMAND_DICT[self._stress_tool_name],
                                                        self._stress_tool_name,
                                                        self._stress_app_path)
        self._log.info("Stress test process has successfully started..")
        self._log.info("Waiting for stress test to be completed in (%d seconds)", prime95_run_time)

        execute_time = time.time() + prime95_run_time
        size_in_gb_previous = 0
        while time.time() < execute_time:
            system_memory_info = windows_common_lib.get_system_memory()
            # Convert to Gigabyte
            total_size_in_gb = int(system_memory_info[0].split(":")[-1].split()[0].replace(",", "")) / 1024
            avail_size_in_gb = int(system_memory_info[1].split(":")[-1].split()[0].replace(",", "")) / 1024
            size_in_gb = total_size_in_gb - avail_size_in_gb
            size_in_gb_current = size_in_gb
            if int(size_in_gb_current) == int(total_size_in_gb):
                self._log.info("Current memory capacity is equal to total memory capacity - "
                               "{} GB == {} GB.".format(size_in_gb_current, total_size_in_gb))

            if size_in_gb_current < size_in_gb_previous:
                raise content_exceptions.TestFail("The used memory is not going up..")
            self._log.info("The used Memory are gradually going up to the target capacity.")
            self._log.info("Current memory capacity being is - {} GB.".format(size_in_gb))
            # Time gap between every memory check..
            time.sleep(self.MEMORY_CHECK_TIME_GAP)
            size_in_gb_previous = size_in_gb_current

        self._stress_provider.kill_stress_tool(self._stress_tool_name,
                                               self.STRESS_COMMAND_DICT[self._stress_tool_name])
        return True

    def cleanup(self, return_status):

        if self.os.is_alive():
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)
        super(StressWithPrime95OnWin, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StressWithPrime95OnWin.main()
             else Framework.TEST_RESULT_FAIL)
