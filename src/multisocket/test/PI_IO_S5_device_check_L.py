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
import ipccli

from dtaf_core.lib.dtaf_constants import Framework

from src.hsio.upi.hsio_upi_common import HsioUpiCommon
from src.lib import content_exceptions
from src.lib.content_base_test_case import ContentBaseTestCase
from src.multisocket.lib.multisocket_common import MultiSocketCommon
from src.lib.test_content_logger import TestContentLogger
from src.power_management.lib.reset_base_test import ResetBaseTest
from src.multisocket.lib.multisocket_common import MultiSocketCommon


class PiIoS5DeviceCheckL(ContentBaseTestCase):
    """
    Phoenix 18014075427, PI_IO_S5_device_check_L
    PCH IO Devices S5 cycling test
    """

    TEST_CASE_ID = ["18014075427", "PI_IO_S5_device_check_L"]
    step_data_dict = {1: {'step_details': 'Boot to OS.',
                          'expected_results': 'The OS should boot ...'},
                      2: {'step_details': 'Check the IOE devices ',
                          'expected_results': 'IOE devices should be listed properly in the OS ...'},
                      3: {'step_details': 'Perform S5 cycle ',
                          'expected_results': 'S5 Cycle should happen properly...'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance PiIoS5DeviceCheckL
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        :return: None
        :raises: None
        """

        # calling base class init
        super(PiIoS5DeviceCheckL, self).__init__(test_log, arguments, cfg_opts)

        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._multisock_obj = MultiSocketCommon(test_log, arguments, cfg_opts)
        self._silicon_family = self._common_content_lib.get_platform_family()
        self.hsio_obj = HsioUpiCommon(test_log, arguments, cfg_opts)
        self._reset_base_test = ResetBaseTest(test_log, arguments, cfg_opts)
        self.initialize_sv_objects()
        self.initialize_sdp_objects()

    def prepare(self):
        # type: () -> None
        """
        To clear OS logs and load default bios settings.
        :return: None
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        mode = self._multisock_obj.get_mode_info(self.serial_log_dir, self._SERIAL_LOG_FILE)
        self._log.info("System is in {}".format(mode))
        super(PiIoS5DeviceCheckL, self).prepare()
        self._multisock_obj.check_topology_speed_lanes(self.SDP)
        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. Get the list of all SSD,PCI and USB devices
        2. Run 10 S5 cycles
        :return: True, if the test case is successful.
        """
        # Step logger Start for Step 1
        self._test_content_logger.start_step_logger(2)
        # Get a list of all SSDs, PCIs and USBs devices in the setup.
        get_ioe_device_dict_before_cycle = self._multisock_obj.get_ioe_device_dict()
        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)
        # Step logger Start for Step 3
        self._test_content_logger.start_step_logger(3)
        for cycle_number in range(self._common_content_configuration.get_num_of_s5_dpmo_cycles()):
            self._reset_base_test.graceful_s5()
            get_ioe_device_dict_after_ac_cycle = self._multisock_obj.get_ioe_device_dict()
            self._multisock_obj.check_topology_speed_lanes(self.SDP)
            if get_ioe_device_dict_before_cycle != get_ioe_device_dict_after_ac_cycle:
                raise content_exceptions.TestFail("IOE devices are not same after and before DC cycle")
            self._log.info("IO device Status is Verified after DC Cycle no: {}".format(cycle_number))
        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiIoS5DeviceCheckL.main() else Framework.TEST_RESULT_FAIL)
