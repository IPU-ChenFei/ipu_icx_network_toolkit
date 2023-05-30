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

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider

from src.provider.sgx_provider import SGXProvider
from src.lib import content_base_test_case, content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.lib.dtaf_content_constants import TimeConstants
from src.security.tests.sgx.sgx_common import SgxCommon


class SgxHydraTestWindows(SgxCommon):
    """
    Phoenix ID : P18015174685-SGXHydra_Test

    SGXHydra is an application that can be run on windows to stress test SGX.
    """
    TEST_CASE_ID = ["P18015174685", "SGXHydra_Test"]
    STEP_DATA_DICT = {
        1: {'step_details': 'Enable SGX and verify in BIOS',
            'expected_results': 'SGX enabled and verified successfully'},
        2: {'step_details': 'Copy Hydra tool and run hydra tool for specific duration',
            'expected_results': 'Hydra tool should be copied and executed successfully'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SgxHydraTest

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(SgxHydraTestWindows, self).__init__(test_log, arguments, cfg_opts)
        if self.os.os_type != OperatingSystems.WINDOWS:
            raise content_exceptions.TestNAError("This test is not applicable for " + self.os.os_type)
        self.enclave_mb = arguments.ENCLAVEMB
        self.num_enclave_threads = arguments.ENCLAVETHREAD
        self.num_regular_threads = arguments.REGULARTHREAD
        self.time_duration = arguments.TIME
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self.sgx_provider = SGXProvider.factory(self._log, cfg_opts, self.os, self.sdp)

    @classmethod
    def add_arguments(cls, parser):
        """
        :param parser: argument parser
        :return: None
        """
        super(SgxHydraTestWindows, cls).add_arguments(parser)
        parser.add_argument("-en", "--ENCLAVEMB", action="store", dest="ENCLAVEMB", default="128")
        parser.add_argument("-et", "--ENCLAVETHREAD", action="store", dest="ENCLAVETHREAD", default="12")
        parser.add_argument("-rt", "--REGULARTHREAD", action="store", dest="REGULARTHREAD", default="12")
        parser.add_argument("-t", "--TIME", action="store", dest="TIME", default=TimeConstants.FIVE_MIN_IN_SEC)

    def prepare(self):
        """preparing the setup by enabling sgx and verifying if sgx is enabled successfully"""
        self._test_content_logger.start_step_logger(1)
        super(SgxHydraTestWindows, self).prepare()
        self.sgx_provider.check_sgx_enable()
        self._log.info("SGX set successfully")
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        This method Runs Hydra tool for specific duration of time.

        :return: True if the Test pass else False
        """
        self._test_content_logger.start_step_logger(2)
        self.sgx_provider.execute_fvt_and_app_test()
        self.sgx_provider.run_hydra_test(int(self.time_duration), self.enclave_mb, self.num_enclave_threads,
                                         self.num_regular_threads)
        self._test_content_logger.end_step_logger(2, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SgxHydraTestWindows.main() else Framework.TEST_RESULT_FAIL)
