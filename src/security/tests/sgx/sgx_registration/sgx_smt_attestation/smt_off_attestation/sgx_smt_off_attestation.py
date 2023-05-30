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
import os
import time

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions

from src.security.tests.sgx.sgx_registration.sgx_registration_common import SgxRegistrationCommon


class SgxSmtOffAttestation(SgxRegistrationCommon):
    """
    Phoenix ID : P18015104712-SGX SMT-Off Attestation

    Verify Multi-Package (MP) Registration can be completed with SMT (Hyper-Threading) disabled
    """
    SMT_OFF_BIOS_CONFIG_FILE = "sgx_smt_off_attestation.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SgxSmtOffAttestation

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.smt_off_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.SMT_OFF_BIOS_CONFIG_FILE)
        super(SgxSmtOffAttestation, self).__init__(test_log, arguments, cfg_opts, self.smt_off_config_file)

    def prepare(self):
        # type: () -> None
        """preparing the setup
        Disabling SMT (hyper-Threading)"""
        super(SgxSmtOffAttestation, self).prepare()
        time.sleep(60)
        self.execute_sgx_registration()

    def execute(self):
        """
        Set up bios knobs and verify MP registration is successful with SMT-OFF

        :return: True if Test case pass else False
        """
        self.enable_mp_registration_bios_knob()
        self.sgx.check_sgx_enable()
        if not self.sgx.verify_mp_registration():
            raise content_exceptions.TestFail("MP Registration failed")
        self._log.info("MP registration is successful with SMT-OFF(hyper threading")
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SgxSmtOffAttestation.main() else Framework.TEST_RESULT_FAIL)
