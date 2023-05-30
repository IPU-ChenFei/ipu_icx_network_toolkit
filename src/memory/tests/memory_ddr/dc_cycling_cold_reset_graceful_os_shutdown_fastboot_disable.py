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
from src.memory.tests.memory_ddr.ddr_common import DDRCommon


class StressTestShutdownFastBootDis(DDRCommon):
    """
    Glasgow ID: 63307
    This test case is to demonstrate DC system reset cycles including OS boot and shutdown without unexpected errors.
    This testing covers the below tasks..
    1. Covers reliability testing of a standard Memory configuration with OS shutdown to system off, then power on (DC)
    cycling.
    2. Memory "Fast" Warm and Cold reset are disabled, forcing a platform memory reconfiguration by the MRC on each boot
    cycle.
    3. Stressapptest is executed for about two minutes on each cycle to exercise system memory.
    """
    _bios_config_file = "dc_os_shutdown_fastboot_disable.cfg"
    TEST_CASE_ID = "G63307"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new StressTestRebootFastBootDisable object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(StressTestShutdownFastBootDis, self).__init__(test_log,
                                                            arguments, cfg_opts,
                                                            self._bios_config_file)

    def prepare(self):
            # type: () -> None
            """
            set, verify and apply  bios settings.
            Copy the platform cycler tar file to SUT and installed it.

            :return: None
            """

            super().prepare()
            self._common_content_lib.clear_all_os_error_logs()  # To clear Os logs
            self._platform_cycler_extract_path = self._install_collateral.install_platform_cycler()

    def execute(self):
        """
        Used to get number of cycles, wait time and timeout.
        Also, checks whether operating system is alive or not and wait till the operating system to boot up.

        :return: True, if the test case is successful.
        :raise: SystemError: Os is not alive even after specified wait time.
        """
        # call installer reboot stress test
        self.execute_installer_dcgraceful_stress_test_linux(self._platform_cycler_extract_path)
        if self._os.is_alive():
            self._log.info("SUT is alive after stress test ...")
        else:
            self._log.info("SUT is not alive after stress test and we will wait for reboot "
                           "timeout for SUT to come up ...")
            self._os.wait_for_os(self._reboot_timeout)  # should check this for os timeout.

        if not self._os.is_alive():
            self._log.error("SUT did not come-up even after waiting for specified time...")
            raise SystemError("SUT did not come-up even after waiting for specified time...")

        self._common_content_lib.delete_testcaseid_folder_in_host(test_case_id=self.TEST_CASE_ID)
        log_path_to_parse = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self.LINUX_PLATFORM_DC_CYCLER_LOG_PATH,extension=".log")

        return self.log_parsing(log_file_path=log_path_to_parse)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StressTestShutdownFastBootDis.main() else Framework.TEST_RESULT_FAIL)
