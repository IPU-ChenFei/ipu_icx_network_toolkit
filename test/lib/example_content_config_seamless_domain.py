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

from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.lib.dtaf_constants import Framework

from src.lib.content_configuration import ContentConfiguration


class ExampleContentConfigSeamlessDomain(BaseTestCase):
    DOMAIN_NAME = "seamless"

    def __init__(self, test_log, arguments, cfg_opts):
        super(ExampleContentConfigSeamlessDomain, self).__init__(test_log, arguments, cfg_opts)
        self._cfg = cfg_opts
        self._log = test_log
        self._content_config = ContentConfiguration(test_log)

    def execute(self):
        expected_ver = self._content_config.config_file_path(
                "SEAM_BMC_0003_send_sps_update_capsule/upgrade/expected_ver", self.DOMAIN_NAME)
        self._log.info(expected_ver)
        reboot_time = self._content_config.get_reboot_timeout()
        self._log.info(reboot_time)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ExampleContentConfigSeamlessDomain.main() else Framework.TEST_RESULT_FAIL)
