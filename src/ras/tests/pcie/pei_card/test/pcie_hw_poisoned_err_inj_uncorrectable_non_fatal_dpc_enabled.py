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
import os
import sys
import time
from pathlib import Path

from dtaf_core.lib.dtaf_constants import Framework

from src.lib import content_exceptions
from src.ras.tests.pcie.pei_card.test.pcie_hw_leaky_bucket_basetest import PcieHWLeakyBucketBaseTest


class PcieHwPoisonedErrInjUncorrectableNonFatalDpcEnabled(PcieHWLeakyBucketBaseTest):
    """
    Phoenix_id : 22013419976

    The objective of this test is to verify platform response to a Non-Fatal HW error injection from a PCIe card
    connected to the CPU lanes under a Linux OS environment.

     Requirements:

     1. BIOS config file path configured in system_configuration.xml
     2. Socket of PEI 4.0 card configured in content_configuration.xml
     3. pxp port of PEI 4.0 card configured in content_configuration.xml
     4. PEI 4.0 HW injector card

     Usage:

     Error type injection is controlled by the "test" parameter in the execute() method and is set to "POISON_TLP" by
     default. To execute the test for POISON_TLP, set test="poisonTLP" or tag from common_content_config.xml can be used
     <pei_card>
            <err_type>poisonedTLP</err_type>
     </pei_card>

    Note: Please add BDF for the endpoint at "<ras>/<linux_os_pcie_bdf>"
    """
    BIOS_CONFIG_FILE = "pcie_hw_err_injection_bios_knobs_spr_dpc_aer_fatal_enabled.cfg"
    ENDPOINT_BIOS_CONFIG_FILE = os.path.join(Path(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))),
                                             BIOS_CONFIG_FILE)
    ENDPOINT_ADDR_EXTRACT_CMD = 'lspci -s {} -vv | grep "Region 0"'
    NUMS_OF_ITERATION = 2

    def __init__(self, test_log, arguments, cfg_opts, bios_config_file=None):
        """
        Creates a new PcieHwPoisonedErrInjUncorrectableNonFatalDpcEnabled object

        :param test_log: Used for debug and info messages
        :param arguments:
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        """
        super(PcieHwPoisonedErrInjUncorrectableNonFatalDpcEnabled, self).__init__(test_log, arguments, cfg_opts)

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
        super(PcieHwPoisonedErrInjUncorrectableNonFatalDpcEnabled, self).prepare()

    def execute(self):
        """
        This method checks the OS log for errors given a supported error type = "poisonedTLP"

        return: True
        raise: TestFail
        """
        err_type = self.hw_err_injection.POISONED
        self._log.info("Testing %s case" % err_type)
        self._log.info("Clearing OS logs")
        self._common_content_lib.clear_os_log()

        self.sdp_obj.halt()
        time.sleep(self._common_content_configuration.itp_halt_time_in_sec())

        for iter in range(self.NUMS_OF_ITERATION):

            self._log.info("Checking config register values before PEI error injection")
            try:
                self.check_config_registers(self.REGISTER_CHECKLIST)
            except:
                self.clear_pcie_error(self.cscripts_obj, self.sdp_obj)
                time.sleep(self.CLR_PCIE_ERR_WAIT_TIME_SEC)
                self.check_config_registers(self.REGISTER_CHECKLIST)

            # checking erruncsev register
            time.sleep(self.WAIT_TIME_FOR_STABILIZING_SYSTEM_SEC)
            if not self.assign_value_to_register_and_verify(self.REG_ERRUNCSEV_PTLPES, self.PCIE_SOCKET,
                                                            self.PCIE_PXP_PORT) != 0:
                raise content_exceptions.TestFail("ptlpes Bit not set to 0 for erruncsev register....")

            if iter == 0:
                self.sdp_obj.halt()
                time.sleep(self._common_content_configuration.itp_halt_time_in_sec())
            self._log.info("Injecting errors")
            self.inject_pei_errors(err_type, run_lspci=False)
            time.sleep(self.INJECT_ERR_WAIT_TIME_SEC)

            self.sdp_obj.go()
            time.sleep(self._common_content_configuration.itp_resume_delay_in_sec())

            if not self.os.is_alive():
                raise content_exceptions.TestFail("OS is not alive after injection, Test Failed")

            self._log.info("Verify OS Log")
            self.check_os_errors_reported(err_type)

            # clear dmesg before proceeding to next loop.
            self._common_content_lib.clear_os_log()

        # injection with Endpoint
        err_type = "tlp_gen"
        self.ENDPOINT_BDF = self._common_content_configuration.get_linux_os_pcie_bdf()
        self._log.info("Endpoint Ethernet BDF provided - {}".format(self.ENDPOINT_BDF))
        addr_info_list = self.os.execute(self.ENDPOINT_ADDR_EXTRACT_CMD.
                                         format(self.ENDPOINT_BDF), self._command_timeout).stdout.split()
        for item in range(len(addr_info_list)):
            if addr_info_list[item] == "(64-bit,":
                bar_address = addr_info_list[item - 1]
                break
        bar_address = "0x" + bar_address
        self._log.info("Addr extracted for the given endpoint - {}".format(bar_address))

        # set required bios knobs
        self.set_and_verify_bios_knobs(self.ENDPOINT_BIOS_CONFIG_FILE)

        # checking erruncsev register
        time.sleep(self.WAIT_TIME_FOR_STABILIZING_SYSTEM_SEC)
        if not self.assign_value_to_register_and_verify(self.REG_ERRUNCSEV_PTLPES_ZERO, self.PCIE_SOCKET,
                                                        self.PCIE_PXP_PORT) != 0:
            raise content_exceptions.TestFail("ptlpes Bit not set to 0 for erruncsev register....")

        self._common_content_lib.clear_dmesg_log()

        # Injecting Error
        self.sdp_obj.halt()
        time.sleep(self._common_content_configuration.itp_halt_time_in_sec())

        self._log.info("Injecting errors using bar address of endpoint")

        getattr(self.hw_injector, self.PEI_TEST_TYPES[err_type])(field={"Fmt": 3, "Type": 0,
                                                                        "Length": 1, "BE_1st": 0xf,
                                                                        "EP":1, "ReqID_Req": 0x0d4b,
                                                                        "Addr_64": int(bar_address, 16)}, count=1)
        time.sleep(self.INJECT_ERR_WAIT_TIME_SEC)
        self.sdp_obj.go()
        time.sleep(self._common_content_configuration.itp_resume_delay_in_sec())

        if not self.os.is_alive():
            raise content_exceptions.TestFail("OS is not alive after injection, Test Failed")

        error_type = "poisonedTLP_endpoint"
        self._log.info("Verify OS Log")
        self.check_os_errors_reported(error_type)

        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PcieHwPoisonedErrInjUncorrectableNonFatalDpcEnabled.main() else Framework.TEST_RESULT_FAIL)
