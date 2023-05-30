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
from src.lib.test_content_logger import TestContentLogger
from src.memory.tests.memory_cr.barlow_pass.cycling.cr_cycling_common import CrCyclingCommon
from src.memory.tests.memory_cr.apache_pass.provisioning.cr_provisioning_2lm_mixed_mode_50_50_interleaved_dax_linux \
    import CRProvisioning2LM50AppDirect50MemoryModeDaxLinux


class CrDcGracefuleADREnable(CrCyclingCommon):
    """
    Glasgow ID: 59994
    This test case is to demonstrate dc system reset cycles including OS boot and shutdown without unexpected errors.
    This testing covers the below tasks..
    1. Confirm that DCPMMs maintain configuration settings, and the system configuration does not fail with any error
    conditions.
    2. Verify that a system can perform cold "DC" system reset cycles including system power on, OS boot and shutdown
    without unexpected errors with "Multi-Threaded MRC" enabled.
    3. Confirm that DCPMMs maintain confguration settings, and the system configuration does not fail with any error
    conditions.
    4. Command line access to DCPMM management functionality is available through the ipmctl component & native OS
    commands.
    5. Verify data persistence and integrity on DCPMMs provisioned with persistent regions after a cold system reset.
    6. eADR is invoked by the platform upon AC power loss is DCPMM DIMMs are configured in the AppDirect mode.
    7. eADR stands for Extended Asynchronous DRAM Refresh.
    8. eADR is a platform flow whereby the system power supply unit detects loss of AC power and causes data in the
    eADR safe zone to be flushed to DCPMM.
    9. This process is critical during a power loss event or system crash to ensure the contents are in a safe state.
    10. A memory stress test is executed on each cycle.
    11. If persistent memory (DCPMM) filesystems are detected, stress is also executed targeting each filesystem.
        Attempt Fast Boot & Fast Cold Boot are Enabled.
    12. DCPMMs or system do not log any error conditions.

    """
    _bios_config_file = "cr_rsc2_dc_cycling_graceful_os_shutdown_eadr_multicpu_linux.cfg"
    TEST_CASE_ID = "G59994"
    _dcpmm_dc_graceful_cycler_command = "--dcpmm --dcgraceful"
    step_data_dict = {1: {"step_details": "clear os log, Set & verify Bios kobs and install Platform cycler, "
                                          "FIO and StressTestApp tools on SUT",
                          "expected_results": "Clear ALL the system Os logs, BIOS setup options are updated with "
                          "changes saved and Platform cycler, FIO and StressTestApp tools are installed"},
                      2: {"step_details": "Verify the installed memory is reported accurately under the Linux Os and "
                                          "DCPMMS were previously provisional with a Liux recognizable file system",
                          "expected_results": "Successfully verified is reported accurately on Os and the expected "
                                              "pmem device(s) & filesystems are present"},
                      3: {"step_details": "Run the dcpmm platform cycler with dcpmm dcgraceful cycles",
                          "expected_results": "dcpmm dcgraceful cycles should executed successfully"},
                      4: {"step_details": "platform_dc_graceful, dcpmm_dirtyshutdown, dcpmm, memory, mce, sel, "
                                          "journalctl and dmesg logs need to review",
                          "expected_results": "All the logs should not report any errors"}}

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

        #  calling base class init
        super(CrDcGracefuleADREnable, self).__init__(test_log, arguments, cfg_opts, self._bios_config_file)

        #  Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

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
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        self._common_content_lib.clear_os_log()  # Clear os logs
        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.

        command = "rm -rf {}".format(self.LINUX_PLATFORM_DC_GRACEFUL_CYCLER_LOG_PATH)  # To delete the previous logs
        self._common_content_lib.execute_sut_cmd(command, "To delete previous logs", self._command_timeout)
        self._install_collateral.install_stress_test_app()  # To install StressTestApp Tool
        self._install_collateral.install_fio()  # To install FIO Tool
        # To install platform cycler tool
        self._dcpmm_platform_cycler_file_path = self._install_collateral.install_dcpmm_platform_cycler()
        #  Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        1. Runs dc graceful cycle.
        2. Used to get number of cycles, wait time and timeout.
        3. Also, checks whether operating system is alive or not and wait till the operating system to boot up.
        4. Parsing the logs generated by the test.

        :return: True, if the test case is successful.
        :raise: SystemError: Os is not alive even after specified wait time.
        """
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        #  Show System Memory info
        system_memory_data = self._cr_provisioning_50appdirect.show_system_memory_report_linux()

        #  Verify 2LM provisioning mode
        self._cr_provisioning_50appdirect.verify_lm_provisioning_configuration_linux(
            self._cr_provisioning_50appdirect.dcpmm_disk_goal, system_memory_data, mode="2LM")

        #  To get the DCPMM disk namespaces information
        namespace_info = self._cr_provisioning_50appdirect.dcpmm_get_disk_namespace()

        #  Verify namespace presence
        result_status = self._cr_provisioning_50appdirect.verify_pmem_device_presence(namespace_info)

        # Step Logger end for Step 2
        self._test_content_logger.end_step_logger(2, result_status)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        # call installer dc graceful test
        self.execute_installer_dc_stress_test_linux(self._dcpmm_platform_cycler_file_path,
                                                    self._dcpmm_dc_graceful_cycler_command)

        # Step Logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)

        # Step Logger start for Step 4
        self._test_content_logger.start_step_logger(4)

        self._common_content_lib.delete_testcaseid_folder_in_host(test_case_id=self.TEST_CASE_ID)
        log_path_to_parse = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self.LINUX_PLATFORM_DC_GRACEFUL_CYCLER_LOG_PATH,
            extension=".log")

        final_result = [self._mem_parse_log.dcpmm_platform_log_parsing
                        (log_path=os.path.join(log_path_to_parse, "platform_dc_graceful.log")),
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

        # Step Logger end for Step 4
        self._test_content_logger.end_step_logger(4, all(final_result))

        return all(final_result)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CrDcGracefuleADREnable.main() else Framework.TEST_RESULT_FAIL)
