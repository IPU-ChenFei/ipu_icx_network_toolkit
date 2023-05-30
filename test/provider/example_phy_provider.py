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
import re
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.base_test_case import BaseTestCase
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.providers.physical_control import PhysicalControlProvider
from dtaf_core.providers.ac_power import AcPowerControlProvider
from dtaf_core.lib.configuration import ConfigurationHelper

from src.lib.common_content_lib import CommonContentLib
from src.lib.content_configuration import ContentConfiguration
from src.lib.dtaf_content_constants import PhysicalProviderConstants


class ExamplePhyProvider(BaseTestCase):
    """
    Test Storage Provider APIs.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        super(ExamplePhyProvider, self).__init__(test_log, arguments, cfg_opts)

        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        ac_config = cfg_opts.find(AcPowerControlProvider.DEFAULT_CONFIG_PATH)
        self.ac = ProviderFactory.create(ac_config, test_log)  # type: AcPowerControlProvider

        sut = ConfigurationHelper.get_sut_config(cfg_opts)

        id_value = '{}'.format(PhysicalProviderConstants.PHY_SX_STATE)
        phy_cfg = ConfigurationHelper.filter_provider_config(sut=sut,
                                                             provider_name=r"physical_control",
                                                             attrib=dict(id=id_value))
        phy_cfg1 = phy_cfg[0]

        id_value = '{}'.format(PhysicalProviderConstants.PHY_POST_CODE)
        phy_cfg = ConfigurationHelper.filter_provider_config(sut=sut,
                                                             provider_name=r"physical_control",
                                                             attrib=dict(id=id_value))

        phy_cfg2 = phy_cfg[0]

        self._phy1 = ProviderFactory.create(phy_cfg1, test_log)  # type: PhysicalControlProvider
        self._phy2 = ProviderFactory.create(phy_cfg2, test_log)  # type: PhysicalControlProvider

        self._common_content_lib = CommonContentLib(test_log, self._os, cfg_opts)

    def prepare(self):
        """
        prepare.
        """
        pass

    def execute(self):
        """
        executes storage provider APIs.
        """
        sx_state = self._common_content_lib.get_power_state(self._phy1)
        self._log.info("sx_state='{}'".format(sx_state))

        bios_pc, fpga_pc = self._common_content_lib.get_post_code(self._phy2)
        self._log.info("BIOS post code={}".format(bios_pc))
        self._log.info("FPGA post code={}".format(fpga_pc))

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ExamplePhyProvider.main() else Framework.TEST_RESULT_FAIL)
