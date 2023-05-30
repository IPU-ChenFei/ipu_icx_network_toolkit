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

from dtaf_core.lib.dtaf_constants import Framework
from src.lib import content_exceptions
from src.ras.tests.pcie.pei_card.test.pcie_hw_leaky_bucket_basetest import PcieHWLeakyBucketBaseTest


class PcieHWLeakyBucketExpectedBerChangeTest(PcieHWLeakyBucketBaseTest):
    """
    Phoenix_id : 22012665605

    The objective of this test is to enable verification of Leaky Bucket flow in response to bad DLLP and bad TLP packets
    by way of injecting them with PEI 4.0 card. Verfiy the Leaky Bucket Flow with various BER value for Leaky Bucket

     Requirements:

     1. BIOS config file path configured in system_configuration.xml
     2. Socket of PEI 4.0 card configured in content_configuration.xml
     3. pxp port of PEI 4.0 card configured in content_configuration.xml
     4. PEI 4.0 HW injector card

     Usage:

     Error type injection is controlled by the "test" parameter in the execute() method and is set to "badDLLP" by default
     To execute the test for bad TLP, set test="badTLP"

    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new PcieHWLeakyBucketBaseTest object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PcieHWLeakyBucketExpectedBerChangeTest, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs whether they updated properly.

        :return: None
        """
        super(PcieHWLeakyBucketExpectedBerChangeTest, self).prepare()

    def execute(self, err_type="badDLLP", expect_link_degrade=True):
        """
        This method checks the OS log for errors given a supported error type

        param: string err_type - one of the supported error types (i.e.: "badDLLP", "badTLP")
        return: True
        raise: TestFail
        """
        self._log.debug("Checking the PCIE Link speed")
        initial_gen = self.get_link_speed_detail()
        super(PcieHWLeakyBucketExpectedBerChangeTest, self).execute(err_type, expect_link_degrade)
        self._log.info("verify PCIE Link speed after PEI error injection")
        self.check_link_degrade(initial_gen)

        self._log.info("Configure ExpectedBer in Bios knob to 2952790015")
        self.change_ber_in_bios_knob(bios_field="ExpectedBer", value="0x00000000AFFFFFFF")

        # Change the exp_ber in LEKBERR register according to the BIOS Knob ExpectedBer value
        self.LEAKY_BUCKET_CONFIG_REGISTER_CHECKLIST = [self.CONFIG_REG_LEKBERR, {"lekberr1": {"g3aggrerr": 0x2, "exp_ber": 0x0}},
                                              {"lekberr0": {"exp_ber": 0xafffffff}}, self.CONFIG_REG_LEKBPROERR]
        super(PcieHWLeakyBucketExpectedBerChangeTest, self).execute(err_type, expect_link_degrade)
        self._log.info("verify PCIE Link speed after PEI error injection")
        self.check_link_degrade(initial_gen)

        self._log.info("Configure ExpectedBer in Bios knob to 0")
        self.change_ber_in_bios_knob(bios_field="ExpectedBer", value="0x0000000000000000")

        # Change the exp_ber in LEKBERR register according to the BIOS Knob ExpectedBer value
        self.LEAKY_BUCKET_CONFIG_REGISTER_CHECKLIST = [self.CONFIG_REG_LEKBERR,
                                                      {"lekberr1": {"g3aggrerr": 0x2, "exp_ber": 0x0}},
                                                      {"lekberr0": {"exp_ber": 0x0}}, self.CONFIG_REG_LEKBPROERR]
        super(PcieHWLeakyBucketExpectedBerChangeTest, self).execute(err_type, expect_link_degrade=False)
        self._log.info("verify PCIE Link speed after PEI error injection.")
        self.check_link_degrade(initial_gen, expect_link_degrade=False)
        return True

    def inject_pei_errors(self, error_type):
        """
        This method overrides the base class method as
        This method is used to inject errors of a given supported type
            a. less than threshold
            b. check the leaky bucket error rate
            c. inject error beyond threshold

        param: string error_type - one of the supported error types (i.e.: "badDLLP", "badTLP")
        return: nothing
        """
        self._log.debug("Running lspci in a loop to generate some PCIe traffic while injecting bad packets")
        self._os.execute_async("while true; do lspci; sleep 1; done")


        self._log.info("Injecting error below leaky bucket error threshold")
        actual_leaky_bucket_error_threshold = self._bios_util.get_bios_knob_current_value(self.THRESHOLD_KNOB_NAME[self.cscripts_obj.silicon_cpu_family])
        self.LEAKY_BUCKET_ERROR_THRESHOLD = str(hex(int(actual_leaky_bucket_error_threshold, 16) - 1))
        super(PcieHWLeakyBucketExpectedBerChangeTest, self).inject_pei_errors(error_type)

        self._log.debug("Checking the leaky bucket error counter after the PEI error injection")
        self.verify_leaky_bucket_error_leak_rate()

        self._log.info("Injecting error equal to leaky bucket error threshold")
        self.LEAKY_BUCKET_ERROR_THRESHOLD = actual_leaky_bucket_error_threshold
        super(PcieHWLeakyBucketExpectedBerChangeTest, self).inject_pei_errors(error_type)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieHWLeakyBucketExpectedBerChangeTest.main() else Framework.TEST_RESULT_FAIL)
