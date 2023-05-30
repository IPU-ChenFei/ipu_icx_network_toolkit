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

from src.lib import content_exceptions
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.bios_util import SerialBiosUtil
from src.lib.test_content_logger import TestContentLogger
from src.storage.lib.nvme_raid_util import NvmeRaidUtil
from src.environment.os_installation import OsInstallation
from src.provider.storage_provider import StorageProvider
from src.lib.dtaf_content_constants import SutInventoryConstants, RaidConstants
from src.storage.test.storage_common import StorageCommon
from dtaf_core.lib.os_lib import LinuxDistributions


class NVMeOSInstallationRAIDMode(ContentBaseTestCase):
    """
    PHOENIX id : 16013527604 - PCie NVMe-OS installation in RAID Mode(0,1,5,10) -use mix of all Models
                16013549989 - PCieSSD-VMD enable - OS Install to PCie NvMe in VMD enable with raid Mode(0,1,5,10) and NVME driver installation check
                16013592851 - U.2 NVMe-Gen4 OS installation in RAID Mode(0,1,5,10) -use mix of all Models U.2 NVMe
                16013592268 - U.2 NVMe - Gen4 OS installation in RAID Mode(0, 1, 5, 10) - use mix of all Models U.2 NVMe CENTOS
                16013557273 - U.2 NVME -Gen3 OS installation in RAID Mode(0,1,5,10)-use mix of all Models U.2 NVME
                16013611633 - U.2 NVMe-Gen4 OS installation in RAID Mode(0,1,5,10) -use mix of all Models U.2 NVMe

    This class used for create RAID0M, RAID1, RAID5, RAID10
    Install RHEL OS on RAID and delete RAID.
    """

    TEST_CASE_ID = ["16013527604", "PCie NVMe-OS installation in RAID Mode(0,1,5,10) -use mix of all Models CENTOS",
                    "16013549989",
                    "PCieSSD-VMD enable - OS Install to PCie NvMe in VMD enable with raid Mode(0,1,5,10) and NVME driver installation check",
                    "16013592851", "U.2 NVMe-Gen4 OS installation in RAID Mode(0,1,5,10) -use mix of all Models U.2 NVMe",
                    "16013592268", "U.2 NVMe - Gen4 OS installation in RAID Mode(0, 1, 5, 10) - use mix of all Models U.2 NVMe CENTOS"
                    "16013557273", "U2_NVME_Gen3_OS_installation_in_RAID_Mode_0_1_5_10_use_mix_of_all_Models_U2_NVME",
                    "16013611633", "U2_NVMe_Gen4_OS_installation_RAID_Mode_0_1_5_10_all_Models_U2_NVMe"
                    ]
    step_data_dict = {
                        1: {'step_details': 'Enable the VMD knobs according to PCIe slot settings',
                            'expected_results': 'Successfully enabled the VMD knobs'},
                        2: {'step_details': 'create the RAID0/RAID1/RAID5,RAID10 using two NVME Drives',
                            'expected_results': 'RAID0/RAID1/RAID5/RAID10 Creation is successful'},
                        3: {'step_details': 'Install RHEL OS on RAID0/RAID1 and boot to  OS',
                            'expected_results': 'Successfully installed OS in RAID0/RAID1/RAID5/RAID10'},
                        4: {'step_details': 'Verify OS is successfully installed in created RAID0/RAID1/RAID5/RAID10',
                            'expected_results': 'Verified OS installation is successful in RAID0/RAID1/RAID5/RAID10'},
                        5: {'step_details': 'delete RAID0/RAID1/RAID5/RAID10 Volume',
                            'expected_results': 'Successfully deleted RAID0/RAID1/RAID5/RAID10 Volume'}
                      }

    def __init__(self, test_log, arguments, cfg_opts):
        """
         Creates a new NVMeOSInstallationRAIDMode object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        self._log = test_log
        self._cfg_opts = cfg_opts

        self._cc_log_path = arguments.outputpath

        super(NVMeOSInstallationRAIDMode, self).__init__(test_log, arguments, cfg_opts)
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
        1. get the non raid disk name from sut inventory and update the sut inventory file with the target device to
        install rhel os
        2. enabling the vmd knobs according to the PCIe slot connected

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
        self._common_content_lib.update_sut_inventory_file(SutInventoryConstants.NVME, self.os.os_subtype.lower())

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        self._log.info("Enabling the VMD BIOS Knobs as per the pcie slots connected ...")
        self._storage_common.enable_vmd_bios_knobs()

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This function is responsible for below tasks
        1. Creating RAID on connected PCIe/U.2,
        2. Installing RHEL/CentOS OS On RAID device and verify
        3. delete RAID.

        :return: True if RAID creation, OS installation and deletion Successful else False
        """
        # initialize package counter to extract the OS and software package only once and to skip the extraction step for
        # further installations.
        package_extract_counter = 0
        ret_val = []

        self.raid_levels = [RaidConstants.RAID0, RaidConstants.RAID1, RaidConstants.RAID5, RaidConstants.RAID10]

        for raid_level in self.raid_levels:

            # Step logger start for Step 2
            self._test_content_logger.start_step_logger(2)

            raid_creation_screen = self._raid_util.create_raid(raid_level)
            self._log.debug("After RAID creation :".format(raid_creation_screen))
            self.os.wait_for_os(self.reboot_timeout)

            # Step logger end for Step 2
            self._test_content_logger.end_step_logger(2, return_val=True)

            self._log.info("Closing the Serial Port")
            self.cng_log.__exit__(None, None, None)

            # Step logger start for Step 3
            self._test_content_logger.start_step_logger(3)
            self._log.info("\'{}\' OS is going to install on {} Volume".format(self.os.os_subtype,
                                                                                             raid_level))
            if package_extract_counter > 0:
                if self.os.os_subtype.lower() == LinuxDistributions.RHEL.lower():
                    ret_val.append(self._os_installation_lib.rhel_os_installation(os_extract=False, software_extract=False))
                elif self.os.os_subtype.lower() == LinuxDistributions.CentOS.lower():
                    ret_val.append(self._os_installation_lib.centos_os_installation(installation_mode="offline", os_extract=False, software_extract=False))
                else:
                    raise content_exceptions.TestFail(
                        "Unsupported os subtype {} for this test case. Please provide the correct"
                        " os subtype in system_configuration file".format(self.os.os_subtype))
            else:
                if self.os.os_subtype.lower() == LinuxDistributions.RHEL.lower():
                    ret_val.append(self._os_installation_lib.rhel_os_installation())
                elif self.os.os_subtype.lower() == LinuxDistributions.CentOS.lower():
                    ret_val.append(self._os_installation_lib.centos_os_installation())
                else:
                    raise content_exceptions.TestFail(
                        "Unsupported os subtype {} for this test case. Please provide the correct"
                        " os subtype in system_configuration file".format(self.os.os_subtype))
            package_extract_counter += 1

            # Step logger end for Step 3
            self._test_content_logger.end_step_logger(3, True)

            # Step logger start for Step 4
            self._test_content_logger.start_step_logger(4)

            md_stat_res = self._storage_provider.get_booted_raid_disk()
            self._log.debug("booted device is {}".format(str(md_stat_res)))

            if md_stat_res.upper() not in raid_level.upper():
                raise content_exceptions.TestFail("OS not installed on the RAID, please try again..")

            self._log.info("Successfully verified that OS installed in {} device..".format(md_stat_res.upper()))

            # Step logger end for Step 4
            self._test_content_logger.end_step_logger(4, return_val=True)

            self._log.info("Reopening the Serial Port")
            try:
                self._serial_bios_util = SerialBiosUtil(self.ac_power, self._log, self._common_content_lib, self._cfg_opts)
                self._raid_util = NvmeRaidUtil(self._log, self._common_content_lib, self._common_content_configuration,
                                               self.bios_util, self._serial_bios_util, self.ac_power)
            except Exception as ex:
                self._log.debug("Exception occurred while creating serial_bios_util but we can ignore it:{}".format(ex))

            # Step logger start for Step 5
            self._test_content_logger.start_step_logger(5)

            self._raid_util.delete_raid(raid_level, self.non_raid_disk_name)
            self.os.wait_for_os(self.reboot_timeout)

            # Step logger end for Step 5
            self._test_content_logger.end_step_logger(5, return_val=True)

        return True

    def cleanup(self, return_status):
        """Test Cleanup"""
        self._common_content_lib.store_os_logs(self.log_dir)
        self.bios_util.load_bios_defaults()
        self.perform_graceful_g3()
        super(NVMeOSInstallationRAIDMode, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if NVMeOSInstallationRAIDMode.main() else Framework.TEST_RESULT_FAIL)
