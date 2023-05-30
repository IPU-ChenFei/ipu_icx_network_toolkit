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


class StorageRaid0NVMeVROCL(StorageCommon):
    """
    HPQC ID : H80250_PI_Storage_VROC_NVMe_RAID0_L

    This Class Creates RAID0 and installs RHEL os in it.
    """
    TEST_CASE_ID = ["H80250", "PI_Storage_VROC_NVMe_RAID0_L"]
    BIOS_CONFIG_FILE = "c_state_bios_knobs.cfg"

    STEP_DATA_DICT = {
        1: {'step_details':'Enable the VMD BIOS knobs and do reset',
            'expected_results': 'All the knobs to be enabled and system to be reset successfully'},
        2: {'step_details':'Create RAID0 volume',
            'expected_results': 'RAID0 volume to be created successfully'},
        3: {'step_details':'Start OS installation on the Created RAID0 Volume',
            'expected_results': 'OS to be installed successfully'},
        4: {'step_details': 'Verify if the system is booted from the RAID0 successfully',
            'expected_results':'System should boot from the installed RAID0 Volume'}
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new StorageRaidVMDL object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(StorageRaid0NVMeVROCL, self).__init__(test_log, arguments, cfg_opts)
        self._c_state_bios = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                                          self.BIOS_CONFIG_FILE)
        self.storage_provider = StorageProvider.factory(self._log, self.os, cfg_opts, "os")
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._serial_bios_util = SerialBiosUtil(self.ac_power, test_log, self._common_content_lib, cfg_opts)
        self._raid_util = NvmeRaidUtil(self._log, self._common_content_lib, self._common_content_configuration,
                                       self.bios_util, self._serial_bios_util, self.ac_power)
        self._os_installation_lib = OsInstallation(test_log, cfg_opts)
        self._cfg_opts = cfg_opts

    def prepare(self):
        # type: () -> None
        """
        This is Method is used to get the Non RAID SSD name to boot into OS.
        :return None
        """
        sut_inv_file_path = self._os_installation_lib.get_sut_inventory_file_path()
        with open(sut_inv_file_path, "r") as fh:
            for line in fh.readlines():
                if "non_raid_ssd_name" in line:
                    self.non_raid_disk_name = line
                    break

        if not self.non_raid_disk_name:
            raise content_exceptions.TestError("Unable to find non RAID SSD name, please check the file under "
                                               "{}".format(sut_inv_file_path))

        self.non_raid_disk_name = self.non_raid_disk_name.split("=")[1]
        self._log.info("non RAID SSD Name from config file : {}".format(self.non_raid_disk_name))
        self._common_content_lib.update_sut_inventory_file(SutInventoryConstants.NVME, SutInventoryConstants.RHEL)

        try:
            self.bios_util.set_bios_knob(bios_config_file=self._c_state_bios)
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)
            self.bios_util.verify_bios_knob(bios_config_file=self._c_state_bios)
        except Exception as ex:
            raise content_exceptions.TestFail("Failed to ste the BIOS knobs ", ex)

    def execute(self):
        """
        This method does the below
        1. Enables all the VMD bios knobs as per the pcie ports.
        2. Creates the RAID0
        3. Install Linux OS in the Created RAID0
        4. Verify if the system is booted from RAID0

        :return: None
        """
        self._test_content_logger.start_step_logger(1)
        self._log.info("Enabling the VMD BIOS Knobs")
        self.enable_vmd_bios_knobs()
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        self._log.info("Creating RAID 0")
        self._raid_util.create_raid(RaidConstants.RAID0)
        self._log.info("Waiting for SUT to boot to OS")
        self.os.wait_for_os(self.reboot_timeout)
        self._log.info("Closing the Serial Port")
        self.cng_log.serial.close()
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        self._os_installation_lib.rhel_os_installation()
        self._test_content_logger.end_step_logger(3, True)

        self._test_content_logger.start_step_logger(4)
        md_stat_res = self._storage_provider.get_booted_raid_disk()
        self._log.debug("booted device is {}".format(str(md_stat_res)))
        if md_stat_res.upper() not in RaidConstants.RAID0.split("(")[0]:
            raise content_exceptions.TestFail("OS not installed on the RAID, please try again..")
        self._log.info("Successfully verified that OS installed in {} device..".format(md_stat_res.upper()))
        self._log.info("Reopening the Serial Port to delete the created the RAID0")
        try:
            self._serial_bios_util = SerialBiosUtil(self.ac_power, self._log, self._common_content_lib, self._cfg_opts)
            self._raid_util = NvmeRaidUtil(self._log, self._common_content_lib, self._common_content_configuration,
                                           self.bios_util, self._serial_bios_util, self.ac_power)
        except Exception as ex:
            self._log.debug("Exception occurred while creating serial_bios_util but we can ignore it:{}".format(ex))
        self._raid_util.delete_raid(RaidConstants.RAID0, self.non_raid_disk_name)
        self.os.wait_for_os(self.reboot_timeout)
        self._common_content_lib.store_os_logs(self.log_dir)
        self._test_content_logger.end_step_logger(4, True)
        return True

    def cleanup(self, return_status):
        """
        This Method is used to clear the created RAID0 Volume
        """
        self.bios_util.load_bios_defaults()
        self.perform_graceful_g3()
        super(StorageRaid0NVMeVROCL, self).cleanup(return_status)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StorageRaid0NVMeVROCL.main() else Framework.TEST_RESULT_FAIL)

