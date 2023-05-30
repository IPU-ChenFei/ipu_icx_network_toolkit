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
import ipccli
from pathlib import Path

from dtaf_core.lib.dtaf_constants import Framework
from src.hsio.upi.hsio_upi_common import HsioUpiCommon
from src.multisocket.lib.multisocket_common import MultiSocketCommon
from src.lib.test_content_logger import TestContentLogger
from src.ras.tests.io_power_management.io_power_management_common import IoPmCommon
from src.rdt.lib.rdt_utils import RdtUtils
from src.lib.platform_config import PlatformConfiguration
from src.lib import content_exceptions
from src.provider.cpu_info_provider import CpuInfoProvider


class PIStressWithMixedUPIMLC(HsioUpiCommon):
    """
    phoenix ID: 16013719256 PI_stress_with_mixed_UPI_using_MLC_L

    This test Stress test with Mixed UPI speeds on Linux.
    """
    UPI_MIXED_LINK_SPEED_BIOS_KNOBS_4S = os.path.join(Path(os.path.dirname(os.path.realpath(__file__))),
                                                 "upi_disable_ports_4s.cfg")

    UPI_MIXED_LINK_SPEED_BIOS_KNOBS_8S = os.path.join(Path(os.path.dirname(os.path.realpath(__file__))),
                                                   "upi_disable_ports_8s.cfg")
    TEST_CASE_ID = ["16013719256", "PI_stress_with_mixed_UPI_using_MLC_L"]

    step_data_dict = {1: {'step_details': 'unlock itp',
                          'expected_results': 'successfully unlocked itp'},
                      2: {'step_details': 'set random upi link speeds',
                          'expected_results': 'random link speed set successfully'},
                      3: {'step_details': 'verify UPI details',
                          'expected_results': 'verified UPI details successfully...'},
                      4: {'step_details': 'run mlc stress ',
                          'expected_results': 'mlc stress ran successfully...'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new PIStressWithMixedUPIMLC object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PIStressWithMixedUPIMLC, self).__init__(
            test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._io_pm_obj = IoPmCommon(test_log, arguments, cfg_opts, config=None)
        self._multisock_obj = MultiSocketCommon(test_log, arguments, cfg_opts)
        self._silicon_family = self._common_content_lib.get_platform_family()
        self._rdt = RdtUtils(test_log, self._common_content_lib, self._common_content_configuration, self.os, cfg_opts)
        self.initialize_sv_objects()
        self.initialize_sdp_objects()
        self._cpu_info_provider = CpuInfoProvider.factory(test_log, cfg_opts, self.os)

    def check_topology_speed_lane(self):
        """
        This method checks the upi topology, link speed and verifies the link lane
        """
        self.SDP.start_log("print_topology.log")
        self.SDP.itp.resettarget()
        self._io_pm_obj.set_bios_break(self.reg_provider_obj, self._io_pm_obj.UPI_POST_CODE_BREAK_POINT)
        # wait for target to enter break point
        self._io_pm_obj.check_bios_progress_code(self.reg_provider_obj, self._io_pm_obj.UPI_POST_CODE_BREAK_POINT)
        self._io_pm_obj.clear_bios_break(self.reg_provider_obj)
        self.os.wait_for_os(self._io_pm_obj.RESUME_FROM_BREAK_POINT_WAIT_TIME_SEC)
        self.print_upi_topology()
        self.print_upi_link_speed()
        self.verify_upi_topology()
        if not (self.verify_rx_ports_l0_state() and self.lanes_operational_check() and self.verify_tx_ports_l0_state()):
            raise content_exceptions.TestFail(" verification of lo state failed")
        self.SDP.stop_log()
        self._multisock_obj.print_topology_logs("print_topology.log")

    def execute(self):
        """
        This method is used to execute PI_stress_with_mixed_UPI_using_MLC_L

        :return True  if successful
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        self._cpu_info_provider.populate_cpu_info()
        sockets_present = self._cpu_info_provider.get_number_of_sockets()
        if sockets_present == 4:
            self.set_and_verify_bios_knobs(self.UPI_MIXED_LINK_SPEED_BIOS_KNOBS_4S)
        elif sockets_present == 8:
            self.set_and_verify_bios_knobs(self.UPI_MIXED_LINK_SPEED_BIOS_KNOBS_8S)

        # check total Memory size before stress
        total_mem_before_stress = self._multisock_obj.get_mem_details()
        self._log.info("Total Memory before Stress : {}".format(total_mem_before_stress))

        self.itp = ipccli.baseaccess()
        self.itp.unlock()
        self.itp.forcereconfig()
        self._test_content_logger.end_step_logger(1, return_val=True)

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        self.set_upi_link_random_speed()
        self._log.info("Bios set, performing cold reset...")
        self.perform_graceful_g3()
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)
        self.check_topology_speed_lane()
        self._test_content_logger.end_step_logger(3, return_val=True)

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)
        mlc_tool_path = self._install_collateral.install_mlc_internal_linux()
        num_iter = self._common_content_configuration.get_mlc_exec_iterations()
        for iter in range(1, num_iter):
            self._log.info("executing mlc stress {} iteration".format(iter))
            self._rdt.run_mlc_stress(mlc_tool_path, self.MLC_STRESS_CMD)

        self.check_topology_speed_lane()
        total_mem_after_stress = self._multisock_obj.get_mem_details()
        self._log.info("Total Memory before Stress : {}".format(total_mem_after_stress))

        self.SDP.start_log("mlc_topology.log")
        pysv_output = self.SV.get_by_path(
            self.SV.UNCORE, PlatformConfiguration.MCE_EVENTS_CHECK_CONFIG[self._silicon_family])
        if str(pysv_output) != "0x0":
            self._log.error("Mce logging check output : {}".format(pysv_output))
            raise content_exceptions.TestFail("Mce error check returned non zero value")
        self.SDP.stop_log()
        self._multisock_obj.print_topology_logs("mlc_topology.log")

        self._test_content_logger.end_step_logger(4, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PIStressWithMixedUPIMLC.main() else Framework.TEST_RESULT_FAIL)
