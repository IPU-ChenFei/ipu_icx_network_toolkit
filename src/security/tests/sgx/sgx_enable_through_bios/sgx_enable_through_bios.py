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
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.lib.bios_util import ItpXmlCli, PlatformConfigReader
from src.lib import content_base_test_case
from src.lib import content_exceptions


class SGXEnableThroughBios(content_base_test_case.ContentBaseTestCase):
    """
    Glasgow ID : G58854.10-Enable_SGX
    HPQC ID: H80099-PI_Security_SGX_Enable_SGX_L/H81527-PI_Security_SGX_Enable_SGX_W

    Verify SGX enabled through bios
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
    TEST_CASE_ID = ["G58854.10-Enable_SGX", "H80099-PI_Security_SGX_Enable_SGX_L", "H81527-PI_Security_SGX_Enable_SGX_W"]
    TME_BIOS_CONFIG_FILE = "total_memory_encryption.cfg"
    SGX_BIOS_CONFIG_FILE = "sw_guard_extensions.cfg"
    TME_KNOB_NAME = "EnableTme"
    SGX_KNOB_NAME = "EnableSgx"
    WAIT_TIME_DELAY = 60

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SGXEnableThroughBios

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.tme_bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), self.TME_BIOS_CONFIG_FILE)
        self.sgx_bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), self.SGX_BIOS_CONFIG_FILE)
        super(SGXEnableThroughBios, self).__init__(
                test_log, arguments,cfg_opts)
        self._csp_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self._csp = None

    def prepare(self):
        # type: () -> None
        """preparing the setup and setting knobs"""
        super(SGXEnableThroughBios, self).prepare()

    def execute(self):
        """
        This method executes the following steps:
        1. Verify Total Memory Encryption (TME) option is exposed in the BIOS
        2. Enable TME knob
        3. Verify SGX (SW Guard Extensions) option is exposed in the BIOS
        4. Enable SGX knob

        :raise: content exception if TME or SGX knob is not exposed
        :return: True if Test case pass
        """
        # Generating the platform config file
        self._csp = ProviderFactory.create(self._csp_cfg, self._log)  # type: SiliconRegProvider
        platform_file = ItpXmlCli(self._log, self._cfg)
        platform_read = PlatformConfigReader(platform_file.get_platform_config_file_path(), test_log=self._log)
        # Check TME Bios Knob is visible or not
        tme_knob_status = platform_read.get_knob_status(self.TME_KNOB_NAME)
        self._log.info("TME Knob status in bios menu= %s", tme_knob_status)
        if platform_read.HIDDEN_KNOB_STATUS == tme_knob_status:
            raise content_exceptions.TestFail("TME Knob is not visible")
        self._log.info("TME knob is exposed in bios")
        time.sleep(self.WAIT_TIME_DELAY)
        # Enable TME Bios Knob
        self.bios_util.set_bios_knob(bios_config_file=self.tme_bios_config_file)
        self.perform_graceful_g3()
        time.sleep(self.WAIT_TIME_DELAY)
        self.bios_util.verify_bios_knob(bios_config_file=self.tme_bios_config_file)
        # Updating the platform config file
        platform_read.update_xml_file(platform_file.get_platform_config_file_path())
        # Check SGX Bios Knob is visible or not
        sgx_knob_status = platform_read.get_knob_status(self.SGX_KNOB_NAME)
        self._log.info("SGX Knob status in bios menu= %s", sgx_knob_status)
        if platform_read.HIDDEN_KNOB_STATUS == sgx_knob_status:
            raise content_exceptions.TestFail("SGX knob is still not exposed after enabling TME")
        self._log.info("SGX is exposed in bios")
        time.sleep(self.WAIT_TIME_DELAY)
        # Enable SGX Bios Knob
        self.bios_util.set_bios_knob(bios_config_file=self.sgx_bios_config_file)
        self.perform_graceful_g3()
        time.sleep(self.WAIT_TIME_DELAY)
        self.bios_util.verify_bios_knob(bios_config_file=self.sgx_bios_config_file)
        self._log.info("SGX is enabled  successfully")

        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(SGXEnableThroughBios, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SGXEnableThroughBios.main() else
             Framework.TEST_RESULT_FAIL)
