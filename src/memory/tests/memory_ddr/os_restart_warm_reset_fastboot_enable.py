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


class StressTestRebootFastBootEn(DDRCommon):
    """
    Glasgow ID : 57804
    This test case is to demonstrate OS warm Restart and verify that the system can perform many OS warm restarts
    without error with a given memory configuration.
    Operating System: Linux
    This testing covers the below tasks..
    1. OS warm restart testing of a Memory configuration.
    2. Memory "Fast" Warm and Cold reset are enabled, forcing a platform memory reconfiguration by the MRC on each boot
    cycle.
    3. Stressapptest is executed for about two minutes on each cycle to exercise system memory.
    """
    _bios_config_file = "memory_bios_knobs_fastboot_enable.cfg"  # Bios knob config file to set the appropriate knobs.
    TEST_CASE_ID = "G57804"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new StressTestRebootFastBootEn object
        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(StressTestRebootFastBootEn, self).__init__(test_log, arguments, cfg_opts, self._bios_config_file)
        self._platform_cycler_extract_path = None

    def prepare(self):
        # type: () -> None
        """
        1. Setting the bios knobs to its default mode.
        2. Setting the bios knobs as per the test case.
        3. Rebooting the SUT to apply the new bios settings.
        4. Verifying the bios knobs that are set.
        5. Copy platform cycler tool tar file to Linux SUT.
        6. Unzip tar file under user home folder.
        :return: None
        """
        self._common_content_lib.clear_all_os_error_logs()  # To clear Os logs
        self._bios.default_bios_settings()  # To set the Bios Knobs to its default mode.
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.
        self._platform_cycler_extract_path = self._install_collateral.install_platform_cycler()  # Install platform cycler
        # tool in SUT

    def execute(self):
        """
        Used to get number of cycles, wait time and timeout.
        Also, checks whether operating system is alive or not and wait till the operating system to boot up.
        :return: True, if the test case is successful.
        :raise: SystemError: Os is not alive even after specified wait time.
        """
        # call installer reboot stress test
        self.execute_installer_reboot_stress_test_linux(self._platform_cycler_extract_path)

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
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self.LINUX_PLATFORM_REBOOTER_LOG_PATH, extension=".log")

        return self.log_parsing_rebooter(log_file_path=log_path_to_parse)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if StressTestRebootFastBootEn.main() else Framework.TEST_RESULT_FAIL)
