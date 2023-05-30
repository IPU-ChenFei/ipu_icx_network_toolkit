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
    :TD Workload Base Test Case:

    Launch a given number of TD guests and run a specific workload or stress test suite on each TD guest for prescribed
    amount of time.
"""

import sys
import os
import time

from dtaf_core.lib.dtaf_constants import Framework

from src.lib import content_exceptions
from src.security.tests.tdx.tdx_common_windows import WindowsTdxBaseTest
from src.security.tests.common.common_windows import VmOS


class TDGuestWorkloadBaseTestWindows(WindowsTdxBaseTest):
    """
            This is a base test for workload testing with TD guests as part of the TDX feature.

            The following parameters in the content_configuration.xml file should be populated before running a test.

            Change <TDX><num_of_vms> to control the number of TD guests that will be run in parallel.
            Each test will have its own parameter to adjust for run time; this should be explained in the individual
            test case.

            :Scenario: Launch the number of TD guests prescribed, initiate the workload on each TD guest, run for the
            necessary time to complete the tests, then verify the SUT and the TD guests have not crashed.

            :Phoenix IDs:

            :Test steps:

                :1: Launch a TD guest.

                :2: On TD guest, launch a stress suite or workload.

                :3: Repeat steps 1 and 2 for the prescribed number of TD guests.

                :4: Run until workload tests complete.

            :Expected results: Each TD guest should boot and the workload suite should run to completion with no
            errors on the SUT or any of the TD guests.

            :Reported and fixed bugs:

            :Test functions:

        """
    RUN_APP_USING_POWERSHELL = r"$arg= '/C {0}'; Start-Process 'cmd.exe' -WorkingDirectory '{1}' -ArgumentList $arg -Verb RunAs; return 'Success'"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of test case.
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        :return: None
        """
        super(TDGuestWorkloadBaseTestWindows, self).__init__(test_log, arguments, cfg_opts)

        self._vm_os = VmOS.WINDOWS  # vm os flavor LINUX or WINDOWS
        self._tool_base_loc_in_sut = r"C:\\"  # where to copy the pkgs at SUT
        self._tools_destination_path_in_vm = ""  # where to copy the pkgs at VM
        self._tool_name_in_artifactory = ""  # tool name in artifactory as zip/tar format or binary name
        self._tool_process_name = ""   # process name to check the app is running in VM
        self._tool_exe_name = ""  # executable name
        self._tool_output_result_file_name = ""  # tools output saved to a file
        self._tool_run_command_in_vm = ""  # actual command to be run in the VM
        self._tool_run_async = False  # launch the tool as aysnc mode.

        self._tool_known_results_failures = list()  # known error list to be verify
        self._bios_log_known_errors_list = list()  # known bios log errors list
        self._tool_source_code_bld_cmd_list = list()  # if the application need to be build
        self._tool_run_command_in_sut = ""  # list()  # applicable only for ntttcp
        self._software_pkg_lists = list()  # if there is a dependency on main tool
        self._host_tool_folder_path = ""  # The location of the tool in host machine.
        self._tool_run_time = 0  # tool run time.

    def prepare(self):
        super(TDGuestWorkloadBaseTestWindows, self).prepare()
        
    def install_software_pkgs_in_linux_vm(self, vm_ip_address: str) -> None:
        """install software packages in linux VM
        :param vm_ip_address: VM ip address"""

        if len(self._software_pkg_lists) == 0:
            return
        for install_pkg_name in self._software_pkg_lists:
            try:
                self.run_command_in_linux_vm_using_ssh(vm_ip_address, install_pkg_name)
            except RuntimeError:
                self._log.debug(f"exception while running {install_pkg_name}")

    def copy_tool_from_host_to_sut_to_vm(self, vm_name: str, vm_ipaddress: str) -> str:
        """Copy tool(zip, tar or binary) host to sut, then copy to VM
        :param vm_name: VM name
        :param vm_ipaddress: virtual machine ip address
        :return: package path/extracted path at VM machine """

        return self.copy_file_from_host_to_sut_to_vm(vm_name,
                                                     vm_ipaddress,
                                                     self._tool_name_in_artifactory,
                                                     self._tool_process_name,
                                                     self._host_tool_folder_path,
                                                     self._tool_base_loc_in_sut,
                                                     self._tools_destination_path_in_vm,
                                                     self._vm_os)

    def build_tools_in_linux_vm(self, vm_ipaddress: str) -> bool:
        """Build the source code.
        :param vm_ipaddress: vm ip address for communication
        :return: True if source code build is success else False
        """
        if len(self._tool_source_code_bld_cmd_list) == 0:
            return True
        try:
            # build the tool
            for bld_cmd in self._tool_source_code_bld_cmd_list:
                self.run_command_in_linux_vm_using_ssh(vm_ipaddress, bld_cmd)
            return True
        except RuntimeError as err:
            self._log.debug(err)
            return False

    def verify_failures_in_logs_vm(self, result_file_path: str, console_log_ref_number: int = 0) -> None:
        """Verify all possible failures caused by tools in result file, bios log and events.
        :param result_file_path: expected results file location
        :param console_log_ref_number: the reference count of the console log before starting the test.
        :return: None
        :raise content_exception.TestFail if the logs have known errors."""

        get_file_content = "powershell.exe " + self.GET_FILE_CONTENT.format(result_file_path)
        results_file_content = self._common_content_lib.execute_sut_cmd(get_file_content, get_file_content, self.command_timeout)
        for known_error in self._tool_known_results_failures:
            if known_error in results_file_content:
                raise content_exceptions.TestFail(f"{self._tool_process_name} run failed by {known_error}")

        ret_val = self.verify_console_log_for_known_error(console_log_ref_number, self._bios_log_known_errors_list)
        if ret_val is False:
            raise content_exceptions.TestFail(f"bios log failure:- {self._tool_process_name} run failed ")

    def launch_guest(self, key: int, vm_name: str) -> None:
        """Launch a Linux VM or Windows VM as per the derived class's selection
        :param key: id to identify the vm
        :param vm_name: VM name"""

        if self._vm_os == VmOS.LINUX:
            self.launch_ubuntu_td_guest(key, vm_name)
        else:
            self.launch_td_guest(key, vm_name)
            self.enable_vm_integration(vm_name)  # enable vm image integration

    def install_dependency_pkgs_in_vm(self, vm_name: str, vm_ip_address: str) -> None:
        """Install software packages to build the source code
        :param vm_name: VM name
        :param vm_ip_address: VM ip address
        :return None"""

        self._log.debug("Windows OS comes with all relevant SW solutions")
        if self._vm_os == VmOS.LINUX:
            self.install_software_pkgs_in_linux_vm(vm_ip_address)

    def build_source_code(self, vm_name: str, vm_ip_address: str) -> bool:
        """build the source code(applicable only for Linux OS).
        :param vm_name: VM name
        :param vm_ip_address: VM ip address
        :return None """

        if self._vm_os == VmOS.LINUX:
            return self.build_tools_in_linux_vm(vm_ip_address)
        return True

    def get_ipaddress_vm(self, vm_name) -> str:
        """This is a temporary solution for Linux VM. Once linux-azure package issue solved,
        it will be removed.
        :param vm_name: VM name
        :return VM's ipaddress"""

        if self._vm_os == VmOS.LINUX:
            return self.get_vm_ipaddress_for_linux_guest(vm_name)
        else:
            return self.get_vm_ipaddress(vm_name)

    def run_command_in_vm(self, vm_name: str, vm_ip_address: str, tool_installation_path_vm: str, command_timeout: int = 0) -> None:
        """Run the application in Linux VM or Windows VM
        :param vm_name: VM name
        :param vm_ip_address: VM's ip address
        :param tool_installation_path_vm: The location of the application available to run
        :param command_timeout: command timeout.
        :return: None
        """
        if self._vm_os == VmOS.LINUX:
            command_in_vm = f"cd {tool_installation_path_vm}; {self._tool_run_command_in_vm}"
            self.run_command_in_linux_vm_using_ssh(vm_ip_address, command_in_vm, command_timeout, self._tool_run_async)
        else:
            command_in_vm = self.RUN_APP_USING_POWERSHELL.format(self._tool_run_command_in_vm,
                                                                 tool_installation_path_vm)
            self.run_powershell_command_in_vm(vm_name, command_in_vm)

    def run_command_in_sut(self, exec_command: str, command_timeout: int = 0) -> None:
        """Run a command in SUT.
        :param exec_command: command to run in SUT
        :param command_timeout: timeout for the command
        :return: None """
        if not self._tool_run_async:
            self._common_content_lib.execute_sut_cmd(exec_command, exec_command, command_timeout)
        else:
            self.run_command_as_async_in_sut(exec_command)

    def wait_for_application_termination(self, vm_name: str, vm_ip_address: str,  timeout: int = 5):
        """Wait and terminate the application
        :param vm_name: VM name
        :param vm_ip_address: VM's ip address
        :param timeout: timeout of the application to exit by itself."""

        if self._vm_os == VmOS.LINUX:
            self.wait_for_application_execution_in_linux_vm(vm_ip_address, self._tool_process_name, timeout)
        else:
            self.wait_for_application_execution(vm_name, self._tool_process_name, timeout)

    def verify_process_running_in_vm(self, vm_name: str, vm_ip_address: str, process_name: str) -> bool:
        """Verify the application is running in Linux/Windows VM
        :param vm_name: VM name
        :param vm_ip_address: VM's ip address
        :param process_name: process name.
        :return: True if process running in VM else False"""
        if self._vm_os == VmOS.LINUX:
            ret_val = self.check_process_running_in_linux_vm(vm_ip_address, process_name)
        else:
            ret_val = self.check_process_running(vm_name, process_name)
        if ret_val is True:
            self._log.info(f"{process_name} still running")
        else:
            self._log.info(f"{process_name} exited")
        return ret_val

    def execute(self):
        """
        1. Create a linux tdx vm
        2. Run application for test
        3. Verify the results and bios log error.
        """
        tdvm_key = -1
        self._log.info("Get all VM lists in the hyper v manager")
        self.get_vm_list()
        self.clean_all_vms()
        if self._vm_os == VmOS.LINUX:
            self.clean_linux_vm_tdx_apps()
        num_vms = int(self.tdx_properties[self.tdx_consts.NUMBER_OF_VMS])
        vm_name_ipadd_dict = dict()
        tool_installation_path_vm = ""
        os_ver = ""
        if self._vm_os == VmOS.LINUX:
            os_ver = "LINUX"
        elif self._vm_os == VmOS.WINDOWS:
            os_ver = "WINDOWS"

        self._log.info(f"Creating and launching {num_vms} VMs.")
        for idx in range(0, num_vms):
            self._log.info(f"Create {self._vm_os} TDVM and launch")
            tdvm_key, vm_name = self.create_vm_name(tdvm_key + 1, legacy=False, vm_os=os_ver)
            self.launch_guest(tdvm_key, vm_name)
            # get vm name and ipaddress combinations
            vm_ip_address = self.get_ipaddress_vm(vm_name)
            vm_name_ipadd_dict[vm_name] = vm_ip_address
            tool_installation_path_vm = self.copy_tool_from_host_to_sut_to_vm(vm_name, vm_ip_address)
            # install dependency packages.
            self.install_dependency_pkgs_in_vm(vm_name, vm_ip_address)
            # if need, build the source code.
            ret_val = self.build_source_code(vm_name, vm_ip_address)
            if not ret_val:
                raise content_exceptions.TestFail("Source code build failed")

        # get console log counts before starting the application
        console_log_line_count = self.get_console_log_line_count()

        # run server commands(applicable only for ntttcp)
        if self._tool_run_command_in_sut != "":
            self.run_command_in_sut(self._tool_run_command_in_sut, self.command_timeout)  # for ntttcp server

        # run client commands at VM.
        for vm_ip_address in vm_name_ipadd_dict.items():
            self.run_command_in_vm(vm_ip_address[0], vm_ip_address[1], tool_installation_path_vm, self.command_timeout)
            self.verify_process_running_in_vm(vm_ip_address[0], vm_ip_address[1], self._tool_process_name)

        self._log.info(f"{self._tool_process_name} has successfully started..")
        self._log.info(f"Waiting {self._tool_run_time} seconds to complete the application {self._tool_process_name}")
        time.sleep(self._tool_run_time)

        # Verify the bios log and application results.txt file for each vms
        results_file = tool_installation_path_vm + r"/" + self._tool_output_result_file_name
        for vm_ip_address in vm_name_ipadd_dict.items():
            self.wait_for_application_termination(vm_ip_address[0], vm_ip_address[1], 5)
            filename = f"{vm_ip_address[0]}_{self._tool_process_name}_results.txt"
            result_file_path_at_sut = os.path.join(self.sut_log_path, filename)
            self.delete_folder_at_sut(result_file_path_at_sut)
            if self._vm_os == VmOS.LINUX:
                self.copy_files_between_sut_and_linux_vm(results_file, result_file_path_at_sut, False, vm_ip_address[1], to_vm=False)
            else:
                self.copy_file_between_sut_and_vm(vm_ip_address[0], results_file, result_file_path_at_sut, to_vm=False)
            self.verify_failures_in_logs_vm(result_file_path_at_sut, console_log_line_count)

        # copy all vm logs to dtaf log folder
        zip_file_full_path = os.path.join("C:\\", self.COMPRESSED_TDVM_FILES)
        self.delete_folder_at_sut(zip_file_full_path)
        self.compress_folder_at_sut(self.sut_log_path, zip_file_full_path)
        self.os.copy_file_from_sut_to_local(zip_file_full_path, f"{self.log_dir}\\{self.COMPRESSED_TDVM_FILES}")
        self.delete_folder_at_sut(zip_file_full_path)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TDGuestWorkloadBaseTestWindows.main() else Framework.TEST_RESULT_FAIL)
