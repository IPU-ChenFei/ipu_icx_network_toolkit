import sys
import argparse
import subprocess
from lnx_exec_with_check import lnx_exec_command
from log_keyword_check import check_keyword
from constant import *
from log import logger
from check_error import check_error
from get_cpu_num import get_cpu_num
import time

def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='distribute the dlb resource'
                    '--device <device type,dlb,qat,iax,dsa>'
                    '--num <the number of physical device bind>')
    parser.add_argument('-d', '--device', required=True, dest='device', action='store', help='device name')
    parser.add_argument('-n', '--num', default='all', dest='num', action='store', help='the number of physical device to bind')
    ret = parser.parse_args(args)
    return ret

def bind_device(device,num):
    num = int(num)
    device_code = {'iax': '0cfe', 'dsa': '0b25', 'qat': '-e 4940 -e 4944', 'dlb': 'grep -e 2710 -e 2714'}
    return_code, out, err = lnx_exec_command(f'lspci | grep {device_code[device]}')
    if return_code:
        sys.exit(return_code)
    else:
        lnx_exec_command('modprobe vfio-pci')
        line_list = out.strip().split('\n')
        if len(line_list) == 0:
            print('no such device')
            sys.exit(1)
        else:
            for k, line in enumerate(line_list):
                if k >= num:
                    break
                print(f'this is {k} device')
                bdf = line.split(' ')[0]
                return_code,out,err = lnx_exec_command(f'cd {Accelerator_REMOTE_TOOL_PATH}/dpdk && ./usertools/dpdk-devbind.py -b vfio-pci {bdf}',cwd=f'{Accelerator_REMOTE_TOOL_PATH}/dpdk',timeout=60)
                if return_code:
                    sys.exit(return_code)


if __name__ == '__main__':
    args_parse = setup_argparse()
    bind_device(args_parse.device, args_parse.num)

