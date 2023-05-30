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
# treaty provisions. No part of the Material may be used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or disclosed
# in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
##########################################################################
import sys
import os
import time

from dtaf_core.lib.dtaf_constants import Framework
from src.lib.install_collateral import InstallCollateral

from src.lib.common_content_lib import CommonContentLib
from src.ras.lib.ras_upi_util import RasUpiUtil
from src.ras.lib.ras_einj_common import RasEinjCommon
from src.provider.vm_provider import VMs
from src.ras.tests.io_virtualization.io_virtualization_common import IoVirtualizationCommon
from src.lib import content_exceptions


class VmmUceErrorsAndVmsUnderLoadLinux(IoVirtualizationCommon):
    """
    While running stress on multiple VMs, Inject UCE errors via EINJ into VMM host.
    Glossgow: G68714
    """

    BIOS_CONFIG_FILE = "uce_error_bios_knobs.cfg"

    VM = [VMs.RHEL]

    def __init__(
            self,
            test_log,
            arguments,
            cfg_opts
    ):
        """
        Create an instance of VmmUceErrorsAndVmsUnderLoadLinux

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        """
        bios_config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), self.BIOS_CONFIG_FILE)
        super(
            VmmUceErrorsAndVmsUnderLoadLinux,
            self).__init__(
            test_log,
            arguments,
            cfg_opts, bios_config_file=bios_config_file)
        self._ras_einj_util = RasEinjCommon(self._log, self.os, self._common_content_lib,
                              self._common_content_configuration, self.ac_power, cfg_opts)
        self.memory_address = [0x12345200, 0x12345100, 0x12345300]

    def prepare(self):  # type: () -> None
        """
        This method is to execute prepare.
        """
        super(VmmUceErrorsAndVmsUnderLoadLinux, self).prepare()

    def execute(self):  # type: () -> bool
        """
        This method is to
        1. Create VM
        2. Verify VM
        3. Inject memory uncorrectable non fatal error
        4. Verify error in OS log
        5. Verify VM

        """
        crunch_stess_tool_ramp_up_time_in_sec = 300
        log_check_wait_timer_in_sec = 10
        for index in range(self.num_vms):
            #  Create VM names dynamically according to the OS
            vm_name = self.VM[0] + "_" + str(index)

            self.create_and_verify_vm(vm_name, self.VM[0], crunch_tool=True, enable_yum_repo=True)

        time.sleep(crunch_stess_tool_ramp_up_time_in_sec)
        for mem_address in self.memory_address:
            self._common_content_lib.clear_all_os_error_logs()
            self._log.info("Loading EINJ module on SUT")
            self._common_content_lib.execute_sut_cmd("modprobe einj", "install einj", self._command_timeout)
            self._log.info("Injecting Einj at memory address - {}".format(mem_address))
            ret_val = self._ras_einj_util.einj_inject_error(self._ras_einj_util.EINJ_MEM_UNCORRECTABLE_NONFATAL, mem_address, viral=True)
            if not ret_val:
                raise content_exceptions.TestFail("Failed to inject memory error")
            time.sleep(log_check_wait_timer_in_sec)
            if not self._ras_einj_util.einj_check_os_log(self._ras_einj_util.EINJ_MEM_UNCORRECTABLE_NONFATAL):
                raise content_exceptions.TestFail("Fail to get the expected error message at OS logs")

        self._log.info("Verification of VM status after error injection")
        for index in range(self.num_vms):
            vm_name = self.VM[0] + "_" + str(index)
            self.virtualization_obj.verify_vm_functionality(vm_name, self.VM[0])

        return True

    def cleanup(self, return_status):
        for index in range(self.num_vms):
            vm_name = self.VM[0] + "_" + str(index)
            self._vm_provider_obj.destroy_vm(vm_name)
        super(VmmUceErrorsAndVmsUnderLoadLinux, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VmmUceErrorsAndVmsUnderLoadLinux.main()
             else Framework.TEST_RESULT_FAIL)
