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
import re
import time

from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.install_collateral import InstallCollateral
from src.lib import content_base_test_case
from src.dpdk.lib.dpdk_common_lib import DpdkCommonLib
from src.lib import content_exceptions


class DpdkCommon(content_base_test_case.ContentBaseTestCase):
    """
    Base class extension for DPDKCommon which holds common functionality
    """

    LIST_OF_DPDK_DIR = ['app', 'build', 'include', 'kmod', 'lib', 'Makefile']
    LIST_INSTALLED_FILES_CMD = "ls x86_64-native-linuxapp-gcc"
    MODPROBE_CMD = "modprobe uio"
    INSMOD_CMD = "insmod x86_64-native-linuxapp-gcc/kmod/igb_uio.ko"
    LSMOD_CMD = "lsmod | grep uio"
    GET_HUGEPAGE_INFO = "cat /proc/meminfo | grep Huge"
    DPDK_INSTALLATION_PATH = None
    HUGEPAGES_TOTAL_REGEX = "HugePages_Total:\s+(\d+)"
    HUGEPAGES_FREE_REGEX = "HugePages_Free:\s+(\d+)"
    INITIAL_PAGE_SIZE = "0"
    HUGEPAGE_SIZE = "256"
    HUGEPAGE_ALLOCATION_CMD = "echo {} > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages".format(HUGEPAGE_SIZE)
    DIR_HUGE = "mkdir /mnt/huge"
    MOUNT_HUGE_DIR = "mount -t hugetlbfs nodev /mnt/huge"
    BIND_STATUS = "./usertools/dpdk-devbind.py --status"
    DRIVER_NAME = "igb_uio"
    BIND_CMD = "./usertools/dpdk-devbind.py -b {} {}"
    LSPCI_CMD = "lspci | grep '{}'"
    DRIVER_REGEX = "drv=(.*)\s+"
    SET_RTE_SDK_VAR = "export RTE_SDK={}"
    SET_RTE_TARGET_VAR = "export RTE_TARGET=x86_64-native-linuxapp-gcc"
    OUTPUT_FILE = "run_result.txt"
    PROCESS_KILL_CMD = "pkill -INT {}"
    CAT_CMD = "cat {}"
    ERROR_LIST = ["error", "warning", "failure"]
    L2FWD_STR = "l2fwd"
    L3FWD_STR = "l3fwd"
    RXTX_STR = "rxtx_callbacks"
    TEST_LOCATION = "/examples/{}"
    DIR_FIND_CMD = 'find $(pwd) -type d -name {}'
    L2FWD_CMD = "./build/l2fwd -c 0xffff -n 4 -- -p 3 > {}"
    L3FWD_CMD ='./build/l3fwd -c 606 -n 4 -- -p 0x3 --config="(0,0,1),(0,1,2),(1,0,9),(1,1,10)"  > {}'
    RXTX_CMD = "./build/rxtx_callbacks -c 2 -n 4 > {}"
    MAKE_CMD = "make"
    RXTX_DURATION = 1800
    L2FWD_DURATION = L3FWD_DURATION = 5
    TOP_CMD = r"top -1 -n 5 -b| grep 'Cpu1\b'"
    CURR_PROCESS_GREP_CMD = 'ps -ef | grep {}'
    TEST_PMD_PATH = "/x86_64-native-linuxapp-gcc/build/app/test-pmd"
    TESTPMD_PACKET_FORWARD_CMD = "./testpmd -c7 -n3 -- --nb-cores=2 --nb-ports=2 --total-num-mbufs=2048 --tx-first > {}"
    TESTPMD_DURATION = 54000

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of DpdkCommon

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(DpdkCommon, self).__init__(test_log, arguments, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise NotImplementedError("DPDK installation is not implemented for the os: {}".format(self.os.os_type))
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._dpdk_common_lib = DpdkCommonLib(self._log, cfg_opts, self.os)
        self._nic_name = self._common_content_configuration.get_fortville_nic_device_name()

    def prepare(self):
        # type: () -> None
        """Test preparation/setup """

        super(DpdkCommon, self).prepare()

    def install_and_verify_dpdk(self):
        """
        This method installs DPDK and verify if it is installed properly.

        :raise: content Exception if DPDK folders are not present.
        """
        dir_not_present = []
        self._log.info("Installing and verifying DPDK in SUT")
        self.DPDK_INSTALLATION_PATH = self._install_collateral.install_dpdk()  # Install DPDk in sut
        command_result = self._common_content_lib.execute_sut_cmd(self.LIST_INSTALLED_FILES_CMD, "list dpdk dir cmd",
                                                                   self._command_timeout, cmd_path=self.DPDK_INSTALLATION_PATH)
        self._log.debug("DPDK installed directories are '{}' ".format(command_result))

        for item in self.LIST_OF_DPDK_DIR:
            if item not in command_result.split():
                dir_not_present.append(item)
        if dir_not_present:
            raise content_exceptions.TestFail("These dpdk folders are not present '{}", dir_not_present)
        self._log.info("All DPDK folders are present...")

    def get_nic_bdf_value(self):
        """
        This method is to get the bdf value of the connected Ethernet NIC.

        :return: ethernet_device_id bdf value of NIC device
        """
        ethernet_device_id = []
        self._log.info("Execute to get NIC name from Config File")
        regex_cmd = r"(.*:\d+.\d+).* {}".format(self._nic_name)

        command_output = self._common_content_lib.execute_sut_cmd(sut_cmd=self.LSPCI_CMD.format(self._nic_name),
                                                               cmd_str="nic name",
                                                               execute_timeout=self._command_timeout)
        self._log.debug("Result of lspci command is {}".format(command_output))
        ethernet_devices_info = [each_device for each_device in command_output.split("\n") if each_device != ""]
        for device in ethernet_devices_info:
            regex_search = re.search(regex_cmd, device.strip())
            if regex_search is not None:
                ethernet_device_id.append(regex_search.group(1))
        return ethernet_device_id[0], ethernet_device_id[1]

    def hugepages_setup_and_port_bind(self):
        """
        This method bind the NIC ports

        :raise: Content Exception Huge page is not allocated or Port binding is not successful
        """
        self._log.info("Binding the NIC ports")
        self._common_content_lib.execute_sut_cmd(self.MODPROBE_CMD, self.MODPROBE_CMD, self._command_timeout,
                                                 cmd_path=self.DPDK_INSTALLATION_PATH)
        self._common_content_lib.execute_sut_cmd(self.INSMOD_CMD, self.INSMOD_CMD, self._command_timeout,
                                                 cmd_path=self.DPDK_INSTALLATION_PATH)
        self._common_content_lib.execute_sut_cmd(self.LSMOD_CMD, self.LSMOD_CMD, self._command_timeout,
                                                 cmd_path=self.DPDK_INSTALLATION_PATH)

        # Hugepages Setup Steps
        initial_huge_page_info = self._common_content_lib.execute_sut_cmd(self.GET_HUGEPAGE_INFO,
                                                                          self.GET_HUGEPAGE_INFO,
                                                                          self._command_timeout,
                                                                          cmd_path=self.DPDK_INSTALLATION_PATH)
        self._log.debug("Hugepage status info is {}".format(initial_huge_page_info))
        total_hugepage_initial = re.search(self.HUGEPAGES_TOTAL_REGEX, initial_huge_page_info).group(1)
        free_hugepage_initial = re.search(self.HUGEPAGES_FREE_REGEX, initial_huge_page_info).group(1)
        if total_hugepage_initial != self.INITIAL_PAGE_SIZE and free_hugepage_initial != self.INITIAL_PAGE_SIZE:
            raise content_exceptions.TestFail("Huge page size is not as expected, expected total hugepage {}, "
                                              "free hugepage {} and got total hugepage {} and free hugepage {}".format(
                self.INITIAL_PAGE_SIZE, self.INITIAL_PAGE_SIZE, total_hugepage_initial, free_hugepage_initial))
        self._common_content_lib.execute_sut_cmd(self.HUGEPAGE_ALLOCATION_CMD,
                                                 self.HUGEPAGE_ALLOCATION_CMD,
                                                 self._command_timeout, cmd_path=self.DPDK_INSTALLATION_PATH)
        final_huge_page_info = self._common_content_lib.execute_sut_cmd(self.GET_HUGEPAGE_INFO,
                                                                        self.GET_HUGEPAGE_INFO,
                                                                        self._command_timeout,
                                                                        cmd_path=self.DPDK_INSTALLATION_PATH)
        self._log.debug("Hugepage status info is {}".format(final_huge_page_info))
        total_hugepage_final = re.search(self.HUGEPAGES_TOTAL_REGEX, final_huge_page_info).group(1)
        free_hugepage_final = re.search(self.HUGEPAGES_FREE_REGEX, final_huge_page_info).group(1)
        if total_hugepage_final != self.HUGEPAGE_SIZE and free_hugepage_final != self.HUGEPAGE_SIZE:
            raise content_exceptions.TestFail("Huge page size is not as expected, expected total hugepage {}, "
                                              "free hugepage {} and got total hugepage {} and free hugepage {}".format(
                self.HUGEPAGE_SIZE, self.HUGEPAGE_SIZE, total_hugepage_final, free_hugepage_final))

        # Mount Hugepages
        self.os.execute(self.DIR_HUGE, self._command_timeout, cwd=self.DPDK_INSTALLATION_PATH)

        self._common_content_lib.execute_sut_cmd(self.MOUNT_HUGE_DIR, self.MOUNT_HUGE_DIR, self._command_timeout,
                                                 cmd_path=self.DPDK_INSTALLATION_PATH)

        # Binding the NIC ports
        port1, port2 = self.get_nic_bdf_value()
        status_output_initial = self._common_content_lib.execute_sut_cmd(self.BIND_STATUS, self.BIND_STATUS,
                                                                         self._command_timeout,
                                                                         cmd_path=self.DPDK_INSTALLATION_PATH)
        self._log.debug("status before binding is {}".format(status_output_initial))
        self._common_content_lib.execute_sut_cmd(self.BIND_CMD.format(self.DRIVER_NAME, port1), self.BIND_CMD.format(
            self.DRIVER_NAME, port1), self._command_timeout, cmd_path=self.DPDK_INSTALLATION_PATH)
        self._common_content_lib.execute_sut_cmd(self.BIND_CMD.format(self.DRIVER_NAME, port2), self.BIND_CMD.format(
            self.DRIVER_NAME, port2), self._command_timeout, cmd_path=self.DPDK_INSTALLATION_PATH)
        status_output_final = self._common_content_lib.execute_sut_cmd(self.BIND_STATUS, self.BIND_STATUS,
                                                                       self._command_timeout,
                                                                       cmd_path=self.DPDK_INSTALLATION_PATH)
        self._log.debug("status after port binding is {}".format(status_output_final))
        for line in status_output_final.split("\n"):
            if self._nic_name in line and re.search(self.DRIVER_REGEX, line).group(1) != self.DRIVER_NAME:
                raise content_exceptions.TestFail("Port binding is not successful")
        self._log.info("Ports are bind successfully")

    def build_and_run_l2fwd_test(self, dpdk_install_path):
        """
        This method compile the l2fwd application and run the test and checks if the command launched successfully
        without any error/failures

        :param dpdk_install_path: dpdk directory path in sut
        :raise: Content Exception if the test is not launch successfully or if any error/failure found during test
        execution
        """
        self._log.info("Compiling the L2fwd application and launching the test")
        l2wfd_path = dpdk_install_path + self.TEST_LOCATION.format(self.L2FWD_STR)
        # Generate build for l2fwd
        self.compile_test_application(l2wfd_path, dpdk_install_path)
        # Launch l2fwd test
        self.os.execute_async(self.L2FWD_CMD.format(self.OUTPUT_FILE), cwd=l2wfd_path)
        self.is_dpdk_test_running(self.L2FWD_STR)  # Checking if the test is launch successfully
        self._log.info("L2fwd test is launched and running successfully")
        time.sleep(self.L2FWD_DURATION)  # L2fwd test duration
        # Stop l2fwd test
        self._common_content_lib.execute_sut_cmd(self.PROCESS_KILL_CMD.format(self.L2FWD_STR), self.PROCESS_KILL_CMD.format(
            self.L2FWD_STR), self._command_timeout, cmd_path=l2wfd_path)
        self._log.info("L2fwd test is stopped successfully")
        # check log file for searching error or failure
        self.check_error(l2wfd_path)

    def build_and_run_l3fwd_test(self, dpdk_install_path):
        """
        This method compile the l3fwd application and run the test and checks if the command launched successfully
        without any error/failures

        :param dpdk_install_path: dpdk directory path in sut
        :raise: Content Exception if the test is not launch successfully or if any error/failure found during test
        execution
        """
        self._log.info("Compiling the L3fwd application and launching the test")
        l3fwd_path = dpdk_install_path + self.TEST_LOCATION.format(self.L3FWD_STR)
        # Generate build for l3fwd
        self.compile_test_application(l3fwd_path, dpdk_install_path)
        self.os.execute_async(self.L3FWD_CMD.format(self.OUTPUT_FILE), cwd=l3fwd_path)
        self.is_dpdk_test_running(self.L3FWD_STR)
        self._log.info("L3fwd test is launched and running successfully")
        time.sleep(self.L3FWD_DURATION)  # L3fwd test duration
        # Checks if l3fwd test process is running and then kill
        self._common_content_lib.execute_sut_cmd(self.PROCESS_KILL_CMD.format(self.L3FWD_STR), self.PROCESS_KILL_CMD.format(
            self.L3FWD_STR), self._command_timeout, cmd_path=l3fwd_path)
        self._log.info("L3fwd test is stopped successfully")
        # check log file for searching error or failure
        self.check_error(l3fwd_path)

    def build_and_run_rxtx_test(self, dpdk_install_path):
        """
        This method compile the rxtx_callbacks application and run the test for 30 min and checks if the command
        launched successfully, also checks the CPU usage is close to 100% during test execution
        without any error/failures

        :param dpdk_install_path: dpdk directory path in sut
        :raise: Content Exception if the test is not launch successfully or if any error/failure found during test
        execution
        """
        self._log.info("Compiling the rxtx_callbacks application and launching the test")
        rxtx_path = dpdk_install_path + self.TEST_LOCATION.format(self.RXTX_STR)
        # Generate build for rxtx_callbacks
        self.compile_test_application(rxtx_path, dpdk_install_path)
        self.os.execute_async(self.RXTX_CMD.format(self.OUTPUT_FILE), cwd=rxtx_path)
        self.is_dpdk_test_running(self.RXTX_STR)  # Check if test is not launch successfully
        time.sleep(self.RXTX_DURATION)  # RXTX_callbacks test duration
        output_txt = self._common_content_lib.execute_sut_cmd(self.TOP_CMD, self.TOP_CMD, self._command_timeout)
        self._log.debug("Result of top command is :{}".format(output_txt))
        if not self.check_cpu_usage(output_txt):
            raise content_exceptions.TestFail("CPU usage is not close to 100%")
        self._log.info("CPU usage is close to 100% during the test execution")
        self.is_dpdk_test_running(self.RXTX_STR)  # Check if the test is running properly
        self._common_content_lib.execute_sut_cmd(self.PROCESS_KILL_CMD.format(self.RXTX_STR),
                                                 self.PROCESS_KILL_CMD.format(self.RXTX_STR), self._command_timeout,
                                                 cmd_path=rxtx_path)
        self._log.info("RXTX_callbacks test is stopped successfully")
        # check log file for searching error or failure
        self.check_error(rxtx_path)

    def compile_test_application(self, application_path, install_dpdk_path):
        """
        This method compile the test application and generate the dpdk test build.

        :param application_path: dpdk test application path
        :param install_dpdk_path: dpdk directory path in sut
        """
        self._log.info("Generating dpdk test build")
        compiled_output = self._common_content_lib.execute_sut_cmd(self.SET_RTE_SDK_VAR.format(install_dpdk_path) +
                                                          " && " + self.SET_RTE_TARGET_VAR + " && " + self.MAKE_CMD,
                                                          self.MAKE_CMD, self._command_timeout, application_path)
        self._log.debug("Result after compilation is {}".format(compiled_output))

    def check_cpu_usage(self, top_cmd_output):
        """
        This method checks for if CPU usage is between the range 99-100 during the rxtx_callbacks test

        :param top_cmd_output: output of top command
        :return: True if the usage is in range 99-100 else False
        """
        usage_data = []
        usage_range = []
        cpu_usage_regex = "(\d+.\d)+\s+us"
        top_cmd_data = [cmd_data.strip() for cmd_data in top_cmd_output.split("\n") if cmd_data != ""]
        for valid_data in top_cmd_data:
            usage_data.append(re.search(cpu_usage_regex, valid_data).group(1))
        for each_data in range(len(usage_data)):
            usage_range.append(True) if int(float(usage_data[each_data])) in range(99, 101) else usage_range.append(False)
        return True if all(usage_range) else False

    def is_dpdk_test_running(self, test_suite):
        """
        This method Checks if the DPDK test suite is running on sut

        :param test_suite: dpdk test suite name
        :return: True if DPDK test suite running else False
        """
        self._log.info("Checking DPDK test {} is running on sut".format(test_suite))
        command_res = self.os.execute(self.CURR_PROCESS_GREP_CMD.format(test_suite), self._command_timeout)
        self._log.debug("Process detail is {}".format(command_res.stdout))
        self._log.error("Process detail is {}".format(command_res.stderr))
        test_count = command_res.stdout.count(test_suite)
        if test_count <= 1:
            raise content_exceptions.TestFail("Test {} is not launch successfully".format(test_suite))
        self._log.info("DPDK test {} is running on System".format(test_suite))
        return True

    def check_error(self, test_path):
        """
        This method search if any error or failures occurred during the test

        :param test_path: dpdk test path
        :raise: content exception if error found during test execution
        """
        self._log.info("Check if dpdk test executed successfully without any failure")
        output_txt = self._common_content_lib.execute_sut_cmd(self.CAT_CMD.format(self.OUTPUT_FILE),
                                                              self.CAT_CMD.format(self.OUTPUT_FILE),
                                                              self._command_timeout, cmd_path=test_path)
        self._log.debug("Test run output is: {}".format(output_txt))
        for string_item in self.ERROR_LIST:
            if string_item in output_txt.lower():
                raise content_exceptions.TestFail("Error found in result {}".format(output_txt))
        self._log.info("No error were found during execution of test")

    def run_testpmd_stress(self, dpdk_path):
        """
        This method runs poll-mode driver test for few hours and check the packet forwarding statistic for port 0
        and port 1 are same.

        :param dpdk_path: dpdk directory path in sut
        :raise: content Exception if Packet forward statistics are not fine
        """
        test_pmd_str = "testpmd"
        self._log.info("Run Poll-mode driver test")
        test_pmd_path = dpdk_path + self.TEST_PMD_PATH
        self.os.execute_async(self.TESTPMD_PACKET_FORWARD_CMD.format(self.OUTPUT_FILE), cwd=test_pmd_path)
        self.is_dpdk_test_running(test_pmd_str)  # Check if test is launch successfully
        time.sleep(self.TESTPMD_DURATION)
        self.is_dpdk_test_running(test_pmd_str)  # Check if the test is still running properly
        self._common_content_lib.execute_sut_cmd(self.PROCESS_KILL_CMD.format(test_pmd_str), self.PROCESS_KILL_CMD.format(
            test_pmd_str), self._command_timeout)
        self._log.info("Poll-mode driver test is stopped successfully")
        pmd_output = self._common_content_lib.execute_sut_cmd(self.CAT_CMD.format(self.OUTPUT_FILE),
                                                              self.CAT_CMD.format(self.OUTPUT_FILE),
                                                              self._command_timeout, cmd_path=test_pmd_path)
        self._log.debug("Poll-mode driver Test run output is: {}".format(pmd_output))
        if not self._dpdk_common_lib.evaluate_packet_forward_statistics(pmd_output):
            raise content_exceptions.TestFail("Packet forward statistics are not fine")

        self._log.info("Packet forward statistics are fine")
