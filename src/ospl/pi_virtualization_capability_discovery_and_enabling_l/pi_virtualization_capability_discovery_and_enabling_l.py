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
import re
import sys
import six
if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.silicon import CPUID
from dtaf_core.lib.dtaf_constants import OperatingSystems


from src.lib.content_exceptions import *
from src.virtualization.virtualization_common import VirtualizationCommon
from src.security.tests.dsa.dsa_common import DsaBaseTest


class PiVirtualizationCapabilityDiscoveryAndEnablingL(VirtualizationCommon):
    """
    HPALM ID: 79628 -  PI_Virtualization_CapabilityDiscoveryandEnabling_L
    The purpose of this test case is making sure the creation of VMs guests on KVM using Virt-Manager.
    1. VT-x capability presence in CPUID.
    2. If x2APIC CPU capability is enabled.
    """
    TC_ID = ["H79628", "PI_Virtualization_Capability_Discovery_and_Enabling_L"]
    __BIOS_CONFIG_FILE = "pi_virtualization_capability_discovery_and_enabling_l.cfg"
    VIRT_HOST_VALIDATE_CMD = "virt-host-validate"
    GET_SUT_THREAD_CORE_NO_CMD = "cat /proc/cpuinfo | grep processor | wc -l"
    GET_CORE_CPUID_CMD = "cpuid  | egrep --color -iw 'vmx' | wc -l"
    DMSG_DMAR_IOMMU_DATA_CMD = "dmesg | grep -i DMAR | grep -i IOMMU"
    GET_X2APIC_CMD = "journalctl | grep -i x2apic"
    ACPI_DMAR_SEARCH_STRINGS = ["[DMA Remapping table]", "[IOAPIC Device]", "Raw Table Data: Length"]
    X2APIC_MODE = "DMAR-IR: Enabled IRQ remapping in x2apic mode"
    X2APIC_ENABLE = "x2apic enabled"
    ACPI_SEARCH_REGEX = "DMAR-IR: IOAPIC id(.*)IOMMU"
    VIRT_HOST_VALIDATE_STRING_LIST = ["PASS"]
    HEX_ONE = 0x1
    EXPECTED_DATA = ["QEMU: Checking for hardware virtualization", "QEMU: Checking if device /dev/kvm exists",
                     "QEMU: Checking if device /dev/kvm is accessible",
                     "QEMU: Checking if device /dev/vhost-net exists",
                     "QEMU: Checking if device /dev/net/tun exists",
                     "QEMU: Checking for cgroup 'cpu' controller support",
                     "QEMU: Checking for cgroup 'cpuacct' controller support",
                     "QEMU: Checking for cgroup 'cpuset' controller support",
                     "QEMU: Checking for cgroup 'memory' controller support",
                     "QEMU: Checking for cgroup 'devices' controller support",
                     "QEMU: Checking for cgroup 'blkio' controller support",
                     "QEMU: Checking for device assignment IOMMU support",
                     "QEMU: Checking if IOMMU is enabled by kernel"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new PiVirtualizationCapabilityDiscoveryAndEnablingL object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        self.bios_file_path = os.path.join(Path(os.path.dirname(os.path.abspath(__file__))), self.__BIOS_CONFIG_FILE)
        # calling base class init
        super(PiVirtualizationCapabilityDiscoveryAndEnablingL, self).__init__(test_log, arguments, cfg_opts,
                                                                              create_bridge=False)
        if self.os.os_type != OperatingSystems.LINUX:
            raise TestNotImplementedError("Not implemented for {} OS".format(self.os.os_type))
        self._grubby = DsaBaseTest(test_log, arguments, cfg_opts)

    def prepare(self):
        self.bios_util.load_bios_defaults()
        self.bios_util.set_bios_knob(bios_config_file=self.bios_file_path)
        self._common_content_lib.perform_os_reboot(self.reboot_timeout)
        self.bios_util.verify_bios_knob(bios_config_file=self.bios_file_path)
        self._install_collateral.install_cpuid()
        self._common_content_lib.update_micro_code()

    def execute(self):
        """
        1. VT-x capability presence in CPUID.
        2. If x2APIC CPU capability is enabled.
        """
        # To check and enable intel_iommu by using grub menu
        self._grubby.enable_intel_iommu_by_kernel()
        error_list = []
        # run virt-host-validate command
        cmd_result = self.os.execute(self.VIRT_HOST_VALIDATE_CMD, self._command_timeout, cwd=self.ROOT_PATH)
        self._log.debug("{} command stdout:\n{}".format(self.VIRT_HOST_VALIDATE_CMD, cmd_result.stdout))
        self._log.error("{} command stderr:\n{}".format(self.VIRT_HOST_VALIDATE_CMD, cmd_result.stderr))

        for each_line in cmd_result.stdout.strip().split("\n"):
            each_line = each_line.split("  :")
            if not (each_line[0].strip() in self.EXPECTED_DATA) and \
                    (each_line[1].strip() in self.VIRT_HOST_VALIDATE_STRING_LIST):
                error_list.append("Failure or Warning is present in output:\n{}".format(each_line))
        self._log.error("Error List : {}".format(error_list))

        # get the SUT thread core number
        core_count = self._common_content_lib.get_core_count_from_os()[0]
        core_cmd_result = self._common_content_lib.execute_sut_cmd(self.GET_SUT_THREAD_CORE_NO_CMD, "get SUT thread "
                                                                   "core no", self._command_timeout)
        self._log.debug("{} command stdout:\n{}".format(self.GET_SUT_THREAD_CORE_NO_CMD, core_cmd_result))
        if core_count != int(core_cmd_result.strip()):
            error_list.append("Actual core count is not matching with the Expected one")
        # check the output number, it should match with the core number
        core_cpuid_result = self._common_content_lib.execute_sut_cmd(self.GET_CORE_CPUID_CMD, "get SUT thread "
                                                                     "core no by cpuid", self._command_timeout)
        self._log.debug("{} command stdout:\n{}".format(self.GET_CORE_CPUID_CMD, core_cpuid_result))
        if core_cpuid_result != core_cmd_result:
            raise TestFail("All cores are not VMX enabled")

        dmsg_dmar_data_result = self._common_content_lib.execute_sut_cmd(self.DMSG_DMAR_IOMMU_DATA_CMD,
                                                                         "run {} command".
                                                                         format(self.DMSG_DMAR_IOMMU_DATA_CMD),
                                                                         self._command_timeout)
        self._log.debug("{} command stdout:\n{}".format(self.DMSG_DMAR_IOMMU_DATA_CMD, dmsg_dmar_data_result))
        if not re.search(self.ACPI_SEARCH_REGEX, dmsg_dmar_data_result):
            error_list.append("APIC device is not listed in dmesg data")

        get_x2apic_cmd_result = self._common_content_lib.execute_sut_cmd(
            self.GET_X2APIC_CMD, "run {} command".format(self.GET_X2APIC_CMD), self._command_timeout)
        self._log.debug("{} command stdout:\n{}".format(self.GET_X2APIC_CMD, get_x2apic_cmd_result))

        if self.X2APIC_MODE not in get_x2apic_cmd_result and self.X2APIC_ENABLE not in get_x2apic_cmd_result:
            error_list.append("x2APIC CPU capability is not enabled")

        if error_list:
            raise TestFail("\n".join(error_list))
        self._log.info("Successfully verified Virtulization Capabilities")
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(PiVirtualizationCapabilityDiscoveryAndEnablingL, self).cleanup(return_status)
        if self.os.is_alive():
            self._common_content_lib.delete_micro_code()
            self._common_content_lib.perform_os_reboot(self.reboot_timeout)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if PiVirtualizationCapabilityDiscoveryAndEnablingL.main()
             else Framework.TEST_RESULT_FAIL)
