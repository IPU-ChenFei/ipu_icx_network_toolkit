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

from src.lib.test_content_logger import TestContentLogger
from src.storage.test.storage_common import StorageCommon
from src.provider.storage_provider import StorageProvider
from src.lib import content_exceptions


class StorageRaidVMDL(StorageCommon):
    """
    HPQC ID : H80241_PI_Storage_RAID_VMD_L

    This Class Creates RAID0, RAID1 using command line then stops then RAID.
    """
    TEST_CASE_ID = ["H80241", "PI_Storage_RAID_VMD_L"]
    BIOS_CONFIG_FILE = "c_state_bios_knobs.cfg"
    CLEAR_METADATA = r'mdadm --zero-superblock /dev/nvme[0-1]n1'
    CREATE_RAID_METADATA = r'mdadm -C /dev/md/imsm0 -amd -e imsm -n 2 {} {} -R'
    CREATE_RAID_VOLUME = r'mdadm -C /dev/md/{} -amd -l{}  -n 2 {} {} -R -f'
    VERIFY_RAID = 'mdadm -D /dev/md/{}'
    STOP_RAID = "mdadm -Ss"
    VERIFY_RAID_STOPPED = "cat /proc/mdstat"
    RAID_TYPE = '{}'
    RAID_LEVEL = '{}'

    STEP_DATA_DICT = {
        1: {'step_details': 'Format both the PCIE NVME card',
            'expected_results': 'Both the PCIE NVME cards to be formatted successfully'},
        2: {'step_details':'Enable the VMD BIOS knobs and do warm reset',
            'expected_results': 'All the knobs to be enabled and system to do warm reset successfully'},
        3: {'step_details':'check if the NVME devices are showing in the OS',
            'expected_results': 'NVME device to shown in the system'},
        4: {'step_details':'Create a container and volume and verify if RAID0 volume is created properly',
            'expected_results': 'RAID0 volume to be created and verified'},
        5: {'step_details': 'stop the RAID0 and clear the metadata',
            'expected_results':'stop the RAIDO and Metadata container to be cleared'},
        6: {'step_details': 'Create a container and volume and verify if RAID1 volume is created properly',
            'expected_results': 'RAID1 volume to be created and verified'},
        7: {'step_details': 'Stop the RAID1 and clear the metadata',
            'expected_results': 'Stop the RAID1 and Metadata container to be cleared'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new StorageRaidVMDL object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(StorageRaidVMDL, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)
        self.storage_provider = StorageProvider.factory(self._log, self.os, cfg_opts, "os")
        self.nvme_disk_list = self._common_content_configuration.get_nvme_disks()
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    def prepare(self):
        # type: () -> None
        """
        This method is used to format the disk to mkfs.ext2
        :return None
        """
        self._test_content_logger.start_step_logger(1)
        for disk in self.nvme_disk_list:
            self._log.info("Executing fdisk command on {}".format(disk))
            self._common_content_lib.execute_sut_cmd(self.FDISK_CMD + " " + disk, self.FDISK_CMD + " " + disk,
                                                     self.execute_timeout)
            self._log.info("Executing mkfs command on {}".format(disk))
            self._common_content_lib.execute_sut_cmd(self.MKFS_CMD + " " + disk, self.MKFS_CMD + " " + disk,
                                                     self.execute_timeout)
        self._log.info("Disks have been formatted successfully!")
        self._test_content_logger.end_step_logger(1, True)
        super(StorageRaidVMDL, self).prepare()

    def execute(self):
        """
        This method does the below
        1. Enables all the VMD bios knobs as per the pcie ports.
        2. Creates the Container, and RAID0 and stops it and clear the metadata for RAID0
        3. Creates the Container, and RAID1 and stops it and clear the metadata for RAID1

        :return: None
        """
        self._test_content_logger.start_step_logger(2)
        self._log.info("Enabling the VMD BIOS Knobs")
        self.enable_vmd_bios_knobs()
        self._test_content_logger.end_step_logger(2, True)
        self._test_content_logger.start_step_logger(3)
        for disk in self.nvme_disk_list:  # loop to check if the devices exist on the SUT
            disk_exist = self._common_content_lib.execute_sut_cmd("ls " + disk, "Executing ls on {} to check if the "
                                                            "device exist".format(disk), self.execute_timeout)
            if not (disk == disk_exist.strip()):
                raise content_exceptions.TestFail("NVME disk is not being detected, Please check again")
            self._log.info("NVME {} Device is detected in the SUT".format(disk_exist.strip()))
        self._test_content_logger.end_step_logger(3, True)
        self._test_content_logger.start_step_logger(4)
        # creating raid container metadata using mdadm command
        self._log.info("Creating Metadata Container for Raid 0")
        metadata_output = self.os.execute(self.CREATE_RAID_METADATA.format(
            self.nvme_disk_list[0], self.nvme_disk_list[1]), self.execute_timeout)
        # using stderr due to command output is not being printed in the log
        self._log.debug("Metadata Container for RAID 0 {}".format(metadata_output.stderr))
        self._log.info("Creating RAID 0 Volume")
        # creating raid volume
        create_raid = self.os.execute(self.CREATE_RAID_VOLUME.format(self.RAID_TYPE.format("r0"),
                                                                     self.RAID_LEVEL.format("0"), self.nvme_disk_list[0],
                                                                     self.nvme_disk_list[1]), self.execute_timeout)
        self._log.debug("Raid0 Creation {}".format(create_raid.stderr))
        self._log.info("Verifying if RAID 0 is created")
        # verify if raid was created
        raid_vol = self._common_content_lib.execute_sut_cmd(self.VERIFY_RAID.format("r0"),
                                                 "Verify if Raid was created successfully", self.execute_timeout)
        self._log.debug("Total raid Volume {}".format(raid_vol))
        self._test_content_logger.end_step_logger(4, True)
        self._test_content_logger.start_step_logger(5)
        self._log.info("Stopping RAID0")
        # Stop the raid
        self._common_content_lib.execute_sut_cmd(self.STOP_RAID, self.STOP_RAID, self.execute_timeout)
        # verify if raid has been stopped
        stop_raid = self._common_content_lib.execute_sut_cmd(self.VERIFY_RAID_STOPPED,
                                                 "Verify if raid has been stopped", self.execute_timeout)
        self._log.debug("Volume after stopping RAID0 {}".format(stop_raid))
        self._log.info("Clearing the Metadata")
        # clear the metadata
        self._common_content_lib.execute_sut_cmd(self.CLEAR_METADATA, self.CLEAR_METADATA, self.execute_timeout)
        self._test_content_logger.end_step_logger(5, True)
        self._test_content_logger.start_step_logger(6)
        # creating raid container metadata using mdadm command
        self._log.info("Creating Metadata Container for Raid 1")
        metadata_output = self.os.execute(self.CREATE_RAID_METADATA.format(
            self.nvme_disk_list[0], self.nvme_disk_list[1]), self.execute_timeout)
        # using stderr due to command output is not being printed in the log
        self._log.debug("Metadata Container for RAID 1 {}".format(metadata_output.stderr))
        self._log.info("Creating RAID 1 Volume")
        # creating raid volume
        create_raid = self.os.execute(self.CREATE_RAID_VOLUME.format(self.RAID_TYPE.format("r1"),
                                                                     self.RAID_LEVEL.format("1"),
                                                                     self.nvme_disk_list[0],
                                                                     self.nvme_disk_list[1]), self.execute_timeout)
        # using stderr due to command output is not being printed in the log
        self._log.debug("Raid Creation output is {}".format(create_raid.stderr))
        self._log.info("Verifying if RAID 1 is created")
        # verify if raid was created
        raid_vol = self._common_content_lib.execute_sut_cmd(self.VERIFY_RAID.format("r1"),
                                                            "Verify if Raid was created successfully",
                                                            self.execute_timeout)
        self._log.debug("Total Raid Volume is {}".format(raid_vol))
        self._test_content_logger.end_step_logger(6, True)
        self._test_content_logger.start_step_logger(7)
        # Stop the raid
        self._log.info("Stopping the RAID")
        self._common_content_lib.execute_sut_cmd(self.STOP_RAID, self.STOP_RAID, self.execute_timeout)
        # verify if raid has been stopped
        stop_raid = self._common_content_lib.execute_sut_cmd(self.VERIFY_RAID_STOPPED,
                                                 "Verify if raid has been stopped", self.execute_timeout)
        self._log.debug("Volume after STOP Raid Command is {}".format(stop_raid))
        self._log.info("Clearing the Metadata")
        # clear the metadata
        self._common_content_lib.execute_sut_cmd(self.CLEAR_METADATA, self.CLEAR_METADATA, self.execute_timeout)
        self._test_content_logger.end_step_logger(7, True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StorageRaidVMDL.main() else Framework.TEST_RESULT_FAIL)
