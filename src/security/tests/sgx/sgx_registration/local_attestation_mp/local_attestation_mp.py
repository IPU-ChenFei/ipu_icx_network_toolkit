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

import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.security.tests.sgx.sgx_registration.sgx_auto_multipackage_registration.sgx_auto_multipackage_registration \
    import SgxAutoMultiPackageRegistration

from src.security.tests.sgx.sgx_registration.sgx_registration_common import SgxRegistrationCommon


class LocalAttestationMP(SgxRegistrationCommon):
    """
    Phoenix ID : P18014072748-Local Attestation MP

    This test aims to test SGX in cross processor core scenario:
    1. verify cached launch blob can be used in each processor core
    2. verify sealing key is same in each process core
    3. verify local attestation creation from each processor core
    4. verify provisioning key is same in each processor core
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of LocalAttestationMP

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(LocalAttestationMP, self).__init__(test_log, arguments, cfg_opts)
        self.sgx_reg = SgxAutoMultiPackageRegistration(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """calling prepare and execute of auto_multi_registration"""
        self.sgx_reg.prepare()
        self.sgx_reg.execute()

    def execute(self):
        """
        Installing local attestation mp and verifying the output of sgxcrossproctestserver and sgxcrossproctest

        :return: True if Test case pass else False
        """
        local_attestation_path = self.sgx.install_local_attestation_mp_tool()
        self.sgx.verify_local_attestation_output(local_attestation_path)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if LocalAttestationMP.main() else Framework.TEST_RESULT_FAIL)
