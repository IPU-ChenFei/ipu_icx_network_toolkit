# !/usr/bin/env python
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
from dtaf_core.providers.sut_os_provider import SutOsProvider
from dtaf_core.lib.dtaf_constants import OperatingSystems
from src.lib.common_content_lib import CommonContentLib


class TpmInitializeTurnOn(BaseTestCase):
    """
    Glasgow ID : 44799
    Test TPM device on Windows with TPM module installed.
    Ensure coordinated events with: BIOS, TPM device, OS (embedded) driver, and TPM Console (OS).
    """

    PS_CMD_GET_TPM_STATUS = 'powershell.exe "Get-TPM"'

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance for TpmInitializeTurnOn

        :param test_log: Used for error, debug and info messages.
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(TpmInitializeTurnOn, self).__init__(test_log, arguments, cfg_opts)
        sut_os_cfg = cfg_opts.find(SutOsProvider.DEFAULT_CONFIG_PATH)
        self._os = ProviderFactory.create(sut_os_cfg, test_log)  # type: SutOsProvider
        self._common_content_lib = CommonContentLib(self._log, self._os, cfg_opts)
        self._command_timeout = self._common_content_lib.get_sut_execute_cmd_timeout_in_sec()

    def prepare(self):
        """
        Pre validate the SUT should be in windows OS and check SUT is alive or not.
        """
        if not self._os.os_type == OperatingSystems.WINDOWS:
            self._log.error("This test case only applicable for windows system")
            raise RuntimeError("This test case only applicable for windows system")
        if not self._os.is_alive():
            self._log.error("System is not alive")
            raise RuntimeError("OS is not alive")

    def check_tpm_status(self, tpm_info):
        """
        This Function execute TPM command in power shell and get the TPM Status.

        :return True if the both value of TpmPresent and TPMReady is True and False if any one of the value is False.
        """
        TPM_PRESENT_STR = "TpmPresent"
        TPM_READY_STR = "TpmReady"
        tpm_info_val = tpm_info.lstrip().replace(" ", "").split("\n")  # Fetching values for TpmPresent and TpmReady
        ret_val = []
        for value in tpm_info_val:
            if TPM_PRESENT_STR in value and "True" in value:
                self._log.info("'{}' is ready for use".format(TPM_PRESENT_STR))
                ret_val.append(True)
            elif TPM_PRESENT_STR in value and "False" in value:
                self._log.info("'{}' is not ready for use".format(TPM_PRESENT_STR))
                ret_val.append(False)
            if TPM_READY_STR in value and "True" in value:
                self._log.info("'{}' is ready for use".format(TPM_READY_STR))
                ret_val.append(True)
            elif TPM_READY_STR in value and "False" in value:
                self._log.info("'{}' is not ready for use".format(TPM_READY_STR))
                ret_val.append(False)
        return all(ret_val)

    def execute(self):
        """
        Checking TPM status is ready or not in windows OS.

        :return True if TPM is ready for use else False
        """
        # Fetching data from power shell command "get-tpm".
        tpm_info = self._common_content_lib.execute_sut_cmd(
            self.PS_CMD_GET_TPM_STATUS, "GET TPM", self._command_timeout, None)
        return self.check_tpm_status(tpm_info)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if TpmInitializeTurnOn.main() else Framework.TEST_RESULT_FAIL)
