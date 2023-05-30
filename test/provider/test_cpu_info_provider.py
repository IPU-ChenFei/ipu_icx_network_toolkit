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
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.provider.cpu_info_provider import CpuInfoProvider


class TestCpuInfoProvider(BaseTestCase):
    """
    Test bios util APIs.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        super(TestCpuInfoProvider, self).__init__(test_log, arguments, cfg_opts)

        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        self._cpu_info_provider = CpuInfoProvider.factory(self._log, cfg_opts, self._os) # type: CpuInfoProvider

    def prepare(self):
        """
        To check whether the host is alive or not.
        """
        pass

    def execute(self):
        """
        Copy platform specific smbios configuration file to C:||Automation folder if it does not exists.
        """
        self._log.info("Max Freq='{}'".format(self._cpu_info_provider.get_max_cpu_frequency()))
        self._log.info("Current Freq='{}'".format(self._cpu_info_provider.get_current_cpu_frequency()))
        self._log.info("# of Logical Processors='{}'".format(self._cpu_info_provider.get_logical_processors()))

        if self._os.os_type == OperatingSystems.LINUX:
            self._log.info("L1i cache='{}'".format(self._cpu_info_provider.get_l1i_cache_size()))
            self._log.info("L1d cache='{}'".format(self._cpu_info_provider.get_l1d_cache_size()))
            self._log.info("Min Freq='{}'".format(self._cpu_info_provider.get_min_cpu_frequency()))

        self._log.info("# of Sockets='{}'".format(self._cpu_info_provider.get_number_of_sockets()))
        self._log.info("# of cores='{}'".format(self._cpu_info_provider.get_number_of_cores()))
        self._log.info("L2 Cache Size='{}'".format(self._cpu_info_provider.get_l2_cache_size()))
        self._log.info("L1 Cache Size='{}'".format(self._cpu_info_provider.get_l3_cache_size()))
        self._log.info("Virtualization='{}'".format(self._cpu_info_provider.get_virtualization_data()))

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TestCpuInfoProvider.main() else Framework.TEST_RESULT_FAIL)
