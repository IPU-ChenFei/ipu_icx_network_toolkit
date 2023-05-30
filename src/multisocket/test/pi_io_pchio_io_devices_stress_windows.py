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
import re
from xml.etree import ElementTree

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib import content_exceptions
from src.lib.dtaf_content_constants import ProviderXmlConfigs
from src.lib.platform_config import PlatformConfiguration

from src.lib.test_content_logger import TestContentLogger
from src.multisocket.lib.multisocket_common import MultiSocketCommon
from src.provider.stressapp_provider import StressAppTestProvider
from src.provider.vss_provider import VssProvider
from src.lib.install_collateral import InstallCollateral
from src.storage.test.storage_common import StorageCommon


class IOPCHIOIODevicesStressW(ContentBaseTestCase):
    """
    Phoenix 16014692546, PI_IO_PCHIO_IO_devices_stress_W

    PCH IO Devices stress test on Windows
    """

    TEST_CASE_ID = ["16014692546", "PI_IO_PCHIO_IO_devices_stress_W"]
    PROCESS_NAME = "mem64.exe"
    LOG_NAME = "iwvss_log.log"
    step_data_dict = {1: {'step_details': 'To clear OS logs and load default bios settings ...',
                          'expected_results': 'Cleared OS logs and default bios settings done ...'},
                      2: {'step_details': 'Select package in iwVSS and run workload ',
                          'expected_results': 'No errors should be reported ...'},
                      3: {'step_details': 'Check MCE Error logs for Errors ',
                          'expected_results': 'No errors should be reported ...'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance IOPCHIOIODevicesStressW

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        :return: None
        :raises: None
        """

        # calling base class init
        super(IOPCHIOIODevicesStressW, self).__init__(test_log, arguments, cfg_opts)

        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)

        self._vss_provider_obj = VssProvider.factory(self._log, cfg_opts=cfg_opts, os_obj=self.os)
        self._stress_provider = StressAppTestProvider.factory(test_log, cfg_opts, self.os)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
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
        mode = self._multisock_obj.get_mode_info(self.serial_log_dir, self._SERIAL_LOG_FILE)
        self._log.info("System is in {}".format(mode))
        super(IOPCHIOIODevicesStressW, self).prepare()
        self._multisock_obj.check_topology_speed_lanes(self.SDP)
        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        1. Format the U.2 device and Mount the U.2 devices
        2. Select package in iwVSS and run workload.

        :return: True, if the test case is successful.
        """

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)

        self._install_collateral.install_vc_redist()

        self._log.info("Executing the iwvss ...")
        # To copy the package and Execute iwvss configuration for stress
        self._vss_provider_obj.execute_vss_memory_test_package(flow_tree="Mem")

        # wait for the iwvss to complete
        self._vss_provider_obj.wait_for_vss_to_complete(self.PROCESS_NAME)

        # Parsing iwvss log
        return_value = self._vss_provider_obj.verify_vss_logs(self.LOG_NAME)

        # Step logger end for Step 2
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)
        self._multisock_obj.check_topology_speed_lanes(self.SDP)
        # Run sv.sockets.uncore.ubox.ncevents.mcerrloggingreg.show() and check logs
        self.SDP.start_log("mlc_topology.log")
        pysv_output = self.SV.get_by_path(
            self.SV.UNCORE, PlatformConfiguration.MCE_EVENTS_CHECK_CONFIG[self._silicon_family])
        if str(pysv_output) != "0x0":
            self._log.error("Mce logging check output : {}".format(pysv_output))
            raise content_exceptions.TestFail("Mce error check returned non zero value")
        self.SDP.stop_log()
        self._multisock_obj.print_topology_logs("mlc_topology.log")
        # Step logger end for Step 3
        self._test_content_logger.end_step_logger(3, return_val=True)
        self._log.info("system is working fine without any errors and No hard hang occured during execution")
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if IOPCHIOIODevicesStressW.main() else Framework.TEST_RESULT_FAIL)

