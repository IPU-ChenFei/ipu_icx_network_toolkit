import sys
import argparse
from lnx_exec_with_check import lnx_exec_command
from add_environment_to_file import add_environment_to_file


def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='Create DLB SRIOV config'
                    '--dlb_device_index <dlb device index>')
    parser.add_argument('-d', '--dlb_device_index', required=True, dest='dlb_device_index', action='store',
                        help='dlb device index')
    ret = parser.parse_args(args)
    return ret


def __create_dlb_mdev_egs(MDEV_PATH):
    lnx_exec_command(f'echo 2048 > {MDEV_PATH}/num_atomic_inflights', timeout=60, cwd='/root')
    lnx_exec_command(f'echo 4096 > {MDEV_PATH}/num_dir_credits', timeout=60, cwd='/root')
    lnx_exec_command(f'echo 64 > {MDEV_PATH}/num_dir_ports', timeout=60, cwd='/root')
    lnx_exec_command(f'echo 2048 >  {MDEV_PATH}/num_hist_list_entries', timeout=60, cwd='/root')
    lnx_exec_command(f'echo 8192 >  {MDEV_PATH}/num_ldb_credits', timeout=60, cwd='/root')
    lnx_exec_command(f'echo 64 >  {MDEV_PATH}/num_ldb_ports', timeout=60, cwd='/root')
    lnx_exec_command(f'echo 32 >  {MDEV_PATH}/num_ldb_queues', timeout=60, cwd='/root')
    lnx_exec_command(f'echo 32 >  {MDEV_PATH}/num_sched_domains', timeout=60, cwd='/root')
    lnx_exec_command(f'echo 16 >  {MDEV_PATH}/num_sn0_slots', timeout=60, cwd='/root')
    lnx_exec_command(f'echo 16 >  {MDEV_PATH}/num_sn1_slots', timeout=60, cwd='/root')


def __create_dlb_mdev_bhs(MDEV_PATH):
    lnx_exec_command(f'echo 2048 > {MDEV_PATH}/num_atomic_inflights', timeout=60, cwd='/root')
    lnx_exec_command(f'echo 96 > {MDEV_PATH}/num_dir_ports', timeout=60, cwd='/root')
    lnx_exec_command(f'echo 2048 >  {MDEV_PATH}/num_hist_list_entries', timeout=60, cwd='/root')
    lnx_exec_command(f'echo 16384 >  {MDEV_PATH}/num_ldb_credits', timeout=60, cwd='/root')
    lnx_exec_command(f'echo 64 >  {MDEV_PATH}/num_ldb_ports', timeout=60, cwd='/root')
    lnx_exec_command(f'echo 32 >  {MDEV_PATH}/num_ldb_queues', timeout=60, cwd='/root')
    lnx_exec_command(f'echo 32 >  {MDEV_PATH}/num_sched_domains', timeout=60, cwd='/root')
    lnx_exec_command(f'echo 16 >  {MDEV_PATH}/num_sn0_slots', timeout=60, cwd='/root')
    lnx_exec_command(f'echo 16 >  {MDEV_PATH}/num_sn1_slots', timeout=60, cwd='/root')


def create_dlb_mdev(dlb_device_index):
    """
          Purpose: Create DLB SRIOV config
          Args:
              dlb_dev: DLB device id number, device id number begin from 0
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Create DLB SRIOV config
                  creat_dlb_mdev(0)
    """
    add_environment_to_file('SYSFS_PATH', f'export SYSFS_PATH=/sys/class/dlb2/dlb{dlb_device_index}')
    lnx_exec_command('uuidgen > uuidgen.txt', timeout=60, cwd='/root/')
    _, out, err = lnx_exec_command('cat uuidgen.txt', timeout=60, cwd='/root/')
    line_list = out.strip().split('\n')
    uuidgen = line_list[0]
    MDEV_PATH = f'/sys/bus/mdev/devices/{uuidgen}/dlb2_mdev'
    lnx_exec_command(f'echo {uuidgen} > $SYSFS_PATH/device/mdev_supported_types/dlb2-dlb/create ', timeout=60,
                     cwd='/root')
    __create_dlb_mdev_egs(MDEV_PATH)


if __name__ == '__main__':
    args_parse = setup_argparse()
    create_dlb_mdev(args_parse.dlb_device_index)



