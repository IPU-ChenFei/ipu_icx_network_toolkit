import sys
import argparse
from lnx_exec_with_check import lnx_exec_command
from log_keyword_check import check_keyword
from get_cpu_num import get_cpu_num
from constant import *
from log import logger


def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='Accelerator device mode test{./Setup_Randomize_DSA_Conf.sh -r}'
                    '--acce_ip <accelerator type> {dsa, iax, qat, dlb}'
                    '--is_random <Test is random or not>')
    parser.add_argument('-a', '--acce_ip', required=True, dest='acce_ip', action='store', help='accelerator type')
    parser.add_argument('-d', '--is_random', required=True, dest='is_random', action='store',
                        help='Test is random or not>')
    ret = parser.parse_args(args)
    return ret


def get_folder_name(variable_path):
    _, out, err = lnx_exec_command('ll', cwd=variable_path)
    line_list = out.strip().split('\n')
    for line in line_list:
        if line[0] == 'd':
            file_name = line.split(' ')[-1]
            return file_name


def device_mode_test(acce_ip, is_random=False):
    """
         Purpose: Run acce_ip user mode test
         Args:
             acce_ip: Which device need to check the device status, such as: 'DSA' or 'IAX'
             is_random: Run value is random or not
         Returns:
             No
         Raises:
             RuntimeError: If any errors
         Example:
             Simplest usage: Run acce_ip user mode test
                 device_mode_test('IAX', False)
   """
    folder_name = get_folder_name(ACCE_RANDOM_CONFIG_PATH_L)
    _, out, err = lnx_exec_command(f'./Setup_Randomize_{acce_ip}_Conf.sh -r', timeout=5 * 60,
                                   cwd=f'{ACCE_RANDOM_CONFIG_PATH_L}{folder_name}/')
    get_cpu_num()
    cpu_num = int((lnx_exec_command('cat /home/logs/cpu_num.log')[1]).strip())
    device_num = 0
    if acce_ip == 'QAT':
        device_num = QAT_DEVICE_NUM * cpu_num * 8
    elif acce_ip == 'DLB':
        device_num = DLB_DEVICE_NUM * cpu_num * 8
    elif acce_ip == 'DSA':
        device_num = DSA_DEVICE_NUM * cpu_num * 8
    elif acce_ip == 'IAX':
        device_num = IAX_DEVICE_NUM * cpu_num * 8
    device_wq = 0
    line_list = out.strip().split('\n')
    for line in line_list:
        if 'WQs:' in line:
            device_wq = line.strip().split(':')[1].strip()
    thread_num = int(device_wq) * 24
    if is_random:
        check_keyword([f'{thread_num} of {thread_num} tests passed'], out, 'Device mode test failed')
    else:
        if device_num != int(device_wq):
            logger.error('Not all WQ are detected')
            raise Exception('Not all WQ are detected')
        else:
            check_keyword([f'{thread_num} of {thread_num} tests passed'], out, 'Device mode test failed')


if __name__ == '__main__':
    args_parse = setup_argparse()
    device_mode_test(args_parse.acce_ip, args_parse.is_random)


