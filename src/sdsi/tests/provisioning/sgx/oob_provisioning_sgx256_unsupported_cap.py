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

import src.lib.content_exceptions as ContentExceptions
import src.sdsi.lib.sdsi_exceptions as SDSiExceptions
from src.sdsi.lib.license.sdsi_license_names import FeatureNames
from src.sdsi.tests.provisioning.sgx.sdsi_sgx_common_test import OutOfBandSdsiSgxCommon


class SDSiSGXUnsupportedCap(OutOfBandSdsiSgxCommon):
    """
    Glasgow_ID: 69348
    Phoenix_ID: 22013738120
    This test case verifies that a feature is not activated when license provisioning is attempted using a SDSi CAP
    license key for a feature that is not specifically supported on a processor SKU.
    Note: This test case is for use with Linux operating systems only.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SDSiSGXUnsupportedCap
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(SDSiSGXUnsupportedCap, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
            Perform test preparation.
            Validate basic test requirements.
        """
        super(SDSiSGXUnsupportedCap, self).prepare()
        if self.initial_memory_available <= 256:
            error_msg = 'The system does not contain the minimum memory required to run this test.'
            self._log.error(error_msg)
            raise ContentExceptions.TestUnSupportedError(error_msg)

    def execute(self):
        """
            Execute the test.
            Apply SG20 and verify that the feature is not working for the unsupported platform.
        """
        for cpu_counter in range(self._sdsi_obj.number_of_cpu):
            self._log.info("Write the licence key certificate for CPU_{}.".format(cpu_counter + 1))
            self._sdsi_obj.apply_license_key_certificate(cpu_counter)
        self.perform_and_validate_sgx_operation(FeatureNames.SG20.value)
        if not self.set_and_validate_prm_size(self.prm_size_to_apply[FeatureNames.SG20.value]):
            error_msg = "Prm max GB should not increase after enabling unsupported SGX CAP"
            self._log.error(error_msg)
            raise SDSiExceptions.ProvisioningError(error_msg)
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """
            Perform Test Cleanup
        """
        super(SDSiSGXUnsupportedCap, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SDSiSGXUnsupportedCap.main()
             else Framework.TEST_RESULT_FAIL)
