import sys
import argparse
import subprocess
from constant import *
from get_cpu_num import get_cpu_num
import time

def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='distribute the dlb resource'
                    '--device <device type,dlb,qat>'
                    '--pdev <the number of physical device to derive vf>'
                    '--scale <the number vfs derived from a pf>'
                    '--guest_vf <the number of vfs in a guest vm>')
    parser.add_argument('-d', '--device', required=True, dest='device', action='store', help='device name')
    parser.add_argument('-p', '--pdev', default='all', dest='pdev', action='store', help='the number of physical device to derive vf')
    parser.add_argument('-s', '--scale', required=True, dest='scale', action='store', help='the number vfs derived from a pf')
    parser.add_argument('-g', '--guest_vf', required=True, dest='guest_vf', action='store', help='the number of vfs in a guest vm')
    parser.add_argument('-m', '--mode', default='sym', dest='mode', action='store', help='mode of device, for qat')
    ret = parser.parse_args(args)
    return ret

def lnx_exec_startvm(cmd, cwd=None):
    # timeout = float(timeout)
    print("LNX Execute: " + cmd + "\n", flush=True)

    sub = subprocess.Popen(cmd,
                           shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           encoding='utf-8',
                           cwd=cwd)
    try:
        sub.communicate(timeout = 5)
    finally:
        return

def uuid_gen(num):
    """
          Purpose: Generate UUID and store it into uuid.log
          Args:
              num:the number of UUID to generate
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Generate 5 uuid
                    uuid_gen(5)
    """
    lnx_exec_command('mkdir -p /home/logs/')
    lnx_exec_command('rm -rf /home/logs/uuid.log')
    for _ in range(int(num)):
        lnx_exec_command(f'echo `uuidgen` >> /home/logs/uuid.log')
    return


def port_gen(num,check=True):
    """
          Purpose: Generate available port and store it into port.log
          Args:
              num:the number of port to generate
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Generate 5 available ports
                    port_gen(5)
    """
    ini_port = 2201
    lnx_exec_command('mkdir -p /home/logs/')
    lnx_exec_command('rm -rf /home/logs/port.log')
    for p in range(num):
        port_num = ini_port + p
        if check:
            _, out, err = lnx_exec_command(f'lsof -i:{port_num}', timeout=60)
            if out == '':
                lnx_exec_command(f'echo {port_num} >> /home/logs/port.log')
        else:
            lnx_exec_command(f'echo {port_num} >> /home/logs/port.log')
    return

def resource_config_login(device, pdev, scale_factor, guestvf, mode):
    """
          Purpose: 'distribute the dlb resource according to the portion number'
          Args:
              device: device type
              pdev: the number of physical device to derive vf
              scale: vdev number from every physical device
              guestvf: the number of vfs in a guest vm
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: 'distribute the dlb resource into 1 portion'
                    resource_config_login('dlb',2,2,1)
    """
    physical_device = 0
    virtual_device = 0
    vm_number = 0
    scale_factor = int(scale_factor)
    guestvf = int(guestvf)
    get_cpu_num()
    cpu_num = int((lnx_exec_command('cat /home/logs/cpu_num.log')[1]).strip())
    if device == 'dlb':
        if pdev == 'all':
            physical_device = cpu_num*4 #use all as default
        else:
            physical_device = int(pdev)
        virtual_device = scale_factor*physical_device
        vm_number = int(virtual_device/guestvf)
        port_gen(vm_number)
        uuid_gen(physical_device*scale_factor)
        _, out, err = lnx_exec_command('cat /home/logs/uuid.log', timeout=60)
        uuid_list = out.strip().split('\n')
        _, out, err = lnx_exec_command('cat /home/logs/port.log', timeout=60)
        port_list = out.strip().split('\n')
        for i,uuid in enumerate(uuid_list):
            SYSFS_PATH = f'/sys/class/dlb2/dlb{int(i/scale_factor)}'
            MDEV_PATH = f'/sys/bus/mdev/devices/{uuid}/dlb2_mdev'
            lnx_exec_command(f'echo {uuid} > {SYSFS_PATH}/device/mdev_supported_types/dlb2-dlb/create')
            lnx_exec_command(f'echo {int(2048/scale_factor)} > {MDEV_PATH}/num_atomic_inflights')
            lnx_exec_command(f'echo {int(4096/scale_factor)} > {MDEV_PATH}/num_dir_credits')
            lnx_exec_command(f'echo {int(64/scale_factor)} > {MDEV_PATH}/num_dir_ports')
            lnx_exec_command(f'echo {int(2048/scale_factor)} > {MDEV_PATH}/num_hist_list_entries')
            lnx_exec_command(f'echo {int(8192/scale_factor)} > {MDEV_PATH}/num_ldb_credits')
            lnx_exec_command(f'echo {int(64/scale_factor)} > {MDEV_PATH}/num_ldb_ports')
            lnx_exec_command(f'echo {int(32/scale_factor)} > {MDEV_PATH}/num_ldb_queues')
            lnx_exec_command(f'echo {int(32/scale_factor)} > {MDEV_PATH}/num_sched_domains')
            lnx_exec_command(f'echo {int(16/scale_factor)} > {MDEV_PATH}/num_sn0_slots')
            lnx_exec_command(f'echo {int(16/scale_factor)} > {MDEV_PATH}/num_sn1_slots')
        for j in range(vm_number):
            cmd = f'/usr/libexec/qemu-kvm -name DLBGuest{j} -machine q35 -enable-kvm -global kvm-apic.vapic=false -m 8192 -cpu host -net nic,model=virtio -nic user,hostfwd=tcp::{port_list[j]}-:22 -drive format=raw,file=/home/vm{j}.img -bios /home/OVMF.fd -smp 4 -serial mon:stdio'
            for k in range(guestvf):
                cmd = cmd + f' -device vfio-pci,sysfsdev=/sys/bus/mdev/devices/{uuid_list[j*guestvf+k]}'
            lnx_exec_startvm(cmd)
        time.sleep(5)
    elif device == 'qat':
        if pdev == 'all':
            physical_device = cpu_num*4 #use all as default
        else:
            physical_device = int(pdev)
        virtual_device = scale_factor*physical_device
        vm_number = int(virtual_device/guestvf)
        port_gen(vm_number)
        _, out, err = lnx_exec_command('cat /home/logs/port.log', timeout=60)
        port_list = out.strip().split('\n')

        #uuid_gen(physical_device*scale_factor)
        #_, out, err = lnx_exec_command('cat /home/logs/uuid.log', timeout=60)
        #uuid_list = out.strip().split('\n')
        uuid_list = []
        bdf_list = []
        return_code, out, err = lnx_exec_command(f'lspci |grep {qat_id}', timeout=5 * 60, cwd=QAT_DRIVER_PATH_L)
        line_list = out.strip().split('\n')
        if return_code:
            sys.exit(return_code)
        else:
            for k, line in enumerate(line_list):
                if k >= physical_device:
                    break
                print(f'this is {k} device')
                bdf = line.split(' ')[0]
                for _ in range(scale_factor):
                    return_code, out_create, err = lnx_exec_command('./build/vqat_ctl create' + ' ' + '0000:' + str(bdf) + ' ' + mode, timeout=10 * 60, cwd=QAT_DRIVER_PATH_L)
                    if return_code:
                        sys.exit(return_code)
                    else:
                        line_list_create = out_create.strip().split('\n')
                        for line_create in line_list_create:
                            if 'created successfully, device name =' in line_create:
                                uuid = line_create.split(' = ')[1]
                                uuid_list.append(uuid)
                                bdf_list.append(bdf)
                            else:
                                print('device creation fail')
                                sys.exit(1)
        for j in range(vm_number):
            cmd = f'/usr/libexec/qemu-kvm -name guestVM{j} -machine q35 -enable-kvm -global kvm-apic.vapic=false -m 4096 -cpu host -net nic,model=virtio -nic user,hostfwd=tcp::{port_list[j]}-:22 -drive format=raw,file=/home/vm{j}.img -bios /home/OVMF.fd -smp 4 -serial mon:stdio -nographic'
            for k in range(guestvf):
                print(j*guestvf+k, len(bdf_list), len(uuid_list), j, len(port_list))
                bdf = '0000:' + bdf_list[j*guestvf+k]
                uuid = uuid_list[j*guestvf+k]
                pci = 'pci' + bdf[0:7]
                cmd = cmd + f' -device vfio-pci,sysfsdev=/sys/devices/{pci}/{bdf}/{uuid}'
            lnx_exec_startvm(cmd)
        time.sleep(5)
    elif device == 'iax':
        if pdev == 'all':
            physical_device = cpu_num*4 #use all as default
        else:
            physical_device = int(pdev)
        virtual_device = scale_factor*physical_device
        vm_number = int(virtual_device/guestvf)
        port_gen(vm_number)
        _, out, err = lnx_exec_command('cat /home/logs/port.log', timeout=60)
        port_list = out.strip().split('\n')


        uuid_list = []
        bdf_list = []
        return_code, out, err = lnx_exec_command(f'lspci |grep {iax_id}', timeout=5 * 60)
        line_list = out.strip().split('\n')
        if return_code:
            sys.exit(return_code)
        else:
            for k, line in enumerate(line_list):
                if k >= physical_device:
                    break
                print(f'this is {k} device')
                bdf = line.split(' ')[0]
                for _ in range(scale_factor):
                    return_code, out_create, err = lnx_exec_command(f'echo 0000:{str(bdf)} > /sys/bus/pci/devices/0000:{str(bdf)}/driver/unbind', timeout=10 * 60)
                    if return_code:
                        sys.exit(return_code)
                    else:
                        line_list_create = out_create.strip().split('\n')
                        for line_create in line_list_create:
                            if 'created successfully, device name =' in line_create:
                                uuid = line_create.split(' = ')[1]
                                uuid_list.append(uuid)
                                bdf_list.append(bdf)
                            else:
                                print('device creation fail')
                                sys.exit(1)

        # -accel kvm -monitor pty -drive format=raw,file=/home/qemu_centos_12.qcow2 -bios /home/OVMF.fd -net nic,model=virtio -nic user,hostfwd=tcp::2222-:22 -device intel-iommu,caching-mode=on,dma-drain=on,x-scalable-mode="modern",device-iotlb=on,aw-bits=48 -device vfio-pci,host=6a:02.0 -nographic
        for j in range(vm_number):
            cmd = f'/usr/libexec/qemu-kvm -name guestVM{j} -machine q35 -enable-kvm -global kvm-apic.vapic=false -m 8192 -cpu host -net nic,model=virtio -nic user,hostfwd=tcp::{port_list[j]}-:22 -drive format=raw,file=/home/vm{j}.img -bios /home/OVMF.fd -smp 4 -serial mon:stdio -nographic'
            for k in range(guestvf):
                print(j*guestvf+k, len(bdf_list), len(uuid_list), j, len(port_list))
                bdf = '0000:' + bdf_list[j*guestvf+k]
                uuid = uuid_list[j*guestvf+k]
                pci = 'pci' + bdf[0:7]
                cmd = cmd + f' -device vfio-pci,sysfsdev=/sys/devices/{pci}/{bdf}/{uuid}'
            lnx_exec_startvm(cmd)
        time.sleep(5)



if __name__ == '__main__':
    args_parse = setup_argparse()
    resource_config_login(args_parse.device, args_parse.pdev, args_parse.scale, args_parse.guest_vf, args_parse.mode)


