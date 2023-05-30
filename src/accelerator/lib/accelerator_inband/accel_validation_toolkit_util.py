import os
import sys
import argparse
from lnx_exec_with_check import lnx_exec_command

TOOLKIT_NAME = 'spr-accelerators-random-config-and-test.zip'


def get_toolkit_folder_name():
    toolkit_name = TOOLKIT_NAME.split('.')[0]
    return toolkit_name


def download_accel_validation_toolkit():
    toolkit_fname = get_toolkit_folder_name()
    if os.path.exists(toolkit_fname):
        return 0
    else:
        cmd = 'unzip ' + TOOLKIT_NAME
        ret_v, outs, errs = lnx_exec_command(cmd)
        return ret_v

def find_recent_vm_script_path():
    vm_path = None
    root_dir =  os. getcwd()
    toolkit_dir = get_toolkit_folder_name()
    try:
        log_root = os.path.join(root_dir, toolkit_dir, "logs")
        dir_list = [f for f in os.listdir(log_root) if not os.path.isfile(f)]
        for log_dir in dir_list:
            if "DSA_MDEV" in log_dir:
                if vm_path is None:
                    vm_path = os.path.join(log_root, log_dir, 'launch_vm.sh')
                else:
                    print("\n ***** Multiple DSA_MDEV directory ***** \n")
        return str(vm_path)

    except Exception as e:
        print(e)
        return None

def launch_recent_vm():
    vm_script_path = find_recent_vm_script_path()
    if vm_script_path is None:
        return -1
    print(vm_script_path)
    return 0

if __name__ == '__main__':
    ret_v = 0
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='control the acceleration validation toolkit!'
                    '--install '
                    '--run command')
    parser.add_argument('-i', '--install', action='store_true', help='download and install')
    parser.add_argument('-r', '--run', default='none', dest='run', action='store', help='op to execute')

    parse_args = parser.parse_args(args)

    if parse_args.install:
        ret_v = download_accel_validation_toolkit()

    if parse_args.run == 'launch_recent_vm':
        ret_v = launch_recent_vm()
        sys.exit(ret_v)

    if parse_args.run != 'none':
        cmd = "cd " + get_toolkit_folder_name()
        ret_v, _, _ = lnx_exec_command(cmd)

        cmd = "rm -rf ./log"
        ret_v, _, _ = lnx_exec_command(cmd)

        ret_v, _, _ = lnx_exec_command(parse_args.run)

    sys.exit(ret_v)

