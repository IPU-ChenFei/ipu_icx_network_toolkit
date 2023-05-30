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

from dtaf_core.lib.dtaf_constants import Framework, ProductFamilies
from dtaf_core.providers.provider_factory import ProviderFactory
from src.lib import content_exceptions

from src.lib.install_collateral import InstallCollateral

from src.ras.tests.io_virtualization.pass_through_base_test import PciPassThroughBaseTest


class VirtualizationHyperVNVMePassthroughAndPerformDegrade(PciPassThroughBaseTest):
    """
    This test case is to pass the NVMe to VM (VT-d) and perform degrade test.
    """

    bios_config_file = "vtd_bios_knobs.cfg"

    def __init__(
            self,
            test_log,
            arguments,
            cfg_opts
    ):
        """
        Create an instance of VirtualizationHyperVNVMePassthroughAndPerformDegrade

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(
            VirtualizationHyperVNVMePassthroughAndPerformDegrade,
            self).__init__(
            test_log,
            arguments,
            cfg_opts, bios_config_file=self.bios_config_file)
        self.cfg_opts = cfg_opts

    def prepare(self):  # type: () -> None
        """
        execute the prepare.
        """
        super(VirtualizationHyperVNVMePassthroughAndPerformDegrade, self).prepare()

    def execute(self):  # type: () -> bool
        """
        execute the test steps.
        """
        super(VirtualizationHyperVNVMePassthroughAndPerformDegrade, self).execute()
        index = 0
        vm_name = self.VM_OS[0] + "_" + str(index)

        import time
        time.sleep(self.WAIT_TIME)

        vm_os_obj = self.virtualization_obj.windows_vm_object(vm_name=vm_name, vm_type="RS5")

        tool_path = self.install_disk_spd_tool_on_vm(vm_os_obj)

        drive_created_output = vm_os_obj.execute(
            "powershell.exe New-Partition -DiskNumber 1 -UseMaximumSize -DriveLetter E ^| "
            "Format-Volume -FileSystem NTFS", self._command_timeout)

        if drive_created_output.cmd_failed():
            drive_created_output = vm_os_obj.execute(
                "powershell.exe Get-Partition -DiskNumber 1 ^| Set-Partition -NewDriveLetter E", self._command_timeout)

        self._log.error(drive_created_output.stderr)

        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        sdp = ProviderFactory.create(self.si_dbg_cfg, self._log)

        socket = self._common_content_configuration.get_pcie_device_socket_to_degrade()
        port = self._common_content_configuration.get_pcie_device_pxp_port_to_degrade()

        self._log.info("Degrade the NVMe speed to Gen4")
        self.degrade_nvme_gen_speed(cscripts_obj, sdp, socket, port, gen=4)

        gen_4_read_speed, gen_4_write_speed = self.get_read_write_speed(vm_os_obj, tool_path)

        self._log.info("Degrade the NVMe Speed to gen 1")
        self.degrade_nvme_gen_speed(cscripts_obj, sdp, socket, port, gen=1)

        gen_1_read_speed, gen_1_write_speed = self.get_read_write_speed(vm_os_obj, tool_path)

        if not (gen_4_read_speed > gen_1_read_speed and gen_4_write_speed > gen_1_write_speed):
            self._log.error("Gen 4 Sequential Read and Write Operation Speed are - {} and {}".format(gen_4_read_speed,
                                                                                gen_4_write_speed))
            self._log.error("Gen 1 Sequential Read and Write Operation Speed are - {} and {}".format(gen_1_read_speed,
                                                                                gen_1_write_speed))
            raise content_exceptions.TestFail("Read-Write Operation speed found unexpected...")

        self._log.info("Sequential read-write operation speed found as expected after degrading to gen 1")

        self._log.info("Degrading the NVMe speed to Gen 4 again")
        self.degrade_nvme_gen_speed(cscripts_obj, sdp, socket, port, gen=4)

        gen_4_read_speed, gen_4_write_speed = self.get_read_write_speed(vm_os_obj, tool_path)

        if not (gen_4_read_speed > gen_1_read_speed and gen_4_write_speed > gen_1_write_speed):
            self._log.error("Gen 4 Sequential Read and Write Operation Speed are - {} and {}".format(gen_4_read_speed,
                                                                                gen_4_write_speed))
            self._log.error("Gen 1 Sequential Read and Write Operation Speed are - {} and {}".format(gen_1_read_speed,
                                                                                gen_1_write_speed))
            raise content_exceptions.TestFail("Read-Write Operation speed found unexpected...")

        self._log.info("Sequential read-write operation speed found as expected after degrading to gen 4")
        return True

    def cleanup(self, return_status):
        """
        execute the cleanup.
        """
        super(VirtualizationHyperVNVMePassthroughAndPerformDegrade, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationHyperVNVMePassthroughAndPerformDegrade.main()
             else Framework.TEST_RESULT_FAIL)
