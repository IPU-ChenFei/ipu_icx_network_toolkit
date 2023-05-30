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
    :TDX RAS Interop Mix stress-ng:

    Launch Fisher RAS test suite for an extended period of time.  Calculate the failure rate if applicable and determine
    if it is acceptable.
"""
import sys

from dtaf_core.lib.dtaf_constants import Framework

from src.security.tests.tdx.interop.ras.fisher.fisher_base_test import TdxRasFisherBaseTest


class TdxMixStressng(TdxRasFisherBaseTest):
    """
           This is a base test for workload testing with TD guests as part of the TDX feature.

           The following parameters in the content_configuration.xml file should be populated before running a test.

            Change <TDX><num_of_vms> to control the number of TD guests that will be run in parallel.

            :Scenario: Launch the number of TD guests prescribed, initiate fisher application on the SUT, run for the
            necessary time to complete the tests, then verify the SUT and the TD guests have not crashed.

            :Phoenix IDs:  22012573451

            :Test steps:

                :1: Launch a TD guest.

                :2: Repeat step 1 for the prescribed number of TD guests.

                :3: On the TD host, launch the Fisher RAS test.

                :4: Run until Fisher RAS test completes.

                :5: If applicable, calculate the error ratio.

            :Expected results: Each TD guest should boot and the workload suite should run to completion with no
            errors on the SUT or any of the TD guests.

            :Reported and fixed bugs:

            :Test functions:

        """

    def __init__(self, test_log, arguments, cfg_opts):
        """Create an instance of TdxBaseTest

        :param cfg_opts: Configuration Object of provider
        :type cfg_opts: str
        :param test_log: Log object
        :type arguments: Namespace
        :param arguments: None
        :type cfg_opts: Namespace
        :return: None
        """
        super(TdxMixStressng, self).__init__(test_log, arguments, cfg_opts)
        self.workload_name = "stress-ng"
        self.run_time = 10  # 10 hours time out
        self.fisher_command = "fisher --workload=\"stress-ng --class cpu,cpu-cache,memory -x " \
                              "opcode,sigsegv,lockbus,atomic,misaligned,rmap --sequential \\$(shuf -i1-$(nproc) -n1) " \
                              "--verify --timeout 4\" --injection-type=memory-uncorrectable-non-fatal " \
                              f"--match='DRd_^(?!mov)' --workload-exit-code=0,2 --runtime={self.run_time}h"

        self.pass_ratio = 0.8
        self.bios_knobs = ["fisher_poison_knobs.cfg"]


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TdxMixStressng.main() else Framework.TEST_RESULT_FAIL)
