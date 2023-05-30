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
import re
import sys

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.test_content_logger import TestContentLogger
from src.storage.test.storage_common import StorageCommon
from src.provider.storage_provider import StorageProvider
from src.lib import content_exceptions


class StorageRaidVMDWitOsCommand(StorageCommon):
    """
    Phoenix ID : P16013565615 - HHHL - VMD RAID Volume Management with OS commands (0,1,5,10) in rhel
                 P16013544492 - NVME-HHHL- VMD RAID Volume Management with OS commands (0,1,5,10) in Centos

    Create raid(0,1,5,10) from OS level on the pcie ssd on rhel or Centos OS.
    """
    TEST_CASE_ID = ["P16013565615", "HHHL - VMD RAID Volume Management with OS commands (0,1,5,10) in rhel",
                    "P16013544492", "NVME-HHHL- VMD RAID Volume Management with OS commands (0,1,5,10) in Centos"]
    DELETE_RAID = "mdadm -S /dev/{}"
    STOP_RAID = "mdadm -Ss"
    VERIFY_RAID_CMD = "cat /proc/mdstat"
    FORMAT_DISK_CMD = "yes | mkfs.ext4 {}"
    CHECK_NVME_DEVICE = "ls /dev/nvme*n1"
    RAID_REG = "md\d+.*"
    CREATE_RAID_CMD = "yes | sudo mdadm --create /dev/md0 --level={} --raid-devices={} {}"
    RAID_LEVEL = {"raid0": "stripe", "raid1": "mirror", "raid5": 5, "raid10": 10}
    RAID_DEVICE = {"raid0": 2, "raid1": 2, "raid5": 3, "raid10": 4}

    STEP_DATA_DICT = {
        1: {'step_details': 'Delete existing raid if any from the system',
            'expected_results': 'Existing raid deleted successfully'},
        2: {'step_details': 'Enable the VMD BIOS knobs and do warm reset',
            'expected_results': 'All the knobs to be enabled and system to do warm reset successfully'},
        3: {'step_details': 'Format both the PCIE NVME card',
            'expected_results': 'Both the PCIE NVME cards to be formatted successfully'},
        4: {'step_details': 'Create RAID0, RAID1, RAID5, RAID10 and verify, stop and delete each raid after successful '
                            'creation',
            'expected_results': 'RAID0, RAID1, RAID5, RAID10 created successfully and verified and stopped and '
                                'deleted as well'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new StorageRaidVMDWitOsCommand object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(StorageRaidVMDWitOsCommand, self).__init__(test_log, arguments, cfg_opts)
        self.storage_provider = StorageProvider.factory(self._log, self.os, cfg_opts, "os")
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    def prepare(self):
        # type: () -> None
        """
        This method is used to format the disk to mkfs.ext4
        :return None
        """
        raid_list = []
        self._test_content_logger.start_step_logger(1)
        raid_exist = self._common_content_lib.execute_sut_cmd(self.VERIFY_RAID_CMD, "Verify RAID", self.execute_timeout)
        raid_list = re.findall(self.RAID_REG, raid_exist)
        raid_str_list = list(map(lambda raid: raid.split(":")[0].strip(), raid_list))
        if len(raid_str_list) != 0:
            for raid in raid_str_list:
                self._common_content_lib.execute_sut_cmd(self.DELETE_RAID.format(raid), "Delete RAID",
                                                         self.execute_timeout)
        self._test_content_logger.end_step_logger(1, True)
        super(StorageRaidVMDWitOsCommand, self).prepare()

    def execute(self):
        """
        This method does the below
        1. Enables all the VMD bios knobs as per the pcie ports.
        2. Create RAID0, RAID1, RAID5, RAID10 and verify, stop and delete each raid after successful creation

        :return: None
        """
        self._test_content_logger.start_step_logger(2)
        self._log.info("Enabling the VMD BIOS Knobs")
        self.enable_vmd_bios_knobs()
        self._test_content_logger.end_step_logger(2, True)
        self._test_content_logger.start_step_logger(3)
        nvme_device = self._common_content_lib.execute_sut_cmd(self.CHECK_NVME_DEVICE, self.CHECK_NVME_DEVICE,
                                                               self.execute_timeout)
        nvme_device_list = nvme_device.strip().split("\n")
        if len(nvme_device_list) != 0:
            for disk in nvme_device_list:
                self._log.info("Formatting disk {}".format(disk))
                output = self._common_content_lib.execute_sut_cmd(self.FORMAT_DISK_CMD.format(disk),
                                                                  self.FORMAT_DISK_CMD.format(disk),
                                                                  self.execute_timeout)
                self._log.debug("Disk {} has been formatted :- output {}".format(disk, output))
            self._log.info("PCIe NVMe Disks have been formatted successfully!")
        else:
            raise content_exceptions.TestSetupError("NVME Disk are not connected")
        self._test_content_logger.end_step_logger(3, True)

        self._test_content_logger.start_step_logger(4)
        for raid_type, raid_level in self.RAID_LEVEL.items():
            self._log.info("Creating {}".format(raid_type))
            devices = " ".join(nvme_device_list[0:self.RAID_DEVICE[raid_type]])
            cmd = self.CREATE_RAID_CMD.format(raid_level, self.RAID_DEVICE[raid_type], devices)
            self._log.debug("Executing command {} for raid {} creation".format(cmd, raid_type))
            # Create the raid
            raid_output = self._common_content_lib.execute_sut_cmd(cmd, "Create RAID", self.execute_timeout)
            self._log.debug("{} created and output is {}".format(raid_type, raid_output))
            # Verify the raid
            verify_raid = self._common_content_lib.execute_sut_cmd(self.VERIFY_RAID_CMD, "Verify RAID",
                                                                   self.execute_timeout)

            self._log.debug("Verify raid command output".format(verify_raid))
            raid_list = re.findall(self.RAID_REG, verify_raid)
            if len(raid_list) != 0:
                for raid in raid_list:
                    if raid_type in raid.split(":")[1].strip():
                        self._log.info("{} has been created successfully {}".format(raid_type, verify_raid))
                    else:
                        raise content_exceptions.TestFail("Raid {} creation was unsuccessful".format(raid_type))
                    # Delete the raid
                    self._log.info("Deleting raid {}".format(raid.split(":")[0].strip()))
                    self._common_content_lib.execute_sut_cmd(self.DELETE_RAID.format(raid.split(":")[0].strip()),
                                                             "Delete RAID",
                                                             self.execute_timeout)
                    # verify raid after deletion
                    raid_exist = self._common_content_lib.execute_sut_cmd(self.VERIFY_RAID_CMD, "Verify RAID",
                                                                          self.execute_timeout)
                    raid_list = re.findall(self.RAID_REG, raid_exist)
                    raid_str_list = list(map(lambda raid: raid.split(":")[0].strip(), raid_list))
                    if len(raid_str_list) != 0:
                        for each in raid_str_list:
                            self._common_content_lib.execute_sut_cmd(self.DELETE_RAID.format(each), "Delete RAID",
                                                                     self.execute_timeout)
        self._test_content_logger.end_step_logger(4, True)

        return True

    def cleanup(self, return_status):
        """Test Cleanup"""
        # if raid exists
        raid_exist = self._common_content_lib.execute_sut_cmd(self.VERIFY_RAID_CMD, "Verify RAID",
                                                              self.execute_timeout)
        raid_list = re.findall(self.RAID_REG, raid_exist)
        raid_str_list = list(map(lambda raid: raid.split(":")[0].strip(), raid_list))
        if len(raid_str_list) != 0:
            for each in raid_str_list:
                self._common_content_lib.execute_sut_cmd(self.DELETE_RAID.format(each), "Delete RAID",
                                                         self.execute_timeout)
        nvme_device = self._common_content_lib.execute_sut_cmd(self.CHECK_NVME_DEVICE, self.CHECK_NVME_DEVICE,
                                                               self.execute_timeout)
        nvme_device_list = nvme_device.strip().split("\n")
        if len(nvme_device_list) != 0:
            for disk in nvme_device_list:
                self._log.info("Formatting disk {}".format(disk))
                output = self._common_content_lib.execute_sut_cmd(self.FORMAT_DISK_CMD.format(disk),
                                                                  self.FORMAT_DISK_CMD.format(disk),
                                                                  self.execute_timeout)
                self._log.debug("Disk {} has been formatted :- output {}".format(disk, output))
            self._log.info("PCIe NVMe Disks have been formatted successfully!")

        super(StorageRaidVMDWitOsCommand, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StorageRaidVMDWitOsCommand.main() else Framework.TEST_RESULT_FAIL)
