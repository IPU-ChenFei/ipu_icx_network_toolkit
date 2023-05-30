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
from src.virtualization.virtualization_common import VirtualizationCommon
from src.ras.tests.viral.viral_common import ViralCommon
from src.ras.tests.io_virtualization.io_virtualization_common import IoVirtualizationCommon
from src.lib import content_exceptions


class UpiLlrFatalViral1GuestOsWithVmCpuWorkloads(ViralCommon):
    """
    GLASGOW ID: G69436
    UPI uncorrectable CRC error


    Test case flow:
    Clear registers with AC cycle
    Setup bios
    Verify Viral is enabled
    Start/verify 1 guest OS Vm is runing with stress(crunch)
    Injects continuous CRC errors to cause a uncorr condition to occur
    Verify OS has hung (fatal )
    verify Viral status bits are set as expected after a uncorrected UPI event
    Reset target
    Verify OS is up and ready

    Verify viral is still enabled
    """
    VM = [VMs.RHEL]
    VM_NAME = None
    BIOS_CONFIG_FILE = "upi_llr_fatal_viral_bios_knob.cfg"
    TEST_CASE_ID = ["G69436", "UPI_LLR_Fatal_Viral_1_Guest_OS_with_VM_CPU_workloads"]

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new UpiLlrFatalViral1GuestOsWithVmCpuWorkloads object.

        :param test_log: Used for debug and info messages
        :param cfg_opts: xml.etree.ElementTree.Element of configuration options for execution environment.
        :return: None
        :raises: None
        """
        # calling base class init
        super(UpiLlrFatalViral1GuestOsWithVmCpuWorkloads, self).__init__(test_log, arguments, cfg_opts,
                                                                             config=self.BIOS_CONFIG_FILE
                                                                             )
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.virtualization_obj = VirtualizationCommon(self._log, arguments, cfg_opts)
        self._io_vm_common_obj = IoVirtualizationCommon(self._log, arguments, cfg_opts)

    def prepare(self):  # type: () -> None
        super(UpiLlrFatalViral1GuestOsWithVmCpuWorkloads, self).prepare()

    def execute(self):
        """
        1. create VM
        2. check VM is functioning or not
        3. Verify Viral Signalling is enable.
        4. Run crunch stress tool on VM.
        5. Inject Fatal Error
        6. Verify Viral Signaling Status bit.
        7. Check SUT is Hung or not.
        8. Apply reboot
        9. Check Signalling is enable or not.

        :raise : content_exceptions.TestFail
        :return : True on Success
        """
        index = 0
        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        sdp_obj = ProviderFactory.create(self.si_dbg_cfg, self._log)
        ei_obj = cscripts_obj.get_cscripts_utils().get_ei_obj()
        #  Create VM names dynamically according to the OS
        self.VM_NAME = self.VM[index] + "_" + str(index)

        #  Create VM, Verify VM with crunch Tool Execution
        self._io_vm_common_obj.create_and_verify_vm(self.VM_NAME, self.VM[index], crunch_tool=True,
                                                    enable_yum_repo=True)

        # Verify Viral Signaling is Enabled
        self.check_upi_viral_signaling_enabled(csp=cscripts_obj)

        # Inject Error
        self._log.info("Inject Error")
        ei_obj.injectUpiError(socket=0, port=0, num_crcs=0, stopInj=True)

        # Verify Viral Signaling Status bit
        self.verify_upi_viral_state_and_status_bit(csp=cscripts_obj)

        # Check SUT is Hang or not
        if self.os.is_alive():
           raise content_exceptions.TestFail("SUT is alive after injecting error")
        self._log.info("OS got Hung as Expected")

        # Apply reboot
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        self.os.wait_for_os(self.reboot_timeout)

        # Verify Viral signaling Still enabled
        self.check_upi_viral_signaling_enabled(csp=cscripts_obj)

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
        super(UpiLlrFatalViral1GuestOsWithVmCpuWorkloads, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if UpiLlrFatalViral1GuestOsWithVmCpuWorkloads.main()
             else Framework.TEST_RESULT_FAIL)
