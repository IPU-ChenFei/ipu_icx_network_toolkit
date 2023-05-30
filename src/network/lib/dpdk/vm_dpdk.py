import importlib
import re
import time
import traceback
import sys
import pexpect

from ppexpect import LinuxChildShell

DPDK_PATH = None

start_dpdk = '/home/BKCPkg/domains/network/start_dpdk.log'
sut_install_1 = '/home/BKCPkg/domains/network/install_1.log'
sut_network = '/home/BKCPkg/domains/network/'
tool_name = 'dpdk-21.05.tar.xz'
install_dpdk_path = '/home/dpdk-21.05'

install_path = '/home'
sut_path = '/home/BKCPkg/domains/network/dpdk-21.05.0.tar.xz'

yum_repo = '/home/BKCPkg/domains/network/intel-rhel82-yum.repo'

flag = 'flag.txt'


class LinuxChildShellLog(LinuxChildShell):
    def send(self, cmd):
        """
        Send cmd to child process and print cmd
        """
        print(f'Execute expect cmd >>> {cmd}')

        return self.child.sendline(cmd)

    def output(self):
        """
        Results from child process
        """
        res = self.child.before + self.child.after
        print(res.decode('utf-8'))
        return res


def __dynamic_import(module):
    """
    dynamic import
    :param module:module name
    :return: module
    """
    return importlib.import_module(module)


def __ssh_connect(ip):
    cs = None
    try:
        print(f'+++++ ssh {ip} +++++ ')
        cs = LinuxChildShellLog(f'ssh {ip}')
        a = cs.expect(['password:', 'The authenticity of host'])
        if a == 0:
            cs.send('password')
            cs.expect("]#")
            print('connect successful !')
        if a == 1:
            print('this ip will be added to know_host files!')
            cs.send('yes')
            cs.expect('password:')
            cs.send('password')
            cs.expect("]#")

    except pexpect.EOF:
        traceback.print_exc()
    return cs


def scp_file(args):
    print('=========================')
    print(type(args))
    print(args)
    ip = args[0]
    local_path = args[1]
    if len(args) <= 2:
        remote_path = install_path
    else:
        remote_path = args[2]
    cs = None
    try:
        print(f'+++++ scp -r {local_path} root@{ip}:{remote_path} +++++ ')
        cs = LinuxChildShellLog(f'scp -r {local_path} root@{ip}:{remote_path}')
        a = cs.expect(['password:', 'The authenticity of host'])
        if a == 0:
            cs.send('password')
            time.sleep(10)
            cs.output()
            print('connect successful !')
        if a == 1:
            print('this ip will be added to know_host files!')
            cs.send('yes')
            cs.expect('password:')
            cs.send('password')
            time.sleep(10)
            cs.output()
    except pexpect.EOF:
        traceback.print_exc()


        # cs.kill()


# def net_set(ip):
#     print(f'+++++ net_set +++++ ')
#     cs = __ssh_connect(f'{ip}')
#     # cs.send(f'cd {sut_network}')
#     # cs.send(f'cp -r {yum_repo} /etc/yum.repos.d/')
#     cs.expect(']#')
#     cs.send(f'echo "proxy=http://proxy-prc.intel.com:911" >> /etc/yum.conf')
#     cs.expect(']#')
#     cs.kill()
def rm_old_yum(args):
    global temp_file, cs
    try:
        ip = args[0]
        cs = __ssh_connect(f'{ip}')
        temp_file = open(f'{sut_install_1}', 'wb')
        cs.child.logfile = temp_file
        cs.send(f'rm -f /etc/yum.repos.d/*')
        cs.expect(']#')
    except pexpect.EOF:
        traceback.print_exc()
    finally:
        temp_file.close()
        cs.kill()

def install_dpdk(args):
    global temp_file, cs
    try:
        ip = args[0]

        print(f'+++++ start_vm +++++ ')
        cs = __ssh_connect(f'{ip}')
        temp_file = open(f'{sut_install_1}', 'wb')

        cs.child.logfile = temp_file

        # cs.send(f'mkdir -p {install_path}')
        # cs.expect(']#')
        cs.send(f'cd {install_path}')
        cs.expect(']#')
        cs.send(f'tar -xvf {tool_name}')
        time.sleep(2)
        cs.expect(']#')
        cs.send(f'echo "proxy=http://child-prc.intel.com:913" >> /etc/yum.conf')
        cs.send('yum -y install meson')
        time.sleep(200)
        cs.expect(']#')

        #cs.send('export https_proxy=proxy=http://child-prc.intel.com:913')
        #cs.expect(']#')
        cs.send('pip3 install pyelftools --proxy=http://child-prc.intel.com:913')
        time.sleep(60)
        cs.expect(']#')
        #cs.send('pip3 install pyelftools --proxy=http://child-prc.intel.com:913')
        #time.sleep(30)
        #cs.expect(']#')
        #cs.send('pip3 install pyelftools --proxy=http://child-prc.intel.com:913')
        #time.sleep(30)
        #cs.expect(']#')

        cs.send(f'cd {install_dpdk_path}')
        cs.send('meson -Denable_kmods=true -Dexamples=all build')
        time.sleep(30)
        cs.expect(']#')
        cs.output()
        cs.send(f'cd {install_dpdk_path}/build')
        cs.expect(']#')
        cs.send('yum install elfutils-libelf-devel')
        cs.send('y')
        time.sleep(30)
        cs.send('yum install libpcap*')
        time.sleep(30)
        cs.send('y')
        time.sleep(30)
        cs.send('ninja')
        time.sleep(600)
        cs.expect(']#')
        cs.send('ninja')
        cs.output()
        time.sleep(600)
        cs.expect(']#')
        cs.output()
        cs.send('ninja install')
        time.sleep(20)
        cs.expect(']#')
        cs.output()
        cs.send('ldconfig')
        time.sleep(10)
        cs.expect(']#')
        cs.output()

    except pexpect.EOF:
        traceback.print_exc()
    finally:
        temp_file.close()
        cs.kill()


def start_dpdk_vm(args):
    ip = args[0]
    # path = args[1]
    # path2 = args[2]

    print(f'+++++ start_vm +++++ ')
    cs = __ssh_connect(f'{ip}')
    temp_file = open(f'{start_dpdk}', 'wb')
    cs.child.logfile = temp_file

    cs.send('lspci | grep -i "Virtual f"')
    cs.expect(']#')
    res = cs.output().decode('utf-8')
    nics = str(res)[:-1].split('\n')
    en1 = nics[1].strip().split(' ')[0]
    en2 = nics[2].strip().split(' ')[0]
    print(en1, en2)

    cs.send(f'echo 8192 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages')
    cs.expect(']#')
    cs.send('mkdir -p /mnt/huge')
    cs.expect(']#')
    cs.send('mount -t hugetlbfs nodev')
    cs.expect(']#')
    cs.send('modprobe vfio-pci')
    cs.expect(']#')
    cs.send('echo 1 > /sys/module/vfio/parameters/enable_unsafe_noiommu_mode')
    cs.expect(']#')
    cs.send('echo "options vfio enable_unsafe_noiommu_mode=1" > /etc/modprobe.d/vfio-noiommu.conf')
    cs.expect(']#')
    cs.send(f'cd {install_dpdk_path}/usertools')
    cs.expect(']#')

    cs.send(f'./dpdk-devbind.py -b vfio-pci {en1} {en2}')
    time.sleep(20)
    cs.expect(']#')
    cs.send(f'cd {install_dpdk_path}/build/app')
    cs.expect(']#')

    cs.send(r"./dpdk-testpmd -c7 -n3 -- -i --nb-cores=2 --nb-ports=2 --total-num-mbufs=8192")
    time.sleep(5)
    cs.expect('testpmd>')

    cs.send("set fwd mac")
    cs.expect('testpmd>')
    time.sleep(2)
    cs.send('start tx_first')
    time.sleep(30)
    cs.expect('testpmd>')
    time.sleep(2)
    res = cs.output()
    print(res.decode('utf-8'))
    cs.send('show port stats all')
    cs.expect('testpmd>')
    time.sleep(10)
    cs.send('stop')
    cs.expect('testpmd>')
    cs.send('quit')
    res = cs.output()
    print(res.decode('utf-8'))
    cs.send(f'cd {install_dpdk_path}/usertools')
    cs.expect(']#')
    cs.send(f'dpdk-devbind.py --unbind {en1} {en2}')
    time.sleep(5)
    cs.expect(']#')
    cs.send(f'dpdk-devbind.py -b iavf {en1} {en2}')
    time.sleep(5)
    cs.expect(']#')
    print('close!!!')
    cs.kill()
    temp_file.close()
    # cs.send('dpdk-testpmd -c7 -n3 -- -i --nb-cores=2 --nb-ports=2 --total-num-mbufs=8192')
    # cs.expect('testpmd>')
    # cs.send('start tx_first')
    # print("Wait 30 minutes")
    # time.sleep(60)
    # cs.expect('testpmd>')
    # cs.send('stop')
    # cs.expect('testpmd>')
    # cs.output()
    # cs.kill()
    # temp_file.close()


if __name__ == '__main__':

    if len(sys.argv) >= 3:
        print(len(sys.argv))
        module = __dynamic_import('vm_dpdk')
        # python dpdk_expect.py method_name args path
        getattr(module, sys.argv[1])(sys.argv[2:])
    else:
        print('args value no correct')
        print('python dpdk_expect.py send_packet2 mac iface path')
        sys.exit()
