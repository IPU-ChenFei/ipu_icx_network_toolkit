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
import time

import ipccli

from dtaf_core.lib.dtaf_constants import Framework

from src.hsio.upi.hsio_upi_common import HsioUpiCommon
from src.multisocket.lib.multisocket_common import MultiSocketCommon
from src.lib.install_collateral import InstallCollateral
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.platform_config import PlatformConfiguration
from src.lib.test_content_logger import TestContentLogger
from src.ras.tests.io_power_management.io_power_management_common import IoPmCommon
from src.rdt.lib.rdt_utils import RdtUtils
from src.lib import content_exceptions


class ProcesorCPUMEMStress(ContentBaseTestCase):
    """
    phoenix ID: 16013411473 PI_Procesor_CPU_MEM_stress_L

    The intention is to check the system behavior when the system is  MEM- stressed using MLC
    and STREAM stress tools and ensure the all CPU cores comes back to idle state after the test.
    """
    TEST_CASE_ID = ["16013411473", "PI_Procesor_CPU_MEM_stress_L"]
    MLC_STRESS_CMD = "./mlc_internal"
    CHECK_SOCKET_CONF_CMD = "lscpu | grep 'NUMA node(s)'"
    STREAM_COMMAND = "./stream"
    PKILL_STREAM_COMMAND = "pkill stream"
    step_data_dict = {1: {'step_details': 'Check if the System is 8S or 4S',
                          'expected_results': 'successfully Checked if the System is 8S or 4S'},
                      2: {'step_details': 'Install MLC Tool and run stress',
                          'expected_results': 'MLC stress ran successfully without any errors.'},
                      3: {'step_details': 'Install and Run Stream Benchmark',
                          'expected_results': 'Stream Benchmark Ran successfully without encountering any errors!'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new ProcesorCPUMEMStress object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(ProcesorCPUMEMStress, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._io_pm_obj = IoPmCommon(test_log, arguments, cfg_opts, config=None)
        self._rdt = RdtUtils(test_log, self._common_content_lib, self._common_content_configuration, self.os, cfg_opts)
        self._install_collateral = InstallCollateral(test_log, self.os, cfg_opts)
        self.hsio_obj = HsioUpiCommon(test_log, arguments, cfg_opts)
        self._silicon_family = self._common_content_lib.get_platform_family()
        self._multisock_obj = MultiSocketCommon(test_log, arguments, cfg_opts)
        self.initialize_sv_objects()
        self.initialize_sdp_objects()

    def prepare(self):  # type: () -> None
        """
        To check topology is same as the DUT configuration

        :return: None
        """
        # check total Memory size before stress
        total_mem_before_stress = self._multisock_obj.get_mem_details()
        self._log.info("Total Memory before Stress : {}".format(total_mem_before_stress))

        self._common_content_lib.clear_os_log()  # To clear os logs
        self._common_content_lib.clear_dmesg_log()  # To clear dmesg logs
        self._multisock_obj.check_topology_speed_lanes(self.SDP)
    def execute(self):
        """
        This method is used to execute PI_stress_with_mixed_UPI_using_MLC_L

        :return True  if successful
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        cmd_output = self._common_content_lib.execute_sut_cmd(self.CHECK_SOCKET_CONF_CMD, self.CHECK_SOCKET_CONF_CMD,
                                                              self._command_timeout)
        self._log.debug("{} Command Output : {}".format(self.CHECK_SOCKET_CONF_CMD, cmd_output))
        self._log.info("This testcase is Running on {}S system configuration".format(cmd_output.split(":")[1].strip()))
        self._test_content_logger.end_step_logger(1, return_val=True)

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        # copy mlc tool and install it on the SUT
        mlc_tool_path = self._install_collateral.install_mlc_internal_linux()
        num_iter = self._common_content_configuration.get_mlc_exec_iterations()
        for iter in range(1, num_iter):
            self._log.info("executing mlc stress {} iteration".format(iter))
            self._rdt.run_mlc_stress(mlc_tool_path, self.MLC_STRESS_CMD)

        # Run sv.sockets.uncore.ubox.ncevents.mcerrloggingreg.show() and check dmesg error logs
        self._log.info("Dump dmesg and search for 'Fatal' or 'error' keywords")
        cmd_output = self._common_content_lib.execute_sut_cmd("dmesg", "dmesg", self._command_timeout)
        if any(word in cmd_output for word in ["Fatal", "FATAL", "fatal", "Error", "error"]):
            raise content_exceptions.TestFail("dmesg returned errors : {}".format(cmd_output))
        self._log.info("No Error Found in dmesg logs")

        self.SDP.start_log("mlc_topology.log")
        pysv_output = self.SV.get_by_path(
            self.SV.UNCORE, PlatformConfiguration.MCE_EVENTS_CHECK_CONFIG[self._silicon_family])
        if str(pysv_output) != "0x0":
            self._log.error("Mce logging check output : {}".format(pysv_output))
            raise content_exceptions.TestFail("Mce error check returned non zero value")
        self.SDP.stop_log()
        self._multisock_obj.print_topology_logs("mlc_topology.log")
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(3)
        self.stream_folder_path = self._install_collateral.install_rdt_stream_tool_to_sut()

        for iter in range(1, num_iter):
            self._log.info("executing stream benchmark stress {} iteration".format(iter))
            self.os.execute_async(self.STREAM_COMMAND, self.stream_folder_path)
            self._rdt.check_rdt_monitor_command_running_status(self.STREAM_COMMAND)
            time.sleep(60)
            self._common_content_lib.execute_sut_cmd(self.PKILL_STREAM_COMMAND, "running {}".format(self.PKILL_STREAM_COMMAND),
                                                     self._command_timeout, self.stream_folder_path)

        # Run sv.sockets.uncore.ubox.ncevents.mcerrloggingreg.show() and check logs
        self.SDP.start_log("mlc_topology.log")
        pysv_output = self.SV.get_by_path(
            self.SV.UNCORE, PlatformConfiguration.MCE_EVENTS_CHECK_CONFIG[self._silicon_family])
        if str(pysv_output) != "0x0":
            self._log.error("Mce logging check output : {}".format(pysv_output))
            raise content_exceptions.TestFail("Mce error check returned non zero value")
        self.SDP.stop_log()
        self._multisock_obj.print_topology_logs("mlc_topology.log")

        # check total Memory size after stress
        total_mem_after_stress = self._multisock_obj.get_mem_details()
        self._log.info("Total Memory before Stress : {}".format(total_mem_after_stress))

        self._log.info("Dump dmesg and search for 'Fatal' or 'error' keywords")
        cmd_output = self._common_content_lib.execute_sut_cmd("dmesg", "dmesg", self._command_timeout)
        if any(word in cmd_output for word in ["Fatal", "FATAL", "fatal", "Error", "error"]):
            raise content_exceptions.TestFail("dmesg returned errors : {}".format(cmd_output))
        self._log.info("No Error Found in dmesg logs")
        self._multisock_obj.check_topology_speed_lanes(self.SDP)
        self._test_content_logger.end_step_logger(3, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ProcesorCPUMEMStress.main() else Framework.TEST_RESULT_FAIL)
