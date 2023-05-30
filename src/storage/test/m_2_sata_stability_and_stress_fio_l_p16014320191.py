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
import os
import sys
import re

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.fio_utils import FIOCommonLib
from src.lib.test_content_logger import TestContentLogger
from src.lib.install_collateral import InstallCollateral
from src.provider.storage_provider import StorageProvider
from src.storage.test.storage_common import StorageCommon
from src.lib import content_exceptions


class M2SATAStabilityAndStressFIO(StorageCommon):
    """
    Phoenix ID : 16014320191 - M_2_SATA_Stability_and_Stress_FIO
    This test case functionality is to install, execute fio tool on m.2 sata ssd and verify bandwidth
    """
    TEST_CASE_ID = ["16014320191", "M_2_SATA_Stability_and_Stress_FIO"]
    READ_WRITE_OPERATION = "read_write_operation"
    FIO_RUN_TIME = "fio_runtime"
    FILE_NAMES = "file_name"
    FIO_TYPE = "randrw"
    FIO_LOG_FILE = "fio_randrw.log"
    step_data_dict = {1: {'step_details': 'Install and execute fio tool for required time',
                          'expected_results': 'Successfully installed and executed fio tool'},
                      2: {'step_details': 'Copy log file and Verify bandwidth',
                          'expected_results': 'Successfully verified bandwidth'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new M2SATAStabilityAndStressFIO object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(M2SATAStabilityAndStressFIO, self).__init__(test_log, arguments, cfg_opts)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self.storage_provider = StorageProvider.factory(test_log, self.os, cfg_opts, "os")
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self._fio_common_lib = FIOCommonLib(test_log, self.os)
        self.name_ssd = None

    def prepare(self):
        # type: () -> None
        """
        :return None
        """
        super(M2SATAStabilityAndStressFIO, self).prepare()

    def execute(self):
        """
        This method functionality is to install, execute fio tool on m2 sata ssd and verify bandwidth

        :return: True
        :raise: If installation failed raise content_exceptions.TestFail
        """

        # Step logger Start for Step 1
        self._test_content_logger.start_step_logger(1)

        # Installing FIO Tool
        self._install_collateral.install_fio(install_fio_package=False)
        # Get user inputs from content configuration
        fio_values = self._common_content_configuration.get_fio_tool_values()
        self._log.info("fio tool values from the config :{}".format(fio_values))

        self._fio_common_lib.run_fio_cmd(name="m.2stress", rw=self.FIO_TYPE, numjobs=15, bs="64k",
                                         filename=fio_values[self.FILE_NAMES], size="8G", ioengine="posixaio",
                                         runtime=fio_values[self.FIO_RUN_TIME], iodepth=2, output=self.FIO_LOG_FILE)

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, True)

        # Step logger Start for Step 2
        self._test_content_logger.start_step_logger(2)

        self._log.info("Copying FIO log file to local...")
        self.os.copy_file_from_sut_to_local(self.FIO_LOG_FILE, os.path.join(
            self.log_dir, self.FIO_LOG_FILE))
        result = self._fio_common_lib.verify_fio_log_pattern(log_path=os.path.join(
            self.log_dir, self.FIO_LOG_FILE), pattern="read:|write:")
        self._log.info("Copying {} FIO log file to local was successful".format(self.FIO_TYPE))

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, True)

        return result

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""

        super(M2SATAStabilityAndStressFIO, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if M2SATAStabilityAndStressFIO.main() else Framework.TEST_RESULT_FAIL)
