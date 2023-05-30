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
import os
import re
import sys
import time

from dtaf_core.lib.dtaf_constants import OperatingSystems, Framework
from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider
from src.ras.lib.ras_common_utils import RasCommonUtil

from src.lib.dtaf_content_constants import ErrorTypeAttribute
from src.lib.install_collateral import InstallCollateral

from src.provider.vm_provider import VMProvider, VMs
from src.ras.tests.io_virtualization.io_virtualization_common import IoVirtualizationCommon

from src.virtualization.virtualization_common import VirtualizationCommon

from src.lib import content_exceptions
from src.ras.lib.os_log_verification import OsLogVerifyCommon
from src.lib.common_content_lib import CommonContentLib


class VmmCscriptsPcieErrorInjectionBaseTest(IoVirtualizationCommon):
    """
    This Class is Used as Common Class For CscriptsPcieErrorInjection
    """

    VM_OS = []
    VM_NAME = None
    FUNCTIONALITY_TEST_CYCLE = 1
    LIST_OF_VM_NAMES = []
    VM_TYPE = "RS5"
    NETWORK_ASSIGNMENT_TYPE = "DDA"
    VSWITCH_NAME = "ExternalSwitch"
    ADAPTER_NAME = None
    LOG_WAIT_CHECK_TIMER_IN_SEC = 150
    ERROR_INJECT_WAIT_TIME_SEC = 90
    NUMBER_OF_VMS = 1
    MEM_10_GB = 10240
    NUM_OF_INJECTIONS = 30
    SET_VM_MEMORY_CMD = "powershell.exe Set-VMMemory {} -StartupBytes {}MB"
    SET_VM_PROCESSOR_CMD = "powershell.exe Set-VMProcessor {} -Count {}"
    STRESS_COMMAND_DICT = {"prime95": "prime95.exe -t"}

    ERR_SIG = {
        OperatingSystems.LINUX: {
                ErrorTypeAttribute.UNC_NON_FATAL: ["section_type: PCIe error", "event severity: fatal", "Hardware error"],
                ErrorTypeAttribute.UNC_FATAL: ["section_type: PCIe error", "event severity: fatal", "Hardware error"],
                ErrorTypeAttribute.CORRECTABLE: ["section_type: PCIe error", "event severity: corrected", "Hardware error"]
        },
        OperatingSystems.WINDOWS: {
            ErrorTypeAttribute.CORRECTABLE: ["corrected hardware error", "PCI Express Root Port",
                                             "Error Source: Generic"],
            ErrorTypeAttribute.UNC_FATAL: ["fatal hardware error"],
            ErrorTypeAttribute.UNC_NON_FATAL: ["fatal hardware error"],
            ErrorTypeAttribute.CORRECTABLE_AER: ["corrected hardware error", "PCI Express Root Port",
                                                 "Error Source: Advanced Error Reporting"],
            ErrorTypeAttribute.UNC_NON_FATAL_EDPC_DISABLED: ["corrected hardware error", "PCI Express Root Port",
                                                 "Error Source: Advanced Error Reporting", "UncorrectableErrorStatus: 0x4000"],
        }
    }

    MEM_ERR_SIG = {
        OperatingSystems.WINDOWS: {
            ErrorTypeAttribute.CORRECTABLE: ['A corrected hardware error has occurred', 'Component: Memory']
    }
    }

    MEM_CMD_ERR_SIG = {
        OperatingSystems.WINDOWS: {
            ErrorTypeAttribute.CORRECTABLE: ['1 new correctable HA error detected', 'Found a Correctable ECC Error']
        }
    }

    UNC_LIST = [ErrorTypeAttribute.UNC_FATAL, ErrorTypeAttribute.UNC_NON_FATAL]

    def __init__(
            self,
            test_log,
            arguments,
            cfg_opts,
            bios_config_file=None
    ):
        """
        Create an instance of CscriptsPcieErrorInjectionBaseTest

        :param test_log: Log object
        :param arguments: None
        :param cfg_opts: Configuration Object of provider
        :param bios_config_file: Bios Configuration file name
        """
        super(
            IoVirtualizationCommon,
            self).__init__(
            test_log,
            arguments,
            cfg_opts, bios_config_file_path=bios_config_file)
        self.cfg_opts = cfg_opts
        self.virtualization_obj = VirtualizationCommon(self._log, arguments, cfg_opts)
        self._vm_provider_obj = VMProvider.factory(test_log, cfg_opts, self.os)
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._os_log_obj = OsLogVerifyCommon(self._log, self.os, self._common_content_configuration)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self.num_vms = self._common_content_configuration.get_num_vms_to_create()
        self._common_content_lib = CommonContentLib(self._log, self.os, self.cfg_opts)

    def smm_break_and_inject_pcie_error_via_cscripts(self, csp=None, sdp=None, socket=0, port="pxp3.pcieg5.port0",
                                                     err_type=None, severity=None):
        """
        This method is to set smm and inject the error.

        :param csp - Cscripts obj
        :param sdp - Sdp objects
        :param socket - Socket
        :param port - port
        :param err_type - eg. "ce", "uce"
        :param severity - eg. "fatal", "Non-fatal"
        """
        #  Apply Halt
        sdp.halt_and_check()
        try:
            sdp.start_log("inject_pcie_error.log")

            sdp.itp.smmentrybreak = 1
            pcie = csp.get_cscripts_utils().get_pcie_obj()
            pcie.topology()
            pcie.port_map()
            ei = csp.get_cscripts_utils().get_ei_obj()
            ei.resetInjectorLockCheck()

            if severity:
                ei.injectPcieError(socket=socket, port=port, errType=err_type, severity=severity)
            else:
                ei.injectPcieError(socket=socket, port=port, errType=err_type)

            sdp.stop_log()

            with open("inject_pcie_error.log") as fp:
                err_log = fp.read()
                self._log.info(err_log)

        except Exception as ex:
            raise RuntimeError("Failed during error injection with an exception- {}".format(ex))

        finally:
            self._log.info("Resume the Machine")
            sdp.go()

    def cscripts_pcie_error_injection_vmm_linux_vm(self, err_type=ErrorTypeAttribute.CORRECTABLE, severity=None, existing_vm=0):
        """
        This method is to create VM, check VM functionality, error injection and verification for Linux.

        :param err_type - "ce", "uce"
        :param severity - "fatal", "non-fatal"
        :param existing_vm - no of VM already exist
        :return True or False
        """
        self.VM_OS = [VMs.RHEL]
        VM_NAME = None

        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        sdp_obj = ProviderFactory.create(self.si_dbg_cfg, self._log)
        if err_type in self.UNC_LIST:
            error_type = "uce"
        elif err_type == ErrorTypeAttribute.CORRECTABLE:
            error_type = "ce"
        else:
            raise content_exceptions.TestFail("Test is not implemented for error type -{}".format(err_type))

        for index in range(existing_vm, existing_vm + self.num_vms):
            #  Create VM names dynamically according to the OS
            self.VM_NAME = self.VM_OS[0] + "_" + str(index)

            # #  Create VM
            self.virtualization_obj.create_vm(self.VM_NAME, self.VM_OS[0])

        #  Verify VM
        for index in range(existing_vm, existing_vm + self.num_vms):
            self.VM_NAME = self.VM_OS[0] + "_" + str(index)
            self.virtualization_obj.verify_vm_functionality(self.VM_NAME, self.VM_OS[0])

        #  Get socket and port from config
        socket = self._common_content_configuration.get_cscripts_ei_pcie_device_socket()
        port = self._common_content_configuration.get_cscripts_ei_pcie_device_pxp_port()

        #  Inject PCIe Error
        self.smm_break_and_inject_pcie_error_via_cscripts(csp=cscripts_obj, sdp=sdp_obj, socket=socket, port=port,
                                                          err_type=error_type, severity=severity)

        if err_type in self.UNC_LIST:
            ras_common_util = RasCommonUtil(self._log, self.os, self.cfg_opts, self._common_content_configuration)
            ras_common_util.ac_cycle_if_os_not_alive(self.ac_power, auto_reboot_expected=True)

        err_signature_list = self.ERR_SIG[self.os.os_type][err_type]

        time.sleep(self.LOG_WAIT_CHECK_TIMER_IN_SEC)

        #  Verify error in OS
        vmm_indicated_err_in_dmesg = self._os_log_obj.verify_os_log_error_messages(__file__,
                                                                                   self._os_log_obj.DUT_DMESG_FILE_NAME,
                                                                                   err_signature_list)

        if not vmm_indicated_err_in_dmesg:
            raise content_exceptions.TestFail("Error Signature was not Captured in OS Log")
        self._log.info("Error Signature was found as Expected in OS Log")

        return True

    def execute(self, err_type=ErrorTypeAttribute.CORRECTABLE, severity=None, existing_vm=0):
        """
        This method is to create, verify VM functionality, inject the error and Verify in OS.

        :param err_type
        :param severity
        :param existing_vm - no of VM already exist
        :return True or False
        """
        if self.os.os_type == OperatingSystems.LINUX:
            return self.cscripts_pcie_error_injection_vmm_linux_vm(err_type=err_type, severity=severity, existing_vm=existing_vm)
        elif self.os.os_type == OperatingSystems.WINDOWS:
            return self.cscripts_pcie_error_injection_vmm_windows_vm(err_type=err_type, severity=severity, existing_vm=existing_vm)
        else:
            raise content_exceptions.TestFail("Test is not implemented for OS type - {}".format(self.os.os_type))

    def cscripts_pcie_error_injection_vmm_windows_vm(self, err_type=ErrorTypeAttribute.CORRECTABLE, severity=None, existing_vm=0):
        """
        This method is to create VM, check VM functionality, error injection and verification for Windows.

        :param err_type - "ce", "uce"
        :param severity - "fatal", "non-fatal"
        :param existing_vm - no of VM already exist
        :return True or False
        """
        self._common_content_lib._clear_all_windows_os_error_logs(set_date=False)
        self.VM_OS = [VMs.WINDOWS]

        #  Create Cscripts, sdp, ei Object
        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        sdp_obj = ProviderFactory.create(self.si_dbg_cfg, self._log)

        if err_type in self.UNC_LIST:
            error_type = "uce"
        elif err_type == ErrorTypeAttribute.CORRECTABLE or err_type == ErrorTypeAttribute.CORRECTABLE_AER:
            error_type = "ce"
        else:
            raise content_exceptions.TestFail("Test is not implemented for error type -{}".format(err_type))

        for index in range(existing_vm, existing_vm + self.num_vms):
            # Creates VM names dynamically according to the OS and its resources
            self._log.info("Creating VM on Hyper V")
            vm_name = self.VM_OS[0] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self.virtualization_obj.create_hyperv_vm(vm_name, self.VM_TYPE)  # Create VM function
            self._vm_provider_obj.wait_for_vm(vm_name)  # Wait for VM to boot
            # Assign Network Adapter to VM using Direct Assignment method
            self._vm_provider_obj.add_vm_network_adapter(self.NETWORK_ASSIGNMENT_TYPE, vm_name, self.ADAPTER_NAME,
                                                         self.VSWITCH_NAME, mac_addr=True)
            self.virtualization_obj.verify_hyperv_vm(vm_name, self.VM_TYPE)

        socket = self._common_content_configuration.get_cscripts_ei_pcie_device_socket()
        port = self._common_content_configuration.get_cscripts_ei_pcie_device_pxp_port()

        #  Inject PCIe Error
        self.smm_break_and_inject_pcie_error_via_cscripts(csp=cscripts_obj, sdp=sdp_obj, socket=socket, port=port,
                                                          err_type=error_type, severity=severity)

        if err_type in self.UNC_LIST:
            ras_common_util = RasCommonUtil(self._log, self.os, self.cfg_opts, self._common_content_configuration)
            ras_common_util.ac_cycle_if_os_not_alive(self.ac_power, auto_reboot_expected=True)

        error_signautre_list = self.ERR_SIG[OperatingSystems.WINDOWS][err_type]

        time.sleep(self.LOG_WAIT_CHECK_TIMER_IN_SEC)

        #  Verify error in OS
        vmm_indicated_err_in_event_log =self._os_log_obj.verify_os_log_error_messages(
            __file__, self._os_log_obj.DUT_WINDOWS_WHEA_LOG, error_signautre_list)

        if not vmm_indicated_err_in_event_log:
            raise content_exceptions.TestFail("Error Signature was not Captured in OS Log")
        self._log.info("Error Signature was found as Expected in OS Log")

        return True

    def cscripts_memory_error_injection_vmm_windows_vm(self, err_type=ErrorTypeAttribute.CORRECTABLE, vm_memory=4):
        """
        This method is to create, verify VM functionality, inject the memory error and Verify in OS.

        :param err_type - error injection type
        :param vm_memory - VM memory size
        :return True or False
        """
        self.VM_OS = [VMs.WINDOWS]

        #  Create Cscripts, sdp, ei Object
        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        sdp_obj = ProviderFactory.create(self.si_dbg_cfg, self._log)
        ei_obj = cscripts_obj.get_cscripts_utils().get_ei_obj()

        for index in range(self.num_vms):
            # Creates VM names dynamically according to the OS and its resources
            self._log.info("Creating VM on Hyper V")
            vm_name = self.VM_OS[0] + "_" + str(index)
            self.LIST_OF_VM_NAMES.append(vm_name)
            self.virtualization_obj.create_hyperv_vm(vm_name, self.VM_TYPE, vm_memory)  # Create VM function
            self._vm_provider_obj.wait_for_vm(vm_name)  # Wait for VM to boot
            # Assign Network Adapter to VM using Direct Assignment method
            self._vm_provider_obj.add_vm_network_adapter(self.NETWORK_ASSIGNMENT_TYPE, vm_name, self.ADAPTER_NAME,
                                                         self.VSWITCH_NAME)
            self.virtualization_obj.verify_hyperv_vm(vm_name, self.VM_TYPE)

        return self.inject_and_verify_mem_error(err_type)

    def inject_and_verify_mem_error(self, err_type):
        """
        Method to inject the Memory Error.

        :param err_type
        """
        #  Create Cscripts, sdp, ei Object
        cscripts_obj = ProviderFactory.create(self.sil_cfg, self._log)
        sdp_obj = ProviderFactory.create(self.si_dbg_cfg, self._log)
        ei_obj = cscripts_obj.get_cscripts_utils().get_ei_obj()

        # Get the Socket, channel, sub-channel, DIMM, RANK
        socket_list = self._common_content_configuration.get_einj_mem_location_socket()
        channel_list = self._common_content_configuration.get_einj_mem_location_channel()
        sub_channel_list = self._common_content_configuration.get_einj_mem_location_subchannel()
        dimm_list = self._common_content_configuration.get_einj_mem_location_dimm()
        rank_list = self._common_content_configuration.get_einj_mem_location_rank()

        if len(socket_list) != len(channel_list) != len(sub_channel_list) != len(dimm_list) != len(rank_list):
            raise content_exceptions.TestFail(
                "<einj_mem_location tag> is not configured correctly in content_configuration.xml")

        if err_type in self.UNC_LIST:
            error_type = "uce"
        elif err_type == ErrorTypeAttribute.CORRECTABLE:
            error_type = "ce"
        else:
            raise content_exceptions.TestFail("Test is not implemented for error type -{}".format(err_type))

        for soc, channel, sub_channel, dimm, rank in zip(socket_list, channel_list, sub_channel_list, dimm_list,
                                                         rank_list):
            self._common_content_lib._clear_all_windows_os_error_logs(False)
            if not self.einj_mem_error_check_logs(sdp_obj=sdp_obj, ei_obj=ei_obj, soc=int(soc), ch=int(channel),
                                                               sub_ch=int(sub_channel), dimm=int(dimm),
                                                               rank=int(rank), error_type=error_type,
                                                  signature=self.MEM_CMD_ERR_SIG[self.os.os_type][err_type]):
                raise content_exceptions.TestFail("memory error injection failed")

            err_signature_list = self.MEM_ERR_SIG[self.os.os_type][err_type]

            time.sleep(self.ERROR_INJECT_WAIT_TIME_SEC)

            #  Verify error in OS
            vmm_indicated_err_in_whea = self._os_log_obj.verify_os_log_error_messages(__file__,
                                                                                       self._os_log_obj.DUT_WINDOWS_WHEA_LOG,
                                                                                       err_signature_list)

            if not vmm_indicated_err_in_whea:
                raise content_exceptions.TestFail("Error Signature was not Captured in OS Log")
            self._log.info("Error Signature was found as Expected in OS Log")

        return True

    def einj_mem_error_check_logs(self, sdp_obj, ei_obj, soc, ch, sub_ch, dimm, rank, error_type, signature):
        """
        This method is used to inject the memory error

        :param sdp_obj - Sdp object
        :param ei_obj - Sdp object
        :param soc - Socket
        :param ch - Channel
        :param sub_ch - Sub Channel
        :param dimm - dimm slot
        :param rank - rank
        :param error_type - type of error to inject
        :param signature - error signature to look up in log

        : return - True / False
        """
        try:
            sdp_obj.start_log("mem_error_injection.log", "w")
            ei_obj.resetInjectorLockCheck()
            ei_obj.injectMemError(socket=soc, channel=ch, sub_channel=sub_ch, dimm=dimm, rank=rank, errType=error_type)
            sdp_obj.stop_log()
            with open("mem_error_injection.log", "r") as log_file:
                memory_error_injection_log = log_file.read()
                self._log.info(memory_error_injection_log)
            for error in signature:
                if not error in memory_error_injection_log:
                    self._log.info("Error Signature : {} - is not found in error injection command output".format(error))
                    return False
                self._log.info("Error Signature : {} - is found on error injection output".format(error))
            return True
        except Exception as ex:
            raise RuntimeError("Failed during memory error injection with an exception- {}".format(ex))
        finally:
            self._log.info("Resume the Machine")
            sdp_obj.go()

    def cleanup(self, return_status):  # type: (bool) -> None
        """
        Test Cleanup
        1. Destroy Created VM.
        """
        try:
            for index in range(self.num_vms):
                self._log.info("Deleting VM{}".format(index))
                self.VM_NAME = self.VM_OS[0] + "_" + str(index)
                self._vm_provider_obj.destroy_vm(self.VM_NAME)
        except Exception as ex:
            raise content_exceptions.TestFail("Unable to Destroy the VM")
        super(VmmCscriptsPcieErrorInjectionBaseTest, self).cleanup(return_status)


if __name__ == "__main__":
    sys.exit(Framework.TEST_RESULT_PASS if VmmCscriptsPcieErrorInjectionBaseTest.main()
             else Framework.TEST_RESULT_FAIL)
