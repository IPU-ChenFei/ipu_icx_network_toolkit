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
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib import content_exceptions
from src.security.tests.sgx.sgx_common import SgxCommon


class SGXCheckDataSealing(SgxCommon):
    """
    HPALM ID : H80194-PI_Security_SGX_DataSealing_L
    Glasgow ID : G58583.7-Data_Sealing
    Phoneix ID : P18014073500-Data Sealing
    3rd steps has to be implemented put SGX in check PSW provider.
    Verify SGX Simple enclave creation done
    Hardware
    Serer should be configured with 2S configuration

    Boot to the OS and verify SGX PSW for Linux is installed (Refer to glasgow://testCase=59448 for
    more details if required)
    cd into /opt/APP/APPs/SGX_Rhel_Intel-Next/sgx_test on the SUT and run the following command:
    ./sgx_app -auto
    cd into /opt/intel/sgxsdk/SampleCode/SampleEnclave and compile the App:
    #make
    From /opt/intel/sgxsdk/SampleCode/SampleEnclave, execute the binary:
    ./app
    """

    TEST_CASE_ID = ["H80194-PI_Security_SGX_DataSealing_L", "G58583.7-Data_Sealing", "P18014073500-Data_Sealing"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SGXSimpleEnclaveCreation

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(SGXCheckDataSealing, self).__init__(test_log, arguments, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("This test is not applicable for " + self.os.os_type)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(SGXCheckDataSealing, self).prepare()
        self.sgx_provider.check_sgx_enable()

    def execute(self):
        """Check for SGX simple enclave creation"""
        self._log.info("SGX set successfully")
        self.sgx_provider.check_data_sealing()
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(SGXCheckDataSealing, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SGXCheckDataSealing.main()
             else Framework.TEST_RESULT_FAIL)
