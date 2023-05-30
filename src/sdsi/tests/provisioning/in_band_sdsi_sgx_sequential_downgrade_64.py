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


class SdsiSgxSequentialDowngrade64(InBandSdsiSgxCommon):
    """
    Glasgow_ID: NA
    Phoenix_ID: NA
    Sequentially enable and verify each SGX version from SG40 down to SG00
    Validation is performed by checking if SgxPrmSize knobs are able to be set to the
    corresponding values for each SGX version, and not any higher The available memory on
    the platform must also decrease by approximately the same amount as the SgxPrmSize set.
    """
    # Each SGX Version to iterate, along with the expected result.
    # SG20 is set to False, since it is unsupported on the platform, so the expected result is a failure.
    SGX_ORDER = [["SG40", True],
                 ["SG20", False],
                 ["SG10", True],
                 ["SG08", True]]
    SGX_VER_NAME = 0
    SGX_EXPECTED_RESULT = 1

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SDSiSGXUnsupportedCap
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(SdsiSgxSequentialDowngrade64, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
            Perform test preparation.
            Validate basic test requirements.
        """
        super(SdsiSgxSequentialDowngrade64, self).prepare()

    def execute(self):
        """
        Execute the test.
        Sequentially enable and verify each SGX version from SG40 down to SG00
        Validation is performed by checking if SgxPrmSize knobs are able to be set to the
        corresponding values for each SGX version, and not any higher The available memory on
        the platform must also decrease by approximately the same amount as the SgxPrmSize set.
        """
        # Find entry point for SGX provisioning depending on platform memory
        entry_point = -1
        for i in range(len(self.SGX_ORDER)):
            if self.initial_memory_available >= self.prm_size_to_apply[self.SGX_ORDER[i][self.SGX_VER_NAME]]:
                entry_point = i
                break
        assert entry_point != -1, 'This Platform does not have enough memory to validate SGX functionality.'
        self._log.info("SGX Entry Point for this test is {}.".format(self.SGX_ORDER[entry_point][self.SGX_VER_NAME]))

        # Starting from entry point, sequentially downgrade and validate SGX Versions.
        for sgx_version in self.SGX_ORDER[entry_point:]:
            # Perform SGX operation to apply payload
            self.perform_and_validate_sgx_operation(sgx_version[self.SGX_VER_NAME])

            # Fetch the maximum PrmSgxSize for the given SGX Version.
            prm_size_to_apply = max([self.prm_size_to_apply[sgx_version[self.SGX_VER_NAME]],
                                     self.get_prm_default_max()])

            # Attempts to set PrmSgxSize to above maximum value for this SGX Version
            # This SHOULD FAIL, But wont with current BIOS knobs not being limited to max for current provision.
            assert not self.set_and_validate_prm_size(prm_size_to_apply * 2), \
                'Prm Size should not be able to be set above current SGX provisioning max.'

            # Attempts to set PrmSgxSize to the expected maximum for this SGX Version
            # Is expected to pass except when the given version is not supported on the CPU
            assert sgx_version[self.SGX_EXPECTED_RESULT] == self.set_and_validate_prm_size(
                self.prm_size_to_apply[sgx_version[self.SGX_VER_NAME]]), \
                'Prm Size was unable to be set according to SGX Version.' if sgx_version[
                    self.SGX_EXPECTED_RESULT] else 'Prm Size was able to be set for unsupported CAP'
            self._sdsi_obj.erase_payloads_from_nvram()

        if entry_point != 0:
            self._log.info("Test case passed, however platform did not have enough memory for full test.")
            self._log.info("This test started at {}.".format(self.SGX_ORDER[entry_point][self.SGX_VER_NAME]))
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """
            Perform Test Cleanup
        """
        self._sdsi_obj.erase_payloads_from_nvram()
        super(SdsiSgxSequentialDowngrade64, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SdsiSgxSequentialDowngrade64.main()
             else Framework.TEST_RESULT_FAIL)