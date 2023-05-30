#!/usr/bin/env python
##########################################################################
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
##########################################################################
"""
    :TDX Attestation HT On:

    Enable TDX and Hyperthreading, then run TDX attestation check.
"""
import sys
import os

from dtaf_core.lib.dtaf_constants import Framework
from src.security.tests.tdx.attestation.linux_attestation_base_test import TdAttestation


class TdAttestationHtOn(TdAttestation):
    """
            This test case is to test the coexistence of HyperThreading and TDX attestation.

            :Scenario: Enable HyperThreading in BIOS and run TDX attestation verification script.

            :Phoenix IDs: 22013145058

            :Test steps:

                :1: Enable HyperThreading in BIOS.

                :2: Enable TDX in BIOS.

                :3: Boot to OS and run TDX attestation script.

            :Expected results: Attestation script should complete with exit code 0 and no errors.

            :Reported and fixed bugs:

            :Test functions:

        """
    def __init__(self, test_log, arguments, cfg_opts):
        """Create an instance of LinuxTdxBaseTest

        :param cfg_opts: Configuration Object of provider
        :type cfg_opts: str
        :param test_log: Log object
        :type arguments: Namespace
        :param arguments: None
        :type cfg_opts: Namespace
        :return: None
        """
        super(TdAttestationHtOn, self).__init__(test_log, arguments, cfg_opts)
        self.hyper_threading_en_bios_knob_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                              "../collateral/smt_en_reference_knobs.cfg")

    def prepare(self) -> None:
        super(TdAttestationHtOn, self).prepare()
        self.check_knobs(self.hyper_threading_en_bios_knob_file, set_on_fail=True)

    def execute(self) -> bool:
        return super(TdAttestationHtOn, self).execute()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TdAttestationHtOn.main() else Framework.TEST_RESULT_FAIL)
