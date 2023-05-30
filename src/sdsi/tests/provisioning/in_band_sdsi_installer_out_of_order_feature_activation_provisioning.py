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
import re
import sys

from dtaf_core.lib.dtaf_constants import Framework

import src.sdsi.lib.sdsi_exceptions as SDSiExceptions
from src.lib.content_base_test_case import ContentBaseTestCase
from src.provider.cpu_info_provider import CpuInfoProvider
from src.sdsi.lib.sdsi_installer_lib import SDSIInstallerLib


class InBandSDSiInstallerOutOfOrderFeatureActivationProvisioning(ContentBaseTestCase):
    """
    Glasgow_ID: 75096
    Phoenix_ID: 22013740200
    Expectation is that a license with a higher revision id than those previously applied are provisioned,
    but if a revision id is skipped, then a license for that CPU with that revision id will not be provisioned.
    The OOB-MSM driver will need to be configured to load on every OS boot since our content includes system resets.
    """

    def _get_common_lib(self):
        """
        Get the common library used for this test
        """
        self._log.info("Using In Band Common Library")
        from src.sdsi.lib.sdsi_common_lib import InbandSDSICommonLib
        return InbandSDSICommonLib(self._log, self.os, self._common_content_lib, self._common_content_configuration,
                                   self._sdsi_installer, self.ac_power)

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of InBandSDSiInstallerOutOfOrderFeatureActivationProvisioning
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(InBandSDSiInstallerOutOfOrderFeatureActivationProvisioning, self).__init__(test_log, arguments, cfg_opts)
        self._sdsi_installer = SDSIInstallerLib(self._log, self.os, self._common_content_lib,
                                                self._common_content_configuration, self.ac_power)
        self._sdsi_obj = self._get_common_lib()
        self._cpu_info_provider = CpuInfoProvider.factory(self._log, cfg_opts, self.os)
        self._cpu_info_provider.populate_cpu_info()

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super().prepare()
        self._sdsi_obj.erase_payloads_from_nvram()
        self._sdsi_installer.verify_sdsi_installer()

        for socket in range(self._sdsi_obj.number_of_cpu):
            self._log.info(f"Verify the failure counters for socket {socket} after graceful G3.")

            if self._sdsi_obj.get_license_key_auth_fail_count(socket) != 0:
                error_msg = f"License key failure counter is not reset to 0 for socket {socket}."
                self._log.error(error_msg)
                raise SDSiExceptions.LicenseKeyError(error_msg)

            if self._sdsi_obj.get_license_auth_fail_count(socket) != 0:
                error_msg = f"CAP authentication failure counter is not reset to 0 for socket {socket}."
                self._log.error(error_msg)
                raise SDSiExceptions.CapFailCountError(error_msg)

    def execute(self):
        """
            Expectation is that a license with a higher revision id than those previously applied are provisioned,
            but if a revision id is skipped, then a license for that CPU with that revision id will not be provisioned.
        """
        for socket in range(self._sdsi_obj.number_of_cpu):
            self._log.info(f"Write the licence key certificate for socket {socket}.")
            self._sdsi_obj.apply_license_key_certificate(socket)

            available_payloads = self._sdsi_obj.get_applicable_payloads(socket=socket)
            payload_keys = list(available_payloads.keys())

            self._log.info(f"Read updates and payload failure counter for socket {socket} before applying CAP.")
            payload_fail_count_before = self._sdsi_obj.get_license_auth_fail_count(socket=socket)
            max_ssku_updates_before = self._sdsi_obj.get_ssku_updates_available(socket=socket)

            self._log.info(f"Apply a CAP configuration to socket {socket}.")
            valid_payload_file = self._sdsi_obj.get_capability_activation_payload(socket)
            self._sdsi_obj.apply_capability_activation_payload(valid_payload_file, socket)

            self._log.info(f"Read updates and payload failure counter for socket {socket} after applying CAP.")
            payload_fail_count_after = self._sdsi_obj.get_license_auth_fail_count(socket=socket)
            max_ssku_updates_after = self._sdsi_obj.get_ssku_updates_available(socket=socket)
            self._log.info(f"Verify the failure counter and ssku updates remaining values for socket {socket}.")
            if payload_fail_count_before != payload_fail_count_after:
                error_msg = f"Payload fail counter increased after provisioning."
                self._log.error(error_msg)
                raise SDSiExceptions.CapFailCountError(error_msg)
            if max_ssku_updates_after != max_ssku_updates_before - 1:
                error_msg = f"Max SSKU updates did not decrease after provisioning."
                self._log.error(error_msg)
                raise SDSiExceptions.AvailableUpdatesError(error_msg)

            if not self._sdsi_obj.is_payload_available(valid_payload_file[1], socket):
                error_msg = f"Socket {socket} not provisioned with {valid_payload_file[1]} after the write operation."
                self._log.error(error_msg)
                raise SDSiExceptions.MissingCapError(error_msg)

            self._log.info(f"Apply an Out of Order CAP configuration for socket {socket}.")
            out_of_order_payload_file = available_payloads[payload_keys[0]]
            out_of_order_payload_name = re.search(r'rev_\S*_(.*)', payload_keys[0]).group(1)
            out_of_order_payload_rev = int((re.search(r'rev_(.+?)_', payload_keys[0]).group(1)), 16)
            out_of_order_payload_info = [out_of_order_payload_rev, out_of_order_payload_name, out_of_order_payload_file]
            try:
                self._sdsi_obj.apply_capability_activation_payload(out_of_order_payload_info, socket)
                error_msg = f"Out of order CAP was applied on socket {socket}"
                self._log.error(error_msg)
                raise SDSiExceptions.CapRevisionError(error_msg)
            except SDSiExceptions.ProvisioningError:
                self._log.info(f"Out of order CAP was not applied on socket {socket} as expected.")

            self.perform_graceful_g3()

            self._log.info(f"Read updates and payload failure counter for socket {socket} before applying CAP.")
            payload_fail_count_before = self._sdsi_obj.get_license_auth_fail_count(socket=socket)
            max_ssku_updates_before = self._sdsi_obj.get_ssku_updates_available(socket=socket)

            self._log.info(f"Apply a CAP configuration to socket {socket}.")
            valid_payload_file = self._sdsi_obj.get_capability_activation_payload(socket)
            self._sdsi_obj.apply_capability_activation_payload(valid_payload_file, socket)

            self._log.info(f"Read updates and payload failure counter for socket {socket} after applying CAP.")
            payload_fail_count_after = self._sdsi_obj.get_license_auth_fail_count(socket=socket)
            max_ssku_updates_after = self._sdsi_obj.get_ssku_updates_available(socket=socket)
            self._log.info(f"Verify the failure counter and ssku updates remaining values for socket {socket}.")
            if payload_fail_count_before != payload_fail_count_after:
                error_msg = f"Payload fail counter increased after provisioning."
                self._log.error(error_msg)
                raise SDSiExceptions.CapFailCountError(error_msg)
            if max_ssku_updates_after != max_ssku_updates_before - 1:
                error_msg = f"Max SSKU updates did not decrease after provisioning."
                self._log.error(error_msg)
                raise SDSiExceptions.AvailableUpdatesError(error_msg)

            if not self._sdsi_obj.is_payload_available(valid_payload_file[1], socket):
                error_msg = f"Socket {socket} not provisioned with {valid_payload_file[1]} after the write operation."
                self._log.error(error_msg)
                raise SDSiExceptions.MissingCapError(error_msg)

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        self._log.info("Perform graceful G3 for resetting the counters after test irrespective of pass/fail.")
        self.perform_graceful_g3()
        super(InBandSDSiInstallerOutOfOrderFeatureActivationProvisioning, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if InBandSDSiInstallerOutOfOrderFeatureActivationProvisioning.main()
             else Framework.TEST_RESULT_FAIL)
