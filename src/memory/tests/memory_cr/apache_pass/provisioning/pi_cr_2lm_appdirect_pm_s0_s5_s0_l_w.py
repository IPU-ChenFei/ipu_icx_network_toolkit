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
import six
import pickle

if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path
from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.power_management.lib.reset_base_test import ResetBaseTest
from src.lib.test_content_logger import TestContentLogger
from src.memory.tests.memory_cr.apache_pass.provisioning.cr_provisioning_common import CrProvisioningTestCommon
from src.memory.tests.memory_cr.apache_pass.provisioning.pi_cr_2lm_appdirect_basicflow \
    import PiCR2lmAppdirectBasicFlow
from src.provider.partition_provider import PartitionProvider
from src.memory.lib.memory_common_lib import MemoryCommonLib


class PICR2lmAppDirectPMS0S5S0(CrProvisioningTestCommon):
    """
    HP QC  ID: 79531 (Linux) / H82166 (Windows)

    To check system power sequence with 2LM CR: so->s5->s0
    """

    TEST_CASE_ID = "H79531/H82166-PiCR2lmAppDirectPMS0S5S0"

    step_data_dict = {1: {'step_details': 'To provision the crystal ridge with 2LM 50% AppDirect mode and '
                                          '50% Memory mode',
                          'expected_results': 'Successfully provisioned crystal ridge with LM 50% AppDirect mode and '
                                          '50% Memory mode '},
                      2: {'step_details': 'To generate a 5GB test file in SUT',
                          'expected_results': '5GB test file generated in the SUT'},
                      3: {'step_details': 'Copying the 5GB TEST file from local HDD to the CR BLK disk and '
                                          'calculate the checksum by using md5sum command',
                          'expected_results': 'Calculated the checksum'},
                      4: {'step_details': 'shutdown and power ON the SUT',
                          'expected_results': 'The SUT has to boot to OS'},
                      5: {'step_details': 'Calculate the checksum 5GB TEST file after reboot by using md5sum command',
                          'expected_results': 'Calculated checksum before reboot and after reboot are same'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PICR2lmAppDirectPMS0S5S0 object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """

        #  Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        # Provisioning 2LM 50% App Direct and 50% memory mode
        self._cr_provisioning_50appdirect_50memory = PiCR2lmAppdirectBasicFlow(test_log, arguments, cfg_opts)
        self._cr_provisioning_50appdirect_50memory.prepare()
        self._provisioning_result = self._cr_provisioning_50appdirect_50memory.execute()

        # calling base class init
        super(PICR2lmAppDirectPMS0S5S0, self).__init__(test_log, arguments, cfg_opts, bios_config_file=None)

        if self._provisioning_result:
            self._log.info("Provisioning of DCPMM with 50% app direct and 50% memory mode has been done successfully!")
        else:
            err_log = "Provisioning of DCPMM with 50% app direct and 50% memory mode mode failed!"
            self._log.error(err_log)
            raise RuntimeError(err_log)

        if OperatingSystems.LINUX == self._os.os_type:
            self.pmem_list = self._cr_provisioning_50appdirect_50memory.mount_list
        elif OperatingSystems.WINDOWS == self._os.os_type:
            with open(PartitionProvider.DRIVE_LETTERS_FILE, "rb") as fp:
                self.pmem_list = pickle.load(fp)
            self._log.info("List of pmem drive letters:\n{}".format(self.pmem_list))
        else:
            raise NotImplementedError("Not supported for OS {}".format(self._os.os_type))
        self._s5_object = ResetBaseTest(test_log, arguments, cfg_opts)

        #  Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=self._provisioning_result)

    def prepare(self):
        # type: () -> None
        """
        To generate a 5GB test file

        :return: None
        """
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        ret_value = self._memory_common_lib.generate_5gb_test_file()

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=ret_value)

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. To copy 5 GB file from local Hard disk to CR disk.
        2. Calculate the checksum value using md5sum before S5 (shutdown).
        3. Shutdown the SUT.
        4. Calculate the checksum value using md5sum after S5 (Shutdown).
        5. Compare the checksum's

        :return: True, if the test case is successful.
        :raise: None
        """
        checksum_list_values_before_s5 = list()
        checksum_list_values_after_s5 = list()
        return_value = True
        test_file_path = ""
        drive_separator = ":\\"

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        self._log.info("copying 5GB test file from hard disk to pmem drive")

        self._memory_common_lib.copy_test_file_from_hard_disk_to_pmem_drive(self.pmem_list)

        for each_data in self.pmem_list:
            if OperatingSystems.LINUX == self._os.os_type:
                test_file_path = Path(os.path.join(each_data, MemoryCommonLib.TEST_FILE_NAME)).as_posix()
            elif OperatingSystems.WINDOWS == self._os.os_type:
                test_file_path = os.path.join(each_data + drive_separator, MemoryCommonLib.TEST_FILE_NAME)

            checksum_list_values_before_s5.append(self._memory_common_lib.calculate_checksum(test_file_path))

        self._log.info("checksum values before S5 are : {}".format(checksum_list_values_before_s5))

        #  Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=checksum_list_values_before_s5)

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)

        # To reboot the SUT.
        self._s5_object.graceful_s5()

        # Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=True)

        # Step logger start for Step 5
        self._test_content_logger.start_step_logger(5)

        # To get the checksum values after the S5
        for each_data in self.pmem_list:
            if OperatingSystems.LINUX == self._os.os_type:
                test_file_path = Path(os.path.join(each_data, MemoryCommonLib.TEST_FILE_NAME)).as_posix()
            elif OperatingSystems.WINDOWS == self._os.os_type:
                test_file_path = os.path.join(each_data + drive_separator, MemoryCommonLib.TEST_FILE_NAME)

            checksum_list_values_after_s5.append(self._memory_common_lib.calculate_checksum(test_file_path))

        self._log.info("checksum values are after S5 : {}".format(checksum_list_values_before_s5))

        # compare checksum values before S5 and after S5
        if checksum_list_values_before_s5 != checksum_list_values_after_s5:
            self._log.info("checksum values before S5 and after S5 are not same")
            return_value = False

        self._log.info("checksum values before S5 and after S5 are same")

        # To delete TEST FILE in hard disk and pmem disk
        self._memory_common_lib.delete_file(MemoryCommonLib.TEST_FILE_NAME)

        # To delete the TEST FILE in pmem disk
        for each_data in self.pmem_list:
            if OperatingSystems.LINUX in self._os.os_type:
                test_file_path = Path(os.path.join(each_data, MemoryCommonLib.TEST_FILE_NAME)).as_posix()
            elif OperatingSystems.WINDOWS in self._os.os_type:
                test_file_path = os.path.join(each_data + drive_separator, MemoryCommonLib.TEST_FILE_NAME)
            self._memory_common_lib.delete_file(test_file_path)

        if os.path.exists(PartitionProvider.DRIVE_LETTERS_FILE):
            os.remove(PartitionProvider.DRIVE_LETTERS_FILE)

        # Step logger end for Step 5
        self._test_content_logger.end_step_logger(5, return_val=return_value)

        return return_value

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PICR2lmAppDirectPMS0S5S0, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PICR2lmAppDirectPMS0S5S0.main() else Framework.TEST_RESULT_FAIL)
