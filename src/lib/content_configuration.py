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
import platform
import re
import six

if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path

from xml.etree import ElementTree

from dtaf_core.lib.dtaf_constants import Framework, ProductFamilies
from src.lib.dtaf_content_constants import PcieSlotAttribute
from src.lib import content_exceptions
from src.lib.dtaf_content_constants import PcieSlotAttribute, RasIoConstant, PassThroughAttribute, TimeConstants


class ContentConfiguration(object):
    """
    To fetch the domain based configurations accordingly to the test case from the xml file to be used on
    across memory, RAS and Security domains.
    """

    def __init__(self, log):
        self._log = log
        self.platform_path_pcie = "./pcie/cards/card/Type/"
        self.dmi_path_pcie = "./pcie/cards/card/"

    def config_file_path(self, attrib, domain=None):
        """
        Function to fetch the attribute values from the xml configuration file for the domain / common configs.
        :param attrib: name of the attribute, should be unique.
        :param domain: name of the domain that configuration needs to be picked up from C:\Automation folder or from
        Framework.
        :return: Value of the attribute in string type.
        """
        domain_config_name = config_end_string_check = "content_configuration.xml"
        if domain is not None:
            domain_config_name = "content_configuration_{}.xml".format(domain)
            config_end_string_check = "{}.xml".format(domain)

        exec_os = platform.system()
        try:
            cfg_file_default = Framework.CFG_BASE
        except KeyError:
            err_log = "Error - execution OS " + str(exec_os) + " not supported!"
            self._log.error(err_log)
            raise err_log

        # Get the Automation folder config file path based on OS.
        cfg_file_automation_path = cfg_file_default[exec_os] + domain_config_name

        config_file_src_path = None
        tree = ElementTree.ElementTree()
        config_file_path = Path(os.path.dirname(os.path.realpath(__file__))).parent
        for root, dirs, files in os.walk(str(config_file_path)):
            for name in files:
                if name.startswith(domain_config_name.split(".")[0]) and name.endswith(config_end_string_check):
                    config_file_src_path = os.path.join(root, name)

        if domain is not None:
            err_log = "Domain configuration file does not exists under C:/Automation directory or inside of " \
                      "framework, please check.."
            config_found = "Domain configuration exists under '{}'.. proceeding further to check attrib-{}.."
        else:
            err_log = "Content configuration file does not exists under C:/Automation directory or inside of " \
                      "framework, please check.."
            config_found = "Content configuration exists under '{}'.. proceeding further to check attrib-{}.."

        # First check whether the config file exists in C:\Automation folder else it goes to src configuration.
        if cfg_file_automation_path is None and config_file_src_path is None:
            self._log.error(err_log)
            raise IOError(err_log)
        elif os.path.isfile(cfg_file_automation_path):
            self._log.info(config_found.format(cfg_file_automation_path, attrib))
            tree.parse(cfg_file_automation_path)
        elif config_file_src_path is None:
            self._log.error(err_log)
            raise IOError(err_log)
        elif os.path.isfile(config_file_src_path):
            self._log.info(config_found.format(config_file_src_path, attrib))
            tree.parse(config_file_src_path)

        root = tree.getroot()
        return root.find(r".//{}".format(attrib)).text.strip()

    def get_profile0_params(self):
        """
        Function to get the ifwi boot profile info 0 from the content configuration xml file.
        """
        profile_dict = {}
        content_config = self.get_content_config()
        for node in content_config.findall(r".//profile0/"):
            for subnode in node.iter():
                profile_dict[subnode.tag] = subnode.text.strip()
        return profile_dict

    def get_profile4_params(self):
        """
        Function to get the ifwi boot profile info 4 from the content configuration xml file.
        """
        profile_dict = {}
        content_config = self.get_content_config()
        for node in content_config.findall(r".//profile4/"):
            for subnode in node.iter():
                profile_dict[subnode.tag] = subnode.text.strip()
        return profile_dict

    def get_profile5_params(self):
        """
        Function to get the ifwi boot profile info 5 from the content configuration xml file.
        """
        profile_dict = {}
        content_config = self.get_content_config()
        for node in content_config.findall(r".//profile5/"):
            for subnode in node.iter():
                profile_dict[subnode.tag] = subnode.text.strip()
        return profile_dict

    def get_xmlcli_tools_name(self):
        """
        Function to get the xmlcli tool name.
        """
        return str(self.config_file_path(attrib="tools/xmlcli_tool_name"))

    def get_profile3_params(self):
        """
        Function to get the ifwi boot profile info 3 from the content configuration xml file.
        """
        profile_dict = {}
        content_config = self.get_content_config()
        for node in content_config.findall(r".//profile3/"):
            for subnode in node.iter():
                profile_dict[subnode.tag] = subnode.text.strip()
        return profile_dict

    def get_ifwi_build_xml_modifier(self):
        """
        Function to get the ifwi build xml modifier from the content configuration xml file.
        """
        profile_xml_dict = {}
        content_config = self.get_content_config()
        for node in content_config.findall(r".//build_xml_modifier/"):
            for subnode in node.iter():
                profile_xml_dict[subnode.tag] = subnode.text.strip()
        return profile_xml_dict

    def get_spsfit_params(self):
        """
        Function to get the fit tool path and name from the content configuration xml file.
        """
        fit_tool_path = str(self.config_file_path(attrib="fit_tool/path"))
        fit_tool_name = str(self.config_file_path(attrib="fit_tool/name"))
        return fit_tool_path, fit_tool_name

    def get_cxl_stress_execution_runtime(self, tool="ctg"):
        """
        This Function is to get the time for executing the CXL stress.
        """
        try:
            ret_val = int(self.config_file_path(attrib="pcie/cxl/{}/stress_execution_timeout_in_sec".format(tool)))
        except AttributeError:
            ret_val = TimeConstants.TWO_HOUR_IN_SEC
        return ret_val

    def get_user_inputs_for_cxl_flag(self):
        """
        This method is to get the Flag to identify whether to take user inputs or whole cxl device inventory available.
        True - cxl config inputs from auto inventory
        False - Cxl config inputs from the user
        """
        try:
            return eval(self.config_file_path(attrib="pcie/cxl/cxl_auto_discovery"))
        except Exception as ex:
            return ""

    def get_user_inputs_for_pcie_flags(self):
        """
        This method is to get the Flag to identify whether to take user inputs or whole PCIe device inventory available.
        True - PCIe config inputs from auto inventory
        False - PCIe config inputs from the user
        """
        try:
            return eval(self.config_file_path(attrib="pcie/pcie_auto_inventory"))
        except Exception as ex:
            return ""

    def get_cxl_dax_device(self):
        """
        This Function is to get the cxl dax device id.
        """
        try:
            ret_val = self.config_file_path(attrib="pcie/cxl/cxl_cards_dax_mapping/dax_device").split(",")
        except AttributeError:
            self._log.error("Dax data not present in the xml file")
            ret_val = []
        return ret_val

    def get_socket_for_cxl_dax_device(self):
        """
        This Function is to get the cxl dax device id.
        """
        try:
            ret_val = self.config_file_path(attrib="pcie/cxl/cxl_cards_dax_mapping/sockets").split(",")
        except AttributeError:
            self._log.error("Dax data not present in the xml file")
            ret_val = []
        return ret_val

    def get_port_for_cxl_dax_device(self):
        """
        This Function is to get the cxl dax device id.
        """
        try:
            ret_val = self.config_file_path(attrib="pcie/cxl/cxl_cards_dax_mapping/ports").split(",")
        except AttributeError:
            self._log.error("Dax data not present in the xml file")
            ret_val = []
        return ret_val

    def get_cxl_write_bw_value(self):
        """
        This Function is to get the cxl_write_bw_value.
        """
        try:
            ret_val = int(self.config_file_path(attrib="pcie/cxl/cxl_write_bw_value"))
        except AttributeError:
            self._log.error("cxl_write_bw data not present in the xml file")
            ret_val = ""
        return ret_val

    def get_cxl_read_bw_value(self):
        """
        This Function is to get the cxl_read_bw_value.
        """
        try:
            ret_val = int(self.config_file_path(attrib="pcie/cxl/cxl_read_bw_value"))
        except AttributeError:
            self._log.error("cxl_read_bw data not present in the xml file")
            ret_val = ""
        return ret_val

    def get_cxl_ctg_socket_list(self):
        """
        This method is to get the socket.
        """
        try:
            ret_val = self.config_file_path(attrib="pcie/cxl/ctg/sockets").split(',')
        except AttributeError:
            ret_val = []
        return ret_val

    def get_num_of_cxl_cycling(self):
        """
        This method is to get the number of Cycle.
        """
        try:
            ret_val = int(self.config_file_path(attrib="pcie/cxl/num_of_cycle"))
        except AttributeError:
            self._log.error("<num_of_cycle> -- tag was not correctly configured. So proceeding the Test with "
                            "default - 150 cycle")
            ret_val = 150
        return ret_val

    def get_sut_wakeup_time_in_sec(self):
        """
        This method is to get the wakeup time in sec.
        """
        try:
            ret_val = int(self.config_file_path(attrib="sut_wake_up_time_in_sec"))
        except AttributeError:
            self._log.error("<sut_wake_up_time_in_sec> -- tag was not configured correctly. So, proceeding with"
                            " default - 180 sec")
            ret_val = 180
        return ret_val

    def get_cxl_cache_dimm_list_to_target(self, tool="ctg", socket=0):
        """
        This Function is to get the Cache dimm in list to target for the stress.
        """
        return str(self.config_file_path(attrib="pcie/cxl/{}/targeted_dimms/socket_{}".format(tool, socket))).split(',')

    def get_cxl_target_peer_point_device_list(self, tool="ctg"):
        """
        This method is to get the Peer to Peer device name.
        """
        return str(self.config_file_path(attrib="pcie/cxl/{}/targeted_peer_point".format(tool))).split(',')

    def get_cxl_target_bus_list(self, tool="ctg"):
        """
        This method is to get the bus in list
        """
        return str(self.config_file_path(attrib="pcie/cxl/{}/targeted_bus".format(tool))).split(',')

    def get_cxl_cache_en_list(self):
        """
        This method is to get the CXL Cache enable list
        """
        return str(self.config_file_path(attrib="pcie/cxl/cxl_slots/cxl_cache_en")).split(',')

    def get_cxl_mem_en_list(self):
        """
        This method is to get the CXL Mem enable list
        """
        return str(self.config_file_path(attrib="pcie/cxl/cxl_slots/cxl_mem_en")).split(',')

    def get_cxl_io_en_list(self):
        """
        This method is to get the CXL IO enable list
        """
        return str(self.config_file_path(attrib="pcie/cxl/cxl_slots/cxl_io_en")).split(',')

    def get_ifwi_override(self):
        """
        Function to get the ifwi override file name from the content configuration xml file.
        """
        try:
            ifwi_override = str(self.config_file_path(attrib="ifwi_override"))
            return ifwi_override
        except:
            raise content_exceptions.TestFail("Please check Content Configuration details for tag name- {}".format(
                "ifwi_override"))

    def get_ifwi_params(self):
        """
        Function to get the Ifwi path and name from the content configuration xml file.
        """
        ifwi_file_path = str(self.config_file_path(attrib="ifwi_file/path"))
        ifwi_file_name = str(self.config_file_path(attrib="ifwi_file/name"))
        return ifwi_file_path, ifwi_file_name

    def get_ini_params(self):
        """
        Function to get the ini path and name from the content configuration xml file.
        """
        ini_file_path = str(self.config_file_path(attrib="ini_file/ini_path"))
        ini_file_name = str(self.config_file_path(attrib="ini_file/ini_name"))
        return os.path.join(ini_file_path, ini_file_name)

    def get_ucode_file(self):
        """This function is to get the microcode file from xml config file
        """
        ucode_path = str(self.config_file_path(attrib="ucode/ucode_path")).strip()
        ucode_name = str(self.config_file_path(attrib="ucode/ucode_name")).strip()
        ucode_cpuid_list = self.config_file_path(attrib="ucode/ucode_cpuid").split(",")
        return os.path.join(ucode_path, ucode_name), ucode_cpuid_list

    def get_cxl_sockets(self):
        """
        This method is to get the cxl sockets.
        """
        return self.config_file_path(attrib="pcie/cxl/cxl_slots/sockets").split(',')

    def get_cxl_ports(self):
        """
        This method is to get the cxl ports.
        """
        return self.config_file_path(attrib="pcie/cxl/cxl_slots/ports").split(',')

    def get_pxp_port_list(self):
        """
        This method is to get the pcie slot register from config.

        :return: List
        """
        try:
            ret_val = self.config_file_path(attrib="pcie/pxp_port_list").split(',')
        except:
            self._log.error("Error: Please check the tag - <pxp_port_list> in content config")
            ret_val = []
        return ret_val

    def get_cxl_current_link_speed(self):
        """
        This method is to get the cxl device current link speed.
        """
        return self.config_file_path(attrib="pcie/cxl/cxl_slots/current_link_speed").split(',')

    def get_cxl_version(self):
        """
        This method is to get the cxl version
        """
        return self.config_file_path(attrib="pcie/cxl/cxl_slots/version").split(',')

    def get_cxl_link_width(self):
        """
        This method is to get the Cxl Link Width
        """
        return self.config_file_path(attrib="pcie/cxl/cxl_slots/link_width").split(',')

    def get_cxl_device_type(self):
        """
        This method is to get the cxl device type.
        """
        return self.config_file_path(attrib="pcie/cxl/cxl_slots/device_type").split(',')

    def get_ifwi_container_params(self):
        """
        Function to get the profile container information from the content configuration xml file.
        """

        container_path = str(self.config_file_path(attrib="ifwi_file/path"))
        container_build_xml = str(self.config_file_path(attrib="container/build_xml"))
        container_build_file = str(self.config_file_path(attrib="container/build_file"))
        return container_path, container_build_xml, container_build_file

    def get_content_config(self):
        """
        This function to get the content configuration xml file path and return content configuration xml file root.
        :return: return configuration xml file root .
        """
        exec_os = platform.system()
        try:
            cfg_file_default = Framework.CFG_BASE
        except KeyError:
            err_log = "Error - execution OS " + str(exec_os) + " not supported!"
            self._log.error(err_log)
            raise err_log

        # Get the Automation folder config file path based on OS.
        cfg_file_automation_path = cfg_file_default[exec_os] + "content_configuration.xml"

        config_file_src_path = None
        tree = ElementTree.ElementTree()
        config_file_path = Path(os.path.dirname(os.path.realpath(__file__))).parent
        for root, dirs, files in os.walk(str(config_file_path)):
            for name in files:
                if name.startswith("content_configuration") and name.endswith(".xml"):
                    config_file_src_path = os.path.join(root, name)

        # First check whether the config file exists in C:\Automation folder else it goes to src configuration.

        if os.path.isfile(cfg_file_automation_path):
            tree.parse(cfg_file_automation_path)
        elif os.path.isfile(config_file_src_path):
            tree.parse(config_file_src_path)
        else:
            err_log = "Configuration file does not exists, please check.."
            self._log.error(err_log)
            raise IOError(err_log)

        root = tree.getroot()
        return root

    def get_dsa_device_count(self):
        """
        Function to get the num dsa devices to verify
        """
        return int(self.config_file_path(attrib="accelerator/dsa_device_count"))

    def get_reboot_timeout(self):
        """
        Function to get the timeout value for rebooting from the xml config file.
        """
        return int(self.config_file_path(attrib="reboot_time"))

    def get_itp_reset_timeout(self):
        """
        Function to get the timeout value for reset time from the xml config file.
        """
        return int(self.config_file_path(attrib="itp_reset_time_out"))

    def get_bring_sut_up_value(self):
        """
        Function to get the bring sut up value (True/False).
        """
        return eval(self.config_file_path(attrib="bring_sut_up"))

    def get_test_prepare_disable_value(self):
        """
        Function to get the prepare section in DTAF to be disabled value (True/False).
        """
        return eval(self.config_file_path(attrib="test_prepare_disable"))

    def get_command_timeout(self):
        """
        Function to get the timeout value for command from the xml config file.
        """
        return int(self.config_file_path(attrib="sut_command_time"))

    def itp_halt_time_in_sec(self):
        """
        Function to get tje ITP Halt Time from xml config file
        """
        return int(self.config_file_path(attrib="itp_halt_time_in_sec"))

    def itp_resume_delay_in_sec(self):
        """
        Funtion to get resume delay from xml config file.
        """
        return int(self.config_file_path(attrib="itp_resume_delay_time_in_sec"))

    def memory_number_of_cycle(self):
        """
        Function to get the number of cycles to be executed from xml config file.
        """
        return int(self.config_file_path(attrib="number_cycles"))

    def memory_next_reboot_wait_time(self):
        """
        Function to get the next reboot wait time on OS level from xml config file.
        """
        return int(self.config_file_path(attrib="next_reboot_wait_time"))

    def memory_dc_on_time(self):
        """
        Function to get the time taken to get the SUT after dc power on to OS level from xml config file.
        """
        return int(self.config_file_path(attrib="dc_on_boot_time"))

    def memory_test_execute_time(self):
        """
        Function to get the time taken to finish the stress test application from xml config file.
        """
        return int(self.config_file_path(attrib="test_execute_time"))

    def security_mprime_running_time(self):
        """
        Function to get the running time to finish the mprime application from xml config file.
        """
        return int(self.config_file_path(attrib="security/mprime/running_time"))

    def security_stressng_running_time(self):
        """
        Function to get the running time to finish the stress-ng application from xml config file.
        """
        return int(self.config_file_path(attrib="security/stressng/running_time"))

    def security_iperf_running_time(self):
        """
        Function to get the running time to finish the iperf application from xml config file.
        """
        return int(self.config_file_path(attrib="security/iperf/running_time"))

    def security_ntttcp_running_time(self):
        """
        Function to get the running time to finish the stress-ng application from xml config file.
        """
        return int(self.config_file_path(attrib="security/ntttcp/running_time"))

    def security_pmutils_running_time(self):
        """
        Function to get the running time to finish the pmutil application from xml config file.
        """
        return self.config_file_path(attrib="security/power_management/pmutils_timeout")

    def memory_stress_test_execute_time(self):
        """
        Function to get the running time to finish the stress app test from xml config file.
        """
        return int(self.config_file_path(attrib="stress_test_execute_time"))

    def memory_fio_run_time(self):
        """
        Function to get the running time to finish the FIO app test from xml config file.
        """
        return int(self.config_file_path(attrib="fio_runtime"))

    def bios_boot_menu_entry_wait_time(self):
        """
        Function to get bios boot menu to select the bios option from xml config file.
        """
        return int(self.config_file_path(attrib="bios_boot_menu_entry_wait_time_in_sec"))

    def bios_boot_menu_select_time_in_sec(self):
        """
        Function to select the bios option from the bios boot menu from xml config  file
        """
        return int(self.config_file_path(attrib="bios_boot_menu_select_time_in_sec"))

    def uefi_command_timeout(self):
        """
        Function to get uefi commond timeout value from xml config file
        """
        return int(self.config_file_path(attrib="execute_uefi_cmd_timeout_in_sec"))

    def sut_shutdown_delay(self):
        """
        Function to get SUT shutdown delay timeout from xml config file
        """
        return int(self.config_file_path(attrib="sut_shutdown_delay"))

    def get_pretest_bios_knobs_file_path(self):
        """
        Function to get BIOS knob path for setting pretest knobs before normal test execution
        """

        try:
            return self.config_file_path(attrib="pretest_bios_knobs_file_path")
        except Exception as ex:
            return ""

    def get_uefi_select_key(self):
        """
        Function to get UEFI Internal Shell from xml config file
        """
        return str(self.config_file_path(attrib="UEFI_SELECT_KEY"))

    def os_full_ac_cycle_time_out(self):
        """
        Function to get full ac power cycle timeout to come in OS from xml config file.
        """
        return int(self.config_file_path(attrib="full_ac_cycle_time_out"))

    def get_vm_vhdx_drive_name(self, os_type="Linux"):
        """
        This method is to get the drive name in which VM need to create.
        :param os_type - Linux, Windows_19, Windows_16
        """
        if os_type == "Linux":
            return str(self.config_file_path(attrib="io_virtualization/linux_vhdx_drive_name"))
        elif os_type == "Windows_19":
            return str(self.config_file_path(attrib="io_virtualization/windows_2019_vhdx_drive_name"))
        elif os_type == "Windows_16":
            return str(self.config_file_path(attrib="io_virtualization/windows_2016_vhdx_drive_name"))
        else:
            raise content_exceptions.TestFail("Please check config details")

    def get_ethernet_adapter_for_vm(self):
        """
        This method is used to get the ethernet adapter for VM.
        """
        return self.config_file_path(attrib="io_virtualization/ethernet_adapter_for_vm")

    def get_default_sut_network_adpter_name(self):
        """
        This method is to get the ethernet
        """
        return self.config_file_path(attrib="io_virtualization/platform_default_network_adapter_name")

    def get_vm_2019_static_ip(self):
        """
        This method is used to return the static ip for 2019 win VM.
        """
        return self.config_file_path(attrib="io_virtualization/win_2019_vm_static_ip")

    def get_vm_2016_static_ip(self):
        """
        This method is used to return the static ip for 2016 win VM.
        """
        return self.config_file_path(attrib="io_virtualization/win_2016_vm_static_ip")

    def get_stress_execution_time_for_vm(self):
        """
        This method is to get the time for which stress need to execute.
        """
        return int(self.config_file_path(attrib="io_virtualization/vm_stress_time_in_sec"))

    def memory_mlc_run_time(self):
        """
        Function to get the running time to finish the MLC app test from xml config file.
        """
        return int(self.config_file_path(attrib="mlc_runtime"))

    def memory_mlc_idle_lateny_threshold(self):
        """
        Function to get the idle_latency_threshold value from xml config file.
        """
        return int(self.config_file_path(attrib="idle_latency_threshold"))

    def memory_mlc_peak_memory_bandwidth_threshold(self):
        """
        Function to get the peak_memory_bandwidth value from xml config file.
        """
        return int(self.config_file_path(attrib="peak_memory_bandwidth"))

    def memory_mlc_memory_bandwidth_threshold(self):
        """
        Function to get the memory_bandwidth threshold value from xml config file.
        """
        return int(self.config_file_path(attrib="memory_bandwidth"))

    def get_msr_timeout(self):
        """
        Function to get sleep time value for msr values.
        """
        return int(self.config_file_path(attrib="time_sleep_msr"))

    def get_disk_spd_command_time_out(self):
        """
        Function to get diskspd command timeout from xml config file.
        """
        return int(self.config_file_path(attrib="disk_spd_run_time"))

    def frequencies_supported(self):
        """
        Function to get the frequencies from xml config file.
        """
        frequencies = self.config_file_path(attrib="frequency_list")
        return frequencies.split(',')

    def get_uefi_exec_delay_time(self):
        """
        Function to put a delay before running the command in uefi shell
        """
        return int(self.config_file_path(attrib="uefi_exec_delay"))

    def get_production_silicon(self):
        """
        Function to get the silicon used.
        """
        return int(self.config_file_path(attrib="production_silicon"))

    def einj_mem_default_address(self):
        """
        This Function is used to fetch default Memory Address while Injecting Memory Errors
        """
        return int(self.config_file_path(attrib="einj_mem_addr"), 16)

    def einj_pcie_default_address(self):
        """
        This Function is used to fetch default Pcie Address while Injecting Pcie Errors
        """
        return int(self.config_file_path(attrib="einj_pcie_addr"), 16)

    def get_device_id_list(self):
        """
        This method is to get the device id from config.
        """
        return str(self.config_file_path(attrib="pcie/device_ids")).split(',')

    def ac_timeout_delay_in_sec(self):
        """
        Function to get ac_timeout_delay for AC Cycle
        """
        return int(self.config_file_path(attrib="ac_timeout_delay_in_sec"))

    def waiting_time_after_injecting_uncorr_error(self):
        """
        Function to get waiting_time_after_injecting_uncorr_error
        """
        return int(self.config_file_path(attrib="waiting_time_after_injecting_uncorr_error"))

    def dmi_link_down_delay(self):
        """
        Function to get DMI Link Down Delay
        """
        return int(self.config_file_path(attrib="dmi_link_down"))

    def wait_for_pcie_cto_timeout_reconfig(self):
        """
        Function to get wait time for PCIE CTO Timeout after Reconfig
        :return:
        """
        return int(self.config_file_path(attrib="pcie_cto_timeout_reconfig"))

    def stream_mp_run_time(self):
        """
        Function to get the running time to finish the Stream MP from xml config file.
        """
        return int(self.config_file_path(attrib="stream_run_time"))

    def stream_mp_threshold_value(self):
        """
        Function to get the threshold pass value for Stream MP from xml config file.
        """
        return int(self.config_file_path(attrib="rate_threshold_value"))

    def memory_ilvss_run_time(self):
        """
        Function to get the run time of ilvss tool on the sut from xml config file.
        """
        return int(self.config_file_path(attrib="ilvss_run_time"))

    def dc_power_sleep_time(self):
        """
        Function to wait before DC power on the sut from xml config file.
        """
        return int(self.config_file_path(attrib="dc_delay_in_sec"))

    def default_mask_value(self):
        """
        Function to Extract Default Mask Value for Injecting the Error
        """
        return int(self.config_file_path(attrib="mask_value"), 16)

    def memory_stream_run_time(self):
        """
        Function to get the running time to finish the stream app test from xml config file.
        """
        return int(self.config_file_path(attrib="stream_runtime"))

    def memory_stream_threshold_value(self):
        """
        Function to get the stream_threshold value from xml config file.
        """
        return int(self.config_file_path(attrib="stream_threshold_value"))

    def ac_power_off_wait_time(self):
        """
        Function to get the AC power off wait time from xml config file.
        """
        return int(self.config_file_path(attrib="ac_power_off_wait_time_in_sec"))

    def memory_ilvss_script_sleep_time(self):
        """
        Function to get the sleep time in percentage of SUT after ilvss tool started its execution on the sut from xml
        config file.
        """
        return float(self.config_file_path(attrib="script_sleep_time_percent"))

    def get_pcie_dmi_data(self, cpu_family):
        """
        Function to fetch the attribute values of pcie from the xml configuration file.
        :param cpu_family: cpu family name
        :return: dictionary of Values of the attributes in string type.
        """
        pcie_dmi_dict = {}
        tags = self.get_content_config()
        var = tags.find(r"./pcie/dmi")
        for node in var:
            for sub_node in node.iter():
                pcie_dmi_dict[sub_node.tag] = sub_node.text.strip()

        return pcie_dmi_dict

    def get_sata_storage_device(self):
        """
        Function to fetch the attribute values of sata storage device from the xml configuration file.
        :return: List of the storage device name
        """
        sata_device_name_list = []
        tags = self.get_content_config()
        var = tags.find(r".//sata_drive_name")
        for node in var:
            for sub_node in node.iter():
                sata_device_name_list.append(sub_node.text.strip())
        return sata_device_name_list

    def get_pcie_slot_to_check(self):
        """
        This method is to get the PCIe Slot.
        :return List
        """
        tag_info = str(self.config_file_path(attrib="pcie/select_slot"))
        return tag_info.split(",")

    def get_pcie_slot_mcio_check(self, product_family):
        """
        This method is to get the required device details from config.
        :param product_family
        :return list
        """
        required_pcie_device_list = []
        tag_info = str(self.config_file_path(attrib="pcie/select_slot"))
        mcio_slot_list = tag_info.split(",")
        tag = self.get_content_config()
        if product_family in ["SPR", "EMR"]:
            all_mcio = PcieSlotAttribute.ALL_MCIO_SLOT
        else:
            raise content_exceptions.TestFail("Still Not Implemented for - {}".format(product_family))
        for each_mcio_slot in mcio_slot_list:
            if each_mcio_slot not in all_mcio:
                self._log.error("Received empty required_pcie_u_2_slot_list")
                raise content_exceptions.TestFail("Please Add tag for required Pcie U.2 Slot")
            mcio_pcie_details_dict = {}
            mcio_pcie_details_dict[PcieSlotAttribute.SLOT_NAME] = each_mcio_slot
            var = tag.find(r".//pcie_device_population/{}".format(each_mcio_slot))
            for node in var.iter():
                if not node.tag == each_mcio_slot:
                    mcio_pcie_details_dict[node.tag] = node.text.strip()
            required_pcie_device_list.append(mcio_pcie_details_dict)
        self._log.debug("PCIe Slot list from config file: {}".format(required_pcie_device_list))

        return required_pcie_device_list

    def get_bifurcation_pcie_slot_to_check(self):
        """
        This method is to get the Bifurcation PCIe Slot.
        :return List
        """
        tag_info = str(self.config_file_path(attrib="pcie/bifurcation_select_slot"))
        return tag_info.split(",")

    def get_required_pcie_device_details(self, product_family, required_slot_list=None):
        """
        This method is to get the required device details from config.
        :param required_slot_list
        :param product_family
        :return list
        """
        try:
            required_pcie_device_list = []
            tags = self.get_content_config()
            if not required_slot_list:
                self._log.error("Received empty required_slot_list")
                raise content_exceptions.TestFail("Please Add tag for required Slot")
            if "All_Slot" in required_slot_list:
                if product_family in ["SPR", "EMR"]:
                    required_slot_list = PcieSlotAttribute.PCIE_ALL_SLOT
                else:
                    raise content_exceptions.TestFail("Still Not Implemented for Product Family- {}".format(
                        product_family))
            for each_slot in required_slot_list:
                each_slot_dict = {}
                each_slot_dict[PcieSlotAttribute.SLOT_NAME] = each_slot
                var = tags.find(r".//pcie_device_population/{}".format(each_slot))
                for node in var.iter():
                    if not node.tag == each_slot:
                        each_slot_dict[node.tag] = node.text.strip()
                required_pcie_device_list.append(each_slot_dict)
            self._log.debug("PCIe Slot list from config file: {}".format(required_pcie_device_list))
            return required_pcie_device_list
        except:
            raise content_exceptions.TestFail("Please check content_configuaration.xml for PCIe device details")

    def get_ac_power_cfg(self):
        """
        This method is to get ac power cfg.
        :return cfg object
        """
        tag = self.get_content_config()
        var = tag.find(r"provider/ac")
        return var

    def get_keysight_card_socket(self):
        """
        This method is to get Keysight card connected socket.
        :return socket
        """
        return int(self.config_file_path(attrib="keysight_pcie_card/socket"))

    def get_keysight_card_pxp_port(self):
        """
        This method is to get Keysight card connected pxp port.
        :return pxp_port
        """
        return str(self.config_file_path(attrib="keysight_pcie_card/pxp_port"))

    def get_pcie_slot_data(self, cpu_family, slot="slot_c"):
        """
        Function to fetch the attribute values of pcie slot from the xml configuration file.
        :param slot: which slot need to check
        :param cpu_family: cpu family name
        :return: dictionary of Values of the attributes in string type.
        """
        pcie_slot_dict = {}
        tags = self.get_content_config()
        var = tags.find(r".//pcie_device_details/{}/{}".format(cpu_family, slot))
        for node in var:
            for sub_node in node.iter():
                pcie_slot_dict[sub_node.tag] = sub_node.text.strip()

        return pcie_slot_dict

    def get_pcie_cpu_root_linkcap_speed(self, cpu_family):
        """
        Function to fetch the linkcap speed from the xml configuration file.
        :param cpu_family: cpu family name
        :return: dictionary of Values of the attributes in string type.
        """

        return str(self.config_file_path(attrib="pcie/cpu_root/{}/lnkcap".format(cpu_family.upper())))

    def get_pcie_enumeration_data(self, card_type):
        """
        Function to fetch the attribute values of pcie from the xml configuration file.
        :param cpu_family: cpu family name
        :return: dictionary of Values of the attributes in string type.
        """
        pcie_cards_dict = {}
        list_of_pcie_cards_data = []
        tags = self.get_content_config()
        var = tags.findall(r".//cards/{}".format(card_type))
        for node in var:
            for sub_node in node.iter():
                pcie_cards_dict[sub_node.tag] = sub_node.text.strip()
            list_of_pcie_cards_data.append(pcie_cards_dict)
        return list_of_pcie_cards_data

    def memory_supported_highest_capacity_dimm(self, processor_name):
        """
        Function to get the capacity,speed,form factor of a dimm & particular processor from xml config file.
        """
        # Get the Automation folder config file path based on OS.
        temp_dict = {}
        tags = self.get_content_config()
        var = tags.find(r".//supported_highest_capacity_dimms/{}".format(processor_name))
        for node in var:
            for sub_node in node.iter():
                temp_dict[sub_node.tag] = sub_node.text.strip()
        return temp_dict

    def memory_bios_post_memory_capacity(self):
        """
        Function to get the bios post_memory_capacity from xml config file.
        """
        return int(self.config_file_path(attrib="bios_post_memory_capacity"))

    def memory_bios_total_dcpmm_memory_capacity(self):
        """
        Function to get the bios_total_dcpmm_memory_capacity from xml config file.
        """
        return int(self.config_file_path(attrib="bios_total_dcpmm_memory_capacity"))

    def get_num_of_ac_cycles(self):
        """
        Function to get the Number of Ac Cycles from xml config file.
        """
        return int(self.config_file_path(attrib="ac_cycles"))

    def get_num_of_g3_dpmo_cycles(self):
        """
        Function to get the Number of g3 Cycles from xml config file.
        """
        return int(self.config_file_path(attrib="power_management/dpmo/g3_cycles"))

    def get_ddr_freq_for_dpmo(self):
        """
        Function to get the frequency for DPMO.
        """
        return int(self.config_file_path(attrib="power_management/dpmo/ddr_frquency"))

    def get_num_of_s5_dpmo_cycles(self):
        """
        Function to get the Number of s5 Cycles from xml config file.
        """
        return int(self.config_file_path(attrib="power_management/dpmo/s5_cycles"))

    def get_num_of_warm_reset_dpmo_cycles(self):
        """
        Function to get the Number of warm reset Cycles from xml config file.
        """
        return int(self.config_file_path(attrib="power_management/dpmo/warm_reset_cycles"))

    def get_ignore_machine_check(self):
        """
        Function to get flag to ignore Machine Check(break point).
        :return:
        """
        return eval(self.config_file_path(attrib="power_management/dpmo/machine_check"))

    def get_ignore_mce_errors_value(self):
        """
        Function to get the ignore_mce_errors from xml config file.
        """
        return eval(self.config_file_path(attrib="power_management/dpmo/ignore_mce_errors"))

    def get_health_check_value(self):
        """
        Function to get the get_health_check_value from xml config file.
        """
        return eval(self.config_file_path(attrib="power_management/dpmo/health_check"))

    def get_stop_on_failure_value(self):
        """
        Function to get the get_health_check_value from xml config file.
        """
        try:
            stop_on_failure = self.config_file_path(attrib="stop_on_failure")
            list_stop_on_failure = [analyzer.lower().strip() for analyzer in stop_on_failure.split(",")]
            return list_stop_on_failure
        except Exception as ex:
            return []

    def get_python_sv_dump_list(self):
        """
        Function to get the pythonsv dump command in list.
        :return list
        """
        try:
            python_sv_dump_domains = self.config_file_path(attrib="pythonsv_dump")
            list_domain = [domain.lower().strip() for domain in python_sv_dump_domains.split(",")]
            return list_domain
        except Exception as ex:
            return []

    def get_memory_health_check_type_list(self):
        """
        Function to get the list of all memory health check type.
        """
        try:
            analyzers = self.config_file_path(attrib="memory_health_check_type")
            memory_health_check_list = [analyzer.lower().strip() for analyzer in analyzers.split(",")]
            return memory_health_check_list
        except Exception as ex:
            return []

    def get_dpmo_topology(self):
        """
        Function to get the topology from xml config file.
        """
        return self.config_file_path(attrib="power_management/dpmo/topology")

    def get_dpmo_link_speed(self):
        """
        Function to get the link speed from xml config file.
        """
        return self.config_file_path(attrib="power_management/dpmo/link_speed")

    def get_num_of_reboot_cycles(self):
        """
        Function to get the Number of Reboot Cycles from xml config file.
        """
        return int(self.config_file_path(attrib="reboot_cycles"))

    def get_num_of_dc_cycles(self):
        """
        Function to get the Number of Dc Cycles from xml config file.
        """
        return int(self.config_file_path(attrib="dc_cycles"))

    def get_dpdk_file(self):
        """
        Function to get the dpdk file name from xml config file.
        :return: return the dpdk file name
        """
        return self.config_file_path(attrib="tools/dpdk_file_name")

    def get_vm_dpdk_file(self):
        """
        Function to get the dpdk file name from xml config file.
        :return: return the dpdk file name
        """
        try:
            return self.config_file_path(attrib="tools/vm_dpdk_file_name")
        except Exception as ex:
            self._log.error("VM dpdk driver file name not defined in content_configuration.xml file, Test may fail!")
            return self.get_dpdk_file()

    def get_vm_dpdk_patch_file(self):
        """
        Function to get the dpdk patch file name from xml config file.
        :return: return the dpdk patch file name
        """
        try:
            return self.config_file_path(attrib="tools/vm_dpdk_patch_file_name")
        except Exception as ex:
            self._log.debug("dpdk vm patch file name is missing in config file for dpdk driver,returning "" ")
            return self.get_dpdk_patch_file()

    def get_vm_kernel_dsa_rpm_file(self):
        """
        Function to get the kernel rpm file name from xml config file.
        :return: return the kernel rpm file name
        """
        try:
            return self.config_file_path(attrib="tools/vm_kernel_rpm_dsa_file_name")
        except Exception as ex:
            self._log.error("VM Kernel dsa rpm file name not defined in content_configuration.xml file, Test may fail!")
            return ""

    def get_kernel_dsa_rpm_file(self):
        """
        Function to get the kernel rpm file name from xml config file.
        :return: return the kernel rpm file name
        """
        try:
            return self.config_file_path(attrib="tools/kernel_rpm_dsa_file_name")
        except Exception as ex:
            self._log.error("VM Kernel dsa rpm file name not defined in content_configuration.xml file, Test may fail!")
            return ""

    def get_dpdk_patch_file(self):
        """
        Function to get the dpdk patch file name from xml config file.
        :return: return the dpdk patch file name
        """
        try:
            return self.config_file_path(attrib="tools/dpdk_patch_file_name")
        except Exception as ex:
            self._log.debug("dpdk patch file name is missing in config file for dpdk driver,returning "" ")
            return ""

    def get_num_of_cold_reset_cycles(self):
        """
        Function to get the Number of Cold Reset Cycles from xml config file.
        """
        return int(self.config_file_path(attrib="cold_reset_cycles"))

    def get_memory_variance_percent(self):
        """
        Function to get the variance_percent from xml config file.
        """
        return float(self.config_file_path(attrib="variance_percent"))

    def get_device_booted_device_type(self):
        """
        This method is used to get the type of device that system is booted
        """
        return self.config_file_path(attrib="storage/device_type")

    def get_cr_1lm_power_cycle(self, power_cycle_str):
        """
        Function to get the Number for cold Reboot, graceful_g3, graceful_s5 Cycles from xml config file for cr 1lm.
        :param: power_cycle_str name of the cycle - cold_reboot, warm_reboot, dc_cycle
        :return : Number of cycles as per the content configuration file.
        """
        power_cycle = int(self.config_file_path(attrib="cr_1lm_power_cycle/{}".format(power_cycle_str)))
        return power_cycle

    def get_cr_2lm_power_cycle(self, power_cycle_str):
        """
        Function to get the Number for cold Reboot, graceful_g3, graceful_s5 Cycles from xml config file for cr 2lm.
        :param: power_cycle_str name of the cycle - cold_reboot, warm_reboot, dc_cycle
        :return : Number of cycles as per the content configuration file.
        """
        power_cycle = int(self.config_file_path(attrib="cr_2lm_power_cycle/{}".format(power_cycle_str)))
        return power_cycle

    def get_cpu_qdf_info(self, cpu_family, qdf_tag_name):
        """
        Function to fetch the attribute values of pcie from the xml configuration file.
        :param cpu_family: name of the cpu family
        :return: dictionary of Values of the attributes in string type.
        """
        cpu_info_dict = {}
        tags = self.get_content_config()
        var = tags.find(r".//CPU_INFO/{}/{}".format(cpu_family, qdf_tag_name))
        for node in var:
            for sub_node in node.iter():
                cpu_info_dict[sub_node.tag] = sub_node.text.strip()

        return cpu_info_dict

    def get_cpu_info(self, cpu_family):
        """
        Function to fetch the attribute values of pcie from the xml configuration file.
        :param cpu_family: name of the cpu family
        :return: dictionary of Values of the attributes in string type.
        """
        cpu_info_dict = {}
        tags = self.get_content_config()
        var = tags.find(r".//CPU_INFO/{}".format(cpu_family))
        for node in var:
            for sub_node in node.iter():
                cpu_info_dict[sub_node.tag] = sub_node.text.strip()

        return cpu_info_dict

    def get_security_sgx_params(self, os, attrib, sub_os=None):
        """
        Function to get SGX properties from xml config file.
        """
        if sub_os:
            attrib = (os + "/" + sub_os + "/" + attrib).upper()
        else:
            attrib = (os + "/" + attrib).upper()
        return str(self.config_file_path(attrib=attrib))

    def get_security_tdx_params(self, sut_os):
        """Function to get the information for TDX for a specific OS.
        :param sut_os: OS type (Linux, Windows, ESXi)
        :type: str
        :return: dict of all entries in TDX/$OS
        :rtype: dict"""
        temp_dict = {}
        tags = self.get_content_config()
        var = tags.find(r"./security/TDX/{}".format(sut_os.upper()))
        for node in var:
            for sub_node in node.iter():
                temp_dict[sub_node.tag] = sub_node.text.strip()
        return temp_dict

    def get_security_secure_boot_params(self) -> dict:
        """Function to get the information for UEFI Secure Boot for a specific OS.
        :return: dict of all entries in UEFI Secure Boot"""
        temp_dict = {}
        tags = self.get_content_config()
        var = tags.find(r"./security/SECURE_BOOT")
        for node in var:
            for sub_node in node.iter():
                temp_dict[sub_node.tag] = sub_node.text.strip()
        return temp_dict

    def get_memory_supported_smallest_info(self, processor_name):
        """
        Function to get the capacity,speed,form factor of a dimm & particular processor from xml config file.
        """
        # Get the Automation folder config file path based on OS.
        temp_dict = {}
        tags = self.get_content_config()
        var = tags.find(r".//supported_smallest_capacity_dimms/{}".format(processor_name))
        for node in var:
            for sub_node in node.iter():
                temp_dict[sub_node.tag] = sub_node.text.strip()
        return temp_dict

    def get_rdt_file(self):
        """
        Function to get the RDT file name from xml config file.
        """
        return self.config_file_path(attrib="tools/rdt_file_name")

    def get_kernel_rpm_file(self):
        """
        Function to get the kernel rpm file name from xml config file.
        :return: return the kernel rpm file name
        """
        return self.config_file_path(attrib="tools/kernel_rpm_file_name")

    def get_vm_kernel_rpm_file(self):
        """
        Function to get the vm kernel rpm file name from xml config file.
        :return: return the vm kernel rpm file name
        """
        try:
            return self.config_file_path(attrib="tools/vm_kernel_rpm_file_name")
        except Exception as ex:
            self._log.error("VM Kernel rpm file name not defined in content_configuration.xml file, Test may fail!")
            return ""

    def get_qat_file(self):
        """
        Function to get the qat file name from xml config file.
        :return: return the qat file name
        """
        return self.config_file_path(attrib="tools/qat_file_name")

    def get_vm_qat_file(self):
        """
        Function to get the qat file name from xml config file.
        :return: return the qat file name
        """
        try:
            return self.config_file_path(attrib="tools/vm_qat_file_name")
        except Exception as ex:
            self._log.error("VM QAT file name not defined in content_configuration.xml file, Test may fail!")
            return self.get_qat_file()

    def get_qat_file_esxi(self):
        """
        Function to get the qat file name from xml config file.
        :return: return the qat file name
        """
        try:
            return self.config_file_path(attrib="tools/qat_file_name_esxi")
        except Exception as ex:
            self._log.error("ESXi QAT driver file name not defined in content_configuration.xml file, Test may fail!")
            return ""

    def get_dlb_file_esxi(self):
        """
        Function to get the dlb file name from xml config file.
        :return: return the dlb file name
        """
        try:
            return self.config_file_path(attrib="tools/dlb_file_name_esxi")
        except Exception as ex:
            self._log.error("ESXi DLB driver file name not defined in content_configuration.xml file, Test may fail!")
            return ""

    def get_pcie_device_name(self):
        """
        Function to get PCIE Name
        :return: return the pcie name
        """
        return self.config_file_path(attrib="ras/pcie_device_name")

    def get_network_drivers(self):
        """
        Function to get the Network Drivers file from xml config file.
        :return: return the Network Drivers file path
        """
        return self.config_file_path(attrib="drivers/network_drivers")

    def get_memory_prime95_running_time(self):
        """
        Function to get the running time to finish the prime95 application from xml config file.
        """
        return int(self.config_file_path(attrib="prime95/running_time"))

    def get_cpu_utilization_percent_for_prime95_test(self):
        """
        Function to get the cpu_utilization_percent xml config file.
        """
        return int(self.config_file_path(attrib="prime95/percent_cpu_utilization"))

    def get_mem_utilization_percent_for_prime95_test(self):
        """
        Function to get the memory_utilization_percent xml config file.
        """
        return self.config_file_path(attrib="prime95/percent_memory_utilization")

    def get_percent_of_total_memory_for_prime95_test(self):
        """
        Function to get the 90_percent_of_total_memory xml config file.
        """
        return float(self.config_file_path(attrib="prime95/percent_memory_for_prime95_test"))

    def get_min_percent_of_total_memory_for_prime95_test(self):
        """
        Function to get the minimum_torture_mem_percent xml config file.
        """
        return float(self.config_file_path(attrib="prime95/minimum_prime95_mem_percent"))

    def get_max_percent_of_total_memory_for_prime95_test(self):
        """
        Function to get the 90_percent_of_total_memory xml config file.
        """
        return float(self.config_file_path(attrib="prime95/maximum_prime95_mem_percent"))

    def get_supported_sata_port_speed(self):
        """
        Function to get the storage Sata Link Speed from xml config file.
        eg. SATA link Speed
        return list
        raise:None
        """
        temp_list = []
        tags = self.get_content_config()
        var = tags.find(r"./storage/SATA")
        for node in var:
            for sub_node in node.iter():
                temp_list.append(sub_node.text.strip())
        return temp_list

    def get_iwvss_run_time(self):
        """
        Function to get the running time to finish the iwvss tool test from xml config file.
        """
        return int(self.config_file_path(attrib="iwvss_run_time"))

    def get_mem_utilization_percent(self):
        """
        Function to get the memory_utilization_percent xml config file.
        """
        return float(self.config_file_path(attrib="memory_utilization"))

    def get_cpu_utilization_percent(self):
        """
        Function to get the cpu_utilization_percent xml config file.
        """
        return int(self.config_file_path(attrib="cpu_utilization"))

    def get_ipmctl_efi_file(self):
        """
        Function to get the host_tool_path from xml config file.
        """
        return self.config_file_path(attrib="tools/ipmctl_efi_file_name")

    def get_sps_tool_info(self):
        """
        Function to collect sps_Tools zip file
        :return: return the file path and version
        """
        path = self.config_file_path(attrib="tools/sps/path")
        version = self.config_file_path(attrib="tools/sps/version")
        return path, version

    def get_vcenter_ip(self):
        """
        Function to get the vcenter ip from xml config file.
        """
        try:
            return str(self.config_file_path(attrib="virtualization/esxi/vcenter_ip"))
        except Exception as ex:
            self._log.error(
                "ESXi vcenter ip Identifier is not defined in content_configuration.xml file, Test may fail!")
            return ""

    def get_vcenter_username(self):
        """
        Function to get the vcenter username from xml config file.
        """
        try:
            return str(self.config_file_path(attrib="virtualization/esxi/vcenter_username"))
        except Exception as ex:
            self._log.error(
                "ESXi vcenter username Identifier is not defined in content_configuration.xml file, Test may fail!")
            return ""

    def get_vcenter_password(self):
        """
        Function to get the vcenter password from xml config file.
        """
        try:
            return str(self.config_file_path(attrib="virtualization/esxi/vcenter_password"))
        except Exception as ex:
            self._log.error(
                "ESXi vcenter password Identifier is not defined in content_configuration.xml file, Test may fail!")
            return ""

    def get_vm_memory_size(self, os_name, os_flavour):
        """
        Function to get the memory_size from xml config file.
        """
        return int(self.config_file_path(attrib="virtualization/{}/{}/ISO/memory_size".format(os_name, os_flavour)))

    def get_number_of_linux_vm(self):
        """
        Function to get the total number of Linux vm from config file to create vm.
        """
        return str(self.config_file_path(attrib="virtualization/number_of_linux_vm"))

    def get_number_of_windows_vm(self):
        """
        Function to get the total number of windows vm from config file to create vm.
        """
        return str(self.config_file_path(attrib="virtualization/number_of_windows_vm"))

    def enable_with_mac_id(self):
        """
        This method is to get the flag to Assign MAC id to Network Adapter.
        """
        return eval(self.config_file_path(attrib="virtualization/enable_with_registered_mac_id"))

    def get_wait_for_vm_os_time_out(self):
        """
        This method is to get the wait for VM OS time out in sec.
        """
        return int(self.config_file_path(attrib="virtualization/wait_for_vm_os_in_sec"))

    def get_vm_no_of_cpu(self, os_name, os_flavour):
        """
        Function to get the no_of_cpu from xml config file.
        """
        return int(self.config_file_path(attrib="virtualization/{}/{}/ISO/num_of_cpus".format(os_name, os_flavour)))

    def get_vm_disk_size(self, os_name, os_flavour):
        """
        Function to get the disk_size from xml config file.
        """
        return int(
            self.config_file_path(attrib="virtualization/{}/{}/ISO/disk_space_in_gb".format(os_name, os_flavour)))

    def get_os_iso_location_on_host(self, sut_os_type, vm_os_subtype):
        """
        :param sut_os_type - SUT Os Type
        :param vm_os_subtype - VM OsSub Type
        Function to get the image_host_location of vm_os_type from xml config file.
        """
        return str(self.config_file_path(attrib="virtualization/{}/{}/ISO/os_iso_location_on_host".format(sut_os_type,
                                                                                                          vm_os_subtype)))

    def get_vm_esxi_guestos_identifier(self, os_name, os_flavour):
        """
        Function to get the guest_os_identifier from xml config file.
        """
        try:
            return str(
                self.config_file_path(attrib="virtualization/{}/{}/ISO/esxi_guestos_id".format(os_name, os_flavour)))
        except Exception as ex:
            self._log.error("ESXi Guest OS Identifier is not defined in content_configuration.xml file, Test may fail!")
            return ""

    def get_vm_esxi_guestos_pwrcli_identifier(self, os_name, os_flavour):
        """
        Function to get the guest_os_identifier from xml config file.
        """
        try:
            return str(self.config_file_path(
                attrib="virtualization/{}/{}/ISO/esxi_guestos_pwrcli_id".format(os_name, os_flavour)))
        except Exception as ex:
            self._log.error(
                "ESXi Guest OS PwrCli Identifier is not defined in content_configuration.xml file, Test may fail!")
            return ""

    def get_vm_os_variant(self, os_name, os_flavour):
        """
        Function to get the os_variant from xml config file.
        """
        return str(self.config_file_path(attrib="virtualization/{}/{}/ISO/os_variant".format(os_name, os_flavour)))

    def get_centos_iso_image_host_location(self):
        """
        Function to get the image_host_location of RHEL from  xml config file.
        """
        return str(self.config_file_path(attrib="virtualization/linux/CENTOS/ISO/os_iso_location_on_host"))

    def get_rhel_iso_image_host_location(self):
        """
        Function to get the image_host_location of RHEL from  xml config file.
        """
        return str(self.config_file_path(attrib="virtualization/linux/RHEL/ISO/os_iso_location_on_host"))

    def get_centos_img_image_host_location(self):
        """
        Function to get the image_host_location of RHEL from  xml config file.
        """
        try:
            return str(self.config_file_path(attrib="virtualization/linux/CENTOS/ISO/os_img_location_on_host"))
        except Exception as ex:
            self._log.error("CentOs Raw Image Path is not defined in content_configuration.xml file, Test may fail!")
            return ""

    def get_rhel_img_image_host_location(self):
        """
        Function to get the image_host_location of RHEL from  xml config file.
        """
        try:
            return str(self.config_file_path(attrib="virtualization/linux/RHEL/ISO/os_img_location_on_host"))
        except Exception as ex:
            self._log.error("RHEL Raw Image Path is not defined in content_configuration.xml file, Test may fail!")
            return ""

    def get_os_iso_location_on_host(self, sut_os_type, vm_os_subtype):
        """
        :param sut_os_type - SUT Os Type
        :param vm_os_subtype - VM OsSub Type
        Function to get the image_host_location of vm_os_type from xml config file.
        """
        return str(self.config_file_path(attrib="virtualization/{}/{}/ISO/os_iso_location_on_host".format(sut_os_type,
                                                                                                          vm_os_subtype)))

    def get_vm_mac_id(self, os_name, os_flavour):
        """
        Function to get the VM MAC id from xml config file.
        """
        try:
            return str(self.config_file_path(attrib="virtualization/{}/{}/ISO/mac_id".format(os_name, os_flavour))) \
                .split(",")
        except Exception as ex:
            raise content_exceptions.TestSetupError("Please provide the Pre Registered free mac ids under this tag {}"
                                                    " in content_configuration.xml file"
                                                    .format("virtualization/{}/{}/ISO/mac_id"
                                                            .format(os_name, os_flavour)))

    def get_windows_iso_image_host_location(self):
        """
        Function to get the image_host_location of Windows from  xml config file.
        """
        return str(self.config_file_path(attrib="virtualization/windows/RS5/ISO/os_iso_location_on_host"))

    def get_rhel_vm_template_host_location(self):
        """
        Function to get the template_vm_location of RHEL from  xml config file.
        """
        return str(self.config_file_path(attrib="virtualization/linux/RHEL/VM_Template/template_location_on_host"))

    def get_windows_vm_template_host_location(self):
        """
        Function to get the template_vm_location of Windows from  xml config file.
        """
        return str(self.config_file_path(attrib="virtualization/windows/RS5/VM_Template/template_location_on_host"))

    def get_vm_kernel_version(self, os_name, os_flavour):
        """
        Function to get the kernel_version from xml config file.
        """
        return str(self.config_file_path(attrib="virtualization/{}/{}/ISO/kernel_version".format(os_name, os_flavour)))

    def get_linux_vm_password(self, os_name, os_flavour):
        """
        Function to get the Linux VM password
        :param os_name - SUT OS type
        :param os_flavour - VM OS subType
        """
        return str(self.config_file_path(attrib="virtualization/{}/{}/ISO/password".format(os_name, os_flavour)))

    def get_linux_vm_user_name(self, os_name, os_flavour):
        """
        This method is to get the Linux VM User name.
        :param os_name- SUT OS Type
        :param os_flavour- VM OS Sub Type
        """
        return str(self.config_file_path(attrib="virtualization/{}/{}/ISO/user_name".format(os_name, os_flavour)))

    def get_mac_address_for_vm(self, os_name, os_flavour, nesting_level=None):
        """
        This method is to get the MacAddr in List.
        :param os_name - SUT OS
        :param os_flavour - VM OS flavor
        :nesting_level - VM nesting level in case of the Nested VM None for l1 /l2
        :return MacAddresses in List - eg: [12:57:00:3d:22:11, 12:57:00:3d:23:12]
        :raise content_exceptions - raise if MacAddress is not found with IEEE Std.
        """
        if nesting_level is None:
            mac_address_tag = "mac_address"
        else:
            mac_address_tag = "mac_address_{}".format(nesting_level)

        mac_addr_list = str(self.config_file_path(attrib="virtualization/{}/{}".format(os_name, mac_address_tag))
                            ).split(',')
        import re
        for each_mac_address in mac_addr_list:
            if not re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", each_mac_address.lower()):
                raise content_exceptions.TestFail("Please keep Correct format MacAddress in content config"
                                                  "Please refer Example: 12:56:00:3b:21:12")

        if os_name == "windows":
            windows_mac_addr_list = []
            for each_addr in mac_addr_list:
                windows_mac_addr_list.append(each_addr.replace(':', ''))
            self._log.info("MacAddresses from Config- {}".format(windows_mac_addr_list))
            return windows_mac_addr_list
        else:
            self._log.info("MacAddresses from Config- {}".format(mac_addr_list))
            return mac_addr_list

    def get_yum_repo_name(self, os_name, os_flavour):
        """
        Function to get the kernel_version from xml config file.
        """
        return str(self.config_file_path(
            attrib="virtualization/{}/{}/ISO/yum_repos_location_on_host".format(os_name, os_flavour)))

    def get_num_vms_to_create(self):
        """
        Function to get the number of VM to create for IO.
        """
        return int(self.config_file_path(attrib="io_virtualization/number_of_vms"))

    def get_validation_runner_location(self, sut_os):
        """
        Function to get validation runner from xml config file.
        """
        return str(self.config_file_path(attrib="validation_runner/{}".format(sut_os)))

    def get_no_of_cycles_to_execute_linpack(self):
        """
        Method to get the number of cycles to execute linpack.
        """
        return int(self.config_file_path(attrib="linpack_tool/no_of_time_to_execute"))

    def get_shutdown_timeout(self):
        """
        Method to get Shutdown Timeout from xml config file for Manageability Test Cases
        """
        return int(self.config_file_path(attrib="manageability/shutdown_timeout"))

    def get_softshutdown_timeout(self):
        """
        Method to get Soft Shutdown Timeout from xml config file for Manageability Test Cases
        """
        return int(self.config_file_path(attrib="manageability/softshutdown_timeout"))

    def get_usb_set_time_delay(self):
        """
        Function to delay time till the usb is setup.
        """
        return int(self.config_file_path(attrib="usb_set_time"))

    def get_usb_device(self):
        """
        Get the type of the usb device connected and bcd value of the device
        """
        usb_device = {}
        usb_device["type"] = self.config_file_path(attrib="usb/device/type")
        usb_device["bcd"] = self.config_file_path(attrib="usb/device/bcd")
        usb_device["bcd_mouse"] = self.config_file_path(attrib="usb/device/bcd_mouse")
        usb_device["bcd_keyboard"] = self.config_file_path(attrib="usb/device/bcd_keyboard")
        usb_device["bcd_usb_key"] = self.config_file_path(attrib="usb/device/bcd_usb_key")
        usb_device["bcd_hub"] = self.config_file_path(attrib="usb/device/bcd_hub")
        usb_device["bcd_hdd"] = self.config_file_path(attrib="usb/device/bcd_hdd")
        usb_device["bcd_hdd_centos"] = self.config_file_path(attrib="usb/device/bcd_hdd_centos")
        return usb_device

    def hdd_model_number(self):
        """
        This method is to get hdd model number
        """
        return str(self.config_file_path(attrib="usb/device/hdd_model_number"))

    def hdd_serial_number(self):
        """
        This method is to get hdd serial number
        """
        return str(self.config_file_path(attrib="usb/device/hdd_serial_number"))

    def get_solar_tool_name(self, sut_os):
        """
        Function to get solar tool name from xml config file.
        """
        return str(self.config_file_path(attrib="solar/{}".format(sut_os)))

    def get_hqm_file(self):
        """
        Function to get the hqm driver name from xml config file
        .
        :return: return the hqm file name
        """
        return self.config_file_path(attrib="tools/hqm_file_name")

    def get_vm_hqm_file(self):
        """
        Function to get the hqm driver name from xml config file
        .
        :return: return the hqm file name
        """
        try:
            return self.config_file_path(attrib="tools/vm_hqm_file_name")
        except Exception as ex:
            self._log.error("VM HQM file name not defined in content_configuration.xml file, Test may fail!")
            return self.get_hqm_file()

    def get_vcenter_esxi_file(self):
        """
        Function to get the vcenter driver name from xml config file
        .
        :return: return the vcenter file name
        """
        try:
            return self.config_file_path(attrib="tools/vcenter_esxi_file_name")
        except Exception as ex:
            return ""

    def get_vcenter_json_file(self):
        """
        Function to get the vcenter json driver name from xml config file
        .
        :return: return the vcenter json file name
        """
        try:
            return self.config_file_path(attrib="tools/vcenter_json_file_name")
        except Exception as ex:
            return ""

    def get_idx_file(self):
        """
        Function to get the hqm driver name from xml config file
        .
        :return: return the hqm file name
        """
        return self.config_file_path(attrib="tools/idx_file_name")

    def get_vm_idx_file(self):
        """
        Function to get the idxd driver name from xml config file
        .
        :return: return the idxd file name
        """
        try:
            return self.config_file_path(attrib="tools/vm_idx_file_name")
        except Exception as ex:
            self._log.error("VM IDXD file name not defined in content_configuration.xml file, Test may fail!")
            return self.get_idx_file()

    def get_nvme_file(self):
        """
        Function to get the nvme driver name from xml config file
        .
        :return: return the nvme file name
        """
        try:
            return self.config_file_path(attrib="tools/nvme_file_name")
        except Exception as ex:
            return ""

    def get_disk_esxi(self):
        """
        Function to get the get_disk_esxi name from xml config file
        .
        :return: return the get_disk_esxi
        """
        try:
            return self.config_file_path(attrib="virtualization/esxi/disk_name")
        except Exception as ex:
            return ""

    def get_datastore_name(self):
        """
        Function to get the get_disk_esxi name from xml config file
        .
        :return: return the get_disk_esxi
        """
        try:
            return self.config_file_path(attrib="virtualization/esxi/datastore_name")
        except Exception as ex:
            return ""

    def get_spr_file(self):
        """
        Function to get the hqm driver name from xml config file
        .
        :return: return the hqm file name
        """
        return self.config_file_path(attrib="tools/spr_file_name")

    def miv_warm_reset_timeout(self):
        """
        Function to get the MIV warm reset Timeout from xml config file
        """
        return int(self.config_file_path(attrib="miv_warm_reset_timeout"))

    def get_max_reserved_capacity_gib_memory(self):
        """
        Function to get the maximum inaccessible reserved capacity from xml config file
        """
        return int(self.config_file_path(attrib="max_reserved_capacity_gib"))

    def get_supported_ddr_frequencies(self, processor_name):
        """
        Function to get the the supported frequencies from xml config file
        """
        return list(self.config_file_path(attrib=r"Supported_Frquencies/{}/frequencies".format(processor_name)).
                    split(','))

    def get_pcie_cycling_time_to_execute(self):
        """
        Function to get the time in sec to execute the cycling Test Case.
        """

        return int(self.config_file_path(attrib="pcie/cycling_time"))

    def make_filesystem_timeout(self):
        """
        Function to get the max timeout value from the xml config file.
        """
        return float(self.config_file_path(attrib="wait_time_to_create_filesystem"))

    def get_ilvss_file_name_license_name(self):
        """"
        Function to get the ilvss file name and license key file name from xml config file
        """
        ilvss_file_name = self.config_file_path(attrib="memory/ilvss/ilvss_file_name")
        licence_key_file_name = self.config_file_path(attrib="memory/ilvss/ilvss_licence_key")
        return ilvss_file_name, licence_key_file_name

    def burnin_test_execute_time(self):
        """
        Function to get the running time to finish the burnin test from xml config file.
        """
        return int(self.config_file_path(attrib="burnin_test_execute_time"))

    def get_intel_optane_pmem_mgmt_file(self):
        """
        Function to get the get_intel_optane_pmem_mgmt_file from xml config file.
        """
        return self.config_file_path(attrib="tools/intel_optane_pmem_mgmt_file_name")

    def get_number_of_cycle_to_execute_devcon_utility_test(self):
        """
        Function to get the number of cycle to execute devcon utility test.
        """
        return self.config_file_path(attrib="pcie/no_of_cycle")

    def memory_mlc_loaded_latency_threshold(self):
        """
        Function to get the mlc loaded latency threshold value from xml config file.
        """
        return int(self.config_file_path(attrib="loaded_latency_threshold"))

    def get_intelssd_location(self, sut_os):
        """
        Function to get intel ssd dc tool from xml config file.
        """
        return self.config_file_path(attrib="intelssd/{}".format(sut_os))

    def get_hqm_ldb_traffic_data(self):
        """
        Function to get the hqm ldb traffic data from xml config file.
        """
        return self.config_file_path(attrib="hqm_ldb_traffic")

    def get_number_of_cycle_to_test_ltssm(self):
        """
        Function to get the number of cycle to Test Lttsm.
        """
        return self.config_file_path(attrib="pcie/no_of_cycle_to_test")

    def get_vroc_tool_location(self, sut_os):
        """
        Function to get vroc_tool from xml config file.
        """
        return str(self.config_file_path(attrib="vroc_tool/{}".format(sut_os)))

    def get_os_pkg_path(self, os_type):
        """
        Function to get the OS package path.
        """
        return self.config_file_path(attrib="os_installation/{}/os_pkg_path".format(os_type))

    def get_sft_pkg_path(self, os_type):
        """
        Function to get the software package path.
        """
        return self.config_file_path(attrib="os_installation/{}/sft_pkg_path".format(os_type))

    def get_cfg_file_name(self, os_type):
        """
        Function to get the cfg file name.
        """
        return self.config_file_path(attrib="os_installation/{}/cfg_file_name".format(os_type))

    def get_current_bmc_fw_file_path(self):
        """
        Function to get the new bmc FW file path to be updated.
        :return: return the new bmc FW file path
        """
        return str(self.config_file_path(attrib="ifwi/current_bmc_fw_file"))

    def get_previous_bmc_fw_file_path(self):
        """
        Function to get the current bmc FW file path to be updated.
        :return: return the new bmc FW file path
        """
        return str(self.config_file_path(attrib="ifwi/previous_bmc_fw_file"))

    def get_driver_device_id(self, driver_name):
        """
        Function to get the driver device id of the given driver.
        :param driver_name: Driver name
        :return: Device ID of the driver
        """
        from src.provider.driver_provider import NetworkDrivers
        if driver_name == NetworkDrivers.FOXVILLE_DRIVER_NAME:
            return self.config_file_path(attrib="foxville/devices/device/deviceid")
        elif driver_name == NetworkDrivers.FORTVILLE_DRIVER_NAME:
            return self.config_file_path(attrib="fortville/devices/device/deviceid")
        elif driver_name == NetworkDrivers.CARLSVILLE_DRIVER_NAME:
            return self.config_file_path(attrib="carlsville/devices/device/deviceid")
        elif driver_name == NetworkDrivers.JACKSONVILLE_DRIVER_NAME:
            return self.config_file_path(attrib="jacksonville/devices/device/deviceid")
        elif driver_name == NetworkDrivers.COLUMBIAVILLE_DRIVER_NAME:
            return self.config_file_path(attrib="columbiaville/devices/device/deviceid")
        else:
            raise content_exceptions.TestNotImplementedError("Configuration not done for {}".format(driver_name))

    def get_driver_inf_file_name(self, driver_name):
        """
        Function to get the inf file of the given driver.
        :param driver_name: Driver name
        :return: inf file of the driver
        """
        from src.provider.driver_provider import NetworkDrivers
        if driver_name == NetworkDrivers.FOXVILLE_DRIVER_NAME:
            return self.config_file_path(attrib="foxville/devices/device/inf_file_name")
        elif driver_name == NetworkDrivers.FORTVILLE_DRIVER_NAME:
            return self.config_file_path(attrib="fortville/devices/device/inf_file_name")
        elif driver_name == NetworkDrivers.CARLSVILLE_DRIVER_NAME:
            return self.config_file_path(attrib="carlsville/devices/device/inf_file_name")
        elif driver_name == NetworkDrivers.JACKSONVILLE_DRIVER_NAME:
            return self.config_file_path(attrib="jacksonville/devices/device/inf_file_name")
        elif driver_name == NetworkDrivers.COLUMBIAVILLE_DRIVER_NAME:
            return self.config_file_path(attrib="columbiaville/devices/device/inf_file_name")
        else:
            raise content_exceptions.TestNotImplementedError("Configuration not done for {}".format(driver_name))

    def get_nvme_cards_info(self):
        """
        Function to fetch the attribute values of pcie slots from the xml configuration file.
        :return: List of Values of the attributes in string type.
        """
        list_of_pcie_slots_data = []
        tags = self.get_content_config()
        var = tags.findall(r".//nvme_cards/")
        for node in var:
            for sub_node in node.iter():
                list_of_pcie_slots_data.append(sub_node.text.strip())

        return list_of_pcie_slots_data

    def get_ifwi_image_path(self, profile):
        """
        Function to get IFWI image file path from xml config file.
        :param: profile: IFWI profile Type
        :return: IFWI file path
        """
        if profile == "Profile0":
            return self.config_file_path(attrib="ifwi/ifwi_profile_bin_path/profile0")
        elif profile == "Profile3":
            return self.config_file_path(attrib="ifwi/ifwi_profile_bin_path/profile3")
        elif profile == "Profile4":
            return self.config_file_path(attrib="ifwi/ifwi_profile_bin_path/profile4")
        elif profile == "Profile5":
            return self.config_file_path(attrib="ifwi/ifwi_profile_bin_path/profile5")
        elif profile == "IFWI Current Version":
            return self.config_file_path(attrib="ifwi/ifwi_profile_bin_path/current_ifwi_version")
        elif profile == "IFWI Previous Version":
            return self.config_file_path(attrib="ifwi/ifwi_profile_bin_path/previous_ifwi_version")
        else:
            raise content_exceptions.TestNotImplementedError("Configuration not added for {} image".format(profile))

    def get_dynamo_location(self, sut_os):
        """
        Function to get dynamo tool location from xml config file.
        :param: sut_os: OS Type
        :return: Dynamo meter path
        """
        return self.config_file_path(attrib="dynamo/{}".format(sut_os))

    def get_iometer_tool_config_file(self):
        """
        Function to get iometer config file tool location from xml config file.
        :param: sut_os: OS Type
        :return: Dynamo meter path
        """
        return self.config_file_path(attrib="iometer_tool_config_file")

    def get_cscripts_ei_pcie_device_socket(self):
        """
        Function to fetch error injection socket.
        :return:
        """
        return int(self.config_file_path(attrib="cscripts_ei_pcie_device/socket"))

    def get_pcie_device_socket_to_degrade(self):
        """
        Function to fetch socket to degrade speed.
        """
        return int(self.config_file_path(attrib="io_virtualization/pcie_degrade_ports/socket"))

    def get_pcie_device_pxp_port_to_degrade(self):
        """
        Function to fetch pxp port to degrade speed.
        """
        return str(self.config_file_path(attrib="io_virtualization/pcie_degrade_ports/pxp_port"))

    def get_cscripts_ei_pcie_device_pxp_port(self):
        """
        Function to fetch error injection port.
        :return:
        """
        return str(self.config_file_path(attrib="cscripts_ei_pcie_device/pxp_port"))

    def get_linux_os_pcie_bdf(self):
        """
        Function to fetch test card OS pcie bdf information
        :return:
        """
        return str(self.config_file_path(attrib="linux_os_pcie_bdf"))

    def get_keysight_card_bdf_in_windows(self):
        """
        This method is to get Keysight Card bdf in Windows.
        :return bdf
        """
        return str(self.config_file_path(attrib="keysight_card_bdf"))

    def get_memory_address_to_inject_error_for_keysight_card(self):
        """
        This method is to get memory address to inject the error.
        :return address in str
        """
        return str(self.config_file_path(attrib="memory_addr_to_inject_error"))

    def get_memory_address_to_inject_poison_error_for_keysight_card(self):
        """
        This method is to get memory address to inject the poison error.
        :return address in str
        """
        return str(self.config_file_path(attrib="memory_addr_to_inject_error"))

    def get_keysight_card_bdf_in_uefi(self):
        """
        This method is to get Keysight Card bdf in uefi.
        :return bdf
        """
        return str(self.config_file_path(attrib="keysight_card_bdf"))

    def get_nvme_partition_to_mount(self):
        """
        Function to fetch partition path to mount on Linux
        :return:
        """
        return str(self.config_file_path(attrib="partition_to_mount"))

    def get_nvme_disks(self):
        """
        Function to get the NVME disks
        :return: NVME DISK LIST if NVME disk is update in content config else empty list raise exception
        """
        try:
            nvme_disks = self.config_file_path(attrib="nvme_disks_linux")
            list_nvme_disks = [disks.strip() for disks in nvme_disks.split(",")]
            return list_nvme_disks
        except Exception as ex:
            return []

    def get_fortville_nic_device_name(self):
        """
        Function to get Fortville NIC Name
        :return: return the Fortville NIC Name
        """
        return self.config_file_path(attrib="tools/fortville_nic")

    def get_columbiaville_nic_device_name(self):
        """
        Function to get Columbiaville NIC Name
        :return: return the Columbiaville NIC Name
        """
        return self.config_file_path(attrib="tools/columbiaville_nic")

    def get_mellanox_nic_device_name(self):
        """
        Function to get Mellanox NIC Name
        :return: return the Mellanox NIC Name
        """
        return self.config_file_path(attrib="tools/mellanox_nic")

    def get_gen5_nic_device_name(self):
        """
        Function to get GEN5 NIC Name
        :return: return the GEN5 NIC Name
        """
        return self.config_file_path(attrib="tools/gen5_nic")

    def get_accel_tool_path(self):
        """
        Function to get the accel config tool path from xml config file.
        :return: return the accel config tool path
        """
        return self.config_file_path(attrib="tools/accel_tool_path")

    def get_ptu_tool_location(self, sut_os):
        """
        Function to get ptu tool location from xml config file.
        """
        return str(self.config_file_path(attrib="ptu/{}".format(sut_os)))

    def get_bus_id(self, product, slot_name):
        """
        This method is to get the slot c or m2 slot bus id based on input param.
        :param product
        :param slot_name
        :return bus id
        """
        return str(self.config_file_path(attrib="pcie_device_population/{}/bus".format(slot_name)))

    def get_num_of_cycle_to_load_unload_driver(self):
        """
        This method is use to get the number of driver cycling.
        """

        return int(self.config_file_path(attrib="pcie/number_of_cycle_to_load_unload_driver"))

    def get_pch_slot_nvme_m2_info(self, product_family):
        """
        This method is to get the required device details from config.
        :param product_family
        :return list
        """
        m2_pch_details_dict = {}
        m2_slot = "pcie_m_2"
        tag = self.get_content_config()
        m2_pch_details_dict[PcieSlotAttribute.SLOT_NAME] = m2_slot
        var = tag.find(r".//pcie_device_population/{}".format(m2_slot))
        for node in var.iter():
            if not node.tag == m2_slot:
                m2_pch_details_dict[node.tag] = node.text.strip()
        self._log.debug("PCH Slot list from config file: {}".format(m2_pch_details_dict))
        return m2_pch_details_dict

    def get_pch_slot_c_spr_info(self, product_family):
        """
        This method is to get the required device details from config.
        :param product_family
        :return list
        """
        pcie_pch_details_dict = {}
        pcie_slot_c = "slot_c"
        tag = self.get_content_config()
        pcie_pch_details_dict[PcieSlotAttribute.SLOT_NAME] = pcie_slot_c
        var = tag.find(r".//pcie_device_population/{}/{}".format(product_family, pcie_slot_c))
        for node in var.iter():
            if not node.tag == pcie_slot_c:
                pcie_pch_details_dict[node.tag] = node.text.strip()
        self._log.debug("PCH Slot list from config file: {}".format(pcie_pch_details_dict))
        return pcie_pch_details_dict

    def get_pch_slot_c_info(self, product_family):
        """
        This method is to get the required device details from config.
        :param product_family
        :return list
        """
        pcie_pch_details_dict = {}
        pcie_slot_c = "slot_c"
        tag = self.get_content_config()
        pcie_pch_details_dict[PcieSlotAttribute.SLOT_NAME] = pcie_slot_c
        var = tag.find(r".//pcie_device_population/{}".format(pcie_slot_c))
        for node in var.iter():
            if not node.tag == pcie_slot_c:
                pcie_pch_details_dict[node.tag] = node.text.strip()
        self._log.debug("PCH Slot list from config file: {}".format(pcie_pch_details_dict))
        return pcie_pch_details_dict

    def get_sut_nic_driver_module_name(self):
        """
        Fetches the name of the Linux driver module for the NIC endpoint under test
        :return: The requested driver module name from content_configuration.xml
        """
        return str(self.config_file_path(attrib="sut_nic_driver_module_name"))

    def get_sut_nic_endpoint1_ip_address_1(self):
        """
        Fetches the IP address for NIC endpoint 1, first ethernet port
        :return: The requested IP address from content_configuration.xml
        """
        return str(self.config_file_path(attrib="sut_nic_endpoint1_ip_address_1"))

    def get_sut_nic_endpoint2_ip_address_1(self):
        """
        Fetches the IP address for NIC endpoint 2, first ethernet port
        :return: The requested IP address from content_configuration.xml
        """
        return str(self.config_file_path(attrib="sut_nic_endpoint2_ip_address_1"))

    def get_sut_nic_endpoint1_netdev_1(self):
        """
        Fetches the system netdev name for NIC endpoint 1, first ethernet port
        :return: The requested netdev name from content_configuration.xml
        """
        return str(self.config_file_path(attrib="sut_nic_endpoint1_netdev_1"))

    def get_sut_nic_endpoint2_netdev_1(self):
        """
        Fetches the system netdev name for NIC endpoint 2, first ethernet port
        :return: The requested netdev name from content_configuration.xml
        """
        return str(self.config_file_path(attrib="sut_nic_endpoint2_netdev_1"))

    def get_sut_nic_endpoint1_netmask(self):
        """
        Fetches the CIDR netmask for NIC endpoint 1
        :return: The requested CIDR netmask from content_configuration.xml
        """
        return str(self.config_file_path(attrib="sut_nic_endpoint1_cidr_netmask"))

    def get_sut_nic_endpoint2_netmask(self):
        """
        Fetches the CIDR netmask for NIC endpoint 2
        :return: The requested CIDR netmask from content_configuration.xml
        """
        return str(self.config_file_path(attrib="sut_nic_endpoint2_cidr_netmask"))

    def get_alt_socket_einj_injection_iteration_count(self):
        """
        Fetches the number of desired injection attempts for the APEI EINJ method
        :return: The requested number of injection iterations from content_configuration.xml
        """
        return str(self.config_file_path(attrib="alt_socket_einj_injection_iteration_count"))

    def get_sut_upi_minimum_hit_threshold_count(self):
        """
        Fetches the desired minimum number of NUMA "other_node" hits
        :return: The requested minimum number of other_node hits from content_configuration.xml
        """
        return str(self.config_file_path(attrib="sut_upi_minimum_hit_threshold_count"))

    def get_corr_err_inj_post_wait_time(self):
        """
        Fetches the desired wait time after a correctable error
        :return: The requested wait time from content_configuration.xml
        """
        return str(self.config_file_path(attrib="waiting_time_after_injecting_correctable_error"))

    def ras_stress_test_execute_time(self):
        """
        Fetches the desired time to run any test from xml config file, ras section.
        :return: A value that can be used to define test run length
        """
        return int(self.config_file_path(attrib="ras_stress_test_execute_time"))

    def get_keysight_card_gen(self):
        """
        This method is to get gen of Keysight Card.
        :return Gen number
        """
        return int(self.config_file_path(attrib="keysight_pcie_card/keysight_pcie_card_gen"))

    def get_keysight_card_width(self):
        """
        This method is to get width of Keysight Card.
        :return width
        """
        return int(self.config_file_path(attrib="keysight_pcie_card/keysight_pcie_card_width"))

    def get_sriov_adapter(self):
        """
        This method is used to get the SRIOV adapter
        """
        return self.config_file_path(attrib="io_virtualization/sriov_adapter")

    def get_loop_back_adapter(self):
        """
        This method is used to return the adapter which is connected in loop back mode to VM (SRIOV) adapter
        """
        return self.config_file_path(attrib="io_virtualization/loop_back_adapter")

    def get_sut_static_ip(self):
        """
        This method is used to return the static ip to be configured on SUT adapter
        """
        return self.config_file_path(attrib="io_virtualization/sut_static_ip")

    def get_vm_static_ip(self):
        """
        This method is used to return the static ip to be configured on VM adapter
        """
        return self.config_file_path(attrib="io_virtualization/vm_static_ip")

    def get_gateway_ip(self):
        """
        This method is used to return the gateway ip to be configured on adapter
        """
        return self.config_file_path(attrib="io_virtualization/sut_gateway_ip")

    def get_subnet_mask(self):
        """
        This method is used to return the subnet mask to be configured on adapter
        """
        return self.config_file_path(attrib="io_virtualization/sut_subnet_mask")

    def get_num_of_s3_cycles(self):
        """
        Function to get the Number of S3 Cycles from xml config file.
        """
        return int(self.config_file_path(attrib="s3_cycles"))

    def get_waiting_time_of_s3_cycles(self):
        """
        Function to get the Waiting Time of S3 Cycles from xml config file.
        """
        return int(self.config_file_path(attrib="s3_waiting_time"))

    def get_num_of_s4_cycles(self):
        """
        Function to get the Number of S4 Cycles from xml config file.
        """
        return int(self.config_file_path(attrib="s4_cycles"))

    def get_waiting_time_of_s4_cycles(self):
        """
        Function to get the Waiting Time of S4 Cycles from xml config file.
        """
        return int(self.config_file_path(attrib="s4_waiting_time"))

    def get_boot_media_device(self):
        """
        Function to get the Booting media device from xml config file.
        """
        try:
            return self.config_file_path(attrib="boot_media_device")
        except Exception:
            raise content_exceptions.TestFail("Boot media device name is missing in configuration file, Please add it")

    def get_dpmo_ignore_pc_errors_list(self):
        """
        Function to get the frequencies from xml config file.
        """
        try:
            reg_exp = "^[A-Fa-f0-9]{2}$"
            pc_errors = self.config_file_path(attrib="ignore_pc_errors")
            list_ignore_pc_errors = [pc.strip().upper() for pc in pc_errors.split(",") if
                                     re.search(reg_exp, pc.strip())]
            return list_ignore_pc_errors
        except Exception as ex:
            return []

    def get_axon_analyzers(self):
        try:
            analyzers = self.config_file_path(attrib="axon_analyzers")
            list_analyzers = [analyzer.strip() for analyzer in analyzers.split(",")]
            return list_analyzers
        except Exception as ex:
            return []

    def get_pc_stuck_time(self):
        try:
            return int(self.config_file_path(attrib="post_code_stuck_time"))
        except Exception as ex:
            return 0

    def get_pcie_cards_to_be_diabled(self):
        """
        Function to get the list of device ids of pcie cards to be disabled from xml config file.
        """
        return self.config_file_path(attrib="pcie_disable_cards_device_id_list").split(",")

    def disable_pcie_cards(self):
        """
        Function to get the status of pcie cards to be disabled or not from xml config file.
        """
        if self.config_file_path(attrib="pcie_disable") == "True":
            return True
        else:
            return False

    def get_extreme_core_count_multiplier(self):
        """
        Function to get the extreme core count value from xml config file.
        """
        return int(self.config_file_path(attrib="eXtreme_Core_Count_multiplier"))

    def get_high_core_count_multiplier(self):
        """
        Function to get the high core count value from xml config file.
        """
        return int(self.config_file_path(attrib="High_Core_Count_multiplier"))

    def get_low_core_count_multiplier(self):
        """
        Function to get the low core count value from xml config file.
        """
        return int(self.config_file_path(attrib="low_Core_Count_multiplier"))

    def get_sed_update_soc_watch(self):
        """
        Function to get the sed update value in /etc/yum.repos.d/Intel-Embargo.repo
        """
        return self.config_file_path(attrib="sed_update_socwatch")

    def get_sgx_num_of_cycles(self, cycling_str):
        """
        Function to get the sgx Number for Warm Reboot, graceful_g3, graceful_s5 Cycles from xml config file.
        :param: cycling_str name of the cycle - warm_reboot, ac_cycle, dc_cycle
        :return : Number of cycles and recovery_mode as per the content configuration file.
        """
        reboot_cycle = self.config_file_path(attrib="SGX/cycling/{}/number_of_cycles".format(cycling_str))
        recovery_status = self.config_file_path(attrib="SGX/cycling/{}/recovery_mode".format(cycling_str))
        recovery_status = True if recovery_status.lower() == "true" else False
        return int(reboot_cycle), recovery_status

    def get_ddr_cr_population_from_config(self):
        """
        Function to get the population of DDR and CR in the system
        """
        return str(self.config_file_path(attrib="cr_ddr_population"))

    def get_e810_network_adapter_driver(self):
        """
        Function to get Network Adapter Driver for E810 Series Devices
        :return: return the E810 driver details
        """
        return str(self.config_file_path(attrib="tools/E810_network_adapter_driver_name"))

    def get_pre_requisite_packages(self):
        """
        Function to get pre-requisite packages to be installed on SUT
        :return: return the list of packages
        """
        tag_info = str(self.config_file_path(attrib="tools/required_pre_requisite_package"))
        return tag_info.split(",")

    def get_fio_tool_values(self):
        """
        Function to get the fio tool values from the content configuration xml file.
        :return: fio tool values in dictionary format
        """
        fio_dict = {}
        content_config = self.get_content_config()
        for node in content_config.findall(r".//fio/"):
            for subnode in node.iter():
                fio_dict[subnode.tag] = subnode.text.strip()
        return fio_dict

    def get_reboot_iteration(self):
        """
        Function to get the number of reboot iteration
        :return: return number of iteration
        """
        return int(self.config_file_path(attrib="reboot_iteration"))

    def get_pcie_socket_slot_data(self):
        """
        Function to fetch the attribute values of pcie_slots from the xml configuration file.
        :return: list_of_pcie_cards_data
        """
        list_of_pcie_cards_data = []
        tags = self.get_content_config()
        tags_list = tags.findall(r".//pcie_slots")
        for node in tags_list:
            for sub_node in node.iter():
                if sub_node.text.strip() == "True":
                    list_of_pcie_cards_data.append(sub_node.tag)
        return list_of_pcie_cards_data

    def get_telemetry_collector(self):
        """
        Function to check does telemetry collection is required to start or not
        :return: (bool) True - to collect, False - not to collect
        """
        try:
            return eval(self.config_file_path(attrib="telemetry/start_telemetry_collector"))
        except Exception as ex:
            return False

    def get_memory_socket(self):
        """
        This method is to get socket available for the memory to inject error.
        :return socket
        """
        return int(self.config_file_path(attrib="memory/socket"))

    def get_memory_channel(self):
        """
        This method is to get channel available for the memory to inject error.
        :return channel
        """
        return int(self.config_file_path(attrib="memory/channel"))

    def get_memory_micro_controller(self):
        """
        This method is to get micro_controller available for the memory to inject error.
        :return micro_controller
        """
        return int(self.config_file_path(attrib="memory/memory_controller"))

    def get_runner_tool(self):
        """
        Function to get runner tool installation
        :return: return the runner tool details
        """
        return str(self.config_file_path(attrib="tools/runner_file_name"))

    def get_tboot_num_of_cycles(self, cycling_str):
        """
        Function to get the Tboot Number for Warm Reboot, graceful_g3, graceful_s5 Cycles from xml config file.
        :param: cycling_str name of the cycle - warm_reboot, ac_cycle, dc_cycle
        :return : Number of cycles and recovery_mode as per the content configuration file.
        """
        self._log.info("cycling str {}".format(cycling_str))
        reboot_cycle = self.config_file_path(attrib="TBOOT/cycling/{}/number_of_cycles".format(cycling_str))
        recovery_status = self.config_file_path(attrib="TBOOT/cycling/{}/recovery_mode".format(cycling_str))
        recovery_status = True if recovery_status.lower() == "true" else False
        return int(reboot_cycle), recovery_status

    def get_iax_bdf(self):
        """
        This method is to get iax bdf.
        :return bdf
        """
        return str(self.config_file_path(attrib="Iax_BDF"))

    def einj_runner_ce_addr(self):
        """
        This Function is used to fetch Address while Injecting correctable Error
        """
        return str(self.config_file_path(attrib="einj_ce_addr"))

    def acpi_einj_runner_ce_addr(self):
        """
        This Function is used to fetch Address while Injecting correctable Error
        """
        return str(self.config_file_path(attrib="acpi_einj_ce_address"))

    def prime95_execution_time(self):
        """
        This fucntion to get Prime95 Tool execution time from the xml config file
        :return prime95_execution_time
        """
        return int(self.config_file_path(attrib="prime95/H82232_prime95_execution_time"))

    def get_nvme_storage_device(self):
        """
        Function to fetch the attribute values of nvme storage device from the xml configuration file.
        :return: List of the nvme storage device name
        """
        nvme_device_name_list = []
        tags = self.get_content_config()
        var = tags.find(r".//nvme_drive_name")
        for node in var:
            for sub_node in node.iter():
                nvme_device_name_list.append(sub_node.text.strip())
        return nvme_device_name_list

    def get_pcie_nvme_storage_device(self):
        """
        Function to fetch the attribute values of pcie nvme storage device from the xml configuration file.
        :return: List of the nvme storage device name
        """
        nvme_device_name_list = []
        tags = self.get_content_config()
        var = tags.find(r".//nvme_pcie_drive_name")
        for node in var:
            for sub_node in node.iter():
                nvme_device_name_list.append(sub_node.text.strip())
        return nvme_device_name_list

    def get_u2_nvme_storage_device(self):
        """
        Function to fetch the attribute values of u2 nvme storage device from the xml configuration file.
        :return: List of the nvme storage device name
        """
        nvme_device_name_list = []
        tags = self.get_content_config()
        var = tags.find(r".//u2_nvme_drive_name")
        for node in var:
            for sub_node in node.iter():
                nvme_device_name_list.append(sub_node.text.strip())
        return nvme_device_name_list

    def get_nvme_m2_drive_name(self):
        """
        Function to get the nvme m.2 drive name from xml config file.
        """
        return str(self.config_file_path(attrib="storage/nvme_m2_drive_name"))

    def get_sata_m2_drive_name(self):
        """
        Function to get the nvme m.2 drive name from xml config file.
        """
        return str(self.config_file_path(attrib="storage/sata_m2_drive_name"))

    def get_time_to_run_einj_stressapptest(self):
        """
        This function is to get the execution wait time for einj stressapptest"
        """
        return int(self.config_file_path(attrib="wait_time_to_einj_stressapptests"))

    def get_sut1_ip(self):
        """
        This method is Used to get the Sut1 IP for 2 sut Config Test cases from xml config file.
        """
        return self.config_file_path(attrib="sut1_ip")

    def get_sut2_ip(self):
        """
        This Method is Used to get Sut2 Ip for 2 Sut Config Test Cases from xml config file.
        """
        return self.config_file_path(attrib="sut2_ip")

    def get_sut2_usb_to_ethernet_ip(self):
        """
        This Method is Used to Get Ip Address used to Communicate between Host and Sut2.
        """
        return self.config_file_path(attrib="sut2_usb_to_ethernet_ip")

    def get_sut1_ipv6_address(self):
        """
        This Method is Used to Get IPv6 Address of Sut1 from xml Config File.
        """
        return self.config_file_path(attrib="sut1_ipv6")

    def get_sut2_ipv6_address(self):
        """
        This Method is Used to Get IPv6 Address of Sut2 from xml Config File.
        """
        return self.config_file_path(attrib="sut2_ipv6")

    def get_pass_through_device_name_list(self, type=PassThroughAttribute.Network.value):
        """
        This method is to get the Name of device in list which needs to be pass to VM.
        :return devices in List
        """
        try:
            device_names = self.config_file_path(attrib="{}/{}/pass_through_device_name".format(
                RasIoConstant.RasIoVirtualization, type))
            return device_names.split(',')
        except:
            raise content_exceptions.TestFail("Please Content Configuration details for tag name- {}".format(
                "pass_through_device_name"))

    def get_driver_inf_file_name_in_list(self):
        """
        This method is to get the driver file names in list which needs to be installed to VM.
        :return driver names in List
        """
        try:
            driver_file_names = self.config_file_path(attrib="driver_inf_file_name")
            return driver_file_names.split(',')
        except:
            raise content_exceptions.TestFail("Please Content Configuration details for tag name- {}".format(
                "driver_inf_file_name"))

    def get_device_id_name_in_list(self, type=PassThroughAttribute.Network.value):
        """
        This method is to get the device id names in list which needs driver to be installed to VM.
        :return driver names in List
        """
        try:
            driver_file_names = self.config_file_path(attrib="{}/{}/device_id_to_install_driver".format(
                RasIoConstant.RasIoVirtualization, type))
            return driver_file_names.split(',')
        except:
            raise content_exceptions.TestFail("Please check the tag -{}".format(
                "{}/{}/device_id_to_install_driver".format(RasIoConstant.RasIoVirtualization, type)))

    def get_driver_tools_path(self, type=PassThroughAttribute.Network.value):
        """
        Function to get the driver Location path.
        """
        return str(self.config_file_path(attrib="{}/{}/driver_tool_path".format(RasIoConstant.RasIoVirtualization,
                                                                                type)))

    def get_pass_through_device_type(self):
        """
        Function to get device type list for Pass through. ex. nvme, net -type
        """
        try:
            driver_file_names = self.config_file_path(attrib="select_pass_through_type")
            return driver_file_names.split(',')
        except:
            raise content_exceptions.TestFail("Please update the Pass through Card type. eg- NVMe,Net under -{}".format(
                "select_pass_through_type"))

    def get_einj_mem_location_socket(self):
        """
        Function to fetch the attributes value of the socket to inject memory error
        :return: socket in List
        """
        socket = str(self.config_file_path(attrib="einj_mem_location/socket"))
        return socket.split(',')

    def get_einj_mem_location_channel(self):
        """
        Function to fetch the attributes value of the channel to inject memory error
        :return: channel
        """
        channel = str(self.config_file_path(attrib="einj_mem_location/channel"))
        return channel.split(',')

    def get_einj_mem_location_subchannel(self):
        """
        Function to fetch the attributes value of the sun-channel to inject memory error
        :return: sub channel
        """
        sub_channel = str(self.config_file_path(attrib="einj_mem_location/sub_channel"))
        return sub_channel.split(',')

    def get_einj_mem_location_dimm(self):
        """
        Function to fetch the attributes value of the dimm to inject memory error
        :return: dimm
        """
        dimm = str(self.config_file_path(attrib="einj_mem_location/dimm"))
        return dimm.split(',')

    def get_einj_mem_location_rank(self):
        """
        Function to fetch the attributes value of the rank to inject memory error
        :return: rank
        """
        rank = str(self.config_file_path(attrib="einj_mem_location/rank"))
        return rank.split(',')

    def get_ssh_folder_path(self):
        return str(self.config_file_path(attrib="virtualization/ssh_tool_path"))

    def get_memory_core(self):
        """
        This method is to get thread available for the memory to check msrs list.
        :return core
        """
        return int(self.config_file_path(attrib="memory/core"))

    def get_memory_thread(self):
        """
        This method is to get thread available for the memory to check msrs list.
        :return thread
        """
        return int(self.config_file_path(attrib="memory/thread"))

    def get_atf_iso_path(self, os_type):
        """
        Function to get the artifactory iso package path.
        """
        return self.config_file_path(attrib="os_installation/{}/atf_iso_path".format(os_type))

    def collect_io_telemetry_flag(self):
        """
        Function to check does IO-telemetry collection is required to start or not
        :return: (bool) True - to collect, False - not to collect
        """
        return eval(self.config_file_path(attrib="io_telemetry/collect_io_telemetry_flag"))

    def collect_upi_telemetry_flag(self):
        """
        Function to check does UPI-telemetry collection is required to start or not
        :return: (bool) True - to collect, False - not to collect
        """
        return eval(self.config_file_path(attrib="upi_telemetry/collect_upi_telemetry_flag"))

    def get_io_telemetry_csv_path(self):
        """
        Function to return  IO-telemetry csv file path
        :return: csv file path
        """
        return str(self.config_file_path(attrib="io_telemetry/io_telemetry_csv_path"))

    def get_upi_telemetry_csv_path(self):
        """
        Function to return  UPI-telemetry csv file path
        :return: csv file path
        """
        return str(self.config_file_path(attrib="upi_telemetry/upi_telemetry_csv_path"))

    def einj_runner_uce_addr(self):
        """
        This Function is used to fetch Address while Injecting correctable Error
        """
        return str(self.config_file_path(attrib="einj_uce_addr"))

    def get_iwvss_exe_licence_file_name(self):
        """"
        Function to get the iwVSS exe file name and licence key file name from xml config file
        """
        iwvss_file_name = str(self.config_file_path(attrib="memory/iwvss/iwvss_exe_file_name")).strip()
        iwvss_licence_key_file_name = str(self.config_file_path(attrib="memory/iwvss/iwvss_licence_key")).strip()
        return iwvss_file_name, iwvss_licence_key_file_name

    def get_einj_mem_location_sub_rank(self):
        """
        Function to fetch the attributes value of the sub_rank to inject memory error
        :return: sub_rank
        """
        sub_rank = str(self.config_file_path(attrib="einj_mem_location/sub_rank"))
        return sub_rank.split(',')

    def get_einj_mem_location_bank_group(self):
        """
        Function to fetch the attributes value of the bank_group to inject memory error
        :return: bank_group
        """
        bank_group = str(self.config_file_path(attrib="einj_mem_location/bank_group"))
        return bank_group.split(',')

    def get_einj_mem_location_bank(self):
        """
        Function to fetch the attributes value of the bank to inject memory error
        :return: bank
        """
        bank = str(self.config_file_path(attrib="einj_mem_location/bank"))
        return bank.split(',')

    def sandstone_version_number(self):
        """
        This method is used to get sandstone version number
        """
        return int(self.config_file_path(attrib="sandstone_test_version_number"))

    def get_num_of_sandstone_cycles(self):
        """
        Function to get the Number of sandstone reset Cycles from xml config file.
        """
        return int(self.config_file_path(attrib="sandstone_test_reset_number"))

    def get_socket_slot_pcie_errinj(self):
        """
        This method is to get the AER Slot.
        :return List
        """
        tag_info = str(self.config_file_path(attrib="aer_pcie_slot_info/socket"))
        return tag_info.split(",")

    def get_pxp_port_pcie_errinj(self):
        """
        This method is to get the pxp_port.
        :return List
        """
        tag_info = str(self.config_file_path(attrib="aer_pcie_slot_info/pxp_port"))
        return tag_info.split(",")

    def get_cr_stepping_from_config(self):
        """
        Function to get the CR stepping from the xml config file.
        """
        return str(self.config_file_path(attrib="memory/cr_dimm_stepping"))

    def get_sql_powerbi_config_flag(self):
        """
        Function to check does sql collection is required to start or not
        :return: (bool) True - to collect, False - not to collect
        """
        return eval(self.config_file_path(attrib="sql_powerbi_config/start_sql_connection"))

    def get_subsystem_name(self):
        """
        Function to get the subsystem Name
        :return: (str)  - Subsystem Name
        """
        return str(self.config_file_path(attrib="sql_powerbi_config/subsystem_name"))

    def get_mysql_powerbi_host(self):
        """
        Function to get mysql host
        :return: (str) host address
        """
        return self.config_file_path(attrib="sql_powerbi_config/mysql_host")

    def get_mysql_powerbi_user(self):
        """
        Function to get mysql user name
        :return: (str) user name
        """
        return str(self.config_file_path(attrib="sql_powerbi_config/mysql_user"))

    def get_mysql_powerbi_pwd(self):
        """
              Function to get mysql password
              :return: (str) password
              """
        return str(self.config_file_path(attrib="sql_powerbi_config/mysql_pwd"))

    def get_mysql_powerbi_db(self):
        """
              Function to get mysql dbname
              :return: (str) dbname
              """
        return str(self.config_file_path(attrib="sql_powerbi_config/mysql_db_name"))

    def get_mysql_powerbi_tablename(self):
        """
        Function to get mysql tablename
        :return: (str) tablename
        """
        return self.config_file_path(attrib="sql_powerbi_config/mysql_table_name")

    def get_rdt_script_path(self):
        """
        Function to get the rdt script path
        :return: the path of the script
        """
        return str(self.config_file_path(attrib="RDT/script_path"))

    def get_hbm_memory_per_socket_config(self):
        """
        This Function is used to get the HBM memory per socket from the config xml
        """
        return int(self.config_file_path(attrib="hbm_memory_per_socket"))

    def get_socwatch_tool_name_config(self, sut_os):
        """
        Function to get socwtach tool name from xml config file.
        """
        return str(self.config_file_path(attrib="socwatch/{}".format(sut_os)))

    def get_pcie_bridge_values(self):
        """
        This method is to get the PCIe Bridge Values.
        :return List
        """
        try:
            tag_info = str(self.config_file_path(attrib="einj_pcie_bridge_values"))
            return tag_info.split(",")
        except Exception as ex:
            raise RuntimeError("Please update the proper PCIe Cards bridge value in the content_configuration.xml, "
                               "for supporting readme doc go to src/ras/tests/einj_tests/README.md")

    def get_git_repo_name(self):

        """
        Function to get the git repo name from content configuration
        :return: return the repo str
        """
        return str(self.config_file_path(attrib="accelerator/repo_name"))

    def get_access_token(self):

        """
        Function to get the personal access token from content configuration
        :return: return the access token str
        """
        return str(self.config_file_path(attrib="accelerator/access_token"))

    def get_mlc_tool_path(self):
        """
        Function to get Mlc stress tool name from xml config file.
        """
        return self.config_file_path(attrib="tools/mlc_stress_file")

    def get_mlc_exec_iterations(self):
        """
        Function to get num iterations
        """
        return int(self.config_file_path(attrib="tools/mlc_iterations"))

    def get_ltssm_debug_tool_provider(self):
        """
        Function to get the name of the ltssm provider that will run ltssm tests
        :return: ltssm provider name (i.e.: cscripts)
        """
        ltssm_debug_tool_provider = str(self.config_file_path(attrib="pcie/debug_tool_provider")).strip()
        return ltssm_debug_tool_provider

    def get_ltssm_test_list(self):
        """
        Function to get the name of ltssm tests to run
        :return: list with ltssm test names
        """
        ltssm_test_list = str(self.config_file_path(attrib="pcie/ltssm_test_list"))
        return ltssm_test_list.split(',')

    def get_bifurcation_slots_details_dict(self):
        """
        This method is to get the list of slot (Bifurcation) from content config.
        :return:  dict - eg:- { 's1_pxp1': {'bifurcation': 'x4x4x4x4', 'socket': 1, 'pxp': 1, port_0: {'speed': 16,
        'width': 8}, port_1: {'speed': 16, 'width': 8}, port_2: {'speed': 16, 'width': 8},
        port_3: {'speed': 16, 'width': 8}}
        """
        socket_pxp_name_list = str(self.config_file_path(attrib=
                                                         "pcie/pcie_slots_bifurcation/socket_pxp_name")).split(',')
        bifurcation_list = str(self.config_file_path(attrib="pcie/pcie_slots_bifurcation/bifurcation")).split(',')
        speed_list = str(self.config_file_path(attrib="pcie/pcie_slots_bifurcation/speed")).split(',')
        width_list = str(self.config_file_path(attrib="pcie/pcie_slots_bifurcation/width")).split(',')
        bif_slot_dict = {}
        for pxp_name, bifurcation, speed, width in zip(socket_pxp_name_list, bifurcation_list, speed_list, width_list):
            each_pxp_dict = {}
            each_pxp_dict['bifurcation'] = bifurcation
            socket_number = pxp_name.split('_')[0].replace('s', '')
            pxp_number = pxp_name.split('_')[1].replace('pxp', '')
            each_pxp_dict['socket'] = socket_number
            each_pxp_dict['pxp'] = pxp_number
            no_of_port = bifurcation.count('x')
            each_slot_bifurcation_list = bifurcation.split('x')

            for index in range(no_of_port):

                each_pxp_dict['port_{}'.format(index)] = \
                    {'speed': speed.split('-')[no_of_port - index - 1],
                     'width': width.split('-')[no_of_port - index - 1],
                     'bifurcated': "x" + each_slot_bifurcation_list[no_of_port - index]
                     }

            bif_slot_dict[pxp_name] = each_pxp_dict
        self._log.debug("Slot details from Content Config - {}".format(bif_slot_dict))
        return bif_slot_dict

    def get_pcie_bifurcation_auto_discovery(self):
        """
        This method is to get the Flag to enable Auto discovery.
        """
        try:
            return eval(self.config_file_path(attrib="pcie/pcie_slots_bifurcation/pcie_bifurcation_auto_discovery"))
        except Exception as ex:
            return ""

    def get_process_terminate_list(self):
        """
        Function to get a list of processes to terminate
        :return: list with process names
        """
        try:
            process_list = str(self.config_file_path(attrib="host_process/terminate_list"))
            return process_list.split(',')
        except AttributeError:
            pass

    def pei_card_err_type(self):
        """
        Function to get the error type to be injected through pei card.
        """
        return str(self.config_file_path(attrib="pcie/pei_card/err_type"))

    def get_micro_code_file_path(self):
        """
        Function to get the micro code file path on host
        :return: .pdb file path
        """
        return str(self.config_file_path(attrib="micro_code_file_path"))

    def get_driver_folder_path(self):
        """
        Function to get the driver Location path.
        """
        return str(self.config_file_path(attrib="virtualization/driver_tool_path"))

    def get_tboot_file_path(self):
        """
        Function to get the tboot file path and sinit.bin file path on host
        :return: tboot file path and sinit.bin file path
        """
        tboot_zip_file_path = str(self.config_file_path(attrib="TBOOT/tboot_zip"))
        tboot_sinit_bin_file = str(self.config_file_path(attrib="TBOOT/sinit_bin_file"))
        return tboot_zip_file_path, tboot_sinit_bin_file

    def get_num_of_sockets(self):
        """
        Function to get the number of sockets system is having
        :return: no of sockets the system is having
        """
        return str(self.config_file_path(attrib="common/num_of_sockets"))

    def get_kernel_version(self):
        """
        This method is to get the kernel version user wants to boot
        """
        return str(self.config_file_path(attrib="kernel_version_to_boot"))

    def get_usb_name_memtest86(self):
        """
        This method used to get the usb name for memtest86
        """
        return str(self.config_file_path(attrib="memory_hbm/pi_memory_hbm_mode_memtest/usb_name"))

    def get_usb_size_memtest86(self):
        """
        This method used to get the usb name for memtest86
        """
        return self.config_file_path(attrib="memory_hbm/pi_memory_hbm_mode_memtest/usb_size")

    def get_accel_config_version(self):
        """
        This method used to get the version number of accel config tool from content_configuration file.
        :return: return the version number
        """
        return str(self.config_file_path(attrib="accelerator/version"))

    def get_ssd_device_model_details(self):
        """
        Function to get the storage Sata drive manufacturer and Model Number from xml config file.

        return list
        raise:None
        """
        return {"device": str(self.config_file_path(attrib="storage/SSD/device")),
                "model": str(self.config_file_path(attrib="storage/SSD/model_number"))}

    def get_intelmastool_path(self):
        """
       This method used to get the version number of accel config tool from content_configuration file.
       :return: return the version number
       """
        return str(self.config_file_path(attrib="storage/intelmastool_path"))

    def get_usb_device_name(self):
        """
        Function to get the usb device name.
        """
        return self.config_file_path(attrib="virtualization/usb_device_name")

    def get_security_mktme_params(self, sut_os):
        """Function to get the information for MKTME for a specific OS.
        :param sut_os: OS type (Linux, Windows, ESXi)
        :type: str
        :return: dict of all entries in TDX/$OS
        :rtype: dict"""
        temp_dict = {}
        tags = self.get_content_config()
        var = tags.find(r"./security/mktme/{}".format(sut_os.lower()))
        for node in var:
            for sub_node in node.iter():
                temp_dict[sub_node.tag] = sub_node.text.strip()
        return temp_dict

    def is_container_env(self):
        """
        bool: Function to determine if the environment is in a container
        """
        try:
            return eval(self.config_file_path(attrib="is_container_env"))
        except AttributeError:
            return False

    def get_reset_count(self):
        """
        This method used to get the no of cold/warm resets cycles required from content_configuration file.
        :return: return the reset cycle count
        """
        return int(self.config_file_path(attrib="storage/reset_count"))

    def get_timeout_for_powercycles(self):
        """
        This method used to get the timeout value required for startup.nsh to complete 100 cycles
         from content_configuration file.
        :return: return the time in seconds
        """
        return int(self.config_file_path(attrib="storage/timeout_in_secs"))

    def get_cpu_device_id(self):
        """
        Function to fetch the CPU device-id from the xml configuration file.

        :return: Values of the attributes in string type.
        """

        return str(self.config_file_path(attrib="pcie/device_driver_map/CPU/device_id"))

    def get_pch_device_id(self):
        """
        Function to fetch the pch device-id from the xml configuration file.

        :return: Values of the attributes in string type.
        """

        return str(self.config_file_path(attrib="pcie/device_driver_map/PCH/device_id"))

    def get_xhci_device_id(self):
        """
        Function to fetch the xhci device-id from the xml configuration file.

        :return: Values of the attributes in string type.
        """

        return str(self.config_file_path(attrib="pcie/device_driver_map/XHCI/device_id"))

    def get_sata_device_id(self):
        """
        Function to fetch the sata device-id from the xml configuration file.

        :return: Values of the attributes in string type.
        """

        return str(self.config_file_path(attrib="pcie/device_driver_map/SATA/device_id"))

    def get_me_device_id(self):
        """
        Function to fetch the me device-id from the xml configuration file.

        :return: Values of the attributes in string type.
        """

        return str(self.config_file_path(attrib="pcie/device_driver_map/ME/device_id"))

    def get_lpc_espi_device_id(self):
        """
        Function to fetch the lpc_espi device-id from the xml configuration file.

        :return: Values of the attributes in string type.
        """

        return str(self.config_file_path(attrib="pcie/device_driver_map/LPC_ESPI/device_id"))

    def get_smbus_device_id(self):
        """
        Function to fetch the smbus device-id from the xml configuration file.

        :return: Values of the attributes in string type.
        """

        return str(self.config_file_path(attrib="pcie/device_driver_map/SMBUS/device_id"))

    def get_spi_device_id(self):
        """
        Function to fetch the spi device-id from the xml configuration file.

        :return: Values of the attributes in string type.
        """

        return str(self.config_file_path(attrib="pcie/device_driver_map/SPI/device_id"))

    def get_ethernet_device_id(self):
        """
        Function to fetch the ethernet device-id from the xml configuration file.

        :return: Values of the attributes in string type.
        """

        return str(self.config_file_path(attrib="pcie/device_driver_map/ETHERNET/device_id"))

    def get_ethernet_kernel_driver(self):
        """
        Function to fetch the ethernet kernel driver from the xml configuration file.

        :return: Values of the attributes in string type.
        """

        return str(self.config_file_path(attrib="pcie/device_driver_map/ETHERNET/driver"))

    def get_ahci_device_id(self):
        """
        Function to fetch the ahci device-id from the xml configuration file.

        :return: Values of the attributes in string type.
        """

        return str(self.config_file_path(attrib="pcie/device_driver_map/AHCI/device_id"))

    def get_device_driver_from_config(self):
        """
        Function to decide does device-id needs to be fetched from config file

        :return: Values of the attributes in boolean type.
        """

        return eval(self.config_file_path(attrib="pcie/device_driver_map/config_device_driver"))

    def get_burnin_test_runtime(self):
        """
        This method is to get the execution time of the burning test for storage devices.
        return:burnin_test_runtime
        """
        return int(self.config_file_path(attrib="storage/burnin_test_runtime"))

    def get_ssd_serial_number(self):
        """
        Function to fetch the ssd serial number

        :return: return ssd serial number
        """
        return str(self.config_file_path(attrib="ssdfw/serial_number"))

    def get_ssd_fw_version(self):
        """
        Function to fetch the ssd fw version

        :return: return ssd fw version
        """
        return str(self.config_file_path(attrib="ssdfw/fw_version"))

    def get_ssd_fw_file_path(self):
        """
        Function to fetch the ssd fw file path

        :return: return ssd fw file path
        """
        return str(self.config_file_path(attrib="ssdfw/fw_file_path"))

    def get_fio_cmd(self):
        """
        Function to fetch the fio command to execute in sut

        :return: return fio command
        """
        return str(self.config_file_path(attrib="ssdfw/fio_cmd"))

    def get_drive_letter(self):
        """
        Function to fetch the ssd drive letter

        :return: return drive letter
        """
        return str(self.config_file_path(attrib="ssdfw/drive_letter"))

    def get_win_vm_name(self):
        """
        Function to fetch the windows vm name

        :return: return windows vm name
        """
        return str(self.config_file_path(attrib="ssdfw/win_vm_name"))

    def get_vm_artifactory_link(self):
        """
        Function to fetch the vm artifactory link

        :return: return vm artifactory link
        """
        return str(self.config_file_path(attrib="ssdfw/vm_artifactory_link"))

    def get_iometer_tool_path(self):
        """
        Function to fetch the iometer tool path
        :return: return iometer tool path
        """
        return str(self.config_file_path(attrib="ssdfw/iometer_tool_path"))

    def get_vroc_key_info(self):
        """
        This method is to get the VROC key details from content config file.
        return:Premium/Standard/Intel
        """
        return str(self.config_file_path(attrib="storage/hw_vroc_key_type"))

    def get_workload_time(self):
        """
        Function to get the timeout value for rebooting from the xml config file.
        """
        return int(self.config_file_path(attrib="interop/workload_runtime"))

    def get_kickstart_file_name_centos(self):
        """
        Function to get the kickstart file from  xml config file.
        """
        try:
            return str(self.config_file_path(attrib="virtualization/linux/CENTOS/kickstart_file_name"))
        except Exception as ex:
            return "linux_vm_centos_kstart.cfg"


    def get_iperf_tool_path(self):
        """
        Function to get the iperf tool path from  xml config file.
        """
        return str(self.config_file_path(attrib="iperf_tool"))


    def get_port_number_for_vm(self):
        """
        Function to get the timeout value for rebooting from the xml config file.
        """
        return self.config_file_path(attrib="interop/port_number_vm")

    def get_fisher_port_number_for_err_injection(self):
        """
        Function to get the timeout value for rebooting from the xml config file.
        """
        return self.config_file_path(attrib="interop/fisher_port_number")

    def get_iometer_tool_config_file_name(self):
        """
        Function to get iometer config file tool name from xml config file.
        :param: sut_os: OS Type
        :return: config file name for IOMeter
        """
        try:
            return self.config_file_path(attrib="iometer_tool_configfile")
        except Exception as ex:
            return "iometer_configfile.icf"

    def get_proxy_server_ref(self):
        try:
            return str(self.config_file_path(attrib="virtualization/proxy_server"))
        except Exception as ex:
            return ""

    def get_proxy_server_vm_ref(self):
        try:
            return str(self.config_file_path(attrib="virtualization/proxy_server_vm"))
        except Exception as ex:
            return ""

    def update_repo_files_for_centos(self):
        try:
            return str(self.config_file_path(attrib="virtualization/update_repo_files_for_centos"))
        except Exception as ex:
            return str("False")    

    def get_cpu_stress_enabled(self):
        """
        This method is used to get the cpu stress domain/feature activation indication from content_configuration file.
        :return: return True/False
        """
        return str(self.config_file_path(attrib="cpu_stress_enabled"))

    def get_memory_stress_enabled(self):
        """
        This method is used to get the memory stress domain/feature activation indication from content_configuration file.
        :return: return True/False
        """
        return str(self.config_file_path(attrib="memory_stress_enabled"))

    def get_network_enabled(self):
        """
        This method is used to get the network traffic domain/feature activation indication from content_configuration file.
        :return: return True/False
        """
        return str(self.config_file_path(attrib="network_enabled"))

    def get_storage_enabled(self):
        """
        This method is used to get the storage domain/feature activation indication from content_configuration file.
        :return: return True/False
        """
        return str(self.config_file_path(attrib="storage_enabled"))

    def get_qat_enabled(self):
        """
        This method is used to get the qat domain/feature activation indication from content_configuration file.
        :return: return True/False
        """
        return str(self.config_file_path(attrib="qat_enabled"))

    def get_dlb_enabled(self):
        """
        This method is used to get the dlb domain/feature activation indication from content_configuration file.
        :return: return True/False
        """
        return str(self.config_file_path(attrib="dlb_enabled"))

    def get_dsa_enabled(self):
        """
        This method is used to get the dsa domain/feature activation indication from content_configuration file.
        :return: return True/False
        """
        return str(self.config_file_path(attrib="dsa_enabled"))

    def get_iaa_enabled(self):
        """
        This method is used to get the iaa domain/feature activation indication from content_configuration file.
        :return: return True/False
        """
        return str(self.config_file_path(attrib="iaa_enabled"))

    def get_cps_enabled(self):
        """
        This method is used to get the cps domain/feature activation indication from content_configuration file.
        :return: return True/False
        """
        return str(self.config_file_path(attrib="cps_enabled"))

    def get_cxl_enabled(self):
        """
        This method is used to get the cxl domain/feature activation indication from content_configuration file.
        :return: return True/False
        """
        return str(self.config_file_path(attrib="cxl_enabled"))

    def get_sgx_enabled(self):
        """
        This method is used to get the sgx domain/feature activation indication from content_configuration file.
        :return: return True/False
        """
        return str(self.config_file_path(attrib="sgx_enabled"))

    def get_tdx_enabled(self):
        """
        This method is used to get the tdx domain/feature activation indication from content_configuration file.
        :return: return True/False
        """
        return str(self.config_file_path(attrib="tdx_enabled"))

    def get_tmul_enabled(self):
        """
        This method is used to get the tmul domain/feature activation indication from content_configuration file.
        :return: return True/False
        """
        return str(self.config_file_path(attrib="tmul_enabled"))

    def get_ras_enabled(self):
        """
        This method is used to get the ras domain/feature activation indication from content_configuration file.
        :return: return True/False
        """
        return str(self.config_file_path(attrib="ras_enabled"))

    def get_pm_enabled(self):
        """
        This method is used to get the pm domain/feature activation indication from content_configuration file.
        :return: return True/False
        """
        return str(self.config_file_path(attrib="pm_enabled"))

    def get_saf_enabled(self):
        """
        This method is used to get the saf domain/feature activation indication from content_configuration file.
        :return: return True/False
        """
        return str(self.config_file_path(attrib="saf_enabled"))

    def get_seamless_enabled(self):
        """
        This method is used to get the seamless domain/feature activation indication from content_configuration file.
        :return: return True/False
        """
        return str(self.config_file_path(attrib="seamless_enabled"))

    def get_uram_enabled(self):
        """
        This method is used to get the uram domain/feature activation indication from content_configuration file.
        :return: return True/False
        """
        return str(self.config_file_path(attrib="uram_enabled"))

    def get_nic_interface_name_sut(self):
        """
        This method is used to get the nic interface name of sut from content_configuration file.
        :return: return the sut nic interface name
        """
        return str(self.config_file_path(attrib="nic_interface_name_sut"))

    def get_nic_interface_name_peer(self):
        """
                This method is used to get the nic interface name of peer from content_configuration file.
                :return: return the peer nic interface name
                """
        return str(self.config_file_path(attrib="nic_interface_name_peer"))

    def get_static_ip_sut(self):
        """
        This method is used to get the static ip of sut from content_configuration file.
        :return: return the sut static ip
        """
        return str(self.config_file_path(attrib="static_ip_sut"))

    def get_static_ip_peer(self):
        """
        This method is used to get the static ip of peer from content_configuration file.
        :return: return the peer static ip
        """
        return str(self.config_file_path(attrib="static_ip_peer"))
    def get_duration_iperf_op(self):
        """
        This method is used to get the output interval duration of iperf from content_configuration file.
        :return: return the interval duration of iperf output
        """
        return str(self.config_file_path(attrib="duration_iperf_op"))


    def get_parallel_thread_count(self):

        """
        This method is used to get the thread count for iperf from content_configuration file.
        :return: return the iperf parallel thread count
        """
        return str(self.config_file_path(attrib="parallel_thread_count"))

    def get_peer_host_name(self):

        """
        This method is used to get the host name of peer from content_configuration file.
        :return: return the iperf host name
        """
        return str(self.config_file_path(attrib="peer_host_name"))

    def get_peer_user_name(self):

        """
        This method is used to get the user name of peer from content_configuration file.
        :return: return the peer user name
        """
        return str(self.config_file_path(attrib="peer_user_name"))

    def get_peer_password(self):

        """
        This method is used to get the password of peer from content_configuration file.
        :return: return the  peer password
        """
        return str(self.config_file_path(attrib="peer_password"))

    def get_random_cycles(self):

        """
        This method is used to get the random cycles for LTSSM test from content_configuration file.
        :return: return the LTSSM random cycles
        """
        return str(self.config_file_path(attrib="random_cycles"))

    def get_bus_value_of_the_PCIe_device_width_speed(self):

        """
        This method is used to get the bus value of the PCIe device from content_configuration file.
        :return: return the bus value of the PCIe device width speed
        """
        return str(self.config_file_path(attrib="bus_value_of_the_PCIe_device_width_speed"))

    def get_accelerator_error_strings(self):
        """
        Function to fetch the attribute values of accelerator error strings from the xml configuration file.
        :return: List of the accelerator error strings name
        """
        error_str_list = []
        tags = self.get_content_config()
        var = tags.find(r"./interop/error_string")
        for node in var:
            for sub_node in node.iter():
                error_str_list.append(sub_node.text.strip())
        return error_str_list

    def artifactory_tool_overwrite(self):
        """
        Function obtains the boolean value to overwrite existing tool found on host with version found on Artifactory
        :return: Boolean value or empty string if parameter does not exist
        """
        try:
            return eval(self.config_file_path(attrib="common/artifactory_tool_overwrite"))
        except Exception as ex:
            return ""

    def get_sgx_properties_params(self) -> dict:
        """Function to get the information for SGX.
        :return: return dict of all entries in SGX section.
        """
        tags = self.get_content_config()
        sgx_tag = tags.find(r"./security/SGX")
        sgx_properties = [elem for elem in sgx_tag.iter()]
        sgx_property_params = {}
        for properties in sgx_properties:
            if properties.text:
                sgx_property_params[properties.tag] = properties.text.strip()
        return sgx_property_params

    def get_pcie_ltssm_auto_discovery(self):
        """
        Function obtains the boolean value to use auto-discovery of PCIe endpoints for LTSSM testing
        :return: Boolean value or empty string if parameter does not exist
        """
        try:
            return eval(self.config_file_path(attrib="pcie/pcie_ltssm_auto_discovery"))
        except Exception as ex:
            return ""

    def get_dimm_population_for_1dps(self):
        """
        This method is to get the 1DPS dimm position from content config file.
        return:Premium/Standard/Intel
        """
        return str(self.config_file_path(attrib="multisocket/dps_configuration"))

    def get_gen3_present(self):
        """
        This method is used to get the gen3 availability details from content_configuration file.
        :return: return yes/no.
        """

        return str(self.config_file_path(attrib="gen3_present"))

    def get_gen3_bdf_values(self):
        """
        This method is used to get the gen3 bdf details from content_configuration file.
        :return: return bdf value.
        """

        return str(self.config_file_path(attrib="gen3_bdf_values"))

    def get_gen3_type(self):
        """
        This method is used to get the gen3 type details from content_configuration file.
        :return: return network/storage.
        """

        return str(self.config_file_path(attrib="gen3_type"))

    def get_gen3_storage_device_name(self):
        """
        This method is used to get the gen3 storage device details from content_configuration file.
        :return: return gen3_storage_device name.
        """

        return str(self.config_file_path(attrib="gen3_storage_device_name"))

    def get_gen4_present(self):
        """
        This method is used to get the gen4 availability details from content_configuration file.
        :return: return yes/no.
        """

        return str(self.config_file_path(attrib="gen4_present"))

    def get_gen4_bdf_values(self):
        """
        This method is used to get the gen3 bdf details from content_configuration file.
        :return: return bdf value.
        """

        return str(self.config_file_path(attrib="gen4_bdf_values"))

    def get_gen4_type(self):
        """
        This method is used to get the gen4 type details from content_configuration file.
        :return: return network/storage.
        """

        return str(self.config_file_path(attrib="gen4_type"))

    def get_gen4_storage_device_name(self):
        """
        This method is used to get the gen4 storage device details from content_configuration file.
        :return: return gen4_storage_device name.
        """

        return str(self.config_file_path(attrib="gen4_storage_device_name"))

    def get_gen5_present(self):
        """
        This method is used to get the gen5 availability details from content_configuration file.
        :return: return yes/no.
        """

        return str(self.config_file_path(attrib="gen5_present"))

    def get_gen5_bdf_values(self):
        """
        This method is used to get the gen5 bdf details from content_configuration file.
        :return: return bdf value.
        """

        return str(self.config_file_path(attrib="gen5_bdf_values"))

    def get_gen5_type(self):
        """
        This method is used to get the gen5 type details from content_configuration file.
        :return: return network/storage.
        """

        return str(self.config_file_path(attrib="gen5_type"))

    def get_gen5_storage_device_name(self):
        """
        This method is used to get the gen5 storage device details from content_configuration file.
        :return: return gen5_storage_device name.
        """

        return str(self.config_file_path(attrib="gen5_storage_device_name"))

    def get_gen_nic_interface_name_sut(self):
        """
        This method is used to get the gen interface name of sut details from content_configuration file.
        :return: return gen5_storage_device name.
        """

        return str(self.config_file_path(attrib="gen_nic_interface_name_sut"))

    def get_gen_nic_interface_name_peer(self):
        """
        This method is used to get the gen interface name of sut details from content_configuration file.
        :return: return gen5_storage_device name.
        """

        return str(self.config_file_path(attrib="gen_nic_interface_name_peer"))

    def get_gen_static_ip_sut(self):
        """
        This method is used to get the gen static ip of sut details from content_configuration file.
        :return: return gen sut static ips.
        """

        return str(self.config_file_path(attrib="gen_static_ip_sut"))

    def get_gen_static_ip_peer(self):
        """
        This method is used to get the gen static ips of peer details from content_configuration file.
        :return: return gen peer static ips.
        """

        return str(self.config_file_path(attrib="gen_static_ip_peer"))

    def get_ipmctl_tool_path_centos_zip(self):
        """
        Function to fetch the ipmctl tool path (centos zip)  path
        :return: return ipmctl tool path (centos zip)  path
        """
        return str(self.config_file_path(attrib="pmem/ipmctl_tool_path_centos_zip"))

    def get_ipmctl_tool_path_windows_zip(self):
        """
        Function to fetch the ipmctl tool path (windows zip)  path
        :return: return ipmctl tool path (windows zip)  path
        """
        return str(self.config_file_path(attrib="pmem/ipmctl_tool_path_windows_zip"))

    def get_nvdimmutil_tool_path_windows_zip(self):
        """
        Function to fetch the ipmctl tool path (windows zip)  path
        :return: return ipmctl tool path (windows zip)  path
        """
        return str(self.config_file_path(attrib="pmem/nvdimmutil_tool_path_windows_zip"))

    def get_windows_sut_root_path(self):
        """
        Function to fetch the windows working directory path in sut
        :return: return windows working directory path in sut
        """
        return str(self.config_file_path(attrib="pmem/windows_sut_root_path"))

    def get_ipmctl_tool_file(self):
        """
        Function to fetch the windows working directory path in sut
        :return: return windows working directory path in sut
        """
        return str(self.config_file_path(attrib="pmem/ipmctl_tool_file"))

    def get_dsa_tool_file_path(self):
        """
        Function to fetch the windows dsa tool path
        :return: return windows working directory path in host
        """
        return str(self.config_file_path(attrib="dsa/dsa_tool_file_path"))

    def get_ptu_lin_tool_file_path(self):
        """
        Function to fetch the ptu linux tool path
        :return: return ptu linux tool path
        """
        return str(self.config_file_path(attrib="pm/ptu_lin_tool_file_path"))

    def get_ptu_win_tool_file_path(self):
        """
        Function to fetch the ptu Windows tool path
        :return: return ptu Windows tool path
        """
        return str(self.config_file_path(attrib="pm/ptu_win_tool_file_path"))

    def get_ezfio_tool_path(self):
        """
        Function to fetch the windows working directory path in sut
        :return: return windows working directory path in sut
        """
        return str(self.config_file_path(attrib="pmem/ezfio_tool_path"))

    def get_socwatch_lin_tool_file_path(self):
        """
        Function to fetch the socwatch Windows tool path
        :return: return socwatch Windows tool path
        """
        return str(self.config_file_path(attrib="pm/socwatch_lin_tool_file_path"))

    def get_socwatch_win_tool_file_path(self):
        """
        Function to fetch the socwatch Windows tool path
        :return: return socwatch Windows tool path
        """
        return str(self.config_file_path(attrib="pm/socwatch_win_tool_file_path"))
    
    def get_pmutil_snoozetime(self):
        """
        This method is used to get the snooze interval for pmutil from content_configuration file.
        :return: return the harsser snooze interval in seconds
        """
        return str(self.config_file_path(attrib="pmutil_snoozetime"))


    def get_target_bus_list(self):
        """
        Gets target bus numbers for IO stress of target device. eg: 0x38,0x98
        """
        val = str(self.config_file_path(attrib="pcie/io_stress/target_bus")).lower().strip()
        if val == "auto":
            return val
        else:
            return val.split(',')

    def get_ptg_target_address(self):
        """
        Gets the address to feed in the PTG tool.
        """
        return str(self.config_file_path(attrib="pcie/io_stress/ptg/address"))

    def get_stress_runtime(self):
        """
        Runtime for all IO stress tests in seconds. Recommended - 6-8 hours -> 21600 to 28800
        """
        return str(self.config_file_path(attrib="pcie/io_stress/runtime"))

    def get_ptg_pattern_runtime(self):
        """
        Runtime of a single test pattern in seconds. Recommended - 10 seconds
        """
        return str(self.config_file_path(attrib="pcie/io_stress/ptg/each_pattern_runtime"))

    def get_sut_path_linux(self):
        """
        This function is used for finding the dsa in sut linux
        """
        return str(self.config_file_path(attrib="dsa/sut_path_linux"))

    def get_dsa_file_name_pmem(self):
        """
        This function is used for finding dsa file name in sut
        """
        return str(self.config_file_path(attrib="dsa/dsa_file_name_pmem"))

    def get_dsa_timeout(self):
        """
        This function is used for dsa execution timeout
        """
        return str(self.config_file_path(attrib="dsa/dsa_timeout"))
