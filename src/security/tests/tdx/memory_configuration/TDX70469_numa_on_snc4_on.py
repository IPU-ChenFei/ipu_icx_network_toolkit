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
    :TDX NUMA ON / SNC4 ON Memory Configuration:

    Verify the TDX memory range compatibility with NUMA ON and SNC4 ON.
"""
import sys
import os

from dtaf_core.lib.dtaf_constants import Framework
from src.security.tests.tdx.tdvm.TDX008a_launch_tdvm_linux import TDVMLaunchLinux
from src.lib import content_exceptions


class TdxNumaOnSncFour(TDVMLaunchLinux):
    """
            This recipe tests memory configuration compatibility and is applicable to TDX compatible OSs.

            :Scenario: Verify the TDX memory range compatibility with NUMA ON and SNC4 ON. Verifying system set-up of
            PRMRR regions with TDX enabled in memory configuration mode NUMA ON and SNC4 ON.  All slot 0 DIMMS must be
            populated for this test.

            :Prerequisite:  SUT must be configured with the latest BKC applicable for the platform and an ITP probe
            must be attached to the SUT.

            :Phoenix ID: 18014074024

            :Test steps:

                :1: Verify TDX is enabled.

                :2: Boot to BIOS menu.

                :3: Verify the status of the following BIOS knobs:  Numa is enabled, UMA-based clustering is disabled.

                :4: Set Sub NUMA BIOS knob to SNC4 (4-clusters).

                :5: Reboot SUT to apply BIOS knobs and boot to OS.

                :6: Boot a TD guest.

            :Expected results: SUT should boot to OS with TDX enabled and there should be 8 unique non-zero PRMRR bases.
            TD guest should be able to boot.

            :Reported and fixed bugs:

            :Test functions:

        """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of test case.
        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        :return: None
        """
        super(TdxNumaOnSncFour, self).__init__(test_log, arguments, cfg_opts)
        self._NUMA_SNC_KNOB = "../collateral/numa_snc4_en_reference_knob.cfg"
        self._NUMBER_SNC_CLUSTERS = 0

    def prepare(self):
        if not self.one_dpc_config_check() and not self.two_dpc_config_check():
            raise content_exceptions.TestSetupError("Dimm configuration on SUT does not support SNC4.")
        super(TdxNumaOnSncFour, self).prepare()
        self._NUMBER_SNC_CLUSTERS = 8

    def execute(self):
        validate_dict = []
        bios_knob_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self._NUMA_SNC_KNOB)
        self._log.info("Checking BIOS knobs that Numa is enabled and Sub NUMA is set to enable SNC4 (4-clusters).")
        self._log.info("If knobs need to be modified, the knobs will be set and the SUT will undergo a warm reset.")
        self.check_knobs(bios_knob_file, set_on_fail=True)

        if self._NUMBER_SNC_CLUSTERS == 0:
            self._log.debug("SNC should not enable with TDX/SGX with the number of sockets on the system.")

        self._log.info("Checking number of nonzero PRMRR base registers.")
        registers = self.read_prmrr_base_msrs()
        if len(registers) != self._NUMBER_SNC_CLUSTERS:
            self._log.error("Expected {} nonzero PRMRR base register values but got {}.".format(
                self._NUMBER_SNC_CLUSTERS, len(registers)))
            return False
        else:
            self._log.info("Expected {} nonzero PRMRR base register values and got {}.".format(
                self._NUMBER_SNC_CLUSTERS, len(registers)))

        self._log.info("Checking the nonzero PRMRR base register values are unique.")
        for register in registers:
            if registers[register] in validate_dict:
                self._log.error("Register value {} has shown up more than once in MSR values read.")
                self._log.debug("Contents of registers structure {}".format(registers))
                return False
            else:
                validate_dict.append([registers[register]])  # add to list of registers known for comparison
        self._log.info("All nonzero PRMRR base register values are unique.  Values: {}".format(registers))

        self._log.info("Verifying TDX is still enabled and in valid configuration.")
        if not self.validate_tdx_setup():
            raise RuntimeError("TDX is no longer enabled with SNC disabled.")

        return super(TdxNumaOnSncFour, self).execute()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TdxNumaOnSncFour.main() else Framework.TEST_RESULT_FAIL)
