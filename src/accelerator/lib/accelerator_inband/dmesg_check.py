import sys
import argparse
from lnx_exec_with_check import lnx_exec_command
from log import logger
import time
from constant import *
from check_error import check_error


def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='check dmesg error'
                    '--ignore_str <ignore error>')
    parser.add_argument('-i', '--ignore_str', default="", dest='ignore_str', action='store', help='ignore error')
    ret = parser.parse_args(args)
    return ret


def dmesg_error_check(ignore_str):
    """
          Purpose: To check dmesg error
          Args:
              ignore_list: some error can ignore, input ignore string, eg: ignore_str = 'Error Record', 'error code -5'
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: check dmesg error
                  dmesg_check('Error Record', 'error code -5')
    """
    current_time = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
    lnx_exec_command('rm -rf dmesg*.log', timeout=60, cwd='/root/')
    lnx_exec_command('dmesg > /home/dmesg.log', timeout=60)
    #lnx_exec_command(f'cp /root/dmesg.log {LOGS_L}')
    ret, out, err = lnx_exec_command(f"cat /home/dmesg.log |grep -i 'error'", timeout=60)
    line_list = out.strip().split('\n')
    ignore_list = ignore_str.split(',')
    for line in line_list:
        ignore_flag = 0
        for i in range(len(ignore_list)):
            if ignore_list[i] in line and ignore_list[i] != "":
                ignore_flag = 1
                break
        if ('Error' in line or 'error' in line) and not ignore_flag:
            print(ignore_list,line,ignore_flag)
            logger.error('dmesg show error')
            raise Exception('dmesg show error')


if __name__ == '__main__':
    args_parse = setup_argparse()
    dmesg_error_check(args_parse.ignore_str)


