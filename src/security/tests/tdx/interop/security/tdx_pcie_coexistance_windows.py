#!/usr/bin/env python
##########################################################################
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
##########################################################################
"""
    :TD Guest can work with  NVME storage devices.

    :TD Guest can do data transfer to NVME storage device connected
"""

import sys
import argparse
import logging
import time
import os
from xml.etree import ElementTree
from typing import Union

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.security.tests.tdx.tdx_common_windows import WindowsTdxBaseTest
from src.security.tests.common.common_windows import VmOS

class TdxPCIeWindows(WindowsTdxBaseTest):
    """
            This recipe tests TD guest boot and requires the use of a OS supporting TD guests.

            :Scenario: Connect 1 or 2 Intel/Samsung NVMe storage devices to PCIe bus and load a td guest with
            a NVMe hard drive and run IOmeter

            :Phoenix IDs: 22013655937

            :Test steps:

                :1:  Enable TME Bypass knob in BIOS menu.

                :2: Boot to TDX enabled Linux stack.

                :3: Launch a TD guest.

                :4: Disconnect a NVME disk from SUT as Offline mode and attach to the TD guest.

                :5: Run the IOmeter test in VM targeting to the newly connected NVMe storage device

                :6: If there is a second NVMe disk available do the above steps for second TD guest.

            :Expected results: TD guests can work with attached NVMe device.

            :Reported and fixed bugs:

            :Test functions:


        """
    def __init__(self, test_log: logging.Logger, arguments: argparse.Namespace, cfg_opts: ElementTree) -> None:
        """
        Create an instance of test case.
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(TdxPCIeWindows, self).__init__(test_log, arguments, cfg_opts)
        self._tool_name_in_artifactory = "IOMeter_1_1_0_Win64.zip"
        self._tool_base_loc_in_sut = r"C:\\"
        self._tool_base_loc_in_vm = "C:\\Automation"
        self._process_name = "IOmeter"
        self._exec_name = "IOmeter.exe"
        self._exec_arg = f"/c {self._tool_base_loc_in_vm}\\IOMeter_1_1_0_Win64\\iometer.icf /r {self._tool_base_loc_in_vm}\\IOMeter_1_1_0_Win64\\result.csv"

        self._io_meter_run_time = 300  # 5 minutes for each functional test.
        self._sut_log_path = r"C:\Automation\Logs"
        self._tool_output_result_file_name = "result.csv"

    def format_the_new_drive_and_change_drive_letter_in_win_vm(self, vm_name: str, vm_disk_no: int) -> None:
        """Using to format the new attached NVMe drive in VM and change the drive letter to G(ioMeter config file
        is expecting the new test drive name should be G: New Volume
        :param vm_name: vm name
        :param vm_disk_no: the new disk number attached to the VM"""

        drive_letter_list = self.get_all_drive_letters_of_disk_win_vm(vm_name, vm_disk_no)
        drive_letter = ""
        for drive_name in drive_letter_list:
            if drive_name.isalpha():
                drive_letter = drive_name
                break
        if not drive_letter.isalpha():
            raise content_exceptions.TestFail(f"Failed to identify the driver letter of new drive in VM {vm_name}")

        self.format_drive_in_win_vm(vm_name, drive_letter)

        # change drive letter to G:
        drive_letter_expected_by_iometer = "G"
        self.change_drive_letter_in_win_vm(vm_name, drive_letter, drive_letter_expected_by_iometer)

    def set_iometer_execution_time(self, vm_name: str, file_path:str, exec_time_in_sec: int) -> None:
        """The default iometer.cfg file configured to run 1 hr for each functional test. It can be
        changed by the user input.
        :param vm_name: vm name
        :param file_path: config file location to be modify with new values
        :param exec_time_in_sec: execution time in seconds"""

        exc_time_in_min = int(exec_time_in_sec/60)
        powershell_cmd = f"(Get-Content {file_path}) -Replace '60','{exc_time_in_min}' ^| Set-Content {file_path}"
        command_output = self.run_powershell_command_in_vm(vm_name, powershell_cmd)
        self._log.debug(command_output)

    def update_license_reg_for_iometer(self, vm_name: str) -> None:
        """A license warning has to be accepted to run the IOmeter.
        :param vm_name: vm name"""

        command = r"reg add HKEY_CURRENT_USER\Software\iometer.org\Iometer\Settings /v Version /t REG_SZ /d \"1.1.0\" /f"
        command_output = self.run_powershell_command_in_vm(vm_name, command)
        self._log.debug(command_output)

    def verify_failures_in_logs_vm(self, result_file_path_at_sut: str) -> bool:
        """ Verify the result of IOMeter execution.
        :param result_file_path_at_sut: the location of the result file in sut
        :return: True if there is no error reported else False"""

        get_file_content = "powershell.exe " + self.GET_FILE_CONTENT.format(result_file_path_at_sut)
        results_file_content = self._common_content_lib.execute_sut_cmd(get_file_content, get_file_content,
                                                                        self.command_timeout)
        errors_count=0
        read_errors_count = 0
        write_errors_count =0

        errors_count_index = 27
        read_errors_count_index = 28
        write_errors_count_index = 29

        line_identification_tokens = ["ALL", "MANAGER", "WORKER", "DISK"]

        str_list = results_file_content.split('\n')
        for line in str_list:
            string_tokens = line.split(",")
            if string_tokens[0] in line_identification_tokens:
                if len(string_tokens) >= 30 :
                    try:
                        errors_count = errors_count + int(string_tokens[errors_count_index])
                        read_errors_count = read_errors_count + int(string_tokens[read_errors_count_index])
                        write_errors_count = write_errors_count + int(string_tokens[write_errors_count_index])
                    except Exception as err:
                        print(str(err))

        self._log.info(" Errors count " + str(errors_count))
        self._log.info(" Read Error Count " + str(read_errors_count))
        self._log.info(" Write Errors Count " + str(write_errors_count))
        return True if (errors_count + read_errors_count + write_errors_count) == 0 else False

    def run_iometer_in_win_vm(self, vm_ipaddress: str):
        """Run the IOmeter command in VM using PsExec.
        :return None:"""
        tool_abs_path = f"{self._tool_base_loc_in_vm}\\IOMeter_1_1_0_Win64"
        try:
            run_command = f"psexec.exe \\\\{vm_ipaddress} -u {self.vm_user_name} -p {self.vm_user_pwd} -accepteula -d -i " \
                          f" cmd.exe /C \"{tool_abs_path}\\IOmeter.exe /c {tool_abs_path}\\iometer.icf " \
                          f" /r {tool_abs_path}\\result.csv\""
            self.os.execute(run_command, self.command_timeout)
        except RuntimeError as err:
            self._log.debug(f"Error codes returned by PsExec are specific to the applications you execute, not PsExec."
                            f"So please check the process is running: {err}")

    def launch_td_win_vm_with_nvme_disk(self, vm_name: str, key: int, nvme_disk_number: int,
                                        host_tool_folder_path: str) -> Union[None, str]:
        """Launch a tdvm with a NVMe disk
        :param vm_name: new VM name
        :param key: key number for the new VM
        :param nvme_disk_number: disk number to be attached to the new VM
        :param host_tool_folder_path: Location where the tools are copied from artifactory or manually
        :return: If everything is successful it returns the path of the IOmeter location else None """

        # change the disk's readonly mode to ReadWrite mode.
        if not self.set_disk_to_rw_mode_sut(nvme_disk_number):
            return None

        # mark disk as offline to attach to VM.
        if not self.set_disk_to_offline_mode_sut(nvme_disk_number):
            return None

        # get guid of the nvme disk to compare the physical disk presence in VM
        guid_of_disk = self.get_disk_property_in_sut(nvme_disk_number, "Guid")

        # launch TD Windows vm
        self.launch_td_guest(key, vm_name)
        self.enable_vm_integration(vm_name)  # enable vm image integration
        # Shutdown VM to attach NVMe disk
        self.teardown_vm(vm_name)
        time.sleep(90)

        # attach the new NVMe disk to VM's settings.
        self.add_hard_disk_to_vm(vm_name, nvme_disk_number)
        self.start_vm(vm_name)
        time.sleep(90)

        # Get disk number in VM which is matching with guid got from SUT.
        nvme_disk_no_in_vm = self.get_disk_number_in_win_vm(vm_name, guid_of_disk)
        if nvme_disk_no_in_vm is None:
            raise content_exceptions.TestFail(f"Failed to identify disk in VM matching with NVMe disk")

        # activate the disk in VM by RW mode and change to ONLINE mode.
        self.activate_disk_in_win_vm(vm_name, nvme_disk_no_in_vm)

        # change the drive letter to G: and format, IOMeter config works only with G: drive
        self.format_the_new_drive_and_change_drive_letter_in_win_vm(vm_name, nvme_disk_no_in_vm)

        # copy IOMeter to VM and extract it
        package_path_in_vm = self.copy_file_from_host_to_sut_to_vm(vm_name, "", self._tool_name_in_artifactory,
                                                                   self._process_name, host_tool_folder_path,
                                                                   self._tool_base_loc_in_sut, self._tool_base_loc_in_vm,
                                                                   VmOS.WINDOWS)
        # Set the execution in icf file
        self.set_iometer_execution_time(vm_name, package_path_in_vm + "\\iometer.icf", self._io_meter_run_time)

        # Set license accept settings for iometer application.
        self.update_license_reg_for_iometer(vm_name)

        # return the application location in vm
        return package_path_in_vm

    def execute(self) -> bool:
        tdvm_key = -1
        self._log.info("Get all VM lists in the hyper v manager")
        self.get_vm_list()
        self.clean_all_vms()

        # download the IOmeter to host
        host_tool_folder_path = self._artifactory_obj.download_tool_to_automation_tool_folder(
            self._tool_name_in_artifactory)
        self._log.info(f"Copying {self._tool_name_in_artifactory} to SUT")

        nvme_disk_number_lists = self.get_all_nvme_disk_numbers_in_sut()
        if len(nvme_disk_number_lists) == 0:
            raise content_exceptions.TestSetupError("The SUT doesn't have enough NVMe drives attached")

        os_disk_number = self.get_os_disk_number_of_drive_letter_in_sut()
        if os_disk_number in nvme_disk_number_lists:
            # remove the os disk_number from the list
            nvme_disk_number_lists.remove(os_disk_number)

        num_of_nvme_disks_worked = 0
        vm_names_launched_successfully = list()
        pkg_path_in_vm = ""

        for disk_number in nvme_disk_number_lists:
            nvme_disk_number = int(disk_number)
            tdvm_key, vm_name = self.create_vm_name(tdvm_key + 1, legacy=False)

            # Launch a VM and attach NVMe for IOmeter testing.
            pkg_path_in_vm = self.launch_td_win_vm_with_nvme_disk(vm_name, tdvm_key, nvme_disk_number, host_tool_folder_path)
            if pkg_path_in_vm is None:
                self._log.info(f"Failed to setup {vm_name} with disk number {disk_number}")
                continue
            # keep the VM lists for further testing.
            vm_names_launched_successfully.append(vm_name)
            num_of_nvme_disks_worked = num_of_nvme_disks_worked + 1
            if num_of_nvme_disks_worked >= 2:
                break   # Maximum 2 NVMe is sufficient for this test.

        # Run IOMeter testing in each VMs.
        for vm_name in vm_names_launched_successfully:
            vm_ipaddress = self.get_vm_ipaddress(vm_name)
            # self.start_process_in_vm_cmd_line(vm_name, self._exec_name, pkg_path_in_vm, self._exec_arg)
            self.run_iometer_in_win_vm(vm_ipaddress)

            time.sleep(10)
            ret_val = self.check_process_running(vm_name, self._process_name)
            if not ret_val:
                # self._log.error(f"{self._process_name} is not running in {vm_name}")
                raise content_exceptions.TestSetupError("Failed to start Iometer.exe")

        # Wait till the application execution time
        io_meter_run_time = (self._io_meter_run_time * 16) + 600  # 16 functional test * 5 minutes per test + 10 minutes buffer time
        self._log.info(f"Please wait till IOmeter completes by {io_meter_run_time}")
        time.sleep(io_meter_run_time)

        # Verify the bios log and application results.txt file for each vms
        results_file = pkg_path_in_vm + r"\\" + self._tool_output_result_file_name

        test_result = True
        for vm_name in vm_names_launched_successfully:
            self.wait_for_application_execution(vm_name, self._process_name, 1800)
            filename = f"{vm_name}_{self._process_name}_results.txt"
            result_file_path_at_sut = os.path.join(self._sut_log_path, filename)
            self.delete_folder_at_sut(result_file_path_at_sut)
            self.copy_file_between_sut_and_vm(vm_name, results_file, result_file_path_at_sut, to_vm=False)
            if not self.verify_failures_in_logs_vm(result_file_path_at_sut):
                self._log.error(f"IOMeter test failed  in {vm_name}. Checking other VMs")
                test_result = False

        # copy all vm logs to dtaf log folder
        zip_file_full_path = os.path.join("C:\\", self.COMPRESSED_TDVM_FILES)
        self.delete_folder_at_sut(zip_file_full_path)
        self.compress_folder_at_sut(self.sut_log_path, zip_file_full_path)
        self.os.copy_file_from_sut_to_local(zip_file_full_path, f"{self.log_dir}\\{self.COMPRESSED_TDVM_FILES}")
        self.delete_folder_at_sut(zip_file_full_path)
        if not test_result:
            raise content_exceptions.TestFail("IOmeter test got failed")

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TdxPCIeWindows.main() else Framework.TEST_RESULT_FAIL)
