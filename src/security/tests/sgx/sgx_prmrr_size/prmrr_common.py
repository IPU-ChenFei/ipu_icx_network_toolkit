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
from src.lib.dtaf_content_constants import TimeConstants
from src.security.tests.sgx.sgx_common import SgxCommon


class SgxPrmBaseTest(SgxCommon):
    """
    Base class extension for TXT which holds common arguments, functions
    """

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        """
        Create an instance of SgxPrmBaseTest

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.enclave_mb = arguments.ENCLAVEMB
        self.num_enclave_threads = arguments.ENCLAVETHREAD
        self.num_regular_threads = arguments.REGULARTHREAD
        self.time_duration = arguments.TIME
        self.bios_config_file_path_prm = bios_config_file
        super(SgxPrmBaseTest, self).__init__(test_log, arguments, cfg_opts)

    @classmethod
    def add_arguments(cls, parser):
        """
        :param parser: argument parser
        :return: None
        """
        super(SgxPrmBaseTest, cls).add_arguments(parser)
        parser.add_argument("-en", "--ENCLAVEMB", action="store", dest="ENCLAVEMB", default="128")
        parser.add_argument("-et", "--ENCLAVETHREAD", action="store", dest="ENCLAVETHREAD", default="12")
        parser.add_argument("-rt", "--REGULARTHREAD", action="store", dest="REGULARTHREAD", default="12")
        parser.add_argument("-t", "--TIME", action="store", dest="TIME", default=TimeConstants.FIVE_MIN_IN_SEC)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(SgxPrmBaseTest, self).prepare()
        self.set_bios_knob_without_default(self.bios_config_file_path_prm)

    def execute(self):
        """
        1. Verify EAX and MSR value for SGX and
        2. Run hydra app for Windows os
        """
        self.sgx_provider.check_sgx_enable()
        self.sgx_provider.execute_fvt_and_app_test()
        self.sgx_provider.run_hydra_test(int(self.time_duration), self.enclave_mb, self.num_enclave_threads,
                                         self.num_regular_threads)
