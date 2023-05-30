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

from src.lib import content_exceptions

from src.security.tests.sgx.sgx_registration.sgx_auto_multipackage_registration.sgx_auto_multipackage_registration import \
    SgxAutoMultiPackageRegistration
from src.security.tests.sgx.sgx_registration.sgx_registration_common import SgxRegistrationCommon


class SgxRegistrationNormalBoot(SgxRegistrationCommon):
    """
    Phoenix ID : P18014073133-Normal Boot (N+1 boot)

    Verify the platform can maintain SGX enabled status from a previous boot using FLASH stored keys/manifest up to the OS
    This is the scenario that takes place when a fully functional SGX platform is restarted (and no package addition or
    package replacement or BIOS update has been performed)
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SgxRegistrationNormalBoot

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(SgxRegistrationNormalBoot, self).__init__(test_log, arguments, cfg_opts)
        self.sgx_reg = SgxAutoMultiPackageRegistration(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """This method calls prepare and execute of P18015104661-Auto MultiPackage (MP) Registration"""
        self.sgx_reg.prepare()
        self.sgx_reg.execute()

    def execute(self):
        """
        Performs warm reset and verify MP registration

        :return: True if Test case pass else False
        """
        self.perform_graceful_g3()
        if not self.sgx.verify_mp_registration():
            raise content_exceptions.TestFail("MP Registration verification failed")
        self._log.info("Auto Multi package Registration verified successfully")

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SgxRegistrationNormalBoot.main() else Framework.TEST_RESULT_FAIL)
