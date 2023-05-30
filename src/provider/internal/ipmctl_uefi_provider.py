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
#   UEFI IPMCTL PROVIDER
from src.lib import content_exceptions
from src.provider.ipmctl_provider import IpmctlProvider
from src.lib.memory_dimm_info_lib import MemoryDimmInfo

import re


class IpmctlProviderUefi(IpmctlProvider):
    PROVISIONING_COMMAND = "ipmctl.efi show -d modessupported -system -capabilities"
    PROVISIONING_DIMM_COMMAND = "ipmctl.efi show -dimm"
    PROVISIONING_APP_DIRECT_COMMAND = "ipmctl.efi show -d recommendedappdirectsettings -system -capabilities"
    NAMESPACE_SHOW_COMMAND = "ipmctl.efi  show -a -namespace"
    NAMESPACE_CLEAR_COMMAND = "ipmctl.efi delete -f -namespace"
    CREATE_GOAL_COMMAND = "ipmctl.efi create -f -goal persistentmemorytype=appdirectnotinterleaved"
    SHOW_MEMEORY_SUPPORT_CMD = "ipmctl.efi  show -memoryresources"
    SHOW_ALL_REGION_COMMAND = "ipmctl.efi show -a -region"
    SHOW_REGION_COMMAND = "ipmctl.efi show -region"
    CREATE_REGION_COMMAND = "ipmctl.efi create -f -namespace -region"
    MAP_COMMAND = "map -r"
    SHOW_GOAL_COMMAND = "ipmctl.efi show -goal"
    CONFIG_CSV_COMMAND = "ipmctl.efi dump -destination config.csv -system -config"
    UEFI_CONFIG_PATH = 'suts/sut/providers/uefi_shell'
    BIOS_BOOTMENU_CONFIGPATH = "suts/sut/providers/bios_bootmenu"
    IPMCTL_CMD_SHOW_SENSOR = r" show -sensor"
    IPMCTL_CMD_SHOW_DIMM_STATUS = r" show -d HealthState,ManageabilityState,FWVersion,DeviceLocator -dimm"
    IPMCTL_CMD_DUMP_CONFIG_CSV = r" dump -destination config.csv -system -config"
    IPMCTL_CMD_SHOW_APP_DIRECT_MODE_SETTINGS = r" show -d recommendedappdirectsettings -system -capabilities"
    IPMCTL_CMD_SHOW_DIMM_THERMAL_ERR_STATUS = " show -error Thermal -dimm"
    IPMCTL_CMD_SHOW_DIMM_MEDIA_ERR_STATUS = " show -error media -dimm"
    IPMCTL_SHOW_MANAGEABILTY_CMD = " show -d ManageabilityState -dimm"
    IPMCTL_CMD_SHOW_DIMM = r" show -dimm"
    IPMCTL_CMD_SHOW_TOPOLOGY = r" show -topology"
    IPMCTL_CMD_SHOW_MODES = r" show -d modessupported -system -capabilities"
    IPMCTL_CMD_SHOW_GOAL = r" show -goal"
    IPMCTL_CMD_SHOW_MEM_RESOURCES = r" show -memoryresources"
    NAMESPACE_ID_REGX = r"NamespaceId=0x[0-9]*"
    MEM_REGEX = r"Mem:\s*[0-9]*"
    IPMCTL_CMD_DUMP_CURRENT_PROVISION_CONFIG = " dump -destination {} -system -config"
    IPMCTL_CMD_CREATE_GOAL_FROM_CONFIG_FILE = " load -f -source {} -goal"
    IPMCTL_PCD_CFG = "ipmctl.efi show -dimm -pcd Config"
    IPMCTL_CMD_FOR_LISTING_EXISTING_DCPMM_ERRORS = " show -error Media -dimm {}"
    IPMCTL_CMD_FOR_FATAL_MEDIA_ERROR = r"ipmctl set -dimm {} FatalMediaError=1"
    IPMCTL_CMD_FOR_CLEAR_INJECTED_POISON = r" set -dimm {} Clear=1 FatalMediaError=1"
    IPMCTL_CMD_FOR_VIRAL_STATUS = " show -d ViralPolicy,ViralState -dimm"
    REGEX_CMD_FOR_HEALTH_STATUS_CHANGE_ERROR = r"Error\sType\s+:\s+\S+\s-\sSmart\sHealth\sStatus\sChange"
    DELETE_PCD_COMMAND = " delete -f -pcd -dimm"

    def __init__(self, log, os_obj, uefi_util_obj=None, cfg_opts=None):
        super(IpmctlProviderUefi, self).__init__(log, os_obj, uefi_util_obj, cfg_opts)
        self._log = log
        self._os = os_obj
        self.ipmctl_cmd_name = "ipmctl.efi"
        self.mount_list = []
        self.store_generated_dcpmm_drive_letters = []
        self.dimm_healthy_list = []
        self.dimm_healthy_and_manageable_list = []
        self.df_dimm_fw_version_op = None
        self.show_dimm_dataframe = None

    def get_dimm_info(self):
        """
        Function to run dimm info via uefi shell

        :return: ret_val
        """
        ret_val = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.PROVISIONING_DIMM_COMMAND)
        dimm_info = ' '.join(map(str, ret_val))
        if not dimm_info:

            error_msg = "Failed to get dimm values"
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.debug("DIMM information with capacity and FW verion...{}".format(dimm_info))
        return dimm_info

    def dcpmm_get_app_direct_mode_settings(self):
        """
        Function to run app  direct support command  via uefi shell

        :return: ret_val
        """
        ret_val = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.PROVISIONING_APP_DIRECT_COMMAND)
        if len(ret_val) == 0:
            error_msg = "Failed to get app direct values"
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully get app direct values...")
        return ret_val

    def show_all_region_data(self):
        """
        Function to show  all the regions on uefi shell after goal creation

        :return: list of regions
        """
        ret_val = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.SHOW_ALL_REGION_COMMAND)
        region_data = ''.join(map(str, ret_val))
        if not region_data:
            error_msg = "Failed to create region ID"
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully created region ID...")
        return region_data

    def region_data_after_goal(self, index):
        """
        Function to create all the regions after goal creation

        :return: list of regions
        """
        ret_val = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.CREATE_REGION_COMMAND + " " + index)
        ret_val = ''.join(map(str, ret_val))
        ret_val_list = ret_val.split(",")

        for line in ret_val_list:
            if "HealthState=Unknown" in line:
                self._log.debug("{} - The region health cannot be determined.".format(index))
            elif "HealthState=Healthy" in line:
                self._log.debug("{} - Underlying DCPMM persistent memory capacity is available.".format(index))
            elif "HealthState=Pending" in line:
                self._log.debug("{} - A new memory allocation goal has been created but not applied.".format(index))
            elif "HealthState=Error" in line:
                self._log.debug("{} - There is an issue with some or all of the underlying DCPMM capacity "
                                "because the interleave set has failed.".format(index))
            elif "HealthState=Locked" in line:
                self._log.debug("{} - One or more of the of the underlying DCPMMs are locked.".format(index))

        if ret_val:
            self._log.info("A namespace is created without issues on region - {}.".format(index))
        else:
            error_msg = "Failed to create a namespace region on {}."
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        return ret_val

    def get_list_of_dimms_which_are_healthy_and_manageable(self):
        """
        This Method is Used to Fetch List of All the Healthy and Manageable Dimm's and raise the RunTimeError if
        there are no Healthy and Manageable Dimms.

        :raise: RuntimeError if there are no Healthy and Manageable Dimm's
        """
        if len(self.dimm_healthy_and_manageable_list) > 0:
            for dimm in self.dimm_healthy_and_manageable_list:
                self._log.debug("Dimm{} is Healthy and Manageable".format(dimm))
        else:
            log_error = "We don't have Dimm's which are Healthy and Manageable"
            self._log.error(log_error)
            raise RuntimeError(log_error)

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
                self._log.debug("There are no '{}' errors in log stored under '{}'".format(err_type, log_path))

        return ret_val

    def show_dimm_status(self):
        """
        Function to get the dimm status of by using IPMCTL tool

        :return: dimm_status_result
        """
        dimm_status_result = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_DIMM_STATUS)
        dimm_status_result = ''.join(map(str, dimm_status_result))
        if dimm_status_result != '':
            self._log.debug("Present Status of DIMMs are... {}".format(dimm_status_result))

        return dimm_status_result

    def create_config_csv(self):
        """
        Store the currently configured memory allocation settings for all DCPMMs in the system to a file

        :return None
        """
        store_configs = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.CONFIG_CSV_COMMAND)
        store_configs = ''.join(map(str, store_configs))
        if store_configs:
            self._log.info("Successfully created csv file in usb drive..")
        else:
            error_msg = "Failed to create csv file in usb drive.."
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.debug("Storing the currently configured memory allocation settings for all DCPMMs "
                       "in the system to a file...  {}".format(store_configs))

    def delete_pcd_data(self):
        """
        This function is used to delete the PCD data.

        :return: None
        """
        self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.ipmctl_cmd_name + self.DELETE_PCD_COMMAND)

    def dump_provisioning_data(self, config_file_name):
        """
        Function to Store the currently configured memory allocation settings for all DCPMMs in the system to a file.

        :param config_file_name: file name in which current provisioning configuration will save

        :return : true on success
        :raise: RuntimeError
        """
        result = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.ipmctl_cmd_name +
                                                                          self.IPMCTL_CMD_DUMP_CURRENT_PROVISION_CONFIG.
                                                                          format(config_file_name))
        result = ' '.join(map(str, result))
        if "Successfully" not in result:
            err_msg = "Fail to dump the current provisioning configuration data"
            self._log.error(err_msg)
            raise RuntimeError(err_msg)
        self._log.debug("Successfully dumped the current provisioning data : {}".format(result))
        return True

    def get_error_logs(self, *err_type):
        """
        Function to get the error logs for media and thermal using ipmctl commands.

        :param err_type: will hold the error types.
        :return None
        """
        for err_tp in err_type:
            cmd_run = " show -error {} -dimm > {}.log".format(err_tp, err_tp)

            self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.ipmctl_cmd_name + cmd_run)

    def get_list_of_dimms_which_are_healthy(self):
        """
        This Method is Used to Fetch List of All the Healthy Dimm's.

        :return: None
        :raise: RuntimeError if there are no Healthy Dimm's
        """
        if len(self.dimm_healthy_list) > 0:
            for dimm in self.dimm_healthy_list:
                self._log.debug("Dimm {} is Healthy".format(dimm))
        else:
            log_error = "We don't have Dimm's which are Healthy.."
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def get_system_capability(self):
        """
        Function to configure all available pmem devices with namespaces.

        :return ipmctl_system_cap: the namespace has been created.
        """
        sys_capability = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.IPMCTL_CAPABILITY_CMD)
        sys_capability = ' '.join(map(str, sys_capability))
        if not sys_capability:
            error_msg = "Failed to run system capability command "
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully run system capability command...")
        return sys_capability

    def show_mem_resources(self):
        """
        Function to configure DCPMM devices are normal and the DCPMM mapped memory configuration
        matches the applied goal.

        :return dcpmm_mem_resource: memory information
        """
        ret_val = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.SHOW_MEMEORY_SUPPORT_CMD)
        ret_val = ''.join(map(str, ret_val))
        if not ret_val:
            error_msg = "Failed to execute memory support command"
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        return ret_val

    def get_supported_modes(self):
        """
        Function to get the DCPMM dimm topology.

        :return ipmctl_show_sup_mode: supported modes
        """
        ret_val = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.PROVISIONING_COMMAND)
        ret_val = ' '.join(map(str, ret_val))
        if not ret_val:
            error_msg = "Failed to get the modes supported values"
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully get the modes supported values...")
        return ret_val

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

            ipmctl_show_topology = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(
                self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_TOPOLOGY)
            ipmctl_show_topology = ''.join(map(str, ipmctl_show_topology))
            self.show_topology_output = ipmctl_show_topology.split(",")[0]

            ipmctl_show_dimm = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(
                self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_DIMM)
            ipmctl_show_dimm = ''.join(map(str, ipmctl_show_dimm))
            show_dimm_command_output = ipmctl_show_dimm.split(",")[0]

            # Get manageability output using ipmctl command
            command_result = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(
                self.ipmctl_cmd_name + self.IPMCTL_SHOW_MANAGEABILTY_CMD)
            command_result = ''.join(map(str, command_result))
            manageability_state_command_output = command_result.split(',')[0]

            # Object creation
            memory_info_obj = MemoryDimmInfo(self.show_topology_output, show_dimm=show_dimm_command_output,
                                             manageability=manageability_state_command_output)

            self.dimm_healthy_list = memory_info_obj.get_dimm_info_healthy()

            self.dimm_healthy_and_manageable_list = memory_info_obj.get_dimm_info_healthy_manageable()

            self.df_dimm_fw_version_op = memory_info_obj.df_dimm_fw_version

            self._log.debug("DCPMM topology data frame...  {} ".format(self.df_dimm_fw_version_op))

            self.show_dimm_dataframe = memory_info_obj.get_show_dimm_data_frame()

            self._log.debug("DCPMM show dimm info data frame...  {} ".format(self.show_dimm_dataframe))

            return show_dimm_command_output
        except Exception as ex:
            log_error = "Unable to Execute IPMCTL Commands on SUT {}".format(ex)
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def restore_memory_allocation_settings(self, config_file_name):
        """
        Function to Restore the previous configured memory allocation settings from stored config file.

        :param config_file_name: file name from which provisioning configuration data will load

        :return : true on success
        :raise: RuntimeError
        """
        result_data = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_CREATE_GOAL_FROM_CONFIG_FILE.format(config_file_name))
        result_data = ''.join(map(str, result_data))
        if result_data == "":
            err_msg = "Fail to restore the memory allocation from the config file"
            self._log.error(err_msg)
            raise RuntimeError(err_msg)
        self._log.debug("Successfully loaded the goal from configuration file : {}".format(result_data))
        return result_data

    def show_dimm_media_error(self):
        """
        Function to get the dimm thermal errors using IPMCTL tool

        :return: dimm_thermal errors
        """
        dimm_media_result = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_DIMM_MEDIA_ERR_STATUS)
        dimm_media_result = ''.join(map(str, dimm_media_result))
        if dimm_media_result != '':
            self._log.debug("Present Status of DIMMs are...{}".format(dimm_media_result))

        return dimm_media_result

    def show_dimm_thermal_error(self):
        """
        Function to get the dimm thermal errors using IPMCTL tool

        :return: dimm_thermal errors
        """
        dimm_thermal_result = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_DIMM_THERMAL_ERR_STATUS)
        dimm_thermal_result = ''.join(map(str, dimm_thermal_result))
        if dimm_thermal_result != '':
            self._log.debug("Present Status of DIMMs are... {}".format(dimm_thermal_result))

        return dimm_thermal_result

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

    def show_topology(self):
        """
        Function to run the DCPMM topology command via uefi shell

        :return:topology_val
        """
        topology_val = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.ipmctl_cmd_name +
                                                                                self.IPMCTL_CMD_SHOW_TOPOLOGY)
        if not topology_val:
            error_msg = "Failed to run system topology command "
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully run system topology command...")
        return topology_val

    def show_firmware(self):
        """
        Function to run the DCPMM topology command via uefi shell

        :return:firmware_val
        """
        firmware_val = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response("ipmctl.efi show -firmware")
        if not firmware_val:
            error_msg = "Failed to run system firmware command "
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully run system firmware command...")
        return firmware_val

    def dimm_version(self):
        """
        Function to run ipmctl version via uefi shell

        :return: ipmctl_version
        """
        ipmctl_version = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.IPMCTL_VERSION)
        ipmctl_version = ' '.join(map(str, ipmctl_version))
        if not ipmctl_version:
            error_msg = "Failed to get ipmctl version"
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully get ipmctl version...")
        return ipmctl_version

    def dimm_diagnostic_security(self):
        """
        Function to run diagnostic security command via uefi shell

        :return: diagnostic_val
        """
        diagnostic_val = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            "ipmctl.efi start -diagnostic Security")
        if not diagnostic_val:
            error_msg = "Failed to run diagnostic security command "
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully run diagnostic security command...")
        return diagnostic_val

    def dimm_diagnostic_help(self):
        """
        Function to run diagnostic help command via uefi shell

        :return: diagnostic_val
        """
        diagnostic_help = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            "ipmctl.efi start -help -diagnostic")
        diagnostic_help = ''.join(map(str, diagnostic_help))
        if not diagnostic_help:
            error_msg = "Failed to run diagnostic help command "
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully run diagnostic help command...")
        return diagnostic_help

    def get_dimm_id(self):
        """
        Function to get dimm ids  via uefi shell

        :return: list_dimm_id
        """
        list_dimm_id = []
        dimm_info = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.PROVISIONING_DIMM_COMMAND)
        for index in dimm_info:
            if re.search("0x[0-9]*", index):
                list_dimm_id.extend(re.findall("0x[0-9]*", index))
        return list_dimm_id

    def dimm_diagnostic_check(self, dimm_id):
        """
        Function to execute the quick check diagnostic on a single DCPMM  via uefi shell

        :param: dimm_id
        :return: diagnostic_check_val
        """
        for index in dimm_id:
            diagnostic_check_val = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(
                "ipmctl.efi start -diagnostic Quick -dimm" + " " + index)
            if not diagnostic_check_val:
                error_msg = "Failed to run quick  diagnostic command "
                self._log.error(error_msg)
                raise RuntimeError(error_msg)
            self._log.info("Successfully run diagnostic quick command...")
            return diagnostic_check_val

    def dimm_diagnostic_quick_check(self):
        """
        Function to run quick check diagnostic on all installed DCPMMs via uefi shell

        :return: qucik_check_val
        """
        qucik_check_val = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            "ipmctl.efi start -diagnostic Quick")
        if not qucik_check_val:
            error_msg = "Failed to run diagnostic quick check command "
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully run diagnostic quick check command...")
        return qucik_check_val

    def dimm_diagnostic(self):
        """
        Function to Execute the default set of all diagnostics on installed DCPMMs via uefi shell

        :return: diagnostic_val
        """
        diagnostic_val = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response("ipmctl.efi start -diagnostic")
        if not diagnostic_val:
            error_msg = "Failed to run diagnostic security command "
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully run diagnostic security command...")
        return diagnostic_val

    def dimm_diagnostic_config_check(self):
        """
        Function to run quick check diagnostic on all installed DCPMMs via uefi shell

        :return: diagnostic_val
        """
        qucik_config_val = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            "ipmctl.efi start -diagnostic Config")
        if not qucik_config_val:
            error_msg = "Failed to run diagnostic config command "
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully run diagnostic config command...")
        return qucik_config_val

    def system_nfit(self):
        """
        Function to run NFIT commands to show that the system via uefi shell

        :return: nfit_val
        """
        nfit_val = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response("ipmctl.efi  show -system NFIT")
        if not nfit_val:
            error_msg = "Failed to run system NFIT command "
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully run system NFIT command...")
        return nfit_val

    def system_pmtt(self):
        """
        Function to run PMTT commands to show that the system via uefi shell

        :return: pmtt_val
        """
        pmtt_val = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response("ipmctl.efi  show -system PMTT")
        if not pmtt_val:
            error_msg = "Failed to run system PMTT command "
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully run system PMTT command...")
        return pmtt_val

    def check_thermal_error(self):
        """
        Function to run thermal command in uefi shell

        :return: thermal_val
        """
        thermal_val = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response("ipmctl.efi show -error Thermal -dimm")
        if not thermal_val:
            log_error = "Thermal command failed "
            self._log.error(log_error)
            raise RuntimeError(log_error)
        return thermal_val

    def check_media_error(self):
        """
        Function to run media command in uefi shell

        :return: dimm_val
        """
        media_val = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response("ipmctl.efi show -error Media -dimm")
        media_val = ''.join(map(str, media_val))
        if not media_val:
            log_error = "Media command failed "
            self._log.error(log_error)
            raise RuntimeError(log_error)
        return media_val

    def get_boot_status_register(self):
        """
        Function to run boot status register command in uefi shell

        :return: boot_reg_val
        """
        boot_reg_val = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response("ipmctl.efi show -d BootStatus -dimm")
        boot_reg_val = ''.join(map(str, boot_reg_val))
        if not boot_reg_val:
            log_error = "Boot status register command failed "
            self._log.error(log_error)
            raise RuntimeError(log_error)
        return boot_reg_val

    def get_system_pcat(self):
        """
        Function to run NFIT commands to show that the system via uefi shell

        :return: pcat_val
        """
        pcat_val = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response("ipmctl.efi  show -system PCAT")
        if not pcat_val:
            error_msg = "Failed to run system PCAT command "
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully run system PCAT command...")
        return pcat_val

    def show_sensors(self):
        """
        Function to get the DIMM sensor information.

        :return ipmctl_show_sensors: sensor information
        """
        ipmctl_show_sensors = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_SENSOR)
        ipmctl_show_sensors = ''.join(map(str, ipmctl_show_sensors))
        self._log.debug("DCPMM show sensor information... \n {}".format(ipmctl_show_sensors))

        return ipmctl_show_sensors

    def get_dcpmm_disk_list(self):
        """
        Function to display the pmem block info

        :return: stdout of the command ran
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "Windows or Linux shell..".format("get_dcpmm_disk_list"))

    def dcpmm_new_pmem_disk(self):
        """
        Function to configure all available pmem devices with namespaces.

        :return pmem_unused_new: the namespace has been created.
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "Windows or Linux shell..".format("dcpmm_new_pmem_disk"))

    def verify_mem_resource_provisioned_capacity(self, mem_resource_op):
        """
        Function to verify_mem_resource_provisioned_capacity

        :param mem_resource_op: mem_resource_op
        :raise NotImplementedError
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "Windows or Linux shell..".format("verify_mem_resource_provisioned_capacity"))

    def verify_dimms_firmware_version(self):
        """
        This method is used to verify the show topology firmware output with pmem device output.

        :return True if we have correct location of dimm
        """
        deviec_locator_result = []
        pmem_device_output = self.show_dimm_status()
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
        :raise NotImplementedError
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "Windows or Linux shell..".format("verify_dimms_device_locator"))

    def remove_fstab_data(self):
        """
        This function is used to remove PMEM data in the /etc/fstab file.

        :raise: NotImplementedError
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "Windows or Linux shell..".format("remove_fstab_data"))

    def umount_existing_devices(self):
        """
        This function is used to un mount the pmem devices.

        :raise: NotImplementedError
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "Windows or Linux shell..".format("umount_existing_devices"))

    def get_pmem_device(self):
        """
        This is function is used to get the persistent memory device information

        :raise NotImplementedError
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "Windows or Linux shell..".format("get_pmem_device"))

    def dcpmm_get_disk_namespace(self):
        """
        Function to get the DCPMM disk namespaces information.

        :return dcpmm_disk_namespace: disk namespace info
        """
        list_namespace_drives = []
        list_namespace = []
        ret_val = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.NAMESPACE_SHOW_COMMAND)
        self._log.debug("DCPMM Disk Namespace info succefully done...{}".format(ret_val))
        ret_val_str = ''.join(map(str, ret_val))
        if ret_val_str != '':
            for index in ret_val:
                if re.search(self.NAMESPACE_ID_REGX, index):
                    list_namespace_drives.extend(re.findall(self.NAMESPACE_ID_REGX, index))
            for index in list_namespace_drives:
                list_name = index.split("=")
                list_namespace.append(list_name[1])
        return list_namespace

    def dcpmm_get_pmem_device_fl_info(self):
        """
        Function to list the persistent memory regions.

        :raise NotImplementedError
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "Windows or Linux shell..".format("dcpmm_get_pmem_device_fl_info"))

    def dcpmm_get_pmem_unused_region(self):
        """
        The unused space now matches the installed persistent memory capacity

        :raise NotImplementedError
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "Windows or Linux shell..".format("dcpmm_get_pmem_unused_region"))

    def dcpmm_check_disk_namespace_initilize(self, namespace_info):
        """
        Function to check if there are existing namespaces present, execute the following command to initialize the
        DIMMs and remove all existing namespaces.

        :param namespace_info: namespace.
        :return initialize_dimm: disk namespace info
        """
        initialize_dimm = None

        if namespace_info != '':
            initialize_dimm = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.NAMESPACE_CLEAR_COMMAND)

            self._log.debug("DCPMM disk pre-existing namespace Initialization started...  {}".format(initialize_dimm))
        else:
            self._log.info("There are no existing namespaces, continue to configure the installed DCPMM(s)..")

        return initialize_dimm

    def dcpmm_configuration(self, cmd=None, cmd_str=None):
        """
        Function to configure DCPMM dimms with appropriate volatile memory and persistent memory.
        Also, to fetch the memory allocation goal and its resources.

        :param cmd: holds the command to allocate the mode.
        :param cmd_str: str - holds the info about the command.
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "Windows or Linux shell..".format("dcpmm_configuration"))

    def show_goal(self):
        """
         Function to execute the show goal command in uefi

         :param: None
         :return: None
         """
        show_goal = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.SHOW_GOAL_COMMAND)
        show_goal = ''.join(map(str, show_goal))
        if not show_goal:
            error_msg = "Failed to show goal region "
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        return show_goal

    def get_existing_mount_points_fstab(self):
        """
        This function is used to get the mount points from the /etc/fstab file

        :raise: NotImplementedError
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "Windows or Linux shell..".format("get_existing_mount_points_fstab"))

    def get_pcd_config(self):
        """
        Function to run the platform configuration data for each DCPMM via uefi shell

        :param: None
        :return: pcd_cfg
        """
        pcd_cfg = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.IPMCTL_PCD_CFG)
        pcd_cfg = ''.join(map(str, pcd_cfg))
        if not pcd_cfg:
            error_msg = "Failed to get platform configuration data for each DCPMM "
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully to get platform configuration data for each DCPMM...")
        return pcd_cfg

    def list_dcpmm_existing_error_logs(self):
        """
        This Method is Used to List the Existing DCPMM Error Logs.

        :raise: NotImplementedError
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "Windows or Linux shell..".format("list_dcpmm_existing_error_logs"))

    def clear_fatal_media_error(self):
        """
        This Method clear a Fatal Media Error from DCPMM media

        :raise: NotImplementedError
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "Windows or Linux shell..".format("clear_fatal_media_error"))

    def get_viral_status_of_dcpmm_dimms(self):
        """
        This Method provides viral status and viral Policy of DCPMM DIMMS.

        :return: True if all DCPMMS viral Policy is 1 else False
        """
        ret_value = True

        ret_val = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_FOR_VIRAL_STATUS)

        list_cmd_output = ret_val
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
        This Method Injects a Fatal Media Error to DCPMM media

        :raise: NotImplementedError
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "Windows or Linux shell..".format("inject_fatal_media_error"))

    def show_region(self):
        """
        Function to show the regions on uefi shell after goal creation.

        :return: list of regions
        """
        ret_val = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.SHOW_REGION_COMMAND)
        region_data = ''.join(map(str, ret_val)).replace("\r", "\n")

        if not region_data:
            error_msg = "Failed to create region ID"
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully created region ID...")

        return region_data

    def get_disk_namespace_info(self):
        """
        Function to get the DCPMM disk namespaces information.

        :return dcpmm_disk_namespace: disk namespace info
        """

        ret_val = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(self.NAMESPACE_SHOW_COMMAND)

        return ret_val

    def dimm_diagnostic_firmware(self):
        """
        Function to run diagnostic firmware command via uefi shell

        :return: diagnostic_val
        """
        diagnostic_val = self.uefi_util_obj.execute_cmd_in_uefi_and_read_response(
            "ipmctl.efi start -diagnostic firmware")
        if not diagnostic_val:
            error_msg = "Failed to run diagnostic firmware command "
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully run diagnostic firmware command...")
        return diagnostic_val

    def show_dimm_pcd(self):
        """
        Function to show the pcd data.

        :return: pcd_info
        """
        pcd_info = self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_FOR_SHOW_PCD, "To display PCD info",
            self.command_timeout, self.ipmctl_path)

        self._log.info("The DCPMM PCD data: \n{}".format(pcd_info))

        return pcd_info

    def show_system(self):
        """
        Function to show the system data.

        :return: show_system_info
        """
        show_system_info = self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_FOR_SHOW_SYSTEM, "To display system info",
            self.command_timeout, self.ipmctl_path)
        self._log.info("The DCPMM system info : \n {}".format(show_system_info))

        return show_system_info

    def show_dimm_performance(self):
        """
        Function to show the dimm performance.

        :return: show_dimm_performance
        """
        show_dimm_performance = self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_DIMM_PERFORMANCE, "To show dimm performance info",
            self.command_timeout, self.ipmctl_path)
        self._log.info("The DCPMM DIMM performance info info : \n {}".format(show_dimm_performance))

        return show_dimm_performance

    def show_ars_status(self):
        """
        Function to show the ARSStatus

        :return: show_ars_status
        """
        show_ars_status = self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_ARS_STATUS, "To show ARSStatus info",
            self.command_timeout, self.ipmctl_path)
        self._log.info("The DCPMM show ARSStatus info : \n {}".format(show_ars_status))

        return show_ars_status

    def show_socket(self):
        """
        Function to show the socket info

        :return: show_socket_info
        """
        show_socket_info = self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_SOCKET, "To show Socket info",
            self.command_timeout, self.ipmctl_path)
        self._log.info("The DCPMM show socket info : \n {}".format(show_socket_info))

        return show_socket_info

    def show_preferences(self):
        """
        Function to show the preferences info

        :return: show_preferences_info
        """
        show_preferences_info = self.common_content_lib_obj.execute_sut_cmd(
            self.ipmctl_cmd_name + self.IPMCTL_CMD_SHOW_PREFERENCES, "To show Socket info",
            self.command_timeout, self.ipmctl_path)
        self._log.info("The DCPMM DIMM preferences info : \n {}".format(show_preferences_info))
        return show_preferences_info

    def verify_lm_provisioning_configuration(self, dcpmm_disk_goal, mode):
        """
        Function to verify provisioning configuration.

        :raise: NotImplementedError
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "Windows or Linux shell..".format("verify_lm_provisioning_configuration"))

    def verify_pmem_device_presence_cap(self, present_namespace_list, appdirect_percent=None):
        """
        Function to get the the listof pmem devices and verify if the desired devices are present or not on linux SUT

        :param present_namespace_list: Namespace output
        :param appdirect_percent: mode percent
        :raise: NotImplementedError
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "Windows or Linux shell..".format("verify_pmem_device_presence_cap"))

    def clear_inject_media_error(self, dimm, addr):
        """
        This Method provides clear media error.

        :param dimm: dimm number
        :param addr: address to clear
        :raise NotImplementedError
        """
        raise NotImplementedError("The function '{}' is supported only from "
                                  "Windows or Linux shell..".format("clear_inject_media_error"))

    def delete_pmem_device(self):
        """
        Function to delete the pmem devices.

        :raise NotImplementedError
        """
        raise NotImplementedError
