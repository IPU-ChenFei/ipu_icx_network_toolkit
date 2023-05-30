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
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.provider_factory import ProviderFactory

import src.lib.content_exceptions as content_exception
from src.ras.tests.io_power_management.io_power_management_common import IoPmCommon
import time


class PcieLinkDegradeG3Cycle(IoPmCommon):
    """
    Glasgow_id : 70825 PM RAS - Linux - PCIe link degrade - G3 AC cycle cycle

    AC cycle platform
    Stop Linux OS from booting at a designated post code
    Cause link degrade
    Continue boot and verify OS boots
    Recycle the process



    Need to set c:\Automation\content_configuration.xml to appropiate unbifurcated pcie port with at least x4 width
    content->ras->cscripts_ei_pcie_device
    """
    NUM_CYCLES = 10
    MIN_PCIE_WIDTH = 4
    BUS_RESET_DELAY_SEC = 4
    CLEAR_LOG_DELAY_SEC = 10
    _BIOS_CONFIG_FILE = "pcie_link_degrade_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new PcieLinkDegradeWarmReboot object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        super(PcieLinkDegradeG3Cycle, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)
        # Get Socket and PCIe complex.port number from content_configuration.xml
        self.PCIE_SOCKET = self._common_content_configuration.get_cscripts_ei_pcie_device_socket()
        self.PCIE_PXP_PORT = self._common_content_configuration.get_cscripts_ei_pcie_device_pxp_port()
        self.OS_PCIE_BDF = self._common_content_configuration.get_linux_os_pcie_bdf()

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
        super(PcieLinkDegradeG3Cycle, self).prepare()

    def execute(self):
        """
        Pcie link degradation in early boot during warm boot cycling.

        :return: True or False based on Test Case fail or pass.
        """
        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        sdp_obj = ProviderFactory.create(self.si_dbg_cfg, self._log)

        for i in range(self.NUM_CYCLES):
            try:
                self._log.info("Executing loop: " + str(i))
                self._log.info("Clearing OS logs .......")
                self._common_content_lib.clear_all_os_error_logs()
                time.sleep(self.CLEAR_LOG_DELAY_SEC)

                # Checking OS data on pcie card
                os_pcie_width = self.get_os_pcie_width()

                # initiate Ac cycle
                self._log.info("Ac cycle platform ..")
                self.g3_cycle_non_blocking()

                # set BIOS break point
                self.set_bios_break(cscripts_obj, self.UPI_POST_CODE_BREAK_POINT)
                # wait for target to enter break point
                self.check_bios_progress_code(cscripts_obj, self.UPI_POST_CODE_BREAK_POINT)
                self._log.info("Stop boot at found BIOS break point")

                # Halt system
                sdp_obj.halt_and_check()

                # Degrade pcie link
                pcie_obj = cscripts_obj.get_cscripts_utils().get_pcie_obj()

                pcie_width = int(str(pcie_obj.get_negotiated_link_width(self.PCIE_SOCKET, self.PCIE_PXP_PORT)).split
                                 ('x')[1], base=16)
                # verify OS matches cscripts
                if os_pcie_width != pcie_width:
                    log_err = "OS pcie width does not match cscripts-" + str(os_pcie_width) + " vs " + str(pcie_width)
                    self._log.error(log_err)
                    raise content_exception.TestFail(log_err)
                self._log.info("OS pcie width matches cscripts width")

                if pcie_width < self.MIN_PCIE_WIDTH:
                    log_err = "Test requires x4 or greater PCIE card)"
                    self._log.error(log_err)
                    raise content_exception.TestFail(log_err)

                pcie_half_width = "x" + str(int(pcie_width / 2))

                # Halt system
                sdp_obj.halt_and_check()

                # set degraded width
                pcie_obj.setSlotWidth(self.PCIE_SOCKET, self.PCIE_PXP_PORT, pcie_half_width)

                sdp_obj.go()
                time.sleep(self.BUS_RESET_DELAY_SEC)

                # Check if link downgraded
                pcie_test_width_degraded = int(str(pcie_obj.get_negotiated_link_width(self.PCIE_SOCKET,
                                               self.PCIE_PXP_PORT)).split('x')[1], base=16)

                if pcie_test_width_degraded == int(pcie_half_width.split('x')[1]):
                    self._log.info("pcie card was successfully degraded from " + "x" + str(pcie_width) +
                                   " to " + pcie_half_width)
                else:
                    log_err = "Failed to degrade pcie card - exiting"
                    self._log.error(log_err)
                    raise content_exception.TestFail(log_err)

                # reset break point
                self.clear_bios_break(cscripts_obj)
                self._log.info("Removing Bios break point - continue boot process")

                # wait for os and check os logs
                self._log.info("Waiting for Os to boot")
                self.os.wait_for_os(self.RESUME_FROM_BREAK_POINT_WAIT_TIME_SEC)

                # verify OS matches cscripts after degrade
                # Checking OS data on pcie card
                os_pcie_degraded_width = self.get_os_pcie_width()

                if os_pcie_degraded_width != pcie_test_width_degraded:
                    log_err = "OS pcie width does not match cscripts after degrade-" + str(os_pcie_width) + \
                              " vs " + str(pcie_width)
                    self._log.error(log_err)
                    RuntimeError(log_err)
                self._log.info("OS pcie width matches cscripts width after degrade")

                # bring card back to normal width
                self._log.info("Setting pcie slot back to normal ...")
                # Halt system
                sdp_obj.halt_and_check()

                pcie_obj.setSlotWidth(self.PCIE_SOCKET, self.PCIE_PXP_PORT, "x" + str(pcie_width))

                # Issue a bus reset
                pcie_obj.sbr(self.PCIE_SOCKET, self.PCIE_PXP_PORT)

                sdp_obj.go()
                time.sleep(self.BUS_RESET_DELAY_SEC)
                if not self._os_log_obj.verify_os_log_error_messages(__file__,
                                                                     self._os_log_obj.DUT_JOURNALCTL_CURRENT_BOOT,
                                                                     self.GENERIC_HW_ERROR_JOURNALCTL,
                                                                     check_error_not_found_flag=True):
                    log_err = "Error found in OS logs! No error expected in OS logs when injecting CE prior to OS Boot."
                    self._log.error(log_err)
                    raise content_exception.TestFail(log_err)
                else:
                    self._log.info("OS logs detected no errors as expected")

            except Exception as ex:
                self._log.error("Failed on loop: " + str(i))
                log_err = "An Exception Occurred : {}".format(ex)
                self._log.error(log_err)
                raise content_exception.TestFail(log_err)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieLinkDegradeG3Cycle.main() else Framework.TEST_RESULT_FAIL)
