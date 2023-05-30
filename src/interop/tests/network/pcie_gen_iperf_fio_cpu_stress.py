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

class PcieFioCpuIperf(ContentBaseTestCase):
    """
    HPQALM ID : 16016997582 -RAID using VMD VROC + Storage IO (FIO-16K block size rw)+ Network Traffic(iperf) + Memory(Prime95), CPU stress(Prime95) + SGX+PM harassers+Accelerators Workloads+PCie error injection
    This class to verify stress and stability after running Prime95, Stressapp, iperf and LTSSM tool, accelerator workload, Fio on raid, with PM harassers and pcie error
    injection.
    """
    TEST_CASE_ID = ["16016997582 -RAID using VMD VROC + Storage IO (FIO-16K block size rw)+ Network Traffic(iperf) + Memory(Prime95), CPU stress(Prime95) + SGX+PM harassers+Accelerators Workloads+PCie error injection"]
    STEP_DATA_DICT = {
        1: {'step_details': 'prime95 installation check',
            'expected_results': 'prime95 installation check successful'},
        2: {'step_details': 'Iperf Installation',
            'expected_results': 'Iperf installed successfully'},
        3: {'step_details': 'Run all workloads',
            'expected_results': 'Ran all workloads successfully'},
    }
    COPY_FILE_TO_SUT = "storage_test.txt"

    def __init__(self, test_log, arguments, cfg_opts):
        # """
        # Creates a new object for PcieFioCpuIperf
        #
        # :param test_log: Used for debug and info messages
        # :param arguments:
        # :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        # """
        super(PcieFioCpuIperf, self).__init__(test_log, arguments, cfg_opts)
        #
        self._common_content_configuration = ContentConfiguration(self._log)
        self.cpu_stress_reqd = self._common_content_configuration.get_cpu_stress_enabled().strip()
        self.storage_reqd = self._common_content_configuration.get_storage_enabled().strip()
        self.network_traffic_reqd = self._common_content_configuration.get_network_enabled().strip()
        self.gen_nic_interface_name_sut = self._common_content_configuration.get_gen_nic_interface_name_sut()
        self.gen_nic_interface_name_peer = self._common_content_configuration.get_gen_nic_interface_name_peer()
        self.gen_static_ip_sut = self._common_content_configuration.get_gen_static_ip_sut()
        self.gen_static_ip_peer = self._common_content_configuration.get_gen_static_ip_peer()

        if self.os.os_type != OperatingSystems.LINUX:
            raise NotImplementedError("This Test Case is Only Supported on Linux")
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._support_methods = SupportMethods(self._log, self.os, cfg_opts)
        self._stress_provider = StressAppTestProvider.factory(test_log, cfg_opts, self.os)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._thread_logger = ThreadLogUtil(self._log, self.os, cfg_opts)
        self.fio_thread_list = []
        self.fio_log_handler_list = []

    def prepare(self):
        # type: () -> None
        """

        1. Check Prime95  installation
        2. Check iperf installation

        :return: None
        """
        super(PcieFioCpuIperf, self).prepare()
        # To install screen package

        self._install_collateral.screen_package_installation()
        if self.cpu_stress_reqd.lower() == 'true':
            self._test_content_logger.start_step_logger(1)
            self._mprime_sut_folder_path = self._install_collateral.install_prime95()
            self._install_collateral.copy_collateral_script(Mprime95ToolConstant.MPRIME95_LINUX_SCRIPT_FILE,
                                                         self._mprime_sut_folder_path.strip())
            self._test_content_logger.end_step_logger(1, return_val=True)

        if self.network_traffic_reqd.lower() == 'true':
            self._test_content_logger.start_step_logger(2)
            echo_op = self._support_methods.sut_iperf_check()
            if not echo_op:
                 self._install_collateral.install_iperf_on_linux()
            self._test_content_logger.end_step_logger(2, return_val=True)

    def execute(self):
        """
        This method is used to run the CPU stress, run network traffic and FIO for gen type pcie devices.

        :return: True or False
        :raise: if non zero errors raise content_exceptions.TestFail
        """

        self._log.info("Gen identification and variable extraction")
        self.gen_nic_interface_name_peer_list, self.gen_static_ip_sut_list, \
        self.gen_static_ip_peer_list, self.gen_storage_device_list = self._support_methods.gen_variables()

        self._log.info("Creating fio threads for storage devices")
        if len(self.gen_storage_device_list) > 0:
            for storage_device in self.gen_storage_device_list:
                self._log.info("starting thread for {}".format(storage_device))
                fio_thread = threading.Thread(target= self._support_methods.raid_fio , args= (storage_device,))
                self.fio_thread_list.append(fio_thread)
                fio_log_handler = self._thread_logger.thread_logger(fio_thread)
                self.fio_log_handler_list.append(fio_log_handler)


        self._log.info("Creating cpu thread")
        cpu_stress_thread = threading.Thread(target= self._support_methods.cpu_stress_mprime, args= (self._mprime_sut_folder_path,))
        cpu_stress_log_handler = self._thread_logger.thread_logger(cpu_stress_thread)

        self._log.info("creating network thread")
        network_traffic_thread = threading.Thread(target= self._support_methods.gen_network_traffic_test)
        network_traffic_log_handler = self._thread_logger.thread_logger(network_traffic_thread)

        self._test_content_logger.start_step_logger(3)
        if self.cpu_stress_reqd.lower() == 'true':
            cpu_stress_thread.start()

        if self.network_traffic_reqd.lower() == 'true':
            if self.gen_nic_interface_name_sut.lower() != "na" and self.gen_nic_interface_name_peer.lower() != "na" and \
               self.gen_static_ip_sut.lower() != "na" and self.gen_static_ip_peer.lower() != "na"  :
                    network_traffic_thread.start()

        if self.storage_reqd.lower() == 'true':
            if len(self.gen_storage_device_list) > 0:
                for thread_fio in self.fio_thread_list:
                    thread_fio.start()

        cpu_stress_thread.join()
        if self.gen_nic_interface_name_sut.lower() != "na" and self.gen_nic_interface_name_peer.lower() != "na" and \
                self.gen_static_ip_sut.lower() != "na" and self.gen_static_ip_peer.lower() != "na" :
            network_traffic_thread.join()

        if len(self.gen_storage_device_list) > 0:
            for thread_fio in self.fio_thread_list:
                thread_fio.join()

        self._test_content_logger.end_step_logger(3, return_val=True)

        for fio_log_handler in self.fio_log_handler_list:
            self._thread_logger.stop_thread_logging(fio_log_handler)

        self._thread_logger.stop_thread_logging(cpu_stress_log_handler)
        self._thread_logger.stop_thread_logging(network_traffic_log_handler)



        return True

    def cleanup(self, return_status):
        if self.cpu_stress_reqd.lower() == 'true':
            self._stress_provider.kill_stress_tool(stress_tool_name=Mprime95ToolConstant.MPRIME_TOOL_NAME,
                                                   stress_test_command="./" + Mprime95ToolConstant.MPRIME_TOOL_NAME)

        super(PcieFioCpuIperf, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieFioCpuIperf.main()
             else Framework.TEST_RESULT_FAIL)
