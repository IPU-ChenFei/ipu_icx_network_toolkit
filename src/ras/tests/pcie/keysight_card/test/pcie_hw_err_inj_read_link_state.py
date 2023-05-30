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


class PcieHwErrorInjReadLinkState(KeysightPcieErrorInjectorCommon):
    """
    Glasgow_id : G43872

    PCIe HW Injector - Read Link State.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new PcieHwErrorInjReadLinkState object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PcieHwErrorInjReadLinkState, self).__init__(test_log, arguments, cfg_opts)
        self._width = self._common_content_configuration.get_keysight_card_width()
        self._card_gen = self._common_content_configuration.get_keysight_card_gen()

    def prepare(self):
        # type: () -> None
        """ prepare for Test"""
        pass

    def execute(self):
        """
        1. Create Keysight provider obj.
        2. Check Speed and Width.

        :return: True
        """
        #  Create Keysight provider object
        key_sight_provider = self.create_keysight_provider_object()

        if not key_sight_provider:
            raise content_exceptions.TestFail("Keysight Provider object is not created")
        width_output = key_sight_provider.get_keysight_link_width()
        if width_output != self._width:
            raise content_exceptions.TestFail("KeySight Card width was found as : {} which is not an expected."
                                              " Expected width is : {} ".format(width_output, self._width))
        self._log.info("LinkWidth was found as Expected: {}".format(width_output))

        gen_output = key_sight_provider.get_keysight_link_speed()
        if gen_output != self._card_gen:
            raise content_exceptions.TestFail("KeySight Card Gen was found as : {} which is not an expected."
                                              " Expected Gen is : {} ".format(gen_output, self._card_gen))
        self._log.info("Keysight Card Gen was found as expected: {}".format(gen_output))

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieHwErrorInjReadLinkState.main() else
             Framework.TEST_RESULT_FAIL)
