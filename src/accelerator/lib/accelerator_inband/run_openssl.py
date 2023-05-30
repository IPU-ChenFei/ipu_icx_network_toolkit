import sys
import argparse
from lnx_exec_with_check import lnx_exec_command
from log_keyword_check import check_keyword
from check_qat_service_status import check_qat_service_status
from modify_qat_config_file import qat_asym_config
from constant import *
from log import logger
from check_error import check_error


def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='Run openssl symmetric or asymmetric'
                    '--is_asym <openssl mode> {symmetric or asymmetric}')
    parser.add_argument('-i', '--is_asym',  default='', dest='is_asym', action='store', help='openssl mode')
    ret = parser.parse_args(args)
    return ret


def openssl_asymmetric():
    """
          Purpose: Run openssl asymmetric
          Args:
              No
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Run openssl asymmetric
                  openssl_asymmetric()
    """
    _, out, err = lnx_exec_command('openssl engine -t -c -v qatengine', timeout=60,
                                   cwd=f'{QAT_ENGINE_PATH_L}QAT_Engine-master/')
    check_keyword(['available'], out, 'run openssl engine fail')
    qat_asym_config()
    check_qat_service_status()
    _, out, err = lnx_exec_command('openssl speed -engine qatengine -elapsed -async_jobs 72 rsa2048', timeout=60,
                                   cwd=f'{QAT_ENGINE_PATH_L}QAT_Engine-master/')
    lnx_exec_command('dos2unix QAT_Linux_OpenSSL_Speed_Test_Script_Asymmetric.sh', timeout=60, cwd=f'{QAT_ASYM_PATH_L}')
    lnx_exec_command('chmod 777 *', timeout=60, cwd=f'{QAT_ASYM_PATH_L}')
    _, out, err = lnx_exec_command('./QAT_Linux_OpenSSL_Speed_Test_Script_Asymmetric.sh', timeout=30*60,
                                   cwd=f'{QAT_ASYM_PATH_L}')


def openssl_symmetric():
    """
          Purpose: Run openssl symmetric
          Args:
              No
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Run openssl symmetric
                  openSSL_symmetric()
    """
    _, out, err = lnx_exec_command('openssl engine -t -c -v qatengine', timeout=10*60,
                                   cwd=f'{QAT_ENGINE_PATH_L}QAT_Engine-master/')
    check_keyword(['available'], out, 'openssl engine test fail')
    lnx_exec_command('dos2unix QAT_Linux_OpenSSL_Speed_Test_Script_Symmetric.sh', timeout=60, cwd=f'{QAT_SYM_PATH_L}')
    lnx_exec_command('chmod 777 *', timeout=60, cwd=f'{QAT_SYM_PATH_L}')
    _, out, err = lnx_exec_command('./QAT_Linux_OpenSSL_Speed_Test_Script_Symmetric.sh', timeout=30*60,
                                   cwd=f'{QAT_SYM_PATH_L}')


def copy_script():
    lnx_exec_command(f'mkdir -p {QAT_ASYM_PATH_L}')
    lnx_exec_command('rm -rf *', timeout=60, cwd=QAT_ASYM_PATH_L)
    lnx_exec_command(f'cp -r {QAT_ASYM_NAME} {QAT_ASYM_PATH_L}')
    lnx_exec_command(f'mkdir -p {QAT_SYM_PATH_L}')
    lnx_exec_command('rm -rf *', timeout=60, cwd=QAT_SYM_PATH_L)
    lnx_exec_command(f'cp -r {QAT_SYM_NAME} {QAT_SYM_PATH_L}')
    lnx_exec_command(f'mkdir -p {QAT_TEST_SCRIPT_PATH_L}')
    lnx_exec_command('rm -rf *', timeout=60, cwd=QAT_TEST_SCRIPT_PATH_L)
    lnx_exec_command(f'cp -r {QAT_TEST_SCRIPT_NAME} {QAT_TEST_SCRIPT_PATH_L}')


def run_openssl(is_asym=False):  # -->True/False
    """
          Purpose: Run openssl symmetric or asymmetric
          Args:
              is_asym: is openssl symmetric or asymmetric
          Returns:
              None
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Run openssl symmetric
                  run_openssl(False)
    """
    copy_script()
    # lnx_exec_command('rm -rf *', timeout=60, cwd=QAT_ASYM_PATH_L)
    # self.sut.upload_to_remote(localpath=QAT_ASYM_H, remotepath=QAT_ASYM_PATH_L)
    # lnx_exec_command('rm -rf *', timeout=60, cwd=QAT_SYM_PATH_L)
    # self.sut.upload_to_remote(localpath=QAT_SYM_H, remotepath=QAT_SYM_PATH_L)
    # lnx_exec_command('rm -rf *', timeout=60, cwd=QAT_TEST_SCRIPT_PATH_L)
    # self.sut.upload_to_remote(localpath=QAT_TEST_SCRIPT_H, remotepath=QAT_TEST_SCRIPT_PATH_L)
    if is_asym:
        openssl_asymmetric()
    else:
        openssl_symmetric()
        
        
if __name__ == '__main__':
    run_openssl()



