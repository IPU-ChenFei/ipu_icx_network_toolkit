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
from src.lib.platform_config import PlatformConfiguration
from src.lib.test_content_logger import TestContentLogger
from src.multisocket.lib.multisocket_common import MultiSocketCommon
from src.hsio.upi.hsio_upi_common import HsioUpiCommon



class ProcessorUpilinkDetails4sL(HsioUpiCommon):
    """
    Phoenix 16013410489, PI_Processor_UPI_Link_details_4S

    Processor upi link test on Linux
    """

    TEST_CASE_ID = ["16013410489", "PI_Processor_UPI_Link_details_4S"]
    step_data_dict = {1: {'step_details': 'To clear OS logs and load default bios settings ...',
                          'expected_results': 'Cleared OS logs and default bios settings done ...'},
                      2: {'step_details': 'power on board and boot to OS ',
                          'expected_results': 'unlock is working fine ...'},
                      3: {'step_details': 'To get the link Speed ',
                          'expected_results': 'link speed set to SPR and EMR ...'},
                      4: {'step_details': 'Get the link status ',
                          'expected_results': 'link status hould be L0 ...'},
                      5: {'step_details': 'To get the link lane ',
                          'expected_results': 'Link lane verified ...'},
                      6: {'step_details': 'Check MCE Error logs for Errors ',
                          'expected_results': 'No errors should be reported ...'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance ProcessorUpilinkDetails4sL

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        :return: None
        :raises: None
        """

        # calling base class init
        super(ProcessorUpilinkDetails4sL, self).__init__(test_log, arguments, cfg_opts)

        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

        self._multisock_obj = MultiSocketCommon(test_log, arguments, cfg_opts)
        self._silicon_family = self._common_content_lib.get_platform_family()
        self.initialize_sv_objects()
        self.initialize_sdp_objects()

    def prepare(self):
        # type: () -> None
        """
        To clear OS logs and load default bios settings.

        :return: None
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        super(ProcessorUpilinkDetails4sL, self).prepare()
        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)


    def execute(self):
        """
        1. To check itp unlock status
        2. Verify the topology and link speed
        3. To check mce errors

        :return: True, if the test case is successful.
        """
        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        self.SDP.start_log("print_topology.log")
        # PythonSv command to check unlock is working fine.
        self.SDP.itp.unlock()
        self.SDP.itp.forcereconfig()
        self.SV._sv.refresh()
        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)
        # Output details of linkspeed
        self.print_upi_link_speed()
        # verify the linkspeed
        self.verify_max_link_speed_set()
        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)

        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)
        self.print_upi_topology()
        self.print_link()
        # verify the topology
        self.verify_upi_topology()
        self.lanes_operational_check()
        if not self.verify_no_upi_errors_indicated():
            raise content_exceptions.TestFail("UPI errors detected")
        # Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=True)

        # Step logger start for Step 5
        self._test_content_logger.start_step_logger(5)
        # To get the link lane
        pysv_output = self.SV.get_by_path(
            self.SV.UNCORE, PlatformConfiguration.UPI_KTIREUT_PH_CSS[self._silicon_family])
        self._log.debug("link lane : {}".format(pysv_output))
        # Step logger end for Step 4
        self._test_content_logger.end_step_logger(4, return_val=True)

        # Step logger start for Step 6
        self._test_content_logger.start_step_logger(6)
        # Check MCE errors
        pysv_output = self.SV.get_by_path(
            self.SV.UNCORE, PlatformConfiguration.MCE_EVENTS_CHECK_CONFIG[self._silicon_family])
        if str(pysv_output) != "0x0":
            self._log.error("Mce logging check output : {}".format(pysv_output))
            raise content_exceptions.TestFail("Mce error check returned non zero value")

        self.SDP.stop_log()
        self._multisock_obj.print_topology_logs("print_topology.log")
        # Step logger end for Step 6
        self._test_content_logger.end_step_logger(6, return_val=True)

        self._log.info("system is working fine without any errors and No hard hang occur during execution")
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ProcessorUpilinkDetails4sL.main() else Framework.TEST_RESULT_FAIL)
