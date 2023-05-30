import datetime
import logging
import os
import pathlib
import subprocess
import re
import sys
import time
import getopt
import xml.etree.cElementTree as elementTree

import pexpect


def get_logger():
    log_obj = logging.getLogger()
    formatter = logging.Formatter("%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    log_obj.setLevel(logging.DEBUG)

    file_handle = logging.FileHandler("vm_sut_l_{}.log".format(datetime.datetime.now().strftime("%Y%m%dZ%Hh%Mm%Ss")))
    stream_handle = logging.StreamHandler()
    file_handle.setFormatter(formatter)
    stream_handle.setFormatter(formatter)

    log_obj.addHandler(file_handle)
    log_obj.addHandler(stream_handle)

    return log_obj


log = get_logger()


def exec_command(cmd):
    log.debug("Executing cmd: {}".format(cmd))
    ret = subprocess.Popen(cmd,
                           shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    out, err = ret.communicate()

    if err.decode() != "":
        log.error(f"Failed to execute cmd: {cmd}\n "
                  f"error message: {err.decode()}\n")
        # raise RuntimeError("Command execution failed! error: \n{}".format(err.decode()))
    return out.decode('utf-8')


KSTART_FILE_NAME = "case_tools/anaconda-ks.cfg"
SUT_ISO_IMAGE_LOCATION = "/home/BKCPkg/domains/network"
SUT_TOOL_PATH = r"/home/BKCPkg/domains/network"
PMEMBLK_LIB_PATH = f'{SUT_TOOL_PATH}/libpmemblk-1.6.1-1.el8.x86_64.rpm'
FIO_TOOL_PATH = f'{SUT_TOOL_PATH}/fio-3.7-3.el8.x86_64.rpm'


GET_NETWORK_INTERFACE_NAME_CMD = r"ip addr show | awk '/inet.*brd/{print $NF; exit}'"
CMD_TO_CHECK_NW_CONFIG_FILE = "cat {}/ifcfg-{}"
ADD_ADDR_NAME_TO_CONFIGURATION_FILE = r"sed -i.bak '$ a\{}' {}/ifcfg-{}"
GET_MAC_ADDRESS_CMD = "ip -o link | awk '$2 != \"lo:\" {{print $2, $(NF-2)}}' | grep {}"
BRIDGE_CONFIG_FILE_CONTENTS = ["DEVICE=br0", "TYPE=Bridge", "BOOTPROTO=dhcp", "ONBOOT=yes", "DELAY=0"]
ATTACH_DISK_CMD = "virsh attach-disk {} {}{} {} --cache none"
CREATE_DISK_CMD = "qemu-img create -f raw {} {}G"
SUSPEND_VM_CMD_LINUX = "virsh suspend {}"
RESUME_VM_CMD_LINUX = "virsh resume {}"
VM_NETWORK_INTERFACE_NAME = "eth0"
ENABLE_NETWORK_MANAGER_CMDS = ["chkconfig NetworkManager on", "service NetworkManager start"]
SAVE_VM_CONFIG_CMD = "virsh save {} --bypass-cache {}"
RESTORE_VM_CONFIG_CMD = "virsh restore --bypass-cache {}"


def create_vm_from_qcow2(vm_name, mem_sz, cpu_num):
    qemu_cmd = "qemu-img create -f qcow2 -b {}/RHEL_VM.qcow2 " \
               "/var/lib/libvirt/images/{}.qcow2".format(SUT_ISO_IMAGE_LOCATION, vm_name)
    exec_command(qemu_cmd)

    install_cmd = "virt-install --name {} --ram {} --vcpus {} " \
                  "--disk /var/lib/libvirt/images/{}.qcow2,bus=virtio " \
                  "--import --noautoconsole --os-variant rhel7.0".format(vm_name, mem_sz, cpu_num, vm_name)
    exec_command(install_cmd)

    time.sleep(45)
    log.info("Successfully created vm {}".format(vm_name))


def get_vm_ip(vm_name, net_interface):
    """
    Get the specified vm ip, including default and attached ones
    """
    ifcfg = exec_command(f"ifconfig {net_interface}")

    sut_ip = re.search(r'((2[0-5]|1[0-9]|[0-9])?[0-9]\.){3}((2[0-5]|1[0-9]|[0-9])?[0-9])', ifcfg, re.I).group()
    log.info("Ifconfig for sut_ip: {}".format(sut_ip))
    sub_ip = ".".join(sut_ip.split(".")[:1]) + "."

    cmd = exec_command("virsh -q domifaddr {} --source agent | grep {}".format(vm_name, sub_ip))
    log.info("cmd return: \n{}".format(cmd))
    vm_ip = re.search(r'((2[0-5]|1[0-9]|[0-9])?[0-9]\.){3}((2[0-5]|1[0-9]|[0-9])?[0-9])', cmd, re.I).group()
    log.info("Got vm ip: {}".format(vm_ip))

    return vm_ip


def attach_sriov_pci_device(vm_name, vf_bus_id):
    """
    Create a virtual pci device with specified vf and attach it onto the vm
    """
    log.debug("Using vf bus id {} to attach".format(vf_bus_id))

    bus = vf_bus_id[0:2]
    slot = vf_bus_id[3:5]
    function = vf_bus_id[6:]
    vf_xml = get_sriov_xml(vm_name, bus, slot, function)

    state = exec_command('virsh domstate {}'.format(vm_name))
    if state.strip() != 'running':
        log.info("Target vm is down, booting now")
        exec_command("virsh start {}".format(vm_name))
        time.sleep(60)

    exec_command("virsh attach-device {} {} --live --config".format(vm_name, SUT_TOOL_PATH + "/" + vf_xml))


def get_bus_id(net_type='I210'):
    """
    Get all bus ids with specified NIC type on sut
    """
    nets = exec_command('lspci | grep -i {}'.format(net_type)).split("\n")
    if nets is None:
        log.error("No PCI network device detected")
        raise RuntimeError("No PCI device found")
    bus_list = []
    for n in nets:
        if net_type in n:
            nic_bus = n.split()[0]
            if "0000" in nic_bus:
                bus_list.append(n.split()[5:])
            else:
                bus_list.append(nic_bus)

    if len(bus_list) == 0:
        log.error("No available NIC found")
        raise RuntimeError("No PCI device found")
    return bus_list


def get_network_bus_id(pci_name):
    """
    Use the NIC card type to grab card bus id
    """
    # device_name = exec_command("ifconfig | grep -i running | grep -i en | awk -F: '{print $1}'")
    device_name = exec_command("ifconfig | grep -i UP | grep -i ib | awk -F: '{print $1}'")
    device_list = device_name.strip().split('\n')

    if device_list is None:
        log.error("No PCI network device detected")
        raise RuntimeError("No PCI device found")

    temp_ids = []
    bus_ids = []
    for d in device_list:
        if d in 'lo':
            continue
        out = exec_command("ethtool -i {} | grep -i bus-info".format(d))
        temp_ids.append(out[15:-1])
    for bus_id in get_bus_id(pci_name):
        for temps in temp_ids:
            if bus_id == temps:
                bus_ids.append(bus_id)

    log.info(f"Bus_ids: {bus_ids}")
    return bus_ids


def get_vf_list():
    """
    Get all the vf created on current sut
    """
    vf_bus_list = []
    vf_list = exec_command("lspci").split('\n')

    for vf in vf_list:
        if "Virtual" in vf:
            vf_bus_id = vf.split()[0]
            if "0000" in vf_bus_id:
                vf_bus_list.append(vf.split()[5:])
            else:
                vf_bus_list.append(vf_bus_id)

    log.info("Got vf list: {}".format(vf_bus_list))
    return vf_bus_list


def get_sriov_xml(vm_name, bus, slot, function):
    """
    Create a pci device xml to attach, return the path of created xml file
    """
    xml_path = "pci_device.xml"

    conf = elementTree.parse(xml_path)
    root = conf.getroot()
    addr = root.find('source/address')
    addr.attrib['bus'] = f'0x{bus}'
    addr.attrib['slot'] = f'0x{slot}'
    addr.attrib['function'] = f'0x{function}'
    xml_tmp = 'xml_tmp'
    if not os.path.exists(xml_tmp):
        os.makedirs(xml_tmp)
    vf_file = f'xml_tmp/pci_device_{vm_name}_{bus}_{slot}_{function}.xml'
    conf.write(vf_file)
    return vf_file


def clear_vm(vm_name):
    """
    Clear all data created during the test, including vm created
    """
    # remove sr-iov xml file folder
    xml_path = pathlib.Path("/home/BKCPkg/domains/network/xml_tmp")
    if xml_path.exists():
        exec_command("rm -rf {}".format(xml_path))

    # delete vm
    log.info("Destroying vm {}".format(vm_name))
    exec_command('virsh destroy {}'.format(vm_name))
    exec_command('virsh undefine --domain {} --remove-all-storage'.format(vm_name))
    log.info("Vm related data cleared successfully")


def ssh_and_ping(vm_ip, vm2_ip):
    """
    Connect to the vm with vm1_ip using ssh connections and ping vm2_ip from there
    """
    ping_cmd = "ping -c 4 {}".format(vm2_ip)

    ping_ret = _pexpect_ssh_cmd(vm_ip, ping_cmd)

    log.info(ping_ret)
    if ping_ret.find('100% packet loss') != -1:
        log.error("Failed to ping vm {} ".format(vm2_ip))
        raise RuntimeError('vm ping failed')
    log.info(">>>>>>>>>Pinged {} successfully".format(vm2_ip))


def _pexpect_ssh_cmd(host, cmd, timeout=60):
    log.info("pexpect spawning cmd: ssh root@{} {} ".format(host, cmd))
    p_exp = pexpect.spawn('ssh root@{} {}'.format(host, cmd), timeout=timeout)
    p_exp.expect(r"password:*")
    p_exp.sendline('password')
    to_return = p_exp.read().decode().strip()
    p_exp.close()

    if "failed" in to_return.lower():
        log.error("pexpect execution error: " + to_return)
        raise RuntimeError("pexpect execution error: " + to_return)
    return to_return


def _handle_vm_firewall(vm_ip):
    try:
        _pexpect_ssh_cmd(vm_ip, 'systemctl stop firewall')
        _pexpect_ssh_cmd(vm_ip, 'systemctl disable firewall')
    except Exception as e:
        if "Unit firewall.service not loaded" in str(e):
            _pexpect_ssh_cmd(vm_ip, 'pkill -f firewalld && systemctl start firewalld')
        else:
            raise e


def _get_network_interface():
    interface = exec_command(GET_NETWORK_INTERFACE_NAME_CMD)

    interface_name = interface.strip()
    if not interface_name:
        raise RuntimeError("Failed to get network interface")

    log.info("Got net interface name: {}".format(interface_name))
    return interface_name


def _check_attach_and_get_interface(vm_ip):
    cmd = "\'lspci | grep -i \"Virtual Function\"\'"
    vm_pci_device = _pexpect_ssh_cmd(vm_ip, cmd)
    log.info("pexpect return: " + vm_pci_device)

    if not vm_pci_device.startswith("00:"):
        raise RuntimeError("Adapter addition failed")
    vm_pci_bus_id = vm_pci_device[:7].split(":")
    log.debug("got vm bus id: {}".format(vm_pci_bus_id))
    cmd = f"'ls /sys/bus/pci/devices/0000\\:{vm_pci_bus_id[0]}\\:{vm_pci_bus_id[1]}/net'"
    get_interface = _pexpect_ssh_cmd(vm_ip, cmd)
    log.debug("got vm interface name: {}".format(get_interface))
    return get_interface


# =========== Not Used ============
def __create_vm(vm_name, cpu_num, disk_sz, mem_sz):
    """
    Create a linux vm from scratch with specified variables
    """
    iso_path = SUT_ISO_IMAGE_LOCATION + "RHEL-8.3.0-20201009.2-x86_64-dvd1.iso"

    commands = f"virt-install --name {vm_name} --ram {mem_sz} --vcpus {cpu_num} --disk size={disk_sz} " \
               f"--location={iso_path} " \
               f"--initrd-inject={'/root' + KSTART_FILE_NAME} --cpu host --extra-args ks=file:anaconda-ks.cfg " \
               f" --noautoconsole"

    exec_result = exec_command(commands)

    log.debug("Creation cmd return: {}".format(exec_result))
    if vm_name and "Domain creation completed." and "Restarting guest." not in exec_result:
        raise RuntimeError("Failed to create the {} VM".format(vm_name))
    log.info("Successfully create the {} linux VM".format(vm_name))


def __copy_file_to_vm(vm_ip, src, dest):
    """
    Move a file from sut to specified vm
    """
    log.info("Copying file from path {} to vm path {}".format(src, dest))
    exec_command("sshpass -p password scp {} root@{}:{}".format(src, vm_ip, dest))
    log.info("File transmitted successfully")


def __ssh_and_install_vm_driver(vm_ip, path, vm_driver):
    """
    Use ssh connection to install relative driver and its dependencies
    """
    vm_cmd = "tar zxvf {} -C {}".format(path + vm_driver, path)
    exec_command("sshpass -p password ssh -p 22 root@{} {}".format(vm_ip, vm_cmd))

    # authenticate first
    vm_cmd = "cd {} && chmod 777 *".format(path + vm_driver[:-4])
    exec_command("sshpass -p password ssh -p 22 root@{} '{}'".format(vm_ip, vm_cmd))

    # install driver dependencies
    vm_cmd = "cd {} && yum localinstall -y ./{}".format(path)
    exec_command("sshpass -p password ssh -p 22 root@{} '{}'".format(vm_ip, vm_cmd))

    # run driver install
    vm_cmd = "cd {}/ && ./mlnxofedinstall".format(path + vm_driver[:-4])
    exec_command("sshpass -p password ssh -p 22 root@{} '{}'".format(vm_ip, vm_cmd))


def _pexpect_scp_file(host, src, dest):
    log.info("pexpect spawning cmd: scp {} root@{}:{} ".format(src, host, dest))
    p_exp = pexpect.spawn('scp {} root@{}:{}'.format(src, host, dest))
    p_exp.expect(r"password:*")
    p_exp.sendline('password')
    to_return = p_exp.read().decode().strip()
    p_exp.close()

    if "failed" in to_return.lower():
        log.error("pexpect execution error: " + to_return)
        raise RuntimeError("pexpect execution error: " + to_return)
    return to_return


if __name__ == '__main__':
    vm_name, net_inter, sut2_ip = None, None, None
    opts, args = getopt.getopt(sys.argv[1:],  shortopts="",
                               longopts=["vm_name=", "net_inter=", "sut2_ip="])
    for opt, val in opts:
        if opt == '--vm_name':
            vm_name = val
        elif opt == '--net_inter':
            net_inter = val
        elif opt == '--sut2_ip':
            sut2_ip = val

    # Run first time to get vm ip and return in out
    if sut2_ip is None:
        create_vm_from_qcow2(vm_name, 8192, 2)

        # Check stability of the created vm
        retry = 0
        for i in range(15):
            out = exec_command(f"virsh -q domifaddr {vm_name}")
            if "domain is not running" in out:
                retry += 1
                time.sleep(15)
            else:
                break

        if retry >= 15:
            raise RuntimeError("Cannot establish connection with created VM, retry exceeds maximum limit")

        # Get created vf(s) to create pci xml for attachment
        sut_vm_ip = get_vm_ip(vm_name, net_inter)
        vf_list = get_vf_list()
        vf_bus_id = vf_list[-1]
        attach_sriov_pci_device(vm_name, vf_bus_id)

        # Check if the pci device has been attached successfully
        vm_interface = _check_attach_and_get_interface(sut_vm_ip)

        # assign ip to added vf
        _pexpect_ssh_cmd(sut_vm_ip, 'mst start && systemctl start opensm')
        _pexpect_ssh_cmd(sut_vm_ip, 'ifconfig {} 192.168.13.100/24 up'.format(vm_interface))

        # disable firewall on vm
        _handle_vm_firewall(sut_vm_ip)

        # pinging sut2 from sut1
        ssh_and_ping(vm_ip=sut_vm_ip, vm2_ip='192.168.13.2')

        _pexpect_scp_file(sut_vm_ip, PMEMBLK_LIB_PATH, '/opt/libpmemblk.rpm')
        _pexpect_scp_file(sut_vm_ip, FIO_TOOL_PATH, '/opt/fio.rpm')
        _pexpect_ssh_cmd(sut_vm_ip, 'cd /opt && rpm -ivU libpmemblk.rpm')
        _pexpect_ssh_cmd(sut_vm_ip, 'cd /opt && rpm -ivU fio.rpm')

        sys.stdout.write('192.168.13.100')

    # Run for second time to run actual stress
    else:
        sut_vm_ip = get_vm_ip(vm_name, net_inter)

        # running fio
        cmd_fio = r'fio --randrepeat=1 --ioengine=mmap --direct=1 --gtod_reduce=1 --name=testnfs --readwrite=randrw --rwmixread=75 --size=4G --filename={test_path}'
        _pexpect_ssh_cmd(sut_vm_ip, 'setenforce 0')
        _pexpect_ssh_cmd(sut_vm_ip, 'mkdir -p /home/testdir')
        _pexpect_ssh_cmd(sut_vm_ip, f'mount {sut2_ip}:/home/nfstemp /home/testdir')
        _pexpect_ssh_cmd(sut_vm_ip, 'ls /home/testdir | grep target')
        stdout = _pexpect_ssh_cmd(sut_vm_ip, cmd_fio.format(test_path='/home/testdir/testfile'), timeout=3000)
        _pexpect_ssh_cmd(sut_vm_ip, 'umount /home/testdir')

        clear_vm(vm_name)

        sys.stdout.write(stdout)
