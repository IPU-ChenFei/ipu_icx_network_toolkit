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
from dtaf_core.providers.sut_os_provider import SutOsProvider

from src.lib.dmidecode_verification_lib import DmiDecodeVerificationLib
from dtaf_core.lib.base_test_case import BaseTestCase


class TestCopySmBiosConfigFile(BaseTestCase):
    """
    Class to copy file smbios config file if does not exists on host.
    """

    def __init__(self, test_log, arguments, cfg_opts):
        super(TestCopySmBiosConfigFile, self).__init__(test_log, arguments, cfg_opts)

        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider

        self._dmi_decode_verification = DmiDecodeVerificationLib(test_log, self._os)

    def prepare(self):
        """
        To check whether the host is alive or not.
        """
        if not self._os.is_alive():
            self._log.error("System is not alive")
            raise RuntimeError("OS is not alive")

    def execute(self):
        """
        Copy platform specific smbios configuration file to C:||Automation folder if it does not exists.
        """
        self._dmi_decode_verification.copy_smbios_config_file_if_not_exist()
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TestCopySmBiosConfigFile.main() else Framework.TEST_RESULT_FAIL)
