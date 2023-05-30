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
from dtaf_core.providers.provider_factory import ProviderFactory

from src.ras.tests.iomca_emca.iomca_emca_common import IomcaEmcaCommon
from src.ras.lib.iomca_emca_util import IomcaEmcaUtil
from dtaf_core.lib.dtaf_constants import ProductFamilies


class VerifyIomcaEnabled(IomcaEmcaCommon):
    """
        Glasgow_id : 58468
        This test verifies if BIOS is enabling IOMCA
        This feature allows reporting of IIO uncorrected errors via Machine Check Architecture using a dedicated MCA
        bank (bank#6). Without this feature, all the IIO uncorrected errors would be reported either via NMI or via
        platform specific error handler using SMI or ERROR_N[2:1] pins. Motivation behind this feature is to provide
        a uniform error reporting architecture aligned with MCA and not to rely on NMI for uncorrected error signaling.

        This test verifies if BIOS is enabling IOMCA.

        Test case flow:

        -Cleanup system logs
        -Verify if IOMCA is enabled

    """
    BIOS_CONFIG_FILE = {
        ProductFamilies.CLX: "neoncity_iomca_enable_bios_knob.cfg",
        ProductFamilies.CPX: "neoncity_iomca_enable_bios_knob.cfg",
        ProductFamilies.SKX: "neoncity_iomca_enable_bios_knob.cfg",
        ProductFamilies.ICX: "wilsoncity_iomca_enable_bios_knob.cfg",
        ProductFamilies.SNR: "wilsoncity_iomca_enable_bios_knob.cfg",
        ProductFamilies.SPR: "wilsoncity_iomca_enable_bios_knob.cfg",
    }
    # BIOS_CONFIG_FILE = "wilsoncity_iomca_enable_bios_knob.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new VerifyIomcaEnabled object

        :param test_log: Used for debug and info messages
        :param arguments: Arguments used in Baseclass
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(VerifyIomcaEnabled, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)
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
        super(VerifyIomcaEnabled, self).prepare()

    def execute(self):
        """
        This Method is used to execute the method is_IOMCA_enabled to verify if IOMCA is enabled or not
        :return: iomca enable status
        :return:
        """
        with ProviderFactory.create(self.sil_cfg, self._log) as cscripts_obj:
            iomca_emca_utils_obj = IomcaEmcaUtil(self._log, self._cfg, cscripts_obj, self._common_content_lib)
            return iomca_emca_utils_obj.is_iomca_enabled()


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VerifyIomcaEnabled.main() else Framework.TEST_RESULT_FAIL)
