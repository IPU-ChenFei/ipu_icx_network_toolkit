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
import re
import os
import time

from dtaf_core.lib.dtaf_constants import Framework
from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib.content_exceptions import *
from src.provider.vm_provider import VMs
from src.virtualization.virtualization_common import VirtualizationCommon
from src.lib.common_content_lib import CommonContentLib
from src.lib.install_collateral import InstallCollateral
from src.lib.test_content_logger import TestContentLogger

from pathlib import Path
class VirtualizationVmwareVtdPassthroughFunctionality(VirtualizationCommon):
    """
    Phoenix ID: 18014072697
    The objective to this TC is to verify that VT-d (or also knowned as VMdirectPath) functions properly and
    that the virtual machine that is assigned to the device is able to see the device.

    1. Enable VT-d bios on ESXi sut.
    2. Copy Centos ISO image to ESXi SUT under 'vmfs/volumes/datastore1'.
    4. Create VM.
    5. Verify VM is running.
    6. Verify VMware tool installed on VM or not.
    """
    VM = [VMs.WINDOWS]
    VM_TYPE = "WINDOWS"
    # vm_name = "centos"
    PCI_TYPE = "NVMe"


    HOST_IOMETER_PATH = r"C:\Automation\Tools\Esxi\iometer_tool"
    CONFIG_PATH = r"C:\Iometer\iometer_1.icf"
    IO_LOG = r"C:\Iometer\iometer_tool\iometer_result.log"
    IO_RUN_TIME = 10 #7200

    SUT_TOOLS_LINUX_ROOT = SUT_TOOLS_VMWARE_ROOT = '/home/BKCPkg'
    SUT_TOOLS_LINUX_VIRTUALIZATION = SUT_TOOLS_VMWARE_VIRTUALIZATION = f'{SUT_TOOLS_LINUX_ROOT}/domains/virtualization'

    TEST_CASE_ID = ["P18014072697", "Virtualization_VMware_Vtd_Passthrough_functionality_check"]
    STEP_DATA_DICT = {
        1: {'step_details': "Install and verify Bios knobs for VT-d",
            'expected_results': "Bios knobs installed and verified successfully'"},
        2: {'step_details': "Create CentOS VM on ESXi SUT",
            'expected_results': "VM Created Successfully"},
        3: {'step_details': "Verify VMware Tool installed on VM or not",
            'expected_results': "Successfully verified VMware Tool on VM"},
        4: {'step_details': "Shutdown VM",
            'expected_results': "VM shutdown was successful"},
        5: {'step_details': "Passthrough PCI device to the VM and reserve memory",
            'expected_results':"passthrough was successfully done"},
        6: {'step_details': "Enable ssh in VM",
            'expected_results' : "Successfully enabled ssh in VM"},
        7: {'step_details': "Download FIO tool into the VM and run FIO/IO workload in VM",
            'expected_results': "Successfully ran the IO workload on PCI device in VM"},
    }

    def __init__(self, test_log, arguments, cfg_opts):
        """
        Create a new VirtualizationVmwareVtdPassthroughFunctionality object.

        """
        super(VirtualizationVmwareVtdPassthroughFunctionality, self).__init__(test_log, arguments, cfg_opts)
        self._cfg_opts = cfg_opts
        self._log = test_log
        self._test_content_logger = TestContentLogger(self._log, self.TEST_CASE_ID, self.STEP_DATA_DICT)
        self._common_content_lib = CommonContentLib(self._log, self.os, cfg_opts)
        self.collateral_installer = InstallCollateral(self._log, self.os, cfg_opts)

    def prepare(self):
        # Need to implement bios configuration for ESXi SUT
        self._test_content_logger.start_step_logger(1)
        if self.os.os_type != OperatingSystems.ESXI:
            raise TestNotImplementedError("Not implemented for {} OS".format(self.os.os_type))
        self._log.info("VMWare ESXi SUT detected for the testcase")
        self._test_content_logger.end_step_logger(1, return_val=True)

    def execute(self):
        """
        1. create VM.
        2. Start the VM.
        3. Verify VMware tool installed or not on VM.
        """
        self._log.info("Find a PCI device:")
        devs = self._common_content_lib.execute_sut_cmd(f"lspci -vv | grep -i {self.PCI_TYPE}",
                                                        f"lspci -vv | grep -i {self.PCI_TYPE}",
                                                        self._command_timeout)
        self._log.info("{}".format(devs))
        self._log.info(f"pci NVME SSD output results:[{devs}]")
        self._log.info("Active the PCI device:")
        nvme_device_list = self._vm_provider.get_passthrough_device_details(self.PCI_TYPE)


        dev_id = nvme_device_list[0].split(" ")[0]
        out = self._common_content_lib.execute_sut_cmd(f"esxcli hardware pci pcipassthru set -d={dev_id} -e=on  -a", "Executing Passthrough Command",
                                                       execute_timeout=self._command_timeout)
        self._log.info("The device is configured to passthru ")

        vm_sut_obj_list = []
        for index in range(len(self.VM)):
            self._test_content_logger.start_step_logger(2)
            vm_name = self.VM[index] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self._vm_provider.destroy_vm(vm_name)
            self.create_vmware_vm(vm_name, self.VM_TYPE, mac_addr=True, use_powercli="use_powercli")
            self._test_content_logger.end_step_logger(2, return_val=True)
            self._test_content_logger.start_step_logger(3)
            self._vm_provider.install_vmware_tool_on_vm(vm_name)
            self._test_content_logger.end_step_logger(3, return_val=True)
            vm_os_obj = self.create_esxi_vm_host(vm_name, self.VM_TYPE)
            vm_sut_obj_list.append(vm_os_obj)
            common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            self._test_content_logger.start_step_logger(4)

            ##Shutdown the VM
            self.shutdown_vm_esxi(vm_name)
            self._test_content_logger.end_step_logger(4, return_val=True)

            ##############################################

            self._test_content_logger.start_step_logger(5)
            sut_ip = self.get_sut_ip_esxi()
            self._log.info("Get the Passthrough available device list from the host:")
            self.virt_execute_host_cmd_esxi(f'Get-PassthroughDevice -VMHost {sut_ip} | '
                                                        f'Where-Object {{$_.Name -match \\"{self.PCI_TYPE}\\"}}',
                                                        timeout=60 * 3)
            self._log.info("Get the Passthrough devices successful!")

            self._log.info(
                "Get the Passthrough available PCI device list from the host and build PCI device connection to VM:")
            """
                $scsiDeviceList = Get-PassthroughDevice -VMHost <server_ip> -Type Pci
                $scsiDeviceList
            """
            # # out, err = self.virt_execute_host_cmd_esxi(
            # #     f'Get-PassthroughDevice -VM {vm_name} | Remove-PassthroughDevice -confirm:$false')

            self.virt_execute_host_cmd_esxi(f'$scsiDeviceList=Get-PassthroughDevice -VMHost {sut_ip} '
                                                     f'-Type Pci | Where-Object{{$_.Name -match \\"{self.PCI_TYPE}\\"}};'
                                                     f'Add-PassthroughDevice -VM {vm_name} -PassthroughDevice $scsiDeviceList[0];'
                                                     f'echo $scsiDeviceList[0]',
                                                     timeout=60 * 3)
            self._log.info("PCI device connection to VM successful!")

            self._log.info(
                'Centos OS SSD Passthrough requires "Reserve all guest memory"(All Locked), use the command below to select:')
            self.virt_execute_host_cmd_esxi("$spec=New-Object VMware.Vim.VirtualMachineConfigSpec;"
                                                     "$spec.memoryReservationLockedToMax = $true;"
                                                     f"(Get-VM {vm_name}).ExtensionData.ReconfigVM_Task($spec)")
            self._log.info("setting Reserve all guest memory successful!")
            self._log.info("Get the ip of VM and Start Virtual Machine:")
            self.start_vm_esxi(vm_name)

            vm_ip = self.get_vm_ip_esxi(vm_name)
            self._log.info(f"get the vm ip successful [{vm_ip}] ")
            self._test_content_logger.end_step_logger(5, return_val=True)

            self._test_content_logger.start_step_logger(6)
            ####enable ssh in vm
            vm_id = self.get_vm_id_esxi(vm_name)
            self.create_ssh_vm_object(vm_id=vm_id, vm_name=vm_name, copy_open_ssh=True,
                                      common_content_lib_vm_obj=common_content_lib_vm_obj)

            self._log.info("Operate in SSH connect vm and Check the PCI device::")
            cmd_to_get_nvme = 'powershell.exe $progressPreference = "silentlyContinue"; Get-Disk ^| Where-Object IsSystem -eq $False ^| ' \
                              'Where-Object BusType -EQ "{}" ^| Where-Object OperationalStatus -EQ "Online" ^|' \
                              'Select-Object *'
            common_content_lib_vm_obj.execute_sut_cmd(cmd_to_get_nvme.format(self.PCI_TYPE), "get nvme in vm", self._command_timeout)
            self._log.info("PCI devices can be displayed normally")
            self._test_content_logger.end_step_logger(6, return_val=True)

            self._test_content_logger.start_step_logger(7)
            # ###install iometer in windows VM
            iometer_file = self._install_collateral.install_iometer_tool_on_host_esxi(common_content_lib=common_content_lib_vm_obj)
            time.sleep(10)
            self._install_collateral.iometer_reg_add_esxi(common_content_lib=common_content_lib_vm_obj)

            self._log.info("Execute IOMeter tool in VM")
            cmd= "powershell.exe $progressPreference = 'silentlyContinue';" \
                 "$dateTime = (Get-Date).AddSeconds(10).ToString('h:mm:ss tt');" \
                 "$taskAction = New-ScheduledTaskAction -Execute 'powershell.exe' -Argument 'C:\Iometer\iometer_tool\IOmeter.exe /c {} /r {}';" \
                 "$taskTrigger = New-ScheduledTaskTrigger -Once -At $dateTime;" \
                 "$taskName = 'IometerApp';" \
                 "$description = 'Run Io Meter App';" \
                 "Unregister-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue -Confirm:$false;" \
                 "Register-ScheduledTask -TaskName $taskName -Action $taskAction -Trigger $taskTrigger -Description $description -Force;" \
                 "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser "
            common_content_lib_vm_obj.execute_sut_cmd(cmd.format(self.CONFIG_PATH, self.IO_LOG), "IO Workload", self._command_timeout)

            time.sleep(self.IO_RUN_TIME+20)
            vm_os_obj.copy_file_from_sut_to_local(self.IO_LOG, os.path.join(self.log_dir, "IOmeter_log.log"))
            time.sleep(20)
            self._test_content_logger.end_step_logger(7, return_val=True)

        ##############################################
        return True

    def cleanup(self, return_status):  # type: (bool) -> None
        super(VirtualizationVmwareVtdPassthroughFunctionality, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VirtualizationVmwareVtdPassthroughFunctionality.main()
             else Framework.TEST_RESULT_FAIL)
