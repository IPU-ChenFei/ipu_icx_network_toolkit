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

import os
import sys
from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from src.processor.upi_linkspeed_status.upi_common import ProcessorUPIInfo
from src.provider.stressapp_provider import StressAppTestProvider
from src.lib.test_content_logger import TestContentLogger
from src.lib import content_base_test_case, content_exceptions
from src.lib.install_collateral import InstallCollateral


class ProcessorUPILinkSpeedStatus(ProcessorUPIInfo):
    """
    HPQC ID : H77963-PI_Processor_UPI_LinkSpeed_Status_W

    Test and verify if UPI link speed is normal or not.
    """
    TEST_CASE_ID = ["H77963","PI_Processor_UPI_LinkSpeed_Status_W"]
    LOG_FILENAME_BEFORE_STRESS = "upi_check_beforeStress.log"
    LOG_FILENAME_AFTER_STRESS = "upi_check_afterStress.log"
    STEP_DATA_DICT = {
        1: {'step_details': 'Halt the System and Run command log(upi_check_beforeStress.log), Run command '
                            '"upi.topology()", "nolog" and Use "go" command to release processor and '
                            'prepare to run stress tool.',
            'expected_results': 'Executed command without any errors'},
        2: {'step_details': 'Run CPU stress test tool (prime95)',
            'expected_results': 'CPU stress tool running successfully'},
        3: {'step_details': 'use "halt" command to stop processor instruction executing. Run command '
                            '"log("upi_check_afterStress.log") and "upi.topology()" , "nolog" and "go" '
                            'commands to save the logs after stressing the system ',
            'expected_results': 'Saved the upi topology after stressing the system successfully'},
        4: {'step_details': 'Compare UPI logs collected before and After stress',
            'expected_results': 'Successfully Compared UPI logs collected before and After stress'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of ProcessorUPILinkSpeedStatus

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(ProcessorUPILinkSpeedStatus, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._stress_provider = StressAppTestProvider.factory(test_log, os_obj=self.os, cfg_opts=cfg_opts)
        self.log_file_path_before_stress = os.path.join(self.log_dir, self.LOG_FILENAME_BEFORE_STRESS)
        self.log_file_path_after_stress = os.path.join(self.log_dir, self.LOG_FILENAME_AFTER_STRESS)
        self.stress_app_path, self.stress_tool_name = self._install_collateral.install_prime95(app_details=True)

    def prepare(self):  # type: () -> None
        """Test preparation/setup"""
        super(ProcessorUPILinkSpeedStatus, self).prepare()

    def execute(self):
        """
        This method executes the below:
         1:Halt the System and Run command log(upi_check_beforeStress.log)
         2:Run command "upi.topology()", "nolog" and Use "go" command to
           release processor and prepare to run stress tool.
         3:Run CPU stress test tool
         4:use "halt" command to stop processor instruction executing.
         5:Run command log("upi_check_afterStress.log") and "upi.topology()",
           "nolog" and "go" commands to save the logs after stressing the system
         6: Compare UPI logs collected before and After stress

        :raises: contentException.Testfail if failed
        """
        self._test_content_logger.start_step_logger(1)
        self.log_upi_topology(self.log_file_path_before_stress)
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        self._stress_provider.execute_async_stress_tool(self.STRESS_COMMAND_DICT[self.stress_tool_name],
                                                        self.stress_tool_name,
                                                        self.stress_app_path)
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        self.log_upi_topology(self.log_file_path_after_stress)
        self._test_content_logger.end_step_logger(3, return_val=True)

        self._test_content_logger.start_step_logger(4)
        upi_link_speed_dict_before_stress = self.get_upi_linkspeed_details(self.log_file_path_before_stress)
        upi_link_speed_dict_after_stress = self.get_upi_linkspeed_details(self.log_file_path_after_stress)
        self._log.info("UPI Link Speed Before Stressing CPU :{}".format(upi_link_speed_dict_before_stress))
        self._log.info("UPI Link Speed After Stressing CPU :{}".format(upi_link_speed_dict_after_stress))

        if upi_link_speed_dict_before_stress!=upi_link_speed_dict_after_stress:
            raise content_exceptions.TestFail("UPI Link Speed Varied after stressing the CPU")
        self._log.info("UPI Link Speed did not downgrade after stressing the CPU")
        self._test_content_logger.end_step_logger(4, return_val=True)

        return True

    def cleanup(self, return_status):
        """Test Cleanup"""
        self._stress_provider.kill_stress_tool(self.stress_tool_name, self.STRESS_COMMAND_DICT[self.stress_tool_name])
        super(ProcessorUPILinkSpeedStatus, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ProcessorUPILinkSpeedStatus.main() else Framework.TEST_RESULT_FAIL)
