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

import src.sdsi.lib.sdsi_exceptions as SDSiExceptions
from src.lib.content_base_test_case import ContentBaseTestCase
from src.sdsi.lib.sdsi_common_lib import SDSICommonLib
from src.sdsi.lib.sdsi_installer_lib import SDSIInstallerLib


class OutOfBandProvisioningWithCorruptCap(ContentBaseTestCase):
    """
    Glasgow_ID: 72074
    Phoenix_ID: 22012928283
    This test case is to verify the OOB provisioning of the SSKU enabled CPU by applying the license key certificate,
    and a capability activation payload and verify it is available.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of OutOfBandProvisioningTest

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(OutOfBandProvisioningWithCorruptCap, self).__init__(test_log, arguments, cfg_opts)
        self._sdsi_installer = SDSIInstallerLib(self._log, self.os, self._common_content_lib,
                                                self._common_content_configuration, self.ac_power)
        self._sdsi_obj = SDSICommonLib(self._log, self.os, self._common_content_lib,
                                       self._common_content_configuration, self._sdsi_installer, self.ac_power)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(OutOfBandProvisioningWithCorruptCap, self).prepare()

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
            self._log.info("Write the licence key certificate for CPU_{}.".format(cpu_counter + 1))
            self._sdsi_obj.apply_license_key_certificate(cpu_counter)
            self._log.info(
                "Read the SSKU updates remaining and payload failure counter for CPU_{} before applying CAP.".format(
                    cpu_counter + 1))
            payload_fail_count_before = self._sdsi_obj.get_license_auth_fail_count(socket=cpu_counter)
            max_ssku_updates_before = self._sdsi_obj.get_ssku_updates_available(socket=cpu_counter)

            payload_information = self._sdsi_obj.get_capability_activation_payload(socket=cpu_counter)
            payload_name = payload_information[1]
            payload_binary = payload_information[2]
            payload_information[2] = self._sdsi_obj._generate_corrupted_key(payload_binary)

            self._log.info("Apply the corrupted payload configuration for CPU_{}.".format(cpu_counter + 1))
            try:
                self._sdsi_obj.apply_capability_activation_payload(payload_information, cpu_counter)
            except SDSiExceptions.ProvisioningError:
                pass

            self._log.info(
                "Read the SSKU updates remaining and payload failure counter for CPU_{} after applying CAP.".format(
                    cpu_counter + 1))
            payload_fail_count_after = self._sdsi_obj.get_license_auth_fail_count(socket=cpu_counter)
            max_ssku_updates_after = self._sdsi_obj.get_ssku_updates_available(socket=cpu_counter)

            self._log.info(
                "Verify the ssku updates available counter value is updated as expected for CPU_{}.".format(
                    cpu_counter + 1))
            assert max_ssku_updates_before == max_ssku_updates_after, \
                "Expecting the available ssku updates counter not to change, but the values are Expected: {}, Found: {} for CPU_{}.".format(
                    max_ssku_updates_before, max_ssku_updates_after, cpu_counter + 1)
            assert not self._sdsi_obj.is_payload_available(payload_name,
                                                           cpu_counter), "Expecting the corrupted CAP {} shouldn't be available for CPU_0. But found.".format(
                payload_information[2], cpu_counter + 1)

            self._log.info("Corrupted CAP configuration is not applied CPU_{}.".format(cpu_counter + 1))

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        self._log.info("Perform graceful G3 for resetting the counters after test irrespective of pass/fail.")
        self.perform_graceful_g3()
        super(OutOfBandProvisioningWithCorruptCap, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if OutOfBandProvisioningWithCorruptCap.main()
             else Framework.TEST_RESULT_FAIL)
