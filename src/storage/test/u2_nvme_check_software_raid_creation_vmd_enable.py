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

from src.lib.test_content_logger import TestContentLogger
from src.storage.test.storage_common import StorageCommon
from src.provider.storage_provider import StorageProvider
from src.environment.os_installation import OsInstallation
from src.lib import content_exceptions
from src.lib.dtaf_content_constants import RaidConstants, SutInventoryConstants
from src.storage.lib.nvme_raid_util import NvmeRaidUtil
from src.lib.bios_util import SerialBiosUtil
import re

class U2NvmeRAIDinVMDenable(StorageCommon):
    """
    PHOENIX ID : 16013579805 - U.2 NVME Check Software RAID creation in VMD Enable with RAID

    This Class Creates RAID0/RAID1/RAID5/RAID10 using OS level commands.
    """
    TEST_CASE_ID = ["16013579805", "U.2 NVME Check Software RAID creation in VMD Enable with RAID"]
    CMD_CREATE_RAID = "yes | mdadm --create --verbose /dev/md{} --level={} --raid-devices={} {}"
    CMD_DELETE_RAID = "mdadm -S /dev/{}"
    REGEX_MD_LEVEL = "(md\d+)"

    STEP_DATA_DICT = {
        1: {'step_details':'Enable the VMD BIOS knobs and do reset',
            'expected_results': 'All the knobs to be enabled and system to be reset successfully'},
        2: {'step_details':'Create RAID0/RAID1/RAID5/RAID10 volume',
            'expected_results': 'RAID0/RAID1/RAID5/RAID10 volume to be created successfully'},
        3: {'step_details': 'Verify RAID0/RAID1/RAID5/RAID10 created',
            'expected_results':'verified RAID0/RAID1/RAID5/RAID10 Volume successfully'},
        4: {'step_details': 'delete RAID0/RAID1/RAID5/RAID10 ',
            'expected_results': 'deleted RAID0/RAID1/RAID5/RAID10 Volume successfully'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new U2NvmeRAIDinVMDenable object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(U2NvmeRAIDinVMDenable, self).__init__(test_log, arguments, cfg_opts)
        self.storage_provider = StorageProvider.factory(self._log, self.os, cfg_opts, "os")
        self.nvme_disk_list = self._common_content_configuration.get_nvme_disks()
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._raid_util = NvmeRaidUtil(self._log, self._common_content_lib, self._common_content_configuration,
                                       self.bios_util, self._serial_bios_util, self.ac_power)
        self._cfg_opts = cfg_opts
        self.sup_nvme_disk_list = None
        self.raid_levels = [RaidConstants.RAID0, RaidConstants.RAID1, RaidConstants.RAID5, RaidConstants.RAID10]
        self.raid_levels_int = [0, 1, 5, 10]

    def prepare(self):
        # type: () -> None
        """
        This is Method is used to get the Non RAID SSD name to boot into OS.
        :return None
        """

        for disk in self.nvme_disk_list: # loop to check if the devices exist on the SUT
            disk_exist = self._common_content_lib.execute_sut_cmd("ls " + disk, "Executing ls on {} to check if the "
                                                                                "device exist".format(disk),
                                                                  self.execute_timeout)
            if not (disk == disk_exist.strip()):
                raise content_exceptions.TestFail("NVME disk is not being detected, Please check again")
            self._log.info("NVME {} Device is detected in the SUT".format(disk_exist.strip()))

            self._log.info("Executing fdisk command on {}".format(disk))
            self._common_content_lib.execute_sut_cmd(self.FDISK_CMD + " " + disk, self.FDISK_CMD + " " + disk,
                                                     self.execute_timeout)
            self._log.info("Executing mkfs command on {}".format(disk))
            self._common_content_lib.execute_sut_cmd(self.MKFS_CMD + " " + disk, self.MKFS_CMD + " " + disk,
                                                     self.execute_timeout)
        self._log.info("Disks have been formatted successfully!")

    def execute(self):
        """
        This method does the below
        1. Enables all the VMD bios knobs as per the pcie/U.2 ports.
        2. Creates the RAID0/RAID1/RAID5/RAID10
        4. Verify RAID0/RAID1/RAID5/RAID10

        :return: None
        """

        self._test_content_logger.start_step_logger(1)
        self._log.info("Enabling the VMD BIOS Knobs")
        self.enable_vmd_bios_knobs()
        self._test_content_logger.end_step_logger(1, True)

        for raid_level_int, raid_level in zip(self.raid_levels_int,self.raid_levels):
            self.sup_nvme_disk_list = self._raid_util.get_supported_nvme_drive_list(raid_level=raid_level,
                                                                                    nvme_drive_list=self.nvme_disk_list)
            nvme_devices_str = ' '.join(map(str,self.sup_nvme_disk_list))
            # creating raid volume
            self._test_content_logger.start_step_logger(2)
            create_raid = self.os.execute(self.CMD_CREATE_RAID.format(raid_level_int,raid_level_int,len(self.sup_nvme_disk_list),nvme_devices_str),
                self.execute_timeout)
            self._log.debug("creating RAID level {} : {}".format(raid_level, create_raid.stderr))
            self._test_content_logger.end_step_logger(2, True)
            self._test_content_logger.start_step_logger(3)

            md_stat_res = self._storage_provider.get_booted_raid_disk()
            if md_stat_res.upper() not in raid_level.upper():
                raise content_exceptions.TestFail("{} creation failed ".format(raid_level))
            self._test_content_logger.end_step_logger(3, True)

            self._test_content_logger.start_step_logger(4)

            md_dev = self._common_content_lib.execute_sut_cmd("lsblk ", "Executing lsblk to check md device present ",
                                                              self.execute_timeout)
            md_dev_res = re.findall(self.REGEX_MD_LEVEL, md_dev)
            if md_dev_res:
                md_dev_res = list(set(md_dev_res))[0]
                self._log.info("executing command {} to delete raid ".format(self.CMD_DELETE_RAID.format(md_dev_res)))
                delete_raid = self.os.execute(self.CMD_DELETE_RAID.format(md_dev_res),self.execute_timeout)
                self._log.debug("RAID deleted {}".format(delete_raid.stderr))
            self._test_content_logger.end_step_logger(4, True)

        return True

    def cleanup(self, return_status):
        """
        This Method is used to clear the created RAID0 Volume
        """
        self.bios_util.load_bios_defaults()
        self.perform_graceful_g3()
        super(U2NvmeRAIDinVMDenable, self).cleanup(return_status)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if U2NvmeRAIDinVMDenable.main() else Framework.TEST_RESULT_FAIL)

