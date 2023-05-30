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
import os

from dtaf_core.lib.dtaf_constants import Framework
from src.lib.windows_event_log import WindowsEventLog
from src.provider.stressapp_provider import StressAppTestProvider
from src.lib.install_collateral import InstallCollateral
from src.manageability.lib.redfish_test_common import RedFishTestCommon
from src.processor.processor_cpuinfo.processor_cpuinfo_common import ProcessorCPUInfoBase
import src.lib.content_exceptions as content_exception


class ProcessorIntelBurnTestStress(ProcessorCPUInfoBase):
    """
    HPQC ID : H81726_PI_Processor_IntelBurnTest_Stress_W
    Insert full number PHY CPU into stock , open BurnIn Test.exe, set CPU loading to 100% and set the running time
    """
    TEST_CASE_ID = ["H81726_PI_Processor_IntelBurnTest_Stress_W"]
    BURNING_100_WORKLOAD_CONFIG_FILE = "cmdline_cpu_100_workload_windows.bitcfg"
    bit_location = None
    _MIN_NUMBER_OF_SOCKETS = 2

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new  ProcessorIntelBurnTestStress object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(ProcessorIntelBurnTestStress, self).__init__(test_log, arguments, cfg_opts,
                                                           eist_enable_bios_config_file=None,
                                                           eist_disable_bios_config_file=None)

        self.burnin_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                               self.BURNING_100_WORKLOAD_CONFIG_FILE)
        self.burnin_collateral_obj = InstallCollateral(self._log,self.os, cfg_opts)
        self.stress_app_provider = StressAppTestProvider.factory(test_log, os_obj=self.os, cfg_opts=cfg_opts)
        self.obj_redfish = RedFishTestCommon(test_log, arguments, cfg_opts)
        self._windows_event_log = WindowsEventLog(self._log, self.os)

    def prepare(self):
        # type: () -> None
        """
        Setup actions for this test case. Executed before the test logic in execute is called.
        """

        super(ProcessorIntelBurnTestStress, self).prepare()
        self._common_content_lib.clear_all_os_error_logs()
        self.obj_redfish.clear_sel()

    def execute(self):
        """
        1. Verify whether the system supports two or more socket.
        2. To run burnin tool with cpu 100%
        3. Verify with no error in sel and system event logs

        :return: True if test completed successfully, False otherwise.
        :raise: content_exception.TestFail
        """
        self.bit_location = self.burnin_collateral_obj.install_burnin_windows()
        if int(self.get_cpu_info()[self._NUMBER_OF_SOCKETS]) < self._MIN_NUMBER_OF_SOCKETS:
            raise content_exception.TestFail("Failed to execute the test case on this SUT because we would need "
                                             "minimum of 2 Sockets on the platform..")
        self._log.info("Successfully verified that SUT is supporting two or more sockets...")
        burnin_tool_runtime = self._common_content_configuration.burnin_test_execute_time()
        self.stress_app_provider.execute_burnin_test(self.log_dir, burnin_tool_runtime, self.bit_location,
                                                     config_file=self.burnin_config_file)
        self.obj_redfish.check_sel()
        burnin_test_result = []
        whea_logs = self._windows_event_log.get_whea_error_event_logs()

        # Check if there are any errors, warnings of category WHEA found
        if whea_logs is None or len(str(whea_logs)) == 0:
            self._log.info("No WHEA errors or warnings found in Windows System event log...")
            burnin_test_result.append(True)
        else:
            self._log.error("Found WHEA errors or warnings in Windows System event log...")
            self._log.error("WHEA error logs: \n" + str(whea_logs))
            burnin_test_result.append(False)

        return all(burnin_test_result)

if __name__ == '__main__':
    test_result = ProcessorIntelBurnTestStress.main()
    sys.exit(Framework.TEST_RESULT_PASS if test_result else Framework.TEST_RESULT_FAIL)
