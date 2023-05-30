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
import time

from dtaf_core.lib.dtaf_constants import Framework
from src.memory.tests.memory_cr.apache_pass.provisioning.cr_provisioning_common import CrProvisioningTestCommon
from src.memory.tests.memory_ddr.stress_app_test_stress import StressAppTestStress


class CRProvisioning1LM100Reserved(CrProvisioningTestCommon):
    """
    Glasgow ID: 59807
    Verification of the platform supported DCPMM capabilities in a Linux os environment.

    1. Create a persistent memory goal with 100% of available capacity provisioned in "AppDirect" mode
        as "Reserved" using Linux provisioning tools.
    2. The recommended DDR4 DRAM to Intel® Optane DC Persistent Memory volatile capacity ratio is 1:8. Ranges from 1:4
       through 1:16 are supported.
    3. This operation stores the specified goal on the DCPMM(s) for the BIOS to read on the next reboot in order to
        map the DCPMM capacity into the system address space.
    4. Command line access to DCPMM management functionality is available through the ipmctl component &
        native OS commands.
    """

    BIOS_CONFIG_FILE = "cr_provisioning_1lm_100_appdirect_reserved_bios_knobs.cfg"
    TEST_CASE_ID = "G59807"
    _ipmctl_executer_path = "/root"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new CRProvisioning2LM50AppDirect50MemoryModeLinux object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # For using the functionalists of stress test case
        self._stress_test = StressAppTestStress(test_log, arguments, cfg_opts)

        # calling base class init
        super(CRProvisioning1LM100Reserved, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)

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
        self._install_collateral.install_stress_test_app()

    def execute(self):
        """
        Function is responsible for the below tasks,
        1. It is first confirmed that the DCPMMs are capable of supporting 1LM AppDirect mode.
        2. All installed DCPMM(s) are configured with 100% of AppDirect capacity as Reserved (Inaccessible).
        3. User attempts to view regions and create a namespace for each persistent region.
        4. Expectation is that no regions are present and that namespaces cannot be created since the
            DCPMM capacity is reserved.
        5. Save DCPMM configuration data to a file.

        :return: True, if the test case is successful.
        :raise: None
        """

        return_value = []

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

        # Get the platform supported modes.
        dimm_mode = self.ipmctl_show_modes(self._ipmctl_executer_path)

        #  Verify App Direct mode capabilities
        return_value.append(self.verify_provisioning_mode(result_data=dimm_mode))

        #  To display the recommended App Direct Mode setting capabilities
        dimm_app_direct_settings = self.dcpmm_get_app_direct_mode_settings(self._ipmctl_executer_path)

        #  TO verify the App Mode Setting Capabilities
        return_value.append(self.verify_recommended_app_direct_mode(dimm_app_direct_settings))

        # Pre-existing namespaces are identified here.
        namespace_info = self.dcpmm_get_disk_namespace()

        #  Remove existing all the namespaces
        self.dcpmm_check_disk_namespace_initilize(namespace_info)

        #  Configure the capacity on all installed DCPMM(s) with 100% as AppDirect memory, designated as "Reserved".
        dcpmm_disk_goal = self.dcpmm_configuration(
            self._ipmctl_executer_path,
            cmd=r"ipmctl create -f -goal persistentmemorytype=appdirect Reserved=100",
            cmd_str="with 100% as AppDirect reserved memory")

        #  Restart the SUT
        self._os.reboot(self._reboot_timeout)

        #  Get the present memory resources
        mem_resources_output = self.ipmctl_show_mem_resources(self._ipmctl_executer_path)

        self.verify_mem_resource_provisioned_capacity(mem_resources_output)

        #  After reboot verify the mode provisioning
        return_value.append(
            self.verify_app_direct_mode_provisioning(mode="mem", mode_percentage=100,
                                                     total_memory_result_data=dimm_show,
                                                     app_direct_result_data=dcpmm_disk_goal, reserved=True))
        return_value.append(
            self.verify_app_direct_mode_provisioning(mode="pmem", mode_percentage=100,
                                                     total_memory_result_data=dimm_show,
                                                     app_direct_result_data=dcpmm_disk_goal, reserved=True))

        #  Show System Memory info
        self.show_system_memory_report_linux()

        #  Get the list of all regionX device name
        region_data_list = self.get_all_region_data_linux()

        #  Create namespace for each regionX
        self.create_namespace(region_data_list, mode="fsdax")

        #  List the present namespaces
        namespace_check = self.dcpmm_get_disk_namespace()

        if namespace_check:
            return_value.append(False)
        else:
            return_value.append(True)

        # Confirm that the DCPMMs are still healthy and manageable with the correct FW version displayed.
        #  Get the DIMM information
        self.populate_memory_dimm_information(self._ipmctl_executer_path)

        # Get the list of dimms which are healthy and log them.
        self.get_list_of_dimms_which_are_healthy()

        # Verify the list of dimms which are healthy
        self.verify_all_dcpmm_dimm_healthy()

        # Verify the list of dimms which are healthy and manageable
        self.get_list_of_dimms_which_are_healthy_and_manageable()

        # Verify the firmware version of each dimms
        self.verify_dimms_firmware_version(ipmctl_executor_path=self._ipmctl_executer_path)

        #  Show the memory and process info
        self.get_memory_process_info_linux()

        #  Show memory resources
        self.ipmctl_show_mem_resources(self._ipmctl_executer_path)

        # Shutdown the system
        if self._ac.ac_power_off():
            self._log.info("Waiting for the platform to power off completely.. ")

            while self._os.is_alive():
                self._log.info("Still waiting for the platform to power off completely..")

            self._log.info("The platform powered off completely..")
            self._log.info("After about 15 seconds, the platform will power on and will boot to OS..")
            time.sleep(15)
            if self._ac.ac_power_on():
                self._log.info("Powering on the platform..")
                self._os.wait_for_os(self._reboot_timeout)
                self._log.info("The platform is now in OS..")
            else:
                self._log.error("The platform did not power on..")
                raise SystemError("The platform did not power on..")
        else:
            self._log.error("The platform did not power off..")
            raise SystemError("The platform did not power off..")

        # Show present namespaces
        namespace_info = self.dcpmm_get_disk_namespace()

        #  Verify pmem disk are not listed
        return_value.append(self.verify_pmem_device_presence(namespace_info))

        self._stress_test.execute_installer_stressapp_test_linux()

        load_avg_value = self._stress_test.get_load_average()
        max_load_avg = self._stress_test.get_max_load_average(load_avg_value)
        self._log.info("Correct load average value {}".format(max_load_avg))
        if float(max_load_avg) >= self._stress_test.CMP_LOAD_AVERAGE_AFTER_STRESSAPP:
            self._log.info("Correct load average value...")
        else:
            log_error = "Incorrect load average value"
            self._log.error(log_error)
            raise RuntimeError(log_error)

        self._common_content_lib.create_dmesg_log()
        self._common_content_lib.create_mce_log()

        # Store the currently configured memory allocation settings for all DCPMMs in the system to a file.
        self.create_config_csv(ipmctl_path=self._ipmctl_executer_path)

        # Delete the test case id folder from our host if it is exists.
        self._common_content_lib.delete_testcaseid_folder_in_host(test_case_id=self.TEST_CASE_ID)

        # copy the configuration file to host.
        config_file_path_host = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self._ipmctl_executer_path, extension=".csv")

        # Verify the provisioned capacity matches the DCPMMs total capacity.
        return_value.append(self.verify_provisioning_final_dump_data_csv(
            log_file_path=config_file_path_host, reserved=True))

        # Get the media and Thermal error logs
        self.get_ipmctl_error_logs(self._ipmctl_executer_path, "Media", "Thermal")

        log_path_to_parse = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self._stress_test.LINUX_USR_ROOT_PATH,
            extension=".log")

        return_value.append(self._stress_test.log_parsing_stress_app_test(log_file_path=log_path_to_parse))

        return_value.append(self.verify_ipmctl_error("Media", os.path.join(log_path_to_parse,
                                                                           "Media.log")))
        return_value.append(self.verify_ipmctl_error("Thermal", os.path.join(log_path_to_parse,
                                                                             "Thermal.log")))

        return all(return_value)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if CRProvisioning1LM100Reserved.main()
             else Framework.TEST_RESULT_FAIL)
