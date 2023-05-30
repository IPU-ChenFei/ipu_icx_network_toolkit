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
import os
import sys
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from src.lib.test_content_logger import TestContentLogger

from src.provider.sgx_provider import SGXProvider
from src.lib import content_base_test_case, content_exceptions


class SGXDynamicEnclaveMemoryAllocation(content_base_test_case.ContentBaseTestCase):
    """
    Glasgow ID : G59143.3-Dynamic Enclave Memory Allocation
    Verify the platforms ability to increase of enclave size
    on demand relative to data size being moved into and/or out of the enclave. EDMM enables capability for enclaves
    to add/expand memory (heap, stack, thread TCS) after it is initialized

    Run the SGX SDK Sample Enclave App with dynamic threads: For a static thread, total available stack is 0x40000
    However, for a dynamic thread, once it is created, total available stack is  0x2000, the gap, that is 0x40000 -
    0x2000, can be dynamically expanded as necessary.

    In the SGX SDK, use sample configuration file config04.xml for the Sample Enclave - config04 makes use of dynamic
    heap, thread for enclave and so it uses EDMM instructions automatically. For a dynamic thread, stack will
    expanded as necessary to exercise EDMM flow
    """
    TEST_CASE_ID = ["G59143.3", "Dynamic_Enclave_Memory_Allocation"]
    BIOS_CONFIG_FILE = "../sgx_enable_through_bios.cfg"

    STEP_DATA_DICT = {
        1: {'step_details': 'Enable SGX in the BIOS',
            'expected_results': 'Successfully set SGX in the BIOS'},
        2: {'step_details': 'Verify that SGX is enabled',
            'expected_results': 'Successfully Verified that SGX is enabled'},
        3: {'step_details': 'Modify Makefile ,Build the SampleEnclave App and Run the app using ./ap',
            'expected_results': 'Modified Makefile, Built SampleEnclave App and '
                                'SampleEnclave successfully returned'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SGXDynamicEnclaveMemoryAllocation

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(SGXDynamicEnclaveMemoryAllocation, self).__init__(test_log, arguments, cfg_opts,
                                                                bios_config_file_path=self.bios_config_file)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.sgx_provider = SGXProvider.factory(self._log, cfg_opts, self.os, self.sdp)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        self._test_content_logger.start_step_logger(1)
        super(SGXDynamicEnclaveMemoryAllocation, self).prepare()
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        Steps :
        1) Verify that SGX is enabled in the BIOS
        2) Boot to the OS and ensure that the SGX driver, SDK, PSW and FunctionalValidationTool (FVT) are installed
        3) On OS boot, cd into /opt/intel/sgxsdk/SampleCode/SampleEnclave
        4) Modify Makefile to use sample configuration file config04.xml for the Sample Enclave - config4.xml
        5) Build the SampleEnclave App and make Verify that the app successfully builds with the following output:
                Succeed. SIGN =>  enclave.signed.so
                The project has been built in debug hardware mode
        5)Run the app using ./app Capture the console log and verify that the SampleEnclave successfully returned.

        :return: True if the testcase passes.
        """
        self._test_content_logger.start_step_logger(2)
        self._log.info("SGX set successfully through bios")
        self.sgx_provider.check_sgx_enable()
        self._log.info("SGX capability is supported")
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        self.sgx_provider.dynamic_enclave_memory_allocation()
        self._log.info("Dynamic Enclave memory allocation verified")
        self._test_content_logger.end_step_logger(3, return_val=True)

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(SGXDynamicEnclaveMemoryAllocation, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SGXDynamicEnclaveMemoryAllocation.main()
             else Framework.TEST_RESULT_FAIL)
