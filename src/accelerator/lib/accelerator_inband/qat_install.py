import sys
import argparse
from lnx_exec_with_check import lnx_exec_command
from constant import *
from log import logger


def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='Install QAT driver in host'
                    '--is_sriov <Install QAT driver is enable sriov or not>')
    parser.add_argument('-i', '--is_sriov', default="True", dest='is_sriov', action='store', help='Enable sriov or not')
    parser.add_argument('-w', '--who', default="host", dest='who', action='store', help='host or guest')
    ret = parser.parse_args(args)
    return ret


def copy_qat():
    lnx_exec_command(f'mkdir -p {QAT_DRIVER_PATH_L}')
    lnx_exec_command(f'rm -rf {QAT_DRIVER_PATH_L}*', timeout=60)
    lnx_exec_command(f'cp -r {QAT_DRIVER_NAME} {QAT_DRIVER_PATH_L}')


def qat_install(is_sriov,who):
    """
          Purpose: To install QAT driver
          Args:
              is_siov: Install qat driver with siov or not
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Install QAT driver
                  qat_install(False)
    """
    copy_qat()
    lnx_exec_command('unzip *.zip', timeout=60, cwd=QAT_DRIVER_PATH_L)
    lnx_exec_command('tar -zxvf *.tar.gz', timeout=60, cwd=QAT_DRIVER_PATH_L)
    if is_sriov == "True":
        lnx_exec_command(f'./configure --enable-icp-sriov={who}', timeout=15 * 60, cwd=QAT_DRIVER_PATH_L)
    else:
        lnx_exec_command('./configure', timeout=15 * 60, cwd=QAT_DRIVER_PATH_L)
    lnx_exec_command('make all', timeout=15 * 60, cwd=QAT_DRIVER_PATH_L)
    lnx_exec_command('make install', timeout=15 * 60, cwd=QAT_DRIVER_PATH_L)
    lnx_exec_command('make samples-install', timeout=15 * 60, cwd=QAT_DRIVER_PATH_L)
    _, out, err = lnx_exec_command('lsmod | grep qat', timeout=60)
    line_list = out.strip().split('\n')
    if who == 'host':
        key_list = ['qat_4xxx', 'intel_qat']
    else:
        key_list = ['intel_qat']
    for kw in key_list:
        for line in line_list:
            item_list = line.split()
            if kw in item_list[0]:
                break
        else:
            logger.error('Issue - QAT driver install failed')
            raise Exception('Issue - QAT driver install failed')


if __name__ == '__main__':
    args_parse = setup_argparse()
    qat_install(args_parse.is_sriov,args_parse.who)
	
	
	