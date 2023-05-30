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
import os
import configparser as config_parser

from pathlib import Path

from dtaf_core.lib.dtaf_constants import Framework

from src.memory.tests.memory_cr.apache_pass.performance.cr_performance_common import CrPerformance
from src.memory.tests.memory_cr.apache_pass.provisioning\
    .cr_provisioning_2lm_mixed_mode_50_50_interleaved_dax_linux import \
    CRProvisioning2LM50AppDirect50MemoryModeDaxLinux
from src.memory.lib.memory_common_lib import MemoryCommonLib
from src.lib.dmidecode_parser_lib import DmiDecodeParser


class ReducedSpeed1LM100AppDirectInterleavedDAXStressLinux(CrPerformance):
    """
    Glasgow ID: 58175

    1. DCPMMs in 1LM AppDirect 100% Interleaved modes at the reduced Memory Operational Speed BIOS settings
    using Linux provisioning tools.
    2. All DCPMMs will be provisioned as 100% persistent memory.
    3. System is stressed using MLC and FIO Tools

    """

    BIOS_CONFIG_FILE = "cr_reduced_speed_1lm_100_appdirectinterleaved_dax_stess_bios_knobs_58175.cfg"
    TEST_CASE_ID = "G58175"
    LOG_FOLDER = "mlc_fio_logs"

    _ipmctl_execute_path = None
    _mlc_execute_path = None
    _memory_frequency = None
    _frequency_list = None

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new ReducedSpeed1LM100AppDirectInterleavedDAXStressLinux object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """

        # calling cr performance init
        super(ReducedSpeed1LM100AppDirectInterleavedDAXStressLinux, self).__init__(test_log, arguments, cfg_opts,
                                                                                   self.BIOS_CONFIG_FILE)
        # calling CRProvisioning2LM50AppDirect50MemoryModeLinux of Glasgow ID : 58172
        self._cr_provisioning_2lm_mixed_mode = CRProvisioning2LM50AppDirect50MemoryModeDaxLinux(self._log,
                                                                                                arguments, cfg_opts)
        self._cr_provisioning_2lm_mixed_mode.prepare()
        self._cr_provisioning_2lm_mixed_mode.execute()

        self._dmidecode_parser = DmiDecodeParser(self._log, self._os)

        self._mlc_runtime = self._common_content_configuration.memory_mlc_run_time()
        self._idle_latency_threshold = self._common_content_configuration.memory_mlc_idle_lateny_threshold()
        self._peak_memory_bandwidth_threshold = \
            self._common_content_configuration.memory_mlc_peak_memory_bandwidth_threshold()
        self._memory_bandwidth_threshold = self._common_content_configuration.memory_mlc_memory_bandwidth_threshold()

        self._mem_parse_log = MemoryCommonLib(self._log, cfg_opts, self._os, 0)

    def prepare(self):
        # type: () -> None
        """
        1. To install mlc tool
        2. To install fio tool
        3. To get the frequency list from xml file

        :return: None
        """
        self._ipmctl_execute_path = self.ROOT
        self._mlc_execute_path = self._install_collateral.install_mlc()
        self._install_collateral.install_fio()
        self._frequency_list = self._common_content_configuration.frequencies_supported()

    def execute(self):
        """
        To get the frequency from dmi decode output
        To verify DCPMMs in 1LM AppDirect 100% Interleaved modes at the reduced Memory Operational Speed

        :return: True if no errors else False
        """
        dmi_cmd = "dmidecode > dmi.txt"
        self._common_content_lib.execute_sut_cmd(dmi_cmd, "get dmi dmidecode output", self._command_timeout,
                                                 cmd_path=self.ROOT)

        self._common_content_lib.delete_testcaseid_folder_in_host(test_case_id=self.TEST_CASE_ID)
        log_path_to_parse = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self.ROOT, extension=".txt")

        # Check whether the dmi.txt exists in the folder has been done inside the "dmidecode_parser" function.
        dict_dmi_decode_from_tool = self._dmidecode_parser.dmidecode_parser(log_path_to_parse)
        speed_list = list()
        for key, value in dict_dmi_decode_from_tool.items():
            if dict_dmi_decode_from_tool[key]['DMIType'] == 17:
                speed_val = dict_dmi_decode_from_tool[key]['Speed']
                if speed_val != "Unknown":
                    speed_list.append(int(speed_val.split(' ')[0]))
        speed_threshold = min(speed_list)  # speed from the dmi decode output
        frequency_to_be_tested = []

        for each_speed in self._frequency_list:
            if speed_threshold >= int(each_speed):
                frequency_to_be_tested.append(int(each_speed))
        self._log.info("Frequencies to be tested : {}".format(frequency_to_be_tested))
        result = []
        # To update the Memory Frequency in the bios config file.
        for frequency in frequency_to_be_tested:
            cp = config_parser.ConfigParser()
            cp.read(self.BIOS_CONFIG_FILE)
            list_sections = cp.sections()
            if "Memory Frequency" in list_sections:
                cp.get("Memory Frequency", 'Target')
                cp.set("Memory Frequency", 'Target', str(frequency))
                self._memory_frequency = cp.get("Memory Frequency", 'Target')
                self._log.info("Memory Frequency is : {}".format(self._memory_frequency))

            with open(self.BIOS_CONFIG_FILE, 'w') as configfile:
                cp.write(configfile)

            result.append(self.provisioning_app_direct_interleaved())
        return all(result)

    def provisioning_app_direct_interleaved(self):
        """
        1. Set the bios knobs as per the test case.
        2. Reboot the SUT to apply the new bios settings.
        3. Verify the bios knobs that are set.
        4. Clear OS and dmesg logs
        5. Create 1LM 100% AppDirect_Interleaved_DAX
        6. Confirm persistent memory regions are configured as expected.
        7. Create namespaces for the persistent regions.
        8. Verify namespaces and region status.
        9. Execute MLC and FIO tools.

        :return: True if all log files parsed without any errors else False
        """
        self._bios_util.set_bios_knob()  # To set the bios knob setting.
        self._os.reboot(self._reboot_timeout)  # To apply the new bios setting.
        self._bios_util.verify_bios_knob()  # To verify the bios knob settings.

        self._common_content_lib.clear_os_log()  # To clear os logs
        self._common_content_lib.clear_dmesg_log()  # To clear dmesg logs

        return_value = []
        dimm_show = self._cr_provisioning_2lm_mixed_mode.populate_memory_dimm_information(self._ipmctl_execute_path)

        # Get the list of dimms which are healthy and log them.
        self._cr_provisioning_2lm_mixed_mode.get_list_of_dimms_which_are_healthy()

        # Verify the list of dimms which are healthy
        self._cr_provisioning_2lm_mixed_mode.verify_all_dcpmm_dimm_healthy()

        # Verify the firmware version of each dimms
        self._cr_provisioning_2lm_mixed_mode.verify_dimms_firmware_version(
            ipmctl_executor_path=self._ipmctl_execute_path)

        # Verify the device location of each dimms
        self._cr_provisioning_2lm_mixed_mode.verify_dimms_device_locator(ipmctl_executor_path=self._ipmctl_execute_path)

        # Pre-existing namespaces are identified here.
        namespace_info = self._cr_provisioning_2lm_mixed_mode.dcpmm_get_disk_namespace()

        # Remove existing all the namespaces
        self._cr_provisioning_2lm_mixed_mode.dcpmm_check_disk_namespace_initilize(namespace_info)

        self._cr_provisioning_2lm_mixed_mode.delete_pcd_data()

        goal_command = r"ipmctl create -f -goal persistentmemorytype=appdirect"

        # Configure the capacity on all installed DCPMM(s) with 100% persistent memory
        dcpmm_disk_goal = self._cr_provisioning_2lm_mixed_mode.dcpmm_configuration(
            self._ipmctl_execute_path, cmd=goal_command, cmd_str="with 100%  persistent memory")

        # Verify the mode provisioning
        return_value.append(
            self._cr_provisioning_2lm_mixed_mode.verify_app_direct_mode_provisioning(
                mode="pmem", mode_percentage=100, total_memory_result_data=dimm_show,
                app_direct_result_data=dcpmm_disk_goal))
        # Restart the SUT
        self._os.reboot(self._reboot_timeout)

        # Get the present memory resources
        self._cr_provisioning_2lm_mixed_mode.ipmctl_show_mem_resources(self._ipmctl_execute_path)

        # After reboot verify the mode provisioning
        return_value.append(self._cr_provisioning_2lm_mixed_mode.verify_app_direct_mode_provisioning(
            mode="pmem", mode_percentage=100, total_memory_result_data=dimm_show,
            app_direct_result_data=dcpmm_disk_goal))

        # Get the list of all regionX device name
        region_data_list = self._cr_provisioning_2lm_mixed_mode.get_all_region_data_linux()

        # Create namespace for each region
        new_created_namespace_list = self._cr_provisioning_2lm_mixed_mode.create_namespace(
            region_data_list, mode="fsdax")

        # Show present namespaces
        namespace_info = self._cr_provisioning_2lm_mixed_mode.dcpmm_get_disk_namespace()

        # Verify namespace presence
        return_value.append(self._cr_provisioning_2lm_mixed_mode.verify_pmem_device_presence(namespace_info))

        disk_partition_command = "parted -s -a optimal /dev/{} mklabel gpt -- mkpart primary ext4 1MiB 16GB"
        # To partition the disks
        self.disk_partition_linux(new_created_namespace_list, disk_partition_command)

        # Show pmem block info
        self._cr_provisioning_2lm_mixed_mode.show_pmem_block_info()

        linux_cmd_to_create_ex4_file_system = "mkfs -t ext4 /dev/{}"
        # Create an ext4  file system
        self.create_ext4_filesystem(
            new_created_namespace_list, linux_cmd_to_create_ex4_file_system)

        # Create mount point on each Persistent memory device
        self._cr_provisioning_2lm_mixed_mode.create_mount_point(new_created_namespace_list, mode="dax")

        # Verify mount is successful or not
        return_value.append(self._cr_provisioning_2lm_mixed_mode.verify_mount_point(new_created_namespace_list))

        self._cr_provisioning_2lm_mixed_mode.verify_device_partitions(new_created_namespace_list)

        self._common_content_lib.execute_sut_cmd("chmod +x mlc", "giving permissions to mlc", self._command_timeout,
                                                 self._mlc_execute_path)

        self._common_content_lib.execute_sut_cmd("rm -rf {}".format(self.LOG_FOLDER), "To delete log folder",
                                                 self._command_timeout, cmd_path=self.ROOT)
        self._common_content_lib.execute_sut_cmd("mkdir {}".format(self.LOG_FOLDER), "create a log folder",
                                                 self._command_timeout, cmd_path=self.ROOT)

        command = "./mlc -Z 2>&1 | tee -a  /root/mlc_fio_logs/mlc_1lm.log"
        self._log.info("Executing the mlc command ...")
        self._common_content_lib.execute_sut_cmd(command, "mlc command", self._mlc_runtime,
                                                 cmd_path=self._mlc_execute_path)

        mount_points = self.create_fiotest_mount_points(self._cr_provisioning_2lm_mixed_mode.mount_list)

        self._log.info("Executing fio sequential write ...")
        command = "fio --name=write --rw=write --direct=1 --ioengine=sync --bs=256k " \
                  "--iodepth=8 --numjobs=16 --runtime={} --time_based --size=10G  " \
                  "--output=/root/mlc_fio_logs/fio_write.log {}"
        self._fio.fio_sequential_write(mount_points, command)

        self._log.info("Executing fio sequential read ...")
        command = "fio --name=read --rw=read --direct=1 --ioengine=sync --bs=256k " \
                  "--iodepth=8 --numjobs=16 --runtime={} --time_based --size=10G  " \
                  "--output=/root/mlc_fio_logs/fio_read.log {}"
        self._fio.fio_sequential_read(mount_points, command)

        var_log_messages = Path(os.path.join(self.LOG_FOLDER, "var_log_messages.log")).as_posix()
        self._common_content_lib.execute_sut_cmd("less /var/log/messages > {}".format(var_log_messages),
                                                 "var/log/messages ", self._command_timeout)

        journalctl_log_path = Path(os.path.join(self.LOG_FOLDER, "journalctl.log")).as_posix()
        self._common_content_lib.execute_sut_cmd("journalctl -u mcelog.service  > {}".format(journalctl_log_path),
                                                 "Journalctl command", self._command_timeout)

        dmesg_log_path = Path(os.path.join(self.LOG_FOLDER, "dmesg.log")).as_posix()
        self._common_content_lib.execute_sut_cmd("dmesg  > {}".format(dmesg_log_path), "dmesg log command",
                                                 self._command_timeout)

        # To display thermal errors
        thermal_error_data = self._cr_provisioning_2lm_mixed_mode.show_dimm_thermal_error_ipmctl(ipmctl_path=self.ROOT)
        self._log.info("Thermal error data \n{}".format(thermal_error_data))

        # To display media errors
        media_error_data = self._cr_provisioning_2lm_mixed_mode.show_dimm_media_error_ipmctl(ipmctl_path=self.ROOT)
        self._log.info("Media error data \n{}".format(media_error_data))

        # Delete the test case id folder from our host if it is exists.
        self._common_content_lib.delete_testcaseid_folder_in_host(test_case_id=self.TEST_CASE_ID)

        # copy the log files to host.
        log_file_path_host = self._common_content_lib.copy_log_files_to_host(
            test_case_id=self.TEST_CASE_ID, sut_log_files_path=self.LOG_FOLDER, extension=".log")

        self._log.info("Logs parsing for the memory frequency : {}".format(self._memory_frequency))
        return self.log_parsing(log_file_path_host)

    def log_parsing(self, log_file_path_host):
        """
        This function is used for the verification of logs.

        :param log_file_path_host: Log file path in the Host
        :return: True if all log files parsed without any errors else False
        """
        final_result = [
            self._mlc.verify_mlc_log(log_path=os.path.join(log_file_path_host, "mlc_1lm.log"),
                                     idle_latency=self._idle_latency_threshold,
                                     peak_injection_memory_bandwidth=self._peak_memory_bandwidth_threshold,
                                     memory_bandwidth=self._memory_bandwidth_threshold),
            self._fio.fio_log_parsing(log_path=os.path.join(log_file_path_host, "fio_write.log"), pattern="WRITE:"),
            self._fio.fio_log_parsing(log_path=os.path.join(log_file_path_host, "fio_read.log"), pattern="READ:"),
            self._mem_parse_log.parse_log_for_error_patterns(log_path=os.path.join(log_file_path_host, "dmesg.log")),
            self._mem_parse_log.parse_log_for_error_patterns(log_path=os.path.join(log_file_path_host,
                                                                                     "journalctl.log")),
            self._mem_parse_log.parse_log_for_error_patterns(log_path=os.path.join(log_file_path_host,
                                                               "var_log_messages.log"), encoding="UTF-8")]
        return all(final_result)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ReducedSpeed1LM100AppDirectInterleavedDAXStressLinux.main() else
             Framework.TEST_RESULT_FAIL)
