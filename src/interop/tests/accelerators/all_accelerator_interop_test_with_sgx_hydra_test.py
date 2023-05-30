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
import threading

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider

from src.interop.lib.accelerator_library import AcceleratorLibrary
from src.interop.lib.common_library import CommonLibrary
from src.lib.test_content_logger import TestContentLogger
from src.provider.sgx_provider import SGXProvider
from src.security.tests.hqm.hqm_common import HqmBaseTest
from src.security.tests.qat.qat_common import QatBaseTest
from src.security.tests.sgx.sgx_constant import SGXConstant


class AllAcceleratorInteropSgxHydra(HqmBaseTest, QatBaseTest):
    """
    Phoenix ID : 16016262266-All accelerator interop test with SGX Hydra Test
    Verify that all 4 accelerators(DSA/IAA/QAT/DLB) + SGX Hydra Test workloads are functioning properly
    while running at the same time on Host System, In other words monitoring the effect while all accelerator workloads
    are executing concurrently with SGX Hydra test
    """
    ACC_BIOS_CONFIG_FILE = "../accelerator_config.cfg"
    TEST_CASE_ID = ["16016262266", "All_accelerator_interop_test_with_SGX_Hydra_Test"]
    INTEL_IOMMU_ON_STR = "intel_iommu=on,sm_on iommu=on"
    STEP_DATA_DICT = {1: {'step_details': 'Set the BIOS knobs',
                          'expected_results': 'BIOS knobs set successfully'},
                      2: {'step_details': 'QAT Driver Installation',
                          'expected_results': 'QAT Driver  Installed successfully'},
                      3: {'step_details': 'DLB driver Installation, DPDK Installation',
                          'expected_results': 'DLB driver Installation, DPDK Installation successful'},
                      4: {'step_details': 'Accel Config',
                          'expected_results': 'Accel config install successful'},
                      5: {'step_details': 'Install SGX driver and SGX Hydra tool',
                          'expected_results': 'SGX driver and Hydra tool Installation successful'},
                      6: {'step_details': 'Run 4 Accelerators workloads and SGX Hydra test concurrently for an hour',
                          'expected_results': 'Ran 4 Accelerators workloads and SGX Hydra test concurrently '
                                              'for an hour successfully'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of AllAcceleratorInteropSgxHydra

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.ACC_BIOS_CONFIG_FILE)
        self.bios_config_file = SGXConstant(test_log).sgx_bios_knobs(bios_config_file)
        super(AllAcceleratorInteropSgxHydra, self).__init__(test_log, arguments, cfg_opts,
                                                            bios_config_file_path=self.bios_config_file)
        self._log.info("Bios config file: {}".format(bios_config_file))
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.sgx = SGXProvider.factory(test_log, cfg_opts, self.os, self.sdp)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._accelerator_lib = AcceleratorLibrary(self._log, self.os, cfg_opts)  # ..
        self._library = CommonLibrary(self._log, self.os, cfg_opts)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        self._test_content_logger.start_step_logger(1)
        super(AllAcceleratorInteropSgxHydra, self).prepare()
        self._log.info("Interop and SGX bios knob set successfully")
        self._library.update_kernel_args_and_reboot([self.INTEL_IOMMU_ON_STR])
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Run all 4 accelerator workload with SGX hydra tool

        :return: True if Test case pass else False
        """
        self._log.info("QAT Installation")
        self._test_content_logger.start_step_logger(2)
        self.install_qat_tool(configure_spr_cmd='./configure --enable-icp-sriov=host')
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._log.info("DLB Installation")
        self._test_content_logger.start_step_logger(3)
        self.install_hqm_driver_libaray()
        self._test_content_logger.end_step_logger(3, return_val=True)

        # self._test_content_logger.start_step_logger(4)
        # Place holder for copying accel-random scripts to SUT
        # self._test_content_logger.end_step_logger(4, return_val=True)

        self._test_content_logger.start_step_logger(5)
        hydra_tool_path = self._accelerator_lib.install_sgx_hydra_tool()
        self._test_content_logger.end_step_logger(5, return_val=True)

        self._test_content_logger.start_step_logger(6)
        qat_workload_thread = threading.Thread(target=self._accelerator_lib.run_qat_workload_on_host)
        dlb_workload_thread = threading.Thread(target=self._accelerator_lib.run_dpdk_workload_on_host)
        dsa_workload_thread = threading.Thread(target=self._accelerator_lib.dsa_workload_on_host)
        iax_workload_thread = threading.Thread(target=self._accelerator_lib.iax_workload_on_host)
        sgx_hydra_workload_thread = threading.Thread(target=self._accelerator_lib.run_hydra_test,
                                                     args=(hydra_tool_path, self._accelerator_lib.run_time,))

        qat_workload_thread.start()
        dlb_workload_thread.start()
        dsa_workload_thread.start()
        iax_workload_thread.start()
        sgx_hydra_workload_thread.start()

        qat_workload_thread.join()
        dlb_workload_thread.join()
        dsa_workload_thread.join()
        iax_workload_thread.join()
        sgx_hydra_workload_thread.join()

        self._test_content_logger.end_step_logger(6, return_val=True)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if AllAcceleratorInteropSgxHydra.main() else Framework.TEST_RESULT_FAIL)
