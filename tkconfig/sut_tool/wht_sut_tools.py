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
SUT_TOOLS_LINUX_VIRTUALIZATION = SUT_TOOLS_VMWARE_VIRTUALIZATION = f'{SUT_TOOLS_LINUX_ROOT}/domains/virtualization'
HOST_TOOLS_WINDOWS_VIRTUALIZATION = f'{SUT_TOOLS_WINDOWS_ROOT}\\domains\\virtualization'
VM_TOOLS_WINDOWS_VIRTUALIZATION = f'{SUT_TOOLS_WINDOWS_ROOT}\\domains\\virtualization'

# Default SUT tools root path for Multisocket
SUT_TOOLS_WINDOWS_MULTISOCKET = f'{SUT_TOOLS_WINDOWS_ROOT}\\domains\\multisocket'
HOST_TOOLS_MULTISOCKET = SUT_TOOLS_WINDOWS_MULTISOCKET
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
SUT_TOOLS_VMWARE_VIRTUALIZATION_IMGS = SUT_TOOLS_LINUX_VIRTUALIZATION_IMGS
SUT_TOOLS_WINDOWS_VIRTUALIZATION_IMGS = f'{SUT_TOOLS_WINDOWS_VIRTUALIZATION}\\imgs'

SUT_TOOLS_LINUX_VIRTUALIZATION_TOOLS = f'{SUT_TOOLS_LINUX_VIRTUALIZATION}/tools'
SUT_TOOLS_VMWARE_VIRTUALIZATION_TOOLS = SUT_TOOLS_LINUX_VIRTUALIZATION_TOOLS
SUT_TOOLS_WINDOWS_VIRTUALIZATION_TOOLS = f'{SUT_TOOLS_WINDOWS_VIRTUALIZATION}\\tools'

SUT_TOOLS_LINUX_FIO = f'{SUT_TOOLS_LINUX_VIRTUALIZATION_TOOLS}/fio-3.19-3.el8.src.rpm'

Virtualization_LOCAL_TOOL_PATH = HOST_TOOLS_WINDOWS_VIRTUALIZATION
ETHR_W = os.path.join(Virtualization_LOCAL_TOOL_PATH, 'ethr-windows.zip')
NTTTCP_W = os.path.join(Virtualization_LOCAL_TOOL_PATH, 'ntttcp-5.38.zip')
SGX_W = os.path.join(Virtualization_LOCAL_TOOL_PATH, 'SGX.zip')

Virtualization_REMOTE_TOOL_PATH = SUT_TOOLS_WINDOWS_VIRTUALIZATION
SUT_TOOLS_WINDOWS_VIRTUALIZATION_ETHR = f'{SUT_TOOLS_WINDOWS_VIRTUALIZATION}\\ethr'
SUT_TOOLS_WINDOWS_VIRTUALIZATION_NTTTCP = f'{SUT_TOOLS_WINDOWS_VIRTUALIZATION}\\ntttcp'
SUT_TOOLS_WINDOWS_VIRTUALIZATION_SGX = f'{SUT_TOOLS_WINDOWS_VIRTUALIZATION}\\sgx'

SUT_TOOLS_VM_VIRTUALIZATION = SUT_TOOLS_WINDOWS_VIRTUALIZATION
SUT_TOOLS_VM_VIRTUALIZATION_SGX = SUT_TOOLS_WINDOWS_VIRTUALIZATION_SGX

# Multisocket tool definition
MS_MLC_W = f'{SUT_TOOLS_WINDOWS_MULTISOCKET}\\MLC_Windows'
MS_STITCH_PATH = f'{HOST_TOOLS_MULTISOCKET}\\stitch_tool'


# RAS tool definition


# Accelerator tool definition
PLATFORM_NAME = 'EGS'
# Accelerator_LOCAL_TOOL_PATH = f'{SUT_TOOLS_WINDOWS_ACCELERATOR}\\WWXX'
Accelerator_LOCAL_TOOL_PATH = HOST_TOOLS_WINDOWS_ACCELERATOR
QATZIP_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'QATzip-master.zip')
QATZIP_SCRIPT_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'qatzip.sh')
OPENSSL_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'openssl-master.zip')
QAT_ENGINE_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'QAT_Engine-master.zip')
LINPACK_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'pnpwls-master.zip')
QAT_DRIVER_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'qat20.l.0.8.0-00071_4.zip')
DLB_DRIVER_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'release_ver_7.2.0.zip')
DPDK_DRIVER_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, '20.11.1.zip')
DSA_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'idxd-config-master.zip')
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
KERNEL_DEVEL_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'kernel-next-server-devel-5.12.0-2021.05.07_49.el8.x86_64.rpm')
PPEXPECT_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'ppexpect.py')
OVMF_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'OVMF.fd')
PRIME95_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'p95v303b6.linux64.tar.gz')
PRIME95_SCRIPT_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'prime95.py')
TDX_SEAM_LOADER_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'tdx-seam_1.0_v0.14.0_seamldr.zip')
TDX_SEAM_MODULE_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'tdx-seam_1.0_v0.14.0.zip')
SGX_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'sgx-2.14.100.2-rhel.zip')
SGXHYDRA_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'SGXHydra.zip')
SGXSDK_SCRIPT_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'sgx_sdk.py')
SRC_SCRIPT_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'src.zip')
IDXD_KTEST_MASTER_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'idxd_ktest-master.zip')
DSA_RANDOM_CONFIG_SCRIPT_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'spr-accelerators-random-config-and-test-master.zip')


QAT_DRIVER_NAME = 'qat20.l.0.8.0-00071_4.zip'
DLB_DRIVER_NAME = 'release_ver_7.2.0.zip'
KERNEL_HEADER_NAME = 'kernel-next-headers-5.12.0-2021.05.07_49.el8.x86_64.rpm'
KERNEL_DEVEL_NAME = 'kernel-next-server-devel-5.12.0-2021.05.07_49.el8.x86_64.rpm'
DPDK_DRIVER_NAME = '20.11.1.zip'
DSA_ACCEL_CONFIG_NAME = 'idxd-config-master.zip'
IDXD_KTEST_MASTER_NAME = 'idxd_ktest-master.zip'
DSA_RANDOM_CONFIG_NAME = 'spr-accelerators-random-config-and-test-master.zip'
IMAGE_NAME = 'centos_base.qcow2'


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
PPEXPECT_MEGA_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/mega_script/'
PPEXPECT_prime95_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/prime95/'
VM_PATH_L = 'https://emb-pub.ostc.intel.com/overlay/centos/8.4.2105/202111012334/images/centos-8.4.2105-embargo-coreserver-202111012334.img.xz'
ISO_PATH_L = 'https://emb-pub.ostc.intel.com/overlay/centos/8.4.2105/202111012334/images/centos-8.4.2105-embargo-installer-202111012334.iso'
OVMF_PATH_L = '/home/'
PRIME95_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/prime95/'
PRIME95_SCRIPT_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/prime95/'
TDX_SEAM_LOADER_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/tdx_loader/'
TDX_SEAM_MODULE_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/tdx_module/'
PPEXPECT_SGXSDK_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/sgx/'
SGX_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/sgx/'
SGXHYDRA_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/sgx/'
SGXSDK_SCRIPT_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/sgx/'
SRC_SCRIPT_PATH_L = f'{SUT_TOOLS_LINUX_VIRTUALIZATION}/auto-poc/'
IDXD_KTEST_MASTER_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/idxd_ktest/'
DSA_RANDOM_CONFIG_SCRIPT_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/dsa_random_config/'
IMAGE_PATH_L = f'{Accelerator_REMOTE_TOOL_PATH}/imgs/'