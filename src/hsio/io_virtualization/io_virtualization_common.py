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
import re
import threading
import time


from dtaf_core.providers.silicon_reg_provider import SiliconRegProvider
from dtaf_core.providers.silicon_debug_provider import SiliconDebugProvider

from src.lib.common_content_lib import CommonContentLib, VmUserWin
from src.lib.install_collateral import InstallCollateral
from dtaf_core.lib.dtaf_constants import OperatingSystems
from src.lib.os_lib import WindowsCommonLib
from src.provider.stressapp_provider import StressAppTestProvider


from src.provider.vm_provider import VMProvider, VMs
from src.hsio.lib.ras_upi_util import RasUpiUtil

from src.hsio.io_virtualization.virtualization_common import VirtualizationCommon
from src.lib.dtaf_content_constants import StressMprimeTool
from src.lib.content_base_test_case import ContentBaseTestCase
from src.hsio.lib.os_log_verification import OsLogVerifyCommon
from src.lib import content_exceptions


class IoVirtualizationCommon(ContentBaseTestCase):
    """
    This Class is Used as Common Class For all the IO Virtualization Test Cases
    """

    WINDOWS_VM_USERNAME = VmUserWin.USER
    WINDOWS_VM_PASSWORD = VmUserWin.PWD
    NETWORK_ASSIGNMENT_TYPE = "DDA"
    VSWITCH_NAME = "ExternalSwitch"
    ADAPTER_NAME = None
    WAIT_TIME_IN_SEC = 300
    TWO_MIN_IN_SEC = 120
    FIVE_MIN_IN_SEC = 300
    ONE_HRS_IN_SEC = 3600
    PCIERRPOLL_HOST_FILE_NAME = "pcie_err_poll_output.txt"
    PCIERRPOLL_CMD_WIN = "PCIERRpoll_debug.exe -all >> {}".format(PCIERRPOLL_HOST_FILE_NAME)
    IPERF_HOST_FILE_NAME = "iperf_client_sut.txt"
    ERR_SIGNATURE = "Errors found in device"

    def __init__(
            self,
            test_log,
            arguments,
            cfg_opts,
            bios_config_file=None
    ):
        """
        Create an instance of IoVirtualizationCommon

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
        self.args = arguments
        self._vm_provider_obj = VMProvider.factory(test_log, cfg_opts, self.os)
        self.sil_cfg = cfg_opts.find(SiliconRegProvider.DEFAULT_CONFIG_PATH)
        self.si_dbg_cfg = cfg_opts.find(SiliconDebugProvider.DEFAULT_CONFIG_PATH)
        self._os_log_obj = OsLogVerifyCommon(self._log, self.os, self._common_content_configuration)
        self._install_collateral = InstallCollateral(self._log, self.os, cfg_opts)
        self.num_vms = self._common_content_configuration.get_num_vms_to_create()

        self.WAIT_TIME_FOR_TOOL_START_SEC = 10
        self.WAIT_TIME_FOR_MEMORY_INCREASE_CHECK_SEC = 40
        self.NUM_OF_CHECKS = 20
        self.GREP_CURR_MEM_CMD = "grep current server.xml"
        self.MEM_2G = "2097152"
        self.CHANGE_CURR_MEM_CMD = "sed -i " + "\"" + "s/unit='KiB'>10485760<\/currentMemory>/unit='KiB'>{}" \
                                                      "<\/currentMemory>/g" + "\"" + " server.xml"
        self.ENABLE_AUTODEFLATE_CMD = "sed -i " + "\"" + "s/memballoon[[:space:]]model='virtio'/memballoon model" \
                                                         "='virtio' autodeflate='on'/g" + "\"" + " server.xml"
        self.FISHER_WORKLOAD = "{}/crunch-static-102"
        self.FISHER_RUN_DURATION = "1h"
        self.FISHER_TOOL_CMD = "fisher --workload='{}' --runtime={} --injection-type=memory-correctable --" \
                               "match=CRd"
        self.FISHER_TOOL_WORKLOAD = "crunch"
        self.FISHER_TOOL_RUN_CMD = "./fisher_cmd.sh"
        self.DUT_JOURNALCTL_CE_CHECK_CMD = "journalctl |grep 'Corrected memory errors'|wc -l"
        self.DUT_JOURNALCTL_ERROR_CHECK_CMD = "journalctl |grep 'Uncorrected error'|wc -l"
        self.FISHER_TOOL_CHECK_STRING = "/fisher"
        self.FISHER_TOOL_RUN_CHECK_CMD = "ps -ef | grep fisher"
        self.REGEX_CMD_FOR_ADAPTER_IP_PINGABLE_LINUX = r".*bytes\sfrom.*icmp_seq.*ttl.*time.*"
        self.FISHER_WORKLOAD_UCE = "{}/crunch-static-102  -e 0 -e 1 -e 2 -e 8 -e 9 -e 11 -e 13 -e 14 -e 16 -e 23"
        self.FISHER_TOOL_CMD_UCE = "fisher --workload='{}' --runtime={} --injection-type=memory-uncorrectable-non-" \
                                   "fatal  --match=CRd"
        self.IPERF_TOOL_NAME_DICT = {"RS5": "iperf3.exe", "RHEL": "iperf3"}
        self.BURNING_100_WORKLOAD_CONFIG_FILE = "cpu_memory_100_workload.txt"
        self.SIOV_KERNEL_OPTIONS = r"intel_iommu=on,sm_on iommu=on"
        self.VM_IMAGE_LOCATION = "/var/lib/libvirt/images"
        self.GET_BUSID_CMD = "ethtool -i {}"
        self.SIOV_WITH_VM_LAUNCH_CMD = "qemu-system-x86_64 -enable-kvm -m 16G -smp 8 -device " \
                                       "vfio-pci,sysfsdev=/sys/bus/mdev/devices/{}/ -drive file={}"
        self.WAIT_TIME_TO_SPAWN_VM_SEC = 30
        self.INTERFACE_LIST_CMD = "ls /sys/class/net"
        self.DELETE_MDEV_CMD = "echo 1 > /sys/bus/mdev/devices/*/remove"
        self.SHUTDOWN_VM = "shutdown -h now"
        self.QEMU_KVM_CHECK_CMD = "ls /usr/bin/ | grep -i {}"
        self.QEMU_KVM_FILE_NAMES = ["qemu-system-x86_64", "qemu-kvm"]
        self.QEMU_KVM_INSTALL_CMD = "dnf install qemu"
        self.LIST_INTERFACES = "ip a"

    def create_and_verify_vm(self, vm_name, vm_type, crunch_tool=False,
                             enable_yum_repo=False, libquantum_tool=False, mprime_tool=False):
        """
        This method is to create VM.

        :param vm_name: Name of the VM.
        :param vm_type: Types of VM eg. RHEL
        :param crunch_tool: True if vm to verify with crunch tools.
        :param enable_yum_repo: True if yum repo  need to enable on SUT.
        :param libquantum_tool: True if vm to verify with libquantum tool.
        :param mprime_tool: True if vm to verify with mprime tool.
        :return vm_os_obj: VM Os object.
        """
        mac_addr_flag = self._common_content_configuration.enable_with_mac_id()
        self.virtualization_obj.create_vm(vm_name, vm_type, mac_addr_flag)

        #  Verify VM
        self.virtualization_obj.verify_vm_functionality(vm_name, vm_type, enable_yum_repo=enable_yum_repo)

        #  Create VM Os Object
        vm_os_obj = self.virtualization_obj.create_vm_host(vm_name, vm_type)
        self.vm_common_content_lib = CommonContentLib(self._log, vm_os_obj, self._cfg)

        #  Install Screen package on VM SUT
        self.vm_install_collateral = InstallCollateral(self._log, vm_os_obj, self._cfg)
        self.vm_install_collateral.screen_package_installation()

        self.vm_ras_upi_util = RasUpiUtil(vm_os_obj, self._log, self._cfg, self.vm_common_content_lib, self.args)

        if crunch_tool:
            #  Run crunch stress tool on VM
            self.vm_ras_upi_util.execute_crunch_tool()

        if libquantum_tool:
            #  Run libquantum stress tool on VM
            tool_path = self.vm_ras_upi_util.install_libquantum_tool()
            self.vm_ras_upi_util.execute_libquantum_tool(tool_path)

        if mprime_tool:
            #  Run mprime stress tool on VM
            tool_path = self.vm_ras_upi_util.install_mprime_tool()
            self.vm_ras_upi_util.execute_mprime_tool(tool_path)

        return vm_os_obj

    def get_current_memory_value(self, os_obj, vm_name):
        """
        Method to get the current memory value on a particular VM.

        :param: os_obj: os object for VM
        :param: vm_name: name of VM
        :return: curmem: memory (integer value)

        """
        self._log.info("Get current memory value on VM - {}".format(vm_name))
        output = os_obj.execute(self.virtualization_obj.GET_MEMORY_DUMP_CMD.format(vm_name), self._command_timeout).stdout
        curmem = int(re.findall(r'\d+', output)[1])
        self._log.info("Current Memory - {}".format(curmem))
        return curmem

    def wait_for_tool_run_completion(self, os_obj, tool_name=None):
        """
        Exits when the particualr tool run gets completed.

        :param: os_obj: os of VM or SUT.
        :param: tool_name: Tool name
        :return: True/False
        """
        while tool_name:
            status = os_obj.execute("ps -ef | grep {}".format(tool_name), self._command_timeout).stdout.split()
            if "./{}".format(tool_name) in status:
                self._log.info("{} still running, will re-check after 5 mins".format(tool_name))
                time.sleep(self.WAIT_TIME_FOR_TOOL_START_SEC * 30)
            else:
                break
        return True

    def check_for_memory_increase(self, os_obj, vm_name, curmem, num_of_times=10):
        """
        Checking for memory increase with load increase.

        :param: num_of_times: number of checks
        :param: os_obj: os object
        :param: vm_name: name of VM
        :param: curmem: current memory value
        :return: True/False

        """
        for check in range(num_of_times):
            self._log.info("Current Memory check - {}".format(check))
            lastmem = curmem
            curmem = self.get_current_memory_value(os_obj, vm_name)
            time.sleep(self.WAIT_TIME_FOR_MEMORY_INCREASE_CHECK_SEC)
            self._log.info("lastmem - {}, currentmem - {}".format(lastmem, curmem))
            if curmem < lastmem:
                self._log.info("Memory didn't increase from last check")
                return False
        return True

    def check_if_vm_is_alive(self, os_obj, num_of_times=5):
        """
        Checking for memory increase with load increase.

        :param: num_of_times: number of checks
        :param: os_obj: VM os object

        """
        for check in range(num_of_times):
            try:
                if os_obj.is_alive():
                    self._log.info("VM is alive after stress tool runs as expected")
                    break
            except:
                self._log.info("Checking again - {} times........................".format(check+1))
                time.sleep(self.WAIT_TIME_FOR_TOOL_START_SEC)
            finally:
                self._log.info("VM ssh is expected to be broken due to load")

    def edit_vm_for_kvm_balloon(self, vm_os_obj, vm_name, memory):
        """
        Edit VM for KVM Ballooning.

        :param: vm_os_obj: os object for VM
        :param: vm_name: Name of VM
        :param: memory: memory to set in VM
        :Return: None

        """
        # Edit VM
        self._log.info("Shutting down VM..")
        self.os.execute(self.virtualization_obj.SHUTDOWN_VM_COMMAND.format(vm_name), self._command_timeout)
        self._log.info("Editing current memory to - {}".format(memory))
        self.os.execute(self.virtualization_obj.DUMP_TO_XML_CMD.format(vm_name), self._command_timeout)
        self.os.execute(self.virtualization_obj.UNDEFINE_VM_CMD.format(vm_name), self._command_timeout)
        output = self.os.execute(self.GREP_CURR_MEM_CMD, self._command_timeout).stdout
        self.curmem = int(re.findall(r'\d+', output)[0])
        self._log.info("default memory - {}".format(self.curmem))
        self.os.execute(self.CHANGE_CURR_MEM_CMD.format(memory), self._command_timeout)
        self.os.execute(self.ENABLE_AUTODEFLATE_CMD, self._command_timeout)
        self.os.execute(self.virtualization_obj.DEFINE_VM_CMD, self._command_timeout)
        self._log.info("Starting VM.....")
        time.sleep(self.WAIT_TIME_FOR_TOOL_START_SEC)
        self.os.execute(self.virtualization_obj.START_VM_CMD.format(vm_name), self._command_timeout)
        time.sleep(self.WAIT_TIME_FOR_TOOL_START_SEC)
        if not vm_os_obj.is_alive():
            self.os.execute(self.virtualization_obj.START_VM_CMD.format(vm_name), self._command_timeout)
            time.sleep(self.WAIT_TIME_FOR_TOOL_START_SEC)

    def start_mprime_tool_for_stress_kvm_balloon(self, vm_os_obj, vm_name):
        """
        Open Console, create prime.txt and run mprime.

        :param: vm_os_obj: os object for VM
        :param: vm_name: Name of VM
        :Return: None

        """
        self._log.info("Opening VM Console.....")
        self.os.execute(self.virtualization_obj.CONSOLE_VM_CMD.format(vm_name), self._command_timeout)

        self._log.info("Start prime95 from vm console.....")
        tool_path = self.vm_ras_upi_util.install_mprime_tool()
        vm_os_obj.execute(StressMprimeTool.REMOVE_PRIME_FILE, self._command_timeout, tool_path)

        for txt in StressMprimeTool.PRIME_FILE_CONTENT:
            vm_os_obj.execute("echo '{}' >> prime.txt".format(txt), self._command_timeout, tool_path)

        # Running prime95
        time.sleep(self.WAIT_TIME_FOR_TOOL_START_SEC * 2)
        vm_os_obj.execute_async(StressMprimeTool.START_MPRIME_STRESS_ON_SUT_CMD, tool_path)
        time.sleep(self.WAIT_TIME_FOR_TOOL_START_SEC)

    def start_fisher_tool(self, fisher_tool_cmd, fisher_tool_workload, fisher_tool_duration):
        """
        Method to start fisher tool in parallel with mprime.

        :param: fisher_tool_cmd: command to run fisher tool
        :param: fisher_tool_workload: workload on the fisher execution
        :param: fisher_tool_duration: duration for fisher tool
        :return: None

        """
        self._log.info("Starting Fisher tool in parallel...........")
        self._log.info("Running Fisher tool...")
        self.os.execute("""echo "{}" > fisher_cmd.sh""".format(fisher_tool_cmd).
                        format(fisher_tool_workload,fisher_tool_duration), self._command_timeout)
        time.sleep(self.WAIT_TIME_FOR_TOOL_START_SEC/2)
        self.os.execute("chmod 777 {}".format(self.FISHER_TOOL_RUN_CMD), self._command_timeout)
        time.sleep(self.WAIT_TIME_FOR_TOOL_START_SEC/5)
        self.os.execute_async("""{}""".format(self.FISHER_TOOL_RUN_CMD))
        time.sleep(self.WAIT_TIME_FOR_TOOL_START_SEC/5)
        try:
            cmd_output = self.os.execute(self.FISHER_TOOL_RUN_CHECK_CMD, self._command_timeout).stdout
            if self.FISHER_TOOL_CHECK_STRING not in cmd_output:
                raise content_exceptions.TestFail("fisher tool is not executing")
        except:
            self._log.info("Fisher tool run Couldn't check because of load, rechecking in 10 sec")
            time.sleep(self.WAIT_TIME_FOR_TOOL_START_SEC)
            cmd_output = self.os.execute(self.FISHER_TOOL_RUN_CHECK_CMD, self._command_timeout).stdout
            if self.FISHER_TOOL_CHECK_STRING not in cmd_output:
                raise content_exceptions.TestFail("fisher tool is not executing")
        self._log.info("Confirming - fisher Tool is Successfully Started")

    def check_vm_ping_linux(self, vm_os_obj, vm_name, vm_ip):
        """
        Check if VM is pinging.

        :param: vm_os_obj: vm os object
        :param: vm_name: name of VM
        :param: vm_ip: ip of VM
        :return: True/False

        """
        self._log.info("Pinging VM - {} for IP - {}".format(vm_name, vm_ip))
        for check in range(int(self.NUM_OF_CHECKS/4)):
            try:
                result = self.os.execute("ping -c 4 {}".format(vm_ip), self._command_timeout).stdout
                self._log.info("ping result for VM - '{}' = {}".format(vm_name, str(result)))
                if re.findall(self.REGEX_CMD_FOR_ADAPTER_IP_PINGABLE_LINUX, "".join(result)):
                    self._log.info("VM - {} is pinging...........".format(vm_name))
                    return True
            except:
                self._log.info("Retry - {} for pinging VM - {}".format(check+1, vm_name))
        self._log.info("VM - {} is not pinging...........".format(vm_name))
        return False

    def create_vm_on_windows_sut(self, vm_name, vm_type, template=False, vm_os_type=OperatingSystems.WINDOWS,
                                 vhdx_path=True):
        """
        This method is to create (Windows, or Linux) VM on Windows SUT.
        :param vm_name - Name of the Virtual Machine
        :param vm_type - Sub Type of VM eg- RHEL, RS5
        :param template - Need to keep True to create VM from Template else False if need to create from ISO.
        :param vm_os_type - VM Os Type for eg: Linux, Windows
        :param vhdx_path - path to create the hardisk for VM. If False it will create on default path C:\\Automation
        """
        #  Get Mac id flag from config to Assign the Mac id to Network
        mac_id_flag = self._common_content_configuration.enable_with_mac_id()
        if vhdx_path:
            vhdx_path = self._common_content_configuration.get_vm_vhdx_drive_name(vm_name)

        if template:
            self._vm_provider_obj.create_vm_from_template(vm_name, vhdx_path=vhdx_path)  # Create VM function
            self._vm_provider_obj.start_vm(vm_name)
            time.sleep(self.WAIT_TIME_IN_SEC)
        else:
            self.virtualization_obj.create_hyperv_vm(vm_name, vm_type, vhd_dir_path=vhdx_path)
            time.sleep(self._common_content_configuration.get_wait_for_vm_os_time_out())
        self._windows_common_lib = WindowsCommonLib(self._log, self.os)
        device_name = self._common_content_configuration.get_default_sut_network_adpter_name()
        adapter_name = self._windows_common_lib.get_network_adapter_name(device_name)
        self._vm_provider_obj.add_vm_network_adapter(self.NETWORK_ASSIGNMENT_TYPE, vm_name, adapter_name,
                                                     self.VSWITCH_NAME, mac_addr=mac_id_flag)

        self.virtualization_obj.verify_hyperv_vm(vm_name, vm_type)

        if vm_os_type == OperatingSystems.LINUX:
            vm_os_obj = self.virtualization_obj.create_linux_vm_object_in_hyperv(vm_name, vm_type,
                                                                                 enable_yum_repo=True)
        else:
            vm_os_obj = self.virtualization_obj.windows_vm_object(vm_name, vm_type)

        return vm_os_obj

    def install_burnin_tool_on_vm(self, vm_os_obj, vm_os_type):
        """
        This method is to install the burnin tool on VM.

        :param vm_os_type - VM Os type
        :param vm_os_obj - VM os obj
        """
        install_collateral = InstallCollateral(self._log, vm_os_obj, self.cfg_opts)
        if vm_os_type == VMs.RS5:
            return install_collateral.install_burnin_tool_on_windows()
        else:
            return install_collateral.install_burnintest()

    def start_burnin_stress_on_vm(self, vm_os_obj, vm_os_type, duration_time=1200, sut_tool_path=None):
        """
        This method is to start burnin stress on VM.
        :param vm_os_type - VM OS type - "RS5", "RHEL"
        :param vm_os_obj - VM os object
        :param duration_time - duration time in sec to execute burnin test
        :param sut_tool_path - burnin stress tool path
        """
        stress_app = StressAppTestProvider.factory(self._log, self.cfg_opts, vm_os_obj)
        install_collateral = InstallCollateral(self._log, vm_os_obj, self.cfg_opts)
        if vm_os_type == VMs.RS5:
            config_file_path = install_collateral.download_tool_to_host("cmd_100_newbit.bitcfg")
            burning_thread = threading.Thread(target=stress_app.execute_burnin_test,
                                              args=(self.log_dir, duration_time, sut_tool_path,
                                                    config_file_path, None, False,))
            burning_thread.start()
        else:
            burnin_config_file = install_collateral.download_tool_to_host(self.BURNING_100_WORKLOAD_CONFIG_FILE)
            burnin_thread = threading.Thread(target=stress_app.execute_burnin_test,
                                             args=(self.log_dir, duration_time, sut_tool_path,
                                                   burnin_config_file, None, False,))

            burnin_thread.start()

    def run_iperf_as_server(self, os_obj=None, os_type=None, sut_iperf_path=None,
                            tool_execution_time_seconds=21600, vm_name=None, bidirectional=False):
        """
        This method is to run iperf as a server
        :param os_obj - os object
        :param os_type - OS type - "RS5", "RHEl"
        :param sut_iperf_path - iperf tool folder path
        :param tool_execution_time_seconds - time delay in sec to run iperf
        :param vm_name - VM name
        :param bidirectional - to run bidirectional
        """
        iperf_tool_name = self.IPERF_TOOL_NAME_DICT[os_type.upper()]
        bidirectional_option = " "
        if bidirectional:
            bidirectional_option = " -d "
        if vm_name:
            #  framing iperf server tool name
            iperf_server_cmd = "{} -s -p{}5201 > iperf_server_{}.txt".format(iperf_tool_name, bidirectional_option, vm_name)
        else:
            iperf_server_cmd = "{} -s -p{}5201 > iperf_server_{}.txt".format(iperf_tool_name, bidirectional_option, "sut")

        stress_app_on_sut = StressAppTestProvider.factory(self._log, self.cfg_opts, os_obj)
        if os_type == VMs.RHEL:
            stress_app_on_sut.execute_async_stress_tool(iperf_server_cmd, iperf_tool_name, sut_iperf_path)
        else:
            stress_app_on_sut.execute_async_stress_tool(iperf_server_cmd, iperf_tool_name, sut_iperf_path,
                                                        tool_execution_time_seconds)

        self._log.info("Started iperf server on OS type- {}".format(os_type))
        return True

    def run_iperf_as_client(self, os_obj=None, os_type=None, sut_iperf_path=None, ip=None,
                            tool_execution_time_seconds=21600, vm_name=None, bidirectional=False):
        """
        This method is to run iperf as a client.
        :param os_obj - Os on=bject
        :param os_type - OS type - RHEL, RS5
        :param sut_iperf_path - sut iperf folder path
        :param ip - server ip where needs to establish communication
        :param tool_execution_time_seconds - tool execution time.
        :param vm_name - VM name
        :param bidirectional - to run bidirectional
        """
        stress_app_on_sut = StressAppTestProvider.factory(self._log, self.cfg_opts, os_obj)
        iperf_tool_name = self.IPERF_TOOL_NAME_DICT[os_type.upper()]
        bidirectional_option = " "
        if bidirectional:
            bidirectional_option = " -d "
        if vm_name:
            iperf_client_cmd = "{} -c {} -u -t {} -i 1 -p{}5201 >> iperf_client_{}.txt".format(
                iperf_tool_name, ip, tool_execution_time_seconds, bidirectional_option, vm_name)
        else:
            iperf_client_cmd = "{} -c {} -u -t {} -i 1 -p{}5201 >> iperf_client_{}.txt".format(
                iperf_tool_name, ip, tool_execution_time_seconds, bidirectional_option, "sut")
        self._log.info("iperf command from client side- {}".format(iperf_client_cmd))
        if os_type == "RHEL":
            stress_app_on_sut.execute_async_stress_tool(iperf_client_cmd, iperf_tool_name, sut_iperf_path)
        else:
            stress_app_on_sut.execute_async_stress_tool(iperf_client_cmd, iperf_tool_name, sut_iperf_path,
                                                        tool_execution_time_seconds)

    def assign_static_ip_to_vm(self, vm_os_obj, physical_adpater, static_ip, subnet_mask, gateway_ip):
        """
        This method is to assign static ip to VM.
        :param vm_os_obj
        :param physical_adpater
        :param static_ip
        :param subnet_mask
        :param gateway_ip
        """
        if vm_os_obj.os_type == OperatingSystems.LINUX:
            out_put = vm_os_obj.execute("ifconfig {} {}".format(physical_adpater, static_ip),
                                        self._command_timeout)
            if out_put.cmd_failed():
                raise content_exceptions.TestFail("Failed with std_err- {}".format(vm_os_obj.stderr))
        else:
            windows_common_lib_vm = WindowsCommonLib(self._log, vm_os_obj)
            windows_common_lib_vm.configure_static_ip(physical_adpater, static_ip, subnet_mask, gateway_ip)

        return True

    def get_non_dhcp_network_adapter(self, network_adapter_name_list, dhcp_adapter_name):
        """
        This method is to get network adapter that is not the network adapter configured for DHCP.

        :param network_adapter_name_list - List of Ethernet Adapter eg:- ["Ethernet 6", "Ethernet 11"]
        :param dhcp_adapter_name - Adpter Name which is already assigned with dhcp ip.
        """
        static_adapter_name = None
        for each_name in network_adapter_name_list:
            if each_name != dhcp_adapter_name:
                static_adapter_name = each_name
                break
        if static_adapter_name is None:
            raise content_exceptions.TestFail("Adapter is not found in VM for Assigning static IP")
        return static_adapter_name

    def run_pcierrpoll_win(self, timeout, pcierrpoll_path):
        """
        This method is to run pcie err poll tools.

        :param timeout - timeout for execute command
        :param pcierrpoll_path - tool path
        """
        self._log.info("Executing the command : {}".format(self.PCIERRPOLL_CMD_WIN))
        self.os.execute(cmd=self.PCIERRPOLL_CMD_WIN, timeout=self._command_timeout + timeout, cwd=pcierrpoll_path)

    def is_qemu_kvm_installed(self):
        """
        This method checks for "qemu-system-x86_64" and "qemu-kvm" files present at /usr/bin/.

        :param None
        :Return True/False
        """
        for file in self.QEMU_KVM_FILE_NAMES:
            self._log.info("Checking for {} file at /usr/bin/".format(file))
            if file not in self.os.execute(self.QEMU_KVM_CHECK_CMD.format("qemu"), self._command_timeout).stdout.split():
                self._log.info("{} is not installed on sut".format(file))
                return False
        return True

    def install_qemu_kvm(self):
        """
        This method installs "qemu-system-x86_64" and "qemu-kvm" files.

        :param None
        :Return None
        """
        self._log.info("Installing QEMU & KVM")
        self.os.execute(self.QEMU_KVM_INSTALL_CMD, self._command_timeout)
        for file in self.QEMU_KVM_FILE_NAMES:
            self._log.info("Checking for {} file at /usr/bin/".format(file))
            if file not in self.os.execute(self.QEMU_KVM_CHECK_CMD.format("qemu"), self._command_timeout).stdout.split():
                raise content_exceptions.TestFail("{} is not getting installed on sut".format(file))

    def extract_installed_vm_image_linux(self, vm_name):
        """
        This method will create and undefine VM, but will return it's installed version ".qcow2" to be linked with SIOV.

        :param vm_name: name of VM
        :return vm_file_path: installed VM path
        """
        vm_file = "{}.qcow2".format(vm_name)
        vm_file_path = self.VM_IMAGE_LOCATION + "/" + vm_file
        if vm_file in self.os.execute("ls", self._command_timeout, cwd=self.VM_IMAGE_LOCATION).stdout:
            self.os.execute("rm -rf {}".format(vm_file_path), self._command_timeout)
        # create VM
        self.vm_os_obj = self.create_and_verify_vm(vm_name, vm_name)
        self._log.info("Shutting down and undefining VM - {}".format(vm_name))
        self.os.execute(self.virtualization_obj.SHUTDOWN_VM_COMMAND.format(vm_name), self._command_timeout)
        self.os.execute(self.virtualization_obj.UNDEFINE_VM_CMD.format(vm_name), self._command_timeout)
        return vm_file_path

    def find_interface_on_linux(self, vm_obj, module):
        """
        This method will find out the given module type interface.

        :param vm_obj: OS/VM object
        :param module: driver module name
        :return interface: interface list
        """
        interface = []
        self._log.info("Finding {} driver interface...".format(module))
        interface_list = vm_obj.execute(self.INTERFACE_LIST_CMD, self._command_timeout).stdout.split()
        for intrfce in interface_list:
            self._log.info("Looking in interface - {}".format(intrfce))
            if module in (vm_obj.execute("ethtool -i {}".format(intrfce), self._command_timeout).stdout.split()):
                self._log.info("{} driver interface found in- {}".format(module, intrfce))
                interface.append(intrfce)
        return interface

    def find_siov_interface_on_sut(self):
        """
        This method finds out the interface on which siov instance need to be created.

        :param None
        :return interface: SIOV active interface
        """
        drive_module_name = self._common_content_configuration.get_sut_nic_driver_module_name()
        self._log.info("Driver Module name on SUT - {}".format(drive_module_name))
        module_interface_list = self.find_interface_on_linux(self.os, drive_module_name)
        all_interface = self.os.execute(self.LIST_INTERFACES, self._command_timeout).stdout.split()
        for interface in module_interface_list:
            index = all_interface.index(interface + ":")
            if "NO-CARRIER" not in all_interface[index+1]:
                self._log.info("Active Ethernet SIOV interface on which mdev instance will be created - {}".format(interface))
                return interface
        raise content_exceptions.TestFail("Cannot find SUT interface.....")

    def install_iperf_on_vm(self, vm_obj, vm_type):
        """
        The method will install iperf tool on OS

        :param vm_obj: VM object
        :param vm_type: type of os
        :return None
        """
        _install_collateral = InstallCollateral(self._log, vm_obj, self.cfg_opts)
        if vm_type == VMs.RHEL:
            _install_collateral.screen_package_installation()
            _install_collateral.install_iperf_on_vm()
