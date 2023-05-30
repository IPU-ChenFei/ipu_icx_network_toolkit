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

from src.lib import content_exceptions
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.bios_util import SerialBiosUtil
from src.lib.test_content_logger import TestContentLogger
from src.storage.lib.nvme_raid_util import NvmeRaidUtil
from src.environment.os_installation import OsInstallation
from src.provider.storage_provider import StorageProvider
from src.lib.dtaf_content_constants import SutInventoryConstants, RaidConstants
from src.storage.test.storage_common import StorageCommon


class PcieDataRaidInPchCpuSlot(ContentBaseTestCase):
    """
    PHOENIX id : 16013541315 - Pcie ssd - DATA RAID between PCH and CPU SLOT


    This class used for create RAID0
    Install RHEL OS on RAID and delete RAID.
    """
    BIOS_CONFIG_FILE = "verify_system_booting_with_vmd_enable_for_pch_slot_c.cfg"
    TEST_CASE_ID = ["16013541315", "Pcie ssd - DATA RAID between PCH and CPU SLOT"]

    step_data_dict = {
                        1: {'step_details': 'Enable the VMD knobs and Slot-C according to PCIe slot settings',
                            'expected_results': 'Successfully enabled the VMD knobs'},
                        2: {'step_details': 'create the RAID0 using two NVME Drives',
                            'expected_results': 'RAID0 Creation is successful'},
                        3: {'step_details': 'delete RAID0 Volume',
                            'expected_results': 'Successfully deleted RAID0 Volume'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
         Creates a new PcieDataRaidInPchCpuSlot object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        self._log = test_log
        self._cfg_opts = cfg_opts

        self._cc_log_path = arguments.outputpath
        self.bios_config_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                             self.BIOS_CONFIG_FILE)
        super(PcieDataRaidInPchCpuSlot, self).__init__(test_log, arguments, cfg_opts, self.bios_config_file)
        self._serial_bios_util = SerialBiosUtil(self.ac_power, test_log, self._common_content_lib, cfg_opts)
        self._raid_util = NvmeRaidUtil(self._log, self._common_content_lib, self._common_content_configuration,
                                       self.bios_util, self._serial_bios_util, self.ac_power)

        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

        self._os_installation_lib = OsInstallation(test_log, cfg_opts)
        self._storage_provider = StorageProvider.factory(self._log, self.os, self._cfg_opts, "os")
        self._storage_common = StorageCommon(test_log, arguments, cfg_opts)
        self.raid_levels = list()
        self._ac = self.ac_power
        self.non_raid_disk_name = None

    def prepare(self):
        # type: () -> None
        """
        This method is to do the below tasks
        1. get the non raid disk name from sut inventory and update the sut inventory file
        2. enabling the vmd knobs according to the PCIe slot connected and slot-c also

        :return None
        """
        super(PcieDataRaidInPchCpuSlot, self).prepare()
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

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        self._storage_common.enable_vmd_bios_knobs()
        # Enable Slot-C knob
        self._storage_common.enable_slot_c_knob()
        self._log.info("Enabling the VMD BIOS Knobs as per the pcie slots connected ...")

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This function is responsible for below tasks
        1. Creating RAID on connected PCIe Nvme
        2. delete RAID.

        :return: True if RAID creation else False
        """

        self.raid_levels = [RaidConstants.RAID0]

        for raid_level in self.raid_levels:

            # Step logger start for Step 2
            self._test_content_logger.start_step_logger(2)

            raid_creation_screen = self._raid_util.create_raid(raid_level)
            self._log.debug("After RAID creation :".format(raid_creation_screen))
            self.os.wait_for_os(self.reboot_timeout)

            # Step logger end for Step 2
            self._test_content_logger.end_step_logger(2, return_val=True)

            # Step logger start for Step 3
            self._test_content_logger.start_step_logger(3)

            self._raid_util.delete_raid(raid_level, self.non_raid_disk_name)
            self.os.wait_for_os(self.reboot_timeout)

            # Step logger end for Step 3
            self._test_content_logger.end_step_logger(3, return_val=True)

        return True

    def cleanup(self, return_status):
        """Test Cleanup"""
        self._common_content_lib.store_os_logs(self.log_dir)
        self.bios_util.load_bios_defaults()
        self.perform_graceful_g3()
        super(PcieDataRaidInPchCpuSlot, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieDataRaidInPchCpuSlot.main() else Framework.TEST_RESULT_FAIL)
