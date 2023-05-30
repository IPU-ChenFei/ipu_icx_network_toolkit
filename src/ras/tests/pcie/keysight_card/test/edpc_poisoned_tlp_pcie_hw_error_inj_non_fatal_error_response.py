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
from src.ras.lib.ras_common_utils import RasCommonUtil
from src.lib import content_exceptions


class EdpcPoisonedTlpPcieHwErrNonFatalErrorResponseLinux(KeysightPcieErrorInjectorCommon):
    """
    Glasgow_id : 58969

    The objective of this test is the verify eDPC Advance RAS feature ability to prevent poisoned data (Egress)
    from poisoning a downstream port though Containment and Recovery Phase mechanisms..
    """

    BIOS_CONFIG_FILE = "edpc_poisoned_tlp_test_bios_knobs.cfg"
    INJECT_ERR_DELAY_TIME_IN_SEC = 40

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new EdpcPoisonedTlpPcieHwErrNonFatalErrorResponseLinux object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(EdpcPoisonedTlpPcieHwErrNonFatalErrorResponseLinux, self).__init__(test_log, arguments, cfg_opts,
                                                                                 self.BIOS_CONFIG_FILE)
        self._socket = self._common_content_configuration.get_keysight_card_socket()
        self._pxp_port = self._common_content_configuration.get_keysight_card_pxp_port()
        self._ras_common_util_obj = RasCommonUtil(self._log, self.os, cfg_opts, self._common_content_configuration)

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
        super(EdpcPoisonedTlpPcieHwErrNonFatalErrorResponseLinux, self).prepare()

    def execute(self):
        """
        1. Create csp obj.
        2. Create spd object.
        3. Create Keysight provider obj.
        4. Halt the Machine before injecting an Error.
        5. Check Poisoned TLP Error status.
        6. Inject Poisoned TLP Error
        7. Check Poisoned TLP Error Status after injection.
        8. Check OS Log.

        :return: True
        """
        #  Create csp object
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

        #  Check- Poison TLP Error should not Captured before injection.
        self._log.info("Check Poisoned TLP Error Status register before error injection")
        self.check_poisoned_tlp_error_status(csp=csp, socket=self._socket, port=self._pxp_port,
                                             ptlpe_status_reg_indicates_error=False)

        #  Wait for some time after halt.
        time.sleep(self._common_content_configuration.itp_halt_time_in_sec())

        #  Address to inject error
        self._log.info("Getting the address to inject the error")
        targeted_addr_to_inject = self.get_memory_addr_to_inject()
        self._log.info("Targeted address is- {}".format(targeted_addr_to_inject))

        #  Get requester id
        self._log.info("Getting requester id for error injection")
        requester_id = self.get_requester_id()
        self._log.info("Requester id- {}".format(requester_id))

        #  halt the Machine.
        sdp.halt_and_check()

        #  Inject Poison TLP Error.
        self._log.info("Injecting Poison TLP Error")
        key_sight_provider.poisoned_tlp(addy=targeted_addr_to_inject, data=self.POISON_TLP_DATA, reqid=requester_id)
        self._log.info("Poison TLP error injection process is completed")

        #  Wait for some time after Error injection.
        time.sleep(self.INJECT_ERR_DELAY_TIME_IN_SEC)

        #  Check- Poison TLP Error should Captured After injection.
        self._log.info("Checking Poison TLP error status after error injection")
        self.check_poisoned_tlp_error_status(csp=csp, socket=self._socket, port=self._pxp_port,
                                             ptlpe_status_reg_indicates_error=True)

        #  Resume the SUT Machine
        sdp.go()

        time.sleep(self._common_content_configuration.itp_resume_delay_in_sec())

        self._log.info("Checking SUT is still Alive or not")
        if not self.os.is_alive():
          raise content_exceptions.TestFail("System should not get Hung after Error injection")
        self._log.info("SUT is Alive as Expected")

        #  Verify in OS
        self._log.info("Checking Error signature in OS Log")
        os_error_log_found = self._os_log_ver_obj.verify_os_log_error_messages(
            __file__, self._os_log_ver_obj.DUT_DMESG_FILE_NAME, self.EDPC_POISONED_TLP_UCF_SIG_LINUX)

        if not os_error_log_found:
            raise content_exceptions.TestFail("Expected signature was not captured in OS Log")
        self._log.info("Expected Error Signature was captured in OS")

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if EdpcPoisonedTlpPcieHwErrNonFatalErrorResponseLinux.main() else
             Framework.TEST_RESULT_FAIL)
