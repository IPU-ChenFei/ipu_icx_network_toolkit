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
import time
import os
import threading

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from src.provider.vss_provider import VssProvider

from src.rdt.lib.rdt_utils import RdtUtils
from src.lib.dtaf_content_constants import PcieSlotAttribute
from src.lib.test_content_logger import TestContentLogger
from src.pcie.tests.pi_pcie.pcie_common import PcieCommon
from src.provider import vss_provider
from src.lib import content_exceptions
from src.lib.dtaf_content_constants import TimeConstants


class PCIECorrectableErrorCheckingRASDuringStressWindows(PcieCommon):
    """
    phoenix id: 18014075893 - PCIe Correctable error checking in windows- RAS during stress

    The purpose of this test is to ensure that no PCIe correctable errors occur
    during execution of stress on one or more PCIe devices in the SUT.
    This test is intended to be run in parallel with a stress test case.
    """
    TEST_CASE_ID = ["18014075893", "PI_PCIe_Correctable_error_checking-RAS_during_stress_Gen5_W"]
    IWVSS_CMD = r"cmd /C t.exe /pkg EGS\EGS_pcie.pkx /reconfig /pc EGS /flow S145 /run /minutes {} /RR {}"
    IWVSS_LOG = "iwvss_log.log"
    IWVSS_ERROR = "ERROR"
    step_data_dict = {
        1: {'step_details': 'Check if All slots are populated or not',
            'expected_results': 'All slots are populated with required PCIE cards.'},
        2: {'step_details': 'Install and Run PCIERRPoll tool on the SUT',
            'expected_results': 'Successfully installed and executed PCIERRPoll tool'},
        3: {'step_details': 'Install iwvss tool',
            'expected_results': 'Successfully installed iwvss tool'},
        4: {'step_details': 'Start the iwvss tool and PCIERRPoll to stress the system',
            'expected_results': 'Successfully initiated the Stress into the SUT'},
        5: {'step_details': 'Check for any PCIe Correctable errors from the run',
            'expected_results': 'PCIe errors in total is be below the acceptable '
                                'error threshold for the platform as Expected'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a PCIECorrectableErrorCheckingRASDuringStressWindows object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PCIECorrectableErrorCheckingRASDuringStressWindows, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)
        self._vss_provider_obj = VssProvider.factory(self._log, cfg_opts=cfg_opts, os_obj=self.os)


    def prepare(self):  # type: () -> None
        """
        Setup actions for this test case. Executed before the test logic in execute is called.
        """
        super(PCIECorrectableErrorCheckingRASDuringStressWindows, self).prepare()


    def execute(self):
        """
        This method is to execute:
        1. Check if All slots are populated or not
        2. Install PCIERRPoll tool on the SUT
        3. Install iwvss tool
        4. Start the iwvss tool and PCIERRPoll to stress the system
        5. Check for any PCIe Correctable errors from the run

        :return: True or False
        """

        # Check if All slots are populated or not
        self._test_content_logger.start_step_logger(1)
        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        slot_list = self._common_content_configuration.get_pcie_slot_to_check()
        pcie_slot_device_list = self._common_content_configuration.get_required_pcie_device_details(
            product_family=self._product_family, required_slot_list=slot_list)
        self.verify_required_slot_pcie_device(cscripts_obj=cscripts_obj, pcie_slot_device_list=pcie_slot_device_list,
                                              generation=5, lnk_cap_width_speed=False, lnk_stat_width_speed=False)
        self._test_content_logger.end_step_logger(1, True)

        # Install PCIERRPoll tool on the SUT
        self._test_content_logger.start_step_logger(2)

        pcierrpoll_path = self._install_collateral.install_pcierrpoll()
        pcie_err_thread = threading.Thread(target=self.run_pcierrpoll_win,
                                           args=(TimeConstants.TEN_MIN_IN_SEC, pcierrpoll_path,))
        pcie_err_thread.start()
        time.sleep(int(TimeConstants.TEN_MIN_IN_SEC) - int(TimeConstants.ONE_MIN_IN_SEC))
        self._stres_provider_obj.kill_stress_tool(stress_tool_name="PCIERRpoll_debug")
        pcie_err_thread.join()

        # Start the iwvss tool and PCIERRPoll to stress the system
        self._test_content_logger.start_step_logger(4)
        self.sut_platform_pkg_path = os.path.join(self._vss_provider_obj._vss_path, "EGS")

        self.host_platform_pkg_path = self._install_collateral.download_tool_to_host("EGS_pcie.pkx")
        self.os.copy_local_file_to_sut(self.host_platform_pkg_path, self.sut_platform_pkg_path)

        pcie_err_thread = threading.Thread(target=self.run_pcierrpoll_win,
                                           args=(self._command_timeout, pcierrpoll_path,))
        iwvss_thread = threading.Thread(target=self.execute_vss, args=(
                                    self.IWVSS_CMD.format(self._command_timeout, self.IWVSS_LOG),
                                    self._vss_provider_obj._vss_path,))
        iwvss_thread.start()
        pcie_err_thread.start()
        time.sleep(self._command_timeout - int(TimeConstants.ONE_MIN_IN_SEC))
        self._stres_provider_obj.kill_stress_tool(stress_tool_name="t")
        self._stres_provider_obj.kill_stress_tool(stress_tool_name="PCIERRpoll_debug")
        iwvss_thread.join()
        pcie_err_thread.join()

        # Parsing iwvss log
        log_dir = self._common_content_lib.get_log_file_dir()
        log_file_path_host = self._common_content_lib.copy_log_files_to_host(
            test_case_id=log_dir, sut_log_files_path=str(self._vss_provider_obj._vss_path), extension=".log")

        # Check for any PCIe Correctable errors from the run
        self._test_content_logger.start_step_logger(5)
        log_file_path_host = self._common_content_lib.copy_log_files_to_host(
            test_case_id=log_dir, sut_log_files_path=str(self._vss_provider_obj._vss_path), extension=".log")

        iwvss_hostfilepath = self.log_dir + os.sep + self.IWVSS_LOG
        with open(iwvss_hostfilepath, "r") as iwvss_handler:
            if self.IWVSS_ERROR not in iwvss_handler.readlines():
                content_exceptions.TestFail(
                    "Correctable errors found in selected PCIe devices while running the stress")
        self._log.info("No errors found in selected PCIe devices while running the stress")
        self._test_content_logger.end_step_logger(5, True)
        return True


    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PCIECorrectableErrorCheckingRASDuringStressWindows, self).cleanup(return_status)

    def execute_vss(self, cmd, vss_path):
        """
        Function to run the iwVSS command on the SUT.

        :param cmd: iwvss command
        :param vss_path: path of the iwvss executables
        :return None
        """
        self._log.info("Executing the command : {}".format(cmd))
        self.os.execute(cmd, self._command_timeout, str(self._vss_provider_obj._vss_path))


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PCIECorrectableErrorCheckingRASDuringStressWindows.main() else
             Framework.TEST_RESULT_FAIL)
