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

import sys
import time

from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.lib.dtaf_constants import Framework
from src.ras.tests.io_power_management.io_power_management_common import IoPmCommon


class SolarPcieCorrectableErrorsTurbo(IoPmCommon):
    """
    Glasgow_id : 70255 PM RAS - Windows 2019 Server + Turbo + Solar Workload + C-Scripts PCIe Correctable Error Injection

    This test case walks you through how to do PCIE error injection to the platform.
    The platform will be running CPU stress in turbo frequency during the injection.
    """
    _BIOS_CONFIG_FILE = "solar_pstate_pcie_err_bios_knob.cfg"
    TURBO_START_DELAY_SEC = 10
    EVENT_LOGGING_DELAY_SEC = 3
    NUM_CYCLE = 235

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new SolarPcieCorrectableErrorsTurbo object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """

        super(SolarPcieCorrectableErrorsTurbo, self).__init__(
            test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

        self.SOCKET = self._common_content_configuration.get_cscripts_ei_pcie_device_socket()
        self.PXP_PORT = self._common_content_configuration.get_cscripts_ei_pcie_device_pxp_port()

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs that are set.

        :return: None
        """
        super(SolarPcieCorrectableErrorsTurbo, self).prepare()

    def execute(self):

        self.solar_install()

        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        sdp_obj = ProviderFactory.create(self.si_dbg_cfg, self._log)

        self.solar_execute(self.SOLAR_TEST_PSTATE, self.SOLAR_WL_SSE2)
        time.sleep(self.TURBO_START_DELAY_SEC)
        if not self.check_processor_turbo_mode_win():
            self._log.error("System not in Turbo Mode!")
            self.solar_kill_process()
            return False

        for i in range(0, self.NUM_CYCLE):

            self._log.info("Starting cycle {}...".format(i))
            self._log.info("Clearing OS logs .......")
            self._common_content_lib.clear_all_os_error_logs()

            self.inject_pcie_error(cscripts_obj, sdp_obj, self.SOCKET, self.PXP_PORT, err_type="ce")

            time.sleep(self.EVENT_LOGGING_DELAY_SEC)

            event_check = self._os_log_obj.verify_os_log_error_messages(__file__,
                                                                        self._os_log_obj.DUT_WINDOWS_WHEA_LOG,
                                                                        self.WINDOWS_PCIE_CORRECTABLE_ERR_SIGNATURE)
            if not event_check:
                self._log.info("Error Log not found on first try...")
                time.sleep(self.EVENT_LOGGING_DELAY_SEC)
                event_check = self._os_log_obj.verify_os_log_error_messages(__file__,
                                                                            self._os_log_obj.DUT_WINDOWS_WHEA_LOG,
                                                                            self.WINDOWS_PCIE_CORRECTABLE_ERR_SIGNATURE)
                if not event_check:
                    self._log.info("Test failed at cycle {}".format(i))
                    self.solar_kill_process()
                    return False

        self.solar_kill_process()
        return True


if __name__ == "__main__":

    sys.exit(Framework.TEST_RESULT_PASS if SolarPcieCorrectableErrorsTurbo.main()
             else Framework.TEST_RESULT_FAIL)
