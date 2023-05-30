# import base64
# from typing import List
# from src.mev.lib.mevconfig import *
# from src.mev.lib.components import *
# from pyartifactory import Artifactory
# from src.lib.toolkit.auto_api import *
# from xml.etree import ElementTree as ET
# from src.lib.toolkit.basic.config import LOG_PATH
# from src.lib.toolkit.infra.logs.dtaf_log import dtaf_logger
# from src.lib.toolkit.steps_lib.os_scene import OperationSystem
# from dtaf_core.providers.provider_factory import ProviderFactory
# from src.mev.lib.utility import BaseConsoleLogProvider2, iperf3_data_conversion, gen_wait_and_expect_func, get_core_list
# from src.configuration.config.sut_tool.egs_sut_tools import SUT_TOOLS_LINUX_MEV, SUT_TMP_LINUX_MEV, SUT_MEV_ROOT_LINUX,\
#     SUT_IMAGE_LINUX_MEV, HOST_TMP_MEV, HOST_IMAGE_MEV
import base64
from typing import List
from src.network.lib.mevconfig import *
from src.network.lib.components import *
from pyartifactory import Artifactory
from dtaf_core.lib.tklib.auto_api import *
from xml.etree import ElementTree as ET
from dtaf_core.lib.tklib.basic.config import LOG_PATH
from dtaf_core.lib.tklib.infra.logs.dtaf_log import dtaf_logger
from dtaf_core.lib.tklib.steps_lib.os_scene import OperationSystem
from dtaf_core.providers.provider_factory import ProviderFactory
from src.network.lib.utility import BaseConsoleLogProvider2, iperf3_data_conversion, gen_wait_and_expect_func, get_core_list
from tkconfig.sut_tool.egs_sut_tools import SUT_TOOLS_LINUX_MEV, SUT_TMP_LINUX_MEV, SUT_MEV_ROOT_LINUX,\
    SUT_IMAGE_LINUX_MEV, HOST_TMP_MEV, HOST_IMAGE_MEV


class MEV:
    def __init__(self, sut, acc_port=local_mev['ACC'], imc_port=local_mev['IMC']):
        self.xhc = XHC(sut)
        self.imc = IMC(sut)
        self.acc = ACC(self.imc)
        self.vm_list = []
        self._peer = {}
        self._sut = sut
        self.acc_console = ProviderFactory.create(
            ET.fromstring(f"""
            <console>
                <driver>
                    <com>
                        <baudrate>460800</baudrate>
                        <port>{acc_port}</port>
                        <timeout>5</timeout>
                    </com>
                </driver>
                <credentials user="root" password=""/>
                <login_time_delay>10</login_time_delay>
            </console>
             """), dtaf_logger)
        com_cfg_dict = ET.fromstring(f"""
            <console>
                <driver>
                    <com>
                        <baudrate>460800</baudrate>
                        <port>{imc_port}</port>
                        <timeout>5</timeout>
                    </com>
                </driver>
                <credentials user="root" password=""/>
                <login_time_delay>10</login_time_delay>
            </console>
             """)
        self.imc_log = BaseConsoleLogProvider2(com_cfg_dict, 'IMC')

    @property
    def peer(self):
        return self._peer

    @property
    def components(self):
        # com_list = [self.xhc, self.imc]
        com_list = [self.xhc, self.imc, self.acc]
        com_list.extend(self.vm_list)
        return com_list

    def execute_imc_cmd(self, cmd, timeout=60, cwd='/home/root', async_cmd=False):
        return self.imc.execute_shell_cmd_async(cmd, timeout, cwd) if async_cmd\
            else self.imc.execute_shell_cmd(cmd, timeout, cwd)

    def execute_acc_cmd(self, cmd, timeout=60, cwd='/home/root', async_cmd=False):
        return self.acc.execute_shell_cmd_async(cmd, timeout, cwd) if async_cmd \
            else self.acc.execute_shell_cmd(cmd, timeout, cwd)

    def general_bring_up(self, mac_address='00:00:00:00:03:14'):
        """
        API for bringing up MEV card
        :param mac_address: mac address of MEV card, default is '00:00:00:00:03:14'
        :return: None
        """
        # check whether IMC have brought up already
        if self.imc.get_ether_name(1452, 0):
            logger.debug('Get NIC Ethernet name on IMC. IMC is brought up')
        else:
            logger.debug('Bring up IMC now')
            [day, cur_time] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()).split(' ')
            self.execute_imc_cmd(f'date -s "{day}"')
            self.execute_imc_cmd(f'date -s "{cur_time}"')
            self.execute_imc_cmd('modprobe icc_net')
            time.sleep(10)
            self.execute_imc_cmd('ip addr add 192.168.96.1/24 dev eth2')
            self.execute_imc_cmd('ip link set eth2 up')
            self.execute_imc_cmd(rf"sed -i 's/00:00:00:00:03:14/{mac_address}/g' cp_init.cfg",
                                 cwd='/usr/bin/cplane')
            self.execute_imc_cmd('./imccp 0000:00:01.6 0 cp_init.cfg'
                                 , 10, cwd='/usr/bin/cplane', async_cmd=True)
            time.sleep(30)
            self.execute_imc_cmd('modprobe idpf')
            Case.wait_and_expect('load idpf successfully on IMC.', 60,
                                 gen_wait_and_expect_func, 10, self.imc.get_ether_name, '1452', 0)
            self.execute_imc_cmd('ip link set lo up')
        self.imc.get_mac()
        # ACC
        if self.acc.get_ether_name(1452, 0):
            logger.debug('Get NIC Ethernet name on ACC. ACC is brought up')
        else:
            self.acc_console.wait_for_login(10)
            self.acc_console.login()
            assert self.acc_console.in_console()
            self.acc_console.execute('modprobe icc_net', timeout=10, end_pattern=re.compile('root@mev-acc'))
            self.acc_console.execute('ip addr add 192.168.96.2/24 dev eth0', timeout=10,
                                     end_pattern=re.compile('root@mev-acc'))
            self.acc_console.execute('ip link set eth0 up', timeout=10, end_pattern=re.compile('root@mev-acc'))
            self.acc_console.exit()
            logger.debug('Bring up ACC now')
            self.execute_acc_cmd('modprobe idpf')
            Case.wait_and_expect('load idpf successfully on ACC.', 60,
                                 gen_wait_and_expect_func, 10, self.acc.get_ether_name, '1452', 0)
            self.execute_acc_cmd('ip link set lo up')
        self.acc.get_mac()
        # check whether XHC have brought up already
        if self.xhc.get_ether_name(1452, 0):
            logger.debug('Get NIC Ethernet name on XHC. XHC is brought up')
        else:
            logger.debug('Bring up XHC now')
            ret, _, _ = self._sut.execute_shell_cmd_async('./start_xeoncp.sh -i 8086:1453', timeout=5,
                                                          cwd='/usr/bin/cplane')
            Case.expect("start CP on XHC", ret == 0)
            self.xhc.execute_shell_cmd('modprobe idpf')
            Case.wait_and_expect('load idpf successfully on XHC.', 60,
                                 gen_wait_and_expect_func, 10, self.xhc.get_ether_name, '1452', 0)
            self._sut.execute_shell_cmd('ip link set lo up')
        self.xhc.get_mac()

    def pass_xhc_traffic(self):
        """
        Pass all traffic for XHC
        :return: None
        """
        self.execute_imc_cmd('devmem 0x202920C100 64 0x801')

    def pass_imc_traffic(self):
        """
        Pass all traffic for IMC
        :return: None
        """
        self.execute_imc_cmd('devmem 0x202920C100 64 0x806')

    def pass_acc_traffic(self):
        """
        Pass all traffic for ACC
        :return: None
        """
        self.execute_imc_cmd('devmem 0x202920C100 64 0x805')

    def pass_vf_traffic(self, vm):
        """
        Pass all traffic for specific vm
        :param: vm: object of VM
        :return: None
        """
        vid = f'0{vm.vsi_id}' if len(vm.vsi_id) == 1 else vm.vsi_id
        self.execute_imc_cmd(f'devmem 0x202920C100 64 0x8{vid}')

    def upload_file_to_imc(self, source_path, destination_path, loc='sut'):
        if loc == 'sut':
            self.imc.copy_file_from_sut_to_local(source_path, destination_path)
        elif loc == 'host':
            ret, _, _ = self._sut.execute_shell_cmd(f'ls {SUT_TMP_LINUX_MEV}')
            if ret != 0:
                self._sut.execute_shell_cmd(f'mkdir {SUT_TMP_LINUX_MEV}', cwd=SUT_MEV_ROOT_LINUX)
            file_name = source_path.split('\\')[-1]
            self._sut.upload_to_remote(source_path, SUT_TMP_LINUX_MEV)
            self.imc.copy_file_from_sut_to_local(f'{SUT_TMP_LINUX_MEV}/{file_name}', destination_path)
            self._sut.execute_shell_cmd(f'rm -f {SUT_TMP_LINUX_MEV}/{file_name}')
        else:
            raise RuntimeError("unsupported mode")

    def download_file_from_imc(self, source_path, destination_path, loc='sut'):
        if loc == 'sut':
            self.imc.copy_local_file_to_sut(source_path, destination_path)
        elif loc == 'host':
            ret, _, _ = self._sut.execute_shell_cmd(f'ls {SUT_TMP_LINUX_MEV}')
            if ret != 0:
                self._sut.execute_shell_cmd(f'mkdir {SUT_TMP_LINUX_MEV}', cwd=SUT_MEV_ROOT_LINUX)
            file_name = source_path.split('/')[-1]
            self.imc.copy_local_file_to_sut(source_path, f'{SUT_TMP_LINUX_MEV}/{file_name}')
            self._sut.download_to_local(f'{SUT_TMP_LINUX_MEV}/{file_name}', destination_path)
            self._sut.execute_shell_cmd(f'rm -f {SUT_TMP_LINUX_MEV}/{file_name}')

    def create_vf(self, vf_num):
        def count_vf_num(num):
            _, out, _ = self.execute_imc_cmd(f'/usr/bin/cplane/cli_client | grep -i "is_vf: yes" | wc -l')
            return int(out.strip('\n')) == num

        ret, _, _ = self.xhc.execute_shell_cmd(f'echo {vf_num} > /sys/class/net/{self.xhc.eth_name}/device/sriov_numvfs'
                                               , timeout=20 + vf_num * 0.5)
        Case.expect('create vf successfully', ret == 0)
        self.xhc.execute_shell_cmd('modprobe iavf')
        Case.wait_and_expect('All VFs are shown to OS.', 20 + vf_num * 1.5,
                             gen_wait_and_expect_func, 10, count_vf_num, self._sut, vf_num)

    def create_vms(self, vm_num, mem_sz=2048, cpu_num=2, hugepage=False):
        """
        Create VMs with VFs. one VF per VM
        :param vm_num: number of VMs
        :param mem_sz: memory size for each VM
        :param cpu_num: number of  CPU for each VM
        :param hugepage: enable hugepage or not
        """
        vf_list = self.__get_vf_list()
        if len(vf_list) != vm_num:
            self.create_vf(vm_num)
        while len(vf_list) != vm_num:
            vf_list = self.__get_vf_list()
            time.sleep(5)
        for i in range(vm_num):
            vm_name = f'vm{i}'
            vf = vf_list[i]
            cnt = 20
            name = None
            while not name:
                _, name, _ = self.xhc.execute_shell_cmd(f'ls /sys/bus/pci/devices/{vf}/net')
                cnt -= 1
                time.sleep(10)
            assert name
            _, out, _ = self.xhc.execute_shell_cmd(f'ifconfig {name}')
            pat = r'[A-Fa-f0-9]{2}'
            mac = re.search(fr'{pat}:{pat}:{pat}:{pat}:{pat}:{pat}', out, re.I).group()
            _, out, _ = self.execute_imc_cmd(f"/usr/bin/cplane/cli_client -q -c | grep '{mac}'")
            vsi_id = re.findall(r'vsi_id:\s0x([0-9a-fA-F]+)', out, re.I)[0]
            vm = VM(sut=self.xhc.sut, vm_name=vm_name, host_bdf=vf, mac=mac, vsi_id=vsi_id)
            _, out, _ = self._sut.execute_shell_cmd('virsh list --all')
            if vm_name not in out:
                vm.create(mem_sz, cpu_num, hugepage)
            vm.attach_device(vm.vf_host_bdf)
            vm.get_vm_ip()
            ret, _, _ = self._sut.execute_shell_cmd(f'virsh reboot {vm_name}')
            assert ret == 0
            while not vm.is_alive():
                time.sleep(10)
            vm.execute_shell_cmd('rmmod iavf')
            vm.execute_shell_cmd('modprobe iavf')

            Case.wait_and_expect('load iavf successfully.', 60,
                                 gen_wait_and_expect_func, 10, vm.get_ether_name, 'Function', 0)
            vm.update_vf_info()
            self.vm_list.append(vm)

    def __get_vf_list(self):
        """
        Get all the vf created on current sut
        """
        vf_bus_list = []
        out = self.xhc.sut.execute_shell_cmd("lspci")[1].split('\n')

        for item in out:
            if "Virtual Function" in item:
                vf_bus_id = item.split()[0]
                if len(vf_bus_id.split(":")) == 2:
                    vf_bus_id = "0000:" + vf_bus_id
                vf_bus_list.append(vf_bus_id)

        logger.debug("Got vf list: {}".format(vf_bus_list))
        return vf_bus_list

    def clean_up(self):
        if self.vm_list:
            for vm in self.vm_list:
                vm.detach_device(vm.vf_host_bdf)
                vm.shutdown()
            ret, _, _ = self.xhc.execute_shell_cmd(
                f'echo 0 > /sys/class/net/{self.xhc.eth_name}/device/sriov_numvfs'
                , timeout=60)
            if ret != 0:
                self.xhc.sut.ac_off()

    def add_peer(self, name, mac, ipv4=None, ipv6=None, eth_name='eth0'):
        self._peer[name] = Peer(name, mac, ipv4, ipv6, eth_name)


class MEVConn:
    def __init__(self, interface1, interface2):
        self.__port1 = MEV(interface1, local_mev['ACC'], local_mev['IMC'])
        self.__port2 = MEV(interface2, peer_mev['ACC'], peer_mev['IMC'])

    @property
    def port1(self):
        return self.__port1

    @property
    def port2(self):
        return self.__port2

    def connect(self):
        for comp in self.port2.components:
            self.port1.add_peer(str(comp), comp.mac, comp.ip_v4, comp.ip_v6, comp.eth_name)
        for comp in self.port1.components:
            self.port2.add_peer(str(comp), comp.mac, comp.ip_v4, comp.ip_v6, comp.eth_name)

    def bring_up(self):
        self.port1.general_bring_up()
        self.port2.general_bring_up(mac_address='00:00:00:00:04:14')


class MEVOp:
    DHCP = Peer(name='DHCP', mac=peer_dhcp['mac'], ipv4=peer_dhcp['ipv4'],
                ipv6=peer_dhcp['ipv6'], eth_name=peer_dhcp['eth_name'])

    @staticmethod
    def lce_common_prepare_step(mev):
        Case.predefined_steps_start('Load LCE env')
        mev.xhc.execute_shell_cmd('rmmod qat_lce_apfxx')
        mev.xhc.execute_shell_cmd('rmmod qat_lce_common')

        mev.general_bring_up()

        mev.execute_imc_cmd('devmem 0x204b034458 w 0x10')
        mev.execute_imc_cmd('devmem 0x204880040C w 0xA800FC00')
        Case.predefined_steps_end()

    @staticmethod
    def rdma_common_prepare_step(mev):
        Case.predefined_steps_start('Load RDMA env')
        mev.execute_imc_cmd("devmem 0x2042C40008 32 0xb000")
        mev.execute_imc_cmd("devmem 0x2042C40004 32 2")
        mev.execute_imc_cmd("devmem 0x2042C50008 32 0xb000")
        mev.execute_imc_cmd("devmem 0x2042C50004 32 2")
        mev.execute_imc_cmd("devmem 0x204200d77c 32 0x2004d")
        mev.execute_imc_cmd("devmem 0x204200d778 32 0x10000000")
        mev.execute_imc_cmd("devmem 0x204200d774 32 0x48")
        mev.execute_imc_cmd("devmem 0x204200d770 32 0x70000000")
        mev.execute_imc_cmd("devmem 0x204200d76c 32 0x80000001")
        _, out, _ = mev.execute_imc_cmd("devmem 0x204200d620")
        Case.expect("verify CPU STATUS is 0x80", "80" in out)
        mev.general_bring_up()

        mev.execute_imc_cmd("devmem 0x2023e01b88 64 0x00032418009d0019")
        mev.execute_imc_cmd("0x2023800120 64 0x00032418009d0019")

        _, _, err = mev.xhc.execute_shell_cmd("modinfo irdma")
        if err:
            Case.step("irdma not exist, install now.")
            mev.xhc.execute_shell_cmd(r'rpm -qa | grep "ibacm\|infiniband-diags\|iwpmd\|ibumad\|ibverbs\|rdma\|'
                                      r'srp_daemon\|pyverbs" | xargs rpm -e --nodeps')
            image_path = f'{SUT_IMAGE_LINUX_MEV}/{stepping}_{CI}/host/packages/mev_hw_{stepping}_fedora30'
            _, out, _ = mev.xhc.execute_shell_cmd("ls | grep rdma-core", cwd=image_path)
            out = out.strip('\n').split('\n')
            rdma_version = ''
            for name in out:
                if not name.startswith('rdma-core-d'):
                    rdma_version = name.replace('rdma-core-', '')
            mev.xhc.execute_shell_cmd(f'rpm -ivh libibverbs-{rdma_version}', cwd=image_path)
            mev.xhc.execute_shell_cmd(f'rpm -ivh libibverbs-utils-{rdma_version}', cwd=image_path)
            mev.xhc.execute_shell_cmd(f'rpm -ivh rdma-core-{rdma_version}', cwd=image_path)
            mev.xhc.execute_shell_cmd(f'rpm -ivh libibumad-{rdma_version}', cwd=image_path)
            mev.xhc.execute_shell_cmd(f'rpm -ivh librdmacm-{rdma_version}', cwd=image_path)
            mev.xhc.execute_shell_cmd(f'rpm -ivh librdmacm-utils-{rdma_version}', cwd=image_path)
            mev.xhc.execute_shell_cmd(f'rpm -ivh ibacm-{rdma_version}', cwd=image_path)
            mev.xhc.execute_shell_cmd(f'rpm -ivh infiniband-diags-{rdma_version}', cwd=image_path)
            mev.xhc.execute_shell_cmd(f'rpm -ivh rdma-core-devel-{rdma_version}', cwd=image_path)
            mev.xhc.execute_shell_cmd(f'rpm -ivh irdma-0*', cwd=image_path)
            mev.xhc.execute_shell_cmd(f'rpm -ivh iwpmd-{rdma_version}', cwd=image_path)
            mev.xhc.execute_shell_cmd(f'rpm -ivh srp_daemon-{rdma_version}', cwd=image_path)
        mev.xhc.execute_shell_cmd('modprobe ib_uverbs')
        mev.xhc.execute_shell_cmd('modprobe irdma')
        Case.sleep(15)
        _, out, _ = mev.xhc.execute_shell_cmd("ibv_devices | wc -l")
        Case.expect(f'check device presence\n{out}', int(out.strip('\n')) >= 3)
        Case.predefined_steps_end()

    @staticmethod
    def load_loop_back_env(mev):
        Case.predefined_steps_start("Setup loop back mode and add 2 namespace")
        mev.pass_xhc_traffic()
        mev.execute_imc_cmd("devmem 0x2045000028 64 0x2")
        mev.xhc.execute_shell_cmd("ip netns add ns0")
        mev.xhc.execute_shell_cmd("ip netns add ns1")
        mev.xhc.execute_shell_cmd(f"ip link add link {mev.xhc.eth_name} ipvl0 type ipvlan mode l2 vepa")
        mev.xhc.execute_shell_cmd(f"ip link add link {mev.xhc.eth_name} ipvl1 type ipvlan mode l2 vepa")
        mev.xhc.execute_shell_cmd("ip link set dev ipvl0 netns ns0")
        mev.xhc.execute_shell_cmd("ip link set dev ipvl1 netns ns1")
        Case.predefined_steps_end()

    @staticmethod
    def flash_spi_image(sut, img_path):
        try:
            sut.usb_to_sut()
            time.sleep(10)
            _, out, _ = sut.execute_shell_cmd(f'ls /sys/bus/usb/drivers/ftdi_sio/')
            pat = re.compile(r'[0-9]\S*[0-9]')
            usb_id = re.search(pat, out).group()[:-2]
        except Exception:
            raise Exception("Switch USB to SUT failed.")
        ret1, _, _ = sut.execute_shell_cmd(f"echo '{usb_id}.1'> /sys/bus/usb/drivers/ftdi_sio/unbind")
        ret2, _, _ = sut.execute_shell_cmd(f"echo '{usb_id}.3'> /sys/bus/usb/drivers/ftdi_sio/unbind")
        ret3, _, _ = sut.execute_shell_cmd(f'dotnet EthProgrammer.dll --flash {img_path}',
                                           timeout=300, cwd=f'{SUT_TOOLS_LINUX_MEV}/EthProgrammer-Linux')
        Case.expect('flash spi successful!', ret1 == ret2 == ret3 == 0)
        sut.usb_to_host()
        OperationSystem[OS.get_os_family(sut.default_os)].g3_cycle_step(sut)

    @staticmethod
    def download_ci(sut, ci_id, release_type='release', ci_type='ci'):
        if not os.path.exists(SUT_IMAGE_LINUX_MEV):
            os.makedirs(SUT_IMAGE_LINUX_MEV)
        file_type = ['acc', 'mev', 'fedora30', 'imc', 'fedora30-sources']
        download_local_path = f'{HOST_IMAGE_MEV}\\{stepping}_{ci_id}'
        if os.path.exists(download_local_path):
            logger.debug('CI build exists.')
        else:
            execute_host_cmd(f'mkdir {stepping}_{ci_id}', cwd=HOST_IMAGE_MEV)
            art = Artifactory(url=r'https://ubit-artifactory-or.intel.com/artifactory',
                              auth=('zijianhu', base64.decodebytes('U0pUVTEyMTcuLmxrdw=='.encode()).decode()))
            logger.debug('Begin to download CI build!')
            for ft in file_type:
                file = f'mev-hw-{stepping}-ci-release.{ci_id}-{ft}.tgz'
                art.artifacts.download(f'mountevans_sw_bsp-or-local/builds/official/mev-{release_type}'
                                       f'/{ci_type}/mev-{release_type}-{ci_type}-{ci_id}/deploy/{file}',
                                       f'{HOST_IMAGE_MEV}\\{stepping}_{ci_id}')
                logger.debug(f'Download {file} successfully!')
        sut.upload_to_remote(download_local_path, SUT_IMAGE_LINUX_MEV, timeout=1800)
        _, out, _ = sut.execute_shell_cmd('ls', cwd=f"{SUT_IMAGE_LINUX_MEV}/{stepping}_{ci_id}")
        items = out.split()
        for item in items:
            sut.execute_shell_cmd(f'tar -xvf {item}', timeout=600, cwd=f"{SUT_IMAGE_LINUX_MEV}/{stepping}_{ci_id}")

    @staticmethod
    def flash_ssd_image(mev: MEV, img_path):
        Case.predefined_steps_start("Flash SSD Image")
        img_name = img_path.split('/')[-1]
        mev.upload_file_to_imc(img_path, f'/home/root/{img_name}', loc='sut')
        mev.execute_imc_cmd("sed -E -i '/.*(klogd|syslogd).*/d' /etc/inittab && kill -1 1 &&"
                            " pkill syslogd && pkill klogd && umount /log && umount /mnt")
        ret, _, _ = mev.execute_imc_cmd(f'dd if=/home/root/{img_name} of=/dev/nvme0n1 bs=64k')
        Case.expect("flash ssd successfully.", ret == 0)
        Case.predefined_steps_end()

    @staticmethod
    def clean_up(arg):
        def collect_os_log(sut, name):
            ret, _, _ = sut.execute_shell_cmd(f"echo alive")
            if ret != 0:
                logger.debug('OS may not alive')
                return
            sut.execute_shell_cmd(f"rm -f {SUT_TMP_LINUX_MEV}/*")
            sut.execute_shell_cmd(f"dmesg -T > {SUT_TMP_LINUX_MEV}/{name}_os_dmesg.log")
            sut.execute_shell_cmd(f"cat /var/log/messages > {SUT_TMP_LINUX_MEV}/{name}_os_messages.log")
            sut.download_to_local(f"{SUT_TMP_LINUX_MEV}/{name}_os_dmesg.log", log_path)
            sut.download_to_local(f"{SUT_TMP_LINUX_MEV}/{name}_os_messages.log", log_path)

        def collect_imc_log(mev, name):
            ret, _, _ = mev.execute_imc_cmd("echo alive")
            if ret != 0:
                logger.debug('IMC may not alive')
                return
            try:
                mev.execute_imc_cmd(f'dmesg > /home/root/{name}_imc_dmesg_case_end.log')
                mev.execute_imc_cmd(f'cat /log/messages > /home/root/{name}_imc_message_case_end.log')
                mev.download_file_from_imc(f'/home/root/{name}_imc_dmesg_case_end.log',
                                           log_path, loc='host')
                mev.download_file_from_imc(f'/home/root/{name}_imc_message_case_end.log',
                                           log_path, loc='host')
            except Exception:
                logger.debug('collect imc log fail...')

        log_path = os.path.join(LOG_PATH, f'clean_up')
        if isinstance(arg, MEV):
            arg.clean_up()
            collect_os_log(arg.xhc.sut, 'local')
            collect_imc_log(arg, 'local')
        elif isinstance(arg, MEVConn):
            arg.port1.clean_up()
            arg.port2.clean_up()
            collect_os_log(arg.port1.xhc.sut, 'local')
            collect_os_log(arg.port2.xhc.sut, 'remote')
            collect_imc_log(arg.port1, 'local')
            collect_imc_log(arg.port2, 'remote')

    @staticmethod
    def ping_to_dhcp(component: GenericComponent, count=20, mode='ipv4'):
        Case.predefined_steps_start("Connect to DHCP server and check connectivity")
        if isinstance(component, VM):
            component.execute_shell_cmd('rmmod iavf')
            component.execute_shell_cmd('modprobe iavf')
            Case.wait_and_expect('load iavf successfully.', 60,
                                 gen_wait_and_expect_func, 10, component.get_ether_name, 'Function', 0)
        else:
            Case.step("load idpf")
            component.execute_shell_cmd('modprobe idpf')
            Case.wait_and_expect('load idpf successfully.', 60,
                                 gen_wait_and_expect_func, 10, component.get_ether_name, '1452', 0)
        _, out, _ = component.execute_shell_cmd('nmcli c show')
        if 'dhcp' not in out:
            ret, _, _ = component.execute_shell_cmd(f'nmcli connection add '
                                                    f'type ethernet ifname {component.eth_name}'
                                                    f' con-name dhcp')
        time.sleep(15)
        if mode == 'ipv4':
            Case.expect(f"get dhcp ip {component.ip_v4} successfully", component.get_ip(component.eth_name))
            ret = component.ping_to_dst(dst_ip=MEVOp.DHCP.ip_v4, count=count, mode=mode)
        elif mode == 'ipv6':
            Case.expect(f"get dhcp ip {component.ip_v6} successfully",
                        component.get_ip(component.eth_name, mode='ipv6'))
            ret = component.ping_to_dst(dst_ip=MEVOp.DHCP.ip_v6, count=count, mode=mode)
        else:
            raise RuntimeError("Unsupported Ping mode")
        component.execute_shell_cmd('nmcli connection delete dhcp')
        Case.predefined_steps_end()
        return ret

    @staticmethod
    def generate_rules(mev: MEV, components: List[GenericComponent], timeout=300,
                       ipv4_prefix='10.2.29', ipv6_prefix='fec0::0000:0000:0002'):
        """
        :param mev: MEV object
        :param components: List of GenericComponent. For example [XHC, IMC, Peer, VM]
        :param timeout: timeout for generation
        :param ipv4_prefix: specify the ipv4 address
        :param ipv6_prefix: specify the ipv6 address
        :return: None
        """
        content = 'Interfaces:\n'
        ipv4_subid = 20
        ipv6_subid = 10
        for comp in components:
            if not comp.ip_v4:
                comp.ip_v4 = f'{ipv4_prefix}.{ipv4_subid}'
                ipv4_subid += 1
            if not comp.ip_v6:
                comp.ip_v6 = f'{ipv6_prefix}:{ipv6_subid}'
                ipv6_subid += 1
            rule_tmp = f"- Name: {comp}\n" \
                       f"  Adapter: {comp.eth_name}\n" \
                       f"  IPv4 Address: {comp.ip_v4}\n" \
                       f"  IPv4 Address Mask: 24\n" \
                       f"  IPv6 Address: {comp.ip_v6}\n" \
                       f"  IPv6 Address Mask: 112\n" \
                       f"  MAC Address: {comp.mac}\n" \
                       f"  VID Ext : 0\n" \
                       f"  VID Int : 0\n" \
                       f"  Type: {comp.port_type}\n" \
                       f"  ID: {int('0x' + str(comp.vsi_id), 16)}\n" \
                       f"  Slot: 0\n"
            content += rule_tmp
        with open(f'{HOST_TMP_MEV}\\rule_tmp.yml', 'w') as f:
            f.write(content)
        mev.xhc.sut.upload_to_remote(f'{HOST_TMP_MEV}\\rule_tmp.yml', SUT_TMP_LINUX_MEV)
        mev.xhc.execute_shell_cmd(f'python3 Generate_Rules.py -R nd_linux-mev_rpi/single_rule_creator.py -C'
                                  f' {SUT_TMP_LINUX_MEV}/rule_tmp.yml -F {SUT_TMP_LINUX_MEV}/SEM_Rules_tmp.txt',
                                  timeout=timeout, cwd=f'{SUT_TOOLS_LINUX_MEV}/mevrick/Scripts/Generate_Rules')
        mev.upload_file_to_imc(f'{SUT_TMP_LINUX_MEV}/SEM_Rules_tmp.txt', '/usr/bin/cplane', loc='sut')
        ret, _, _ = mev.execute_imc_cmd(f'./cli_client -x -f SEM_Rules_tmp.txt', timeout=30, cwd='/usr/bin/cplane')
        Case.expect('Apply rule successfully.', ret == 0)
        mev.xhc.execute_shell_cmd(f'python3 Netup_Config_to_Bash.py -C {SUT_TMP_LINUX_MEV}/rule_tmp.yml'
                                  f' -F {SUT_TMP_LINUX_MEV}/Netup_script_tmp.sh',
                                  timeout=30, cwd=f'{SUT_TOOLS_LINUX_MEV}/mevrick/Scripts/Generate_Rules')
        mev.xhc.execute_shell_cmd(f'rm -f {SUT_TMP_LINUX_MEV}/rule_tmp.yml')
        mev.xhc.execute_shell_cmd(f'rm -f {SUT_TMP_LINUX_MEV}/SEM_Rules_tmp.txt')
        for comp in components:
            if not isinstance(comp, Peer):
                comp.copy_file_from_sut_to_local(f'{SUT_TMP_LINUX_MEV}/Netup_script_tmp.sh', '~')
                comp.execute_shell_cmd('chmod 777 Netup_script_tmp.sh', cwd='~')
                comp.execute_shell_cmd(f'./Netup_script_tmp.sh {comp}', cwd='~')
                comp.execute_shell_cmd(f'rm -f Netup_script_tmp.sh', cwd='~')
        mev.xhc.execute_shell_cmd(f'rm -f {SUT_TMP_LINUX_MEV}/Netup_script_tmp.sh')

    @staticmethod
    def ping_to_each(components: List[GenericComponent], count=20, mode='ipv4'):
        for i in range(len(components)):
            for j in range(i + 1, len(components)):
                logger.info(f'ping from {components[i]} to {components[j]}...')
                ip = components[j].ip_v4 if mode == 'ipv4' else components[j].ip_v6
                if not components[i].ping_to_dst(ip, count, mode=mode):
                    return False
        return True

    @staticmethod
    def pass_all_traffic(conn: MEVConn, timeout=300):
        def pass_one_side_traffic(port: MEV):
            component_list = []
            component_list.extend(port.components)
            component_list.extend(port.peer.values())
            MEVOp.generate_rules(port, component_list, timeout)
            return component_list

        pass_one_side_traffic(conn.port2)
        for peer_name, peer_comp in conn.port2.peer.items():
            for comp in conn.port1.components:
                if str(comp) == peer_name:
                    comp.ip_v4 = peer_comp.ip_v4
                    comp.ip_v6 = peer_comp.ip_v6
                    break
        for comp in conn.port2.components:
            for peer_name, peer_comp in conn.port1.peer.items():
                if str(comp) == peer_name:
                    peer_comp.ip_v4 = comp.ip_v4
                    peer_comp.ip_v6 = comp.ip_v6
        return pass_one_side_traffic(conn.port1)

    @staticmethod
    def iperf3_stress(duration, client: GenericComponent, servers: List[GenericComponent], thread_num=4):
        """
        Run iperf stress with duration seconds, and check results meet connection requirements
        Recommend to use script on SUT OS for completing this
        Need to run 4 iperf threads for getting the correct tcp throughput (especially for high speed/rate connection)

        Args:
            duration: stress time, unit is second
            client: GenericComponent object
            servers: List of GenericComponent object
            thread_num: number of iperf3 thread

        Returns:
            None

        Raises:
            RuntimeError: If any errors
        """
        port = 5201

        log_folder_name = 'iperf3_log'
        remote_folder_path = '/root/' + log_folder_name
        cmd = 'iperf3'

        sut2 = client.sut
        client.get_ip(client.eth_name)

        exit_code, stdout, stderr = client.execute_shell_cmd(f'mkdir {remote_folder_path}')
        if exit_code == 1 and 'exist' in stderr:
            OperationSystem[OS.get_os_family(sut2.default_os)].remove_folder(sut2, remote_folder_path)
            client.execute_shell_cmd(f'mkdir {remote_folder_path}')

        port_no = port
        for server in servers:
            sut1 = server.sut
            server.get_ip(server.eth_name)

            logger.info(f'-----------kill all iperf3 server process on {server}-----------')
            _, stdout, _ = server.execute_shell_cmd(f'ps -e | grep iperf3', 30)
            if stdout != '':
                server.execute_shell_cmd('kill -9 $(pidof iperf3)')

            # create new log folder for running iperf3 in sut
            exit_code, stdout, stderr = server.execute_shell_cmd(f'mkdir {remote_folder_path}')
            if exit_code == 1 and 'exist' in stderr:
                OperationSystem[OS.get_os_family(sut1.default_os)].remove_folder(sut1, remote_folder_path)
                server.execute_shell_cmd(f'mkdir {remote_folder_path}')

            logger.info(f'-----------start iperf3 server on {server}-----------')
            for i in range(thread_num):
                port_no = port + i
                # --one-off flag mean iperf3 server will stop service after one client test
                log_file = f'{remote_folder_path}/server_{port_no}.txt'
                server.execute_shell_cmd_async(f'{cmd} -s --one-off -p {port_no} > {log_file}')

            logger.info(f'-----------start iperf3 client on {client}-----------')
            for i in range(thread_num):
                port_no = port + i
                log_file = f'{remote_folder_path}/client_{port_no}.txt'
                client.execute_shell_cmd_async(f'{cmd} -c {server.ip_v4} -p {port_no} -t {duration} > {log_file}')

            port = port_no + 1

        # wait for iperf3 finish transfer
        if duration >= 60 * 5:
            sleep_time = duration + 90
        else:
            sleep_time = duration * 1.2
        logger.info(f'-----------sleep {sleep_time} sec to wait for iperf3 finish transfer-----------')
        time.sleep(sleep_time)

        # download log file to check result
        sut2.download_to_local(remote_folder_path, LOG_PATH)

        # calc sum of transfer and bandwith
        transfer = 0
        bandwidth = 0
        for root, dirs, files in os.walk(os.path.join(LOG_PATH, log_folder_name)):
            for file in files:
                if file.startswith('client_') and file.endswith('.txt'):
                    log_file = os.path.join(root, file)
                    with open(log_file, 'r') as fs:
                        data = fs.read()
                        receiver_str = re.search(r'.*sec(.*/sec).*receiver', data).group(1)
                        receiver_data = re.split(r'\s+', receiver_str.strip())
                        transfer += float(receiver_data[0])
                        bandwidth += float(receiver_data[2])

        transfer_unit = receiver_data[1]
        bandwidth_unit = receiver_data[3]

        logger.debug(f'iperf total transfer = {transfer} {transfer_unit}')
        logger.debug(f'iperf total bandwidth = {bandwidth} {bandwidth_unit}')

        # convert data to unified unit
        transfer = iperf3_data_conversion(transfer, transfer_unit[0], bandwidth_unit[0])

        logger.debug(f'check transfer > bandwidth / 8 * duration * 0.9 with unit {bandwidth_unit[0]}Bytes')

        if transfer > bandwidth / 8 * duration * 0.9:
            logger.info(
                f'test iperf3 stress from {str(client)} with {client.ip_v4} to '
                f'{",".join(str(server for server in servers))} with'
                f' {",".join(server.ip_v4 for server in servers)} pass')
        else:
            raise RuntimeError(
                f'test iperf3 stress from {str(client)} with {client.ip_v4} to '
                f'{",".join(str(server for server in servers))} with'
                f' {",".join(server.ip_v4 for server in servers)} fail')

    @staticmethod
    def perf_prepare(conn: MEVConn, direction, queue, rx, tx):
        assert direction in ['unidirectional', 'bidirectional']
        server = conn.port1.xhc
        client = conn.port2.xhc
        sut1 = server.sut
        sut2 = client.sut

        core_list1 = get_core_list(sut1)
        core_list2 = get_core_list(sut2)

        sut1.execute_shell_cmd('rmmod idpf')
        sut1.execute_shell_cmd(rf"sed -i 's/eth=\S*/eth=\"{server.eth_name}\"/' start_drv_1_4k.sh",
                               cwd=f"{SUT_TOOLS_LINUX_MEV}/mev_perf_driver_scripts")
        sut1.execute_shell_cmd(rf"sed -i 's#.*set_irq_affinity.sh.*#./set_irq_affinity.sh "
                               rf"{core_list1[0]}-{core_list1[0] + queue} $eth#' start_drv_1_4k.sh",
                               cwd=f"{SUT_TOOLS_LINUX_MEV}/mev_perf_driver_scripts")
        sut1.execute_shell_cmd(rf"./start_drv_1_4k.sh {queue} {rx} {tx}", timeout=120,
                               cwd=f"{SUT_TOOLS_LINUX_MEV}/mev_perf_driver_scripts")

        sut2.execute_shell_cmd('rmmod idpf')
        sut2.execute_shell_cmd(rf"sed -i 's/eth=\S*/eth=\"{client.eth_name}\"/' start_drv_2_4k.sh",
                               cwd=f"{SUT_TOOLS_LINUX_MEV}/mev_perf_driver_scripts")
        sut1.execute_shell_cmd(rf"sed -i 's#.*set_irq_affinity.sh.*#./set_irq_affinity.sh "
                               rf"{core_list2[0]}-{core_list2[0] + queue} $eth#' start_drv_2_4k.sh",
                               cwd=f"{SUT_TOOLS_LINUX_MEV}/mev_perf_driver_scripts")
        sut2.execute_shell_cmd(rf"./start_drv_2_4k.sh {queue} {rx} {tx}", timeout=120,
                               cwd=f"{SUT_TOOLS_LINUX_MEV}/mev_perf_driver_scripts")

        server.get_ip(server.eth_name)
        client.get_ip(client.eth_name)
