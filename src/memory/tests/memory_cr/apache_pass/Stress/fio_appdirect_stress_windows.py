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
from src.memory.tests.memory_cr.apache_pass.Stress.cr_stress_common import CrStressTestCommon
from src.memory.tests.memory_cr.apache_pass.provisioning.cr_provisioning_2lm_mixed_mode_25_75_interleaved_block import \
    CRProvisioning2LM25AppDirect75MemoryMode
from src.lib.memory_constants import PowerScheme

class CRFioAppDirectStress(CrStressTestCommon):
    """
    Glasgow ID: 57880
    Stress test is to ensure overall platform stability when configured with DCPMM and DDR DIMMs in
    AppDirect mode with storage partitions.

    FIO is used for targeted stress Disk IO Workload stress of the AppDirect DCPMM Provision.
    FIO works on both files and block operations.
    """

    BIOS_CONFIG_FILE = "fio_appdirect_stress_windows_bios_knobs.cfg"
    TEST_CASE_ID = "G57880"

    _ipmctl_executer_path = None
    _fio_executer_path = None

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new CRFioAppDirectStress object.

        :param test_log: Used for error, debug and info messages.
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # Provisioning test case
        self._cr_provisioning_25appdirect = CRProvisioning2LM25AppDirect75MemoryMode(test_log, arguments, cfg_opts)
        self._cr_provisioning_25appdirect.prepare()
        self._provisioning_result = self._cr_provisioning_25appdirect.execute()

        # calling base class init
        super(CRFioAppDirectStress, self).__init__(test_log, arguments, cfg_opts,
                                                   self.BIOS_CONFIG_FILE)

        if self._provisioning_result:
            self._log.info("Provisioning of DCPMM with 25% persistent and 75% memory mode has been done successfully!")
        else:
            err_log = "Provisioning of DCPMM with 25% persistent and 75% memory mode is failed!"
            self._log.error(err_log)
            raise RuntimeError(err_log)

    def prepare(self):
        # type: () -> None
        """
        1. Set the bios knobs to its default mode.
        2. Set the bios knobs as per the test case.
        3. Reboot the SUT to apply the new bios settings.
        4. Verify the new bios knobs.
        5. Copy ipmctl tool to windows SUT.
        6. Unzip file under home folder.

        :return: None
        """
        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.

        #  Clear system even log
        self._windows_event_log.clear_system_event_logs()

        #  Clear Application log
        self._windows_event_log.clear_application_logs()

        self._ipmctl_executer_path = self._install_collateral.install_ipmctl()
        self._fio_executer_path = self._install_collateral.install_fio()

        # Confirm the power scheme is set to "Balanced".
        self._os_lib.set_power_scheme(option=PowerScheme.BALANCED)

        # Set the display to never turn off (Disable screen blanking and / or the screen saver).
        self._os_lib.screen_awake_settings()

    def execute(self):
        """
        Function is responsible for the below tasks,

        1. Ensure platform is configured to log all Correctable memory errors to the SEL.
        2. Platform memory is in NUMA mode and booted to Windows OS.
        3. Confirm AppDirect provisioning for persistent storage.
        4. FIO is used for targeted stress Disk IO Workload stress of the AppDirect DCPMM Provision.
        5. Clear SEL.
        6. Execute FIO stress as specified in the test case.
        7. Check OS application and system event logs for unexpected errors.
        8. Check Thermal and Media errors on the dimms.

        :return: True, if the test case is successful else false
        :raise: None
        """
        return_value = []

        #  Show System Memory info
        self._cr_provisioning_25appdirect.ipmctl_get_system_capability()

        # Pre-existing namespaces are identified here.
        pmem_disk_list = self._cr_provisioning_25appdirect.dcpmm_get_disk_namespace()

        # Verify that the pmem disk size is greater then 10GB
        return_value.append(self.verify_pmem_disk_size(pmem_disk_list))

        # This will get us the dcpmm disk list in number
        disk_list = self._cr_provisioning_25appdirect.get_dcpmm_disk_list()

        self._log.info("{} DCPMM device(s) attached to this system board {}.".format(len(disk_list), disk_list))

        # Verify the pmem disk partitioning happened correctly.
        return_value.append(self._cr_provisioning_25appdirect.verify_disk_partition(
            disk_lists=disk_list, drive_letters=self._cr_provisioning_25appdirect.store_generated_dcpmm_drive_letters))

        # verify the amount of "Total Physical Memory" reported.
        self._cr_provisioning_25appdirect.getting_system_memory()

        # Get the system utility information
        system_info_log_path = self._cr_provisioning_25appdirect.store_system_information()

        # Fio app commands will run only if the provisioning and verification of pmem disks are passed.
        if all(return_value):
            fio_test_drives = self.create_fiotest_drive_letters(
                self._cr_provisioning_25appdirect.store_generated_dcpmm_drive_letters)

            # FIO commands
            # Sequential write:
            self._fio_common_lib.fio_sequential_write(fio_test_drives)

            # Sequential read:
            self._fio_common_lib.fio_sequential_read(fio_test_drives)

            # Mixed read/write:
            self._fio_common_lib.fio_mixed_read_write(fio_test_drives)

            # Random write:
            self._fio_common_lib.fio_random_write(fio_test_drives)

            # Random read:
            self._fio_common_lib.fio_random_read(fio_test_drives)
        else:
            err_log = "The pmem verfication failed, please try again after provisioning."
            self._log.error(err_log)
            raise RuntimeError(err_log)

        self._common_content_lib.delete_testcaseid_folder_in_host(test_case_id=self.TEST_CASE_ID)

        # Copy the system utility information log file.
        log_file_path_host = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=system_info_log_path, extension=".log")

        stress_test_result = []
        # Get whea error,warning logs
        whea_logs = self._windows_event_log.get_whea_error_event_logs()
        # Check if there are any errors, warnings of category WHEA found
        if whea_logs is None or len(str(whea_logs)) == 0:
            self._log.info("No WHEA errors or warnings found in Windows System event log...")
            stress_test_result.append(True)
        else:
            self._log.error("Found WHEA errors or warnings in Windows System event log...")
            self._log.error("WHEA error logs: \n" + str(whea_logs))
            stress_test_result.append(False)

        application_logs = self._windows_event_log.get_application_event_error_logs("-EntryType Error,Warning")
        # Check if there are any errors, warnings
        if application_logs is None or len(str(application_logs)) == 0:
            self._log.info("No errors or warnings found in OS application log...")
            stress_test_result.append(True)
        else:
            self._log.error("Found errors or warnings in OS application log...")
            self._log.error("Error logs: \n" + str(application_logs))
            stress_test_result.append(False)

        fio_log_results = [
            self._fio_common_lib.fio_log_parsing(log_path=os.path.join(log_file_path_host, "win_fio_seq_write.log"),
                                                 pattern="WRITE:"),
            self._fio_common_lib.fio_log_parsing(log_path=os.path.join(log_file_path_host, "win_fio_seq_read.log"),
                                                 pattern="READ:"),
            self._fio_common_lib.fio_log_parsing(log_path=os.path.join(log_file_path_host, "win_fio_mixed_rw.log"),
                                                 pattern="READ:|WRITE:"),
            self._fio_common_lib.fio_log_parsing(log_path=os.path.join(log_file_path_host, "win_fio_ran_read.log"),
                                                 pattern="WRITE:"),
            self._fio_common_lib.fio_log_parsing(log_path=os.path.join(log_file_path_host, "win_fio_ran_write.log"),
                                                 pattern="WRITE:")
        ]

        # Pmem filesystems are still intact & consistent with earlier reporting.
        return_value.append(self._cr_provisioning_25appdirect.verify_disk_partition(
            disk_lists=disk_list, drive_letters=self._cr_provisioning_25appdirect.store_generated_dcpmm_drive_letters))

        # Display unexpected thermal and media errors
        self.get_ipmctl_error_logs(self._ipmctl_executer_path, "Media", "Thermal")

        log_file_path_host = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self._ipmctl_executer_path, extension=".log")

        return_value.append(self.verify_ipmctl_error("Media", os.path.join(log_file_path_host,
                                                                           "Media.log")))
        return_value.append(self.verify_ipmctl_error("Thermal", os.path.join(log_file_path_host,
                                                                             "Thermal.log")))

        return_value.append(all(stress_test_result))
        return_value.append(all(fio_log_results))

        return all(return_value)


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if CRFioAppDirectStress.main() else Framework.TEST_RESULT_FAIL)
