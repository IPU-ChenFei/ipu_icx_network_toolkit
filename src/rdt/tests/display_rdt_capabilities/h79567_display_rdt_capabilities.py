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

from dtaf_core.lib.dtaf_constants import Framework, OperatingSystems

from src.lib import content_base_test_case
from src.rdt.lib.rdt_utils import RdtUtils
from src.lib import content_exceptions


class DisplayRdtCapabilities(content_base_test_case.ContentBaseTestCase):
    """
    HPQC ID : H79567-PI_RDT_A_DisplayRDTCapabilities_L

    This test case Display current RDT capabilities via pqos -d commands
     and checks if there is any error or warnings found during the execution of pqos commands.
    """

    TEST_CASE_ID = ["H79567-PI_RDT_A_DisplayRDTCapabilities_L"]
    PQOS_CMD_LIST = [["pqos -d", "Displays supported RDT capabilities"],
                ["pqos -D", "Displays detailed information about supported RDT capabilities"
                            " and ‘Cache information’ section"]]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create an instance of DisplayRdtCapabilities

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(DisplayRdtCapabilities, self).__init__(test_log, arguments, cfg_opts)
        self._rdt = RdtUtils(self._log, self._common_content_lib, self._common_content_configuration, self.os, cfg_opts)
        if self.os.os_type != OperatingSystems.LINUX:
            raise content_exceptions.TestNAError("RDT installation is not implemented for the os: {}".format(
                self.os.os_type))

    def execute(self):
        """
        This method executes the pqos commands.

        :return: True if test case pass
        """
        self._log.info("Checking RDT is installed in sut")
        self._rdt.install_rdt()
        self._log.info("Executing pqos capabilities commands")
        self._rdt.execute_pqos_cmd(self.PQOS_CMD_LIST)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if DisplayRdtCapabilities.main() else Framework.TEST_RESULT_FAIL)
