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
from src.provider.copy_usb_provider import UsbRemovableDriveProvider
from src.memory.tests.memory_cr.apache_pass.provisioning.cr_provisioning_common import CrProvisioningTestCommon


class CRProvisioning2LmMixedMode75Memory25Appdirect(CrProvisioningTestCommon):
    """
    Glasgow ID : 55802.10
    Verification of the platform supported DCPMM capabilities in a UEFI pre-boot environment.

    1. Create a 2LM mixed mode goal with persistent memory, 25% AppDirect & 75% Memory Mode not interleaved capacity
    2. All installed DCPMM(s) are configured with 75% of capacity as volatile memory and the the remainder
    as a region of "not interleaved" persistent memory.
    3. DCPMMs are capable of supporting AppDirect mode with 2LM enabled.
    4. Command line access to the DIMM management functionality is available through the ipmctl component & uefi
    commands.
    """

    BIOS_CONFIG_FILE = "cr_provisioning_2lm_mixed_mode_25_75_not_interleaved_uefi.cfg"
    TC_ID = "G55802"

    step_data_dict = {1: {'step_details': 'Copy ipmctl efi file from host to usb and Set & Verify BIOS knobs'
                                          'and memory check in POST and BIOS.',
                          'expected_results': 'Ipmctl.efi copied from host to usb and BIOS setup options are updated'
                                              'with changes saved and memory check successful.'},
                      2: {'step_details': 'Boot to UEFI shell, Launch ipmctl tool to check modes supported and dimm '
                                          'information verification.',
                          'expected_results': 'Ipmctl launches successfully, Memory & App Direct Modes are both '
                                              'supported, All installed DCPMMs are listed with IDs and capacities '
                                              'and are healthy. The correct DCPMM FW Version is displayed.'},
                      3: {'step_details': 'Display the recommended App Direct Mode setting capabilities  namespaces '
                                          'are listed and existing namespace delete ',
                          'expected_results': 'App Direct interleave settings are verified  as format '
                                              'x[Way] - [(IMCSize) iMC x (ChannelSize) Channel] and Existing '
                                              'namespaces are identified and deleted '},
                      4: {'step_details': 'Delete pcd data.', 'expected_results': 'Successfully deleted pcd data.'},
                      5: {'step_details': 'Check whether the DIMMs have pre-existing namespaces.',
                          'expected_results': 'Commands complete without errors, Pre-existing namespaces are '
                                              'identified and removed from DIMMs.'},
                      6: {'step_details': 'Create goal of 75% Memory mode and rest as appdirect not-interleaved mode, '
                                          'display goal information and restart the SUT ',
                          'expected_results': 'The memory allocation goal for the DCPMM configuration that was just '
                                              'created is displayed and SUT been rebooted successfully.'},
                      7: {'step_details': 'After SUT restated the goal was applied, Confirm namespaces were '
                                          'successfully created and accurately reported.',
                          'expected_results': 'Each of the newly created namespaces are listed and healthy with '
                                              'expected capacity, Namespaces are listed with expected attributes such '
                                              'as: NamespaceID, Capacity, HealthState'},
                      8: {'step_details': 'Show all the attributes for the newly created namespace,pmem block device'
                                          'is available in the UEFI shell ',
                          'expected_results': 'The newly created namespaces should be listed with mapped paths in the '
                                              'UEFI shell, verified pmem block available uefi shell and its Persistent '
                                              'Memory Regions and FreeCapacity.'},
                      9: {'step_details': 'Store the memory allocation settings for all DCPMMs in the system to a '
                                          'file for later use and SUT reboot',
                          'expected_results': 'Successfully The currently configured DCPMM allocation settings are '
                                              'saved to a file and The file contents are as expected SUT rebooted'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new CRProvisioning2LM 75% memory mode and 25% appdirect .

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        super(
            CRProvisioning2LmMixedMode75Memory25Appdirect, self).__init__(test_log, arguments, cfg_opts,
                                                                          self.BIOS_CONFIG_FILE)

        #  Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TC_ID, self.step_data_dict)

        self._copy_usb = UsbRemovableDriveProvider.factory(test_log, cfg_opts, self._os)
        _opt_obj, _test_log_obj = cfg_opts, test_log
        self.usb_file_path = None
        self.sut_os = self._os.os_type
        self._bios_boot_menu_entry_wait_time = self._common_content_configuration.bios_boot_menu_entry_wait_time()

    def prepare(self):
        # type: () -> None
        """
        1. Copy ipmctl efi file from host to SUT and SUT to USB
        1. Set the bios knobs to its default mode.
        2. Set the bios knobs as per the test case.
        3. Reboot the SUT to apply the new bios settings.
        4. Verify the bios knobs that are set.

        :return: None
        """

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        ipmctl_file_name = os.path.split(self._ipmctl_efi_tool_path_config)[-1].strip()

        if OperatingSystems.WINDOWS == self._os.os_type:
            zip_file_path = self._install_collateral.download_and_copy_zip_to_sut(
                ipmctl_file_name.split(".")[0], ipmctl_file_name)

            self.usb_file_path = self._copy_usb.copy_file_from_sut_to_usb(
                self._common_content_lib, self._common_content_configuration, zip_file_path)
        elif OperatingSystems.LINUX == self._os.os_type:
            zip_file_path = self._install_collateral.download_and_copy_zip_to_sut(
                ipmctl_file_name.split(".")[0], ipmctl_file_name)

            self.usb_file_path = self._copy_usb.copy_file_from_sut_to_usb(
                self._common_content_lib, self._common_content_configuration, zip_file_path)
        else:
            log_err = "Test case 'CR Provisioning 2LM mixed mode UEFI' is not supported on OS {}" \
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

        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
        try:
            self._bios_util.verify_bios_knob()  # To verify the new bios setting.
        except Exception as ex:
            self._log.debug(ex)  # Bypassing false Negative scenario while verifying SNC bios knob.

        #  Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. It is first confirmed that the DCPMMs are capable of supporting AppDirect mode with 2LM enabled.
        2. All installed DCPMM(s) 75% of capacity as volatile memory and the remainder as regions
         of persistent memory.
        3. Delete the existing namespaces.
        5. Create namespaces for the persistent regions.
        6. Verify namespaces and region status.
        7. Save DCPMM configuration data to a file.

        :return: True, if the test case is successful.
        :raise: None
        """

        return_value = []
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

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

        #  Step logger start for Step 2
        self._test_content_logger.end_step_logger(2, True)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        #  To display the recommended App Direct Moe setting capabilities
        dimm_app_direct_settings = self._ipmctl_provider_uefi.dcpmm_get_app_direct_mode_settings()

        #  TO verify the App Mode Setting Capabilities
        return_value.append(self.verify_recommended_app_direct_mode(dimm_app_direct_settings))

        #  Step logger start for Step 3
        self._test_content_logger.end_step_logger(3, all(return_value))

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)

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

        #  Step logger start for Step 4
        self._test_content_logger.end_step_logger(4, True)

        # Step logger start for Step 5
        self._test_content_logger.start_step_logger(5)

        # To get namespace info
        list_namespace = self._ipmctl_provider_uefi.dcpmm_get_disk_namespace()

        # To clear namespace id's if exists
        self._ipmctl_provider_uefi.dcpmm_check_disk_namespace_initilize(list_namespace)

        #  Step logger start for Step 5
        self._test_content_logger.end_step_logger(5, True)

        # Step logger start for Step 6
        self._test_content_logger.start_step_logger(6)

        #  Configure the capacity on all installed DCPMM(s) with 75% as volatile memory and the remainder as a region
        #  of "Not-Interleaved" persistent memory
        dcpmm_disk_goal = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            "ipmctl.efi create -f -goal memorymode=75 persistentmemorytype=appdirectnotinterleaved")

        dcpmm_disk_goal = ' '.join([str(elem) for elem in dcpmm_disk_goal])

        if not dcpmm_disk_goal:
            raise content_exceptions.TestFail("Failed to provision crystal ridge DIMMS with 75% Memory Mode and 25% "
                                              "Appdirect more ...")

        #  To show the goal data
        goal_info = self._ipmctl_provider_uefi.show_goal()
        self._log.info("Show DCPMM information...{}".format(goal_info))

        self._log.info("Successfully provisioned crystal ridge DIMMS as 75% Memory Mode... Rebooting to apply the "
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

        #  To confirm that this goal is with an allocation of 75% volatile memory and remaining capacity is allocated
        #  a "AppDirect" non-interleaved persistent memory
        self.verify_app_direct_mode_provisioning(mode="pmem", mode_percentage=25,
                                                 total_memory_result_data=dimm_val,
                                                 app_direct_result_data=dcpmm_disk_goal)

        #  "Memory mode" verification
        self.verify_app_direct_mode_provisioning(mode="mem", mode_percentage=75,
                                                 total_memory_result_data=dimm_val,
                                                 app_direct_result_data=dcpmm_disk_goal)

        #  Step logger start for Step 6
        self._test_content_logger.end_step_logger(6, True)

        # Step logger start for Step 7
        self._test_content_logger.start_step_logger(7)

        #  To get the memory supported values
        mem_resources_data = self._ipmctl_provider_uefi.show_mem_resources()

        self._log.debug("Memory resources info...{}".format(mem_resources_data))

        # To get normal region information
        region_data = self._ipmctl_provider_uefi.show_region()

        # To verify the region ID attribute
        return_value.append(self._memory_common_lib.verify_region_id_existence(region_data))

        # To get region information with param "-a"
        region_data_with_a_param = self._ipmctl_provider_uefi.show_all_region_data()

        # To verify the default region attributes
        self._memory_common_lib.verify_region_default_attribs_mode(region_data_with_a_param,
                                                                   mode="AppDirectNotInterleaved")

        #  To get the all region ID
        region_id_list = self.get_all_region_data_uefi(region_data_with_a_param)

        namespace_create_list = []

        for index in region_id_list:
            if index != '':
                # Namespace creation with region id after goal created
                namespace_create_list.append(self._ipmctl_provider_uefi.region_data_after_goal(index))

        #  To show the namespace created after goal
        post_namespace_creation_report = self._ipmctl_provider_uefi.get_disk_namespace_info()

        self._memory_common_lib.verify_created_namespace_params(region_id_list, post_namespace_creation_report,
                                                                namespace_create_list)

        #  Step logger start for Step 7
        self._test_content_logger.end_step_logger(7, True)

        # Step logger start for Step 8
        self._test_content_logger.start_step_logger(8)

        #  To map the device block in uefi shell after goal creation
        map_output = self.map_device_uefi()

        #  To verify the pmem block available in uefi shell
        self.verify_pmem_block_uefi(map_output)

        #  To display the region data in uefi shell
        region_data = self._ipmctl_provider_uefi.show_region()

        # To get the Persistent memory type
        region_persistent_type = self._memory_common_lib.get_region_data(region_data, 2)

        for mem_type in region_persistent_type:
            if "AppDirectNotInterleaved" not in mem_type:
                content_exceptions.TestFail("Persistent Memory type is not AppDirect on this region.. Exiting..")

        self._log.debug("Successfully verified that persistent Memory type is AppDirect on all the available regions..")

        # To get the FreeCapacity info
        region_free_capacity = self._memory_common_lib.get_region_data(region_data, 4)

        for cap_region in region_free_capacity:
            if "0 B" not in cap_region:
                content_exceptions.TestFail("This region free capacity is not '0 B'.. Exiting..")

        self._log.debug("Successfully verified that all the available regions free capacity is 0 Bytes...")

        #  Step logger start for Step 8
        self._test_content_logger.end_step_logger(8, True)

        # Step logger start for Step 9
        self._test_content_logger.start_step_logger(9)

        #  To create config csv file in USB drive
        self._ipmctl_provider_uefi.create_config_csv()

        # To keep the same boot order options, so that it will not fail to at length matching at xmlCli
        # set boot order function.
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

        sut_file_path = self._copy_usb.copy_file_from_usb_to_sut(self._common_content_lib,
                                                                 self._common_content_configuration, self.usb_file_path)
        host_file_path = self._common_content_lib.copy_log_files_to_host(self.TC_ID, str(sut_file_path), ".csv")

        #  To verify the data in csv file
        return_data = self.verify_provisioning_final_dump_data_csv(log_file_path=host_file_path)
        return_value.append(return_data)

        #  Step logger start for Step 9
        self._test_content_logger.end_step_logger(9, return_data)

        return all(return_value)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CRProvisioning2LmMixedMode75Memory25Appdirect.main()
             else Framework.TEST_RESULT_FAIL)
