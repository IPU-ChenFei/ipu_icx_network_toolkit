from dtaf_core.lib.tklib.auto_api import *


class VIRTUAL_MACHINE_OS:
    RHEL = 'RHEL'
    CENTOS = 'CENTOS'
    WINDOWS = 'WINDOWS'


class VM_INFO:
    ID = 'Id'
    NAME = 'Name'
    UUID = 'UUID'
    OS_TYPE = 'OS Type'
    STATE = 'State'
    CPU_NUM = 'CPU(s)'
    MAX_MEMORY = 'Max memory'
    USED_MEMORY = 'Used memory'
    IS_PERSISTENT = 'Persistent'
    IS_AUTOSTART = 'Autostart'
    ENABLE_AUTOSTART = 'enable'
    DISABLE_AUTOSTART = 'disable'


TEMP_NIC_FILENAME = 'temp_nic.xml'
TEMP_PCI_FILENAME = 'temp_pci.xml'

############################### Virtual Machine Constants ##############################################################
NEW_IMG_PATH = "/var/lib/libvirt/images/qemu.qcow2"
KVM_RHEL_TEMPLATE = sut_tool('VT_RHEL_TEMPLATE_L')
KVM_WINDOWS_TEMPLATE = sut_tool('VT_WINDOWS_TEMPLATE_L')
QEMU_CENT_TEMPLATE = sut_tool('VT_QEMU_CENT_TEMPLATE_L')
HYPERV_RHEL_TEMPLATE = f"{sut_tool('VT_IMGS_W')}\\rhel0.vhdx"
HYPERV_WINDOWS_TEMPLATE = f"{sut_tool('VT_IMGS_W')}\\windows0.vhdx"
ESXI_RHEL_TEMPLATE = f"/vmfs/volumes/datastore1/rhel0"
ESXI_CENTOS_TEMPLATE = f"/vmfs/volumes/datastore1/centos0"
ESXI_WINDOWS_TEMPLATE = f"/vmfs/volumes/datastore1/windows0"

DEFAULT_MEMORY = 2048
DEFAULT_SWITCH_NAME = "ExternalSwitch"

############################### Precondition items #####################################################################
PRECOND_MAIN_TYPE_VM = "VIRTUAL_MACHINE"
PRECOND_MAIN_TYPE_DEV = "DEVICE"
PRECOND_SUB_TYPE_DISK = "DISK"
PRECOND_SUB_TYPE_NIC = "NETWORK_CARD"
PRECOND_MAIN_TYPE_SWITCH = "VIRTUAL_SWITCH"
PRECOND_MAIN_TYPE_BRIDGE = "VIRTUAL_BRIDGE"
PRECOND_MAIN_TYPE_FILE = "FILE"


class PrecondInfo:
    AUTO_POC_L = {"name": "auto_poc/", "auto_setup": False, "type": PRECOND_MAIN_TYPE_FILE, "keyword": "VT_AUTO_POC_L"}
    AUTO_POC_W = {"name": "auto_poc\\", "auto_setup": False, "type": PRECOND_MAIN_TYPE_FILE, "keyword": "VT_AUTO_POC_W"}
    RHEL1_VM = {"name": "rhel1", "auto_setup": True, "type": PRECOND_MAIN_TYPE_VM}
    RHEL2_VM = {"name": "rhel2", "auto_setup": True, "type": PRECOND_MAIN_TYPE_VM}
    WINDOWS1_VM = {"name": "windows1", "auto_setup": True, "type": PRECOND_MAIN_TYPE_VM}
    WINDOWS2_VM = {"name": "windows2", "auto_setup": True, "type": PRECOND_MAIN_TYPE_VM}
    CENTOS1_VM = {"name": "centos1", "auto_setup": True, "type": PRECOND_MAIN_TYPE_VM}
    VSPHERE_VM = {"name": "Vsphere", "auto_setup": False, "type": PRECOND_MAIN_TYPE_VM}
    NIC_X710 = {"name": "X710", "auto_setup": False, "type": PRECOND_MAIN_TYPE_DEV, "subtype": PRECOND_SUB_TYPE_NIC,
                "keyword": "710"}
    NIC_MLX = {"name": "MLX NIC", "auto_setup": False, "type": PRECOND_MAIN_TYPE_DEV, "subtype": PRECOND_SUB_TYPE_NIC,
               "keyword": "Mell"}
    USB = {"name": "U-Disk", "auto_setup": False, "type": PRECOND_MAIN_TYPE_DEV, "subtype": PRECOND_SUB_TYPE_DISK,
           "keyword": "kingston"}
    # TODO: change the method of check USB devices
    NVME_SSD = {"name": "NVME SSD", "auto_setup": False, "type": PRECOND_MAIN_TYPE_DEV, "subtype": PRECOND_SUB_TYPE_DISK,
                "keyword": "NVM"}

    # LINUX
    VIRTUAL_BRIDGE = {"name": "br0", "auto_setup": True, "type": PRECOND_MAIN_TYPE_BRIDGE, "keyword": "br0"}
    KVM_UNIT_TESTS_L = {"name": "kvm_unit_tests", "auto_setup": False, "type": PRECOND_MAIN_TYPE_FILE,
                        "keyword": "VT_KVM_UNIT_TESTS_L"}
    ACPICA_UNIX_L = {"name": "acpica_unix.tar.gz", "auto_setup": False, "type": PRECOND_MAIN_TYPE_FILE,
                     "keyword": "VT_ACPICA_UNIX_L"}
    CPUID_L = {"name": "cpuid", "auto_setup": False, "type": PRECOND_MAIN_TYPE_FILE, "keyword": "VT_CPUID_L"}
    CPUID2_L = {"name": "cpuid2", "auto_setup": False, "type": PRECOND_MAIN_TYPE_FILE, "keyword": "VT_CPUID2_L"}
    RHEL_ISO_L = {"name": "rhel_iso.iso", "auto_setup": False, "type": PRECOND_MAIN_TYPE_FILE,
                  "keyword": "VT_RHEL_ISO_L"}
    SGX_ROOT_L = {"name": "SGX/", "auto_setup": False, "type": PRECOND_MAIN_TYPE_FILE, "keyword": "VT_SGX_ROOT_L"}
    SGXFUNCTIONALVALIDATION_L = {"name": "SGXFunctionalValidation.zip", "auto_setup": False, "type": PRECOND_MAIN_TYPE_FILE, "keyword": "VT_SGXFUNCTIONALVALIDATION_L"}
    MSR_TOOLS_L = {"name": "msr_tools.zip", "auto_setup": False, "type": PRECOND_MAIN_TYPE_FILE,
                   "keyword": "VT_MSR_TOOLS_L"}
    RHEL_TEMPLATE_L = {"name": "rhel0.qcow2", "auto_setup": False, "type": PRECOND_MAIN_TYPE_FILE,
                       "keyword": "VT_RHEL_TEMPLATE_L"}
    WINDOWS_TEMPLATE_L = {"name": "windows0.qcow2", "auto_setup": False, "type": PRECOND_MAIN_TYPE_FILE,
                          "keyword": "VT_WINDOWS_TEMPLATE_L"}
    QEMU_CENT_TEMPLATE_L = {"name": "cent0.img", "auto_setup": False, "type": PRECOND_MAIN_TYPE_FILE,
                            "keyword": "VT_QEMU_CENT_TEMPLATE_L"}
    CENTOS_TEMPLATE_L = {"name": "centos0.qcow2", "auto_setup": False, "type": PRECOND_MAIN_TYPE_FILE,
                         "keyword": "VT_CENTOS_TEMPLATE_L"}

    # WINDOWS
    RHEL_TEMPLATE_W = {"name": "rhel0.vhdx", "auto_setup": False, "type": PRECOND_MAIN_TYPE_FILE,
                       "keyword": "VT_RHEL_TEMPLATE_W"}
    WINDOWS_TEMPLATE_W = {"name": "windows0.vhdx", "auto_setup": False, "type": PRECOND_MAIN_TYPE_FILE,
                          "keyword": "VT_WINDOWS_TEMPLATE_W"}
    SGX_ZIP_W = {"name": "SGX.zip", "auto_setup": False, "type": PRECOND_MAIN_TYPE_FILE, "keyword": "VT_SGX_ZIP_W"}
    VIRTUAL_SWITCH = {"name": "ExternalSwitch", "auto_setup": True, "type": PRECOND_MAIN_TYPE_SWITCH,
                      "keyword": "ExternalSwitch"}

    # VMWARE
    RHEL_TEMPLATE_V = {"name": "rhel0.ovf", "auto_setup": False, "type": PRECOND_MAIN_TYPE_FILE,
                       "keyword": "VT_RHEL_TEMPLATE_H"}
    WINDOWS_TEMPLATE_V = {"name": "windows0.ovf", "auto_setup": False, "type": PRECOND_MAIN_TYPE_FILE,
                          "keyword": "VT_WINDOWS_TEMPLATE_H"}
    CENTOS_TEMPLATE_V = {"name": "centos0.ovf", "auto_setup": False, "type": PRECOND_MAIN_TYPE_FILE,
                         "keyword": "VT_CENTOS_TEMPLATE_H"}
    IOMETER_H = {"name": "iometer/", "auto_setup": False, "type": PRECOND_MAIN_TYPE_FILE,
                 "keyword": "VT_IOMETER_H", "host": True}
    VMD_V = {"name": "vmd.zip", "auto_setup": False, "type": PRECOND_MAIN_TYPE_FILE, "keyword": "VT_VMD_V"}
    # VMW_ESX_V = {"name": "VMW_esx.zip", "auto_setup": False, "type": PRECOND_MAIN_TYPE_FILE, "keyword": "VT_VMW_ESX_V"}
    INTEL_NVME_VMD_H = {"name": "intel_nvme_vmd.zip", "auto_setup": False, "type": PRECOND_MAIN_TYPE_FILE,
                        "keyword": "VT_INTEL_NVME_VMD_H", "host": True}
