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
import re
import pandas as pd


import src.lib.content_exceptions as content_exception
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.bios_provider import BiosProvider
from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.providers.uefi_shell import UefiShellProvider
from dtaf_core.providers.ac_power import AcPowerControlProvider

from src.lib import content_exceptions
from src.lib.common_content_lib import CommonContentLib
from src.lib.memory_dimm_info_lib import MemoryDimmInfo
from src.lib.bios_util import BiosUtil, ItpXmlCli
from src.lib.install_collateral import InstallCollateral
from src.lib.content_configuration import ContentConfiguration
from src.lib.uefi_util import UefiUtil
from src.lib.content_base_test_case import ContentBaseTestCase
from src.memory.lib.memory_common_lib import MemoryCommonLib
from src.provider.copy_usb_provider import UsbRemovableDriveProvider
from src.provider.ipmctl_provider import IpmctlProvider
from src.provider.memory_provider import MemoryProvider


class CrProvisioningTestCommon(ContentBaseTestCase):
    """
    Base class for all CR Provisioning related test cases with Interleaved or Non-Interleaved memory mode.
    This base class covers below glasgow IDs.

    1. 57779
    2. 57207
    3. 57741
    """

    REGEX_CMD_FOR_EXPECTED_APP_DIRECT_MODE = r"RecommendedAppDirectSettings=x[0-9].-\s[0-9]KB\siMC" \
                                              r"\sx\s[0-9]KB\sChannel.*"
    PS_CMD_GET_DCPMM_DISK_LIST = 'powershell.exe "Get-PmemDisk | select DiskNumber"'
    PS_CMD_GET_PMEM_PHYSICAL_DEV = "powershell Get-PmemPhysicalDevice"
    IPMCTL_CMD_SHOW_DIMM = r" show -dimm"
    IPMCTL_CMD_SHOW_TOPOLOGY = r" show -topology"
    IPMCTL_CMD_SHOW_MODES = r" show -d modessupported -system -capabilities"
    PS_CMD_GET_NAMESPACE = "powershell Get-PmemDisk"
    PS_CMD_INITIALIZE_PMEM_DEV = 'powershell.exe "Get-PmemDisk | Get-PmemPhysicalDevice | ' \
                                 'Initialize-PmemPhysicalDevice -Force"'
    PS_CMD_GET_UNUSED_NAMESPACE = "powershell Get-PmemUnusedRegion"
    IPMCTL_CMD_SHOW_GOAL = r" show -goal"
    IPMCTL_CMD_SHOW_MEM_RESOURCES = r" show -memoryresources"
    PS_CMD_FL_INFO = 'powershell.exe "Get-PmemPhysicalDevice | fl"'
    PS_CMD_CREATE_NEW_PMEM_DISK = 'powershell.exe "Get-PmemUnusedRegion | New-PmemDisk"'
    IPMCTL_CMD_DUMP_CONFIG_CSV = r" dump -destination config.csv -system -config"
    IPMCTL_CMD_SHOW_APP_DIRECT_MODE_SETTINGS = r" show -d recommendedappdirectsettings -system -capabilities"
    SYSTEM_INFO_CMD = "Systeminfo"

    C_DRIVE_PATH = "C:\\"
    ROOT = "/root"

    IPMCTL_CMD_SHOW_DIMM_STATUS = r" show -d HealthState,ManageabilityState,FWVersion,DeviceLocator -dimm"
    NDCTL_CMD_GET_NAMESPACE = "ndctl list --namespaces"
    NDCTL_CMD_REMOVE_NAMESPACE = "ndctl destroy-namespace all -f"
    GPRE_CMD_TO_GET_MOUNT_INFO = "mount | grep pmem"
    MOUNT_VERIFICATION_STR = "/dev/{} on "
    LINUX_CMD_TO_GET_PARTITION_INFO = "lsblk"
    CREATE_DIRECTORY_MOUNT_POINT_CMD = "mkdir q /mnt/QM-{}"
    MOUNT_FILE_SYSTEM_CMD = "mount /dev/{} /mnt/QM-{}"
    MOUNT_DAX_FILE_SYSTEM_CMD = "mount -o dax /dev/{} /mnt/QM-{}"
    SHOW_BLOCK_INFO_CMD = "fdisk -l"
    NDCTL_CMD_TO_CREATE_NAMESPACE = "ndctl create-namespace --mode sector --region={}"
    LINUX_CMD_TO_CREATE_EX4_FILE_SYSTEM = "mkfs.ext4 -F /dev/{}"
    NDCTL_CMD_TO_LIST_ALL_REGION = "ndctl list --region=all"
    LINUX_PARTITION_CMD = "parted -s -a optimal /dev/{} mklabel gpt -- mkpart primay ext4 1MiB 32GB"

    PROVISIONING_COMMAND = "ipmctl.efi show -d modessupported -system -capabilities"
    PROVISIONING_DIMM_COMMAND = "ipmctl.efi show -dimm"
    PROVISIONING_APP_DIRECT_COMMAND = "ipmctl.efi show -d recommendedappdirectsettings -system -capabilities"
    NAMESPACE_SHOW_COMMAND = "ipmctl.efi  show -a -namespace"
    NAMESPACE_CLEAR_COMMAND = "ipmctl.efi delete -f -namespace"
    CREATE_GOAL_COMMAND = "ipmctl.efi create -f -goal persistentmemorytype=appdirectnotinterleaved"
    SHOW_MEMEORY_SUPPORT_CMD = "ipmctl.efi  show -memoryresources"
    SHOW_REGION_COMMAND = "ipmctl.efi show -a -region"
    CREATE_REGION_COMMAND = "ipmctl.efi create -f -namespace -region"
    MAP_COMMAND = "map -r"
    SHOW_GOAL_COMMAND = "ipmctl.efi show -goal"
    CONFIG_CSV_COMMAND = "ipmctl.efi dump -destination config_uefi_adni.csv -system -config"
    UEFI_CONFIG_PATH = 'suts/sut/providers/uefi_shell'
    BIOS_BOOTMENU_CONFIGPATH = "suts/sut/providers/bios_bootmenu"

    DELETE_PCD_COMMAND = " delete -f -pcd -dimm"
    CREATE_AUTO_MOUNT_CMD = 'echo "/dev/{} /mnt/QM-{} ext4 defaults,nofail 0 1" >> /etc/fstab'

    IPMCTL_CMD_SHOW_DIMM_THERMAL_ERR_STATUS = " show -error Thermal -dimm"
    IPMCTL_CMD_SHOW_DIMM_MEDIA_ERR_STATUS = " show -error media -dimm"
    IPMCTL_SHOW_MANAGEABILTY_CMD = " show -d ManageabilityState -dimm"

    MEM_REGEX = r"Mem:\s*[0-9]*"

    NAMESPACE_ID_REGX = r"NamespaceId=0x[0-9]*"

    IPMCTL_CMD_DUMP_CURRENT_PROVISION_CONFIG = " dump -destination {} -system -config"
    IPMCTL_CMD_CREATE_GOAL_FROM_CONFIG_FILE = " load -f -source {} -goal"

    IPMCTL_VERSION = "ipmctl.efi version"
    IPMCTL_PCD_CFG = "ipmctl.efi show -dimm -pcd Config"
    IPMCTL_CAPABILITY_CMD = "ipmctl.efi show -system -capabilities"
    IPMCTL_CMD_FOR_100_PERCENT_APP_DIRECT = r"ipmctl create -f -goal PersistentMemoryType=AppDirect"
    IPMCTL_CMD_FOR_100_PERCENT_MEMORY_MODE = r"ipmctl create -f -goal MemoryMode=100"
    IPMCTL_CMD_FOR_50_AD_50_MEMORY_MODE = r"ipmctl create -f -goal MemoryMode=50 PersistentMemoryType=AppDirect"

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None, mode=None):

        super(CrProvisioningTestCommon, self).__init__(test_log, arguments, cfg_opts, bios_config_file)
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        bios_cfg = cfg_opts.find(BiosProvider.DEFAULT_CONFIG_PATH)
        self._bios = ProviderFactory.create(bios_cfg, test_log)

        ac_power_cfg = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac = ProviderFactory.create(ac_power_cfg, test_log)

        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)

        cur_path = os.path.dirname(os.path.realpath(__file__))
        bios_config_file_path = self._common_content_lib.get_config_file_path(cur_path, bios_config_file)
        self._bios_util = BiosUtil(cfg_opts, bios_config_file_path, self._bios, self._log, self._common_content_lib)

        self.windows_home_drive_path = None
        self.store_generated_dcpmm_drive_letters = []

        self._common_content_configuration = ContentConfiguration(self._log)
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        self._command_timeout = self._common_content_configuration.get_command_timeout()
        self._post_mem_capacity = self._common_content_configuration.memory_bios_post_memory_capacity()
        self._dcpmm_mem_capacity = self._common_content_configuration.memory_bios_total_dcpmm_memory_capacity()
        self._variance_percent = self._common_content_configuration.get_memory_variance_percent()

        self._install_collateral = InstallCollateral(self._log, self._os, cfg_opts)

        self.dimm_healthy_list = []
        self.dimm_healthy_and_manageable_list = []
        self.df_dimm_fw_version_op = None
        self.show_dimm_dataframe = None
        self._uefi_util_obj = None
        self._ac_obj = None
        self._uefi_obj = None
        self._bios_boot_menu_obj = None
        self._opt_obj = cfg_opts
        self._test_log_obj = test_log

        self.mount_list = []

        self.ipmctl_cmd_name = self._common_content_lib.get_ipmctl_name()
        self._memory_common_lib = MemoryCommonLib(self._log, cfg_opts, self._os)
        self._ipmctl_provider = IpmctlProvider.factory(test_log, self._os, execution_env="os", cfg_opts=cfg_opts)
        self.create_uefi_obj(self._opt_obj, self._test_log_obj)
        self._ipmctl_provider_uefi = IpmctlProvider.factory(test_log, self._os, execution_env="uefi", cfg_opts=cfg_opts
                                                            , uefi_obj=self._uefi_util_obj)
        self._itp_xmlcli = ItpXmlCli(self._log, cfg_opts)
        self._copy_usb = UsbRemovableDriveProvider.factory(test_log, cfg_opts, self._os)
        self._ipmctl_efi_tool_path_config = self._common_content_configuration.get_ipmctl_efi_file()
        self._memory_provider = MemoryProvider.factory(test_log, cfg_opts=cfg_opts, os_obj=self._os)

    def get_pmem_device(self):
        """
        This is function is used to get the persistent memory device information

        :return get_pmem output
        """
        get_pmem = self._common_content_lib.execute_sut_cmd(
            self.PS_CMD_GET_PMEM_PHYSICAL_DEV, "DCPMM info", self._command_timeout)

        return get_pmem

    def populate_memory_dimm_information(self, ipmctl_path):
        """
        This Function populated memory dimm information by running below ipmctl commands on SUT
        - ipmctl show -topology
        - ipmctl show -dimm
        Finally it will create object of class MemoryDimmInfo.

        :return: show_dimm_command_output
        :raise: RuntimeError for any error during ipmctl command execution or parsing error.
        """
        try:
            self._log.info("Checking the Topology to Identify the DIMMs..")

            ipmctl_show_topology = self._common_content_lib.execute_sut_cmd(
                self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_TOPOLOGY, "DCPMM Topology", self._command_timeout,
                ipmctl_path)

            self.show_topology_output = ipmctl_show_topology.split(",")[0]

            ipmctl_show_dimm = self._common_content_lib.execute_sut_cmd(
                self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_DIMM, "DCPMM info", self._command_timeout, ipmctl_path)

            show_dimm_command_output = ipmctl_show_dimm.split(",")[0]

            # Get manageability output using ipmctl command
            command_result = self._common_content_lib.execute_sut_cmd(
                self.ipmctl_cmd_name + self.IPMCTL_SHOW_MANAGEABILTY_CMD, "DCPMM manageability info",
                self._command_timeout)

            manageability_state_command_output = command_result.split(',')[0]

            # Object creation
            memory_info_obj = MemoryDimmInfo(self.show_topology_output, show_dimm=show_dimm_command_output,
                                             manageability=manageability_state_command_output)

            self.dimm_healthy_list = memory_info_obj.get_dimm_info_healthy()

            self.dimm_healthy_and_manageable_list = memory_info_obj.get_dimm_info_healthy_manageable()

            self.df_dimm_fw_version_op = memory_info_obj.df_dimm_fw_version

            self._log.info("DCPMM topology data frame... \n {} \n".format(self.df_dimm_fw_version_op))

            self.show_dimm_dataframe = memory_info_obj.get_show_dimm_data_frame()

            self._log.info("DCPMM show dimm info data frame... \n {} \n".format(self.show_dimm_dataframe))

            return show_dimm_command_output
        except Exception as ex:
            log_error = "Unable to Execute IPMCTL Commands on SUT {}".format(ex)
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def verify_dimms_firmware_version(self, ipmctl_executor_path=None):
        """
        This method is used to verify the show topology firmware output with pmem device output.

        :return True if we have correct firmware version
        """
        firmware_version_result = []
        if OperatingSystems.WINDOWS in self._os.os_type:
            pmem_device_output = self.get_pmem_device()
            for dimm_fw_version in self.df_dimm_fw_version_op["FWVersion"]:
                if dimm_fw_version != 0:
                    for pmem in pmem_device_output.split("\n"):
                        if str(dimm_fw_version) in pmem:
                            firmware_version_result.append(True)

        elif OperatingSystems.LINUX in self._os.os_type:
            pmem_device_output = self.show_dimm_status_ipmctl(ipmctl_path=ipmctl_executor_path)
            for dimm_fw_version in self.df_dimm_fw_version_op["FWVersion"]:
                if dimm_fw_version != 0:
                    for pmem in pmem_device_output.split("\n"):
                        if str(dimm_fw_version) in pmem.replace(".", ""):
                            firmware_version_result.append(True)
        else:
            self._log.error("Functionality is not supported for this OS %s" % self._os.os_type)
            raise NotImplementedError("Functionality is not supported for this OS %s" % self._os.os_type)

        if len(firmware_version_result) >= len(self.show_dimm_dataframe):
            self._log.info("The firmware version of the DCPMM Dimms are matching..")
        else:
            err_log = "The firmware version of the DCPMM Dimms does not match.."
            self._log.error(err_log)
            raise RuntimeError(err_log)

    def verify_dimms_device_locator(self, ipmctl_executor_path=None):
        """
        This method is used to verify the show topology device locator output with pmem device output.

        :return True if we have correct location of dimm
        """
        deviec_locator_result = []
        pmem_device_output = None
        if OperatingSystems.WINDOWS in self._os.os_type:
            pmem_device_output = self.get_pmem_device()
        elif OperatingSystems.LINUX in self._os.os_type:
            pmem_device_output = self.show_dimm_status_ipmctl(ipmctl_path=ipmctl_executor_path)
        else:
            self._log.error("Functionality is not supported for this OS %s" % self._os.os_type)
            raise NotImplementedError("Functionality is not supported for this OS %s" % self._os.os_type)
        for index in range(len(self.df_dimm_fw_version_op)):
            if self.df_dimm_fw_version_op["HealthState"][index + 1] == "Healthy":
                for pmem in pmem_device_output.split("\n"):
                    if str(self.df_dimm_fw_version_op["DeviceLocator"][index + 1]) in pmem:
                        deviec_locator_result.append(True)

        if len(deviec_locator_result) >= len(self.show_dimm_dataframe):
            self._log.info("The Device location of the DCPMM Dimms are correct..")
        else:
            err_log = "The Device location of the DCPMM Dimms are not correct.."
            self._log.error(err_log)
            raise RuntimeError(err_log)

    def verify_all_dcpmm_dimm_healthy(self):
        """
        This Method is Used to verify all the DCPMM dimms are Healthy Dimm's.

        :return: True if healthy
        """
        if len(self.show_dimm_dataframe) == len(self.dimm_healthy_list):
            self._log.info("All the DCPMM Dimms are healthy")
        else:
            err_log = "One or more DCPMM Dimms are not healthy, please check.."
            self._log.error(err_log)
            raise RuntimeError(err_log)

    def get_list_of_dimms_which_are_healthy(self):
        """
        This Method is Used to Fetch List of All the Healthy Dimm's.

        :return: None
        :raise: RuntimeError if there are no Healthy Dimm's
        """
        if len(self.dimm_healthy_list) > 0:
            for dimm in self.dimm_healthy_list:
                self._log.info("Dimm {} is Healthy".format(dimm))
        else:
            log_error = "We don't have Dimm's which are Healthy.."
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def get_dcpmm_disk_list(self):
        """
        Function to get the DCPMM disk list that needs to be partitioned.

        :return: list of disk numbers
        """
        powershell_list_phy_device = self._os.execute(
            self.PS_CMD_GET_DCPMM_DISK_LIST, self._command_timeout,
            self._common_content_lib.C_DRIVE_PATH)
        digit_list = []

        for disk_num in powershell_list_phy_device.stdout.strip().split("\n"):
            disk_num_striped = disk_num.strip()
            if disk_num_striped.isdigit():
                digit_list.append(disk_num_striped)

        return sorted(digit_list)

    def ipmctl_show_modes(self, ipmctl_path):
        """
        Function to get the DCPMM dimm topology.

        :param ipmctl_path: path of the ipmctl tool
        :return ipmctl_show_sup_mode: supported modes
        """
        # The current App Direct Mode capabilities are as expected for 2LM mixed mode provisioning
        ipmctl_show_sup_mode = self._common_content_lib.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_MODES, "DCPMM mode", self._command_timeout,
            ipmctl_path)
        self._log.info("DCPMM supported modes... \n {}".format(ipmctl_show_sup_mode))

        return ipmctl_show_sup_mode

    def dcpmm_get_disk_namespace(self):
        """
        Function to get the DCPMM disk namespaces information.

        :return dcpmm_disk_namespace: disk namespace info
        """
        dcpmm_disk_namespace = None
        if OperatingSystems.WINDOWS in self._os.os_type:
            dcpmm_disk_namespace = self._common_content_lib.execute_sut_cmd(
                self.PS_CMD_GET_NAMESPACE, "DCPMM disk namespace", self._command_timeout)

        elif OperatingSystems.LINUX in self._os.os_type:
            dcpmm_disk_namespace = self._common_content_lib.execute_sut_cmd(
                self.NDCTL_CMD_GET_NAMESPACE, "DCPMM disk namespace", self._command_timeout)

        else:
            self._log.error("DCPMM functionality is not supported for this OS %s" % self._os.os_type)
            raise NotImplementedError("DCPMM functionality is not supported for this OS %s" % self._os.os_type)

        if dcpmm_disk_namespace != '':
            self._log.info("DCPMM disk namespace... \n {}".format(dcpmm_disk_namespace))
        else:
            self._log.info("There are no namespaces to display.")

        return dcpmm_disk_namespace

    def dcpmm_check_disk_namespace_initilize(self, namespace_info):
        """
        Function to check if there are existing namespaces present, execute the following command to initialize the
        DIMMs and remove all existing namespaces.

        :param namespace_info: namespace.
        :return initialize_dimm: disk namespace info
        """
        initialize_dimm = None

        if OperatingSystems.WINDOWS in self._os.os_type:
            if namespace_info != '':
                initialize_dimm = self._common_content_lib.execute_sut_cmd(
                    self.PS_CMD_INITIALIZE_PMEM_DEV, "DCPMM disk namespace Initialize", self._command_timeout)
                self._log.info("DCPMM disk namespace Initialization started... \n {}".format(initialize_dimm))
            else:
                self._log.info("There are no existing namespaces, continue to configure the installed DCPMM(s)..")

        elif OperatingSystems.LINUX in self._os.os_type:
            if namespace_info != '':
                initialize_dimm_result = self._os.execute(self.NDCTL_CMD_REMOVE_NAMESPACE, self._command_timeout)
                if initialize_dimm_result.cmd_failed():
                    #  Deleting Existing mount points
                    self.umount_existing_devices()
                    self.remove_fstab_data()
                    initialize_dimm = self._common_content_lib.execute_sut_cmd(
                        self.NDCTL_CMD_REMOVE_NAMESPACE, "DCPMM disk namespace Initialize", self._command_timeout)
                self._log.info("DCPMM disk namespace Initialization started... \n {}".format(initialize_dimm))
            else:
                self._log.info("There are no existing namespaces, continue to configure the installed DCPMM(s)..")

        else:
            self._log.error("DCPMM functionality is not supported for this OS %s" % self._os.os_type)
            raise NotImplementedError("DCPMM functionality is not supported for this OS %s" % self._os.os_type)

        return initialize_dimm

    def dcpmm_get_pmem_unused_region(self):
        """
        The unused space now matches the installed persistent memory capacity

        :return dcpmm_disk_unused_region: unused pmem regions
        """

        dcpmm_disk_unused_region = self._common_content_lib.execute_sut_cmd(
            self.PS_CMD_GET_UNUSED_NAMESPACE, "DCPMM un used region", self._command_timeout)
        self._log.info("DCPMM disk un used region... \n {}".format(dcpmm_disk_unused_region))

        return dcpmm_disk_unused_region

    def dcpmm_configuration(self, ipmctl_path, cmd, cmd_str):
        """
        Function to configure DCPMM dimms with appropriate volatile memory and persistent memory.
        Also, to fetch the memory allocation goal and its resources.

        :param ipmctl_path: path of the ipmctl tool.
        :param cmd: holds the command to allocate the mode.
        :param cmd_str: str - holds the info about the command.
        :return dcpmm_disk_goal: goal that was created.
        """

        dcpmm_disk_create_mixed_mode = self._common_content_lib.execute_sut_cmd(
            cmd, "DCPMM mode allocation", self._command_timeout, ipmctl_path)
        self._log.info("DCPMM disk has been created with {}..{}".format(cmd_str, dcpmm_disk_create_mixed_mode))

        # The memory allocation goal has been done.
        dcpmm_disk_goal = self._common_content_lib.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_GOAL, "DCPMM goal", self._command_timeout, ipmctl_path)
        self._log.info("DCPMM disk goal... \n {}".format(dcpmm_disk_goal))

        return dcpmm_disk_goal

    def ipmctl_show_mem_resources(self, ipmctl_path):
        """
        Function to configure DCPMM devices are normal and the DCPMM mapped memory configuration
        matches the applied goal.

        :param ipmctl_path: path of the ipmctl tool.
        :return dcpmm_mem_resource: memory information
        """

        dcpmm_mem_resource = self._common_content_lib.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_MEM_RESOURCES, "DCPMM memory resource", self._command_timeout,
            ipmctl_path)
        self._log.info("DCPMM memory resources... \n {}".format(dcpmm_mem_resource))

        return dcpmm_mem_resource

    def dcpmm_get_pmem_device_fl_info(self):
        """
        Function to list the persistent memory regions.

        :return pmem_phy_device: Pmem regions info.
        """

        pmem_phy_device = self._common_content_lib.execute_sut_cmd(
            self.PS_CMD_FL_INFO, "Pmem regions", self._command_timeout)
        self._log.info("DCPMMs are listed... \n {}".format(pmem_phy_device))

        return pmem_phy_device

    def dcpmm_new_pmem_disk(self):
        """
        Function to configure all available pmem devices with namespaces.

        :return pmem_unused_new: the namespace has been created.
        """

        pmem_unused_new = self._common_content_lib.execute_sut_cmd(
            self.PS_CMD_CREATE_NEW_PMEM_DISK, "DCPMM new namespace", self._command_timeout)
        self._log.info("DCPMM creating new namespaces... \n {}".format(pmem_unused_new))

        return pmem_unused_new

    def create_config_csv(self, ipmctl_path):
        """
        Store the currently configured memory allocation settings for all DCPMMs in the system to a file

        :param ipmctl_path: path of the ipmctl tool.
        :return None
        """

        store_configs = self._common_content_lib.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_DUMP_CONFIG_CSV, "Store the configuration",
            self._command_timeout, ipmctl_path)

        self._log.info("Storing the currently configured memory allocation settings for all DCPMMs "
                       "in the system to a file... \n {}".format(store_configs))

    def verify_provisioning_final_dump_data_csv(self, log_file_path, reserved=None):
        """
        Parsing all the necessary logs.

        :param log_file_path: log file path from host
        :param reserved: Whether the provisioning is reserved or not
        :return: false if the test case is failed log parsing else true
        """
        mode_return = []
        data_frame = pd.read_csv(os.path.join(log_file_path, "config.csv"))
        for row in range(len(data_frame)):
            if reserved:
                if (data_frame.MemorySize[row] + data_frame.AppDirect1Size[row]) == 0:
                    self._log.info("The total capacity of the DCPMM {} is {}, \n"
                                   "Memory mode:{}\nAppDirect mode:{}.".format(row, data_frame.Capacity[row],
                                                                               data_frame.MemorySize[row],
                                                                               data_frame.AppDirect1Size[row]))
                    self._log.info("The verification of the DCPMM reserved provisioning is successful.")
                    mode_return.append(True)
                else:
                    mode_return.append(False)
                    self._log.error("The verification of the DCPMM reserved provisioning is failed.")
            else:
                if data_frame.Capacity[row] == (data_frame.MemorySize[row] + data_frame.AppDirect1Size[row]):
                    self._log.info("The total capacity of the DCPMM {} is {}, matched with the provisioning \n"
                                   "Memory mode:{}\nAppDirect mode:{}.".format(row, data_frame.Capacity[row],
                                                                               data_frame.MemorySize[row],
                                                                               data_frame.AppDirect1Size[row]))
                    self._log.info("The verification of the DCPMM provisioning is successful.")
                    mode_return.append(True)
                else:
                    mode_return.append(False)
                    self._log.error("The verification of the DCPMM provisioning is failed.")

        return all(mode_return)

    def create_partition_dcpmm_disk(self, convert_type, disk_lists, mode="block"):
        """
        Function to create the new DCPMM disk partitions.

        :param convert_type: gpt / mbr
        :param disk_lists: number of DCPMM disks available.
        :param mode: Mode of DCPMM like DAX / Block
        :return: true if the disk is available for partition else false
        """
        if len(disk_lists) != 0:
            for digit in disk_lists:
                drive_letter = self._common_content_lib.get_free_drive_letter()
                self.store_generated_dcpmm_drive_letters.append(drive_letter)
                with open("createpartition.txt", "w+") as fp:

                    list_commands = ["select disk {}\n".format(digit), "attributes disk clear readonly\n",
                                     "convert {}\n".format(convert_type), "create partition primary\n",
                                     "assign letter={}\n".format(drive_letter)]
                    fp.writelines(list_commands)

                self._os.copy_local_file_to_sut("createpartition.txt", self.C_DRIVE_PATH)
                create_partition = self._common_content_lib.execute_sut_cmd(r"diskpart /s createpartition.txt",
                                                                            "Partition creation",
                                                                            self._command_timeout,
                                                                            self.C_DRIVE_PATH)
                self._log.info("A new partition has been created with letter {} and .."
                               "{}".format(drive_letter, create_partition))

                if mode == 'block':
                    mode_cmd = "/q /y"
                else:
                    mode_cmd = "/q /y /dax"
                format_disk = self._common_content_lib.execute_sut_cmd("format {}: {}".format(drive_letter, mode_cmd),
                                                                       "Format the new partition",
                                                                       self._command_timeout)
                self._log.info("{}".format(format_disk))

            if os.path.exists("createpartition.txt"):
                os.remove("createpartition.txt")

            self._os.reboot(self._reboot_timeout)
            return True
        else:
            err_log = "Unable to locate any DCPMM disks.."
            self._log.error(err_log)
            raise RuntimeError(err_log)

    def verify_disk_partition(self, disk_lists, drive_letters=None):
        """
        Function to verify that the partitions are created correctly.

        :param disk_lists: number of DCPMM disks available.
        :param drive_letters: number of partition letters in list.
        :return: true if partitions are created else false
        """
        ret_val = []
        detail_disk = None

        if drive_letters:
            self.store_generated_dcpmm_drive_letters = list(drive_letters)

        if len(disk_lists) != 0:
            for digit in disk_lists:
                with open("verifypartition.txt", "w+") as file_listdisk:
                    list_commands = ["list volume\n", "list disk\n", "select disk {}\n".format(digit), "detail disk"]
                    file_listdisk.writelines(list_commands)

                self._os.copy_local_file_to_sut("verifypartition.txt", self.C_DRIVE_PATH)

                detail_disk = self._common_content_lib.execute_sut_cmd("diskpart /s verifypartition.txt",
                                                                       "Partition information",
                                                                       self._command_timeout, self.C_DRIVE_PATH)
                self._log.info(
                    "Information on the created disks are shown below... \n {}".format(detail_disk))

            rm_dup_list_current_drive_letters = []
            list_healthy_operational_drives = []

            if re.search("Partition", detail_disk):
                list_healthy_operational_drives = re.findall(r"Healthy", detail_disk, re.IGNORECASE)

                list_current_drive_letters = re.findall(r"\s[A-BD-Z]\s", detail_disk)

                rm_dup_list_current_drive_letters = list(dict.fromkeys(list_current_drive_letters))

                rm_dup_list_current_drive_letters = [ltr.strip(' ') for ltr in
                                                     rm_dup_list_current_drive_letters]

            self._log.info("Current drive letters present in the system, {}".format
                           (rm_dup_list_current_drive_letters))

            self._log.info("Partitioned drive letters, {}".format(self.store_generated_dcpmm_drive_letters))

            if len(list_healthy_operational_drives) >= len(rm_dup_list_current_drive_letters):
                self._log.info("The operational status is 'healthy' for all the drive letters..")
                ret_val.append(True)
            else:
                self._log.error("The operational status is not 'healthy' for all the drive letters..")
                ret_val.append(False)

            if len(self.store_generated_dcpmm_drive_letters) != 0:
                res = list(set(sorted(rm_dup_list_current_drive_letters)).intersection(sorted(
                    self.store_generated_dcpmm_drive_letters)))
                if len(res) == len(self.store_generated_dcpmm_drive_letters):
                    self._log.info("Pmem volumes/disks are listed showing correct drive letters..")
                    ret_val.append(True)
                else:
                    self._log.error("Pmem volumes/disks are listed not showing correct drive letters..")
                    ret_val.append(False)

            if os.path.exists("verifypartition.txt"):
                os.remove("verifypartition.txt")

            return all(ret_val)
        else:
            err_log = "Unable to locate any DCPMM disks.."
            self._log.error(err_log)
            raise RuntimeError(err_log)

    def verify_dimm_info(self, dimm_result):
        """
        Function to verify if Device Types are INVDIMM device and HealthStatus is Healthy

        :param dimm_result: result of the dimm info command.
        :return: True on success else False
        """

        result_flag = False
        if ("INVDIMM" in dimm_result) and ("Healthy" in dimm_result):
            result_flag = True
        if not result_flag:
            error_msg = "INVDIMM Devices are not found or DIMMs are Unhealthy!"
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully verified DIMM Information.")
        return result_flag

    def verify_provisioning_mode(self, result_data):
        """
        Function to verify if ModesSupported=1LM, Memory Mode and App Direct are present within the IPMCTL App Direct
        Mode capability command

        :param result_data: Dimm information.
        :return: True on success
        :raise: RuntimeError
        """
        if not ("ModesSupported=1LM" and "Memory Mode" and "App Direct" in result_data):
            error_msg = "Expected provisioning mode is not supported.."
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully verified the expected provisioning mode..")
        return True

    def get_app_direct_mode_data(self, result_data):
        """
        Function to get the AppDirect1Size value after provisioning

        :param result_data: Dimm information.
        :return: app_direct1size_list
        """
        app_direct1size_list = []
        match_data = re.findall("0x.*", result_data)
        if len(match_data) != 0:
            for element in match_data:
                app_direct1size_list.append(float(element.split("|")[3].strip().split(" ")[0]))
        self._log.info("AppDirect1Size values are: {}".format(app_direct1size_list))
        return app_direct1size_list

    def get_memory_mode_data(self, result_data):
        """
        Function to get the AppDirect1Size value after provisioning

        :param result_data: Dimm information.
        :return: memory_mode_list
        """
        memory_mode_list = []
        match_data = re.findall("0x.*", result_data)
        if len(match_data) != 0:
            for element in match_data:
                memory_mode_list.append(float(element.split("|")[2].strip().split(" ")[0]))
        self._log.info("Memory mode values are: {}".format(memory_mode_list))

        return memory_mode_list

    def verify_app_direct_mode_provisioning(self, mode, mode_percentage, total_memory_result_data,
                                            app_direct_result_data, reserved=None):
        """
        Function to verify if the Provisioning is happened with the given percentage

        :param mode: Memory or persistent or mixed mode
        :param mode_percentage: Mode provisioning percent.
        :param total_memory_result_data: Total DCPMM capacity.
        :param app_direct_result_data: Provisioning result data.
        :param reserved: provisioning mode.
        :return: True on success
        :raise: RuntimeError
        """
        #  Total DIMM values before Provisioning
        before_provisioning_dimm_values = self._memory_common_lib.get_total_dimm_memory_data(total_memory_result_data)

        #  Get the expected DIMM value
        threshold_value_list = list(map(lambda x: x * (mode_percentage / 100), before_provisioning_dimm_values))

        #  Get threshold DIMM values of +5%
        celling_threshold_value_list = list(map(lambda x: x + (x * 0.05), threshold_value_list))

        #  Get threshold DIMM values of -5%
        floor_threshold_value_list = list(map(lambda x: x - (x * 0.05), threshold_value_list))

        #  Get the actual DIMM value after Provisioning
        if mode == "mem":
            after_provisioning_dimm_values = self.get_memory_mode_data(app_direct_result_data)
        else:
            after_provisioning_dimm_values = self.get_app_direct_mode_data(app_direct_result_data)

        if reserved:
            result = all(after_provisioning_dimm_values[index] == 0 for index in range(
                0, len(after_provisioning_dimm_values)))
        else:
            #  Compare the current values with the expected ones
            result = all(floor_threshold_value_list[index] < after_provisioning_dimm_values[index]
                         < celling_threshold_value_list[index] for index in
                         range(0, len(after_provisioning_dimm_values)))

        if not result:
            error_msg = "Failed to configure {}% of the DCPMM capacity as per provisioning..".format(mode_percentage)
            self._log.error(error_msg)
            raise RuntimeError(error_msg)

        self._log.info(
            "Successfully configured {}% of the DCPMM capacity as per provisioning..".format(mode_percentage))
        return True

    def verify_recommended_app_direct_mode(self, app_direct_result_data,
                                           pattern=r"RecommendedAppDirectSettings=x[\d]*\s[(ByOne)]*|"
                                                   r"RecommendedAppDirectSettings=x[\d*]\s-\s[\d*][A-Z]*\siMC\sx\s["
                                                   r"\d*][A-Z]*\sChannel"):
        """
        Function to verify if Recommended App Direct Settings is present.

        :param: app_direct_result_data
        :param: pattern: which type pattern to check against.
        :return: True on success
        :raise: RuntimeError
        """
        match_found = False
        if pattern is not None:
            for line in app_direct_result_data:
                if re.search(pattern, line):
                    match_found = True
            if not match_found:
                error_msg = "Expected Pattern or App Direct Mode Setting is not correct, please check again.."
                self._log.error(error_msg)
                raise RuntimeError(error_msg)
        else:
            error_msg = "Expected Pattern is not available, please check again.."
            self._log.error(error_msg)
            raise RuntimeError(error_msg)

        self._log.info("Successfully Verified Expected App Direct Mode Settings")
        return True

    def dcpmm_get_app_direct_mode_settings(self, ipmctl_path):
        """
        Function to  display the recommended App Direct Mode setting capabilities

        :param: Path of ipmctl tool
        :return dcpmm_disk_namespace: disk namespace info
        """

        dcpmm_app_direct_mode_settings = self._common_content_lib.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_APP_DIRECT_MODE_SETTINGS, "To display the recommended "
            "App Direct Mode setting capabilities", self._command_timeout, ipmctl_path)
        if dcpmm_app_direct_mode_settings != '':
            self._log.info("App Direct Mode Settings capabilities... \n {}".format(dcpmm_app_direct_mode_settings))

        return dcpmm_app_direct_mode_settings

    def ipmctl_get_system_capability(self):
        """
        Function to configure all available pmem devices with namespaces.

        :return ipmctl_system_cap: the namespace has been created.
        """

        ipmctl_system_cap = self._common_content_lib.execute_sut_cmd(
            "ipmctl.exe show -system -capabilities", "Get system capability", self._command_timeout)
        self._log.info("DCPMM system capabiities... \n {}".format(ipmctl_system_cap))

        return ipmctl_system_cap

    def store_system_information(self):
        """
        Function to store the system information to a log.

        :return: cd_cmd - current working directory which has the log file
        """
        cd_cmd = self._common_content_lib.execute_sut_cmd("cd", "CWD", self._command_timeout)
        self._log.info("Current working directory... {}".format(cd_cmd))

        self._common_content_lib.execute_sut_cmd("Systeminfo > systeminfo.log", "System infomation",
                                                 self._command_timeout, cmd_path=cd_cmd)

        return cd_cmd.split("\n")[0]

    def getting_system_memory(self):
        """
        This function is used to parse the total physical memory and Available physical memory from Systeminfo
        :return: total physical memory value, available physical memory value
        """
        cmd_result = self._os.execute(self.SYSTEM_INFO_CMD, self._command_timeout)
        if cmd_result.cmd_failed():
            log_error = "Failed to run command '{}' with return value = '{}' and std_error='{}'..". \
                format(self.SYSTEM_INFO_CMD, cmd_result.return_code, cmd_result.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        memory_total_value = re.findall("Total Physical Memory:.*", cmd_result.stdout)
        if not memory_total_value:
            raise RuntimeError("Failed to get the Total Memory Value from System Info")
        self._log.info("The Amount of Total Physical Memory reported by the OS is : {}"
                       .format(memory_total_value[0].strip()))

        memory_free_value = re.findall("Available Physical Memory:.*", cmd_result.stdout)
        if not memory_free_value:
            raise RuntimeError("Failed to get the Available Physical Memory Value from System Info")
        self._log.info("The Amount of Available Physical Memory reported by the OS is : {}"
                       .format(memory_free_value[0].strip()))

        return memory_total_value[0].strip(), memory_free_value[0].strip()

    def show_system_memory_report_linux(self):
        """
        Function to get the system memory information for linux SUT

        :return: memory info
        """
        get_memory_info = self._common_content_lib.execute_sut_cmd(
            "free -m", "System Memory info", self._command_timeout)
        if get_memory_info != "":
            self._log.info("Displaying System Memory information... \n {}".format(get_memory_info))

        return get_memory_info

    def get_all_region_data_linux(self):
        """
        Function to get all the regions on linux SUT

        :return: list of regions
        """
        region_data_list = []
        get_region_data = self._common_content_lib.execute_sut_cmd(self.NDCTL_CMD_TO_LIST_ALL_REGION,
                                                                   "List of all the region",
                                                                   self._command_timeout)
        self._log.info("Listing all the regions...\n{}".format(get_region_data))
        match = re.findall("region.*", get_region_data)
        if match:
            for index in range(0, len(match)):
                region_data_list.append(match[index].split('"')[0])

        if len(region_data_list) == 0:
            self._log.info("There are no regions to display.")
        return region_data_list

    def create_namespace(self, region_data_list, mode=None):
        """
        Function to create new Namespaces on linux SUT

        :param: region_data_list
        :return: list of the created Device Namespaces
        """

        block_dev_list = []
        for index in range(0, len(region_data_list)):
            if mode is None:
                create_namespace = self._common_content_lib.execute_sut_cmd(
                    "ndctl create-namespace --mode sector --region={}".format(region_data_list[index]),
                    "Creating Namespace of {}".format(region_data_list[index]), self._command_timeout)
            else:
                create_namespace = self._common_content_lib.execute_sut_cmd(
                    "ndctl create-namespace --mode={} sector --region={}".format(mode, region_data_list[index]),
                    "Creating Namespace of {}".format(region_data_list[index]), self._command_timeout)
            self._log.info("Successfully created the Namespaces\n{}".format(create_namespace))
            blockdev_names_match = re.findall("pmem.*", create_namespace)
            if blockdev_names_match:
                block_dev_list.append(blockdev_names_match[0].split('"')[0])
        return sorted(block_dev_list)

    def show_pmem_block_info(self):
        """
        Function to display the pmem block info of linux SUT

        :return: stdout of the command ran
        """
        pmem_block_info = self._common_content_lib.execute_sut_cmd(
            self.SHOW_BLOCK_INFO_CMD, "Display pmem block devices present in the OS", self._command_timeout)
        self._log.info(
            "Display pmem block devices present in the OS\n{}".format(pmem_block_info))
        return pmem_block_info

    def verify_pmem_block_info(self, show_pmem_block_info, block_dev_list):
        """
        Function to verify if the desired pmem block info of is present in the cmd output for linux SUT

        :return: True on success
        """
        for index in range(0, len(block_dev_list)):
            if r"Disk /dev/{}".format(block_dev_list[index]) not in show_pmem_block_info:
                error_msg = "{} device is not present under the expected block".format(block_dev_list[index])
                self._log.error(error_msg)
                raise RuntimeError(error_msg)
        self._log.info("Successfully verified the pmem_block_info")
        return True

    def get_memory_process_info_linux(self):
        """
        Function to show Memory and Partition information for linux SUT

        :return: meminfo and partition data
        """
        mem_info_result = self._common_content_lib.execute_sut_cmd("cat /proc/meminfo", "Get Memory Information",
                                                                   self._command_timeout)
        if mem_info_result != "":
            self._log.info("Successfully fetched the memory information...\n{}".format(mem_info_result))

        process_info_result = self._common_content_lib.execute_sut_cmd("cat /proc/partitions", "Get Partition "
                                                                                               "Information",
                                                                       self._command_timeout)
        if process_info_result != "":
            self._log.info("Successfully fetched the partition information...\n{}".format(process_info_result))

        return mem_info_result, process_info_result

    def verify_pmem_device_presence(self, present_namespace_list):
        """
        Function to get the the listof pmem devices and verify if the desired devices are present or not on linux SUT

        :return: meminfo and partition data
        """
        pmem_device_list = self._os.execute("ls -l /dev/pmem*", self._command_timeout)

        if pmem_device_list.cmd_failed():
            # ls -l command returns non zero value, if No such file or directory
            self._log.info("There are no pmem disks present in the system...")
            return True
        elif pmem_device_list.return_code == 0:
            pmem_device_list = pmem_device_list.stdout

        result = [index for index in range(0, len(present_namespace_list)) if present_namespace_list[index] in
                  pmem_device_list]
        if result:
            self._log.info("Successfully fetched and verified the pmem device list..\n{}".format(pmem_device_list))
        return pmem_device_list

    def disk_partition_linux(self, pmem_device_list):
        """
        Function to run the command to do the partition by 'parted' on linux SUT

        :param: pmem_device_list
        :return: partition result
        """
        partition_result = ""
        for index in range(0, len(pmem_device_list)):
            partition_result = self._common_content_lib.execute_sut_cmd(self.LINUX_PARTITION_CMD.format(
                pmem_device_list[index]), "Create a generic "
                                          "partition on each PMEM device "
                                          "using parted", self._command_timeout)
        if partition_result != "":
            self._log.info("Successfully created a generic partition on each PMEM device using parted")
        return partition_result

    def create_ext4_filesystem(self, pmem_device_list):
        """
        Function to create an ext4 Linux file system on each enumerated PM blockdev device on linux SUT

        :param: pmem_device_list
        :return: stdout data
        """
        ext4_result_data = ""
        for index in range(0, len(pmem_device_list)):
            ext4_result_data = self._common_content_lib.execute_sut_cmd(self.LINUX_CMD_TO_CREATE_EX4_FILE_SYSTEM.
                                                                        format(pmem_device_list[index]),
                                                                        "Create an ext4 Linux file system on each "
                                                                        "enumerated ", self._command_timeout)
        if len(ext4_result_data) != 0:
            self._log.info("Successfully created an ext4 Linux file system on each enumerated block..\n{}".
                           format(ext4_result_data))

        return ext4_result_data

    def create_mount_point(self, pmem_device_list, mode="block"):
        """
        Function to create mount point on each enumerated PM blockdev device on linux SUT

        :param: pmem_device_list, mode(optional param)
        :return: stdout data
        """
        for index in range(0, len(pmem_device_list)):
            cmd_result = self._os.execute(self.CREATE_DIRECTORY_MOUNT_POINT_CMD.format(str(index)),
                                          self._command_timeout)
            if cmd_result.cmd_failed():
                self._common_content_lib.execute_sut_cmd("rmdir q ".format(str(index)),
                                                         "removing directory", self._command_timeout)

                self._common_content_lib.execute_sut_cmd("rmdir /mnt/QM-{} ".format(str(index)),
                                                         "removing directory", self._command_timeout)

                self._common_content_lib.execute_sut_cmd(self.CREATE_DIRECTORY_MOUNT_POINT_CMD.format(str(index)),
                                                         "Creating a directory", self._command_timeout)
            self.mount_list.append("/mnt/QM-{}".format(str(index)))

            self._log.info("Successfully created the directory mount point for the device {}".format(pmem_device_list[
                index]))
            if mode == "dax":
                cmd_result = self._common_content_lib.execute_sut_cmd(
                    self.MOUNT_DAX_FILE_SYSTEM_CMD.format(pmem_device_list[index],str(index)),
                    "Mount the Linux file system",
                    self._command_timeout)
                self._log.info("Successfully mount the Linux file system with DAX Access\n{}".format(cmd_result))
            else:
                cmd_result = self._common_content_lib.execute_sut_cmd(
                    self.MOUNT_FILE_SYSTEM_CMD.format(
                        pmem_device_list[index],
                        str(index)),
                    "Mount the Linux file system",
                    self._command_timeout)
                self._log.info("Successfully  mount the Linux file system with Block Access\n{}".format(cmd_result))
            #  Write the pmem mount data in /etc/fstab
            self._common_content_lib.execute_sut_cmd(
                self.CREATE_AUTO_MOUNT_CMD.format(pmem_device_list[index], str(index)), "Create Auto Mount",
                self._command_timeout)
            self._log.info("Successfully Auto mounted the pmem device")

    def verify_mount_point(self, pmem_device_list):
        """
        Function to verify mount point on each enumerated PM blockdev device on linux SUT

        :param: pmem_device_list
        :return: return on Success
        :raise: RuntimeError
        """
        cmd_result = self._common_content_lib.execute_sut_cmd(self.GPRE_CMD_TO_GET_MOUNT_INFO, "Show mount "
                                                                                               "information",
                                                              self._command_timeout)
        verification_result = [index for index in range(0, len(pmem_device_list)) if self.MOUNT_VERIFICATION_STR.format(
            pmem_device_list[index]) in cmd_result]
        if not verification_result:
            error_msg = "Mount is Not successful on each device"
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Mount is successful on each device..\n")
        return True

    def verify_device_partitions(self, pmem_device_list):
        """
        Function to verify the device partition of PM blockdev device on linux SUT

        :param: pmem_device_list
        :return: return on Success
        :raise: RuntimeError
        """
        cmd_result = self._common_content_lib.execute_sut_cmd(self.LINUX_CMD_TO_GET_PARTITION_INFO, "Show partition "
                                                                                                    "information",
                                                              self._command_timeout)
        verification_result = [index for index in range(0, len(pmem_device_list)) if (pmem_device_list[index]) in
                               cmd_result]
        if not verification_result:
            error_msg = "Fail to verify the device partition"
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully verified the device partitions...\n")
        return True

    def show_dimm_status_ipmctl(self, ipmctl_path):
        """
        Function to get the dimm status of by using IPMCTL tool

        :param ipmctl_path: path of the ipmctl tool.
        :return: dimm_status_result
        """
        dimm_status_result = self._common_content_lib.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_DIMM_STATUS, "To display the DIMM's present status",
            self._command_timeout, ipmctl_path)
        if dimm_status_result != '':
            self._log.info("Present Status of DIMMs are... \n {}".format(dimm_status_result))

        return dimm_status_result

    def get_supported_modes_uefi(self):
        """
        Function to run mode supported command via uefi shell

        :param: None
        :return: ret_val
        """
        ret_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.PROVISIONING_COMMAND)
        ret_val = ' '.join(map(str, ret_val))
        if not ret_val:
            error_msg = "Failed to get the modes supported values"
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully get the modes supported values...")
        return ret_val

    def get_dimm_info_uefi(self):
        """
        Function to run dimm info via uefi shell

        :param: None
        :return: ret_val
        """
        ret_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.PROVISIONING_DIMM_COMMAND)
        dimm_info = ' '.join(map(str, ret_val))
        if not dimm_info:
            error_msg = "Failed to get dimm values"
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("DIMM information with capacity and FW verion... \n {}".format(dimm_info))
        return dimm_info

    def get_app_direct_settings_uefi(self):
        """
        Function to run app  direct support command  via uefi shell

        :param: None
        :return: ret_val
        """
        ret_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.PROVISIONING_APP_DIRECT_COMMAND)
        ret_val = ret_val[1].split(",")
        if not ret_val:
            error_msg = "Failed to get app direct  values"
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully get app direct values...")
        return ret_val[0]

    def get_namespace_ipmctl_uefi(self):
        """
        Function to execute  the namespace command  via uefi shell

        :param: None
        :return: list_namespace
        """
        list_namespace_drives = []
        list_namespace = []
        ret_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.NAMESPACE_SHOW_COMMAND)
        self._log.info("Namespace info succefully done...{}".format(ret_val))

        if ret_val != '':
            for index in ret_val:
                if re.search(self.NAMESPACE_ID_REGX, index):
                    list_namespace_drives.extend(re.findall(self.NAMESPACE_ID_REGX, index))
            for index in list_namespace_drives:
                list_name = index.split("=")
                list_namespace.append(list_name[1])
        return list_namespace

    def clear_namespace_uefi(self, index):
        """
        Function to run namespace comand via uefi shell

        :param: None
        :return: ret_val
        """
        namespace_list = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            self.NAMESPACE_CLEAR_COMMAND + " " + index)
        if not namespace_list:
            error_msg = "Failed to get namespace list values"
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully get namespace list ... {}".format(namespace_list))
        return namespace_list

    def show_goal_uefi(self):
        """
         Function to execute the show goal command in uefi

         :param: None
         :return: None
         """
        show_goal = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.SHOW_GOAL_COMMAND)
        show_goal = ''.join(map(str, show_goal))
        if not show_goal:
            error_msg = "Failed to show goal region "
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        return show_goal

    def show_memory_support(self):
        """
         Function to execute memory support command in uefi shell

         :return: None
         """
        ret_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.SHOW_MEMEORY_SUPPORT_CMD)
        if not ret_val:
            error_msg = "Failed to execute memory support command"
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        return ret_val

    def show_region_data_uefi(self):
        """
         Function to show  all the regions on uefi shell after goal creation

         :param: None
         :return: list of regions
         """
        ret_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.SHOW_REGION_COMMAND)
        region_data = '\n'.join(map(str, ret_val))
        if not region_data:
            error_msg = "Failed to create region ID"
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully created region ID...")
        return region_data

    def get_all_region_data_uefi(self, region_data):
        """
        Function to get all the regions on uefi

        :return: list of regions
        """
        region_data_list = []
        self._log.info("Listing all the regions...")
        match = re.findall("RegionID=0x[0-9]*", region_data)
        if match:
            for index in range(0, len(match)):
                region_data_list.append((match[index].split("=")[1]))
        return region_data_list

    def region_data_after_goal_uefi(self, index):
        """
         Function to create all the regions after goal creation

         :return: list of regions
         """
        ret_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.CREATE_REGION_COMMAND + " " + index)
        if ret_val:
            self._log.info("Successfully created region ID")
        else:
            error_msg = "Failed to create region ID"
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        return ret_val

    def map_device_uefi(self):
        """
         Function to run map command

         :return: None
         """
        ret_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.MAP_COMMAND)
        ret_val = ''.join(map(str, ret_val))
        if ret_val:
            self._log.info("Successfully mapped to usb drive..")
        else:
            error_msg = "Failed to map usb drive.."
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        return ret_val

    def create_uefi_obj(self, _opt_obj, _test_log_obj):
        #  UEFI object creation
        ac_cfg = self._opt_obj.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac_obj = ProviderFactory.create(ac_cfg, self._test_log_obj)  # type: AcPowerControlProvider
        uefi_cfg = self._opt_obj.find(self.UEFI_CONFIG_PATH)
        self._uefi_obj = ProviderFactory.create(uefi_cfg, self._test_log_obj)  # type: UefiShellProvider
        bios_boot_menu_cfg = self._opt_obj.find(self.BIOS_BOOTMENU_CONFIGPATH)
        self._bios_boot_menu_obj = ProviderFactory.create(
            bios_boot_menu_cfg, self._test_log_obj)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._uefi_util_obj = UefiUtil(
            self._log,
            self._uefi_obj,
            self._bios_boot_menu_obj,
            self._ac_obj,
            self._common_content_configuration,
            self._os)

    def delete_pcd_data(self):
        """
        This function is used to delete the PCD data.

        :return: None
        """
        self._common_content_lib.execute_sut_cmd(
            self.ipmctl_cmd_name + self.DELETE_PCD_COMMAND, "To delete the pcd data", self._command_timeout, self.ROOT)

    def umount_existing_devices(self):
        """
        This function is used to un mount the pmem devices.

        :return: None
        """
        existing_mount_points = self.get_existing_mount_points_fstab()[0]
        for index in existing_mount_points:
            self._common_content_lib.execute_sut_cmd(
                "umount {}".format(index), "unmounting device", self._command_timeout)
        self._log.info("Successfully Unmounted the existing drives")

    def get_existing_mount_points_fstab(self):
        """
        This function is used to get the mount points from the /etc/fstab file

        :return: existing_drive_list, cmd_opt_list
        """
        existing_drive_list = []
        cmd_opt = self._common_content_lib.execute_sut_cmd("cat /etc/fstab", "Get fstab data", self._command_timeout)
        pmem_match = re.findall("/pmem.*", cmd_opt)
        if pmem_match:
            for ele in pmem_match:
                mnt_data = re.findall("/mnt/.*", ele)
                drive_name = mnt_data[0].split(" ")[0]
                existing_drive_list.append(drive_name)
        self._log.info("Successfully got the existing mount points from /etc/fstab")
        cmd_opt_list = cmd_opt.split("\n")
        return existing_drive_list, cmd_opt_list

    def remove_fstab_data(self):
        """
        This function is used to remove PMEM data in the /etc/fstab file.

        :return: True if Successfully removed the data from /etc/fstab
        """

        index_list = []
        cmd_opt_list = self.get_existing_mount_points_fstab()[1]
        for index in range(0, len(cmd_opt_list)):
            if "/mnt/QM" in cmd_opt_list[index]:
                index_list.append(index)
        self._common_content_lib.execute_sut_cmd(
            "sed -i.bak -e '{},{}d' /etc/fstab".format(index_list[0] + 1, index_list[-1] + 2),
            "Deleting mount data from fstab", self._command_timeout, cmd_path=self.ROOT)
        self._common_content_lib.execute_sut_cmd("rm -f /etc/fstab.bak", "deleting backup file", self._command_timeout)
        self._log.info("Successfully removed the data from fstab")
        return True

    def show_dimm_thermal_error_ipmctl(self, ipmctl_path):
        """
        Function to get the dimm thermal errors using IPMCTL tool

        :param ipmctl_path: path of the ipmctl tool.
        :return: dimm_thermal errors
        """
        dimm_thermal_result = self._common_content_lib.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_DIMM_THERMAL_ERR_STATUS, "To display the DIMM's thermal status",
            self._command_timeout, ipmctl_path)
        if dimm_thermal_result != '':
            self._log.info("Present Status of DIMMs are... \n {}".format(dimm_thermal_result))

        return dimm_thermal_result

    def show_dimm_media_error_ipmctl(self, ipmctl_path):
        """
        Function to get the dimm thermal errors using IPMCTL tool

        :param ipmctl_path: path of the ipmctl tool.
        :return: dimm_thermal errors
        """
        dimm_media_result = self._common_content_lib.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_DIMM_MEDIA_ERR_STATUS, "To display the DIMM's media status",
            self._command_timeout, ipmctl_path)
        if dimm_media_result != '':
            self._log.info("Present Status of DIMMs are... \n {}".format(dimm_media_result))

        return dimm_media_result

    def verify_mem_resource_provisioned_capacity(self, mem_resource_op):

        pattern_reserved = r"^ReservedCapacity=[\d]*"
        pattern_inaccessible = r"^InaccessibleCapacity=[\d]*"
        pattern_tot_capacity = r"^Capacity=[\d]*"
        res_capacity = 0
        tot_capacity = 0
        inacc_capacity = 0
        for cap in mem_resource_op.split("\n"):
            if re.search(pattern_reserved, cap):
                res_capacity = list(map(lambda sub: int(''.join([ele for ele in sub if ele.isnumeric()])),
                                        re.findall(pattern_reserved, cap)))

            if re.search(pattern_tot_capacity, cap):
                tot_capacity = list(map(lambda sub: int(''.join([ele for ele in sub if ele.isnumeric()])),
                                        re.findall(pattern_tot_capacity, cap)))
            if re.search(pattern_inaccessible, cap):
                inacc_capacity = list(map(lambda sub: int(''.join([ele for ele in sub if ele.isnumeric()])),
                                          re.findall(pattern_inaccessible, cap)))

        res_capacity = int("".join(map(str, res_capacity)))
        tot_capacity = int("".join(map(str, tot_capacity)))
        inacc_capacity = int("".join(map(str, inacc_capacity)))

        if (res_capacity > 0 or inacc_capacity > 0) and int(tot_capacity) > 0:
            if res_capacity == tot_capacity or inacc_capacity == tot_capacity:
                self._log.info("The Reserved/Inaccessible capacity and total capacity are equal, verification "
                               "successful.\n"
                               "All available capacity is now designated as 'Reserved'.")
            else:
                err_log = "The Reserved/Inaccessible capacity and total capacity are not equal, please re-provision " \
                          "the dimms and try verifying once again."
                self._log.error(err_log)
                raise RuntimeError(err_log)
        else:
            err_log = "The Reserved/Inaccessible capacity or total capacity is zero, please re-provision " \
                      "the dimms and try verifying once again."
            self._log.error(err_log)
            raise RuntimeError(err_log)

    def get_list_of_dimms_which_are_healthy_and_manageable(self):
        """
        This Method is Used to Fetch List of All the Healthy and Manageable Dimm's and raise the RunTimeError if
        there are no Healthy and Manageable Dimms.

        :return: None
        :raise: RuntimeError if there are no Healthy and Manageable Dimm's
        """
        if len(self.dimm_healthy_and_manageable_list) > 0:
            for dimm in self.dimm_healthy_and_manageable_list:
                self._log.info("Dimm{} is Healthy and Manageable".format(dimm))
        else:
            log_error = "We don't have Dimm's which are Healthy and Manageable"
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def get_ipmctl_error_logs(self, ipmctl_path, *err_type):
        """
        Function to get the error logs for media and thermal using ipmctl commands.

        :param ipmctl_path: where the logs will generate.
        :param err_type: will hold the error types.
        :return None
        """
        for err_tp in err_type:
            cmd_run = "ipmctl show -error {} -dimm > {}.log".format(err_tp, err_tp)

            self._common_content_lib.execute_sut_cmd(cmd_run, "Get {} error".format(err_tp),
                                                     self._command_timeout, ipmctl_path)

    def verify_ipmctl_error(self, err_type, log_path):
        """
        Function to check whether we find any Media or Thermal error on the dimms

        :param err_type: will hold the error type.
        :param log_path: log file path
        :return ret_val: false if error else true
        """
        ret_val = True

        with open(log_path, "r") as ipmctl_file:
            if "{} Error occurred".format(err_type) in ipmctl_file.read():
                self._log.error("Error has encountered on dimms, please check the '{}' "
                                "for more information.".format(log_path))
                ret_val = False
            else:
                self._log.info("There are no '{}' errors in log stored under '{}'".format(err_type, log_path))

        return ret_val

    def dump_provisioning_data(self, config_file_name, ipmctl_path):
        """
        Function to Store the currently configured memory allocation settings for all DCPMMs in the system to a file.

        :param config_file_name: file name in which current provisioning configuration will save
        :param ipmctl_path: ipmctl executor path
        :return : true on success
        :raise: RuntimeError
        """
        result = self._common_content_lib.execute_sut_cmd(self.ipmctl_cmd_name +
                                                          self.IPMCTL_CMD_DUMP_CURRENT_PROVISION_CONFIG.
                                                          format(config_file_name),
                                                          "Dump current provisioning data", self._command_timeout,
                                                          cmd_path=ipmctl_path)
        if "Successfully" not in result:
            err_msg = "Fail to dump the current provisioning configuration data"
            self._log.error(err_msg)
            raise RuntimeError(err_msg)
        self._log.info("Successfully dumped the current provisioning data\n{}".format(result))
        return True

    def restore_memory_allocation_settings(self, config_file_name, ipmctl_path):
        """
        Function to Restore the previous configured memory allocation settings from stored config file.

        :param config_file_name: file name from which provisioning configuration data will load
        :param ipmctl_path: ipmctl executor path
        :return : true on success
        :raise: RuntimeError
        """
        result_data = self._common_content_lib.execute_sut_cmd(self.ipmctl_cmd_name +
                                                               self.IPMCTL_CMD_CREATE_GOAL_FROM_CONFIG_FILE.
                                                               format(config_file_name),
                                                               "loading goal from configuration file",
                                                               self._command_timeout,
                                                               cmd_path=ipmctl_path)

        if result_data == "":
            err_msg = "Fail to restore the memory allocation from the config file"
            self._log.error(err_msg)
            raise RuntimeError(err_msg)
        self._log.info("Successfully loaded the goal from configuration file\n{}".format(result_data))
        return result_data

    def get_total_system_memory_data_linux(self, get_memory_info):
        """
        Function to get the total system memory data from Os.

        :param get_memory_info: system memory data from Os
        :return mem_total_val: total current memory of the system in float type
        :raise: RuntimeError
        """
        mem_total_val = None
        if re.search(self.MEM_REGEX, get_memory_info):
            mem_match_data = re.findall(self.MEM_REGEX, get_memory_info)
            mem_total_val = mem_match_data[0].split(":")[1].strip()
        if not mem_total_val:
            err_msg = "Fail to fetch the total memory value"
            self._log.error(err_msg)
            raise RuntimeError(err_msg)
        self._log.info("Successfully got the total memory value from OS: {}".format(mem_total_val))
        return float(mem_total_val)

    def verify_lm_provisioning_configuration_linux(self, dimm_data, system_total_memory, mode):
        """
        Function to verify if system is LM provisioned or not for Linux Os

        :param dimm_data: output of DIMM info data from IPMCTL command
        :param system_total_memory: system memory data from Os
        :param mode: Provisioning mode expected values are "1LM" or "2LM"
        :return : true on success
        :raise: RuntimeError
        """
        total_dimm_memory = None
        if mode == "1LM":
            # Get total DIMM DDR4 memory value from Os
            total_dimm_memory = sum(self.get_total_ddr4_memory_data(dimm_data))
        elif mode == "2LM":
            # Get total DIMM DCPMM memory value from Os
            total_dimm_memory = sum(self.get_memory_mode_data(dimm_data))
        else:
            err_msg = "{} mode is not supported".format(mode)
            self._log.error(err_msg)
            raise RuntimeError

        # Convert the DIMM memory value to MB unit
        dimm_capacity = total_dimm_memory * 1024.0

        # Get the total System memory value from Os
        get_total_memory_data_linux = self.get_total_system_memory_data_linux(system_total_memory)

        # Get the threshold floor value
        threshold_dimm_capacity_floor = (dimm_capacity - (dimm_capacity * 0.05))

        # Get the threshold celling value
        threshold_dimm_capacity_celling = (dimm_capacity + (dimm_capacity * 0.05))

        # Compare Total DIMM Memory mode values with System memory value
        if not (threshold_dimm_capacity_floor < get_total_memory_data_linux < threshold_dimm_capacity_celling):
            err_msg = "Fail to verify {} provisioning configuration".format(mode)
            self._log.error(err_msg)
            raise RuntimeError(err_msg)
        self._log.info("Successfully verified {} provisioning configuration".format(mode))
        return True

    def get_total_ddr4_memory_data(self, topology_data):
        """
        Function to verify if system is 2LM provisioned or not.

        :param topology_data: output from 'ipmctl show -topology command'
        :return ddr4_capacity_list: list of DDR4 memory capacilty values
        """
        ddr4_capacity_list = []
        match_data = re.findall("DDR4.*", topology_data)
        if len(match_data) != 0:
            for element in match_data:
                ddr4_capacity_list.append(float(element.split("|")[1].strip().split(" ")[0]))
        self._log.info("Total DDR4 memory capacity values are: {}".format(ddr4_capacity_list))
        return ddr4_capacity_list

    def verify_lm_provisioning_configuration_win(self, dimm_data, mode):
        """
        Function to verify if system is LM provisioned or not for Windows SUT.

        :param dimm_data: output of DIMM info data from IPMCTL command
        :param mode: Provisioning mode expected values are "1LM" or "2LM"
        :return : true on success
        :raise: RuntimeError
        """
        total_dimm_memory = None
        if mode == "1LM":
            # Get total DIMM DDR4 memory value from Os
            total_dimm_memory = sum(self.get_total_ddr4_memory_data(dimm_data))
        elif mode == "2LM":
            # Get total DIMM DCPMM memory value from Os
            total_dimm_memory = sum(self.get_memory_mode_data(dimm_data))
        else:
            err_msg = "{} mode is not supported".format(mode)
            self._log.error(err_msg)
            raise RuntimeError

        # Convert the DIMM memory value to MB unit
        dimm_capacity = total_dimm_memory * 1024.0

        # Get the total System memory value from Os
        get_total_memory_data_win = self.getting_system_memory()[0].split(":")[1].strip("MB").strip().replace(",", "")

        # Get the threshold floor value
        threshold_dimm_capacity_floor = (dimm_capacity - (dimm_capacity * 0.05))

        # Get the threshold celling value
        threshold_dimm_capacity_celling = (dimm_capacity + (dimm_capacity * 0.05))

        # Compare Total DIMM Memory mode values with System memory value
        if not (threshold_dimm_capacity_floor < float(get_total_memory_data_win) < threshold_dimm_capacity_celling):
            err_msg = "Fail to verify {} provisioning configuration".format(mode)
            self._log.error(err_msg)
            raise RuntimeError(err_msg)
        self._log.info("Successfully verified {} provisioning configuration".format(mode))
        return True

    def get_dimm_id_uefi(self):
        """
        Function to get dimm ids  via uefi shell

        :param: None
        :return: list_dimm_id
        """
        list_dimm_id = []
        dimm_info = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.PROVISIONING_DIMM_COMMAND)
        for index in dimm_info:
            if re.search("0x[0-9]*", index):
                list_dimm_id.extend(re.findall("0x[0-9]*", index))
        return list_dimm_id

    def ipmctl_version_uefi(self):
        """
        Function to run ipmctl version via uefi shell

        :param: None
        :return: ipmctl_version
        """
        ipmctl_version = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.IPMCTL_VERSION)
        if not ipmctl_version:
            error_msg = "Failed to get ipmctl version"
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully get ipmctl version...")
        return ipmctl_version

    def ipmctl_pcd_config_uefi(self):
        """
        Function to run the platform configuration data for each DCPMM via uefi shell

        :param: None
        :return: pcd_cfg
        """
        pcd_cfg = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.IPMCTL_PCD_CFG)
        pcd_cfg = ''.join(map(str, pcd_cfg))
        if not pcd_cfg:
            error_msg = "Failed to get platform configuration data for each DCPMM "
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully to get platform configuration data for each DCPMM...")
        return pcd_cfg

    def ipmctl_system_capability_uefi(self):
        """
        Function to run the platform configuration data for each DCPMM via uefi shell

        :param: None
        :return: sys_capability
        """
        sys_capability = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.IPMCTL_CAPABILITY_CMD)
        sys_capability = ' '.join(map(str, sys_capability))
        if not sys_capability:
            error_msg = "Failed to run system capability command "
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully run system capability command...")
        return sys_capability

    def ipmctl_show_topology_uefi(self):
        """
        Function to run the DCPMM topology command via uefi shell

        :param: None
        :return:topology_val
        """
        topology_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response("ipmctl.efi show -topology")
        if not topology_val:
            error_msg = "Failed to run system topology command "
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully run system topology command...")
        return topology_val

    def ipmctl_show_firmware_uefi(self):
        """
        Function to run the DCPMM topology command via uefi shell

        :param: None
        :return:firmware_val
        """
        firmware_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response("ipmctl.efi show -firmware")
        if not firmware_val:
            error_msg = "Failed to run system firmware command "
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully run system firmware command...")
        return firmware_val

    def ipmctl_diagnostic_security_uefi(self):
        """
        Function to run diagnostic security command via uefi shell

        :param: None
        :return: diagnostic_val
        """
        diagnostic_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            "ipmctl.efi start -diagnostic Security")
        if not diagnostic_val:
            error_msg = "Failed to run diagnostic security command "
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully run diagnostic security command...")
        return diagnostic_val

    def ipmctl_diagnostic_help_uefi(self):
        """
        Function to run diagnostic help command via uefi shell

        :param: None
        :return: diagnostic_val
        """
        diagnostic_help = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            "ipmctl.efi start -help -diagnostic")
        diagnostic_help = ''.join(map(str, diagnostic_help))
        if not diagnostic_help:

            error_msg = "Failed to run diagnostic help command "
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully run diagnostic help command...")
        return diagnostic_help

    def ipmctl_diagnostic_check_uefi(self, dimm_id):
        """
        Function to execute the quick check diagnostic on a single DCPMM  via uefi shell

        :param: None
        :return: diagnostic_check_val
        """
        for index in dimm_id:
            diagnostic_check_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(
                "ipmctl.efi start -diagnostic Quick -dimm" + " " + index)
            if not diagnostic_check_val:
                error_msg = "Failed to run quick  diagnostic command "
                self._log.error(error_msg)
                raise RuntimeError(error_msg)
            self._log.info("Successfully run diagnostic quick command...")
            return diagnostic_check_val

    def ipmctl_diagnostic_quick_check_uefi(self):
        """
        Function to run quick check diagnostic on all installed DCPMMs via uefi shell

        :param: None
        :return: qucik_check_val
        """
        qucik_check_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            "ipmctl.efi start -diagnostic Quick")
        if not qucik_check_val:
            error_msg = "Failed to run diagnostic quick check command "
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully run diagnostic quick check command...")
        return qucik_check_val

    def ipmctl_diagnostic_config_check_uefi(self):
        """
        Function to run quick check diagnostic on all installed DCPMMs via uefi shell

        :param: None
        :return: diagnostic_val
        """
        qucik_config_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            "ipmctl.efi start -diagnostic Config")
        if not qucik_config_val:
            error_msg = "Failed to run diagnostic config command "
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully run diagnostic config command...")
        return qucik_config_val

    def ipmctl_diagnostic_uefi(self):
        """
        Function to Execute the default set of all diagnostics on installed DCPMMs via uefi shell

        :param: None
        :return: diagnostic_val
        """
        diagnostic_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response("ipmctl.efi start -diagnostic")
        if not diagnostic_val:
            error_msg = "Failed to run diagnostic security command "
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully run diagnostic security command...")
        return diagnostic_val

    def ipmctl_system_nfit_uefi(self):
        """
        Function to run NFIT commands to show that the system via uefi shell

        :param: None
        :return: nfit_val
        """
        nfit_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response("ipmctl.efi  show -system NFIT")
        if not nfit_val:
            error_msg = "Failed to run system NFIT command "
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully run system NFIT command...")
        return nfit_val

    def ipmctl_system_pcat_uefi(self):
        """
        Function to run NFIT commands to show that the system via uefi shell

        :param: None
        :return: pcat_val
        """
        pcat_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response("ipmctl.efi  show -system PCAT")
        if not pcat_val:
            error_msg = "Failed to run system PCAT command "
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully run system PCAT command...")
        return pcat_val

    def ipmctl_system_pmtt_uefi(self):
        """
        Function to run PMTT commands to show that the system via uefi shell

        :param: None
        :return: pmtt_val
        """
        pmtt_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response("ipmctl.efi  show -system PMTT")
        if not pmtt_val:
            error_msg = "Failed to run system PMTT command "
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully run system PMTT command...")
        return pmtt_val

    def verify_pcd_data(self, input_data):
        """
         Function to verify pcd config data in uefi shell

         :param: None
         :return: None
         """
        sign_match = re.findall("Signature.*", input_data)
        for index in sign_match:
            sig_val = index.split(":")[1].strip()
            if not re.match("[A-Z].*", sig_val):
                self._log.error("Signature data section having null data value")
                raise RuntimeError("Signature data section having null data value")
            else:
                self._log.info("Signature data section having expected data value...{}".format(sig_val))

        len_match = re.findall("Length.*", input_data)
        for index in len_match:
            len_data = index.split(":")[1].strip()
            if not re.match("0x.*", len_data):
                log_error = "Length data section having null data value"
                self._log.error(log_error)
                raise RuntimeError(log_error)
            else:
                self._log.info("Length data section having expected data value...{}".format(len_data))

    @staticmethod
    def get_config_val(quick_config_val):
        """
         Function to get quick config data in uefi shell

         :param: None
         :return: list_config_val
         """
        list_config_val = []
        if quick_config_val != '':
            for index in quick_config_val:
                if re.search("Diagnostic.*", index):
                    config_match = re.findall("Diagnostic.*", index)
                    for index in range(0, len(config_match)):
                        list_config_val.append(config_match[index].strip("\r---\r"))
                elif re.search("State.*", index):
                    config_match = re.findall("State.*", index)
                    for index in range(0, len(config_match)):
                        list_config_val.append(config_match[index].strip("\r\r"))
                elif re.search("Message.*", index):
                    config_match = re.findall("Message.*", index)
                    for index in range(0, len(config_match)):
                        list_config_val.append(config_match[index].strip("\r\r"))
            return list_config_val

    @staticmethod
    def get_diagnostic_quick_val(quick_val):
        """
         Function to get diagnostic quick  data in uefi shell

         :param: None
         :return: list_quick_val
         """
        list_quick_val = []
        if quick_val != '':
            for index in quick_val:
                if re.search("Diagnostic.*", index):
                    config_match = re.findall("Diagnostic.*", index)
                    for index in range(0, len(config_match)):
                        list_quick_val.append(config_match[index].strip("\r---\r"))
                elif re.search("State.*", index):
                    config_match = re.findall("State.*", index)
                    for index in range(0, len(config_match)):
                        list_quick_val.append(config_match[index].strip("\r\r"))
                elif re.search("Message.*", index):
                    config_match = re.findall("Message.*", index)
                    for index in range(0, len(config_match)):
                        list_quick_val.append(config_match[index].strip("\r\r"))
            return list_quick_val

    @staticmethod
    def get_diagnostic_security_val(security_val):
        """
         Function to get diagnostic security  data in uefi shell

         :param: None
         :return: list_security_val
         """
        list_security_val = []
        if security_val != '':
            for index in security_val:
                if re.search("Diagnostic.*", index):
                    config_match = re.findall("Diagnostic.*", index)
                    for index in range(0, len(config_match)):
                        list_security_val.append(config_match[index].strip("\r---\r"))
                elif re.search("State.*", index):
                    config_match = re.findall("State.*", index)
                    for index in range(0, len(config_match)):
                        list_security_val.append(config_match[index].strip("\r\r"))
                elif re.search("Message.*", index):
                    config_match = re.findall("Message.*", index)
                    for index in range(0, len(config_match)):
                        list_security_val.append(config_match[index].strip("\r\r"))
            return list_security_val

    def get_system_acpi_val(self, nfit_val):
        """
           Function to get ACPI  data attributes in uefi shell

           :param: None
           :return: type_data_list
           """
        type_data_list = []
        if nfit_val != '':
            for index in nfit_val:
                if re.search("Signature.*", index):
                    match = re.findall("Signature.*", index)
                    for index in range(0, len(match)):
                        type_data_list.append(match[index].split(":")[1].strip("\r"))
                elif re.search("MODULE.*", index):
                    match = re.findall("MODULE.*", index)
                    for index in range(0, len(match)):
                        type_data_list.append(match[index].strip("----\r"))
                elif re.search("iMC.*", index):
                    match = re.findall("iMC.*", index)
                    for index in range(0, len(match)):
                        type_data_list.append(match[index].strip("-------------------\r"))
            type_data_list = list(dict.fromkeys(type_data_list))
        self._log.info("The NFIT interface table expected values{}".format(type_data_list))
        return type_data_list

    @staticmethod
    def get_system_val(nfit_val):
        """
           Function to get PCD attributes data in uefi shell

           :param: None
           :return: type_data_list
           """
        type_data_list = []
        if nfit_val != '':
            for index in nfit_val:
                if re.search("TypeEquals.*", index):
                    match = re.findall("TypeEquals.*", index)
                    for index in range(0, len(match)):
                        type_data_list.append(match[index].split(":")[1].strip("\r"))
                type_data_list = list(dict.fromkeys(type_data_list))
        return type_data_list

    def ipmctl_thermal_error_uefi(self):
        """
           Function to run thermal command in uefi shell

           :param: None
           :return: thermal_val
           """
        thermal_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response("ipmctl.efi show -error Thermal -dimm")
        if not thermal_val:
            log_error = "Thermal command failed "
            self._log.error(log_error)
            raise RuntimeError(log_error)
        return thermal_val

    def ipmctl_media_error_uefi(self):
        """
       Function to run media command in uefi shell

       :return: media_val
       """
        media_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response("ipmctl.efi show -error Media -dimm")
        media_val = ''.join(map(str, media_val))
        if not media_val:
            log_error = "Media command failed "
            self._log.error(log_error)
            raise RuntimeError(log_error)
        return media_val

    def verify_thermal_media_error(self, thermal_media_val):
        """
           Function to verify thermal and media data in uefi shell

           :param: thermal_media_val
           :return: RuntimeError
           """
        match = []
        if thermal_media_val != '':
            for index in thermal_media_val:
                if re.search("No error.*", index):
                    match = re.findall("No error.*", index)
        if match != '':
            self._log.info("No Thermal-media error found in DIMM")
        else:
            log_error = "Thermal-media error found in DIMM"
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def verify_pmem_block_uefi(self, map_output):
        """
        Function to verify pmem blocks are available

        :return: None
        :raise: RunTimeError
        """
        if "Msg" not in map_output:
            error_msg = "pmem block is not available uefi shell "
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        else:
            self._log.info("pmem block is available in uefi shell")

    def verify_serial_no_nfit(self, no_of_dimms, nfit_list):
        """
        Function to verify the number of Serial Number entries in NFIT table match with physical dimms

        :return: None
        :raise: RunTimeError
        """
        nfit_data_list = []
        if nfit_list != '':
            for index in nfit_list:
                if re.search("SerialNumber:*", index):
                    match = re.findall("SerialNumber:*", index)
                    for index in range(0, len(match)):
                        nfit_data_list.append(match[index])
            if len(nfit_data_list) == len(no_of_dimms):
                self._log.info(
                    "The number of SerialNumber entries matches the number of DCPMMs that are physically installed")
            else:
                log_error = "The number of SerialNumber entries does not matches the number of DCPMMs" \
                            " that are physically installed"
                self._log.error(log_error)
                raise RuntimeError(log_error)

    def verify_memory_capability_pcat(self, pcat_list):
        """
        Function to verify memory capability in PCAT table to match 0x27

        :return: None
        :raise: RunTimeError
        """
        pcat_data_list = []
        pcat_mode_list = []
        pcat_val = "27"
        if pcat_list != '':
            for index in pcat_list:
                if re.search("MemoryModeCapabilities.*", index):
                    match = re.findall("MemoryModeCapabilities.*", index)
                    for index in range(0, len(match)):
                        pcat_data_list.append(match[index].split(":")[1].strip("\r"))
            for index in pcat_data_list:
                if re.search("27.*", index):
                    match = re.findall("27.*", index)
                    for index in range(0, len(match)):
                        pcat_mode_list.append(match[index])

            if (pcat_val in pcat_mode_list):
                self._log.info("PCAT output file shows the correct capability flags for the configuration")
            else:
                log_error = "PCAT output does not have correct capability flags for the configuration"
                self._log.error(log_error)
                raise RuntimeError(log_error)

    def get_boot_status_register_uefi(self):
        """
           Function to run boot status register command in uefi shell

           :param: None
           :return: boot_reg_val
           """
        boot_reg_val = self._uefi_util_obj.execute_cmd_in_uefi_and_read_response("ipmctl.efi show -d BootStatus -dimm")
        boot_reg_val = ''.join(map(str, boot_reg_val))
        if not boot_reg_val:
            log_error = "Boot status register command failed "
            self._log.error(log_error)
            raise RuntimeError(log_error)
        return boot_reg_val

    def verify_recommended_app_direct_mode_for_1lm(self, app_direct_result_data):
        """
        Function to verify if RecommendedAppDirect is present within the IPMCTL App Direct Mode
        setting capabilities command

        :param: app_direct_result_data
        :return: True on success
        :raise: RuntimeError
        """
        if re.findall(self.REGEX_CMD_FOR_EXPECTED_APP_DIRECT_MODE, app_direct_result_data):
            self._log.info("Successfully Verified Expected App Direct Mode Setting")
        else:
            error_msg = "Expected App Direct Mode Setting is not enabled"
            self._log.error(error_msg)
            raise content_exception.TestFail(error_msg)

        return True

