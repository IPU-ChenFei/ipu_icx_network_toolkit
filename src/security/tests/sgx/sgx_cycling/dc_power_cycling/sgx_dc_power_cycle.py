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

import src.lib.content_exceptions as content_exceptions
from src.security.tests.sgx.sgx_cycling.sgx_cycling_common import SGXCyclingCommon
from src.provider.sgx_provider import SGXProvider


class SGXDcPowerCycle(SGXCyclingCommon):
    """
    Testcase_id : P18015174655-DC Power Cycling (Cold Reset)
    This TestCase is Used to Verify SGX Status by Performing DC Cycles and verifying the SGX status in Every Cycle.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new SGXDcPowerCycle object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(SGXDcPowerCycle, self).__init__(test_log, arguments, cfg_opts)
        self.total_sgx_dc_cycle_number, self.dc_cycle_recovery_mode = \
            self._common_content_configuration.get_sgx_num_of_cycles(self._DC_CYCLE)

    def prepare(self):
        # type: () -> None
        """
        1. Set the bios knobs to its default mode.
        2. Set the bios knobs as per the test case.
        3. Reboot the SUT to apply the new bios settings.
        4. Verify the bios knobs whether they updated properly.
        """
        super(SGXDcPowerCycle, self).prepare()

    def execute(self):
        """
        This Method is used to verify sgx status in various dc cycles
        :raise: raise content_exceptions.TestFail if MSR for SGX does not match
                raise content_exceptions.TestFail if warm reboot cycle fails
        :return: True if all dc power cycle complete else False
        """
        dc_cycle_str = "DC Cycle"
        if not self.sgx_provider.is_sgx_enabled():
            raise content_exceptions.TestFail("Verifying SGX with MSR and EAX value is not successful")
        self.sgx_provider.check_sgx_tem_base_test()
        self.trigger_sgx_cycle(self.total_sgx_dc_cycle_number, self.sgx_cycle_type[self._DC_CYCLE],
                               dc_cycle_str, self.dc_cycle_recovery_mode)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SGXDcPowerCycle.main() else Framework.TEST_RESULT_FAIL)
