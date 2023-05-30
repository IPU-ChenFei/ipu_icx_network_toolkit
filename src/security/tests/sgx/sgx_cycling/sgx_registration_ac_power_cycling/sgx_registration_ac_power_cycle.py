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
from src.security.tests.sgx.sgx_registration.sgx_auto_multipackage_registration.\
    sgx_auto_multipackage_registration import SgxAutoMultiPackageRegistration


class SGXRegistrationAcPowerCycle(SGXCyclingCommon):
    """
    Testcase_id : P18015174664
    This TestCase is Used to Verify SGX Status by Performing AC Cycles and verifying the status in Every Cycle.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new SGXRegistrationAcPowerCycle object

        :param test_log: Used for debug and info messages
        :param arguments:None
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(SGXRegistrationAcPowerCycle, self).__init__(test_log, arguments, cfg_opts)
        self.total_sgx_ac_cycle_number, self.ac_cycle_recovery_mode = \
            self._common_content_configuration.get_sgx_num_of_cycles(self._AC_CYCLE_REG)
        self._sgx_auto_reg_obj = SgxAutoMultiPackageRegistration(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        Function calling AutoRegistration prepare and execute method
        """
        self._sgx_auto_reg_obj.prepare()
        self._sgx_auto_reg_obj.execute()

    def execute(self):
        """
        This Method is Used to execute verify sgx status in various ac cycles
        :return: True if all AC power cycle complete else False
        """
        ac_cycle_str = "AC Cycle Registration"
        self.sgx_provider.check_sgx_tem_base_test()
        self.trigger_sgx_cycle(self.total_sgx_ac_cycle_number, self.sgx_cycle_type[self._AC_CYCLE_REG],
                               ac_cycle_str, self.ac_cycle_recovery_mode, True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SGXRegistrationAcPowerCycle.main() else Framework.TEST_RESULT_FAIL)
