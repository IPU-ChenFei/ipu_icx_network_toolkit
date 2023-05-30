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

import os
import re
import time
import csv

from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.dc_power import DcPowerControlProvider
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider

from src.lib.content_base_test_case import ContentBaseTestCase
from src.provider.storage_provider import StorageProvider
import src.lib.content_exceptions as content_exceptions
from src.lib.install_collateral import InstallCollateral
from src.collateral_scripts.windows_disk_drives import WindowsStorageDevice
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from src.lib.dtaf_content_constants import IOmeterToolConstants, DiskCheckConstant
from src.lib.bios_util import SerialBiosUtil
from src.lib.bios_constants import BiosSerialPathConstants


class StorageCommon(ContentBaseTestCase):
    """
    This Class is Used as Common Class For all the Storage Functionality Test Cases
    """
    C_DRIVE_PATH = "C:\\"
    REQUIRED_MOUNT_SPACE = 500
    ROOT_DIR = "/root"
    CMD_TO_UNMOUT = "umount {}"
    SX_SLEEP_TIME = 150
    POST_SLEEP_DELAY = 30
    AC_POWER_DELAY = 4
    DC_POWER_DELAY = 5
    COPY_FILE_TO_SUT = "storage_test.txt"
    REGEX_TO_GET_SATA_SPEED_LINK = r"SATA\sVersion\sis\:\s+SATA\s\S+\s\S+\s\S+\s\(current\:\s(\S+\s\S+)\)"
    SMARTCTL_CMD_TO_SCAN = r"smartctl.exe --scan"
    CMD_FOR_SATA_LINK_SPEED = r"smartctl.exe -a {}"
    CMD_FOR_SATA_LINK_SPEED_C_DRIVE = r"smartctl.exe -a c:"
    CMD_TO_GET_SATA_SPEED_LINK = r"smartctl -i {} | egrep SATA"
    CMD_TO_COPY_FILE_TO_STORAGE_DEVICE = "cp /root/storage_test.txt {}"
    REGEX_FOR_WINDOWS_SATA_DISK = r"(\/dev\/\S+)\s+\-.*ATA\sdevice"
    SERIAL_NUMBER_REGEX_PATTERN = r"Serial Number[^A-Za-z0-9]*(\S+)"
    TEST_FILE = "test.txt"
    TEST_STRING = 'Testing on SATA'
    DATA_STRING = "TESTING DATA"
    ECHO_CMD_TEST_SATA = "echo '{}' > {}".format(TEST_STRING, TEST_FILE)
    ECHO_CMD_TEST_DATA = "echo '{}' > {}".format(DATA_STRING, TEST_FILE)
    REGEX_CMD_FOR_SOCKET = r"SOCKET{}"
    REGEX_CMD_FOR_PYTHONSV_PORT = r"Port.*pcieg5.*LTSSM.*UP_L0"
    _FILE_NAME = "cscripts_log_file"
    PXP1 = "pxp1"
    PXP2 = "pxp2"
    PXP3 = "pxp3"
    PXP4 = "pxp4"
    PXP5 = "pxp5"
    PORT1 = "Port1"
    PORT2 = "Port2"
    PORT3 = "Port3"
    PORT4 = "Port4"
    PORT5 = "Port5"
    SOCKET = "SOCKET{}"
    VMD_ENABLED = "VMDEnabled_{}"
    VMD_PORT_ENABLED = "VMDPortEnable_{}"
    VMD_HOTPLUG_ENABLE = "VMDHotPlugEnable_{}"
    PORT_MAPPING_DICT = {
        PXP1: PORT1,
        PXP2: PORT2,  # ports has been swapped between port 2 and port 4( IOU3 to IOU1 for socket 1 #BKC 46 onwards)
        PXP3: PORT3,
        PXP4: PORT5,
        PXP5: PORT4,  #ports has been swapped between port 2 and port 4( IOU3 to IOU1 for socket 1 #BKC 46 onwards)
    }
    PCH_PORT_CONFIG_DICT = {}
    VMD_BIOS_ENABLE = "0x01"
    DISK_INFO_REGEX = "Disk\s([0-9])"
    VOLUME_INFO = "Volume\s\d\s+C\s+\S+.*\s*Boot"
    DEVICE_INDEX = 1
    CHECK_M2_DEVICE_STR = "M.2"
    SLOT_MAPPING_DICT = {'left_riser_bottom_slot': {'socket': "SOCKET0", 'pxp_name': 'pxp1'},
                         'left_riser_top_slot': {'socket': "SOCKET0", 'pxp_name': 'pxp2'},
                         'slot_b': {'socket': "SOCKET0", 'pxp_name': 'pxp3'},
                         'slot_e': {'socket': "SOCKET1", 'pxp_name': 'pxp1'},
                         'right_riser_top_slot': {'socket': "SOCKET1", 'pxp_name': 'pxp2'},
                         'right_riser_bottom_slot': {'socket': "SOCKET1", 'pxp_name': 'pxp3'},
                         'mcio_s0_pxp4_pcieg_port0': {'socket': "SOCKET0", 'pxp_name': 'pxp4'},
                         'mcio_s0_pxp4_pcieg_port1': {'socket': "SOCKET0", 'pxp_name': 'pxp4'},
                         'mcio_s0_pxp4_pcieg_port2': {'socket': "SOCKET0", 'pxp_name': 'pxp4'},
                         'mcio_s0_pxp4_pcieg_port3': {'socket': "SOCKET0", 'pxp_name': 'pxp4'},
                         'mcio_s0_pxp5_pcieg_port0': {'socket': "SOCKET0", 'pxp_name': 'pxp5'},
                         'mcio_s0_pxp5_pcieg_port1': {'socket': "SOCKET0", 'pxp_name': 'pxp5'},
                         'mcio_s0_pxp5_pcieg_port2': {'socket': "SOCKET0", 'pxp_name': 'pxp5'},
                         'mcio_s0_pxp5_pcieg_port3': {'socket': "SOCKET0", 'pxp_name': 'pxp5'},
                         'mcio_s1_pxp4_pcieg_port0': {'socket': "SOCKET1", 'pxp_name': 'pxp4'},
                         'mcio_s1_pxp4_pcieg_port1': {'socket': "SOCKET1", 'pxp_name': 'pxp4'},
                         'mcio_s1_pxp4_pcieg_port2': {'socket': "SOCKET1", 'pxp_name': 'pxp4'},
                         'mcio_s1_pxp4_pcieg_port3': {'socket': "SOCKET1", 'pxp_name': 'pxp4'},
                         'mcio_s1_pxp5_pcieg_port0': {'socket': "SOCKET1", 'pxp_name': 'pxp5'},
                         'mcio_s1_pxp5_pcieg_port1': {'socket': "SOCKET1", 'pxp_name': 'pxp5'},
                         'mcio_s1_pxp5_pcieg_port2': {'socket': "SOCKET1", 'pxp_name': 'pxp5'},
                         'mcio_s1_pxp5_pcieg_port3': {'socket': "SOCKET1", 'pxp_name': 'pxp5'},
                         }
    FDISK_CMD = "fdisk -l"
    MKFS_CMD = "mkfs.ext2"
    SMARTCTL_CMD = "smartctl -i {}"
    REGEX_TO_MATCH_MODEL = "Model Family: \s+(.*)\sSSDs"
    REGEX_TO_MATCH_DEVICE = "Device Model:\s+(.*)"

    SHOW_CMD = "intelmas show -intelssd"
    LOAD_CMD = "intelmas load -force -intelssd {}"
    INTELMASTOOL_SUCCESS_MSG1 = "Firmware updated successfully. Please reboot the system."
    INTELMASTOOL_SUCCESS_MSG2 = "The selected drive contains current firmware as of this tool release"
    MNT_POINT = "/mnt/nvme{}"
    NVME_DEVICE_TYPE = "NVMe"
    DEVICE_NAME = 'Pcie_Device_Name'
    PCH_STR = "(PCH)"

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file_path=None):
        """
        Create an instance of StorageCommon Class

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        self._cfg_opts = cfg_opts
        super(StorageCommon, self).__init__(test_log, arguments, cfg_opts, bios_config_file_path=bios_config_file_path)
        cur_path = os.path.dirname(os.path.realpath(__file__))

        self.file_path = self._common_content_lib.get_config_file_path(cur_path, self.COPY_FILE_TO_SUT)
        self._storage_provider = StorageProvider.factory(test_log, self.os, execution_env="os", cfg_opts=cfg_opts)
        self._storage_config_data = self._common_content_configuration.get_supported_sata_port_speed()
        ac_power_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac_power = ProviderFactory.create(ac_power_cfg, test_log)
        dc_power_cfg = cfg_opts.find(DcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._dc_power = ProviderFactory.create(dc_power_cfg, test_log)  # type: DcPowerControlProvider

        self._install_collateral_obj = InstallCollateral(self._log, self.os, cfg_opts)
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._log = test_log
        self._log_file_path = self.get_cscripts_log_file()
        self.execute_timeout = self._common_content_configuration.get_command_timeout()
        self._serial_bios_util = SerialBiosUtil(self.ac_power, self._log, self._common_content_lib, self._cfg_opts)
        self._product_family = self._common_content_lib.get_platform_family()

    def check_ahci_link_speed(self):
        """
        This method is to check the ahci link speed for SATA disk

        return: True if all SATA link speed for SATA found as expected else False
        raise: None
        """
        out_put_list = []
        if OperatingSystems.WINDOWS == self.os.os_type:
            execute_cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=self.SMARTCTL_CMD_TO_SCAN,
                                                                          cmd_str=self.SMARTCTL_CMD_TO_SCAN,
                                                                          execute_timeout=self._command_timeout,
                                                                          cmd_path=self.C_DRIVE_PATH)
            sata_disk_list = re.findall(self.REGEX_FOR_WINDOWS_SATA_DISK, execute_cmd_output)
        else:
            sata_disk_list = []
            sata_disk_info_list = self._storage_provider.enumerate_sata_disks()
            for sata_disk in sata_disk_info_list:
                for sata_disk_key, sata_disk_path in sata_disk.items():
                    if sata_disk_key == self._storage_provider.KEY_DISK_NAME:
                        sata_disk_list.append(sata_disk_path)

        if len(sata_disk_list) > 0:
            for sata_disk in sata_disk_list:
                if OperatingSystems.WINDOWS == self.os.os_type:
                    cmd_out_put = self._common_content_lib.execute_sut_cmd(sut_cmd=self.CMD_FOR_SATA_LINK_SPEED.format(
                        sata_disk),
                        cmd_str=self.CMD_FOR_SATA_LINK_SPEED.format(sata_disk),
                        execute_timeout=self._command_timeout,
                        cmd_path=self.C_DRIVE_PATH)
                else:
                    cmd_out_put = self._common_content_lib.execute_sut_cmd(
                        sut_cmd=self.CMD_TO_GET_SATA_SPEED_LINK.format(sata_disk),
                        cmd_str=self.CMD_TO_GET_SATA_SPEED_LINK.format(sata_disk),
                        execute_timeout=self._command_timeout)
                port_speed = re.findall(self.REGEX_TO_GET_SATA_SPEED_LINK, cmd_out_put)[0]
                if port_speed in self._storage_config_data:
                    self._log.info("Link Speed for disk {} is {} found as expected".
                                   format(sata_disk, port_speed))
                    out_put_list.append(True)
                else:
                    out_put_list.append(False)
                    raise content_exceptions.TestFail("Unexpected Link Speed for Disk {} is found as {}".format(
                        sata_disk, port_speed))
            return all(out_put_list)
        else:
            log_err = "SATA Disk was not available on SUT"
            self._log.error(log_err)
            content_exceptions.TestFail(log_err)

    def check_storage_device_work_fine_after_boot(self, boot_option="restart", storage_devices=['sata', 'nvm', 'usb']):
        """
        This Method is to check the storage device work fine after boot.

        :param boot_option
        :return True if work fine else False
        :raise content exception
        """
        total_disk_list = self._storage_provider.enumerator_storage_device()
        total_disk_available = len(total_disk_list)
        mount_point_list = []
        storage_device_type = []
        storage_device = storage_devices
        for disk_dict in total_disk_list:
            index = 0
            for key, value in disk_dict.items():
                if key == self._storage_provider.KEY_PARTITION_DISK_NAME.format(index):
                    index += 1
                    if not (value[self._storage_provider.KEY_MOUNT_POINT] == self._storage_provider.LVM or
                            value[self._storage_provider.KEY_MOUNT_POINT] == self._storage_provider.SWAP or
                            value[self._storage_provider.KEY_AVAILABLE_DISK_SIZE] < self.REQUIRED_MOUNT_SPACE):
                        mount_point_list.append(value[self._storage_provider.KEY_MOUNT_POINT])
                elif key == self._storage_provider.KEY_BUS_TYPE:
                    storage_device_type.append(value)
        for each_storage_devie in storage_device:
            if each_storage_devie in storage_device_type:
                self._log.info("Storage device type: {} is available procceding test for the device: {}".format(
                    each_storage_devie, each_storage_devie))
            else:
                raise content_exceptions.TestFail("storage device type: {} is not available"
                                                  " ".format(each_storage_devie))

        self._log.info("Copy File to the SUT")
        self.os.copy_local_file_to_sut(self.file_path, self.ROOT_DIR)
        for mount_point in mount_point_list:
            self.os.execute(self.CMD_TO_COPY_FILE_TO_STORAGE_DEVICE.format(mount_point), self._command_timeout)

        self._log.info("Boot the system...")
        if boot_option == "restart":
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)
        elif boot_option == "s5":
            self._log.info("Apply DC Power Cycle to Machine")
            self._dc_power.dc_power_off(self.DC_POWER_DELAY)
            time.sleep(self.SX_SLEEP_TIME)
            self._dc_power.dc_power_on(self.DC_POWER_DELAY)
            self.os.wait_for_os(self.reboot_timeout)
            time.sleep(self.POST_SLEEP_DELAY)
        elif boot_option == "ac_cycle":
            self._log.info("Apply AC Power Cycle to Machine")
            self._common_content_lib.perform_graceful_ac_off_on(self._ac_power)
            self.os.wait_for_os(self.reboot_timeout)

        expected_list = []
        self._log.info("Check all the device is available after boot")
        storage_disk_list_after_boot = self._storage_provider.enumerator_storage_device()
        if total_disk_available == len(storage_disk_list_after_boot):
            self._log.info("All device is available after boot")
        else:
            log_err = "Unexpected list of drive found after boot"
            raise content_exceptions.TestFail(log_err)
        self._log.info("Verify the File exist after boot the Machine")
        for dir_to_check in mount_point_list:
            cmd_out_put = self.os.execute("ls", self._command_timeout, cwd=dir_to_check)
            if cmd_out_put.cmd_failed():
                log_err = "Failed to execute with return value {} and stdout value {}".format \
                    (cmd_out_put.return_code, cmd_out_put.stderr)
                self._log.error(log_err)
                raise content_exceptions.TestFail(log_err)
            if self.COPY_FILE_TO_SUT in cmd_out_put.stdout.strip():
                self._log.info("Copied file exist for mounted drive : {}".format(dir_to_check))
                expected_list.append(True)
            else:
                log_err = "Copied File Does not exist after boot the Machine"
                self._log.error(log_err)
                raise content_exceptions.TestFail(log_err)
            self._common_content_lib.execute_sut_cmd(sut_cmd=self.CMD_TO_UNMOUT.format(dir_to_check), cmd_str="umount",
                                                     execute_timeout=self._command_timeout)

        return all(expected_list)

    def check_storage_drive_before_after_restart(self):
        """
        1. Checking Disk size before restart
        2. Disk drive information before restart
        3. Performs shutdown and boot the SUT
        4. Checking Disk size after restart
        5. Disk drive information after restart
        6. Verify the drive size before and after restart
        7. To check the link speed for SATA disk
        8. Copied a text file to all the sata device

        :return: None
        :raise: content_exceptions.TestFail
        """
        # DiskDrive letter and drive size before restart
        drive_size_info_dict_before_restart = self.get_drive_size_info_dict()
        self._log.info("DiskDrive letter and drive size before restart :{}".format(drive_size_info_dict_before_restart))
        # DiskDrive Information before Restart
        before_restart = self._storage_provider.get_diskdirves()
        self._log.debug("DiskDrive Information before Restart :{}".format(before_restart))

        # Performs shutdown and restart the SUT
        self._common_content_lib.perform_os_reboot(self.reboot_timeout)

        # DiskDrive Information after Restart
        after_restart = self._storage_provider.get_diskdirves()
        self._log.debug("DiskDrive Information after Restart :{}".format(after_restart))

        # DiskDrive size and drive letter after restart
        drive_size_info_dict_after_restart = self.get_drive_size_info_dict()
        self._log.debug("DiskDrive size and drive letter after restart :{}".format(drive_size_info_dict_after_restart))
        self.verify_drive_size(drive_size_info_dict_before_restart, drive_size_info_dict_after_restart)

        self._log.info("To check the ahci link speed for SATA disk")
        # To check the link speed for SATA disk
        self.check_ahci_link_speed()

        # copy text file to all sata drives
        self.copy_text_file_to_all_sata_drives()

    def get_drive_size_info_dict(self):
        """
        This method is getting  drive size

        :return: result_dict
        :raise: content_exceptions.TestNotImplementedError
        """
        sata_device_list = self._storage_provider.enumerate_sata_disks()
        if self.os.os_type == OperatingSystems.WINDOWS:
            result_dict = {}
            for each_sata_device in sata_device_list:
                index = 0
                for key, value in each_sata_device.items():
                    if key == WindowsStorageDevice.KEY_DRIVE_LETTERS:
                        if bool(value):
                            drive_letter = value[WindowsStorageDevice.KEY_DRIVE_LETTER.format(index)]
                            index += 1
                            self._storage_provider.find_disk_size(drive_letter)
                            result_dict[drive_letter] = self._storage_provider.find_disk_size(drive_letter)
        else:
            raise content_exceptions.TestNotImplementedError("Code is not implemented for Linux")
        return result_dict

    def verify_drive_size(self, before_restart_dict, after_restart_dict):
        """
        verifying the before and after restart drive size
        :param before_restart_dict:
        :param after_restart_dict:

        :return: None
        :raise: content_exceptions.TestFail
        """
        for x_values, y_values in zip(before_restart_dict.items(), after_restart_dict.items()):
            if x_values != y_values:
                raise content_exceptions.TestFail("Drive size was not matching before restart:{} "
                                                  "and after restart:{}".format(x_values, y_values))
        self._log.info("Drive size is was matched before restart and aftere restart")

    def copy_text_file_to_all_sata_drives(self):
        """
        Copied the text file into all the drives

        :return: None
        :raise: content_exceptions.TestFail
        """
        sata_device_list = self._storage_provider.enumerate_sata_disks()

        drive_letter = []
        for each_sata_device in sata_device_list:
            index = 0
            for key, value in each_sata_device.items():
                if key == WindowsStorageDevice.KEY_DRIVE_LETTERS:
                    if bool(value):
                        drive_letter.append(value[WindowsStorageDevice.KEY_DRIVE_LETTER.format(index)])
                        index += 1
        self._log.debug("Sata Drive Letter: {}".format(drive_letter))
        for each_partition in drive_letter:
            self._common_content_lib.execute_sut_cmd(sut_cmd=self.ECHO_CMD_TEST_SATA,
                                                     cmd_str="Writing on SATA", execute_timeout=self._command_timeout,
                                                     cmd_path=each_partition.strip() + '\\')
        for each_partition in drive_letter:
            cmd_out_put = self._common_content_lib.execute_sut_cmd(sut_cmd="powershell get-content {}"
                                                                   .format(self.TEST_FILE),
                                                                   cmd_str="Reading from device",
                                                                   execute_timeout=self._command_timeout,
                                                                   cmd_path=each_partition.strip() + '\\')
            if self.TEST_STRING not in cmd_out_put:
                raise content_exceptions.TestFail("Read and Write Operation on SATA device did not happen")
            self._log.debug("Verified IO operation for partition: {}".format(each_partition))
        self._log.info("Read and Write Operation is Successfully Completed and Verified on SATA device")


    def copy_text_file_to_all_drives(self):
        """
        Copied the text file into all the drives

        :return: None
        :raise: content_exceptions.TestFail
        """
        total_disk_list = self._storage_provider.enumerator_storage_device()

        storage_device = ['sata', 'nvm', 'usb']
        drive_letter = []
        # for each_device in total_disk_list:
        index = 0
        for key, value in total_disk_list.items():
            if key == WindowsStorageDevice.KEY_DRIVE_LETTERS:
                if bool(value):
                    drive_letter.append(value[WindowsStorageDevice.KEY_DRIVE_LETTER.format(index)])
                    index += 1
        self._log.debug("Drive Letters: {}".format(drive_letter))
        for each_partition in drive_letter:
            self._common_content_lib.execute_sut_cmd(sut_cmd=self.ECHO_CMD_TEST_DATA,
                                                     cmd_str="Writing data to Drive ", execute_timeout=self._command_timeout,
                                                     cmd_path=each_partition.strip() + '\\')
        for each_partition in drive_letter:
            cmd_out_put = self._common_content_lib.execute_sut_cmd(sut_cmd="powershell get-content {}"
                                                                   .format(self.TEST_FILE),
                                                                   cmd_str="Reading from device",
                                                                   execute_timeout=self._command_timeout,
                                                                   cmd_path=each_partition.strip() + '\\')
            if self.TEST_STRING not in cmd_out_put:
                raise content_exceptions.TestFail("Read and Write Operation on SATA device did not happen")
            self._log.debug("Verified IO operation for partition: {}".format(each_partition))
        self._log.info("Read and Write Operation is Successfully Completed and Verified on SATA device")


    def check_ahci_link_speed_windows(self):
        """
        This method is to check the ahci link speed for SATA disk

        return: True if SATA link speed for SATA found as expected else raise TestFail exception
        raise: TestFail
        """
        cmd_out_put = self._common_content_lib.execute_sut_cmd(
            sut_cmd=self.CMD_FOR_SATA_LINK_SPEED_C_DRIVE, cmd_str=self.CMD_FOR_SATA_LINK_SPEED_C_DRIVE,
            execute_timeout=self._command_timeout, cmd_path=self.C_DRIVE_PATH)
        self._log.debug("command {} : output is \n:{}".format(self.CMD_FOR_SATA_LINK_SPEED_C_DRIVE, cmd_out_put))
        port_speed = re.findall(self.REGEX_TO_GET_SATA_SPEED_LINK, cmd_out_put)[0]
        self._log.info("Port speed is : {}".format(port_speed))
        self._log.info("From config link speed is : {}".format(self._storage_config_data))
        if port_speed in self._storage_config_data:
            self._log.info("Link Speed for disk C:\\ drive is {} found as expected".format(port_speed))
        else:
            raise content_exceptions.TestFail("Link Speed for disk C:\\ drive is not {} found as expected from config".
                                              format(port_speed))
        return True

    def get_cscripts_log_file(self):
        """
        We are getting the Path for Cscripts Log file

        :return: log_file_path
        """
        cur_path = os.path.dirname(os.path.realpath(__file__))
        path = os.path.join(cur_path, self._FILE_NAME)
        return path

    def get_pythonsv_port(self):
        """
        This Method is Used to Get PythonSv Port on which NVMe Card is Connected.

        :return: socket_port, sockets_count
        """
        pcie_slot_list = self._common_content_configuration.get_pcie_socket_slot_data()
        self._log.info("PCIe Cards information from the configuration : {}".format(pcie_slot_list))
        socket_port, sockets_count = self.verify_pcie_sls_command_output(pcie_slot_list)
        return socket_port, sockets_count

    def verify_pcie_sls_command_output(self, pcie_slot_list):
        """
        This function is used to verify pcie.sls() command output

        :param pcie_slot_list: connected PCIe NVMe cards in SUT from config
        :return: socket_port, sockets_count
        """
        # To initialize sdp object
        self.initialize_sdp_objects()
        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)  # type: SiliconRegProvider
        pcie_obj = cscripts_obj.get_cscripts_utils().get_pcie_obj()
        # To get the sockets count
        sockets_count = cscripts_obj.get_socket_count()
        self._log.info("Sockets Count : {}".format(sockets_count))
        self.SDP.start_log(self._log_file_path, "w")
        pcie_obj.sls()
        self.SDP.stop_log()
        with open(self._log_file_path, "r") as log_file:
            log_file_list = log_file.readlines()
        self._log.info("pcie.sls Log file data : {}".format(log_file_list))
        socket_port = []
        # To verify the connected slots in pcie.sls command output
        for each in range(len(log_file_list)):
            pxp_string = re.findall(self.REGEX_CMD_FOR_PYTHONSV_PORT, log_file_list[each])
            if pxp_string:
                pythonsv_port = pxp_string[0].split(".")[0].split(" ")[1]
                log_file = list(map(str.rstrip, log_file_list))
                index = log_file.index(pxp_string[0])
                for socket_index in reversed(range(sockets_count)):
                    if re.findall(self.REGEX_CMD_FOR_SOCKET.format(socket_index), "".join(log_file[each::-1])):
                        socket = self.SOCKET.format(socket_index)
                        socket_port.append({'socket': socket, 'pxp_name': pythonsv_port})
                        self._log.info("Nvme Card is Connected to PythonSv Port {} on {}".format(pythonsv_port, socket))
                        break
        self._log.info("Socket and port information : {}".format(socket_port))
        for slot in pcie_slot_list:
            if self.SLOT_MAPPING_DICT[slot] not in socket_port:
                raise content_exceptions.TestFail("Nvme card is not connected to slot : {} and mapping :{}.Please check"
                                                  " the configuration file.".format(slot, self.SLOT_MAPPING_DICT[slot]))
        return socket_port, sockets_count

    def get_vmd_bios_knobs(self):
        """
        This Method is Used to get VMD BiosKnobs to be Enabled for IOU.
        VMD Config for PCH ports is not listed by this method

        :return:vmd_bios_knobs_list
        """

        socket_port, sockets_count = self.get_pythonsv_port()
        pcie_list = self._common_content_configuration.get_pcie_socket_slot_data()
        vmd_bios_knobs_list = []
        for slot in pcie_list:
            pythonsv_port, socket = self.SLOT_MAPPING_DICT[slot]['pxp_name'], self.SLOT_MAPPING_DICT[slot]['socket']
            self._log.info("Nvme Card is Connected to PythonSv Port {} on {}".format(pythonsv_port, socket))
            bios_mapping_port = self.PORT_MAPPING_DICT[pythonsv_port]
            self._log.debug("Bios Mapping Port is {}".format(bios_mapping_port))

            for socket_index in range(sockets_count):
                self.PCH_PORT_CONFIG_DICT[self.SOCKET.format(socket_index)] = self.VMD_ENABLED.format(socket_index*8)
            pch_port = int(self.PCH_PORT_CONFIG_DICT[socket].split("_")[1])
            base_vmd = self.VMD_ENABLED.format(pch_port+int(bios_mapping_port[-1]))
            vmd_bios_knobs_list.append(base_vmd)
            for index in range((pch_port+int(bios_mapping_port[-1]))*8, ((pch_port+int(bios_mapping_port[-1]))*8)+8):
                vmd_bios_knobs_list.append(self.VMD_PORT_ENABLED.format(index))
            self._log.info("Vmd Bios Knobs Which Needs To be enabled are {}".format(", ".join(vmd_bios_knobs_list)))
        return vmd_bios_knobs_list

    def enable_vmd_bios_knobs(self):
        """
        This Method is Used to Enable Vmd Bios Knobs and Verify.

        :return: None
        :raise: content_exceptions.TestFail if Bios Knobs are Not as Expected.
        """
        vmd_bios_knobs_list = self.get_vmd_bios_knobs()
        self._log.debug("Enabling VMD Bios Knobs : {}".format(vmd_bios_knobs_list))

        call_func_set_bios_knobs = "self.bios.set_bios_knobs("
        for arg in vmd_bios_knobs_list:
            bios_knob = '"' + arg + '"'
            value_to_set = '"' + str(self.VMD_BIOS_ENABLE) + '"'
            call_func_set_bios_knobs = call_func_set_bios_knobs + bios_knob + ", " + value_to_set + ", "

        self._log.info("Executing function : {}".format(call_func_set_bios_knobs))
        call_func_set_bios_knobs = call_func_set_bios_knobs + "overlap=True)"
        # call set_bios_knobs function now
        ret_value = eval(call_func_set_bios_knobs)

        if not ret_value[0]:
            error_log = "Failed to set the bios knobs due to error '{}'".format(ret_value[1])
            self._log.error(error_log)
            raise RuntimeError(error_log)

        self._log.info("VMD BiosKnobs are Enabled and Performing Reboot to Apply the Settings")
        self._common_content_lib.perform_os_reboot(self.reboot_timeout)
        self._log.info("Verifying Bios Settings")
        for knob in vmd_bios_knobs_list:
            actual_knob_value = self.bios_util.get_bios_knob_current_value(knob).strip(r"\r\n\t ")
            self._log.info("Actual Knob value of the %s bios knob is %s", knob, actual_knob_value)
            if eval(actual_knob_value) != eval(self.VMD_BIOS_ENABLE):
                raise content_exceptions.TestFail("%s value is not set" % knob)

    def verify_os_device_info(self, device_type):
        """
        This Method is Used to verify from which device OS is booted.

        :param: Installed OS device type.
        :return: True if found OS booted from device of device_type
        :raise: content_exceptions.TestFail if OS failed to boot from required device.
        """
        with open(IOmeterToolConstants.FILE_NAME, "w+") as fp:
            list_commands = ["List Disk\n"]
            fp.writelines(list_commands)

        self.os.copy_local_file_to_sut(IOmeterToolConstants.FILE_NAME, self.C_DRIVE_PATH)
        disk_info = self._common_content_lib.execute_sut_cmd(r"diskpart /s {}".format(IOmeterToolConstants.FILE_NAME),
                                                             "List Disk",
                                                             self._command_timeout,
                                                             self.C_DRIVE_PATH)
        self._log.info("List Disk Command Output: {}".format(disk_info))
        disk_lists = re.findall(self.DISK_INFO_REGEX, disk_info)
        flag = False
        for digit in disk_lists:
            with open(IOmeterToolConstants.FILE_NAME, "w+") as fp:
                list_commands = ["select disk {}\n".format(digit), "detail disk"]
                fp.writelines(list_commands)

            self.os.copy_local_file_to_sut(IOmeterToolConstants.FILE_NAME, self.C_DRIVE_PATH)
            detail_disk = self._common_content_lib.execute_sut_cmd(r"diskpart /s {}"
                                                                   .format(IOmeterToolConstants.FILE_NAME),
                                                                   "Select Disk", self._command_timeout,
                                                                   self.C_DRIVE_PATH)
            self._log.info("Detail Disk Command Output: {}".format(detail_disk))
            if "Type   : {}".format(device_type).lower() in detail_disk.lower():
                volume_check = re.findall(self.VOLUME_INFO, detail_disk)
                self._log.info("OS Partition Details: {}".format(volume_check))
                if volume_check:
                    flag = True
                    break
        os.remove(IOmeterToolConstants.FILE_NAME)
        if not flag:
            raise content_exceptions.TestFail("OS failed to boot from {} device.".format(device_type))

        return flag

    def copy_csv_file_from_sut_to_host(self, log_dir, log_path, log_name):
        """
        This function copy the IOMeter result.csv file from SUT to HOST

        :param log_dir: Log directory
        :param log_path: Tool installed directory path
        :raise: content_exception.TestFail if not getting csv file path
        """
        find_cmd = "where /R {} {}".format(log_path, log_name)

        self._log.info("Copy the CSV file from SUT to Host")
        csv_file_path = self._common_content_lib.execute_sut_cmd(find_cmd, "Finding path {} file".format(log_name),
                                                                 self._command_timeout, log_path)
        self._log.debug("csv file path {}".format(csv_file_path.strip()))
        if not csv_file_path.strip():
            raise content_exceptions.TestFail("{} file not found".format(log_name))
        self.os.copy_file_from_sut_to_local(csv_file_path.strip(), os.path.join(log_dir, log_name))

    def parse_iometer_result_csv_data(self, filename, column):
        """ parse the iometer result file

        :param filename: csv file
        :param column: column name
        :return: python dictionary format
        """
        data = {}
        with open(filename, 'r') as csvfile:
            # creating a csv reader object
            csvreader = csv.reader(csvfile)
            # extracting field names through device index row
            csvreader_list = list(csvreader)
            for row in range(len(csvreader_list)):
                if column in csvreader_list[row]:
                    self.DEVICE_INDEX = row
                    for element in csvreader_list[self.DEVICE_INDEX]:
                        if element not in data.keys():
                            data[element] = []
                    row_list = csvreader_list[self.DEVICE_INDEX]
                    flag =0
                    for item_list in range(self.DEVICE_INDEX+1, len(csvreader_list)):
                        if flag:
                            break
                        for values in range(len(row_list)):
                            if "PROCESSOR" in csvreader_list[item_list]:
                                flag =1
                                break
                            data[row_list[values]].append(csvreader_list[item_list][values])

        return data

    def get_column_data(self, column, filename):
        """
        Get particular column data of the device.

        :param column: column name.
        :param filename: csv file.
        :return: python list format
        """
        data = self.parse_iometer_result_csv_data(filename, column)

        try:
            if column in data.keys():
                return data[column]
        except KeyError:
            raise content_exceptions.TestFail("%s is not found in the iometer result data" % column)

    def get_smartctl_drive_list(self):
        """
        Get smartctl drive list

        :param column: Non.
        :return: Drive list
        """
        if self.os.os_type == OperatingSystems.LINUX:
            drive_list_cmd = "smartctl --scan"
            path = "/root"

        elif self.os.os_type == OperatingSystems.WINDOWS:
            drive_list_cmd = "smartctl.exe --scan"
            path = r"C:\smart_tools\bin"
        else:
            self._log.error("Smartctl tool is not implented on OS")
            raise NotImplementedError("Smartctl tool is not implented on OS")

        self._log.info("Executing smartctl scan command: {}".format(drive_list_cmd))
        execute_cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=drive_list_cmd,
                                                                      cmd_str=drive_list_cmd,
                                                                      execute_timeout=self._command_timeout,
                                                                      cmd_path=path)
        self._log.debug("Smartctl scan command: {} Output: {}".format(drive_list_cmd, execute_cmd_output))
        drive_list = [line.split(" ")[0] for line in execute_cmd_output.split("\n")]
        drive_list = ' '.join(drive_list).split()
        self._log.debug("Drive list: {}".format(drive_list))

        return drive_list

    def get_drive_name(self, hard_disk_name):
        """
        This Method is to get the drive name from hard disk name

        :param hard_disk_name: hard disk name.
        :return: drive_name
        :raise: content_exception.TestFail if hard_disk_name not connected
        """
        if self.os.os_type == OperatingSystems.LINUX:
            smartctl_cmd = "smartctl -i {} | grep 'Serial Number:'"
            path = "/root"
        elif self.os.os_type == OperatingSystems.WINDOWS:
            smartctl_cmd = "smartctl -i {} | findstr 'Serial Number'"
            path = r"C:\\"
        else:
            self._log.error("Smartctl tool is not implented on OS")
            raise NotImplementedError("Smartctl tool is not implented on OS")

        drive_list = self.get_smartctl_drive_list()
        drive_name_list = list()
        for drive in drive_list:
            cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=smartctl_cmd.format(drive),
                                                                  cmd_str=smartctl_cmd.format(drive),
                                                                  execute_timeout=self._command_timeout,
                                                                  cmd_path=path)
            self._log.debug("SmartCTL Command: {} Output:{}".format(smartctl_cmd.format(drive), cmd_output))
            if re.findall(self.SERIAL_NUMBER_REGEX_PATTERN, cmd_output)[0] in hard_disk_name:
                drive_name_list.append(drive)
        if len(drive_name_list) != 1:
            raise content_exceptions.TestFail("Expected hard drive not found. Please verify the {}"
                                              "the hard drive connected".format(hard_disk_name))
        drive_name = drive_name_list[0].split('/')[-1]
        if self.os.os_type == OperatingSystems.LINUX:
            lsscsi_output = self._common_content_lib.execute_sut_cmd(sut_cmd="lsscsi | grep {}".format(drive_name),
                                                                     cmd_str="executing lsscsi",
                                                                     execute_timeout=self._command_timeout)
            self._log.debug("lsscsi command output {}".format(lsscsi_output))
            regex_output = re.findall(drive_name + ".*", lsscsi_output)
            drive_name = regex_output[0]
        else:
            self._log.error("lsscsi implemented for linux OS")
            raise content_exceptions.TestFail("lsscsi implemented for only linux OS")

        return drive_name

    def check_m_2_device(self):
        """
        Check and verify M.2 device is connected or not

        :return: None
        :raise: content_exception.TestFail if M.2 is not connected
        """
        if self.os.os_type == OperatingSystems.LINUX:
            smartctl_cmd = "smartctl -i {} | grep 'Form Factor:'"
            path = "/root"

        if self.os.os_type == OperatingSystems.WINDOWS:
            smartctl_cmd = r'smartctl.exe -i {}'
            self._install_collateral_obj.copy_smartctl_exe_file_to_sut()
            path = r"C:\\"
        drive_list = self.get_smartctl_drive_list()
        for drive in drive_list:
            cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=smartctl_cmd.format(drive),
                                                                  cmd_str=smartctl_cmd.format(drive),
                                                                  execute_timeout=self._command_timeout,
                                                                  cmd_path=path)
            self._log.debug("SmartCTL Command: {} Output:{}".format(smartctl_cmd.format(drive), cmd_output))
            if self.CHECK_M2_DEVICE_STR in cmd_output:
                self._log.info("M.2 SATA device found. proceeding further")
                break
        else:# else Executed only if there is no break
            raise content_exceptions.TestFail(
                    "M.2 SATA device not found. Please connect M.2 SATA Device and retry")

    def check_m_2_nvme(self):
        """
        Check M.2 NVMe ssd

        :raise: If M.2 NVMe drive is not connected
        :return: if M.2 NVMe drive is connected
        """
        nvme_drive = self._common_content_configuration.get_nvme_m2_drive_name()
        self._log.debug("NVMe M.2 drive name {}".format(nvme_drive))
        diskpart_script_name = "check_disk.txt"
        with open(diskpart_script_name, "w+") as fp:
            list_commands = ["List Disk\n"]
            fp.writelines(list_commands)

        self.os.copy_local_file_to_sut(diskpart_script_name, self.C_DRIVE_PATH)
        disk_info = self._common_content_lib.execute_sut_cmd(r"diskpart /s {}".format(diskpart_script_name),
                                                             "List Disk",
                                                             self._command_timeout,
                                                             self.C_DRIVE_PATH)
        self._log.info("List Disk Command Output: {}".format(disk_info))
        disk_lists = re.findall(self.DISK_INFO_REGEX, disk_info)
        for digit in disk_lists:
            with open(diskpart_script_name, "w+") as fp:
                list_commands = ["select disk {}\n".format(digit), "detail disk"]
                fp.writelines(list_commands)

            self.os.copy_local_file_to_sut(diskpart_script_name, self.C_DRIVE_PATH)
            detail_disk = self._common_content_lib.execute_sut_cmd(r"diskpart /s {}"
                                                                   .format(diskpart_script_name),
                                                                   "Select Disk", self._command_timeout,
                                                                   self.C_DRIVE_PATH)
            self._log.info("Detail Disk Command Output: {}".format(detail_disk))
            if nvme_drive in detail_disk and \
                    "Type   : {}".format(self.NVME_DEVICE_TYPE).lower() in detail_disk.lower():
                self._log.info("M.2 NVMe is connected {}.".format(nvme_drive))
                return
        raise content_exceptions.TestSetupError("M.2 NVMe drive is not connected")

    def format_m_2_nvme_win(self, device_type, format_type="ntfs"):
        """
        Format M.2 NVMe drive
        """
        assign_letter = self._common_content_lib.get_free_drive_letter()
        nvme_m2_drive = self._common_content_configuration.get_nvme_m2_drive_name()
        diskpart_script_name = "check_disk.txt"
        with open(diskpart_script_name, "w+") as fp:
            list_commands = ["List Disk\n"]
            fp.writelines(list_commands)

        self.os.copy_local_file_to_sut(diskpart_script_name, self.C_DRIVE_PATH)
        disk_info = self._common_content_lib.execute_sut_cmd(r"diskpart /s {}".format(diskpart_script_name),
                                                             "List Disk",
                                                             self._command_timeout,
                                                             self.C_DRIVE_PATH)
        self._log.info("List Disk Command Output: {}".format(disk_info))
        disk_lists = re.findall(self.DISK_INFO_REGEX, disk_info)
        format_disk_list = []
        for digit in disk_lists:
            with open(diskpart_script_name, "w+") as fp:
                list_commands = ["select disk {}\n".format(digit), "detail disk"]
                fp.writelines(list_commands)

            self.os.copy_local_file_to_sut(diskpart_script_name, self.C_DRIVE_PATH)
            detail_disk = self._common_content_lib.execute_sut_cmd(r"diskpart /s {}"
                                                                   .format(diskpart_script_name),
                                                                   "Select Disk", self._command_timeout,
                                                                   self.C_DRIVE_PATH)
            self._log.info("Detail Disk Command Output: {}".format(detail_disk))
            if nvme_m2_drive in detail_disk and \
                    "Type   : {}".format(device_type).lower() in detail_disk.lower():
                format_disk_list.append(digit)
                break
        os.remove(diskpart_script_name)

        # formatting the 1st drive from the list
        with open(diskpart_script_name, "w+") as fp:
            list_commands = ["select disk {}\n".format(format_disk_list[0]), "clean\n", "create partition primary\n",
                             "format fs={} quick\n".format(format_type), "assign letter={}\n".format(
                    assign_letter)]
            fp.writelines(list_commands)

        self.os.copy_local_file_to_sut(diskpart_script_name, self.C_DRIVE_PATH)
        format_disk = self._common_content_lib.execute_sut_cmd(r"diskpart /s {}"
                                                               .format(diskpart_script_name),
                                                               "format Disk", self._command_timeout,
                                                               self.C_DRIVE_PATH)
        self._log.info("Detail Disk Command Output: {}".format(format_disk))
        self._log.info("Successfully formatted the {} drive".format(device_type))
        os.remove(diskpart_script_name)

    def verify_device_in_edkii_menu(self, device_name):
        """
        This method is to verify a device in the EDKII menu

        :param device_name : name of the device to be checked in EDKII eg: INTEL SSDPELKX010T8-PHLJ011300641P0I
        :return : None
        :raise: content_exception.TestFail if the device is not connected
        """
        self.FOUND = False
        try:
            self._serial_bios_util.select_edkii_menu()
            time.sleep(60)
            screen_info = self._serial_bios_util.get_current_screen_info()
            self._log.info("Screen Info {}".format(screen_info))
            for item in screen_info[0]:
                if device_name in item:
                    self.FOUND = True
                    self._log.info("Device \'{}\' is found in EDKII Menu page:: {}".format(device_name, item))
            if not self.FOUND:
                raise content_exceptions.TestFail("The device {} not found in EDKII Menu page".format(device_name))
        except Exception as ex:
            self._log.error("An exception occurred:\n{}".format(str(ex)))
        finally:
            if not self.os.is_alive():
                self._log.info("SUT is not alive ...")
                self.perform_graceful_g3()

    def verify_os_boot_device_type_windows(self, device_type):
        """
        This Method is Used to verify from which device OS is booted.
        :param: Installed OS device type.
        :return: True if found OS booted from device of device_type
        :raise: content_exceptions.TestFail if OS failed to boot from required device.
        """
        diskpart_script_name = "check_disk.txt"
        with open(diskpart_script_name, "w+") as fp:
            list_commands = ["List Disk\n"]
            fp.writelines(list_commands)

        self.os.copy_local_file_to_sut(os.path.abspath(diskpart_script_name), self.C_DRIVE_PATH)
        disk_info = self._common_content_lib.execute_sut_cmd(r"diskpart /s {}".format(diskpart_script_name),
                                                             "List Disk",
                                                             self._command_timeout,
                                                             self.C_DRIVE_PATH)
        self._log.info("List Disk Command Output: {}".format(disk_info))
        disk_lists = re.findall(self.DISK_INFO_REGEX, disk_info)
        flag = False
        for digit in disk_lists:
            with open(diskpart_script_name, "w+") as fp:
                list_commands = ["select disk {}\n".format(digit), "detail disk"]
                fp.writelines(list_commands)

            self.os.copy_local_file_to_sut(diskpart_script_name, self.C_DRIVE_PATH)
            detail_disk = self._common_content_lib.execute_sut_cmd(r"diskpart /s {}".format(diskpart_script_name),
                                                                   "Select Disk", self._command_timeout,
                                                                   self.C_DRIVE_PATH)
            self._log.info("Detail Disk Command Output: {}".format(detail_disk))
            if "Type   : {}".format(device_type).lower() in detail_disk.lower() and \
                    "Boot Disk  : Yes".lower() in detail_disk.lower():
                volume_check = re.findall(self.VOLUME_INFO, detail_disk)
                self._log.info("OS Partition Details: {}".format(volume_check))
                if volume_check:
                    flag = True
                    break
        os.remove(diskpart_script_name)
        if not flag:
            raise content_exceptions.TestFail("OS failed to boot from {} device.".format(device_type))

        return flag

    def format_drive_win(self, device_type, format_type="ntfs"):
        """
        This Method is to format nvme drive which is not having OS and assign it to the given drive letter

        :param: Installed OS device type.
        :return: True if found OS booted from device of device_type
        :raise: content_exceptions.TestFail if OS failed to boot from required device.
        """
        assign_letter = ['s', 't', 'u', 'v', 'w', 'x', 'y', 'z']
        diskpart_script_name = "check_disk.txt"
        with open(diskpart_script_name, "w+") as fp:
            list_commands = ["List Disk\n"]
            fp.writelines(list_commands)

        self.os.copy_local_file_to_sut(diskpart_script_name, self.C_DRIVE_PATH)
        disk_info = self._common_content_lib.execute_sut_cmd(r"diskpart /s {}".format(diskpart_script_name),
                                                             "List Disk",
                                                             self._command_timeout,
                                                             self.C_DRIVE_PATH)
        self._log.info("List Disk Command Output: {}".format(disk_info))
        disk_lists = re.findall(self.DISK_INFO_REGEX, disk_info)
        format_disk_list = []
        for digit in disk_lists:
            with open(diskpart_script_name, "w+") as fp:
                list_commands = ["select disk {}\n".format(digit), "detail disk"]
                fp.writelines(list_commands)

            self.os.copy_local_file_to_sut(diskpart_script_name, self.C_DRIVE_PATH)
            detail_disk = self._common_content_lib.execute_sut_cmd(r"diskpart /s {}"
                                                                   .format(diskpart_script_name),
                                                                   "Select Disk", self._command_timeout,
                                                                   self.C_DRIVE_PATH)
            self._log.info("Detail Disk Command Output: {}".format(detail_disk))
            if "Boot Disk  : Yes".lower() not in detail_disk.lower() or \
                "Type   : {}".format(device_type).lower() in detail_disk.lower():
                format_disk_list.append(digit)
        os.remove(diskpart_script_name)
        length_disk_list = len(format_disk_list)
        list_disk_drive = list(zip(format_disk_list, assign_letter[0:length_disk_list]))
        # formatting the all drive from the list
        for disk_format, drive_letter in list_disk_drive:
            with open(diskpart_script_name, "w+") as fp:
                list_commands = ["select disk {}\n".format(disk_format), "clean\n", "create partition primary\n",
                                 "format fs={} quick\n".format(format_type), "assign letter={}\n".format(drive_letter)]
                fp.writelines(list_commands)

            self.os.copy_local_file_to_sut(diskpart_script_name, self.C_DRIVE_PATH)
            format_disk = self._common_content_lib.execute_sut_cmd(r"diskpart /s {}"
                                                                   .format(diskpart_script_name),
                                                                   "format Disk", self._command_timeout,
                                                                   self.C_DRIVE_PATH)
            self._log.info("Detail Disk Command Output: {}".format(format_disk))
            self._log.info("Successfully formatted the {} drive".format(device_type))
            os.remove(diskpart_script_name)

    def execute_and_verify_fio_on_all_ssds(self, fio_command, operation):
        """
        This Method executes fio tool on all ssds present in the SUT and verifies if the fio tool is running .

        :param: fio_command : fio command that is to be executed on SUT
        :param: operation : Give any one required operation among these readwrite, randrw
        :raise: content_exception.TestFail if fio tool fails to run
        """
        self._log.info("Execution of FIO tool for {} operation for 200 seconds".format(fio_command))
        self.os.execute_async(fio_command)
        check_process_cmd = "ps -aux | grep fio | grep {}".format(operation)
        cmd_output = self._common_content_lib.execute_sut_cmd(check_process_cmd, check_process_cmd, self._command_timeout)
        self._log.debug("{} Command Output : {}".format(check_process_cmd, cmd_output))
        if cmd_output.count(fio_command)<=1:
            raise content_exceptions.TestFail("The fio command {} failed to execute on all SSDs".format(fio_command))
        self._log.info("The fio Command has been successfully executed on all SSDs")

    def check_ssd_manufacturer_and_model(self, ssd):
        """
        This method executes smartctl -i {ssd name} on SUT and verifies the
        manufacturer and model details from content_configuration.xml file.

        :param ssd : Example /dev/sda - ssd name
        :raise: content_exception.TestFail if model number or manufacture details fail to match.
        """
        cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=self.SMARTCTL_CMD.format(ssd),
                                                              cmd_str=self.SMARTCTL_CMD.format(ssd),
                                                              execute_timeout=self._command_timeout)
        model_from_os = re.findall(self.REGEX_TO_MATCH_MODEL, cmd_output)
        device_from_os = re.findall(self.REGEX_TO_MATCH_DEVICE, cmd_output)
        ssd_details_dict = self._common_content_configuration.get_ssd_device_model_details()
        if not (any(each_device in device_from_os[0] for each_device in ssd_details_dict["device"].split(",")) and any(
                each_model in model_from_os[0] for each_model in ssd_details_dict["model"].split(","))):
            raise content_exceptions.TestFail("Drive Manufacturer and Model Details of SSD did not match!")
        self._log.info("Model Number of {} from OS : {}".format(ssd, model_from_os))
        self._log.info("Device Number of {} from OS : {}".format(ssd, device_from_os))
        self._log.debug("Model Number of {} from Config.xml : {}".format(ssd, ssd_details_dict["model"]))
        self._log.debug("Device Number of {} from Config.xml : {}".format(ssd, ssd_details_dict["device"]))
        self._log.info("Drive Manufacturer and Model Details of {} is as expected.".format(ssd))

    def get_intelssd(self):
        """
        This method returns the intel SSDs present in the system
        :return: List of SSD ID's of Intel SSDs connected in the system
        """
        # Run show command to get the SSD details
        show_cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=self.SHOW_CMD,
                                                                   cmd_str=self.SHOW_CMD,
                                                                   execute_timeout=self._command_timeout)
        self._log.debug("Command output : {}".format(show_cmd_output))
        intelssd_list = re.findall("- (\d+) Intel", show_cmd_output)
        return intelssd_list

    def get_ssd_version(self, ssd_id):
        """
        This method returns the version of given SSD present in the system

        :param ssd_id: SSD number from intelmas tool show command output
        :return: ssd version
        """
        # Run show command to get the SSD details
        show_cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=self.SHOW_CMD + " " + ssd_id,
                                                                   cmd_str=self.SHOW_CMD + " " + ssd_id,
                                                                   execute_timeout=self._command_timeout)
        self._log.info("{} Command output : {}".format(self.SHOW_CMD + " " + ssd_id, show_cmd_output))
        ssd_version = re.findall("Firmware : (\S+)", show_cmd_output)
        self._log.info("SSD FW version is {}".format(ssd_version))
        return ssd_version[0]

    def upgrade_ssd_fw_and_verify(self, ssd_id):
        """
        This method upgrades the SSD using intelmastool and verifies if the SSD FW is in latest version.
        raise: content_exception.TestFail if FW Upgrade fails
        """
        ssd_version_before_upgrade = self.get_ssd_version(ssd_id)
        ver_num_before_upgrade = int(re.findall("(\d+)", ssd_version_before_upgrade)[0])
        self._log.info("SSD Version before Upgrade = {}".format(ssd_version_before_upgrade))
        load_cmd_output = self.os.execute(self.LOAD_CMD.format(ssd_id), self._command_timeout)
        if not (
                self.INTELMASTOOL_SUCCESS_MSG1 in load_cmd_output.stdout or self.INTELMASTOOL_SUCCESS_MSG2 in load_cmd_output.stdout):
            raise content_exceptions.TestError("{} command execution failed".format(self.LOAD_CMD.format(ssd_id)))
        self._log.info("Intelmas tool load command execution successfull")
        ssd_version_after_upgrade = self.get_ssd_version(ssd_id)
        self._log.info("SSD Version after Upgrade = {}".format(ssd_version_after_upgrade))
        ver_num_after_upgrade = int(re.findall("(\d+)", ssd_version_after_upgrade)[0])
        if ver_num_before_upgrade > ver_num_after_upgrade:
            raise content_exceptions.TestFail("Failed to upgrade the FW Version of given SSD ID {}".format(ssd_id))
        self._log.info("Successfully Upgraded the FW from {} version to {}".format(ssd_version_before_upgrade,
                                                                                   ssd_version_after_upgrade))

    def verify_storage_device(self):
        """
        Check and verify Model and serial number of the device connected
        :return: device Names with serial number and model number
        """
        device_name = []
        cmd_output = None
        device_model = None
        serial_number = None
        # to get the config from windows sut
        if self.os.os_type == OperatingSystems.WINDOWS:
            self._install_collateral_obj.copy_smartctl_exe_file_to_sut()
            smartctl_cmd = r'smartctl.exe -i {} | findstr "Model Number, Serial Number"'
            win_path = r"C:\smart_tools\\bin"
        drive_list = self.get_smartctl_drive_list()  # to get the devices connected
        for drive in drive_list:
            try:
                if self.os.os_type == OperatingSystems.WINDOWS:
                    win_path = r"C:\smart_tools\\bin"
                    device_model = "Model Number"
                    serial_number = "Serial Number"
                    cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=smartctl_cmd.format(drive),
                                                                          cmd_str=smartctl_cmd.format(drive),
                                                                          execute_timeout=self._command_timeout,
                                                                          cmd_path=win_path)
                    self._log.debug("SmartCTL Command: {} Output:{}".format(smartctl_cmd.format(drive), cmd_output))
                elif self.os.os_type == OperatingSystems.LINUX:
                    device_model = "Device Model"
                    serial_number = "Serial Number"
                    smartctl_cmd = r'smartctl -i {}'
                    linux_path = self.ROOT_DIR
                    cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=smartctl_cmd.format(drive),
                                                                          cmd_str=smartctl_cmd.format(drive),
                                                                          execute_timeout=self._command_timeout,
                                                                          cmd_path=linux_path)
                cmd_output = cmd_output.split("\n")
                for devices in cmd_output:
                    if devices.startswith(device_model):
                        device_model = devices.split(":")[1]
                    elif devices.startswith(serial_number):
                        serial_model = devices.split(":")[1]
                        device_name.append(device_model.strip() + " " + serial_model.strip())
            except Exception as e:
                if self.os.os_type == OperatingSystems.WINDOWS:
                    smartctl_cmd = r'smartctl.exe -i {}'
                    cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=smartctl_cmd.format(drive),
                                                                          cmd_str=smartctl_cmd.format(drive),
                                                                          execute_timeout=self._command_timeout,
                                                                          cmd_path=win_path)
                    if "USB" in cmd_output:
                        self._log.info("{} is USB".format(drive))

        device_name = [device.strip() for device in device_name]
        self._log.info(device_name)
        return device_name

    def get_mounted_storage_disks(self, mounting_devices):
        """
        This Method is used to unmount and make ext4 file system then re-mount.
        :param mounting_devices: list of devices needed to be mounted
        """

        for mnt in mounting_devices:
            try:
                self._common_content_lib.execute_sut_cmd("umount {}".format(mnt), "delete mount point",
                                                         self._command_timeout)
                self._common_content_lib.execute_sut_cmd("mkfs.ext4 {}".format(mnt), "make ext4 fs",
                                                         self._command_timeout)
            except Exception as e:
                pass
            finally:
                self._storage_provider.mount_the_drive(mnt, self.MNT_POINT.format(mounting_devices.index(mnt)))

    def verify_disks_in_sut_and_host(self, check=None):
        """
        This method is to get the U.2, M.2, PCIE, NVME devices from the SUT and compare with the inventory.
        """
        inventory_disk = []
        devices_detected_in_sut = self.verify_storage_device()
        devices_connected_list = self._common_content_configuration.get_nvme_storage_device()
        if check=="sata":
            devices_connected_list = self._common_content_configuration.get_sata_storage_device()
        for disk in devices_connected_list:
            if disk.strip() not in devices_detected_in_sut:
                self._log.error("{} Device not detected in SUT, please check the connections".format(
                    disk.strip()))
            self._log.info("{} disk detected in SUT".format(disk.strip()))

    def verify_sata_disks_in_sut_and_host(self):
        """
        This method is to get the SATA devices from the SUT and compare with the inventory.
        """
        devices_detected_in_sut = self.verify_storage_device()
        devices_connected_list = self._common_content_configuration.get_sata_storage_device()
        for disk in devices_connected_list:
            if disk.strip() not in devices_detected_in_sut:
                self._log.error("{} Device not detected in SUT, please check the connections".format(
                    disk.strip()))
            self._log.info("{} disk detected in SUT".format(disk.strip()))

    def enable_vmd_bios_knob_using_port(self, vmd_port):
        """
        This Method is to enable the BIOS KNOBS for IOU ports from all the sockets
        :param vmd_port: Port which you want to enable knobs, ex: iou0, iou1
        """
        vmd_port = int(vmd_port[3]) + 1
        socket_knobs = []
        vmd_bios_knobs_list = []
        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        sockets_count = cscripts_obj.get_socket_count()
        socket_knobs.append(self.VMD_ENABLED.format(vmd_port))
        vmd_bios_knobs_list.append(self.VMD_ENABLED.format(vmd_port))
        vmd_bios_knobs_list.append(self.VMD_HOTPLUG_ENABLE.format(vmd_port))
        for slot in range(1, sockets_count):
            vmd_port += 8
            socket_knobs.append(self.VMD_ENABLED.format(vmd_port))
            vmd_bios_knobs_list.append(self.VMD_ENABLED.format(vmd_port))
            vmd_bios_knobs_list.append(self.VMD_HOTPLUG_ENABLE.format(vmd_port))
        for index in socket_knobs:
            start_index = int(index.split("_")[1]) * 8
            end_index = int(index.split("_")[1]) * 8 + 8
            for list_index in range(start_index, end_index):
                vmd_bios_knobs_list.append(self.VMD_PORT_ENABLED.format(list_index))
        self._log.info("Vmd Bios Knobs Which Needs To be enabled are {}".format(", ".join(vmd_bios_knobs_list)))
        self._log.debug("Enabling VMD Bios Knobs : {}".format(vmd_bios_knobs_list))
        call_func_set_bios_knobs = "self.bios.set_bios_knobs("
        for arg in vmd_bios_knobs_list:
            bios_knob = '"' + arg + '"'
            value_to_set = '"' + str(self.VMD_BIOS_ENABLE) + '"'
            call_func_set_bios_knobs = call_func_set_bios_knobs + bios_knob + ", " + value_to_set + ", "
        self._log.info("Executing function : {}".format(call_func_set_bios_knobs))
        call_func_set_bios_knobs = call_func_set_bios_knobs + "overlap=True)"
        # call set_bios_knobs function now
        ret_value = eval(call_func_set_bios_knobs)
        if not ret_value[0]:
            error_log = "Failed to set the bios knobs due to error '{}'".format(ret_value[1])
            self._log.error(error_log)
            raise RuntimeError(error_log)
        self._log.info("VMD BiosKnobs are Enabled and Performing Reboot to Apply the Settings")
        self._common_content_lib.perform_os_reboot(self.reboot_timeout)
        self._log.info("Verifying Bios Settings")
        for knob in vmd_bios_knobs_list:
            actual_knob_value = self.bios_util.get_bios_knob_current_value(knob).strip(r"\r\n\t ")
            self._log.info("Actual Knob value of the %s bios knob is %s", knob, actual_knob_value)
            if eval(actual_knob_value) != eval(self.VMD_BIOS_ENABLE):
                raise content_exceptions.TestFail("%s value is not set" % knob)

    def check_disk_detected_intel_vroc(self, disk_type=None):
        """
        This Method is used to check the devices that connected are being
        detected after enabling the VMD BIOS Knobs
        """
        # get connected NVME device names from content config file
        self._log.info("Getting NVME Name info from config file")
        if disk_type == "PCIE":
            nvme_drive_list = self._common_content_configuration.get_pcie_nvme_storage_device()
        elif disk_type == "U2_NVME":
            nvme_drive_list = self._common_content_configuration.get_u2_nvme_storage_device()
        else:
            nvme_drive_list = self._common_content_configuration.get_nvme_storage_device()
        self._log.info("Navigating to the BIOS Page")
        status, ret_val = self._serial_bios_util.navigate_bios_menu()
        if not status:
            raise content_exceptions.TestFail("Bios Knobs did not navigate to the Bios Page")
        serial_path = BiosSerialPathConstants.INTEL_VROC_NVME_CONTROLLER[self._product_family.upper()]
        self._serial_bios_util.select_enter_knob(serial_path)
        screen_info = self._serial_bios_util.get_current_screen_info()
        vmd_disk_bios = re.findall("INTEL\s\S+\sSN:\S+", str(screen_info[0]))
        for disk in vmd_disk_bios:
            model = disk.split("SN:")[0].strip()
            serial = disk.split("SN:")[1].split(",")[0].strip()
            disk_from_serial = model + " " + serial
            if disk_from_serial not in nvme_drive_list:
                raise content_exceptions.TestFail("{} disk not detected in VMD Controller".format(disk_from_serial))
            self._log.info("{} disk detected in VMD Controller".format(disk_from_serial))
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self.os.wait_for_os(self.reboot_timeout)

    def get_m_2_device(self):
        """
        Function is used to get the M.2 device name connected in SUT.

        return :drive : like /dev/sda
        """
        smartctl_cmd = None
        path = None
        drive_list = self.get_smartctl_drive_list()
        self._log.info("Drive list : {}".format(drive_list))
        if self.os.os_type == OperatingSystems.LINUX:
            smartctl_cmd = "smartctl -i {}"
            path = "/root"

        if self.os.os_type == OperatingSystems.WINDOWS:
            smartctl_cmd = r'smartctl.exe -i {}'
            self._install_collateral_obj.copy_smartctl_exe_file_to_sut()
            path = r"C:\\"

        for drive in drive_list:
            cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=smartctl_cmd.format(drive),
                                                                  cmd_str=smartctl_cmd.format(drive),
                                                                  execute_timeout=self._command_timeout,
                                                                  cmd_path=path)
            self._log.debug("SmartCTL Command: {} Output:{}".format(smartctl_cmd.format(drive), cmd_output))
            if self.CHECK_M2_DEVICE_STR in cmd_output:
                self._log.info("M.2 SATA device found. proceeding further")
                break
        else:  # else Executed only if there is no break
            raise content_exceptions.TestFail(
                "M.2 SATA device not found. Please connect M.2 SATA Device and retry")
        return drive

    def format_assign_drive_m_2_win(self, format_type="ntfs"):
        """
        This Method is to format M.2 drive which is not having OS and assign it to the drive letter

        :raise: content_exceptions.TestFail if OS booted from M.2 device.
        """
        if self.os.os_type == OperatingSystems.WINDOWS:
            self._install_collateral_obj.copy_smartctl_exe_file_to_sut()
            drive_list = self.get_smartctl_drive_list()
            smartctl_cmd = r'smartctl.exe -i {}'
            path = r"C:\smart_tools\bin"
            for index in range(len(drive_list)):
                cmd_output = self._common_content_lib.execute_sut_cmd(
                    sut_cmd=smartctl_cmd.format(drive_list[index]), cmd_str=smartctl_cmd.format(drive_list[index]),
                    execute_timeout=self._command_timeout, cmd_path=path)
                self._log.debug("SmartCTL Command: {} Output:{}".format(smartctl_cmd.format(drive_list[index]),
                                                                        cmd_output))
                if self.CHECK_M2_DEVICE_STR in cmd_output:
                    self._log.info("M.2 SATA device found. proceeding further")
                    break
            else:  # else Executed only if there is no break
                raise content_exceptions.TestFail("M.2 device not found. Please connect M.2 SATA Device and retry")
            self._log.info("M.2 storage disk number : {} :".format(index))
            diskpart_script_name = "check_disk.txt"

            with open(diskpart_script_name, "w+") as fp:
                list_commands = ["select disk {}\n".format(index), "detail disk"]
                fp.writelines(list_commands)

            self.os.copy_local_file_to_sut(diskpart_script_name, self.C_DRIVE_PATH)
            detail_disk = self._common_content_lib.execute_sut_cmd(
                r"diskpart /s {}".format(diskpart_script_name), "Select Disk", self._command_timeout, self.C_DRIVE_PATH)
            self._log.info("Detail Disk Command Output: {}".format(detail_disk))
            if "Boot Disk  : Yes".lower() in detail_disk.lower():
                raise content_exceptions.TestFail("We can not format the booted Storage device ...")
            os.remove(diskpart_script_name)
            assign_letter = self._common_content_lib.get_free_drive_letter()  # To get free drive letter
            # formatting the M.2 drive
            with open(diskpart_script_name, "w+") as fp:
                list_commands = ["select disk {}\n".format(index), "clean\n", "create partition primary\n",
                                 "format fs={} quick\n".format(format_type), "assign letter={}\n".format(assign_letter)]
                fp.writelines(list_commands)

            self.os.copy_local_file_to_sut(diskpart_script_name, self.C_DRIVE_PATH)
            format_disk = self._common_content_lib.execute_sut_cmd(
                r"diskpart /s {}".format(diskpart_script_name), "format Disk", self._command_timeout, self.C_DRIVE_PATH)
            self._log.info("Detail Disk Command Output: {}".format(format_disk))
            os.remove(diskpart_script_name)

    def enable_slot_c_knob(self):
        """
        This method is used to enable slot c knobs
        """
        self.product_family = self._common_content_lib.get_platform_family()
        slot_c_info = self._common_content_configuration.get_pch_slot_c_spr_info(self.product_family)
        self._log.info("PCIE NVME Drive connected to Slot C is {}".format(slot_c_info[self.DEVICE_NAME]))
        self._log.info("Navigating to the BIOS Page")
        status, ret_val = self._serial_bios_util.navigate_bios_menu()
        if not status:
            content_exceptions.TestFail("Bios Knobs did not navigate to the Bios Page")

        serial_path = BiosSerialPathConstants.INTEL_VROC_NVME_CONTROLLER[self.product_family.upper()]
        self._serial_bios_util.select_enter_knob(serial_path)
        screen_info = self._serial_bios_util.get_current_screen_info()
        self._log.debug("Intel VROC VMD Controller output is {}".format(screen_info))
        flag = 0
        for each_line in screen_info[0]:
            if re.search(slot_c_info[self.DEVICE_NAME], each_line):
                index_value = screen_info[0].index(each_line)
                if re.search(self.PCH_STR, screen_info[0][index_value + 1]):
                    self._log.info("SLOT C connected drive {} and drive detect under VROC VMD controller {} are same".
                                   format(slot_c_info[self.DEVICE_NAME], each_line))
                    flag += 1
                    break
        if flag == 0:
            raise content_exceptions.TestFail("SLOT C connected drive {} not detected under VROC VMD controller".
                                              format(slot_c_info[self.DEVICE_NAME]))
        self._serial_bios_util.go_back_a_screen()
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self._log.info("Waiting for SUT to boot to OS..")
        self.os.wait_for_os(self.reboot_timeout)
        self._log.info("System boot to RHEL/Centos OS successfully with PCH slot enabled")

    def enable_vmd_bios_knob_using_port_socket(self, vmd_port, socket_number):
        """
        This Method is to enable the BIOS KNOBS for specific IOU of specific socket
        e.x. ("iou0", 0) which will enable VMD for socket 0 IOU0 all port 
        :param vmd_port: Port which user want to enable knobs, ex: iou0, iou1
        :param socket_number: Socket  numberto enable VMD, e.g.: 0 for socket 0, 1 for socket 1
        """
        vmd_port = int(vmd_port[3]) + 1
        socket_knobs = []
        vmd_bios_knobs_list = []
        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        socket_knobs.append(self.VMD_ENABLED.format(vmd_port))
        vmd_bios_knobs_list.append(self.VMD_ENABLED.format(vmd_port))

        self._log.info(f"Enabling VMD for Port: {vmd_port} of Socket: {socket_number} .")
        
        for slot in range(socket_number):
            vmd_port += 8
            socket_knobs.append(self.VMD_ENABLED.format(vmd_port))
            vmd_bios_knobs_list.append(self.VMD_ENABLED.format(vmd_port))

        for index in socket_knobs:
            start_index = int(index.split("_")[1]) * 8
            end_index = int(index.split("_")[1]) * 8 + 8
            for list_index in range(start_index, end_index):
                vmd_bios_knobs_list.append(self.VMD_PORT_ENABLED.format(list_index))

        self._log.info("VMD Bios Knobs Which are going to be enabled are {}".format(", ".join(vmd_bios_knobs_list)))
        self._log.debug("Enabling VMD Bios Knobs : {}".format(vmd_bios_knobs_list))

        # preparing set_bios_knobs_function 
        call_func_set_bios_knobs = "self.bios.set_bios_knobs("
        
        for arg in vmd_bios_knobs_list:
            bios_knob = '"' + arg + '"'
            value_to_set = '"' + str(self.VMD_BIOS_ENABLE) + '"'
            call_func_set_bios_knobs = call_func_set_bios_knobs + bios_knob + ", " + value_to_set + ", "
        
        self._log.info("Executing function : {}".format(call_func_set_bios_knobs))
        
        call_func_set_bios_knobs = call_func_set_bios_knobs + "overlap=True)"
        
        # call set_bios_knobs function now
        ret_value = eval(call_func_set_bios_knobs)
        
        if not ret_value[0]:
            error_log = "Failed to set the bios knobs due to error '{}'".format(ret_value[1])
            self._log.error(error_log)
            raise RuntimeError(error_log)
        
        self._log.info("VMD BiosKnobs are Enabled and Performing Reboot to Apply the Settings")
        self._common_content_lib.perform_os_reboot(self.reboot_timeout)
        self._log.info("Verifying Bios Settings")
        
        for knob in vmd_bios_knobs_list:
            actual_knob_value = self.bios_util.get_bios_knob_current_value(knob).strip(r"\r\n\t ")
            self._log.info("Actual Knob value of the %s bios knob is %s", knob, actual_knob_value)
            if eval(actual_knob_value) != eval(self.VMD_BIOS_ENABLE):
                raise content_exceptions.TestFail("%s value is not set" % knob)
