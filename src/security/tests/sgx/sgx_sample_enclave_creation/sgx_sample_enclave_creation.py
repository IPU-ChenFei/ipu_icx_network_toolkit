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

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.provider.sgx_provider import SGXProvider
from src.lib import content_base_test_case
from src.lib import content_exceptions


class SGXSampleEnclaveCreation(content_base_test_case.ContentBaseTestCase):
    """
    Glasgow ID : G58561.10-Sample_Enclave_Creation
    HPALM ID : H80104-PI_Security_SGX_Sample_Enclave_Creation_L
    Verify SGX Simple enclave creation done
    Hardware
    Serer should be configured with 2S configuration

    Boot to the OS and verify SGX PSW for Linux is installed (Refer to glasgow://testCase=59448 for more details if required)
    cd into /opt/APP/APPs/SGX_Rhel_Intel-Next/sgx_test on the SUT and run the following command:
    ./sgx_app -auto
    cd into /opt/intel/sgxsdk/SampleCode/SampleEnclave and compile the App:
    #make
    From /opt/intel/sgxsdk/SampleCode/SampleEnclave, execute the binary:
    ./app
    """
    BIOS_CONFIG_FILE = "../sgx_enable_through_bios.cfg"
    TEST_CASE_ID = ["G58561.10", "Sample_Enclave_Creation", "H80104", "PI_Security_SGX_Sample_Enclave_Creation_L"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SGXSimpleEnclaveCreation

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), self.BIOS_CONFIG_FILE)

        super(SGXSampleEnclaveCreation, self).__init__(test_log, arguments, cfg_opts,
                                                       bios_config_file_path=bios_config_file)
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("This test is not applicable for " + self.os.os_type)
        self._log.debug("Bios config file: %s", bios_config_file)
        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.srp = ProviderFactory.create(sil_cfg, test_log)  # type: SiliconRegProvider
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.sgx = SGXProvider.factory(test_log, cfg_opts, self.os,
                                       self.sdp)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(SGXSampleEnclaveCreation, self).prepare()
        self.sgx.check_sgx_enable()

    def execute(self):
        """Check for SGX simple enclave creation"""
        self._log.info("SGX set successfully")
        self.sgx.check_sample_enclave_creation()
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(SGXSampleEnclaveCreation, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SGXSampleEnclaveCreation.main()
             else Framework.TEST_RESULT_FAIL)
