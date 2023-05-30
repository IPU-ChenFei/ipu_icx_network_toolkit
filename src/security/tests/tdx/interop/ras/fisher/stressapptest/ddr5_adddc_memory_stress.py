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
    :TDX RAS Interop DDR5 ADDDC Memory Stress:

    Launch Fisher RAS test suite for an extended period of time.  Calculate the failure rate if applicable and determine
    if it is acceptable.
"""
import six
import sys

from abc import ABCMeta

from dtaf_core.lib.dtaf_constants import Framework

from src.security.tests.tdx.interop.ras.fisher.fisher_base_test import TdxRasFisherBaseTest


@six.add_metaclass(ABCMeta)
class TdxDdrADDDCMemoryStress(TdxRasFisherBaseTest):
    """
           This is a base test for workload testing with TD guests as part of the TDX feature.

           The following parameters in the content_configuration.xml file should be populated before running a test.

            Change <TDX><num_of_vms> to control the number of TD guests that will be run in parallel.

            :Scenario: Launch the number of TD guests prescribed, initiate fisher application on the SUT, run for the
            necessary time to complete the tests, then verify the SUT and the TD guests have not crashed.

            :Phoenix IDs:  22012573275

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
        super(TdxDdrADDDCMemoryStress, self).__init__(test_log, arguments, cfg_opts)
        self.workload_name = "stressapptest"
        self.run_time = 10  # 10 hours run time
        self.pass_ratio = 0.8
        self.bios_knobs = ["fisher_adddc_knobs.cfg"]

    def execute(self):
        self.fisher_command = f"fisher --workload=\"stressapptest -W -M {int(self.free_mem)} -C --cc_test -s 14400 " \
                              f"--max_errors 1 --pause_delay 100000000 --stop_on_errors\" " \
                              f"--injection-type=memory-correctable --match=DRd --runtime={int(self.run_time)}h " \
                              f"--injection-delay-min=60s --injection-delay-max=120s --injection-max-per-address=1"
        return super(TdxDdrADDDCMemoryStress, self).execute()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TdxDdrADDDCMemoryStress.main() else Framework.TEST_RESULT_FAIL)
