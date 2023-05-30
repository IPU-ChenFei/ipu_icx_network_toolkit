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


class StorageOSInstallSataM2DeviceL(ContentBaseTestCase):
    """
    Phoenix ID : P18014074439-PI_Storage_SATA_AHCI_OS_Install_to_mSATA_SSD_device_L

    Validation check of SATA drive link speeds in an ESB2 or ICH or PCH based design.
    This method is defined to validate that the SATA Gen2/Gen3 drive is linking at 3Gbs/6Gbs on each physical SATA port.
    Passive mid-plane and backplane designs routed to the PCH/ICH/ESB2 SATA ports should be validated
    using this procedure.
    """
    BIOS_CONFIG_FILE_NAME = "pi_storage_os_install_to_m2_ssd_device.cfg"
    TEST_CASE_ID = ["P18014074439", "PI_Storage_SATA_AHCI_OS_Install_to_mSATA_SSD_device_L"]
    step_data_dict = {1: {'step_details': 'Set the bios knob SATA Mode Selection to AHCI',
                          'expected_results': 'bios setting is done'},
                      2: {'step_details': 'start linux OS installation in sata M.2',
                          'expected_results': 'linux OS installed successfully in sata M.2'},
                      3: {'step_details': 'Verify the bios knob SATA Mode Selection to AHCI',
                          'expected_results': 'Verified the bios knob SATA Mode Selection to AHCI'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new StorageOSInstallSataM2DeviceL object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """

        self._log = test_log
        self._cfg_opts = cfg_opts
        super(StorageOSInstallSataM2DeviceL, self).__init__(test_log, arguments, cfg_opts)
        self._storage_provider = StorageProvider.factory(self._log, self.os, self._cfg_opts, "os")
        cur_path = os.path.dirname(os.path.realpath(__file__))
        self._bios_config_file_path = os.path.join(cur_path, self.BIOS_CONFIG_FILE_NAME)
        self._os_installation_lib = OsInstallation(test_log, cfg_opts)
        self.log_dir = self._common_content_lib.get_log_file_dir()
        self._storage_common = StorageCommon(test_log, arguments, self._cfg_opts)
        self._sata_ssd_name = None

        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        This method is to do the below tasks
        1. Verifying the sata m.2 is connected in the SUT
        2. Setting the bios knob SATA Mode Selection to AHCI

        :return None
        """
        self._log.info("Closing the Serial Port")
        self.cng_log.__exit__(None, None, None)

        # Getting the Device from sut inventory file for installation
        sut_inv_file_path = self._os_installation_lib.get_sut_inventory_file_path()
        with open(sut_inv_file_path, "r") as fh:
            for line in fh.readlines():
                if SutInventoryConstants.SATA_SSD_NAME_RHEL in line:
                    self._sata_ssd_name = line
                    break

        if not self._sata_ssd_name:
            raise content_exceptions.TestError("Unable to find sata ssd name, please check the file under "
                                               "{}".format(sut_inv_file_path))
        self._sata_ssd_name = self._sata_ssd_name.split("=")[1]
        self._log.info("SSD Name from config file : {}".format(self._sata_ssd_name))
        self._common_content_lib.update_sut_inventory_file(SutInventoryConstants.SATA, SutInventoryConstants.RHEL)

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        self.bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self.bios_util.set_bios_knob(bios_config_file=self._bios_config_file_path)  # To set the bios knob setting.

        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This method is used to install the RHEL OS in sata M.2
        """
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        ret_val = list()

        ret_val.append(self._os_installation_lib.rhel_os_installation())

        self._log.info("linux OS installed successfully ...")

        # Verifying if os installed in SATA or not
        self.log_dir = self._common_content_lib.get_log_file_dir()
        lsblk_res = self._storage_provider.get_booted_device()
        self._log.info("booted device is {}".format(str(lsblk_res)))

        device_info = self._storage_provider.get_device_type(lsblk_res, self._sata_ssd_name)

        if not device_info["usb_type"]:
            raise content_exceptions.TestFail("Unable to fetch the SATA device type..")

        if not device_info["serial"]:
            raise content_exceptions.TestFail("Unable to fetch the serial number information of the device..")

        if "SATA" not in device_info["usb_type"].upper():
            raise content_exceptions.TestFail("OS not installed on the SATA SSD, please try again..")

        self._log.info("Successfully verified that OS installed in SATA device..")

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=ret_val)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        self.bios_util.verify_bios_knob(bios_config_file=self._bios_config_file_path)  # To verify the bios knob settings

        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)

        return all(ret_val)

    def cleanup(self, return_status):
        """Test Cleanup"""
        self._common_content_lib.store_os_logs(self.log_dir)
        super(StorageOSInstallSataM2DeviceL, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StorageOSInstallSataM2DeviceL.main() else Framework.TEST_RESULT_FAIL)
