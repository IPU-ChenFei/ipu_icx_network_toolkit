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
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import ProductFamilies
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.install_collateral import InstallCollateral
from src.ras.tests.pcie.aer.ras_pcie_aer_common import PcieAerCommon
from src.ras.lib.os_log_verification import OsLogVerifyCommon
from src.lib.dtaf_content_constants import RasErrorType
from src.lib import content_exceptions


class RasPcieCorrectableError(PcieAerCommon):
    """
    Glasgow id : 59687.5

    Inject a correctable bad TLP error into the device with header log words 0 1 2 3.
    """
    BIOS_CONFIG_FILE = "ras_pcie_aer_bios_knobs.cfg"
    TEST_CASE_ID = ["G59687", "PI_RAS_PCIe_AER_CorrectableError"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new RasPcieCorrectableError object

        :param test_log: Used for debug and info messages
        :param arguments: Arguments used in Baseclass
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(RasPcieCorrectableError, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self._os_log_verification_obj = OsLogVerifyCommon(self._log, self.os, self._common_content_configuration,
                                                          self._common_content_lib)

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
        super(RasPcieCorrectableError, self).prepare()
        self._common_content_lib.update_micro_code()
        self._aer_inject_tool_path = self._install_collateral.install_aer_inject_tool()

    def execute(self):
        """
        This method is to execute
        1. Create Aer File
        2. get the bdf value of required PCIe.
        3. Clear OS Log.
        4. inject the error
        5. Verify in Os Log

        :return True
        """
        self.create_aer_file(type_error=RasErrorType.CORRECTABLE, cmd_path=self._aer_inject_tool_path)
        pcie_device_name = self._common_content_configuration.get_pcie_device_name()
        bdf_value = self._common_content_lib.get_pcie_device_bdf(pcie_device_name=pcie_device_name)[0]
        self._log.info("First PCIe device: {} with bdf: {} is targeting for injecting Error".format(pcie_device_name,
                                                                                                    bdf_value))
        self._common_content_lib.clear_all_os_error_logs()
        self._log.info("Execute 'modprobe aer-inject'")
        self._common_content_lib.execute_modprobe_aer_inject(cmd_path=self._aer_inject_tool_path)
        self.inject_aer_error(bdf_value=bdf_value, cmd_path=self._aer_inject_tool_path)
        self.DMESG_BAD_TLP_CORR_ERR_SIG.append(self.CORR_ERR_RECEIVED.format(bdf_value))
        ret_val = self._os_log_verification_obj.verify_os_log_error_messages(
            __file__, self._os_log_verification_obj.DUT_DMESG_FILE_NAME, self.DMESG_BAD_TLP_CORR_ERR_SIG)
        if not ret_val:
            raise content_exceptions.TestFail("Expected OS Log Signature was not Captured")
        if self.os.is_alive():
            self._common_content_lib.delete_micro_code()
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RasPcieCorrectableError.main() else Framework.TEST_RESULT_FAIL)
