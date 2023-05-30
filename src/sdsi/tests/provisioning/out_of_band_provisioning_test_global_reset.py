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


class OutOfBandProvisioningTestGlobalReset(ContentBaseTestCase):
    """
    Glasgow_ID: 69671
    Phoenix_ID: 18014075658
    This test case is to verify the OOB provisioning of the SSKU enabled CPU by applying the license key certificate,
    and a capability activation payload and verify it is available with Global reset enabled.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of OutOfBandProvisioningTestGlobalReset

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(OutOfBandProvisioningTestGlobalReset, self).__init__(test_log, arguments, cfg_opts)
        self._sdsi_installer = SDSIInstallerLib(self._log, self.os, self._common_content_lib,
                                                self._common_content_configuration, self.ac_power)
        self._sdsi_obj = SDSICommonLib(self._log, self.os, self._common_content_lib,
                                       self._common_content_configuration, self._sdsi_installer, self.ac_power)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(OutOfBandProvisioningTestGlobalReset, self).prepare()

        self._log.info("Verify the license key auth fail count and payload auth fail count is 0.")
        self._sdsi_obj.validate_default_registry_values()

    def execute(self):
        """
            1. Enable Global Reset by disabling Global Reset Lock in the BIOS.
            2. Verify the license key auth fail count and payload auth fail count is 0.
            3. Get the CPU PPIN/Hardware ID of the CPU.
            4. Write the licence key certificate to the CPU. (If it is not present on the CPU)
            5. Write a random capability activation payload to the CPU.
            6. Verify the payload is available on the CPU.
            7. Verify the failure counter and max ssku updates counter values.
        """
        self._log.info("Enable Global Reset by disabling Global Reset Lock in the BIOS.")
        global_reset_value = "0x0"
        self.bios_util.set_single_bios_knob("MeGrLockEnabled", "0x0")

        self._log.info("Powercycle the SUT for the BIOS changes to take effect.")
        self.perform_graceful_g3()

        self._log.info("Verify the Global reset is enabled")
        current_global_reset = self.bios_util.get_bios_knob_current_value("MeGrLockEnabled")
        if int(current_global_reset, 16) != int(global_reset_value, 16):
            log_error = "Global reset is not enabled."
            self._log.error(log_error)
            raise RuntimeError(log_error)

        for cpu_counter in range(self._sdsi_obj.number_of_cpu):
            self._log.info("Write the licence key certificate for CPU{}.".format(cpu_counter))
            self._sdsi_obj.apply_license_key_certificate(cpu_counter)

            self._log.info(
                "Get the SSKU updates remaining and payload failure counter for CPU{} before applying CAP.".format(
                    cpu_counter))
            payload_fail_count_before = self._sdsi_obj.get_license_auth_fail_count(socket=cpu_counter)
            max_ssku_updates_before = self._sdsi_obj.get_ssku_updates_available(socket=cpu_counter)

            self._log.info("Get a random CAP configuration for CPU{}.".format(cpu_counter))
            payload_info = self._sdsi_obj.get_capability_activation_payload(socket=cpu_counter)

            self._log.info("Apply the CAP configuration for CPU{}.".format(cpu_counter))
            self._sdsi_obj.apply_capability_activation_payload(payload_info, cpu_counter)

            self._log.info(
                "Get the SSKU updates remaining and payload failure counter for CPU{} after applying CAP.".format(
                    cpu_counter))
            payload_fail_count_after = self._sdsi_obj.get_license_auth_fail_count(socket=cpu_counter)
            max_ssku_updates_after = self._sdsi_obj.get_ssku_updates_available(socket=cpu_counter)

            self._log.info(
                "Verify the payload failure and ssku updates available counters are updated as expected for CPU{}.".format(
                    cpu_counter))
            assert payload_fail_count_before == payload_fail_count_after, "Expected failure counter to be {}, but found {} for CPU {}.".format(
                payload_fail_count_before, payload_fail_count_after, cpu_counter)
            assert max_ssku_updates_before - 1 == max_ssku_updates_after, "Expecting the max available ssku updates counter to be reduced by 1, but the values are Expected: {}, Found: {} for CPU {}.".format(
                max_ssku_updates_before, max_ssku_updates_after, cpu_counter)

        self._log.info("Cold reset the SUT to the provisioning to take effect.")
        self.perform_graceful_g3()

        for cpu_counter in range(self._sdsi_obj.number_of_cpu):
            ssku_updates_available = self._sdsi_obj.get_ssku_updates_available(socket=cpu_counter)
            max_ssku_updates_available = self._sdsi_obj.get_max_ssku_updates_available(socket=cpu_counter)
            assert ssku_updates_available == max_ssku_updates_available, "Expecting the max available ssku updates counter to be reduced by 1, but the values are Expected: {}, Found: {} for CPU {}.".format(
                ssku_updates_available, max_ssku_updates_available, cpu_counter)

            self._log.info("Verify the CAP config is available for CPU{}.".format(cpu_counter))
            assert self._sdsi_obj.is_payload_available(
                payload_name=payload_info[1],
                socket=cpu_counter), "CPU{} is not provisioned after write operation. {} CAP information is not found.".format(
                cpu_counter, payload_info[1])

            self._log.info("CAP config is applied successfully for CPU{}.".format(cpu_counter))

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        self._log.info("Disable Global Reset by enabling Global Reset Lock in the BIOS.")
        global_reset_value = "0x1"
        self.bios_util.set_single_bios_knob("MeGrLockEnabled", global_reset_value)

        self._log.info("Perform graceful G3 for resetting the counters after test irrespective of pass/fail and for the BIOS changes to take effect.")
        self.perform_graceful_g3()

        self._log.info("Verify the Global reset is disabled")
        current_global_reset = self.bios_util.get_bios_knob_current_value("MeGrLockEnabled")
        if int(current_global_reset, 16) != int(global_reset_value, 16):
            log_error = "Global reset is not disabled."
            self._log.error(log_error)
            raise RuntimeError(log_error)
        super(OutOfBandProvisioningTestGlobalReset, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if OutOfBandProvisioningTestGlobalReset.main()
             else Framework.TEST_RESULT_FAIL)
