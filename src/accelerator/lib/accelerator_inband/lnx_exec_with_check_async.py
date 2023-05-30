import subprocess
import sys
import argparse
from cmd_check_utlis import setup_argparse, result_checking
from log import logger
from threading import Timer
import os


def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='Install QAT driver in host'
                    '--cmd <Install QAT driver is enable sriov or not>'
                    '--cwd <Install QAT driver is enable sriov or not>')
    parser.add_argument('-c', '--cmd', default=None, dest='cmd', action='store', help='Enable sriov or not')
    parser.add_argument('-w', '--cwd', default=None, dest='cwd', action='store', help='Enable sriov or not')
    ret = parser.parse_args(args)
    return ret

def lnx_exec_command_async(cmd, cwd=None, timeout=None):
    cmd = '{} &'.format(cmd)
    os.system(cmd)
    logger.info(f'SUT execute cmd: {cmd}')


if __name__ == '__main__':
    args_parse = setup_argparse()
    lnx_exec_command_async(cmd=args_parse.cmd, cwd=args_parse.cwd)
