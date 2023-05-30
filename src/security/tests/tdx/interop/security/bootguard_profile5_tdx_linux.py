#!/usr/bin/env python
##########################################################################
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
##########################################################################
"""
    :BootGuard Profile 5 Interop with TDX:

    With BootGuard Profile 5 enabled, boot a TD guest successfully.
"""

import os
import sys
import time
import argparse
import logging
from xml.etree import ElementTree

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import ProductFamilies
from dtaf_core.lib.configuration import ConfigurationHelper
from dtaf_core.providers.flash_provider import FlashProvider
from dtaf_core.providers.provider_factory import ProviderFactory

from src.lib import content_exceptions
from src.lib.flash_util import FlashUtil
from src.lib.dtaf_content_constants import PowerStates
from src.security.tests.tdx.tdvm.TDX050_launch_multiple_tdvm_linux import MultipleTDVMLaunch
from src.security.tests.cbnt_boot_guard.boot_guard.boot_guard_common import BootGuardValidator
from src.security.tests.cbnt_boot_guard.cbnt_boot_guard_constants import BootGuardConstants


class TdxBtgProfile5(MultipleTDVMLaunch):
    """
            This recipe enables BootGuard and TDX together and verifies a TD guest can launch with BootGuard profile 5
            enabled.

            :Scenario: Enable BootGuard profile 5 in IFWI, enable TDX, and boot to OS.  Then launch defined number of
            TD guests (per <NUM_OF_VMS> param in content_configuration.xml).  If SUT is not set up with Banino, SUT
            will need to have a BootGuard profile 5 enabled IFWI programmed onto the SUT.

            :Phoenix ID: https://hsdes.intel.com/appstore/article/#/18014074009

            :Test steps:

                :1:  Enable BootGuard profile 5 on SUT and boot to trusted MLE

                :2:  Enable TDX and boot to OS.

                :3:  Launch a TD guest.

                :4:  Verify BootGuard profile 5 is enabled.

            :Expected results: TD guest should boot and should not yield MCEs.  MSR values should match expected for
            BootGuard profile 5.

            :Reported and fixed bugs:

            :Test functions:

        """

    def __init__(self, test_log: logging.Logger, arguments: argparse.Namespace, cfg_opts: ElementTree) -> None:
        """
        Create an instance of test case.
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(TdxBtgProfile5, self).__init__(test_log, arguments, cfg_opts)
        try:
            self.bootguard = BootGuardValidator(test_log, arguments, cfg_opts)
            if not os.ispath.isfile(self._common_content_configuration.get_ifwi_image_path(self.bootguard.PROFILE5)):
                raise content_exceptions.TestSetupError(f"IFWI is not defined for BootGuard Profile 5 "
                                                        f"(<ifwi><ifwi_profile_bin_path><profile5> in "
                                                        f"content_configuration.xml): "
                                                        f"{self._common_content_configuration.get_ifwi_image_path(self.bootguard.PROFILE5)}")
            if not os.ispath.isfile(self._common_content_configuration.get_ifwi_image_path("IFWI Current Version")):
                raise content_exceptions.TestSetupError(f"No IFWI provided for current IFWI programmed "
                                                        f"(<ifwi><ifwi_profile_bin_path><current_ifwi_version> in "
                                                        f"content_configuration.xml): "
                                                        f"{self._common_content_configuration.get_ifwi_image_path('IFWI Current Version')}")
        except IndexError:
            self.bootguard = None
            self._log.warning("SUT is not equipped with flash provider tools required for BootGuard test.  Will not "
                              "attempt to reflash the IFWI and will instead check MSR if BootGuard profile 5 is "
                              "enabled.  Refer to Flashing_provider_configuration_bkm.md at repo root for set up "
                              "instructions.")
            self.bootguard_constants = BootGuardConstants

    def prepare(self):
        if self.bootguard:
            self.bootguard.flash_binary_image(self.bootguard.PROFILE5)
            if not self.bootguard.verify_profile_5():
                raise content_exceptions.TestSetupError("BootGuard profile 5 is not active on the IFWI.")
        else:
            bootguard_msr_value = self.msr_read(self.bootguard_constants.BTG_SACM_INFO_MSR_ADDRESS)
            results = bootguard_msr_value in self.bootguard_constants.BootGuardValues.CBNT_BTG_P5_VALID
            if not results:
                raise content_exceptions.TestFail("Failed to verify profile 5 on SUT.  Expected one of the following "
                                                  f"{', '.join(hex(val) for val in self.bootguard_constants.BootGuardValues.CBNT_BTG_P5_VALID)}, got "
                                                  f"0x{bootguard_msr_value:0x}.")
        super(TdxBtgProfile5, self).prepare()

    def execute(self) -> bool:
        if not super(TdxBtgProfile5, self).execute():
            raise content_exceptions.TestFail("Failed to boot TD guests.")
        return True

    def cleanup(self, return_status: bool) -> None:
        self.bootguard.cleanup(return_status)
        super(TdxBtgProfile5, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TdxBtgProfile5.main() else Framework.TEST_RESULT_FAIL)
