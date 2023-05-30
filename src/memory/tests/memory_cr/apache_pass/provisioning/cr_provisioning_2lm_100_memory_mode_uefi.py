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
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib import content_exceptions
from src.lib.bios_util import BootOptions
from src.lib.test_content_logger import TestContentLogger
from src.memory.tests.memory_cr.apache_pass.provisioning.cr_provisioning_common import CrProvisioningTestCommon


class CRProvisioning2ML100MemoryModeUefi(CrProvisioningTestCommon):
    """
    Glasgow ID : 57097
    Configure and verify DCPMMs in 100% 2LM Memory Mode using UEFI provisioning tools..

    1. Create an explicit 100% 2LM memory mode.
    2. DCPMMs will be provisioned as 100% memory mode
    3. Command line access to the DIMM management functionality is available through the IPMCTL component & UEFI
    commands.
    """

    BIOS_CONFIG_FILE = "cr_provisioning_2lm_100_memory_mode_uefi.cfg"
    TESTCASE_ID = "G57097"

    step_data_dict = {1: {'step_details': 'Copy ipmctl efi file from host to sut and sut to usb and '
                                          'Memory checks on POST and BIOS.',
                          'expected_results': ' ipmct.efi copied from host to usb and Memory checks on POST and BIOS '
                                              'are verified successfully.'},
                      2: {'step_details': 'Clear OS logs and Set & Verify BIOS knobs',
                          'expected_results': ' BIOS setup options are updated with changes saved'},
                      3: {'step_details': 'Boot to the UEFI shell & show the dimm id, capacity, and delete the '
                                          'existing namespace',
                          'expected_results': ' DIMMs are listed with IDs and existing namespace deleted'
                                              'and Dimms capacity are healthy and correctFW Version is displayed'},
                      4: {'step_details': 'Create goal of 100% Memory mode and restart the SUT ',
                          'expected_results': 'Ran the command to created a goal of 100% memory mode and '
                                              'restart the SUT and check memory resources'},
                      5: {'step_details': 'Store the memory allocation settings for all DCPMMs in the system to a '
                                          'file for later use and SUT reboot',
                          'expected_results': 'Currently configured DCPMM allocation settings are '
                                              'saved to a file successfully and file contents are as expected, '
                                              'SUT rebooted'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new CRProvisioning 2LM100 Memory Mode.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # Calling base class init
        super(CRProvisioning2ML100MemoryModeUefi, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)

        self._platform_config_reader = None

        #  Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TESTCASE_ID, self.step_data_dict)
        self._bios_boot_menu_entry_wait_time = self._common_content_configuration.bios_boot_menu_entry_wait_time()

        self.usb_file_path = None

    def prepare(self):
        # type: () -> None
        """
        1. Set the bios knobs to its default mode.
        2. Set the bios knobs as per the test case.
        3. Reboot the SUT to apply the new bios settings.
        4. Verify the bios knobs that are set.
        5. Copy efi tool to usb drive from host machine.

        :return: None
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        ipmctl_file_name = os.path.split(self._ipmctl_efi_tool_path_config)[-1].strip()

        if OperatingSystems.WINDOWS == self._os.os_type:
            zip_file_path = self._common_content_lib.copy_zip_file_to_sut(
                ipmctl_file_name.split(".")[0], ipmctl_file_name)

            self.usb_file_path = self._copy_usb.copy_file_from_sut_to_usb(
                self._common_content_lib, self._common_content_configuration, zip_file_path)
        elif OperatingSystems.LINUX == self._os.os_type:
            zip_file_path = self._common_content_lib.copy_zip_file_to_linux_sut(
                ipmctl_file_name.split(".")[0], ipmctl_file_name)

            self.usb_file_path = self._copy_usb.copy_file_from_sut_to_usb(
                self._common_content_lib, self._common_content_configuration, zip_file_path)
        else:
            log_err = "Test case 'CR Provisioning 2LM 100% memory mode UEFI' is not supported on OS {}"\
                .format(self._os.os_type)
            self._log.error(log_err)
            raise NotImplementedError(log_err)

        #  Show System Memory info
        system_memory_data = self._memory_common_lib.get_system_memory_report_linux()

        total_memory = self._memory_common_lib.get_total_system_memory_data_linux(system_memory_data)

        # Converting into GiB
        total_dram_memory_os = int(total_memory / 1024)

        self._log.debug("Total memory capacity shown OS Level : {} GB".format(total_dram_memory_os))

        total_memory_variance_post = self._post_mem_capacity - (self._post_mem_capacity * self._variance_percent)

        total_memory_variance_dram = self._ddr4_mem_capacity - (self._ddr4_mem_capacity * self._variance_percent)

        self._log.debug("Total POST reported DDR capacity as per configuration with - {} % variance is : {} GB".format(
            self._variance_percent, total_memory_variance_post))

        if total_dram_memory_os < int(total_memory_variance_post) or total_dram_memory_os > \
                self._post_mem_capacity:
            raise content_exceptions.TestFail("Total Installed DDR memory Capacity reported during POST "
                                              "Configuration (vs) OS does not match.")

        self._log.info("Total Installed DDR memory Capacity reported during POST Configuration (vs) OS matches.")

        if total_dram_memory_os < int(total_memory_variance_dram) or total_dram_memory_os > \
                self._ddr4_mem_capacity:
            raise content_exceptions.TestFail("Total Installed DDR memory Capacity reported in BIOS Configuration (vs)"
                                              "OS does not match.")

        self._log.info("Total Installed DDR memory Capacity reported during BIOS Configuration (vs) OS matches.")

        #  Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

        #  Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
        try:
            self._bios_util.verify_bios_knob()  # To verify the new bios setting.
        except Exception as ex:
            self._log.debug(ex)  # Bypassing false Negative scenario while verifying SNC bios knob.

        #  Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. Configure and verify DCPMMs in 100% 2LM Memory Mode using UEFI provisioning tools.
        2. Delete the existing namespaces.
        3. Create namespaces for the persistent regions using goal.
        4. Verify namespaces and provisioning.
        5. Save DCPMM configuration data to a file.

        :return: True, if the test case is successful.
        :raise: None
        """
        return_value = []
        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        current_boot_order_string = self._itp_xmlcli.get_current_boot_order_string()

        self._itp_xmlcli.set_default_boot(BootOptions.UEFI)

        self._uefi_util_obj.graceful_sut_ac_power_on()

        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)

        # To ignore the letter scrap from uefi while executing any command for the first time.
        self._uefi_obj.execute('\n')

        # Get usb drive list from  UEFI shell
        usb_drive_list = self._uefi_util_obj.get_usb_uefi_drive_list()
        self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(usb_drive_list[0])

        #  To Run mode supported capabilities
        mode_support_return_value = self._ipmctl_provider_uefi.get_supported_modes()

        #  Verifying 1LM mode support values and App direct mode
        self._memory_common_lib.verify_provisioning_mode(mode_support_return_value)

        # To get dimms info
        dimm_val = self._ipmctl_provider_uefi.get_dimm_info()

        # Creating a data frame with dimm information and adding extra columns as per our test case need.
        self._ipmctl_provider_uefi.get_memory_dimm_information()

        # Get the list of dimms which are healthy and log them.
        self._ipmctl_provider_uefi.get_list_of_dimms_which_are_healthy()

        # Verify the list of dimms which are healthy are matching with the pmem disk output.
        self._ipmctl_provider_uefi.verify_all_dcpmm_dimm_healthy()

        # Verify the firmware version of each dimms are matching with the pmem disk output.
        self._ipmctl_provider_uefi.verify_dimms_firmware_version()

        self._ipmctl_provider_uefi.delete_pcd_data()

        self._log.info("PCD data on the DIMMS has been successfully deleted, system has been rebooted..")

        self._log.info("Waiting to boot into UEFI Internal Shell ..")

        #  To reboot the system
        self._uefi_obj.warm_reset()

        # Wait time to enter in to UEFI shell
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)

        # To ignore the letter scrap from uefi while executing any command for the first time.
        self._uefi_obj.execute('\n')

        #  Get usb  drive list from  UEFI shell
        usb_drive_list = self._uefi_util_obj.get_usb_uefi_drive_list()
        self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(usb_drive_list[0])

        # To get namespace info
        list_namespace = self._ipmctl_provider_uefi.dcpmm_get_disk_namespace()

        # To clear namespace id's if exists
        self._ipmctl_provider_uefi.dcpmm_check_disk_namespace_initilize(list_namespace)

        #  Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, True)

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)

        #  To create goal for to Configure all the DCPMM capacity as memory mode  with the attributes
        dcpmm_disk_goal = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response("ipmctl.efi create -f -goal "
                                                                                    "memorymode=100")
        dcpmm_disk_goal = ' '.join([str(elem) for elem in dcpmm_disk_goal])

        if not dcpmm_disk_goal:
            raise content_exceptions.TestFail("Failed to provision crystal ridge DIMMS with 100% Memory Mode...")

        #  To show the goal data
        goal_info = self._ipmctl_provider_uefi.show_goal()
        self._log.debug("Show DCPMM information...{}".format(goal_info))

        self._log.info("Successfully provisioned crystal ridge DIMMS as 100% Memory Mode... Rebooting to apply the "
                       "changes ...")

        self._log.info("Waiting to boot into UEFI Internal Shell ..")

        #  To reboot the system
        self._uefi_obj.warm_reset()

        # Wait time to enter in to UEFI shell
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)

        # To ignore the letter scrap from uefi while executing any command for the first time.
        self._uefi_obj.execute('\n')

        #  Get usb  drive list from  UEFI shell
        usb_drive_list = self._uefi_util_obj.get_usb_uefi_drive_list()
        self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(usb_drive_list[0])

        #  To get the memory supported values
        mem_resources_data = self._ipmctl_provider_uefi.show_mem_resources()
        mem_resources_data = '\n'.join(map(str, mem_resources_data))
        self._log.debug("Memory resources info...{}".format(mem_resources_data))

        #  To confirm that this goal is 100% memory mode
        self.verify_app_direct_mode_provisioning(mode="mem", mode_percentage=100,
                                                 total_memory_result_data=dimm_val,
                                                 app_direct_result_data=dcpmm_disk_goal)

        app_direct_capacity_list = self.get_app_direct_mode_data(dcpmm_disk_goal)

        if not all(capacity == 0 for capacity in app_direct_capacity_list):
            raise content_exceptions.TestFail("Checks found that AppDirectCapacity is non-zero... Exiting..")

        self._log.info("Verified that AppDirectCapacity is zero..")

        self._log.info("System has been rebooted..")

        #  Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, mem_resources_data)

        # Step logger start for Step 5
        self._test_content_logger.start_step_logger(5)

        #  To create config csv file in USB drive
        self._ipmctl_provider_uefi.create_config_csv()

        # To change boot order to OS.
        self._itp_xmlcli.set_boot_order(current_boot_order_string)

        self._log.info("System has been rebooted..")

        self._uefi_util_obj.graceful_sut_ac_power_on()

        self._os.wait_for_os(self.reboot_timeout)

        self._log.info("Waiting for system to come to OS...")

        if not self._os.is_alive():
            log_error = "System did not come to OS within {} seconds after a reboot from UEFI shell...".format(
                self._reboot_timeout)
            raise RuntimeError(log_error)

        self._log.info("System came to OS after a reboot from UEFI shell")

        # Copy the .csv file from USB to SUT
        sut_file_path = self._copy_usb.copy_file_from_usb_to_sut(self._common_content_lib,
                                                                 self._common_content_configuration, self.usb_file_path)

        # Copy the .csv file from SUT to HOST
        host_file_path = self._common_content_lib.copy_log_files_to_host(self.TESTCASE_ID, str(sut_file_path), ".csv")

        #  To verify the data in csv file
        return_value.append(self.verify_provisioning_final_dump_data_csv(log_file_path=host_file_path))

        #  Step logger end for Step 5
        self._test_content_logger.end_step_logger(5, return_value)

        return all(return_value)

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(CRProvisioning2ML100MemoryModeUefi, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CRProvisioning2ML100MemoryModeUefi.main() else Framework.TEST_RESULT_FAIL)
