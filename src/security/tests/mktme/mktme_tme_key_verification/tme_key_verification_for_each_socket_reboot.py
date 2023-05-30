#!/usr/bin/env python
##########################################################################
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and
# proprietary and confidential information of Intel Corporation and its
# suppliers and licensors, and is protected by worldwide copyright and trade
# secret laws and treaty provisions. No part of the Material may be used,
# copied, reproduced, modified, published, uploaded, posted, transmitted,
# distributed, or disclosed in any way without Intel's prior express written
# permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
##########################################################################
import sys
import os
import argparse
import logging
from xml.etree import ElementTree

from dtaf_core.lib.dtaf_constants import Framework

from src.security.tests.mktme.mktme_common import MktmeBaseTest
from src.lib import content_exceptions


class MkTmeKeyCheckForEachSocketWithReboot(MktmeBaseTest):
    """
    Phoenix ID : 18014070573 - Verify BIOS generates new TME key for each socket on every reboot 
    """
    TEST_CASE_ID = "18014070573"

    _BIOS_CONFIG_FILE_ENABLE = r"..\collateral\tme_and_tme_mt_enable_knob.cfg"

    def __init__(self, test_log: logging.Logger, arguments: argparse.Namespace, cfg_opts: ElementTree) -> None:
        """Create an instance of MkTmeKeyCheckForEachSocket

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """

        self.tme_bios_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)), self._BIOS_CONFIG_FILE_ENABLE)
        super(MkTmeKeyCheckForEachSocketWithReboot, self).__init__(test_log, arguments, cfg_opts)
        self.socket_count = 0

    def prepare(self):
        # type: () -> None
        super(MkTmeKeyCheckForEachSocketWithReboot, self).prepare()

    def initialize_pythonsv(self):
        """"Initialize the python sv objects at the base class """

        self.initialize_sv_objects()
        self.initialize_sdp_objects()
        self.unlock_itp()

    def verify_tme_and_tme_mt_values(self) -> None:
        """Verify the tme and tme-mt values and validate it
        :return: None
        :raise content_exceptions.TestFail: if capability or activate is 0 values"""

        # refresh the sv object to get the latest updates.
        self.SV.refresh()
        # get tme capability value
        tme_capability = self.SV.get_by_path(self.SV.UNCORE, "memss.mc0.ch0.tme.tme_capability")

        # get tme activate value
        tme_activate = self.SV.get_by_path(self.SV.UNCORE, "memss.mc0.ch0.tme.tme_activate")

        self._log.info(f"TME Capability value is : {tme_capability}")
        if tme_capability == 0:
            raise content_exceptions.TestFail("tme_capability is 0")

        self._log.info(f"TME Activate value is : {tme_activate}")
        if tme_activate == 0:
            raise content_exceptions.TestFail("tme_activate is 0")

    def get_tme_key(self, socket: int = 0) -> str:
        """ get the tme key created by socket

        :param socket: socket number
        :return : the tme_key as single concatenated string value
        """
        self.SV.refresh()
        tme_k1_high = self.SV.get_by_path(self.SV.UNCORE, "memss.mc0.ch0.tme.cr_tme_k1_high_0", socket_index=socket)
        tme_k1_low = self.SV.get_by_path(self.SV.UNCORE, "memss.mc0.ch0.tme.cr_tme_k1_low_0", socket_index=socket)
        tme_k2_high = self.SV.get_by_path(self.SV.UNCORE, "memss.mc0.ch0.tme.cr_tme_k2_high_0", socket_index=socket)
        tme_k2_low = self.SV.get_by_path(self.SV.UNCORE, "memss.mc0.ch0.tme.cr_tme_k2_low_0", socket_index=socket)
        self._log.info(f"Key Values {str(hex(tme_k1_high))} {str(hex(tme_k1_low))} {str(hex(tme_k2_high))}"
                       f" {str(hex(tme_k2_low))}")

        ret_val: str = str(hex(tme_k1_high)) + str(hex(tme_k1_low)).lstrip('0x') +\
                       str(hex(tme_k2_high)).lstrip('0x') + str(hex(tme_k2_low).lstrip('0x'))
        self._log.debug(f"Combined tme-key value for socket {socket} is {ret_val}")
        return ret_val

    def execute(self):
        """ Sets the bios knobs according to configuration file.
        Then verifies the tme_capability and tme_activate values are non zero.
        Tme_key for each socket is unique even after reboot the SUT
        """

        # if TME and TME-MT is not enabled by default, then set the values, reboot and verify again
        try:
            self.bios_util.verify_bios_knob(bios_config_file=self.tme_bios_enable)
        except RuntimeError:
            # Enable TME and TME-MT now.
            self.bios_util.set_bios_knob(bios_config_file=self.tme_bios_enable)
            self.perform_graceful_g3()
            self.bios_util.verify_bios_knob(bios_config_file=self.tme_bios_enable)

        self.initialize_pythonsv()
        self.socket_count = self.SV.get_socket_count()
        self._log.info("Socket count : {}".format(self.socket_count))
        self.SV.refresh()

        self.verify_tme_and_tme_mt_values()

        tme_keys: str = []
        for socket_index in range(0, self.socket_count):
            new_tme_key = self.get_tme_key(socket_index)
            # If the new value belongs to anther socket, just throw exception.
            if new_tme_key not in tme_keys:
                tme_keys.append(new_tme_key)
            else:
                raise content_exceptions.TestFail("TME key is duplicated")

        # reboot the system and check the values.
        self.perform_graceful_g3()
        self.unlock_itp()
        self.SV.refresh()
        self.verify_tme_and_tme_mt_values()
        for socket_index in range(0, self.socket_count):
            new_tme_key = self.get_tme_key(socket_index)
            if new_tme_key not in tme_keys:
                tme_keys.append(new_tme_key)
            else:
                raise content_exceptions.TestFail("TME key is duplicated after reboot")

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MkTmeKeyCheckForEachSocketWithReboot.main() else Framework.TEST_RESULT_FAIL)
