import re
import os
import abc
import time
from src.lib.toolkit.basic.log import logger
import xml.etree.cElementTree as elementTree
from src.lib.toolkit.basic.testcase import Case
from src.mev.lib.utility import execute_host_cmd
from src.configuration.config.sut_tool.egs_sut_tools import SUT_TOOLS_LINUX_MEV, HOST_TMP_MEV


class GenericComponent:
    """
    A Generic component of MEV card contains below properties
    - bdf: the bdf of component
    - eth_name: ethernet interface
    - mac: mac address
    - ip_v4: ipv4 address
    - ip_v6: ipv6 address
    - port_type: 'VSI' or 'Port'
    - vsi_id: vsi id, which is used to identify itself and create rules
    """

    def __init__(self, eth_name=None, mac=None, bdf=None, ipv4=None, ipv6=None, port_type='VSI', vsi_id=0, sut=None):
        self.eth_name = eth_name
        self.mac = mac
        self.bdf = bdf
        self.ip_v4 = ipv4
        self.ip_v6 = ipv6
        self.port_type = port_type
        self.vsi_id = vsi_id
        self._sut = sut

    @property
    def sut(self):
        return self._sut

    @abc.abstractmethod
    def execute_shell_cmd(self, cmd, timeout=30, cwd=None):
        pass

    def execute_shell_cmd_async(self, cmd, timeout=5, cwd=None, powershell=False):
        raise NotImplementedError

    def is_alive(self):
        out = None
        try:
            out = self.execute_shell_cmd('echo alive', 10)[0] == 0
        except Exception:
            pass
        return out

    def get_ip(self, net_interface, mode='ipv4'):
        """
        Acquire IP address
        :param net_interface: Ethernet interface name
        :param mode: 'ipv4' or 'ipv6'
        :return: True if IP exists
        :raise RuntimeError if get unsupported mode.
        """
        _, ifcfg, _ = self.execute_shell_cmd(f"ifconfig {net_interface}")
        if mode == 'ipv4':
            try:
                self.ip_v4 = re.search(r'((2[0-5]|1[0-9]|[0-9])?[0-9]\.){3}((2[0-5]|1[0-9]|[0-9])?[0-9])', ifcfg,
                                       re.I).group()
            except AttributeError:
                return False
        elif mode == 'ipv6':
            ip6_regex = r'\s*((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|' \
                        r'(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|' \
                        r'((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|' \
                        r'(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:' \
                        r'((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|' \
                        r'(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:' \
                        r'((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|' \
                        r'(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:' \
                        r'((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|' \
                        r'(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:' \
                        r'((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|' \
                        r'(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:' \
                        r'((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|' \
                        r'(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:' \
                        r'((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?\s*'
            ip_v6_list = re.findall(ip6_regex, ifcfg, re.I)
            if not ip_v6_list:
                return False
            for item in ip_v6_list:
                if not item[0].startswith('fe80'):
                    self.ip_v6 = item[0]
                    break
        else:
            raise RuntimeError("Unsupported Mode")
        return True

    def get_mac(self):
        """
        Acquire mac address
        :return: True if mac exists
        """
        _, out, _ = self.execute_shell_cmd(f'ifconfig {self.eth_name}')
        pat = r'[A-Fa-f0-9]{2}'
        try:
            self.mac = re.search(fr'{pat}:{pat}:{pat}:{pat}:{pat}:{pat}', out, re.I).group()
            return True
        except AttributeError:
            return False

    def get_ether_name(self, nic_id, nic_port_index):
        """
        Acquire ethernet name
        :param nic_id: NIC specification ID or name
        :param nic_port_index: if equals to -1, will get all available results according to nic_id
        :return: False if don't exist
        """
        if not self.get_bdf(nic_id, nic_port_index):
            logger.debug(f"couldn't find device according to {nic_id}")
            return False
        _, ether_name, std_err = self.execute_shell_cmd(f'ls /sys/bus/pci/devices/{self.bdf}/net')
        if ether_name == '':
            return False
        ether_list = ether_name.split()
        self.eth_name = ether_list[nic_port_index]
        return True

    def get_bdf(self, nic_id, nic_port_index):
        """
        Acquire bdf
        :param nic_id: NIC specification ID or name
        :param nic_port_index: if equals to -1, will get all available results according to nic_id
        :return: False if don't exist
        """
        try:
            _, nics, _ = self.execute_shell_cmd(f'lspci | grep -i {nic_id}')
            nics = str(nics)[:-1].split('\n')
            nic_info = nics[nic_port_index].strip().split(' ')
            self.bdf = nic_info[0]
            if len(self.bdf.split(":")) == 2:
                self.bdf = "0000:" + self.bdf
            return True
        except Exception:
            return False

    def ping_to_dst(self, dst_ip, count=20, mode='ipv4'):
        """
        Ping to specific IP address
        :param dst_ip: destination IP address to ping to
        :param count: times of ping test
        :param mode: 'ipv4' or 'ipv6'
        :return: Bool, True if ping is successfully, and vase vice
        """
        src_ip = self.ip_v4 if mode == 'ipv4' else self.ip_v6
        _, out, _ = self.execute_shell_cmd(f'ping -{mode[-1]} -c {count} -I {src_ip} {dst_ip}', timeout=10*count)
        loss_data = re.search(r'(\d+)% packet loss', out).group(1)
        # if loss percentage larger than 20%, check fail
        if int(loss_data) > 20:
            return False
        else:
            return True

    @abc.abstractmethod
    def copy_local_file_to_sut(self, src_path, dst_path):
        pass

    @abc.abstractmethod
    def copy_file_from_sut_to_local(self, src_path, dst_path):
        pass


class XHC(GenericComponent):
    def __init__(self, sut):
        super(XHC, self).__init__(vsi_id=1, sut=sut)

    def execute_shell_cmd(self, cmd, timeout=30, cwd=None):
        return self._sut.execute_shell_cmd(cmd, timeout, cwd)

    def execute_shell_cmd_async(self, cmd, timeout=5, cwd=None, powershell=False):
        return self._sut.execute_shell_cmd_async(cmd, timeout, cwd, powershell)

    def __str__(self):
        return 'XHC'

    def copy_local_file_to_sut(self, src_path, dst_path):
        if src_path != dst_path:
            self.execute_shell_cmd(f'cp {src_path} {dst_path}')

    def copy_file_from_sut_to_local(self, src_path, dst_path):
        if src_path != dst_path:
            self.execute_shell_cmd(f'cp {src_path} {dst_path}')


class IMC(GenericComponent):
    def __init__(self, sut):
        super(IMC, self).__init__(eth_name='eth2', vsi_id=6, sut=sut)

    def execute_shell_cmd(self, cmd, timeout=30, cwd='/home/root'):
        """
        Execute command on IMC console.
        :param cmd: command to be executed
        :param timeout: execution timeout
        :param cwd: optional, current working directory on remote os
        :return (return_code, stdout, stderr) if executed
            None if failed to get response from remote OS
        """
        res = self._sut.execute_shell_cmd(r"ssh -q root@100.0.0.100 -o 'StrictHostKeyChecking=no' "
                                          "-o 'UserKnownHostsFile /dev/null' \"cd {} && {}\""
                                          .format(cwd, cmd), timeout)
        if not res:
            raise Exception("Execute IMC command fail.")
        return res

    def execute_shell_cmd_async(self, cmd, timeout=5, cwd=None, powershell=False):
        return self._sut.execute_shell_cmd(r"ssh -q root@100.0.0.100 -o 'StrictHostKeyChecking=no' "
                                           "-o 'UserKnownHostsFile /dev/null' \"cd {} && nohup {} >/dev/null 2>&1 &\""
                                           .format(cwd, cmd), timeout)

    def copy_local_file_to_sut(self, src_path, dst_path):
        self._sut.execute_shell_cmd("scp -o 'StrictHostKeyChecking=no' root@100.0.0.100:{} {}"
                                    .format(src_path, dst_path), timeout=60)

    def copy_file_from_sut_to_local(self, src_path, dst_path):
        self._sut.execute_shell_cmd("scp -o 'StrictHostKeyChecking=no' {} root@100.0.0.100:{}"
                                    .format(src_path, dst_path), timeout=60)

    def __str__(self):
        return 'IMC'


class ACC(GenericComponent):
    def __init__(self, imc):
        super(ACC, self).__init__(eth_name='enp0s1f0', vsi_id=5)
        self.__imc = imc

    def execute_shell_cmd(self, cmd, timeout=30, cwd='/home/root'):
        res = self.__imc.execute_shell_cmd(r"ssh -q root@192.168.96.2 -o 'StrictHostKeyChecking=no' "
                                           "-o 'UserKnownHostsFile /dev/null' 'cd {} && {}'"
                                           .format(cwd, cmd), timeout)
        if not res:
            raise Exception("Execute ACC command fail.")
        return res

    def execute_shell_cmd_async(self, cmd, timeout=30, cwd='/home/root', powershell=False):
        return self.__imc.execute_shell_cmd(r"ssh -q root@192.168.96.2 -o 'StrictHostKeyChecking=no' "
                                            "-o 'UserKnownHostsFile /dev/null' 'cd {} && nohup {} >/dev/null 2>&1 &'"
                                            .format(cwd, cmd), timeout)

    def __str__(self):
        return 'ACC'

    def copy_local_file_to_sut(self, src_path, dst_path):
        self.__imc.execute_shell_cmd("scp -o 'StrictHostKeyChecking=no' root@192.168.96.2:{} {}"
                                     .format(src_path, dst_path), timeout=60)

    def copy_file_from_sut_to_local(self, src_path, dst_path):
        self.__imc.execute_shell_cmd("scp -o 'StrictHostKeyChecking=no' {} root@192.168.96.2:{}"
                                     .format(src_path, dst_path), timeout=60)


class VM(GenericComponent):
    """
    A VM object contains below properties
    - name: the name of VM
    - ip: the IP address given by KVM through NAT method
    - vf: the VF assigned to VM
    """

    def __init__(self, sut, vm_name, host_bdf, mac, vsi_id):
        super(VM, self).__init__(sut=sut, mac=mac, vsi_id=vsi_id)
        self.__host_bdf = host_bdf
        self.__name = vm_name
        self.__ip = None
        self.__xml_file = {}

    @property
    def ip(self):
        return self.__ip

    @property
    def name(self):
        return self.__name

    @property
    def vf_host_bdf(self):
        return self.__host_bdf

    def __str__(self):
        return self.name

    def create(self, mem_sz=2048, cpu_num=2, hugepage=False):
        qemu_cmd = "qemu-img create -f qcow2 -F qcow2 -b {}/centos8_vm.qcow2 " \
                   "/var/lib/libvirt/images/{}.qcow2".format(SUT_TOOLS_LINUX_MEV, self.__name)
        ret, _, _ = self._sut.execute_shell_cmd(qemu_cmd)

        install_cmd = "virt-install --name {} --memory {} --vcpus {} " \
                      "--disk /var/lib/libvirt/images/{}.qcow2,bus=virtio " \
                      "--import --noautoconsole --os-variant centos8".format(self.__name, mem_sz,
                                                                             cpu_num, self.__name)
        if hugepage:
            install_cmd += ' --boot menu=on --memorybacking hugepages=yes'
        ret, _, _ = self._sut.execute_shell_cmd(install_cmd)
        Case.expect("create vm successfully", ret == 0)

    def shutdown(self):
        self._sut.execute_shell_cmd(f"virsh destroy {self.__name}")

    def copy_local_file_to_sut(self, src_path, dst_path):
        self._sut.execute_shell_cmd("sshpass -p password scp -o 'StrictHostKeyChecking=no' root@{}:{} {}"
                                    .format(self.__ip, src_path, dst_path), timeout=60)

    def copy_file_from_sut_to_local(self, src_path, dst_path):
        self._sut.execute_shell_cmd("sshpass -p password scp -o 'StrictHostKeyChecking=no' {} root@{}:{}"
                                    .format(src_path, self.__ip, dst_path), timeout=60)

    def attach_device(self, bdf):
        """
            Create a virtual pci device with specified vf and attach it onto the vm
            """
        vf_xml = self.__create_sriov_xml(bdf)

        _, state, _ = self._sut.execute_shell_cmd('virsh domstate {}'.format(self.__name))
        if state.strip() != 'running':
            logger.debug("Target vm is down, booting now")
            self._sut.execute_shell_cmd("virsh start {}".format(self.__name))

        self._sut.execute_shell_cmd("virsh attach-device {} {} --live --config".format(self.__name, vf_xml))
        self.__xml_file[bdf] = vf_xml
        # Case.expect("attach vf successfully", ret == 0)

    def detach_device(self, bdf):
        self._sut.execute_shell_cmd("virsh detach-device {} {} --live --config".format(self.__name, self.__xml_file[bdf]))

    def __create_sriov_xml(self, bdf):
        """
            Create a pci device xml to attach, return the path of created xml file
            """
        domain = bdf[0:4]
        bus = bdf[5:7]
        slot = bdf[8:10]
        function = bdf[11:]
        xml_path = f"{HOST_TMP_MEV}\\pci_device.xml"

        conf = elementTree.parse(xml_path)
        root = conf.getroot()
        addr = root.find('source/address')
        addr.attrib['domain'] = f'0x{domain}'
        addr.attrib['bus'] = f'0x{bus}'
        addr.attrib['slot'] = f'0x{slot}'
        addr.attrib['function'] = f'0x{function}'
        xml_tmp = f'{HOST_TMP_MEV}\\xml_tmp'
        if not os.path.exists(xml_tmp):
            os.makedirs(xml_tmp)
        vf_file = f'{xml_tmp}\\pci_device_{self.__name}_{bus}_{slot}_{function}.xml'
        conf.write(vf_file)
        self._sut.upload_to_remote(vf_file, f"{SUT_TOOLS_LINUX_MEV}/xml_tmp")
        execute_host_cmd(f'del /s /q {vf_file}')
        return f'{SUT_TOOLS_LINUX_MEV}/xml_tmp/pci_device_{self.__name}_{bus}_{slot}_{function}.xml'

    def get_vm_ip(self):
        """
        Get the specified vm ip, including default and attached ones
        """
        _, ifcfg, _ = self._sut.execute_shell_cmd("ifconfig virbr0")
        sut_ip = re.search(r'((2[0-5]|1[0-9]|[0-9])?[0-9]\.){3}((2[0-5]|1[0-9]|[0-9])?[0-9])', ifcfg, re.I).group()
        sub_ip = ".".join(sut_ip.split(".")[:1]) + "."

        ret = 1
        while ret:
            ret, out, _ = self._sut.execute_shell_cmd("virsh -q domifaddr {} --source agent | grep {}"
                                                      .format(self.__name, sub_ip))
            time.sleep(5)
        self.__ip = re.search(r'((2[0-5]|1[0-9]|[0-9])?[0-9]\.){3}((2[0-5]|1[0-9]|[0-9])?[0-9])', out, re.I).group()

    def delete_vm(self):
        self._sut.execute_shell_cmd('virsh destroy {}'.format(self.__name))
        ret, _, _ = self._sut.execute_shell_cmd(
            'virsh undefine --domain {} --remove-all-storage'.format(self.__name))
        if ret != 0:
            raise RuntimeError('delete vm fail')

    def execute_shell_cmd(self, cmd, timeout=30, cwd='/root'):
        """
        execute cmd for VM
        :param cmd: command to be executed
        :param timeout: execution timeout
        :param cwd: position for execution
        :return (return_code, stdout, stderr) if executed
            None if failed to get response from remote OS
        """
        return self._sut.execute_shell_cmd(r"sshpass -p password ssh -q root@{} -o 'StrictHostKeyChecking=no' "
                                           "-o 'UserKnownHostsFile /dev/null' \"cd {} && {}\""
                                           .format(self.__ip, cwd, cmd), timeout)

    def execute_shell_cmd_async(self, cmd, timeout=5, cwd=None, powershell=False):
        if not cwd:
            cwd = '~'
        return self._sut.execute_shell_cmd(r"sshpass -p password ssh -q root@{} -o 'StrictHostKeyChecking=no'"
                                           r" -o 'UserKnownHostsFile /dev/null' "
                                           "\"cd {} && screen -dmS fabric bash -c '{}'\""
                                           .format(self.__ip, cwd, cmd), timeout)

    def update_vf_info(self):
        """
        update VF information of bdf, eth_name, ip_v4, ip_v6 if exist
        """
        if not self.bdf:
            self.get_bdf(r"'Function'", 0)
        if not self.eth_name:
            self.get_ether_name(r"'Function'", 0)
        if not self.ip_v4:
            self.get_ip(self.eth_name)
        if not self.ip_v6:
            self.get_ip(self.eth_name, mode='ipv6')


class Peer(GenericComponent):
    """
    A Peer object is considered as a Component as well, it could be IMC/ACC/XHC/VM or even a common SUT
    connected with current machine, the difference is its port_type
    """
    def __init__(self, name, mac, ipv4=None, ipv6=None, eth_name='eth0'):
        super(Peer, self).__init__(eth_name=eth_name, mac=mac, ipv4=ipv4, ipv6=ipv6, port_type='Port', vsi_id=0)
        self.name = name

    def __str__(self):
        return f'Peer_{self.name}'

    @classmethod
    def from_comp(cls, comp: GenericComponent):
        return cls(str(comp), comp.mac, comp.ip_v4, comp.ip_v6, comp.eth_name)

    def execute_shell_cmd(self, cmd, timeout=30, cwd=None):
        raise NotImplementedError

    def execute_shell_cmd_async(self, cmd, timeout=5, cwd=None, powershell=False):
        raise NotImplementedError

    def copy_local_file_to_sut(self, src_path, dst_path):
        raise NotImplementedError

    def copy_file_from_sut_to_local(self, src_path, dst_path):
        raise NotImplementedError

