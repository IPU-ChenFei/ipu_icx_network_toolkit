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


class Prime95FioAndStressAppStressLinux(ContentBaseTestCase):
    """
    HPQALM ID : H82234
    This class to verify stress and stability after running Stress App, Prime95 and fio stress tool
    """
    TEST_CASE_ID = ["H82234"]
    REGEX_FOR_FIO = r'\serr=\s0'
    REGEX_FOR_STRESS_APP_STATUS = r'\sStatus:\sPASS\s+\S+.*'
    STRESS_APP_EXECUTE_TIME = 20
    CMD_TO_GET_APP_STRESS_LOG = r"cat {}"
    CLEAR_STRESS_LOG = "echo ''>{}"
    STRESS_APP_EXECUTE_CMD = "./stressapptest -s {} -M 256 -m 8 -W -l stress.log "
    ARGUMENT_IN_DICT = {"Join Gimps?": "N", "Your choice:": "15", "Number of torture test threads to run": "0",
                        "Type of torture test to run ": "4", "Customize settings": "Y", "Min FFT size": "4",
                        "Max FFT size": "4096", "Memory to use ": "500G", "Time to run each FFT size": "60",
                        "Run a weaker torture test": "N", "Accept the answers above?": "Y"}
    UNEXPECTED_EXPECT = ["Your choice:", "Join Gimps?", "Customize settings", "Run a weaker torture test"]
    FIO_CMD = r'fio -filename=/dev/sda3 -direct=1 -iodepth 1 -thread -rw=randrw -rwmixread=70 -ioengine=psync -bs=4k ' \
              r'-size=300G -numjobs=50 -runtime=180 -group_reporting -name=randrw_70read_4k'

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new object for Prime95FioAndStressAppStressLinux

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(Prime95FioAndStressAppStressLinux, self).__init__(test_log, arguments, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise NotImplementedError("This Test Cae is Only Supported on Linux")
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._stress_provider = StressAppTestProvider.factory(test_log, cfg_opts, self.os)
        self._mprime_sut_folder_path = self._install_collateral.install_prime95()
        self._install_collateral.install_stress_test_app()

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
        super(Prime95FioAndStressAppStressLinux, self).prepare()
        self._install_collateral.copy_collateral_script(Mprime95ToolConstant.MPRIME95_LINUX_SCRIPT_FILE,
                                                        self._mprime_sut_folder_path.strip())

    def execute(self):
        """"
        This method install validation runner tool and executing and validating LinPack

        :return: True or False
        :raise: if non zero errors raise content_exceptions.TestFail
        """
        self._common_content_lib.execute_sut_cmd(sut_cmd=
                                                 self.CLEAR_STRESS_LOG.format(Mprime95ToolConstant.STRESS_APP_LOG),
                                                 cmd_str="clear stress Log file", execute_timeout=self._command_timeout)
        self._stress_provider.execute_installer_stressapp_test(
            self.STRESS_APP_EXECUTE_CMD.format(self.STRESS_APP_EXECUTE_TIME))
        command_out_put = self._common_content_lib.execute_sut_cmd(sut_cmd=self.CMD_TO_GET_APP_STRESS_LOG.format(
            Mprime95ToolConstant.STRESS_APP_LOG), cmd_str="App Stress Log",  execute_timeout=self._command_timeout)
        self._log.debug("Stress Log Output: {}".format(command_out_put))
        stress_app_status = re.findall(self.REGEX_FOR_STRESS_APP_STATUS, command_out_put)
        self._log.debug(stress_app_status)
        if not stress_app_status:
            raise content_exceptions.TestFail('Stress App Test is Failed')

        self._stress_provider.check_app_running(app_name=Mprime95ToolConstant.STRESS_APP_TEST,
                                                stress_test_command="./" + Mprime95ToolConstant.STRESS_APP_TEST)

        core_count = self._common_content_lib.get_core_count_from_os()[0]
        self._log.debug('Number of cores %d', core_count)
        if self.ARGUMENT_IN_DICT.get("Number of torture test threads to run", None):
            self.ARGUMENT_IN_DICT["Number of torture test threads to run"] = \
                str(core_count)
        (unexpected_expect, successful_test) = self._stress_provider.execute_mprime(
            arguments=self.ARGUMENT_IN_DICT, execution_time=TimeConstants.TWELVE_HOURS_IN_SEC,
            cmd_dir=self._mprime_sut_folder_path.strip())
        self._log.debug("List of Unexpected Expect : {}".format(unexpected_expect))
        self._log.debug("List of captured successful test : {}".format(successful_test))
        if len(successful_test) != core_count:
            raise content_exceptions.TestFail('Torture Test is not started on {} threads'.format(core_count))
        invalid_expect = []
        for expect in unexpected_expect:
            if expect not in self.UNEXPECTED_EXPECT:
                invalid_expect.append(expect)
        self._log.debug("List of invalid expect: {}", invalid_expect)
        if invalid_expect:
            raise content_exceptions.TestFail('%s are Mandatory options for torture Test' % invalid_expect)
        self._stress_provider.check_app_running(app_name=Mprime95ToolConstant.MPRIME_TOOL_NAME,
                                                stress_test_command="./" + Mprime95ToolConstant.MPRIME_TOOL_NAME)

        self._log.info('Install the fio tool...')
        self._install_collateral.install_fio(install_fio_package=True)
        self._log.info('Execute the fio command...')
        fio_cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=self.FIO_CMD, cmd_str=self.FIO_CMD,
                                                                  execute_timeout=self._command_timeout)
        self._log.info("fio command {}, out put : {}".format(self.FIO_CMD, fio_cmd_output.strip()))
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
        super(Prime95FioAndStressAppStressLinux, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if Prime95FioAndStressAppStressLinux.main()
             else Framework.TEST_RESULT_FAIL)
