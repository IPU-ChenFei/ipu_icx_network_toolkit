#!/usr/bin/env python
##########################################################################
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and
# proprietary and confidential information of Intel Corporation and its
# suppliers and licensors, and is protected by worldwide copyright and trade
# secret laws and treaty provisions. No part of the Material may be used,copied,
# reproduced, modified, published, uploaded, posted, transmitted, distributed,
# or disclosed in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
##########################################################################

import os
import sys

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.providers.provider_factory import ProviderFactory

from src.lib.test_content_logger import TestContentLogger
from src.lib import content_exceptions
from src.security.tests.mktme.mktme_common import MktmeBaseTest
from src.provider.rdmsr_and_cpuid_provider import RdmsrAndCpuidProvider
from src.lib.common_content_lib import CommonContentLib


class MktmeDiscoveryMsrsUsingRdMsr(MktmeBaseTest):
    """
    HPALM ID = "H79554 - PI_Security_MKTME_Discovery_MSRs"
    Phoneix ID = P18014074689 PI_Security_MKTME_Discovery_MSRs
    This Test case is,
    Verify the presence of the following TME MSRs:
    IA32_TME_CAPABILITY (981H)
    IA32_TME_ACTIVATE (982H)
    IA32_TME_EXCLUDE_MASK (983H)
    IA32_TME_EXCLUDE_BASE (984H)
    """
    BIOS_CONFIG_FILE = "../security_tme_mktme_bios_enable.cfg"
    TEST_CASE_ID = ["H79554", "PI_Security_MKTME_Discovery_MSRs", "P18014074689", "PI_Security_MKTME_Discovery_MSRs"]
    STEP_DATA_DICT = {1: {'step_details': 'Verify if CPU SKU Supports MKTME',
                          'expected_results': 'CPU SKU Supports MKTME'},
                      2: {'step_details': 'Enable TME and MKTME Bios Knobs',
                          'expected_results': 'Verify TME and MKTME Bios Knobs are set'},
                      3: {'step_details': 'Checking Msr values of TME and MkTme',
                          'expected_results': 'Verify TME and MkTme Msr Values are same as Expected'}}

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create instance of MktmeDiscoveryMsrsUsingRdMsr

        :param cfg_opts: Configuration Object of provider
        :param test_log: Log object
        :param arguments: None
        """
        self.tme_mktme_bios_enable = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(MktmeDiscoveryMsrsUsingRdMsr, self).__init__(test_log, arguments, cfg_opts,
                                                           self.tme_mktme_bios_enable)
        self._test_content_logger = TestContentLogger(test_log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._rdmsr_and_cpuid_obj = RdmsrAndCpuidProvider.factory(self._log, self.os, cfg_opts)
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)

    def prepare(self):
        # type: () -> None
        """
        This Method is Used to Verify CPU Sku Supports MKTME and Enable TME and MK-TME Bios knobs.

        :raise TestSetupError if Cpu Sku Doesn't Support MKTME.
        """
        self._test_content_logger.start_step_logger(1)
        # Verify platform Supports MKTME by using ITP Commands
        if not self.verify_mktme():
            raise content_exceptions.TestSetupError("This CPU SKU does not support for MK-TME")
        self._log.info("SUT supports MK-TME Bios Knob")
        self._test_content_logger.end_step_logger(1, return_val=True)

        self._test_content_logger.start_step_logger(2)
        super(MktmeDiscoveryMsrsUsingRdMsr, self).prepare()
        self._test_content_logger.end_step_logger(2, return_val=True)

    def execute(self):
        """
        check the TME and MK-TME MSR Values.

        :return True if Msr Values are as Expected else false
        """
        self._test_content_logger.start_step_logger(3)
        sdp_obj = ProviderFactory.create(self.si_dbg_cfg, self._log)
        itp_connected = self._common_content_lib.is_itp_connected(sdp_obj)
        if itp_connected:
            self._log.info("ITP connected")
            self.verify_rdmsr_with_itp()
        else:
            self.verify_rdmsr_with_tool()

        self._test_content_logger.end_step_logger(3, return_val=True)

        return True

    def verify_rdmsr_with_tool(self):
        """
        This function is used to verify msr value for the address 0x981, 0x982, 0x983, 0x984 by by using msr tool.

        """
        self._log.info("Installing msr tool ...")
        self._rdmsr_and_cpuid_obj.install_msr_tools()

        # execute rdmsr command for register 0x981
        rdmsr_cmd_output = self._rdmsr_and_cpuid_obj.execute_rdmsr_command(self.RDMSR_COMMAND.format(hex(
            self.MSR_TME_CAPABILITY_ADDRESS)))
        self.verify_rdmsr_output(hex(self.MSR_TME_CAPABILITY_ADDRESS), hex(self.MSR_TME_CAPABILITY_VALUE),
                                 rdmsr_cmd_output)

        # execute rdmsr command for register 0x982
        rdmsr_cmd_output = self._rdmsr_and_cpuid_obj.execute_rdmsr_command(self.RDMSR_COMMAND.format(hex(
            self.MSR_TME_ADDRESS)))
        self.verify_rdmsr_output(hex(self.MSR_TME_ADDRESS), hex(self.ENABLE_TME_MSR_VALUE),
                                 rdmsr_cmd_output)

        # execute rdmsr command for register 0x983
        rdmsr_cmd_output = self._rdmsr_and_cpuid_obj.execute_rdmsr_command(self.RDMSR_COMMAND.format(hex(
            self.MSR_TME_EXCLUDE_MASK_ADDRESS)))
        self.verify_rdmsr_output(hex(self.MSR_TME_EXCLUDE_MASK_ADDRESS), hex(self.MSR_TME_EXCLUDE_MASK_VALUE),
                                 rdmsr_cmd_output)

        # execute rdmsr command for register 0x984
        rdmsr_cmd_output = self._rdmsr_and_cpuid_obj.execute_rdmsr_command(self.RDMSR_COMMAND.format(hex(
            self.MSR_TME_EXCLUDE_BASE_ADDRESS)))
        self.verify_rdmsr_output(hex(self.MSR_TME_EXCLUDE_BASE_ADDRESS), hex(self.MSR_TME_EXCLUDE_BASE_VALUE),
                                 rdmsr_cmd_output)

    def verify_rdmsr_with_itp(self):
        """"
        This function is used to verify msr value for the address 0x981, 0x982, 0x983, 0x984 by using ITP commands.

        """
        # Check the msr value of 0x981 using ITP
        self.msr_read_and_verify(self.MSR_TME_CAPABILITY_ADDRESS, self.MSR_TME_CAPABILITY_VALUE)
        # Check the msr value of 0x982 using ITP
        self.msr_read_and_verify(self.MSR_TME_ADDRESS, self.ENABLE_TME_MSR_VALUE)
        # Check the msr value of 0x983 using ITP
        self.msr_read_and_verify(self.MSR_TME_EXCLUDE_MASK_ADDRESS, self.MSR_TME_EXCLUDE_MASK_VALUE)
        # Check the msr value of 0x984 using ITP
        self.msr_read_and_verify(self.MSR_TME_EXCLUDE_BASE_ADDRESS, self.MSR_TME_EXCLUDE_BASE_VALUE)
        # Step logger end for Step 3


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if MktmeDiscoveryMsrsUsingRdMsr.main() else Framework.TEST_RESULT_FAIL)
