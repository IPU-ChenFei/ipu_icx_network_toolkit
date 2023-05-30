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
import os
import time
import random

from src.seamless.lib.seamless_common import SeamlessBaseTest
from src.seamless.tests.bmc.constants.ssd_constants import SsdWindows, NvmeConstants, TimeDelay, LinuxPath, RandomSeed
from src.seamless.lib.pm_common import PmCommon, SocwatchCommon
from dtaf_core.lib.dtaf_constants import OperatingSystems


class SsdCommon(SeamlessBaseTest):
    """
    This Class is Used as Common Class For all the SSD FW Test Cases
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SsdCommon

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super().__init__(test_log, arguments, cfg_opts)
        self.device_name = None
        self.device_path = None
        self.vm_artifactory_link = self._common_content_configuration.get_vm_artifactory_link()
        self.activation_start_time = None
        self.activation_end_time = None
        self.activation_time = None
        self.pm_soc = SocwatchCommon(test_log, arguments, cfg_opts)

    def ssd_prepare(self, device_name, device_path, fw_file_path):
        """
        This function will prepare the SSD HW with required tools

        :device_name: ssd device name
        :device_path: ssd device path
        """
        self._log.info("preparing the ssd hw")
        if self._os_type != OperatingSystems.WINDOWS:
            mount_path = self.verify_device_mount(device_name)
            if not mount_path:
                self.format_ssd(device_path, device_name)
                self.mount_device(f"{device_path}p1", device_name)
                mount_path = self.verify_device_mount(device_name)
                if not mount_path:
                    raise RuntimeError("Unable to mount ssd")
            cmd = 'cd {} && ls'.format(LinuxPath.ROOT_PATH)
            result = self.run_ssh_command(cmd, False)
            file_name = os.path.basename(fw_file_path)
            if file_name not in result.stdout:
                self.sut_ssh.copy_local_file_to_sut(fw_file_path, LinuxPath.ROOT_PATH)
            if self.fio:
                self.install_fio()
            if self.vm:
                self.copy_vm_file(destination="/mnt/{}".format(device_name), artifactory_link=self.vm_artifactory_link)
                self.vm_installation_linux(destination="/mnt/{}".format(device_name), server_name=self.vm)
        else:
            self.get_disk_drive_partition(self.ssd_serial_number, self.drive_letter)
            self.sut_ssh.copy_local_file_to_sut(fw_file_path, SsdWindows.C_DRIVE_PATH)
            self.run_ssh_command(f"robocopy {SsdWindows.VM_FOLDER_PATH}  {self.drive_letter}"
                                 f"{SsdWindows.SSD_VM_FOLDER_PATH} {SsdWindows.VM_FILE_NAME} "
                                 f"{SsdWindows.VM_SEAMLESS_FILE_NAME}", log_output=False)
            vm_os_path = f"{self.drive_letter}{SsdWindows.SSD_VM_FOLDER_PATH}{SsdWindows.VM_FILE_NAME}"
            if self.iometer:
                self.install_iometer(self.iometer_tool_path)
            if self.hyperv:
                self.create_hyper_v_windows(self.win_vm_name, vm_os_path)
        if self.ptu:
            PmCommon.ptu_prepare(self)
        if self.socwatch:
            self.pm_soc.socwatch_prepare()

    def update_storage_fw_up_down_grade(self, index, slot_number, fw_file_path):
        """
        This function will upgrade/downgrade fw version for the storage device

        :index: index value of ssd hw
        :slot_number: slot number for ssd hw
        :fw_file_path: fw file path
        """
        self._log.info("Initiating storage FW upgrade/downgrade")
        file_name = os.path.basename(fw_file_path)
        if self._os_type == OperatingSystems.WINDOWS:
            self.activation_start_time = time.time()
            self.run_ssh_command(SsdWindows.FW_UPDATE_CMD.format(index, SsdWindows.C_DRIVE_PATH + file_name, slot_number))
            self.activation_end_time = time.time()

    def get_storage_index(self, disk_details, friendly_name):
        """
        This function will get the storage device index

        :disk_details: SSD disk information
        :friendly_name: SSD disk name
        """
        index = -1
        for line in disk_details.strip().split("\n"):
            index = index - 1
            result = re.search("----", line)
            if result:
                break
        for line in disk_details.strip().split("\n"):
            index = index + 1
            result = re.search(friendly_name, line)
            if result:
                self._log.info("count inside the pattern search {}".format(index))
                return index
        raise RuntimeError("unable to find the index for the ssd device")

    def get_slot_number(self, index):
        """
        This function will search and provide the slot number for the SSD FW
        """
        regex_slot_number = r"SlotNumber\s*:\s{(\w.*)}"
        self._log.info("Verify Storage device FW Version")
        storage_fw_result = self.run_ssh_command(SsdWindows.STORAGE_FW_VERSION.format(index))
        self._log.info("Storage disk FW version slot details {}".format(storage_fw_result.stdout))
        slot_number = re.search(regex_slot_number, storage_fw_result.stdout)
        if not slot_number:
            raise RuntimeError("Not able to find slot number")
        self._log.info("Get the Slot Number {}".format(slot_number.group(1)))
        return slot_number.group(1)[0]

    def verify_fw_version(self, index, exp_fw_version):
        """
        This function verify the fw version
        :index: ssd hw index value
        :exp_fw_version: Expected FW version to verify
        """
        self._log.info("Verify Storage device FW Version")
        storage_fw_result = self.run_ssh_command(SsdWindows.STORAGE_FW_VERSION.format(index))
        if exp_fw_version not in storage_fw_result.stdout:
            self._log.error("Expected FW version is not matching")
            raise RuntimeError("Expected FW version is not matching")
        self._log.info("Successfully verified FW version")

    def pre_update(self, device_name):
        """
                This function will start workload and vm prior to fw update

                :return: NA
        """
        if self.fio:
            self.before_workload = self.get_iostat(device_name)
            self._log.info("Before workload start values {}".format(self.before_workload))
            self.begin_workloads_lin(self.fio_cmd.format(device_name))
            self.after_workload = self.get_iostat(device_name)
            self._log.info("After workload values {}".format(self.after_workload))
            for work in range(LinuxPath.FIO_TABLE_INDEX, len(self.before_workload)):
                if not int(self.before_workload[work]) < int(self.after_workload[work]):
                    raise RuntimeError("Fio workload is not stated properly")

        if self.vm:
            self.run_vm_linux(self.vm)
            time.sleep(TimeDelay.VM_STABLE_TIMEOUT)
            if not self.verify_vm(self.vm):
                raise RuntimeError("VM is not running")

        if self.ptu:
            PmCommon.deleting_file(self)
            PmCommon.execute_ptu_tool(self)

        if self.socwatch:
            self.pm_soc.execute_socwatch_tool()

    def post_update(self):
        """
            This function will stop the workload
        """
        if self.iometer:
            self.kill_iometer_tool()
        if self.fio:
            self.stop_workloads_lin()
        if self.ptu:
            PmCommon.post_update(self)
        if self.socwatch:
            self.pm_soc.copy_socwatch_csv_file_from_sut_to_host()
            CC6_CONDITION = "%s > " + str(self.cc6_value)
            self.pm_soc.verify_core_c_state_residency_frequency(CoreCStates.CORE_C_STATE_CC6,
                                                                CC6_CONDITION %
                                                                CoreCStates.CORE_C_STATE_CC6)

    def update_ssd(self, device_name, filepath, exp_fw_version):
        """
        This function will do upgrade/downgrade ssd fw
        With fio workload and VM as optional

        :device_name:  SSD device name
        :filepath: Location of the FW file
        :exp_fw_version: Expected FW version
        :return: True if update is successful
        """
        if self.vm:
            if not self.verify_vm(self.vm):
                raise RuntimeError("VM is not running")
        if self.seed_value:
            random.seed(self.seed_value)
            self.summary_log.info("Seed value is {}".format(self.seed_value))
        else:
            random_seed = random.randrange(1, RandomSeed.SEED_VALUE)
            random.seed(random_seed)
            self.summary_log.info("Seed value is {}".format(random_seed))
        delay = random.randrange(TimeDelay.DELAY_BW_UPDATE_L, TimeDelay.DELAY_BW_UPDATE_U)
        self._log.info("Waiting {}s before update".format(delay))
        time.sleep(delay)
        if self._os_type != OperatingSystems.WINDOWS:
            nvme_version = self.get_nvme_version()
            self.download_ssd_fw_linux(device_name, filepath)
            self.activate_ssd_fw_linux(nvme_version, device_name)

        # below code is for with reset
        # nvme_reset_cmd = f"sudo nvme reset /dev/nvme0"
        # self.run_ssh_command(nvme_reset_cmd)
            verify_fw_activate = f"sudo nvme id-ctrl /dev/{device_name} | grep fr"
            res = self.run_ssh_command(verify_fw_activate)
            if exp_fw_version not in res.stdout:
                raise RuntimeError("Expected FW Version not Found")

            res = self.run_ssh_command(NvmeConstants.NVME_LIST_CMD)
            nvme_found = False
            for line in res.stdout.split('\n'):
                if device_name in line:
                    if exp_fw_version not in line:
                        self._log.info("Expected FW Version not Found")
                        return False
                    nvme_found = True

            if not nvme_found:
                self._log.info("NVME not found")
                return False
        else:
            if self.iometer:
                self.check_iometer_status()
            if self.hyperv:
                if not self.verify_vm(self.win_vm_name):
                    self.start_hyperv_vm(self.win_vm_name)
            disk_details = self.get_current_version()
            index = self.get_storage_index(disk_details, self.ssd_serial_number)
            slot_number = self.get_slot_number(index)
            self.update_storage_fw_up_down_grade(index, slot_number, filepath)
            self.verify_fw_version(index, exp_fw_version)
            if self.iometer:
                self.check_iometer_status()
            if self.hyperv:
                if not self.verify_vm(self.win_vm_name):
                    raise RuntimeError("VM is not running")
        if self.fio:
            self.after_fw_update = self.get_iostat(device_name)
            for work in range(LinuxPath.FIO_TABLE_INDEX, len(self.after_workload)):
                if not int(self.after_workload[work]) < int(self.after_fw_update[work]):
                    raise RuntimeError("Fio workload is not stated properly")
        if self.vm:
            if not self.verify_vm(self.vm):
                raise RuntimeError("VM is not running")
        self.activation_time = self.activation_end_time - self.activation_start_time
        self._log.info("Activation Time:{}".format(self.activation_time))
        if self.activation_time > 10:
            self._log.info("Warning : Activation time is more then 10S")
        return True

    def download_ssd_fw_linux(self, device_name, filepath):
        """
        This function will download the ssd fw linux

        :device_name: ssd device name
        :filepath: ssd fw file path
        """
        self._log.info("Download the ssd fw")
        fw_download_cmd = f"sudo nvme fw-download /dev/{device_name} --fw {filepath}"
        self.run_ssh_command(fw_download_cmd)

    def activate_ssd_fw_linux(self, nvme_version, device_name):
        """
        This function will activate or commit the ssd fw

        :nvme_version: nvme version
        :device_name: ssd device name
        """
        self._log.info("Activate the ssd fw")
        if nvme_version <= NvmeConstants.NVME_MIN_VERSION:
            fw_activate_cmd = f"sudo nvme fw-activate /dev/{device_name} --slot=0 --action=3"
        else:
            fw_activate_cmd = f"sudo nvme fw-commit /dev/{device_name} --slot=0 --action=3"
        self.activation_start_time = time.time()
        self.run_ssh_command(fw_activate_cmd)
        self.activation_end_time = time.time()

    def format_ssd(self, device_path, device_name):
        """
        Function to Format the ssd

        :device_path: device location
        :device_name: device name
        :return: ssd device partition info
        """
        cmd = "( echo 'd'; echo 'n'; echo 'p'; echo ''; echo ''; echo ''; echo 'w') | fdisk {}".format(device_path)
        self.run_ssh_command(cmd)
        cmd = "fdisk -l {} | grep /dev/{}p".format(device_path, device_name)
        result = self.run_ssh_command(cmd)
        partition_name = re.findall("{}p\d".format('/dev/'+ device_name), result.stdout)
        if len(partition_name) > 0:
            self.run_ssh_command("mkfs.ext4 {}".format(partition_name[0]))
        return partition_name[0]

    def get_ssd_device_path_device_name(self, serial_number):
        """
        Function to fetch the ssd device path and device name from ssd serial number

        :serial_number: device number/Logical name
        :return: device path and device name
        """
        cmd = 'nvme list '
        result = self.run_ssh_command(cmd, False)
        for line in result.stdout.split('\n'):
            if serial_number in line:
                list1 = re.split("\s+", line)
                for i in list1:
                    if "/dev/" in i:
                        var_dev = [i, i.split("/")[2]]
                        if var_dev == "":
                            raise RuntimeError("Unable to find the partition")
                        return var_dev
                raise RuntimeError("Not able to find the /dev path of SSD Serial number: ", self.ssd_serial_number)
        raise RuntimeError("Not able to find the SSD with Serial number: {}".format(self.ssd_serial_number))

    def verify_file_system(self, device_name):
        """
        Function to verify the ssd file system

        :device_name: ssd device name
        :return: True if ssd format is ext4
        """
        cmd = "lsblk -f | grep {}p".format(device_name)
        result = self.run_ssh_command(cmd)

        if result != "" and ("ext4" in result.stdout):
            res = re.findall("{}p\d".format(device_name), result.stdout)
        else:
            self._log.info("Unable to find the partition")
            return False
        if len(res) != 1:
            self._log.info("More partition are present/No partition is present")
            return False
        return True

    def get_device_name_path(self):
        """
        This function will get the device name and path from the ssd serial number
        """
        if self._os_type != OperatingSystems.WINDOWS:
            self.device_path = self.get_ssd_device_path_device_name(self.ssd_serial_number)[0]
            self.device_name = self.get_ssd_device_path_device_name(self.ssd_serial_number)[1]
