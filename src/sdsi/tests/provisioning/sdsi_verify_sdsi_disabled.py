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


class SdsiVerifySdsiDisabled(ContentBaseTestCase):
    """
    Glasgow_ID: NA
    Phoenix_ID: NA
    This test case is to verify the ...
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SdsiVerifySdsiDisabled

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(SdsiVerifySdsiDisabled, self).__init__(test_log, arguments, cfg_opts)
        self._sdsi_installer = SDSIInstallerLib(self._log, self.os, self._common_content_lib,
                                                self._common_content_configuration, self.ac_power)
        self._sdsi_obj = SDSICommonLib(self._log, self.os, self._common_content_lib,
                                       self._common_content_configuration, self._sdsi_installer, self.ac_power)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(SdsiVerifySdsiDisabled, self).prepare()

        self._log.info("Verify the SPR_SDSi_Installer by initiating --help command.")
        self._sdsi_installer.verify_sdsi_installer()

        self._log.info("Verify the license key auth fail count and payload auth fail count is 0.")

        self._log.info("Verify the license key auth fail counter for CPU 1.")
        license_key_auth_failures = self._sdsi_obj.get_license_key_auth_fail_count(socket=0)
        payload_auth_fail_count = self._sdsi_obj.get_license_auth_fail_count(socket=0)
        assert (license_key_auth_failures == 0 and payload_auth_fail_count == 0), \
            "Authentication key failure counter is not reset to 0 after after fresh powercycle on CPU 0."

        self._log.info("License key authentication and payload authentication failure counters are verified successfully for CPU 0.")

        self._log.info("Get the CPU PPIN/Hardware ID of the CPU.")
        cpu_ppin = self._sdsi_obj.get_cpu_hw_asset_id(socket=0)
        self._log.info("CPU PPIN/Hardware Asset ID of the CPU 0 is '{}'".format(cpu_ppin))

    def execute(self):
        """
        """
        self._log.info("Verify SDSi is enabled for CPU 0.")
        assert not self._sdsi_obj.is_sdsi_enabled(socket=0), "SDSi enabled value is mismatching."

        self._log.info(
            "Get the SSKU updates remaining and license failure counter for CPU 0 before applying License key.")
        license_fail_count_before = self._sdsi_obj.get_license_auth_fail_count(socket=0)
        ssku_updates_before = self._sdsi_obj.get_ssku_updates_available(socket=0)

        self._log.info("Write the licence key certificate for CPU0 and check correct error message is throwing.")
        response = self._sdsi_obj.apply_license_key_certificate(socket=0)
        if "Writing Authentication Key Certificate... Write failed due to 'Flow Failure'." not in response:
            log_error = "Expected error message was not thrown after license write operation on SDSi unsupported processor."
            self._log.error(log_error)
            raise RuntimeError(log_error)

        self._log.info(
            "Get the SSKU updates remaining and license failure counter for CPU 0 after applying License key.")
        license_fail_count_after = self._sdsi_obj.get_license_auth_fail_count(socket=0)
        ssku_updates_after = self._sdsi_obj.get_ssku_updates_available(socket=0)

        self._log.info(
            "Verify the ssku updates available counters are updated as expected for CPU 0.")
        assert ssku_updates_before == ssku_updates_after, "Expecting the max available ssku updates counter to be reduced by 1, but the values are Expected: {}, Found: {} for CPU0.".format(
            ssku_updates_before, ssku_updates_after)
        assert license_fail_count_before == license_fail_count_after, "Expecting the failure counters to be unchanged after write operation. But the values are Expected: {}, Found: {} for CPU0.".format(
            license_fail_count_before, license_fail_count_after)

        self._log.info("Verify the License key config is not available for CPU 0.")
        assert not self._sdsi_obj.is_license_key_available(socket=0), "License key config is available for CPU0"

        self._log.info("SDSi is not supported for CPU0 and License key config is not applied.")

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(SdsiVerifySdsiDisabled, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SdsiVerifySdsiDisabled.main() else Framework.TEST_RESULT_FAIL)
