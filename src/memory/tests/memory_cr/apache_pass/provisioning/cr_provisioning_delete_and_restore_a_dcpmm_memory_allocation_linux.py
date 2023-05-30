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
from src.memory.tests.memory_cr.apache_pass.provisioning.cr_provisioning_2lm_100_memory_mode_linux \
    import CRProvisioning2LM100MemoryModeLinux


class CRProvisioningDeleteAndRestoreDcpmmMemoryAllocationLinux(CrProvisioningTestCommon):
    """
    Glasgow ID: 55792
    Verification of the platform supported DCPMM capabilities in a Linux os environment.

    1. Overwrite a 100% memory mode provisioning on a DCPMM configuration with a 75% AppDirect configuration.
    2. Restore the previous DCPMM configuration.
    3. A combination of Memory Mode and App Direct Mode is referred to as Mixed Mode.
    4. This operation stores the specified goal on the DCPMM(s) for the BIOS to read on the next reboot in order to
       map the DCPMM capacity into the system address space.
    5. Command line access to DCPMM management functionality is available through the ipmctl component & native OS
    commands.
    """

    BIOS_CONFIG_FILE = "cr_provisioning_delete_and_restore_a_dcpmm_memory_allocation_linux.cfg"
    TEST_CASE_ID = "G55792"
    _ipmctl_executer_path = "/root"
    MEMORY_CONFIG_FILE_NAME = "2LMcfg.csv"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new CRProvisioning2LM50AppDirect50MemoryModeLinux object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(CRProvisioningDeleteAndRestoreDcpmmMemoryAllocationLinux, self).__init__(test_log,
                                                                                       arguments, cfg_opts,
                                                                                       self.BIOS_CONFIG_FILE)

        # calling CRProvisioning2LM100MemoryModeLinux of Glasgow ID : 57092
        self._cr_provisioning_2lm_memory_mode = CRProvisioning2LM100MemoryModeLinux(self._log,
                                                                                    arguments, cfg_opts)
        self._log.info("Start of 2LM 100% Memory Mode Linux Provisioning TestCase. [Glasgow ID : 57092]")
        self._cr_provisioning_2lm_memory_mode.prepare()
        self._cr_provisioning_2lm_memory_mode.execute()
        self._log.info("End of 2LM 100% Memory Mode Linux Provisioning TestCase. [Glasgow ID : 57092]")

    def prepare(self):
        # type: () -> None
        """
        1. Set the bios knobs to its default mode.
        2. Set the bios knobs as per the test case.
        3. Reboot the SUT to apply the new bios settings.
        4. Verify the bios knobs that are set.

        :return: None
        """
        self._common_content_lib.clear_os_log()  # TO clear Os logs
        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._os.reboot(int(self._reboot_timeout))  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. It is first confirmed that the DCPMMs are capable of supporting Memory mode with 2LM enabled.
        2. Create a 2LM mixed mode goal with persistent memory, 75% AppDirect & 25% Memory Mode.
        3. Confirm persistent memory regions are configured as expected.
        4. Restore the previous DCPMM configuration.
        5. Confirm persistent memory regions are configured as expected.

        :return: True, if the test case is successful.
        :raise: None
        """
        return_value = []

        #  Show System Memory info
        self.show_system_memory_report_linux()

        #  Get the DIMM information
        dimm_show = self.populate_memory_dimm_information(self._ipmctl_executer_path)

        # Get the platform supported modes.
        dimm_mode = self.ipmctl_show_modes(self._ipmctl_executer_path)

        #  Verify App Direct mode capabilities
        return_value.append(self.verify_provisioning_mode(result_data=dimm_mode))

        #  To display the recommended App Direct Mode setting capabilities
        dimm_app_direct_settings = self.dcpmm_get_app_direct_mode_settings(self._ipmctl_executer_path)

        #  TO verify the App Mode Setting Capabilities
        return_value.append(self.verify_recommended_app_direct_mode(dimm_app_direct_settings))

        # Pre-existing namespaces are identified here.
        self.dcpmm_get_disk_namespace()

        # Dump data current memory provision configuration
        self.dump_provisioning_data(self.MEMORY_CONFIG_FILE_NAME, self._ipmctl_executer_path)

        #  Configure the capacity on all installed DCPMM(s) with 25% as volatile memory and the remainder as a region
        #  of persistent memory
        dcpmm_disk_goal = self.dcpmm_configuration(
            self._ipmctl_executer_path,
            cmd=r"ipmctl create -f -goal  memorymode=25 persistentmemorytype=appdirect",
            cmd_str="with 75% as volatile memory and remainder as persistent memory")

        #  Verify the mode provisioning
        return_value.append(
            self.verify_app_direct_mode_provisioning(mode="pmem", mode_percentage=75,
                                                     total_memory_result_data=dimm_show,
                                                     app_direct_result_data=dcpmm_disk_goal))

        #  Restart the SUT
        self._os.reboot(self._reboot_timeout)

        #  Show System Memory info
        system_memory_data = self.show_system_memory_report_linux()

        #  Verify 2LM provisioning mode
        return_value.append(self.verify_lm_provisioning_configuration_linux(dcpmm_disk_goal, system_memory_data,
                                                                            mode="2LM"))

        #  Get the present memory resources
        self.ipmctl_show_mem_resources(self._ipmctl_executer_path)

        #  Get the list of all regionX device name
        self.get_all_region_data_linux()

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

        # Restore the Memory allocation Settings
        new_dcpmm_disk_goal = self.restore_memory_allocation_settings(self.MEMORY_CONFIG_FILE_NAME,
                                                                      self._ipmctl_executer_path)

        #  Get the DIMM information
        dimm_show = self.populate_memory_dimm_information(self._ipmctl_executer_path)

        # Verify the goal is displayed showing 100% of the DCPMM capacity is configured as Volatile memory.
        return_value.append(self.verify_app_direct_mode_provisioning(mode="mem",
                                                                     mode_percentage=100,
                                                                     total_memory_result_data=dimm_show,
                                                                     app_direct_result_data=new_dcpmm_disk_goal))

        #  Restart the SUT
        self._os.reboot(self._reboot_timeout)

        #  Get the DIMM information
        dimm_show = self.populate_memory_dimm_information(self._ipmctl_executer_path)

        #  Get the present memory resources
        self.ipmctl_show_mem_resources(self._ipmctl_executer_path)

        # Verify the goal is displayed showing 100% of the DCPMM capacity is configured as Volatile memory.
        return_value.append(self.verify_app_direct_mode_provisioning(mode="mem",
                                                                     mode_percentage=100,
                                                                     total_memory_result_data=dimm_show,
                                                                     app_direct_result_data=new_dcpmm_disk_goal))
        #  Show System Memory info
        system_memory_data = self.show_system_memory_report_linux()

        #  Verify 2LM provisioning mode
        return_value.append(self.verify_lm_provisioning_configuration_linux(new_dcpmm_disk_goal, system_memory_data,
                                                                            mode="2LM"))

        return all(return_value)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CRProvisioningDeleteAndRestoreDcpmmMemoryAllocationLinux.main()
             else Framework.TEST_RESULT_FAIL)
