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

import sys,os
import threading
from src.interop.lib.network_storage_common import SupportMethods
from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral
from src.provider.stressapp_provider import StressAppTestProvider
from src.lib.dtaf_content_constants import Mprime95ToolConstant
from src.lib.content_configuration import ContentConfiguration
from src.lib.test_content_logger import TestContentLogger
from src.interop.lib.thread_log_util import ThreadLogUtil



class NetworkCpuMemoryLtssm(ContentBaseTestCase):
    """
    HPQALM ID : 16014289655-Network Traffic on Host (iperf)+ CPU ( Prime95), Memory Stress(StresApp)+ PCIe Randomization scripts(LTSSM)
    This class to verify stress and stability after running Prime95, Stressapp, iperf and LTSSM tool
    """
    TEST_CASE_ID = ["16014289655","Network Traffic on Host (iperf)+ CPU ( Prime95), Memory Stress(StresApp)+ PCIe Randomization scripts(LTSSM)"]
    step_data_dict = {
                      1: {'step_details': 'bios settings',
                            'expected_results': 'bios settings done successfully'},
                      2: {'step_details': 'install Prime95',
                          'expected_results': 'prime95 Installed successfully'},
                      3: {'step_details': 'install LTSSM',
                          'expected_results': 'LTSSM Installed successfully'},
                      4: {'step_details': 'stressapp installation check',
                          'expected_results': 'stressapp installation check successful'},
                      5: {'step_details': 'Iperf Installation',
                          'expected_results': 'Iperf installed successfully'},
                      6: {'step_details': 'Run 4 workloads',
                          'expected_results': 'Ran 4 workloads successfully'},
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new object for NetworkCpuMemoryLtssm

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(NetworkCpuMemoryLtssm, self).__init__(test_log, arguments, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self.cpu_stress_reqd = self._common_content_configuration.get_cpu_stress_enabled().strip()
        self.memory_stress_reqd = self._common_content_configuration.get_memory_stress_enabled().strip()
        self.ltssm_test_reqd = self._common_content_configuration.get_storage_enabled().strip()
        self.network_traffic_reqd = self._common_content_configuration.get_network_enabled().strip()
        if self.os.os_type != OperatingSystems.LINUX:
            raise NotImplementedError("This Test Cae is Only Supported on Linux")
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._support_methods = SupportMethods(self._log, self.os, cfg_opts)
        self._stress_provider = StressAppTestProvider.factory(test_log, cfg_opts, self.os)
        self._thread_logger = ThreadLogUtil(self._log, self.os, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        1. Check Stressapptest installation
        2. Check Iperf installation
        3. Install StressTest app
        4. Reboot the SUT to apply the new bios settings.
        5. Install LTSSM and Iperf if not present

        :return: None
        """
        self._test_content_logger.start_step_logger(1)
        super(NetworkCpuMemoryLtssm, self).prepare()
        self._test_content_logger.end_step_logger(1, return_val=True)
        # To install screen package
        self._install_collateral.screen_package_installation()
        if self.cpu_stress_reqd.lower() == 'true':
            self._test_content_logger.start_step_logger(2)
            self._mprime_sut_folder_path = self._install_collateral.install_prime95()
            self._install_collateral.copy_collateral_script(Mprime95ToolConstant.MPRIME95_LINUX_SCRIPT_FILE,
                                                        self._mprime_sut_folder_path.strip())
            self._test_content_logger.end_step_logger(2, return_val=True)
        # self._install_collateral.install_stress_test_app()
        if self.ltssm_test_reqd.lower() == 'true':
            self._test_content_logger.start_step_logger(3)
            self._ltssm_folder_path = self._install_collateral.install_ltssm_tool()
            self._install_collateral.install_ltssm_tool()
            self._test_content_logger.end_step_logger(3, return_val=True)

        if self.memory_stress_reqd.lower() == 'true':
            self._test_content_logger.start_step_logger(4)
            self.stdout_msg = self._support_methods.stressapptest_installation_check()
            memory_msg = self._support_methods.memory_check_before_stressapptest()
            self._test_content_logger.end_step_logger(4, return_val=True)

        if self.network_traffic_reqd.lower() == 'true':
            self._test_content_logger.start_step_logger(5)
            echo_op = self._support_methods.sut_iperf_check()
            if not echo_op:
                self._install_collateral.install_iperf_on_linux()
            self._test_content_logger.end_step_logger(5, return_val=True)

    def execute(self):
        """
        This method is used to run the Memory and CPU stress, run network traffic and LTSSM tool

        :return: True or False
        :raise: if non zero errors raise content_exceptions.TestFail
        """
        self._log.info("Creating workload threads")
        cpu_stress_thread = threading.Thread(target= self._support_methods.cpu_stress_mprime, args= (self._mprime_sut_folder_path,))
        cpu_stress_log_handler = self._thread_logger.thread_logger(cpu_stress_thread)

        memory_stress_thread = threading.Thread(target= self._support_methods.memory_stress_stressapptest, args= (self.stdout_msg,))
        memory_stress_log_handler = self._thread_logger.thread_logger(memory_stress_thread)

        ltssm_thread = threading.Thread(target= self._support_methods.ltssm_test, args = (self._ltssm_folder_path,))
        ltssm_log_handler = self._thread_logger.thread_logger(ltssm_thread)

        network_traffic_thread = threading.Thread(target=self._support_methods.network_traffic_test_iperf)
        network_traffic_log_handler = self._thread_logger.thread_logger(network_traffic_thread)

        self._log.info("Starting workload threads")
        if self.cpu_stress_reqd.lower() == 'true':
            cpu_stress_thread.start()

        if self.memory_stress_reqd.lower() == 'true':
            memory_stress_thread.start()

        if self.ltssm_test_reqd.lower() == 'true':
            ltssm_thread.start()

        if self.network_traffic_reqd.lower() == 'true':
            network_traffic_thread.start()

        if self.cpu_stress_reqd.lower() == 'true':
            cpu_stress_thread.join()
        if self.memory_stress_reqd.lower() == 'true':
            memory_stress_thread.join()
        if self.ltssm_test_reqd.lower() == 'true':
            ltssm_thread.join()
        if self.network_traffic_reqd.lower() == 'true':
            network_traffic_thread.join()

        self._test_content_logger.end_step_logger(6, return_val=True)


        self._thread_logger.stop_thread_logging(cpu_stress_log_handler)
        self._thread_logger.stop_thread_logging(memory_stress_log_handler)
        self._thread_logger.stop_thread_logging(ltssm_log_handler)
        self._thread_logger.stop_thread_logging(network_traffic_log_handler)

        error_str_list = self._common_content_configuration.get_accelerator_error_strings()
        self._thread_logger.verify_workload_logs(error_str_list)
        return True

    def cleanup(self, return_status):
        if self.cpu_stress_reqd.lower() == 'true':
            self._stress_provider.kill_stress_tool(stress_tool_name=Mprime95ToolConstant.MPRIME_TOOL_NAME,
                                               stress_test_command="./" + Mprime95ToolConstant.MPRIME_TOOL_NAME)
        super(NetworkCpuMemoryLtssm, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if NetworkCpuMemoryLtssm.main()
             else Framework.TEST_RESULT_FAIL)
