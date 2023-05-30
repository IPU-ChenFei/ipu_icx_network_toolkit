#!/usr/bin/env python
##########################################################################
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
##########################################################################

import sys
import os

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.test_content_logger import TestContentLogger
from src.lib.fio_utils import FIOCommonLib
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral
from src.provider.storage_provider import StorageProvider
from src.lib import content_exceptions
from src.storage.test.storage_common import StorageCommon


class StabilityAndStressUsingFioInVmdDisableMode(ContentBaseTestCase):
    """
    Pheonix ID: ["16013961309", "NVME_Stability_and_stress_using_FIO_in_VMD_disable_mode"]
    """
    TEST_CASE_ID = ["16013961309", "NVME-Stability and stress using FIO in VMD disable mode"]
    MNT_POINT = "/mnt/nvme{}"
    name_ssd = None
    FIO_LOG_FILE = "fio_{}.log"
    FIO_RUN_TYPE = ["read", "write", "randread", "randwrite"]
    STEP_DATA_DICT = {
                        1: {'step_details': 'Verify disks connected and booted disk Install FIO in RHEL OS',
                            'expected_results': 'All the disk mentioned in Disk Inventory to be detected and '
                                                'system to be booted from M.2 Sata SSD FIO to be '
                                                'installed successfully'},
                        2: {'step_details': 'Make the system for mounting the FIO',
                            'expected_results': 'Mount point creation to be successful'},
                        3: {'step_details': 'Execute FIO commands and copy logs to local and verify if the bandwidth '
                                            'is as expected ',
                            'expected_results': 'Execution of FIO commands to be successful and logs to be '
                                                'verified successfully.'}
                    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new StabilityAndStressUsingFioInVmdDisableMode object
        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(StabilityAndStressUsingFioInVmdDisableMode, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._fio_common_lib = FIOCommonLib(test_log, self.os)
        self.storage_provider = StorageProvider.factory(test_log, self.os, cfg_opts, "os")
        self._install_collateral = InstallCollateral(test_log, self.os, cfg_opts)
        self._storage_common = StorageCommon(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        1. Installing FIO
        :return: None
        """
        self._test_content_logger.start_step_logger(1)
        self._storage_common.verify_disks_in_sut_and_host()
        lsblk_res = self.storage_provider.get_booted_device()
        device_info = self.storage_provider.get_device_type(lsblk_res, self.name_ssd)
        nvme_m2_drive = self._common_content_configuration.get_sata_m2_drive_name()
        nvme_m2_drive = nvme_m2_drive.split(" ")[2]
        if "SATA" not in device_info["usb_type"].upper() and nvme_m2_drive not in device_info["serial"]:
            raise content_exceptions.TestFail("OS not Booted from on the SATA SSD, please try again..")
        self._log.info("SUT booted from M.2 SATA SSD")
        super(StabilityAndStressUsingFioInVmdDisableMode, self).prepare()
        self._install_collateral.install_fio(install_fio_package=False)
        self._test_content_logger.end_step_logger(1, True)

    def execute(self):
        """
        1. Check if the load average Value is close to zero
        2. Execute FIO Command and Injecting the Pcie Correctable Error and validating the error log
        3. Copying FIO logs to local
        4. Checking and clearing SEL logs
        :return result: True if error detected else False
        """
        final_result = []
        self._test_content_logger.start_step_logger(2)
        fio_mounting = self._common_content_configuration.get_nvme_disks()
        if not fio_mounting:
            raise content_exceptions.TestFail("NVME Device Not Connected")
        self._log.info('Creating Mount Point for fio')
        self._storage_common.get_mounted_storage_disks(fio_mounting)
        self._test_content_logger.end_step_logger(2, True)
        device = 0
        for fio_type in self.FIO_RUN_TYPE:
            self._test_content_logger.start_step_logger(3)
            self._log.info("Executing {} FIO command".format(fio_type))
            if fio_type == "read":
                self._fio_common_lib.run_fio_cmd(name=fio_type, rw=fio_type, numjobs=2, bs="8k",
                                                 filename=fio_mounting[device], size="4G",ioengine="posixaio",
                                                 runtime=20, iodepth=2, output=self.FIO_LOG_FILE.format(fio_type))
            elif fio_type == "write":
                self._fio_common_lib.run_fio_cmd(name="write", rw=fio_type, numjobs=2, bs="8k",
                                                 filename=fio_mounting[device], size="4G", ioengine="posixaio",
                                                 runtime=20, iodepth=2, output=self.FIO_LOG_FILE.format(fio_type))
            elif fio_type == "randread":
                self._fio_common_lib.run_fio_cmd(name=self.FIO_RUN_TYPE[0], rw=fio_type, numjobs=100, bs="8k",
                                                 filename=fio_mounting[device], size="16G", ioengine="posixaio",
                                                 runtime=20, iodepth=1, output=self.FIO_LOG_FILE.format("read"))
            elif fio_type == "randwrite":
                self._fio_common_lib.run_fio_cmd(name="write", rw=fio_type, numjobs=500, bs="64k",
                                                 filename=fio_mounting[device], size="8G", ioengine="posixaio",
                                                 runtime=20, iodepth=1, output=self.FIO_LOG_FILE.format(fio_type))
            self._log.info("Copying {} FIO log file to local".format(fio_type))
            self.os.copy_file_from_sut_to_local(self.FIO_LOG_FILE.format(fio_type), os.path.join(
                self.log_dir, self.FIO_LOG_FILE.format(fio_type)))
            final_result.append(self._fio_common_lib.verify_fio_log_pattern(log_path=os.path.join(
                self.log_dir, self.FIO_LOG_FILE.format(fio_type)), pattern="read:|write:"))
            self._log.info("Copying {} FIO log file to local was successful".format(fio_type))
            self._log.info("FIO Command execution has completed successfully and been Verified Bandwidth!")
            device += 1
            self._test_content_logger.end_step_logger(3, True)
        return all(final_result)

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(StabilityAndStressUsingFioInVmdDisableMode, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StabilityAndStressUsingFioInVmdDisableMode.main()
             else Framework.TEST_RESULT_FAIL)
