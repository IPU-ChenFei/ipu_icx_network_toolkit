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

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral
from src.provider.stressapp_provider import StressAppTestProvider
from src.storage.lib.storage_common import StorageCommon
from src.lib.test_content_logger import TestContentLogger


class SataStabilityStressBurnInAhciModeWindows(ContentBaseTestCase):
    """
    Phoenix ID : 16013762512 - SATA_Stability_and_Stress_Burnin_in_AHCI_Mode_W

    """
    BURNING_WORKLOAD_CONFIG_FILE = "non_booted_sata_disk.bitcfg"
    BIOS_CONFIG_FILE_NAME = "pi_storage_os_install_to_m2_ssd_device.cfg"
    TEST_CASE_ID = ["1509347587", "SATA-Stability and Stress- Burnin in AHCI Mode_l"]
    step_data_dict = {1: {'step_details': 'Set the bios knob SATA Mode Selection to AHCI and SGPIO',
                          'expected_results': 'bios setting is done'},
                      2: {'step_details': '8 Sata SSD to be connected',
                          'expected_results': 'Listed all sata SSD devices'},
                      3: {'step_details': 'Copy burnin tool to OS and install burnin tool',
                          'expected_results': 'Burnin tool installed in OS'},
                      4: {'step_details': 'Start Burnin tool on AHCI mode',
                          'expected_results': 'BurnIn tool started successfully where OS not available'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new SataStabilityStressBurnInWindows object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """

        self._log = test_log
        self._cfg_opts = cfg_opts
        super(SataStabilityStressBurnInAhciModeWindows, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE_NAME)
        self.burnin_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                               self.BURNING_WORKLOAD_CONFIG_FILE)
        self.stress_app_provider = StressAppTestProvider.factory(test_log, os_obj=self.os, cfg_opts=cfg_opts)
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)
        self.storage_common_lib = StorageCommon(self._log, cfg_opts)
        # get the burnin tool run time in minutes from content_configuration.xml file
        self.burnin_execution_time = self._common_content_configuration.get_burnin_test_runtime()
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        This method is to do the below tasks
        1. Verifying the sata devices are connected in the SUT
        2. Setting the bios knob SATA Mode Selection to AHCI
        3. Copy and install burin tool.
        4. Execute burin tool in SSD where OS not installed.

        :return None
        """
        # start of step 1
        self._test_content_logger.start_step_logger(1)

        super(SataStabilityStressBurnInAhciModeWindows, self).prepare()

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, True)

    def execute(self):
        """
        This method is used to install and execute burnin tool.
        """
        # start of step 2
        self._test_content_logger.start_step_logger(2)
        disk_info = self._common_content_lib.execute_sut_cmd("wmic diskdrive list brief", "list disk drive", self._command_timeout)
        self._log.info("Physical  Sata SSD show information...{}".format(disk_info))
        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, True)

        # start of step 3
        self._test_content_logger.start_step_logger(3)
        # install burnin tool
        bit_location = self.collateral_installer.install_burnintest()

        # formatting the sata drive without OS installed
        self.storage_common_lib.format_drive_win(device_type="SATA", booted_format_drive=False)
        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, True)

        # start of step 4
        self._test_content_logger.start_step_logger(4)
        self.stress_app_provider.execute_burnin_test(self.log_dir, self.burnin_execution_time, bit_location,
                                                     self.burnin_config_file, )
        # Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, True)

        return True

    def cleanup(self, return_status):
        """Test Cleanup"""
        self._common_content_lib.store_os_logs(self.log_dir)
        super(SataStabilityStressBurnInAhciModeWindows, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SataStabilityStressBurnInAhciModeWindows.main() else Framework.TEST_RESULT_FAIL)
