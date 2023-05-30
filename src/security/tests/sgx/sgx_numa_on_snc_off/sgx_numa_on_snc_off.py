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
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.provider.sgx_provider import SGXProvider
from src.lib import content_base_test_case
from src.lib import content_exceptions


class SGXNumaOnSNCOFF(content_base_test_case.ContentBaseTestCase):
    """
    HPALM ID : H67510/H81538
    In the BIOS setting interface,
    for SGX reserved memory, set NUMA ON, set Sub Noma Disable and checks the system boots up
    """
    BIOS_CONFIG_FILE = "../sgx_enable_through_bios.cfg"
    SELF_CONFIG_FILE = "sgx_numa_on_snc_off.cfg"
    TEST_CASE_ID = ["H67510-PI_Security_SGX_NUMA_On_SNC_Off_SGX", "H81538-PI_Security_SGX_NUMA_On_SNC_Off_SGX_W"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SGXNumaOnSNCOFF

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), self.BIOS_CONFIG_FILE)

        self.self_bios_config_file = os.path.join(os.path.dirname(
            os.path.abspath(__file__)), self.SELF_CONFIG_FILE)

        super(SGXNumaOnSNCOFF, self).__init__(test_log, arguments, cfg_opts,
                                              bios_config_file_path=bios_config_file)
        self._log.debug("Bios config file: %s", bios_config_file)
        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.srp = ProviderFactory.create(sil_cfg, test_log)  # type: SiliconRegProvider
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.sgx_provider = SGXProvider.factory(self._log, cfg_opts, self.os,
                                        self.sdp)

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(SGXNumaOnSNCOFF, self).prepare()

    def execute(self):
        """test main logic to enable and check
        the SUT boots up after disable Sub Numa
        """
        self._log.info("SGX set successfully through bios")
        self.sgx_provider.check_sgx_enable()
        self._log.info("Disabling sub numa")
        self.bios_util.set_bios_knob(self.self_bios_config_file)
        self.perform_graceful_g3()
        self.sgx_provider.check_sgx_enable()
        self.bios_util.verify_bios_knob(self.self_bios_config_file)
        self._log.info("SGX is verified with SNC off")
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(SGXNumaOnSNCOFF, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SGXNumaOnSNCOFF.main() else
             Framework.TEST_RESULT_FAIL)
