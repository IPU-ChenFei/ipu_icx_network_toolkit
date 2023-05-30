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

from src.hsio.upi.hsio_upi_common import HsioUpiCommon


class UpiLinkwidthdWithMLCLoad(HsioUpiCommon):
    """
    hsdes_id :  22012954129 upi_linkwidth with mlc load

    This test verifies link width is stable and all lanes are active through cscripts -
    MLC load for about 2 hours
    After MLC  has completed verify the bandwidth >=  85% of expected (based on current link speed)
    Note: Test requires a mlc_path entry in the content_configuration.xml and an MLC app zip in hte collaterals.
    """
    _BIOS_CONFIG_FILE = "upi_base_stress.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new UpiLinkwidthdWithMLCLoad object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(UpiLinkwidthdWithMLCLoad, self).__init__(test_log, arguments, cfg_opts, self._BIOS_CONFIG_FILE)

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
        super(UpiLinkwidthdWithMLCLoad, self).prepare()

    def execute(self):
        """
        This method is used to execute verify_upi_linkwidth_with_mlc to verify that bandwidth is >=85% after MLC

        :return: True or False based on the Output of upi_with_mlc
        """

        return self.verify_upi_with_mlc(test_type=self._upi_checks.LANE)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if UpiLinkwidthdWithMLCLoad.main() else Framework.TEST_RESULT_FAIL)
