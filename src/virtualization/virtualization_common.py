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
import time
import subprocess
import socket
import csv
import threading
import pandas as pd

from collections import defaultdict
from pathlib import Path

from dtaf_core.lib.dtaf_constants import OperatingSystems

from src.lib import content_exceptions
from src.lib.common_content_lib import CommonContentLib

from src.lib.content_base_test_case import ContentBaseTestCase
from src.lib.tools_constants import ArtifactoryName, ArtifactoryTools
from src.provider.vm_provider import VMProvider
from src.lib.install_collateral import InstallCollateral
from src.lib.dtaf_content_constants import CommonConstants
from src.lib.content_artifactory_utils import ContentArtifactoryUtils
from src.lib.dtaf_content_constants import TimeConstants, DynamoToolConstants, IOmeterToolConstants, Mprime95ToolConstant
from src.lib.common_content_lib import VmUserLin
from src.lib.common_content_lib import VmUserWin

from dtaf_core.providers.provider_factory import ProviderFactory
from dtaf_core.providers.internal.ssh_sut_os_provider import SshSutOsProvider

class VirtualizationCommon(ContentBaseTestCase):
    """
    Base class for all Virtualization Test Cases.
    This base class covers below Test Case IDs.

    1. H80292
    2. H80290
    3. H84452
    4. H80281
    5. H84469
    6. H84470
    7. H84453
    """
    VM_USERNAME = VmUserLin.USER
    VM_PASSWORD = VmUserLin.PWD
    WINDOWS_VM_USERNAME = VmUserWin.USER
    WINDOWS_VM_PASSWORD = VmUserWin.PWD

    VM_IP_LIST = dict()
    VM_WAIT_TIME = 500
    QEMU_VM_WAIT_TIME = 60
    LIST_OF_MOUNT_DEVICE = []
    LIST_OF_POOL = []
    LIST_OF_POOL_VOL = defaultdict(list)
    LIST_OF_VM_NAMES = []
    LIST_OF_NESTED_VM_NAMES = []
    REBOOT_VM_COMMAND = "virsh reboot {}"
    VM_DISK_NAME = "vdb"
    STR_ENABLE = "enable"
    STR_SHUT_OFF = "shut off"
    STR_RUNNING = "running"
    START_VM_CMD = "virsh start {}"
    SHUTDOWN_VM_CMD = "virsh shutdown {}"
    ENABLE_AUTO_START_CMD = "virsh autostart {}"
    SET_MAX_MEMORY_CMD = "virsh setmaxmem {} {}M --config"
    DEFINE_VM_CMD = "virsh define server.xml"
    DUMP_TO_XML_CMD = "virsh dumpxml {} > server.xml"
    UNDEFINE_VM_CMD = "virsh undefine {}"
    CONSOLE_VM_CMD = "virsh console {}"
    _REGEX_TO_FETCH_PCIE_DBSF_VALUES = r'\b([0-9a-fA-F]{4}:[0-9a-fA-F]{2}:[0-9a-fA-F]{2}.\d{1}\S*)'
    READ_IP_ADDRESS_ALL = r"ifconfig | grep -Eo 'inet ?([0-9]*\.){3}[0-9]*' | grep -Eo '([0-9]*\.){3}[0-9]*'"
    ROOT_PATH = "/root"
    TEST_VM_FILE_NAME = "vm_test_file.txt"
    KVM_UNIT_TEST_FILE_NAME = "kvm-unit-tests-master.tar"
    INTEL_IOMMU_ON_STR_VM = r"intel_iommu=on,sm_on iommu=pt no5lvl idle=poll"
    INTEL_IOMMU_ON_STR = r"intel_iommu=on,sm_on iommu=on"
    VIRT_HOST_VALIDATE_CMD = "virt-host-validate"
    CHECK_INTEL_IOMMU_REGEX = "Checking if IOMMU is enabled by kernel.*PASS"
    KVM_UNIT_TEST_CONFIGURATION_COMMANDS = ["modprobe -r kvm_intel",
                                            "modprobe kvm_intel nested=1"]
    KVM_NESTED_COMMAND = "cat /sys/module/kvm_intel/parameters/nested"
    KVM_UNIT_TEST_INSTALL_COMMANDS = ["./configure", "make standalone"]
    KVM_UNIT_TESTS_STR = "kvm-unit-tests-master"
    KVM_UNIT_TEST_VMX_COMMAND = "./tests/vmx"
    KVM_UNIT_TEST_SMAP_COMMAND = "./tests/smap"
    KVM_UNIT_TEST_ACCESS_COMMAND = "./tests/access"
    KVM_UNIT_TEST_INTEL_IOMMU_COMMAND = "./tests/intel_iommu"
    KVM_UNIT_TEST_REALMODE_COMMAND = "./tests/realmode"
    REPOS_FOLDER_PATH_SUT = "/etc/yum.repos.d"
    PROXY_STR = "proxy={}".format(CommonConstants.HTTP_PROXY)
    YUM_CONF_FILE_PATH = "/etc/yum.conf"
    VCENTER_USERNAME = "Administrator@vsphere.local"
    VCENTER_PASSWORD = "Intel@123"
    ENABLE_YUM_REPO_COMMANDS = ["yum clean all", " yum makecache", " yum search pciutils-devel"]
    CREATE_SNAPSHOT_COMMAND = "virsh snapshot-create-as --domain {} --name {}"
    RESTORE_SNAPSHOT_COMMAND = "virsh snapshot-revert {} {}"
    DELETE_SNAPSHOT_COMMAND = "virsh snapshot-delete --domain {} --snapshotname {}"
    PCI_DEVICE_XML_FILE_DATA = """<hostdev mode='subsystem' type='pci' managed='yes'>
                <source>
                    <address domain="{}" bus="{}" slot="{}" function="{}"/>
                </source>
            </hostdev>"""
    PCI_DEVICE_XML_FILE_HEX_DATA = """<hostdev mode='subsystem' type='pci' managed='yes'>
                <source>
                    <address domain="0x{}" bus="0x{}" slot="0x{}" function="0x{}"/>
                </source>
            </hostdev>"""
    PCI_VFIO_DEVICE_XML_FILE_HEX_DATA = """<hostdev mode='subsystem' type='pci' managed='yes'>
                <driver name='vfio'/>
                <source>
                    <address type='pci' domain="0x{}" bus="0x{}" slot="0x{}" function="0x{}"/>
                </source>
            </hostdev>"""
    VQAT_DEVICE_XML_FILE_DATA = """<hostdev mode='subsystem' type='mdev' managed='yes' model='vfio-pci'>
                                <driver name='vfio'/>
                                <source>
                                    <address uuid='{}'/>
                                </source>
                            </hostdev>"""
    MDEV_DEVICE_XML_FILE_DATA = """<hostdev mode='subsystem' type='mdev' managed='yes' model='vfio-pci'>
                                <source>
                                    <address uuid='{}'/>
                                </source>
                            </hostdev>"""
    PCI_DEVICE_XML_FILE_NAME = "pci_device.xml"
    MDEV_DEVICE_XML_FILE_NAME = "mdev_device.xml"
    VQAT_DEVICE_XML_FILE_NAME = "vqat_device.xml"
    KVM_UNIT_TEST_EXECUTION_TIMEOUT = 300
    VM_CREATE_WAIT_TIMEOUT = 1200  #20*60
    SHUTDOWN_VM_COMMAND = "virsh shutdown {}"
    RESUME_VM_COMMAND = "virsh resume {}"
    REBOOT_VM_COMMAND = "virsh reboot {}"
    CLONE_VM_COMMAND = "virt-clone --original {} --name {} --auto-clone"

    ASSIGN_STATIC_IP_COMMAND = r"ifconfig {} {} netmask {}"
    STATIC_IP = "10.10.10.1{}"
    REMOVE_STATIC_IP_COMMAND = r"ifconfig {} 0.0.0.0"
    NETMASK = "255.255.255.0"
    SYSTEM_IP_COMMAND = "ipconfig"
    REGEX_CMD_FOR_SYSTEM_IP = r"IPv4\sAddress.*:.*192.*"
    NETWORK_INTERFACE_COMMAND_L = "nmcli device status"
    NETWORK_INTERFACE_COMMAND_W = "netsh interface show interface"
    NETWORK_INTERFACE_COMMAND_E = "esxcfg-nics -l"
    REGEX_CMD_FOR_NETWORK_ADAPTER_NAME = r".*Connected.*"
    NETWORK_ADAPTER_COMMAND = 'netsh interface set interface "{}" {}'
    REGEX_CMD_FOR_NETWORK_ADAPTER_INTERFACE_IP = r"IPv4\sAddress.*:.*"
    ADAPTER_NAME = None
    NETWORK_ASSIGNMENT_TYPE = "DDA"
    VSWITCH_NAME = "ExternalSwitch"

    REGEX_CMD_FOR_NW_ADAPTER_NAME = r"ethernet\s.*\s.*"
    REGEX_CMD_FOR_ALL_NETWORK_ADAPTER_NAME = r".*\sethernet\s.*\s*\n"
    SYSTEM_IP_COMMAND_DEVICE = "ifconfig {}"
    REGEX_CMD_FOR_SYSTEM_IP_INET = r"inet.*.*"
    REGEX_FOR_NW_ADAPTER_INTERFACE = r".*ethernet.*\sconnected.*"
    REGEX_FOR_NW_BRIDGE_INTERFACE = r".*bridge.*\sconnected.*"
    WAITING_TIME_IN_SEC = 30
    REGEX_FOR_DATA_LOSS = r".*sec.*0.00.*Bytes.*0.00.*bits.sec$"

    REGEX_TO_VALIDATE_FIO_OUTPUT = r'\serr=\s0'
    FIO_CMD = r'fio -filename=/dev/sda3 -direct=1 -iodepth 1 -thread -rw=randrw -rwmixread=70 -ioengine=psync -bs=4k ' \
              r'-size=300G -numjobs=50 -runtime=180 -group_reporting -name=randrw_70read_4k'
    MOUNT_POINT = ""
    CMD_FDISK = 'fdisk -l'
    IP_ADDRESS_SUT = "ip route get 1.2.3.4 | awk '{print $7}'"
    NVME_DISK_INFO_REGEX = ".*\/dev\/nvme0n1:\s(\S+.\S+)"
    NVME1_DISK_INFO_REGEX = ".*\/dev\/nvme1n1:\s(\S+.\S+)"
    SATA_DISK_INFO_REGEX = ".*\/dev\/sda:\s(\S+.\S+)"
    REGEX_CMD_FOR_ADAPTER_IP = r"inet.*netmask.*broadcast.*"
    GENERATING_VIRTUAL_ADAPTER_CMD = "echo {} > /sys/class/net/{}/device/sriov_numvfs"
    VERIFYING_VIRTUAL_ADAPTER_CMD = "lspci |grep net"
    REGEX_CMD_FOR_VERIFYING_VIRTUAL_ADAPTER = r".*Ethernet\scontroller.*Virtual\sFunction.*"
    STATIC_IP_FOR_VIRTUAL_ADAPTER = "20.20.20.2{}"

    REGEX_CMD_FOR_ADAPTER_IP_PINGABLE = r".*bytes\sfrom.*icmp_seq.*ttl.*time.*"

    RESET_VIRTUAL_ADAPTER_CMD = "echo 0 > /sys/class/net/{}/device/sriov_numvfs"
    REGEX_CMD_FOR_IPV6 = "inet6.*"
    FOXVILLE_DEVICE_ID = "15f2"
    VF_MODULE_STR = "iavf"
    TEMPLATE_MAC_ID = "AA:BB:CC:EE:FF:00"

    ATTACH_USB_DEVICE_COMMAND = " virsh attach-device {} --file {} --current"
    DETACH_USB_DEVICE_COMMAND = " virsh detach-device {} --file {} --current"
    CREATE_STORAGE_POOL = "virsh pool-define-as {} --type dir --target {}"
    START_STORAGE_POOL = "virsh pool-start {}"
    AUTOSTART_STORAGE_POOL = "virsh pool-autostart {}"
    STORAGE_POOL_INFO = "virsh pool-info {} | awk '/Available:*/ {{print $2 $3}}'"
    COLLATERAL_DIR_NAME = 'collateral'
    GET_VIRTUAL_NET_ADAPTER_CMD = "lshw -class network -businfo | grep -i 'Ethernet' | cut -d' ' -f3"
    GET_VIRTUAL_NET_ADAPTER_CMD1 ="lshw -class network -businfo | grep -i E810 | cut -f1 -d' '"
    GET_VIRTUAL_FUNCTION_MAC_ADDR = "virsh nodedev-list | grep .*v.*"
    GET_VF_NET_ADAPTER_NAME = "lshw -class network -businfo | grep 'Virtual Function' | cut -f3 -d' '"
    HQM_DEVICE_ID = "2710"

    VF_MODULE_STR = "iavf"
    TEMPLATE_MAC_ID = "AA:BB:CC:EE:FF:00"
    CVL_ICE_DRIVER_FILE_NAME = "ice-1.5.0_rc35_24_g9904f5da_dirty.tar.gz"
    CVL_IAVF_DRIVER_FILE_NAME = "iavf-4.2.7.tar.gz"
    UNTAR_FILE_CMD = r"tar -xvf {}"
    MDEV_PATH = "/sys/class/mdev_bus/"

    LDB_TRAFFIC_FILE_CMD = r"ldb_traffic -n 1024 -w poll"
    LDB_REGEX_TX = r"Sent\s(\d+)\sevents"
    LDB_REGEX_RX = r"Received\s(\d+)\sevents"

    CPU_INFO = "lscpu"
    THREADS_CORE_SOCKET = "Thread\(s\)\sper core:\s+([0-9]+)"
    CORE_SOCKET = "Core\(s\)\sper socket:\s+([0-9]+)"
    SOCKET = "Socket\(s\):\s+([0-9]+)"
    vm_create_thread_list = []
    vm_create_key_lock = threading.Lock()

    MLC_TOOL_CMD = "./mlc"
    MLC_STR = "mlc"
    MLC_DELAY_TIME_SEC = 30
    MLC_COMMAND_LINUX = "./mlc_script.sh | tee -a {}"

    PTU_CPU_TEST = "ct"
    PTU_CPU_TEST_CORE_IA_SSE_TEST = "3"
    PTU_START_DELAY_SEC = 3

    PRIME_TOOL = "prime95.tar.gz"
    CAT_COMMAND = "cat {}"
    _mlc_runtime = 10
    QAT_DEVICE_NUM = 4
    DLB_DEVICE_NUM = 4
    DSA_DEVICE_NUM = 4
    IAX_DEVICE_NUM = 4
    DEVICE_ID = {
        'EGS': {
            'QAT_DEVICE_ID': '4940',
            'DLB_DEVICE_ID': '2710',
            'DSA_DEVICE_ID': '0b25',
            'IAX_DEVICE_ID': '0cfe',
            'QAT_VF_DEVICE_ID': '4941',
            'DLB_VF_DEVICE_ID': '2711',
            'DSA_MDEV_DEVICE_ID': '',
            'IAX_MDEV_DEVICE_ID': '',
            'QAT_MDEV_DEVICE_ID': '0da5',
            'DLB_MDEV_DEVICE_ID': '',
        },
        'BHS': {
            'QAT_DEVICE_ID': '4944',
            'DLB_DEVICE_ID': '2714',
            'DSA_DEVICE_ID': '0b25',
            'IAX_DEVICE_ID': '0cfe',
            'QAT_VF_DEVICE_ID': '4945',
            'DLB_VF_DEVICE_ID': '2715',
            'DSA_MDEV_DEVICE_ID': '',
            'IAX_MDEV_DEVICE_ID': '',
            'QAT_MDEV_DEVICE_ID': '0da5',
            'DLB_MDEV_DEVICE_ID': '',
        }
    }

    def __init__(self, test_log, arguments, cfg_opts, create_bridge=True, os_obj = None):
        self.create_bridge = create_bridge
        super(VirtualizationCommon, self).__init__(test_log, arguments, cfg_opts)
        if os_obj is None:
            os_obj = self.os
        sut_ssh_cfg = cfg_opts.find(SshSutOsProvider.DEFAULT_CONFIG_PATH)
        self.sut_ssh = ProviderFactory.create(sut_ssh_cfg, test_log)  # type: SutOsProvider
        self.sut_user = self.sut_ssh._config_model.driver_cfg.user
        self.sut_pass = self.sut_ssh._config_model.driver_cfg.password
        self.sut_ip = self.sut_ssh._config_model.driver_cfg.ip
        self._vm_provider = VMProvider.factory(test_log, cfg_opts, os_obj)
        self._common_content_lib = CommonContentLib(self._log, os_obj, cfg_opts)
        self._sut_os = self.os.os_type.lower()
        self._cfg_opts = cfg_opts
        self.vcenter_ip = self._common_content_configuration.get_vcenter_ip()
        self.VCENTER_USERNAME = self._common_content_configuration.get_vcenter_username()
        self.VCENTER_PASSWORD = self._common_content_configuration.get_vcenter_password()
        self._reboot_timeout = self._common_content_configuration.get_reboot_timeout()
        self._install_collateral = InstallCollateral(test_log, os_obj, cfg_opts)
        self._artifactory_obj = ContentArtifactoryUtils(test_log, os_obj, self._common_content_lib, cfg_opts)
        self.network_interface_name = self.get_network_interface_name_all()
        self.network_interface_dict = self.get_network_adapter_interfaces()
        self._ldb_traffic_data = self._common_content_configuration.get_hqm_ldb_traffic_data()
        self.virtual_network_interface_list = []
        self.cmd_for_iperf_client = r"iperf3 -c {} -t {}"
        self.cmd_for_iperf_server = "iperf3 -s -i 1"
        self.cmd_for_iperf_client_with_port = r"iperf3 -c {} -p {} -t {} -i 1 -b 5M -P 4"
        self.cmd_for_iperf_client_with_port_esxi = r"iperf3 -c {} -p {} -t {}"
        self.cmd_for_iperf_server_with_port = "iperf3 -s -p {} -i 4"
        self.cmd_for_iperf_server_with_port_esxi = "./iperf3 -s -p {} -i 1"
        self.cmd_for_iperf_server_esxi = "./iperf3 -s -i 1"
        self.cmd_for_ping = r"ping -f {} -w {} -q"
        #self.INTEL_IOMMU_ON_STR = "intel_iommu=on"
        self.GET_MEMORY_DUMP_CMD = "virsh dumpxml {}|grep -i memo"
        self.GET_ALL_VM_LIST = "virsh list --all"

    def wait_for_vm_create_to_complete_linux(self, vm_name, vm_type="CENTOS", timeout=VM_WAIT_TIME):
        """
        This function is to wait for VM to be created on Linux system by Qemu/virt-install
        :param vm_name Name of VM
        :param timeout
        """
        self._log.info("Waiting {} seconds to boot the VM {} to OS".format(timeout, vm_name))
        ps_cmd = "ps -ef | grep {} | grep 'virt[-install]' | grep -v qemu | grep -v grep".format(vm_name)
        start_time = time.time()
        wait_seconds = timeout
        while True:
            time.sleep(2)
            current_time = time.time()
            elapsed_time = current_time - start_time

            ps_cmd_status = self._common_content_lib.execute_sut_cmd_no_exception(ps_cmd,
                                                                                  "run ps command:{}".format(
                                                                                      ps_cmd),
                                                                                  self._command_timeout,
                                                                                  self.ROOT_PATH,
                                                                                  ignore_result="ignore")

            if ps_cmd_status == "" or vm_name not in ps_cmd_status:
                break

            if elapsed_time > wait_seconds:
                self._log.info("Finished max wait for VM creation: " + str(int(elapsed_time)) + " seconds")
                break

        time.sleep(60)

    def wait_for_vm_os_bootup_linux(self, vm_name, vm_type="CENTOS", timeout=VM_WAIT_TIME):
        """
        This function is to wait for VM to be created on Linux system by Qemu/virt-install
        :param vm_name Name of VM
        :param timeout
        """
        self._log.info("Waiting {} seconds to boot the VM {} OS!".format(timeout, vm_name))
        os_booted = False
        vm_ip = None
        start_time = time.time()
        wait_seconds = timeout
        while True:
            time.sleep(10)
            current_time = time.time()
            elapsed_time = current_time - start_time
            try:
                vm_ip = self.verify_vm_functionality(vm_name, vm_type)
            except:
                if elapsed_time > wait_seconds:
                    self._log.info("Finished max wait for VM creation: " + str(int(elapsed_time)) + " seconds")
                    break
                else:
                    continue
            else:
                time.sleep(15)
                current_time = time.time()
                elapsed_time = current_time - start_time
                # check using ping
                if self.check_and_wait_for_system_bootup(vm_ip, 30) == True:
                    self._log.info("{} OS Booted up successfully after {} sec!".format(vm_name, elapsed_time))
                    break
                else:
                    if elapsed_time > wait_seconds:
                        self._log.info("Finished max wait for VM OS to bootup: " + str(int(elapsed_time)) + " seconds")
                        break
                    else:
                        continue
        time.sleep(15)

    def create_vm_with_bridge(self, vm_name, vm_type, mac_addr=None):
        """
        This method is to create VM according to the given specification

        :param vm_name: name of the VM. ex: RHEL_1 , WINDOWS_1
        :param vm_type: type of VM. ex: RHEL , RS5 (WINDOWS Redstone 5)
        :param mac_addr: if pre-registered MAC address to be used [None or some value/True]
        :return: None
        :raise: None
        """
        # get memory_size, no_of_cpu, os_variant, disk_size
        memory_size = self._common_content_configuration.get_vm_memory_size(self._sut_os, vm_type)
        no_of_cpu = self._common_content_configuration.get_vm_no_of_cpu(self._sut_os, vm_type)
        disk_size = self._common_content_configuration.get_vm_disk_size(self._sut_os, vm_type)
        os_variant = self._common_content_configuration.get_vm_os_variant(self._sut_os, vm_type)
        self._vm_provider.create_vm(vm_name, os_variant, no_of_cpu=no_of_cpu, disk_size=disk_size,
                                    memory_size=memory_size, vm_creation_timeout=2700,
                                    vm_create_async=None, mac_addr=mac_addr, pool_id=None, nw_bridge="bridge")
        self._log.info("Waiting {} seconds to boot the VM to OS".format(self.VM_WAIT_TIME))
        time.sleep(self.VM_WAIT_TIME)

    def create_vm(self, vm_name, vm_type, mac_addr=None):
        """
        This method is to create VM according to the given specification

        :param vm_name: name of the VM. ex: RHEL_1 , WINDOWS_1
        :param vm_type: type of VM. ex: RHEL , RS5 (WINDOWS Redstone 5)
        :param mac_addr: if pre-registered MAC address to be used [None or some value/True]
        :return: None
        :raise: None
        """
        # get memory_size, no_of_cpu, os_variant, disk_size
        memory_size = self._common_content_configuration.get_vm_memory_size(self._sut_os, vm_type)
        no_of_cpu = self._common_content_configuration.get_vm_no_of_cpu(self._sut_os, vm_type)
        disk_size = self._common_content_configuration.get_vm_disk_size(self._sut_os, vm_type)
        os_variant = self._common_content_configuration.get_vm_os_variant(self._sut_os, vm_type)
        self._vm_provider.create_vm(vm_name, os_variant, no_of_cpu=no_of_cpu, disk_size=disk_size,
                                    memory_size=memory_size, vm_creation_timeout=2700,
                                    vm_create_async=None, mac_addr=mac_addr, pool_id=None,
                                    pool_vol_id=None, cpu_core_list = None)
        self._log.info("Waiting {} seconds to boot the VM to OS".format(self.VM_WAIT_TIME))
        time.sleep(self.VM_WAIT_TIME)

    def create_vm_pool(self, vm_name, vm_type, mac_addr=None, pool_id=None):
        """
        This method is to create VM according to the given specification

        :param vm_name: name of the VM. ex: RHEL_1 , WINDOWS_1
        :param vm_type: type of VM. ex: RHEL , RS5 (WINDOWS Redstone 5)
        :param mac_addr: if pre-registered MAC address to be used [None or some value/True]
        :param pool_id: Storage pool id from storage pool created
        :return: None
        :raise: None
        """
        # get memory_size, no_of_cpu, os_variant, disk_size
        memory_size = self._common_content_configuration.get_vm_memory_size(self._sut_os, vm_type)
        no_of_cpu = self._common_content_configuration.get_vm_no_of_cpu(self._sut_os, vm_type)
        disk_size = self._common_content_configuration.get_vm_disk_size(self._sut_os, vm_type)
        os_variant = self._common_content_configuration.get_vm_os_variant(self._sut_os, vm_type)
        self._vm_provider.create_vm(vm_name, os_variant, no_of_cpu=no_of_cpu, disk_size=disk_size,
                                    memory_size=memory_size,vm_creation_timeout=2700,
                                    vm_create_async=None, mac_addr=mac_addr, pool_id=pool_id,
                                    pool_vol_id=None, cpu_core_list = None)
        self._log.info("Waiting {} seconds to boot the VM to OS".format(self.VM_WAIT_TIME))
        time.sleep(self.VM_WAIT_TIME)

    def create_vm_pool_nested(self, vm_name, vm_type, vm_create_async=None, mac_addr=None, pool_id=None,
                              extra_disk_space=None, nesting_level=None):
        """
        This method is to create VM according to the given specification

        :param vm_name: name of the VM. ex: RHEL_1 , WINDOWS_1
        :param vm_type: type of VM. ex: RHEL , RS5 (WINDOWS Redstone 5)
        :param vm_create_async: if VM is Nested VM [None or some value/True ]
        :param mac_addr: if pre-registered MAC address to be used [None or some value/True]
        :param pool_id: Storage pool id from storage pool created
        :param extra_disk_space: extra disk space required for nested VMs
        :return: None
        :raise: None
        """
        # get memory_size, no_of_cpu, os_variant, disk_size
        memory_size = self._common_content_configuration.get_vm_memory_size(self._sut_os, vm_type)
        no_of_cpu = self._common_content_configuration.get_vm_no_of_cpu(self._sut_os, vm_type)
        disk_size = self._common_content_configuration.get_vm_disk_size(self._sut_os, vm_type)
        if extra_disk_space is not None:
            disk_size = disk_size + extra_disk_space
        os_variant = self._common_content_configuration.get_vm_os_variant(self._sut_os, vm_type)
        self._vm_provider.create_vm(vm_name, os_variant, no_of_cpu=no_of_cpu, disk_size=disk_size,
                                    memory_size=memory_size,vm_creation_timeout=2700,
                                    vm_create_async=vm_create_async, mac_addr=mac_addr, pool_id=pool_id,
                                    pool_vol_id=None, cpu_core_list=None, nw_bridge="bridge",
                                    nesting_level=nesting_level)

        self._log.info("Waiting {} seconds to boot the VM to OS".format(self.VM_WAIT_TIME))
        time.sleep(self.VM_WAIT_TIME)

    def __create_vm_generic(self, vm_name, vm_type, vm_parallel=None, vm_create_async=None, mac_addr=None, pool_id=None,
                            pool_vol_id=None, cpu_core_list=None, nw_bridge=None, devlist=[], qemu=None):
        """
        This method is to create VM according to the given specification

        :param vm_name: name of the VM. ex: RHEL_1 , WINDOWS_1
        :param vm_type: type of VM. ex: RHEL , RS5 (WINDOWS Redstone 5)
        :param vm_create_async: if VM is Nested VM [None or some value/True ]
        :param mac_addr: if pre-registered MAC address to be used [None or some value/True]
        :param pool_id: Storage pool id from storage pool created
        :param pool_vol_id: Storage pool Volume id from storage volume created in the given pool
        :param cpu_core_list: CPU core list to be assigned to VM with --cpuset
        :return: None
        :raise: None
        """
        # get memory_size, no_of_cpu, os_variant, disk_size
        self._log.info(" __create_vm_generic called for VM:{}.".format(vm_name))
        if vm_parallel is not None and pool_vol_id is None:
            self.vm_create_key_lock.acquire()
        memory_size = self._common_content_configuration.get_vm_memory_size(self._sut_os, vm_type)
        disk_size = self._common_content_configuration.get_vm_disk_size(self._sut_os, vm_type)
        if cpu_core_list is None:
            cpu_core_list = "auto"
            no_of_cpu = self._common_content_configuration.get_vm_no_of_cpu(self._sut_os, vm_type)
        else:
            cpu = cpu_core_list.split("-")
            if len(cpu) == 2:
                # cpu_list = list(range(int(cpu[0]), int(cpu[1])))
                no_of_cpu = int(cpu[1]) - int(cpu[0]) + 1
            elif len(cpu) > 2:
                cpu = cpu_core_list.split("-")
                cpu0 = cpu[0].split(",")
                cpu1 = cpu[1].split(",")
                no_of_cpu = len(cpu0) + len(cpu1) + 1
            else:
                no_of_cpu = self._common_content_configuration.get_vm_no_of_cpu(self._sut_os, vm_type)
        # cpu_core_list = "auto"
        os_variant = self._common_content_configuration.get_vm_os_variant(self._sut_os, vm_type)
        self._vm_provider.create_vm(vm_name, os_variant, no_of_cpu=no_of_cpu, disk_size=disk_size,
                                    memory_size=memory_size,vm_creation_timeout=2700,
                                    vm_create_async=vm_create_async, mac_addr=mac_addr, pool_id=pool_id,
                                    pool_vol_id=pool_vol_id, cpu_core_list = cpu_core_list,
                                    nw_bridge=nw_bridge, devlist=devlist, qemu=qemu)

        if vm_parallel is not None or vm_create_async is not None:
            time.sleep(5)
            if vm_parallel is not None and pool_vol_id is None:
                self.vm_create_key_lock.release()

            ps_cmd = "ps -ef | grep {} | grep 'virt[-install]' | grep -v qemu | grep -v grep".format(vm_name)
            start_time = time.time()
            wait_seconds = self.VM_CREATE_WAIT_TIMEOUT
            while True:
                time.sleep(1)
                current_time = time.time()
                elapsed_time = current_time - start_time

                ps_cmd_status = self._common_content_lib.execute_sut_cmd_no_exception(ps_cmd,
                                                                                       "run ps command:{}".format(
                                                                                           ps_cmd),
                                                                                       self._command_timeout,
                                                                                       self.ROOT_PATH,
                                                                                       ignore_result="ignore")

                if ps_cmd_status == "" or vm_name not in ps_cmd_status:
                    break

                if elapsed_time > wait_seconds:
                    self._log.info("Finished max wait for VM creation: " + str(int(elapsed_time)) + " seconds")
                    break
            # self._log.info("Waiting {} seconds to boot the VM to OS".format(self.VM_WAIT_TIME))
            if elapsed_time < wait_seconds and "linux" in self._sut_os.lower():
                self.wait_for_vm_os_bootup_linux(vm_name, vm_type=vm_type, timeout=self.VM_WAIT_TIME)
        else:
            if qemu != None:
                self._log.info("Waiting {} seconds to boot the Qemu VM to OS".format(self.QEMU_VM_WAIT_TIME))
                time.sleep(self.QEMU_VM_WAIT_TIME)
            else:
                self._log.info("Waiting {} seconds to boot the VM to OS".format(self.VM_WAIT_TIME))
                # time.sleep(self.VM_WAIT_TIME)
                self.wait_for_vm_os_bootup_linux(vm_name, vm_type=vm_type, timeout=self.VM_WAIT_TIME)

        if "linux" in self._sut_os.lower() and ("rs5" in vm_name.lower() or "windows" in vm_name.lower()):
            self.reboot_linux_vm(vm_name)
            time.sleep(30)

    def create_vm_qemu_generic(self, vm_name, vm_type, vm_parallel=None, vm_create_async=None, mac_addr=None, pool_id=None,
                               pool_vol_id=None, cpu_core_list=None, nw_bridge=None, devlist=[]):
        """
        This method is to create VM according to the given specification

        :param vm_name: name of the VM. ex: RHEL_1 , WINDOWS_1
        :param vm_type: type of VM. ex: RHEL , RS5 (WINDOWS Redstone 5)
        :param vm_create_async: if VM is Nested VM [None or some value/True ]
        :param mac_addr: if pre-registered MAC address to be used [None or some value/True]
        :param pool_id: Storage pool id from storage pool created
        :param pool_vol_id: Storage pool Volume id from storage volume created in the given pool
        :param cpu_core_list: CPU core list to be assigned to VM with --cpuset
        :return: None
        :raise: None
        """
        vm_thread = None
        if vm_parallel is not None:
            # Trigger VM creation in a thread
            vm_thread = threading.Thread(target=self.__create_vm_generic,
                                         args=(vm_name, vm_type, vm_parallel,
                                               vm_create_async, mac_addr, pool_id, pool_vol_id, cpu_core_list,
                                               nw_bridge, devlist, "qemu"))
            vm_thread.start()
            self._log.info(" Started VM creation thread for VM:{}.".format(vm_name))
            self.vm_create_thread_list.append(vm_thread)
        else:
            # Trigger VM creation in sequential manner
            self.__create_vm_generic(vm_name=vm_name, vm_type=vm_type, vm_parallel=vm_parallel,
                                     vm_create_async=vm_create_async,
                                     mac_addr=mac_addr, pool_id=pool_id, pool_vol_id=pool_vol_id,
                                     cpu_core_list=cpu_core_list, nw_bridge=nw_bridge, devlist=devlist, qemu="qemu")

        ssh_port = self._vm_provider.get_ssh_port_qemu_vm_linux(vm_name)
        if ssh_port != None:
            ip_show = "ip addr show | awk '/inet.*brd.*dynamic/{print $2; exit}'"
            result_cmd_for_ip = self.virt_com_exec_cmd_on_qemu_vm(vm_name, cmd=ip_show,
                                                                  cmd_str="Getting Network ip : {}".format(
                                                                  ip_show),
                                                                  cmd_path="/",
                                                                  execute_timeout=self._command_timeout)
            if not result_cmd_for_ip:
                self._log.error("Unable to get the current network info : {}".format(result_cmd_for_ip))
            else:
                self._log.info("Current network info fetched, IP: {}".format(result_cmd_for_ip))
        return vm_thread

    def create_vm_generic(self, vm_name, vm_type, vm_parallel=None, vm_create_async=None, mac_addr=None, pool_id=None,
                            pool_vol_id=None, cpu_core_list=None, nw_bridge = None):
        """
        This method is to create VM according to the given specification

        :param vm_name: name of the VM. ex: RHEL_1 , WINDOWS_1
        :param vm_type: type of VM. ex: RHEL , RS5 (WINDOWS Redstone 5)
        :param vm_create_async: if VM is Nested VM [None or some value/True ]
        :param mac_addr: if pre-registered MAC address to be used [None or some value/True]
        :param pool_id: Storage pool id from storage pool created
        :param pool_vol_id: Storage pool Volume id from storage volume created in the given pool
        :param cpu_core_list: CPU core list to be assigned to VM with --cpuset
        :return: None
        :raise: None
        """
        vm_thread = None
        devlist=[]
        if vm_parallel is not None:
            # Trigger VM creation in a thread
            vm_thread = threading.Thread(target=self.__create_vm_generic,
                                              args=(vm_name, vm_type, vm_parallel,
                                              vm_create_async, mac_addr, pool_id, pool_vol_id, cpu_core_list,
                                              nw_bridge, devlist,
                                              None))
            vm_thread.start()
            self._log.info(" Started VM creation thread for VM:{}.".format(vm_name))
            self.vm_create_thread_list.append(vm_thread)
        else:
            # Trigger VM creation in sequential manner
            self.__create_vm_generic(vm_name=vm_name, vm_type=vm_type, vm_parallel=vm_parallel,
                                     vm_create_async=vm_create_async,
                                     mac_addr=mac_addr, pool_id=pool_id, pool_vol_id=pool_vol_id,
                                     cpu_core_list = cpu_core_list, nw_bridge = nw_bridge, devlist=devlist, qemu=None)

        return vm_thread

    def create_vm_wait(self, thread_list=None):
        if thread_list is None:
            thread_list = self.vm_create_thread_list
        for index, thread_vm in enumerate(thread_list):
            self._log.info(" Waiting for thread for VM:{}.".format(index))
            thread_vm.join()
            self._log.info(" Cleaned thread for VM:{}.".format(index))
        time.sleep(self.VM_WAIT_TIME)

    def create_hyperv_vm(self, vm_name, vm_type, vm_memory=None, vhd_dir_path=None):
        """
        This method is to create VM according to the given specification

        :param vm_name: name of the VM. ex: RHEL_1 , WINDOWS_1
        :param vm_type: type of VM. ex: RHEL , RS5 (WINDOWS Redstone 5)
        :param vm_memory: Memory for VM
        :param vhd_dir_path: drive directory to create VM
        :return: None
        :raise: None
        """
        # get memory_size, no_of_cpu, os_variant, disk_size
        if vm_memory is None:
            memory_size = self._common_content_configuration.get_vm_memory_size(self._sut_os, vm_type)
        else:
            memory_size = vm_memory
        no_of_cpu = self._common_content_configuration.get_vm_no_of_cpu(self._sut_os, vm_type)
        disk_size = self._common_content_configuration.get_vm_disk_size(self._sut_os, vm_type)
        os_variant = self._common_content_configuration.get_vm_os_variant(self._sut_os, vm_type)
        self._vm_provider.create_vm(vm_name, os_variant, no_of_cpu=no_of_cpu, disk_size=disk_size,
                                    memory_size=memory_size, vm_os_subtype=vm_type, vhdx_dir_path=vhd_dir_path)
        self._log.info("Starting VM:".format(vm_name))
        self._vm_provider.start_vm(vm_name)

    def update_vm_cpu_affinity_vmware(self, vm_name, cpu_core_list, num, cores_per_socket):
        """
        This function is to set CPU affinity for a VM in ESXi platforms.
        Get-VM vm02 | Get-VMResourceConfiguration | Set-VMResourceConfiguration -CpuAffinityList 4,5,6,7
        vm_name: Name of the VM
        cpu_core_list: list of cpu cores to be assigned to VM, e.g. 0-30, 20-40, 180-190, for future : "0-5,8,10"
        return: stdout, stderr
        """
        # create "'" separated string with cpu list
        cpu_list = ""
        cpu_num = ""
        cpu_start = int(cpu_core_list.split("-")[0].strip())
        cpu_end = int(cpu_core_list.split("-")[1].strip())
        for cpu in range(cpu_start, cpu_end + 1):
            if cpu_end == cpu:
                cpu_str = "{}".format(cpu)
            else:
                cpu_str = "{},".format(cpu)
            cpu_list = cpu_list + cpu_str

        self.shutdown_vm_esxi(vm_name)  # probably not needed
        out, err = self.virt_execute_host_cmd_esxi(
            f'Get-VM {vm_name} | Get-VMResourceConfiguration | Set-VMResourceConfiguration -CpuAffinityList {cpu_list}')

        out_split = str(out).split("\\r\\n")
        if len(out_split) > 1:
            self._log.info("Set CPU Affinity to vm successful")
            for line in out_split:
                self._log.info("{}".format(line))
        else:
            self._log.info("Set CPU Affinity to vm successful {}".format(out))
        result1, err1 = self.virt_execute_host_cmd_esxi(f'Get-VM {vm_name} | Set-VM -NumCpu {num} -Confirm:$false')
        self._log.info('CLI exec successfully and returns a zero return code {}'.format(result1))
        result11, err11 = self.virt_execute_host_cmd_esxi(f'Get-VM {vm_name} | Set-VM -CoresPerSocket {cores_per_socket}  -Confirm:$false')
        self._log.info('CLI exec successfully and returns a zero return code {}'.format(result11))
        self.start_vm_esxi(vm_name)  # probably not needed
        return out, err

    def create_vmware_vm_generic(self, vm_name, vm_type, vm_parallel=None, vm_create_async=None, mac_addr=None, pool_id=None,
                            pool_vol_id=None, cpu_core_list=None, nw_bridge = None, use_powercli=None):
        """
        This method is to create VM according to the given specification

        :param vm_name: name of the VM. ex: RHEL_1 , WINDOWS_1
        :param vm_type: type of VM. ex: RHEL , RS5 (WINDOWS Redstone 5)
        :param vm_create_async: if VM is Nested VM [None or some value/True ]
        :param mac_addr: if pre-registered MAC address to be used [None or some value/True]
        :param pool_id: Storage pool id from storage pool created
        :param pool_vol_id: Storage pool Volume id from storage volume created in the given pool
        :param cpu_core_list: CPU core list to be assigned to VM with --cpuset
        :return: None
        :raise: None
        """
        vm_thread = None
        devlist=[]
        if vm_parallel is not None:
            # Trigger VM creation in a thread
            vm_thread = threading.Thread(target=self.__create_vmware_vm_generic,
                                              args=(vm_name, vm_type, vm_parallel,
                                              vm_create_async, mac_addr, pool_id, pool_vol_id, cpu_core_list,
                                              nw_bridge, devlist, use_powercli,
                                              None))
            vm_thread.start()
            self._log.info(" Started VM creation thread for VM:{}.".format(vm_name))
            self.vm_create_thread_list.append(vm_thread)
        else:
            # Trigger VM creation in sequential manner
            self.__create_vmware_vm_generic(vm_name=vm_name, vm_type=vm_type, vm_parallel=vm_parallel,
                                     vm_create_async=vm_create_async,
                                     mac_addr=mac_addr, pool_id=pool_id, pool_vol_id=pool_vol_id,
                                     cpu_core_list = cpu_core_list, nw_bridge = nw_bridge, devlist=devlist,
                                     use_powercli=use_powercli, qemu=None)

        return vm_thread

    def __create_vmware_vm_generic(self, vm_name, vm_type, vm_parallel=None, vm_create_async=None, mac_addr=None, pool_id=None,
                            pool_vol_id=None, cpu_core_list=None, nw_bridge=None, devlist=[], use_powercli=None, qemu=None):
        """
        This method is to create VM according to the given specification

        :param vm_name: name of the VM. ex: RHEL_1 , WINDOWS_1
        :param vm_type: type of VM. ex: RHEL , RS5 (WINDOWS Redstone 5)
        :param vm_create_async: if VM is Nested VM [None or some value/True ]
        :param mac_addr: if pre-registered MAC address to be used [None or some value/True]
        :param pool_id: Storage pool id from storage pool created
        :param pool_vol_id: Storage pool Volume id from storage volume created in the given pool
        :param cpu_core_list: CPU core list to be assigned to VM with --cpuset
        :return: None
        :raise: None
        """
        # get memory_size, no_of_cpu, os_variant, disk_size
        self._log.info(" __create_vm_generic called for VM:{}.".format(vm_name))
        if vm_parallel is not None:
            pass
            # self.vm_create_key_lock.acquire()
        # memory_size = self._common_content_configuration.get_vm_memory_size(self._sut_os, vm_type)
        # disk_size = self._common_content_configuration.get_vm_disk_size(self._sut_os, vm_type)
        # if cpu_core_list is None:
        #     cpu_core_list = "auto"
        #     no_of_cpu = self._common_content_configuration.get_vm_no_of_cpu(self._sut_os, vm_type)
        # else:
        #     cpu = cpu_core_list.split("-")
        #     if len(cpu) == 2:
        #         # cpu_list = list(range(int(cpu[0]), int(cpu[1])))
        #         no_of_cpu = int(cpu[1]) - int(cpu[0]) + 1
        #     elif len(cpu) > 2:
        #         cpu = cpu_core_list.split("-")
        #         cpu0 = cpu[0].split(",")
        #         cpu1 = cpu[1].split(",")
        #         no_of_cpu = len(cpu0) + len(cpu1) + 1
        #     else:
        #         no_of_cpu = self._common_content_configuration.get_vm_no_of_cpu(self._sut_os, vm_type)
        # cpu_core_list = "auto"
        # os_variant = self._common_content_configuration.get_vm_os_variant(self._sut_os, vm_type)
        # self._vm_provider.create_vm(vm_name, os_variant, no_of_cpu=no_of_cpu, disk_size=disk_size,
        #                             memory_size=memory_size,vm_creation_timeout=2700,
        #                             vm_create_async=vm_create_async, mac_addr=mac_addr, pool_id=pool_id,
        #                             pool_vol_id=pool_vol_id, cpu_core_list = cpu_core_list,
        #                             nw_bridge=nw_bridge, devlist=devlist, qemu=qemu)

        self.create_vmware_vm(vm_name=vm_name, vm_type=vm_type, vm_parallel=vm_parallel,
                                     vm_create_async=vm_create_async,
                                     mac_addr=mac_addr, use_powercli=use_powercli)
        if vm_parallel is not None or vm_create_async is not None:
            if vm_parallel is not None:
                pass
                # self.vm_create_key_lock.release()

            start_time = time.time()
            wait_seconds = self.VM_CREATE_WAIT_TIMEOUT
            while True:
                cmd = "$vm = get-vm {}; Start-Sleep -Seconds 30;$tm=0;" \
                      "$vm | Get-VMQuestion | Set-VMQuestion -DefaultOption -confirm:$false;" \
                      "do {{ Start-Sleep -Seconds 5; $tm = $tm + 5;" \
                      "$vm = get-vm {}; $vm | Get-VMQuestion | Set-VMQuestion -DefaultOption -confirm:$false;" \
                      "$toolsStatus = $vm.extensionData.Guest.ToolsStatus;}}" \
                      " while($toolsStatus -ne 'toolsOK' -And $tm -le {}); echo $toolsStatus;".format(vm_name, vm_name, int(self.VM_WAIT_TIME/4))
                cmd_tool_status_out, err = self.virt_execute_host_cmd_esxi(cmd=cmd, cwd=".", timeout=self.VM_WAIT_TIME)
                cmd = "Start-Sleep -Seconds 2;"
                self.virt_execute_host_cmd_esxi(cmd=cmd, cwd=".", timeout=60)

                current_time = time.time()
                elapsed_time = current_time - start_time

                if "toolsOK" in cmd_tool_status_out:
                    self._log.info("VM {} up and running ".format(vm_name) + str(int(elapsed_time)) + " seconds")
                    break

                if elapsed_time > wait_seconds:
                    self._log.info("Finished max wait for VM {} creation: ".format(vm_name) + str(int(elapsed_time)) + " seconds")
                    break
        else:
            self._log.info("Waiting {} seconds to boot the VM {} to OS".format(self.VM_WAIT_TIME, vm_name))
            self._vm_provider.wait_check_for_vm_to_bootup_esxi(vm_name, self.VM_WAIT_TIME)
        # why do we need to restart the VM again as below id doing, do we need to remove it ???
        self.start_vm_esxi(vm_name)

    def create_vmware_vm(self, vm_name, vm_type, vm_parallel=None, vm_create_async=None, mac_addr=None,
                         use_powercli=None):
        """
        This method is to create VM according to the given specification

        :param vm_name: name of the VM. ex: RHEL_1 , WINDOWS_1
        :param vm_type: type of VM. ex: RHEL , RS5 (WINDOWS Redstone 5)
        :param mac_addr: if pre-registered MAC address to be used [None or some value/True]
        :return: None
        :raise: None
        """
        memory_size = self._common_content_configuration.get_vm_memory_size(self._sut_os, vm_type)
        no_of_cpu = self._common_content_configuration.get_vm_no_of_cpu(self._sut_os, vm_type)
        disk_size = self._common_content_configuration.get_vm_disk_size(self._sut_os, vm_type)
        os_variant = self._common_content_configuration.get_vm_os_variant(self._sut_os, vm_type)
        os_version = self._common_content_configuration.get_vm_os_variant(self._sut_os, vm_type)
        # self._common_content_configuration.get_vm_kernel_version(self._sut_os, vm_type)
        if use_powercli == None:
            esxi_guestos_id = self._common_content_configuration.get_vm_esxi_guestos_identifier(self._sut_os,
                                                                                                vm_type)
        else:
            esxi_guestos_id = self._common_content_configuration.get_vm_esxi_guestos_pwrcli_identifier(self._sut_os,
                                                                                                       vm_type)

        if vm_parallel is not None and mac_addr is not None:
            self._vm_provider.create_vm(vm_name, os_variant=esxi_guestos_id, no_of_cpu=no_of_cpu, disk_size=disk_size,
                                        memory_size=memory_size, vm_creation_timeout=2700,
                                        vm_parallel=vm_parallel, vm_create_async=vm_create_async, mac_addr=mac_addr,
                                        os_version=os_version,
                                        use_powercli=use_powercli)

        elif vm_parallel is not None and mac_addr is None:
            self._vm_provider.create_vm(vm_name, os_variant=esxi_guestos_id, no_of_cpu=no_of_cpu, disk_size=disk_size,
                                        memory_size=memory_size, vm_creation_timeout=2700,
                                        vm_parallel=vm_parallel, vm_create_async=vm_create_async, mac_addr=mac_addr,
                                        os_version=os_version,
                                        use_powercli=use_powercli)

        elif vm_parallel is None and mac_addr is not None:
            self._vm_provider.create_vm(vm_name, os_variant=esxi_guestos_id, no_of_cpu=no_of_cpu, disk_size=disk_size,
                                        memory_size=memory_size, vm_creation_timeout=2700,
                                        vm_create_async=None, mac_addr=mac_addr, os_version=os_version,
                                        use_powercli=use_powercli)
        else:
            self._vm_provider.create_vm(vm_name, os_variant=esxi_guestos_id, no_of_cpu=no_of_cpu, disk_size=disk_size,
                                        memory_size=memory_size, vm_creation_timeout=2700,
                                        vm_create_async=None, mac_addr=None, os_version=os_version,
                                        use_powercli=use_powercli)

    def create_hyperv_vm_pool_mac(self, vm_name, vm_type, vm_memory=None, pool_id=None, mac_addr=None):
        """
        This method is to create VM according to the given specification

        :param vm_name: name of the VM. ex: RHEL_1 , WINDOWS_1
        :param vm_type: type of VM. ex: RHEL , RS5 (WINDOWS Redstone 5)
        :return: None
        :raise: None
        """
        # get memory_size, no_of_cpu, os_variant, disk_size
        if vm_memory is None:
            memory_size = self._common_content_configuration.get_vm_memory_size(self._sut_os, vm_type)
        else:
            memory_size = vm_memory
        no_of_cpu = self._common_content_configuration.get_vm_no_of_cpu(self._sut_os, vm_type)
        disk_size = self._common_content_configuration.get_vm_disk_size(self._sut_os, vm_type)
        os_variant = self._common_content_configuration.get_vm_os_variant(self._sut_os, vm_type)
        self._vm_provider.create_vm(vm_name, os_variant, no_of_cpu=no_of_cpu, disk_size=disk_size,
                                    memory_size=memory_size, vm_creation_timeout=2700,
                                    vm_create_async=None, mac_addr=mac_addr, pool_id=pool_id)
        self._log.info("Starting VM:".format(vm_name))
        self._vm_provider.start_vm(vm_name)

    def wait_for_vm(self, vm_name):
        """
        This method is to wait for VM to boot properly after starting the VM
        """
        self._log.info("Waiting for VM: {} to boot".format(vm_name))
        wait_for_vm_result = self._common_content_lib.execute_sut_cmd(
            self.WAIT_VM_CMD.format(self.SILENT_CONTINUE, vm_name), "Wait for VM to boot", self.VM_TIME_OUT)
        time.sleep(self.WAIT_VM)

    def get_crossvm_ip_linux(self, vm_name):
        """
        Get the IP of the VM using file with name as /home/<MAC address>.txt
        e.g. /home/AA-BB-CC-DD-EE-FF.txt
        param vm_name: Name of Virtual Machine

        return ip_address:ip_address/None
        """
        ip_address = None
        cmd_for_mac = "virsh domiflist {}".format(vm_name)
        result_cmd_for_mac = self._common_content_lib.execute_sut_cmd_no_exception(cmd_for_mac,
                                                                                  "Getting Network info : {}".format(
                                                                                  cmd_for_mac),
                                                                                  self._command_timeout,
                                                                                  ignore_result="ignore")
        if not result_cmd_for_mac:
            self._log.error("Unable to get the current network info")
            return None

        res = re.search(r'([0-9A-F]{2}[:-]){5}([0-9A-F]{2})', result_cmd_for_mac, re.M | re.I)
        if res:
            mac = res.group()

        ip_filename = "/home/{}.txt".format(mac.replace(":","-").upper())
        # opening and reading the file
        result_cat_file = self._common_content_lib.execute_sut_cmd_no_exception("cat {}".format(ip_filename),
                                                                                   "Execute command cat {}".format(
                                                                                       ip_filename),
                                                                                   self._command_timeout,
                                                                                   ignore_result="ignore")
        if not result_cat_file:
            self._log.error("Unable to get the VM network IP info list")
            return None

        # declaring the regex pattern for IP addresses
        pattern = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
        ip_reg = re.compile(r'\d+\:\d+\:\d+\:\d+')
        # initializing the list object
        ip_cat_list = result_cat_file.split("\n")
        ip_lst = []
        # extracting the IP addresses
        for ip_elem in ip_cat_list:
            ip_address_search_res = pattern.search(ip_elem)
            if ip_address_search_res is not None:
                ip_lst.append(ip_address_search_res[0])

        for ip in ip_lst:
            if ip != "127.0.0.1":
                ip_address = ip
                return ip_address

        return ip_address

    def verify_vm_functionality(self, vm_name, vm_type, enable_yum_repo=False):
        """
        This method is to verify VM is functioning or not

        :param vm_name: name of the VM. ex: RHEL_1
        :param vm_type: type of VM. ex: RHEL
        :param enable_yum_repo: Optional param, by default True
        :return: None
        :raise: RuntimeError
        """
        vm_ip = None
        os_variant = self._common_content_configuration.get_vm_os_variant(self._sut_os, vm_type)
        kernel_vr = self._common_content_configuration.get_vm_kernel_version(self._sut_os, vm_type)
        repo_folder_path = self._common_content_configuration.get_yum_repo_name(self._sut_os, vm_type)
        if vm_type == "RS5" or vm_type == "WINDOWS":
            vm_os = self.windows_vm_object(vm_name, vm_type)
            vm_result = vm_os.execute("ipconfig", self._command_timeout)
            vm_ip = self._vm_provider.get_vm_ip(vm_name)
        elif vm_type == "RHEL" or vm_type == "CENTOS":
            if self._vm_provider.check_if_vm_is_qemu_vm(vm_name):
                vm_ip = self._vm_provider.get_qemu_vm_ip(vm_name)
            else:
                vm_ip = self._vm_provider.get_vm_ip(vm_name)
            vm_os = self._vm_provider.create_vm_host(vm_type, os_variant, kernel_vr, self.VM_USERNAME, self.VM_PASSWORD, vm_ip)
            if enable_yum_repo:
                self._enable_yum_repo_in_vm(vm_os, repo_folder_path)
            vm_result = vm_os.execute("ifconfig", self._command_timeout)
        self._log.debug("VM output {}\n".format(vm_result.stdout))
        if vm_ip is not None and vm_ip not in vm_result.stdout:
            raise RuntimeError("Could not get IP to VM")
        self._log.info("Successfully verified VM is working")
        return vm_ip

    def verify_hyperv_vm(self, vm_name, vm_type):
        """
        This method is to verify VM pinging or not

        :param vm_name: name of the VM. ex: windows_0 ,RHEL_0
        :param vm_type: type of VM. ex: RS5 (Windows Redstone 5), RHEL
        :return: None
        :raise: TestFail exception
        """
        self._log.info("Verify VM IP address, and start ping test from SUT")
        vm_ip = self._vm_provider.get_vm_ip(vm_name)
        ping_result = self._vm_provider.ping_vm_from_sut(vm_ip, vm_name, self.WINDOWS_VM_USERNAME, self.WINDOWS_VM_PASSWORD)
        if vm_ip not in ping_result:
            raise content_exceptions.TestFail("{} VM is not pinging".format(vm_name))
        self._log.info("Successfully verified VM is pinging")
        return vm_ip

    def verify_hyperv_functionality(self, vm_name, vm_type, test_range):
        """
        This method is to verify VM is functioning or not

        :param vm_name: name of the VM. ex: RHEL_1 or windows_1
        :param vm_type: type of VM. ex: RHEL or Windows10
        :param test_range: Functionality test cycle
        """
        vm_ip = None
        self._log.info("Performing Hyper-V Basic Functionality for VM {}, {}".format(vm_name, test_range))
        # Performs SUT power cycle and verify VM functionality
        self._log.info("Performs shutdown and boot the SUT")
        self._common_content_lib.perform_graceful_ac_off_on(self.ac_power)
        time.sleep(self.VM_WAIT_TIME)
        vm_ip = self.verify_hyperv_vm(vm_name, vm_type)
        # Performs SUT reboot and verify VM functionality
        self._log.info("Performs SUT reboot")
        try:
            self._common_content_lib.perform_os_reboot(self._reboot_timeout)
        except Exception as ex:
            self._log.error("SUT takes time to reboot due to certain application needs force close")
        self.os.wait_for_os(self._reboot_timeout)
        time.sleep(200)
        vm_ip = self.verify_hyperv_vm(vm_name, vm_type)
        # Performs VM powerycle and verify VM functionality
        self._log.info("Performs VM shutdown and boot operation")
        self._vm_provider._shutdown_vm(vm_name)
        self._vm_provider.start_vm(vm_name)
        time.sleep(200)
        vm_ip = self.verify_hyperv_vm(vm_name, vm_type)
        # Performs VM reboot and verify VM functionality
        self._log.info("Performs VM reboot")
        self._vm_provider.reboot_vm(vm_name)
        time.sleep(200)
        vm_ip = self.verify_hyperv_vm(vm_name, vm_type)
        self._log.info("Successfully verified VM Basic functionality")
        return vm_ip

    def cleanup_storage_pool_vol(self):
        """
        This method is clean all the storage pool and volumes created for VMs
        """
        for pool_index in range(len(self.LIST_OF_POOL)):
            pool_id = self.LIST_OF_POOL[pool_index]
            for pool_vol_index in range(len(self.LIST_OF_POOL_VOL[pool_id])):
                pool_vol_id = self.LIST_OF_POOL_VOL[pool_id][pool_vol_index]
                if self._vm_provider.find_if_storage_pool_vol_exist(pool_id, pool_vol_id):
                    self._vm_provider.delete_storage_pool_vol(pool_id, pool_vol_id)
            if self._vm_provider.find_if_storage_pool_exist(pool_id):
                self._vm_provider.delete_storage_pool(pool_id)

    def update_qat_siov_in_file(self, adis_range, file_path, common_content_object=None):
        """
        This function enable SIOV, rather than SR-IOV enabled by default.
        It will modify PF configure file file_path. Detail steps are list below.
        Modify PF configure file to enable SIOV
        # vim /etc/4xxx_dev0.conf
        # vim /etc/4xxx_dev1.conf
        set as below
        ##############################################
        # ADI Section for Scalable IOV
        ##############################################
        [SIOV]
        NumberAdis = 0 --> NumberAdis = 4      ([1,64] ===> This is range , you can give the desired value)
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        cmd = "fin = open(\"{}\", \"rt\"); data = fin.read();fin.close();" \
        "data = data.replace(\"NumberAdis = 0\", \"NumberAdis = {}\");" \
        "fin = open(\"{}\", \"wt\");fin.write(data);fin.close();exit();".format(file_path, adis_range, file_path)
        common_content_object.execute_sut_cmd("python -c '{}'".format(cmd), "enable SIOV",
                                              self._command_timeout, "/root")

    def stop_and_disable_frewalld_l(self, common_content_lib = None):
        """
        Stop and Disable Firewalld on machine
        """
        if common_content_lib is None:
            common_content_lib = self._common_content_lib
        self._log.info("Stopping and disabling firewall")

        cmd_stop_firewalld = "systemctl stop firewalld"
        cmd_disable_firewalld = "systemctl disable firewalld"

        # execute systemctl stop firewalld cmd
        fw_stop_result = common_content_lib.execute_sut_cmd_no_exception(cmd_stop_firewalld,
                                                                          "executing systemctl stop firewalld",
                                                                          self._command_timeout,
                                                                          cmd_path="/root",
                                                                          ignore_result="ignore")
        self._log.debug("execute systemctl stop firewalld cmd : {}".format(fw_stop_result))

        # execute systemctl disable firewalld cmd
        fw_firewall_result = common_content_lib.execute_sut_cmd_no_exception(cmd_disable_firewalld,
                                                                          "executing systemctl disable firewalld",
                                                                          self._command_timeout,
                                                                          cmd_path="/root",
                                                                          ignore_result="ignore")

        self._log.debug("execute systemctl disable firewalld cmd : {}".format(fw_firewall_result))

    def run_dlb_work_load_vm(self, vm_name, common_content_lib = None):
        """
        Run the dlb workload
        """
        self._install_collateral.run_dlb_workload(vm_name=vm_name, common_content_lib=common_content_lib)

    def run_dlb_work_load_vmware(self, vm_name,vm_parallel = None, common_content_lib=None, runtime=7200):
        """
        Run the dlb workload
        """
        self._install_collateral.run_dlb_workload_vmware(vm_name=vm_name,vm_parallel = vm_parallel, common_content_lib=common_content_lib, runtime=runtime)

    def run_dpdk_work_load_vm(self, vm_name, common_content_lib = None):
        """
        Run the dpdk workload
        """
        self._install_collateral.run_dpdk_workload(vm_name=vm_name, common_content_lib=common_content_lib)

    def run_dlb_work_load(self, common_content_lib = None):
        """
        Run the dlb workload
        """
        self._install_collateral.run_dlb_workload(vm_name=None, common_content_lib=common_content_lib)

    def run_dpdk_work_load(self, common_content_lib = None):
        """
        Run the dpdk workload
        """
        self._install_collateral.run_dpdk_workload(vm_name=None, common_content_lib=common_content_lib)

    def install_hqm_dpdk_library(self, os_obj=None, common_content_lib = None, is_vm=None):
        """
        This function installing the hqm driver library in sut
        """
        #install patch
        if is_vm != None:
            self._install_collateral.install_kernel_rpm_on_linux(os_obj=os_obj, common_content_lib=common_content_lib, is_vm="yes")
        else:
            self._install_collateral.install_kernel_rpm_on_linux()
        self.yum_virt_install(package_group="patch meson boost-devel* cc* gcc* clang*", common_content_lib=common_content_lib, flags="--nobest --skip-broken")
        # install hqm driver and dpdk library
        self._install_collateral.install_hqm_dpdk_driver(common_content_lib = common_content_lib, is_vm=is_vm)

    def install_hqm_driver_library(self, os_obj=None, common_content_lib=None, is_vm=None):
        """
        This function installing the hqm driver library in sut
        """
        #install patch
        if is_vm != None:
            self._install_collateral.install_kernel_rpm_on_linux(os_obj=os_obj, common_content_lib=common_content_lib, is_vm="yes")
        else:
            self._install_collateral.install_kernel_rpm_on_linux()
        self.yum_virt_install(package_group="patch meson boost-devel* cc* gcc* clang*", common_content_lib=common_content_lib, flags="--nobest --skip-broken")
        # install hqm driver library
        self._install_collateral.install_hqm_driver(common_content_lib, is_vm=is_vm)

    def verify_hqm_dlb_kernel(self, common_content_lib = None):
        """
        This function verify the HQM kernel driver in the sut.
        Remove the hqmv2 driver
        """
        regex_kernel_driver = r"Kernel driver in use:\s(.*)"
        lspci_dlb_kernel_cmd = "lspci -v -d :{}".format(self.HQM_DEVICE_ID)
        hqm_kernel = "hqmv2"
        rmmod_cmd = "rmmod"
        if common_content_lib is None:
            common_content_lib = self._common_content_lib
        self._log.info("Verify the hqm kernel driver used in the sut")
        cmd_output = common_content_lib.execute_sut_cmd(lspci_dlb_kernel_cmd, "find the Kernel driver in use"
                                                                                    " the sut", self._command_timeout)
        self._log.debug("lspci command output results {}".format(cmd_output))
        available_kernel_driver = re.findall(regex_kernel_driver, "".join(cmd_output))
        self._log.debug("Present kernel driver in the sut {}".format(available_kernel_driver))
        if not available_kernel_driver:
            self._log.debug("{} kernel driver not available".format(hqm_kernel))
            return
        for kernel_item in available_kernel_driver:
            if kernel_item == hqm_kernel:
                # self.os.execute(rmmod_cmd + " " + hqm_kernel, self._command_timeout)
                common_content_lib.execute_sut_cmd(rmmod_cmd + " " + hqm_kernel,
                                                   "rmmod the hqm kernel driver",
                                                   self._command_timeout)
                self._log.info("Removed the hqmv2 kernel driver from the sut")
                return

    def execute_dlb_traffic(self, common_content_lib = None):
        """
        This function execute dlb_traffic command and verify the tx/rx data events

        :raise: content_exceptions.TestFail If not getting expected tx/rx data events
        """
        if common_content_lib is None:
            common_content_lib = self._common_content_lib
        find_libldb_dir = "find $(pwd) -type d -name 'libdlb'"
        export_cmd = r"export LD_LIBRARY_PATH="
        examples_folder = r"/examples/"
        self._log.info("Execute dlb_traffic command")
        libdlb_dir_path = common_content_lib.execute_sut_cmd(find_libldb_dir, "find the libdlb dir in the sut",
                                                                   self._command_timeout, cmd_path=self.ROOT_PATH)
        self._log.debug("libdlb dir path {}".format(libdlb_dir_path.strip()))

        ldb_traffic_cmd = r"export LD_LIBRARY_PATH={};" \
                            "{}/{}/{};".format(libdlb_dir_path.strip(), libdlb_dir_path.strip(), examples_folder,
                                           self.LDB_TRAFFIC_FILE_CMD)


        ldb_traffic_result = common_content_lib.execute_sut_cmd(ldb_traffic_cmd, "execute ldb traffic command",
                                                              self._command_timeout, cmd_path=self.ROOT_PATH)



        self._log.debug("ldb traffic command results {}".format(ldb_traffic_result))
        ldb_tx_traffic = re.search(self.LDB_REGEX_TX, ldb_traffic_result)
        ldb_rx_traffic = re.search(self.LDB_REGEX_RX, ldb_traffic_result)
        if not (ldb_tx_traffic and ldb_rx_traffic):
            raise content_exceptions.TestFail("Failed to get the TX/RX data events")
        if (ldb_tx_traffic.group(1) != self._ldb_traffic_data) and (ldb_rx_traffic.group(1) != self._ldb_traffic_data):
            raise content_exceptions.TestFail("Failed to get the ldb_traffi TX/RX data events")
        self._log.info("The ldb traffic run successfully without any errors")

    def check_acce_driver_esxi(self, acce_module_name, common_content_object=None):
        if common_content_object is None:
            common_content_object = self._common_content_lib
        command_result = common_content_object.execute_sut_cmd(
            "esxcfg-module -l | grep {}".format(acce_module_name),
            "check for the accelerator driver",
            self._command_timeout)
        self._log.debug("Driver found successfully with output '{}'"
                        .format(command_result))

    def dlb_driver_install_esxi(self, driver_type="sriov", common_content_object=None):
        """
          Purpose: To install QAT driver
          Args:
              No
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Install DLB driver
                  dlb_driver_install_esxi
        """
        dlb_folder_name = "HQM"
        sut_path = "/vmfs/volumes/datastore1/{}/".format(dlb_folder_name)
        if common_content_object is None:
            common_content_object = self._common_content_lib
        command_result = common_content_object.execute_sut_cmd("rm -rf /vmfs/volumes/datastore1/{}".format(dlb_folder_name),
                                                               "Install development tools",
                                                               self._command_timeout)
        dlb_file_name = os.path.split(self._install_collateral.dlb_file_path_esxi)[-1].strip()
        dlb_host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(dlb_file_name)
        dlb_host_path = dlb_host_path.strip()
        # Copy the DLB file to SUT

        sut_folder_path = common_content_object.copy_zip_file_to_esxi(dlb_folder_name, dlb_host_path)
        sut_folder_path = sut_folder_path.strip()
        self._log.info("DLB file is extracted and copied to SUT path {}".format(sut_folder_path))

        self._common_content_lib.execute_sut_cmd(
            "mv /vmfs/volumes/datastore1/{}/dlb_ext_rel_bin_*-dvx.tar.gz "
            "/vmfs/volumes/datastore1/{}/siov_dlb_ext_rel_bin-dvx.tar.gz".format(dlb_folder_name, dlb_folder_name),
            "prefix the siov file name with siov_", 60, cmd_path=sut_path)

        self._common_content_lib.execute_sut_cmd(
            "mv /vmfs/volumes/datastore1/{}/dlb_ext_rel_bin_*.tar.gz "
            "/vmfs/volumes/datastore1/{}/sriov_dlb_ext_rel_bin.tar.gz".format(
                dlb_folder_name, dlb_folder_name),
            "prefix the sriov file name with siov_", 60, cmd_path=sut_path)

        if driver_type == "sriov":
            driver_file_name = "sriov_dlb_ext_rel_bin.tar.gz"
        elif driver_type == "siov":
            driver_file_name = "siov_dlb_ext_rel_bin-dvx.tar.gz"
        else:
            raise content_exceptions.TestSetupError("Invalid driver type, valid options: sriov/siov!")

        self._common_content_lib.execute_sut_cmd("tar -xzf /vmfs/volumes/datastore1/{}/{}".format(dlb_folder_name,
                                                                                                  driver_file_name),
                                                 "untar driver file name", 60,cmd_path=sut_path)
        # Install packages required for DLB
        # Installing Development tools
        try:
            cmand_out = "esxcfg-module -u dlb"
            self._common_content_lib.execute_sut_cmd(cmand_out, "verify dlb", 60)
        except:
            pass
        command_result = common_content_object.execute_sut_cmd(
                "esxcli software component apply --no-sig-check -d /vmfs/volumes/datastore1/{}/*-esx-*-Intel-dlb-*.zip".format(dlb_folder_name),
                "Installed: Intel-dlb",self._command_timeout)
        if command_result is not None:
            self._log.info("Installed: Intel-dlb Operation finished successfully with output '{}'"
                       .format(command_result))
        else:
            self._log.info("DLB driver install failed with output '{}'"
                            .format(command_result))
        cmand_reboot = "reboot"
        self._common_content_lib.execute_sut_cmd(cmand_reboot, "reboot the sut", 60)
        time.sleep(300)
        self.load_driver_esxi()
        self.check_acce_driver_esxi('dlb')

    def dlb_driver_uninstall_esxi(self):
        """
        esxcfg-module -u dlb
        esxcli software component remove -n Intel-dlb
        """
        try:
            self._common_content_lib.execute_sut_cmd("esxcfg-module -u dlb", "check for the driver", 60)
        except:
            pass
        try:
            self._common_content_lib.execute_sut_cmd("esxcli software component remove -n Intel-dlb", "uninstall driver", 60)
        except:
            pass

        cmand_reboot = "reboot;"
        self._common_content_lib.execute_sut_cmd(cmand_reboot, "reboot the sut", 60)
        time.sleep(300)

    def load_driver_esxi(self, common_content_object=None):
        if common_content_object is None:
            common_content_object = self._common_content_lib
        try:
            command_result = common_content_object.execute_sut_cmd(
                "kill -HUP $(cat /var/run/vmware/vmkdevmgr.pid)",
                "kill -HUP $(cat /var/run/vmware/vmkdevmgr.pid)",
                self._command_timeout)
        except:
            self._log.debug("load driver failed: {}".format(command_result))
            pass
        self._log.debug("command_result for load driver {}".format(command_result))
        if command_result != 0:
            self._log.error('kill vmkdevmgr fail')
        time.sleep(30)

    def uninstall_driver_esxi(self, acce_module_name, common_content_object=None):
        """
              Purpose: To uninstall accelerator device driver
              Args:
                  acce_module_name: this is accelerator device name, eg: 'qat', 'dlb', 'iadx'
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Uninstall accelerator device driver
                      uninstall_driver_esxi()
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib

        if acce_module_name == 'qat':
            try:
                command_result = common_content_object.execute_sut_cmd(
                    "esxcfg-module -u {}".format(acce_module_name),
                    "uninstall the module",
                    self._command_timeout)
                self._log.debug("Uninstalled module successfully with output '{}'".format(command_result))
            except:
                pass

            try:
                command_result = common_content_object.execute_sut_cmd(
                    "esxcli software vib remove -n {}".format(acce_module_name),
                    "uninstall the module",
                    self._command_timeout)
                self._log.debug("Uninstalled module successfully with output '{}'".format(command_result))
            except:
                pass

        elif acce_module_name == 'dlb':
            try:
                command_result = common_content_object.execute_sut_cmd("esxcfg-module -u dlb", "check for the driver",
                                                                       60)
                self._log.debug("Uninstalled module successfully with output '{}'".format(command_result))
            except:
                pass

            try:
                command_result = common_content_object.execute_sut_cmd("esxcli software component remove -n Intel-dlb",
                                                                       "uninstall driver", 60)
                self._log.debug("Uninstalled module successfully with output '{}'".format(command_result))
            except:
                pass

        elif acce_module_name == 'iadx':
            try:
                command_result = common_content_object.execute_sut_cmd(
                    "vmkload_mod --unload {}".format(acce_module_name),
                    "uninstall the module",
                    self._command_timeout)
                self._log.debug("Uninstalled module successfully with output '{}'".format(command_result))
            except:
                pass

            try:
                command_result = common_content_object.execute_sut_cmd(
                    "esxcli software vib remove --maintenance-mode -n {}".format(acce_module_name),
                    "remove the software componenet of the module",
                    self._command_timeout)
                self._log.debug("Uninstalled module successfully with output '{}'".format(command_result))
            except:
                pass

        cmand_reboot = "reboot;"
        self._common_content_lib.execute_sut_cmd(cmand_reboot, "reboot the sut", 60)
        time.sleep(300)
        self._log.info("Removed the {} driver of the module from sut successfully".format(acce_module_name))

    def install_vcenter_esxi(self):
        """
        This function installing the vcenter for esxi in host
        """
        # install vcenter for esxi
        vcenter_file_name,vcenter_file_path = self._install_collateral.download_vcenter_file_for_esxi()
        vcenter_json_file_name = self._install_collateral.download_json_for_esxi()
        try:
            cmd = r"New-Item -Path 'C:\Automation\vcenterimg' -ItemType Directory"
            self._vm_provider.vmp_execute_host_cmd(cmd,timeout=30, cwd=None, powershell=True)
            path1 = r"C:\Automation\vcenterimg"
            EXTRACT_FILE_STR = "Expand-Archive -Path '{}' -DestinationPath '{}'"
            self._vm_provider.vmp_execute_host_cmd(EXTRACT_FILE_STR.format(vcenter_file_path,path1),timeout=150, powershell=True)
            time.sleep(100)
        except Exception as ex:
            pass
        path2 = r"C:\Automation\vcenterimg\vcsa-cli-installer\win32"
        cmd1 = r".\vcsa-deploy.exe install --accept-eula --verify-template-only " \
               r"C:\Automation\Tools\SPR\Esxi\embedded_vCSA_on_ESXi.json"
        self._vm_provider.vmp_execute_host_cmd(cmd1, timeout=30, cwd=path2, powershell=True)
        self._log.info("verify vcenter for installation")
        cmd2 = r".\vcsa-deploy.exe install --acknowledge-ceip --accept-eula --no-esx-ssl-verify " \
               r"C:\Automation\Tools\SPR\Esxi\embedded_vCSA_on_ESXi.json"
        self._vm_provider.vmp_execute_host_cmd(cmd2, timeout=600, cwd=path2, powershell=True)
        self._log.info("Installed vcenter for esxi")

    def yum_virt_install(self, package_group, common_content_lib=None, flags=None, cmd_path=None, group=False):
        """
        This method will install the given linux package

        :param package_group: name of the linux packages to be installed
        :param flags: flags that will apply when installing the package, except '-y'
        :param cmd_path: path of the execute command
        :param group: if pkg name is a group install (such as Development Tools)
        :type: bool
        :return : Function returns if package is already installed
        :raise : raise: contents_exception.TestSetupError If unable to install yum packages
        """
        if common_content_lib is None:
            common_content_lib = self._common_content_lib
        max_attempts = 5
        is_yum_success = 0
        wait_delay = 5
        # check if package already installed
        package_list = package_group.split()
        package_name = ""
        for package in package_list:
            cmd_line = "yum list installed {}".format(package.strip())
            cmd_result = common_content_lib.execute_sut_cmd_no_exception(cmd_line,
                                                                         "running yum list installed {}".format(package.strip()),
                                                                         self._command_timeout,
                                                                         ignore_result="ignore")
            if cmd_result:
                if str(package.strip()).lower() in str(cmd_result).lower():
                    self._log.info("The package '{}' is already installed.".format(package.strip()))
                else:
                    package_name = package_name + " " + package.strip()
            else:
                package_name = package_name + " " + package.strip()

        package_name = package_name.strip()
        if package_name == "":
            self._log.info("The packages '{}' are already installed.".format(package_group))
            return

        self._log.debug("Installing the {} packages".format(package_name))

        cmd_result = common_content_lib.execute_sut_cmd("rm -f /var/lib/rpm/__db*;rpm --rebuilddb; rpm --import /etc/pki/rpm-gpg/RPM-GPG-KEY*;",
                                                              "Importing rpm key", self._command_timeout)
        self._log.debug(cmd_result)
        if flags is not None:
            package_name = package_name + " " + flags
        for no_attempts in range(max_attempts):
            try:
                self._log.debug("Running yum command for attempt {}".format(no_attempts + 1))
                # yum -y install {} --allowerasing --nobest --skip-broken
                if not group:
                    install_result = common_content_lib.execute_sut_cmd("rm -f /var/lib/rpm/__db*;rpm --rebuilddb; yum -y install {} --allowerasing;".format(package_name),
                                                                              "yum install cmd", self._command_timeout,
                                                                              cmd_path)
                else:
                    # yum -y groupinstall {} --allowerasing
                    install_result = common_content_lib.execute_sut_cmd(
                        " rpm --rebuilddb;yum -y groupinstall {} --allowerasing;".format(package_name),
                        "yum install cmd", self._command_timeout,
                        cmd_path)
                self._log.debug("Yum installation output is: {}".format(install_result))
                is_yum_success = 1
                break
            except Exception as ex:
                self._log.error("Error: {} for attempt {}, trying once again for command: {}".
                                format(ex, no_attempts + 1, package_name))
            time.sleep(wait_delay)
        if not is_yum_success:
            raise content_exceptions.TestSetupError("Command {} execution failed after {} attempts".format(
                package_name, max_attempts))
        self._log.info("Successfully installed the {} package".format(package_name))

    def yum_virt_remove(self, package_name, common_content_lib=None):
        """
        This method will uninstall/remove the given linux package

        :param package_name: name of the linux package to be removed
        :return : None
        :raise : None
        """
        if common_content_lib is None:
            common_content_lib = self._common_content_lib

        self._log.info("Removing the {} package".format(package_name))
        uninstall_result = common_content_lib.execute_sut_cmd("yum -y remove {}".format(package_name),
                                                                    "remove {}".format(package_name),
                                                                    self._command_timeout)
        self._log.debug(uninstall_result)
        self._log.info("Successfully removed the {} package".format(package_name))

    def windows_vm_object(self, vm_name, vm_type):
        """
        This method is to create Windows VM object

        :param vm_name: name of the VM. ex: windows_0 ,RHEL_0
        :param vm_type: type of VM. ex: Windows, RHEL
        :return: VM os executable object
        :raise: RuntimeError
        """
        self._log.info("Creating VM object to execute commands")
        windows_flavour_list = ["WINDOWS", "RS5"]
        if vm_type.upper() not in windows_flavour_list:
            vm_ip = self.get_crossvm_ip_linux(vm_name)
            if vm_ip is None:
                raise RuntimeError("Could not get IP to VM")
            self._log.info("Successfully got VM IP")
        else:
            vm_ip = self._vm_provider.get_vm_ip(vm_name)
        os_variant = self._common_content_configuration.get_vm_os_variant(self._sut_os, vm_type)
        kernel_vr = self._common_content_configuration.get_vm_kernel_version(self._sut_os, vm_type)
        vm_os_obj = self._vm_provider.create_vm_host(vm_type, os_variant, kernel_vr,
                                                 self.WINDOWS_VM_USERNAME, self.WINDOWS_VM_PASSWORD, vm_ip)
        self._vm_provider.install_opennssh_sut_win()
        try:
            if self._sut_os == "windows":
                self.create_ssh_vm_object_win(vm_name, copy_open_ssh=True)
            else:
                self.create_ssh_vm_object(vm_name,copy_open_ssh=True)
            ipconfig_output = vm_os_obj.execute("ipconfig", self._command_timeout)
            self._log.info("IPCONFIG- {}".format(ipconfig_output.stdout))
        except:
            self._log.error("SSH is not established properly....trying again to enable the ssh")
            if self._sut_os == "windows":
                self.create_ssh_vm_object_win(vm_name, copy_open_ssh=True)
            else:
                self.create_ssh_vm_object(vm_name, copy_open_ssh=True)
            ipconfig_output = vm_os_obj.execute("ipconfig", self._command_timeout)
            self._log.info("IPCONFIG- {}".format(ipconfig_output.stdout))
        return vm_os_obj

    def create_linux_vm_object_in_hyperv(self, vm_name, vm_os_subtype, enable_yum_repo=None):
        """
        This method is to create Linux VM object(Windows Host).

        :param vm_name
        :param vm_os_subtype
        :return VM os executable object
        :raise RuntimeError
        """
        self._log.info("Creating VM object to execute commands")
        vm_ip = self._vm_provider.get_vm_ip(vm_name)
        os_variant = self._common_content_configuration.get_vm_os_variant(self._sut_os, vm_os_subtype)
        kernel_version = self._common_content_configuration.get_vm_kernel_version(self._sut_os, vm_os_subtype)
        password = VmUserLin.PWD
        user_name = VmUserLin.USER
        vm_os_obj = self._vm_provider.create_vm_host(vm_os_subtype, os_variant, kernel_version,
                                                     user_name, password, vm_ip)

        if enable_yum_repo:
            repo_folder_path = self._common_content_configuration.get_yum_repo_name(self._sut_os, vm_os_subtype)
            self._enable_yum_repo_in_vm(vm_os_obj, repo_folder_path)

        return vm_os_obj

    def verify_os_device_info_w(self, device_type):
        """
        This Method is Used to verify from which device OS is booted.

        :param: Installed OS device type.
        :return: True if found OS booted from device of device_type
        :raise: content_exceptions.TestFail if OS failed to boot from required device.
        """
        with open(IOmeterToolConstants.FILE_NAME, "w+") as fp:
            list_commands = ["List Disk\n"]
            fp.writelines(list_commands)

        self.os.copy_local_file_to_sut(IOmeterToolConstants.FILE_NAME, self.C_DRIVE_PATH)
        disk_info = self._common_content_lib.execute_sut_cmd(r"diskpart /s {}".format(IOmeterToolConstants.FILE_NAME),
                                                             "List Disk",
                                                             self._command_timeout,
                                                             self.C_DRIVE_PATH)
        self._log.info("List Disk Command Output: {}".format(disk_info))
        disk_lists = re.findall(self.DISK_INFO_REGEX, disk_info)
        flag = False
        for digit in disk_lists:
            with open(IOmeterToolConstants.FILE_NAME, "w+") as fp:
                list_commands = ["select disk {}\n".format(digit), "detail disk"]
                fp.writelines(list_commands)

            self.os.copy_local_file_to_sut(IOmeterToolConstants.FILE_NAME, self.C_DRIVE_PATH)
            detail_disk = self._common_content_lib.execute_sut_cmd(r"diskpart /s {}"
                                                                   .format(IOmeterToolConstants.FILE_NAME),
                                                                   "Select Disk", self._command_timeout,
                                                                   self.C_DRIVE_PATH)
            self._log.info("Detail Disk Command Output: {}".format(detail_disk))
            if "Type   : {}".format(device_type).lower() in detail_disk.lower():
                volume_check = re.findall(self.VOLUME_INFO, detail_disk)
                self._log.info("OS Partition Details: {}".format(volume_check))
                if volume_check:
                    flag = True
                    break
        os.remove(IOmeterToolConstants.FILE_NAME)
        if not flag:
            raise content_exceptions.TestFail("OS failed to boot from {} device.".format(device_type))

        return flag

    def copy_csv_file_from_sut_to_host_w(self, vm_name, log_dir, log_path, log_name, common_content=None, os_obj=None):
        """
        This function copy the IOMeter result.csv file from SUT to HOST

        :param log_dir: Log directory
        :param log_path: Tool installed directory path
        :raise: content_exception.TestFail if not getting csv file path
        """
        vm_ip = self._vm_provider.get_vm_ip(vm_name)

        if common_content is None:
            common_content = self._common_content_lib
        find_cmd = "where /R {} {}".format(log_path, log_name)

        self._log.info("Copy the CSV file from SUT to Host")
        csv_file_path = common_content.execute_sut_cmd(find_cmd, "Finding path {} file".format(log_name),
                                                                 self._command_timeout, log_path)
        self._log.debug("csv file path {}".format(csv_file_path.strip()))
        if not csv_file_path.strip():
            raise content_exceptions.TestFail("{} file not found".format(log_name))
        cmd = r"powershell.exe pscp -scp -pw intel@123 Administrator@{}:{} {}".format(vm_ip, csv_file_path.strip(),
                                                                                        os.path.join(log_dir, log_name))
        common_content.execute_sut_cmd(cmd, self._command_timeout, csv_file_path.strip())
        # self.os.copy_file_from_sut_to_local(csv_file_path.strip(), os.path.join(log_dir, log_name))

    def parse_iometer_result_csv_data_w(self, filename, column):
        """ parse the iometer result file

        :param filename: csv file
        :param column: column name
        :return: python dictionary format
        """
        data = {}
        with open(filename, 'r') as csvfile:
            # creating a csv reader object
            csvreader = csv.reader(csvfile)
            # extracting field names through device index row
            csvreader_list = list(csvreader)
            for row in range(len(csvreader_list)):
                if column in csvreader_list[row]:
                    self.DEVICE_INDEX = row
                    for element in csvreader_list[self.DEVICE_INDEX]:
                        if element not in data.keys():
                            data[element] = []
                    row_list = csvreader_list[self.DEVICE_INDEX]
                    flag =0
                    for item_list in range(self.DEVICE_INDEX+1, len(csvreader_list)):
                        if flag:
                            break
                        for values in range(len(row_list)):
                            if "PROCESSOR" in csvreader_list[item_list]:
                                flag =1
                                break
                            data[row_list[values]].append(csvreader_list[item_list][values])

        return data

    def get_column_data_w(self, column, filename):
        """
        Get particular column data of the device.

        :param column: column name.
        :param filename: csv file.
        :return: python list format
        """
        data = self.parse_iometer_result_csv_data(filename, column)

        try:
            if column in data.keys():
                return data[column]
        except KeyError:
            raise content_exceptions.TestFail("%s is not found in the iometer result data" % column)

    def get_smartctl_drive_list_w(self):
        """
        Get smartctl drive list

        :param column: Non.
        :return: Drive list
        """
        if self.os.os_type == OperatingSystems.LINUX:
            drive_list_cmd = "smartctl --scan"
            path = "/root"

        elif self.os.os_type == OperatingSystems.WINDOWS:
            drive_list_cmd = "smartctl.exe --scan"
            path = r"C:\\"
        else:
            self._log.error("Smartctl tool is not implented on OS")
            raise NotImplementedError("Smartctl tool is not implented on OS")

        self._log.info("Executing smartctl scan command: {}".format(drive_list_cmd))
        execute_cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=drive_list_cmd,
                                                                      cmd_str=drive_list_cmd,
                                                                      execute_timeout=self._command_timeout,
                                                                      cmd_path=path)
        self._log.debug("Smartctl scan command: {} Output: {}".format(drive_list_cmd, execute_cmd_output))
        drive_list = [line.split(" ")[0] for line in execute_cmd_output.split("\n")]
        self._log.debug("Drive list: {}".format(drive_list))

        return drive_list

    def create_ssh_vm_object_win(self, vm_name, copy_open_ssh=True):
        """
        This method is to create SSH vm object

        :param vm_name: name of the VM. ex: windows_0 ,RHEL_0
        :param vm_type: type of VM. ex: Windows, RHEL
        :param copy_open_ssh: copy open ssh to VM to enable ssh.
        :return: None
        :raise: None
        """
        self._log.info("Creating SSH object to enable ssh on VM")
        if self._sut_os == "windows":
            self._vm_provider._enable_ssh_in_vm(vm_name, self.WINDOWS_VM_USERNAME,
                                                self.WINDOWS_VM_PASSWORD,
                                                copy_open_ssh=copy_open_ssh)
        else:
            raise Exception("Create and Enable function is implemented only for Windows Platform!")

    def create_ssh_vm_object(self, vm_id, vm_name, copy_open_ssh=True, common_content_lib_vm_obj=None):
        """
        This method is to create SSH vm object

        :param vm_name: name of the VM. ex: windows_0 ,RHEL_0
        :param vm_type: type of VM. ex: Windows, RHEL
        :param copy_open_ssh: copy open ssh to VM to enable ssh.
        :return: None
        :raise: None
        """
        self._log.info("Creating SSH object to enable ssh on VM")
        self._vm_provider._enable_ssh_in_vm(vm_id, vm_name, self.WINDOWS_VM_USERNAME, self.WINDOWS_VM_PASSWORD,
                                            copy_open_ssh=copy_open_ssh,
                                            common_content_lib_vm_obj=common_content_lib_vm_obj)
        self._log.info("Successfully enabled open ssh on VM")

    def cleanup(self, return_status):
        # type: (bool) -> None
        """VM cleanup"""
        try:
            for vm_name in self.LIST_OF_VM_NAMES:
                self._vm_provider.destroy_vm(vm_name)
        except Exception as ex:
            raise RuntimeError("Unable to Destroy the VM")
        super(VirtualizationCommon, self).cleanup(return_status)

    def add_storage_device_to_vm(self, vm_name, vm_type, storage_size):
        """
        This method is add additional storage device to VM

        :param vm_name: name of the VM
        :param vm_type: type of the VM
        :param storage_size: size of the storage device to add in GB
        :return: None
        """
        self._vm_provider.add_storage_device_to_vm(vm_name, self.VM_DISK_NAME, storage_size)
        # verify if the disk is reflecting on VM or not
        self._log.info("Verifying {} disk is added or not".format(self.VM_DISK_NAME))
        vm_os = self.create_vm_host(vm_name, vm_type)
        check_device = vm_os.execute("lsblk | grep {}".format(self.VM_DISK_NAME), self._command_timeout)
        self._log.debug(check_device.stdout)
        self._log.error(check_device.stderr)
        if self.VM_DISK_NAME not in check_device.stdout or str(storage_size)+"G" not in check_device.stdout:
            raise RuntimeError("Fail to verify {} in {} VM".format(self.VM_DISK_NAME, vm_name))
        self._log.info("Successfully verified additional disk {} is added to {} VM".format(self.VM_DISK_NAME, vm_name))

    def get_auto_start_state(self, vm_name):
        """
        This method is to return the AutoStart State of the VM

        :param vm_name: name of the VM
        :return : AutoStart state(enable or disable)
        """
        dom_info_data = self._vm_provider.get_vm_info(vm_name)
        return dom_info_data["Autostart"]

    def get_vm_power_state(self, vm_name):
        """
        This method is to return the Power State of the VM

        :param vm_name: name of the VM
        :return : Power State state(shut off or running)
        """
        dom_info_data = self._vm_provider.get_vm_info(vm_name)
        return dom_info_data["State"]

    def get_max_memory_size(self, vm_name):
        """
        This method is to return the Max memory of the VM

        :param vm_name: name of the VM
        :return maximum_memory: Maximum memory(in Kib Unit)
        """
        dom_info_data = self._vm_provider.get_vm_info(vm_name)
        return dom_info_data["Max memory"]

    def start_vm(self, vm_name):
        """
        This method is to start the VM & verify if it is running

        :param vm_name: name of the VM
        :raise: RuntimeError
        """
        # start the VM
        self._log.info("Starting {} VM".format(vm_name))
        start_result = self._common_content_lib.execute_sut_cmd(self.START_VM_CMD.format(vm_name),
                                                                "start {} VM".format(vm_name),
                                                                self._command_timeout)
        self._log.debug(start_result)
        # wait for the VM to boot
        self._log.info("Waiting {} seconds for VM to boot to OS".format(self.VM_WAIT_TIME))
        time.sleep(self.VM_WAIT_TIME)
        # verify VM is running or not
        if self.get_vm_power_state(vm_name) != self.STR_RUNNING:
            raise RuntimeError("Fail to start the {} VM".format(vm_name))
        self._log.info("Successfully started the {} VM".format(vm_name))

    def shutdown_vm(self, vm_name):
        """
        This method is to shutdown the VM & verify if it is running

        :param vm_name: name of the VM
        :raise: RuntimeError
        """
        # shut down the VM
        self._log.info("Shutting down {} VM".format(vm_name))
        shut_down_result = self._common_content_lib.execute_sut_cmd(self.SHUTDOWN_VM_CMD.format(vm_name),
                                                                    "shutdown {} VM".format(vm_name),
                                                                    self._command_timeout)
        self._log.debug(shut_down_result)
        # wait for the VM to shutdown
        self._log.info("Waiting {} seconds for VM to shutdown".format(self.VM_WAIT_TIME))
        time.sleep(self.VM_WAIT_TIME)
        # verify VM is shut down or not
        if self.get_vm_power_state(vm_name) != self.STR_SHUT_OFF:
            raise RuntimeError("Fail to shutdown the {} VM".format(vm_name))
        self._log.info("Successfully shut down the {} VM".format(vm_name))

    #==================================================================================================================
    def get_vm_id_esxi(self, vm_name):
        self._log.info(f'get the virtual machine id')
        return self._vm_provider.get_esxi_vm_id_data(vm_name)

    def get_vm_list_esxi(self, vm_name):
        self._log.info(f'get the virtual machine list')

        cmd = f'vim-cmd vmsvc/getallvms {vm_name} | awk \'' + '{' + 'print $2}\''
        cmd_result = self._common_content_lib.execute_sut_cmd(cmd,
                                                               "Command to get VM id",
                                                               self._command_timeout )

        return cmd_result.strip().splitlines()[1:]

    def get_vm_ip_esxi(self, vm_name):
        vm_id = self.get_vm_id_esxi(vm_name)
        cmd = f"vim-cmd vmsvc/get.summary {vm_id} | grep ipAddress | awk -F '[\\t\",]' '" + "{" + "print $2}'"
        std_out = self._common_content_lib.execute_sut_cmd(cmd, "Command to get VM ip",
                                                               self._command_timeout )
        return std_out.strip()

    def is_vm_running_esxi(self, vm_name):
        vm_id = self.get_vm_id_esxi(vm_name)
        cmd = f'vim-cmd vmsvc/power.getstate {vm_id}'
        std_out = self._common_content_lib.execute_sut_cmd(cmd, "Command to get VM state",
                                                           self._command_timeout)
        return 'off' not in std_out

    def set_vm_memory_esxi(self, vm_name, ram_mb):
        self._log.info(f'set {vm_name}\'s max memory to {ram_mb}')

        cmd = f'Get-VM ${vm_name} | Set-VM -MemoryMB {ram_mb} -Confirm:$false'
        out, std_err = self.virt_execute_host_cmd_esxi(cmd)
        if out != 0:
            raise Exception(std_err)

    def start_vm_esxi(self, vm_name):
        self._log.info(f'start the virtual machine {vm_name}')

        if self.is_vm_running_esxi(vm_name):
            self._log.error(f'start virtual machine failed: {vm_name} is already started')
            return

        self._vm_provider.start_vm(vm_name)
        self._log.info(f"waitting form {vm_name} boot into OS...")
        time.sleep(3 * 60)

    def shutdown_vm_esxi(self, vm_name):
        self._log.info(f'shutdown the virtual machine {vm_name}')

        if not self.is_vm_running_esxi(vm_name):
            self._log.error(f'shutdown virtual machine failed: {vm_name} is not running')
            return

        vm_id = self.get_vm_id_esxi(vm_name)
        cmd = f'vim-cmd vmsvc/power.off {vm_id}'
        self._common_content_lib.execute_sut_cmd(cmd, "Command to start VM",
                                                 self._command_timeout)

    def suspend_vm_esxi(self, vm_name):
        self._log.info(f'reboot virtual machine {vm_name}')

        return self._vm_provider.suspend_vm(vm_name)

    def reboot_vm_esxi(self, vm_name):
        self._log.info(f'reboot virtual machine {vm_name}')

        if not self.is_vm_running_esxi(vm_name):
            raise Exception(f'reboot virtual machine failed: {vm_name} is not running')
        self._vm_provider.reboot_vm(vm_name)


    def resume_vm_esxi(self, vm_name):
        self._log.info(f'reboot virtual machine {vm_name}')
        return self._vm_provider.resume_vm(vm_name)

    def undefine_vm_esxi(self, vm_name):
        self._log.info(f'undefine {vm_name}')

        if self.is_vm_running_esxi(vm_name):
            self.shutdown_vm_esxi(vm_name)

        vm_id = self.get_vm_id_esxi(vm_name)
        cmd = f'vim-cmd vmsvc/unregister {vm_id}'
        rcode = self._common_content_lib.execute_sut_cmd(cmd, "Command to undefine VM",
                                                 self._command_timeout)
        if rcode != 0:
            raise Exception("unregister failed")

    #==================================================================================================================

    def create_vm_host(self, vm_name, vm_type):
        """
        This method is to create the create_vm_host object

        :param vm_name: name of the VM
        :param vm_type: type of the VM
        """
        if vm_type == "RS5" or vm_type == "WINDOWS":
            if vm_type.lower() != self._sut_os.lower():
                vm_ip = self.get_crossvm_ip_linux(vm_name)
                if vm_ip is None:
                    raise RuntimeError("Could not get IP to VM")
            else:
                vm_ip = self._vm_provider.get_vm_ip(vm_name)
            self._log.info("Successfully verified VM is working")
        else:
            vm_ip = self._vm_provider.get_vm_ip(vm_name)
        os_variant = self._common_content_configuration.get_vm_os_variant(self._sut_os, vm_type)
        kernel_vr = self._common_content_configuration.get_vm_kernel_version(self._sut_os, vm_type)
        vm_os = self._vm_provider.create_vm_host(vm_type, os_variant, kernel_vr, self.VM_USERNAME, self.VM_PASSWORD, vm_ip)
        self.VM_IP_LIST[vm_name] = vm_ip
        return vm_os

    def create_nested_vm_host(self, vm_name, vm_type, nesting_level=None):
        """
        This method is to create the create_vm_host object

        :param vm_name: name of the VM
        :param vm_type: type of the VM
        """
        if vm_type == "RS5" or vm_type == "WINDOWS":
            if nesting_level != None:
                raise RuntimeError("Nested VM with Win OS Not Supported")
            else:
                if vm_type.lower() != self._sut_os.lower():
                    vm_ip = self.get_crossvm_ip_linux(vm_name)
                    if vm_ip is None:
                        raise RuntimeError("Could not get IP to VM")
                else:
                    vm_ip = self._vm_provider.get_vm_ip(vm_name)
                self._log.info("Successfully verified VM is working")
        else:
            if nesting_level != None:
                vm_ip = self._vm_provider.get_nested_vm_ip(vm_name, nesting_level=nesting_level)
            else:
                vm_ip = self._vm_provider.get_vm_ip(vm_name)
        os_variant = self._common_content_configuration.get_vm_os_variant(self._sut_os, vm_type)
        kernel_vr = self._common_content_configuration.get_vm_kernel_version(self._sut_os, vm_type)
        vm_os = self._vm_provider.create_vm_host(vm_type, os_variant, kernel_vr, self.VM_USERNAME, self.VM_PASSWORD, vm_ip)
        self.VM_IP_LIST[vm_name] = vm_ip
        return vm_os

    def create_esxi_vm_host(self, vm_name, vm_type):
        """
        This method is to create the create_vm_host object

        :param vm_name: name of the VM
        :param vm_type: type of the VM
        """
        vm_id = self._vm_provider.get_esxi_vm_id_data(vm_name)
        vm_ip = self._vm_provider.get_vm_ip(vm_id, vm_name)
        os_variant = self._common_content_configuration.get_vm_os_variant(self._sut_os, vm_type)
        kernel_vr = self._common_content_configuration.get_vm_kernel_version(self._sut_os, vm_type)
        vm_os = self._vm_provider.create_vm_host(vm_type, os_variant, kernel_vr, vm_ip)
        return vm_os

    def copy_file_from_sut_to_vm(self, vm_name, vm_type, source, destination):
        """
        Method to copy a test file from SUT to VM and verify it

        :param vm_name: name of the VM. ex: RHEL_1
        :param vm_type: type of VM. ex: RHEL
        :param source: source file path
        :param destination: destination file path
        :return: None
        :raise: RuntimeError
        """
        vm_os = self.create_vm_host(vm_name, vm_type)
        self._vm_provider.copy_file_from_sut_to_vm(vm_name, self.VM_USERNAME, source, destination)
        # verify file copied or not
        copy_status = vm_os.check_if_path_exists(destination)
        if not copy_status:
            raise RuntimeError("Fail to verify the Copy operation")
        self._log.info("Successfully verified the file copy operation")

    def verify_kvm_unit_test_results(self, command, expected_result):
        """
        This method is to execute KVM_UNIT_TEST tool and veriry with the given output

        :param: command
        :param: expected_result:
        :return: True in Success
        :raise: RuntimeError
        """
        kvm_unit_test_path = self._configure_kvm_unit_test()
        self._log.info("Executing KVM Unit Test command {}".format(command))
        unit_test_result = self.os.execute(command, self._command_timeout+self.KVM_UNIT_TEST_EXECUTION_TIMEOUT,
                                           cwd=kvm_unit_test_path)
        self._log.debug("'{}' command stdout:\n{}".format(command, unit_test_result.stdout))
        self._log.error("'{}' command stderr:\n{}".format(command, unit_test_result.stderr))
        output = self._common_content_lib.escape_ansii_from_sequence(unit_test_result.stdout)
        self._log.debug("Without AnsII characters: %s", output)
        if expected_result not in output:
            raise RuntimeError("KVM Unit Test command '{}' output does not contain Expected output '{}'".format(command,
                               expected_result))
        self._log.info("Successfully executed KVM Unit Test command '{}' and verified output data contains expected "
                       "output {}".format(command, expected_result))
        return True

    def _configure_kvm_unit_test(self):
        """
        This method will copy the KVM_UNIT test tool from HOST to SUT and configure it.

        :return kvm_unit_test_path: installed path of the tool
        """
        self._log.info("Copying {} file to SUT and unzipping it".format(self.KVM_UNIT_TEST_FILE_NAME))
        artifactory_name = ArtifactoryName.DictLinuxTools[ArtifactoryTools.KVM_UNIT_TEST_FILE]
        zip_file_path = self._install_collateral._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
        kvm_unit_test_path = self._common_content_lib.copy_zip_file_to_linux_sut(self.KVM_UNIT_TESTS_STR,
                                                                                 zip_file_path)
        kvm_unit_test_path = kvm_unit_test_path + "/" + self.KVM_UNIT_TESTS_STR
        self._install_collateral.install_development_tool_linux()
        self._install_collateral.yum_install("make")
        self._log.info("Configuring KVM Unit Test Tool")
        if not self._check_nested_kvm():
            for configure_command in self.KVM_UNIT_TEST_CONFIGURATION_COMMANDS:
                configure_command_result = self.os.execute(configure_command, self._command_timeout,
                                                           cwd=kvm_unit_test_path)
                self._log.debug("{} command stdout:\n {}".format(configure_command, configure_command_result.stdout))
                self._log.error("{} command stderr:\n {}".format(configure_command, configure_command_result.stderr))
            if not self._check_nested_kvm():
                raise RuntimeError("Fail to configure Nested KVM")
        else:
            self._log.info("Successfully configured Nested KVM")
        for install_command in self.KVM_UNIT_TEST_INSTALL_COMMANDS:
            install_command_result = self.os.execute(install_command, self._command_timeout, cwd=kvm_unit_test_path)
            self._log.debug("{} command stdout:\n {}".format(install_command, install_command_result.stdout))
            self._log.error("{} command stderr:\n {}".format(install_command, install_command_result.stderr))
        self._log.info("Successfully configured KVM Unit Test Tool")
        return kvm_unit_test_path

    def _check_nested_kvm(self):
        """
        This method will check if nested KVM is enabled or not

        :return: True or False
        """
        result = self._common_content_lib.execute_sut_cmd(self.KVM_NESTED_COMMAND, "Executing {} command".format(
                                                          self.KVM_NESTED_COMMAND), self._command_timeout)
        if "1" in result or "Y" in result:
            self._log.info("Nested KVM is configured")
            return True
        self._log.info("Nested KVM is not configured")
        return False

    def execute_sut_cmd_virt_common(self, common_content_lib, sut_cmd, cmd_str, execute_timeout, cmd_path=None):
        """
        This function returns execution details of OS commands.

        :param sut_cmd: Get OS commands like lsmem/lscpu/lspci
        :param cmd_str: Get the name of the command
        :param execute_timeout: timeout for execute command
        :param cmd_path: path of the execute commmand
        :return: returning the output of the OS commands
        """
        MAX_RETRY_CNT = 5
        retry_cnt = 0
        while (True):
            try:
                sut_cmd_result = common_content_lib._os.execute(sut_cmd, execute_timeout, cmd_path)
            except Exception as ex:
                if retry_cnt > MAX_RETRY_CNT:
                    self._log.error("SSH Communicating ip is Down {}, retry cnt exceeded = {}".format(ex, retry_cnt))
                    break
                else:
                    retry_cnt = retry_cnt + 1
                    self._log.error("SSH Communicating ip is Down {}, retry again = {}".format(ex, retry_cnt))
                    common_content_lib.execute_cmd_on_host("ssh-keygen -R %s" % common_content_lib._os._ip)
                    continue
            else:
                # success case
                break
        if sut_cmd_result.cmd_failed():
            log_error = "Failed to run '{}' command with return value = '{}' and " \
                        "std_error='{}'..".format(cmd_str, sut_cmd_result.return_code, sut_cmd_result.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)
        else:
            self._log.debug(sut_cmd_result.stdout)

        return sut_cmd_result.stdout

    def enable_proxy_vm(self, common_content_lib=None):
        """
        This function will enable the proxy setting as per the input from content_configuration.xml file
        virtualization/proxy_server ==> "chain"/"iind"/""
        """
        if common_content_lib is None:
            common_content_lib = self._common_content_lib

        http_proxy_reference_vm = self._common_content_configuration.get_proxy_server_vm_ref()

        if http_proxy_reference_vm == "iind" or http_proxy_reference_vm == "chain":
            proxy_commands_sh_vm = "echo export http_proxy=http://proxy-{}.intel.com:911 >> /etc/profile.d/dtaf_proxy.sh;" \
                      "echo export HTTP_PROXY=http://proxy-{}.intel.com:911 >> /etc/profile.d/dtaf_proxy.sh;" \
                      "echo export https_proxy=http://proxy-{}.intel.com:911 >> /etc/profile.d/dtaf_proxy.sh;" \
                      "echo export HTTPS_PROXY=http://proxy-{}.intel.com:911 >> /etc/profile.d/dtaf_proxy.sh;" \
                      "echo \"export no_proxy=\'localhost, 127.0.0.1, intel.com, .intel.com\'\" >> /etc/profile.d/dtaf_proxy.sh;".format(
                       http_proxy_reference_vm, http_proxy_reference_vm, http_proxy_reference_vm, http_proxy_reference_vm)

            proxy_commands_env_vm = "echo export http_proxy=http://proxy-{}.intel.com:911 >> /etc/environment;" \
                 "echo export HTTP_PROXY=http://proxy-{}.intel.com:911 >> /etc/environment;" \
                 "echo export https_proxy=http://proxy-{}.intel.com:911 >> /etc/environment;" \
                 "echo export HTTPS_PROXY=http://proxy-{}.intel.com:911 >> /etc/environment;" \
                 "echo \"export no_proxy=\'localhost, 127.0.0.1, intel.com, .intel.com\'\" >> /etc/environment;".format(
                  http_proxy_reference_vm, http_proxy_reference_vm, http_proxy_reference_vm, http_proxy_reference_vm)
        else:
            self._log.info("No Proxy setting done as http_proxy_reference is not valid {}!".format(http_proxy_reference_vm))
            self._log.error(
                "No Proxy setting done as http_proxy_reference is not valid {}!".format(http_proxy_reference_vm))
            return

        #check if file already present
        check_if_file_exist = '[ -f /etc/profile.d/dtaf_proxy.sh ] && echo "FileExist" || echo "FileNotExist"'
        # output = common_content_lib.execute_sut_cmd(check_if_file_exist, "Enabling Proxy in System", 10)
        output = self.execute_sut_cmd_virt_common(common_content_lib, check_if_file_exist, "Enabling Proxy in System", 10)
        output = output.strip()
        if "FileExist" in output:
            self._log.info("Proxy Setting already enabled as dtaf_proxy.sh file already exist in /etc/profile.d/!")
            self._log.debug("Proxy Setting already enabled as dtaf_proxy.sh file already exist in /etc/profile.d/!")
        else:
            self._log.info("Enabling proxy Settings!")
            # common_content_lib.execute_sut_cmd("touch /etc/profile.d/dtaf_proxy.sh", "Enabling Proxy in System", 10)
            self.execute_sut_cmd_virt_common(common_content_lib, "touch /etc/profile.d/dtaf_proxy.sh", "Enabling Proxy in System", 10)
            #update the file new proxy settings
            # common_content_lib.execute_sut_cmd(proxy_commands_sh_vm, "Enabling Proxy in System", 10)
            self.execute_sut_cmd_virt_common(common_content_lib, proxy_commands_sh_vm, "Enabling Proxy in System", 10)
            self._log.info("Enabled proxy Settings ==> /etc/profile.d/dtaf_proxy.sh!")
            self._log.debug("Enabled proxy Settings ==> /etc/profile.d/dtaf_proxy.sh!")

        #check if the proxy settings are already there
        # common_content_lib.execute_sut_cmd(proxy_commands_env_vm, "Enabling Proxy in environment", 10)
        self.execute_sut_cmd_virt_common(common_content_lib, proxy_commands_env_vm, "Enabling Proxy in environment", 10)
        self._log.info("Enabled proxy Settings ==> /etc/environment!")
        self._log.debug("Enabled proxy Settings ==> /etc/environment!")


    def enable_proxy(self, common_content_lib=None):
        """
        This function will enable the proxy setting as per the input from content_configuration.xml file
        virtualization/proxy_server ==> "chain"/"iind"/""
        """
        if common_content_lib is None:
            common_content_lib = self._common_content_lib

        http_proxy_reference = self._common_content_configuration.get_proxy_server_ref()

        if http_proxy_reference == "iind" or http_proxy_reference == "chain":
            proxy_commands_sh = "echo export http_proxy=http://proxy-{}.intel.com:911 >> /etc/profile.d/dtaf_proxy.sh;" \
                      "echo export HTTP_PROXY=http://proxy-{}.intel.com:911 >> /etc/profile.d/dtaf_proxy.sh;" \
                      "echo export https_proxy=http://proxy-{}.intel.com:911 >> /etc/profile.d/dtaf_proxy.sh;" \
                      "echo export HTTPS_PROXY=http://proxy-{}.intel.com:911 >> /etc/profile.d/dtaf_proxy.sh;" \
                      "echo \"export no_proxy=\'localhost, 127.0.0.1, intel.com, .intel.com\'\" >> /etc/profile.d/dtaf_proxy.sh;".format(
                       http_proxy_reference, http_proxy_reference, http_proxy_reference, http_proxy_reference)

            proxy_commands_env = "echo export http_proxy=http://proxy-{}.intel.com:911 >> /etc/environment;" \
                 "echo export HTTP_PROXY=http://proxy-{}.intel.com:911 >> /etc/environment;" \
                 "echo export https_proxy=http://proxy-{}.intel.com:911 >> /etc/environment;" \
                 "echo export HTTPS_PROXY=http://proxy-{}.intel.com:911 >> /etc/environment;" \
                 "echo \"export no_proxy=\'localhost, 127.0.0.1, intel.com, .intel.com\'\" >> /etc/environment;".format(
                  http_proxy_reference, http_proxy_reference, http_proxy_reference, http_proxy_reference)
        else:
            self._log.info("No Proxy setting done as http_proxy_reference is not valid {}!".format(http_proxy_reference))
            self._log.error("No Proxy setting done as http_proxy_reference is not valid {}!".format(http_proxy_reference))
            return

        #check if file already present
        check_if_file_exist = '[ -f /etc/profile.d/dtaf_proxy.sh ] && echo "FileExist" || echo "FileNotExist"'
        output = common_content_lib.execute_sut_cmd(check_if_file_exist, "Enabling Proxy in System", 10)
        output = output.strip()
        if "FileExist" in output:
            self._log.info("Proxy Setting already enabled as dtaf_proxy.sh file already exist in /etc/profile.d/!")
            self._log.debug("Proxy Setting already enabled as dtaf_proxy.sh file already exist in /etc/profile.d/!")
        else:
            self._log.info("Enabling proxy Settings!")
            common_content_lib.execute_sut_cmd("touch /etc/profile.d/dtaf_proxy.sh", "Enabling Proxy in System", 10)
            #update the file new proxy settings
            common_content_lib.execute_sut_cmd(proxy_commands_sh, "Enabling Proxy in System", 10)
            self._log.info("Enabled proxy Settings ==> /etc/profile.d/dtaf_proxy.sh!")
            self._log.debug("Enabled proxy Settings ==> /etc/profile.d/dtaf_proxy.sh!")

        #check if the proxy settings are already there
        common_content_lib.execute_sut_cmd(proxy_commands_env, "Enabling Proxy in environment", 10)
        self._log.info("Enabled proxy Settings ==> /etc/environment!")
        self._log.debug("Enabled proxy Settings ==> /etc/environment!")

    def get_yum_repo_config(self, os_obj, common_content_lib_obj, os_type=None, machine_type=None):
        """
        This function to get the content configuration xml file path and return content configuration xml file root.
        :param: os_obj OS object for SUT/VM
        :os_obj: common_content_lib_obj Common Content Library Class object
        :os_type : centos, rhel, ubuntu etc.
        :machine_type : host or vm or None etc.
        :return: return configuration xml file root .
        """
        update_repo_files_in_centos_status = self._common_content_configuration.update_repo_files_for_centos()
        self._log.info("Enabling Proxy")
        self._log.debug("Enabling Proxy")
        if machine_type is None:
            self.enable_proxy(common_content_lib_obj)
        else:
            self.enable_proxy_vm(common_content_lib_obj)
        if os_type is not None:
            self._log.info("Configure yum repo files for os {}".format(os_type))
            self._log.debug("Configure yum repo files for os {}".format(os_type))

        if os_type == "centos":
            if machine_type == "vm" and update_repo_files_in_centos_status.lower() == "true":
                self._enable_yum_repo_in_cent_vm(os_obj)
            self._log.info("No repo configuration needed for os {}, already configured.".format(os_type))
            self._log.debug("No repo configuration needed for os {}, already configured.".format(os_type))
            return True

        self._log.info("Deleting old yum repo files in rhel if available..")
        self._log.debug("Deleting old yum repo files in rhel if available..")

        ls_repo_res = os_obj.execute(r"ls *.repo", self._command_timeout, self.REPOS_FOLDER_PATH_SUT)
        self._log.debug("stdout of ls *.repo is :\n{}".format(ls_repo_res.stdout))
        if ls_repo_res.cmd_failed():
            self._log.debug("stderr of ls *.repo is :\n{}".format(ls_repo_res.stderr))

        sut_repo_file_path = []
        if len(ls_repo_res.stdout.strip().split()) != 0:
            for log_file in ls_repo_res.stdout.strip().split():
                if ".repo" in log_file.lower():
                    sut_repo_file_path.append(Path(os.path.join(self.REPOS_FOLDER_PATH_SUT, log_file)).as_posix())

        if len(sut_repo_file_path) != 0:
            for repo in sut_repo_file_path:
                rmrf_repo_res = os_obj.execute(r"rm -rf {}".
                                                 format(repo.strip().replace("(", r"\(").replace(")", "\)")),
                                                 self._command_timeout, self.REPOS_FOLDER_PATH_SUT)

                if rmrf_repo_res.return_code != 0:
                    raise RuntimeError("rmrf command execution failed with error "
                                       ": {}...".format(rmrf_repo_res.stderr))
                self._log.debug("Successfully deleted the old file '{}'".format(repo.strip()))
        else:
            self._log.info("No .repo file(s) present under {}, proceeding further..".format(self.REPOS_FOLDER_PATH_SUT))

        """
        From Host to SUT copy repo starts from here
        """
        repofile = "CentOS_Repos.zip"
        repo_host_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder(repofile)

        # Copy the repo file to SUT
        result_rm = common_content_lib_obj.execute_sut_cmd("rm -rf {}/yum.repos.d".format(self.REPOS_FOLDER_PATH_SUT),
                                                           "To delete a "
                                                           "folder", self._command_timeout, self.ROOT_PATH)
        self._log.debug("Remove the repo files result {}".format(result_rm))
        sut_folder_path = common_content_lib_obj.copy_zip_file_to_linux_sut(self.REPOS_FOLDER_PATH_SUT, repo_host_file_path,
                                                                            dont_delete="True")
        self._log.debug("repo file is extracted and copied to path {}".format(sut_folder_path))
        if sut_folder_path == "":
            os_obj.execute(
                r"curl -X GET bdcspiec010.gar.corp.intel.com/files/test.repo --output /etc/yum.repos.d/test.repo", 10)
            ret = os_obj.execute("ls /etc/yum.repos.d/", 10)
            if (str(ret.stdout.strip()).find("test.repo") != -1):
                self._log.info("REPO Configuration Made for RHEL")
            else:
                self._log.error("REPO Configuration FAILED for RHEL")
                return False
        else:
            copy_result = common_content_lib_obj.execute_sut_cmd_no_exception("cp {}/yum.repos.d/*.repo {}/;sync;".format(
                                                                                    self.REPOS_FOLDER_PATH_SUT,
                                                                                    self.REPOS_FOLDER_PATH_SUT),
                                                                               "executing install repo files",
                                                                                self._command_timeout,
                                                                                cmd_path=self.ROOT_PATH,
                                                                                ignore_result="ignore")
            self._log.debug("Install repo files result {}".format(copy_result))

        for command in self.ENABLE_YUM_REPO_COMMANDS:
            cmd_opt = os_obj.execute(command, self._command_timeout)
        self._log.debug("{} stdout:\n{}".format(command, cmd_opt.stdout))
        self._log.error("{} stderr:\n{}".format(command, cmd_opt.stderr))

        return True

    def install_burnin_dependencies_linux(self, os_obj, common_content_lib_obj):
        """
        This function to get and install burnin tool dependencies.
        :param: os_obj OS object for SUT/VM
        :os_obj: common_content_lib_obj Common Content Library Class object
        :return: True .
        """
        self._log.info("burnin dependencies installations begins...")
        list_of_linux_os_commands = [r"yum install -y libusb*;echo y",
                                        r"yum install -y libQt5*;echo y",
                                        r"yum install -y *Qt*;echo y",
                                        r"yum install -y alsa-utils;echo y",
                                        r"export QT_QPA_PLATFORM=wayland"]

        for command_line in list_of_linux_os_commands:
            cmd_result = os_obj.execute(command_line, self._command_timeout)
            if cmd_result.cmd_failed():
                log_error = "Failed to run command '{}' with " \
                            "return value = '{}' and " \
                            "std_error='{}'..".format(command_line, cmd_result.return_code, cmd_result.stderr)
                self._log.error(log_error)
                # raise RuntimeError(log_error)
            else:
                self._log.info("The command '{}' executed successfully..".format(command_line))
        self._log.info("burnin dependencies installations completed...")

        return True

    def _enable_yum_repo_in_vm(self, vm_os_obj, repo_path_host):
        """
        This method is to enable yum repo in VM

        :param vm_os_obj: os object of VM
        :param repo_path_host: Name of the yum repo
        """
        self._log.info("Enabling yum repo in VM")

        #  Copy repo zip file to collateral
        repo_folder_name = os.path.split(repo_path_host)[-1].strip()

        vm_install_collateral = InstallCollateral(self._log, vm_os_obj, self._cfg)

        #  Move repo.zip file to SUT and extract with folder RHEL_REPOS
        sut_repo_folder_path = vm_install_collateral.download_and_copy_zip_to_sut("RHEL_REPOS", repo_folder_name)

        #  Moving all repo file from RHEL_REPOS folder to /etc/yum.repos.d
        vm_os_obj.execute("yes | cp -rf {}/.* {}".format(sut_repo_folder_path, self.REPOS_FOLDER_PATH_SUT),
                          self._command_timeout)

        self._log.info("Successfully copied the repos file to VM")
        yum_conf_result = vm_os_obj.execute("cat {}".format(self.YUM_CONF_FILE_PATH), self._command_timeout)
        self._log.debug("stdout of {}:\n{}".format(self.YUM_CONF_FILE_PATH, yum_conf_result.stdout))
        self._log.error("stderr of {}:\n{}".format(self.YUM_CONF_FILE_PATH, yum_conf_result.stderr))
        if self.PROXY_STR not in yum_conf_result.stdout:
            vm_os_obj.execute(r"sed -i.bak '$ a\{}' {}".format(self.PROXY_STR, self.YUM_CONF_FILE_PATH),
                              self._command_timeout)
        self._log.info("Added the proxy in {}".format(self.YUM_CONF_FILE_PATH))
        for command in self.ENABLE_YUM_REPO_COMMANDS:
            cmd_opt = vm_os_obj.execute(command, self._command_timeout)
            self._log.debug("{} stdout:\n{}".format(command, cmd_opt.stdout))
            self._log.error("{} stderr:\n{}".format(command, cmd_opt.stderr))
        self._log.info("Successfully enabled YUM repos")

    def ping_vm_from_host(self, vm_ip):
        """
        This method is to ping the VM from HOST system

        :param vm_ip: IP of the VM
        :return: True on Success else False
        """
        ping_process = subprocess.call("ping {}".format(vm_ip))
        self._log.debug("ping {} response:\n{}".format(vm_ip, ping_process))
        if ping_process != 0:
            self._log.error("VM ip {} is not pingable from HOST".format(vm_ip))
            return False
        self._log.info("VM ip {} is pingable from HOST".format(vm_ip))
        return True

    def create_snapshot_of_linux_vm(self, vm_name, snapshot_name):
        """
        This method is to create the snapshot of a VM

        :param vm_name: Name of the VM, whose snapshot is going to be taken
        :param snapshot_name: Name of the snapshot
        :return: None
        """
        self._log.info("Creating snapshot of the VM {}".format(vm_name))
        cmd_result = self._common_content_lib.execute_sut_cmd(self.CREATE_SNAPSHOT_COMMAND
                                                              .format(vm_name, snapshot_name),
                                                              "create snapshot of VM {}".format(vm_name),
                                                              self._command_timeout)
        self._log.info("Successfully created the snapshot of VM {} named {}:\n{}"
                       .format(vm_name, snapshot_name, cmd_result))

    def restore_snapshot_of_linux_vm(self, vm_name, snapshot_name):
        """
        This method is to restore the snapshot with given VM name and snapshot name

        :param vm_name: name of the VM, whose snapshot is going to be restored
        :param snapshot_name: name of the snapshot
        :return: None
        """
        self._log.info("Restoring the snapshot named {}".format(snapshot_name))
        self._common_content_lib.execute_sut_cmd(self.RESTORE_SNAPSHOT_COMMAND.format(vm_name, snapshot_name),
                                                 "restore snapshot of VM {}".format(vm_name), self._command_timeout)
        self._log.info("Successfully restored the snapshot of VM {} named {}".format(vm_name, snapshot_name))

    def delete_snapshot_of_linux_vm(self, vm_name, snapshot_name):
        """
        This method is to delete any existing snapshot with given VM name and snapshot name

        :param vm_name: name of the VM, whose snapshot is going to be deleted
        :param snapshot_name: name of the snapshot which is going to be deleted
        :return: None
        """
        self._log.info("Deleting the snapshot named {}".format(snapshot_name))
        cmd_output = self._common_content_lib.execute_sut_cmd(self.DELETE_SNAPSHOT_COMMAND.
                                                              format(vm_name, snapshot_name),
                                                              "delete snapshot of VM named {}".format(snapshot_name),
                                                              self._command_timeout)
        self._log.info("Successfully deleted the snapshot named {}:\n{}".format(snapshot_name, cmd_output))

    def shutdown_linux_vm(self, vm_name):
        """
        This method is to Shutdown the VM

        :param vm_name: Name of the VM, which is going to be shutdown

        :return: None
        """
        self._log.info("Shutting down the VM {}".format(vm_name))
        cmd_result = self._common_content_lib.execute_sut_cmd(self.SHUTDOWN_VM_COMMAND
                                                              .format(vm_name),
                                                              "create snapshot of VM {}".format(vm_name),
                                                              self._command_timeout)
        self._log.info("Successfully did shutdown of VM named {}:\n{}"
                       .format(vm_name, cmd_result))

    def resume_linux_vm(self, vm_name):
        """
        This method is to Resume the VM

        :param vm_name: Name of the VM, which is going to be resumed
        :return: None
        """
        self._log.info("Resuming up the VM {}".format(vm_name))
        cmd_result = self._common_content_lib.execute_sut_cmd(self.RESUME_VM_COMMAND
                                                              .format(vm_name),
                                                              "create snapshot of VM {}".format(vm_name),
                                                              self._command_timeout)
        self._log.info("Successfully resumed VM named {}:\n{}"
                       .format(vm_name, cmd_result))

    def start_linux_vm(self, vm_name):
        """
        This method is to start the VM

        :param vm_name: name of the VM
        :raise: RuntimeError
        """
        # start the VM
        self._log.info("Starting {} VM".format(vm_name))
        start_result = self._common_content_lib.execute_sut_cmd(self.START_VM_CMD.format(vm_name),
                                                                "start {} VM".format(vm_name),
                                                                self._command_timeout)
        self._log.debug(start_result)
        self._log.info("Successfully started the {} VM".format(vm_name))

    def reboot_linux_vm(self, vm_name, use_shutdown_resume=None):
        """
        This method is to Reboot the VM

        :param vm_name: Name of the VM, which is going to be rebooted
        :return: None
        """
        self._log.info("Rebooting up the VM {}".format(vm_name))
        cmd = "virsh destroy {} --graceful"
        cmd_result = self._common_content_lib.execute_sut_cmd(cmd.format(vm_name),
                                                              "force off VM {}".format(vm_name),
                                                              self._command_timeout)
        cmd_start = "virsh start {}"
        cmd_result = self._common_content_lib.execute_sut_cmd(cmd_start.format(vm_name),
                                                              "start VM {}".format(vm_name),
                                                              self._command_timeout)
        #        if use_shutdown_resume is not None:
 #           self.shutdown_linux_vm(vm_name)
 #           self.resume_linux_vm(vm_name)
 #       else:
 #           cmd_result = self._common_content_lib.execute_sut_cmd(self.REBOOT_VM_COMMAND
  #                                                                .format(vm_name),
  #                                                                "create snapshot of VM {}".format(vm_name),
  #                                                                self._command_timeout)
  #      self._log.info("Successfully rebooted VM {} : result {}\n"
  #                     .format(vm_name, cmd_result))

    def create_clone_of_linux_vm(self, vm_name, clone_vm_name):
        """
        This method is to clone the guest VM with given VM name

        :param vm_name: name of the VM, whose clone is going to be created
        :param clone_vm_name: name of the cloned VM
        :return: None
        """
        self._log.info("Cloning the VM named {}".format(vm_name))
        self._common_content_lib.execute_sut_cmd(self.CLONE_VM_COMMAND.format(vm_name, clone_vm_name),
                                                 "cloning VM {} to {}".format(vm_name, clone_vm_name), self._command_timeout)
        self._log.info("Successfully cloned the VM {} to VM {}".format(vm_name, clone_vm_name))

    def is_intel_iommu_enabled(self, common_content_lib=None):
        """
        This method is to verify if intel IOMMU is enabled by Kernel or not

        :return : True on Success else False
        """
        if common_content_lib is None:
            common_content_lib = self._common_content_lib
        self._log.info("Checking if intel_iommu is enabled by kernel or not")
        result_virt_host_validate = common_content_lib.execute_sut_cmd_no_exception(self.VIRT_HOST_VALIDATE_CMD,
                                                                                "executing virt host validate command",
                                                                                self._command_timeout,
                                                                                cmd_path=self.ROOT_PATH,
                                                                                ignore_result="ignore")
        self._log.debug("virt-host-validate command result {}".format(result_virt_host_validate))

        # virt_host_validate_result = self.os.execute(self.VIRT_HOST_VALIDATE_CMD, self._command_timeout)
        # self._log.debug("stdout of command {} :\n{}".format(self.VIRT_HOST_VALIDATE_CMD,
        #                                                     virt_host_validate_result.stdout))
        # self._log.debug("stderr of command {} :\n{}".format(self.VIRT_HOST_VALIDATE_CMD,
        #                                                     virt_host_validate_result.stderr))
        # although return code is not 0 still the data feed will be on stdout only
        # virt_host_validate_result_data = virt_host_validate_result.stdout
        virt_host_validate_result_data = result_virt_host_validate.strip()
        check_intel_iommu = re.search(self.CHECK_INTEL_IOMMU_REGEX, virt_host_validate_result_data)
        return check_intel_iommu

    def is_vm_alive_pingtest_from_sut(self, ip_address, ping_count=4):
        """
        This Method is Used to check the system after reboot using Ping VM Network Adapter IP Address

        :ip_address: Ip Address of Network Adapter
        :return: True if Network Interface is pinging else False
        """
        self._log.info("Verify the Connectivity of the system by Pinging Ip")
        ping_command = r"ping " + ip_address + " -c {}".format(ping_count)
        result = self._common_content_lib.execute_sut_cmd_no_exception(
                        ping_command, "execute cmd: {}".format(ping_command),
                        self._command_timeout,
                        ignore_result="ignore")

        self._log.info("ping result for Network Interface Ip '{}' = {}".format(ip_address, str(result)))
        if not re.findall(self.REGEX_CMD_FOR_ADAPTER_IP_PINGABLE, "".join(result)):
            self._log.info("Result - ping " + ip_address + " failed")
            return False
        self._log.info("Result - VM can be pinged and Reachable")
        return True

    def is_vm_alive(self, common_content_lib):
        """
        Check if the OS is alive and responsive, NOT TO BE USED TO CHECK IN CASE OF REBOOT.

        :return: True if OS is alive, False otherwise.
        """
        if common_content_lib is None:
            common_content_lib = self._common_content_lib
        start = time.time()
        result_data = common_content_lib.execute_sut_cmd_no_exception(
            "dir", "execute dir command", self._command_timeout, ignore_result="ignore")
        self._log.debug("execute dir command:\n{}".format(result_data))
        if result_data != "":
            end = time.time()
            total_time_taken = (abs(start - end))
            total_time_taken = ("{:05.2f}".format(total_time_taken))
            self._log.debug("OS is Alive {0} Seconds".format(total_time_taken))
            return True
        else:
            return False

    def check_and_wait_for_system_shutdown(self, ip_address, max_wait_seconds):
        """
        Check for the given if system is shutdown and unresponsive.

        :return: True if OS is alive, False otherwise.
        """
        start_time = time.time()
        wait_seconds = max_wait_seconds
        while True:
            time.sleep(1)
            current_time = time.time()
            elapsed_time = current_time - start_time

            cmd_status = self.is_vm_alive_pingtest_from_sut(ip_address, ping_count=4)

            if cmd_status == False:
                time.sleep(1)
                return True

            if elapsed_time > wait_seconds:
                self._log.info("Error: Finished max wait for system shutdown: " + str(int(elapsed_time)) + " seconds")
                break

        return False

    def check_and_wait_for_system_bootup(self, ip_address, max_wait_seconds):
        """
        Check if the OS booted up and responsive.

        :return: True if OS is alive, False otherwise.
        """
        start_time = time.time()
        wait_seconds = max_wait_seconds
        while True:
            time.sleep(1)
            current_time = time.time()
            elapsed_time = current_time - start_time

            cmd_status = self.is_vm_alive_pingtest_from_sut(ip_address, ping_count=4)

            if cmd_status == True:
                time.sleep(1)
                return True

            if elapsed_time > wait_seconds:
                self._log.info("Error: Finished max wait for system bootup: " + str(int(elapsed_time)) + " seconds")
                break

        return False

    def update_kernelargs_and_reboot_vm(self, vm_name, vm_ip, common_content_lib, list_of_args):
        """
        This method is to update the grub config file by using kernel

        :param list_of_args: list of the arguments want to update
        """
        if common_content_lib is None:
            common_content_lib = self._common_content_lib

        result_data = common_content_lib.execute_sut_cmd("grubby --update-kernel=ALL --args='{}'".format(" ".join(list_of_args)),
                                           "updating grub config file",
                                           self._command_timeout)
        self._log.debug("Updated the grub config file with stdout:\n{}".format(result_data))

        result_data = common_content_lib.execute_sut_cmd(
            "echo restarting && sleep 3 && reboot &".format(" ".join(list_of_args)),
            "rebooting kernel :echo restarting && sleep 3 && reboot &",
            self._command_timeout)
        self._log.debug("Kernel rebooted\n{}".format(result_data))
        time.sleep(5)
        if self.check_and_wait_for_system_shutdown(vm_ip, 60):
            self._log.info("Successfully rebooted the kernel")
        else:
            self._log.error("Warning: VM kernel reboot might have been failed.")
            # try rebooting the VM now
            self.reboot_linux_vm(vm_name)
            time.sleep(5)
            if self.check_and_wait_for_system_shutdown(vm_ip, 60):
                self._log.info("Successfully rebooted the VM")
            else:
                self._log.error("Warning: VM reboot might have been failed.")

        self.check_and_wait_for_system_bootup(vm_ip, 60)
        return True

    def enable_intel_iommu_by_kernel_in_vm(self, vm_name, grub_param=None, common_content_lib=None):
        """
        This method is to enable intel_iommu by using grub menu

        :return: True on Success else False
        """
        if common_content_lib is None:
            common_content_lib = self._common_content_lib

        # get the ip address of VM
        ip_address_vm = self.get_ip(common_content_lib)

        if grub_param is None:
            grub_param = self.INTEL_IOMMU_ON_STR_VM
        self._log.info("Enabling Intel IOMMU")
        self._log.info("Updating the grub config file in VM")

        if self.update_kernelargs_and_reboot_vm(vm_name, ip_address_vm, common_content_lib, [grub_param]):
            self._log.info("Successfully enabled intel_iommu by kernel")
        else:
            self._log.info("Failed to enable intel_iommu by kernel")

        if self.is_intel_iommu_enabled(common_content_lib):
            self._log.info("Intel IOMMU is already enabled by kernel")
            return True
        else:
            if grub_param is None:
                grub_param=self.INTEL_IOMMU_ON_STR_VM
            self._log.info("Enabling Intel IOMMU")
            self._log.info("Updating the grub config file in VM")
            if self.update_kernelargs_and_reboot_vm(vm_name, ip_address_vm, common_content_lib, [grub_param]):
                self._log.info("Successfully enabled intel_iommu by kernel")
            else:
                self._log.info("Failed to enable intel_iommu by kernel")

            return self.is_intel_iommu_enabled(common_content_lib)

    def enable_intel_iommu_by_kernel(self, common_content_lib=None):
        """
        This method is to enable intel_iommu by using grub menu

        :return: True on Success else False
        """
        if common_content_lib is None:
            common_content_lib = self._common_content_lib
        self._log.info("Enabling Intel IOMMU")
        self._log.info("Updating the grub config file")
        common_content_lib.update_kernel_args_and_reboot([self.INTEL_IOMMU_ON_STR])

        if self.is_intel_iommu_enabled(common_content_lib):
            self._log.info("Intel IOMMU is already enabled by kernel")
            return True
        else:
            self._log.info("Enabling Intel IOMMU")
            self._log.info("Updating the grub config file")
            common_content_lib.update_kernel_args_and_reboot([self.INTEL_IOMMU_ON_STR])
            self._log.info("Successfully enabled intel_iommu by kernel")
            return self.is_intel_iommu_enabled(common_content_lib)

    def is_intel_iommu_enabled_vm(self, vmobj):
        """
        This method is to verify if intel IOMMU is enabled by Kernel or not
        :return : True on Success else False
        """
        self._log.info("Checking if intel_iommu is enabled by kernel or not")
        virt_host_validate_result = vmobj.execute(self.VIRT_HOST_VALIDATE_CMD, self._command_timeout)
        self._log.debug("stdout of command {} :\n{}".format(self.VIRT_HOST_VALIDATE_CMD,
                                                            virt_host_validate_result.stdout))
        self._log.debug("stderr of command {} :\n{}".format(self.VIRT_HOST_VALIDATE_CMD,
                                                            virt_host_validate_result.stderr))
        # although return code is not 0 still the data feed will be on stdout only
        virt_host_validate_result_data = virt_host_validate_result.stdout
        check_intel_iommu = re.search(self.CHECK_INTEL_IOMMU_REGEX, virt_host_validate_result_data)
        return check_intel_iommu

    def enable_intel_iommu_by_kernel_vm(self, vmobj, common_content, grub_param):
        """
        This method is to enable intel_iommu by using grub menu

        :return: True on Success else False
        """
        if self.is_intel_iommu_enabled_vm(vmobj):
            self._log.info("Intel IOMMU is already enabled by kernel")
            return True
        else:
            self._log.info("Updating the grub config file in vm")
            self._log.info("Successfully enabled intel_iommu by kernel".format(grub_param))
            cmd = "grubby --update-kernel=ALL --args={}"
            result_data = common_content.execute_sut_cmd(cmd.format(grub_param), "Updating grub on VM",
                                                                  self._command_timeout, self.ROOT_PATH)
            self._log.debug("Updated the grub config file with stdout:\n{}".format(result_data))
            self._log.info("Successfully enabled intel_iommu by kernel")
            return self.is_intel_iommu_enabled_vm(vmobj)


    def create_clone_of_linux_vm(self, vm_name, clone_vm_name):
        """
        This method is to clone the guest VM with given VM name

        :param vm_name: name of the VM, whose clone is going to be created
        :param clone_vm_name: name of the cloned VM
        :return: None
        """
        self._log.info("Cloning the VM named {}".format(vm_name))
        self._common_content_lib.execute_sut_cmd(self.CLONE_VM_COMMAND.format(vm_name, clone_vm_name),
                                                 "cloning VM {} to {}".format(vm_name, clone_vm_name),
                                                 self._command_timeout)
        self._log.info("Successfully cloned the VM {} to VM {}".format(vm_name, clone_vm_name))



    def reboot_linux_vm_sleep(self, vm_name):
        """
        This method is to Reboot the VM

        :param vm_name: Name of the VM, which is going to be rebooted
        :return: None
        """
        self._log.info("Rebooting {} VM".format(vm_name))
        if True == self._vm_provider.is_qemu_vm_running(vm_name):
            reboot = "reboot"
            try:
                reboot_result = self.virt_com_exec_asynccmd_on_qemu_vm(vm_name, cmd=reboot,
                                                                  cmd_str=reboot,
                                                                  cmd_path="/",
                                                                  execute_timeout=self._command_timeout)
            except:
                pass
            self._log.debug(reboot_result)
            time.sleep(60)
        else:
            reboot_result = self._common_content_lib.execute_sut_cmd(self.REBOOT_VM_COMMAND.format(vm_name),
                                                                        "Rebooting {} VM".format(vm_name),
                                                                        self._command_timeout)
            self._log.debug(reboot_result)
            time.sleep(120)

    def get_sriovf_enabled_nw_adapters(self, nic_device_name):
        """
        This method is to get the SRIOVF enabled Ethernet Adapter names

        :param nic_device_name: Name of the external PCI NIC card
        :return : device_list
        """
        device_list = []
        self._log.info("Getting All the SRIOVF enabled NW Adapters")
        self._common_content_lib.execute_sut_cmd("modprobe ice",
                                                               "load ice driver",
                                                               self._command_timeout)
        device_data = self._common_content_lib.execute_sut_cmd("lshw -c network -businfo | grep '{}'"
                                                               .format(nic_device_name),
                                                               "getting network PCI device names",
                                                               self._command_timeout)
        self._log.debug("PCI Device Names:\n{}".format(device_data))
        output_list = device_data.strip().split("\n")
        for output in output_list:
            device_list.append(output.split()[1])
        self._log.info("SRIOVF enabled NW Adapter list : {}".format(device_list))
        return device_list

    def assign_static_ip_to_cross_topology_adapters(self, vf_adapter_name, index, common_content_lib_vm):
        """
        This method is to assign static IP to ethernet device

        :param vm_common_content_lib: object to common content class
        :index static IP number indicator
        :vf_adapter_name ethernet device name of VF
        """
        assign_ip_command = "ip link set {} down; ip addr add {} dev {}; ip link set {} up;".format(
            vf_adapter_name, self.STATIC_IP.format(index), vf_adapter_name, vf_adapter_name)
        self._log.info("Assigning IP to the VF adapter")
        ip_add_opt = common_content_lib_vm.execute_sut_cmd("ip addr add {}/{} dev {}".format(self.STATIC_IP.format(index),
                                                                                        self.NETMASK,
                                                                                        vf_adapter_name),
                                                                                        "ip addr add",
                                                                                        self._command_timeout)

        ip_add_opt = common_content_lib_vm.execute_sut_cmd(self.ASSIGN_STATIC_IP_COMMAND.format(vf_adapter_name,
                                                                                        self.STATIC_IP.format(index),
                                                                                        self.NETMASK),
                                                                                        "assign static ip",
                                                                                        self._command_timeout)
        self._log.debug("IP assign command stdout:\n{}".format(ip_add_opt.stdout))
        self._log.error("IP assign command stderr:\n{}".format(ip_add_opt.stderr))
        self._log.info("Successfully added ip {} and subnet {} to the VF adapter {} ".
                       format(self.STATIC_IP.format(index), self.NETMASK, vf_adapter_name))
        return self.STATIC_IP.format(index)

    def get_virtual_ethernet_adapter_device_in_vm(self, vm_common_content_lib, adapter_string):
        """
        This method is to get the Virtual NW adapter name which is passed through to the VM

        :param vm_common_content_lib: object to common content class
        """
        self._log.info("Getting Virtual Network adapter assigned to VM")
        GET_VIRTUAL_NET_ADAPTER = \
            "modprobe ice;lshw -class network -businfo | grep -i 'Ethernet' | grep {}".format(adapter_string)
        data = vm_common_content_lib.execute_sut_cmd(GET_VIRTUAL_NET_ADAPTER,
                                                                  "get vm virtual adapter", self._command_timeout)
        data1 = data.split("\n")
        for get_vf_name_in_vm in data1:
            if get_vf_name_in_vm is not None and get_vf_name_in_vm != "":
                print(get_vf_name_in_vm)
                vf_adapter_name = get_vf_name_in_vm.strip().split()[1]
                if vf_adapter_name != "":
                    break

        self._log.info("Successfully get the Network Pass through VF device name: {}".format(vf_adapter_name))
        return vf_adapter_name

    def get_virtual_adapter_name_in_vm(self, vm_common_content_lib):
        """
        This method is to get the Virtual NW adapter name which is passed through to the VM

        :param vm_common_content_lib: object to common content class
        """
        self._log.info("Getting Virtual Network adapter assigned to VM")
        get_vf_name_in_vm = vm_common_content_lib.execute_sut_cmd(self.GET_VIRTUAL_NET_ADAPTER_CMD1,
                                                                  "get vm virtual adapter", self._command_timeout)
        print(get_vf_name_in_vm)

        vf_adapter_name = get_vf_name_in_vm.strip().split()[0]
        self._log.info("Successfully get the Network Pass through VF device name: {}".format(vf_adapter_name))
        return vf_adapter_name

    def get_vf_net_adapter_name_in_vm(self, vm_common_content_lib):
        """
        This method is to get the Virtual NW adapter name which is passed through to the VM

        :param vm_common_content_lib: object to common content class
        """
        self._log.info("Getting Virtual Network adapter assigned to VM")
        get_vf_name_in_vm = vm_common_content_lib.execute_sut_cmd(self.GET_VIRTUAL_NET_ADAPTER_CMD,
                                                                  "get vm virtual adapter", self._command_timeout)
        print(get_vf_name_in_vm)

        vf_adapter_name = get_vf_name_in_vm.strip().split()[0]
        self._log.info("Successfully get the Network Pass through VF device name: {}".format(vf_adapter_name))
        return vf_adapter_name

    def create_virtual_function_dlb(self, no_of_vf, vm_index):
        """
        This method is to create Virtual Function for dlb

        :param no_of_vf: No of Virtual Function to create
        """

        # create a new VF
        self._log.info("Creating VFs")
        self._common_content_lib.execute_sut_cmd("echo {} > /sys/class/dlb2/dlb{}/device/sriov_numvfs"
                                                 .format(no_of_vf,vm_index),
                                                 "creating VFs", self._command_timeout)
        self._common_content_lib.execute_sut_cmd("lspci -d :2711","Checking dlb", self._command_timeout)
        vf_no = self._common_content_lib.execute_sut_cmd("cat /sys/class/dlb2/dlb{}/device/sriov_numvfs".format(
                                                                                                            vm_index),
                                                         "verifying no VFs", self._command_timeout)
        self._log.info("No of VF is {}".format(vf_no))

        if int(vf_no) != no_of_vf:
            raise content_exceptions.TestFail("Fail to create the desired no of VFs")

    def create_virtual_function(self, no_of_vf, device_name):
        """
        This method is to create Virtual Function by given NW adapter name

        :param no_of_vf: No of Virtual Function to create
        :param device_name: NW adapter name
        """
        # get the maximum no of VFs supported on the SUT
        max_vf_no = self.get_max_supported_vf_no(device_name)

        if max_vf_no < no_of_vf:
            raise content_exceptions.TestFail("No of VF is {}, which is more than supported no {}".format(no_of_vf,
                                                                                                          max_vf_no))

        # create a new VF
        self._log.info("Creating VFs for {} adapter".format(device_name))
        self._common_content_lib.execute_sut_cmd("echo {} > /sys/class/net/{}/device/sriov_numvfs"
                                                 .format(no_of_vf, device_name),
                                                 "creating VFs", self._command_timeout)

        # verify the no of VF
        self._log.info("Getting no of VFs created")
        vf_no = self._common_content_lib.execute_sut_cmd("cat /sys/class/net/{}/device/sriov_numvfs"
                                                         .format(device_name),
                                                         "verifying no VFs", self._command_timeout)
        self._log.info("No of VF is {}".format(vf_no))

        if int(vf_no) != no_of_vf:
            raise content_exceptions.TestFail("Fail to create the desired no of VFs")

    def remove_virtual_function(self, device_name):
        """
        This method is to remove all Virtual Function by given NW adapter name

        :param device_name: NW adapter name
        """
        # remove all VF
        self._log.info("Removing VFs for {} adapter".format(device_name))
        self._common_content_lib.execute_sut_cmd("echo 0 > /sys/class/net/{}/device/sriov_numvfs"
                                                 .format(device_name),
                                                 "creating VFs", self._command_timeout)

        # verify the no of VF
        self._log.info("Getting no of VFs ")
        vf_no = self._common_content_lib.execute_sut_cmd("cat /sys/class/net/{}/device/sriov_numvfs"
                                                         .format(device_name),
                                                         "verifying no VFs", self._command_timeout)
        self._log.info("No of VF is {}".format(vf_no))

        if int(vf_no) != 0:
            raise content_exceptions.TestFail("Fail to remove all of the VFs")

    def get_vf_adapter_details(self):
        """
        This method is to get the VF details
        """
        # get the VF adapter details
        vf_details = self._common_content_lib.execute_sut_cmd("lspci -D | grep 'Virtual Function'",
                                                              "getting VF info", self._command_timeout)
        self._log.info("VF details:\n{}".format(vf_details))
        return vf_details.split("\n")

    def get_nw_adapter_details(self,nw_device_id):
        """
        This method is to get the PCIe device details

        :param nw_device_id: id of the network device
        :return: True on Success else False
        """
        # get the  adapter details
        nw_details = self._common_content_lib.execute_sut_cmd("lspci -D | grep '{}'".format(nw_device_id),
                                                              "getting VF info", self._command_timeout)
        self._log.info("Network adapter details details:\n{}".format(nw_details))
        return nw_details.split("\n")

    def get_bdf_values_of_nw_device(self, pcie_device):
        """
        This method is to get the BDF values of PCIe device

        :param pcie_device: details of the PCIe device. ex: 0000:6b:02.0 Ethernet controller: Intel Corporation Ethernet
                           Virtual Function 700 Series (rev 02)
        :return: domain-bus-slot-function value
        """
        dbsf_value = re.findall(self._REGEX_TO_FETCH_PCIE_DBSF_VALUES, pcie_device.split("\n")[0])
        domain_value = int(dbsf_value[0].split(":")[0], 16)
        bus_value = int(dbsf_value[0].split(":")[1], 16)
        slot_value = int(dbsf_value[0].split(":")[2].split(".")[0], 16)
        function_value = int(dbsf_value[0].split(":")[2].split(".")[1], 16)
        return domain_value, bus_value, slot_value, function_value

    def get_split_int_bdf_values_from_dbdf(self, dbsf_value):
        """
        This method is to get the BDF values separately from dbsf_value

        :param dbsf_value: dbsf value 0000:6b:02.0
        :return: domain-bus-slot-function value
        """
        domain_value = int(dbsf_value.split(":")[0], 16)
        bus_value = int(dbsf_value.split(":")[1], 16)
        slot_value = int(dbsf_value.split(":")[2].split(".")[0], 16)
        function_value = int(dbsf_value.split(":")[2].split(".")[1], 16)

        return domain_value, bus_value, slot_value, function_value

    def get_split_hex_bdf_values_from_dbdf(self, dbsf_value):
        """
        This method is to get the BDF values separately from dbsf_value

        :param dbsf_value: dbsf value 0000:6b:02.0
        :return: domain-bus-slot-function value
        """
        # domain_value = int(dbsf_value.split(":")[0], 16)
        # bus_value = int(dbsf_value.split(":")[1], 16)
        # slot_value = int(dbsf_value.split(":")[2].split(".")[0], 16)
        # function_value = int(dbsf_value.split(":")[2].split(".")[1], 16)
        domain_value = dbsf_value.split(":")[0].strip()
        bus_value = dbsf_value.split(":")[1].strip()
        slot_value = dbsf_value.split(":")[2].split(".")[0].strip()
        function_value = dbsf_value.split(":")[2].split(".")[1].strip()
        return domain_value, bus_value, slot_value, function_value

    def assign_macs_to_vfs(self, no_of_vf, ip_link_show_data, nw_adapter_name):
        """
        This method is to check & assign mac ids to the VF

        :param no_of_vf: no of the VF need to create
        :param ip_link_show_data: output of the "ip link show" command
        :param nw_adapter_name: Name of the particular network adapter
        """
        ip_link_data_list = ip_link_show_data.split("\n")
        mac_counter = 0
        mac_id = self.TEMPLATE_MAC_ID
        mac_id_list = []
        for vf_no in range(no_of_vf):
            ip_link_data_vf = ip_link_data_list[vf_no]
            if "00:00:00:00:00:00" in ip_link_data_vf:
                self._log.info("Default MAC assignment did not happen, Assigning it")
                # add the mac address to the VFs
                if mac_counter != 0:
                    increment = str(int(mac_id[-2:]) + 1)
                    mac_id = mac_id[:-2] + increment.zfill(2)
                result_data = self._common_content_lib.execute_sut_cmd("ip link set {} vf {} mac {}"
                                                                       .format(nw_adapter_name, vf_no, mac_id),
                                                                       "linking mac to the VF", self._command_timeout)
                self._log.debug("mac link output:\n{}".format(result_data))
                mac_counter = mac_counter + 1
                mac_id_list.append(mac_id)
            else:
                assigned_mac = re.search(r'([0-9A-F]{2}[:-]){5}([0-9A-F]{2})', ip_link_data_vf, re.I).group()
                mac_id_list.append(assigned_mac)
        return mac_id_list

    def _enable_yum_repo_in_cent_vm(self, vm_os_obj):

        """
        This method is to enable yum repo in VM



        :param vm_os_obj: os object of VM
        :param repo_path_host: Name of the yum repo
        """

        self._log.info("Enabling yum repo in VM")
        repo_file_name = "CentOS_Repos.zip"
        new = "/root/repo_1"
        vm_os_obj.execute("mkdir {}.format(new)", self._command_timeout)
        repo_file_path = self._install_collateral.download_tool_to_host(repo_file_name)
        vm_install_collateral = InstallCollateral(self._log, vm_os_obj, self._cfg)
        # Move repo.zip file to SUT and extract with folder RHEL_REPOS
        sut_repo_folder_path = vm_install_collateral.download_and_copy_zip_to_sut(new, repo_file_name)
        rm_cmd = "rm -rf /etc/yum.repos.d/*"
        vm_os_obj.execute(rm_cmd, self._command_timeout)
        new = "/root/repo_1/yum.repos.d/test.repo"
        cmd = "cp -rf {} {}"
        vm_os_obj.execute(cmd.format(new, self.REPOS_FOLDER_PATH_SUT), self._command_timeout)
        # Moving all repo file from RHEL_REPOS folder to /etc/yum.repos.d
        # vm_os_obj.execute("yes | cp {} {}".format(sut_repo_folder_path, self.REPOS_FOLDER_PATH_SUT),
        #                  self._command_timeout)
        self._log.info("Successfully copied the repos file to VM")
        yum_conf_result = vm_os_obj.execute("cat {}".format(self.YUM_CONF_FILE_PATH), self._command_timeout)
        self._log.debug("stdout of {}:\n{}".format(self.YUM_CONF_FILE_PATH, yum_conf_result.stdout))
        self._log.error("stderr of {}:\n{}".format(self.YUM_CONF_FILE_PATH, yum_conf_result.stderr))
        if self.PROXY_STR not in yum_conf_result.stdout:
            vm_os_obj.execute(r"sed -i.bak '$ a\{}' {}".format(self.PROXY_STR, self.YUM_CONF_FILE_PATH),
                              self._command_timeout)
        self._log.info("Added the proxy in {}".format(self.YUM_CONF_FILE_PATH))
        for command in self.ENABLE_YUM_REPO_COMMANDS:
            cmd_opt = vm_os_obj.execute(command, self._command_timeout)
        self._log.debug("{} stdout:\n{}".format(command, cmd_opt.stdout))
        self._log.error("{} stderr:\n{}".format(command, cmd_opt.stderr))
        self._log.info("Successfully enabled YUM repos")

    def force_poweroff_and_start_vm_linux(self, vm_name):
        """
        This function is to power off and start the VM
        :param vm_name name of the VM
        """
        vm_ip = self._vm_provider.get_vm_ip(vm_name)
        self.shutdown_linux_vm(vm_name)
        if self.check_and_wait_for_system_shutdown(vm_ip, 60):
            self._log.info("Successfully shutodown the VM")
        else:
            self._log.error("Warning: VM kernel reboot might have been failed.")
            # try shutting down the VM now
            cmd = "virsh destroy {} --graceful"
            self._common_content_lib.execute_sut_cmd(cmd.format(vm_name),
                                                                  "force off VM {}".format(vm_name),
                                                                  self._command_timeout)
            time.sleep(5)
            if self.check_and_wait_for_system_shutdown(vm_ip, 60):
                self._log.info("Successfully shut the VM down")
            else:
                self._log.error("Warning: VM shutdown might have been failed.")

        self.start_linux_vm(vm_name)
        self.check_and_wait_for_system_bootup(vm_ip, 60)

    def attach_pci_nw_device_to_vm(self, pcie_device, vm_name):
         """
         This method is to attach the PCI NW devices to VM

         :param pcie_device: details of the PCIe device. ex: 0000:6b:02.0 Ethernet controller: Intel Corporation Ethernet
                           Virtual Function 700 Series (rev 02)
         :param vm_name: name of the VM
         """
         # writing the value in the pci xml file to add the device to the VM
         self._log.info("Attaching the PCIe card to the VM {}".format(vm_name))
         # get attached bdf values
         domain_value, bus_value, slot_value, function_value = self.get_bdf_values_of_nw_device(pcie_device)
         with open(self.PCI_DEVICE_XML_FILE_NAME, "w+") as fp:
             fp.writelines(self.PCI_DEVICE_XML_FILE_DATA.format(domain_value, bus_value, slot_value, function_value))
         self._log.info("Coping the {} file to SUT".format(self.PCI_DEVICE_XML_FILE_NAME))
         self.os.copy_local_file_to_sut(self.PCI_DEVICE_XML_FILE_NAME, self.ROOT_PATH)
         self._log.info("Successfully copied the {} file to SUT".format(self.PCI_DEVICE_XML_FILE_NAME))
         try:
             self._common_content_lib.execute_sut_cmd("virsh detach-device {} /root/{}".format(vm_name,
                                                                                               self.PCI_DEVICE_XML_FILE_NAME),
                                                      "detaching the PCIe card to the VM", self._command_timeout)
         except:
             pass
         attach_result = self._common_content_lib.execute_sut_cmd("virsh attach-device {} /root/{} --config".format(vm_name,
                                                                                                          self.PCI_DEVICE_XML_FILE_NAME),
                                                                 "attaching the PCIe card to the VM", self._command_timeout)
         # below is required in case attach-device is called with --config but this reboot will remove
         # all dynamically loaded drivers usinf insmod/modprobe
         # If one doesn't want to use --config option which requires reboot of system to make the attached device
         # to be available in system, just remove/comment the below function as well "force_poweroff_and_start_vm_linux()"
         self.force_poweroff_and_start_vm_linux(vm_name)
         self._log.debug("attach result:\n{}".format(attach_result))
         self._log.info("Successfully attached the PCIe card to the VM {}".format(vm_name))

    def attach_vqat_instance_to_vm(self, vm_name, dev_uuid):
        """
        This method is to attach the vqat instance to VM

        :param vm_name: name of the VM
        :param dev_uuid : details of the vqat device. ex: bff48604-6d9e-4796-9ed3-3c1ab250128c
        """
        # writing the value in the xml file to add the device to the VM
        self._log.info("Attaching the mdev instance to the VM {}".format(vm_name))
        # get attached bdf values
        with open(self.VQAT_DEVICE_XML_FILE_NAME, "w+") as fp:
            fp.writelines(self.VQAT_DEVICE_XML_FILE_DATA.format(dev_uuid))
        self._log.info("Coping the {} file to SUT".format(self.VQAT_DEVICE_XML_FILE_NAME))
        self.os.copy_local_file_to_sut(self.VQAT_DEVICE_XML_FILE_NAME, self.ROOT_PATH)
        self._log.info("Successfully copied the {} file to SUT".format(self.VQAT_DEVICE_XML_FILE_NAME))
        try:
            self._common_content_lib.execute_sut_cmd(
                "virsh detach-device {} /root/{}".format(vm_name,
                                                                  self.VQAT_DEVICE_XML_FILE_NAME),
                "detaching the mdev device to the VM",
                self._command_timeout)
        except:
            pass
        attach_result = self._common_content_lib.execute_sut_cmd("virsh attach-device {} /root/{} --config".format(vm_name,
                                                                                                          self.VQAT_DEVICE_XML_FILE_NAME),
                                                                 "attaching the mdev device to the VM",
                                                                 self._command_timeout)
        # below is required in case attach-device is called with --config but this reboot will remove
        # all dynamically loaded drivers usinf insmod/modprobe
        # If one doesn't want to use --config option which requires reboot of system to make the attached device
        # to be available in system, just remove/comment the below function as well "force_poweroff_and_start_vm_linux()"
        self.force_poweroff_and_start_vm_linux(vm_name)
        self._log.debug("attach result:\n{}".format(attach_result))
        self._log.info("Successfully attached the mdev instance to the VM {}".format(vm_name))

    def detach_vqat_instance_from_vm(self, vm_name, dev_uuid):
        """
        This method is to detach the vqat instance from VM

        :param vm_name: name of the VM
        :param dev_uuid : details of the vqat device instance. ex: bff48604-6d9e-4796-9ed3-3c1ab250128c
        """
        # writing the value in the xml file to add the device to the VM
        self._log.info("Detaching the mdev instance to the VM {}".format(vm_name))
        # get attached bdf values
        with open(self.VQAT_DEVICE_XML_FILE_NAME, "w+") as fp:
            fp.writelines(self.VQAT_DEVICE_XML_FILE_DATA.format(dev_uuid))
        self._log.info("Coping the {} file to SUT".format(self.VQAT_DEVICE_XML_FILE_NAME))
        self.os.copy_local_file_to_sut(self.VQAT_DEVICE_XML_FILE_NAME, self.ROOT_PATH)
        self._log.info("Successfully copied the {} file to SUT".format(self.VQAT_DEVICE_XML_FILE_NAME))

        detach_result = self._common_content_lib.execute_sut_cmd_no_exception("virsh detach-device {} /root/{}".format(vm_name,
                                                                                                          self.VQAT_DEVICE_XML_FILE_NAME),
                                                                 "detaching the mdev device from the VM",
                                                                 self._command_timeout,
                                                                 ignore_result="ignore")
        self._log.debug("detach result:\n{}".format(detach_result))
        self._log.info("Successfully detached the mdev instance from the VM {}".format(vm_name))

    def attach_mdev_instance_to_vm(self, vm_name, mdev_uuid):
        """
        This method is to attach the Mdev instance to VM

        :param vm_name: name of the VM
        :param mdev_uuid : details of the mdev_instance device. ex: bff48604-6d9e-4796-9ed3-3c1ab250128c
        """
        # writing the value in the xml file to add the device to the VM
        self._log.info("Detaching the mdev instance to the VM {}".format(vm_name))
        # get attached bdf values
        with open(self.MDEV_DEVICE_XML_FILE_NAME, "w+") as fp:
            fp.writelines(self.MDEV_DEVICE_XML_FILE_DATA.format(mdev_uuid))
        self._log.info("Coping the {} file to SUT".format(self.MDEV_DEVICE_XML_FILE_NAME))
        self.os.copy_local_file_to_sut(self.MDEV_DEVICE_XML_FILE_NAME, self.ROOT_PATH)
        self._log.info("Successfully copied the {} file to SUT".format(self.MDEV_DEVICE_XML_FILE_NAME))
        try:
            self._common_content_lib.execute_sut_cmd("virsh detach-device {} /root/{}".format(vm_name,
                                                                                                       self.MDEV_DEVICE_XML_FILE_NAME),
                                                     "detaching the mdev device to the VM",
                                                     self._command_timeout)
        except:
            pass
        attach_result = self._common_content_lib.execute_sut_cmd("virsh attach-device {} /root/{} --config".format(vm_name,
                                                                                                          self.MDEV_DEVICE_XML_FILE_NAME),
                                                                 "attaching the mdev device to the VM",
                                                                 self._command_timeout)
        # below is required in case attach-device is called with --config but this reboot will remove
        # all dynamically loaded drivers usinf insmod/modprobe
        # If one doesn't want to use --config option which requires reboot of system to make the attached device
        # to be available in system, just remove/comment the below function as well "force_poweroff_and_start_vm_linux()"
        self.force_poweroff_and_start_vm_linux(vm_name)
        self._log.debug("attach result:\n{}".format(attach_result))
        self._log.info("Successfully attached the mdev instance to the VM {}".format(vm_name))

    def detach_mdev_instance_from_vm(self, vm_name, mdev_uuid):
        """
        This method is to detach the Mdev instance from VM

        :param vm_name: name of the VM
        :param mdev_uuid : details of the mdev_instance device. ex: bff48604-6d9e-4796-9ed3-3c1ab250128c
        """
        # writing the value in the xml file to add the device to the VM
        self._log.info("Detaching the mdev instance to the VM {}".format(vm_name))
        # get attached bdf values
        with open(self.MDEV_DEVICE_XML_FILE_NAME, "w+") as fp:
            fp.writelines(self.MDEV_DEVICE_XML_FILE_DATA.format(mdev_uuid))
        self._log.info("Coping the {} file to SUT".format(self.MDEV_DEVICE_XML_FILE_NAME))
        self.os.copy_local_file_to_sut(self.MDEV_DEVICE_XML_FILE_NAME, self.ROOT_PATH)
        self._log.info("Successfully copied the {} file to SUT".format(self.MDEV_DEVICE_XML_FILE_NAME))

        detach_result = self._common_content_lib.execute_sut_cmd("virsh detach-device {} /root/{}".format(vm_name,
                                                                                                          self.MDEV_DEVICE_XML_FILE_NAME),
                                                                 "detaching the mdev device from the VM",
                                                                 self._command_timeout)
        self._log.debug("detach result:\n{}".format(detach_result))
        self._log.info("Successfully detached the mdev instance from the VM {}".format(vm_name))

    def detach_pci_nw_device_from_vm(self, pcie_device, vm_name):
        """
        This method is to detach the pci nw device from the VM

        :param pcie_device: details of the PCIe device. ex: 0000:6b:02.0 Ethernet controller: Intel Corporation Ethernet
                           Virtual Function 700 Series (rev 02)
        :param vm_name: name of the VM
        """
        # writing the value in the pci xml file to add the device to the VM

        self._log.info("Detaching the Pcie device from the {} VM".format(vm_name))
        domain_value, bus_value, slot_value, function_value = self.get_bdf_values_of_nw_device(pcie_device)
        with open(self.PCI_DEVICE_XML_FILE_NAME, "w+") as fp:
            fp.writelines(self.PCI_DEVICE_XML_FILE_DATA.format(domain_value, bus_value, slot_value, function_value))
        self._log.info("Copying the {} file to SUT".format(self.PCI_DEVICE_XML_FILE_NAME))
        self.os.copy_local_file_to_sut(self.PCI_DEVICE_XML_FILE_NAME, self.ROOT_PATH)
        detach_result = self._common_content_lib.execute_sut_cmd("virsh detach-device {} /root/{}".format(vm_name,
                                                                                                          self.PCI_DEVICE_XML_FILE_NAME),
                                                                 "detaching the Pcie device from the VM", self._command_timeout)
        self._log.debug("detach result:\n{}".format(detach_result))
        self._log.info("Successfully detached the Pcie device from the VM {}".format(vm_name))

    def get_nw_adapters_in_vm(self, vm_os_obj, nic_device_name):
        """
        This method is to get the Ethernet Adapter names

        :param nic_device_name: Name of the external PCI NIC card
        :param vm_os_obj: os object of VM
        :return : device_list
        """
        device_list = []
        self._log.info("Getting All the NW Adapters")
        device_data = vm_os_obj.execute("lshw -c network -businfo | grep '{}'"
                                                               .format(nic_device_name),
                                                                self._command_timeout)
        self._log.debug("PCI Device Names:\n{}".format(device_data))
        output_list = device_data.stdout.strip().split("\n")
        for output in output_list:
            device_list.append(output.split()[1])
        self._log.info("NW Adapter list : {}".format(device_list))
        return device_list

    def assign_static_ip_to_nw_adapters_in_vm(self, vm_os_obj, nw_adapter_list):
        """
        This method is to assign static ip to the given NW adapter list

        :param vm_os_obj: os object of VM
        :param nw_adapter_list: a list type with NW adapter names
        :return :network_interface_dict
        """
        network_interface_dict = {}
        for index in range(len(nw_adapter_list)):
            self._log.info("Assigning Static Ip {} to Interface {}".format(self.STATIC_IP.format(index),
                                                                           nw_adapter_list[index]))
            vm_os_obj.execute(self.ASSIGN_STATIC_IP_COMMAND.format(nw_adapter_list[index],
                                                                     self.STATIC_IP.format(index), self.NETMASK),
                                                                    self._command_timeout)
            network_interface_dict[nw_adapter_list[index]] = self.STATIC_IP.format(index), self.NETMASK
        self._log.info("Static IP's are Assigned to Network Interfaces Successfully")
        self._log.debug("Network Interface Dict is {}".format(network_interface_dict))
        return network_interface_dict

    def get_network_interface_ip_list_in_vm(self, vm_os_obj):
        """
        This Method is Used to Get Network Adapter Interface IP's.

        :param vm_os_obj: os object of VM
        :return: ip_list
        """
        self._log.info("Get Network Adapter Interface Ip's")
        ip_list_obj = vm_os_obj.execute(self.READ_IP_ADDRESS_ALL, self._command_timeout)
        ip_list = ip_list_obj.stdout.strip().split("\n")
        self._log.debug("Adapter Ip is : ".format(ip_list))
        return ip_list

    def get_network_interface_name_all(self):
        """
        This method is used to get network interface name by using nmcli device status command

        :return: network_interface_name
        """
        if (self.os.os_type).lower() == (OperatingSystems.LINUX).lower():
            network_interface_cmd = self.NETWORK_INTERFACE_COMMAND_L
        elif (self.os.os_type).lower() == (OperatingSystems.WINDOWS).lower():
            network_interface_cmd = self.NETWORK_INTERFACE_COMMAND_W
        elif (self.os.os_type).lower() == (OperatingSystems.ESXI).lower():
            self._log.info("commands needs to be implemented for ESXi")
            network_interface_cmd = self.NETWORK_INTERFACE_COMMAND_E
        self._log.info("Fetching Network Interface Name")
        network_interface_cmd_output = self._common_content_lib. \
            execute_sut_cmd(network_interface_cmd,
                            network_interface_cmd,
                            self._command_timeout)
        network_interface_string_regex = re.compile(self.REGEX_CMD_FOR_ALL_NETWORK_ADAPTER_NAME, re.MULTILINE)
        network_interface_string = network_interface_string_regex.findall(network_interface_cmd_output)
        network_interface_name = [line.split(" ")[0].strip() for line in network_interface_string]
        self._log.debug("Network Interface name is {}".format(network_interface_name))
        return network_interface_name

    def get_network_interface_name(self):
        """
        This method is used to get network interface name by using nmcli device status command

        :return: network_interface_name
        """
        if (self.os.os_type).lower() == (OperatingSystems.LINUX).lower():
            network_interface_cmd = self.NETWORK_INTERFACE_COMMAND_L
        elif (self.os.os_type).lower() == (OperatingSystems.WINDOWS).lower():
            network_interface_cmd = self.NETWORK_INTERFACE_COMMAND_W
        elif (self.os.os_type).lower() == (OperatingSystems.ESXI).lower():
            network_interface_cmd = self.NETWORK_INTERFACE_COMMAND_E
        self._log.info("Fetching Network Interface Name")
        network_interface_cmd_output = self._common_content_lib. \
            execute_sut_cmd(network_interface_cmd,
                            network_interface_cmd,
                            self._command_timeout)
        network_interface_string = re.compile(self.REGEX_CMD_FOR_NETWORK_ADAPTER_NAME)
        network_interface_name = " ".join(network_interface_string.search(network_interface_cmd_output).group().strip()
                                          .split("\n")[0].strip().split()).split(" ")[2]
        self._log.debug("Network Interface name is {}".format(network_interface_name))
        return network_interface_name

    def assign_ip_to_vf_in_vm(self, vm_os_obj, ip, netmask, vf_adapter_name, vm_name):
        """
        This method is to assign the IP in VF within VM

        :param vm_os_obj:
        :param ip:
        :param netmask:
        :param vf_adapter_name: name of the adapter of the VF in VM
        :param vm_name: Name of the VM
        """
        self._log.info("Assigning IP to the VF adapter in VM")
        ip_add_opt = vm_os_obj.execute("ip addr add {}/{} dev {}".format(ip, netmask, vf_adapter_name),
                                        self._command_timeout)

        ip_add_opt = vm_os_obj.execute(self.ASSIGN_STATIC_IP_COMMAND.format(vf_adapter_name, ip, netmask),
                            self._command_timeout)
        self._log.debug("IP assign command stdout:\n{}".format(ip_add_opt.stdout))
        self._log.error("IP assign command stderr:\n{}".format(ip_add_opt.stderr))
        self._log.info("Successfully added ip {} and subnet {} to the VF adapter {} in VM {}".
                       format(ip, netmask, vf_adapter_name, vm_name))

    def get_vf_adapter_name_in_vm(self, vm_name, vf_mac_id):
        """
        This method is to get the NW adapter name(VF) which is passed through to the VM

        :param vm_name: Name of the VM
        :param vf_mac_id: MAC ID of the VF
        :return vf_adapter_name: name of the adapter of the VF in VM
        """
        self._log.info("Getting Network Pass through VF device name")
        get_vf_name_in_vm = self._common_content_lib.execute_sut_cmd("virsh -q domifaddr {} --source agent | grep {}"
                                                                     .format(vm_name, vf_mac_id.lower()),
                                                                     "get vm ip info", self._command_timeout)
        vf_adapter_name = get_vf_name_in_vm.strip().split()[0]
        self._log.info("Successfully get the Network Pass through VF device name: {}".format(vf_adapter_name))
        return vf_adapter_name

    def verify_vf_in_vm(self, vm_os_obj):
        """
        This method is to verify the VF in VM after attaching the VF

        :param vm_os_obj: os object with VM cfg opts
        """
        self._log.info("Getting VF info in the VM")
        lspci_opt = vm_os_obj.execute("lspci -D| grep -i ethernet", self._command_timeout)
        self._log.debug("VF info command in VM stdout {} stderr {}".format(lspci_opt.stdout,
                                                                           lspci_opt.stderr))

        REGEX_CMD_FOR_VERIFYING_VIRTUAL_ADAPTER_IN_VM = r".*Ethernet\s.*Virtual\sFunction.*"
        lspci_output_list = re.findall(REGEX_CMD_FOR_VERIFYING_VIRTUAL_ADAPTER_IN_VM, lspci_opt.stdout)
        list_len = len(lspci_output_list)
        if list_len == 0:
            raise content_exceptions.TestFail("Fail to verify VF in the VM")
        self._log.info("Successfully verified VF in the VM {}".format(lspci_output_list))
        self._log.info("Getting VF driver in the VM")
        vf_driver_opt = vm_os_obj.execute("lsmod | grep -i vf", self._command_timeout)
        self._log.debug("Stdout of get VF driver command stdout {} stderr {}".format(vf_driver_opt.stdout,
                                                                                     vf_driver_opt.stderr))

    def verify_gen4_vm(self, vm_os_obj):
        """
        This method is to verify the VF in VM after attaching the VF

        :param vm_os_obj: os object with VM cfg opts
        """
        self._log.info("Getting VF info in the VM")
        lspci_opt = vm_os_obj.execute("lspci -D| grep -i E810-C", self._command_timeout)
        self._log.debug("VF info command in VM stdout {} stderr {}".format(lspci_opt.stdout,
                                                                           lspci_opt.stderr))

    def get_vf_mac_details(self, dev_name=None):
        """
        This method is to get the info about the VF MAC details

        :return ip_link_show_opt: output of the "ip link show" command
        """
        if dev_name is None:
            ip_link_show_opt = self._common_content_lib.execute_sut_cmd("ip link show | grep vf",
                                                                        "run ip link show command",
                                                                        self._command_timeout)
        else:
            output = self._common_content_lib.execute_sut_cmd("ip link show",
                                                                        "run ip link show command",
                                                                        self._command_timeout)

            ip_link_show_opt_list = re.findall(r".*vf.*", output)
            if len(ip_link_show_opt_list) == 0:
                # ip_link_show_opt_list = re.findall(r".*{}v\d+.*".format(dev_name), output)
                ip_link_show_opt_list = output.split("\n")
                # initialize an empty string
                ip_link_show_opt = ""
                # ip_link_show_opt = re.findall(r".*{}v\d+.*".format(devname), output, re.M)
                for index, element in enumerate(ip_link_show_opt_list):
                    data = re.findall(r".*{}v\d+.*".format(dev_name), element, re.M)
                    if re.findall(r".*{}v\d+.*".format(dev_name), element, re.M):
                        ip_link_show_opt += element
                        ip_link_show_opt += " "
                        ip_link_show_opt += ip_link_show_opt_list[index + 1]
                        ip_link_show_opt += "\n"

        self._log.info("ip_link_show_opt:\n{}".format(ip_link_show_opt))
        return ip_link_show_opt

    def get_vf_mac_details_list(self):
        """
        This function fetches the mac address details of the virtual function created.
        :return: mac_addr string
        """
        self._log.info("Getting Virtual Network adapter assigned to VM")
        get_vf_name = self._common_content_lib.execute_sut_cmd(self.GET_VIRTUAL_FUNCTION_MAC_ADDR,
                                                                  "get vm virtual adapter", self._command_timeout)
        print(get_vf_name)
        mac_list = []
        link_show_opt_list = re.findall(r"[0-9a-f]{2}[_][0-9a-f]{2}[_][0-9a-f]{2}[_][0-9a-f]{2}[_][0-9a-f]{2}[_][0-9a-f]{2}", get_vf_name)
        for mac_addr in link_show_opt_list:
             mac_list.append(re.sub("_", ":", mac_addr))
        return r"\n".join(mac_list)

    def get_vf_net_adapter_detail_in_vm(self, common_content_lib):
        """
        This function fetches the mac address details of the virtual function created.
        :return: mac_addr string
        """
        self._log.info("Getting Virtual Network adapter assigned to VM")
        get_vf_name = common_content_lib.execute_sut_cmd(self.GET_VF_NET_ADAPTER_NAME,
                                                               "get vm virtual adapter", self._command_timeout)
        print(get_vf_name.strip())
        return get_vf_name

    def verify_vf_mac_details(self, mac_id_list, dev_name = None):
        """
        This method is to verify the VF MAC details

        :param mac_id_list: list of assigned MAC ids
        """
        ip_link_show_opt = self.get_vf_mac_details(dev_name)
        for mac_id in mac_id_list:
            if mac_id.lower() not in ip_link_show_opt:
                raise content_exceptions.TestFail("Fail to verify VF mac details")
        self._log.info("Successfully verified the VF MAC ids")

    def get_and_verify_vf_module_details(self):
        """
        This method is to get the VF module details
        """
        self._log.info("Getting VF module information")
        vf_module_data = self._common_content_lib.execute_sut_cmd("lsmod | grep -i vf",
                                                                  "getting the all VF module info",
                                                                  self._command_timeout)
        self._log.info("VF module info: \n{}".format(vf_module_data))
        if self.VF_MODULE_STR not in vf_module_data:
            raise content_exceptions.TestFail("Fail to verify VF module info")
        self._log.info("Successfully verified the VF module")

    def assign_static_ip_to_nw_adapters(self, nw_adapter_list):
        """
        This method is to assign static ip to the given NW adapter list

        : param nw_adapter_list: a list type with NW adapter names
        :return :network_interface_dict
        """
        network_interface_dict = {}
        for index in range(len(nw_adapter_list)):
            self._log.info("Assigning Static Ip {} to Interface {}".format(self.STATIC_IP.format(index),
                                                                           nw_adapter_list[index]))
            self._common_content_lib. \
                execute_sut_cmd(self.ASSIGN_STATIC_IP_COMMAND.format(nw_adapter_list[index],
                                                                     self.STATIC_IP.format(index), self.NETMASK),
                                "Assigning Static IP", self._command_timeout)
            network_interface_dict[nw_adapter_list[index]] = self.STATIC_IP.format(index), self.NETMASK
        self._log.info("Static IP's are Assigned to Network Interfaces Successfully")
        self._log.debug("Network Interface Dict is {}".format(network_interface_dict))
        return network_interface_dict

    def get_max_supported_vf_no(self, nw_adapter_name):
        """
        This method is to get the maximum supported VF no for a nw adapter

        :param nw_adapter_name: Name of the Network Device ex: ens11f0
        :return: max no of supported VF
        """
        # get the maximum no of VFs supported on the SUT
        max_vf_no = self._common_content_lib.execute_sut_cmd("cat /sys/class/net/{}/device/sriov_totalvfs"
                                                             .format(nw_adapter_name),
                                                             "getting max VF nos", self._command_timeout)
        self._log.info("Maximum supported no of VF for adapter {} is {}".format(nw_adapter_name, max_vf_no))
        return int(max_vf_no)

    def get_network_interfaces(self, common_content_lib=None):
        """
        This Method is Used to Get Network Adapter Interface Names.

        :return: network_interfaces_list
        """
        if (self.os.os_type).lower() == (OperatingSystems.LINUX).lower():
            network_interface_cmd = self.NETWORK_INTERFACE_COMMAND_L
        elif (self.os.os_type).lower() == (OperatingSystems.WINDOWS).lower():
            network_interface_cmd = self.NETWORK_INTERFACE_COMMAND_W
        elif (self.os.os_type).lower() == (OperatingSystems.ESXI).lower():
            network_interface_cmd = self.NETWORK_INTERFACE_COMMAND_E
        if common_content_lib is None:
            common_content_lib = self._common_content_lib
        self._log.info("Fetching Network Adapter Interface Name")
        network_interface_cmd_output = common_content_lib. \
            execute_sut_cmd(network_interface_cmd,
                            network_interface_cmd,
                            self._command_timeout)
        network_interface_regex = re.compile("{}|{}".format(self.REGEX_FOR_NW_ADAPTER_INTERFACE, self.REGEX_FOR_NW_BRIDGE_INTERFACE))
        network_interface_string = network_interface_regex.findall(network_interface_cmd_output)
        network_interfaces_list = [line.split(" ")[0].strip() for line in network_interface_string]
        self._log.debug("Network Adapter Interface's are {}".format(", ".join(network_interfaces_list)))
        return network_interfaces_list


    def get_ip(self, common_content_lib):
        """
        This Method is Used to Get System Ip through Ifconfig Command.

        :return: sys_ip_value
        :raise content_exceptions.TestSetupError: If System is not Configured with 192 Series IP Address.
        """
        self._log.info("Fetching SUT Ip")
        interface_list = self.get_network_interfaces(common_content_lib)
        for interface in interface_list:
            sys_ip_cmd = common_content_lib.execute_sut_cmd(
                self.SYSTEM_IP_COMMAND_DEVICE.format(interface), "SUT IP Command",
                self._command_timeout)
            sys_ip_string = re.compile(self.REGEX_CMD_FOR_SYSTEM_IP_INET)
            if sys_ip_string.search(sys_ip_cmd):
                sys_ip_value = sys_ip_string.search(sys_ip_cmd).group().strip().split(" ")[1]
                self.network_interface_name = interface
                self._log.debug("Network Interface is {}".format(interface))
                self._log.debug("SUT IP is : {}".format(sys_ip_value))
                return sys_ip_value
        raise content_exceptions.TestSetupError("System does not have {} Series Ip Address as part of P2P Connection".format(self.REGEX_CMD_FOR_SYSTEM_IP_INET))

    def get_nvm_info(self):
        nvme_list = []
        fdisk_info = self._common_content_lib.execute_sut_cmd(self.CMD_FDISK, self.CMD_FDISK, self._command_timeout,
                                                              self.ROOT_PATH)
        self._log.debug("Disk information:{}".format(fdisk_info))
        # Check NVMe DISK Details
        nvme_disk_info = re.findall(self.NVME_DISK_INFO_REGEX, fdisk_info)
        self._log.debug("Disk /dev/nvme0n1 size is : {}".format(nvme_disk_info))
        if nvme_disk_info is not None:
            nvme_list.add(nvme_disk_info)
        nvme1_disk_info = re.findall(self.NVME1_DISK_INFO_REGEX, fdisk_info)
        self._log.debug("Disk /dev/nvme1n1 size is : {}".format(nvme1_disk_info))
        if nvme_disk_info is not None:
            nvme_list.add(nvme_disk_info)
        if (not nvme_disk_info) and (not nvme1_disk_info):
            raise content_exceptions.TestFail("Failed to verify NVMe disk information in {}".format(self.CMD_FDISK))
        return nvme_list

    def execute_dynamo(self, timeout_test):
        """
        1. Copy Dynamo tool into Linux target SUT and run EXECUTE_DYNAMO_METER_CMD
        2. Run iometer.reg file in Host machine to accept Intel Open Source License.
        3. On Windows Host system, run EXECUTE_IOMETER_CMD

        :return: True or False
        :raise: content_exceptions.TestFail
        """
        fdisk_info = self._common_content_lib.execute_sut_cmd(self.CMD_FDISK, self.CMD_FDISK, self._command_timeout,
                                                              self.ROOT_PATH)
        self._log.debug("Disk information:{}".format(fdisk_info))
        # Check NVMe DISK Details
        nvme_disk_info = re.findall(self.NVME_DISK_INFO_REGEX, fdisk_info)
        self._log.debug("Disk /dev/nvme0n1 size is : {}".format(nvme_disk_info))
        nvme1_disk_info = re.findall(self.NVME1_DISK_INFO_REGEX, fdisk_info)
        self._log.debug("Disk /dev/nvme1n1 size is : {}".format(nvme1_disk_info))
        if (not nvme_disk_info) and (not nvme1_disk_info):
            raise content_exceptions.TestFail("Failed to verify NVMe disk information in {}".format(self.CMD_FDISK))
        # Copy Dynamo meter to sut
        sut_folder_path = self._install_collateral.install_dynamo_tool_linux()
        # Getting the HOST IP
        hostname = socket.gethostname()
        host_ip = socket.gethostbyname(hostname)
        self._log.debug("HOST IP:{}".format(host_ip))
        # Getting the SUT IP
        sut_ip = self._common_content_lib.execute_sut_cmd(self.IP_ADDRESS_SUT, self.IP_ADDRESS_SUT,
                                                          self._command_timeout, self.ROOT_PATH)
        self._log.debug("SUT IP:{}".format(sut_ip))
        # executing dynamo cmd in the sut
        self.os.execute_async( DynamoToolConstants.EXECUTE_DYNAMO_METER_CMD.format(host_ip, sut_ip), sut_folder_path)
        time.sleep((timeout_test * 60) + TimeConstants.FIVE_MIN_IN_SEC)
        return True

    def execute_ping_flood_test(self, common_content_obj, dest_ip, exec_time):
        """
        This Method is Used to Execute ping with flood.

        :param exec_time: Iperf Execution Time.
        :raise content_exceptions.TestFail: If there is any Data Loss at Client Side.
        """
        src_ip = self.get_ip(common_content_obj)
        self._log.info("start ping from src ip {} to dest ip {}".format(src_ip, dest_ip))
        exec_time_min = 30
        if exec_time_min < exec_time:
            exec_time_min = exec_time
        self._log.debug("Started ping flooding test: {}".format(self.cmd_for_ping.format(dest_ip, exec_time_min)))
        cmd_output = common_content_obj.execute_sut_cmd(self.cmd_for_ping.format(dest_ip, exec_time_min),
                                                              self.cmd_for_ping.format(dest_ip, exec_time_min),
                                                              exec_time_min+self._command_timeout)
        self._log.debug("Completed ping flooding test: {}".format(cmd_output))

        match = re.compile(
            r'(\d+) packets transmitted, (\d+) (?:packets )?received, (\d+\.?\d*)% packet loss').search(cmd_output)
        if not match:
            raise content_exceptions.TestFail('Invalid PING output:\n' + cmd_output)

        sent, received, packet_loss = match.groups()
        # check for ping output and loss

        if (int(sent) != int(received)) and (float(packet_loss) > 5) :
            raise content_exceptions.TestFail("Data Loss is Observed at test {}%".format(packet_loss))
            return False

        self._log.info("There is No Data Loss in ping flodding test from {} ==> {}".format(src_ip, dest_ip))
        return True

    def execute_kill_process(self, exec_time, pname, common_content=None):
        """
        This Method is Used to kill the process after given time

        :param exec_time: Execution Time.
        :param pname: name of the process tobe killed.
        :param common_content: obejct to CommonContentLib.
        :raise content_exceptions.TestFail: If there is any data loss at Server Side.
        """
        self._log.info("Triggering the killing of process {} after {} sec".format(pname, exec_time))
        if common_content is None:
            common_content = CommonContentLib(self._log, self.os, self._cfg_opt)
        time.sleep(exec_time + 10)
        common_content.execute_sut_cmd_no_exception(
            "pkill {}".format(pname),
            "pkill {}".format(pname),
            self._command_timeout,
            ignore_result="ignore")
        self._log.info("Killed the process {} after {} sec".format(pname, exec_time))

    def execute_iperf_client(self, exec_time, port, iperf_server_ip, common_content = None):
        """
        This Method is Used to Set as Iperf Client and verify whether there is any data loss at server side..

        :param exec_time: Iperf Client Execution Time.
        :param port: port of iperf server.
        :param iperf_server_ip: ip of the SUT/VM iperf server.
        :param common_content: obejct to CommonContentLib.
        :raise content_exceptions.TestFail: If there is any data loss at Server Side.
        """
        self._log.info("Set as Iperf Client")

        if common_content is None:
            common_content = CommonContentLib(self._log, self.os, self._cfg_opt)
        self.vm_ip = self.get_ip(common_content)
        exec_time_min = 30
        if exec_time_min < exec_time:
            exec_time_min = exec_time
        cmd_output = common_content.execute_sut_cmd(self.cmd_for_iperf_client_with_port.format(iperf_server_ip, port, exec_time_min),
                                                    self.cmd_for_iperf_client_with_port.format(iperf_server_ip, port, exec_time_min),
                                                             exec_time_min+self._command_timeout)
        self._log.debug("Sut is Successfully Set as Iperf Client and Iperf Response from Server is : {}".format(
            cmd_output))
        if re.search(self.REGEX_FOR_DATA_LOSS, cmd_output):
            raise content_exceptions.TestFail("Data Loss is Observed at Client Side")
        self._log.info("There is No Data Loss at Client Side")

    def execute_iperf_client_esxi_vm(self, iperf_server_ip, port, exec_time, common_content_obj=None):
        """
        This Method is Used to Set as Iperf Client and verify whether there is any data loss at server side..

        :param exec_time: Iperf Client Execution Time.
        :param port: port of iperf server.
        :param iperf_server_ip: ip of the SUT/VM iperf server.
        :param common_content: obejct to CommonContentLib.
        :raise content_exceptions.TestFail: If there is any data loss at Server Side.
        """
        self._log.info("Set as Iperf Client")
        if common_content_obj is None:
            common_content_obj = CommonContentLib(self._log, self.os, self._cfg_opt)
        cmd = "nmcli device status"
        self.vm_ip = common_content_obj.execute_sut_cmd(cmd, "Get the IP of VM", self._command_timeout)
        exec_time_min = 30
        if exec_time_min < exec_time:
            exec_time_min = exec_time
        cmd_output = common_content_obj.execute_sut_cmd(self.cmd_for_iperf_client_with_port_esxi.format(iperf_server_ip, port, exec_time_min),
                                                        self.cmd_for_iperf_client_with_port_esxi.format(iperf_server_ip, port, exec_time_min),
                                                                exec_time_min)
        if re.search(self.REGEX_FOR_DATA_LOSS, cmd_output):
            raise content_exceptions.TestFail("Data Loss is Observed at Client Side")
        self._log.info("There is No Data Loss at Client Side")
        self._log.debug(
            "Sut is Successfully Set as Iperf Client and Iperf Response from Server is : {}".format(cmd_output))


    def execute_sut_as_iperf_server(self, exec_time, port=None):
        """
        This Method is Used to Set Sut as Iperf Server and verify whether there is any data loss at server side..

        :param exec_time: Iperf Server Execution Time.
        :raise content_exceptions.TestFail: If there is any data loss at Server Side.
        """
        self._log.info("Set SUT as Iperf Server")
        cmd_output = ""
        self.vm_ip = self.get_ip(self._common_content_lib)
        sut_common_content_lib = self._common_content_lib #CommonContentLib(self._log, self.os, self._cfg_opts)
        exec_time_min = 30
        if exec_time_min < exec_time:
            exec_time_min = exec_time

        kill_thread = threading.Thread(target=self.execute_kill_process,
                                       args=(exec_time_min + 10, "iperf", sut_common_content_lib))
        kill_thread.start()
        try:
            if port is None:
                cmd_output = sut_common_content_lib.execute_sut_cmd(self.cmd_for_iperf_server,
                                                                    self.cmd_for_iperf_server,
                                                                     exec_time_min+self._command_timeout)
            else:
                cmd_output = sut_common_content_lib.execute_sut_cmd(self.cmd_for_iperf_server_with_port.format(port),
                                                                    self.cmd_for_iperf_server_with_port.format(port),
                                                                    exec_time_min + self._command_timeout)
        except Exception as ex:
            self._log.debug("Sut is Successfully Set and executed as Iperf as Server")

        self._log.debug("Sut is Successfully Set and executed as Iperf as Server")
        if re.search(self.REGEX_FOR_DATA_LOSS, cmd_output):
            raise content_exceptions.TestFail("Data Loss is Observed at Server Side")
        self._log.info("There is No Data Loss at Server Side")

    def execute_esxi_sut_as_iperf_server(self, exec_time, port=None):
        """
        This Method is Used to Set Sut as Iperf Server and verify whether there is any data loss at server side..

        :param exec_time: Iperf Server Execution Time.
        :raise content_exceptions.TestFail: If there is any data loss at Server Side.
        """
        self._log.info("Set SUT as Iperf Server")
        cmd_output = ""
        cmd1 = "esxcli network ip interface ipv4 get"
        self.vm_ip = self._common_content_lib.execute_sut_cmd(cmd1, "get network interface esxi", self._command_timeout)
        sut_common_content_lib = self._common_content_lib  # CommonContentLib(self._log, self.os, self._cfg_opts)
        exec_time_min = 30
        if exec_time_min < exec_time:
            exec_time_min = exec_time

        kill_thread = threading.Thread(target=self.execute_kill_process,
                                       args=(exec_time_min + 100, "iperf3", sut_common_content_lib))
        kill_thread.start()

        try:
            if port is None:
                cmd_output = sut_common_content_lib.execute_sut_cmd(self.cmd_for_iperf_server_esxi,
                                                                    self.cmd_for_iperf_server_esxi,
                                                                    exec_time_min + self._command_timeout,
                                                                    "/vmfs/volumes/datastore1")
            else:
                cmd_output = sut_common_content_lib.execute_sut_cmd(
                    self.cmd_for_iperf_server_with_port_esxi.format(port),
                    self.cmd_for_iperf_server_with_port_esxi.format(port),
                    exec_time_min + self._command_timeout, "/vmfs/volumes/datastore1")
                self._log.debug("IPERF file execution output {}".format(cmd_output))
        except Exception as ex:
            self._log.debug("Sut is Successfully Set and executed as Iperf as Server")

        self._log.debug("Sut is Successfully Set and executed as Iperf as Server")
        if re.search(self.REGEX_FOR_DATA_LOSS, cmd_output):
            raise content_exceptions.TestFail("Data Loss is Observed at Server Side")
        self._log.info("There is No Data Loss at Server Side")

    def execute_vm_as_iperf_client(self, vm_obj, common_content_vm_obj, exec_time):
        """
        This Method is Used to Execute VM as a Iperf Client and Verify Whether there is any Data Loss at Client Side.

        :param exec_time: Iperf Execution Time.
        :raise content_exceptions.TestFail: If there is any Data Loss at Client Side.
        """
        self.sut_ip = self._common_content_lib.execute_sut_cmd(self.IP_ADDRESS_SUT, self.IP_ADDRESS_SUT,
                                                         self._command_timeout, self.ROOT_PATH).strip()
        port = 5201
        self._log.info("Set VM as Iperf Client")
        exec_time_min = 30
        if exec_time_min < exec_time:
            exec_time_min = exec_time
        cmd_output = common_content_vm_obj.execute_sut_cmd_no_exception(
            self.cmd_for_iperf_client.format(self.sut_ip, exec_time_min),
            self.cmd_for_iperf_client.format(self.sut_ip, exec_time_min),
            exec_time_min + self._command_timeout, ignore_result="ignore")
        self._log.debug("VM is Successfully Set as Iperf Client and Iperf Response from Client is : {}".format(
            cmd_output))
        if re.search(self.REGEX_FOR_DATA_LOSS, cmd_output):
            raise content_exceptions.TestFail("Data Loss is Observed at VM Client Side")
        self._log.info("There is No Data Loss at VM Client Side")

    def execute_vm_as_iperf_server(self, vm_obj, common_content_vm_obj, exec_time, port=None):
        """
        This Method is Used to Execute VM as a Iperf Client and Verify Whether there is any Data Loss at Client Side.

        :param exec_time: Iperf Execution Time.
        :raise content_exceptions.TestFail: If there is any Data Loss at Client Side.
        """
        self._log.info("Set VM as Iperf Server")
        cmd_output = ""
        kill_thread = threading.Thread(target=self.execute_kill_process,
                                         args=(exec_time+60+10, "iperf", common_content_vm_obj))
        kill_thread.start()
        try:
            if port is None:
                cmd_output = common_content_vm_obj.execute_sut_cmd(self.cmd_for_iperf_server,
                                                                                 self.cmd_for_iperf_server,
                                                                                 self.exec_time + 60)
            else:
                cmd_output = common_content_vm_obj.execute_sut_cmd(self.cmd_for_iperf_server_with_port.format(port),
                                                                                 self.cmd_for_iperf_server_with_port.format(port),
                                                                                 self.exec_time + 60)

        except Exception as ex:
            self._log.debug("Sut is Successfully Set and executed as Iperf as Server")

        self._log.debug("Sut is Successfully Set and executed as Iperf as Server")
        if re.search(self.REGEX_FOR_DATA_LOSS, cmd_output):
            raise content_exceptions.TestFail("Data Loss is Observed at VM Server Side")
        self._log.info("There is No Data Loss at VM Server Side")

    def execute_sut_as_iperf_client(self, vm_name, exec_time):
        """
        This Method is Used to Set Sut as Iperf Client and verify whether there is any data loss at server side..

        :param exec_time: Iperf Client Execution Time.
        :raise content_exceptions.TestFail: If there is any data loss at Server Side.
        """
        self.vm_ip = self._vm_provider.get_vm_ip(vm_name)
        print("vm ip: - {}-debug".format(self.vm_ip))
        sut_common_content_lib = CommonContentLib(self._log, self.os, self._cfg)
        port = 5201
        self._log.info("Set SUT as Iperf Client")
        exec_time_min = 30
        if exec_time_min < exec_time:
            exec_time_min = exec_time
        cmd_output = sut_common_content_lib.execute_sut_cmd_no_exception(
            self.cmd_for_iperf_client.format(self.vm_ip,exec_time_min),
            self.cmd_for_iperf_client.format(self.vm_ip, exec_time_min),
            exec_time_min + self._command_timeout, ignore_result="ignore")
        self._log.debug("SUT is Successfully Set as Iperf Client and Iperf Response from server is : {}".format(
            cmd_output))
        if re.search(self.REGEX_FOR_DATA_LOSS, cmd_output):
            raise content_exceptions.TestFail("Data Loss is Observed at SUT Client Side")
        self._log.info("There is No Data Loss at SUT Client Side")

    def stop_iperf(self, common_content=None):
        if common_content is None:
            common_content = CommonContentLib(self._log, self.os, self._cfg_opt)

        cmd_output = common_content.execute_sut_cmd_no_exception("pkill iperf3", "pkill iperf3",
                                                    self._command_timeout, ignore_result="ignore")
        self._log.debug("Successfully stopped Iperf : {}".format(cmd_output))

    def fio_execute_thread(self, ut_cmd, cmd_str, execute_timeout, common_content_obj=None):
        """

        Function to execute fio test
        :return: None
        """
        if common_content_obj is None:
            common_content_obj = self._common_content_lib
        self._log.info(" Starting fio stress test")
        fio_cmd_output = common_content_obj.execute_sut_cmd(ut_cmd, cmd_str,
                                                                  self._command_timeout)
        time.sleep((execute_timeout * 60) + TimeConstants.FIVE_MIN_IN_SEC)
        self._log.info("Fio tool command out put : {}".format(fio_cmd_output.strip()))
        reg_output = re.findall(self.REGEX_TO_VALIDATE_FIO_OUTPUT, fio_cmd_output.strip())
        if len(reg_output) == 0:
            raise content_exceptions.TestFail("Un-Expected Error Captured in Fio Output Log")
        self._log.info("No Error Found in Log as Expected")


    def get_network_adapter_interfaces(self, assign_static_ip=False):
        """
        This Method is Used to Assign Static IP's to Network Adapter Interfaces and return dictionary of Interfaces
        and Ip Address as Keys and Values.

        :assign_static_ip: True if need to assign static ip else False
        :return: network_interface_dict
        """
        network_interface_list = self.get_network_interfaces()
        for index in range(len(network_interface_list)):
            if network_interface_list[index] in self.network_interface_name:
                self.network_interface_name.remove(network_interface_list[index])

        network_interface_dict = {}
        if assign_static_ip:
            for index in range(len(self.network_interface_name)):
                self._log.info("Assigning Static Ip {} to Interface {}".format(self.STATIC_IP.format(index),
                                                                               self.network_interface_name[index]))
                self._common_content_lib. \
                    execute_sut_cmd(self.ASSIGN_STATIC_IP_COMMAND.format(self.network_interface_name[index],
                                                                         self.STATIC_IP.format(index)),
                                    "Assigning Static IP", self._command_timeout)
                network_interface_dict[self.network_interface_name[index]] = self.STATIC_IP.format(index)
            self._log.info("Static IP's are Assigned to Network Interfaces Successfully")
            self._log.debug("Network Interface Dict is {}".format(network_interface_dict))
            return network_interface_dict
        for interface in self.network_interface_name:
            self._log.info("Get IP Address assigned to Interface {}".format(interface))
            address = self._common_content_lib.execute_sut_cmd(self.SYSTEM_IP_COMMAND_DEVICE.format(interface),
                                                               self.SYSTEM_IP_COMMAND_DEVICE,
                                                               self._command_timeout)
            ip_string = re.compile(self.REGEX_CMD_FOR_ADAPTER_IP)
            ip_value = ip_string.search(address).group().strip().split(" ")[1] if ip_string.search(address) else ""
            self._log.debug("IP Address for Interface {} is : {}".format(interface, ip_value))
            network_interface_dict[interface] = ip_value
        self._log.info("NetworkInterface Dict is {}".format(network_interface_dict))
        return network_interface_dict

    def generate_virtual_functions(self, num_of_adapters):
        """
        This Method is Used to Generate Virtual Network Adapters and Verify.

        :num_of_adapters: Number of virtual Adapters to be Generated.
        :raise content_exceptions.TestError: When Virtual Network Adapters are not Generated as Expected.
        """
        self._log.info("Generating {} Virtual Network Adapters".format(num_of_adapters))
        network_interface = list(self.network_interface_dict.keys())[0]
        self._common_content_lib.execute_sut_cmd(self.GENERATING_VIRTUAL_ADAPTER_CMD.
                                                 format(num_of_adapters, network_interface),
                                                 "Command to Generate Virtual Adapters", self._command_timeout)

        cmd_output = self._common_content_lib.execute_sut_cmd(self.VERIFYING_VIRTUAL_ADAPTER_CMD,
                                                              "Verification of Generating Virtual Adapters",
                                                              self._command_timeout)
        if not len(re.findall(self.REGEX_CMD_FOR_VERIFYING_VIRTUAL_ADAPTER, cmd_output)) == num_of_adapters:
            raise content_exceptions.TestError("Virtual Network Adapters are Not Generated as Expected")
        for index in reversed(range(num_of_adapters)):
            self.virtual_network_interface_list.append(network_interface + "v{}".format(index))
        self._log.debug("{} Virtual Network Adapters are Generated".format(num_of_adapters))
        return self.virtual_network_interface_list

    def reset_virtual_network_adapters(self):
        """
        This Method is Used to Reset Virtual Network Adapters.

        :raise content_exceptions.TestError: When Unable to Reset Virtual Network Adapters to their Default
        """
        self._log.info("Resetting Virtual Network Adapters to there Default Value")
        network_interface = list(self.network_interface_dict.keys())[0]
        self._common_content_lib.execute_sut_cmd(self.RESET_VIRTUAL_ADAPTER_CMD.
                                                 format(network_interface),
                                                 "Command to Reset Virtual Adapters", self._command_timeout)
        cmd_output = self._common_content_lib.execute_sut_cmd(self.VERIFYING_VIRTUAL_ADAPTER_CMD,
                                                              "Verification of Virtual Adapters Count",
                                                              self._command_timeout)
        if re.findall(self.REGEX_CMD_FOR_VERIFYING_VIRTUAL_ADAPTER, cmd_output):
            raise content_exceptions.TestError("Virtual Network Adapters are Not Reset to there Default Value")
        self._log.info("Virtual Network Adapters are Reset to there Default Value")

    def enumerate_storage_device(self, bus_type, index_value, command_exec_obj):
        """
        This method is to get the Storage Device List

        :param bus_type: Name of the bus type e.g. nvme0 => nvme
        :param index_value : index number for bus e.g. nvme0 => 0 is index_value
        :param command_exec_obj: os object
        :return : device_list
        """
        device_list = []
        self._log.info("Getting All the Storage Devices")
        device_data = command_exec_obj.execute("lshw -c storage -businfo | grep '{}'"
                                        .format(bus_type.lower()+str(index_value)),
                                        self._command_timeout)
        self._log.debug("PCI Device Names:\n{}".format(device_data))
        output_list = device_data.stdout.strip().split("\n")
        for output in output_list:
            dev = output.split(" ")[2]
            if '/' in dev:
                device_list.append(dev.split('/')[2])
            else:
                device_list.append(dev)
        self._log.info("Storage Disk list : {}".format(device_list))
        return device_list

    def get_bdf_values_of_storage_device(self, disk_id, command_exec_obj):
        """
        This method is to get the BDF values of PCIe device

        :param disk_id: storage device id e.g. scsi1, nvme0, nvme1 etc.
        :return: domain-bus-slot-function value
        """
        device_data = command_exec_obj.execute("lshw -c storage -businfo | grep '{}'"
                                        .format(disk_id.lower()),
                                        self._command_timeout)
        dbsf_value = re.findall(self._REGEX_TO_FETCH_PCIE_DBSF_VALUES, device_data.split("\n")[0])
        domain_value = int(dbsf_value[0].split(":")[0].strip(), 16)
        bus_value = int(dbsf_value[0].split(":")[1].strip(), 16)
        slot_value = int(dbsf_value[0].split(":")[2].split(".")[0].strip(), 16)
        function_value = int(dbsf_value[0].split(":")[2].split(".")[1].strip(), 16)
        return domain_value, bus_value, slot_value, function_value

    def get_bdf_values_of_device(self, device_name, index, os_obj):
        """
        This method is to get the BDF values of PCIe device

        :param device_id: device id e.g. dsa0 -> dsa.
        :param index: device index, e.g. dsa0 -> 0
        :return: domain-bus-slot-function value
        """
        device_data = os_obj.execute("ls -l | grep '{}{}'"
                                        .format(device_name.lower(), index),
                                        self._command_timeout)
        dbsf_value = re.findall(self._REGEX_TO_FETCH_PCIE_DBSF_VALUES, device_data.split("\n")[0])
        domain_value = int(dbsf_value[0].split(":")[0].strip(), 16)
        bus_value = int(dbsf_value[0].split(":")[1].strip(), 16)
        slot_value = int(dbsf_value[0].split(":")[2].split(".")[0].strip(), 16)
        function_value = int(dbsf_value[0].split(":")[2].split(".")[1].strip(), 16)
        return domain_value, bus_value, slot_value, function_value

    def get_bdf_values_of_pci_device(self, device_id, command_exec_obj):
        """
        This method is to get the BDF values of PCIe device

        :param device_id: storage device id e.g. scsi1, nvme0, nvme1 etc.
        :return: domain-bus-slot-function value
        """
        device_data = command_exec_obj.execute("lshw -businfo | grep '{}'"
                                        .format(device_id.lower()),
                                        self._command_timeout)
        dbsf_value = re.findall(self._REGEX_TO_FETCH_PCIE_DBSF_VALUES, device_data.split("\n")[0])
        domain_value = int(dbsf_value[0].split(":")[0].strip(), 16)
        bus_value = int(dbsf_value[0].split(":")[1].strip(), 16)
        slot_value = int(dbsf_value[0].split(":")[2].split(".")[0].strip(), 16)
        function_value = int(dbsf_value[0].split(":")[2].split(".")[1].strip(), 16)
        return domain_value, bus_value, slot_value, function_value

    def get_cpu_core_info(self):
        """
        This function is to get the CPU core information
        Returns : cores per socket
        """
        cpu_info_result = self._common_content_lib.execute_sut_cmd(self.CPU_INFO, self.CPU_INFO, self._command_timeout)
        self._log.debug("{} command result:{}".format(self.CPU_INFO, cpu_info_result))

        if not re.search(self.SOCKET, cpu_info_result):
            raise content_exceptions.TestFail("Failed to get socket info from Solar tool")

        socket = int(re.search(self.SOCKET, cpu_info_result).group(1))

        if not re.search(self.THREADS_CORE_SOCKET, cpu_info_result):
            raise content_exceptions.TestFail("Failed to get thread per core info from Solar tool")

        threads_per_core = int(re.search(self.THREADS_CORE_SOCKET, cpu_info_result).group(1))

        if not re.search(self.CORE_SOCKET, cpu_info_result):
            raise content_exceptions.TestFail("Failed to get core per socket info from Solar tool")
        core_socket = int(re.search(self.CORE_SOCKET, cpu_info_result).group(1))

        self._log.info("Core(s) per socket:{}".format(core_socket))
        self._log.info("Thread(s) per core:{}".format(threads_per_core))
        self._log.info("Socket(s):{}".format(socket))

        return (socket, core_socket, threads_per_core)

    def attach_pci_device_to_vm(self, pcie_device, vm_name):
         """
         This method is to attach the PCI devices to VM

         :param pcie_device: details of the PCIe device. ex: enp1s0 OR Ethernet controller E810-C OR nvme1, nvme0, ens5f0np0
         :param vm_name: name of the VM
         """
         # writing the value in the pci xml file to add the device to the VM
         self._log.info("Attaching the PCIe card to the VM {}".format(vm_name))
         # get attached bdf values
         domain_value, bus_value, slot_value, function_value = self.get_bdf_values_of_pci_device(pcie_device)
         with open(self.PCI_DEVICE_XML_FILE_NAME, "w+") as fp:
             fp.writelines(self.PCI_DEVICE_XML_FILE_DATA.format(domain_value, bus_value, slot_value, function_value))
         self._log.info("Coping the {} file to SUT".format(self.PCI_DEVICE_XML_FILE_NAME))
         self.os.copy_local_file_to_sut(self.PCI_DEVICE_XML_FILE_NAME, self.ROOT_PATH)
         self._log.info("Successfully copied the {} file to SUT".format(self.PCI_DEVICE_XML_FILE_NAME))
         try:
             self._common_content_lib.execute_sut_cmd("virsh detach-device {} /root/{}".format(vm_name,
                                                                                               self.PCI_DEVICE_XML_FILE_NAME),
                                                      "detaching the PCIe device to the VM", self._command_timeout)
         except:
             pass
         attach_result = self._common_content_lib.execute_sut_cmd("virsh attach-device {} /root/{} --config".format(vm_name,
                                                                                                          self.PCI_DEVICE_XML_FILE_NAME),
                                                                 "attaching the PCIe device to the VM", self._command_timeout)
         # below is required in case attach-device is called with --config but this reboot will remove
         # all dynamically loaded drivers usinf insmod/modprobe
         # If one doesn't want to use --config option which requires reboot of system to make the attached device
         # to be available in system, just remove/comment the below function as well "force_poweroff_and_start_vm_linux()"
         self.force_poweroff_and_start_vm_linux(vm_name)
         self._log.debug("attach result:\n{}".format(attach_result))
         self._log.info("Successfully attached the PCIe device to the VM {}".format(vm_name))

    def detach_pci_device_from_vm(self, pcie_device, vm_name):
        """
        This method is to detach the pci device from the VM

        :param pcie_device: details of the PCIe device. ex: 0000:6b:02.0 Ethernet controller: Intel Corporation Ethernet
                           Virtual Function 700 Series (rev 02)
        :param vm_name: name of the VM
        """
        # writing the value in the pci xml file to add the device to the VM

        self._log.info("Detaching the Pcie device from the {} VM".format(vm_name))
        domain_value, bus_value, slot_value, function_value = self.get_bdf_values_of_pci_device(pcie_device)
        with open(self.PCI_DEVICE_XML_FILE_NAME, "w+") as fp:
            fp.writelines(self.PCI_DEVICE_XML_FILE_DATA.format(domain_value, bus_value, slot_value, function_value))
        self._log.info("Copying the {} file to SUT".format(self.PCI_DEVICE_XML_FILE_NAME))
        self.os.copy_local_file_to_sut(self.PCI_DEVICE_XML_FILE_NAME, self.ROOT_PATH)
        detach_result = self._common_content_lib.execute_sut_cmd("virsh detach-device {} /root/{}".format(vm_name,
                                                                                                          self.PCI_DEVICE_XML_FILE_NAME),
                                                                 "detaching the Pcie device from the VM", self._command_timeout)
        self._log.debug("detach result:\n{}".format(detach_result))
        self._log.info("Successfully detached the Pcie device from the VM {}".format(vm_name))

    def set_disk_offline(self, disk_id, command_exec_obj):
        """
        This method is to set disk offline for Storage passthrough.

        :param disk_id: Storage Device id e.g. nvme0, nvme1.
        :param command_exec_obj: Object to execute commands. Ex : Sut object or Vm object
        :return: None
        """
        try:
            self._log.info("Set Disk: {} to offline state to enable device sharing".format(disk_id))
            domain_value, bus_value, slot_value, function_value = self.get_bdf_values_of_storage_device(disk_id, command_exec_obj)

            pci_device_name = 'pci_{:04}_{:02}_{:02}_{:01}'.format(domain_value, bus_value, slot_value, function_value)

            cmd_get_name = r"virsh nodedev-list | grep {}".format(pci_device_name)

            result = command_exec_obj.execute_sut_cmd(
                cmd_get_name, "get if device exist using virsh noddev-list",
                self._command_timeout)

            cmd = r"virsh nodedev-detach {}".format(pci_device_name)

            if result is not None:
                command_exec_obj.execute_sut_cmd(
                    cmd, "Set Disk Offline",
                    self._command_timeout)

            get_device_status = command_exec_obj.execute_sut_cmd(
                cmd_get_name, "Get Disk Status",
                self._command_timeout)
            if get_device_status is None:
                self._log.info("Set Disk offline successful on DiskNumber:{}".format(disk_id))
                self._log.debug("{} command stdout\n{}".format(cmd_get_name, get_device_status))
            else:
                return RuntimeError("Failed to set Disk:{} Offline.".format(disk_id))

        except Exception as ex:
            self._log.error("Error while setting Disk:{} to offline State".format(ex))
            raise ex

    def set_disk_online(self, disk_id, command_exec_obj):
        """
        This method is to set disk offline for Storage passthrough.

        :param disk_id: Storage Device id e.g. nvme0, nvme1.
        :param command_exec_obj: Object to execute commands. Ex : Sut object or Vm object
        :return: None
        """
        try:
            self._log.info("Set Disk: {} to online to access from file explorer".format(disk_id))
            domain_value, bus_value, slot_value, function_value = self.get_bdf_values_of_storage_device(disk_id, command_exec_obj)

            pci_device_name = 'pci_{:04}_{:02}_{:02}_{:01}'.format(domain_value, bus_value, slot_value, function_value)

            cmd_get_name = r"virsh nodedev-list | grep {}".format(pci_device_name)

            result = command_exec_obj.execute_sut_cmd(
                cmd_get_name, "get if device exist using virsh noddev-list",
                self._command_timeout)

            cmd = r"virsh nodedev-reattach {}".format(pci_device_name)

            if result is None:
                command_exec_obj.execute_sut_cmd(
                    cmd, "Set Disk Online",
                    self._command_timeout)

            get_device_status = command_exec_obj.execute_sut_cmd(
                cmd_get_name, "Get Disk Status",
                self._command_timeout)
            if get_device_status is not None:
                self._log.info("Set Disk online successful on DiskNumber:{}".format(disk_id))
                self._log.debug("{} command stdout\n{}".format(cmd_get_name, get_device_status))
            else:
                return RuntimeError("Failed to set Disk:{} Online.".format(disk_id))

        except Exception as ex:
            self._log.error("Error while setting Disk:{} to Online State".format(ex))
            raise ex

    def copy_file_to_sut_l(self, sut_folder_name, host_file_path, if_zipped=None):
        """
        copy zip file to Linux SUT and unzip

        :param : sut_folder_name : name of the folder in SUT
        :param : host_zip_file_path : name of the zip file in Host
        :return: The extracted folder path in SUT
        """
        file_name = os.path.basename(host_file_path)
        if not os.path.isfile(host_file_path):
            return RuntimeError("{} does not found".format(host_file_path))

        self.execute_sut_cmd("rm -rf {}".format(sut_folder_name), "To delete a "
                                                                  "folder",
                             self._command_timeout, self.ROOT_PATH)

        self.execute_sut_cmd("mkdir -p {}".format(sut_folder_name), "To Create a "
                                                                    "folder",
                             self._command_timeout, self.ROOT_PATH)

        sut_folder_path = Path(os.path.join(self.ROOT_PATH, sut_folder_name)).as_posix()

        # copying file to Linux SUT in root from host
        self._os.copy_local_file_to_sut(host_file_path, sut_folder_path)

        if if_zipped is None:
            return
        else:
            return self.extract_compressed_file_l(sut_folder_path, file_name, sut_folder_name)

    def extract_compressed_file_l(self, sut_folder_path, zip_file, folder_name):
        """
        This function Extract the compressed file.

        :param : sut_folder_path : sut folder path
        :param : folder_name : name of the folder in SUT
        :param : zip_file : name of the zip file.

        :return: The extracted folder path in SUT.
        """
        self._log.info("extracts the compressed file")
        expected_files_extn = (".tar.gz", ".tar.xz", ".tgz", ".txz", ".tar")
        unzip_command = "unzip {}".format(zip_file)
        if zip_file.endswith(expected_files_extn):
            unzip_command = "tar -xvf {}".format(zip_file)
        self.execute_sut_cmd(unzip_command, "unzip the folder",
                             self._command_timeout, sut_folder_path)

        # self.execute_sut_cmd("unzip {}".format(zip_file), "unzip the folder", self._command_timeout,
        #                    sut_folder_path)

        tool_path_sut = Path(os.path.join(self.ROOT_PATH, folder_name)).as_posix()

        # copying file to Linux SUT in root from host

        self._log.debug("The file '{}' has been unzipped successfully "
                        "..".format(zip_file))
        # Remove the zip file after decompressing
        command_extract_tar_file = self.REMOVE_FILE.format(tool_path_sut + "/" + zip_file)
        self.execute_sut_cmd(command_extract_tar_file, "remove zip file", self._command_timeout)
        self._log.debug("The zip file after decompressing is removed "
                        "successfully")
        self._os.execute("chmod -R 777 %s" % tool_path_sut,
                         self._command_timeout)

        return tool_path_sut


    def get_dsa_uuid(self):
        """
        This function will find the uuid for dsa device
        """
        try:
            cmd_list_mdev = "ls /sys/bus/mdev/devices/"
            dsa_device_str = "dsa"
            dsa_device_type_cmd = "cat /sys/bus/mdev/devices/{}/mdev_type/name"
            dsa_uuid_list = []
            self._log.info("Get the mdev device id")
            uuid_device = self._common_content_lib.execute_sut_cmd(sut_cmd=cmd_list_mdev, cmd_str=cmd_list_mdev,
                                                                        execute_timeout=self._command_timeout,
                                                                        cmd_path=self.ROOT_PATH)
            self._log.info("Available mdev uuid types \n {}".format(uuid_device))
            for uuid in uuid_device.split('\n')[:-1]:
                # get the maximum no of VFs supported on the SUT
                dsa_mdev_device = self._common_content_lib.execute_sut_cmd("cat /sys/bus/mdev/devices/{}/mdev_type/name"
                                                                     .format(uuid),
                                                                     "get dsa mdev device", self._command_timeout)
                self._log.debug("{} command stdout\n{}".format(dsa_device_type_cmd, dsa_mdev_device))
                if dsa_device_str in dsa_mdev_device:
                    self._log.info("Dsa device with UUID:{} found".format(uuid))
                    dsa_uuid_list.append(uuid)
                self._log.info("UUID:{} not a type of dsa device".format(uuid))

            return dsa_uuid_list

        except Exception as ex:
            log_error = "error in getting mdev id"
            self._log.error(log_error)
            RuntimeError(ex)

    def get_iax_uuid(self):
        """
        This function will find the uuid for dsa device
        """
        try:
            cmd_list_mdev = "ls /sys/bus/mdev/devices/"
            iax_device_str = "iax"
            iax_device_type_cmd = "cat /sys/bus/mdev/devices/{}/mdev_type/name"
            iax_uuid_list = []
            self._log.info("Get the mdev device id")
            uuid_device = self._common_content_lib.execute_sut_cmd(sut_cmd=cmd_list_mdev, cmd_str=cmd_list_mdev,
                                                                   execute_timeout=self._command_timeout,
                                                                   cmd_path=self.ROOT_PATH)
            self._log.info("Available mdev uuid types \n {}".format(uuid_device))
            for uuid in uuid_device.split('\n')[:-1]:
                # get the maximum no of VFs supported on the SUT
                iax_mdev_device = self._common_content_lib.execute_sut_cmd("cat /sys/bus/mdev/devices/{}/mdev_type/name"
                                                                     .format(uuid),
                                                                     "get iax mdev device", self._command_timeout)
                self._log.debug("{} command stdout\n{}".format(iax_device_type_cmd, iax_mdev_device))
                if iax_device_str in iax_mdev_device:
                    self._log.info("IAX device with UUID:{} found".format(uuid))
                    iax_uuid_list.append(uuid)
                self._log.info("UUID:{} not a type of IAX device".format(uuid))

            return iax_uuid_list

        except Exception as ex:
            log_error = "error in getting mdev id"
            self._log.error(log_error)
            RuntimeError(ex)

    def attach_pci_device_using_dbdf_to_vm(self, vm_name, domain_value, bus_value, device_value, function_value):
        """
        Attaches the PCI device to VM
        :param : domain_value, bus_value, device_value, function_value : Values as strings '0000','6d','00','d'
        """
        with open(self.PCI_DEVICE_XML_FILE_NAME, "w+") as fp:
            fp.writelines(self.PCI_DEVICE_XML_FILE_HEX_DATA.format(domain_value, bus_value, device_value, function_value))
        self._log.info("Copying the {} file to SUT".format(self.PCI_DEVICE_XML_FILE_NAME))
        self.os.copy_local_file_to_sut(self.PCI_DEVICE_XML_FILE_NAME, self.ROOT_PATH)
        try:
            self._common_content_lib.execute_sut_cmd("virsh detach-device {} /root/{}".format(vm_name,
                                                                                              self.PCI_DEVICE_XML_FILE_NAME),
                                                     "detaching the Pcie device from the VM",
                                                     self._command_timeout)
        except:
            pass
        attach_result = self._common_content_lib.execute_sut_cmd("virsh attach-device {} /root/{} --config".format(vm_name,
                                                                                                          self.PCI_DEVICE_XML_FILE_NAME),
                                                                 "attaching the Pcie device from the VM",
                                                                 self._command_timeout)
        # below is required in case attach-device is called with --config but this reboot will remove
        # all dynamically loaded drivers usinf insmod/modprobe
        # If one doesn't want to use --config option which requires reboot of system to make the attached device
        # to be available in system, just remove/comment the below function as well "force_poweroff_and_start_vm_linux()"
        self.force_poweroff_and_start_vm_linux(vm_name)
        self._log.debug("attach result:\n{}".format(attach_result))
        self._log.info("Successfully attached the Pcie device from the VM {}".format(vm_name))

    def detach_pci_device_using_dbdf_from_vm(self, vm_name, domain_value, bus_value, device_value, function_value):
        """
        Detaches the PCI device to VM
        :param : domain_value, bus_value, device_value, function_value : Values as strings '0000','6d','00','d'
        """
        with open(self.PCI_DEVICE_XML_FILE_NAME, "w+") as fp:
            fp.writelines(self.PCI_DEVICE_XML_FILE_HEX_DATA.format(domain_value, bus_value, device_value, function_value))
        self._log.info("Copying the {} file to SUT".format(self.PCI_DEVICE_XML_FILE_NAME))
        self.os.copy_local_file_to_sut(self.PCI_DEVICE_XML_FILE_NAME, self.ROOT_PATH)
        detach_result = self._common_content_lib.execute_sut_cmd("virsh detach-device {} /root/{}".format(vm_name,
                                                                                                          self.PCI_DEVICE_XML_FILE_NAME),
                                                                 "detaching the Pcie device from the VM",
                                                                 self._command_timeout)
        self._log.debug("detach result:\n{}".format(detach_result))
        self._log.info("Successfully detached the Pcie device from the VM {}".format(vm_name))

    def attach_vfiopci_device_using_dbdf_to_vm(self, vm_name, domain_value, bus_value, device_value, function_value):
        """
        Attaches the PCI device to VM
        :param : domain_value, bus_value, device_value, function_value : Values as strings '0000','6d','00','d'
        """
        with open(self.PCI_DEVICE_XML_FILE_NAME, "w+") as fp:
            fp.writelines(self.PCI_VFIO_DEVICE_XML_FILE_HEX_DATA.format(domain_value, bus_value, device_value, function_value))
        self._log.info("Copying the {} file to SUT".format(self.PCI_DEVICE_XML_FILE_NAME))
        self.os.copy_local_file_to_sut(self.PCI_DEVICE_XML_FILE_NAME, self.ROOT_PATH)
        try:
            self._common_content_lib.execute_sut_cmd("virsh detach-device {} /root/{}".format(vm_name,
                                                                                              self.PCI_DEVICE_XML_FILE_NAME),
                                                     "detaching the Pcie device from the VM",
                                                     self._command_timeout)
        except:
            pass
        attach_result = self._common_content_lib.execute_sut_cmd("virsh attach-device {} /root/{} --config".format(vm_name,
                                                                                                          self.PCI_DEVICE_XML_FILE_NAME),
                                                                 "attaching the Pcie device from the VM",
                                                                 self._command_timeout)
        # below is required in case attach-device is called with --config but this reboot will remove
        # all dynamically loaded drivers usinf insmod/modprobe
        # If one doesn't want to use --config option which requires reboot of system to make the attached device
        # to be available in system, just remove/comment the below function as well "force_poweroff_and_start_vm_linux()"
        self.force_poweroff_and_start_vm_linux(vm_name)
        self._log.debug("attach result:\n{}".format(attach_result))
        self._log.info("Successfully attached the Pcie device from the VM {}".format(vm_name))

    def detach_vfiopci_device_using_dbdf_from_vm(self, vm_name, domain_value, bus_value, device_value, function_value):
        """
        Detaches the PCI device to VM
        :param : domain_value, bus_value, device_value, function_value : Values as strings '0000','6d','00','d'
        """
        with open(self.PCI_DEVICE_XML_FILE_NAME, "w+") as fp:
            fp.writelines(self.PCI_VFIO_DEVICE_XML_FILE_HEX_DATA.format(domain_value, bus_value, device_value, function_value))
        self._log.info("Copying the {} file to SUT".format(self.PCI_DEVICE_XML_FILE_NAME))
        self.os.copy_local_file_to_sut(self.PCI_DEVICE_XML_FILE_NAME, self.ROOT_PATH)
        detach_result = self._common_content_lib.execute_sut_cmd("virsh detach-device {} /root/{}".format(vm_name,
                                                                                                          self.PCI_DEVICE_XML_FILE_NAME),
                                                                 "detaching the Pcie device from the VM",
                                                                 self._command_timeout)
        self._log.debug("detach result:\n{}".format(detach_result))
        self._log.info("Successfully detached the Pcie device from the VM {}".format(vm_name))

    def run_dsa_workload_on_host(self, spr_dir_path):
        """
        This function runs workload on HOST.
        :return: None
        """
        cmd_dma = "./Guest_Mdev_Randomize_DSA_Conf.sh -i 1000 -j 10"
        cmd_output = self._common_content_lib.execute_sut_cmd(sut_cmd=cmd_dma, cmd_str=cmd_dma,
                                                              execute_timeout=self._command_timeout,
                                                              cmd_path=spr_dir_path)
        self._log.info("Running DSA workload on host and output is {}".format(cmd_output))
        cmd_check_error = "journalctl --dmesg | grep 'error'"
        self._log.info("Checking errors if any after running the workload")
        error_output = self._common_content_lib.execute_sut_cmd(sut_cmd=cmd_check_error, cmd_str=cmd_check_error,
                                                                execute_timeout=self._command_timeout,
                                                                cmd_path=spr_dir_path)
        if len(error_output.stdout) == 0:
            self._log.info("No errors found")
        else:
            raise RuntimeError("Errors found after running workload")

    def execute_opcode_test(self, spr_file_path, common_content_lib_vm, vm_obj, device='dsa'):
        """
        This function to test memory opcode

        :param : spr_file_path : Scripts file path
        :param : common_content_lib_vm : Common content object
        :param : vm_os_obj : VM OS object
        :param : device : device type
        :return: None
        """
        self._log.info("Running Execute Opcode test in guest VM pass through test")
        if device =='dsa':
            cmd = "./Guest_Passthrough_Randomize_DSA_Conf.sh -cu"
            cmd_dma = "./Guest_Passthrough_Randomize_DSA_Conf.sh -o 0x3"
        elif device =='iax':
            cmd = "./Guest_Passthrough_Randomize_IAX_Conf.sh -cu"
            cmd_dma = "./Guest_Passthrough_Randomize_IAX_Conf.sh -o 0x3"
        else:
            raise content_exceptions.TestFail("Not implemented for the device {}".format(device))
        cmd_output = common_content_lib_vm.execute_sut_cmd(sut_cmd=cmd, cmd_str=cmd,
                                                           execute_timeout=self._command_timeout,
                                                           cmd_path=spr_file_path)
        self._log.info("Configuring work queues {}".format(cmd_output))
        cmd_output = common_content_lib_vm.execute_sut_cmd(sut_cmd=cmd_dma, cmd_str=cmd_dma,
                                                           execute_timeout=self._command_timeout,
                                                           cmd_path=spr_file_path)
        self._log.info("Running DSA workload on vm and output is {}".format(cmd_output))
        cmd_check_error = "journalctl --dmesg | grep error"
        cmd_opt = vm_obj.execute(cmd_check_error, self._command_timeout)
        if len(cmd_opt.stdout) == 0:
            self._log.info("No errors found")
        else:
            raise RuntimeError("Errors found after running workload")

    def execute_opcode_test_for_dsa(self, spr_file_path, vm_obj, device='dsa'):
        """
        This function to test memory opcode

        :param : spr_file_path : Scripts file path
        :param : common_content_lib_vm : Common content object
        :param : vm_os_obj : VM OS object
        :param : device : device type
        :return: None
        """
        self._log.info("Running Execute Opcode test in guest VM pass through test")
        if device =='dsa':
            cmd = "cd {} && ./Guest_Mdev_Randomize_DSA_Conf.sh -cu".format(spr_file_path)
            cmd_dma = "./Guest_Mdev_Randomize_DSA_Conf.sh -o 0x3".format(spr_file_path)
        else:
            raise content_exceptions.TestFail("Not implemented for the device {}".format(device))
        cmd_output = vm_obj.execute(cmd,self._command_timeout)
        self._log.info("Configuring work queues {}".format(cmd_output))
        cmd_output = vm_obj.execute(cmd_dma, self._command_timeout)
        self._log.info("Running DSA workload on vm and output is {}".format(cmd_output))
        cmd_check_error = "journalctl --dmesg | grep error"
        cmd_opt = vm_obj.execute(cmd_check_error, self._command_timeout)
        if len(cmd_opt.stdout) == 0:
            self._log.info("No errors found")
        else:
            raise RuntimeError("Errors found after running workload")

    def execute_dma_test_vm(self, spr_file_path, vm_obj, device = 'dsa'):
        """
        This function runs workload on VM.

        :param : spr_file_path : Scripts file path
        :param : common_content_lib_vm : Common content object
        :param : vm_os_obj : VM OS object
        :param : device type
        :return: None
        """
        if device =='dsa':
            self._log.info("Running Guest_Passthrough_Randomize_DSA_Conf test")
            cmd = "cd {} && ./Guest_Passthrough_Randomize_DSA_Conf.sh -k".format(spr_file_path)
            cmd_dma = "cd {} && ./Guest_Passthrough_Randomize_DSA_Conf.sh -i 100 -j 2".format(spr_file_path)
        elif device =='iax':
            self._log.info("Running Guest_Passthrough_Randomize_IAX_Conf test")
            cmd = "cd {} && ./Guest_Passthrough_Randomize_IAX_Conf.sh -k".format(spr_file_path)
            cmd_dma = "cd {} && ./Guest_Passthrough_Randomize_IAX_Conf.sh -i 100 -j 2".format(spr_file_path)
        else:
            raise content_exceptions.TestFail("Not implemented for the device {}".format(device))

        cmd_output = vm_obj.execute(cmd, self._command_timeout)
        if cmd_output.cmd_failed():
            raise content_exceptions.TestFail("Work queues not configured.")

        cmd_output = vm_obj.execute(cmd_dma, self._command_timeout)
        if cmd_output.cmd_failed():
            raise content_exceptions.TestFail("DSA workload is not running on vm.")

        cmd_check_error = "journalctl --dmesg | grep error"
        cmd_opt = vm_obj.execute(cmd_check_error, self._command_timeout)
        if len(cmd_opt.stdout) == 0:
            self._log.info("No errors found")
        else:
            raise RuntimeError("Errors found after running workload")

    def execute_dma_test(self, spr_file_path, common_content_lib_vm, vm_obj, device = 'dsa'):
        """
        This function runs workload on VM.

        :param : spr_file_path : Scripts file path
        :param : common_content_lib_vm : Common content object
        :param : vm_os_obj : VM OS object
        :param : device type
        :return: None
        """
        if device =='dsa':
            self._log.info("Running Guest_Passthrough_Randomize_DSA_Conf test")
            cmd = "./Guest_Passthrough_Randomize_DSA_Conf.sh -k"
            cmd_dma = "./Guest_Passthrough_Randomize_DSA_Conf.sh -i 100 -j 2"
        elif device =='iax':
            self._log.info("Running Guest_Passthrough_Randomize_IAX_Conf test")
            cmd = "./Guest_Passthrough_Randomize_IAX_Conf.sh -k"
            cmd_dma = "./Guest_Passthrough_Randomize_IAX_Conf.sh -i 100 -j 2"
        else:
            raise content_exceptions.TestFail("Not implemented for the device {}".format(device))
        cmd_output = common_content_lib_vm.execute_sut_cmd(sut_cmd=cmd, cmd_str=cmd,
                                                           execute_timeout=self._command_timeout,
                                                           cmd_path=spr_file_path)
        self._log.info("Configuring workqueues {}".format(cmd_output))
        cmd_output = common_content_lib_vm.execute_sut_cmd(sut_cmd=cmd_dma, cmd_str=cmd_dma,
                                                           execute_timeout=self._command_timeout,
                                                           cmd_path=spr_file_path)
        self._log.info("Running DSA workload on vm and output is {}".format(cmd_output))
        cmd_check_error = "journalctl --dmesg | grep error"
        cmd_opt = vm_obj.execute(cmd_check_error, self._command_timeout)
        if len(cmd_opt.stdout) == 0:
            self._log.info("No errors found")
        else:
            raise RuntimeError("Errors found after running workload")

    def get_vf_device_dbdf_by_devid(self, devid, common_content_object=None):
        """
        This method is to get the info about the VF Device DBDF

        :return DBDF list: demaon, bus, device , function list
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib

        lspci_cmd = "lspci -D | grep {}".format(devid)

        lspci_ouput = common_content_object.execute_sut_cmd_no_exception(lspci_cmd,
                                                                    "run command:{}".format(lspci_cmd),
                                                                    self._command_timeout,
                                                                    self.ROOT_PATH,
                                                                    ignore_result="ignore")

        # """
        # output will be as below ===>
        # 0000:6a:01.0 System peripheral: Intel Corporation Device 0b25
        # 0000:6f:01.0 System peripheral: Intel Corporation Device 0b25
        # """
        # initialize an empty string
        dbdf_list = re.findall(self._REGEX_TO_FETCH_PCIE_DBSF_VALUES, lspci_ouput, re.MULTILINE)
        self._log.info("device list :\n{}".format(dbdf_list))
        return dbdf_list

    def load_vfio_driver(self, common_content_object=None):
        """
        This function will load vfio and vfio-pci driver
        [root@embargo QAT]# modprobe vfio
        [root@embargo QAT]# modprobe vfio-pci
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        command = "modprobe vfio;modprobe vfio-pci;"

        output = common_content_object.execute_sut_cmd_no_exception(command,
                                                                    "run command:{}".format(command),
                                                                    self._command_timeout,
                                                                    self.ROOT_PATH,
                                                                    ignore_result="ignore")
        output = output.strip()
        self._log.info("Result of the run {} command: {}".format(command, output))

    def host_vfio_accel_driver_unbind(self, dbsf_value, common_content_object=None):
        """
        This function will unbind the host vfio driver
        [root@embargo QAT]# echo 0000:f8:02.0 > /sys/bus/pci/devices/0000\:f8\:02.0/driver/unbind
        :param dbsf_value : Domain Bus Device Function of the VF Device e.g. 0000:AA:BB.C
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib

        domain_value = dbsf_value.split(":")[0].strip()
        bus_value = dbsf_value.split(":")[1].strip()
        slot_value = dbsf_value.split(":")[2].split(".")[0].strip()
        function_value = dbsf_value.split(":")[2].split(".")[1].strip()
        command = "echo {} > /sys/bus/pci/devices/{}\:{}\:{}.{}/driver/unbind".format(dbsf_value.strip(), domain_value,
                                                                                                  bus_value, slot_value,
                                                                                                  function_value)

        output = common_content_object.execute_sut_cmd_no_exception(command,
                                                                    "run command:{}".format(command),
                                                                    self._command_timeout,
                                                                    self.ROOT_PATH,
                                                                    ignore_result="ignore")
        output = output.strip()
        self._log.info("Result of the run {} command: {}".format(command, output))
        
    def guest_vfio_pci_gen4_bind(self, dbsf_value, common_content_object):
        """
        This function will bind the guest vfio-pci driver
        :param dbsf_value : Domain Bus Device Function of the VF Device e.g. 0000:AA:BB.C
        [root@embargo QAT]# echo 8086 4941 > /sys/bus/pci/drivers/vfio-pci/new_id
        [root@embargo QAT]# lspci -s f8:02.0 -k
        """
        command = "echo 8086 1593 > /sys/bus/pci/drivers/vfio-pci/new_id"
        lspci_cmd = "lspci -s {} -k".format(dbsf_value)
        output = common_content_object.execute_sut_cmd_no_exception(command,
                                                                    "run command:{}".format(command),
                                                                    self._command_timeout,
                                                                    self.ROOT_PATH,
                                                                    ignore_result="ignore")
        output = output.strip()
        self._log.info("Result of the run {} command: {}".format(command, output))

        lspci_cmd_output = common_content_object.execute_sut_cmd_no_exception(lspci_cmd,
                                                                    "run command:{}".format(lspci_cmd),
                                                                    self._command_timeout,
                                                                    self.ROOT_PATH,
                                                                    ignore_result="ignore")
        lspci_cmd_output = lspci_cmd_output.strip()
        self._log.info("Result of the run {} command: {}".format(lspci_cmd, lspci_cmd_output))


    def guest_vfio_pci_accel_driver_bind(self, dbsf_value, accel_type, common_content_object=None):
        """
        This function will bind the guest vfio-pci driver
        :param dbsf_value : Domain Bus Device Function of the VF Device e.g. 0000:AA:BB.C
        [root@embargo QAT]# echo 8086 4941 > /sys/bus/pci/drivers/vfio-pci/new_id
        [root@embargo QAT]# lspci -s f8:02.0 -k
        """
        if common_content_object is None:
            common_content_object = self._common_content_lib
        # domain_value_int = int(dbsf_value.split(":")[0], 16)
        # bus_value_int = int(dbsf_value.split(":")[1], 16)
        # slot_value_int = int(dbsf_value.split(":")[2].split(".")[0], 16)
        # function_value_int = int(dbsf_value.split(":")[2].split(".")[1], 16)
        # domain_value = dbsf_value.split(":")[0].strip()
        # bus_value = dbsf_value.split(":")[1].strip()
        # slot_value = dbsf_value.split(":")[2].split(".")[0].strip()
        # function_value = dbsf_value.split(":")[2].split(".")[1].strip()
        if accel_type == "dsa":
            command = "echo 8086 0b25 > /sys/bus/pci/drivers/vfio-pci/new_id"
        else:
            command = "echo 8086 4941 > /sys/bus/pci/drivers/vfio-pci/new_id"
        lspci_cmd = "lspci -s {} -k".format(dbsf_value)
        output = common_content_object.execute_sut_cmd_no_exception(command,
                                                                    "run command:{}".format(command),
                                                                    self._command_timeout,
                                                                    self.ROOT_PATH,
                                                                    ignore_result="ignore")
        output = output.strip()
        self._log.info("Result of the run {} command: {}".format(command, output))

        lspci_cmd_output = common_content_object.execute_sut_cmd_no_exception(lspci_cmd,
                                                                    "run command:{}".format(lspci_cmd),
                                                                    self._command_timeout,
                                                                    self.ROOT_PATH,
                                                                    ignore_result="ignore")
        lspci_cmd_output = lspci_cmd_output.strip()
        self._log.info("Result of the run {} command: {}".format(lspci_cmd, lspci_cmd_output))

    def install_mlc_on_linux_vm(self, vm_os_obj):
        """
        Linux environment mlc installer.
        1. Copy mlc tool tar file to Linux SUT.
        2. Decompress tar file under user home folder.

        :return: None
        """
        self._log.info("Copying mlc tar file to SUT under home folder...")
        if vm_os_obj.execute("./mlc --help", self._command_timeout).return_code == 0:
            self._log.info("MLC already installed.")
        else:
            # This matches the name used in src.lib.install_collateral
            install_collateral_vm = InstallCollateral(self._log, vm_os_obj, self._cfg_opts)
            common_content_lib_vm = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
            mlc_extract_path = install_collateral_vm.install_mlc()
            common_content_lib_vm.execute_sut_cmd("chmod +x mlc", "Assigning executable privledges ",
                                                  self._command_timeout, mlc_extract_path)
            return mlc_extract_path
        if vm_os_obj.execute("./mlc --help", self._command_timeout).return_code == 0:
            self._log.info("MLC has been installed")

        else:
            err_log = "MLC NOT installed successfully!"
            self._log.error(err_log)
            raise Exception(err_log)

    def execute_mlc_test_on_vm(self, vm_name, vm_os_obj, mlc_exec_path):
        """
        Executing the tool and generate the output file.

        :param: mlc_cmd_log_path: log file name
        :return: True on success
        """
        mlc_log_file = vm_name + "_mlc_result.log"
        result = vm_os_obj.execute(self.MLC_COMMAND_LINUX.format(self._mlc_runtime, mlc_log_file),
                                   self._mlc_runtime, cwd=mlc_exec_path)
        if result.cmd_failed():
            error_msg = "Not able to run the command: {}".format(self.MLC_COMMAND_LINUX.format(
                self._mlc_runtime, mlc_log_file))
            self._log.error(error_msg)
            raise RuntimeError(error_msg)
        self._log.info("Successfully ran MLC Tool on VM:{}".format(vm_name))

    def stop_mlc_stress_vm(self, vm_name, vm_os_obj):
        """
        Stop the mlc stress app

        :return:
        """
        self._log.info("Stopping MLC stress app  on VM:{}..".format(vm_name))
        kill_cmd = "pkill {}".format(self.MLC_STR)
        if vm_os_obj.execute("top | grep 'mlc'", self._command_timeout).return_code == 0:
            self._log.info("MLC is running on VM:{}.".format(vm_name))
            vm_os_obj.execute(kill_cmd, self._command_timeout)
            time.sleep(self.MLC_DELAY_TIME_SEC)
        else:
            self._log.info("MLC tool is not running on VM:{}".format(vm_name))

    def install_ptu_on_sut_linux(self, vm_os_obj):
        """
        Copy and install PTU to the Linux SUT

        :return:
        """

        if vm_os_obj.execute("./ptu -v", self._command_timeout).return_code == 1:
            self._log.info("PTU already installed.")
            return
        # This matches the name used in src.lib.install_collateral
        ptu_file_name = "unified_server_ptu.tar.gz"
        install_collateral = InstallCollateral(self._log, vm_os_obj, self._cfg)
        tool_host_path = install_collateral.download_tool_to_host(tool_name=ptu_file_name)
        vm_os_obj.copy_local_file_to_sut(tool_host_path, "/root/")

        vm_os_obj.execute("tar -xvf " + ptu_file_name, self._command_timeout)

        if vm_os_obj.execute("./ptu -h", self._command_timeout).return_code == 1:
            self._log.info("PTU has been installed")
        else:
            err_log = "PTU NOT installed successfully!"
            self._log.error(err_log)
            raise Exception(err_log)

    def ptu_execute_linux(self, vm_os_obj, test_type, workload, duration_sec):
        """
        Running PTU wokload on Linux SUT

        :vm_os_obj: Vm executable object
        :param test_type: Specify the test type. e.g. "ct" for CPU test
        :param workload: Specify the workload to run under each test type.
        :param duration_sec: Specify the duration in second to run ptu workload.
        """
        self.ptu_kill_linux(vm_os_obj)
        vm_os_obj.execute_async("./ptu -y -{} {} -t {} ".format(test_type, workload, duration_sec))

    def ptu_kill_linux(self, vm_os_obj):
        """
        Kill PTU process on Linux SUT
        """
        vm_os_obj.execute("killall ptu", self._command_timeout)

    def install_prime95(self, vm_type, vm_os_obj, common_content_vm, app_details=False):
        """
        Prime95 installer.
        1. Copy the file to SUT and installed it.

        :Param: app_details contains path and name of the application
        :return: application path , name and copy method
        """
        if vm_type == "WINDOWS" or vm_type == "RS5":
            artifactory_name = ArtifactoryName.DictWindowsTools[ArtifactoryTools.PRIME95_ZIP_FILE]
            zip_file_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
            if app_details:
                prime_path = common_content_vm.copy_zip_file_to_sut("prime95", zip_file_path)
                return prime_path, "prime95"
            return common_content_vm.copy_zip_file_to_sut("prime95", zip_file_path)
        elif vm_type == "RHEL" or vm_type == "CENTOS":
            if app_details:
                path = self.copy_mprime_file_to_sut(vm_os_obj)
                return path, "mprime"
            return self.copy_mprime_file_to_sut(vm_os_obj)
        else:
            self._log.error("Prime95 is not supported on OS '%s'" % self._os.sut_os)
            raise NotImplementedError("Prime95 is not supported on OS '%s'" % self._os.sut_os)

    def copy_mprime_file_to_sut(self, vm_os_obj):
        """
        This method copy the Prime95 tool from host machine to sut

        :raise: RuntimeError - If execute method fails to run the commands
        :return:None
        """

        self._log.info("Copying Prime95 tar file to VM under root folder")
        artifactory_name = ArtifactoryName.DictLinuxTools[ArtifactoryTools.STRESS_MPRIME_LINUX_FILE]
        mprime_path = self._artifactory_obj.download_tool_to_automation_tool_folder(artifactory_name)
        # copy Prime95 tar file to VM
        vm_os_obj.copy_local_file_to_sut(mprime_path, self.ROOT_PATH)
        # extract prime95 tar file
        command_extract_tar_file = "tar xvzf {}".format(self.PRIME_TOOL)
        command_result = vm_os_obj.execute(command_extract_tar_file, self._command_timeout, cwd=self.ROOT_PATH)
        if command_result.cmd_failed():
            log_error = "Failed to run {} command with return value = '{}' and std_error='{}'.." \
                .format(command_extract_tar_file, command_result.return_code, command_result.stderr)
            self._log.error(log_error)
            raise RuntimeError(log_error)

        self._log.info("The file '{}' has been decompressed successfully ..".format(self.PRIME_TOOL))

    def execute_mprime(self, vm_os_obj, arguments, execution_time, cmd_dir):
        """
        This method is to execute mprime tool.

        :param cmd_dir
        :param arguments
        :param execution_time
        :return unexpected_expect and successful test
        :raise content_exception
        """
        common_content_lib_vm_obj = CommonContentLib(self._log, vm_os_obj, self._cfg_opts)
        install_collateral_vm_obj = InstallCollateral(self._log, vm_os_obj, self._cfg_opts)
        install_collateral_vm_obj.install_python_package('pexpect')
        args = ""
        cpu_utilisation_old_value = 0
        try:
            for key, value in arguments.items():
                args = args + '"%s"="%s" ' % (key, value)
            args = args.strip()
            self._log.debug(args)
            self._log.debug("Execute : mprime_linux.py {}".format(args))
            vm_os_obj.execute_async("python3 mprime_linux.py %s > %s" % (args, Mprime95ToolConstant.MPRIME_LOG_FILE),
                                   cmd_dir)
            # Waiting for some time to complete mprime questions
            time.sleep(TimeConstants.FIVE_MIN_IN_SEC)
            start_time = time.time()
            while time.time() - start_time <= execution_time:
                if not self.check_app_running(vm_os_obj, app_name=Mprime95ToolConstant.MPRIME_TOOL_NAME,
                                              stress_test_command="./" + Mprime95ToolConstant.MPRIME_TOOL_NAME):
                    raise content_exceptions.TestFail('mprime95 tool is not executing')
                self._log.debug('mprime process is executing...')
                cpu_utilisation = common_content_lib_vm_obj.get_cpu_utilization()
                if cpu_utilisation < cpu_utilisation_old_value:
                    raise content_exceptions.TestFail('Unexpected CPU utilization is Captured and old cpu utilization '
                                                      'value {} and new CPU utilization value is {} '.format(
                        cpu_utilisation_old_value, cpu_utilisation))
                time.sleep(TimeConstants.ONE_MIN_IN_SEC)
            self._log.info("Terminate the mprime process")
            self.kill_stress_tool(vm_os_obj, stress_tool_name=Mprime95ToolConstant.MPRIME_TOOL_NAME, stress_test_command=
            "./" + Mprime95ToolConstant.MPRIME_TOOL_NAME)
            output = common_content_lib_vm_obj.execute_sut_cmd(sut_cmd=self.CAT_COMMAND.format(
                Mprime95ToolConstant.MPRIME_LOG_FILE), cmd_str="check mprime log file",
                execute_timeout=self._command_timeout, cmd_path=cmd_dir)

            self._log.debug(output)

            unexpected_expect_regex = re.search(Mprime95ToolConstant.REGEX_FOR_UNEXPECTED_EXPECTS, output.strip())
            successfull_test_regex = re.search(Mprime95ToolConstant.REGEX_FOR_SUCCESSFULL_EXPECTS, output.strip())
            if not successfull_test_regex:
                raise content_exceptions.TestFail('Unknown Error while executing prime95')
            unexpected_expect_test = []
            successfull_test = eval(successfull_test_regex.group(1).strip())
            if unexpected_expect_regex:
                unexpected_expect_test = eval(unexpected_expect_regex.group(1).strip())

            return unexpected_expect_test, successfull_test
        except Exception as ex:
            raise content_exceptions.TestFail(ex)

    def create_install_driver_vm_object(self, vm_name):
        """
        This method is to create driver vm object
        :param vm_name: name of the VM. ex: windows_0 ,RHEL_0
        :param vm_type: type of VM. ex: Windows, RHEL
        :param copy_driver: copy  driver to VM to copy ini files
        :return: None
        :raise: None
        """
        self._log.info("Creating driver object to install on VM")
        self._vm_provider._install_ini_in_vm(vm_name, self.WINDOWS_VM_USERNAME, self.WINDOWS_VM_PASSWORD)
        self._log.info("Successfully driver files installed  on VM")

    def kill_stress_tool(self, vm_os_obj, stress_tool_name, stress_test_command=None):
        """
        Terminate stress tool process.

        :param vm_os_obj: VM os execute object
        :param stress_tool_name: Name of the stress app tool.
        :param stress_test_command: Command to execute stress tool
        :return : None
        :raise: Raise RuntimeError Exception if failed to kill the stress tool process.
        """
        if not self.check_app_running(vm_os_obj, stress_tool_name, stress_test_command):
            self._log.debug("{} tool is not running ".format(stress_tool_name))
            return

        self._log.info("killing {} tool".format(stress_tool_name))
        vm_os_obj.execute("pkill {}".format(stress_tool_name), self._command_timeout)
        sleep_time = 100
        while sleep_time > 0:
            time.sleep(5)  # give some time for app to terminate itself
            if self.check_app_running(vm_os_obj, stress_tool_name, stress_test_command):
                sleep_time = sleep_time - 5
                continue
            else:
                break
        if self.check_app_running(vm_os_obj, stress_tool_name, stress_test_command):
            raise RuntimeError('{} tool not killed'.format(stress_tool_name))

    def check_app_running(self, vm_os_obj, app_name, stress_test_command=None):
        """
        This method check whether application is running or not

        :param vm_os_obj: VM os execute object
        :param app_name: name of the application.
        :param stress_test_command: Stress command
        :return : False if particular application is not running else True
        :raise: None
        """
        check_app_sut_cmd = "ps -ef |grep {}|grep -v grep".format(app_name)

        command_result = vm_os_obj.execute(check_app_sut_cmd, self._command_timeout)
        self._log.debug(command_result.stdout)
        if stress_test_command not in command_result.stdout:
            return False
        return True

    def virt_execute_host_cmd_esxi(self, cmd, cwd=".", timeout=30):
        return self._vm_provider.vmp_execute_host_cmd_esxi(cmd=cmd, cwd=cwd, timeout=timeout)

    def get_sut_ip_esxi(self):
        return self._vm_provider.sut_ip

    def csv_file_analysis(self, file, key):
        df = pd.DataFrame(pd.read_csv(file, encoding='utf-8', skiprows=13, usecols=[key]))
        result = df[key].value_counts()
        res = dict(result)
        flag = False
        if len(res) == 1 and 0 in res.keys():
            flag = True
        if len(res) == 2 and 0 in res.keys() and key in res.keys():
            flag = True
        return flag, result

    def restore_vm_esxi(self, vm_name):
        self._log.info("restore vm env")
        self.shutdown_vm_esxi(vm_name)
        _, out, err = self.virt_execute_host_cmd_esxi(
            f'Get-PassthroughDevice -VM {vm_name} | Remove-PassthroughDevice -confirm:$false')
        self._log.info("restore vm successful ", err is None)

    def create_datastore(self, name, disk):
        try:
            cmd_create_new_datastore = f'New-Datastore -VMHost {self.sut_ip} -Name {name} -Path {disk}  -VMFS'
            self.virt_execute_host_cmd_esxi(cmd_create_new_datastore)
        except Exception as ex:
            raise content_exceptions.TestFail(ex)

    def connect_vcenter(self, vcenter_ip, vcenter_user, vcenter_password, cmd, cwd=".", timeout=30):
        CMD_SUPRESS_CERT_WARN = f'Set-PowerCLIConfiguration -InvalidCertificateAction Ignore -Confirm:$false ' \
                                f'-WarningAction 0 2>$null|out-null'
        CMD_CONNECT_TO_ESXI_vcenter = f'Connect-VIServer -Server {vcenter_ip} ' + \
                                      f'-Protocol https -User {vcenter_user} ' + \
                                      f'-Password {vcenter_password}'
        self._log.info(f"<{vcenter_ip}> execute host command {CMD_CONNECT_TO_ESXI_vcenter} in PowerCLI")
        host_cmd = f"{CMD_SUPRESS_CERT_WARN}; {CMD_CONNECT_TO_ESXI_vcenter}; {cmd}"
        return self._vm_provider.vmp_execute_host_cmd(cmd=host_cmd, cwd=cwd, timeout=timeout, powershell=True)

    def migrate_vm_to_new_datastore(self, vm_name, dest_datastore):
        try:
            folder_name = "Folder"
            datacenter_name = "datacenter_new"
            cmd_to_get_folder = f"Get-Folder -NoRecursion | New-Folder -Name {folder_name}"
            self.connect_vcenter(self.vcenter_ip, self.VCENTER_USERNAME, self.VCENTER_PASSWORD, cmd_to_get_folder)
            cmd_to_datacenter = f'New-Datacenter -location {folder_name} -Name  {datacenter_name}'
            self.connect_vcenter(self.vcenter_ip, self.VCENTER_USERNAME, self.VCENTER_PASSWORD, cmd_to_datacenter)
            cmd_add_vm_host = f"Add-VMHost -Name {self.sut_ip}  -Location {datacenter_name} -User 'root' -Password 'intel@123' -Force -Confirm:$false"
            self.connect_vcenter(self.vcenter_ip, self.VCENTER_USERNAME, self.VCENTER_PASSWORD,
                                 cmd_add_vm_host.format(self.vcenter_ip))
            cmd_movevm = f'Move-VM -VM  {vm_name} -Datastore {dest_datastore}'
            self.connect_vcenter(self.vcenter_ip, self.VCENTER_USERNAME, self.VCENTER_PASSWORD, cmd_movevm)
        except Exception as ex:
            raise content_exceptions.TestFail(ex)

    def get_datastore_of_vm(self, vm_name, datastore):
        try:
            cmd_get_datastore2 = f'$vm1 = Get-VM -Name {vm_name};Get-Datastore -RelatedObject $vm1 | Select-Object -Property Name | Where-Object Name -EQ {datastore}'
            result_p = self.connect_vcenter(self.vcenter_ip, self.VCENTER_USERNAME, self.VCENTER_PASSWORD,
                                            cmd_get_datastore2)
            for word in result_p:
                if b'datastore_new' in word:
                    self._log.info('Vm migrated successfully to new datastore')
                    return 0
            else:
                raise RuntimeError('Vm dint migrate successfully to new datastore')
        except Exception as ex:
            raise content_exceptions.TestFail(ex)

    def validate_custom_datastore(self,datastore_name):
        try:
           cmd_get_datastore = f'get-datastore {datastore_name}'
           output = self.virt_execute_host_cmd_esxi(cmd_get_datastore)
           if output:
               self._log.info('Got the datastore successfully')
           else:
               raise RuntimeError('datastore is not created successfully, Create a custom size datastore from the host')
        except Exception as ex:
            raise content_exceptions.TestFail(ex)

    def virt_com_exec_cmd_on_qemu_vm(self, vm_name, cmd, cmd_str="", cmd_path="/", execute_timeout=None):
        """
        This function is to rum commands on VM created with Qemu Command on Linux
        :param vm_name:
        :param cmd:
        :param cmd_str:
        :param cmd_path:
        :param execute_timeout:
        :return:
        """
        return self._vm_provider.execute_command_on_qemu_vm(vm_name=vm_name, cmd=cmd, cmd_str=cmd_str,
                                                            cmd_path=cmd_path, execute_timeout=execute_timeout)

    def virt_com_exec_asynccmd_on_qemu_vm(self, vm_name, cmd, cmd_str="", cmd_path="/", execute_timeout=None):
        """
        This function is to rum commands on VM created with Qemu Command on Linux
        :param vm_name:
        :param cmd:
        :param cmd_str:
        :param cmd_path:
        :param execute_timeout:
        :return:
        """
        return self._vm_provider.execute_async_command_on_qemu_vm(vm_name=vm_name, cmd=cmd, cmd_str=cmd_str,
                                                            cmd_path=cmd_path, execute_timeout=execute_timeout)

    @property
    def vm_provider(self):
        return self._vm_provider
