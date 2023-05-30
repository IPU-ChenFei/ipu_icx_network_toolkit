import os

from src.virtualization.lib.const import sut_tool

cur_path = os.path.abspath(__file__)
project_path = f"{cur_path.split('src')[0]}"
project_path_virtual = os.path.join(project_path, "src", "virtualization", "lib")

SGX_INSTALL = f"{project_path_virtual}\\common\\sgx_install.py "
PPEXPECT_PY = f"{project_path_virtual}\\common\\ppexpect.py "
VM_CONNECT_PY = f"{project_path}\\src\\virtualization\\lib\\common\\vm_connect.py "

SGX_REPO_PATH = "/opt/intel"
SGX_RPM_LOCAL_REPO = "sgx_rpm_local_repo.tgz"
FUNC_CMD = "./SGXFunctionalValidation -q -skip_registration_test"

NEW_IMG_PATH = "/var/lib/libvirt/images/qemu.qcow2"

RHEL_VM_NAME = "rhel1"
RHEL_VM_NAME2 = "rhel2"
RHEL_VM_NAME3 = "rhel3"
CENT_VM_NAME = "centos1"
CENT_VM_NAME2 = "centos2"
WINDOWS_VM_NAME = "windows1"
WINDOWS_VM_NAME2 = "windows2"
WINDOWS_VM_NAME3 = "windows3"
VT_OVMF_L = f"{sut_tool('VT_TOOLS_L')}/OVMF.fd"

MKDIR_NAME = 'nvmevmd'
INTEL_NVME_ZIP = 'intel-nvme-vmd-en_2.0.0.1146-1OEM.700.1.0.15843807_16259168-package.zip'
INTEL_NVME_VIB = 'intel-nvme-vmd-2.0.0.1146-1OEM.700.1.0.15843807.x86_64.vib'
INTEL_NVME_VMD = 'intel-nvme-vmd'
VIBS_REMOVED = 'VIBs Removed: INT_bootbank_intel-nvme-vmd_2.0.0.1146-1OEM.700.1.0.15843807'
VIBS_INSTALLED = 'VIBs Installed: INT_bootbank_intel-nvme-vmd_2.0.0.1146-1OEM.700.1.0.15843807'

TEMPLATE = f"{sut_tool('VT_IMGS_L')}/windows0.qcow2"

SWITCH_NAME = 'ExternalSwitch'
NIC_NAME = 'X710'
MELL_NIC_NAME = 'Mellanox'
NIC_SWITCH_NAME = SWITCH_NAME + "_" + NIC_NAME
MELL_NIC_SWITCH_NAME = SWITCH_NAME + "_" + MELL_NIC_NAME

# host tools
HOST_IOMETER_PATH = sut_tool('VT_IOMETER_H')

# tools path
ETHR_TOOL_PATH = f"{sut_tool('SUT_TOOLS_WINDOWS_VIRTUALIZATION')}\\ethr_windows"
NTTTCP_TOOL_PATH = f"{sut_tool('SUT_TOOLS_WINDOWS_VIRTUALIZATION')}\\ntttcp"

USB_TYPE = "kingston"
# PCI device
PCI_NVM_TYPE = "NVM"
I210_NIC_TYPE = "I210"
X710_NIC_TYPE = "710"
E810_NIC_TYPE = "810"
MLX_NIC_TYPE = "Mellanox"

Vsphere = "Vsphere"

SUT_BR0_IP = "11.0.100.2"
VM_BRO_IP = "11.0.100.10"