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

from src.lib import content_exceptions
from src.lib.bios_util import ItpXmlCli
from src.ras.tests.pcie.pei_card.test.pcie_hw_leaky_bucket_basetest import PcieHWLeakyBucketBaseTest
from src.ras.tests.io_virtualization.interleave_base_test import InterleaveBaseTest
from src.ras.lib.bios_log_verification import SerialLogVerifyCommon

class PcieHwPoisonedErrInjUncorrectableNonFatalPreOsNoDpc(PcieHWLeakyBucketBaseTest):
    """
    Phoenix_id : 22013995951

    The objective of this test is to verify platform response to a Non-Fatal HW error injection from a PCIe card
    connected to the CPU lanes under a Linux OS environment.

     Requirements:

     1. BIOS config file path configured in system_configuration.xml
     2. Socket of PEI 4.0 card configured in content_configuration.xml
     3. pxp port of PEI 4.0 card configured in content_configuration.xml
     4. PEI 4.0 HW injector card

     Usage:

     Error type injection is controlled by the "test" parameter in the execute() method and is set to "POISON_TLP" by
     default. To execute the test for POISON_TLP, set test="poisonTLP"

    """

    BIOS_CONFIG_FILE = "pcie_hw_err_injection_bios_knobs_spr.cfg"

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        """
        Creates a new PcieHwPoisonedErrInjUncorrectableNonFatalPreOsNoDpc object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        try:
            super(PcieHwPoisonedErrInjUncorrectableNonFatalPreOsNoDpc, self).__init__(test_log, arguments, cfg_opts)
            self._interleave_base_test = InterleaveBaseTest(test_log, arguments, cfg_opts)
            self._bios_log_verification = SerialLogVerifyCommon(test_log, self.os, cfg_opts, self.serial_log_path)
            self.itp_xml_cli_util = None
        except Exception as e:
            print('Error on line {}'.format(sys.exc_info()[-1].tb_lineno), type(e).__name__, e)

    def prepare(self):
        # type: () -> None
        """
        1. Clear All Os Logs before Starting the Test Case
        2. Set the bios knobs to its default mode.
        3. Set the bios knobs as per the test case.
        4. Reboot the SUT to apply the new bios settings.
        5. Verify the bios knobs whether they updated properly.

        :return: None
        """
        super(PcieHwPoisonedErrInjUncorrectableNonFatalPreOsNoDpc, self).prepare()

    def execute(self):
        """
        This method checks the OS log for errors given a supported error type = "poisonedTLP"

        return: True
        raise: TestFail
        """
        err_type = self.hw_err_injection.POISONED
        test_result = False
        self._log.info("Testing %s case" % err_type)
        self._log.info("Clearing OS logs")
        self._common_content_lib.clear_os_log()
        self._common_content_lib.clear_dmesg_log()
        socket_count = self.cscripts_obj.get_socket_count()

        #  Boot to UEFI
        self.previous_boot_order = self._common_content_lib.boot_to_uefi()
        try:
            self._log.info("Checking config register values before PEI error injection")
            try:
                self.check_config_registers(self.REGISTER_CHECKLIST)
            except:
                self.clear_pcie_error(self.cscripts_obj, self.sdp_obj)
                time.sleep(self.CLR_PCIE_ERR_WAIT_TIME_SEC)
                self.check_config_registers(self.REGISTER_CHECKLIST)

            # checking erruncsev register
            time.sleep(self.WAIT_TIME_FOR_STABILIZING_SYSTEM_SEC)
            if not self.assign_value_to_register_and_verify(self.REG_ERRUNCSEV_PTLPES_ZERO, self.PCIE_SOCKET,
                                                            self.PCIE_PXP_PORT) != 0:
                raise content_exceptions.TestFail("ptlpes Bit not set to 0 for erruncsev register....")

            self.sdp_obj.halt()
            time.sleep(self._common_content_configuration.itp_halt_time_in_sec())
            self._log.info("Injecting errors")
            self.inject_pei_errors(err_type, run_lspci=False)
            time.sleep(self.INJECT_ERR_WAIT_TIME_SEC)
            self.sdp_obj.go()
            time.sleep(self._common_content_configuration.itp_resume_delay_in_sec())
            error_type = err_type + "_pre_os"
            self._log.info("Verify Serial Log for poison injection confirmation")
            time.sleep(self.WAIT_TIME_FOR_STABILIZING_SYSTEM_SEC)
            self._bios_log_verification.verify_bios_log_error_messages(
                passed_error_signature_list_to_parse=self.OS_ERR_SIGNATURE[error_type])
            test_result = True
            self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
            os_hung_wait_time = getattr(self, "OS_WAIT_{}_SOCKET_SEC".format(socket_count))
            self._log.info("Waiting for EFI to come up from reboot/hang status")
            time.sleep(os_hung_wait_time)
        except:
            self._log.info("Test failed, changing boot order back to prior state")
        finally:
            # Bring the SUT to previous boot order state.
            self._log.info("Restore boot order to prior state")
            if self.itp_xml_cli_util is None:
                self.itp_xml_cli_util = ItpXmlCli(self._log, self.cfg_opts)
            self.current_boot_order = self.itp_xml_cli_util.get_current_boot_order_string()
            if str(self.current_boot_order) != str(self.previous_boot_order):
                self.itp_xml_cli_util.set_boot_order(self.previous_boot_order)
                self.perform_graceful_g3()

        return test_result


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieHwPoisonedErrInjUncorrectableNonFatalPreOsNoDpc.main() else Framework.TEST_RESULT_FAIL)
