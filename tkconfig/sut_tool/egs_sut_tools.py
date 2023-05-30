import time

"""
This section is for sut tool root path definition

The constant name consist of prefix string 'SUT_TOOLS', OS name and domain name
e.g. SUT_TOOLS_WINDOWS_BKC

The domain tools root path consist of root path, sub folder with name 'domains' and
the 2nd level sub folder with name of domain. All sub folder name is with lower alphabet
e.g. f'{SUT_TOOLS_WINDOWS_ROOT}\\domains\\bkc'

Finally the definition should be like this:
SUT_TOOLS_WINDOWS_BKC = f'{SUT_TOOLS_WINDOWS_ROOT}\\domains\\bkc'
"""
# Default SUT tools root path
#
import os.path

SUT_TOOLS_WINDOWS_ROOT = 'C:\\BKCPkg'
SUT_TOOLS_LINUX_ROOT = SUT_TOOLS_VMWARE_ROOT = '/home/BKCPkg'

# Default SUT tools root path for BKC
SUT_TOOLS_WINDOWS_BKC = f'{SUT_TOOLS_WINDOWS_ROOT}\\domains\\bkc'
SUT_TOOLS_LINUX_BKC = SUT_TOOLS_VMWARE_BKC = f'{SUT_TOOLS_LINUX_ROOT}/domains/bkc'

# Default SUT tools root path for PM
SUT_TOOLS_WINDOWS_PM = f'{SUT_TOOLS_WINDOWS_ROOT}\\domains\\pm'
SUT_TOOLS_LINUX_PM = SUT_TOOLS_VMWARE_PM = f'{SUT_TOOLS_LINUX_ROOT}/domains/pm'

# Default SUT tools root path for Memory
SUT_TOOLS_WINDOWS_MEMORY = f'{SUT_TOOLS_WINDOWS_ROOT}\\domains\\memory'
SUT_TOOLS_LINUX_MEMORY = SUT_TOOLS_VMWARE_MEMORY = f'{SUT_TOOLS_LINUX_ROOT}/domains/memory'

# Default SUT tools root path for Network
SUT_TOOLS_WINDOWS_NETWORK = f'{SUT_TOOLS_WINDOWS_ROOT}\\domains\\network'
SUT_TOOLS_LINUX_NETWORK = SUT_TOOLS_VMWARE_NETWORK = f'{SUT_TOOLS_LINUX_ROOT}/domains/network'

# Default SUT tools root path for Virtualization
SUT_TOOLS_WINDOWS_VIRTUALIZATION = f'{SUT_TOOLS_WINDOWS_ROOT}\\domains\\virtualization'
SUT_TOOLS_LINUX_VIRTUALIZATION = f'{SUT_TOOLS_LINUX_ROOT}/domains/virtualization'
SUT_TOOLS_VMWARE_VIRTUALIZATION = "/vmfs/volumes/datastore1"

# Default SUT tools root path for Multisocket
SUT_TOOLS_WINDOWS_MULTISOCKET = f'{SUT_TOOLS_WINDOWS_ROOT}\\domains\\multisocket'
SUT_TOOLS_LINUX_MULTISOCKET = SUT_TOOLS_VMWARE_MULTISOCKET = f'{SUT_TOOLS_LINUX_ROOT}/domains/multisocket'

# Default SUT tools root path for RAS
SUT_TOOLS_WINDOWS_RAS = f'{SUT_TOOLS_WINDOWS_ROOT}\\domains\\ras'
SUT_TOOLS_LINUX_RAS = SUT_TOOLS_VMWARE_RAS = f'{SUT_TOOLS_LINUX_ROOT}/domains/ras'

# Default SUT tools root path for Accelerator
HOST_TOOLS_WINDOWS_ACCELERATOR = f'{SUT_TOOLS_WINDOWS_ROOT}\\domains\\accelerator'
SUT_TOOLS_WINDOWS_ACCELERATOR = f'{SUT_TOOLS_WINDOWS_ROOT}\\domains\\accelerator'
SUT_TOOLS_LINUX_ACCELERATOR = SUT_TOOLS_VMWARE_ACCELERATOR = f'{SUT_TOOLS_LINUX_ROOT}/domains/accelerator'

# Default SUT tools root path for Storage
SUT_TOOLS_WINDOWS_STORAGE = f'{SUT_TOOLS_WINDOWS_ROOT}\\domains\\storage'
SUT_TOOLS_LINUX_STORAGE = SUT_TOOLS_VMWARE_STORAGE = f'{SUT_TOOLS_LINUX_ROOT}/domains/storage'

# Default SUT tools root path for Interop
SUT_TOOLS_WINDOWS_INTEROP = f'{SUT_TOOLS_WINDOWS_ROOT}\\domains\\interop'
SUT_TOOLS_LINUX_INTEROP = SUT_TOOLS_VMWARE_INTEROP = f'{SUT_TOOLS_LINUX_ROOT}/domains/interop'

# Default SUT tools root path for Security
SUT_TOOLS_WINDOWS_SECURITY = f'{SUT_TOOLS_WINDOWS_ROOT}\\domains\\security'
SUT_TOOLS_LINUX_SECURITY = SUT_TOOLS_VMWARE_SECURITY = f'{SUT_TOOLS_LINUX_ROOT}/domains/security'

# Default SUT tools root path for Managability
SUT_TOOLS_WINDOWS_MANAGABILITY = f'{SUT_TOOLS_WINDOWS_ROOT}\\domains\\managability'
SUT_TOOLS_LINUX_MANAGABILITY = SUT_TOOLS_VMWARE_MANAGABILITY = f'{SUT_TOOLS_LINUX_ROOT}/domains/managability'

# Default SUT tools root path for Serialsio
SUT_TOOLS_WINDOWS_SERIALSIO = f'{SUT_TOOLS_WINDOWS_ROOT}\\domains\\serialsio'
SUT_TOOLS_LINUX_SERIALSIO = SUT_TOOLS_VMWARE_SERIALSIO = f'{SUT_TOOLS_LINUX_ROOT}/domains/serialsio'



"""
This section is for tool path definition

The constant name consist of domain name, tool name and OS abbreviation(W for windows, L for Linux) and the tool 
name can not contain version number of this tool
e.g. NETWORK_IPERF3_W

The tool path consist of SUT tools root path and filename
e.g. SUT_TOOLS_WINDOWS_NETWORK + '\\iperf3-1.23.5.exe'

Finally the definition should be like this:
NETWORK_IPERF3_W = SUT_TOOLS_WINDOWS_NETWORK + '\\iperf3-1.23.5.exe'
"""
# BKC tool definition


# PM tool definition
PM_IPMI_L = f'{SUT_TOOLS_LINUX_PM}/ipmitool_linux/ipmitool'

# Memory tool definition


# Network tool definition
NW_BIND_L = f"{SUT_TOOLS_LINUX_NETWORK}/dpdk-21.05/usertools"
NW_PMD_L = f"{SUT_TOOLS_LINUX_NETWORK}/build/app"
NW_PKTGEN_ISTALL_L = f"{SUT_TOOLS_LINUX_NETWORK}/pktgen-dpdk-pktgen-21.02.0"
NW_DPDK_INSTALL_L = f"{SUT_TOOLS_LINUX_NETWORK}/dpdk-21.05/build"
NW_DPDK_MESON_L = f"{SUT_TOOLS_LINUX_NETWORK}/dpdk-21.05"
NW_VERSION_CHECK_L = f"{NW_DPDK_INSTALL_L}/app"
NW_DTS_L = f"{SUT_TOOLS_LINUX_NETWORK}/dpdk-21.05/build/examples"
NW_PKTGEN_TEST_L = f"{SUT_TOOLS_LINUX_NETWORK}/pktgen-dpdk-pktgen-21.02.0/builddir/app"
NW_WINDOWS_HEB_W = f"{SUT_TOOLS_WINDOWS_ROOT}\PSTools"

# Virtualization tool definition
SUT_TOOLS_LINUX_VIRTUALIZATION_AUTO_PROJ = f'{SUT_TOOLS_LINUX_VIRTUALIZATION}/auto-poc'
SUT_TOOLS_WINDOWS_VIRTUALIZATION_AUTO_PROJ = f'{SUT_TOOLS_WINDOWS_VIRTUALIZATION}\\auto-poc'

SUT_TOOLS_LINUX_VIRTUALIZATION_IMGS = f'{SUT_TOOLS_LINUX_VIRTUALIZATION}/imgs'
SUT_TOOLS_WINDOWS_VIRTUALIZATION_IMGS = f'{SUT_TOOLS_WINDOWS_VIRTUALIZATION}\\imgs'

VT_AUTO_POC_L = f'{SUT_TOOLS_LINUX_VIRTUALIZATION}/auto-poc'
VT_AUTO_POC_W = f'{SUT_TOOLS_WINDOWS_VIRTUALIZATION}\\auto-poc'

VT_IMGS_L = f'{SUT_TOOLS_LINUX_VIRTUALIZATION}/imgs'
VT_IMGS_W = f'{SUT_TOOLS_WINDOWS_VIRTUALIZATION}\\imgs'
VT_IMGS_H = VT_IMGS_W

VT_TOOLS_L = f'{SUT_TOOLS_LINUX_VIRTUALIZATION}/tools'
VT_TOOLS_W = f'{SUT_TOOLS_WINDOWS_VIRTUALIZATION}\\tools'
VT_TOOLS_V = SUT_TOOLS_VMWARE_VIRTUALIZATION
VT_TOOLS_H = VT_TOOLS_W

VT_FIO_L = f'{VT_TOOLS_L}/fio-3.19-3.el8.src.rpm'
VT_KVM_UNIT_TESTS_L = f'{VT_TOOLS_L}/kvm-unit-tests-master.zip'
VT_KVM_UNIT_TESTS_UNZIP_L = f'{VT_TOOLS_L}/kvm-unit-tests-master'
VT_ETHR_W = f'{SUT_TOOLS_WINDOWS_VIRTUALIZATION}\\ethr'
VT_NTTTCP_W = f'{SUT_TOOLS_WINDOWS_VIRTUALIZATION}\\ntttcp'

VT_SGX_ROOT_L = f'{VT_TOOLS_L}/SGX'
VT_SGX_DRIVER_BIN_L = f'{VT_SGX_ROOT_L}/sgx_linux_x64_driver_2.11.0_2d2b795.bin'
VT_SGXFUNCTIONALVALIDATION_L = f'{VT_SGX_ROOT_L}/SGXFunctionalValidation_v0.8.9.0.tar.gz'
VT_SGX_SDK_BIN_L = f'{VT_SGX_ROOT_L}/sgx_linux_x64_sdk_2.15.100.3.bin'
VT_SGX_ROOT_W = f'{SUT_TOOLS_WINDOWS_VIRTUALIZATION}\\SGX\\'
VT_SGX_ZIP_W = f'{SUT_TOOLS_WINDOWS_VIRTUALIZATION}\\SGX.zip'

SUT_TOOLS_VM_VIRTUALIZATION_W = SUT_TOOLS_WINDOWS_VIRTUALIZATION
VT_VM_SGX_ROOT_W = VT_SGX_ROOT_W
VT_VM_SGX_ZIP_W = VT_SGX_ZIP_W

VT_ACPICA_UNIX_L = f'{VT_TOOLS_L}/acpica-unix-20190509.tar.gz'
VT_CPUID_L = f'{VT_TOOLS_L}/cpuid'
VT_CPUID2_L = f'{VT_TOOLS_L}/cpuid2'
VT_MSR_TOOLS_L = f"{VT_TOOLS_L}/msr-tools-1.3.zip"

VT_RHEL_TEMPLATE_L = f"{VT_IMGS_L}/rhel0.qcow2"
VT_WINDOWS_TEMPLATE_L = f"{VT_IMGS_L}/windows0.qcow2"
VT_QEMU_CENT_TEMPLATE_L = f"{VT_IMGS_L}/cent0.img"
VT_CENTOS_TEMPLATE_L = f"{VT_IMGS_L}/centos0.qcow2"
VT_RHEL_TEMPLATE_W = f'{VT_IMGS_W}\\rhel0.vhdx'
VT_WINDOWS_TEMPLATE_W = f'{VT_IMGS_W}\\windows0.vhdx'
VT_RHEL_TEMPLATE_H = f"{VT_IMGS_H}\\rhel0\\rhel0.ovf"
VT_WINDOWS_TEMPLATE_H = f"{VT_IMGS_H}\\windows0\\windows0.ovf"
VT_CENTOS_TEMPLATE_H = f"{VT_IMGS_H}\\centos0\\centos0.vof"


VT_RHEL_ISO_L = f"{VT_IMGS_L}/RHEL-8.4.0-20210503.1-x86_64-dvd1.iso"

VT_IOMETER_H = f"{VT_TOOLS_H}\\iometer-1.1.0-win64.x86_64-bin"
VT_VMD_V = f"{SUT_TOOLS_VMWARE_VIRTUALIZATION}/vmd_3_0_0_1009_esxi_kit.zip"
VT_VMW_ESX_V = f"VMW-esx-7.0.0-Intel-Volume-Mgmt-Device-3.0.0.1009-1OEM.700.1.0.15843807.zip"
VT_INTEL_NVME_VMD_H = f"{VT_TOOLS_H}\\intel-nvme-vmd-en_2.0.0.1146-1OEM.700.1.0.15843807_16259168-package.zip"
# VT_STRESSAPPTEST_V = f"{SUT_TOOLS_LINUX_VIRTUALIZATION}/stressapptest-master.zip"

##################################################################################

NEW_IMG_PATH = "/var/lib/libvirt/images/qemu_centos_addon.qcow2"

KVM_RHEL_TEMPLATE = f"{SUT_TOOLS_LINUX_VIRTUALIZATION_IMGS}/qemu_centos_12.qcow2"
RHEL_VM_NAME = "rhel2"
TEST_TXT = 'test.txt'
SNAPSHOT_NAME = f'snapshot_{int(time.time())}'
STATE_FILE_NAME = f'state_{int(time.time())}'
CMD_GET_NIC = 'lspci | grep {}'
NIC_TYPEPCLE3 = 'X710'

############################################################################
Rhel_Vm_Name = 'rhel4'
# OVMF_PATH = "/var/lib/libvirt/images/OVMF.fd"
OVMF_PATH = f"{SUT_TOOLS_LINUX_VIRTUALIZATION_IMGS}/OVMF.fd"
FILE_QCOW2 = f"{SUT_TOOLS_LINUX_VIRTUALIZATION_IMGS}/rhel0.qcow2"
DISK_PATH = F"{SUT_TOOLS_LINUX_VIRTUALIZATION_IMGS}"
# FILE_QCOW2 = f"{SUT_TOOLS_LINUX_VIRTUALIZATION_IMGS}/centos-8.4.2105-embargo-coreserver-202111012334.img"
CPU_SIZE = '10240'


############################################################################
CD_KVM_UNIT_TESTS_MASTER = 'cd kvm-unit-tests-master'
CONFIGURE = './configure'
MAKE_STANDALONE = 'make standalone'
TEST_VMX = './tests/vmx'
KVM_UNIT_TESTS_MASTER_PATH = f"{SUT_TOOLS_LINUX_VIRTUALIZATION}/kvm-unit-tests-master/"
UNZIP_KVM_UNIT_TESTS_MASTER = "unzip -o kvm-unit-tests-master.zip"

TEST_ACCESS = './tests/access'


# Multisocket tool definition
#


# RAS tool definition


# Accelerator tool definition
# Accelerator_LOCAL_TOOL_PATH = f'{SUT_TOOLS_WINDOWS_ACCELERATOR}\\WWXX'
Accelerator_LOCAL_TOOL_PATH = HOST_TOOLS_WINDOWS_ACCELERATOR
QATZIP_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'qat_app_q4_21-release.zip')
QATZIP_SCRIPT_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'qatzip.sh')
OPENSSL_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'openssl-OpenSSL_1_1_1-stable.zip')
QAT_ENGINE_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'QAT_Engine-0.6.12.zip')
LINPACK_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'pnpwls-master.zip')
QAT_DRIVER_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'qat20.l.0.9.0-00023_1.zip')
DLB_DRIVER_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'release_ver_7.5.2.zip')
DPDK_DRIVER_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'dpdk-20.11.3.zip')
DSA_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'idxd-config-accel-config-v3.4.6.4.zip')
STRESSAPPTEST_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'stressapptest-master.zip')
QAT_ASYM_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'QAT_Linux_OpenSSL_Speed_Test_Script_Asymmetric.sh')
QAT_SYM_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'QAT_Linux_OpenSSL_Speed_Test_Script_Symmetric.sh')
QAT_TEST_SCRIPT_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'QAT_Linux_OpenSSL_Speed_Test_Script.sh')
PTU_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'PTU_V2.2.zip')
MLC_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'mlc_v3.9a.tgz')
SAMPLE_CODE_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'sample_code.tar.gz')
MEGA_CONF_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'mega.conf')
MEGA_SCRIPT_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'mega_script.py')
KERNEL_HEADER_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'kernel-next-headers-5.12.0-2021.05.07_49.el8.x86_64.rpm')
KERNEL_DEVEL_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'kernel-spr-bkc-pc-devel-8.8-5.el8.x86_64.rpm')
KERNEL_INTERNAL_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'kernel-spr-bkc-pc-modules-internal-6.13-0.el8.x86_64.rpm')
PPEXPECT_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'ppexpect.py')
OVMF_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'OVMF.fd')
PRIME95_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'p95v303b6.linux64.tar.gz')
PRIME95_SCRIPT_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'prime95.py')
TDX_SEAM_LOADER_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'tdx-seam_1.0_v1.00.0_seamldr.zip')
TDX_SEAM_MODULE_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'tdx-seam_1.0_v1.00.0_tm.zip')
SGX_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'sgx-2.14.100.2-rhel.zip')
SGXHYDRA_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'SGXHydra.zip')
SGXSDK_SCRIPT_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'sgx_sdk.py')
SRC_SCRIPT_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'src.zip')
IDXD_KTEST_MASTER_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'idxd_ktest-master.zip')
SPR_ACCE_RANDOM_CONFIG_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'accel-random-config-and-test-main.zip')
SOCWATCH_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'socwatch_chrome_linux_INTERNAL_v2021.2_x86_64.tar.gz')
CPUID_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'cpuid')
SOCWATCH_SCRIPT_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'socwatch.py')
BASHRC_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, '.bashrc')
MSR_tool_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'msr-tools-1.3-17.el8.x86_64.rpm')
QAT_DRIVER_V_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'qat-2.0_ext_rel_bin_2.2.0.47-8.0.0-55830968-dvx.zip')
DLB_DRIVER_V_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'dlb_vmw_0.9.0.43.zip')
DSA_DRIVER_V_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'iads_ext_rel_bin_0.10.0.45-8.0.0-53620472-dvx.zip')
IAX_WB_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'iax_wb.py')
XMLCLI_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'xmlcli.zip')
EFIXMLCLI_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'XmlCliKnobs.zip')



QAT_DRIVER_NAME = 'qat20.l.0.9.0-00023_1.zip'
DLB_DRIVER_NAME = 'release_ver_7.5.2.zip'
KERNEL_HEADER_NAME = 'kernel-next-headers-5.12.0-2021.05.07_49.el8.x86_64.rpm'
KERNEL_DEVEL_NAME = 'kernel-spr-bkc-pc-devel-8.8-5.el8.x86_64.rpm'
KERNEL_INTERNAL_NAME = "kernel-spr-bkc-pc-modules-internal-6.13-0.el8.x86_64.rpm"
DPDK_DRIVER_NAME = 'dpdk-20.11.3.zip'
DSA_ACCEL_CONFIG_NAME = 'idxd-config-accel-config-v3.4.6.4.zip'
IDXD_KTEST_MASTER_NAME = 'idxd_ktest-master.zip'
SPR_ACCE_RANDOM_CONFIG_NAME = 'accel-random-config-and-test-main.zip'
IMAGE_NAME = 'centos.qcow2'
CLEAN_IMAGE_NAME= 'centos.img'
IMAGE_NAME_DLB = 'centos_dlb.qcow2'
IMAGE_BASE_NAME = 'centos_base.qcow2'
SAMPLE_CODE_NAME  = 'sample_code.tar.gz'
MEGA_SCRIPT_NAME  = 'mega_script.py'
PPEXPECT_NAME  = 'ppexpect.py'




Accelerator_REMOTE_TOOL_PATH = SUT_TOOLS_LINUX_ACCELERATOR
QATZIP_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/qatzip/'
QATZIP_SCRIPT_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/qatzip_script/'
OPENSSL_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/openssl/'
QAT_ENGINE_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/qat_engine/'
LINPACK_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/linpack/'
QAT_DRIVER_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/QAT/'
DLB_DRIVER_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/dlb/'
DPDK_DRIVER_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/dpdk_driver/'
DSA_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/DSA/'
STRESSAPPTEST_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/stressapptest/'
QAT_ASYM_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/qat_asym/'
QAT_SYM_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/qat_sym/'
QAT_TEST_SCRIPT_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/qat_test_script/'
PTU_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/ptu/'
MLC_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/mlc/'
SAMPLE_CODE_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/sample_code/'
MEGA_CONF_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/mega_conf/'
MEGA_SCRIPT_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/mega_script/'
KERNEL_HEADER_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/kernel_file/'
KERNEL_DEVEL_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/kernel_file/'
KERNEL_INTERNAL_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/kernel_file/'
PPEXPECT_MEGA_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/mega_script/'
PPEXPECT_prime95_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/prime95/'
PPEXPECT_SOCWATCH_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/socwatch_script/'
VM_PATH_L = 'https://emb-pub.ostc.intel.com/overlay/centos/8.4.2105/202111012334/images/centos-8.4.2105-embargo-coreserver-202111012334.img.xz'
ISO_PATH_L = 'https://emb-pub.ostc.intel.com/overlay/centos/8.4.2105/202111012334/images/centos-8.4.2105-embargo-installer-202111012334.iso'
TDX_SEAM_MODULE_RPM_PATH_L = 'https://ubit-artifactory-or.intel.com/artifactory/linuxmvpstacks-or-local/staging-release/stack-bkc-2022ww19/6/stack-bkc-cs8-internal/x86_64/tdx-seam-module-1.0.1-6.el8.x86_64.rpm'
TDX_SEAM_MODULE_COMMON_PATH_L = 'https://ubit-artifactory-or.intel.com/artifactory/linuxmvpstacks-or-local/staging-release/stack-bkc-2022ww19/6/stack-bkc-cs8-internal/x86_64/tdx-seam-module-common-1.0.1-6.el8.x86_64.rpm'
TDX_SEAM_MODULE_NON_PRODUCTION_PATH_L = 'https://ubit-artifactory-or.intel.com/artifactory/linuxmvpstacks-or-local/staging-release/stack-bkc-2022ww19/6/stack-bkc-cs8-internal/x86_64/tdx-seam-module-non-production-1.0.1-6.el8.x86_64.rpm'
OVMF_PATH_L = '/home/'
PRIME95_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/prime95/'
PRIME95_SCRIPT_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/prime95/'
TDX_SEAM_LOADER_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/tdx_loader/'
TDX_SEAM_MODULE_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/tdx_module/'
TDX_SEAM_RPMS_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/tdx_seam_rpms/'
PPEXPECT_SGXSDK_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/sgx/'
SGX_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/sgx/'
SGXHYDRA_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/sgx/'
SGXSDK_SCRIPT_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/sgx/'
SRC_SCRIPT_PATH_L = f'{SUT_TOOLS_LINUX_VIRTUALIZATION}/auto-poc/'
IDXD_KTEST_MASTER_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/idxd_ktest/'
SPR_ACCE_RANDOM_CONFIG_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/spr_acce_random_config/'
IMAGE_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/imgs/'
PPEXPECT_TDX_LOADER_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/tdx_loader/'
SOCWATCH_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/socwatch/'
CPUID_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/cpuid/'
SOCWATCH_SCRIPT_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/socwatch_script/'
BASHRC_PATH_L = '/root/'
MSR_TOOL_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/msr_tool/'
PPEXPECT_IAX_WB_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/iax_wb/'
IAX_WB_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/iax_wb/'
XMLCLI_TOOL_PATH_L = '/opt/APP/xmlcli/'
EFIXMLCLI_TOOL_PATH_L = '/boot/efi/bkc_tool/'


#ESXI
QAT_DRIVER_PATH_V = f'{SUT_TOOLS_VMWARE_ACCELERATOR}/QAT/'
DLB_DRIVER_PATH_V = f'{SUT_TOOLS_VMWARE_ACCELERATOR}/dlb/'
DSA_DRIVER_PATH_V = f'{SUT_TOOLS_VMWARE_ACCELERATOR}/dsa/'
ESXI_VM_TOOL_PATH_V = f'{SUT_TOOLS_VMWARE_ACCELERATOR}/esxi_vm_tool/'

QAT_DRIVER_PATH_V = f'{SUT_TOOLS_VMWARE_ACCELERATOR}/QAT/'
DLB_DRIVER_PATH_V = f'{SUT_TOOLS_VMWARE_ACCELERATOR}/dlb/'
DSA_DRIVER_PATH_V = f'{SUT_TOOLS_VMWARE_ACCELERATOR}/dsa/'
ESXI_VM_TOOL_PATH_V = f'{SUT_TOOLS_VMWARE_ACCELERATOR}/esxi_vm_tool/'
ESXI_CENTOS_TEMPLATE_PATH_V = "/vmfs/volumes/datastore1/"
ESXI_CENTOS_TEMPLATE_NAME = 'centos_acce'


