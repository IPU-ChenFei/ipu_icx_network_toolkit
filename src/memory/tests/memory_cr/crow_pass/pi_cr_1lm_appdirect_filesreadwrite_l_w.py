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

import pickle
import sys
import os
import six

if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.memory.tests.memory_cr.crow_pass.pi_cr_1lm_appdirect_basicflow_l_w \
    import PiCR1LMAppDirectBasicFlow
from src.lib.test_content_logger import TestContentLogger
from src.provider.partition_provider import PartitionProvider
from src.provider.ipmctl_provider import IpmctlProvider
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib import content_exceptions
from src.memory.lib.memory_common_lib import MemoryCommonLib


class PiCR1LMAppDirectFilesReadWrite(ContentBaseTestCase):
    """
    HP QC  ID: H101105-PI_CR_1LM_AppDirect_FilesReadWrite_L and H101150-PI_CR_1LM_AppDirect_FilesReadWrite_W

    Basic read/write functionality is working normally on CR DIMMs.
    """

    TEST_CASE_ID = ["H101105", "PI_CR_1LM_AppDirect_FilesReadWrite_L",
                    "H101150", "PI_CR_1LM_AppDirect_FilesReadWrite_W"]
    return_value = []
    NUMBER_OF_TIMES_COPY = 5
    ROOT = "/root"
    C_DRIVE_PATH = "C:\\"
    step_data_dict = {1: {'step_details': 'To provision the crystal ridge with 1LM 100% AppDirect mode',
                          'expected_results': 'Successfully provisioned crystal ridge with 1LM 100% AppDirect mode '},
                      2: {'step_details': 'Copying the 5GB TEST file from local HDD to the CR BLK disk and then '
                                          'copy the file from CR BLK disk to local HDD for 5 times',
                          'expected_results': 'No hang/reboot/crash during files copy'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiCR1LMAppDirectFilesReadWrite object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: RuntimeError
        """
        # calling base class init
        super(PiCR1LMAppDirectFilesReadWrite, self).__init__(test_log, arguments, cfg_opts)

        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

        self._partition_provider = PartitionProvider.factory(test_log, cfg_opts=cfg_opts, os_obj=self.os)
        self._ipmctl_provider = IpmctlProvider.factory(test_log, self.os, execution_env="os", cfg_opts=cfg_opts)
        self._memory_common_lib = MemoryCommonLib(test_log, cfg_opts, self.os)
        self.pmem_list = []
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        # Provisioning 1LM App Direct mode
        self._cr_provisioning_100app_direct = PiCR1LMAppDirectBasicFlow(test_log, arguments, cfg_opts)
        self._cr_provisioning_100app_direct.prepare()
        provisioning_result = self._cr_provisioning_100app_direct.execute()

        if provisioning_result:
            self._log.info("Provisioning of DCPMM with 1 LM 100% app direct has been done successfully ...")
        else:
            err_log = "Provisioning of DCPMM with 1 LM 100% app direct mode failed!"
            self._log.error(err_log)
            raise RuntimeError(err_log)

        with open(self._partition_provider.DRIVE_LETTERS_FILE, "rb") as fp:
            self.pmem_list = pickle.load(fp)

        if self.pmem_list:
            self._log.info("List of pmem drive letters: {}".format(self.pmem_list))
        else:
            raise content_exceptions.TestFail("We did not get pmem drive letters ...")

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=self.pmem_list)

    def prepare(self):
        # type: () -> None
        """
        :return: None
        """
        pass

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. To copy 5 GB file from local Hard disk to CR disk.
        2. To copy 5 GB file from CR disk to local Hard disk.

        :return: True, if the test case is successful.
        :raise: RuntimeError : if the SUT is not alive.
        """

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        # To generate 5GB file in the SUT
        self._memory_common_lib.generate_5gb_test_file()

        for count in range(0, self.NUMBER_OF_TIMES_COPY):
            self._log.info("copying 5GB test file from hard disk to pmem drive, count is {}".format(count + 1))

            # To copy file from hard disk to pmem drive
            self._memory_common_lib.copy_test_file_from_hard_disk_to_pmem_drive(self.pmem_list)
            if not self.os.is_alive():
                raise RuntimeError("SUT is not responding while copying 5GB test file from hard disk "
                                   "to pmem drive, count is {}".format(count))

            self._log.info("copying 5GB test file from pmem drive to hard disk, count is {}".format(count + 1))

            # To copy file from pmem drive to Hard disk
            self._memory_common_lib.copy_test_file_from_pmem_drive_to_hard_disk(self.pmem_list)
            if not self.os.is_alive():
                raise RuntimeError("SUT is not responding while copying 5GB test file from pmem drive to hard disk, "
                                   "count is {}".format(count))

        # To delete TEST FILE in hard disk
        if OperatingSystems.LINUX in self.os.os_type:
            self._common_content_lib.execute_sut_cmd("rm -rf {}".format(self._memory_common_lib.TEST_FILE_NAME),
                                                     "To delete file from hard disk", self._command_timeout, self.ROOT)

        elif OperatingSystems.WINDOWS in self.os.os_type:
            self._common_content_lib.execute_sut_cmd("DEL /Q {}".format(self._memory_common_lib.TEST_FILE_NAME),
                                                     "To delete file from hard disk", self._command_timeout,
                                                     self.C_DRIVE_PATH)
            cmd_to_check_file = self._memory_common_lib.PS_CMD_TO_CHECK_FILE_EXISTS_OR_NOT.\
                format(self._memory_common_lib.TEST_FILE_NAME)
            # To verify file is deleted or not
            file_exists = self._common_content_lib.execute_sut_cmd(
                cmd_to_check_file, "To check whether file exists or not", self._command_timeout, self.C_DRIVE_PATH)
            if 'True' in file_exists:
                self._log.info("Error: {} not deleted".format(self._memory_common_lib.TEST_FILE_NAME))
            else:
                self._log.info("Successfully deleted the file {} from hard disk.".format(self._memory_common_lib.
                                                                                         TEST_FILE_NAME))

        # To delete the TEST FILE in pmem disk
        for each_data in self.pmem_list:
            if OperatingSystems.LINUX in self.os.os_type:
                destination_test_file_path = Path(os.path.join(each_data, self._memory_common_lib.TEST_FILE_NAME))\
                    .as_posix()

                self._common_content_lib.execute_sut_cmd("rm -rf {}".format(destination_test_file_path),
                                                         "To delete file from the persistent memory disk",
                                                         self._command_timeout)

            elif OperatingSystems.WINDOWS in self.os.os_type:
                destination_test_file_path = os.path.join(each_data+":\\", self._memory_common_lib.TEST_FILE_NAME)
                self._common_content_lib.execute_sut_cmd("DEL /Q {}".format(destination_test_file_path),
                                                         "To delete file from the persistent memory disk",
                                                         self._command_timeout, self.C_DRIVE_PATH)
                cmd_to_check_file = self._memory_common_lib.PS_CMD_TO_CHECK_FILE_EXISTS_OR_NOT. \
                    format(destination_test_file_path)
                # To verify file is deleted or not
                file_exists = self._common_content_lib.execute_sut_cmd(
                    cmd_to_check_file, "To check whether file exists or not", self._command_timeout, self.C_DRIVE_PATH)
                if 'True' in file_exists:
                    self._log.info("Error: {} not deleted from {}".format(
                        self._memory_common_lib.TEST_FILE_NAME, destination_test_file_path))
                else:
                    self._log.info("Successfully deleted the file {} from {}".format(
                        self._memory_common_lib.TEST_FILE_NAME, destination_test_file_path))
        if os.path.exists(self._partition_provider.DRIVE_LETTERS_FILE):
            os.remove(self._partition_provider.DRIVE_LETTERS_FILE)

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""

        self._ipmctl_provider.delete_pmem_device()

        super(PiCR1LMAppDirectFilesReadWrite, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiCR1LMAppDirectFilesReadWrite.main() else Framework.TEST_RESULT_FAIL)
