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
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from src.lib.bios_util import ItpXmlCli, PlatformConfigReader

from src.provider.sgx_provider import SGXProvider
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib import content_exceptions
from src.lib.test_content_logger import TestContentLogger
from src.security.tests.mktme.mktme_common import MktmeBaseTest


class SGXMktmeCheck(ContentBaseTestCase):
    """
    HPQC ID : H80201-PI_Security_SGX_MKTMEcheck_L
    Phoneix ID : 18014075623-PI_Security_SGX_MKTMEcheck_L
    Verify SGX enabled through bios and the register values
    Verify SGX enabled through CPUID
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
    BIOS_CONFIG_FILE = "../sgx_enable_through_bios.cfg"
    TEST_CASE_ID = ["H80201", "PI_Security_SGX_MKTMEcheck_L", "18014075623-PI_Security_SGX_MKTMEcheck_L"]
    STEP_DATA_DICT = {1: {'step_details': 'Check SUT in Linux OS and CPU '
                                          'SKU Supports MKTME and Enable TME, MKTME and SGX Bios Knobs',
                          'expected_results': 'SUT should be in Linux and'
                                              'OS Supports MKTME and Verify TME, MKTME and SGX Bios Knobs are Set'},
                      2: {'step_details': 'Execute SGX Functional Validation Tool and Verify if SGX is Working as '
                                          'Expected',
                          'expected_results': 'SGX is Working as Expected after Executing Functional Validation Tool'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SGXMktmeCheck

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
                __file__)), self.BIOS_CONFIG_FILE)

        super(SGXMktmeCheck, self).__init__(
                test_log, arguments, cfg_opts,
                bios_config_file_path=bios_config_file)
        self._log.debug("Bios config file: %s", bios_config_file)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.sgx_provider = SGXProvider.factory(self._log, cfg_opts, self.os, self.sdp)
        self._test_content_logger = TestContentLogger(
            test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._mktme = MktmeBaseTest(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        self._test_content_logger.start_step_logger(1)
        if not self._mktme.verify_mktme():
            raise content_exceptions.TestNAError("This CPU SKU does not "
                                                 "support for MK-TME")
        self._log.info("SUT supports MK-TME Bios Knob")
        super(SGXMktmeCheck, self).prepare()
        
    def execute(self):
        """
        Test main logic to enable and check the bios knobs for SGX enable using ITP and execute Functional Validation
        Tool and verify SGX is Working as Expected.

        :raise: content_exceptions.TestFail if SGX capability not supported
        :return: True if test case executed successfully
        """
        self.xml_config_file = ItpXmlCli(self._log, self._cfg)
        self.platform_xml_config_reader = PlatformConfigReader(self.xml_config_file.get_platform_config_file_path(),
                                                               test_log=self._log)
        mktme_knob_status = self.platform_xml_config_reader.get_knob_status(self._mktme.MKTME_KNOB_NAME)
        self._log.info("MK-TME BIOS Knob status in bios menu= %s", mktme_knob_status)
        #  Verify if MK-TME Bios knob is accessible after TME has been enabled
        if self.platform_xml_config_reader.HIDDEN_KNOB_STATUS == mktme_knob_status:
            raise content_exceptions.TestFail("MK-TME BIOS knob is not exposed after enabling TME knob")
        self._test_content_logger.end_step_logger(1, True)

        self._test_content_logger.start_step_logger(2)
        self._log.info("SGX is Enabled through bios")
        self.sgx_provider.check_sgx_enable()
        if not self.sgx_provider.is_sgx_enabled_cpuid():
            raise content_exceptions.TestFail("SGX capability not supported")
        self._log.info("SGX capability is supported")
        self.sgx_provider.check_sgx_tem_base_test()
        self.sgx_provider.execute_functional_validation_tool()
        self._test_content_logger.end_step_logger(2, True)
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(SGXMktmeCheck, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SGXMktmeCheck.main() else Framework.TEST_RESULT_FAIL)
