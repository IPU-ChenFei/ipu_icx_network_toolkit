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
from src.lib.bios_util import ItpXmlCli


class ExampleContentConfig(BaseTestCase):

    def __init__(self, test_log, arguments, cfg_opts):
        super(ExampleContentConfig, self).__init__(test_log, arguments, cfg_opts)
        self._cfg = cfg_opts

        self._content_config = ContentConfiguration(test_log)
        a = ItpXmlCli(self._log, cfg_opts)

    def execute(self):
        list_pc_errors = self._content_config.get_xmlcli_tools_name()
        print(list_pc_errors)
        list_analyzers = self._content_config.get_axon_analyzers()
        print(list_analyzers)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ExampleContentConfig.main() else Framework.TEST_RESULT_FAIL)
