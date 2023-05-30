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

from dtaf_core.lib.dtaf_constants import Framework
from src.memory.tests.memory_cr.barlow_pass.cycling.cr_cycling_common import CrCyclingCommon
from src.memory.tests.memory_cr.apache_pass.provisioning.cr_provisioning_2lm_mixed_mode_50_50_interleaved_dax_linux \
    import CRProvisioning2LM50AppDirect50MemoryModeDaxLinux


class CrDcUngracefuleADREnable(CrCyclingCommon):
    """
    Glasgow ID: 59772
    This test case is to demonstrate dc system reset cycles including OS boot and shutdown without unexpected errors.
    This testing covers the below tasks..
    1. Confirm that DCPMMs maintain configuration settings, and the system configuration does not fail with any error
    conditions.
    2. Command line access to DCPMM management functionality is available through the ipmctl component & native OS
    commands.
    3. Verify data persistence and integrity on DCPMMs provisioned with persistent regions after a sudden DC power
    loss and subsequent recovery and OS boot.
    4. eADR is invoked by the platform upon dc power loss is DCPMM DIMMs are configured in the AppDirect mode.
    5. eADR stands for Extended Asynchronous DRAM Refresh.
    6. eADR is a platform flow whereby the system power supply unit detects loss of DC power and causes data in the
    eADR safe zone to be flushed to DCPMM.
    7. A memory stress test is executed on each cycle.
    8. If persistent memory (DCPMM) filesystems are detected, stress is also executed targeting each filesystem.
    9. Attempt Fast Boot & Fast Cold Boot are Enabled.
    10. DCPMMs or system do not log any error conditions.
    """
    _bios_config_file = "rsc2_dc_ungraceful_os_shutdown_eadr_bios_knob_Linux.cfg"
    TEST_CASE_ID = "G59772"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new CrAcUngracefuleADREnable object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """

        # calling CRProvisioning2LM50AppDirect50MemoryModeDaxLinux
        self._cr_provisioning_50appdirect = CRProvisioning2LM50AppDirect50MemoryModeDaxLinux(test_log, arguments,
                                                                                             cfg_opts)

        self._cr_provisioning_50appdirect._log.info("Provisioning of DCPMM with 50% persistent and 50% memory mode "
                                                    "has been started.")
        self._cr_provisioning_50appdirect.prepare()
        self._cr_provisioning_result = self._cr_provisioning_50appdirect.execute()

        # calling base class init
        super(CrDcUngracefuleADREnable, self).__init__(test_log, arguments, cfg_opts, self._bios_config_file)

        if self._cr_provisioning_result:
            self._log.info("Provisioning of DCPMM with 50% persistent and 50% memory mode has been done successfully!")
        else:
            err_log = "Provisioning of DCPMM with 50% persistent and 50% memory mode is failed!"
            self._log.error(err_log)
            raise RuntimeError(err_log)

        self._dcpmm_platform_cycler_file_path = None

    def prepare(self):
        # type: () -> None
        """
        1. Setting the bios knobs to its default mode.
        2. Setting the bios knobs as per the test case.
        3. Rebooting the SUT to apply the new bios settings.
        4. Verifying the bios knobs that are set.
        5. Removing the old log files.
        6. Copy platform cycler tool tar file to Linux SUT.

        :return: None
        """
        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.

        self._common_content_lib.clear_os_log()

        command = "rm -rf {}".format(self.LINUX_PLATFORM_DC_CYCLER_LOG_PATH)
        # To delete the previous logs
        self._common_content_lib.execute_sut_cmd(command, "To delete previous logs", self._command_timeout)
        self._dcpmm_platform_cycler_file_path = self._install_collateral.install_dcpmm_platform_cycler()

    def execute(self):
        """
        1. Runs dc un graceful cycle.
        2. Used to get number of cycles, wait time and timeout.
        3. Also, checks whether operating system is alive or not and wait till the operating system to boot up.
        4. Parsing the logs generated by the test.

        :return: True, if the test case is successful.
        :raise: SystemError: Os is not alive even after specified wait time.
        """
        command = "--dcpmm --dcungraceful"
        # call installer dc ungraceful test
        self.execute_installer_dc_stress_test_linux(self._dcpmm_platform_cycler_file_path, command)

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
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self.LINUX_PLATFORM_DC_CYCLER_LOG_PATH, extension=".log")

        final_result = [self._mem_parse_log.dcpmm_platform_log_parsing
                        (log_path=os.path.join(log_path_to_parse, "platform_dc_ungraceful.log")),
                        self._mem_parse_log.verification_of_dcpmm_dirtyshutdown_log
                        (log_path=os.path.join(log_path_to_parse, "dcpmm_dirtyshutdowns.log")),
                        self._mem_parse_log.verification_dcpmm_log
                        (log_path=os.path.join(log_path_to_parse, "dcpmm.log")),
                        self._mem_parse_log.check_memory_log
                        (log_path=os.path.join(log_path_to_parse, "memory.log")),
                        self._mem_parse_log.parse_log_for_error_patterns
                        (log_path=os.path.join(log_path_to_parse, "mce.log")),
                        self._mem_parse_log.parse_log_for_error_patterns
                        (log_path=os.path.join(log_path_to_parse, "dmesg.log")),
                        self._mem_parse_log.parse_log_for_error_patterns
                        (log_path=os.path.join(log_path_to_parse, "journalctl.log"), encoding='UTF-8'),
                        self._mem_parse_log.parse_log_for_error_patterns
                        (log_path=os.path.join(log_path_to_parse, "sel.log"), encoding='UTF-8')]

        return all(final_result)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CrDcUngracefuleADREnable.main() else Framework.TEST_RESULT_FAIL)
