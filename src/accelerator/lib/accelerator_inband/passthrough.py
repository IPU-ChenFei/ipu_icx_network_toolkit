import subprocess
import sys
import argparse
from lnx_exec_with_check import lnx_exec_command
from log_keyword_check import check_keyword
from get_cpu_num import get_cpu_num
import time
from resource_config_login import *

def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='pass through physical device and launch vm'
                    '--device <the device to be passed through>'
                    '--guest_num <the number of devices in a guest vm>'                    
                    '--number <the number of devices to pass through>')
    parser.add_argument('-d', '--device', required=True, dest='device', action='store', help='the device to be passed through in lower class')
    parser.add_argument('-n', '--number', default='all', dest='number', action='store', help='the number of devices to pass through')
    parser.add_argument('-g', '--guest_num', required=True, dest='guest_num', action='store', help='the number of devices in a guest vm')
    ret = parser.parse_args(args)
    return ret


def pass_through(device, num, guest_num):
    get_cpu_num()
    cpu_num = int((lnx_exec_command('cat /home/logs/cpu_num.log')[1]).strip())
    num = int(num)
    guest_num = int(num)
    vm_num = int(num/guest_num)
    port_gen(vm_num)
    _, out, err = lnx_exec_command('cat /home/logs/port.log', timeout=60)
    port_list = out.strip().split('\n')
    bdf_list = []
    device_code = {'iax':'0cfe','dsa':'0b25','qat':'-e 4940 -e 4944','dlb':'grep -e 2710 -e 2714'}
    if num == 'all':
        num = 4 * int(cpu_num)
    if num > 4 * int(cpu_num):
        print('required number is more than the physical device number')
        sys.exit(1)
    return_code, out, err = lnx_exec_command(f'lspci | grep {device_code[device]}')
    if return_code:
        sys.exit(return_code)
    else:
        lnx_exec_command('modprobe vfio')
        lnx_exec_command('modprobe vfio-pci')
        line_list = out.strip().split('\n')
        if len(line_list) == 0:
            print('no such device')
            sys.exit(1)
        else:
            device_code[device] = str(line_list[0].split(' ')[6])
        for k, line in enumerate(line_list):
            if k >= num:
                break
            print(f'this is {k} device')
            bdf = line.split(' ')[0]
            bdf_list.append(bdf)
            return_code, out, err = lnx_exec_command(f'echo 0000:{bdf} > /sys/bus/pci/devices/0000:{bdf}/driver/unbind')
            if return_code:
                sys.exit(return_code)
        lnx_exec_command(f'echo 8086 {device_code[device]} > /sys/bus/pci/drivers/vfio-pci/new_id')
        for i in range(vm_num):
            cmd = f'/usr/libexec/qemu-kvm -name guestVM{i} -machine q35 -accel kvm -m 8192 -smp 4 -cpu host -monitor pty -drive format=raw,file=/home/vm{i}.img -bios /home/OVMF.fd -net nic,model=virtio -nic user,hostfwd=tcp::{port_list[i]}-:22 -device intel-iommu,caching-mode=on,dma-drain=on,x-scalable-mode="modern",device-iotlb=on,aw-bits=48 -nographic '
            for j in range(guest_num):
                cmd = cmd + f'-device vfio-pci,host={bdf_list[i*guest_num+j]}'
            lnx_exec_startvm(cmd)
        time.sleep(10)

if __name__ == '__main__':
    args_parse = setup_argparse()
    pass_through(args_parse.device, args_parse.number,args_parse.guest_num)