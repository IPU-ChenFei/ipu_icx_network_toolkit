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

from dtaf_core.lib.dtaf_constants import Framework
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.bios_util import SerialBiosUtil
from src.lib.test_content_logger import TestContentLogger
from src.storage.lib.sata_raid_util import SataRaidUtil
from src.environment.os_installation import OsInstallation
from src.provider.storage_provider import StorageProvider
from src.lib import content_exceptions
from src.lib.dtaf_content_constants import SutInventoryConstants

class StorageBootingToSataRaid0Raid1(ContentBaseTestCase):
    """
    HPALM : 80260-PI_Storage_BootingToSATARAID_RAID0RAID1_L/
            80249-PI_Storage_RSTe_SATA_RAID0RAID1_L
    this class used for create RAID using two SATA drives,
    Install RHEL OS on RAID and delete RAID.
    """

    TEST_CASE_ID = ["H80260", "PI_Storage_BootingToSATARAID_RAID0RAID1_L",
                    "H80249", "PI_Storage_RSTe_SATA_RAID0RAID1_L"]

    step_data_dict = {
                      1: {'step_details': 'create the RAID0 using two SATA Drives',
                          'expected_results': 'RAID0 Creation successful'},
                      2: {'step_details': 'Install RHEL OS on RAID0 and boot to  OS',
                          'expected_results': 'Successfully installed OS'},
                      3: {'step_details': 'Verify OS is successfully installed in RAID0',
                          'expected_results': 'Verified OS installation is successful in RAID0'},
                      4: {'step_details': 'delete RAID0 Volume',
                          'expected_results': 'Successfully deleted RAID0 Volume'},
                      5: {'step_details': 'repeat the steps 1 to 4 for RAID1',
                          'expected_results': 'Successfully verified for RAID1'},
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
         Creates a new StorageBootingToSataRaid0Raid1 object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        self._log = test_log
        self._cfg_opts = cfg_opts

        self._cc_log_path = arguments.outputpath

        super(StorageBootingToSataRaid0Raid1, self).__init__(test_log, arguments, cfg_opts)
        self._serial_bios_util = SerialBiosUtil(self.ac_power, test_log, self._common_content_lib, cfg_opts)
        self._raid_util = SataRaidUtil(self._log, self._common_content_lib, self._common_content_configuration,
                                       self.bios_util, self._serial_bios_util, self.ac_power)
        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

        self._os_installation_lib = OsInstallation(test_log, cfg_opts)
        self._storage_provider = StorageProvider.factory(self._log, self.os, self._cfg_opts, "os")
        self.raid_levels = list()
        self.raid_levels_test = list()
        self._ac = self.ac_power
        self.non_raid_disk_name = None
        self.raid_disk_name = None

    def prepare(self):
        # type: () -> None
        """
        This method is to get the non raid disk name from sut inventory
        :return None
        """
        sut_inv_file_path = self._os_installation_lib.get_sut_inventory_file_path()
        with open(sut_inv_file_path, "r") as fh:
            for line in fh.readlines():
                if SutInventoryConstants.NON_RAID_SSD_NAME in line:
                    self.non_raid_disk_name = line
                if SutInventoryConstants.SATA_RAID_SSD_NAME in line:
                    self.raid_disk_name = line

        if not self.non_raid_disk_name:
            raise content_exceptions.TestError("Unable to find non RAID SSD name, please check the file under "
                                               "{}".format(sut_inv_file_path))
        if not self.raid_disk_name:
            raise content_exceptions.TestError("Unable to find SATA RAID SSD name, please check the file under "
                                               "{}".format(sut_inv_file_path))

        self.non_raid_disk_name = self.non_raid_disk_name.split("=")[1]
        self.raid_disk_name = self.raid_disk_name.split("=")[1]
        self._log.info("SATA RAID SSD Name from config file : {}".format(self.raid_disk_name))
        self._log.info("non RAID SSD Name from config file : {}".format(self.non_raid_disk_name))
        self._common_content_lib.update_sut_inventory_file(SutInventoryConstants.SATA_RAID, SutInventoryConstants.RHEL)

    def execute(self):
        """
        This Function to create RAID, install OS and delete RAID.
        :return: True if RAID creation, OS installation and deletion Successful else False
        """
        ret_val = []
        self.raid_levels = ["RAID0(Stripe)", "RAID1(Mirror)"]
        self._log.info("Getting raid levels info from BIOS page")
        raid_levels_supported = self._raid_util.get_supported_raid_levels()
        self._log.debug("Supported RAID Levels for current Device Setup are {}".format(raid_levels_supported))
        for raid_level in self.raid_levels:
            if raid_level in raid_levels_supported:
                self.raid_levels_test.append(raid_level)

        if len(self.raid_levels_test) < 2:
            raise content_exceptions.TestFail("For Creating a RAID need atleast two Empty  are required, "
                                              "please try again by Connecting two Empty Disks..")
        # performing AC POWER OFF and ON.
        self._common_content_lib.perform_graceful_ac_off_on(self._ac)
        self._log.info("Waiting for SUT to boot to OS..")
        self.os.wait_for_os(self.reboot_timeout)

        for raid_level in self.raid_levels_test:
            # Step logger start for Step 1
            self._test_content_logger.start_step_logger(1)
            bios_info = self._raid_util.create_raid(raid_level)
            self.os.wait_for_os(self.reboot_timeout)
            # Step logger end for Step 1
            self._test_content_logger.end_step_logger(1, return_val=True)
            self._log.info("Closing the Serial Port")
            self.cng_log.__exit__(None, None, None)
            # Step logger start for Step 2
            self._test_content_logger.start_step_logger(2)

            ret_val.append(self._os_installation_lib.rhel_os_installation())
            # Step logger end for Step 2
            self._test_content_logger.end_step_logger(2, return_val=all(ret_val))
            # Step logger start for Step 3
            self._test_content_logger.start_step_logger(3)

            md_stat_res = self._storage_provider.get_booted_raid_disk()
            self._log.debug("booted device is {}".format(str(md_stat_res)))

            if md_stat_res.upper() not in raid_level.upper():
                raise content_exceptions.TestFail("OS not installed on the RAID, please try again..")

            self._log.info("Successfully verified that OS installed in {} device..".format(md_stat_res.upper()))
            # Step logger end for Step 3
            self._test_content_logger.end_step_logger(3, return_val=True)
            self._log.info("Reopening the Serial Port")
            try:
                self._serial_bios_util = SerialBiosUtil(self.ac_power, self._log, self._common_content_lib,
                                                        self._cfg_opts)
                self._raid_util = SataRaidUtil(self._log, self._common_content_lib, self._common_content_configuration,
                                               self.bios_util, self._serial_bios_util, self.ac_power)

            except Exception as ex:
                self._log.debug("Exception occurred while creating serial_bios_util but we can ignore it:{}".format(ex))
            # Step logger start for Step 4
            self._test_content_logger.start_step_logger(4)
            self._raid_util.delete_raid(raid_level, self.non_raid_disk_name)
            self.os.wait_for_os(self.reboot_timeout)
            # Step logger end for Step 4
            self._test_content_logger.end_step_logger(4, return_val=True)

        return all(ret_val)

    def cleanup(self, return_status):
        """Test Cleanup"""
        self._common_content_lib.store_os_logs(self.log_dir)

        # setting back the default bios knobs
        self.bios_util.load_bios_defaults()
        self.perform_graceful_g3()
        super(StorageBootingToSataRaid0Raid1, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StorageBootingToSataRaid0Raid1.main() else Framework.TEST_RESULT_FAIL)
