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
from src.lib.fio_utils import FIOCommonLib
from src.lib.dtaf_content_constants import TimeConstants
from src.lib import content_exceptions
from src.provider.storage_provider import StorageProvider
from src.lib.install_collateral import InstallCollateral


from src.ras.tests.pcie.pei_card.test.pcie_hw_leaky_bucket_basetest import PcieHWLeakyBucketBaseTest
from time import sleep
from os import path


class PcieHWLeakyBucketFio(PcieHWLeakyBucketBaseTest):
    """
    Phoenix_id : 22012710108

    The objective of this test is to enable verification of Leaky Bucket flow while FIO workload is running.

     Requirements:

     1. BIOS config file path configured in system_configuration.xml
     2. Socket of PEI 4.0 card configured in content_configuration.xml
     3. pxp port of PEI 4.0 card configured in content_configuration.xml
     4. NVMe drive connected to PEI 4.0 card

     Usage:

     Error type injection is controlled by the "test" parameter in the execute() method and is set to "badDLLP" by default
     To execute the test for bad TLP, set test="badTLP"

    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new PcieHWLeakyBucketFio object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PcieHWLeakyBucketFio, self).__init__(test_log, arguments, cfg_opts)
        self._fio_common_lib = FIOCommonLib(self._log, self._os)
        self.storage_provider = StorageProvider.factory(test_log, self._os, cfg_opts, "os")
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        :return: None
        """
        super(PcieHWLeakyBucketFio, self).prepare()
        self._install_collateral.install_fio(install_fio_package=False)
        self._log.info("Configure the PEI card in interposer mode")
        self.hw_injector.set_mode(self.pei_image_type.INTERPOSER)
        self.perform_graceful_g3()
        self._log.info("Creating Mount Point for fio")
        fio_mounting = self._common_content_configuration.get_nvme_partition_to_mount()
        if not fio_mounting:
            raise content_exceptions.TestFail("NVMe Device Not Connected, make sure an NVMe device is connected to the "
                                              "PEI card and the PEI card has the interposer image loaded")
        self._log.info("Mounting NVMe drive")
        self.storage_provider.mount_the_drive(fio_mounting, self._fio_common_lib.FIO_MOUNT_POINT)

    def execute(self, err_type="badDLLP", expect_link_degrade=True):
        """
        This method checks the OS log for errors given a supported error type

        param: string err_type - one of the supported error types (i.e.: "badDLLP", "badTLP")
        return: True
        raise: TestFail
        """
        self._log.info("Execute the fio command to run NVMe traffic")
        self._fio_common_lib.fio_execute_async(self._fio_common_lib.TOOL_NAME)

        self._log.info("Run the Leaky Bucket Base Test")
        super(PcieHWLeakyBucketFio, self).execute(err_type, expect_link_degrade)

        self._log.info("Waiting for fio to finish")
        sleep(TimeConstants.TEN_MIN_IN_SEC)

        self._log.info("Copying FIO log file to local")
        self.os.copy_file_from_sut_to_local(self._fio_common_lib.LOG_FILE,
                                            path.join(self.log_dir, self._fio_common_lib.FIO_LOG_FILE))
        self._log.info("Checking fio log file")
        self._fio_common_lib.fio_log_parsing(log_path=path.join(self.log_dir, self._fio_common_lib.FIO_LOG_FILE),
                                             pattern="READ:|WRITE:")

        return True

    def cleanup(self, return_status):
        super(PcieHWLeakyBucketFio, self).cleanup(return_status)
        self._log.info("Configure the PEI card in endpoint mode")
        self.hw_injector.set_mode(self.pei_image_type.ENDPOINT)
        self.perform_graceful_g3()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieHWLeakyBucketFio.main() else Framework.TEST_RESULT_FAIL)
