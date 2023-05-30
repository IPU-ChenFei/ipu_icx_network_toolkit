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
from src.lib.install_collateral import InstallCollateral
from src.ras.tests.pcie.aer.ras_pcie_aer_common import PcieAerCommon
from src.ras.lib.os_log_verification import OsLogVerifyCommon
from src.lib.dtaf_content_constants import RasErrorType
from src.lib import content_exceptions


class RasPcieAerMixedCorrNonFatalError(PcieAerCommon):
    """
    Glasgow id : 59689.2
    Sequentially inject a correctable bad TLP and an uncorrectable/non-fatal completion abort error into the device
    with header  log words 0 1 2 3.
    """
    BIOS_CONFIG_FILE = "ras_pcie_aer_bios_knobs.cfg"
    TEST_CASE_ID = ["G59689", "PI-RAS_PCIe_AER_mixed-corr-nonfatal"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Creates a new RasPcieAerMixedCorrNonFatalError object

        :param test_log: Used for debug and info messages
        :param arguments: Arguments used in Baseclass
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(RasPcieAerMixedCorrNonFatalError, self).__init__(test_log, arguments, cfg_opts, self.BIOS_CONFIG_FILE)
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
        6. Install Aer Tool.

        :return: None
        """
        super(RasPcieAerMixedCorrNonFatalError, self).prepare()
        self._aer_inject_tool_path = self._install_collateral.install_aer_inject_tool()

    def execute(self):
        """
        This method is to execute
        1. Create Aer File
        2. get the bdf value of required PCIe.
        3. Clear OS Log.
        4. inject the error
        5. Verify in Os Log
        """
        bdf_value = []
        self.create_aer_file(type_error=RasErrorType.MIXED_CORRECTABLE_NON_FATAL, cmd_path=self._aer_inject_tool_path)
        socket_list = self._common_content_configuration.get_socket_slot_pcie_errinj()
        port_list = self._common_content_configuration.get_pxp_port_pcie_errinj()
        for item in range(0, len(socket_list)):
            bdf_value.append(self._cscripts.get_by_path(self._cscripts.UNCORE, reg_path="pi5.{}.cfg.secbus".format
            (port_list[item]), socket_index=socket_list[item]))
        self._common_content_lib.clear_all_os_error_logs()
        self._log.info("Execute 'modprobe aer-inject'")
        self._common_content_lib.execute_modprobe_aer_inject(cmd_path=self._aer_inject_tool_path)
        self._log.info("Injects error in sockets {} and ports {}".format(socket_list, port_list))
        for item_value in bdf_value:
            self._common_content_lib.clear_all_os_error_logs()
            self._log.info(
                "PCIe device: with bdf: {} is targeting for injecting Error".format(str("{:02x}".format(item_value))+":00.0"))
            self.inject_aer_error(bdf_value=(str("{:02x}".format(item_value))+":00.0"), cmd_path=self._aer_inject_tool_path)
            self.DMESG_CORR_BAD_TLP_UNC_NONFATAL_COMP_ABORT_SIG.append(self.CORR_ERR_RECEIVED.format(str("{:02x}".format(item_value))+":00.0"))
            self.DMESG_CORR_BAD_TLP_UNC_NONFATAL_COMP_ABORT_SIG.append(self.UNC_NONFATAL_ERR_RECEIVED.format(str("{:02x}".format(item_value))+":00.0"))
            time.sleep(self.WAIT_TIME)
            ret_val = self._os_log_verification_obj.verify_os_log_error_messages(
                __file__, self._os_log_verification_obj.DUT_DMESG_FILE_NAME,
                self.DMESG_CORR_BAD_TLP_UNC_NONFATAL_COMP_ABORT_SIG)
            self.DMESG_CORR_BAD_TLP_UNC_NONFATAL_COMP_ABORT_SIG.pop()
            self.DMESG_CORR_BAD_TLP_UNC_NONFATAL_COMP_ABORT_SIG.pop()
            if not ret_val:
                raise content_exceptions.TestFail("Expected OS Log Signature was not Captured")

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if RasPcieAerMixedCorrNonFatalError.main() else Framework.TEST_RESULT_FAIL)
