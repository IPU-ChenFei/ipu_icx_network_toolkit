from lnx_exec_with_check import lnx_exec_command
from log_keyword_check import check_keyword
from qat_service_restart import qat_service_restart
from check_qat_service_status import check_qat_service_status
from add_environment_to_file import add_environment_to_file
from constant import *
from log import logger
from check_error import check_error


def copy_qatzip():
    lnx_exec_command(f'mkdir -p {QATZIP_PATH_L}')
    lnx_exec_command('rm -rf *', timeout=60, cwd=QATZIP_PATH_L)
    lnx_exec_command(f'cp -r {QATZIP_NAME} {QATZIP_PATH_L}')


def copy_qatzip_script():
    lnx_exec_command(f'mkdir -p {QATZIP_SCRIPT_PATH_L}')
    lnx_exec_command('rm -rf *', timeout=60, cwd=QATZIP_SCRIPT_PATH_L)
    lnx_exec_command(f'cp -r {QATZIP_SCRIPT_NAME} {QATZIP_SCRIPT_PATH_L}')


def qatzip_test():  # qatzip_script-->qatzip.sh
    """
          Purpose: Install QATZIP file and test QATZIP
          Args:
              No
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Install QATZIP file and test QATZIP
                    qatzip_test()
    """
    copy_qatzip()
    copy_qatzip_script()
    lnx_exec_command('unzip *.zip', timeout=60, cwd=QATZIP_PATH_L)
    lnx_exec_command('cp *.conf /etc', timeout=60,
                     cwd=f'{QATZIP_PATH_L}QATzip-master/config_file/c6xx/multiple_process_opt/')
    add_environment_to_file('ICP_ROOT', f'export ICP_ROOT={QAT_DRIVER_PATH_L}')
    add_environment_to_file('QATZIP_ROOT', f'export {QATZIP_PATH_L}QATzip-master/')
    lnx_exec_command('chmod 777 *', timeout=5 * 60, cwd=f'{QATZIP_PATH_L}QATzip-master/')
    lnx_exec_command('./configure', timeout=5 * 60, cwd=f'{QATZIP_PATH_L}QATzip-master/')
    lnx_exec_command('make clean', timeout=60, cwd=f'{QATZIP_PATH_L}QATzip-master/')
    _, out, err = lnx_exec_command('make all install', timeout=5 * 60, cwd=f'{QATZIP_PATH_L}QATzip-master/')
    check_error(err)
    qat_service_restart()
    check_qat_service_status()
    lnx_exec_command('chmod 777 *', timeout=60, cwd=QATZIP_SCRIPT_PATH_L)
    lnx_exec_command('dos2unix qatzip.sh', timeout=60, cwd=QATZIP_SCRIPT_PATH_L)
    _, out, err = lnx_exec_command('sh qatzip.sh', timeout=10 * 60, cwd=QATZIP_SCRIPT_PATH_L)
    check_keyword(['Test finished'], out, 'QATZIP test fail')


if __name__ == '__main__':
    qatzip_test()



