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


class SGXNumaOffUmaMemoryExclusivity(content_base_test_case.ContentBaseTestCase):
    """
    Glasgow ID : G59129.0-NUMA OFF (UMA ON) UMA Memory Exclusivity
    HPALM ID : H80109-PI_Security_SGX_UMA_On_SGX_L
    HPALm ID : H81537_PI_Security_SGX_UMA_On_SGX_W

    Verify inability to enable SGX with memory configuration mode UMA ON.
    Configure the BIOS to have SGX and UMA enabled. SGX and UMA Memory Exclusivity i.e.
    when SGX is enabled, Numa cannot be disabled (in other words, UMA cannot be enabled).
    Only when SGX is disabled, UMA can be enabled.
    """
    TEST_CASE_ID = ["G59129.0", "NUMA OFF (UMA ON) UMA Memory Exclusivity", "H80109", "PI_Security_SGX_UMA_On_SGX_L",
                    "H81537", "PI_Security_SGX_UMA_On_SGX_W"]
    SGX_BIOS_CONFIG_FILE = "sgx_enable_without_numa.cfg"
    NUMA_ENABLED_BIOS_CONFIG_FILE = "numa_enable_bios_config.cfg"
    SGX_DISBALE_BIOS_CONFIG_FILE = "sgx_disable_without_numa.cfg"
    NUMA_KNOB_NAME = "NumaEn"
    WAIT_TIME_DELAY = 60

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of SGXNumaOffUmaMemoryExclusivity

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.sgx_disable_bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                         self.SGX_DISBALE_BIOS_CONFIG_FILE)
        self.numa_bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                  self.NUMA_ENABLED_BIOS_CONFIG_FILE)
        self.sgx_bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.SGX_BIOS_CONFIG_FILE)
        super(SGXNumaOffUmaMemoryExclusivity, self).__init__(test_log, arguments,cfg_opts,
                bios_config_file_path=self.sgx_bios_config_file)
        self._csp_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.platform_file = None
        self.platform_read = None

    def prepare(self):
        # type: () -> None
        """preparing the setup and setting knobs"""
        super(SGXNumaOffUmaMemoryExclusivity, self).prepare()

    def execute(self):
        """
        This method executes the following steps:
        1. Verify Numa knob status should be readonly and it is enabled.
        2. Disable SGX knob
        3. Verify Numa knob status should be accessible and it is enabled.

        :raise: content exception if NUMA is readonly or accessible knob is not exposed
        :return: True if Test case pass
        """
        # Generating the platform config file
        csp = ProviderFactory.create(self._csp_cfg, self._log)  # type: SiliconRegProvider
        self.platform_file = ItpXmlCli(self._log, self._cfg)
        self.platform_read = PlatformConfigReader(self.platform_file.get_platform_config_file_path(),
                                                  test_log=self._log)
        # Check Numa Bios Knob is readonly or not
        numa_knob_status = self.platform_read.get_knob_status(self.NUMA_KNOB_NAME)
        self._log.info("NUMA Knob status in bios menu= %s", numa_knob_status)
        if self.platform_read.READONLY_KNOB_STATUS != numa_knob_status:
            raise content_exceptions.TestFail("NUMA knob is not read only after enable SGX")
        self._log.info("NUMA knob is readonly after enable SGX")
        time.sleep(self.WAIT_TIME_DELAY)
        # Verify the numa knob
        self.bios_util.verify_bios_knob(bios_config_file=self.numa_bios_config_file)
        # Disable SGX bios Knob
        self.bios_util.set_bios_knob(self.sgx_disable_bios_config_file)  # To set the bios knob setting.
        self.perform_graceful_g3()
        self.bios_util.verify_bios_knob(self.sgx_disable_bios_config_file)  # To verify the bios knob settings.
        # Updating the platform config file
        self.platform_read.update_xml_file(self.platform_file.get_platform_config_file_path())
        # Check NUMA Bios Knob is accessible or not
        numa_knob_status = self.platform_read.get_knob_status(self.NUMA_KNOB_NAME)
        self._log.info("NUMA Knob status in bios menu= %s", numa_knob_status)
        if self.platform_read.ACCESSIBLE_KNOB_STATUS != numa_knob_status:
            raise content_exceptions.TestFail("NUMA is not exposed in bios after disable SGX")
        self._log.info("NUMA is exposed in bios after disable SGX")
        time.sleep(self.WAIT_TIME_DELAY)
        # Verify Numa Bios Knob
        self.bios_util.verify_bios_knob(bios_config_file=self.numa_bios_config_file)
        self._log.info("This proves SGX and UMA Memory Exclusivity")
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SGXNumaOffUmaMemoryExclusivity.main() else
             Framework.TEST_RESULT_FAIL)
