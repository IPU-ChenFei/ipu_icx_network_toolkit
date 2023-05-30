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

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.bios_util import SerialBiosUtil
from src.lib.dtaf_content_constants import RaidConstants
from src.provider.storage_provider import StorageProvider
from src.lib.test_content_logger import TestContentLogger
from src.lib.install_collateral import InstallCollateral
from src.provider.stressapp_provider import StressAppTestProvider
from src.storage.lib.sata_raid_util import SataRaidUtil
from src.storage.test.storage_common import StorageCommon


class SataStabilityStressBurnInWithRaid1L(StorageCommon):
    """
    Phoenix ID : 1509349711 - SATA-Stability and Stress- Burnin with RAID 1
    """
    BURNING_100_WORKLOAD_CONFIG_FILE = "cmdline_config_100_workload.txt"
    BIOS_CONFIG_FILE_NAME = "sata_stability_stress_burnin_with_raid1.cfg"
    TEST_CASE_ID = ["1509349711", "SATA-Stability and Stress- Burnin with RAID 1"]
    step_data_dict = {1: {'step_details': 'Set the bios knob SATA Mode Selection to RAID and SGPIO',
                          'expected_results': 'bios setting is done'},
                      2: {'step_details': 'List all Sata SSD connected',
                          'expected_results': 'Listed all sata SSD devices'},
                      3: {'step_details': 'Create Raid 1',
                          'expected_results': 'Raid1 has been created successfully'},
                      4: {'step_details': 'Copy burnin tool to OS and install burnin tool',
                          'expected_results': 'Burnin tool installed in OS'},
                      5: {'step_details': 'Start Burnin tool on RAID disk',
                          'expected_results': 'BurnIn tool started successfully on RAID disk'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new SataStabilityStressBurnInWithRaid1L object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        self._log = test_log
        self._cfg_opts = cfg_opts

        super(SataStabilityStressBurnInWithRaid1L, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE_NAME)
        self._storage_provider = StorageProvider.factory(self._log, self.os, self._cfg_opts, "os")
        self._serial_bios_util = SerialBiosUtil(self.ac_power, self._log, self._common_content_lib,
                                                self._cfg_opts)
        self._raid_util = SataRaidUtil(self._log, self._common_content_lib, self._common_content_configuration,
                                       self.bios_util, self._serial_bios_util, self.ac_power)
        cur_path = os.path.dirname(os.path.realpath(__file__))
        self._bios_config_file_path = os.path.join(cur_path, self.BIOS_CONFIG_FILE_NAME)
        self.log_dir = self._common_content_lib.get_log_file_dir()
        self.collateral_installer = InstallCollateral(test_log, self.os, self._cfg_opts)
        self._stress_provider = StressAppTestProvider.factory(test_log, cfg_opts, self.os)
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        self._ac = self.ac_power
        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        Setting the bios knob SATA Mode Selection to RAID

        :return None
        """
        # start of step 1
        self._test_content_logger.start_step_logger(1)
        super(SataStabilityStressBurnInWithRaid1L, self).prepare()
        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, True)

    def execute(self):
        """
        This method is to do the below tasks
        1. Verifying the sata devices are connected in the SUT
        2. Create Raid
        3. Copy and install burin tool.
        4. Execute burin tool on raid volume
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
        self.raid_levels_test = []
        ret_val = []
        self.raid_level = RaidConstants.RAID1
        self._log.info("Getting raid levels info from BIOS page")
        raid_levels_supported = self._raid_util.get_supported_raid_levels()
        self._log.debug("Supported RAID Levels for current Device Setup are {}".format(raid_levels_supported))
        if RaidConstants.RAID1 in raid_levels_supported:
            self.raid_levels_test.append(RaidConstants.RAID1)

        self._common_content_lib.perform_graceful_ac_off_on(self._ac)
        self._log.info("Waiting for SUT to boot to OS..")
        self.os.wait_for_os(self.reboot_timeout)

        bios_info = self._raid_util.create_raid(RaidConstants.RAID1)
        self.os.wait_for_os(self.reboot_timeout)
        self._log.info("Closing the Serial Port")
        self.cng_log.__exit__(None, None, None)
        self._log.info("Reopening the Serial Port")
        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)

        # start of step 4
        self._test_content_logger.start_step_logger(4)
        # install burnin tool
        bit_location = self.collateral_installer.install_burnintest()
        # Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, True)

        # start of step 5
        self._test_content_logger.start_step_logger(5)
        self.burnin_config_file_host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
            self.BURNING_100_WORKLOAD_CONFIG_FILE)
        burnin_tool_runtime = self._common_content_configuration.burnin_test_execute_time()
        self._stress_provider.execute_burnin_stresstest_on_raid(self.log_dir, burnin_tool_runtime, bit_location,
                                                                self.burnin_config_file_host_path)
        # Step logger end for Step 5
        self._test_content_logger.end_step_logger(5, True)

        return True

    def cleanup(self, return_status):
        """Test Cleanup"""
        self._common_content_lib.store_os_logs(self.log_dir)
        super(SataStabilityStressBurnInWithRaid1L, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SataStabilityStressBurnInWithRaid1L.main() else Framework.TEST_RESULT_FAIL)
