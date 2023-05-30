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
import re

from dtaf_core.lib.dtaf_constants import Framework

from src.environment.os_installation import OsInstallation
from src.provider.storage_provider import StorageProvider
from src.lib.test_content_logger import TestContentLogger
from src.lib.install_collateral import InstallCollateral
from src.provider.stressapp_provider import StressAppTestProvider
from src.storage.test.storage_common import StorageCommon


class SataStabilityStressBurnInAhciMode(StorageCommon):
    """
    Phoenix ID : 1509347587 - SATA_Stability_and_Stress_Burnin_in_AHCI_Mode_L

    """
    BURNING_100_WORKLOAD_CONFIG_FILE = "cmdline_config_100_workload.txt"
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
        Creates a new SataStabilityStressBurnIn object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """

        self._log = test_log
        self._cfg_opts = cfg_opts
        super(SataStabilityStressBurnInAhciMode, self).__init__(test_log, arguments, cfg_opts,self.BIOS_CONFIG_FILE_NAME)
        self._storage_provider = StorageProvider.factory(self._log, self.os, self._cfg_opts, "os")
        cur_path = os.path.dirname(os.path.realpath(__file__))
        self._bios_config_file_path = os.path.join(cur_path, self.BIOS_CONFIG_FILE_NAME)
        self._os_installation_lib = OsInstallation(test_log, cfg_opts)
        self.log_dir = self._common_content_lib.get_log_file_dir()
        self._storage_common = StorageCommon(test_log, arguments, self._cfg_opts)
        self.collateral_installer = InstallCollateral(test_log, self.os, self._cfg_opts)
        self._stress_provider = StressAppTestProvider.factory(test_log, cfg_opts, self.os)
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        sata_ssd = set(self._storage_common.get_smartctl_drive_list())
        booted_device = self._storage_provider.get_booted_device()
        booted_device = re.findall("[a-zA-Z]*", booted_device)[0]
        booted_device_drive = set("/dev/" + str(booted_device))
        lsblk_res = sata_ssd - booted_device_drive
        non_os_disk = " "
        for each in lsblk_res:
            non_os_disk = non_os_disk + each + " "

        # Object of TestContentLogger class
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

        super(SataStabilityStressBurnInAhciMode, self).prepare()

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, True)

    def execute(self):
        """
        This method is used to install and execute burnin tool.
        """
        # start of step 2
        self._test_content_logger.start_step_logger(2)
        dict_storage_devices = self._storage_provider.enumerate_sata_disks()
        dict_storage_devices = [each ['DiskName'] for each in dict_storage_devices]
        self._log.info("Total number of devices list = {} and device list = {}".format(len(dict_storage_devices), dict_storage_devices))
        self.os.reboot(self._reboot_timeout)
        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, True)

        # start of step 3
        self._test_content_logger.start_step_logger(3)
        # install burnin tool
        bit_location = self.collateral_installer.install_burnintest()
        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, True)
        # start of step 4
        self._test_content_logger.start_step_logger(4)
        self.burnin_config_file_host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
            self.BURNING_100_WORKLOAD_CONFIG_FILE)
        burnin_tool_runtime = self._common_content_configuration.burnin_test_execute_time()
        self._stress_provider.execute_burnin_stresstest(self.log_dir, burnin_tool_runtime, bit_location,
                                                        self.BURNING_100_WORKLOAD_CONFIG_FILE, stress_boot=False)

        # Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, True)

        return True

    def cleanup(self, return_status):
        """Test Cleanup"""
        self._common_content_lib.store_os_logs(self.log_dir)
        super(SataStabilityStressBurnInAhciMode, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SataStabilityStressBurnInAhciMode.main() else Framework.TEST_RESULT_FAIL)
