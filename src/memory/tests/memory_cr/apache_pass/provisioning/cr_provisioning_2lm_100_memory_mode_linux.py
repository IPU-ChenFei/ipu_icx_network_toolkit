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
from src.lib.test_content_logger import TestContentLogger
from src.memory.tests.memory_cr.apache_pass.provisioning.cr_provisioning_common import CrProvisioningTestCommon


class CRProvisioning2LM100MemoryModeLinux(CrProvisioningTestCommon):
    """
    Glasgow ID: 57092
    Verification of the platform supported DCPMM capabilities in a Linux OS environment.

    1. Create DCPMMs in 2LM Memory Mode 100% mode.
    2. Two-level memory (2LM) hierarchical memory model with DCPMM is referred to as Memory Mode.
    3. The DCPMM configured volatile memory acts as the second tier which provides large memory capacities.
    4. Confirm all existing Namespaces are removed and the entire memory configuration is configured as 2LM memory.
    """

    BIOS_CONFIG_FILE = "cr_provision_2lm_memory_mode_100_bios_knobs.cfg"
    TEST_CASE_ID = "G57092"

    _ipmctl_executer_path = "/root"

    step_data_dict = {1: {'step_details': 'Clear OS logs and Set & Verify BIOS knobs', 'expected_results':
                          'Clear ALL the system Os logs and BIOS setup options are updated with changes saved'},
                      2: {'step_details': 'Run Os commands to get System Memory details and IPMCTL commands to get '
                                          'DIMMS status',
                          'expected_results': 'System Memory should reported correctly and DIMMs status '
                                              'also reported successfully'},
                      3: {'step_details': 'Initialize NameSpaces, Create a goal of 100% Memory Mode and Restart the '
                                          'SUT',
                          'expected_results': 'Successfully initialize namespace, ran the command to created a goal of '
                                              '100% Memory mode and restart the SUT'},
                      4: {'step_details': 'Run Os commands to get System Memory details and IPMCTL command to get '
                                          'memory resources',
                          'expected_results': 'The total usable DCPMM memory resource allocation across the SUT is '
                                              'displayed and Verify that total memory is +/-5% of DCPMM capacity'},
                      5: {'step_details': 'Store the memory allocation settings for all DCPMMs in the system to a '
                                          'file for later use',
                          'expected_results': 'Successfully The currently configured DCPMM allocation settings are '
                                              'saved to a file and The file contents are as expected'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new CRProvisioning2LM100MemoryModeLinux object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(CRProvisioning2LM100MemoryModeLinux, self).__init__(test_log,
                                                                  arguments, cfg_opts,
                                                                  self.BIOS_CONFIG_FILE)
        #  Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self.dcpmm_disk_goal = None

    def prepare(self):
        # type: () -> None
        """
        1. Setting the bios knobs to its default mode.
        2. Setting the bios knobs as per the test case.
        3. Rebooting the SUT to apply the new bios settings.
        4. Verifying the bios knobs that are set.

        :return: None
        """

        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        self._common_content_lib.clear_os_log()  # TO clear Os logs
        self._bios_util.load_bios_defaults()  # To set the Bios Knobs to its default mode.
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.
        #  Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. It is first confirmed that the DCPMMs are capable of supporting Memory mode with 2LM enabled.
        2. All installed DCPMM(s) are configured with 100% of capacity as volatile memory.
        4. Create namespaces for the memory regions.
        5. Verify namespaces and region status.
        6. Save DCPMM configuration data to a file.

        :return: True, if the test case is successful.
        :raise: None
        """
        return_value = []

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        #  Show System Memory info
        self.show_system_memory_report_linux()

        #  Get the DIMM information
        dimm_show = self.populate_memory_dimm_information(self._ipmctl_executer_path)

        # Get the list of dimms which are healthy and log them.
        self.get_list_of_dimms_which_are_healthy()

        # Verify the list of dimms which are healthy
        self.verify_all_dcpmm_dimm_healthy()

        # Verify the firmware version of each dimms
        self.verify_dimms_firmware_version(ipmctl_executor_path=self._ipmctl_executer_path)

        # Verify the device location of each dimms
        self.verify_dimms_device_locator(ipmctl_executor_path=self._ipmctl_executer_path)

        # Get the platform supported modes.
        dimm_mode = self.ipmctl_show_modes(self._ipmctl_executer_path)

        #  Verify App Direct mode capabilities
        return_value.append(self.verify_provisioning_mode(result_data=dimm_mode))

        #  To display the recommended App Direct Mode setting capabilities
        dimm_app_direct_settings = self.dcpmm_get_app_direct_mode_settings(self._ipmctl_executer_path)

        #  TO verify the App Mode Setting Capabilities
        verify_mode_status = self.verify_recommended_app_direct_mode(dimm_app_direct_settings)
        return_value.append(verify_mode_status)

        # Step Logger end for Step 2
        self._test_content_logger.end_step_logger(2, verify_mode_status)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)

        # Pre-existing namespaces are identified here.
        namespace_info = self.dcpmm_get_disk_namespace()

        #  Remove existing all the namespaces
        self.dcpmm_check_disk_namespace_initilize(namespace_info)

        # Configure all capacity on the installed DCPMM(s) with 100% as volatile memory.
        self.dcpmm_disk_goal = self.dcpmm_configuration(
            self._ipmctl_executer_path, cmd=r"ipmctl create -f -goal memorymode=100", cmd_str="with 100% as "
            "volatile memory")
        self._os.reboot(self._reboot_timeout)

        # Step Logger end for Step 3
        self._test_content_logger.end_step_logger(3, self.dcpmm_disk_goal)

        # Step Logger start for Step 4
        self._test_content_logger.start_step_logger(4)

        # Verify the goal is displayed showing 100% of the DCPMM capacity is configured as Volatile memory.
        return_value.append(self.verify_app_direct_mode_provisioning(mode="mem",
                                                                     mode_percentage=100,
                                                                     total_memory_result_data=dimm_show,
                                                                     app_direct_result_data=self.dcpmm_disk_goal))
        #  Show System Memory info
        system_memory_data = self.show_system_memory_report_linux()

        #  Verify 2LM provisioning mode
        verify_provisioning_status = self.verify_lm_provisioning_configuration_linux(self.dcpmm_disk_goal,
                                                                                     system_memory_data, mode="2LM")

        # Step Logger end for Step 4
        self._test_content_logger.end_step_logger(4, verify_provisioning_status)

        # Step Logger start for Step 5
        self._test_content_logger.start_step_logger(5)

        # Store the currently configured memory allocation settings for all DCPMMs in the system to a file.
        self.create_config_csv(ipmctl_path=self._ipmctl_executer_path)

        # Delete the test case id folder from our host if it is exists.
        self._common_content_lib.delete_testcaseid_folder_in_host(test_case_id=self.TEST_CASE_ID)

        # copy the configuration file to host.
        config_file_path_host = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self._ipmctl_executer_path, extension=".csv")

        # Verify the provisioned capacity matches the DCPMMs total capacity.
        return_data = self.verify_provisioning_final_dump_data_csv(log_file_path=config_file_path_host)
        return_value.append(return_data)

        # Step Logger end for Step 5
        self._test_content_logger.end_step_logger(5, return_data)

        return all(return_value)


if __name__ == "__main__":
    sys.exit(
        Framework.TEST_RESULT_PASS if CRProvisioning2LM100MemoryModeLinux.main() else Framework.TEST_RESULT_FAIL)
