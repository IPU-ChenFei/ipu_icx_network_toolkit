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

from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.lib.dtaf_constants import Framework

from src.lib import content_exceptions
from src.hsio.upi.hsio_upi_common import HsioUpiCommon
from src.lib.dtaf_content_constants import StreamToolTypes


class UpRxStateWithStream(HsioUpiCommon):
    """
    hsdes_id :  1509257374 upi_rx_state with stream load

    This test verifies UPI rcv port is in L0 ready state after the stress test using Stream.
    run stream load for about 2 hours
    After stream has completed verify the bandwidth >=  76% of expected (based on current link speed)
    Note: Test requires a stream_path which would be installed on SUT, DTAF would install the stream on SUT.
    """
    _BIOS_CONFIG_FILE = "upi_base_stress.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new UpRxStateWithStream object

        :param test_log: Used for debug and info messages
        :param arguments: None
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(UpRxStateWithStream, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.

        :return: None
        """
        super(UpRxStateWithStream, self).prepare()

    def execute(self):
        """
        This method is used to check DIMM configuration and execute verify_upi_error_rate_with_stream to verify that bandwidth is >=76% after stream

        :return: True or False
        """

        # Test content is expected to run for 2 Hrs
        return self.verify_upi_error_rate_with_stream(self._upi_checks.RX_STATE, stream_type=StreamToolTypes.STREAM_TYPE_AVX3, test_duration_hrs=2)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if UpRxStateWithStream.main() else Framework.TEST_RESULT_FAIL)
