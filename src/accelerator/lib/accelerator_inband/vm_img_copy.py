import sys
import argparse
from constant import *
import time
import subprocess
import re
from lnx_exec_with_check import lnx_exec_command
from get_cpu_num import get_cpu_num

def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='copy img file from source img file'
                    '--d <device name>'
                    '--pdev <the number of physical device to derive vf>'
                    '--scale <the number vfs derived from a pf>'
                    '--guest_vf <the number of vfs in a guest vm>'
                    '--file <source img file path>'
                    '--num <directly specify a number to copy>')
    parser.add_argument('-n', '--num', default='', dest='num', action='store', help='directly specify a number to copy')
    parser.add_argument('-d', '--device', default='qat', dest='device', action='store', help='device name')
    parser.add_argument('-p', '--pdev', default='all', dest='pdev', action='store', help='the number of physical device to derive vf')
    parser.add_argument('-s', '--scale', default='1', dest='scale', action='store', help='the number vfs derived from a pf')
    parser.add_argument('-g', '--guest_vf', default='1', dest='guest_vf', action='store', help='the number of vfs in a guest vm')
    parser.add_argument('-f', '--file', required=True, dest='file', action='store', help='source img file path')
    ret = parser.parse_args(args)
    return ret


def vm_img_copy(num,device, pdev, scale, guestvf, file):
    vm_number = 0
    get_cpu_num()
    cpu_num = int((lnx_exec_command('cat /home/logs/cpu_num.log')[1]).strip())
    if num =='':
        if device == 'dlb' or device == 'qat' or device == 'iax' or device == 'dsa':
            if pdev == 'all':
                physical_device = cpu_num*4 #use all as default
            else:
                physical_device = int(pdev)
            virtual_device = int(scale)*physical_device
            vm_number = int(virtual_device/int(guestvf))
    else:
        vm_number = int(num)
    for i in range(int(vm_number)):
        lnx_exec_command(f'\cp {file} /home/vm{i}.img',timeout=60*10)
    return

if __name__ == '__main__':
    args_parse = setup_argparse()
    vm_img_copy(args_parse.num,args_parse.device, args_parse.pdev, args_parse.scale, args_parse.guest_vf, args_parse.file)


