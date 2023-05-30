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

from src.ras.tests.pcie.keysight_card.keysight_card_common import KeysightPcieErrorInjectorCommon
from src.lib import content_exceptions


class LcrcCorrectibleErrorResponseLinux(KeysightPcieErrorInjectorCommon):
    """
    Glasgow_id : 59911

    The objective of this test is to verify platform response to a Correctible HW error injection from a
    PCIe card in an Linux OS environment (LCRC).
    """

    BIOS_CONFIG_FILE = "key_sight_lcrc_test_bios_knobs.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new LcrcCorrectibleErrorResponseLinux object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(LcrcCorrectibleErrorResponseLinux, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)
        self._socket = self._common_content_configuration.get_keysight_card_socket()
        self._pxp_port = self._common_content_configuration.get_keysight_card_pxp_port()

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
        super(LcrcCorrectibleErrorResponseLinux, self).prepare()

    def execute(self):
        """
        1. Create csp obj.
        2. Create spd object.
        3. Create Keysight provider obj.
        4. Halt the Machine before injecting an Error.
        5. Check LCRC Error status

        :return: True
        """
        # #  Create csp object
        csp = ProviderFactory.create(self._csp_cfg, self._log)

        #  Create sdp object
        sdp = ProviderFactory.create(self._sdp_cfg, self._log)

        #  Create Keysight provider object
        key_sight_provider = self.create_keysight_provider_object()

        is_card_enumerated = self.is_keysight_card_fully_enumerated(port=self._pxp_port, socket=self._socket,
                                                                    csp_obj=csp, sdp_obj=sdp, exec_env="os")
        if not is_card_enumerated:
            key_sight_provider = self.create_keysight_provider_object()
            is_card_enumerated = self.is_keysight_card_fully_enumerated(port=self._pxp_port, socket=self._socket,
                                                                        csp_obj=csp, sdp_obj=sdp, exec_env="os")
            if not is_card_enumerated:
                raise content_exceptions.TestFail("KeySight Card is not Enumerated....")

        #  halt the Machine
        sdp.halt()

        #  check LCRC register before injecting error
        self.check_lcrc_error_status(csp=csp, socket=self._socket, port=self._pxp_port,
                                     expected_bdtlp_status=False)

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

        #  Wait to update the error in OS log
        time.sleep(self.LOG_WAIT_CHECK_TIMER_IN_SEC)

        #  Verify in OS
        dmesg_log_found = self._os_log_ver_obj.verify_os_log_error_messages(__file__,
                                                                       self._os_log_ver_obj.DUT_DMESG_FILE_NAME,
                                                                       self.LCRC_ERR_SIG)
        journal_log_found = self._os_log_ver_obj.verify_os_log_error_messages(__file__,
                                                                         self._os_log_ver_obj.DUT_JOURNALCTL_FILE_NAME,
                                                                         self.LCRC_ERR_SIG)

        if not (dmesg_log_found and journal_log_found):
            raise content_exceptions.TestFail("Expected signature was not captured in OS Log")
        self._log.info("Expected Error Signature was captured in OS")

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if LcrcCorrectibleErrorResponseLinux.main() else
             Framework.TEST_RESULT_FAIL)
