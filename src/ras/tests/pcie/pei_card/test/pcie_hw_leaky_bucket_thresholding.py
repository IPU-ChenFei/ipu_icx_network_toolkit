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
from time import sleep


class PcieHWLeakyBucketThresholding(PcieHWLeakyBucketBaseTest):
    """
    Phoenix_id : 22012665731

    The objective of this test is to enable verification of Leaky Bucket error threshold change

     Requirements:

     1. BIOS config file path configured in system_configuration.xml
     2. Socket of PEI 4.0 card configured in content_configuration.xml
     3. pxp port of PEI 4.0 card configured in content_configuration.xml
     4. PEI 4.0 HW injector card with interposer image loaed
     5. NVMe drive connected to PEI 4.0 card

     Usage:

     Error type injection is controlled by the "test" parameter in the execute() method and is set to "badDLLP" by default
     To execute the test for bad TLP, set test="badTLP"

    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new PcieHWLeakyBucketThresholding object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PcieHWLeakyBucketThresholding, self).__init__(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        :return: None
        """
        super(PcieHWLeakyBucketThresholding, self).prepare()

    def execute(self, err_type="badDLLP", expect_link_degrade=True):
        """
        This method checks the OS log for errors given a supported error type

        param: string err_type - one of the supported error types (i.e.: "badDLLP", "badTLP")
        return: True
        raise: TestFail
        """

        self._log.info("Checking config register values before PEI error injection below threshold")
        self.check_config_registers()
        self._log.info("Injecting errors below threshold")
        self.LEAKY_BUCKET_ERROR_THRESHOLD = '0xE'
        self.inject_pei_errors(err_type)
        self._log.info("Checking config register values after PEI error injection below threshold")
        self.check_config_registers()
        self.verify_leaky_bucket_flow(err_type, triggered=False)
        self._log.info("Waiting for error lane count to decrement to zero")
        sleep(self.LEAKY_BUCKET_DEFAULT_BER_LEAK_RATE_IN_SECONDS * int(self.LEAKY_BUCKET_ERROR_THRESHOLD, 16))
        if self.get_leaky_bucket_error_count(self.PCIE_SOCKET, self.PCIE_PXP_PORT) != 0:
            raise content_exceptions.TestFail("Lane error decrement to zero timeout")
        self._log.info("Injecting errors at threshold")
        self.LEAKY_BUCKET_ERROR_THRESHOLD = self._bios_util.get_bios_knob_current_value(
            self.THRESHOLD_KNOB_NAME[self.cscripts_obj.silicon_cpu_family])
        self.inject_pei_errors(err_type)
        self.verify_leaky_bucket_flow(err_type)
        self._log.info("Set leaky bucket threshold knob to max value")
        self._bios_util.set_single_bios_knob(self.THRESHOLD_KNOB_NAME[self.cscripts_obj.silicon_cpu_family],
                                             self.THRESHOLD_KNOB_MAX_VALUE)
        self._log.info("Reboot OS for BIOS changes to take effect")
        self._common_content_lib.perform_os_reboot(self._reboot_timeout_in_sec)

        # set leaky bucket threshold new value to max knob threshold value
        self.LEAKY_BUCKET_ERROR_THRESHOLD = self._bios_util.get_bios_knob_current_value(
            self.THRESHOLD_KNOB_NAME[self.cscripts_obj.silicon_cpu_family])

        if self.LEAKY_BUCKET_ERROR_THRESHOLD != self.THRESHOLD_KNOB_MAX_VALUE:
            raise RuntimeError("BIOS knob for leaky bucket threshold was not successfully changed to max value %s" %
                               self.THRESHOLD_KNOB_MAX_VALUE)

        self._log.info("Injecting errors at max threshold")
        self.inject_pei_errors(err_type)
        self.verify_leaky_bucket_flow(err_type)

        self._log.info("Reboot OS")
        self._common_content_lib.perform_os_reboot(self._reboot_timeout_in_sec)
        # set leaky bucket threshold new value to above max knob threshold value
        self.LEAKY_BUCKET_ERROR_THRESHOLD = '0x1F'
        self._log.info("Injecting errors above max threshold")
        self.inject_pei_errors(err_type)
        self.verify_leaky_bucket_flow(err_type)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieHWLeakyBucketThresholding.main() else Framework.TEST_RESULT_FAIL)
