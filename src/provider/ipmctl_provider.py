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

from importlib import import_module

from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.memory.lib.memory_common_lib import MemoryCommonLib
from src.provider.base_provider import BaseProvider
from abc import ABCMeta, abstractmethod
from six import add_metaclass

from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib.dtaf_content_constants import ExecutionEnv


@add_metaclass(ABCMeta)
class IpmctlProvider(BaseProvider):

    def __init__(self, log, os_obj, uefi_util_obj=None, cfg_opts=None):
        """
        Create a new IpmctlProvider object.

        :param log: Logger object to use for output messages
        :param os_obj: OS object
        :param uefi_util_obj: uefi object
        """
        super(IpmctlProvider, self).__init__(log, None, os_obj)
        self._log = log
        self._os = os_obj
        self.uefi_util_obj = uefi_util_obj
        self._sut_os = self._os.os_type
        self._cfg_opts = cfg_opts
        #  common_content_obj and config object
        self.common_content_lib_obj = CommonContentLib(self._log, self._os, cfg_opts)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._memory_common_lib = MemoryCommonLib(self._log, self._cfg_opts, self._os)
        self.command_timeout = self._common_content_configuration.get_command_timeout()
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()

    @staticmethod
    def factory(log, os_obj, cfg_opts=None, execution_env=None, uefi_obj=None):
        """
        To create a factory object.
        :param log: Logger object to use for output messages
        :param os_obj: OS object
        :param cfg_opts: config object
        :param uefi_obj: uefi object
        :param execution_env: Execution environment details(OS or uefi)
        :return: object
        """
        package = r"src.provider.internal"

        if execution_env and execution_env not in {ExecutionEnv.OS, ExecutionEnv.UEFI}:
            raise ValueError("Invalid value has been provided for "
                             "argument 'execution_env'. it should be 'os' or 'uefi'")
        elif execution_env == ExecutionEnv.UEFI:
            pass  # Do nothing when env is UEFI
        else:
            execution_env = ExecutionEnv.OS  # default to OS

        #   Getting the required module name
        if execution_env == ExecutionEnv.UEFI:
            if uefi_obj is None:
                raise ValueError('uefi util object can not be empty')

            module_name = "IpmctlProviderUefi"
        else:
            if ExecutionEnv.OS == execution_env:
                execution_env = os_obj.os_type.lower()
            if OperatingSystems.WINDOWS == os_obj.os_type:
                module_name = "IpmctlProviderWindows"
            elif OperatingSystems.LINUX == os_obj.os_type:
                module_name = "IpmctlProviderLinux"
            else:
                raise NotImplementedError("IPMCTL provider is not implemented for "
                                          "specified OS '{}'".format(os_obj.os_type))

        import src.provider.internal as ipmctl_os_provider
        get_module = import_module("{}.{}".format(ipmctl_os_provider.__name__, "ipmctl_{}_provider"
                                                  .format(execution_env)))
        aclass = getattr(get_module, module_name)
        return aclass(log=log, os_obj=os_obj, uefi_util_obj=uefi_obj, cfg_opts=cfg_opts)

    @abstractmethod
    def verify_dimms_firmware_version(self):
        """
        This method is used to verify the show topology firmware output with pmem device output.

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def verify_dimms_device_locator(self):
        """
        This method is used to verify the show topology device locator output with pmem device output.

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def show_sensors(self):
        """
        Function to get the DIMM sensor information.

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def verify_all_dcpmm_dimm_healthy(self):
        """
        This Method is Used to verify all the DCPMM dimms are Healthy Dimm's.

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def dcpmm_get_disk_namespace(self):
        """
        Function to get the DCPMM disk namespaces information.

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def dcpmm_check_disk_namespace_initilize(self, namespace_info):
        """
        Function to check if there are existing namespaces present, execute the following command to initialize the
        DIMMs and remove all existing namespaces.

        :param namespace_info: namespace.
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_list_of_dimms_which_are_healthy(self):
        """
        This Method is Used to Fetch List of All the Healthy Dimm's.

        :return: None
        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_memory_dimm_information(self):
        """
        This Function populated memory dimm information by running below ipmctl commands on SUT
        - ipmctl show -topology
        - ipmctl show -dimm
        Finally it will create object of class MemoryDimmInfo.

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_dcpmm_disk_list(self):
        """
        Function to get the DCPMM disk list that needs to be partitioned.

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_supported_modes(self):
        """
        Function to get the DCPMM dimm topology.

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def dcpmm_get_pmem_unused_region(self):
        """
        The unused space now matches the installed persistent memory capacity

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def dcpmm_configuration(self, cmd=None, cmd_str=None):
        """
        Function to configure DCPMM dimms with appropriate volatile memory and persistent memory.
        Also, to fetch the memory allocation goal and its resources.

        :raise NotImplementedError
        """
        raise NotImplementedError

    def show_goal(self):
        """
         Function to execute the show goal command in uefi

         :param: None
         :return: None
         """
        raise NotImplementedError

    @abstractmethod
    def show_mem_resources(self):
        """
        Function to configure DCPMM devices are normal and the DCPMM mapped memory configuration
        matches the applied goal.

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def dcpmm_get_pmem_device_fl_info(self):
        """
        Function to list the persistent memory regions.

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def dcpmm_new_pmem_disk(self, region_data_list, mode=None):
        """
        Function to configure all available pmem devices with namespaces.

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def create_config_csv(self):
        """
        Store the currently configured memory allocation settings for all DCPMMs in the system to a file

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_system_capability(self):
        """
        Function to configure all available pmem devices with namespaces.

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def show_dimm_status(self):
        """
        Function to get the dimm status of by using IPMCTL tool

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_dimm_info(self):
        """
        Function to run dimm info via uefi shell

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def dcpmm_get_app_direct_mode_settings(self):
        """
        Function to run app  direct support command  via uefi shell

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def show_topology(self):
        """
        Function to run the DCPMM topology command via uefi shell

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def dimm_diagnostic(self):
        """
        Function to Execute the default set of all diagnostics on installed DCPMMs via uefi shell

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def dimm_diagnostic_quick_check(self):
        """
        Function to run quick check diagnostic on all installed DCPMMs via uefi shell

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def dimm_diagnostic_check(self, dimm_id):
        """
        Function to execute the quick check diagnostic on a single DCPMM  via uefi shell

        :param: dimm_id
        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_dimm_id(self):
        """
        Function to get dimm ids  via uefi shell

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def dimm_diagnostic_help(self):
        """
        Function to run diagnostic help command via uefi shell

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def dimm_diagnostic_security(self):
        """
        Function to run diagnostic security command via uefi shell

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def show_firmware(self):
        """
        Function to run the DCPMM topology command via uefi shell

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def dimm_version(self):
        """
        Function to run ipmctl version via uefi shell

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def show_all_region_data(self):
        """
         Function to show  all the regions on uefi shell after goal creation

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def region_data_after_goal(self, index):
        """
         Function to create all the regions after goal creation

        :param index: index
        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def dimm_diagnostic_config_check(self):
        """
        Function to run quick check diagnostic on all installed DCPMMs via uefi shell

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def system_nfit(self):
        """
        Function to run NFIT commands to show that the system via uefi shell

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def system_pmtt(self):
        """
        Function to run PMTT commands to show that the system via uefi shell

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def check_thermal_error(self):
        """
        Function to run thermal command in uefi shell

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def check_media_error(self):
        """
        Function to run media command in uefi shell

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_boot_status_register(self):
        """
        Function to run boot status register command in uefi shell

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_system_pcat(self):
        """
        Function to run NFIT commands to show that the system via uefi shell

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def delete_pcd_data(self):
        """
        This function is used to delete the PCD data.

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def umount_existing_devices(self):
        """
        This function is used to un mount the pmem devices.

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_existing_mount_points_fstab(self):
        """
        This function is used to get the mount points from the /etc/fstab file

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def remove_fstab_data(self):
        """
        This function is used to remove PMEM data in the /etc/fstab file.

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def show_dimm_thermal_error(self):
        """
        Function to get the dimm thermal errors using IPMCTL tool

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def show_dimm_media_error(self):
        """
        Function to get the dimm thermal errors using IPMCTL tool

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def verify_mem_resource_provisioned_capacity(self, mem_resource_op):
        """
        Function to verify_mem_resource_provisioned_capacity

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_list_of_dimms_which_are_healthy_and_manageable(self):
        """
        This Method is Used to Fetch List of All the Healthy and Manageable Dimm's and raise the RunTimeError if
        there are no Healthy and Manageable Dimms.

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_error_logs(self, *err_type):
        """
        Function to get the error logs for media and thermal using ipmctl commands.

        :param err_type: will hold the error types.
        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def verify_media_thermal_error(self, err_type, log_path):
        """
        Function to check whether we find any Media or Thermal error on the dimms

        :param err_type: will hold the error type.
        :param log_path: log file path
        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def dump_provisioning_data(self, config_file_name):
        """
        Function to Store the currently configured memory allocation settings for all DCPMMs in the system to a file.

        :param config_file_name: file name in which current provisioning configuration will save
        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def restore_memory_allocation_settings(self, config_file_name):
        """
        Function to Restore the previous configured memory allocation settings from stored config file.

        :param config_file_name: file name from which provisioning configuration data will load
        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_pmem_device(self):
        """
        This is function is used to get the persistent memory device information

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_pcd_config(self):
        """
        Function to run the platform configuration data for each DCPMM.

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def list_dcpmm_existing_error_logs(self):
        """
        This Method is Used to List the Existing DCPMM Error Logs.

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def clear_fatal_media_error(self):
        """
        This Method clears Injected Fatal Media Error to DCPMM media.

        :return:
        :raise: RuntimeError if injection fails.
        """
        raise NotImplementedError

    @abstractmethod
    def get_viral_status_of_dcpmm_dimms(self):
        """
        This Method provides viral status and viral Policy of DCPMM DIMMS.

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def inject_fatal_media_error(self):
        """
        This Method provides viral status and viral Policy of DCPMM DIMMS.

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
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
        Function to show all the regions on uefi shell after goal creation.

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def get_disk_namespace_info(self):
        """
        Function to get the DCPMM disk namespaces information.

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def show_dimm_pcd(self):
        """
        Function to show the pcd data.

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def show_system(self):
        """
        Function to show the system data.

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def show_dimm_performance(self):
        """
        Function to show the dimm performance.

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def show_ars_status(self):
        """
        Function to show the ARSStatus

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def show_socket(self):
        """
        Function to show the socket info

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def show_preferences(self):
        """
        Function to show the preferences info

        :raise: NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def dimm_diagnostic_firmware(self):
        """
        Function to run firmware check diagnostic on all installed DCPMMs

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def verify_lm_provisioning_configuration(self, dcpmm_disk_goal, mode):
        """
        Function to verify provisioning configuration.
        """
        raise NotImplementedError

    @abstractmethod
    def verify_pmem_device_presence_cap(self, namespace_info, appdirect_percent=None):
        """
        Function to get the the list of pmem devices and verify if the desired devices are present on SUT

        :raise NotImplementedError
        """
        raise NotImplementedError

    @abstractmethod
    def delete_pmem_device(self):
        """
        Function to delete the pmem devices.

        :raise NotImplementedError
        """
        raise NotImplementedError
