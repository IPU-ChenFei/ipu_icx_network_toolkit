import sys
import argparse
from check_kernel_args import check_kernel_args
from modify_kernel_grub import modify_kernel_grub


def set_accel_kernel_args(op, cmd):
    if op == 'check':
        return check_kernel_args(cmd)
    elif op == "check_and_add":
        if not check_kernel_args(cmd):
            return 0
        else:
            return modify_kernel_grub(cmd, True)
    elif op == "remove":
        if check_kernel_args(cmd) == 1:
            return 0
        else:
            return modify_kernel_grub(cmd, False)
    else:
        return -1

if __name__ == '__main__':
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='Check Accel kernel argument, only support latest kernel!'
                    '--op <check_and_add, remove, check> '
                    '--cmd <command to set feature> ')
    parser.add_argument('-o', '--op', default='check', dest='op', action='store',
                        help='operation, {check_and_add, remove, check}')
    parser.add_argument('-c', '--cmd', dest='cmd', action='store', help='set feature command')
    parse_args = parser.parse_args(args)
    ret = set_accel_kernel_args(parse_args.op, parse_args.cmd)
    sys.exit(ret)

