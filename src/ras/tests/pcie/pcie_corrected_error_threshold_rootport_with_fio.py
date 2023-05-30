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


from dtaf_core.lib.dtaf_constants import Framework
from src.lib.fio_utils import FIOCommonLib
from src.lib.dtaf_content_constants import TimeConstants
from src.provider.storage_provider import StorageProvider
from src.lib.install_collateral import InstallCollateral
from src.ras.tests.pcie.pcie_corrected_error_threshold_rootport import PcieCorrectedErrorThresholdRootPort
from src.lib import content_exceptions
from sys import exit
from time import time
from os import path


class PcieCorrectedErrorThresholdRootPortFio(PcieCorrectedErrorThresholdRootPort):
    """
    Phoenix_ID: ["14013813441", "PCIe Correctable Error Thresholding - NVMe Workloads - FIO Test - Linux OS : cscripts"]

    This TestCase Injects PCIe correctable errors above set threshold in BIOS and checks error is reported to the OS
    with FIO traffic running.
    """
    TEST_CASE_ID = ["14013813441", "PCIe_Correctable_Error_Thresholding_FIO_Test_-_Linux_OS_:_cscripts"]

    def __init__(self, test_log, arguments, cfg_opts):
        super(PcieCorrectedErrorThresholdRootPortFio, self).__init__(test_log, arguments, cfg_opts)
        self._fio_common_lib = FIOCommonLib(self._log, self._os)
        self.storage_provider = StorageProvider.factory(test_log, self._os, cfg_opts, "os")
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        :return: None
        """
        super(PcieCorrectedErrorThresholdRootPortFio, self).prepare()
        self._install_collateral.install_fio(install_fio_package=False)
        self._log.info('Creating Mount Point for fio')
        fio_mounting = self._common_content_configuration.get_nvme_partition_to_mount()
        if not fio_mounting:
            raise content_exceptions.TestFail("NVME Device Not Connected")
        self._log.info('Mounting NVMe drive')
        self.storage_provider.mount_the_drive(fio_mounting, self._fio_common_lib.FIO_MOUNT_POINT)

    def execute(self):
        """
        This test case provides the validation plan and recipe for error reporting enhancement where corrected
        error reporting within the PCI Express module can be configured to only signal once a predetermined
        threshold is reached with FIO traffic running.

        :return: True if passed else False
        :raise: None
        """

        t_end = time() + TimeConstants.TEN_MIN_IN_SEC

        self._log.info('Execute the fio command to run NVMe traffic')
        self._fio_common_lib.fio_execute_async(self._fio_common_lib.TOOL_NAME)

        while time() < t_end:
            self._log.info('Run PCIe corrected error threshold rootport test')
            super(PcieCorrectedErrorThresholdRootPortFio, self).execute()

        self._log.info("Copying FIO log file to local")
        self.os.copy_file_from_sut_to_local(self._fio_common_lib.LOG_FILE,
                                            path.join(self.log_dir, self._fio_common_lib.FIO_LOG_FILE))
        self._log.info("Checking fio log file")
        self._fio_common_lib.fio_log_parsing(log_path=path.join(self.log_dir, self._fio_common_lib.FIO_LOG_FILE),
                                             pattern="READ:|WRITE:")

        return True


if __name__ == "__main__":
    exit(Framework.TEST_RESULT_PASS if PcieCorrectedErrorThresholdRootPortFio.main()
         else Framework.TEST_RESULT_FAIL)
