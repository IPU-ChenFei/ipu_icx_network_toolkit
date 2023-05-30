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
import re

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.test_content_logger import TestContentLogger
from src.lib.install_collateral import InstallCollateral
from src.storage.test.storage_common import StorageCommon
from src.lib import content_exceptions


class M2NVMEStabilityAndStressFIOLinux(StorageCommon):
    """  Phoenix ID : 16013670882 M2 NVME-Stability and Stress- FIO(CENTOS)
         Phoenix ID : 16013670865 M2 NVME-Stability and Stress- FIO(RHEL)
    This test case functionality is to install, execute fio tool on m.2 nvme ssd and verify bandwidth
    """
    TEST_CASE_ID = ["16013670882", "M2 NVME-Stability and Stress- FIO(CENTOS)",
                    "16013670865", "M2 NVME-Stability and Stress- FIO(RHEL)"]
    FIO_TOOL_CMD = "fio -name=m.2stress --rw={} --bs=64k --iodepth=4 --runtime={} " \
                   "--filename={} --size=1G --ioengine=posixaio " \
                   "--time_based --group_reporting --numjobs=100"
    BANDWIDTH_REGEX = "bw=(\d+)"
    FIO = "fio"
    READ_WRITE_OPERATION = "read_write_operation"
    FIO_RUN_TIME = "fio_runtime"
    FILE_NAMES = "file_name"
    EXPECTED_BANDWIDTH = "expected_bandwidth"
    step_data_dict = {
        1: {'step_details': 'Install and execute fio tool for required time',
            'expected_results': 'Successfully installed and executed fio tool'},
        2: {'step_details': 'Verify bandwidth speed limit',
            'expected_results': 'Successfully verified bandwidth'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new M2NVMEStabilityAndStressFIOLinux object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(M2NVMEStabilityAndStressFIOLinux, self).__init__(test_log, arguments, cfg_opts)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

    def prepare(self):
        # type: () -> None
        """
        :return None
        """
        super(M2NVMEStabilityAndStressFIOLinux, self).prepare()

    def execute(self):
        """
        This method functionality is to install, execute fio tool on m2 sata ssd and verify bandwidth

        :return: True
        :raise: If installation failed raise content_exceptions.TestFail
        """
        # Step logger Start for Step 1
        self._test_content_logger.start_step_logger(1)
        # Installing FIO Tool
        self._install_collateral.yum_install(self.FIO)
        # Get user inputs from content configuration
        fio_values = self._common_content_configuration.get_fio_tool_values()
        self._log.info("fio tool values:{}".format(fio_values))
        fio_command = self.FIO_TOOL_CMD.format(fio_values[self.READ_WRITE_OPERATION],int(fio_values[self.FIO_RUN_TIME]),
                                                                   fio_values[self.FILE_NAMES])
        self._log.info("Execution FIO tool for {} operation for {} seconds".format(fio_values[self.READ_WRITE_OPERATION],
                                                                                   fio_values[self.FIO_RUN_TIME]))
        command_output = self._common_content_lib.execute_sut_cmd(fio_command, fio_command, self._command_timeout)
        self._log.debug("fio tool command output for {} operation is:\n{}".format(fio_values[self.READ_WRITE_OPERATION],
                                                                             command_output))
        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, True)
        # Step logger Start for Step 2
        self._test_content_logger.start_step_logger(2)
        bw_regex_result = re.search(self.BANDWIDTH_REGEX, command_output)
        if int(fio_values[self.EXPECTED_BANDWIDTH]):
            if int(bw_regex_result.group(1)) < 80/100*int(fio_values[self.EXPECTED_BANDWIDTH]):
                raise content_exceptions.TestFail("Fio tool bandwidth value {} is less than {}".format(
                    bw_regex_result.group(1),int(fio_values[self.EXPECTED_BANDWIDTH])))
        else:
            if int(bw_regex_result.group(1)) <= 0:
                raise content_exceptions.TestFail("Fio tool bandwidth value {} is less than {}".format(
                    bw_regex_result.group(1), int(fio_values[self.BANDWIDTH_REGEX])))
        self._log.info("Successfully executed Fio tool and verified bandwidth value")
        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, True)

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""

        super(M2NVMEStabilityAndStressFIOLinux, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if M2NVMEStabilityAndStressFIOLinux.main() else Framework.TEST_RESULT_FAIL)
