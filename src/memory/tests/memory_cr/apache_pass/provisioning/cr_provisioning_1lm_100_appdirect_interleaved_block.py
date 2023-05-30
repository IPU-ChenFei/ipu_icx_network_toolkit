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
from src.memory.tests.memory_cr.apache_pass.provisioning.cr_provisioning_common import CrProvisioningTestCommon


class CRProvisioning1LM100AppDirectInterLeavedBlockLinux(CrProvisioningTestCommon):
    """
    Glasgow ID: 57624
    Verification of the platform supported DCPMM capabilities in a Linux os environment.

    1. Create a 1LM with persistent memory, interleaved capacity.
    """

    BIOS_CONFIG_FILE = "cr_provisioning_1lm_100_appdirect_interleaved_block.cfg"
    TEST_CASE_ID = "G57624"
    CREAT_APP_DIRECT = r"ipmctl create -f -goal persistentmemorytype=appdirect"
    _ipmctl_executer_path = "/root"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new CRProvisioning1LM100AppDirectInterLeavedBlockLinux object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(CRProvisioning1LM100AppDirectInterLeavedBlockLinux, self).__init__(test_log,
                                                                                 arguments, cfg_opts,
                                                                                 self.BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Clear Os Log
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs that are set.

        :return: None
        """
        self._common_content_lib.clear_all_os_error_logs()  # To clear Os logs
        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._os.reboot(int(self._reboot_timeout))  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. It is first confirmed that the DCPMMs are capable of supporting AppDirect mode with 2LM enabled.
        2. Create a 1LM persistent memory, interleaved block capacity.
        3. Confirm persistent memory regions are configured as expected.
        4. Create namespaces for the persistent regions.
        5. Verify namespaces and region status.
        6. Save DCPMM configuration data to a file.

        :return: True, if the test case is successful.
        :raise: None
        """
        return_value = []
        #  Show System Memory info
        self.show_system_memory_report_linux()

        #  Get the DIMM information
        dimm_show = self._ipmctl_provider.get_memory_dimm_information()

        # Get the list of dimms which are healthy and log them.
        self._ipmctl_provider.get_list_of_dimms_which_are_healthy_and_manageable()

        # Verify the list of dimms which are healthy
        self._ipmctl_provider.verify_all_dcpmm_dimm_healthy()

        # Verify the firmware version of each dimms
        self._ipmctl_provider.verify_dimms_firmware_version()

        # Verify the device location of each dimms
        self._ipmctl_provider.verify_dimms_device_locator()

        # Get the platform supported modes.
        dimm_mode = self._ipmctl_provider.ipmctl_show_modes()

        # Verify App Direct mode capabilities
        return_value.append(self.verify_provisioning_mode(result_data=dimm_mode))

        #  To display the recommended App Direct Mode setting capabilities
        dimm_app_direct_settings = self.dcpmm_get_app_direct_mode_settings(self._ipmctl_executer_path)

        #  TO verify the App Mode Setting Capabilities
        return_value.append(self.verify_recommended_app_direct_mode_for_1lm(dimm_app_direct_settings))

        # Pre-existing namespaces are identified here.
        namespace_info = self._ipmctl_provider.dcpmm_get_disk_namespace()

        # Remove all existing namespaces
        self._ipmctl_provider.dcpmm_check_disk_namespace_initilize(namespace_info)

        dcpmm_disk_goal = self._ipmctl_provider.dcpmm_configuration(
            cmd=self.CREAT_APP_DIRECT,
            cmd_str="with 100% as persistent memory")

        #  Verify the mode provisioning
        return_value.append(
            self.verify_app_direct_mode_provisioning(mode="pmem", mode_percentage=100,
                                                     total_memory_result_data=dimm_show,
                                                     app_direct_result_data=dcpmm_disk_goal))

        self._os.reboot(int(self._reboot_timeout))
        self._os.wait_for_os(self._reboot_timeout)

        #  Show System Memory info
        self.show_system_memory_report_linux()

        #  Get the present memory resources
        self.ipmctl_show_mem_resources(self._ipmctl_executer_path)

        #  After reboot verify the mode provisioning
        return_value.append(self.verify_app_direct_mode_provisioning(mode="pmem", mode_percentage=100,
                                                                     total_memory_result_data=dimm_show,
                                                                     app_direct_result_data=dcpmm_disk_goal))

        #  Show System Memory info
        self.show_system_memory_report_linux()

        #  Get the list of all regionX device name
        region_data_list = self.get_all_region_data_linux()

        #  Create namespace for each regionX
        new_created_namespace_list = self.create_namespace(region_data_list)

        #  List the present namespaces
        self.dcpmm_get_disk_namespace()

        #  Show block creation
        show_pmem_block_info = self.show_pmem_block_info()

        #  Verify block creation
        return_value.append(self.verify_pmem_block_info(show_pmem_block_info, new_created_namespace_list))

        #  Get the DIMM information
        self._ipmctl_provider.get_memory_dimm_information()

        # Get the list of dimms which are healthy and log them.
        self._ipmctl_provider.get_list_of_dimms_which_are_healthy_and_manageable()

        # Verify the list of dimms which are healthy
        self._ipmctl_provider.verify_all_dcpmm_dimm_healthy()

        # Verify the firmware version of each dimms
        self._ipmctl_provider.verify_dimms_firmware_version()

        # Verify the device location of each dimms
        self._ipmctl_provider.verify_dimms_device_locator()

        #  Show the memory and process info
        self.get_memory_process_info_linux()

        #  Show memory resources
        self.ipmctl_show_mem_resources(self._ipmctl_executer_path)

        # Show present namespaces
        namespace_info = self.dcpmm_get_disk_namespace()

        #  Verify namespace presence
        return_value.append(self.verify_pmem_device_presence(namespace_info))

        #  To partition the disks
        self.disk_partition_linux(new_created_namespace_list)

        #  Create an ext4 Linux file system on each enumerated PM blockdev device
        self.create_ext4_filesystem(new_created_namespace_list)

        #  Create mount point on each PM blockdev device
        self.create_mount_point(new_created_namespace_list)

        #  Verify mount is successful or not
        return_value.append(self.verify_mount_point(new_created_namespace_list))

        #  Verify disk partition
        return_value.append(self.verify_device_partitions(new_created_namespace_list))

        #  Reboot the System
        self._os.reboot(int(self._reboot_timeout))

        #  Show pmem block info
        block_info = self.show_pmem_block_info()

        #  Verify pmem block info
        return_value.append(self.verify_pmem_block_info(block_info, new_created_namespace_list))

        #  To get the DCPMM disk namespaces information
        namespace_info = self.dcpmm_get_disk_namespace()

        #  Verify namespace presence
        return_value.append(self.verify_pmem_device_presence(namespace_info))

        # Store the currently configured memory allocation settings for all DCPMMs in the system to a file.
        self.create_config_csv(ipmctl_path=self._ipmctl_executer_path)

        # Delete the test case id folder from our host if it is exists.
        self._common_content_lib.delete_testcaseid_folder_in_host(test_case_id=self.TEST_CASE_ID)

        # copy the configuration file to host.
        config_file_path_host = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self._ipmctl_executer_path, extension=".csv")

        # Verify the provisioned capacity matches the DCPMMs total capacity.
        return_value.append(self.verify_provisioning_final_dump_data_csv(
            log_file_path=config_file_path_host))

        return all(return_value)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CRProvisioning1LM100AppDirectInterLeavedBlockLinux.main()
             else Framework.TEST_RESULT_FAIL)
