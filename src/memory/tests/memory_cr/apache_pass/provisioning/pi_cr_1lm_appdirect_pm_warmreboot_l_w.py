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

from src.lib.test_content_logger import TestContentLogger
from src.memory.tests.memory_cr.apache_pass.provisioning.cr_provisioning_common import CrProvisioningTestCommon
from src.memory.tests.memory_cr.apache_pass.provisioning.pi_cr_1lm_appdirect_basicflow_l_w \
    import PiCR1lmAppdirectBasicFlow
from src.provider.partition_provider import PartitionProvider


class PICR1lmAppDirectPMWarmReboot(CrProvisioningTestCommon):
    """
    HP QC  ID: 79530 (Linux) and 82165 (Windows)

    To check system power sequence with 1LM CR: Warm reboot
    """

    TEST_CASE_ID = "H79530/H82165-Pi_CR_1lm_AppDirect_PM_WarmReboot"

    step_data_dict = {1: {'step_details': 'To provision the crystal ridge with 1LM 100% AppDirect mode',
                          'expected_results': 'Successfully provisioned crystal ridge with 1LM 100% AppDirect mode '},
                      2: {'step_details': 'Copying the 5GB TEST file from local HDD to the CR BLK disk and '
                                          'calculate the checksum by using md5sum command',
                          'expected_results': 'Calculated the checksum'},
                      3: {'step_details': 'Reboot the SUT', 'expected_results': 'The SUT has been rebooted'},
                      4: {'step_details': 'Calculate the checksum 5GB TEST file after reboot by using md5sum command',
                          'expected_results': 'Calculated checksum before reboot and after reboot are same'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PICR1lmAppDirectPMWarmReboot object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """

        #  Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

        self._partition_provider = PartitionProvider.factory(test_log, cfg_opts=cfg_opts, os_obj=self._os)

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        # Provisioning test case
        self._cr_provisioning_100app_direct = PiCR1lmAppdirectBasicFlow(test_log, arguments, cfg_opts)
        self._cr_provisioning_100app_direct.prepare()
        self._provisioning_result = self._cr_provisioning_100app_direct.execute()

        # calling base class init
        super(PICR1lmAppDirectPMWarmReboot, self).__init__(test_log, arguments, cfg_opts, bios_config_file=None)

        if self._provisioning_result:
            self._log.info("Provisioning of DCPMM with 100% app direct has been done successfully!")
        else:
            err_log = "Provisioning of DCPMM with 100% app direct mode failed!"
            self._log.error(err_log)
            raise RuntimeError(err_log)

        if OperatingSystems.LINUX in self._os.os_type:
            self.pmem_list = self._cr_provisioning_100app_direct.mount_list
        elif OperatingSystems.WINDOWS in self._os.os_type:
            with open(self._partition_provider.DRIVE_LETTERS_FILE, "rb") as fp:
                self.pmem_list = pickle.load(fp)
            self._log.info("List of pmem drive letters:\n{}".format(self.pmem_list))

        #  Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=self._provisioning_result)

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
        2. Calculate the checksum value using md5sum before reboot.
        3. Reboot the SUT.
        4. Calculate the checksum value using md5sum after reboot.
        5. Compare the checksum's

        :return: True, if the test case is successful.
        :raise: None
        """
        checksum_list_values_before_reboot = list()
        checksum_list_values_after_reboot = list()
        return_value = True
        test_file_path = ""
        drive_separator = ":\\"

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        # To generate 5GB file in the SUT
        self._memory_common_lib.generate_5gb_test_file()

        self._log.info("copying 5GB test file from hard disk to pmem drive")

        self._install_collateral.copy_test_file_from_hard_disk_to_pmem_drive(self.pmem_list)

        for each_data in self.pmem_list:
            if OperatingSystems.LINUX in self._os.os_type:
                test_file_path = Path(os.path.join(each_data, self._memory_common_lib.TEST_FILE_NAME)).as_posix()
            elif OperatingSystems.WINDOWS in self._os.os_type:
                test_file_path = os.path.join(each_data + drive_separator, self._memory_common_lib.TEST_FILE_NAME)
            checksum_list_values_before_reboot.append(self._memory_common_lib.calculate_checksum(test_file_path))

        self._log.info("checksum values before reboot are : {}".format(checksum_list_values_before_reboot))

        #  Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=checksum_list_values_before_reboot)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        # To reboot the SUT.
        self._common_content_lib.perform_os_reboot(self._reboot_timeout)

        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)

        # To get the checksum values after the reboot
        for each_data in self.pmem_list:
            if OperatingSystems.LINUX in self._os.os_type:
                test_file_path = Path(os.path.join(each_data, self._memory_common_lib.TEST_FILE_NAME)).as_posix()
            elif OperatingSystems.WINDOWS in self._os.os_type:
                test_file_path = os.path.join(each_data + drive_separator, self._memory_common_lib.TEST_FILE_NAME)
            checksum_list_values_after_reboot.append(self._memory_common_lib.calculate_checksum(test_file_path))
        self._log.info("checksum values are after reboot : {}".format(checksum_list_values_before_reboot))

        # compare checksum values before reboot and after reboot
        if checksum_list_values_before_reboot != checksum_list_values_before_reboot:
            self._log.info("check sum values before reboot and after reboot are not same")
            return_value = False

        self._log.info("check sum values before reboot and after reboot are same")

        # To delete TEST FILE in hard disk
        self._memory_common_lib.delete_file(self._memory_common_lib.TEST_FILE_NAME)

        # To delete the TEST FILE in pmem disk
        for each_data in self.pmem_list:
            if OperatingSystems.LINUX in self._os.os_type:
                test_file_path = Path(os.path.join(each_data, self._memory_common_lib.TEST_FILE_NAME)).as_posix()
            elif OperatingSystems.WINDOWS in self._os.os_type:
                test_file_path = os.path.join(each_data + drive_separator, self._memory_common_lib.TEST_FILE_NAME)
            self._memory_common_lib.delete_file(test_file_path)

        if os.path.exists(self._partition_provider.DRIVE_LETTERS_FILE):
            os.remove(self._partition_provider.DRIVE_LETTERS_FILE)

        # Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=return_value)

        return return_value

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(PICR1lmAppDirectPMWarmReboot, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PICR1lmAppDirectPMWarmReboot.main() else Framework.TEST_RESULT_FAIL)
