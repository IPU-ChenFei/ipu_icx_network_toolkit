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

from argparse import Namespace
from typing import Union, List
import xml.etree.ElementTree as ET
import sys

from src.lib.content_base_test_case import ContentBaseTestCase
from src.provider.sgx_provider import SGXProvider

from dtaf_core.lib.dtaf_constants import Framework


class SgxWithLogicalIntegrity(ContentBaseTestCase):
    """
    Test ID: 22014628938
    Enabling SGX with Logical Integrity (SGX-Li)
    Test Pre-requisites: SGX-enabled CPU
    """

    TEST_CASE_ID: List[str] = ["22014628938", "Enabling SGX with Logical Integrity (SGX-Li)"]
    BIOS_CONFIG_FILE: str = "sgx_with_li.cfg"

    def __init__(self, test_log: str, arguments: Union[Namespace, None], cfg_opts: ET.ElementTree):
        super(SgxWithLogicalIntegrity, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)

        self.initialize_sv_objects()
        self.initialize_sdp_objects()
        self.sgx: SGXProvider = SGXProvider.factory(test_log, cfg_opts, self.os, self.SDP)

    def execute(self) -> bool:
        self.sgx.check_sgx_enable()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if SgxWithLogicalIntegrity.main() else Framework.TEST_RESULT_FAIL)
