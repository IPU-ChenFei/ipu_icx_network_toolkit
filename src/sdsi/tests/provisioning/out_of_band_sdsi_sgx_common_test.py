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
from math import isclose

from src.lib.content_base_test_case import ContentBaseTestCase
from src.sdsi.lib.sdsi_common_lib import SDSICommonLib
from src.sdsi.lib.sdsi_installer_lib import SDSIInstallerLib


class SDSiSGXCommonTest(ContentBaseTestCase):
    """
    This is a base class for SGX test cases where all the SGX related additional functions are performed here.
    This test enables SGX by default and contains functions to enable SGX payloads and change SgxPrmSize bios knob
    """

    SGX_BIOS_DEFAULT = "sgx_bios_knobs.cfg"
    PRM_SIZE_SET = {1: "0x40000000", 2: "0x80000000", 4: "0x100000000", 8: "0x200000000",
                    16: "0x400000000", 32: "0x800000000", 64: "0x1000000000", 128: "0x2000000000", 256: "0x4000000000"}
    PRM_DEFAULT = 16

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SDSiSGXCommonTest
        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        super(SDSiSGXCommonTest, self).__init__(test_log, arguments, cfg_opts, self.SGX_BIOS_DEFAULT)
        self._sdsi_installer = SDSIInstallerLib(self._log, self.os, self._common_content_lib,
                                                self._common_content_configuration, self.ac_power)
        self._sdsi_obj = SDSICommonLib(self._log, self.os, self._common_content_lib, self._common_content_configuration,
                                       self._sdsi_installer, self.ac_power)
        self.prm_size_to_apply = {"SG04": 32, "SG08": 64, "SG10": 128, "SG20": 256, "SG40": 512}
        self.initial_memory_available = self._sdsi_obj.get_total_memory_in_gb()

    def prepare(self):
        # type: () -> None
        """
            Perform common test preparation.
            Clear existing payloads and set Sgx values to default.
        """
        super(SDSiSGXCommonTest, self).prepare()
        self._log.info("Clear any existing payloads from the CPU")
        self._sdsi_obj.erase_payloads_from_nvram()
        self._log.info("Set the PrmSgxSize to default {}GB.".format(self.PRM_DEFAULT))
        self.perform_graceful_g3()
        assert self.set_and_validate_prm_size(self.PRM_DEFAULT), "Failed to set SgxPrmSize default"
        self._log.info("Verify the license key auth fail count and payload auth fail count is 0.")
        self._sdsi_obj.validate_default_registry_values()

    def cleanup(self, return_status):
        # type: (bool) -> None
        """
            Perform common test cleanup
        """
        self._log.info("Perform graceful G3 for resetting the counters after test irrespective of pass/fail.")
        self.perform_graceful_g3()
        super(SDSiSGXCommonTest, self).cleanup(return_status)

    def perform_and_validate_sgx_operation(self, feature_name):
        """
            Enable sgx payload and validate the payload was applies
            :param feature_name: The name of the Sgx feature to enable
        """
        self._log.info("Perform SGX operation for {} and validate.".format(feature_name))
        payload_info = []
        for cpu_counter in range(self._sdsi_obj.number_of_cpu):
            self._log.info("Get the SSKU updates remaining and payload failure counter for CPU{} before applying CAP."
                           .format(cpu_counter + 1))
            payload_fail_count_before = self._sdsi_obj.get_license_auth_fail_count(socket=cpu_counter)
            max_ssku_updates_before = self._sdsi_obj.get_ssku_updates_available(socket=cpu_counter)

            self._log.info("Get {} CAP configuration for CPU{}.".format(feature_name, cpu_counter + 1))
            payload_info.append(self._sdsi_obj.get_capability_activation_payload(socket=cpu_counter,
                                                                                 payload_name=feature_name))

            self._log.info("Apply the CAP configuration for CPU{}.".format(cpu_counter))
            self._sdsi_obj.apply_capability_activation_payload(payload_info[cpu_counter], cpu_counter)

            self._log.info("Get the SSKU updates remaining and payload failure counter for CPU{} after applying CAP."
                           .format(cpu_counter))
            payload_fail_count_after = self._sdsi_obj.get_license_auth_fail_count(socket=cpu_counter)
            max_ssku_updates_after = self._sdsi_obj.get_ssku_updates_available(socket=cpu_counter)

            self._log.info("Verify the payload failure and ssku updates available counters are updated as "
                           "expected for CPU_{}.".format(cpu_counter + 1))
            assert payload_fail_count_before == payload_fail_count_after, \
                "Expected failure counter to be {}, but found {} for CPU_{}." \
                .format(payload_fail_count_before, payload_fail_count_after, cpu_counter + 1)
            assert max_ssku_updates_before - 1 == max_ssku_updates_after, \
                "Expecting the max available SSKU updates counter to be reduced by 1, but the values are Expected: {},"\
                " Found: {} for CPU_{}.".format(max_ssku_updates_before, max_ssku_updates_after, cpu_counter + 1)

        self._log.info("Cold reset the SUT to the provisioning to take effect.")
        self.perform_graceful_g3()

        for cpu_counter in range(self._sdsi_obj.number_of_cpu):
            self._log.info("Verify SSKU Updates reset to max after reboot for CPU{}.".format(cpu_counter + 1))
            ssku_updates_available = self._sdsi_obj.get_ssku_updates_available(socket=cpu_counter)
            max_ssku_updates_available = self._sdsi_obj.get_max_ssku_updates_available(socket=cpu_counter)
            assert ssku_updates_available == max_ssku_updates_available, \
                "Available SSKU Updates should be max for CPU{} after cold reboot, Expected: {}, Found: {}" \
                .format(cpu_counter + 1, max_ssku_updates_available, ssku_updates_available)

            self._log.info("Verify the CAP config is available for CPU{}.".format(cpu_counter + 1))
            assert self._sdsi_obj.is_payload_available(
                payload_name=payload_info[cpu_counter][1],
                socket=cpu_counter), "CPU{} is not provisioned after write operation. {} CAP information is not found." \
                .format(cpu_counter + 1, payload_info[cpu_counter][1])

    def set_and_validate_prm_size(self, size_in_gb) -> bool:
        """
            Set the SgxPrmSize knob to the given size
            :param size_in_gb: The size in GB of the SgxPrmSize to enable. This size is TOTAL GB, not per cpu
            :returns: If the operation was a success. A success is classified by the SgxPrmSize knob being properly set,
                      and the system available memory decreasing by the same amount (within 15%)
        """
        memory_deviation = 0.15
        self._log.info("Set the Prm size to {}GB".format(size_in_gb / self._sdsi_obj.number_of_cpu))
        self.bios_util.set_single_bios_knob("PrmSgxSize", self.PRM_SIZE_SET[size_in_gb / self._sdsi_obj.number_of_cpu])

        self._log.info("Power cycle the SUT for the BIOS changes to take effect.")
        self.perform_graceful_g3()

        current_prm_memory_size = self.bios_util.get_bios_knob_current_value("PrmSgxSize")
        current_prm_size_in_gb = int(current_prm_memory_size, 16) / pow(1024, 3) * self._sdsi_obj.number_of_cpu
        self._log.info("Current Prm memory size is {}GB.".format(current_prm_size_in_gb))
        prm_set_success = (size_in_gb == current_prm_size_in_gb)
        self._log.info("PrmSgxSize is set to given size after power cycle: {}".format(str(prm_set_success)))

        self._log.info("Memory before setting SgxPrmSize was {}GB".format(self.initial_memory_available))
        total_memory_after_sgx = self._sdsi_obj.get_total_memory_in_gb()
        self._log.info("Current system memory size available is {}GB.".format(total_memory_after_sgx))
        memory_difference = self.initial_memory_available - total_memory_after_sgx
        self._log.info("Memory difference after is {}GB.".format(memory_difference))
        self._log.info("Memory difference within {}% of Prm value set: {}".format(
                        str(memory_deviation * 100),
                        isclose(memory_difference, size_in_gb, rel_tol=memory_deviation)))
        prm_set_success = True if isclose(memory_difference, size_in_gb, rel_tol=memory_deviation) else prm_set_success
        return prm_set_success
