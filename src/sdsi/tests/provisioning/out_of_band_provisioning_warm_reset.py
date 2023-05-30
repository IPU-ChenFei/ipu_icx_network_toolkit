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

from src.lib.content_base_test_case import ContentBaseTestCase
from src.sdsi.lib.sdsi_common_lib import SDSICommonLib
from src.sdsi.lib.sdsi_installer_lib import SDSIInstallerLib


class OutOfBandProvisioningWarmReset(ContentBaseTestCase):
    """
    Glasgow_ID: 69672
    Phoenix_ID: 18014075512
    This test is to verify after applying the CAP, the ssku updates available counter is not reset to default value
    after the warm reset of the SUT.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of OutOfBandProvisioningWarmReset

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(OutOfBandProvisioningWarmReset, self).__init__(test_log, arguments, cfg_opts)
        self._sdsi_installer = SDSIInstallerLib(self._log, self.os, self._common_content_lib,
                                                self._common_content_configuration, self.ac_power)
        self._sdsi_obj = SDSICommonLib(self._log, self.os, self._common_content_lib,
                                       self._common_content_configuration, self._sdsi_installer, self.ac_power)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(OutOfBandProvisioningWarmReset, self).prepare()

        self._log.info("Verify the SPR_SDSi_Installer by initiating --help command.")
        self._sdsi_installer.verify_sdsi_installer()

        self._log.debug("Number of sockets connected on the platform is : {}".format(self._sdsi_obj.number_of_cpu))

        self._log.info("Verify the license key auth fail count and payload auth fail count is 0.")

        for cpu_counter in range(self._sdsi_obj.number_of_cpu):
            self._log.info("Verify the failure counters for CPU_{} after graceful G3.".format(cpu_counter + 1))
            license_key_auth_failures = self._sdsi_obj.get_license_key_auth_fail_count(cpu_counter)
            payload_auth_fail_count = self._sdsi_obj.get_license_auth_fail_count(cpu_counter)

            assert license_key_auth_failures == 0, \
                "License key failure counter is not reset to 0 for CPU_{}.".format(cpu_counter + 1)
            self._log.info("License key authentication counter is set to 0 for CPU_{}.".format(cpu_counter + 1))

            assert payload_auth_fail_count == 0, \
                "CAP authentication failure counter is not reset to 0 for CPU_{}.".format(cpu_counter + 1)
            self._log.info("CAP authentication failure counter is set to 0 for CPU_{}.".format(cpu_counter + 1))

            self._log.info("Get the CPU PPIN/Hardware ID of the CPU.")
            cpu_ppin = self._sdsi_obj.get_cpu_hw_asset_id(cpu_counter)
            self._log.info("CPU PPIN/Hardware Asset ID of the CPU_{} is '{}'".format(cpu_counter + 1, cpu_ppin))

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
            self._log.info("Write the licence key certificate for CPU{}.".format(cpu_counter + 1))
            self._sdsi_obj.apply_license_key_certificate(cpu_counter)

            self._log.info(
                "Read the SSKU updates remaining counter for CPU{} before applying CAP.".format(cpu_counter + 1))
            payload_fail_count_before = self._sdsi_obj.get_license_auth_fail_count(socket=cpu_counter)
            ssku_updates_before_cap = self._sdsi_obj.get_ssku_updates_available(socket=cpu_counter)
            self._log.info("Get a random CAP configuration for CPU{}.".format(cpu_counter + 1))
            payload_info = self._sdsi_obj.get_capability_activation_payload(socket=cpu_counter)
            self._log.info("Apply the CAP configuration for CPU{}.".format(cpu_counter + 1))
            self._sdsi_obj.apply_capability_activation_payload(payload_info, cpu_counter)
            self._log.info("Write a payload configuration to the SUT for CPU {}.".format(cpu_counter + 1))
            payload_name = payload_info[1]
            self._log.info(
                "Read the SSKU updates remaining counter for CPU{} after applying CAP.".format(cpu_counter + 1))
            ssku_updates_after_cap = self._sdsi_obj.get_ssku_updates_available(socket=cpu_counter)
            self._log.info("Verify the ssku updates available is reduced by 1 after applying the CAP for CPU{}.".format(
                cpu_counter + 1))
            assert ssku_updates_before_cap - 1 == ssku_updates_after_cap, "Expecting the max available ssku updates counter to reduced by 1, but the values are Expected: {}, Found: {} for CPU {}.".format(
                ssku_updates_before_cap - 1, ssku_updates_after_cap, cpu_counter + 1)

        self._log.info("Perform a warm reset on SUT.")
        self._common_content_lib.perform_os_reboot(self.reboot_timeout)

        for cpu_counter in range(self._sdsi_obj.number_of_cpu):
            self._log.info(
                "Read the SSKU updates remaining counter for CPU{} after warm reset.".format(cpu_counter + 1))
            payload_fail_count_after = self._sdsi_obj.get_license_auth_fail_count(socket=cpu_counter)
            ssku_updates_after_warm_reset = self._sdsi_obj.get_ssku_updates_available(socket=cpu_counter)
            self._log.info(
                "Verify the ssku updates available is not reset to default value after warm reset for CPU{}.".format(
                    cpu_counter + 1))
            assert payload_fail_count_before == payload_fail_count_after, "Expected failure counter to be {}, but found {} for CPU {}.".format(
                payload_fail_count_before, payload_fail_count_after, cpu_counter + 1)
            assert ssku_updates_before_cap - 1 == ssku_updates_after_warm_reset, "Expecting the available ssku updates counter not to reset to default value after warm reset of SUT, but the values are Expected: {}, Found: {} for CPU {}.".format(
                ssku_updates_before_cap - 1, ssku_updates_after_warm_reset, cpu_counter + 1)

        self._log.info("Perform a cold reset.")
        self._sdsi_obj.perform_graceful_powercycle()

        for cpu_counter in range(self._sdsi_obj.number_of_cpu):
            self._log.info(
                "Read the SSKU updates remaining counter for CPU{} after cold reset.".format(cpu_counter + 1))
            payload_fail_count_after = self._sdsi_obj.get_license_auth_fail_count(socket=cpu_counter)
            ssku_updates_after_cold_reset = self._sdsi_obj.get_ssku_updates_available(socket=cpu_counter)
            self._log.info(
                "Verify the ssku updates available is reset to default value after cold reset for CPU{}.".format(
                    cpu_counter + 1))
            assert payload_fail_count_before == payload_fail_count_after, "Expected failure counter to be {}, but found {} for CPU {}.".format(
                payload_fail_count_before, payload_fail_count_after, cpu_counter + 1)
            assert ssku_updates_before_cap == ssku_updates_after_cold_reset, "Expecting the available ssku updates counter to be equal to the value before applying the CAP, but the values are Expected: {}, Found: {} for CPU {}.".format(
                ssku_updates_before_cap, ssku_updates_after_cold_reset, cpu_counter + 1)

            self._log.info(
                "Verify the CAP configuration is available on the NVRAM for CPU{}.".format(cpu_counter + 1))
            assert self._sdsi_obj.is_payload_available(
                payload_name=payload_name,
                socket=cpu_counter), "CPU {} is not provisioned after the write operation. Payload information for {} is not found.".format(
                cpu_counter + 1, payload_name)

            self._log.info("CAP configuration is applied successfully for CPU{}.".format(cpu_counter + 1))

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        self._log.info("Perform graceful G3 for resetting the counters after test irrespective of pass/fail.")
        self.perform_graceful_g3()
        super(OutOfBandProvisioningWarmReset, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if OutOfBandProvisioningWarmReset.main()
             else Framework.TEST_RESULT_FAIL)
