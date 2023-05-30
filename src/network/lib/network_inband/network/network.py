#!/usr/bin/env python
import set_toolkit_src_root
import time
from functools import partial
import re
import sys

from src.network.inband.common.ssh import *
from src.network.inband.common.util import *
from src.network.inband.network.config import *


class Network:
    exec_local = exec_local
    exec_remote = partial(exec_remote, hostname=NicClient.ipaddr, username=NicClient.username,
                          password=NicClient.password)
    print(NicClient.ipaddr)
    upload_to_remote = partial(upload_to_remote, hostname=NicClient.ipaddr, username=NicClient.username,
                               password=NicClient.password)
    download_to_local = partial(download_to_local, hostname=NicClient.ipaddr, username=NicClient.username,
                                password=NicClient.password)

    @classmethod
    def _parse_conn(cls, conn):
        """ Parse connections into a list """
        conn = conn.split(',')
        while '' in conn:
            conn.remove('')
        conn = [c.strip() for c in conn]
        return conn

    @classmethod
    def _get_nic_port(cls, conn, index=1):
        """
        :param conn:
        :param index: The index=1 means 1st workable nic port
        :return:
        """

        def __get_linux_port(role, id):
            _exec = Network.exec_local if role == 'server' else Network.exec_remote

            rs = _exec(f'lspci | grep -i {id}')
            out = rs.stdout[:-1].split('\n')

            ns = []
            for np in out:
                # Match working port
                bdf = np.split(' ')[0]
                rs = _exec(f'ls /sys/bus/pci/devices/0000:{bdf}/net')
                # rs2 = _exec(f'ifconfig {rs.stdout}')
                if rs.stdout != '':
                    # if re.search(f'{rs.stdout}:.*running', rs2.stdout):
                    ns.append(np)

            check_condition(len(ns) >= index)
            np = ns[index - 1].strip()
            bdf = np.split(' ')[0]

            rs = _exec(f'ls /sys/bus/pci/devices/0000:{bdf}/net')
            check_condition(rs.exitcode == 0)
            return rs.stdout.strip()

        def __get_windows_port(role, id):
            _exec = Network.exec_local if role == 'server' else Network.exec_remote

            rs = _exec('Get-NetAdapter', powershell=True)
            out = rs.stdout.split('\r')

            ns = []
            id = id.replace('\'', '')
            for np in out:
                # Match working port
                if id in np and 'Up' in np:
                    ns.append(np)

            check_condition(len(ns) >= index)
            np = ns[index - 1]
            np = np.split('  ')
            np = list(filter(None, np))
            return np[0].strip()

        server_port = ''
        client_port = ''

        nc = NicConnection(conn)
        sid = getattr(nc.server_nic, f'id_in_{NicServer.osname}')
        cid = getattr(nc.client_nic, f'id_in_{NicClient.osname}')

        if NicServer.osname in ['redhat', 'centos', 'sles']:
            server_port = __get_linux_port('server', sid)

        elif NicServer.osname in ['windows']:
            server_port = __get_windows_port('server', sid)
        else:
            raise RuntimeError(f'Not supported [server]\osname={NicServer.osname}')

        if NicClient.osname in ['redhat', 'centos', 'sles']:
            client_port = __get_linux_port('client', cid)
        elif NicClient.osname in ['windows']:
            client_port = __get_windows_port('client', cid)
        else:
            raise RuntimeError(f'Not supported [client]\osname={NicClient.osname}')

        return server_port, client_port

    @classmethod
    def _get_nic_mac(cls, conn, index=1):
        def __get_linux_mac(role, id):
            _exec = Network.exec_local if role == 'server' else Network.exec_remote

            rs = _exec(f'lspci | grep -i {id}')
            out = rs.stdout[:-1].split('\n')

            ns = []
            for np in out:
                # Match working port
                bdf = np.split(' ')[0]
                rs = _exec(f'ls /sys/bus/pci/devices/0000:{bdf}/net')
                # rs2 = _exec(f'ifconfig {rs.stdout}')
                if rs.stdout != '':
                    # if re.search(f'{rs.stdout}:.*running', rs2.stdout):
                    ns.append(np)

            check_condition(len(ns) >= index)
            np = ns[index - 1].strip()
            bdf = np.split(' ')[0]

            rs = _exec(f'ls /sys/bus/pci/devices/0000:{bdf}/net')
            out = str(rs.stdout).replace('\n', '')
            rs = _exec(f'ifconfig {out} | grep -i ether')
            check_condition(rs.exitcode == 0)
            return rs.stdout.strip().split(' ')[1]

        def __get_windows_mac(role, id):
            _exec = Network.exec_local if role == 'server' else Network.exec_remote

            rs = _exec('Get-NetAdapter', powershell=True)
            out = rs.stdout.split('\r')
            ns = []
            id = id.replace('\'', '')
            for np in out:
                # Match working port
                if f'{id}' in np and 'Up' in np:
                    ns.append(np)

            check_condition(len(ns) >= index)
            np = ns[index - 1]
            np = np.split('  ')
            np = list(filter(None, np))

            for mac in np:
                mac = mac.strip()
                if re.match('(\w\w-\w\w-\w\w-\w\w-\w\w-\w\w)', mac):
                    return mac

        server_mac = ''
        client_mac = ''

        nc = NicConnection(conn)
        sid = getattr(nc.server_nic, f'id_in_{NicServer.osname}')
        cid = getattr(nc.client_nic, f'id_in_{NicClient.osname}')

        if NicServer.osname in ['redhat', 'centos', 'sles']:
            server_mac = __get_linux_mac('server', sid)

        elif NicServer.osname in ['windows']:
            server_mac = __get_windows_mac('server', sid)
        else:
            raise RuntimeError(f'Not supported [server]\osname={NicServer.osname}')

        if NicClient.osname in ['redhat', 'centos', 'sles']:
            client_mac = __get_linux_mac('client', cid)
        elif NicClient.osname in ['windows']:
            client_mac = __get_windows_mac('client', cid)
        else:
            raise RuntimeError(f'Not supported [client]\osname={NicClient.osname}')

        return server_mac, client_mac

    @classmethod
    def _set_nic_ip(cls, conn):
        def __set_linux_ip(role, port, ip, v6):
            _exec = Network.exec_local if role == 'server' else Network.exec_remote

            rs = _exec(f'nmcli con modify {port} connection.autoconnect yes && '
                       f'nmcli con modify {port} {v6}.address {ip} &&'
                       f'nmcli con modify {port} {v6}.method manual &&'
                       f'nmcli con up {port}')
            check_condition(rs.exitcode == 0)

        def __set_windows_ip(role, port, ip, v6):
            _exec = Network.exec_local if role == 'server' else Network.exec_remote
            rs = _exec(f'netsh interface {v6} set address \"{port}\" static {ip}')
            check_condition(rs.exitcode == 0)

        def __get_linux_ip(role, port, v6):
            _exec = Network.exec_local if role == 'server' else Network.exec_remote
            _ipstr = f'{port}:.*inet (.*) netmask' if not v6 else f'{port}:.*inet6 (.*) prefixlen'

            rs = _exec(f'ifconfig {port}')
            p = re.search(_ipstr, rs.stdout, re.I | re.DOTALL)
            check_condition(p, f'not find ip address with: {port}')
            return p.group(1).strip()

        def __get_windows_ip(role, port, v6):
            _exec = Network.exec_local if role == 'server' else Network.exec_remote
            _cmd = f'netsh interface {v6} show address "{port}"' if not v6 else f'netsh interface {v6} show address "{port}"'
            _ipstr = f'ip address: (.*)' if not v6 else f'address (.*) Parameters'

            rs = _exec(_cmd)
            p = re.search(_ipstr, rs.stdout, re.I)
            check_condition(p, f'not find ip address with: {port}')

            return p.group(1).strip().split('%')[0] if v6 else p.group(1).strip()

        nc = NicConnection(conn)
        sport = nc.server_port
        cport = nc.client_port
        sv6 = 'ipv6' if ':' in nc.server_ip else 'ipv4'
        cv6 = 'ipv6' if ':' in nc.client_ip else 'ipv4'
        sip = nc.server_ip + '/48' if sv6 == 'ipv6' else nc.server_ip + '/24'
        cip = nc.client_ip + '/48' if cv6 == 'ipv6' else nc.client_ip + '/24'
        dhcp = NicServer.bootproto == 'dhcp'

        if NicServer.osname in ['redhat', 'centos', 'sles']:
            if not dhcp:
                __set_linux_ip('server', sport, sip, sv6)
            else:
                nc.server_ip = __get_linux_ip('server', sport, sv6)
        elif NicServer.osname in ['windows']:
            if not dhcp:
                __set_windows_ip('server', sport, sip, sv6)
            else:
                nc.server_ip = __get_windows_ip('server', sport, sv6)
        else:
            raise RuntimeError(f'Not supported [server]\osname={NicServer.osname}')

        if NicClient.osname in ['redhat', 'centos', 'sles']:
            if not dhcp:
                __set_linux_ip('client', cport, cip, cv6)
            else:
                nc.client_ip = __get_linux_ip('client', cport, sv6)
        elif NicClient.osname in ['windows']:
            if not dhcp:
                __set_windows_ip('client', cport, cip, cv6)
            else:
                nc.client_ip = __get_windows_ip('client', cport, cv6)
        else:
            raise RuntimeError(f'Not supported [client]\osname={NicClient.osname}')

        # Save runtime attributes for using by subsequent steps
        CFGParser.write_cfg('_runtime_attribute', f'{conn}.server_ip', nc.server_ip, RUNTIME)
        CFGParser.write_cfg('_runtime_attribute', f'{conn}.client_ip', nc.client_ip, RUNTIME)

    @classmethod
    def _pad_attribute(cls, *conn):
        """
        Get nic attrs in os, and fill in NicConnection(conn).server_nic.attr & NicConnection(conn).server_nic.attr
        Also, save it to _runtime_attributes
        """
        # Record if more `workable` conns on the same nic
        # If so, set ips based on the appearance sequence in os
        more_server_nic_conns = {}
        more_client_nic_conns = {}
        for c in conn:
            nc = NicConnection(c)

            sid = getattr(nc.server_nic, f'id_in_{NicServer.osname}')
            if sid not in more_server_nic_conns.keys():
                more_server_nic_conns[sid] = 1
            else:
                more_server_nic_conns[sid] += 1

            cid = getattr(nc.client_nic, f'id_in_{NicClient.osname}')
            if cid not in more_client_nic_conns.keys():
                more_client_nic_conns[cid] = 1
            else:
                more_client_nic_conns[cid] += 1

            nc.server_nic.port = cls._get_nic_port(c, index=more_server_nic_conns[sid])[0]
            nc.client_nic.port = cls._get_nic_port(c, index=more_server_nic_conns[sid])[1]
            nc.server_nic.mac = cls._get_nic_mac(c, index=more_client_nic_conns[sid])[0]
            nc.client_nic.mac = cls._get_nic_mac(c, index=more_client_nic_conns[sid])[1]

            # Save runtime attributes for using by subsequent steps
            CFGParser.write_cfg('_runtime_attribute', f'{c}.server_port', nc.server_nic.port, RUNTIME)
            CFGParser.write_cfg('_runtime_attribute', f'{c}.client_port', nc.client_nic.port, RUNTIME)
            CFGParser.write_cfg('_runtime_attribute', f'{c}.server_mac', nc.server_nic.mac, RUNTIME)
            CFGParser.write_cfg('_runtime_attribute', f'{c}.client_mac', nc.client_nic.mac, RUNTIME)

    @classmethod
    def _assign_ip(cls, *conn):
        """
        If: NicServer.bootproto is dhcp, then replace NicConnection(conn).server_ip & client_ip in memory with dhcp ip
        Else: set nic port ip in os with configured NicConnection(conn).server_ip & client_ip
        """
        for c in conn:
            cls._set_nic_ip(c)


class Validation:
    __win_sutos = (os.name == 'nt')
    step = None
    # Initialize with _runtime_attributes
    conn = CFGParser.read_cfg('_runtime_attribute', 'conn', RUNTIME)
    conn = Network._parse_conn(conn)
    # Most tests only use 1 network connection, let it default one
    default_conn = conn[0]
    nc = NicConnection(default_conn)

    @classmethod
    def prepare_server_client_connection(cls):
        """ Prepare step after system boot to os """
        cls.conn = parse_parameter('conn')
        cls.conn = Network._parse_conn(cls.conn)
        check_condition(cls.conn, 'ERROR: --conn=xxx parameter is required, and not empty')
        cls.default_conn = cls.conn[0]
        cls.nc = NicConnection(cls.default_conn)
        Network._pad_attribute(*cls.conn)
        # Network._pad_attribute(cls.conn)

    @classmethod
    def prepare_server_client_ipaddr(cls):
        """ Prepare step after system boot to os """
        Network._assign_ip(*cls.conn)

    @classmethod
    def test_server_client_disconnect(cls):
        if not cls.__win_sutos:
            rs = Network.exec_local(f'ping -c 5 {cls.nc.client_ip}')
            check_output('100% packet loss', rs.stdout + rs.stderr, 'network connection is live', minimal_matches=1)
        else:
            rs = Network.exec_local(f'ping -n 5 {cls.nc.client_ip}')
            check_output('100% loss', rs.stdout + rs.stderr, 'network connection is live', minimal_matches=1)

    @classmethod
    def test_server_client_connect(cls):
        """ Support: number(--conn=) > 1 """
        for c in cls.conn:
            nc = NicConnection(c)
            if not cls.__win_sutos:
                rs = Network.exec_local(f'ping -c 5 {nc.client_ip}')
                check_condition(rs.exitcode == 0, 'connection is lost')
            else:
                rs = Network.exec_local(f'ping -n 5 {nc.client_ip}')
                check_condition(rs.exitcode == 0, 'connection is lost')

    @classmethod
    def __calculate_bandwidth_to_gbits(cls, *outputs, role):
        bandwidth = 0
        for output in outputs:
            log.info(output)
            for line in output.split('\n'):
                if role in line:
                    data = line.split('/sec')[0].split()
                    rate = float(data[-2])
                    unit = data[-1]
                    if unit == 'Mbits':
                        rate = rate / 1000.0
                    bandwidth += rate
        return bandwidth

    @classmethod
    def test_client_start_iperf_server(cls):
        """ Iperf3 throughput with 4 processes """
        if not cls.__win_sutos:
            Network.exec_remote(f'iperf3 -s -p 5101 -D')
            Network.exec_remote(f'iperf3 -s -p 5102 -D')
            Network.exec_remote(f'iperf3 -s -p 5103 -D')
            Network.exec_remote(f'iperf3 -s -p 5104 -D')
        else:
            Network.exec_remote(f'C:\\BKCPkg\\domains\\network\\iperf3\\iperf3.exe -s --one-off -p 5101')
            Network.exec_remote(f'C:\\BKCPkg\\domains\\network\\iperf3\\iperf3.exe -s --one-off -p 5102')
            Network.exec_remote(f'C:\\BKCPkg\\domains\\network\\iperf3\\iperf3.exe -s --one-off -p 5103')
            Network.exec_remote(f'C:\\BKCPkg\\domains\\network\\iperf3\\iperf3.exe -s --one-off -p 5104')

    @classmethod
    def test_server_work_as_iperf_sender(cls):
        for c in cls.conn:
            nc = NicConnection(c)
            if not cls.__win_sutos:
                Network.exec_local(f'iperf3 -c {nc.client_ip} -p 5101 -t 100 > sender1.log', waitfor_complete=False)
                Network.exec_local(f'iperf3 -c {nc.client_ip} -p 5102 -t 100 > sender2.log', waitfor_complete=False)
                Network.exec_local(f'iperf3 -c {nc.client_ip} -p 5103 -t 100 > sender3.log', waitfor_complete=False)
                Network.exec_local(f'iperf3 -c {nc.client_ip} -p 5104 -t 100 > sender4.log', waitfor_complete=False)
                time.sleep(40)

                bandwidth = cls.__calculate_bandwidth_to_gbits(open('sender1.log').read(),
                                                               open('sender2.log').read(),
                                                               open('sender3.log').read(),
                                                               open('sender4.log').read(), role='sender')

                print(bandwidth)
                print(cls.nc.server_nic.rate)
                bandwidth = bandwidth / 4
                check_condition(bandwidth > cls.nc.server_nic.rate * 0.9)
            else:
                Network.exec_local(
                    f'C:\\BKCPkg\\domains\\network\\iperf3\\iperf3.exe -s {nc.client_ip} -p 5101 -t 100 > C:\\BKCPkg\\domains\\network\\iperf3\\sender5.log',
                    waitfor_complete=False)
                Network.exec_local(
                    f'C:\\BKCPkg\\domains\\network\\iperf3\\iperf3.exe -s {nc.client_ip} -p 5102 -t 100 > C:\\BKCPkg\\domains\\network\\iperf3\\sender6.log',
                    waitfor_complete=False)
                Network.exec_local(
                    f'C:\\BKCPkg\\domains\\network\\iperf3\\iperf3.exe -s {nc.client_ip} -p 5103 -t 100 > C:\\BKCPkg\\domains\\network\\iperf3\\sender7.log',
                    waitfor_complete=False)
                Network.exec_local(
                    f'C:\\BKCPkg\\domains\\network\\iperf3\\iperf3.exe -s {nc.client_ip} -p 5104 -t 100 > C:\\BKCPkg\\domains\\network\\iperf3\\sender8.log',
                    waitfor_complete=False)
                time.sleep(110)
                bandwidth = cls.__calculate_bandwidth_to_gbits(
                    open('C:\\BKCPkg\\domains\\network\\iperf3\\sender5.log').read(),
                    open('C:\\BKCPkg\\domains\\network\\iperf3\\sender6.log').read(),
                    open('C:\\BKCPkg\\domains\\network\\iperf3\\sender7.log').read(),
                    open('C:\\BKCPkg\\domains\\network\\iperf3\\sender8.log').read(), role='sender')
                check_condition(bandwidth > cls.nc.server_nic.rate * 0.9)

    @classmethod
    def test_server_work_as_iperf_receiver(cls):
        for c in cls.conn:
            nc = NicConnection(c)
            if not cls.__win_sutos:
                Network.exec_local(f'iperf3 -c {nc.client_ip} -p 5101 -t 100 -R > receiver1.log',
                                   waitfor_complete=False)
                Network.exec_local(f'iperf3 -c {nc.client_ip} -p 5102 -t 100 -R > receiver2.log',
                                   waitfor_complete=False)
                Network.exec_local(f'iperf3 -c {nc.client_ip} -p 5103 -t 100 -R > receiver3.log',
                                   waitfor_complete=False)
                Network.exec_local(f'iperf3 -c {nc.client_ip} -p 5104 -t 100 -R > receiver4.log',
                                   waitfor_complete=False)
                time.sleep(40)

                bandwidth = cls.__calculate_bandwidth_to_gbits(open('receiver1.log').read(),
                                                               open('receiver2.log').read(),
                                                               open('receiver3.log').read(),
                                                               open('receiver4.log').read(), role='receiver')
                print(bandwidth)
                print(cls.nc.server_nic.rate)
                bandwidth = bandwidth / 4
                check_condition(bandwidth > cls.nc.server_nic.rate * 0.9)
            else:
                Network.exec_local(
                    f'C:\\BKCPkg\\domains\\network\\iperf3\\iperf3.exe -c {nc.client_ip} -p 5101 -t 100 -R > receiver1.log',
                    waitfor_complete=False)
                Network.exec_local(
                    f'C:\\BKCPkg\\domains\\network\\iperf3\\iperf3.exe -c {nc.client_ip} -p 5102 -t 100 -R > receiver2.log',
                    waitfor_complete=False)
                Network.exec_local(
                    f'C:\\BKCPkg\\domains\\network\\iperf3\\iperf3.exe -c {nc.client_ip} -p 5103 -t 100 -R > receiver3.log',
                    waitfor_complete=False)
                Network.exec_local(
                    f'C:\\BKCPkg\\domains\\network\\iperf3\\iperf3.exe -c {nc.client_ip} -p 5104 -t 100 -R > receiver4.log',
                    waitfor_complete=False)

                time.sleep(110)

                bandwidth = cls.__calculate_bandwidth_to_gbits(open('receiver1.log').read(),
                                                               open('receiver2.log').read(),
                                                               open('receiver3.log').read(),
                                                               open('receiver4.log').read(), role='receiver')
                check_condition(bandwidth > cls.nc.server_nic.rate * 0.9)

    @classmethod
    def test_server_client_cleanup_iperf(cls):
        if cls.__win_sutos:
            Network.exec_local(f'tasklist /FI \"IMAGENAME eq iperf3.exe\"')
            Network.exec_local(f'taskkill /F /IM iperf3.exe')
        else:
            Network.exec_local(f'kill -9 $(pidof iperf3)')

        if NicClient.osname == 'windows':
            Network.exec_local(f'tasklist /FI \"IMAGENAME eq iperf3.exe\"')
            Network.exec_remote(f'taskkill /F /IM iperf3.exe')
        else:
            Network.exec_remote(f'kill -9 $(pidof iperf3)')

    @classmethod
    def test_server_client_io_stress(cls):
        raise NotImplemented

    @classmethod
    def test_server_connectivity_enable_disable(cls):
        if not cls.__win_sutos:
            Network.exec_local(f'nmcli device disconnect {cls.nc.server_port}')
            cls.test_server_client_disconnect()
            Network.exec_local(f'nmcli device connect {cls.nc.server_port}')
            cls.test_server_client_connect()
        else:
            print(f'Disable-NetAdapter -Name "{cls.nc.server_port}" -Confirm:$False')
            exec_local(f'Disable-NetAdapter -Name "{cls.nc.server_port}" -Confirm:$False', powershell=True)
            cls.test_server_client_disconnect()
            exec_local(f'Enable-NetAdapter -Name "{cls.nc.server_port}" -Confirm:$False', powershell=True)
            cls.test_server_client_connect()

    @classmethod
    def test_server_client_bonding(cls):
        raise NotImplemented

    @classmethod
    def test_server_enable_windows_sriov(cls):
        Network.exec_local(
            f'Set-NetAdapterAdvancedProperty -Name "{cls.nc.server_port}" -DisplayName "SR-IOV" -DisplayValue "Enabled"',
            powershell=True)

    @classmethod
    def test_server_new_windows_vm(cls):
        Network.exec_local(f'Enable-WindowsOptionalFeature -Online -FeatureName Microsoft-Hyper-V -All -NoRestart',
                           powershell=True)
        Network.exec_local(f'Install-WindowsFeature -Name RSAT-Hyper-V-Tools', powershell=True)
        Network.exec_local(
            f'powershell.exe New-VM -Name vm1 -MemoryStartupBytes 4GB -VHDPath C:\BKCPkg\domain\network\win.vhdx',
            powershell=True)

    @classmethod
    def test_server_new_windows_vswitch(cls):
        Network.exec_local(f'New-VMSwitch vs1 -NetAdapterName "{cls.nc.server_port}" -EnableIov 1', powershell=True)

    @classmethod
    def test_server_attach_windows_vswitch_to_vm(cls):
        Network.exec_local(f'Add-VMNetworkAdapter -VMName vm1 -Name test-vs  -SwitchName vs1', powershell=True)

    @classmethod
    def test_server_check_windows_vm_nic(cls):
        cmd = '$account = "administrator" ; ' \
              '$password = "intel_123" ; ' \
              '$secpwd = convertTo-secureString $password -asplaintext -force ; ' \
              '$cred = new-object System.Management.Automation.PSCredential -argumentlist $account,$secpwd ; ' \
              'Invoke-Command -VMName vm1 -Credential $cred -ScriptBlock {(Get-NetAdapter -Name *).Name}'

        Network.exec_local(f'Start-VM -Name vm1', powershell=True)
        rs = Network.exec_local(f'{cmd}', powershell=True)
        check_output('Ethernet', rs.stdout, minimal_matches=2)
        Network.exec_local(f'Stop-VM -Name vm1 -Force ; Remove-VM -Name vm1 -Force ; Remove-VMSwitch -Name vs1 -Force')

    @classmethod
    def test_i_am_a_demo(cls):
        print(cls.default_conn)
        print(cls.nc.server_ip, cls.nc.server_nic.vendor)

    @classmethod
    def _init_context(cls, step):
        cls.step = step

    @classmethod
    def _run_step(cls):
        step = getattr(cls, cls.step, None)
        check_condition(step, f'--step={cls.step} is not supported now')
        return step()


def main():
    step = parse_parameter('step')
    Validation._init_context(step)
    Validation._run_step()


def help():
    r"""
    Module Usage::
    python network.py --step=prepare_server_client_connection --conn=col_conn_v4
    python network.py --step=prepare_server_client_ipaddr
    python network.py --step=test_server_client_connect

    Note::
    Essential <Prepare-Steps> that MUST be executed after booting to OS before all Steps:
        --step=prepare_server_client_connection --conn=col_conn_v4
        --step=prepare_assign_server_client_ipaddr
    """
    print(help.__doc__)


if __name__ == '__main__':
    help()
    main()







