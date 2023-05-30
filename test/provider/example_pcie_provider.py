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
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider # type: SutOsProvider

from src.provider.pcie_provider import PcieProvider  # type: PcieProvider


class ExamplePcieProvider(BaseTestCase):
    """
    Test Pcie Provider APIs.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        super(ExamplePcieProvider, self).__init__(test_log, arguments, cfg_opts)

        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        self._pcie_provider = PcieProvider.factory(self._log, self._os, cfg_opts, execution_env='os', uefi_obj=None)
        # type: PcieProvider

    def prepare(self):
        """
        prepare.
        """
        pass

    def execute(self):
        """
        executes pcie provider APIs.
        """
        linkcap_width = self._pcie_provider.get_linkcap_width('a194')
        self._log.info("Lincap Width: {}".format(linkcap_width))
        linckap_speed = self._pcie_provider.get_linkcap_speed('a194')
        self._log.info("Device detail with linkspeed: {}".format(linckap_speed))
        dict_pcie_devices = self._pcie_provider.get_pcie_devices()
        self._log.info("Pcie Devices={}".format(dict_pcie_devices))
        self._log.info("Device info with device id: {}".format(
             self._pcie_provider.get_device_details_by_device_id('a194')))
        self._log.info("Device info with device class: {}".format(
            self._pcie_provider.get_device_details_by_device_class('System peripheral')))

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if ExamplePcieProvider.main() else Framework.TEST_RESULT_FAIL)
