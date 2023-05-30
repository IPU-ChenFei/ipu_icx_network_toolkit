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
"""Module containing SDSiAgentLib class to interact with an sdsi-agent on the SUT.

    Typical usage example:
        self.sdsi_agent: SDSiAgentLib = SDSiAgentLib(self._log, self.os, self.ac, config)

        self.sdsi_agent.verify_agent()
        self.sdsi_agent.erase_provisioning()
        self.cycling_tool.perform_ac_cycle()
        self.sdsi_agent.validate_default_registry_values()

        active_features = [self.sdsi_agent.apply_lac(socket) for socket in range(self.sdsi_agent.num_sockets)]
        self.cycling_tool.perform_ac_cycle()
        for socket in range(self.sdsi_agent.num_sockets):
            self.sdsi_agent.validate_active_feature_set(socket, active_features[socket])
"""
import json
import os
import random
import re
from logging import Logger
from typing import List, Dict, Tuple
from xml.etree.ElementTree import Element

from dtaf_core.lib.exceptions import OsCommandException
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.providers.sut_os_provider import SutOsProvider

import src.sdsi.lib.sdsi_exceptions as SDSiExceptions
from src.sdsi.lib.license.sdsi_license_names import FeatureNames
from src.sdsi.lib.license.sdsi_license_request_tool import SDSiLicenseTool
from src.sdsi.lib.tools.automation_config_tool import AutomationConfigTool
from src.sdsi.lib.tools.cycling_tool import CyclingTool
from src.sdsi.lib.tools.sut_cpu_info_tool import SutCpuInfoTool
from src.sdsi.lib.tools.sut_os_tool import SutOsTool


class SDSiAgentLib:
    """Library which provides common interactions with the SDSi Agent for SDSi operations.

    Attributes:
        num_sockets (int): The number of sockets on the platform
    """
    WRITE_CERTIFICATE_CMD = 'https_proxy='' HTTPS_PROXY='' ./spr_sdsi_installer --write -c --socket {} -f {}'
    AGENT_WRITE_LICENSE_TEMPLATE = 'sdsi-agent -w -s CPU:{} -f {} -e new-akc,lac-revision-id-gap'
    AGENT_ERASE_TEMPLATE = 'sdsi-agent -w -s CPU:{} -f {} -e incorrect-hw-id,no-cap-in-lac,incorrect-akc-revision-id'
    AGENT_READ_HW_STATE_TEMPLATE = 'sdsi-agent -r -s CPU:{} --debug'
    AGENT_READ_HW_INFO_TEMPLATE = 'sdsi-agent -i'
    FIND_LICENSE_CMD = "find -name '{}*.json'"
    LICENSE_PATH = '/root/sdsi_licenses'
    ROOT_PATH = '/root'
    API_KEY_ENV = 'sdsi_api_key'

    def __init__(self, log: Logger, sut_os: SutOsProvider, ac_power: AcPowerControlProvider, config: Element) -> None:
        """Initialize the SDSiAgentLib

        Args:
            log: logger to use for test logging.
            sut_os: OS provider used for test content to interact with SUT.
            ac_power: AC provider used for test content to control AC power.
            config: configuration options for test content.
        """
        # Intialize test utilities
        self._log = log
        self._sut_os_tool: SutOsTool = SutOsTool(log, sut_os)
        self._cycling_tool: CyclingTool = CyclingTool(log, sut_os, config, ac_power)
        self._platform_info_tool: SutCpuInfoTool = SutCpuInfoTool.factory(log, sut_os, config)
        self.num_sockets = self._platform_info_tool.get_number_of_sockets()

        # Initialize agent command - Default Inband
        self._agent_write_license_cmd = self.AGENT_WRITE_LICENSE_TEMPLATE
        self._agent_read_hw_state_cmd = self.AGENT_READ_HW_STATE_TEMPLATE
        self._agent_read_hw_info_cmd = self.AGENT_READ_HW_INFO_TEMPLATE
        self._agent_erase_cmd = self.AGENT_ERASE_TEMPLATE

        # Initialize license requesting tool for optional automatic license requesting
        self._sdsi_api_key = os.getenv(self.API_KEY_ENV, '')
        self._sdsi_license_tool: SDSiLicenseTool = SDSiLicenseTool(self._sdsi_api_key, self._log.info, self._log.error)

    def swap_to_in_band(self) -> None:
        """This method turns the library into in-band mode. All agent commands will use in-band commands."""
        self._log.info('Swapping SDSi Agent library into in band mode.')
        self._agent_write_license_cmd = self.AGENT_WRITE_LICENSE_TEMPLATE
        self._agent_read_hw_state_cmd = self.AGENT_READ_HW_STATE_TEMPLATE
        self._agent_read_hw_info_cmd = self.AGENT_READ_HW_INFO_TEMPLATE
        self._agent_erase_cmd = self.AGENT_ERASE_TEMPLATE

    def swap_to_out_of_band_mctp(self) -> None:
        """This method turns the library into oob mctp mode. All agent commands will use oob mctp commands."""
        self._log.info('Swapping SDSi Agent library into out of band mctp mode.')
        oob_mctp_flag = self.get_oob_flag() + ',peci-mode=mctp'
        self._agent_write_license_cmd = self.AGENT_WRITE_LICENSE_TEMPLATE + oob_mctp_flag
        self._agent_read_hw_state_cmd = self.AGENT_READ_HW_STATE_TEMPLATE + oob_mctp_flag
        self._agent_read_hw_info_cmd = self.AGENT_READ_HW_INFO_TEMPLATE + oob_mctp_flag
        self._agent_erase_cmd = self.AGENT_ERASE_TEMPLATE + oob_mctp_flag

    def swap_to_out_of_band_wire(self) -> None:
        """This method turns the library into oob wire mode. All agent commands will use oob wire commands."""
        self._log.info('Swapping SDSi Agent library into out of band wire mode.')
        oob_wire_flag = self.get_oob_flag() + ',peci-mode=wire'
        self._agent_write_license_cmd = self.AGENT_WRITE_LICENSE_TEMPLATE + oob_wire_flag
        self._agent_read_hw_state_cmd = self.AGENT_READ_HW_STATE_TEMPLATE + oob_wire_flag
        self._agent_read_hw_info_cmd = self.AGENT_READ_HW_INFO_TEMPLATE + oob_wire_flag
        self._agent_erase_cmd = self.AGENT_ERASE_TEMPLATE + oob_wire_flag

    def get_oob_flag(self) -> str:
        """This method compiles bmc details into an oob flag to be used by the SDSi Agent.

        Returns:
            str: The oob flag to be appened directly to SDSi Agent commands.
        """
        automation_config_tool: AutomationConfigTool = AutomationConfigTool(self._log)
        bmc_ip = automation_config_tool.get_config_value("Section0", "ipaddress")
        bmc_user = automation_config_tool.get_config_value("Section0", "username")
        bmc_pass = automation_config_tool.get_config_value("Section0", "password")
        return f' -o url=https://{bmc_ip},username={bmc_user},password={bmc_pass},insecure=true'

    def verify_agent(self) -> None:
        """This method verifies the functionality of the SDSi agent by running the help command.

        Raises:
            AgentSetupError: If the help command fails.
        """
        self._log.info("Verifying the SDSi agent by running the help command.")
        try: self._sut_os_tool.execute_cmd('sdsi-agent -h', self.ROOT_PATH)
        except OsCommandException as ex:
            error_msg = "Failed to run SDSi Agent help command."
            self._log.error(error_msg)
            raise SDSiExceptions.AgentSetupError(error_msg) from ex

        self._log.info(f"Verifying the {self.LICENSE_PATH} path exists for the SDSi agent to use for provisioning.")
        self._sut_os_tool.execute_cmd(f'mkdir -p {self.LICENSE_PATH}', self.ROOT_PATH)

    @staticmethod
    def get_payload_list_from_lac(lac_filename: str) -> List[str]:
        """This method is used to gather the feature list from an lac filename

        Args:
            lac_filename: The name of the lac file to extract feature list from

        Returns:
            List[str]: The list of features.
                       Ex: '2272C3CAFAEA6754_key_id_1_rev_100_IAA4_SG40.json' -> ['IAA4', 'SG40']
        """
        return re.search(r'rev_.\d+_(.*).json', lac_filename).group(1).split('_')

    def get_available_lac_set(self) -> Dict[int, Dict[int, str]]:
        """This method populates the available payloads on the SUT into a dictionary.

        Returns:
            Dict[int, Dict[int, str]: dictionary containing the payload set for all sockets on the platform.
                                      format {socket: {revision: license}}
        """
        # Remove Corrupted CAPs
        self._log.info("Removing existing corrupted CAP keys.")
        self._sut_os_tool.execute_cmd("rm -f *_corrupted.json", self.LICENSE_PATH)

        # Loop through each socket to search for available payloads
        available_payloads = {}
        for socket in range(self.num_sockets):
            # Get Available licenses for the PPIN
            hw_id = self.get_cpu_hw_asset_id(socket)
            try:
                license_result = self._sut_os_tool.execute_cmd(self.FIND_LICENSE_CMD.format(hw_id), self.LICENSE_PATH)
            except OsCommandException:
                error_msg = f"No license CAPs found for CPU PPIN {hw_id} in SUT path {self.LICENSE_PATH}"
                self._log.error(error_msg)
                raise SDSiExceptions.MissingCapError(error_msg)

            # Repopulate available payloads for the socket
            available_payloads[socket] = {}
            for license_name in license_result.strip().splitlines():
                revision_number = int(re.search(r'key_id_\d_rev_(.*?)_.*.json', license_name).group(1))
                available_payloads[socket][revision_number] = license_name
        return available_payloads

    def get_applicable_lacs(self, socket: int) -> Dict[int, str]:
        """This method is to get a dictionary of applicable payloads which can be applied to the CPU during runtime.

        Args:
            socket: The socket number to check for applicable payloads.

        Returns:
            Dict[int, str]: payloads which can be applied to the socket according to the current revision.
                            format {revision: license} sorted in ascending order by the key.
        """
        available_payloads = self.get_available_lac_set()[socket].items()
        highest_payload_revision = self.get_highest_revision_number(socket)
        return {k: v for k, v in sorted(available_payloads) if k > highest_payload_revision}

    def get_license_activation_code(self, socket: int, feature_list: List[str] = None) -> Tuple[int, str]:
        """Get payload information for a payload with the given features. If none are provided, any will be picked.

        Args:
            socket: the socket number to get a payload for.
            feature_list: specify the features contained in the payload to retrieve.

        Returns:
            Tuple[int, str]: revision and filename of the available payload. (revision, payload_name)

        Raises:
            MissingCapError: If a payload is not available with the given name.
        """
        # Fetch all available payloads in directory and return a corresponding payload
        allowed_payloads = self.get_applicable_lacs(socket)
        if allowed_payloads and not feature_list:
            for key, value in allowed_payloads.items(): return key, value
        for revision, payload in allowed_payloads.items():
            if sorted(feature_list) == sorted(self.get_payload_list_from_lac(payload)): return revision, payload

        # If no payloads are found, raise missing cap error
        highest_revision = self.get_highest_revision_number(socket)
        error_msg = f"Unable to find {feature_list} CAP for socket {socket} with revision > {highest_revision}."
        self._log.error(error_msg)
        raise SDSiExceptions.MissingCapError(error_msg)

    def apply_lac(self, socket: int, lac_information: Tuple[int, str] = None) -> List[str]:
        """This method is used to write an LAC onto the given socket.

        Args:
            socket: CPU socket in which the LAC is going to be provisioned.
            lac_information: CAP information to write for the CPU. If none is provided, pick one at random.

        Returns:
            List[str]: The list of features included in the applied LAC.

        Raises:
            ProvisioningError: If the CAP fails to apply.
            CapFailCountError: If the provisioning failure register increments.
            AvailableUpdatesError: If the available SSKU updates does not decrement after provisioning.
        """
        # Select random LAC to provision if one was not given
        if not lac_information:
            self._log.info(f"No LAC information provided, picking one at random.")
            lac_information = self.get_license_activation_code(socket)

        # Get register values before provisioning
        self._log.info(f"Get the register values for socket {socket} before applying LAC.")
        payload_fail_count_before = self.get_license_auth_fail_count(socket)
        ssku_updates_before = self.get_ssku_updates_available(socket)
        is_already_provisioned = self.is_cpu_provisioned(socket)

        # Provision CPU with LAC
        self._log.info(f"Applying the CAP config {lac_information[1]} for socket {socket}.")
        apply_cap_cmd = self._agent_write_license_cmd.format(socket, lac_information[1])
        try:
            self._sut_os_tool.execute_cmd(apply_cap_cmd, self.LICENSE_PATH)
        except OsCommandException:
            error_msg = f"Failed to apply {lac_information[1]} CAP for socket {socket}."
            self._log.error(error_msg)
            raise SDSiExceptions.ProvisioningError(error_msg)

        # Get register values after provisioning
        self._log.info(f"Get the register values for socket {socket} after applying LAC.")
        payload_fail_count_after = self.get_license_auth_fail_count(socket)
        ssku_updates_after = self.get_ssku_updates_available(socket)

        # Validate register values
        self._log.info(f"Verify the registers are updated as expected for CPU {socket}.")
        if payload_fail_count_before != payload_fail_count_after:
            error_msg = f'Provisioning failure register increased for socket {socket}.'
            self._log.error(error_msg)
            raise SDSiExceptions.CapFailCountError(error_msg)
        decrement_amount = 1 if is_already_provisioned else 2
        if ssku_updates_after != ssku_updates_before - decrement_amount:
            error_msg = f'Available SSKU updates did not decrease by {decrement_amount} for socket {socket}.'
            self._log.error(error_msg)
            raise SDSiExceptions.AvailableUpdatesError(error_msg)

        # Verify highest revision number matches the revision number of the newly applied payload
        if lac_information[0] != self.get_highest_revision_number(socket):
            error_msg = f'Feature {lac_information[1]} is not found on socket {socket} after provisioning.'
            self._log.error(error_msg)
            raise SDSiExceptions.CapRevisionError(error_msg)
        self._log.info(f"{lac_information[1]} payload is applied successfully for CPU {socket}.")

        # Validate the features now exist in the provisioning information, not enabled yet since no reboot.
        feature_list = self.get_payload_list_from_lac(lac_information[1])
        self.validate_available_feature_set(socket, feature_list)
        self.validate_active_feature_set(socket, feature_list, False)
        return feature_list

    def apply_lac_by_name(self, socket: int, features: List[str]) -> List[str]:
        """This method is used to write an LAC with specified features onto the given socket.
        The features must EXACTLY match the CAP to be applied. A CAP will not be applied with extra features.
        If an API key is provided as an environment variable (sdsi_api_key), the license is requested if missing.

        Args:
            socket: CPU socket in which the LAC is going to be provisioned.
            features: Exact feature list within CAP to provision to the CPU.

        Returns:
            List[str]: The list of features included in the applied LAC.

        Raises:
            ProvisioningError: If the CAP fails to apply.
            CapFailCountError: If the provisioning failure register increments.
            AvailableUpdatesError: If the available SSKU updates does not decrement after provisioning.
            MissingCapError: If a CAP with the specified features cannot be found.
        """
        try:
            lac_cap = self.get_license_activation_code(socket, features)
        except SDSiExceptions.MissingCapError as e:
            self._log.info(f'No Valid {features} LAC for socket {socket}. Attempting to request license.')
            if not self._sdsi_api_key:
                error_msg = f'SDSi License API key is not configured on the platform. Add {self.API_KEY_ENV}' \
                            f' environment variable for automatic license requesting.'
                self._log.error(error_msg)
                raise SDSiExceptions.MissingCapError(error_msg) from e
            self._request_and_install_license_on_sut(socket, features)
            lac_cap = self.get_license_activation_code(socket, features)
        return self.apply_lac(socket, lac_cap)

    def validate_available_feature_set(self, socket: int, features: List[str], expected_status: bool = True) -> None:
        """This method validates that a list of features is provisioned on the CPU.

        Args:
            socket: CPU socket in which to check for features.
            features: List of the features to check if they are provisioned.
            expected_status: a bool containing the expected result of the feature set. Provisioned or not.

        Raises:
            ProvisioningError: if the provisioning does not match expected status.
        """
        for feature in features:
            if feature != FeatureNames.BASE.value and expected_status != self.is_feature_available(feature, socket):
                error_msg = f'{feature} does not match available status on socket {socket}.'
                self._log.error(error_msg)
                raise SDSiExceptions.ProvisioningError(error_msg)

    def validate_active_feature_set(self, socket: int, features: List[str], expected_status: bool = True):
        """This method validates that a list of features is provisioned AND ACTIVE on the CPU.

        Args:
            socket: CPU socket in which to check for features.
            features: List of the features to check if they are active.
            expected_status: a bool containing the expected result of the feature set. Active or not.

        Raises:
            ProvisioningError: if the active provisioning status does not match expected status.
        """
        for feature in features:
            if feature != FeatureNames.BASE.value and expected_status != self.is_feature_active(feature, socket):
                error_msg = f'{feature} does not match expected active status on socket {socket}.'
                self._log.error(error_msg)
                raise SDSiExceptions.ProvisioningError(error_msg)

    def get_available_feature_details(self, socket: int) -> Dict[int, List[str]]:
        """This method is used to retrieve the currently available payload information on the CPU.

        Args:
            socket: the socket number to retrieve payload details of.

        Returns:
            Dict[int, List[str]]: Currenly provisioned payloads with revision as key and feature names as value.
                                 Ex: {1: ['IAA4'], 2: ['DLB4'], 3: ['DSA4'], 4: ['SGX512']}
        """
        payload_info = {}
        cap_info = self._get_cpu_hardware_state(socket)['hardwareComponentData'][0]['stateCertificate']
        for cap in cap_info['stateCertificateDebugInfo']['capabilityActivationPayloads']:
            feature_set = [feature['featureShortName'] for feature in cap['features']]
            payload_info[cap['capabilityActivationPayloadRevision']] = feature_set
        return payload_info

    def get_active_feature_details(self, socket: int) -> Dict[int, List[str]]:
        """This method is used to retrieve the currently available features on the CPU that are currently active.

        Args:
            socket: the socket number to retrieve payload details of.

        Returns:
            Dict[int, List[str]]: Currenly active provisioned payloads with revision as key and feature names as value
                                 Ex: {1: ['IAA4'], 2: ['DLB4'], 3: ['DSA4'], 4: ['SGX512']}
        """
        payload_info = {}
        cap_info = self._get_cpu_hardware_state(socket)['hardwareComponentData'][0]['stateCertificate']
        for cap in cap_info['stateCertificateDebugInfo']['capabilityActivationPayloads']:
            feature_set = [feature['featureShortName'] for feature in cap['features'] if feature['isActiveNow']]
            payload_info[cap['capabilityActivationPayloadRevision']] = feature_set
        return payload_info

    def is_feature_available(self, feature_name: str, socket: int) -> bool:
        """This method is used to check whether a payload is provisioned on the CPU or not.

        Args:
            feature_name: Name of the payload which needs to be verified.
            socket: The socket number to check for payload provisioning.

        Returns:
            bool: True if the payload is available. False if the payload is not available.
        """
        for rev, payload in self.get_available_feature_details(socket).items():
            for feature in payload:
                if feature_name == feature:
                    self._log.info(f"CAP {feature_name} with revision {rev} available for socket {socket}.")
                    return True
        return False

    def is_feature_active(self, feature_name: str, socket: int) -> bool:
        """This method is used to check whether a payload is active on the CPU or not.

        Args:
            feature_name: Name of the payload which needs to be verified.
            socket: The socket number to check for payload provisioning.

        Returns:
            bool: True if the payload is active. False if the payload is not active.
        """
        for rev, payload in self.get_active_feature_details(socket).items():
            for feature in payload:
                if feature_name == feature:
                    self._log.info(f"CAP {feature_name} with revision {rev} available for socket {socket}.")
                    return True
        return False

    def apply_invalid_cpu_ppin_lac(self, socket: int):
        """This method is used to apply an incorrect CPU PPIN payload on the CPU.

        Args:
            socket: the socket to apply invalid payload to.

        Raises:
            MissingCapError: If no invalid cpu_ppin payloads are found for the given socket. BASICALLY EXPECTED
        """
        # Get ALL available payloads
        try:
            license_result = self._sut_os_tool.execute_cmd(self.FIND_LICENSE_CMD.format('*'), self.LICENSE_PATH)
        except OsCommandException as ex:
            error_msg = f"No license CAPs found in SUT path {self.LICENSE_PATH}"
            self._log.error(error_msg)
            raise SDSiExceptions.MissingCapError(error_msg) from ex

        # Attempt to apply a payload which does not belong to the given socket
        highest_revision = self.get_highest_revision_number(socket)
        hw_id = self.get_cpu_hw_asset_id(socket)
        for license_name in license_result.strip().splitlines():
            if hw_id not in license_name:
                revision_number = int(re.search(r'key_id_\d_rev_(.*?)_.*.json', license_name).group(1))
                if revision_number > highest_revision:
                    self.apply_lac(socket, (revision_number, license_name))
                    return

        # If no invalid payloads were found, raise error
        error_msg = f"No invalid license CAPs found in SUT path {self.LICENSE_PATH} for socket {socket}."
        self._log.error(error_msg)
        raise SDSiExceptions.MissingCapError(error_msg)

    def is_cpu_provisioned(self, socket: int) -> bool:
        """This method is used to check whether the CPU is in provisioned state or not.

        Args:
            socket: The socket number to check for provisioning.

        Returns:
            bool: True if the CPU is provisioned. False if the CPU is not provisioned.
        """
        return bool(self.get_available_feature_details(socket))

    def erase_provisioning(self) -> None:
        """This method is used to erase the previosly provisioned payloads on the SUT."""
        self._log.info("Clear any existing payloads from all sockets")
        for socket in range(self.num_sockets):
            if not self.get_ssku_updates_available(socket):
                self._log.info('No remaining SSKU updates available, rebooting SUT before applying erase key.')
                self._cycling_tool.perform_ac_cycle()
                break
        [self.erase_provisioning_socket(socket) for socket in range(self.num_sockets)]

    def erase_provisioning_socket(self, socket: int) -> None:
        """This method is used to erase the previosly provisioned payloads on a specific socket from the SUT.

        Args:
            socket: the socket to erase provisioning from.

        Raises:
            EraseProvisioningError: Raised if the erase command fails or if socket is still provisioned afterwards.
            AvailableUpdatesError: Raised if the erase provisioning fails due to unavailable SSKU updates.
        """
        if not self.is_cpu_provisioned(socket):
            self._log.info(f"Socket {socket} is not provisioned, nothing to erase.")
            return

        # Get register values before provisioning
        self._log.info(f"Get the register values for socket {socket} before applying LAC.")
        failure_counter_before_apply = self.get_license_certificate_fail_count(socket)
        ssku_updates_before = self.get_ssku_updates_available(socket)

        # Write the erase certificate to clear provisioning
        self._log.info(f"Applying the erase LAC for socket {socket}.")
        erase_certificate = 'MASTER_ERASE_LAC-EagleStream-00000000-FOR_PREPRODUCTION_CPUS_ONLY.json'
        erase_cmd = self._agent_erase_cmd.format(socket, erase_certificate)
        try:
            self._sut_os_tool.execute_cmd(erase_cmd, self.LICENSE_PATH)
        except OsCommandException:
            error_msg = f"Failed to apply {erase_certificate} CAP for socket {socket}."
            self._log.error(error_msg)
            raise SDSiExceptions.EraseProvisioningError(error_msg)

        # Validate Register values after applying erase certificate
        failure_counter_after_apply = self.get_license_certificate_fail_count(socket)
        ssku_updates_after = self.get_ssku_updates_available(socket)
        if failure_counter_after_apply > failure_counter_before_apply:
            error_msg = "Erase operation failed, Failure counter increased after writing erase certificate."
            self._log.error(error_msg)
            raise SDSiExceptions.EraseProvisioningError(error_msg)
        if ssku_updates_after != ssku_updates_before - 1:
            error_msg = f'Available SSKU updates did not decrease for socket {socket}.'
            self._log.error(error_msg)
            raise SDSiExceptions.AvailableUpdatesError(error_msg)

        if self.is_cpu_provisioned(socket):
            error_msg = f"Erase operation failed, socket {socket} still provisioned."
            self._log.error(error_msg)
            raise SDSiExceptions.EraseProvisioningError(error_msg)

        self._log.info(f"Provisioning erased from socket {socket}.")

    def apply_corrupt_certificate(self, socket: int) -> None:
        """This method is used to create and apply corrupted license key certificate to the CPU.

        Args:
            socket: The CPU socket to apply the corrupt certificate to.
        """
        self._log.info(f"Apply the corrupt licence key certificate to socket {socket}.")
        # Read contents of an available LAC
        available_lac = self.get_license_activation_code(socket)
        read_result = self._sut_os_tool.execute_cmd(f'cat {available_lac[1]}', self.LICENSE_PATH)

        # Corrupt the AKC content of the LAC
        lac_contents = json.loads(read_result.strip())
        old_akc = lac_contents['licenseActivationCode']['authenticationKeyCertificateValue']
        corrupt_akc = ''.join(random.sample(old_akc, len(old_akc)))
        lac_contents['licenseActivationCode']['authenticationKeyCertificateValue'] = corrupt_akc

        # Create the LAC file containing the corrupted contents
        corrupted_name = available_lac[1][:-5] + '_corrupted.json'
        create_cmd = f"echo '{json.dumps(lac_contents)}' > {corrupted_name}"
        self._sut_os_tool.execute_cmd(create_cmd, self.LICENSE_PATH)
        self._log.info(f"Corrupted key {corrupted_name} is generated.")

        # Attempt to apply the corrupted LAC
        try: self.apply_lac(socket, (available_lac[0], corrupted_name))
        finally:
            # Erase the corrupted LAC
            self._log.info(f"Erasing corrupted key {corrupted_name}.")
            erase_cmd = f'rm -rf {corrupted_name}'
            self._sut_os_tool.execute_cmd(erase_cmd, self.LICENSE_PATH)

    def apply_corrupt_lac(self, socket: int) -> None:
        """This method is used to create and apply corrupted license key certificate to the CPU.

        Args:
            socket: The CPU socket to apply the corrupt LAC to.
        """
        # Read contents of an available LAC
        available_lac = self.get_license_activation_code(socket)
        read_result = self._sut_os_tool.execute_cmd(f'cat {available_lac[1]}', self.LICENSE_PATH)

        # Corrupt the CAP content of the LAC
        lac = json.loads(read_result.strip())
        old_cap = lac['licenseActivationCode']['capabilityActivationPayloads'][0]['capabilityActivationPayloadValue']
        corrupted = ''.join(random.sample(old_cap, len(old_cap)))
        lac['licenseActivationCode']['capabilityActivationPayloads'][0]['capabilityActivationPayloadValue'] = corrupted

        # Create the LAC file containing the corrupted contents
        corrupted_name = available_lac[1][:-5] + '_corrupted.json'
        create_cmd = f"echo '{json.dumps(lac)}' > {corrupted_name}"
        self._sut_os_tool.execute_cmd(create_cmd, self.LICENSE_PATH)
        self._log.info(f"Corrupted LAC {corrupted_name} is generated.")

        # Attempt to apply the corrupted LAC
        try:
            self.apply_lac(socket, (available_lac[0], corrupted_name))
        finally:
            # Erase the corrupted LAC
            self._log.info(f"Erasing corrupted key {corrupted_name}.")
            erase_cmd = f'rm -rf {corrupted_name}'
            self._sut_os_tool.execute_cmd(erase_cmd, self.LICENSE_PATH)

    def _get_cpu_hardware_info(self) -> Dict[int, Dict[str, str]]:
        """This method is used to retrieve CPU Hardware information using the SDSi Agent read operation.

        Returns:
            Dict[int, Dict[str, str]]: hardware information for the platform.
                                       format {socket: {hw_key: hw_value}}
        """
        # Run SDSi Agent HW info command
        try:
            hw_response = self._sut_os_tool.execute_cmd(self._agent_read_hw_info_cmd, self.ROOT_PATH)
        except OsCommandException as ex:
            error_msg = f"Failed agent hardware read command."
            self._log.error(error_msg)
            raise SDSiExceptions.AgentReadError(error_msg) from ex

        # Parse HW info command results and repopulate HW info
        cpu_hw_info = {}
        hw_asset_information = hw_response.strip().split('\n')
        del hw_asset_information[1]
        for i, line in enumerate(hw_asset_information):
            hw_asset_information[i] = line.split('|') # noqa
            for j, col in enumerate(hw_asset_information[i]):
                hw_asset_information[i][j] = hw_asset_information[i][j].strip(' ') # noqa
        for socket_info in hw_asset_information[1:]:
            cpu_socket_number = int(socket_info[hw_asset_information[0].index('Index')])
            cpu_hw_info[cpu_socket_number] = {}
            for i, hw_detail in enumerate(socket_info):
                cpu_hw_info[cpu_socket_number][hw_asset_information[0][i]] = hw_detail
        return cpu_hw_info

    def _get_cpu_hardware_state(self, socket: int) -> dict:
        """This method is used to retrieve CPU hardware state information.

        Args:
            socket: The socket to check CPU hardware state information.

        Returns:
            dict: hardware information for the platform.

        Raises:
            SDSiExceptions.AgentReadError: If the hardware state read command fails
        """
        # Run SDSi Agent HW info command
        try:
            hw_response = self._sut_os_tool.execute_cmd(self._agent_read_hw_state_cmd.format(socket), self.ROOT_PATH)
        except OsCommandException as ex:
            error_msg = f"Failed agent hardware state read command."
            self._log.error(error_msg)
            raise SDSiExceptions.AgentReadError(error_msg) from ex
        return json.loads(hw_response.strip())

    def get_cpu_hw_asset_id(self, socket: int) -> str:
        """This method is used to retrieve CPU hardware state information.

        Args:
            socket: The socket number to get hw asset id of.

        Returns:
            str: The value of the cpu hardware id/ppin.
        """
        return self._get_cpu_hardware_info()[socket]['ID']

    def is_sdsi_enabled(self, socket: int) -> bool:
        """This method is used to get the sdsi enabled register for a given socket from the sdsi agent info command.

        Args:
            socket: The socket number to check is enabled for sdsi.

        Returns:
            bool:  True if sdsi is enabled on the socket, False if not.
        """
        return self._get_cpu_hardware_info()[socket]['SDSi enabled'] == 'YES'

    def get_license_auth_fail_count(self, socket: int) -> int:
        """This method is used to get the number of license authorization failures.

        Args:
            socket: The socket number to check license auth fail count of.

        Returns:
            int: Number of license authorization failures.

        Raises:
            SDSiExceptions.AgentReadError: If the register value is not found.
        """
        # Run SDSi Agent HW status command
        hw_state = self._get_cpu_hardware_state(socket)['hardwareComponentData'][0]
        register_info = hw_state['stateCertificate']['stateCertificateDebugInfo']['registers']
        for register in register_info:
            if register[0] == 'S3M_PROVISIONING_AUTH_FAILURE_COUNT.SSKU_LICENSE_AUTH_FAILURE_COUNT':
                return int(register[1], 0)

        # Raise error if register not found
        raise SDSiExceptions.AgentReadError('Failed to find register value.')

    def get_license_certificate_fail_count(self, socket: int) -> int:
        """This method is used to get the number of license key authorization failures.

        Args:
            socket: The socket number to check license key auth fail count of.

        Returns:
            int: Number of license key authorization failures.

        Raises:
            SDSiExceptions.AgentReadError: If the register value is not found.
        """
        # Run SDSi Agent HW status command
        hw_state = self._get_cpu_hardware_state(socket)['hardwareComponentData'][0]
        register_info = hw_state['stateCertificate']['stateCertificateDebugInfo']['registers']
        for register in register_info:
            if register[0] == 'S3M_PROVISIONING_AUTH_FAILURE_COUNT.SSKU_LICENSE_KEY_AUTH_FAILURE_COUNT':
                return int(register[1], 0)

        # Raise error if register not found
        raise SDSiExceptions.AgentReadError('Failed to find register value.')

    def get_max_license_certificate_fail_count(self, socket: int) -> int:
        """This method is used to get the max number of license key authorization failures.

        Args:
            socket: The socket number to check max license key auth fail count of.

        Returns:
            int: Number of max license key authorization failures

        Raises:
            SDSiExceptions.AgentReadError: If the register value is not found.
        """
        # Run SDSi Agent HW status command
        hw_state = self._get_cpu_hardware_state(socket)['hardwareComponentData'][0]
        register_info = hw_state['stateCertificate']['stateCertificateDebugInfo']['registers']
        for register in register_info:
            if register[0] == 'S3M_PROVISIONING_AUTH_FAILURE_COUNT.SSKU_LICENSE_KEY_AUTH_FAILURE_THRESHOLD':
                return int(register[1], 0)

        # Raise error if register not found
        raise SDSiExceptions.AgentReadError('Failed to find register value.')

    def get_max_license_auth_fail_count(self, socket: int) -> int:
        """This method is used to get the number of license authorization failures.

        Args:
            socket: The socket number to check max license auth fail count of.

        Returns:
            int: Number of max license authorization failures.

        Raises:
            SDSiExceptions.AgentReadError: If the register value is not found.
        """
        # Run SDSi Agent HW status command
        hw_state = self._get_cpu_hardware_state(socket)['hardwareComponentData'][0]
        register_info = hw_state['stateCertificate']['stateCertificateDebugInfo']['registers']
        for register in register_info:
            if register[0] == 'S3M_PROVISIONING_AUTH_FAILURE_COUNT.SSKU_LICENSE_AUTH_FAILURE_THRESHOLD':
                return int(register[1], 0)

        # Raise error if register not found
        raise SDSiExceptions.AgentReadError('Failed to find register value.')

    def get_ssku_updates_available(self, socket: int) -> int:
        """This method is used to get the remaining number of ssku updates available for the CPU socket.

        Args:
            socket: The socket number to check remaining SSKU updates available.

        Returns:
            int: The number of ssku updates remaining for the CPU socket.

        Raises:
            SDSiExceptions.AgentReadError: If the register value is not found.
        """
        # Run SDSi Agent HW status command
        hw_state = self._get_cpu_hardware_state(socket)['hardwareComponentData'][0]
        register_info = hw_state['stateCertificate']['stateCertificateDebugInfo']['registers']
        for register in register_info:
            if register[0] == 'S3M_PROVISIONING_AVAILABILITY.SSKU_UPDATES_AVAILABLE':
                return int(register[1], 0)

        # Raise error if register not found
        raise SDSiExceptions.AgentReadError('Failed to find register value.')

    def get_max_ssku_updates_available(self, socket: int) -> int:
        """This method is used to get the maximum number of ssku updates available per boot for the CPU.

        Args:
            socket: The socket number to check max SSKU updates available.

        Returns:
            int: The number of ssku updates remaining for the CPU.

        Raises:
            SDSiExceptions.AgentReadError: If the register value is not found.
        """
        # Run SDSi Agent HW status command
        hw_state = self._get_cpu_hardware_state(socket)['hardwareComponentData'][0]
        register_info = hw_state['stateCertificate']['stateCertificateDebugInfo']['registers']
        for register in register_info:
            if register[0] == 'S3M_PROVISIONING_AVAILABILITY.SSKU_UPDATES_THRESHOLD':
                return int(register[1], 0)

        # Raise error if register not found
        raise SDSiExceptions.AgentReadError('Failed to find register value.')

    def validate_default_registry_values(self) -> None:
        """Validate that the SDSi register values match expected values after a reboot.
        MUST REBOOT BEFORE VALIDATING.

        Raises:
            SDSiExceptions.LicenseKeyFailCountError: If the license key auth fail counter is not 0 after reboot.
            SDSiExceptions.CapFailCountError: If the CAP authentication failure counter is not 0 after reboot.
            SDSiExceptions.AvailableUpdatesError: If SSKU available updates is not reset to maximum after reboot.
        """
        # Loop through each socket and validate registers for each socket.
        for socket in range(self.num_sockets):
            self._log.info(f"Verify the default SDSi registers for socket {socket}.")

            if self.get_license_certificate_fail_count(socket) != 0:
                error_msg = f"License key failure counter is not reset to 0 for socket {socket} after reboot."
                self._log.error(error_msg)
                raise SDSiExceptions.LicenseKeyFailCountError(error_msg)
            if self.get_license_auth_fail_count(socket) != 0:
                error_msg = f" reset to 0 for socket {socket} after reboot."
                self._log.error(error_msg)
                raise SDSiExceptions.CapFailCountError(error_msg)
            if self.get_ssku_updates_available(socket) != self.get_max_ssku_updates_available(socket):
                error_msg = f"SSKU Updates available was not reset to maximum after reboot for socket {socket}."
                self._log.error(error_msg)
                raise SDSiExceptions.AvailableUpdatesError(error_msg)

            self._log.info(f"SDSi registers were reset to default as expected for socket {socket}.")

    def get_highest_revision_number(self, socket: int) -> int:
        """This method returns the highest revision number provisioned on the given socket.

        Args:
            socket: the socket number to check for the highest revision number

        Returns:
            int: the highest current revision provisioned on the socket.
        """
        # Parse highest revision number from state
        hw_state = self._get_cpu_hardware_state(socket)['hardwareComponentData'][0]['stateCertificate']
        cap_info = hw_state['stateCertificateDebugInfo']['capabilityActivationPayloads']
        return cap_info[-1]['capabilityActivationPayloadRevision'] if cap_info else 0

    def _request_and_install_license_on_sut(self, socket: int, features: List[str]) -> None:
        """This method will request the license with the given name using the API request tool, then transfer the LAC
        from the host to the SUT in the license directory.

        Args:
            socket: The socket number to install a license for.
            features: The name of the features to install a license of.
        """
        order_id = self._sdsi_license_tool.create_order([self.get_cpu_hw_asset_id(socket)], features)
        lac_path = self._sdsi_license_tool.install_license_package(order_id)[0]
        try:
            self._sut_os_tool.copy_local_file_to_sut(lac_path, self.LICENSE_PATH)
            chmod_cmd = 'chmod 777 {}'.format(os.path.basename(lac_path))
            self._sut_os_tool.execute_cmd(chmod_cmd, self.LICENSE_PATH)
        finally:
            os.remove(lac_path)
