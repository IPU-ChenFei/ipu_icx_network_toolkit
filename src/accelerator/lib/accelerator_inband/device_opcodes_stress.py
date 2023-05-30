import sys
import argparse
from lnx_exec_with_check import lnx_exec_command
from log_keyword_check import check_keyword
from constant import *
from log import logger
from check_error import check_error


def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='Run accelerator device opcodes test {Setup_Randomize_DSA_Conf.sh -o 0x3}'
                    '--command <execute command> {Setup_Randomize_DSA_Conf.sh}'
                    '--test_index <test index number> {3, 4, 5...}')
    parser.add_argument('-c', '--command', required=True, dest='command', action='store', help='execute command')
    parser.add_argument('-t', '--test_index', required=True, dest='test_index', action='store', help='index number')
    ret = parser.parse_args(args)
    return ret


def get_folder_name(variable_path):
    _, out, err = lnx_exec_command('ls -l', cwd=variable_path)
    line_list = out.strip().split('\n')
    for line in line_list:
        if line[0] == 'd':
            file_name = line.split(' ')[-1]
            return file_name


def device_opcodes_stress(command, test_index):
    """
         Purpose: Run acce_ip test with available OpCodes
         Args:
             command: execute command
             test_index: Which OpCode need to run
         Returns:
             No
         Raises:
             RuntimeError: If any errors
         Example:
             Simplest usage: Run acce_ip test with available OpCodes
                 device_opcodes_stress('Setup_Randomize_DSA_Conf.sh -o', 3)
   """
    folder_name = get_folder_name(ACCE_RANDOM_CONFIG_PATH_L)
    _, out, err = lnx_exec_command(f'./{command} 0x{test_index}', timeout=5 * 60,
                                   cwd=f'{ACCE_RANDOM_CONFIG_PATH_L}{folder_name}/')
    if test_index == 2:
        check_error(err)
    else:
        line_list = out.strip().split('\n')
        actual_wq = 0
        total_wq = 0
        for line in line_list:
            if 'work queues' in line:
                word_list = line.split('of')
                actual_wq = word_list[0].strip()
                total_wq = word_list[1].strip().split('work')[0].strip()
        check_keyword([f'{actual_wq} of {total_wq} work queues logged completion records'], out, 'Not all work queues logged completion records')


if __name__ == '__main__':
    args_parse = setup_argparse()
    device_opcodes_stress(args_parse.command, args_parse.test_index)


