import sys
import argparse
from lnx_exec_with_check import lnx_exec_command
from constant import *
from log import logger


def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='Run accelerator random test {Setup_Randomize_DSA_Conf.sh -i 1000 -j 10}'
                    '--acce_ip <accelerator type> {DSA, IAX, QAT, DLB}')
    parser.add_argument('-c', '--cmd', default='', dest='cmd', action='store', help='the command to be executed')
    parser.add_argument('-a', '--acce_ip', required=True, dest='acce_ip', action='store', help='accelerator type, if cmd not specified')
    ret = parser.parse_args(args)
    return ret


def get_folder_name(variable_path):
    _, out, err = lnx_exec_command('ls -l', cwd=variable_path)
    line_list = out.strip().split('\n')
    for line in line_list:
        if line[0] == 'd':
            file_name = line.split(' ')[-1]
            return file_name


def dmatest_check(acce_ip,args_cmd):
    """
         Purpose: Run dmatest
         Args:
             acce_ip: Which device need to check the device status, such as: 'DSA' or 'IAX'
         Returns:
             No
         Raises:
             RuntimeError: If any errors
         Example:
             Simplest usage: Run dmatest
                 dmatest_check(device_num, 'DSA')
   """
    folder_name = get_folder_name(ACCE_RANDOM_CONFIG_PATH_L)
    if args_cmd != '':
        _, out, err = lnx_exec_command(f'./{args_cmd}', timeout=50 * 60,
                                       cwd=f'{ACCE_RANDOM_CONFIG_PATH_L}{folder_name}/')
    else:
        _, out, err = lnx_exec_command(f'./Setup_Randomize_{acce_ip}_Conf.sh -i 1000 -j 10', timeout=50 * 60,
                                       cwd=f'{ACCE_RANDOM_CONFIG_PATH_L}{folder_name}/')
    line_list = out.strip().split('\n')
    total_thread = 0
    threads_passed = 0
    for line in line_list:
        if 'Total Threads' in line:
            word_list0 = line.split(' ')
            total_thread = word_list0[2]
        if 'Threads Passed' in line:
            word_list1 = line.split(' ')
            threads_passed = word_list1[2]
    if total_thread != threads_passed:
        logger.error('dmatest fail')
        raise Exception('dmatest fail')


if __name__ == '__main__':
    args_parse = setup_argparse()
    dmatest_check(args_parse.acce_ip,args_parse.cmd)

