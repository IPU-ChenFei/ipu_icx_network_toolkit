import sys
import argparse
from lnx_exec_with_check import lnx_exec_command
from get_cpu_num import get_cpu_num
from constant import *
from log import logger
import os


def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='Check accel-config list {accel-config list}'
                    '--acce_ip <accelerator type> {dsa, iax, qat, dlb}')
    parser.add_argument('-a', '--acce_ip', required=True, dest='acce_ip', action='store', help='accelerator type')
    ret = parser.parse_args(args)
    return ret


def __check_all_device_wq(cpu_num, device_num, out):
    line_list = out.strip().split('\n')
    dsa_enable_num = 0
    for line in line_list:
        if '"state":"enabled"' in line:
            dsa_enable_num += 1
    if dsa_enable_num != cpu_num * device_num * 9:
        logger.error('Not all dsa grouped_workqueues are enabled')
        raise Exception('Not all dsa grouped_workqueues are enabled')


def __check_random_device_wq(out, device_num, acce_ip):
    if '"state":"disabled"' in out:
        logger.error('Some disabled wq are showed')
        raise Exception('Some disabled wq are showed')
    enabled_device_num = 0
    line_list = out.strip().split('\n')
    for line in line_list:
        if f'"dev":"{acce_ip}' in line:
            enabled_device_num += 1
    if device_num != enabled_device_num:
        logger.error('Not all device are detected')
        raise Exception(f'Not all device are detected, device num {str(device_num)}, enabled device number {str(enabled_device_num)}')


def accel_config_check(device_num, acce_ip):
    """
         Purpose: Check accel-config list result
         Args:
             device_num: The number of enabled device in work-queues
             acce_ip: Which device need to check the device status, such as: 'DSA' or 'IAX'
         Returns:
             No
         Raises:
             RuntimeError: If any errors
         Example:
             Simplest usage: Check accel-config list result
                 accel_config_check(device_num, 'IAX')
   """
    get_cpu_num()
    cpu_num = int((lnx_exec_command('cat /home/logs/cpu_num.log')[1]).strip())
    _, out, err = lnx_exec_command('accel-config list', timeout=60)
    if acce_ip == 'qat':
        if device_num == "" or device_num == cpu_num * QAT_DEVICE_NUM:
            __check_all_device_wq(cpu_num, QAT_DEVICE_NUM, out)
        else:
            __check_random_device_wq(out, device_num, acce_ip)
    elif acce_ip == 'dlb':
        if device_num == "" or device_num == cpu_num * DLB_DEVICE_NUM:
            __check_all_device_wq(cpu_num, DLB_DEVICE_NUM, out)
        else:
            __check_random_device_wq(out, device_num, acce_ip)
    elif acce_ip == 'dsa':
        if device_num == "" or device_num == cpu_num * DSA_DEVICE_NUM:
            __check_all_device_wq(cpu_num, DSA_DEVICE_NUM, out)
        else:
            __check_random_device_wq(out, device_num, acce_ip)
    elif acce_ip == 'iax':
        if device_num == "" or device_num == cpu_num * IAX_DEVICE_NUM:
            __check_all_device_wq(cpu_num, IAX_DEVICE_NUM, out)
        else:
            __check_random_device_wq(out, device_num, acce_ip)


if __name__ == '__main__':
    args_parse = setup_argparse()
    if os.path.exists('/home/logs/enabled_num.log'):
        device_num = int((lnx_exec_command('cat /home/logs/enabled_num.log')[1]).strip())
    else:
        device_num = ""
    accel_config_check(device_num, args_parse.acce_ip)

