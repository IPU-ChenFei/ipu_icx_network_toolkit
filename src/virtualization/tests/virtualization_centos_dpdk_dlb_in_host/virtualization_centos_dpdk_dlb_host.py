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

import os
import sys

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.virtualization.virtualization_common import VirtualizationCommon

class VirtualizationDpdkDlbHost(VirtualizationCommon):
    """
    Phoenix ID : 16014124028
    The purpose of this test case is to install and verify HQM driver,DPDK has been downloaded and installed & verified
    successfully on SUT.
    Then execute DPDK and DLB workload inside host
    """
    TEST_CASE_ID = ["p16014124028", "Virtualization_Dpdk_Dlb_host"]
    BIOS_CONFIG_FILE = "virtualization_dpdk_dlb_bios_knobs.cfg"
    STEP_DATA_DICT = {
        1: {'step_details': 'Install HQM and verify it installed or not',
            'expected_results': 'HQM is installed successfully and DPDK folders are present'},
        2: {'step_details': 'Execute DPDK and DLB in host',
            'expected_results': 'DPDK and DLB executed successfully inside host'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of InstallAndVerify HQM,Dpdk & run Dpdk, dlb workload inside host

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.virtualization_dpdk_dlb_bios_knobs = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(VirtualizationDpdkDlbHost, self).__init__(test_log, arguments, cfg_opts, self.virtualization_dpdk_dlb_bios_knobs)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._cfg_opt = cfg_opts

    def prepare(self):
        # type: () -> None
        """Test preparation/setup """

        if self.os.os_type == OperatingSystems.LINUX:
            self._log.info("We have Linux OS for test case... proceeding further..")
        else:
            raise content_exceptions.TestFail("Target is not booted with Linux")
        super(VirtualizationDpdkDlbHost, self).prepare()
        self.set_and_verify_bios_knobs(bios_file_path=self.BIOS_CONFIG_FILE)
        self._vm_provider.create_bridge_network("virbr0")

    def execute(self):
        """
        This method installs the HQM, DPDK on sut and verify if it is installed properly.
        Then execute DPDK and DLB workload inside host
        """
        """
            This function calling hqm installation and verify it is installed successfully and execute 
            DPDK and DLB in host 

            :return: True if test case pass else fail
        """
        self._test_content_logger.start_step_logger(1)
        self.verify_hqm_dlb_kernel()
        self.install_hqm_driver_library()
        self.install_hqm_dpdk_library()
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        self.run_dpdk_work_load()
        self.run_dlb_work_load()
        self._test_content_logger.end_step_logger(2, return_val=True)

        return True

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationDpdkDlbHost.main() else Framework.TEST_RESULT_FAIL)
