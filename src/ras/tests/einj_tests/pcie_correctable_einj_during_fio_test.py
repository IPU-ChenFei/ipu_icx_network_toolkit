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

import sys
import os
import time

from dtaf_core.lib.dtaf_constants import Framework

from src.manageability.lib.redfish_test_common import RedFishTestCommon
from src.lib.test_content_logger import TestContentLogger
from src.ras.tests.einj_tests.einj_common import EinjCommon
from src.lib.fio_utils import FIOCommonLib
from src.lib.dtaf_content_constants import TimeConstants
from src.memory.lib.memory_common_lib import MemoryCommonLib
from src.provider.storage_provider import StorageProvider
from src.memory.tests.memory_ddr.ddr_common import DDRCommon
from src.lib import content_exceptions


class PciecorrectableEinjDuringFioTest(EinjCommon):
    """
    Glasgow_ID: ["G62183.2", "PCIe Correctable EINJ during FIO Test"]

    This TestCase Injects a PciecorrectableEinjDuringFioTest and Validate if the error is detected.
    """
    TEST_CASE_ID = ["G62183.2", "PCIe_Correctable_EINJ_during_FIO_Test"]
    BIOS_CONFIG_FILE = "einj_pcie_bios_knobs.cfg"

    STEP_DATA_DICT = {
                        1: {'step_details': 'Verify load average value is close to 0',
                            'expected_results': "Load average value should be close to zero"},
                        2: {'step_details': 'Execute FIO Command and Inject the Error(s)',
                            'expected_results': 'Execute FIO command and Inject the error(s) concurrently'},
                        3: {'step_details': 'Copy FIO log form SUT to local',
                            'expected_results': 'Copy Should be successful.'},
                        4: {'step_details': 'Check logs for Bandwidth Measurement, SEL, elist, dmesg,'
                                            'Check Machine Check Exception logging, Clear the System Event Log (SEL)',
                            'expected_results': 'Check all the logs have been verified successfully.'}
                    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new EinjPciecorrectableDuringFioTest object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PciecorrectableEinjDuringFioTest, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._fio_common_lib = FIOCommonLib(self._log, self.os)
        self._mem_parse_log = MemoryCommonLib(self._log, cfg_opts, self.os)
        self.obj_redfish = RedFishTestCommon(test_log, arguments, cfg_opts)
        self.storage_provider = StorageProvider.factory(test_log, self.os, cfg_opts, "os")
        self.ddr_common = DDRCommon(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        1. Clear SEL LOGS
        2. Installing FIO and Creating Mount Point

        :return: None
        """
        super(PciecorrectableEinjDuringFioTest, self).prepare()
        # Clearing SEL logs
        self.obj_redfish.clear_sel()
        # Installing FIO and Creating a Mount Point in SUT
        self._install_collateral.install_fio(install_fio_package=False)
        self._log.info('Creating Mount Point for fio')
        fio_mounting = self._common_content_configuration.get_nvme_partition_to_mount()
        if not fio_mounting:
            raise content_exceptions.TestFail("NVME Device Not Connected")
        self.storage_provider.mount_the_drive(fio_mounting, self._fio_common_lib.FIO_MOUNT_POINT)

    def execute(self):
        """
        1. Check if the load average Value is close to zero
        2. Execute FIO Command and Injecting the Pcie Correctable Error and validating the error log
        3. Copying FIO logs to local
        4. Checking and clearing SEL logs

        :return result: True if error detected else False
        """
        final_result= []
        failure_num = 0
        passed_num = 0
        test_run = 0
        run_duration_in_sec = TimeConstants.ONE_HOUR_IN_SEC
        t_end = time.time() + run_duration_in_sec

        # Checking load average value is close to zero
        self._test_content_logger.start_step_logger(1)
        load_avg_value = self.ddr_common.get_load_average()
        max_load_avg = self.ddr_common.get_max_load_average(load_avg_value)
        self._log.info("Correct load average value {}".format(max_load_avg))
        if float(max_load_avg) <= self.ddr_common.CMP_LOAD_AVERAGE_BEFORE_STRESSAPP:
            self._log.info("Success as maximum value of load average value is less than threshold value")
        else:
            raise  content_exceptions.TestFail("Failed as maximum value of load average value more than threshold value")
        self._test_content_logger.end_step_logger(1, return_val=True)
        #Executing einj_pcie_correctable_duration.py test
        self._test_content_logger.start_step_logger(2)
        self._log.info('Execute the fio command and inject error parallely')
        self._fio_common_lib.fio_execute_async(self._fio_common_lib.TOOL_NAME)
        while time.time() < t_end:
            result = self._ras_einj_obj.einj_inject_and_check(self._ras_einj_obj.EINJ_PCIE_CORRECTABLE)
            test_run = 1 + test_run
            self._log.info("Test run number ", test_run)
            if result is False:
                failure_num = failure_num + 1
                self._log.info("The test case failed! This is failure number ", failure_num)
            else:
                passed_num = passed_num + 1
                self._log.info("TEST PASSED")
        self._log.info("FIO async execution has completed successfully!")
        self._common_content_lib.get_cpu_utilization()
        self._test_content_logger.end_step_logger(2, return_val=True)
        self._test_content_logger.start_step_logger(3)
        self._log.info("Copying FIO log file to local")
        self.os.copy_file_from_sut_to_local(self._fio_common_lib.LOG_FILE, os.path.join(self.log_dir, self._fio_common_lib.FIO_LOG_FILE))
        final_result.append(self._fio_common_lib.fio_log_parsing(log_path=os.path.join(self.log_dir, self._fio_common_lib.FIO_LOG_FILE),
                                                                 pattern="READ:|WRITE:"))
        self._log.info("Copying FIO log file to local was successful")
        self._test_content_logger.end_step_logger(3, return_val=True)
        self._test_content_logger.start_step_logger(4)
        # Checking and Clearing SEL logs
        if not self.obj_redfish.check_sel():
            raise content_exceptions.TestFail("Unexpected error occurred, please check and validate again")
        self.obj_redfish.clear_sel()
        self._test_content_logger.end_step_logger(4, return_val=True)
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""

        super(PciecorrectableEinjDuringFioTest, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PciecorrectableEinjDuringFioTest.main() else Framework.TEST_RESULT_FAIL)
