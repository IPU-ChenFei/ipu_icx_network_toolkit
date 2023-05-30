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

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral
from src.provider.stressapp_provider import StressAppTestProvider
from src.lib.dtaf_content_constants import TimeConstants
from src.lib.dtaf_content_constants import Mprime95ToolConstant
from src.lib import content_exceptions


class StressWithPrime95OnLinux(ContentBaseTestCase):
    """
    HPQALM ID : H79585-PI_Processor_Prime95_Stress_L
    This class to verify stress and stability after running Prime95 stress tool
    """
    TEST_CASE_ID = ["H79585-PI_Processor_Prime95_Stress_L"]
    ARGUMENT_IN_DICT = {"Join Gimps?": "N", "Your choice": "15", "Number of torture test threads to run": "0",
                        "Type of torture test to run ": "2", "Customize settings": "N", "Run a weaker torture test":
                            "N", "Accept the answers above?": "Y"}
    UNEXPECTED_EXPECT = ["Your choice", "Join Gimps?", "Customize settings", "Run a weaker torture test"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new object for StressWithPrime95AndFio

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(StressWithPrime95OnLinux, self).__init__(test_log, arguments, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise NotImplementedError("This Test Cae is Only Supported on Linux")
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._stress_provider = StressAppTestProvider.factory(test_log, cfg_opts, self.os)
        self._mprime_sut_folder_path = self._install_collateral.install_prime95()

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
        super(StressWithPrime95OnLinux, self).prepare()
        self._common_content_lib.update_micro_code()
        self._install_collateral.copy_collateral_script(Mprime95ToolConstant.MPRIME95_LINUX_SCRIPT_FILE,
                                                        self._mprime_sut_folder_path.strip())

    def execute(self):
        """
        This method install and validate prime stress linux

        :return: True or False
        :raise: if non zero errors raise content_exceptions.TestFail
        """
        core_count = self._common_content_lib.get_core_count_from_os()[0]
        self._log.debug('Number of cores %d', core_count)
        if self.ARGUMENT_IN_DICT.get("Number of torture test threads to run", None):
            self.ARGUMENT_IN_DICT["Number of torture test threads to run"] = \
                str(core_count)
        (unexpected_expect, successfull_test) = \
            self._stress_provider.execute_mprime(arguments=self.ARGUMENT_IN_DICT, execution_time=
                                                 120, cmd_dir=
                                                 self._mprime_sut_folder_path.strip())
        self._log.debug(unexpected_expect)
        self._log.debug(successfull_test)
        if len(successfull_test) != core_count:
            raise content_exceptions.TestFail('Torture Test is not started on {} threads'.format(core_count))
        invalid_expect = []
        for expect in unexpected_expect:
            if expect not in self.UNEXPECTED_EXPECT:
                invalid_expect.append(expect)
        self._log.debug(invalid_expect)
        if invalid_expect:
            raise content_exceptions.TestFail('%s are Mandatory options for torture Test' % invalid_expect)
        self._stress_provider.check_app_running(app_name=Mprime95ToolConstant.MPRIME_TOOL_NAME,
                                                stress_test_command="./" + Mprime95ToolConstant.MPRIME_TOOL_NAME)

        return True

    def cleanup(self, return_status):
        self._stress_provider.kill_stress_tool(stress_tool_name=Mprime95ToolConstant.MPRIME_TOOL_NAME,
                                               stress_test_command="./" + Mprime95ToolConstant.MPRIME_TOOL_NAME)
        if self.os.is_alive():
            self._common_content_lib.delete_micro_code()
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)
        super(StressWithPrime95OnLinux, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StressWithPrime95OnLinux.main()
             else Framework.TEST_RESULT_FAIL)
