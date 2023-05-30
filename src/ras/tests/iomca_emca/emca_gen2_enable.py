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
from dtaf_core.lib.dtaf_constants import ProductFamilies
from dtaf_core.providers.provider_factory import ProviderFactory

from src.ras.tests.iomca_emca.iomca_emca_common import IomcaEmcaCommon
from src.ras.lib.iomca_emca_util import IomcaEmcaUtil


class EmcaGen2Enable(IomcaEmcaCommon):
    """
    Glasgow_id : 58469
    Check if Emca Gen 2 is enabled in BIOS and verifying using ITP.
    """
    BIOS_CONFIG_FILE = "emca_gen2_bios_knob.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new EmcaGen2Enable object

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(EmcaGen2Enable, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)
        self._cfg = cfg_opts

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Setting the bios knobs to its default mode.
        3. Setting the bios knobs as per the test case.
        4. Rebooting the SUT to apply the new bios settings.
        5. Verifying the bios knobs that are set.

        :return: None
        """
        super(EmcaGen2Enable, self).prepare()

    def execute(self):
        """
        Creating IomcaEmcaUtil object and checking emca gen2 is enabled or not.

        :return: emca gen2 enable status
        """
        if self._product != ProductFamilies.SPR:
            self._cscripts = ProviderFactory.create(self.sil_cfg, self._log)  # type: SiliconRegProvider

        iomca_emca_utils_obj = IomcaEmcaUtil(self._log, self._cfg, self._cscripts, self._common_content_lib)
        return iomca_emca_utils_obj.is_emca_gen2_enabled()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if EmcaGen2Enable.main() else Framework.TEST_RESULT_FAIL)
