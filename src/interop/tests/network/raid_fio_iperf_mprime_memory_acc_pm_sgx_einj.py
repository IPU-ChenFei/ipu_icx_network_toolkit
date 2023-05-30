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
import threading
from src.interop.lib.network_storage_common import SupportMethods
from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral
from src.provider.stressapp_provider import StressAppTestProvider
from src.lib.dtaf_content_constants import Mprime95ToolConstant
from src.lib import content_exceptions
from src.lib.content_configuration import ContentConfiguration
import os
from src.interop.lib.accelerator_library import AcceleratorLibrary
from src.interop.lib.common_library import CommonLibrary
from src.security.tests.hqm.hqm_common import HqmBaseTest
from src.security.tests.qat.qat_common import QatBaseTest
from src.lib.common_content_lib import CommonContentLib
from dtaf_core.lib.dtaf_constants import ProductFamilies
from src.ras.lib.ras_einj_common import RasEinjCommon
from src.ras.lib.ras_common_utils import RasCommonUtil
from src.storage.test.storage_common import StorageCommon
from src.provider.storage_provider import StorageProvider
from src.environment.os_installation import OsInstallation
from src.lib.dtaf_content_constants import RaidConstants
from src.storage.lib.nvme_raid_util import NvmeRaidUtil
from src.lib.bios_util import SerialBiosUtil
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from src.lib.test_content_logger import TestContentLogger
from src.interop.lib.thread_log_util import ThreadLogUtil

class NetworkRaidFioCpuMemoryAccHarasserPcieErr(ContentBaseTestCase):
    """
    Phoenix ID : 16016997582 -RAID using VMD VROC + Storage IO (FIO-16K block size rw)+ Network Traffic(iperf) + Memory(Prime95), CPU stress(Prime95) + SGX+PM harassers+Accelerators Workloads+PCie error injection
    This class to verify stress and stability after running Prime95, Stressapp, iperf and LTSSM tool, accelerator workload, Fio on raid, with PM harassers and pcie error
    injection.
    """
    TEST_CASE_ID = ["16016997582 -RAID using VMD VROC + Storage IO (FIO-16K block size rw)+ Network Traffic(iperf) + Memory(Prime95), CPU stress(Prime95) + SGX+PM harassers+Accelerators Workloads+PCie error injection"]
    STEP_DATA_DICT = {1: {'step_details': 'install Prime95',
                          'expected_results': 'prime95 Installed successfully'},
                      2: {'step_details': 'stressapp installation check',
                          'expected_results': 'stressapp installation check successful'},
                      3: {'step_details': 'Iperf Installation',
                          'expected_results': 'Iperf installed successfully'},
                      4: {'step_details': 'set bios knobs',
                          'expected_results': 'bios settings done successfully'},
                      5: {'step_details': 'Install HQM driver',
                          'expected_results': 'HQM driver successfully'},
                      6: {'step_details': 'Enable VMD bios knobs',
                          'expected_results': 'VMD bios knobs enabled successfully'},
                      7: {'step_details': 'Create Raid',
                          'expected_results': 'Raid created successfully'},
                      8: {'step_details': 'Run all workloads',
                          'expected_results': 'Ran all workloads successfully'},
                      }

    ACC_BIOS_CONFIG_FILE = "../accelerator_config.cfg"
    PCIE_BIOS_CONFIG_FILE = "../einj_pcie_biosknobs.cfg"
    INTEL_IOMMU_ON_STR = "intel_iommu=on,sm_on iommu=on"
    REGEX_FOR_FIO = r'\serr=\s0'
    FIO_TOOL_NAME = r"fio"
    COPY_FILE_TO_SUT = "storage_test.txt"

    def __init__(self, test_log, arguments, cfg_opts):
        # """
        # Creates a new object for NetworkRaidFioCpuMemoryAccHarasserPcieErr
        #
        # :param test_log: Used for debug and info messages
        # :param arguments:
        # :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        # """
        super(NetworkRaidFioCpuMemoryAccHarasserPcieErr, self).__init__(test_log, arguments, cfg_opts)

        self._common_content_configuration = ContentConfiguration(self._log)
        self.cpu_stress_reqd = self._common_content_configuration.get_cpu_stress_enabled().strip()
        self.memory_stress_reqd = self._common_content_configuration.get_memory_stress_enabled().strip()
        self.ras_test_reqd = self._common_content_configuration.get_ras_enabled().strip()
        self.storage_reqd = self._common_content_configuration.get_storage_enabled().strip()
        self.network_traffic_reqd = self._common_content_configuration.get_network_enabled().strip()
        self.pm_harassers_reqd = self._common_content_configuration.get_pm_enabled().strip()
        self.dlb_workload_reqd = self._common_content_configuration.get_dlb_enabled().strip()
        self.qat_workload_reqd = self._common_content_configuration.get_qat_enabled().strip()
        self.dsa_workload_reqd = self._common_content_configuration.get_dsa_enabled().strip()
        self.iaa_workload_reqd = self._common_content_configuration.get_iaa_enabled().strip()
        if self.os.os_type != OperatingSystems.LINUX:
            raise NotImplementedError("This Test Cae is Only Supported on Linux")
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._support_methods = SupportMethods(self._log, self.os, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._thread_logger = ThreadLogUtil(self._log, self.os, cfg_opts)
        self._stress_provider = StressAppTestProvider.factory(test_log, cfg_opts, self.os)
        self._hqm_obj = HqmBaseTest(test_log, arguments, cfg_opts)
        self._qat_obj = QatBaseTest(test_log, arguments, cfg_opts)
        self.acc_bios_knobs = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.ACC_BIOS_CONFIG_FILE)
        self.pcie_bios_knobs = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.PCIE_BIOS_CONFIG_FILE)
        self.pcie_einj_acc_biosknobs = self._common_content_lib.get_combine_config(
            [self.acc_bios_knobs, self.pcie_bios_knobs])
        super(NetworkRaidFioCpuMemoryAccHarasserPcieErr, self).__init__(test_log, arguments, cfg_opts, self.pcie_einj_acc_biosknobs)

        self._accelerator_lib = AcceleratorLibrary(self._log, self.os, cfg_opts)  # ..
        self._library = CommonLibrary(self._log, self.os, cfg_opts)  # ..
        self._common_content_lib = CommonContentLib(self._log, self.os, self._cfg)
        self._platform = self._common_content_lib.get_platform_family()
        if self._platform != ProductFamilies.SPR:
            raise content_exceptions.TestFail("HQM Tool required SPR Platform")
        self._ras_einj_obj = RasEinjCommon(self._log, self.os, self._common_content_lib,
                                           self._common_content_configuration, self.ac_power, cfg_opts)
        self._ras_common_obj = RasCommonUtil(self._log, self.os, cfg_opts, self._common_content_configuration)
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.storage_common_obj = StorageCommon(test_log, arguments, cfg_opts)
        self._log_file_path = self.storage_common_obj.get_cscripts_log_file()
        self.execute_timeout = self._common_content_configuration.get_command_timeout()
        self._cfg_opts = cfg_opts
        self._serial_bios_util = SerialBiosUtil(self.ac_power, self._log, self._common_content_lib, self._cfg_opts)
        self._product_family = self._common_content_lib.get_platform_family()
        self.storage_provider = StorageProvider.factory(self._log, self.os, cfg_opts, "os")
        self._raid_util = NvmeRaidUtil(self._log, self._common_content_lib, self._common_content_configuration,
                                       self.bios_util, self._serial_bios_util, self.ac_power)
        self._os_installation_lib = OsInstallation(test_log, cfg_opts)
        self.raid_levels = []
        self.storage_device = 'md126'
        self.FIO_CMDS = ["fio --name=read --rw=read --numjobs=2 --bs=16k --filename=/dev/{}"
                    " --size=4G --ioengine=posixaio --runtime={} --time_based --iodepth=2 --group_reporting"
                             .format(self.storage_device,self._common_content_configuration.get_workload_time())]

    def prepare(self):
        # type: () -> None
        """
        1. Check Stressapptest installation
        2. Install tools
        3. Set bios knobs
        :return: None
        """
        super(NetworkRaidFioCpuMemoryAccHarasserPcieErr, self).prepare()
        # To install screen package

        self._install_collateral.screen_package_installation()
        self._test_content_logger.start_step_logger(1)
        if self.cpu_stress_reqd.lower() == 'true':
            self._mprime_sut_folder_path = self._install_collateral.install_prime95()
            self._install_collateral.copy_collateral_script(Mprime95ToolConstant.MPRIME95_LINUX_SCRIPT_FILE,
                                                             self._mprime_sut_folder_path.strip())
        self._test_content_logger.end_step_logger(1, return_val=True)
        if self.memory_stress_reqd.lower() == 'true':
            self._test_content_logger.start_step_logger(2)
            self.stdout_msg = self._support_methods.stressapptest_installation_check()
            memory_msg = self._support_methods.memory_check_before_stressapptest()
            self._test_content_logger.end_step_logger(2, return_val=True)

        if self.network_traffic_reqd.lower() == 'true':
            self._test_content_logger.start_step_logger(3)
            echo_op = self._support_methods.sut_iperf_check()
            if not echo_op:
                 self._install_collateral.install_iperf_on_linux()
            self._test_content_logger.end_step_logger(3, return_val=True)
        self._common_content_lib.set_datetime_on_linux_sut()
        self._test_content_logger.start_step_logger(4)
        self._library.update_kernel_args_and_reboot([self.INTEL_IOMMU_ON_STR])
        self._test_content_logger.end_step_logger(4, return_val=True)

        if self.dlb_workload_reqd.lower() == 'true':
            self._test_content_logger.start_step_logger(5)
            self._log.info("DLB Installation")
            self._hqm_obj.install_hqm_driver_libaray()
            self._test_content_logger.end_step_logger(5, return_val=True)

        if self.ras_test_reqd.lower() == 'true':
            self._install_collateral.copy_mcelog_binary_to_sut()

        if self.storage_reqd.lower() == 'true':
            self.non_raid_disk_name = self._support_methods.non_raid_creation()
            self._test_content_logger.start_step_logger(6)
            self._log.info("Enabling the VMD BIOS Knobs")
            self.storage_common_obj.enable_vmd_bios_knobs()
            self._test_content_logger.end_step_logger(6, return_val=True)
            self._test_content_logger.start_step_logger(7)
            self.raid_level = RaidConstants.RAID0
            self._log.info("Creating {} volume ".format(self.raid_level))
            self._raid_util.create_raid(self.raid_level)
            self._log.info("Waiting for SUT to boot to OS")
            self.os.wait_for_os(self.reboot_timeout)
            self._test_content_logger.end_step_logger(7, return_val=True)


    def execute(self):
        """
        This method is used to run the Memory and CPU stress, run network traffic, accelerator workload, harassers, pcie
        error injection

        :return: True or False
        :raise: if non zero errors raise content_exceptions.TestFail
        """

        cpu_stress_thread = threading.Thread(target= self._support_methods.cpu_stress_mprime, args= (self._mprime_sut_folder_path,))
        cpu_stress_log_handler = self._thread_logger.thread_logger(cpu_stress_thread)

        memory_stress_thread = threading.Thread(target= self._support_methods.memory_stress_stressapptest, args= (self.stdout_msg,))
        memory_stress_log_handler = self._thread_logger.thread_logger(memory_stress_thread)

        harasser_thread = threading.Thread(target= self._support_methods.launch_harasser)
        harasser_log_handler = self._thread_logger.thread_logger(harasser_thread)

        network_traffic_thread = threading.Thread(target=self._support_methods.network_traffic_test_iperf)
        network_traffic_log_handler = self._thread_logger.thread_logger(network_traffic_thread)

        acc_thread = threading.Thread(target = self._support_methods.accelerator_workload, args= (self.qat_workload_reqd,
                                                                                                  self.dlb_workload_reqd,
                                                                                                  self.dsa_workload_reqd,
                                                                                                  self.iaa_workload_reqd, ))

        pcie_err_thread = threading.Thread(target= self._support_methods.pcie_error_injection, args = (self._ras_einj_obj,))
        pcie_err_log_handler = self._thread_logger.thread_logger(pcie_err_thread)

        raid_fio_thread = threading.Thread(target= self._support_methods.raid_fio , args= (self.FIO_CMDS[0],))
        raid_fio_log_handler = self._thread_logger.thread_logger(raid_fio_thread)

        cpu_usage_thread = threading.Thread(target=self._support_methods.cpu_monitoring)
        cpu_usage_log_handler = self._thread_logger.thread_logger(cpu_usage_thread)

        self._test_content_logger.start_step_logger(8)
        if self.cpu_stress_reqd.lower() == 'true':
            cpu_stress_thread.start()
            cpu_usage_thread.start()
        if self.memory_stress_reqd.lower() == 'true':
            memory_stress_thread.start()
        if self.pm_harassers_reqd.lower() == 'true':
            harasser_thread.start()
        if self.network_traffic_reqd.lower() == 'true':
            network_traffic_thread.start()
        acc_thread.start()
        if self.ras_test_reqd.lower() == 'true':
            pcie_err_thread.start()
        if self.storage_reqd.lower() == 'true':
            raid_fio_thread.start()


        cpu_stress_thread.join()
        cpu_usage_thread.join()
        memory_stress_thread.join()
        harasser_thread.join()
        network_traffic_thread.join()
        acc_thread.join()
        pcie_err_thread.join()
        raid_fio_thread.join()
        self._test_content_logger.end_step_logger(8, return_val=True)

        self._thread_logger.stop_thread_logging(cpu_stress_log_handler)
        self._thread_logger.stop_thread_logging(cpu_usage_log_handler)
        self._thread_logger.stop_thread_logging(memory_stress_log_handler)
        self._thread_logger.stop_thread_logging(harasser_log_handler)
        self._thread_logger.stop_thread_logging(network_traffic_log_handler)
        self._thread_logger.stop_thread_logging(pcie_err_log_handler)
        self._thread_logger.stop_thread_logging(raid_fio_log_handler)

        error_str_list = self._common_content_configuration.get_accelerator_error_strings()
        self._thread_logger.verify_workload_logs(error_str_list)

        return True

    def cleanup(self, return_status):
        if self.cpu_stress_reqd.lower() == 'true':
            self._stress_provider.kill_stress_tool(stress_tool_name=Mprime95ToolConstant.MPRIME_TOOL_NAME,
                                                   stress_test_command="./" + Mprime95ToolConstant.MPRIME_TOOL_NAME)
        if self.storage_reqd.lower() == 'true':
            self._raid_util.delete_raid(self.raid_level, self.non_raid_disk_name)
            self.os.wait_for_os(self.reboot_timeout)
        self._common_content_lib.store_os_logs(self.log_dir)
        self.bios_util.load_bios_defaults()

        super(NetworkRaidFioCpuMemoryAccHarasserPcieErr, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if NetworkRaidFioCpuMemoryAccHarasserPcieErr.main()
             else Framework.TEST_RESULT_FAIL)
