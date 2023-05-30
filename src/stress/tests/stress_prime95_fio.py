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
import datetime

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral
from src.provider.stressapp_provider import StressAppTestProvider
from src.lib.dtaf_content_constants import Mprime95ToolConstant
from src.lib.dtaf_content_constants import TimeConstants
from src.lib import content_exceptions


class StressWithPrime95AndFioLinux(ContentBaseTestCase):
    """
    HPQALM ID : H82232-PI_Stress_Prime95_FIO_L
    This class to verify stress and stability after running Prime95 and fio stress tool
    """
    TEST_CASE_ID = ["H82232", "PI_Stress_Prime95_FIO_L"]
    REGEX_FOR_FIO = r'\serr=\s0'
    ARGUMENT_IN_DICT = {"Join Gimps?": "N", "Your choice:": "15", "Number of torture test threads to run": "0",
                        "Type of torture test to run ": "4", "Customize settings": "Y", "Min FFT size": "4",
                        "Max FFT size": "4096", "Memory to use ": "500G", "Time to run each FFT size": "60",
                        "Run a weaker torture test": "N", "Accept the answers above?": "Y"}
    UNEXPECTED_EXPECT = ["Your choice:", "Join Gimps?", "Customize settings", "Run a weaker torture test"]
    FIO_CMD = r'fio -filename=/dev/sda3 -direct=1 -iodepth 1 -thread -rw=randrw -rwmixread=70 -ioengine=psync -bs=4k ' \
              r'-size=300G -numjobs=50 -runtime=180 -group_reporting -name=randrw_70read_4k'

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new object for StressWithPrime95AndFio

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(StressWithPrime95AndFioLinux, self).__init__(test_log, arguments, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise NotImplementedError("This Test Cae is Only Supported on Linux")
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._stress_provider = StressAppTestProvider.factory(test_log, cfg_opts, self.os)
        self._mprime_sut_folder_path = self._install_collateral.install_prime95()
        self._prime95_execution_time = self._common_content_configuration.prime95_execution_time()

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
        super(StressWithPrime95AndFioLinux, self).prepare()
        # installing screen package
        self._install_collateral.screen_package_installation()
        self._install_collateral.copy_collateral_script(Mprime95ToolConstant.MPRIME95_LINUX_SCRIPT_FILE,
                                                        self._mprime_sut_folder_path.strip())

    def execute(self):
        """"
        This method install validate the stress prime95 and fio.

        :return: True or False
        :raise: if non zero errors raise content_exceptions.TestFail
        """
        core_count = self._common_content_lib.get_core_count_from_os()[0]
        self._log.debug('Number of cores %d', core_count)
        if self.ARGUMENT_IN_DICT.get("Number of torture test threads to run", None):
            self.ARGUMENT_IN_DICT["Number of torture test threads to run"] = \
                str(core_count)
        (unexpected_expect, successfull_test) = self._stress_provider.execute_mprime(
            arguments=self.ARGUMENT_IN_DICT, execution_time=(self._prime95_execution_time * 60),
            cmd_dir=self._mprime_sut_folder_path.strip())
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

        self._log.info('Install the fio tool...')
        self._install_collateral.install_fio(install_fio_package=True)
        self._log.info('Execute the fio command...')
        fio_cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=self.FIO_CMD, cmd_str=self.FIO_CMD,
                                                                  execute_timeout=self._command_timeout)
        self._log.info(fio_cmd_output.strip())
        reg_output = re.findall(self.REGEX_FOR_FIO, fio_cmd_output.strip())
        if not len(reg_output):
            raise content_exceptions.TestFail('Un-expected Error Captured in Fio output Log')
        self._log.info('No Error Captured as Expected')
        self._stress_provider.check_app_running(app_name=Mprime95ToolConstant.FIO_TOOL_NAME,
                                                stress_test_command="./" + Mprime95ToolConstant.FIO_TOOL_NAME)

        return True

    def cleanup(self, return_status):
        self._stress_provider.kill_stress_tool(stress_tool_name=Mprime95ToolConstant.MPRIME_TOOL_NAME,
                                               stress_test_command="./" + Mprime95ToolConstant.MPRIME_TOOL_NAME)
        if self.os.is_alive():
            self._common_content_lib.perform_os_reboot(reboot_time_out=self.reboot_timeout)
        super(StressWithPrime95AndFioLinux, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StressWithPrime95AndFioLinux.main()
             else Framework.TEST_RESULT_FAIL)
