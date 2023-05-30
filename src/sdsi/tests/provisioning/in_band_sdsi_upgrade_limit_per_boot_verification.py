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
from src.sdsi.lib.sdsi_installer_lib import SDSIInstallerLib


class InBandSDSiUpgradeLimitPerBootVerification(ContentBaseTestCase):
    """
    SDSi - SoftSku Upgrade Limit Per Boot Verification
    Glasgow_ID: 74504
    Phoenix_ID: 22013734416
    """

    def _get_common_lib(self):
        self._log.info("Using In Band Common Library")
        from src.sdsi.lib.in_band_sdsi_common_lib import SDSICommonLib
        return SDSICommonLib(self._log, self.os, self._common_content_lib, self._common_content_configuration,
                             self._sdsi_installer, self.ac_power)

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of InBandSDSiUpgradeLimitPerBootVerification
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(InBandSDSiUpgradeLimitPerBootVerification, self).__init__(test_log, arguments, cfg_opts)
        self._sdsi_installer = SDSIInstallerLib(self._log, self.os, self._common_content_lib,
                                                self._common_content_configuration, self.ac_power)
        self._sdsi_obj = self._get_common_lib()

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super().prepare()
        for socket in range(self._sdsi_obj.number_of_cpu):
            self._sdsi_obj.apply_license_key_certificate(socket)

            self._log.info(f"Verify the failure counters for socket {socket} after graceful G3.")
            license_key_auth_failures = self._sdsi_obj.get_license_key_auth_fail_count(socket)
            payload_auth_fail_count = self._sdsi_obj.get_license_auth_fail_count(socket)

            if license_key_auth_failures != 0:
                error_msg = f"License key failure counter is not reset to 0 for socket {socket}."
                self._log.error(error_msg)
                raise SDSiExceptions.LicenseKeyFailCountError(error_msg)

            if payload_auth_fail_count != 0:
                error_msg = f"CAP authentication failure counter is not reset to 0 for socket {socket}."
                self._log.error(error_msg)
                raise SDSiExceptions.CapFailCountError(error_msg)

    def execute(self):
        """
            1. Verify the license key auth fail count and payload auth fail count is 0.
            2. Get the CPU PPIN/Hardware ID of the CPU.
            3. Write the licence key certificate to the CPU. (If it is not present on the CPU)
            4. Write a random CAP to the CPU.
            5. Verify the payload is available on the CPU.
            6. Verify the failure counter and max ssku updates counter values.
            7. Write a random CAP to the CPU again for the second time.
            8. Verify the payload is available on the CPU.
            9. Verify the failure counter and max ssku updates counter values.
            10. Write a random CAP to the CPU for the 3rd time.
            11. Verify the payload is not available on the CPU as we have exhaused the number of allowed ssku updates.
            12. Verify the failure counter and max ssku updates counter values.
        """
        # Provision 2 CAPS onto each socket, expecting each to pass since there are available updates
        for provision_number in range(2):
            for socket in range(self._sdsi_obj.number_of_cpu):
                self._log.info(f"Read the updates and failure counters for socket {socket} before applying CAP.")
                payload_fail_count_before = self._sdsi_obj.get_license_auth_fail_count(socket)
                max_ssku_updates_before = self._sdsi_obj.get_ssku_updates_available(socket)

                self._log.info(f"Apply the #{provision_number} CAP configuration for socket {socket}.")
                payload_info = self._sdsi_obj.get_capability_activation_payload(socket)
                self._sdsi_obj.apply_capability_activation_payload(payload_info, socket)
                payload_name = payload_info[1]

                self._log.info(f"Read the updates and failure counters for socket {socket} after applying CAP.")
                payload_fail_count_after = self._sdsi_obj.get_license_auth_fail_count(socket)
                ssku_updates_after = self._sdsi_obj.get_ssku_updates_available(socket)

                self._log.info(f"Verify the counter values are updated as expected for socket {socket}.")
                if payload_fail_count_before != payload_fail_count_after:
                    error_msg = f"Failure counters increased after provisioning."
                    self._log.error(error_msg)
                    raise SDSiExceptions.CapFailCountError(error_msg)
                if max_ssku_updates_before - 1 != ssku_updates_after:
                    error_msg = f"SSKU updates did not decrease after provisioning."
                    self._log.error(error_msg)
                    raise SDSiExceptions.AvailableUpdatesError(error_msg)

                self._log.info(f"Verify the CAP is available for the socket {socket}.")
                if not self._sdsi_obj.is_payload_available(payload_name, socket):
                    f"Socket {socket} is not provisioned. Payload information for {payload_name} is not found."
                self._log.info(f"1st CAP {payload_name} is applied successfully for socket {socket}.")

        # Provision both sockets with another CAP, expecting failure due to insufficient updates remaining.
        for socket in range(self._sdsi_obj.number_of_cpu):
            self._log.info(f"Apply the CAP configuration for socket {socket}.")
            payload_info = self._sdsi_obj.get_capability_activation_payload(socket)
            payload_name = payload_info[1]
            try:
                self._sdsi_obj.apply_capability_activation_payload(payload_info, socket)
                error_msg = f"Expected provisioning failure due to insufficient updates remaining for socket {socket}"
                self._log.error(error_msg)
                raise SDSiExceptions.ProvisioningError(error_msg)
            except SDSiExceptions.ProvisioningError:
                self._log.info(f"Provisioning failed for socket {socket} as expected.")
                if self._sdsi_obj.is_payload_available(payload_name, socket):
                    error_msg = f"Socket {socket} is provisioned with {payload_name}. Expected failure."
                    self._log.info(error_msg)
                    raise SDSiExceptions.ProvisioningError(error_msg)
                self._log.info(f"1st CAP {payload_name} is applied successfully for socket {socket}.")
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        self._log.info("Perform graceful G3 for resetting the counters after test irrespective of pass/fail.")
        self.perform_graceful_g3()
        super(InBandSDSiUpgradeLimitPerBootVerification, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if InBandSDSiUpgradeLimitPerBootVerification.main()
             else Framework.TEST_RESULT_FAIL)
