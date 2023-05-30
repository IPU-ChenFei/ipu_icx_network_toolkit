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
from src.sdsi.lib.in_band_sdsi_common_lib import SDSICommonLib
from src.sdsi.lib.sdsi_installer_lib import SDSIInstallerLib


class InBandSDSIApplyLicenseWithCorruptKeySignature(ContentBaseTestCase):
    """
    Glasgow_ID: 74503
    Phoenix_ID: 22013659343
    Verify that a feature is not activated when license provisioning is attempted using an authentication key with a
    modified public key (customer) signature on a CPU that supports Soft Sku. Provisioning should be disallowed.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of InBandProvisioningTest

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(InBandSDSIApplyLicenseWithCorruptKeySignature, self).__init__(test_log, arguments, cfg_opts)
        self._sdsi_installer = SDSIInstallerLib(self._log, self.os, self._common_content_lib,
                                                self._common_content_configuration, self.ac_power)
        self._sdsi_obj = SDSICommonLib(self._log, self.os, self._common_content_lib,
                                       self._common_content_configuration, self._sdsi_installer, self.ac_power)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(InBandSDSIApplyLicenseWithCorruptKeySignature, self).prepare()
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
            3. Write the licence key certificate to the CPU. (If it is not present on the CPU)
            4. Verify the license key is not applied.
        """
        self._log.info("Apply the corrupt licence key certificate to the SUT and verify the error.")
        self._sdsi_obj.apply_invalid_license_key_on_sut()

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        self._log.info("Perform graceful G3 for resetting the counters after test irrespective of pass/fail.")
        self.perform_graceful_g3()
        super(InBandSDSIApplyLicenseWithCorruptKeySignature, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if InBandSDSIApplyLicenseWithCorruptKeySignature.main()
             else Framework.TEST_RESULT_FAIL)
