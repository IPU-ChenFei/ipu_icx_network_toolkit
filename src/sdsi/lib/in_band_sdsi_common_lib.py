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
"""DEPRECATION WARNING - Not included in agent scripts/libraries, which will become the standard test scripts."""
import warnings
warnings.warn("This module is not included in agent scripts/libraries.", DeprecationWarning, stacklevel=2)
import os
import re
import time
from collections import defaultdict

import src.sdsi.lib.sdsi_exceptions as SDSiExceptions
from src.provider.cpu_info_provider import CpuInfoProvider


class SDSICommonLib(object):
    """
    Base class extension for SDSICommonLib which holds common functionality for SDSi read write operations.
    Note: This class is under development. Changes are made on the go based on the requirement changes.
    """
    COMMAND_TO_GET_TOTAL_MEMORY = "cat /proc/meminfo"
    LOAD_AVERAGE_COMMAND = "cat /proc/loadavg"
    GOVERNOR_CMD = "cat /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor"

    HW_ID = "hardware_unique_identifier"
    SDSI_ENABLED = "is_sdsi_enabled"
    MAX_SSKU_UPDATES = "max_ssku_updates"
    SSKU_UPDATES_AVAILABLE = "ssku_updates_available"
    MAX_LICENSE_AUTH_FAILS = "max_capability_activation_payload_authentication_failures"
    PAYLOAD_AUTH_FAIL_COUNT = "capability_activation_payload_authentication_failures_counter"
    MAX_LICENSE_KEY_AUTH_FAILS = "max_authentication_key_certificate_authentication_failures"
    AUTH_KEY_CERT_FAIL_COUNT = "authentication_key_certificate_authentication_failures_counter"
    NUMBER_OF_PAYLOADS = "num_of_capability_activation_payloads"
    NUMBER_OF_FEATURE_BUNDLES = "number_of_feature_bundles"
    PAYLOAD_REVISION_ID = "capability_activation_payload_revision_id"
    SSKU_FUSE_BUNDLE_NAME = "ssku_fuse_bundle_encoding"
    STATE = "state"

    READ_HW_STATUS_CMD = 'https_proxy='' HTTPS_PROXY='' ./spr_sdsi_installer --read --socket {} | ./spr_output_parser'
    WRITE_CERTIFICATE_CMD = 'https_proxy='' HTTPS_PROXY='' ./spr_sdsi_installer --write -c --socket {} -f {}'
    WRITE_LICENSE_CMD = 'https_proxy='' HTTPS_PROXY='' ./spr_sdsi_installer --write -p --socket {} -f {}'
    RUN_STRESS_CMD = "tmux new-session -d -s dtaf_stress ./stressapptest -s {} -l stress.log"
    FIND_LICENSE_CMD = "find -maxdepth 1 -name '{}*.bin'"
    COPY_CORRUPT_CMD = 'yes | cp {} {} && printf "00040c: %02x" | xxd -r - {}'
    COLD_RESET_CMD = "tmux new-session -d -s dtaf_cold_reset poweroff --reboot"
    GET_STEPPING_CMD = "lscpu | grep 'Stepping'"

    def __init__(self, log, sut_os, common_content_lib, common_content_config_lib, sdsi_installer, rasp_pi=None,
                 cfg_opts=None):
        """
        Create an instance of sut SDSICommonLib.
        """
        self._log = log
        self._os = sut_os
        self._common_content_lib = common_content_lib
        self._common_content_config_lib = common_content_config_lib
        self._sdsi_installer = sdsi_installer
        self._ac_power = rasp_pi

        self.cmd_timeout = self._common_content_config_lib.get_command_timeout()
        self.reboot_timeout = self._common_content_config_lib.get_reboot_timeout()
        self._wait_time_in_sec = self._common_content_config_lib.itp_halt_time_in_sec()
        self._ac_timeout_delay_in_sec = self._common_content_config_lib.ac_timeout_delay_in_sec()
        self._stress_app_execute_time = self._common_content_config_lib.memory_stress_test_execute_time()

        self._cpu_info_provider = CpuInfoProvider.factory(self._log, cfg_opts, self._os)
        self._cpu_info_provider.populate_cpu_info()
        self.number_of_cpu = int(self._cpu_info_provider.get_number_of_sockets())

        self.sdsi_installer_path = self._sdsi_installer.installer_dest_path
        self.cpu_hw_info = {}
        self._populate_cpu_hardware_info()

        self.highest_payload_revision = None
        self.available_payloads = {}
        self.available_rtb_payloads = {}
        self.get_available_payload_set()
        self.license_key_certificate = self._sdsi_installer.get_license_certificate()
        self.erase_payloads = self._sdsi_installer.get_erase_license_certificate()
        self.cpu_stepping = self._get_cpu_stepping()
        self._log.info("CPU Stepping: {}".format(str(self.cpu_stepping)))

    def _get_cpu_stepping(self):
        """
            This method is used to fetch the CPU stepping of the CPU
            :return: The stepping of the SUT as an integer
        """
        cmd_result = self._os.execute(self.GET_STEPPING_CMD, self.cmd_timeout, self.sdsi_installer_path)
        if cmd_result.cmd_failed():
            log_error = "Failed to get cpu stepping with stderr: {}".format(cmd_result.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        return int(''.join(c for c in cmd_result.stdout if c.isdigit()))

    def get_available_payload_set(self):
        """
        This method is to retrieve the available set of CAP licenses availavle for each CPUs.
        """
        for cpu in range(self.number_of_cpu):
            if self.is_sdsi_enabled(0):
                cpu_ppin = self.get_cpu_hw_asset_id(cpu)
                self.available_payloads[cpu], self.available_rtb_payloads[cpu] = \
                    self._sdsi_installer.populate_available_payloads_for_cpu(cpu_ppin)

    def get_applicable_payloads(self, socket):
        """
        This method is to get the list of applicable payloads which can be applied to the CPU during runtime.
        return: applicable_payloads: The list of payloads which can be applied to the CPU with respect to the highest revision of payload currently on the CPU.
        """
        self._populate_cpu_hardware_info_socket(socket)

        # If there are no payloads currently provisioned on CPU, return all available payloads
        if int(self.cpu_hw_info[socket][self.NUMBER_OF_PAYLOADS][0]) == 0:
            self.highest_payload_revision = 0
            return self.available_payloads[socket]

        # Return all available payloads with revisions higher than current highest revision
        applicable_payloads = {}
        self.highest_payload_revision = max(self.get_payload_details(socket).keys())
        for key, value in self.available_payloads[socket].items():
            if int(re.search(r'rev_(.+?)_', key).group(1), 16) > self.highest_payload_revision:
                applicable_payloads[key] = value
        return applicable_payloads

    def get_applicable_rtb_payloads(self, socket):
        """
        This method is to get the list of applicable return to base payloads which can be applied to the CPU.
        return: applicable_payloads: The list of payloads which can be applied to the CPU with respect to the highest revision of payload currently on the CPU.
        """
        self._populate_cpu_hardware_info_socket(socket)

        # If there are no payloads currently provisioned on CPU, return all available rtb payloads
        if int(self.cpu_hw_info[socket][self.NUMBER_OF_PAYLOADS][0]) == 0:
            self.highest_payload_revision = 0
            return self.available_rtb_payloads[socket]

        # Return all available rtb payloads with revisions higher than current highest revision
        applicable_rtb_payloads = {}
        self.highest_payload_revision = max(self.get_payload_details(socket).keys())
        for key, value in self.available_rtb_payloads[socket].items():
            if int(re.search(r'rev_(.+?)_', key).group(1), 16) > self.highest_payload_revision:
                applicable_rtb_payloads[key] = value
        return applicable_rtb_payloads

    def _generate_corrupted_key(self, original_key):
        """
        This method is used to create and return the name of corrupt license key certificate.
        return: corrupted_key
        """
        corrupted_key = original_key.replace(".bin", "_corrupted.bin")
        corrupt_cmd = self.COPY_CORRUPT_CMD.format(original_key, corrupted_key, corrupted_key)
        self._common_content_lib.execute_sut_cmd(corrupt_cmd, corrupt_cmd, self.cmd_timeout, self.sdsi_installer_path)
        self._log.info("Corruped key {} is generated.".format(corrupted_key))
        return corrupted_key

    def get_capability_activation_payload(self, socket, payload_name=None):
        """
            Get payload information for a payload with the given name. If no name is provided, any will be picked.
        """
        # Fetch all available payloads in directory
        allowed_payloads = self.get_applicable_payloads(socket)
        if not allowed_payloads:
            log_error = "No more payloads are available for CPU_{} to provision." \
                        "Please clear the existing payloads on the CPU.".format(socket + 1)
            self._log.error(log_error)
            raise SDSiExceptions.ProvisioningError(log_error)

        # If no payload name is specified, return the first available
        if payload_name == None:
            payload_file = list(allowed_payloads.values())[0]
            payload_revision = int(re.search(r'rev_(.+?)_', list(allowed_payloads.keys())[0]).group(1), 16)
            payload_name = re.search(r'rev_.*_(.*)', list(allowed_payloads.keys())[0]).group(1)
            return [payload_revision, payload_name, payload_file]

        # If a payload name is specified, return an available payload with that given name
        payload_file = None
        for payload_key, payload in self.available_payloads[socket].items():
            if payload_name in payload_key:
                payload_file = payload
                payload_revision = int(re.search(r'rev_(.+?)_', payload_key).group(1), 16)
                payload_name = re.search(r'rev_.*_(.*)', payload_key).group(1)
                if payload_revision > self.highest_payload_revision:
                    return [payload_revision, payload_name, payload_file]

        # If no payloads are found, raise corresponding error
        if not payload_file:
            log_error = "Unable to find {} CAP.".format(payload_name)
        else:
            log_error = "Unable to find {} CAP with revision > {}".format(payload_name, self.highest_payload_revision)
        self._log.error(log_error)
        raise SDSiExceptions.MissingCapError(log_error)

    def apply_capability_activation_payload(self, cap_information, socket):
        """
        This method is used to write a cap config for the CPU.
        :param cap_information: CAP information which needs to be written for the CPU.
        :param socket: CPU socket in which the payload config is going to write.
        :return: None
        """
        self._log.info("Applying the CAP config {} for CPU {}.".format(cap_information[1], socket))
        apply_cap_cmd = self.WRITE_LICENSE_CMD.format(socket, cap_information[2])
        self._log.info("Executing command".format(apply_cap_cmd))
        write_result = self._os.execute(apply_cap_cmd, self.cmd_timeout, self.sdsi_installer_path)

        if write_result.cmd_failed():
            error = write_result.stderr.strip()
            self._log.info("Failed to apply {} CAP on CPU {} with error: {}".format(cap_information[1], socket, error))
            raise SDSiExceptions.ProvisioningError(error)

        self._log.info("{} payload is applied successfully for CPU {}".format(cap_information[1], socket))

    def return_to_base(self, payload_name, socket):
        """
            This method is used to return to base after a CAP.
        """
        for payload_key, payload in self.get_applicable_rtb_payloads(socket).items():
            if payload_name in payload_key:
                payload_file = payload
                payload_name = re.search(r'rev_.*_(.*)', payload_key).group(1)
                payload_revision = int(re.search(r'rev_(.+?)_', payload_key).group(1), 16)
                self._log.info("The RTB payload going to apply on CPU_{} is {}.".format(socket + 1, payload_name))
                if payload_revision > self.highest_payload_revision:
                    payload_information = [payload_revision, payload_name, payload_file]
                    self.apply_capability_activation_payload(payload_information, socket)
                else:
                    error = "The payload {} cannot be applied on socket {}. Revision {} smaller than current " \
                            "highest {}".format(socket, payload_revision, self.highest_payload_revision)
                    self._log.error(error)
                    raise SDSiExceptions.CapRevisionError(error)

    def get_incorrect_cpu_ppin_cap(self, payload_name):
        """
        This method is used to copy the incorrect CPU PPIN CAP to the SUT and get the binary path.
        :param payload_name: name of the incorrect cpu ppin cap, which needs to be copied to the SUT.
        :return incorrect_cpu_ppin_cap: a list of cap information with payload revision, name and bin file
        """
        self._log.info("Copy the Incorrect CPU PPIN binary to the SUT.")
        self._os.copy_local_file_to_sut(payload_name, self._sdsi_installer.installer_dest_path)
        self._log.info("Get the Incorrect CPU PPIN binary information.")
        incorrect_payload_binary = os.path.split(payload_name)[-1]
        incorrect_payload_name = re.search(r'rev_.*_(.+?).bin', incorrect_payload_binary).group(1)
        incorrect_payload_revision = int(re.search(r'rev_(.+?)_', incorrect_payload_binary).group(1))
        return [incorrect_payload_revision, incorrect_payload_name, incorrect_payload_binary]

    def apply_invalid_cpu_ppin_payload(self, payload_name, socket):
        """
        This method is used to apply an incorrect CPU PPIN payload on the CPU through SDSi command line.
        :param payload_name: Incorrect CPU PPIN binary location on the host.
        :return: None
        """
        self._log.info("Copy the Incorrect CPU PPIN binary to the SUT.")
        self._os.copy_local_file_to_sut(payload_name, self._sdsi_installer.installer_dest_path)
        incorrect_payload_binary = os.path.split(payload_name)[-1]

        if self.get_ssku_updates_available(socket) == 0:
            self.perform_graceful_powercycle()

        self._log.info("Applying the incorrect CPU PPIN CAP {}.".format(incorrect_payload_binary))
        apply_payload_cmd = self.WRITE_LICENSE_CMD.format(socket, incorrect_payload_binary)
        write_result = self._os.execute(apply_payload_cmd, self.cmd_timeout, self._sdsi_installer.installer_dest_path)

        if not write_result.cmd_failed:
            log_error = "Apply an incorrect CPU PPIN payload is not failed."
            self._log.error(log_error)
            raise SDSiExceptions.ProvisioningError(log_error)

    def get_payload_details(self, socket):
        """
        This method is used to retrieve the currently available payload information on the CPU.
        return: The payload rev ID and feature identified list.
        """
        payload_info = {}
        count = 0
        for payload_counter, rev_id in enumerate(self.cpu_hw_info[socket][self.PAYLOAD_REVISION_ID]):
            bundle_len = int(self.cpu_hw_info[socket][self.NUMBER_OF_FEATURE_BUNDLES][payload_counter])
            payload_info[int(rev_id)] = self.cpu_hw_info[socket][self.SSKU_FUSE_BUNDLE_NAME][count:count + bundle_len]
            count += bundle_len
        return payload_info

    def is_payload_available(self, payload_name, socket):
        """
        This method is used to check whether a payload is provisioned on the CPU or not.
        param payload_name: Name of the payload which needs to be verified.
        return: True if the payload is available. False if the payload is not available.
        """
        self._populate_cpu_hardware_info_socket(socket)
        for rev, payload in self.get_payload_details(socket).items():
            for feature in payload:
                if payload_name == feature:
                    self._log.info("CAP {} with revision {} available for CPU{}.".format(payload_name, rev, socket))
                    return True
        return False

    def is_cpu_provisioned(self, socket):
        """
        This method is used to check whether the CPU is in provisioned state or not.
        return: True if the CPU is provisioned. False if the CPU is not provisioned.
        """
        self._populate_cpu_hardware_info_socket(socket)

        if int(self.cpu_hw_info[socket][self.NUMBER_OF_PAYLOADS][0]) == 0:
            self._log.info("CPU{} is not provisioned.".format(socket))
            return False

        self._log.info("SSKU feature bundle(s) available for CPU{}.".format(socket))
        for revision, payload in self.get_payload_details(socket).items():
            self._log.info("CAP feature bundle(s) {} with revision {} is available.".format(payload, revision))
        return True

    def apply_license_key_certificate(self, socket):
        """
        This method is used to write the license key certificate to the SUT.
        return: None
        """
        self._log.info("Verify the license key certificate is avaialable for CPU{}.".format(socket))
        if self.is_license_key_available(socket):
            self._log.info("License key is already available for CPU{}.".format(socket))
            return

        self._log.info("Applying the license key certificate for CPU{}.".format(socket))
        failure_counter_before_write = self.get_license_key_auth_fail_count(socket)
        apply_license_cmd = self.WRITE_CERTIFICATE_CMD.format(socket, self.license_key_certificate)
        write_response = self._os.execute(apply_license_cmd, self.cmd_timeout, self._sdsi_installer.installer_dest_path)
        if write_response.cmd_failed():
            error = "License write operation failed with error {}".format(write_response.stderr.strip())
            self._log.error(error)
            # TODO, instead of returning error message, raise specific exception, and catch exception for negative tests
            return write_response.stderr.strip()

        self._log.info("Cold reset the SUT as the license key is applied and needs to take effect.")
        self.perform_graceful_powercycle()
        if self.get_license_key_auth_fail_count(socket) > failure_counter_before_write:
            error = "Failure counter increased after writing license"
            self._log.error(error)
            raise SDSiExceptions.LicenseKeyError(error)

        self._log.info("License key applied successfully for CPU{}.".format(socket))

    def erase_payloads_from_nvram(self):
        """
        This method is used to erase the previosly provisioned payloads on the SUT.
        return: None
        """
        self._log.info("Clear any existing payloads from all sockets")
        for socket in range(self.number_of_cpu):
            self.erase_payloads_from_nvram_single_socket(socket)

    def erase_payloads_from_nvram_single_socket(self, socket):
        """
        This method is used to erase the previosly provisioned payloads on the SUT.
        return: None
        """
        if (socket >= self.number_of_cpu):
            return

        failure_counter_before_apply = self.get_license_key_auth_fail_count(socket)
        write_license_cmd = self.WRITE_CERTIFICATE_CMD.format(socket, self.erase_payloads)
        self._common_content_lib.execute_sut_cmd(write_license_cmd, write_license_cmd, self.cmd_timeout,
                                                 self._sdsi_installer.installer_dest_path)
        failure_counter_after_apply = self.get_license_key_auth_fail_count(socket)

        if failure_counter_after_apply > failure_counter_before_apply:
            log_error = "Erase operation failed, Failure counter increased " \
                        "from {} to {}".format(failure_counter_before_apply, failure_counter_after_apply)
            self._log.error(log_error)
            raise SDSiExceptions.EraseProvisioningError(log_error)

        if self.is_cpu_provisioned(socket):
            log_error = "Erase operation failed, CPU{} still provisioned.".format(socket)
            self._log.error(log_error)
            raise SDSiExceptions.EraseProvisioningError(log_error)

        self._log.info("Payload configurations are successfully erased from the NVRAM.")

    def apply_invalid_license_key_on_sut(self):
        """
        This method is used to create and apply corrupted license key certificate to the CPU.
        return: None
        """
        corrupt_license = self._generate_corrupted_key(self.license_key_certificate)
        for socket in range(self.number_of_cpu):
            self._log.info("Verify the license key certificate is not avaialable for CPU{}.".format(socket))
            if self.is_license_key_available(socket):
                log_error = "License key is already available on CPU{}.".format(socket)
                self._log.info(log_error)
                # raise RuntimeError(log_error)

            self._log.info("Applying the corrupt license key certificate on CPU{}.".format(socket))
            apply_license_cmd = self.WRITE_CERTIFICATE_CMD.format(socket, corrupt_license)
            cmd_result = self._os.execute(apply_license_cmd, self.cmd_timeout, self.sdsi_installer_path)
            error_response = cmd_result.stderr.strip()

            if not cmd_result.cmd_failed() and "Invalid data size for the mailbox." in error_response:
                log_error = "Invalid license key apply operation is failed."
                self._log.error(log_error)
                raise SDSiExceptions.LicenseKeyError(log_error)

            self._log.info("Corrupt license not applied for CPU{}, error message: {}.".format(socket, error_response))

    def is_license_key_available(self, socket):
        """
        This method will check for the availability of license key certificate on the CPU.
        return: True if the key is available, False if not available.
        """
        self._populate_cpu_hardware_info_socket(socket)
        return self.cpu_hw_info[socket][self.STATE][0] != "[Empty]"

    def is_sdsi_enabled(self, socket):
        """
        This method will check whether the CPU is SDSi supported or not.
        return: True if SDSi supported. False if not supported.
        """
        return self.SDSI_ENABLED in self.cpu_hw_info[socket]

    def perform_graceful_powercycle(self):
        """
        Performs graceful shutdown
        """
        self._common_content_lib.perform_graceful_ac_off_on(self._ac_power)
        self._os.wait_for_os(self.reboot_timeout)
        time.sleep(self._wait_time_in_sec)

    def warm_reset(self):
        """
        Reset SUT gracefully and wait for SUT to boot.
        """
        self._common_content_lib.perform_os_reboot(self.cmd_timeout)
        self._os.wait_for_os(self.reboot_timeout)
        time.sleep(self._wait_time_in_sec)

    def cold_reset(self):
        """
        Perform Cold Reset and wait for SUT to boot.
        """
        self._common_content_lib.execute_sut_cmd(self.COLD_RESET_CMD, self.COLD_RESET_CMD, self.cmd_timeout)
        time.sleep(self._wait_time_in_sec)
        if self._os.is_alive():
            raise RuntimeError("Failed to run command '{}'".format(self.COLD_RESET_CMD))
        self._common_content_lib.perform_boot_script()
        self._os.wait_for_os(self.reboot_timeout)

    def get_load_average(self):
        """
        This method will fetch the load average value from the SUT
        :return: value of Load Average
        """
        response = self._common_content_lib.execute_sut_cmd(self.LOAD_AVERAGE_COMMAND, "Get CPU load", self.cmd_timeout)
        load_average_list = list(map(float, (response.split())[0:3]))
        if not load_average_list:
            log_error = "load_average value is not present in system"
            self._log.error(log_error)
            raise RuntimeError(log_error)
        return load_average_list

    def get_max_load_average(self):
        """
        This method will get max load average value
        :return: Max load average value from list
        """
        list_load_value = self.get_load_average()
        if not list_load_value:
            log_error = "Failed to get load average values"
            self._log.error(log_error)
            raise RuntimeError(log_error)

        max_load_value = max(list_load_value)
        self._log.info("Maximum load average value{}".format(max_load_value))
        return max_load_value

    def execute_stress_app_installer_on_sut(self):
        """
        Execute the stress app test file with specific waiting time.
        :return: None
        :raise: RuntimeError if stress test execution failed.
        """
        stress_wait_time = 120
        try:
            remove_log_cmd = "rm -rf stress.log"
            self._common_content_lib.execute_sut_cmd(remove_log_cmd, remove_log_cmd, self.cmd_timeout)
            self._log.info("Starting the stress app test")
            run_stress_cmd = self.RUN_STRESS_CMD.format(self._stress_app_execute_time)
            # Creating an asynchronous process of stressapp using tmux
            result_verify = self._common_content_lib.execute_sut_cmd(run_stress_cmd, run_stress_cmd, self.cmd_timeout)
            self._log.debug("Wait for {} seconds to generate a sufficient load on the CPU.".format(stress_wait_time))
            time.sleep(stress_wait_time)
        except Exception as ex:
            log_error = "Stress app test  execution failed with exception '{}'...".format(str(ex))
            self._log.error(log_error)
            raise RuntimeError(log_error)

    def validate_default_registry_values(self):
        self._sdsi_installer.verify_sdsi_installer()

        for cpu in range(self.number_of_cpu):
            self._log.info("Verify the failure counters for CPU{} after graceful G3.".format(cpu))
            license_key_auth_failures = self.get_license_key_auth_fail_count(cpu)
            payload_auth_fail_count = self.get_license_auth_fail_count(cpu)

            if license_key_auth_failures != 0:
                error = "License key failure counter is not reset to 0 for CPU{} after reboot.".format(cpu)
                self._log.error(error)
                raise RuntimeError(error)

            if payload_auth_fail_count != 0:
                error = "CAP authentication failure counter is not reset to 0 for CPU{} after reboot.".format(cpu)
                self._log.error(error)
                raise RuntimeError(error)

    def _populate_cpu_hardware_info_socket(self, socket):
        """
        This method is used to populate CPU Hardware info using the spr_sdsi_installer applications' read operation.
        """
        if socket >= self.number_of_cpu:
            return

        if self.cpu_hw_info.get(socket) != None:
            self.cpu_hw_info.get(socket).clear()

        self.cpu_hw_info[socket] = defaultdict(list)
        cpu_hw_info_list = []
        hw_status_read_cmd = self.READ_HW_STATUS_CMD.format(socket)
        hw_response = self._os.execute(hw_status_read_cmd, self.cmd_timeout, self.sdsi_installer_path)

        if hw_response.cmd_failed() and self.is_sdsi_enabled(socket=0) and socket != 0:
            log_error = "Failed installer read for CPU{} with stderr: {}".format(socket, hw_response.stderr)
            self._log.error(log_error)
            raise SDSiExceptions.InstallerReadError(log_error)

        hw_asset_information = hw_response.stdout.strip()
        for hw_info in hw_asset_information.splitlines():
            cpu_hw_info_list.append((hw_info.split("=")[0].strip().lower(), ".".join(hw_info.split("=")[1:]).strip()))

        for header, value in cpu_hw_info_list:
            self.cpu_hw_info[socket][header].append(value)

    def _populate_cpu_hardware_info(self):
        """
        This method is used to populate CPU Hardware information using spr_sdsi_installer applications' read operation.
        """
        self.cpu_hw_info.clear()
        for cpu in range(self.number_of_cpu):
            self._populate_cpu_hardware_info_socket(cpu)

    def get_cpu_hw_asset_id(self, socket):
        """
        This method is used to get the hardware id/cpu ppin from the cpu hardware info.
        return: hardware_asset_id - The value of the cpu hardware id or ppin
        """
        return self.cpu_hw_info[socket][self.HW_ID][0][2:]

    def get_content_type(self, socket):
        """
        """
        return self.cpu_hw_info[socket]['content_type'][0]

    def get_region_rev_id(self, socket):
        """
        """
        return self.cpu_hw_info[socket]['region_rev_id'][0]

    def get_header_size(self, socket):
        """
        """
        return self.cpu_hw_info[socket]['header_size'][0]

    def get_total_size(self, socket):
        """
        """
        return self.cpu_hw_info[socket]['total_size'][0]

    def get_key_size(self, socket):
        """
        """
        return self.cpu_hw_info[socket]['key_size'][0]

    def get_license_auth_fail_count(self, socket):
        """
        This method is used to get the number of license authorization failures.
        return: license_auth_fail_count - Number of license authorization failures
        """
        self._populate_cpu_hardware_info_socket(socket)
        return int(self.cpu_hw_info[socket][self.PAYLOAD_AUTH_FAIL_COUNT][0])

    def get_license_key_auth_fail_count(self, socket):
        """
        This method is used to get the number of license key authorization failures.
        return: license_key_auth_fail_count - Number of license key authorization failures
        """
        self._populate_cpu_hardware_info_socket(socket)
        return int(self.cpu_hw_info[socket][self.AUTH_KEY_CERT_FAIL_COUNT][0])

    def get_max_license_key_auth_fail_count(self, socket):
        """
        This method is used to get the number of license key authorization failures.
        return: license_key_auth_fail_count - Number of license key authorization failures
        """
        return int(self.cpu_hw_info[socket][self.MAX_LICENSE_KEY_AUTH_FAILS][0])

    def get_max_license_auth_fail_count(self, socket):
        """
        This method is used to get the number of license key authorization failures.
        return: license_key_auth_fail_count - Number of license key authorization failures
        """
        return int(self.cpu_hw_info[socket][self.MAX_LICENSE_AUTH_FAILS][0])

    def get_ssku_updates_available(self, socket):
        """
        This method is used to get the remaining number of ssku updates available per boot for the CPU.
        return: The number of ssku updates remaining for the CPU.
        return:
        """
        self._populate_cpu_hardware_info_socket(socket)
        return int(self.cpu_hw_info[socket][self.SSKU_UPDATES_AVAILABLE][0])

    def get_max_ssku_updates_available(self, socket):
        """
        This method is used to get the maximum number of ssku updates available per boot for the CPU.
        return: The number of ssku updates remaining for the CPU.
        """
        return int(self.cpu_hw_info[socket][self.MAX_SSKU_UPDATES][0])

    def get_datetime_on_linux_sut(self):
        """
        This Method is Used to Get the Current Date and Time from Linux SUT
        :return: The current date and time value of the SUT
        """
        self._log.info("Getting the Date and Time in SUT ....")
        response = self._os.execute('date +"%F %T" | tee current_time.txt', self.cmd_timeout)
        return response.stdout

    def change_cpu_governor(self):
        """
        This method will check for the scaling_governor value of the cpu and change it's value to "powersave" if it's
        value is other than "powersave"
        return: None
        """
        governor = self._common_content_lib.execute_sut_cmd(self.GOVERNOR_CMD, "Read CPU governor", self.cmd_timeout)
        if "powersave" not in governor:
            powersave_command = 'for c in $( ls /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor ) ; do echo ' \
                                '"powersave" > $c ; done '
            self._common_content_lib.execute_sut_cmd(powersave_command, "Change to powersave", self.cmd_timeout)

    def get_cpu_frequencies(self):
        """
        This method will get the CPU frequencies from the SUT from "/proc/cpuinfo"
        return: The value of all frequencies collected in a dictionary mapping to right cpu ID.
        """
        cpu_frequency_dict = {}
        cpu = 0
        frequency_cmd = 'grep "cpu MHz" /proc/cpuinfo'
        frequencies = self._common_content_lib.execute_sut_cmd(frequency_cmd, "Read CPU frequencies", self.cmd_timeout)
        for frequency in frequencies.strip().split("\n"):
            cpu_frequency_dict["cpu{}".format(cpu)] = frequency.split(":")[1].strip()
            cpu += 1
        return cpu_frequency_dict

    def get_total_memory_in_gb(self):
        """
        This function will fetch the Total System Memory Value from the Meminfo File
        :return: value of Total Memory
        :raise: RuntimeError: If Memtotal value is not present in the File
        """
        ret_cmd = self._os.execute(self.COMMAND_TO_GET_TOTAL_MEMORY, self.cmd_timeout)
        if ret_cmd.cmd_failed():
            log_error = "Failed to run command {} with std_error: {}".format(ret_cmd, ret_cmd.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        mem_total = re.findall(r"MemTotal:.*", ret_cmd.stdout)[0].split(":")[1].strip()
        mem_total = int(mem_total[:-3])
        if not mem_total:
            self._log.error("MemTotal value is not present under the MemInfo file")
            raise RuntimeError("MemTotal value is not present under the MemInfo file")
        mem_in_giga_bytes = mem_total / (1024 * 1024)
        return mem_in_giga_bytes

    def verify_hqm_dlb_kernel(self, hqm_value):
        """
        This function verify the HQM kernel driver in the sut.
        Remove the hqmv2 driver
        """
        regex_kernel_driver = r"Co-processor: Intel Corporation Device 2710"
        lspci_dlb_kernel_cmd = "lspci -v -d :2710"
        self._log.info("Verify the hqm kernel driver used in the sut")
        cmd_output = self._common_content_lib.execute_sut_cmd(lspci_dlb_kernel_cmd, "find the Kernel driver in use"
                                                                                    " the sut", self.cmd_timeout)
        self._log.debug("lspci command output results {}".format(cmd_output))
        available_kernel_driver = re.findall(regex_kernel_driver, "".join(cmd_output))
        self._log.info("Number of HQM device listed is {}.".format(len(available_kernel_driver)))
        self._log.info("Present HQM device list in the sut {}".format(available_kernel_driver))
        if hqm_value == "HQM4":
            return len(available_kernel_driver) == (4 * self.number_of_cpu)
        elif hqm_value == "HQM2":
            return len(available_kernel_driver) == (2 * self.number_of_cpu)

    def verify_iax_kernel(self):
        """
        This function verify the IAX kernel driver in the sut.
        Remove the hqmv2 driver
        """
        regex_kernel_driver = r"Co-processor: Intel Corporation Device 0cfe"
        lspci_dlb_kernel_cmd = "lspci -v -d :0cfe"
        self._log.info("Verify the iax kernel driver used in the sut")
        cmd_output = self._common_content_lib.execute_sut_cmd(lspci_dlb_kernel_cmd, "find the Kernel driver in use"
                                                                                    " the sut", self.cmd_timeout)
        self._log.debug("lspci command output results {}".format(cmd_output))
        available_kernel_driver = re.findall(regex_kernel_driver, "".join(cmd_output))
        self._log.info("Number of IAX device listed is {}.".format(len(available_kernel_driver)))
        self._log.info("Present IAX device list in the sut {}".format(available_kernel_driver))
        return len(available_kernel_driver) == (2 * self.number_of_cpu)

    def get_hqm_dlb_kernel(self):
        """
        This function verify the HQM kernel driver in the sut.
        Remove the hqmv2 driver
        """
        regex_kernel_driver = r"Intel Corporation Device 2710"
        lspci_dlb_kernel_cmd = "lspci -v -d :2710"
        self._log.info("Verify the hqm kernel driver used in the sut")
        cmd_output = self._common_content_lib.execute_sut_cmd(lspci_dlb_kernel_cmd, "find the Kernel driver in use"
                                                                                    " the sut", self.cmd_timeout)
        self._log.debug("lspci command output results {}".format(cmd_output))
        available_kernel_driver = re.findall(regex_kernel_driver, "".join(cmd_output))
        self._log.info("Number of HQM device listed is {}.".format(len(available_kernel_driver)))
        self._log.info("Present HQM device list in the sut {}".format(available_kernel_driver))
        return available_kernel_driver

    def get_iax_kernel(self):
        """
        This function verify the IAX kernel driver in the sut.
        Remove the hqmv2 driver
        """
        regex_kernel_driver = r"Intel Corporation Device 0cfe"
        lspci_dlb_kernel_cmd = "lspci -v -d :0cfe"
        self._log.info("Verify the iax kernel driver used in the sut")
        cmd_output = self._common_content_lib.execute_sut_cmd(lspci_dlb_kernel_cmd, "find the Kernel driver in use"
                                                                                    " the sut", self.cmd_timeout)
        self._log.debug("lspci command output results {}".format(cmd_output))
        available_kernel_driver = re.findall(regex_kernel_driver, "".join(cmd_output))
        self._log.info("Number of IAX device listed is {}.".format(len(available_kernel_driver)))
        self._log.info("Present IAX device list in the sut {}".format(available_kernel_driver))
        return available_kernel_driver

    def print_single_socket_hardware_info(self, socket):
        """
        This method prints the hw info for a single socket
        """
        hw_status_read_cmd = self.READ_HW_STATUS_CMD.format(socket)
        hw_asset_response = self._os.execute(hw_status_read_cmd, self.cmd_timeout, self.sdsi_installer_path)
        if hw_asset_response.cmd_failed() and self.is_sdsi_enabled(socket=0) and socket != 0:
            log_error = "Failed to perform spr_sdsi_installer read with stderr: ".format(hw_asset_response.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        self._log.debug(hw_asset_response.stdout.strip())

    def print_all_sockets_info(self):
        """
       This method prints hw info for all sockets on SUT
       """
        for cpu in range(self.number_of_cpu):
            self._log.debug("Printing SDSI hardware feature information for CPU{}.".format(cpu))
            self._log.debug("============================================")
            self.print_single_socket_hardware_info(cpu)
            self._log.debug("============================================")
