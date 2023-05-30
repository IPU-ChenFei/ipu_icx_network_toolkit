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
from dtaf_core.lib.base_test_case import BaseTestCase

from src.environment.os_prerequisites import OsPreRequisitesLib


class TestOsPreRequest(BaseTestCase):
    C_DRIVE_PATH = "C:\\"
    SUT_INVENTORY_FILE_NAME = r"C:\Inventory\sut_inventory.cfg" 

    def __init__(self, test_log, arguments, cfg_opts):
        self._log = test_log
        super(TestOsPreRequest, self).__init__(test_log, arguments, cfg_opts)

        self._os_pre_req_lib = OsPreRequisitesLib(test_log, cfg_opts)

    def prepare(self):
        """
        To check whether the host is alive or not.
        """
        pass

    def execute(self):
        """
        Function to test the ssd name picking based on os param and fetching blank sdds.
        """
        ssds = self._os_pre_req_lib.get_ssd_names_config("centos")
        self._log.info("Number of ssds connected with centos / blank: {}".format(ssds))
        self._log.info("Fetching the sdds of only centos..")
        self._os_pre_req_lib.get_sut_inventory_data("centos")

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TestOsPreRequest.main() else Framework.TEST_RESULT_FAIL)
