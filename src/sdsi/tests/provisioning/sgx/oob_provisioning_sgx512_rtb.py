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


class OobProvisioningSgx512RTB(OutOfBandSdsiSgxCommon):
    """
    Glasgow_ID: 70591
    Phoenix_ID: 18014074526
    This test case is specific to SGX 512GB EPC functionality.  Enables a 512GB SGX Enclave Size.
    The return to base operation reduces the available SGX enclave size to default.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of OobProvisioningSgx512RTB
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(OobProvisioningSgx512RTB, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(OobProvisioningSgx512RTB, self).prepare()
        self.total_memory_available = self._sdsi_obj.get_total_memory_in_gb()
        self._log.info("System memory available is {}".format(self.total_memory_available))
        memory_required = self.prm_size_to_apply[FeatureNames.SG40.value] * 1.5
        if self.total_memory_available < memory_required:
            error_msg = f"The SUT is under the  memory requirement of {memory_required}: {self.total_memory_available}."
            self._log.error(error_msg)
            raise ContentExceptions.TestUnSupportedError(error_msg)
        self._sdsi_obj.erase_payloads_from_nvram()

    def execute(self):
        """
            SDSi - SGX Functional Provision 512GB EPC, then RTB and validate PrmSgxSize
        """
        # Provision CPU with SG40 and validate PrmSgxSize increase
        self._log.info("Perform SGX operation for SG40 and validate.")
        self.perform_and_validate_sgx_operation(FeatureNames.SG40.value)
        if not self.set_and_validate_prm_size(self.prm_size_to_apply[FeatureNames.SG40.value]):
            raise SDSiExceptions.SGXError("PrmSgxSize not set to SG40 configuration.")

        # Return CPU to base state and validate PrmSgxSize reduction
        self._log.info("Perform return to base SGX operation and validate.")
        for cpu in range(self._sdsi_obj.number_of_cpu):
            self._sdsi_obj.return_to_base(FeatureNames.BASE.value, cpu)
        self.perform_graceful_g3()
        if not self.set_and_validate_prm_size(self.get_prm_default_max()):
            raise SDSiExceptions.SGXError("PrmSgxSize not set default configuration.")
        if self.set_and_validate_prm_size(self.prm_size_to_apply[FeatureNames.SG40]):
            raise SDSiExceptions.SGXError("SG40 PrmSgxSize should not succeed after return to base.")

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(OobProvisioningSgx512RTB, self).cleanup(return_status)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if OobProvisioningSgx512RTB.main()
             else Framework.TEST_RESULT_FAIL)
