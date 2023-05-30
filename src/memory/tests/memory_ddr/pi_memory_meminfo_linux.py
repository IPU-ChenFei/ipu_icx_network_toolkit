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

from dtaf_core.lib.dtaf_constants import Framework

from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.memory.tests.memory_ddr.ddr_common import DDRCommon


class PiMemoryMemInfo(DDRCommon):
    """
    HP QC ID: 77287
    To sure the memory total approximates the total amount of RAM present in the system.
    """

    TEST_CASE_ID = "H77287"

    step_data_dict = {1: {'step_details': 'Clear OS logs and load default bios knobs',
                          'expected_results': 'Clear ALL the system Os logs and default bios knob setting done.'},
                      2: {'step_details': 'Check the total memory size.',
                          'expected_results': 'The MemTotal should match with the system physical memory size.'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiMemoryMemInfo object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(PiMemoryMemInfo, self).__init__(test_log, arguments, cfg_opts)

        #  Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        1. Set the bios knobs to its default mode.
        2. Reboot the SUT to apply the new bios settings.

        :return: None
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        self._common_content_lib.clear_os_log()  # TO clear Os logs
        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self._log.info("Bios knobs are set to its defaults.. ")
        self._os.reboot(int(self._reboot_timeout))  # To apply the new bios setting.
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. Check memory information.

        :return: True, if the test case is successful.
        :raise: TestFail
        """
        return_value = True

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        #  Show System Memory info
        system_memory_data = self._memory_common_lib.get_system_memory_report_linux()

        total_memory = self._memory_common_lib.get_total_system_memory_data_linux(system_memory_data)

        # Converting into GiB
        memory_in_gib = int(total_memory / 1024)

        self._log.info("Total DDR capacity shown from OS level - {}".format(memory_in_gib))

        self._log.info("Total DDR capacity as per configuration - {}".format(self._ddr4_mem_capacity_config))

        # Memory total with variance
        memtotal_with_variance = int(self._ddr4_mem_capacity_config - (self._ddr4_mem_capacity_config * self._variance_percent))

        self._log.info("Total DDR capacity as per configuration with variance - {}".format(
            memtotal_with_variance))

        if int(memtotal_with_variance) >= memory_in_gib > self._ddr4_mem_capacity_config:
            raise content_exceptions.TestFail("Total DDR Capacity is not same as configuration.")

        self._log.info("Total DDR Capacity is same as configuration.")

        # Step Logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

        return return_value

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PiMemoryMemInfo, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiMemoryMemInfo.main()
             else Framework.TEST_RESULT_FAIL)
