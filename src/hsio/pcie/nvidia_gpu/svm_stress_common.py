#!/usr/bin/env python
##########################################################################
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
##########################################################################
import time

from src.lib import content_exceptions

from src.lib.install_collateral import InstallCollateral
from src.ras.tests.io_virtualization.io_virtualization_common import IoVirtualizationCommon



class SVMStressCommon(IoVirtualizationCommon):
    """
    This Class is Used as Common Class For all the SVM Stress Test Cases
    """

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        """
        Create an instance of SVMStressCommon.

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(SVMStressCommon, self).__init__(test_log, arguments, cfg_opts, bios_config_file)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self.PERFORMANCE_CHECK_CMD = "powershell.exe; (((Get-Counter '\GPU Process Memory(*)\Local Usage')." \
                                     "CounterSamples ^| where CookedValue).CookedValue ^| measure -sum).sum"
        self.TWO_HOURS_TIMER_SEC = 7200
        self.CHECK_INTERVAL_SEC = 300
        self.MEMORY_CHEKPOINT_MB = 500
        self.DELAY_FOR_TIMER_SEC = 1
        self.GPU_MEM_CHECK_ITER_COUNT = 5


    def execute_svm_stress(self, test_file):
        """
        1. Install GFX_nVidia_SVM.zip tool to SUT
        2. Check GPU Performance
        3. Start the SVM stress on nvidia GPU
        4. run it for 2 hours.
        5. Check OS is alive

        :param test_file: SVM algorithm file to trigger
        :return True/False
        """
        # Download and copy SVM tool
        self._log.info("Download SVM tool, copy and extract tool on sut")
        self.svm_path = self._install_collateral.install_svm_tool()

        # Check GPU performance before. starting stress
        gpu_mem_status = self.get_gpu_memory_utilization()
        if gpu_mem_status > self.MEMORY_CHEKPOINT_MB:
            raise content_exceptions.TestFail("GPU is already utilized")
        self._log.info("gpu is not utilized, starting stress")

        # Starting stress
        self._log.info("Triggering {} file.......".format(test_file))
        self.os.execute_async(test_file, "{}\\SVM".format(self.svm_path))
        # 2 hours timer
        while self.TWO_HOURS_TIMER_SEC:
            if self.TWO_HOURS_TIMER_SEC % self.CHECK_INTERVAL_SEC == 0:

                # adjusting 1 sec in the timer wasted for CRC checks
                self.TWO_HOURS_TIMER_SEC -= 1
                self._log.info("Checking for stress on GPU...........")
                gpu_mem_status = self.get_gpu_memory_utilization()
                try:
                    if gpu_mem_status < self.MEMORY_CHEKPOINT_MB:
                        raise content_exceptions.TestFail(
                            "GPU is still not utilized after starting stress, check on stress")
                except:
                    self._log.info("rechecking the gpu utilization status")
                    for iter in range(self.GPU_MEM_CHECK_ITER_COUNT):
                        gpu_mem_status = self.get_gpu_memory_utilization()
                        if gpu_mem_status > self.MEMORY_CHEKPOINT_MB:
                            break
                    if gpu_mem_status < self.MEMORY_CHEKPOINT_MB:
                        raise content_exceptions.TestFail(
                            "GPU is still not utilized after starting stress, check on stress")

            time.sleep(self.DELAY_FOR_TIMER_SEC)

            self.TWO_HOURS_TIMER_SEC -= 1
        self._log.info("Timer finished, 2 hours completed")

        # Check on OS
        if not self.os.is_alive():
            raise content_exceptions.TestFail("OS is not alive after 2 hours stress, TEST FAILED")
        self._log.info("OS is alive after stressing GPU for 2 hours")
        return True

    def get_gpu_memory_utilization(self):
        """
        Check the Nvidia GPU memory utilization.

        :param: None
        :return gpu_mem: GPU memory
        """
        gpu_mem = int(self.os.execute(self.PERFORMANCE_CHECK_CMD, self._command_timeout).stdout) / 1E6
        self._log.info("gpu utilized memory status = {}".format(gpu_mem))
        return gpu_mem