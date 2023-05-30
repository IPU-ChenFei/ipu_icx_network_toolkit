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

import os
import sys

from dtaf_core.lib.dtaf_constants import Framework
from src.hsio.pcie.pcie_surprise_linkdown_trigger_basetest import PcieSurpriseLinkDownBaseTest
from src.lib.bios_util import ItpXmlCli
from src.lib import content_exceptions


class SldLoggingUefi(PcieSurpriseLinkDownBaseTest):
    """
    Phoenix ID: 16016507425

    This Test is to check SLd logging at UEFI level.This is to test out hardware-only behavior
    without interference from OS. Force link-down (With Force-Detect):

    If SLD status is not set, flag an error.
    If SLD status is set and DPC is not triggered, flag an error.
    If SLD status is set and DPC is triggered, clear DPC event
    Then if link is down, flag and error
    else if link is up, test is passing

    Then repeat steps again for 100 iteration on all PCIe slots
    """
    BIOS_CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sld_logging_bios_knobs.cfg")

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a SldLoggingUefi object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(SldLoggingUefi, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)
        self.itp_xml_cli_util = None

    def prepare(self):  # type: () -> None
        """
        prepare
        """
        super(SldLoggingUefi, self).prepare()

    def execute(self):
        """
        This method is to execute:

        1. Get the register from config.
        2. Check Error from ltssm.check_for_error().
        3. Run Suprise Link Down Edpc Run.
        4. Check
        :return: True or False
        """

        self.previous_boot_order = self._common_content_lib.boot_to_uefi()

        try:

            if self.check_for_errors(sdp=self.sdp_obj, pxp_port_list=self._pxp_port_list, clear_errors=1):
                raise content_exceptions.TestFail("Error was captured in ltssm check - check_for_error output")

            self._log.info("No Error is captured in ltssm check - check_for_error output")

            if not self.run_sld_edpc(sdp=self.sdp_obj, socketnum_pxpport_list=self._pxp_port_list, loop=100):
                raise content_exceptions.TestFail("Failed: during surprise link down Edpc run")

            if self.check_for_errors(sdp=self.sdp_obj, pxp_port_list=self._pxp_port_list, clear_errors=1):
                raise content_exceptions.TestFail("Error was captured in ltssm check - check_for_error output")

            self._log.info("No Error is captured in ltssm check - check_for_error output")
        except Exception as ex:
            raise content_exceptions.TestFail("Test Case Failed due to an exception Occur- {}.".format(ex))

        finally:
            # Bring the SUT to previous boot order state.
            if self.itp_xml_cli_util is None:
                self.itp_xml_cli_util = ItpXmlCli(self._log, self._cfg)
            self.current_boot_order = self.itp_xml_cli_util.get_current_boot_order_string()
            if str(self.current_boot_order) != str(self.previous_boot_order):
                self.itp_xml_cli_util.set_boot_order(self.previous_boot_order)
                self.perform_graceful_g3()

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SldLoggingUefi.main() else Framework.TEST_RESULT_FAIL)
