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


class PcieUceNonfatalWarmBootEdpcDisabled(IoPmCommon):
    """
    Glasgow_id : 70819 PM RAS - Linux - PCIe Uncorrectable Nonfatal Warm Reboot Cycling - eDPC Disabled
    Requirement: cscripts_ei_pcie_device socket and pxp_port must be set in content_configuration.xml
    BERT reports error in OS logs on subsequent boot after injecting UCE Nonfatal during boot with EDPC disabled
    """
    NUM_CYCLES = 10
    _BIOS_CONFIG_FILE = "pcie_ei_edpc_disabled_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new PcieUceNonfatalWarmBootEdpcEnabled object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        super(PcieUceNonfatalWarmBootEdpcDisabled, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)
        # Get Socket and PCIe complex.port number from content_configuration.xml
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
        super(PcieUceNonfatalWarmBootEdpcDisabled, self).prepare()

    def execute(self):
        """
        PCIe UCE error injection in early boot during warm boot cycling.
        eDPC Disabled.

        :return: True or False based on Test Case fail or pass.
        """
        self._log.info("PCIe CScripts error injection Socket: {} Complex.Port: {}".format(self.SOCKET, self.PXP_PORT))
        for i in range(self.NUM_CYCLES):
            try:
                self._log.info("Executing injection loop: " + str(i))
                # initiate warm boot
                self.warm_reboot_non_blocking()
                with ProviderFactory.create(self.sil_cfg, self._log) as cscripts_obj:
                    sdp_obj = ProviderFactory.create(self.si_dbg_cfg, self._log)
                    # set BIOS break point
                    self.set_bios_break(cscripts_obj, self.UPI_POST_CODE_BREAK_POINT)
                    # wait for target to enter break point
                    self.check_bios_progress_code(cscripts_obj, self.UPI_POST_CODE_BREAK_POINT)
                    # inject error
                    self.inject_pcie_uce_and_check_regs_cscripts(cscripts_obj,
                                                                 sdp_obj,
                                                                 socket=self.SOCKET,
                                                                 port=self.PXP_PORT,
                                                                 severity=self.CSCRIPTS_SEVERITY["NONFATAL"])

                    # reset break point
                    self.clear_bios_break(cscripts_obj)
                    # initiate warm reset
                    sdp_obj.reset_target()
                # wait for os and check os logs
                self.os.wait_for_os(self.RESUME_FROM_BREAK_POINT_WAIT_TIME_SEC)
                if not self._os_log_obj.verify_os_log_error_messages(__file__,
                                                                     self._os_log_obj.DUT_JOURNALCTL_CURRENT_BOOT,
                                                                     self.BERT_PCIE_UCENF_JOURNALCTL):
                    log_err = "Error NOT found in OS logs!"
                    self._log.error(log_err)
                    raise content_exception.TestFail(log_err)
            except Exception as ex:
                self._log.error("Failed on loop: " + str(i))
                log_err = "An Exception Occurred : {}".format(ex)
                self._log.error(log_err)
                raise content_exception.TestFail(log_err)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieUceNonfatalWarmBootEdpcDisabled.main() else Framework.TEST_RESULT_FAIL)
