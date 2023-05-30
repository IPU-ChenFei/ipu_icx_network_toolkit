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
import sys

from dtaf_core.lib.dtaf_constants import Framework

from src.sdsi.tests.provisioning.sgx.sdsi_sgx_common_test import SDSiSGXCommonTest


class SdsiApplyTwoMultipleFeatureLicenseBundlesWithSameFeatureUpgrades(SDSiSGXCommonTest):
    """
    Glasgow_ID: 70143
    Phoenix_ID: 18014074450
    This test case is to verify the OOB provisioning of the SSKU enabled CPU by applying the license key certificate,
    and a capability activation payload and verify it is available.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SdsiApplyTwoMultipleFeatureLicenseBundlesWithSameFeatureUpgrades

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(SdsiApplyTwoMultipleFeatureLicenseBundlesWithSameFeatureUpgrades, self).__init__(test_log, arguments,
                                                                                               cfg_opts)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""

        super(SdsiApplyTwoMultipleFeatureLicenseBundlesWithSameFeatureUpgrades, self).prepare()

        self._log.info("System memory available is {}".format(self.total_memory_available))
        minimum_memory_required = self.prm_size_to_apply["SG10"] / self._number_of_cpu
        minimum_memory_required = minimum_memory_required + (minimum_memory_required * 0.5)
        assert self.total_memory_available > minimum_memory_required, \
            "Not enough memory intalled on SUT. Available memory is {}GB. Please upgrade to at least {}GB." \
                .format(self.total_memory_available, minimum_memory_required)

    def execute(self):
        """
            1. Verify the license key auth fail count and payload auth fail count is 0.
            2. Get the CPU PPIN/Hardware ID of the CPU.
            3. Write the licence key certificate to the CPU. (If it is not present on the CPU)
            4. Write a random capability activation payload to the CPU.
            5. Verify the payload is available on the CPU.
            6. Verify the failure counter and max ssku updates counter values.
        """
        for cpu_counter in range(self._sdsi_obj.number_of_cpu):
            self._log.info("Write the licence key certificate for CPU_{}.".format(cpu_counter + 1))
            self._sdsi_obj.apply_license_key_certificate(cpu_counter)

        payload_info = []

        self._log.info(
            "Get the SSKU updates remaining and payload failure counter for CPU_1 before applying CAP.")
        payload_fail_count_before = self._sdsi_obj.get_license_auth_fail_count(socket=0)
        max_ssku_updates_before = self._sdsi_obj.get_ssku_updates_available(socket=0)

        self._log.info("Get a HQM4_SG40 CAP configuration for CPU_1.")
        payload_info.append(self._sdsi_obj.get_capability_activation_payload(socket=0, payload_name="IAX4_SG40"))

        self._log.info("Apply the CAP configuration for CPU_1.")
        self._sdsi_obj.apply_capability_activation_payload(payload_info[0], 0)

        self._log.info(
            "Get the SSKU updates remaining and payload failure counter for CPU_1 after applying CAP.")
        payload_fail_count_after = self._sdsi_obj.get_license_auth_fail_count(socket=0)
        max_ssku_updates_after = self._sdsi_obj.get_ssku_updates_available(socket=0)

        self._log.info(
            "Verify the payload failure and ssku updates available counters are updated as expected for CPU_1.")
        assert payload_fail_count_before == payload_fail_count_after, "Expected failure counter to be {}, but found {} for CPU_1.".format(
            payload_fail_count_before, payload_fail_count_after)
        assert max_ssku_updates_before - 1 == max_ssku_updates_after, "Expecting the max available ssku updates counter to be reduced by 1, but the values are Expected: {}, Found: {} for CPU_1.".format(
            max_ssku_updates_before, max_ssku_updates_after)

        self._log.info(
            "Get the SSKU updates remaining and payload failure counter for CPU_2 before applying CAP.")
        payload_fail_count_before = self._sdsi_obj.get_license_auth_fail_count(socket=1)
        max_ssku_updates_before = self._sdsi_obj.get_ssku_updates_available(socket=1)

        self._log.info("Get a IAX4_SG40 CAP configuration for CPU_2.")
        payload_info.append(self._sdsi_obj.get_capability_activation_payload(socket=1, payload_name="HQM4_SG40"))

        self._log.info("Apply the CAP configuration for CPU_2.")
        self._sdsi_obj.apply_capability_activation_payload(payload_info[1], 1)

        self._log.info(
            "Get the SSKU updates remaining and payload failure counter for CPU_2 after applying CAP.")
        payload_fail_count_after = self._sdsi_obj.get_license_auth_fail_count(socket=1)
        max_ssku_updates_after = self._sdsi_obj.get_ssku_updates_available(socket=1)

        self._log.info(
            "Verify the payload failure and ssku updates available counters are updated as expected for CPU_2.")
        assert payload_fail_count_before == payload_fail_count_after, "Expected failure counter to be {}, but found {} for CPU_2.".format(
            payload_fail_count_before, payload_fail_count_after)
        assert max_ssku_updates_before - 1 == max_ssku_updates_after, "Expecting the max available ssku updates counter to be reduced by 1, but the values are Expected: {}, Found: {} for CPU_2.".format(
            max_ssku_updates_before, max_ssku_updates_after)

        self._log.info("Cold reset the SUT to the provisioning to take effect.")
        self.perform_graceful_g3()

        for cpu_counter in range(self._sdsi_obj.number_of_cpu):
            ssku_updates_available = self._sdsi_obj.get_ssku_updates_available(socket=cpu_counter)
            max_ssku_updates_available = self._sdsi_obj.get_max_ssku_updates_available(socket=cpu_counter)
            assert ssku_updates_available == max_ssku_updates_available, "Expecting the max available ssku updates counter to be reduced by 1, but the values are Expected: {}, Found: {} for CPU_{}.".format(
                ssku_updates_available, max_ssku_updates_available, cpu_counter + 1)

            self._log.info("Verify the CAP config is available for CPU_{}.".format(cpu_counter + 1))
            assert self._sdsi_obj.is_payload_available(
                payload_name=payload_info[cpu_counter][1],
                socket=cpu_counter), "CPU_{} is not provisioned after write operation. {} CAP information is not found.".format(
                cpu_counter + 1, payload_info[cpu_counter][1])

        self._log.info("Set Prm size to {}GB for SG40.".format(self.prm_size_to_apply["SG40"] / self._number_of_cpu))
        self.set_and_validate_prm_size("SG40")

        hqm_devices = self._sdsi_obj.get_hqm_dlb_kernel()
        iax_devices = self._sdsi_obj.get_iax_kernel()
        assert len(
            hqm_devices) == 4, "Only CPU_1 is provisioned with HQM4. Only 4 devices are expected to list. But found {} devices.".format(
            len(hqm_devices))
        assert len(
            iax_devices) == 4, "Only CPU_2 is provisioned with IAX4. Only 4 devices are expected to list. But found {} devices.".format(
            len(iax_devices))

        payload_info.clear()

        self._log.info("Perform SGX operation for HQM2 and validate.")
        self.perform_and_validate_sgx_operation("HQM2")

        hqm_devices = self._sdsi_obj.get_hqm_dlb_kernel()
        iax_devices = self._sdsi_obj.get_iax_kernel()
        assert len(
            hqm_devices) == 4, "CPU_1 and CPU_2 are provisioned with HQM2. Only 4 devices are expected to list. But found {} devices.".format(
            len(hqm_devices))
        assert len(
            iax_devices) == 4, "Only CPU_2 is provisioned with IAX4. Only 4 devices are expected to list. But found {} devices.".format(
            len(iax_devices))

        self._log.info("Set Prm size to {}GB for SG40.".format(self.prm_size_to_apply["SG40"] / self._number_of_cpu))
        self.set_and_validate_prm_size("SG40")

        payload_info.clear()

        self._log.info("Perform provision operation for HQM0_IAX2_SG04 and validate.")
        for cpu_counter in range(self._sdsi_obj.number_of_cpu):
            self._log.info(
                "Get the SSKU updates remaining and payload failure counter for CPU_{} before applying CAP.".format(
                    cpu_counter + 1))
            payload_fail_count_before = self._sdsi_obj.get_license_auth_fail_count(socket=cpu_counter)
            max_ssku_updates_before = self._sdsi_obj.get_ssku_updates_available(socket=cpu_counter)

            self._log.info("Get HQM0_IAX2_SG04 CAP configuration for CPU_{}.".format(cpu_counter + 1))
            payload_info = self._sdsi_obj.return_to_base(payload_name="HQM0_IAX2_SG04", socket=cpu_counter)

            self._log.info(
                "Get the SSKU updates remaining and payload failure counter for CPU_{} after applying CAP.".format(
                    cpu_counter + 1))
            payload_fail_count_after = self._sdsi_obj.get_license_auth_fail_count(socket=cpu_counter)
            max_ssku_updates_after = self._sdsi_obj.get_ssku_updates_available(socket=cpu_counter)

            self._log.info(
                "Verify the payload failure and ssku updates available counters are updated as expected for CPU_{}.".format(
                    cpu_counter + 1))
            assert payload_fail_count_before == payload_fail_count_after, "Expected failure counter to be {}, but found {} for CPU_{}.".format(
                payload_fail_count_before, payload_fail_count_after, cpu_counter + 1)
            assert max_ssku_updates_before - 1 == max_ssku_updates_after, "Expecting the max available ssku updates counter to be reduced by 1, but the values are Expected: {}, Found: {} for CPU_{}.".format(
                max_ssku_updates_before, max_ssku_updates_after, cpu_counter + 1)

        self._log.info("Cold reset the SUT to the provisioning to take effect.")
        self.perform_graceful_g3()

        for cpu_counter in range(self._sdsi_obj.number_of_cpu):
            ssku_updates_available = self._sdsi_obj.get_ssku_updates_available(socket=cpu_counter)
            max_ssku_updates_available = self._sdsi_obj.get_max_ssku_updates_available(socket=cpu_counter)
            assert ssku_updates_available == max_ssku_updates_available, "Expecting the max available ssku updates counter to be reduced by 1, but the values are Expected: {}, Found: {} for CPU_{}.".format(
                ssku_updates_available, max_ssku_updates_available, cpu_counter + 1)

            self._log.info("Verify the CAP config is available for CPU_{}.".format(cpu_counter + 1))
            assert self._sdsi_obj.is_payload_available(
                payload_name=payload_info[1],
                socket=cpu_counter), "CPU_{} is not provisioned after write operation. {} CAP information is not found.".format(
                cpu_counter + 1, payload_info[1])
        ## break

        hqm_devices = self._sdsi_obj.get_hqm_dlb_kernel()
        iax_devices = self._sdsi_obj.get_iax_kernel()
        assert len(
            hqm_devices) == 0, "CPU_1 and CPU_2 are provisioned with HQM2. Only 4 devices are expected to list. But found {} devices.".format(
            len(hqm_devices))
        assert len(
            iax_devices) == 4, "CPU_1 and CPU_2 are provisioned with IAX2. Only 4 devices are expected to list. But found {} devices.".format(
            len(iax_devices))

        self._log.info("Verify the PRM memory size is not the size set for SG40 after applying SG04.")
        current_prm_memory_size = self.bios_util.get_bios_knob_current_value("PrmSize")
        current_prm_size_in_gb = int(current_prm_memory_size, 16) / pow(1024, 3)
        self._log.info("Prm memory size after going down to SG08 from SG40 is {}GB.".format(current_prm_size_in_gb))
        assert (self.prm_size_to_apply["SG40"] / self._number_of_cpu) != current_prm_size_in_gb, \
            "Current Prm size is same as of SG40. It should be reduced after applying SG08."
        ###
        self._log.info(
            "Verify the Prm size to cannot be set to {}GB after RTB.".format(
                (self.prm_size_to_apply["SG40"] / self._number_of_cpu)))
        self.bios_util.set_single_bios_knob("PrmSize",
                                            self.PRM_SIZE_SET[
                                                self.prm_size_to_apply["SG40"] / self._number_of_cpu])

        self._log.info("Powercycle the SUT for the BIOS changes to take effect.")
        self.perform_graceful_g3()

        self._log.info(
            "Verify the PRM memory size is not set to {}GB after powercycle.".format(self.prm_size_to_apply["SG40"]))
        current_prm_memory_size = self.bios_util.get_bios_knob_current_value("PrmSize")
        current_prm_size_in_gb = int(current_prm_memory_size, 16) / pow(1024, 3)
        self._log.info("Current Prm memory size is {}GB.".format(current_prm_size_in_gb))
        assert (self.prm_size_to_apply["SG40"] / self._number_of_cpu) != current_prm_size_in_gb, \
            "Prm memory size is still set to {}GB.".format(self.prm_size_to_apply["SG40"])
        ###
        self._log.info("Set the Prm size to default 32GB")
        self.bios_util.set_single_bios_knob("PrmSize", self.PRM_SIZE_SET[32])

        self._log.info("Powercycle the SUT for the BIOS changes to take effect.")
        self.perform_graceful_g3()

        self._log.info("Verify the PRM memory size is set to 32GB after powercycle.")
        current_prm_memory_size = self.bios_util.get_bios_knob_current_value("PrmSize")
        current_prm_size_in_gb = int(current_prm_memory_size, 16) / pow(1024, 3)
        self._log.info("Current Prm memory size is 32GB.")
        assert int(self.PRM_SIZE_SET[32], 16) / pow(1024, 3) == current_prm_size_in_gb, \
            "Prm memory size is not set to 32GB."

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        self._log.info("Perform graceful G3 for resetting the counters after test irrespective of pass/fail.")
        self.perform_graceful_g3()
        super(SdsiApplyTwoMultipleFeatureLicenseBundlesWithSameFeatureUpgrades, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SdsiApplyTwoMultipleFeatureLicenseBundlesWithSameFeatureUpgrades.main()
             else Framework.TEST_RESULT_FAIL)
