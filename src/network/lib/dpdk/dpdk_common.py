import os

from dtaf_core.lib.tklib.basic.testcase import Case
# from infra.Sut import SUT
from tkconfig.sut_tool import bhs_sut_tools
from tkconfig.sut_tool.bhs_sut_tools import SUT_TOOLS_LINUX_NETWORK, SUT_TOOLS_WINDOWS_ROOT

#####################################################


filename = 'flag.txt'
NIC_TYPE = 'E810'
path = os.path.abspath(__file__)
project_path = path.split('src')[0]
#SUT_TOOLS_WINDOWS_NETWORK = f'{SUT_TOOLS_WINDOWS_ROOT}\\domains\\network'
#MLC_H = os.path.join(Accelerator_LOCAL_TOOL_PATH, 'mlc_v3.9a.tgz')
DPDK_EXPECT_PATH = os.path.join('{}src\\network\\lib\\dpdk\\', 'dpdk_expect.py')
DPDK_PPEXPECT_PATH = os.path.join('{}src\\network\\lib\\dpdk\\', 'ppexpect.py')
DPDK_REPO = os.path.join('{}src\\network\\lib\\dpdk\\', 'intel-rhel82-yum.repo')
DPDK_VM_PATH = os.path.join('{}src\\network\\lib\\dpdk\\', 'vm_dpdk.py')
DPDK_XML_PATH = os.path.join('{}src\\network\\lib\\dpdk\\', 'dhcp.xml')
#DPDK_EXPECT_PATH = '{}src\\steps_lib\\domains\\network\\dpdk\\dpdk_expect.py'
#DPDK_PPEXPECT_PATH = '{}src\\steps_lib\\domains\\network\\tool\\ppexpect.py'
#DPDK_REPO = '{}src\steps_lib\\domains\\network\\dpdk\\intel-rhel82-yum.repo'
#DPDK_VM_PATH = '{}src\steps_lib\\domains\\network\\dpdk\\vm_dpdk.py'
#DPDK_XML_PATH = '{}src\\steps_lib\\domains\\network\\dpdk\\dhcp.xml'

YUM_MESON = "yum -y install meson"
PIP_PYELFTOOLS = r'export https_proxy=http://proxy-prc.intel.com:913 && pip3 install pyelftools'
MESON_BUILD = r"meson -Denable_kmods=true -Dexamples=all build"
ECHO_HUGEPAGES = r"echo {} > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages"
MKDIR_MNT_HUGE = r"mkdir -p /mnt/huge"
MOUNT_HUGE = r"mount -t hugetlbfs nodev /mnt/huge"
MODPROBE_VFIO = "modprobe vfio-pci"
ECHO_IOMMU_MODE = r"echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode"
ECHO_VFIO_ENABLE = r'echo "options vfio enable_unsafe_noiommu_mode=1" > /etc/modprobe.d/vfio-noiommu.conf'
NET_STATE = "ifconfig {} 0"
NET_STATE_RECOVER = "ifconfig {} 1"
NET_STATE_IFCONFIG_UP = "ifup {}"
NET_STATE_IFCONFIG_DOWN = "ifdown {}"
GET_NIC = 'lspci | grep -i {}'
BIND_CMD = 'python3 dpdk-devbind.py -b vfio-pci {} {}'
UNBIND_CMD = r'python3 dpdk-devbind.py --unbind {} {}'
BIND_ICE = R'dpdk-devbind.py -b ice {} {}'
sut_yum_repo = '/etc/yum.repos.d'
yum_repo = '/etc/'
VM_DPDK_PATH = '/home/BKCPkg/domains/network/dpdk-21.05.tar.xz'
COPY_IMAGE = 'qemu-img create -f qcow2 -b /home/BKCPkg/domains/network/rhel0.qcow2 /var/lib/libvirt/images/{}.qcow2'
#COPY_IMAGE = 'qemu-img create -f qcow2 -b /home/BKCPkg/domains/network/RHEL_VM.qcow2 /var/lib/libvirt/images/{}.qcow2'
#COPY_IMAGE = 'qemu-img create -f qcow2 -b /home/BKCPkg/domains/network/rhel1.qcow2 /var/lib/libvirt/images/{}.qcow2'
RUN_TCPDUMP = 'tcpdump -i {} -xx > tcpdump.log'
VLAN_LOG = '/home/BKCPkg/domains/network/vlan.log'
tool_p = bhs_sut_tools.NW_DPDK_MESON_L
scapy_tool_path = '/home/BKCPkg/domains/network/scapy-2.4.3rc4'
tool1_p = bhs_sut_tools.NW_DTS_L
pktgen_tool_path = '/home/BKCPkg/domains/network/pktgen-dpdk-pktgen-21.02.0/Builddir/app'

NW_BIND_L = f"{SUT_TOOLS_LINUX_NETWORK}/dpdk-21.05/usertools"
NW_PMD_L = f"{SUT_TOOLS_LINUX_NETWORK}/build/app"
NW_PKTGEN_ISTALL_L = f"{SUT_TOOLS_LINUX_NETWORK}/pktgen-dpdk-pktgen-21.02.0"
NW_DPDK_INSTALL_L = f"{SUT_TOOLS_LINUX_NETWORK}/dpdk-21.05/build"
NW_DPDK_MESON_L = f"{SUT_TOOLS_LINUX_NETWORK}/dpdk-21.05"
NW_VERSION_CHECK_L = f"{NW_DPDK_INSTALL_L}/app"
NW_DTS_L = f"{SUT_TOOLS_LINUX_NETWORK}/dpdk-21.05/build/examples"
NW_PKTGEN_TEST_L = f"{SUT_TOOLS_LINUX_NETWORK}/pktgen-dpdk-pktgen-21.02.0/builddir/app"
NW_WINDOWS_HEB_W = f"{SUT_TOOLS_WINDOWS_ROOT}\PSTools"


#####################################################
def install_dpdk(sut):
    ret = sut.execute_shell_cmd(YUM_MESON, 60 * 2)[0]
    Case.expect("install meson successfully", ret == 0)
    ret = sut.execute_shell_cmd(PIP_PYELFTOOLS)[0]
    Case.expect("install pyelftools successfully", ret == 0)
    ret = sut.execute_shell_cmd(MESON_BUILD, cwd=bhs_sut_tools.NW_DPDK_MESON_L)[0]
    Case.expect("meson successfully", ret == 0)
    ret = sut.execute_shell_cmd("ninja", 60 * 50, cwd=bhs_sut_tools.NW_DPDK_INSTALL_L)[0]
    Case.expect("ninja successfully", ret == 0)
    ret = sut.execute_shell_cmd("ninja install", 60 * 50, cwd=bhs_sut_tools.NW_DPDK_INSTALL_L)[0]
    Case.expect("ninja install successfully", ret == 0)
    sut.execute_shell_cmd("ldconfig")


def upload_dpdk_file(sut):
    sut.upload_to_remote(localpath=DPDK_EXPECT_PATH.format(project_path),
                         remotepath=bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK)
    sut.upload_to_remote(localpath=DPDK_PPEXPECT_PATH.format(project_path),
                         remotepath=bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK)
    sut.upload_to_remote(localpath=DPDK_REPO.format(project_path),
                         remotepath=bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK)
    sut.upload_to_remote(localpath=DPDK_VM_PATH.format(project_path),
                         remotepath=bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK)
    sut.upload_to_remote(localpath=DPDK_XML_PATH.format(project_path),
                         remotepath=bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK)


def set_dpdk(sut, number_huge=2048):
    # type:(SUT) ->None
    """
    Set the hugepages size of dpdk,load vfio_pci,and prepare for bond
    """

    ret = sut.execute_shell_cmd(ECHO_HUGEPAGES.format(number_huge))[0]
    Case.expect(f"echo {number_huge} KB successfully", ret == 0)
    ret = sut.execute_shell_cmd(MKDIR_MNT_HUGE)[0]
    Case.expect(r"mkdir /mnt/huge successfully", ret == 0)
    ret = sut.execute_shell_cmd(MOUNT_HUGE)[0]
    Case.expect("mount successfully", ret == 0)
    ret = sut.execute_shell_cmd(MODPROBE_VFIO)[0]
    Case.expect("modprobe vfio successfully", ret == 0)
    ret = sut.execute_shell_cmd(ECHO_IOMMU_MODE)[0]
    Case.expect("echo successfully", ret == 0)
    ret = sut.execute_shell_cmd(ECHO_VFIO_ENABLE)[0]
    Case.expect("echo successfully", ret == 0)


def bind_dpdk(sut, sut_eth1_name, sut_eth2_name, nic_type):
    # type: (SUT, str, str) -> tuple()
    """
    bond two network ports
    args:
        sut_eth1_name: nic_id1
        sut_eth2_name: nic_id2
    """
    ret = sut.execute_shell_cmd(NET_STATE.format(sut_eth1_name))[0]
    Case.expect("sut eth1 ifconfig successfully", ret == 0)
    ret = sut.execute_shell_cmd(NET_STATE.format(sut_eth2_name))[0]
    Case.expect("sut eth2 ifconfig successfully", ret == 0)
    _, nics, _ = sut.execute_shell_cmd(GET_NIC.format(nic_type))
    nics = str(nics)[:-1].split('\n')
    sut_id1 = nics[0].strip().split(' ')[0]
    sut_id2 = nics[1].strip().split(' ')[0]
    ret = sut.execute_shell_cmd(BIND_CMD.format(sut_id1, sut_id2), 60, cwd=bhs_sut_tools.NW_BIND_L)[0]
    Case.expect("sut bind successfully", ret == 0)

    return sut_id1, sut_id2


def unbind_dpdk(sut, sut_id1, sut_id2):
    Case.step("unbind network")
    ret = sut.execute_shell_cmd(UNBIND_CMD.format(sut_id1, sut_id2), 60, cwd=bhs_sut_tools.NW_BIND_L)[0]
    Case.expect("sut unbind successfully", ret == 0)
    ret = sut.execute_shell_cmd(BIND_ICE.format(sut_id1, sut_id2), 60, cwd=bhs_sut_tools.NW_BIND_L)[0]
    Case.expect("sut bind ice successfully", ret == 0)



def mtu_dpdk(sut1, sut1_eth1_name, sut1_eth2_name):
    ret = sut1.execute_shell_cmd(f'echo 9702 > /sys/class/net/{sut1_eth1_name}/mtu')[0]
    Case.expect("echo successfully", ret == 0)
    ret = sut1.execute_shell_cmd(f'echo 9702 > /sys/class/net/{sut1_eth2_name}/mtu')[0]
    Case.expect("echo successfully", ret == 0)
    ret = sut1.execute_shell_cmd('echo 2048 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages',
                                 cwd=bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK)[0]
    Case.expect("echo 2048 hugepages successfully", ret == 0)
    ret = sut1.execute_shell_cmd('mkdir -p /mnt/huge', cwd=bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK)[0]
    Case.expect("mkdir successfully", ret == 0)
    ret = sut1.execute_shell_cmd('mount -t hugetlbfs nodev /mnt/huge', cwd=bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK)[0]
    Case.expect("mount successfully", ret == 0)


def start_testpmd(sut1, dpdk_expect, start_dpdk, tool_path):

    ret, out, err = sut1.execute_shell_cmd_async(f'python3 {dpdk_expect}.py {start_dpdk} {tool_path}',
                                                 cwd=bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK)
    Case.expect('testpmd should be launched and working without errors.', ret == 0)


def clear_settings(sut, filename):
    # type: (SUT) -> None

    from pathlib import Path
    my_file = Path(filename)
    del_name = None
    if my_file.is_file():
        with open(filename, 'r') as file:
            for line in file:
                vm_name, vfs_sriov_xml = line.partition("=")[::2]
                del_name = vm_name
                # print(f"[{vm_name, vfs_sriov_xml.strip()}]")
                sut.execute_shell_cmd(f'virsh detach-device {vm_name} {vfs_sriov_xml.strip()} --config')
                sut.execute_shell_cmd(f'rm -rf {vfs_sriov_xml}')
            commands = f'virsh destroy {del_name}'
            sut.execute_shell_cmd(commands)
            commands = f'virsh undefine {del_name}'
            sut.execute_shell_cmd(commands)
            sut.execute_shell_cmd(f'rm -rf /home/{del_name}.qcow2')
        os.remove(filename)


def add_dhcp_xml(net_name):
    import xml.etree.cElementTree as elementTree
    xml_path = f"{project_path}\\src\\network\\lib\\dpdk\\dhcp.xml"

    conf = elementTree.parse(xml_path)
    root = conf.getroot()
    source = root.find('source')
    source.attrib['dev'] = net_name
    conf.write(xml_path)
