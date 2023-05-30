#!/usr/bin/env python
##########################################################################
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and proprietary
# and confidential information of Intel Corporation and its suppliers and
# licensors, and is protected by worldwide copyright and trade secret laws and
# treaty provisions0. No part of the Material may be used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or disclosed
# in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
##########################################################################

import os
import re
import sys

from dtaf_core.lib.dtaf_constants import Framework

from src.lib.test_content_logger import TestContentLogger
from src.security.tests.mktme.mktme_common import MktmeBaseTest
from src.lib import content_exceptions


class MktmeDiscoveryTmeEnumWithCpuid(MktmeBaseTest):
    """
    Hpalm Id : H79555- PI_Security_MKTME_Discovery_TmeEnumeration
    Phoneix ID : P18014074766-PI_Security_MKTME_Discovery_TmeEnumeration
    This Test case is Used to  
        1. Verify if Sut's CPU SKU Supports MKTME.
        2. Execute CPUID Command and Verify EAX<ECX and EDX Values are SET.
        3. Enable TME Bios Knob and Verify
    """
    TEST_CASE_ID = ["H79555- PI_Security_MKTME_Discovery_TmeEnumeration",
                    "P18014074766-PI_Security_MKTME_Discovery_TmeEnumeration"]
    STEP_DATA_DICT = {
        1: {'step_details': 'Run ITP commands '
                            'first command (itp.threads[0].cpuid_edx(0x7) & (1 << 18)) != 0  '
                            'second command itp.threads[0].cpuid_eax(0x1b) == 1 '
                            'third command  (itp.threads[0].cpuid_ecx(0x7) & (1 << 13)) != 0 ',
            'expected_results': 'first ,second and third command should return True'},
        2: {'step_details': 'Install CPUID on SUT and Execute CPUID Commands to verify EAX, ECX, EDX are Set',
            'expected_results': 'Cpuid Commands are Executed and EAX, ECX and EDX are Set'},
        3: {'step_details': 'Enable TME bios Knob',
            'expected_results': 'Verify if TME Bios Knob is Successfully Enabled'},
    }

    CPUID_ECX_EDX_CMD = "cpuid -l 0x7 -r"
    CPUID_EAX_CMD = "cpuid -l 0x1b -r"
    REGEX_FOR_ECX = r"ecx=.*\s"
    REGEX_FOR_EDX = r"edx=.*"
    REGEX_FOR_CPUID_EAX_VALUE = r"eax.0x0*1"
    ENABLE_TME_BIOS_KNOB = "../enable_tme/tme_enable_knob.cfg"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of MktmeDiscoveryTmeEnumWithCpuid

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        super(MktmeDiscoveryTmeEnumWithCpuid, self).__init__(test_log, arguments, cfg_opts)
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self.enable_tme_bios_knob_file = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                      self.ENABLE_TME_BIOS_KNOB)

    def prepare(self):
        # type: () -> None
        """
        pre-checks if the sut is alive or not and configure Bios Settings as Required and Install CPUID Tool
         On Sut.
        """
        super(MktmeDiscoveryTmeEnumWithCpuid, self).prepare()
        self._log.info("Install CPUID Tool on SUT")
        self._install_collateral.install_cpuid()

    def execute(self):
        """
        This Method is Used to 
        1. Verify if Sut's CPU SKU Supports MKTME.
        2. Execute CPUID Command and Verify EAX<ECX and EDX Values are SET.
        3. Enable TME Bios Knob and Verify

        :return: True
        raise: content_exceptions.TestFail
        """
        self._test_content_logger.start_step_logger(1)
        if not self.verify_mktme():
            raise content_exceptions.TestFail("SUT's CPU SKU does not supports MKTME.")
        self._log.info("SUT's CPU SKU supports MKTME.")
        self._test_content_logger.end_step_logger(1, True)

        self._test_content_logger.start_step_logger(2)
        cpuid_ecx_edx_output = self.execute_cpuid(command=self.CPUID_ECX_EDX_CMD)
        ecx_value = re.search(re.compile(self.REGEX_FOR_ECX), cpuid_ecx_edx_output).group().split(" ")[0].split("=")[1]
        edx_value = re.search(re.compile(self.REGEX_FOR_EDX), cpuid_ecx_edx_output).group().split("=")[1]
        cpuid_edx_binary_value = self._common_content_lib.convert_hexadecimal([edx_value])
        cpuid_edx_bit18_value = self._common_content_lib.get_binary_bit_range(cpuid_edx_binary_value
                                                                              [edx_value],
                                                                              [18])
        if not cpuid_edx_bit18_value:
            raise content_exceptions.TestFail("expected to have bit 18 as 1 but it has: {}".format(
                cpuid_edx_bit18_value))
        self._log.debug("{} binary bit 18 values is : {}".format(cpuid_edx_binary_value[edx_value],
                                                                 cpuid_edx_bit18_value))
        cpuid_ecx_binary_value = self._common_content_lib.convert_hexadecimal([ecx_value])
        cpuid_ecx_bit13_value = self._common_content_lib.get_binary_bit_range(cpuid_ecx_binary_value
                                                                              [ecx_value],
                                                                              [13])
        if not cpuid_ecx_bit13_value:
            raise content_exceptions.TestFail("expected to have bit 13 as 1 but it has: {}".format(
                cpuid_ecx_bit13_value))
        self._log.debug("{} binary bit 13 values is : {}".format(cpuid_ecx_binary_value[ecx_value],
                                                                 cpuid_ecx_bit13_value))
        cpuid_eax_cmd_output = self.execute_cpuid(command=self.CPUID_EAX_CMD)
        if not re.findall(self.REGEX_FOR_CPUID_EAX_VALUE, cpuid_eax_cmd_output):
            raise content_exceptions.TestFail("EAX is Not Set")
        self._log.info("EAX is Set")
        self._test_content_logger.end_step_logger(2, return_val=True)

        self._test_content_logger.start_step_logger(3)
        self._log.info("Enabling TME Bios Knob")
        self.bios_util.set_bios_knob(bios_config_file=self.enable_tme_bios_knob_file)
        self.perform_graceful_g3()
        self._log.info("Verifying bios settings")
        self.bios_util.verify_bios_knob(bios_config_file=self.enable_tme_bios_knob_file)
        self._test_content_logger.end_step_logger(3, return_val=True)
        return True


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MktmeDiscoveryTmeEnumWithCpuid.main() else Framework.TEST_RESULT_FAIL)
