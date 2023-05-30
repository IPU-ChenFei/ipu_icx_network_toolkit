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
from dtaf_core.providers.console_log import ConsoleLogProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.provider.sgx_provider import SGXProvider
from src.lib import content_base_test_case
from src.lib import content_exceptions


class SGXNumaOnSNCOn(content_base_test_case.ContentBaseTestCase):
    """
    HPALM ID : H80111-PI_Security_SGX_NUMA_ON_SNC_On_SGX_L/H81539-PI_Security_SGX_NUMA_ON_SNC_On_SGX_W
    In the BIOS setting interface,
    for SGX reserved memory, set NUMA ON, set Sub Noma Clustering (SNC) On (Need check SNC2 and SNC4 one by one.)
    """
    BIOS_CONFIG_FILE = "../sgx_enable_through_bios.cfg"
    SNC2_CONFIG_FILE = "snc2.cfg"
    SNC4_CONFIG_FILE = "snc4.cfg"
    _BIOS_LOG_MATCHES = ["[SGX] SgxLateInit exit: success",
                         "SGX activated",
                         "[SGX] SgxAfterPlatformLocksCallback exit: success",
                         "SGX PreMem Init"]
    TEST_CASE_ID = ["H80111-PI_Security_SGX_NUMA_ON_SNC_On_SGX_L", "H81539-PI_Security_SGX_NUMA_ON_SNC_On_SGX_W"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SGXNumaOnSNCOn

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), self.BIOS_CONFIG_FILE)

        self.snc2_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), self.SNC2_CONFIG_FILE)
        self.snc4_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), self.SNC4_CONFIG_FILE)

        super(SGXNumaOnSNCOn, self).__init__(test_log, arguments, cfg_opts,
                                             bios_config_file_path=bios_config_file)
        self._log.debug("Bios config file: %s", bios_config_file)
        sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.srp = ProviderFactory.create(sil_cfg, test_log)  # type: SiliconRegProvider
        si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self.sdp = ProviderFactory.create(si_dbg_cfg, test_log)  # type: SiliconDebugProvider
        self.cng_cfg = cfg_opts.find(ConsoleLogProvider.DEFAULT_CONFIG_PATH)
        self.sgx_provider = SGXProvider.factory(self._log, cfg_opts, self.os,
                                        self.sdp)
        self.errors = []

    def prepare(self):
        # type: () -> None
        """preparing the setup"""
        super(SGXNumaOnSNCOn, self).prepare()

    def rename_console_log(self, log_dir, new_name):
        # type: () -> None
        """Rename the copied console log

        :param log_dir: log directory
        :param new_name: new name for the given file
        """
        self._log.debug("Renaming console log to appropriate file name(%s)", new_name)
        if os.path.exists(log_dir):
            for file in os.listdir(log_dir):
                if file.endswith("_console.log"):
                    os.rename(os.path.join(log_dir, file), os.path.join(log_dir, new_name))

    def set_and_verify_subnuma_knobs(self, config_file, serial_log_file):
        """Set and verify subnuma knobs and also checks the serial logs for
        activation
        """
        self.cng_log.redirect(serial_log_file)
        self.bios_util.set_bios_knob(config_file)
        self.perform_graceful_g3()
        self.sgx_provider.check_sgx_enable()
        self.bios_util.verify_bios_knob(config_file)
        self._log.info("Checking the logs for expected matches")
        with open(serial_log_file) as f:
            console_data = f.read()
            for match in self._BIOS_LOG_MATCHES:
                self._log.debug("Checking %s in console data", match)
                if match not in console_data:
                    self.errors.append("%s not found in %s bios log" % (
                        match, serial_log_file))

    def execute(self):
        """test main logic to enable and check the bios knobs for SGX enable"""
        self._log.info("SGX set successfully through bios")
        self.sgx_provider.check_sgx_enable()
        # SNC2 Verification
        snc2_serial_log = os.path.join(self.serial_log_dir,
                                       "snc2_serial_log.log")
        self.set_and_verify_subnuma_knobs(self.SNC2_CONFIG_FILE, snc2_serial_log)
        snc4_serial_log = os.path.join(self.serial_log_dir,
                                       "snc4_serial_log.log")
        self.set_and_verify_subnuma_knobs(self.SNC4_CONFIG_FILE,
                                          snc4_serial_log)
        self._log.debug("Errors: %s", ",".join(self.errors))
        if len(self.errors):
            raise content_exceptions.TestFail(",".join(self.errors))
        self._log.info("Test has been completed successfully!")
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        """DTAF cleanup"""
        super(SGXNumaOnSNCOn, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SGXNumaOnSNCOn.main() else
             Framework.TEST_RESULT_FAIL)
