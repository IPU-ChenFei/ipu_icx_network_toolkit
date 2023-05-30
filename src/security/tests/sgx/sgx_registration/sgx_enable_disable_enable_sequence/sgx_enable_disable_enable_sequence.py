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

from src.security.tests.sgx.sgx_disable_through_bios.sgx_disable_through_bios import SGXDisableThroughBios
from src.security.tests.sgx.sgx_registration.sgx_registration_common import SgxRegistrationCommon
from src.security.tests.sgx.sgx_registration.sgx_smt_attestation.smt_on_attestation.sgx_smt_on_attestation import \
    SgxSmtOnAttestation


class SgxEnableDisableEnableSequence(SgxRegistrationCommon):
    """
    Phoenix ID : P18015174650-SGX Disable - Enable sequence

    Verify that SGX Disable - Enable sequence works successfully
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SgxEnableDisableEnableSequence

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(SgxEnableDisableEnableSequence, self).__init__(test_log, arguments, cfg_opts)
        self.sgx_disable = SGXDisableThroughBios(test_log, arguments, cfg_opts)
        self.sgx_smt_on = SgxSmtOnAttestation(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """preparing the setup
        This method calls prepare and execute of Security_SGX_Disable
        """
        self.sgx_disable.prepare()
        self.sgx_disable.execute()

    def execute(self):
        """
        This method calls prepare and execute of P18015104684-SGX SMT-On Attestation

        :return: True if Test case pass else False
        """
        self.sgx_smt_on.prepare()
        self.sgx_smt_on.execute()

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SgxEnableDisableEnableSequence.main() else Framework.TEST_RESULT_FAIL)
