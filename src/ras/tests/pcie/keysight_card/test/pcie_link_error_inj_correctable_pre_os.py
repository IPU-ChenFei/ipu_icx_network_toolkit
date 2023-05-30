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

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory

from src.lib.bios_util import ItpXmlCli
from src.ras.tests.pcie.keysight_card.keysight_card_common import KeysightPcieErrorInjectorCommon
from src.ras.lib.bios_log_verification import SerialLogVerifyCommon


class LcrcCorrectibleErrorResponsePreOs(KeysightPcieErrorInjectorCommon):
    """
    Glasgow_id : 59784

    The objective of this test is to verify platform response to a Correctible HW error injection from a PCIe card
    in a (Pre-OS) UEFI environment.
    """

    BIOS_CONFIG_FILE = "key_sight_lcrc_test_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new LcrcCorrectibleErrorResponsePreOs object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(LcrcCorrectibleErrorResponsePreOs, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)
        self._socket = self._common_content_configuration.get_keysight_card_socket()
        self._pxp_port = self._common_content_configuration.get_keysight_card_pxp_port()
        self._bios_log_verification = SerialLogVerifyCommon(self._log, self.os, cfg_opts, self.serial_log_path)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs whether they updated properly.

        :return: None
        """
        self.prepare_for_uefi()
        pass

    def execute(self):
        """
        1. Boot SUT to UEFI.
        2. Create csp obj.
        3. Create spd object.
        4. Create Keysight provider obj.
        5. Halt the Machine before injecting an Error.
        6. Check LCRC Error status

        :return: True
        """
        #  Create csp object
        csp = ProviderFactory.create(self._csp_cfg, self._log)

        #  Create sdp object
        sdp = ProviderFactory.create(self._sdp_cfg, self._log)

        #  Boot to UEFI
        self.previous_boot_order = self._common_content_lib.boot_to_uefi()

        #  Clear All PCIe Error
        self.clear_pcie_error(csp=csp, sdp=sdp)

        #  bdtlp register should be clear before inject error
        self.check_lcrc_error_status(csp=csp, socket=self._socket, port=self._pxp_port, expected_bdtlp_status=False)
        self._log.info("PCIe Error cleared and now proceeding to inject error")

        #  Create Keysight provider object
        key_sight_provider = self.create_keysight_provider_object()

        #  halt the Machine
        sdp.halt()

        #  Wait for some time after halt
        time.sleep(self._common_content_configuration.itp_halt_time_in_sec())

        #  Inject Bad LCRC Error
        key_sight_provider.inject_bad_lcrc_err()

        #  Wait for some time after Error injection
        time.sleep(self._common_content_configuration.itp_halt_time_in_sec())

        #  Check LCRC Error status
        self.check_lcrc_error_status(csp=csp, socket=self._socket, port=self._pxp_port)

        #  Resume the SUT Machine
        sdp.go()

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        """
        This method is to execute cleanup.
        1. Bring SUT to previous boot order state.
        2. Verify error messages in BIOS.
        """
        if self.itp_xml_cli_util is None:
            self.itp_xml_cli_util = ItpXmlCli(self._log, self.cfg_opts)
        self.current_boot_order = self.itp_xml_cli_util.get_current_boot_order_string()
        if str(self.current_boot_order) != str(self.previous_boot_order):
            self.itp_xml_cli_util.set_boot_order(self.previous_boot_order)
            self.perform_graceful_g3()
        super(LcrcCorrectibleErrorResponsePreOs, self).cleanup(return_status)
        self._bios_log_verification.verify_bios_log_error_messages(
            passed_error_signature_list_to_parse=self.LCRC_COR_SERIAL_SIG)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if LcrcCorrectibleErrorResponsePreOs.main() else Framework.TEST_RESULT_FAIL)
