import sys
import argparse
from lnx_exec_with_check import lnx_exec_command
import re


def check_kernel_args(args):
    result_code, out, _ = lnx_exec_command('cat /proc/cmdline')
    if result_code:
        return result_code
    if args not in out:
        return 1
    return 0


if __name__ == '__main__':
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='check kernel args is corrent'
                    '--args <kernel argument> ')
    parser.add_argument('-a', '--args', default=None, dest='args', action='store', help=' kernel args')
    parse_args = parser.parse_args(args)
    ret = check_kernel_args(parse_args.args)
    sys.exit(ret)