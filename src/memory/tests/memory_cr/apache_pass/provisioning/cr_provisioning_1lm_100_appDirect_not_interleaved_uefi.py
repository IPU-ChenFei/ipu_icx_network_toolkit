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
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.common_content_lib import CommonContentLib
from src.provider.copy_usb_provider import UsbRemovableDriveProvider
from src.lib.content_configuration import ContentConfiguration
from src.lib.test_content_logger import TestContentLogger
from src.memory.tests.memory_cr.apache_pass.provisioning.cr_provisioning_common import CrProvisioningTestCommon


class CRProvisioningAppdirectNotInterleavedUefi(CrProvisioningTestCommon):
    """
    Glasgow ID : 55800
    Verification of the platform supported DCPMM capabilities in a UEFI environment.

    1. Create an explicit 100% App Direct namespace with all persistent memory AppDirect interleaved capacity in
    1LM mode.
    2. DCPMMs will be provisioned as 100% persistent memory
    3. Command line access to the DIMM management functionality is available through the ipmctl component & uefi
    commands.
    """

    BIOS_CONFIG_FILE = "cr_provisioning_1lm_100_appdirect_not_interleaved_uefi.cfg"
    TEST_ID = "G55800"
    IPMCTL_TXT_FILE = "ipmctl_efi.zip"
    DELAY_TIME = 10.0

    step_data_dict = {1: {'step_details': 'Copy ipmctl efi file from host to sut and sut to usb',
                          'expected_results':' ipmct.efi file copied from host to usb'},
                      2: {'step_details': 'Set & Verify BIOS knobs',
                          'expected_results':' BIOS setup options are updated with changes saved'},
                      3: {'step_details': 'Boot to the UEFI shell and App Direct Mode capabilities are as displayed '
                                          'for 1LM AppDirectprovisioning with dimm info, FW version and capacity',
                          'expected_results': 'The modes supported include 1LM and AppDirect DIMMs are listed with IDs'
                                              'and Dimms capacity and are healthy and correctFW Version is displayed'},
                      4: {'step_details': 'Display the recommended App Direct Mode setting capabilities  namespaces '
                                          'are listed and display the namespace and  existing namespace delete ',
                          'expected_results': 'App Direct interleave settings are displayed as format '
                                              'x[Way] - [(IMCSize) iMC x (ChannelSize) Channel] and Existing '
                                              'namespaces are identified and deleted '},
                      5: {'step_details': 'Create goal of 100% Memory mode and restart the SUT ',
                          'expected_results': 'Ran the command to created a goal of 100% Appdirect mode and ' 
                                              'restart the SUT'},
                      6: {'step_details': 'After SUT restated the goal was applied and display the  region ',
                          'expected_results': 'Goal applied 100% Memory mode and goal displayed  '},
                      7: {'step_details': 'Enter to uefi shell and show all the attributes for the newly created '
                                          'namespace, pmem block, device is available in the UEFI shell',
                          'expected_results': 'Namespaces are listed as NamespaceID, Capacity, HealthState and '
                                              'verified pmem block available uefi shell  '},
                      8: {'step_details': 'Store the memory allocation settings for all DCPMMs in the system to a '
                                          'file for later use',
                          'expected_results': 'Successfully The currently configured DCPMM allocation settings are '
                                              'saved to a file and The file contents are as expected'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new CRProvisioning1LM100AppDirectInterleaved .

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        super(
            CRProvisioningAppdirectNotInterleavedUefi,
            self).__init__(
            test_log,
            arguments,
            cfg_opts,
            self.BIOS_CONFIG_FILE)
        #  Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_ID, self.step_data_dict)
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._command_timeout = self._common_content_configuration.get_command_timeout()
        self._copy_usb = UsbRemovableDriveProvider.factory(test_log, cfg_opts, self._os)
        _opt_obj, _test_log_obj = cfg_opts, test_log
        self.usb_file_path = None
        self.sut_os = self._os.os_type

    def prepare(self):
        # type: () -> None
        """
        1. Set the bios knobs to its default mode.
        2. Set the bios knobs as per the test case.
        3. Reboot the SUT to apply the new bios settings.
        4. Verify the bios knobs that are set.

        :return: None
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)

        #  To copy ipmctl.efi file from host to usb
        if (OperatingSystems.WINDOWS or OperatingSystems.LINUX) == self.sut_os:
            zip_file_path = self._install_collateral.download_and_copy_zip_to_sut(self.IPMCTL_TXT_FILE.split(".")[0],
                                                                          self.IPMCTL_TXT_FILE)
            self.usb_file_path = self._copy_usb.copy_file_from_sut_to_usb(
                self._common_content_lib, self._common_content_configuration, zip_file_path)

        else:
            self._log.error("Ipmctl efi is not supported on OS '%s'" % self._os.sut_os)
            raise NotImplementedError("Ipmctl efi is not supported on OS '%s'" % self._os.sut_os)

        #  Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

        #  Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self._bios_util.set_bios_knob()  # To set the bios knob setting.z
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.

        #  Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. It is first confirmed that the DCPMMs are capable of supporting AppDirect mode with 1LM enabled.
        2. All installed DCPMM(s) are configured with 100% AppDirect mode
        3. Delete the existing namespaces.
        5. Create namespaces for the persistent regions.
        6. Verify namespaces and region status.
        7. Save DCPMM configuration data to a file.

        :return: True, if the test case is successful.
        :raise: None
        """
        return_value = []

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        #  To enter uefi shell
        self.create_uefi_obj(self._opt_obj, self._test_log_obj)
        if not self._uefi_util_obj.enter_uefi_shell():
            raise RuntimeError("SUT did not enter to UEFI Internal Shell")
        time.sleep(self.DELAY_TIME)

        # Get usb list drive from  uefi shell
        usb_drive_list = self._uefi_util_obj.get_usb_uefi_drive_list()
        self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(usb_drive_list[0])

        #  To Run mode supported capabilities
        mode_support_return_value = self.get_supported_modes_uefi()

        #  Verifying 1LM mode support values and App direct mode
        self.verify_provisioning_mode(mode_support_return_value)

        #  To run provisioning dimm command
        dimm_val = self.get_dimm_info_uefi()

        #  Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, dimm_val)

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)

        # To Run recommended app direct command in uefi shell
        app_direct = self.get_app_direct_settings_uefi()

        #  To verify "x[Way] - [(IMCSize) iMC x (ChannelSize) Channel
        self.verify_recommended_app_direct_mode(app_direct)

        #  To Run namespace command in uefi shell
        list_namespace = self.get_namespace_ipmctl_uefi()

        # To clear namespace id's if exists in system
        for index in list_namespace:
            if index != '':
                self.clear_namespace_uefi(index)
                self._log.info("DCPMM disk namespace Initialization started... {}".format(index))
            else:
                self._log.info("There are no existing namespaces, continue to configure the installed DCPMM(s)..")

        #  Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=True)

        # Step logger start for Step 5
        self._test_content_logger.start_step_logger(5)

        #  To create goal for to Configure all the DCPMM capacity as AppDirect with the attributes
        dcpmm_disk_goal = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.CREATE_GOAL_COMMAND)
        dcpmm_disk_goal = ' '.join([str(elem) for elem in dcpmm_disk_goal])
        if not dcpmm_disk_goal:
            error_msg = "Failed to create goal Appdirect "
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully created goal Appdirect...")

        #  Step logger end for Step 5
        self._test_content_logger.end_step_logger(5, dcpmm_disk_goal)

        # Step logger start for Step 6
        self._test_content_logger.start_step_logger(6)

        #  To show the goal data
        goal_info = self.show_goal_uefi()
        self._log.info("DCPMM show information...{}".format(goal_info))

        #  To confirm that this goal is 100% AppDirect Not Interleaved (x1) capacity
        self.verify_app_direct_mode_provisioning(mode="pmem", mode_percentage=100,
                                                 total_memory_result_data=dimm_val,
                                                 app_direct_result_data=dcpmm_disk_goal)

        #  To reboot the system
        self._uefi_obj.warm_reset()

        #  Step logger end for Step 6
        self._test_content_logger.end_step_logger(6, return_val=True)

        # Step logger start for Step 7
        self._test_content_logger.start_step_logger(7)

        #  To enter UEFI shell
        if not self._uefi_util_obj.enter_uefi_shell():
            raise RuntimeError("SUT did not enter to UEFI Internal Shell")
        time.sleep(self.DELAY_TIME)

        # Get usb list drive from  uefi shell
        usb_drive_list = self._uefi_util_obj.get_usb_uefi_drive_list()
        self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(usb_drive_list[0])

        # To get the memory supported values
        mem_support_val = self.show_memory_support()
        mem_support_val = '\n'.join(map(str, mem_support_val))
        self._log.info("Memory supporting  info...{}".format(mem_support_val))
        region_data = self.show_region_data_uefi()

        #  To get the all region data
        get_region_data = self.get_all_region_data_uefi(region_data)
        for index in get_region_data:
            if index != '':
                # Namespace creation with region id after goal created
                self.region_data_after_goal_uefi(index)
                self.get_namespace_ipmctl_uefi()
                map_output = self.map_device_uefi()
                self.verify_pmem_block_uefi(map_output)
                self.show_region_data_uefi()

        mem_support_val = self.show_memory_support()
        mem_support_val = '\n'.join(map(str, mem_support_val))
        self._log.info("Memory supporting  info...{}".format(mem_support_val))

        #  Step logger end for Step 7
        self._test_content_logger.end_step_logger(7, mem_support_val)

        # Step logger start for Step 8
        self._test_content_logger.start_step_logger(8)

        #  To create config csv file in usb drive
        self.config_csv_data()

        #  To reboot the system
        self._uefi_obj.warm_reset()
        time.sleep(self._reboot_timeout)
        self._log.info("Waiting for system to reboot...")

        if not self._os.is_alive():
            log_error = "SUT did not come to OS within {} seconds after a reboot from UEFI shell...".format(
                self._reboot_timeout)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        self._log.info("SUT came to OS after a reboot from UEFI shell")
        sut_file_path = self._copy_usb.copy_file_from_usb_to_sut(self._common_content_lib,
                                                                 self._common_content_configuration, self.usb_file_path)
        host_file_path = self._common_content_lib.copy_log_files_to_host(self.TEST_ID, str(sut_file_path), ".csv")

        #  To verify the data in csv file
        return_data = self.verify_provisioning_final_dump_data_csv(log_file_path=host_file_path)
        return_value.append(return_data)

        # Step Logger end for Step 8
        self._test_content_logger.end_step_logger(8, return_data)

        return all(return_value)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CRProvisioningAppdirectNotInterleavedUefi.main()
             else Framework.TEST_RESULT_FAIL)
