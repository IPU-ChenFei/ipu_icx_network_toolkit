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
from src.sdsi.lib.in_band_sdsi_common_lib import SDSICommonLib as SDSiInbandCommonLib
from src.sdsi.lib.sdsi_common_lib import SDSICommonLib
from src.sdsi.lib.sdsi_installer_lib import SDSIInstallerLib


class OutOfBandAndInBandProvisioningTest(ContentBaseTestCase):
    """
    Glasgow_ID: 75678
    Phoenix_ID: 22013846466
    This test case is to verify the OOB provisioning of the SSKU enabled CPU by applying the license key certificate,
    and a capability activation payload and verify it is available. This test writes to sockets in numerical order.
    This test performs provisioning using both out of band and inband methods.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of OutOfBandAndInBandProvisioningTest
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(OutOfBandAndInBandProvisioningTest, self).__init__(test_log, arguments, cfg_opts)
        self._sdsi_installer = SDSIInstallerLib(self._log, self.os, self._common_content_lib,
                                                self._common_content_configuration, self.ac_power)
        self._sdsi_obj = SDSICommonLib(self._log, self.os, self._common_content_lib,
                                       self._common_content_configuration, self._sdsi_installer, self.ac_power)
        self._ib_sdsi_obj = SDSiInbandCommonLib(self._log, self.os, self._common_content_lib,
                                       self._common_content_configuration, self._sdsi_installer, self.ac_power)

    def prepare(self):
        # type: () -> None
        """Prepare the system for execution and validate basic test requirements"""
        super(OutOfBandAndInBandProvisioningTest, self).prepare()
        self._sdsi_installer.verify_sdsi_installer()

        for cpu_num in range(self._sdsi_obj.number_of_cpu):
            self._log.info("Verify the initial failure counters for CPU{}".format(cpu_num))
            self._sdsi_obj.apply_license_key_certificate(cpu_num)

            if self._sdsi_obj.get_license_key_auth_fail_count(cpu_num) != 0:
                log_error = "License key authentication error counter is not reset to 0 for CPU{}.".format(cpu_num)
                self._log.error(log_error)
                raise SDSiExceptions.LicenseKeyFailCountError(log_error)

            if self._sdsi_obj.get_license_auth_fail_count(cpu_num) != 0:
                log_error = "License authentication error counter not reset to 0 for CPU{}.".format(cpu_num)
                self._log.error(log_error)
                raise SDSiExceptions.CapFailCountError(log_error)

    def execute(self):
        """
            Apply random CAP provisioning using both out of band and inband methods.
        """
        # Provision Payloads and append information to payload_info
        # Provisioning swtiches between oob and ib methods for each socket
        payload_info = []
        for cpu_num in range(self._sdsi_obj.number_of_cpu):
            sdsi_obj = self._sdsi_obj if cpu_num % 2 == 0 else self._ib_sdsi_obj
            payload_fail_count_before = sdsi_obj.get_license_auth_fail_count(cpu_num)
            max_ssku_updates_before = sdsi_obj.get_ssku_updates_available(cpu_num)

            self._log.info("Get a random CAP configuration for CPU{}.".format(cpu_num))
            current_payload_info = sdsi_obj.get_capability_activation_payload(cpu_num)
            self._log.info("Apply the CAP configuration for CPU_{}.".format(cpu_num + 1))
            sdsi_obj.apply_capability_activation_payload(current_payload_info, cpu_num)
            payload_info.append(current_payload_info)

            payload_fail_count_after = sdsi_obj.get_license_auth_fail_count(cpu_num)
            max_ssku_updates_after = sdsi_obj.get_ssku_updates_available(cpu_num)

            if payload_fail_count_after > payload_fail_count_before:
                log_error = "CAP failure counter increased after provisioning for CPU{}.".format(cpu_num)
                self._log.error(log_error)
                raise SDSiExceptions.CapFailCountError(log_error)

            if max_ssku_updates_after != max_ssku_updates_before - 1:
                log_error = "ssku_updates_available did not decrease after provisioning for CPU{}.".format(cpu_num)
                self._log.error(log_error)
                raise SDSiExceptions.AvailableUpdatesError(log_error)

        # Reboot to apply provisioning
        self.perform_graceful_g3()

        # Validate Provisioning
        # Validation swtiches between ib and oob methods for each socket
        for cpu_num in range(self._sdsi_obj.number_of_cpu):
            sdsi_obj = self._ib_sdsi_obj if cpu_num % 2 == 0 else self._sdsi_obj
            ssku_updates_available = sdsi_obj.get_ssku_updates_available(cpu_num)
            max_ssku_updates_available = sdsi_obj.get_max_ssku_updates_available(cpu_num)
            if ssku_updates_available != max_ssku_updates_available:
                log_error = "ssku_updates_available did not reset to max after provisioning for CPU{}.".format(cpu_num)
                self._log.error(log_error)
                raise SDSiExceptions.AvailableUpdatesError(log_error)

            if not sdsi_obj.is_payload_available(payload_info[cpu_num][1], cpu_num):
                log_error = "CPU{} is not provisioned after write operation. {} CAP information is not found."\
                .format(cpu_num, payload_info[cpu_num][1])
                self._log.error(log_error)
                raise SDSiExceptions.ProvisioningError(log_error)
            self._log.info("{} config is applied successfully for CPU{}.".format(payload_info[cpu_num][1], cpu_num))

        self._sdsi_obj.cold_reset()

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        self.perform_graceful_g3()
        super(OutOfBandAndInBandProvisioningTest, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if OutOfBandAndInBandProvisioningTest.main() else Framework.TEST_RESULT_FAIL)
