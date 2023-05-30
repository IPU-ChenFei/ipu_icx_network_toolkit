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
# secret laws and treaty provisions. No part of the Material may be used,copied,
# reproduced, modified, published, uploaded, posted, transmitted, distributed,
# or disclosed in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
##########################################################################

import os
import sys

from dtaf_core.lib.dtaf_constants import Framework

from src.security.tests.mktme.mktme_common import MktmeBaseTest
from src.security.tests.mktme.enable_mktme_max_keys.enable_mktme_max_keys import EnableMktme


class VerifyRelocationMMIOHBase(MktmeBaseTest):
    """
    Glasgow ID  : G59475.1-Verify the relocation of MMIOH Base
    Phoenix ID  : P18014070600 - Verify the relocation of MMIOH Base
    This Test case is enabling TME and MKTME BIOS Knobs and verify msr values
    and Verirfy MMIOH base knob
    """
    BIOS_CONFIG_FILE_MMIO = "../verify_relocation_mmiohbase/verify_relocation_mmiohbase_knob.cfg"
    TEST_CASE_ID = ["G59475.1-Verify the relocation of MMIOH Base",
                    "P18014070600 - Verify the relocation of MMIOH Base"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of VerifyRelocationMMIOHBase

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.mmioh_base_bios_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE_MMIO)
        super(VerifyRelocationMMIOHBase, self).__init__(test_log, arguments, cfg_opts)
        self._enable_mktme_test_obj = EnableMktme(test_log, arguments, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        This function check verify platform supporting the MKTME and Enabling TME and MK-TME Bios knobs.
        check the TME, MK-TME MSR Value and Verify the Max No of Keys

        :return True else false
        """
        self._enable_mktme_test_obj.prepare()
        self._enable_mktme_test_obj.execute()

    def execute(self):
        """
        Verify the MMiOH Base value.

        :return True else false
        """
        self._log.info("Check MMIO High Base bios setting")
        self.bios_util.verify_bios_knob(bios_config_file=self.mmioh_base_bios_file)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VerifyRelocationMMIOHBase.main() else Framework.TEST_RESULT_FAIL)
