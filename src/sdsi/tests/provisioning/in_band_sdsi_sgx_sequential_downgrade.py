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

from src.sdsi.tests.provisioning.sgx.sdsi_sgx_common_test import InBandSdsiSgxCommon


class SdsiSgxSequentialDowngrade(InBandSdsiSgxCommon):
    """
    Glasgow_ID: 75424
    Phoenix_ID: 22013846354
    Execute the test.
    Sequentially enable and verify each SGX version from SG40 down to SG00
    Validation is performed by checking if SgxPrmSize knobs are able to be set to the
    corresponding values for each SGX version, and not any higher The available memory on
    the platform must also decrease by approximately the same amount as the SgxPrmSize set.
    """
    # Each SGX Version to iterate, along with the expected result.
    # SG20 is set to False, since it is unsupported on the platform, so the expected result is a failure.
    SGX_ORDER = {"SG40": True,
                 "SG20": False,
                 "SG10": True,
                 "SG08": True,
                 "SG04": True,
                 "SG01": True,
                 "SG00": True}
    FULL_TEST_MEMORY_REQUIREMENT = 512

    def execute(self):
        """
        Execute the test.
        Sequentially enable and verify each SGX version from SG40 down to SG00
        Validation is performed by checking if SgxPrmSize knobs are able to be set to the
        corresponding values for each SGX version, and not any higher The available memory on
        the platform must also decrease by approximately the same amount as the SgxPrmSize set.
        """
        for sgx_ver in self.SGX_ORDER.keys():
            # Fetch the maximum PrmSgxSize for the given SGX Version.
            prm_size_to_apply = max(self.prm_size_to_apply[sgx_ver], self.get_prm_default_max())

            # Skip this test if the platform does not have enough memory
            if prm_size_to_apply > self.initial_memory_available:
                continue

            # Apply payload
            self.perform_and_validate_sgx_operation(sgx_ver)

            # Negative test cannot be applied to the largest sgx option. There is no higher knob to set.
            if sgx_ver != "SG40":
                # Attempts to set PrmSgxSize to above maximum value for this SGX Version - failure expected.
                assert not self.set_and_validate_prm_size(prm_size_to_apply * 2), \
                    'Prm Size should not be able to be set above current SGX provisioning max.'

            # Attempts to set PrmSgxSize to the expected maximum for this SGX Version - success expected.
            assert self.SGX_ORDER[sgx_ver] == self.set_and_validate_prm_size(prm_size_to_apply), \
                'Prm Size was unable to be set according to SGX Version.'

            # Reset Payloads for next version.
            self._sdsi_obj.erase_payloads_from_nvram()

        # Inform tester if there was not enough memory on platform for a full test.
        if self.initial_memory_available <= self.FULL_TEST_MEMORY_REQUIREMENT:
            self._log.info("Test case passed, however platform did not have enough memory for full test.")
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """
            Perform Test Cleanup
        """
        self._sdsi_obj.erase_payloads_from_nvram()
        super(SdsiSgxSequentialDowngrade, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SdsiSgxSequentialDowngrade.main()
             else Framework.TEST_RESULT_FAIL)