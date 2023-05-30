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

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems
from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.content_exceptions import *
from src.lib.install_collateral import InstallCollateral


class PiVirtualizationVTXEnablingL(ContentBaseTestCase):
    """
    HPALM ID: 79625
    The purpose of this test case is to install msr-tools and busybox tools check commands values

    """
    TEST_CASE_ID = ["H79625"]
    MSR_TOOLS = "msr-tools"
    BIOS_CONFIG_FILE = "virtualization_vt_x_enabling_bios_knobs.cfg"
    RDMSR_0X3A = "rdmsr -x  0x3a"
    RDMSR_0X1B = "rdmsr -x  0x1B"
    JOURNALCTL = "journalctl | grep -i x2apic"
    X2APIC_MODE = "DMAR-IR: Enabled IRQ remapping in x2apic mode"
    X2APIC_ENABLE = "x2apic enabled"

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiVirtualizationVTXEnablingL object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        self.bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(PiVirtualizationVTXEnablingL, self).__init__(test_log, arguments, cfg_opts, self.bios_config_file)
        if self.os.os_type != OperatingSystems.LINUX:
            raise TestNotImplementedError("Not implemented for {} OS".format(self.os.os_type))
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)

    def prepare(self):  # type: () -> None

        super(PiVirtualizationVTXEnablingL, self).prepare()
        self._common_content_lib.update_micro_code()

    def execute(self):
        """
        This method install msr-tools and busybox tools check commands values
        """
        # Install msr-tools
        self._install_collateral.yum_install(self.MSR_TOOLS)
        
        # Get rdmsr -x  0x3a convert into binary and check bit 1 value
        rdmsr_0x3a_result = self._common_content_lib.execute_sut_cmd(self.RDMSR_0X3A, self.RDMSR_0X3A,
                                                                     self._command_timeout)
        self._log.debug("{} command result:{}".format(self.RDMSR_0X3A, rdmsr_0x3a_result.strip()))
        self._log.info("Converting {} into binary value".format(rdmsr_0x3a_result.strip()))
        rdmsr_0x3a_binary_value = self._common_content_lib.convert_hexadecimal([rdmsr_0x3a_result.strip()])
        rdmsr_0x3a_binary_bit1_value = self._common_content_lib.get_binary_bit_range(rdmsr_0x3a_binary_value
                                                                                     [rdmsr_0x3a_result.strip()],
                                                                                     [1, 1])
        if rdmsr_0x3a_binary_bit1_value != str(1):
            raise TestError("expected to have bit 1 as 1 but it has: {}".format(rdmsr_0x3a_binary_bit1_value))
        self._log.info("{} binary bit 1 values is :{}".format(rdmsr_0x3a_binary_value[rdmsr_0x3a_result.strip()],
                                                              rdmsr_0x3a_binary_bit1_value))

        # Get rdmsr -x  0x1B convert into binary and check bit 10 value
        rdmsr_0x1b_result = self._common_content_lib.execute_sut_cmd(self.RDMSR_0X1B, self.RDMSR_0X1B,
                                                                     self._command_timeout)
        self._log.debug("{} command result:{}".format(self.RDMSR_0X1B, rdmsr_0x1b_result.strip()))
        self._log.info("Converting {} into binary value".format(rdmsr_0x1b_result.strip()))
        rdmsr_0x1b_binary_value = self._common_content_lib.convert_hexadecimal([rdmsr_0x1b_result.strip()])
        rdmsr_0x1b_binary_bit10_value = self._common_content_lib.get_binary_bit_range(rdmsr_0x1b_binary_value
                                                                                      [rdmsr_0x1b_result.strip()],
                                                                                      [10, 10])
        if rdmsr_0x1b_binary_bit10_value != str(1):
            raise TestError("expected to have bit 10 as 1 but it has: {}".format(rdmsr_0x1b_binary_bit10_value))
        self._log.info("{} binary bit 10 values is :{}".format(rdmsr_0x1b_binary_value[rdmsr_0x1b_result.strip()],
                                                               rdmsr_0x1b_binary_bit10_value))

        # Check x2apic mode and x3apic enable in journalctl | grep -i x2apic
        journalctl_cmd_result = self._common_content_lib.execute_sut_cmd(self.JOURNALCTL, self.JOURNALCTL,
                                                                         self._command_timeout)
        self._log.debug("{} command result:\n{}".format(self.JOURNALCTL, journalctl_cmd_result))
        if self.X2APIC_MODE not in journalctl_cmd_result and self.X2APIC_ENABLE not in journalctl_cmd_result:
            raise TestError("{} is not availale in {}".format(self.X2APIC_MODE, self.JOURNALCTL))

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(PiVirtualizationVTXEnablingL, self).cleanup(return_status)
        if self.os.is_alive():
            self._common_content_lib.delete_micro_code()
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiVirtualizationVTXEnablingL.main()
             else Framework.TEST_RESULT_FAIL)
