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
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider

from src.provider.vm_provider import VMs
from src.ras.tests.io_virtualization.io_virtualization_common import IoVirtualizationCommon
from src.virtualization.virtualization_common import VirtualizationCommon
from src.ras.lib.ras_upi_util import RasUpiUtil
from src.lib import content_exceptions
from src.lib.dtaf_content_constants import TimeConstants


class UpiCrcCeInjectionFor1GuestOsWithVmCpuWorkloads(IoVirtualizationCommon):
    """
    GLASGOW ID: G66254

    While running stress on one(1) VM, Inject CRC errors into the host server (socket 0 and 1)

    Verify VM is still functional
    """
    VM = [VMs.RHEL]
    VM_NAME = None
    BIOS_CONFIG_FILE = "upi_crc_error_injection_bios_config_file.cfg"
    TEST_CASE_ID = ["G66254", "UPI_CRC_CE_injection_for_1_Guest_OS_with_VM_CPU_workloads"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new UpiCrcCeInjectionFor1GuestOsWithVmCpuWorkloads object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(
            __file__)), self.BIOS_CONFIG_FILE)
        super(UpiCrcCeInjectionFor1GuestOsWithVmCpuWorkloads, self).__init__(test_log, arguments, cfg_opts,
                                                                             bios_config_file
                                                                             )
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.virtualization_obj = VirtualizationCommon(self._log, arguments, cfg_opts)
        
    def prepare(self):  # type: () -> None
        """
        To Setup prepare
        """
        super(UpiCrcCeInjectionFor1GuestOsWithVmCpuWorkloads, self).prepare()

    def execute(self):
        """
        1. Check CRC CE Error
        2. create VM
        3. check VM is functioning or not
        4. Run crunch stress tool on VM.
        5. Inject CRC CE Error
        6. Check VM still working or not.

        :raise : content_exceptions.TestFail
        :return : True on Success
        """
        index = 0
        ras_util_obj = RasUpiUtil(self.os, self._log, self._cfg, self._common_content_lib, self.args)
        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)

        #  Before test start kti crc err count should be equal to 0x0 as we have not injected error.
        #  If SUT has unexpected kti crc error count, we should Apply AC cycle and re-run TC.
        if not ras_util_obj.inject_and_check_kti_crc_err_cnt(csp=cscripts_obj, num_crcs_value=0x0):
            raise content_exceptions.TestFail("Please Apply AC cycle to clear CRC error")

        #  Create VM names dynamically according to the OS
        self.VM_NAME = self.VM[index] + "_" + str(index)

        vm_os_obj = self.create_and_verify_vm(vm_name=self.VM_NAME, vm_type=self.VM[index], crunch_tool=True,
                                              enable_yum_repo=True)

        #  Inject CRC CE to num_crc value = 40 and check crc error count should update to 40(Dec) or 0x28(Hex).
        if not ras_util_obj.inject_and_check_kti_crc_err_cnt(csp=cscripts_obj, num_crcs_value=0x28, inject_error=True):
            raise content_exceptions.TestFail("Unexpected CRC error count was captured")
        import time
        time.sleep(TimeConstants.ONE_MIN_IN_SEC)
        sut_cmd_result = vm_os_obj.execute("ifconfig", self._command_timeout)
        if sut_cmd_result.cmd_failed():
            raise content_exceptions.TestFail("VM is not alive after CRC CE Injection")
        else:
            self._log.debug(sut_cmd_result.stdout)
        self._log.info("VM is alive after CRC CE Injection as expected")

        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        """
        Test Cleanup
        1. Destroy Created VM.
        """
        try:
            self.virtualization_obj.vm_provider.destroy_vm(self.VM_NAME)
        except Exception as ex:
            raise content_exceptions.TestFail("Unable to Destroy the VM")
        super(UpiCrcCeInjectionFor1GuestOsWithVmCpuWorkloads, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if UpiCrcCeInjectionFor1GuestOsWithVmCpuWorkloads.main()
             else Framework.TEST_RESULT_FAIL)
