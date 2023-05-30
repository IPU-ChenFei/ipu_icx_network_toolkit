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

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from src.provider.vss_provider import VssProvider

from src.rdt.lib.rdt_utils import RdtUtils

from src.lib.dtaf_content_constants import PcieSlotAttribute
from src.lib.test_content_logger import TestContentLogger
from src.pcie.tests.pi_pcie.pcie_common import PcieCommon
from src.provider import vss_provider
from src.lib import content_exceptions


class PCIECorrectableErrorCheckingRASDuringStressLinux(PcieCommon):
    """
    HPQC : 82147-PI_PCIe_Correctable_error_checking-RAS_during_stress_L
    glasgow id: 10712-Stress - PCIe Correctable error checking - RAS during stress
    phoenix id: 18014075888 - PCIe Correctable error checking - RAS during stress

    The purpose of this test is to ensure that no PCIe correctable errors occur
    during execution of stress on one or more PCIe devices in the SUT.
    This test is intended to be run in parallel with a stress test case.
    """
    TEST_CASE_ID = ["H82147", "PI_PCIe_Correctable_error_checking-RAS_during_stress_L",
                    "G10712", "Stress-PCIe Correctable error checking-RAS during stress"]
    ILVSS_CMD = "./t /pkg /opt/ilvss.0/packages/stress_egs.pkx /reconfig /pc EGS /flow S145 /run /minutes {} /rr {}"
    ILVSS_LOG = "ilvss_log.log"
    step_data_dict = {
        1: {'step_details': 'Check if All slots are populated or not',
            'expected_results': 'All slots are populated with required PCIE cards.'},
        2: {'step_details': 'Install and Run PCIERRPoll tool on the SUT',
            'expected_results': 'Successfully installed and executed PCIERRPoll tool'},
        3: {'step_details': 'Install ilvss tool',
            'expected_results': 'Successfully installed ilvss tool'},
        4: {'step_details': 'Start the ilvss tool and PCIERRPoll to stress the system',
            'expected_results': 'Successfully initiated the Stress into the SUT'},
        5: {'step_details': 'Check for any PCIe Correctable errors from the run',
            'expected_results': 'PCIe errors in total is be below the acceptable '
                                'error threshold for the platform as Expected'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a PCIECorrectableErrorCheckingRASDuringStressLinux object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PCIECorrectableErrorCheckingRASDuringStressLinux, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.step_data_dict)
        self._utils = RdtUtils(self._log, self._common_content_lib, self._common_content_configuration, self.os,
                               cfg_opts)
        self._ilvss_runtime = self._common_content_configuration.memory_ilvss_run_time()
        self._vss_provider_obj = VssProvider.factory(self._log, cfg_opts=cfg_opts, os_obj=self.os)

    def prepare(self):  # type: () -> None
        """
        Setup actions for this test case. Executed before the test logic in execute is called.
        """
        super(PCIECorrectableErrorCheckingRASDuringStressLinux, self).prepare()

    def execute(self):
        """
        This method is to execute:
        1. Check if All slots are populated or not
        2. Install PCIERRPoll tool on the SUT
        3. Install ilvss tool
        4. Start the ilvss tool and PCIERRPoll to stress the system
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
        self._install_collateral.screen_package_installation()
        pcierrpoll_path = self._install_collateral.install_pcierrpoll()
        self.run_pcierrpoll(10, pcierrpoll_path)
        self.os.execute_async(self._utils.KILL_CMD.format("PCIERRpoll"))
        self._test_content_logger.end_step_logger(2, True)

        # Install ilvss tool
        self._test_content_logger.start_step_logger(3)
        self._test_content_logger.end_step_logger(3, True)

        # Start the ilvss tool and PCIERRPoll to stress the system
        self._test_content_logger.start_step_logger(4)

        self.run_pcierrpoll(self._command_timeout, pcierrpoll_path)
        self.os.execute_async(self.ILVSS_CMD.format(self._ilvss_runtime, self.ILVSS_LOG),
                              self._vss_provider_obj.OPT_IVLSS)
        time.sleep(self._command_timeout)
        self._test_content_logger.end_step_logger(4, True)

        # Check for any PCIe Correctable errors from the run
        self._test_content_logger.start_step_logger(5)
        ilvss_hostfilepath = self.log_dir + "\\" + self.ILVSS_LOG
        self.os.copy_file_from_sut_to_local(self._vss_provider_obj.OPT_IVLSS + "/" + self.ILVSS_LOG, ilvss_hostfilepath)
        with open(ilvss_hostfilepath, "r") as ilvss_handler:
            self._log.debug("{} contents : {}".format(ilvss_hostfilepath, "\n".join(ilvss_handler.readlines())))
            if self._vss_provider_obj.ILVSS_PCIE_SUCCESS_STR not in ilvss_handler.readlines():
                content_exceptions.TestFail(
                    "Correctable errors found in selected PCIe devices while running the stress")
        self._log.info("No errors found in selected PCIe devices while running the stress")
        self._test_content_logger.end_step_logger(5, True)
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PCIECorrectableErrorCheckingRASDuringStressLinux, self).cleanup(return_status)
        self.os.execute_async(self._utils.KILL_CMD.format(self.ILVSS_STR))
        self.os.execute_async(self._utils.KILL_CMD.format(self.PCIERRPOLL_STR))


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PCIECorrectableErrorCheckingRASDuringStressLinux.main() else
             Framework.TEST_RESULT_FAIL)
