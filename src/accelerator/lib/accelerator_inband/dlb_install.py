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
        description='Install DLB driver in host'
                    '--ch_makefile <Modify Makefile or not>')
    parser.add_argument('-c', '--ch_makefile', required=True, dest='ch_makefile', action='store', help='Modify Makefile')
    ret = parser.parse_args(args)
    return ret


def add_environment_to_file(check_key, add_command):
    """
          Purpose: to check all keys in /root/.bashrc file, if not add environments variable to /root/.bashrc file
          Args:
              check_key: the name of environments variable
              add_command: add environments variable to /root/.bashrc file
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: check key 'end' in /root/.bashrc file
                    add_environment_to_file('end', 'end=$((SECONDS+110))')
    """
    _, out, err = lnx_exec_command('cat /root/.bashrc', timeout=60)
    if check_key not in out:
        lnx_exec_command(f"echo '{add_command}' >> /root/.bashrc", timeout=60)
        lnx_exec_command('source /root/.bashrc', timeout=60)


def copy_dlb_driver():
    lnx_exec_command(f'mkdir -p {DLB_DRIVER_PATH_L}')
    lnx_exec_command('rm -rf *', timeout=60, cwd=DLB_DRIVER_PATH_L)
    lnx_exec_command(f'cp -r {DLB_DRIVER_NAME} {DLB_DRIVER_PATH_L}')


def dlb_install(ch_makefile):
    """
          Purpose: To install DLB driver
          Args:
              ch_makefile: If need to modify DLB make file
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Install DLB driver need modify Makefile
                  dlb_install(True)
    """
    copy_dlb_driver()
    lnx_exec_command('unzip *.zip ', timeout=60, cwd=DLB_DRIVER_PATH_L)
    if ch_makefile == "True":
        lnx_exec_command(
            f"sed -i 's/ccflags-y += -DCONFIG_INTEL_DLB2_SIOV/#  iccflags-y += -DCONFIG_INTEL_DLB2_SIOV/g' {DLB_DRIVER_PATH_L}driver/dlb2/Makefile",
            timeout=60)
    _, out, err = lnx_exec_command('make', timeout=60, cwd=f'{DLB_DRIVER_PATH_L}driver/dlb2/')
    lnx_exec_command('rmmod dlb2', timeout=60, cwd=f'{DLB_DRIVER_PATH_L}driver/dlb2/')
    lnx_exec_command('insmod ./dlb2.ko', timeout=60, cwd=f'{DLB_DRIVER_PATH_L}driver/dlb2/')
    _, out, err = lnx_exec_command('lsmod | grep dlb2', timeout=60)
    check_keyword(['dlb2'], out, 'Issue - dlb driver install fail')
    _, out, err = lnx_exec_command('make', timeout=60, cwd=f'{DLB_DRIVER_PATH_L}libdlb/')
    check_error(err)
    add_environment_to_file('LD_LIBRARY_PATH',
                            f'export LD_LIBRARY_PATH={DLB_DRIVER_PATH_L}libdlb:$LD_LIBRARY_PATH')


if __name__ == '__main__':
    args_parse = setup_argparse()
    dlb_install(args_parse.ch_makefile)