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
#   WINDOWS IPMCTL PROVIDER

from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.ac_power import AcPowerControlProvider

from src.lib import content_exceptions
from src.provider.ipmctl_provider import IpmctlProvider
from src.lib.memory_dimm_info_lib import MemoryDimmInfo
import re
import time


class IpmctlProviderWindows(IpmctlProvider):
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
    IPMCTL_CMD_SHOW_SENSOR = r" show -sensor"
    IPMCTL_CMD_SHOW_DIMM_STATUS = r" show -d HealthState,ManageabilityState,FWVersion,DeviceLocator -dimm"
    C_DRIVE_PATH = "C:\\"
    DELETE_PCD_COMMAND = " delete -f -pcd -dimm"
    CREATE_AUTO_MOUNT_CMD = 'echo "/dev/{} /mnt/QM-{} ext4 defaults,nofail 0 1" >> /etc/fstab'
    IPMCTL_CMD_SHOW_DIMM_THERMAL_ERR_STATUS = " show -error Thermal -dimm"
    IPMCTL_CMD_SHOW_DIMM_MEDIA_ERR_STATUS = " show -error media -dimm"
    IPMCTL_SHOW_MANAGEABILTY_CMD = " show -d ManageabilityState -dimm"
    NAMESPACE_ID_REGX = r"NamespaceId=0x[0-9]*"
    MEM_REGEX = r"Mem:\s*[0-9]*"
    IPMCTL_CMD_DUMP_CURRENT_PROVISION_CONFIG = " dump -destination {} -system -config"
    IPMCTL_CMD_CREATE_GOAL_FROM_CONFIG_FILE = " load -f -source {} -goal"
    IPMCTL_CMD_FOR_LISTING_EXISTING_DCPMM_ERRORS = " show -error Media -dimm {}"
    IPMCTL_CMD_FOR_FATAL_MEDIA_ERROR = r"ipmctl set -dimm {} FatalMediaError=1"
    IPMCTL_CMD_FOR_CLEAR_INJECTED_POISON = r" set -dimm {} Clear=1 FatalMediaError=1"
    IPMCTL_CMD_FOR_VIRAL_STATUS = " show -d ViralPolicy,ViralState -dimm"
    REGEX_CMD_FOR_HEALTH_STATUS_CHANGE_ERROR = r"Error\sType\s+:\s+\S+\s-\sSmart\sHealth\sStatus\sChange"

    SHOW_REGION_COMMAND = " show -region"
    SHOW_ALL_REGIONS_COMMAND = " show -a -region"

    IPMCTL_CMD_DIAGNOSTIC_CONFIG = " start -diagnostic config"
    IPMCTL_CMD_DIAGNOSTIC_FW = " start -diagnostic fw"
    IPMCTL_CMD_DIAGNOSTIC_SEC = " start -diagnostic security"
    IPMCTL_CMD_DIAGNOSTIC_QUICK = " start -diagnostic quick"

    IPMCTL_CMD_FOR_SHOW_PCD = " show -dimm -pcd"
    IPMCTL_CMD_FOR_SHOW_SYSTEM = " show -system"
    IPMCTL_CMD_SHOW_DIMM_PERFORMANCE = " show -dimm -performance"
    IPMCTL_CMD_SHOW_ARS_STATUS = " show -d ARSStatus -dimm"
    IPMCTL_CMD_SHOW_SOCKET = " show -socket"
    IPMCTL_SHOW_FIRMWARE = " show -firmware"
    IPMCTL_CMD_SHOW_PREFERENCES = " show -preferences"
    IPMCTL_CMD_SHOW_SYSTEM_NFIT = " show -system NFIT"
    IPMCTL_CMD_SHOW_SYSTEM_PCAT = " show -system PCAT"

    def __init__(self, log, os_obj, uefi_util_obj=None, cfg_opts=None):
        super(IpmctlProviderWindows, self).__init__(log, os_obj, uefi_util_obj, cfg_opts)
        self._log = log
        self._os = os_obj
        self.ipmctl_cmd_name = r"ipmctl"
        self.dimm_healthy_list = []
        self.dimm_healthy_and_manageable_list = []
        self.df_dimm_fw_version_op = None
        self.show_dimm_dataframe = None
        ac_power_cfg = self._cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self._ac_power = ProviderFactory.create(ac_power_cfg, self._log)

    def show_sensors(self):
        """
        Function to get the DIMM sensor information.

        :return ipmctl_show_sensors: sensor information
        """
        ipmctl_show_sensors = self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_SENSOR, "DCPMM show sensor", self.command_timeout)
        self._log.info("DCPMM show sensor information... \n {}".format(ipmctl_show_sensors))

        return ipmctl_show_sensors

    def show_topology(self):
        """
        Function to get the DIMM sensor information.

        :return ipmctl_show_sensors: sensor information
        """
        ipmctl_show_topology = self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_TOPOLOGY, "DCPMM Topology", self.command_timeout)
        self._log.info("DCPMM show topology information... \n {}".format(ipmctl_show_topology))

        return ipmctl_show_topology

    def dcpmm_new_pmem_disk(self, region_data_list=None, mode=None):
        """
        Function to configure all available pmem devices with namespaces.
        :return pmem_unused_new: the namespace has been created.
        """
        pmem_unused_new = self.common_content_lib_obj.execute_sut_cmd(
            self.PS_CMD_CREATE_NEW_PMEM_DISK, "DCPMM new namespace", self.command_timeout)
        self._log.info("DCPMM creating new namespaces... \n {}".format(pmem_unused_new))

        return pmem_unused_new

    def verify_dimms_firmware_version(self):
        """
        This method is used to verify the show topology firmware output with pmem device output.

        :return True if we have correct location of dimm
        """
        deviec_locator_result = []
        pmem_device_output = None
        pmem_device_output = self.get_pmem_device()
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

    def verify_dimms_device_locator(self):
        """
        This method is used to verify the show topology device locator output with pmem device output.

        :return True if we have correct location of dimm
        """
        deviec_locator_result = []
        pmem_device_output = None
        pmem_device_output = self.get_pmem_device()
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

    def dcpmm_get_disk_namespace(self):
        """
        Function to get the DCPMM disk namespaces information.

        :return dcpmm_disk_namespace: disk namespace info
        """
        dcpmm_disk_namespace = None
        dcpmm_disk_namespace = self.common_content_lib_obj.execute_sut_cmd(
            self.PS_CMD_GET_NAMESPACE, "DCPMM disk namespace", self.command_timeout)

        if dcpmm_disk_namespace != '':
            self._log.info("DCPMM disk namespace...  {}".format(dcpmm_disk_namespace))
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

        if namespace_info != '':
            initialize_dimm = self.common_content_lib_obj.execute_sut_cmd(
                self.PS_CMD_INITIALIZE_PMEM_DEV, "DCPMM disk namespace Initialize", self.command_timeout)
            self._log.info("DCPMM disk namespace Initialization started...  {}".format(initialize_dimm))
        else:
            self._log.info("There are no existing namespaces, continue to configure the installed DCPMM(s)..")

        return initialize_dimm

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

    def get_memory_dimm_information(self):
        """
        This Function populated memory dimm information by running below ipmctl commands on SUT
        - ipmctl show -topology
        - ipmctl show -dimm
        Finally it will create object of class MemoryDimmInfo.

        :raise: RuntimeError for any error during ipmctl command execution or parsing error.
        """
        try:
            self._log.info("Checking the Topology to Identify the DIMMs..")

            ipmctl_show_topology = self.common_content_lib_obj.execute_sut_cmd(
                self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_TOPOLOGY, "DCPMM Topology", self.command_timeout)

            self.show_topology_output = ipmctl_show_topology.split(",")[0]

            ipmctl_show_dimm = self.common_content_lib_obj.execute_sut_cmd(
                self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_DIMM, "DCPMM info", self.command_timeout)

            show_dimm_command_output = ipmctl_show_dimm.split(",")[0]

            # Get manageability output using ipmctl command
            command_result = self.common_content_lib_obj.execute_sut_cmd(
                self.ipmctl_cmd_name + self.IPMCTL_SHOW_MANAGEABILTY_CMD, "DCPMM manageability info",
                self.command_timeout)

            manageability_state_command_output = command_result.split(',')[0]

            # Object creation
            memory_info_obj = MemoryDimmInfo(self.show_topology_output, show_dimm=show_dimm_command_output,
                                             manageability=manageability_state_command_output)

            self.dimm_healthy_list = memory_info_obj.get_dimm_info_healthy()

            self.dimm_healthy_and_manageable_list = memory_info_obj.get_dimm_info_healthy_manageable()

            self.df_dimm_fw_version_op = memory_info_obj.df_dimm_fw_version

            self._log.info("DCPMM topology data frame...  {} ".format(self.df_dimm_fw_version_op))

            self.show_dimm_dataframe = memory_info_obj.get_show_dimm_data_frame()

            self._log.info("DCPMM show dimm info data frame...  \n{} ".format(self.show_dimm_dataframe))

            return show_dimm_command_output
        except Exception as ex:
            log_error = "Unable to Execute IPMCTL Commands on SUT {}".format(ex)
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def get_dcpmm_disk_list(self):
        """
        Function to get the DCPMM disk list that needs to be partitioned.
        :return: list of disk numbers
        """
        powershell_list_phy_device = self._os.execute(
            self.PS_CMD_GET_DCPMM_DISK_LIST, self.command_timeout,
            self.common_content_lib_obj.C_DRIVE_PATH)
        digit_list = []

        for disk_num in powershell_list_phy_device.stdout.strip().split("\n"):
            disk_num_striped = disk_num.strip()
            if disk_num_striped.isdigit():
                digit_list.append(disk_num_striped)

        return sorted(digit_list)

    def get_supported_modes(self):
        """
        Function to get the DCPMM dimm topology.

        :return ipmctl_show_sup_mode: supported modes
        """
        # The current App Direct Mode capabilities are as expected for 2LM mixed mode provisioning
        ipmctl_show_sup_mode = self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_MODES, "DCPMM mode", self.command_timeout)
        self._log.info("DCPMM supported modes...  {}".format(ipmctl_show_sup_mode))

        return ipmctl_show_sup_mode

    def dcpmm_get_pmem_unused_region(self):
        """
        The unused space now matches the installed persistent memory capacity
        :return dcpmm_disk_unused_region: unused pmem regions
        """
        dcpmm_disk_unused_region = self.common_content_lib_obj.execute_sut_cmd(
            self.PS_CMD_GET_UNUSED_NAMESPACE, "DCPMM un used region", self.command_timeout)
        self._log.info("DCPMM disk un used region...  {}".format(dcpmm_disk_unused_region))

        return dcpmm_disk_unused_region

    def dcpmm_configuration(self, cmd=None, cmd_str=None):
        """
        Function to configure DCPMM dimms with appropriate volatile memory and persistent memory.
        Also, to fetch the memory allocation goal and its resources.

        :param cmd: holds the command to allocate the mode.
        :param cmd_str: str - holds the info about the command.
        :return dcpmm_disk_goal: goal that was created.
        """
        dcpmm_disk_create_mixed_mode = self.common_content_lib_obj.execute_sut_cmd(
            cmd, "DCPMM mode allocation", self.command_timeout)
        self._log.info("DCPMM disk has been created with {}..{}".format(cmd_str, dcpmm_disk_create_mixed_mode))

        # The memory allocation goal has been done.
        dcpmm_disk_goal = self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_GOAL, "DCPMM goal", self.command_timeout)
        self._log.info("DCPMM disk goal is :  \n{}".format(dcpmm_disk_goal))

        return dcpmm_disk_goal

    def show_goal(self):
        """
         Function to execute the show goal command in uefi

         :param: None
         :return: None
         """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "UEFI shell..".format("show_goal"))

    def show_mem_resources(self):
        """
        Function to configure DCPMM devices are normal and the DCPMM mapped memory configuration
        matches the applied goal.

        :return dcpmm_mem_resource: memory information
        """
        dcpmm_mem_resource = self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_MEM_RESOURCES, "DCPMM memory resource", self.command_timeout)
        self._log.info("DCPMM memory resources...  {}".format(dcpmm_mem_resource))

        return dcpmm_mem_resource

    def get_pmem_device(self):
        """
        This is function is used to get the persistent memory device information

        :return get_pmem output
        """
        get_pmem = self.common_content_lib_obj.execute_sut_cmd(
            self.PS_CMD_GET_PMEM_PHYSICAL_DEV, "DCPMM info", self.command_timeout)

        return get_pmem

    def dcpmm_get_pmem_device_fl_info(self):
        """
        Function to list the persistent memory regions.
        :return pmem_phy_device: Pmem regions info.
        """
        pmem_phy_device = self.common_content_lib_obj.execute_sut_cmd(
            self.PS_CMD_FL_INFO, "Pmem regions", self.command_timeout)
        self._log.info("DCPMMs are listed...  {}".format(pmem_phy_device))

        return pmem_phy_device

    def create_config_csv(self):
        """
        Store the currently configured memory allocation settings for all DCPMMs in the system to a file

        :return None
        """
        store_configs = self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_DUMP_CONFIG_CSV, "Store the configuration",
            self.command_timeout)

        self._log.info("Storing the currently configured memory allocation settings for all DCPMMs "
                       "in the system to a file...  {}".format(store_configs))

    def get_system_capability(self):
        """
        Function to configure all available pmem devices with namespaces.

        :return ipmctl_system_cap: the namespace has been created.
        """
        ipmctl_system_cap = self.common_content_lib_obj.execute_sut_cmd(
            "ipmctl.exe show -system -capabilities", "Get system capability", self.command_timeout)
        self._log.info("DCPMM system capabiities...  {}".format(ipmctl_system_cap))

        return ipmctl_system_cap

    def show_dimm_status(self):
        """
        Function to get the dimm status of by using IPMCTL tool

        :return: dimm_status_result
        """
        dimm_status_result = self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_DIMM_STATUS, "To display the DIMM's present status",
            self.command_timeout)
        if dimm_status_result != '':
            self._log.info("Present Status of DIMMs are... {}".format(dimm_status_result))

        return dimm_status_result

    def delete_pcd_data(self):
        """
        This function is used to delete the PCD data.

        :return: None
        """
        self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.DELETE_PCD_COMMAND, "To delete the pcd data", self.command_timeout)

    def umount_existing_devices(self):
        """
        This function is used to un mount the pmem devices.

        :raise: NotImplementedError
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "UEFI shell..".format("umount_existing_devices"))

    def get_existing_mount_points_fstab(self):
        """
        This function is used to get the mount points from the /etc/fstab file

        :raise: NotImplementedError
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "UEFI shell..".format("get_existing_mount_points_fstab"))

    def remove_fstab_data(self):
        """
        This function is used to remove PMEM data in the /etc/fstab file.

        :raise: NotImplementedError
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "UEFI shell..".format("remove_fstab_data"))

    def show_dimm_thermal_error(self):
        """
        Function to get the dimm thermal errors using IPMCTL tool

        :return: dimm_thermal errors
        """
        dimm_thermal_result = self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_DIMM_THERMAL_ERR_STATUS, "To display the DIMM's thermal status",
            self.command_timeout)
        if dimm_thermal_result != '':
            self._log.info("Present Status of DIMMs are... {}".format(dimm_thermal_result))
        self._log.info("DCPMM thermal error data : {}".format(dimm_thermal_result))
        return dimm_thermal_result

    def show_dimm_media_error(self):
        """
        Function to get the dimm thermal errors using IPMCTL tool

        :return: dimm_thermal errors
        """

        cmd = self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_DIMM_MEDIA_ERR_STATUS

        dimm_media_result = self._os.execute(cmd, self.command_timeout)

        if dimm_media_result.cmd_failed():
            if "Data Path Error" in dimm_media_result.stdout:
                self._log.info("Crow Pass DIMM Data path error can be ignored as it is referring to the older "
                               "history..")
            else:
                log_error = "Failed to run '{}' command with return value = '{}' and " \
                            "std_error='{}'..".format(cmd, dimm_media_result.return_code, dimm_media_result.stderr)
                self._log.error(log_error)
                raise RuntimeError(log_error)
        else:
            self._log.debug(dimm_media_result.stdout)

        if dimm_media_result.stdout != '':
            self._log.info("Present Status of DIMMs are...{}".format(dimm_media_result.stdout))

        return dimm_media_result.stdout

    def verify_mem_resource_provisioned_capacity(self, mem_resource_op):

        """
        Function to verify_mem_resource_provisioned_capacity

        :param mem_resource_op: mem_resource_op
        :return: boolean(True/False)
        """
        ret_verify_mem_resource = False
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
                ret_verify_mem_resource = True
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
        return ret_verify_mem_resource

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

    def get_error_logs(self, *err_type):
        """
        Function to get the error logs for media and thermal using ipmctl commands.

        :param err_type: will hold the error types.
        :return None
        """
        for err_tp in err_type:
            cmd_run = "ipmctl show -error {} -dimm > {}.log".format(err_tp, err_tp)

            self.common_content_lib_obj.execute_sut_cmd(cmd_run, "Get {} error".format(err_tp),
                                                        self.command_timeout)

    def verify_media_thermal_error(self, err_type, log_path):
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

    def dump_provisioning_data(self, config_file_name):
        """
        Function to Store the currently configured memory allocation settings for all DCPMMs in the system to a file.

        :param config_file_name: file name in which current provisioning configuration will save
        :return : true on success
        :raise: RuntimeError
        """
        result = self.common_content_lib_obj.execute_sut_cmd(self.ipmctl_cmd_name +
                                                             self.IPMCTL_CMD_DUMP_CURRENT_PROVISION_CONFIG.
                                                             format(config_file_name),
                                                             "Dump current provisioning data", self.command_timeout)
        if "Successfully" not in result:
            err_msg = "Fail to dump the current provisioning configuration data"
            self._log.error(err_msg)
            raise RuntimeError(err_msg)
        self._log.info("Successfully dumped the current provisioning data : {}".format(result))
        return True

    def restore_memory_allocation_settings(self, config_file_name):
        """
        Function to Restore the previous configured memory allocation settings from stored config file.

        :param config_file_name: file name from which provisioning configuration data will load
        :return : true on success
        :raise: RuntimeError
        """
        result_data = self.common_content_lib_obj.execute_sut_cmd(self.ipmctl_cmd_name +
                                                                  self.IPMCTL_CMD_CREATE_GOAL_FROM_CONFIG_FILE.
                                                                  format(config_file_name),
                                                                  "loading goal from configuration file",
                                                                  self.command_timeout)

        if result_data == "":
            err_msg = "Fail to restore the memory allocation from the config file"
            self._log.error(err_msg)
            raise RuntimeError(err_msg)
        self._log.info("Successfully loaded the goal from configuration file : {}".format(result_data))
        return result_data

    def show_all_region_data(self):
        """
         Function to show all the regions after goal creation

        :return: dimm_region_info
        """
        return self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.SHOW_ALL_REGIONS_COMMAND, "To display the DIMM's region info",
            self.command_timeout)

    def region_data_after_goal(self, index):
        """
         Function to create all the regions after goal creation

        :param index: index
        :raise: NotImplementedError
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "UEFI shell..".format("region_data_after_goal"))

    def get_dimm_info(self):
        """
        Function to run dimm info via uefi shell

        :raise: NotImplementedError
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "UEFI shell..".format("get_dimm_info"))

    def dcpmm_get_app_direct_mode_settings(self):
        """
        Function to  display the recommended App Direct Mode setting capabilities

        :param: Path of ipmctl tool
        :return dcpmm_disk_namespace: disk namespace info
        """

        dcpmm_app_direct_mode_settings = self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_APP_DIRECT_MODE_SETTINGS, "To display the recommended "
                                                                                  "App Direct Mode setting capabilities",
            self.command_timeout)
        if dcpmm_app_direct_mode_settings != '':
            self._log.info("App Direct Mode Settings capabilities... \n {}".format(dcpmm_app_direct_mode_settings))

        return dcpmm_app_direct_mode_settings

    def dimm_diagnostic_config_check(self):
        """
        Function to run quick check diagnostic on all installed DCPMMs

        :return: diagnostic_val
        """
        config_val = self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_DIAGNOSTIC_CONFIG, "run diagnostic config",
            self.command_timeout)

        self._log.debug("The diagnostic config data is: {}".format(config_val))
        self._log.info("Successfully run diagnostic config command...")

        return config_val

    def system_nfit(self):
        """
        Function to run NFIT commands

        :return: show_system_nfit
        """
        show_system_nfit = self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_SYSTEM_NFIT, "To show system NFIT",
            self.command_timeout)
        self._log.info("DCPMM System NFIT data : {}".format(show_system_nfit))
        return show_system_nfit

    def system_pmtt(self):
        """
        Function to run PMTT commands to show that the system via uefi shell

        :raise: NotImplementedError
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "UEFI shell..".format("system_pmtt"))

    def check_thermal_error(self):
        """
        Function to run thermal command in uefi shell

        :raise: NotImplementedError
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "UEFI shell..".format("check_thermal_error"))

    def check_media_error(self):
        """
        Function to run media command in uefi shell

        :raise: NotImplementedError
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "UEFI shell..".format("check_media_error"))

    def get_boot_status_register(self):
        """
        Function to run boot status register command in uefi shell

        :raise: NotImplementedError
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "UEFI shell..".format("get_boot_status_register"))

    def get_system_pcat(self):
        """
        Function to run NFIT commands

        :return: show_system_pcat
        """
        show_system_pcat = self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_SYSTEM_PCAT, "To show system PCAT",
            self.command_timeout)
        self._log.info("DCPMM system PCAT data : {}".format(show_system_pcat))
        return show_system_pcat

    def dimm_diagnostic(self):
        """
        Function to Execute the default set of all diagnostics on installed DCPMMs via uefi shell

        :raise: NotImplementedError
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "UEFI shell..".format("dimm_diagnostic"))

    def dimm_diagnostic_quick_check(self):
        """
        Function to run quick check diagnostic on all installed DCPMMs.

        :return: diagnostic_val
        """
        diagnostic_val = self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_DIAGNOSTIC_QUICK, "run diagnostic quick",
            self.command_timeout)

        self._log.debug("The diagnostic quick data is: {}".format(diagnostic_val))

        self._log.info("Successfully run diagnostic quick command...")
        return diagnostic_val

    def dimm_diagnostic_check(self, dimm_id):
        """
        Function to execute the quick check diagnostic on a single DCPMM  via uefi shell

        :param: dimm_id
        :raise: NotImplementedError
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "UEFI shell..".format("dimm_diagnostic_check"))

    def get_dimm_id(self):
        """
        Function to get dimm ids  via uefi shell

        :raise: NotImplementedError
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "UEFI shell..".format("get_dimm_id"))

    def dimm_diagnostic_help(self):
        """
        Function to run diagnostic help command via uefi shell

        :raise: NotImplementedError
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "UEFI shell..".format("dimm_diagnostic_help"))

    def dimm_diagnostic_security(self):
        """
        Function to run diagnostic security command

        :raise: security_val
        """
        security_val = self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_DIAGNOSTIC_SEC, "run diagnostic security",
            self.command_timeout)

        self._log.debug("The diagnostic security data is: {}".format(security_val))

        self._log.info("Successfully executed diagnostic security command...")
        return security_val

    def dimm_version(self):
        """
        Function to run ipmctl version via uefi shell

        :raise: NotImplementedError
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "UEFI shell..".format("dimm_version"))

    def show_firmware(self):
        """
        Function to run the DCPMM Firmware

        :return: show_firmware_info
        """
        show_firmware_info = self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_SHOW_FIRMWARE, "To show Firmware info",
            self.command_timeout)

        return show_firmware_info

    def get_pcd_config(self):
        """
        Function to run the platform configuration data for each DCPMM via uefi shell

        :raise: NotImplementedError
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "UEFI shell..".format("get_pcd_config"))

    def list_dcpmm_existing_error_logs(self):
        """
        This Method is Used to List the Existing DCPMM Error Logs.

        :return: command output
        """
        command_result = self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_FOR_LISTING_EXISTING_DCPMM_ERRORS.format
            (self.dimm_healthy_and_manageable_list[0]), "DCPMM Error Logs", self.command_timeout)

        dcpmm_existing_errors_cmd_output = command_result.strip()
        self._log.info(dcpmm_existing_errors_cmd_output)
        return dcpmm_existing_errors_cmd_output

    def clear_fatal_media_error(self):
        """
        This Method clears Injected Fatal Media Error to DCPMM media.

        :return:
        :raise: RuntimeError if fails.
        """
        try:
            self.common_content_lib_obj.execute_sut_cmd(
                self.ipmctl_cmd_name + self.IPMCTL_CMD_FOR_CLEAR_INJECTED_POISON.format(
                    self.dimm_healthy_and_manageable_list[0]),
                "DCPMM clear injected poison", self.command_timeout)
        except Exception as ex:
            log_error = "Unable to clear injected poison due to Exception {}".format(ex)
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def get_viral_status_of_dcpmm_dimms(self):
        """
        This Method provides viral status and viral Policy of DCPMM DIMMS.

        :return: True if all DCPMMS viral Policy is 1 else False
        """
        ret_value = True

        ret_val = self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_FOR_VIRAL_STATUS, "get Viral status", self.command_timeout)

        list_cmd_output = str(ret_val).strip('\n')
        for each in list_cmd_output:
            if "ViralPolicy" in each:
                if each.split("=")[1].strip() != 1:
                    ret_value = False
            if "ViralState" in each:
                if each.split("=")[1].strip() != 0:
                    ret_value = False
        return ret_value

    def inject_fatal_media_error(self):
        """
        This Method Inject a Fatal Media Error to DCPMM media

        :return:
        :raise: RuntimeError if injection fails.
        """
        self._os.execute_async(self.IPMCTL_CMD_FOR_FATAL_MEDIA_ERROR.
                               format(self.dimm_healthy_and_manageable_list[0]))

        if self._os.is_alive():
            log_error = "Failed to run {} command".format(self.IPMCTL_CMD_FOR_FATAL_MEDIA_ERROR)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        else:
            self._log.info("System is hung, requires a power cycle to recover")
            if self._ac_power.ac_power_off(self._common_content_configuration.ac_timeout_delay_in_sec()):
                self._log.info("AC power supply has been removed")
            else:
                log_error = "Failed to power-off SUT.."
                self._log.error(log_error)
                raise RuntimeError(log_error)
            time.sleep(self._common_content_configuration.itp_halt_time_in_sec())
            if self._ac_power.ac_power_on(self._common_content_configuration.ac_timeout_delay_in_sec()):
                self._log.info("AC power supply has been connected")
            else:
                log_error = "Failed to power-on SUT.."
                self._log.error(log_error)
                raise RuntimeError(log_error)
            self._os.wait_for_os(
                self._common_content_configuration.os_full_ac_cycle_time_out())  # Wait for System to come in OS State

    def clear_inject_media_error(self, dimm, addr):
        """
        This Method provides clear media error.

        :param dimm: dimm number
        :param addr: address to clear
        :raise NotImplementedError
        """
        raise NotImplementedError

    def show_region(self):
        """
         Function to show the regions after goal creation

        :return: dimm_region_info
        """
        return self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.SHOW_REGION_COMMAND, "To display the DIMM's region info",
            self.command_timeout)

    def get_disk_namespace_info(self):
        """
        Function to get the DCPMM disk namespaces information.

        :raise: NotImplementedError
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "UEFI shell..".format("get_disk_namespace_info"))

    def dimm_diagnostic_firmware(self):
        """
        Function to run firmware check diagnostic on all installed DCPMMs

        :return: diagnostic_val
        """
        diagnostic_val = self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_DIAGNOSTIC_FW, "run diagnostic firmware",
            self.command_timeout)

        self._log.debug("The diagnostic firmware data is: {}".format(diagnostic_val))
        self._log.info("Successfully run diagnostic firmware command...")
        return diagnostic_val

    def show_dimm_pcd(self):
        """
        Function to show the pcd data.

        :return: pcd_info
        """
        pcd_info = self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_FOR_SHOW_PCD, "To display PCD info",
            self.command_timeout)

        self._log.info("The DCPMM PCD data: \n{}".format(pcd_info))

        return pcd_info

    def show_system(self):
        """
        Function to show the system data.

        :return: show_system_info
        """
        show_system_info = self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_FOR_SHOW_SYSTEM, "To display system info",
            self.command_timeout)
        self._log.info("The DCPMM system info : \n {}".format(show_system_info))

        return show_system_info

    def show_dimm_performance(self):
        """
        Function to show the dimm performance.

        :return: show_dimm_performance
        """
        show_dimm_performance = self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_DIMM_PERFORMANCE, "To show dimm performance info",
            self.command_timeout)
        self._log.info("The DCPMM DIMM performance info info : \n {}".format(show_dimm_performance))

        return show_dimm_performance

    def show_ars_status(self):
        """
        Function to show the ARSStatus

        :return: show_ars_status
        """
        show_ars_status = self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_ARS_STATUS, "To show ARSStatus info",
            self.command_timeout)
        self._log.info("The DCPMM show ARSStatus info : \n {}".format(show_ars_status))

        return show_ars_status

    def show_socket(self):
        """
        Function to show the socket info

        :return: show_socket_info
        """
        show_socket_info = self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_SOCKET, "To show Socket info",
            self.command_timeout)
        self._log.info("The DCPMM show socket info : \n {}".format(show_socket_info))

        return show_socket_info

    def show_preferences(self):
        """
        Function to show the preferences info

        :return: show_preferences_info
        """
        show_preferences_info = self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_PREFERENCES, "To show Socket info",
            self.command_timeout)
        self._log.info("The DCPMM DIMM preferences info : \n {}".format(show_preferences_info))
        return show_preferences_info

    def verify_lm_provisioning_configuration(self, dcpmm_disk_goal, mode):
        """
        Function to verify provisioning configuration.

        :param: dcpmm_disk_goal: goal information
        :param: mode: mode to check 1LM or 2LM
        :return: verify_provisioning_status
        """

        #  Verify 2LM provisioning mode
        verify_provisioning_status = self._memory_common_lib.verify_lm_provisioning_configuration_win(
            dcpmm_disk_goal, mode)
        return verify_provisioning_status

    def verify_pmem_device_presence_cap(self, namespace_info, appdirect_percent=100):
        """
        Function to get the the list of pmem devices and verify if the desired devices are present on SUT

        :param namespace_info: Namespace output
        :param appdirect_percent: mode percent
        :return: mem info and partition data
        """
        dcpmm_capacity_config = int(int(self._common_content_configuration.memory_bios_total_dcpmm_memory_capacity()) *
                                    (appdirect_percent / 100))
        variance_percent = float(self._common_content_configuration.get_memory_variance_percent())

        # Memory total with variance
        dcpmm_total_with_variance_config = (dcpmm_capacity_config - (dcpmm_capacity_config * variance_percent))

        pmem_device_sizes = re.findall(r"[\d]*\sGB", namespace_info)
        total_namespace_size = 0
        for size in pmem_device_sizes:
            total_namespace_size = total_namespace_size + int(re.sub(r"\D", '', size))

        if int(total_namespace_size) < dcpmm_total_with_variance_config or int(total_namespace_size) > \
                dcpmm_capacity_config:
            raise content_exceptions.TestFail("Total dcpmm dimm Capacity is not nearly around {}% of "
                                              "DCPMM..".format(appdirect_percent))

        self._log.info("Successfully verified the dcpmm capacity and it is around {}% of "
                       "DCPMM..".format(appdirect_percent))

    def delete_pmem_device(self):
        """
        Function to delete the pmem devices.

        :return: True
        """
        if not self._os.is_alive():
            self._log.error("System is not alive, wait for the sut online")
            self.common_content_lib_obj.perform_graceful_ac_off_on(self._ac_power)
            self.common_content_lib_obj.wait_for_os(self._reboot_timeout)

        # Get available name space info
        namespace_output = self.dcpmm_get_disk_namespace()

        # Clear the namespaces if exists
        self.dcpmm_check_disk_namespace_initilize(namespace_output)

        # Clear namespace if still persists in system
        namespace_output = self.dcpmm_get_disk_namespace()
        self.dcpmm_check_disk_namespace_initilize(namespace_output)

        self.delete_pcd_data()
        self._log.info("Cleared PCD data on the dimms, restarting the SUT to apply the changes..")

        # Restart the SUT
        self.common_content_lib_obj.perform_os_reboot(self._reboot_timeout)
        return True
