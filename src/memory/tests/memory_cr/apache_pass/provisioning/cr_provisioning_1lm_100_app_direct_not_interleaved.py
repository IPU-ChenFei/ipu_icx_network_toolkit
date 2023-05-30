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


class CRProvisioning1LM100AppDirect(CrProvisioningTestCommon):
    """
    Glasgow ID: 57741
    Verification of the platform supported DCPMM capabilities in a Microsoft Windows OS environment.

    1. Create an explicit 100% App Direct goal with persistent memory AppDirect not interleaved capacity in 1LM mode.
    2. All DCPMMs will be provisioned as 100% persistent memory.
    3. Validate the persistent memory region(s) represents not interleaved AppDirect persistent memory and correct
    namespace sizes.
    3. This operation stores the specified goal on the DCPMM(s) for the BIOS to read on the next reboot in order to
    map the DCPMM capacity into the system address space.
    4. Command line access to the DIMM management functionality is available through the ipmctl component & native OS
    commands.
    """

    BIOS_CONFIG_FILE = "cr_provisioning_1lm_100_app_direct_bios_knobs.cfg"
    TEST_CASE_ID = "G57741"

    _ipmctl_executer_path = None

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new CRProvisioning1LM100AppDirect object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(CRProvisioning1LM100AppDirect, self).__init__(test_log,
                                                            arguments, cfg_opts,
                                                            self.BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Set the bios knobs to its default mode.
        2. Set the bios knobs as per the test case.
        3. Reboot the SUT to apply the new bios settings.
        4. Verify the bios knobs that are set.
        5. Copy ipmctl tool to windows SUT.
        6. Unzip file under home folder.

        :return: None
        """
        self._common_content_lib.clear_all_os_error_logs()  # To clear Os logs
        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.
        self._ipmctl_executer_path = self._install_collateral.install_ipmctl()

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. It is first confirmed that the DCPMMs are capable of supporting AppDirect mode with 1LM enabled.
        2. Create a 1LM mixed mode goal with persistent memory, 100% AppDirect not interleaved block capacity.
        3. All installed DCPMM(s) are configured with regions of persistent memory.
        4. A namespace is created for each x1 interleave set, with a filesystem for each namespace.
        5. Verify namespaces and region status.
        6. Save DCPMM configuration data to a file.

        :return: True, if the test case is successful.
        :raise: None
        """
        return_value = []

        # Creating a data frame with dimm information and adding extra columns as per our test case need.
        dimm_show = self.populate_memory_dimm_information(self._ipmctl_executer_path)

        # Get the list of dimms which are healthy and log them.
        self.get_list_of_dimms_which_are_healthy()

        # Verify the list of dimms which are healthy are matching with the pmem disk output.
        self.verify_all_dcpmm_dimm_healthy()

        # Verify the firmware version of each dimms are matching with the pmem disk output.
        self.verify_dimms_firmware_version()

        # Verify the device location of each dimms are matching with the pmem disk output.
        self.verify_dimms_device_locator()

        #  Show App Direct mode capabilities
        dimm_mode = self.ipmctl_show_modes(self._ipmctl_executer_path)

        #  Verify App Direct mode capabilities
        return_value.append(self.verify_provisioning_mode(result_data=dimm_mode))

        #  To display the recommended App Direct Moe setting capabilities
        dimm_app_direct_settings = self.dcpmm_get_app_direct_mode_settings(self._ipmctl_executer_path)

        #  TO verify the App Mode Setting Capabilities
        return_value.append(self.verify_recommended_app_direct_mode(dimm_app_direct_settings))

        #  Get Namespace info
        namespace_info = self.dcpmm_get_disk_namespace()

        #  To initialize the DIMMs and remove all existing namespaces
        self.dcpmm_check_disk_namespace_initilize(namespace_info)

        #  Configure the capacity on all installed DCPMM(s) with 100% as volatile memory "Not-Interleaved"
        #  persistent memory
        dcpmm_disk_goal = self.dcpmm_configuration(
            self._ipmctl_executer_path,
            cmd=r".\ipmctl.exe create -f -goal persistentmemorytype=appdirectnotinterleaved",
            cmd_str="with 100% as App Direct mode")

        # Verify the goal is displayed showing 100% of the DCPMM capacity is configured as persistent memory.
        return_value.append(
            self.verify_app_direct_mode_provisioning(mode="pmem",
                                                     mode_percentage=100,
                                                     total_memory_result_data=dimm_show,
                                                     app_direct_result_data=dcpmm_disk_goal))

        self._os.reboot(self._reboot_timeout)

        # Get the latest memory information about the DCPMMs after goal creation.
        self.ipmctl_show_mem_resources(self._ipmctl_executer_path)

        # Verify the goal is displayed showing 100% of the DCPMM capacity is configured as persistent memory.
        return_value.append(
            self.verify_app_direct_mode_provisioning(mode="pmem",
                                                     mode_percentage=100,
                                                     total_memory_result_data=dimm_show,
                                                     app_direct_result_data=dcpmm_disk_goal))
        # Get the latest list the persistent memory information after goal creation.
        self.dcpmm_get_pmem_device_fl_info()

        # Configure all available pmem devices with namespaces.
        self.dcpmm_new_pmem_disk()

        self._os.reboot(self._reboot_timeout)

        # Get the list of just created namespaces.
        self.dcpmm_get_disk_namespace()

        # To get the list of DCPMM disks.
        disk_list = self.get_dcpmm_disk_list()

        self._log.info("{} DCPMM device(s) attached to this system board {}.".format(len(disk_list), disk_list))

        # create the new DCPMM disk partitions.
        return_value.append(self.create_partition_dcpmm_disk(convert_type="mbr", disk_lists=disk_list))

        # Get the list of just created namespaces.
        self.dcpmm_get_disk_namespace()

        # Store the currently configured memory allocation settings for all DCPMMs in the system to a file.
        self.create_config_csv(ipmctl_path=self._ipmctl_executer_path)

        # Delete the test case id folder from our host if it is exists.
        self._common_content_lib.delete_testcaseid_folder_in_host(test_case_id=self.TEST_CASE_ID)

        # copy the configuration file to host.
        config_file_path_host = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self._ipmctl_executer_path,
            extension=".csv")

        # Verify the provisioned capacity matches the DCPMMs total capacity.
        return_value.append(self.verify_provisioning_final_dump_data_csv(log_file_path=config_file_path_host))

        # verify the new DCPMM disk partitions for healthy and showing correct drive letters.
        return_value.append(self.verify_disk_partition(disk_lists=disk_list))

        return all(return_value)


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if CRProvisioning1LM100AppDirect.main() else Framework.TEST_RESULT_FAIL)
