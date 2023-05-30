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
from src.memory.tests.memory_cr.crow_pass.pi_cr_2lm_appdirect_basicflow_l_w \
    import PiCR2LMAppDirectBasicFlow
from src.provider.partition_provider import PartitionProvider
from src.provider.ipmctl_provider import IpmctlProvider
from src.power_management.lib.reset_base_test import ResetBaseTest
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral
from src.memory.lib.memory_common_lib import MemoryCommonLib


class PiCR2LMAppDirectPMColdReboot(ContentBaseTestCase):
    """
    HP QC  ID: 101125-PI_CR_2LM_AppDirect_PM_ColdReboot_L and H101170-PI_CR_2LM_AppDirect_PM_ColdReboot_W

    To check system power sequence with 2LM CR: Cold reboot
    """
    TEST_CASE_ID = ["H101125", "PI_CR_2LM_AppDirect_PM_ColdReboot_L",
                    "H101170", "PI_CR_2LM_AppDirect_PM_ColdReboot_W"]

    step_data_dict = {1: {'step_details': 'To provision the crystal ridge with 2LM 50% AppDirect and 50% memory mode',
                          'expected_results': 'Successfully provisioned CR with 2LM 50% AppDirect and 50% memory mode'},
                      2: {'step_details': 'Copying the 5GB TEST file from local HDD to the CR BLK disk and '
                                          'calculate the checksum.',
                          'expected_results': 'Calculated the checksum'},
                      3: {'step_details': 'cold Reboot the SUT', 'expected_results': 'The SUT rebooted and came to OS'},
                      4: {'step_details': 'Calculate the checksum 5GB TEST file after reboot.',
                          'expected_results': 'Calculated checksum before cold reboot and after cold reboot are same'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiCR2LMAppDirectPMColdReboot object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: RuntimeError
        """
        # calling base class init
        super(PiCR2LMAppDirectPMColdReboot, self).__init__(test_log, arguments, cfg_opts)

        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

        self._partition_provider = PartitionProvider.factory(test_log, cfg_opts=cfg_opts, os_obj=self.os)
        self._ipmctl_provider = IpmctlProvider.factory(test_log, self.os, execution_env="os", cfg_opts=cfg_opts)
        self._memory_common_lib = MemoryCommonLib(test_log, cfg_opts, self.os)
        self.base_reboot = ResetBaseTest(self._log, arguments, cfg_opts=cfg_opts)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self.num_of_cycle = self._common_content_configuration.get_cr_2lm_power_cycle(
            self._memory_common_lib.POWER_CYCLE_STR[self._memory_common_lib.COLD_REBOOT])

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        # Provisioning test case
        self._cr_provisioning_mixed_mode = PiCR2LMAppDirectBasicFlow(test_log, arguments, cfg_opts)

        self._cr_provisioning_mixed_mode.prepare()
        self._provisioning_result = self._cr_provisioning_mixed_mode.execute()

        if self._provisioning_result:
            self._log.info("Provisioning of DCPMM with 2LM Mixed has been done successfully!")
        else:
            err_log = "Provisioning of DCPMM with 2LM Mixed mode failed!"
            self._log.error(err_log)
            raise RuntimeError(err_log)

        with open(self._partition_provider.DRIVE_LETTERS_FILE, "rb") as fp:
            self.pmem_list = pickle.load(fp)

        if self.pmem_list:
            self._log.info("List of pmem drive letters:\n{}".format(self.pmem_list))
        else:
            error_log = "Did not get the pmem drive letters :\n".format(self.pmem_list)
            raise RuntimeError(error_log)

        # Step logger end for Step 1
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
        3. Install IOPort tool in SUT for Linux, cold Reboot the SUT.
        4. Calculate the checksum value using md5sum for linux and certutil for windows after cold reboot.
        5. Compare the checksum's before cold reboot and after cold reboot.

        :return: True, if the test case is successful.
        :raise: None
        """
        return_value = True
        test_file_path = ""
        drive_separator = ":\\"
        for cycle in range(self.num_of_cycle):
            checksum_list_values_before_reboot = list()
            checksum_list_values_after_reboot = list()
            # Step logger start for Step 2
            self._test_content_logger.start_step_logger(2)

            # To generate 5GB file in the SUT
            self._memory_common_lib.generate_5gb_test_file()

            self._log.info("copying 5GB test file from hard disk to pmem drive")

            self._memory_common_lib.copy_test_file_from_hard_disk_to_pmem_drive(self.pmem_list)

            for each_data in self.pmem_list:
                if OperatingSystems.LINUX in self.os.os_type:
                    test_file_path = Path(os.path.join(each_data, self._memory_common_lib.TEST_FILE_NAME)).as_posix()
                elif OperatingSystems.WINDOWS in self.os.os_type:
                    test_file_path = os.path.join(each_data + drive_separator, self._memory_common_lib.TEST_FILE_NAME)
                checksum_list_values_before_reboot.append(self._memory_common_lib.calculate_checksum(test_file_path))

            self._log.info("Checksum values before cold reboot cycle: {} are : {}".format(
                cycle + 1, checksum_list_values_before_reboot))

            # Step logger end for Step 2
            self._test_content_logger.end_step_logger(2, return_val=checksum_list_values_before_reboot)

            # Step logger start for Step 3
            self._test_content_logger.start_step_logger(3)

            # Copy and install IOPort rpm
            self._install_collateral.install_ioport()

            # To reboot the SUT.
            self._log.info("Executing Cold Reset")
            self.base_reboot.cold_reset()

            # Step logger end for Step 3
            self._test_content_logger.end_step_logger(3, return_val=True)

            # Step logger start for Step 4
            self._test_content_logger.start_step_logger(4)

            # To get the checksum values after the reboot
            for each_data in self.pmem_list:
                if OperatingSystems.LINUX in self.os.os_type:
                    test_file_path = Path(os.path.join(each_data, self._memory_common_lib.TEST_FILE_NAME)).as_posix()
                elif OperatingSystems.WINDOWS in self.os.os_type:
                    test_file_path = os.path.join(each_data + drive_separator, self._memory_common_lib.TEST_FILE_NAME)
                checksum_list_values_after_reboot.append(self._memory_common_lib.calculate_checksum(test_file_path))
            self._log.info("Checksum values after cold reboot cycle: {} are : {}".format(
                cycle + 1, checksum_list_values_after_reboot))

            # compare checksum values before reboot and after reboot
            if checksum_list_values_before_reboot != checksum_list_values_after_reboot:
                self._log.info("check sum values before cold reboot and after cold reboot are not same")
                return_value = False

            self._log.info("check sum values before cold reboot and after cold reboot are same")

            # To delete TEST FILE in hard disk
            self._memory_common_lib.delete_file(self._memory_common_lib.TEST_FILE_NAME)

            # To delete the TEST FILE in pmem disk
            for each_data in self.pmem_list:
                if OperatingSystems.LINUX in self.os.os_type:
                    test_file_path = Path(os.path.join(each_data, self._memory_common_lib.TEST_FILE_NAME)).as_posix()
                elif OperatingSystems.WINDOWS in self.os.os_type:
                    test_file_path = os.path.join(each_data + drive_separator, self._memory_common_lib.TEST_FILE_NAME)
                self._memory_common_lib.delete_file(test_file_path)

            # Step logger end for Step 4
            self._test_content_logger.end_step_logger(4, return_val=return_value)

        if os.path.exists(self._partition_provider.DRIVE_LETTERS_FILE):
            os.remove(self._partition_provider.DRIVE_LETTERS_FILE)

        return return_value

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""

        self._ipmctl_provider.delete_pmem_device()

        super(PiCR2LMAppDirectPMColdReboot, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiCR2LMAppDirectPMColdReboot.main() else Framework.TEST_RESULT_FAIL)
