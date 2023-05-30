# !/usr/bin/env python
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
from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.security.tests.cbnt_txt.txt_base.Trusted_boot_with_tboot import TrustedBootWithTboot
from src.security.tests.cbnt_boot_guard.cbnt_boot_guard_constants import CBnTConstants


class AnchorCovePublicKeyHashCheckout(BaseTestCase):
    """
    Glasgow ID : 58677
    Verify Production key on production PCH and the Debug key on Debug PCH.
    """

    ADDRESS_TO_READ_PCH_VAL = None
    SIZE_IN_BYTE = 0x8
    BIT_31_VAL = 2**31
    PCH_READ_ADDRESS_BIT = 31

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of AnchorCovePublicKeyHashCheckout

        :param test_log: Used for error, debug and info messages.
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(AnchorCovePublicKeyHashCheckout, self).__init__(test_log, arguments, cfg_opts)
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider
        self._common_content = CommonContentLib(self._log, self._os, cfg_opts)
        self._common_content_config = ContentConfiguration(self._log)
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._sdp = ProviderFactory.create(
            si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self._trusted_boot = TrustedBootWithTboot(test_log, arguments, cfg_opts)
        self._cbnt_const = CBnTConstants()

    def prepare(self):
        """
        Prepares the environment according to test case 58199.

        :return: None
        """
        self._trusted_boot.prepare()  # execute the prepare method of test case 58199
        self._trusted_boot.execute()  # execute the execute method of test case 58199

    def execute(self):
        """
        Checking CPU is production PCH if not then checking debug PCH.

        :return True if verifies the silicon used and false if not
        """
        if self._common_content_config.get_production_silicon():
            self._sdp.halt()
            result = self._sdp.itp.threads[0].mem(self._cbnt_const.ADDRESS_TO_READ_PCH_VAL, self.SIZE_IN_BYTE)
            if result and self.BIT_31_VAL:
                self._log.info("Test Passed: Production PCH is in use")
                ret_val = True
            else:
                self._log.error("Failed : Production PCH is not in use")
                ret_val = False
        else:
            result = self._sdp.itp.threads[0].mem(self._cbnt_const.ADDRESS_TO_READ_PCH_VAL, self.SIZE_IN_BYTE)
            output = self._common_content.get_bits(result, self.PCH_READ_ADDRESS_BIT)
            if not output:
                self._log.info("Test Passed: Debug PCH is in use")
                ret_val = True
            else:
                self._log.error("Failed : Debug PCH is not in use")
                ret_val = False

        return ret_val


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if AnchorCovePublicKeyHashCheckout.main() else Framework.TEST_RESULT_FAIL)
