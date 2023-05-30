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

from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.dtaf_content_constants import SutInventoryConstants

from src.environment.os_installation import OsInstallation
from src.provider.storage_provider import StorageProvider
from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.storage.test.storage_common import StorageCommon


class StorageOSInstallNvmeM2DeviceL(ContentBaseTestCase):
    """
    HPALM ID : H97917-PI_Storage_OS_Install_to_M.2_SSD_device_L

    Install Linux OS on nvme m.2
    """
    BIOS_CONFIG_FILE_NAME = "pi_storage_os_install_to_m2_ssd_device.cfg"
    TEST_CASE_ID = ["H97917", "PI_Storage_OS_Install_to_M.2_SSD_device_L"]
    step_data_dict = {1: {'step_details': 'Verify nvme M.2 is connected in the SUT',
                          'expected_results': 'Successfully verified nvme M.2 is connected in the SUT'},
                      2: {'step_details': 'Set the bios knob SATA Mode Selection to AHCI',
                          'expected_results': 'bios setting is done'},
                      3: {'step_details': 'start linux OS installation in nvme M.2',
                          'expected_results': 'linux OS installed successfully in nvme M.2'},
                      4: {'step_details': 'Verify the bios knob SATA Mode Selection to AHCI',
                          'expected_results': 'Verified the bios knob SATA Mode Selection to AHCI'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new StorageOSInstallNvmeM2DeviceL object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """

        self._log = test_log
        self._cfg_opts = cfg_opts
        super(StorageOSInstallNvmeM2DeviceL, self).__init__(test_log, arguments, cfg_opts)
        self._storage_provider = StorageProvider.factory(self._log, self.os, self._cfg_opts, "os")
        cur_path = os.path.dirname(os.path.realpath(__file__))
        self._bios_config_file_path = os.path.join(cur_path, self.BIOS_CONFIG_FILE_NAME)
        self._os_installation_lib = OsInstallation(test_log, cfg_opts)
        self.log_dir = self._common_content_lib.get_log_file_dir()
        self._storage_common = StorageCommon(test_log, arguments, self._cfg_opts)
        self._nvme_ssd_name = None

        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        This method is to do the below tasks
        1. Verifying the nvme m.2 is connected in the SUT
        2. Setting the bios knob SATA Mode Selection to AHCI

        :return None
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        # Verifying whether the nvme M.2 is connected to the SUT
        self._log.info("Getting the nvme M.2 from the config file")
        nvme_m2_drive = self._common_content_configuration.get_nvme_m2_drive_name()
        self._log.info("Verifying the nvme M.2 \'{}\' in EDKII Menu".format(nvme_m2_drive))
        self._storage_common.verify_device_in_edkii_menu(nvme_m2_drive)
        self._log.info("Closing the Serial Port")
        self.cng_log.__exit__(None, None, None)

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

        # Getting the Device from sut inventory file for installation
        sut_inv_file_path = self._os_installation_lib.get_sut_inventory_file_path()
        with open(sut_inv_file_path, "r") as fh:
            for line in fh.readlines():
                if SutInventoryConstants.NVME_SSD_NAME_RHEL in line:
                    self._nvme_ssd_name = line
                    break

        if not self._nvme_ssd_name:
            raise content_exceptions.TestError("Unable to find nvme ssd name, please check the file under "
                                               "{}".format(sut_inv_file_path))
        self._nvme_ssd_name = self._nvme_ssd_name.split("=")[1]
        self._log.info("SSD Name from config file : {}".format(self._nvme_ssd_name))
        self._common_content_lib.update_sut_inventory_file(SutInventoryConstants.NVME, SutInventoryConstants.RHEL)

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        self.bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self.bios_util.set_bios_knob(bios_config_file=self._bios_config_file_path)  # To set the bios knob setting.

        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

    def execute(self):
        """
        This method is used to install the RHEL OS in nvme M.2
        """
        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)
        ret_val = list()

        ret_val.append(self._os_installation_lib.rhel_os_installation())

        self._log.info("linux OS installed successfully ...")

        # Verifying if os installed in NVME or not
        self.log_dir = self._common_content_lib.get_log_file_dir()
        lsblk_res = self._storage_provider.get_booted_device()
        self._log.info("booted device is {}".format(str(lsblk_res)))

        if "NVME" not in lsblk_res.upper():
            raise content_exceptions.TestFail("OS not installed on the NVME SSD, please try again..")

        self._log.info("Successfully verified that OS installed in NVME device..")

        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=ret_val)

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)

        self.bios_util.verify_bios_knob(bios_config_file=self._bios_config_file_path)  # To verify the bios knob settings

        # Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=True)

        return ret_val

    def cleanup(self, return_status):
        """Test Cleanup"""
        self._common_content_lib.store_os_logs(self.log_dir)
        super(StorageOSInstallNvmeM2DeviceL, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StorageOSInstallNvmeM2DeviceL.main() else Framework.TEST_RESULT_FAIL)
