import sys
import argparse
from lnx_exec_with_check import lnx_exec_command
from get_cpu_num import get_cpu_num
from constant import *
from log import logger


def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='Check all accelerator device status in output file'
                    '--acce_ip <accelerator type> {dsa, iax, qat, dlb}')
    parser.add_argument('-a', '--acce_ip', required=True, dest='acce_ip', action='store', help='accelerator type')
    ret = parser.parse_args(args)
    return ret


def check_acce_device_status(acce_ip):
    """
          Purpose: Check all device in output file
          Args:
              acce_ip : Which device need to check the device status, such as 'qat','dlb','dsa'
              platform_name :'EGS' or 'BHS'
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Check EGS all QAT device
                    check_acce_device_status('qat', 'EGS')
    """
    get_cpu_num()
    cpu_num = int((lnx_exec_command('cat /home/logs/cpu_num.log')[1]).strip())
    if acce_ip == 'qat':
        _, out, err = lnx_exec_command(f'lspci |grep {qat_id}', timeout=60)
        line_list = out.strip().split('\n')
        device_num = 0
        for line in line_list:
            if f'{qat_id}' in line:
                device_num += 1
        if device_num != cpu_num * QAT_DEVICE_NUM:
            logger.error('Not detect all device')
            raise Exception('Not detect all device')
    elif acce_ip == 'dlb':
        _, out, err = lnx_exec_command(f'lspci |grep {dlb_id}', timeout=60)
        line_list = out.strip().split('\n')
        device_num = 0
        for line in line_list:
            if f'{dlb_id}' in line:
                device_num += 1
        if device_num != cpu_num * DLB_DEVICE_NUM:
            logger.error('Not detect all device')
            raise Exception('Not detect all device')
    elif acce_ip == 'dsa':
        _, out, err = lnx_exec_command(f'lspci |grep {dsa_id}', timeout=60)
        line_list = out.strip().split('\n')
        device_num = 0
        for line in line_list:
            if f'{dsa_id}' in line:
                device_num += 1
        if device_num != cpu_num * DSA_DEVICE_NUM:
            logger.error('Not detect all device')
            raise Exception('Not detect all device')
    elif acce_ip == 'iax':
        _, out, err = lnx_exec_command(f'lspci |grep {iax_id}', timeout=60)
        line_list = out.strip().split('\n')
        device_num = 0
        for line in line_list:
            if f'{iax_id}' in line:
                device_num += 1
        if device_num != cpu_num * IAX_DEVICE_NUM:
            logger.error('Not detect all device')
            raise Exception('Not detect all device')


if __name__ == '__main__':
    args_parse = setup_argparse()
    check_acce_device_status(args_parse.acce_ip)



