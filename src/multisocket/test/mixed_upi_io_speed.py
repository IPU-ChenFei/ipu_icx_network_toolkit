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
import time
import ipccli
from src.lib.test_content_logger import TestContentLogger
from src.hsio.upi.hsio_upi_common import HsioUpiCommon
from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.bios_menu import BiosBootMenuProvider
from dtaf_core.providers.uefi_shell import UefiShellProvider
from src.lib.bios_util import ItpXmlCli
from src.lib.bios_util import BootOptions
from src.lib.uefi_util import UefiUtil
from src.ras.tests.io_power_management.io_power_management_common import IoPmCommon


class MixedUpiIoSpeed(HsioUpiCommon):
    """
    Phoenix 18014075269, Mixed_UPI_IO_speed

    This test cases to check the basic UPI topology for a given configuration in BIOS.
    """

    TEST_CASE_ID = ["18014075269", "Mixed_UPI_IO_speed"]
    step_data_dict = {1: {'step_details': 'unlock ITP',
                          'expected_results': 'successfully unlocked ITP ...'},
                      2: {'step_details': 'boot to UEFI shell ...',
                          'expected_results': 'successfully booted to UEFI shell...'},
                      3: {'step_details': 'set the random upi link speed',
                          'expected_results': 'successfully set random UPI speeds ...'},
                      4: {'step_details': 'check for postcode ',
                          'expected_results': 'verified BIOS post code ...'},
                      5: {'step_details': 'print and verify link speed',
                          'expected_results': 'successfully verified mixed link speed'}
                     }

    WAIT_TIME_OUT = 5


    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance MixedUpiIoSpeed

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        :return: None
        :raises: None
        """

        # calling base class init
        super(MixedUpiIoSpeed, self).__init__(test_log, arguments, cfg_opts)
        # Object of TestContentLogger class
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.step_data_dict)
        self.initialize_sv_objects()
        self.initialize_sdp_objects()
        self._io_pm_obj = IoPmCommon(test_log, arguments, cfg_opts, config=None)
        self.itp_xml_cli_util = ItpXmlCli(self._log, cfg_opts)
        uefi_cfg = cfg_opts.find(UefiShellProvider.DEFAULT_CONFIG_PATH)
        self._uefi_obj = ProviderFactory.create(uefi_cfg, test_log)  # type: UefiShellProvider
        bios_boot_menu_cfg = cfg_opts.find(BiosBootMenuProvider.DEFAULT_CONFIG_PATH)
        self._bios_boot_menu_obj = ProviderFactory.create(bios_boot_menu_cfg, test_log)  # type: BiosBootMenuProvider
        self._uefi_util_obj = UefiUtil(
            self._log,
            self._uefi_obj,
            self._bios_boot_menu_obj,
            self.ac_power,
            self._common_content_configuration, self.os)
        self._bios_boot_menu_entry_wait_time = self._common_content_configuration.bios_boot_menu_entry_wait_time()
        self.previous_boot_order = None
        self.current_boot_order = None

    def prepare(self):
        # type: () -> None
        """
        To boot it to UEFI shell


        :return: None
        """
        # Step logger start for Step 1
        self._test_content_logger.start_step_logger(1)
        itp = ipccli.baseaccess()
        itp.forcereconfig()
        itp.unlock()
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        1. To check itp unlock status
        2. set random link speed
        3. verify link speed

        :return: True, if the test case is successful.
        """

        # Step logger start for Step 2
        self._test_content_logger.start_step_logger(2)
        self.previous_boot_order = self.itp_xml_cli_util.get_current_boot_order_string()
        self._log.info("Current boot order {}".format(self.previous_boot_order))
        self._log.info("Setting the default boot order to {}".format(BootOptions.UEFI))
        self.itp_xml_cli_util.set_default_boot(BootOptions.UEFI)
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self._log.info("waiting for UEFI shell")
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        time.sleep(self.WAIT_TIME_OUT)

        # Step logger end for Step 1
        self._test_content_logger.end_step_logger(2, return_val=True)

        # Step logger start for Step 3
        self._test_content_logger.start_step_logger(3)
        self.set_upi_link_random_speed()
        self._uefi_obj.wait_for_uefi(self._bios_boot_menu_entry_wait_time)
        self._test_content_logger.end_step_logger(3, return_val=True)
        # Step logger start for Step 4
        self._test_content_logger.start_step_logger(4)
        self.itp_xml_cli_util.set_boot_order(self.previous_boot_order)
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self._log.info("waiting for os to be alive")
        self.os.wait_for_os(self.reboot_timeout)
        self.SDP.itp.resettarget()
        self._io_pm_obj.set_bios_break(self.reg_provider_obj, self._io_pm_obj.UPI_POST_CODE_BREAK_POINT)
        # wait for target to enter break point.
        self._io_pm_obj.check_bios_progress_code(self.reg_provider_obj, self._io_pm_obj.UPI_POST_CODE_BREAK_POINT)
        self._io_pm_obj.clear_bios_break(self.reg_provider_obj)
        self.os.wait_for_os(self._io_pm_obj.RESUME_FROM_BREAK_POINT_WAIT_TIME_SEC)

        self._test_content_logger.end_step_logger(4, return_val=True)
        # Step logger start for Step 5
        self._test_content_logger.start_step_logger(5)
        self.print_upi_topology()
        self.print_upi_link_speed()
        self.verify_link_speed_mixed()
        self._test_content_logger.end_step_logger(5, return_val=True)
        self.current_boot_order = self.itp_xml_cli_util.get_current_boot_order_string()
        return True

    def cleanup(self, return_status):
        # type: (bool) -> None
        if str(self.current_boot_order) != str(self.previous_boot_order):
            self.itp_xml_cli_util.set_boot_order(self.previous_boot_order)
            self.perform_graceful_g3()
        super(MixedUpiIoSpeed, self).cleanup(return_status)

if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MixedUpiIoSpeed.main() else Framework.TEST_RESULT_FAIL)
