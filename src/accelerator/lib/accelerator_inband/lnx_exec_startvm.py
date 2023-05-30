import subprocess
import sys
import os
import time
from cmd_check_utlis import result_checking
import argparse


def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='execute command only for launching vm'
                    '--cmd <command> : command to execute'
                )
    parser.add_argument('-c', '--cmd', required=True, dest='cmd', action='store', help='command to execute')
    parser.add_argument('-t', '--timeout', default='60', dest='timeout', action='store', help='execute timeout')
    parser.add_argument('-d', '--dir', default='/root/', dest='dir', action='store', help='dir to execute')
    ret = parser.parse_args(args)
    return ret

def lnx_exec_startvm(cmd, cwd=None,timeout=3):
    print("LNX Execute: " + cmd + "\n", flush=True)

    sub = subprocess.Popen(cmd,
                           shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           encoding='utf-8',
                           cwd=cwd)
    try:
        sub.communicate(timeout = 5)
        time.sleep(10)
    finally:
        time.sleep(10)
        return

if __name__ == '__main__':
    args_parse = setup_argparse()
    lnx_exec_startvm(cmd=args_parse.cmd, cwd=args_parse.dir, timeout=int(args_parse.timeout))

