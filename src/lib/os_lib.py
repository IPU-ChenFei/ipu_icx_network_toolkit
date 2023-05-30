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
from src.lib.content_configuration import ContentConfiguration
from src.lib.common_content_lib import CommonContentLib


class WindowsCommonLib:
    """
    This class implements has common functions which can used across the windows platforms.
    """

    SYSTEM_INFO_CMD = "Systeminfo"

    def __init__(self, log, os_obj):
        self._log = log
        self._os = os_obj

        self._common_content_configuration = ContentConfiguration(self._log)
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        self._command_timeout = self._common_content_configuration.get_command_timeout()

        self._common_content_lib = CommonContentLib(self._log, self._os, None)

    def get_system_memory(self):
        """
        This function is used to parse the total physical memory from System info

        :return: total memory value
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
        self._log.info("The Amount of Memory reported by the OS is : {}".format(memory_total_value[0].strip()))

        memory_free_value = re.findall("Available Physical Memory:.*", cmd_result.stdout)
        if not memory_free_value:
            raise RuntimeError("Failed to get the Total Memory Value from System Info")
        self._log.info("The Amount of Memory reported by the OS is : {}".format(memory_free_value[0].strip()))
        system_info_list = [memory_total_value[0].strip(), memory_free_value[0].strip()]
        return system_info_list

    def set_power_scheme(self, option=None):
        """
        This function is used to check the current power scheme and can set to required scheme.

        :param option: takes the power option to set.
        :return: true if power scheme is set as expected else false.
        """

        power_value = False
        hp_option = None

        pwr_list_options = self._common_content_lib.execute_sut_cmd("powercfg -list", "power options",
                                                                    self._command_timeout)
        pwr_list = pwr_list_options.strip().split("\n")

        re_pwr_pattern = "(.*){}(.*)".format(option)

        for line_pwr_options in pwr_list:
            if re.search(re_pwr_pattern, line_pwr_options, re.IGNORECASE):
                hp_option = line_pwr_options.split(":")[1].split()[0].strip()

        self._common_content_lib.execute_sut_cmd("powercfg -setactive {}".format(hp_option),
                                                 "power option set", self._command_timeout)

        pwr_result = self._common_content_lib.execute_sut_cmd("powercfg /getactivescheme", "get current power scheme",
                                                              self._command_timeout)

        self._log.info("The current {}".format(pwr_result))

        if re.search(re_pwr_pattern, pwr_result, re.IGNORECASE):
            power_value = True

        if not power_value:
            err_log = "Power scheme has not been set correctly..."
            self._log.error(err_log)
            raise RuntimeError(err_log)

        return power_value

    def screen_awake_settings(self):
        """
        The function is used to make the system not to go to screen saver or to sleep or to blank screen.

        :return: None
        """
        list_awake_setting = ["powercfg -change -monitor-timeout-dc 0", "powercfg -change -standby-timeout-dc 0",
                              "powercfg -change -standby-timeout-ac 0", "powercfg -change -monitor-timeout-ac 0"]

        for power_option in list_awake_setting:
            self._common_content_lib.execute_sut_cmd(power_option, "set screen awake settings",
                                                     self._command_timeout)

            self._log.info("Power options '{}' has been set correctly...".format(power_option))

    def task_manager_wmic_mem_get(self, task_option=None, list_option=False):
        """
        This function is used to get the memory information from Task manager.

        :param task_option: this can be any parameter like "BankLabel,DeviceLocator,Capacity,Tag"
        :param list_option: to get the info in list
        :return: get_task_str: memory information of the specified parameter
        """
        get_task = self._common_content_lib.execute_sut_cmd("wmic MEMORYCHIP get {}".format(task_option), "Mem info",
                                                            self._command_timeout)

        if list_option:
            get_task_str = list(map(str, get_task.strip().split("\n")))
        else:
            get_task_str = "".join(map(str, get_task.strip().split("\n")))

        self._log.info("The memory chip info {}".format(get_task_str))
        return get_task_str

    def task_manager_wmic_cpu_get(self, task_option=None):
        """
        This function is used to get the cpu load information from Task manager.

        :param task_option: this can be any parameter like "caption,Name,NumberOfCores,NumberOfLogicalProcessors"
        :return: get_task_str: cpu information of the specified parameter
        """
        get_task = self._common_content_lib.execute_sut_cmd("wmic cpu get {}".format(task_option), "get cpu load info",
                                                            self._command_timeout)

        get_task_str = "".join(map(str, get_task.strip().split("\n")))

        self._log.info("The cpu info {}".format(get_task_str))
        return get_task_str

    def task_manager_wmic_baseboard_get(self, task_option=None):

        """
        This function is used to get the baseboard product information from Task manager.

        :param task_option: this can be any parameter like "platform"
        :return: get_task_str: baseboard product information of the specified parameter
        """
        get_task = self._common_content_lib.execute_sut_cmd("wmic baseboard get {}".format(task_option),
                                                            "get baseboard info",
                                                            self._command_timeout)

        get_task_str = "".join(map(str, get_task.strip().split("\n")))

        self._log.info("The baseboard {}".format(get_task_str))
        return get_task_str

    def device_manager_devicelist(self):
        """
        This function gets the device list and their related conditions from Windows DeviceManager.

        :return device_status_dict: dictionary of the devices and their current status
        """
        device_status_dict = {}
        clean_string = lambda x: x.strip()
        raw_output = self._common_content_lib.execute_sut_cmd("wmic path win32_pnpentity get caption,"
                                                              "ConfigManagerErrorCode", "DeviceManager List",
                                                              self._command_timeout)
        self._log.debug("Device Manager list:\n{}".format(raw_output))
        device_list = [clean_string(device) for device in raw_output.splitlines() if clean_string(device) != '']
        for dev in device_list[1::]:
            device_status_dict[clean_string(clean_string(dev)[:len(clean_string(dev)) - 1])] = clean_string(
                clean_string(dev).split()[-1])
        return device_status_dict

    def get_error_devices(self):
        """
        This function gets the warnings devices from DeviceMangerList

        :return warn_devices: list of error devices
        """
        warn_devices = []
        self._log.info("Checking Device Manager for ERROR Device")
        devices = self.device_manager_devicelist()
        for key, value in devices.items():
            if value != "0":
                warn_devices.append(key)
        return warn_devices

    def kill_process(self, process_name):
        """
        This method is going to kill the given process if it is running

        :param process_name: Name of the particular process to kill.(ex: powershell.exe)
        :return: None
        :raise : RuntimeError
        """
        self._log.info("Checking the {} process s running or not".format(process_name))
        result_data = self._common_content_lib.execute_sut_cmd("TASKLIST | FINDSTR /I {}".format(process_name),
                                                               "check {} process is running".format(process_name),
                                                               self._command_timeout)
        self._log.debug("Check Process output data:\n{}".format(result_data))
        self._log.info("Going to kill the process {}".format(process_name))
        kill_cmd_result = self._common_content_lib.execute_sut_cmd("taskkill /F /IM {}".format(process_name),
                                                                   "kill {}".format(process_name),
                                                                   self._command_timeout)
        self._log.debug("Kill process output data:\n{}".format(kill_cmd_result))
        self._log.info("Checking the process is killed successfully or not")
        process_running = self._os.execute('TASKLIST | FINDSTR /I "{}"'.format(process_name), self._command_timeout)
        if process_running.return_code == 0:
            raise RuntimeError("Unable to kill the process {}".format(process_name))
        self._log.info("Successfully killed the process {}".format(process_name))

    def get_os_numa_nodes(self):
        """
        This method is used to get the number of numa nodes in SUT

        return - list of available numa nodes
        raise: Test Fail
        """
        command_result = self._os.execute('powershell Get-VMhostNumaNode', self._common_content_configuration.get_command_timeout())
        self._log.debug("Numa Nodes are \n{}".format(command_result.stdout))
        available_nodes = re.findall(r'NodeId\s+:\s+(\d+)', command_result.stdout)
        if available_nodes:
            self._log.info("Available Numa Nodes on SUT - {}".format(available_nodes))
            return available_nodes
        else:
            raise RuntimeError("SUT Available Numa nodes is not fetched correctly")

    def configure_os_vm_span_numa_node(self, vm_spanning_numa_nodes=True):
        """
        This method is used to enable/disable the Virtual Machines to span physical NUMA nodes

        :param vm_spanning_numa_nodes - to enable / disable the spanning
        return - None
        raise: Test Fail
        """
        command_result = self._os.execute('powershell Set-VMHost -NumaSpanningEnabled ${}'.format({True: 'true', False: 'false'}[vm_spanning_numa_nodes]),
                                          self._common_content_configuration.get_command_timeout())
        if command_result.return_code != 0:
            raise RuntimeError("Fail to configure VM to span physical numa nodes")
        self._log.info("Allow Virtual Machines to span physical NUMA nodes is set to {}".format(vm_spanning_numa_nodes))

    def get_network_adapter_name(self, adapter):
        """
        This method would return the adapter name of the NIC card

        :param adapter - NIC adapter
        return: adapter name
        """
        cmd_line = 'powershell "Get-NetAdapter -InterfaceDescription \'{}\' | Format-List -Property "Name""'.format(adapter)
        command_result = self._os.execute(cmd_line, self._common_content_configuration.get_command_timeout())
        if command_result.return_code != 0:
            raise RuntimeError("Fail to get the network adaper of NIC card -{}".format(adapter))
        adapter = re.search(r'Name\s:\s([A-Za-z0-9]+\s(\d+))', command_result.stdout, re.IGNORECASE | re.MULTILINE)
        if not adapter:
            raise RuntimeError("Fail to get the adapter name of nic card - {}".format(adapter))
        return adapter.group(1)

    def configure_static_ip(self, adapter, static_ip, mask, gateway_ip):
        """
        This method is used to configure static ip on the network adapter

        :param adapter: adapter details
        :param static_ip: static ip
        :param mask: Subnet mask
        :param gateway_ip: gateway ip

        return: None
        raise: RunTimeError while fail to configure static ip
        """
        wait_timer_in_sec = 5
        set_ip_cmd = 'netsh interface ip set address name="{}" static {} {} {}'.format(adapter, static_ip, mask, gateway_ip)
        command_result = self._os.execute(set_ip_cmd, self._common_content_configuration.get_command_timeout())
        if command_result.return_code != 0:
            raise RuntimeError("Fail to configure the static ip {} on adapter {}".format(static_ip, adapter))

        # check does the static ip is configured correctly on the adapter
        time.sleep(wait_timer_in_sec)
        get_ip_cmd ='netsh interface ip show config name="{}"'.format(adapter)
        command_result = self._os.execute(get_ip_cmd, self._common_content_configuration.get_command_timeout())
        if command_result.return_code != 0:
            raise RuntimeError("Fail to get the ip on adapter {}".format(adapter))
        self._log.info("ip config output\n{}".format(command_result.stdout))
        ip = re.search(r'IP\sAddress:\s+(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', command_result.stdout, re.IGNORECASE | re.MULTILINE)
        if not ip:
            raise RuntimeError("Fail to get the ip of the adapter {}".format(adapter))
        if ip.group(1) != static_ip:
            raise RuntimeError("Static ip {} is not configured correctly on the adapter {}".format(static_ip, adapter))


class LinuxCommonLib:
    """
    This class implements has common functions which can used across the Linux platforms.
    """

    _PRIVATE_KEY_GEN_CMD = "openssl genrsa -out %s %s"
    _PUBLIC_KEY_GEN_CMD = "openssl rsa -pubout -in %s -out %s"

    def __init__(self, log, os_obj):
        self._log = log
        self._os = os_obj
        self._common_content_configuration = ContentConfiguration(self._log)
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        self._command_timeout = self._common_content_configuration.get_command_timeout()
        self._common_content_lib = CommonContentLib(self._log, self._os, None)

    def create_rsa_keys(self, privkey, key_size, pubkey):
        """
        Generates rsa keys

        :param privkey: private key
        :param key_size: size for the private and public key
        :param pubkey: public key
        :return:
        """
        self._log.info("Generating rsa keys of size {}".format(key_size))
        self._os.execute(self._PRIVATE_KEY_GEN_CMD % (privkey, key_size), self._command_timeout)
        self._os.execute(self._PUBLIC_KEY_GEN_CMD % (privkey, pubkey), self._command_timeout)

    def get_uuid(self, path: str) -> str:
        """Get UUID for disk device where certs are being stored
        :param path: path to where the certs are stored on a disk
        :return: UUID of device"""
        mount_point = self._os.execute(f"df {path} | tail -n -1 | awk -F\" \" '{{print $1}}'",
                                       self._command_timeout).stdout.strip()
        uuid = self._os.execute(f"lsblk {mount_point} -o partuuid | tail -n -1", self._command_timeout).stdout.strip()
        return uuid
