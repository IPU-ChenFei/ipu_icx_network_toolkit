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

from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.power_management.lib.reset_base_test import ResetBaseTest
from src.multisocket.lib.multisocket_common import MultiSocketCommon
from src.hsio.upi.hsio_upi_common import HsioUpiCommon


class PiSpareModeCheckL(HsioUpiCommon):
    """
    Phoenix 16013411562, PI_spare_mode_check_L
    PCH IO Devices S5 cycling test
    """

    TEST_CASE_ID = ["16013411562", "PI_spare_mode_check_L"]
    step_data_dict = {1: {'step_details': 'System should be in Spare Mode.',
                          'expected_results': 'Verify System is Booted to Spare Mode ...'},
                      2: {'step_details': 'Print UPI details',
                          'expected_results': 'Printed UPI details successfully...'},
                      3: {'step_details': 'Check the IOE devices ',
                          'expected_results': 'IOE devices should be listed properly in the OS ...'},
                      4: {'step_details': 'Perform G3 cycle ',
                          'expected_results': 'G3 Cycle should happen properly...'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance PiSpareModeCheckL
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        :return: None
        :raises: None
        """

        # calling base class init
        super(PiSpareModeCheckL, self).__init__(test_log, arguments, cfg_opts)

        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._multisock_obj = MultiSocketCommon(test_log, arguments, cfg_opts)
        self._silicon_family = self._common_content_lib.get_platform_family()
        self._reset_base_test = ResetBaseTest(test_log, arguments, cfg_opts)
        self.initialize_sv_objects()
        self.initialize_sdp_objects()

    def prepare(self):
        # type: () -> None
        """
        To check if the system booted to Spare mode or not.
        :return: None
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        self.itp = ipccli.baseaccess()
        self.itp.unlock()
        self.itp.forcereconfig()
        self.SV.refresh()
        no_of_sockets_from_pysv = self.SV.get_socket_count()
        socket_data = self._common_content_lib.execute_sut_cmd("lscpu | grep Socket", "getting the no of sockets",
                                                               self._command_timeout)
        no_of_sockets = int(socket_data.split(":")[1].strip())
        if not (no_of_sockets_from_pysv == no_of_sockets):
            raise content_exceptions.TestSetupError("no of Sockets from OS is not same from PythonSV.. Please check the"
                                                    " System")
        self._log.info("No of Sockets in the System is : {}".format(no_of_sockets))
        if no_of_sockets == 4:
            pysv_output_data = self.SV.get_by_path(
                self.SV.SPCH, "pmc.cmt.hcsts2.io_expander_mode", socket_index=1)
            self._log.info("sv.spch1.pmc.cmt.hcsts2.io_expander_mode --> {}".format(pysv_output_data))
            if str(pysv_output_data) != "0x1":
                raise content_exceptions.TestSetupError("System is not in Spare mode please perform the require jumper "
                                                        "settings")
        elif no_of_sockets == 8:
            for i in range(1, 4):
                pysv_output_data = self.SV.get_by_path(
                    self.SV.SPCH, "pmc.cmt.hcsts2.io_expander_mode", socket_index=i)
                self._log.info("sv.spch{}.pmc.cmt.hcsts2.io_expander_mode --> {}".format(i, pysv_output_data))
                if str(pysv_output_data) != "0x1":
                    raise content_exceptions.TestSetupError("System is not in Spare mode please perform the require "
                                                            "jumper settings")
        mode = self._multisock_obj.get_mode_info(self.serial_log_dir, self._SERIAL_LOG_FILE)
        self._log.info("System is in {}".format(mode))
        if mode != "Spare Mode":
            raise content_exceptions.TestSetupError("System is not in Spare mode please perform the require jumper "
                                                    "settings")
        super(PiSpareModeCheckL, self).prepare()
        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. Get the list of all SSD,PCI and USB devices
        2. Run 10 G3 cycles
        :return: True, if the test case is successful.
        """
        # Step logger Start for Step 2
        self._test_content_logger.start_step_logger(2)
        self.print_upi_topology()
        self.print_upi_link_speed()
        self.verify_upi_topology()
        if not self.verify_rx_ports_l0_state():
            raise content_exceptions.TestFail(" verification of lo state failed")
        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)
        # Step logger Start for Step 3
        self._test_content_logger.start_step_logger(3)
        # Get a list of all SSDs, PCIs and USBs devices in the setup.
        get_ioe_device_dict_before_cycle = self._multisock_obj.get_ioe_device_dict()
        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)
        # Step logger Start for Step 4
        self._test_content_logger.start_step_logger(4)
        for cycle_number in range(self._common_content_configuration.get_num_of_g3_dpmo_cycles()):
            self.perform_graceful_g3()
            get_ioe_device_dict_after_ac_cycle = self._multisock_obj.get_ioe_device_dict()
            if get_ioe_device_dict_before_cycle != get_ioe_device_dict_after_ac_cycle:
                raise content_exceptions.TestFail("IOE devices are not same after and before AC cycle")
            self._log.info("IO device Status is Verified after AC Cycle no: {}".format(cycle_number))
        # Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiSpareModeCheckL.main() else Framework.TEST_RESULT_FAIL)
