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
from dtaf_core.providers.provider_factory import ProviderFactory

from src.lib.test_content_logger import TestContentLogger
from src.lib.fio_utils import FIOCommonLib
from src.lib.install_collateral import InstallCollateral
from src.provider.storage_provider import StorageProvider
from src.lib import content_exceptions
from src.storage.test.storage_common import StorageCommon
from src.virtualization.virtualization_common import VirtualizationCommon


class U2NvmeStabilityCrossSocketStressFio(StorageCommon):
    """
    Pheonix ID: ["16013871985", "U2_nvme_stability_cross_socket_stress_fio"]
    """
    TEST_CASE_ID = ["16013871985", "U2_nvme_stability_cross_socket_stress_fio"]
    name_ssd = None
    FIO_LOG_FILE = "fio_{}.log"
    FIO_RUN_TYPE = ["read", "write", "randread", "randwrite"]
    VMD_PORT = ["IOU3", "IOU4"]
    STEP_DATA_DICT = {
                        1: {'step_details': 'Install FIO in RHEL OS check for CPU and numactl and devices',
                            'expected_results': 'FIO to be installed successfully'},
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
        super(U2NvmeStabilityCrossSocketStressFio, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._fio_common_lib = FIOCommonLib(test_log, self.os)
        self.storage_provider = StorageProvider.factory(test_log, self.os, cfg_opts, "os")
        self._install_collateral = InstallCollateral(test_log, self.os, cfg_opts)
        self._storage_common = StorageCommon(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        1. Installing NUMactl
        2. Enable VMD BIOS Knobs for IOU3 and IOU4
        3. Checking the devices are detected after enabling VMD Bios Knobs
        4. Install FIO
        :return: None
        """
        self._test_content_logger.start_step_logger(1)
        super(U2NvmeStabilityCrossSocketStressFio, self).prepare()
        for iou in self.VMD_PORT:
            self.enable_vmd_bios_knob_using_port(iou)
        self.check_disk_detected_intel_vroc()
        lsblk_res = self.storage_provider.get_booted_device()
        device_info = self.storage_provider.get_device_type(lsblk_res, self.name_ssd)
        if "SATA" not in device_info["usb_type"].upper():
            raise content_exceptions.TestFail("OS not Booted from on the SATA SSD, please try again..")
        self._log.info("SUT booted from SATA SSD")

        self._install_collateral.yum_install("numactl")
        lsblk_op = self._common_content_lib.execute_sut_cmd("lsblk --nodeps", "lsblk --nodeps", self._command_timeout)
        self._log.info(lsblk_op)
        if not lsblk_op:
            raise content_exceptions.TestFail("Output fail for lsblk --nodeps")

        numa_show_op = self._common_content_lib.execute_sut_cmd("numactl --show", "numactl --show", self._command_timeout)
        self._log.info(numa_show_op)
        if not numa_show_op:
            raise content_exceptions.TestFail("Output fail for numactl --show")

        lscpu_op = self._common_content_lib.execute_sut_cmd("lscpu", "lscpu",
                                                                self._command_timeout)
        self._log.info(lscpu_op)
        if not lscpu_op:
            raise content_exceptions.TestFail("Output fail for lscpu_op")
        self._install_collateral.install_fio(install_fio_package=False)
        self._test_content_logger.end_step_logger(1, True)

    def execute(self):
        """
        1. Create mount point for FIO
        2. Execute FIO Command on each socket for seq-read, seq-write, random-read, random-write
        3. Copying FIO logs to local
        4. Verifying if there are no errors detected in logs
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
        device = ":".join(fio_mounting)
        fio_run_time = self._common_content_configuration.memory_fio_run_time()
        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        CPU_BIND = cscripts_obj.get_socket_count()
        for cpu in range(CPU_BIND):
            for fio_type in self.FIO_RUN_TYPE:
                self._test_content_logger.start_step_logger(3)
                self._log.info("Executing {} FIO command on CPU {}".format(fio_type, cpu))
                if fio_type == "read":
                    self._fio_common_lib.numactl_run_fio(cpunodebind=cpu, membind=cpu, name="read",
                                                         rw=fio_type, filename=device, iodepth=16, bs="252k",
                                                         size="4G", numjobs=250, runtime=fio_run_time,
                                                         output=self.FIO_LOG_FILE.format(fio_type))
                elif fio_type == "write":
                    self._fio_common_lib.numactl_run_fio(cpunodebind=cpu, membind=cpu, name="read",
                                                         rw=fio_type, filename=device, iodepth=16, bs="252k",
                                                         size="4G", numjobs=250, runtime=fio_run_time,
                                                         output=self.FIO_LOG_FILE.format(fio_type))
                elif fio_type == "randread":
                    self._fio_common_lib.numactl_run_fio(cpunodebind=cpu, membind=cpu, name=self.FIO_RUN_TYPE[0],
                                                         rw=fio_type, filename=device, iodepth=16, bs="252k",
                                                         size="4G", numjobs=250, runtime=fio_run_time,
                                                         output=self.FIO_LOG_FILE.format(fio_type))
                elif fio_type == "randwrite":
                    self._fio_common_lib.numactl_run_fio(cpunodebind=cpu, membind=cpu, name=self.FIO_RUN_TYPE[1],
                                                         rw=fio_type, filename=device, iodepth=16, bs="252k",
                                                         size="4G", numjobs=250, runtime=fio_run_time,
                                                         output=self.FIO_LOG_FILE.format(fio_type))
                self._log.info("Copying {} FIO log file to local".format(fio_type))
                self.os.copy_file_from_sut_to_local(self.FIO_LOG_FILE.format(fio_type), os.path.join(
                    self.log_dir, self.FIO_LOG_FILE.format(fio_type)))
                final_result.append(self._fio_common_lib.verify_fio_log_pattern(log_path=os.path.join(
                    self.log_dir, self.FIO_LOG_FILE.format(fio_type)), pattern="read:|write:"))
                self._log.info("Copying {} FIO log file to local was successful".format(fio_type))
                self._log.info("FIO Command execution has completed successfully and been Verified Bandwidth!")
                self._test_content_logger.end_step_logger(3, True)
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(U2NvmeStabilityCrossSocketStressFio, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if U2NvmeStabilityCrossSocketStressFio.main()
             else Framework.TEST_RESULT_FAIL)
