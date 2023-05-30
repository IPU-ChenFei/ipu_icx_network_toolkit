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
import sys

from dtaf_core.lib.dtaf_constants import Framework

import src.sdsi.lib.sdsi_exceptions as SDSiExceptions
from src.lib.content_base_test_case import ContentBaseTestCase
from src.sdsi.lib.in_band_sdsi_common_lib import SDSICommonLib
from src.sdsi.lib.sdsi_installer_lib import SDSIInstallerLib


class InBandProvisioningUsingIncorrectCpuPpin(ContentBaseTestCase):
    """
    Glasgow_ID: 70146
    Phoenix_ID: 18014075537
    This test is to verify the platform behavior when attempting to apply a license to an incorrect CPU PPIN via In Band
    """
    _INCORRECT_CPU_PPIN_PAYLOAD = "084DE64A6F06E13D_key_id_1_rev_11_SSTE.bin"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of InBandProvisioningUsingIncorrectCpuPpin

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(InBandProvisioningUsingIncorrectCpuPpin, self).__init__(test_log, arguments, cfg_opts)
        self.incorrect_payload_path = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                   self._INCORRECT_CPU_PPIN_PAYLOAD)
        self._sdsi_installer = SDSIInstallerLib(self._log, self.os, self._common_content_lib,
                                                self._common_content_configuration, self.ac_power)
        self._sdsi_obj = SDSICommonLib(self._log, self.os, self._common_content_lib,
                                       self._common_content_configuration, self._sdsi_installer, self.ac_power)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(InBandProvisioningUsingIncorrectCpuPpin, self).prepare()

        self._log.info("Verify the SPR_SDSi_Installer by initiating --help command.")
        self._sdsi_installer.verify_sdsi_installer()

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
            3. Apply the licence key certificate to the CPU. (If it is not present on the CPU)
            4. Apply an incorrect CPU PPIN payload to the CPU.
            5. Verify the payload is not applied by checking the failure counters.
        """

        for cpu_counter in range(self._sdsi_obj.number_of_cpu):
            self._log.info("Write the licence key certificate for CPU{}.".format(cpu_counter + 1))
            self._sdsi_obj.apply_license_key_certificate(cpu_counter)

            self._log.info(
                "Read the SSKU updates remaining and payload failure counter for CPU{} before applying CAP.".format(
                    cpu_counter + 1))
            payload_fail_count_before = self._sdsi_obj.get_license_auth_fail_count(socket=cpu_counter)
            max_ssku_updates_before = self._sdsi_obj.get_ssku_updates_available(socket=cpu_counter)

            self._log.info("Get the incorrect CPU PPIN CAP binary")
            incorrect_cap = self._sdsi_obj.get_incorrect_cpu_ppin_cap(payload_name=self.incorrect_payload_path)

            self._log.info("Apply a CAP configuration for CPU{}.".format(cpu_counter + 1))
            try:
                self._sdsi_obj.apply_capability_activation_payload(incorrect_cap, cpu_counter)
            except SDSiExceptions.ProvisioningError:
                pass

            # self._log.info("Apply a CAP configuration for CPU{}.".format(cpu_counter))
            # payload_name = self._sdsi_obj.apply_invalid_cpu_ppin_payload(payload_name=self.incorrect_payload_path,
            #                                                              socket=cpu_counter)

            self._log.info(
                "Read the SSKU updates remaining and payload failure counter for CPU{} after applying CAP.".format(
                    cpu_counter + 1))
            payload_fail_count_after = self._sdsi_obj.get_license_auth_fail_count(socket=cpu_counter)
            max_ssku_updates_after = self._sdsi_obj.get_ssku_updates_available(socket=cpu_counter)

            self._log.info(
                "Verify the payload failure counter and max ssku updates available counter values are updated as expected for CPU{}.".format(
                    cpu_counter + 1))
            assert payload_fail_count_before + 1 == payload_fail_count_after, "Expected failure counter to be {}, but found {} for CPU{}.".format(
                payload_fail_count_before + 1, payload_fail_count_after, cpu_counter + 1)
            assert max_ssku_updates_before == max_ssku_updates_after, "Expecting the max available ssku updates counter to be unchanged, but the values are Expected: {}, Found: {} for CPU{}".format(
                max_ssku_updates_before, max_ssku_updates_after, cpu_counter + 1)

            self._log.info("Incorrect Capability activation payload is not applied for CPU{}.".format(cpu_counter + 1))

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        self._log.info("Perform graceful G3 for resetting the counters after test irrespective of pass/fail.")
        self.perform_graceful_g3()
        super(InBandProvisioningUsingIncorrectCpuPpin, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if InBandProvisioningUsingIncorrectCpuPpin.main()
             else Framework.TEST_RESULT_FAIL)
