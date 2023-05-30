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

from src.security.tests.sgx.sgx_common import SgxCommon


class SGXEnumerationDiscovery(SgxCommon):
    """
    Glasgow ID : G58852-SGX Enumeration & Discovery
    HPQC ID : H80102-PI_Security_SGX_Enumeration_Discovery_L/H81530-PI_Security_SGX_Enumeration_Discovery_W
    Phoenix ID :P18014073943-SGX Enumeration & Discovery
    Verify SGX enabled through bios and the register values
    Hardware
    Server should be configured with 2S configuration

    Software
    Navigate to EDKII Menu/Socket Configuration/Processor Configuration
    Verify Total Memory Encryption (TME) option is exposed in the BIOS
    EDKII->Socket Configuration->Processor Configuration->Total Memory Encryption (TME) = Enable
    Verify SGX (SW Guard Extensions) option is exposed in the BIOS
    EDKII->Socket Configuration->Processor Configuration->SW Guard Extensions (SGX) = Enable
    Save (F10). Reset at the top of BIOS menu. Wait till BIOS reboot
    """
    TEST_CASE_ID = ["G58852-SGX_Enumeration_Discovery", "H80102-PI_Security_SGX_Enumeration_Discovery_L",
                    "P18014073943-SGX_Enumeration_Discovery"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SGXEnumerationDiscovery

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(SGXEnumerationDiscovery, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(SGXEnumerationDiscovery, self).prepare()

    def execute(self):
        """
        Test main logic to enable and check the bios knobs for SGX enable using ITP and

        :raise: content_exceptions.TestFail if SGX capability not supported
        """
        self._log.info("SGX set successfully through bios")
        self.sgx_provider.check_sgx_enable()
        self._log.info("SGX capability is supported")
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(SGXEnumerationDiscovery, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SGXEnumerationDiscovery.main()
             else Framework.TEST_RESULT_FAIL)
