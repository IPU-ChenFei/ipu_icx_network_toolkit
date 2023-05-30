from lnx_exec_with_check import lnx_exec_command
from log_keyword_check import check_keyword
from add_environment_to_file import add_environment_to_file
from constant import *
from log import logger
from check_error import check_error


def copy_openssl():
    lnx_exec_command(f'mkdir -p {OPENSSL_PATH_L}')
    lnx_exec_command('rm -rf *', timeout=60, cwd=OPENSSL_PATH_L)
    lnx_exec_command(f'cp -r {OPENSSL_NAME} {OPENSSL_PATH_L}')


def openssl_install():
    """
          Purpose: Install openssl file
          Args:
              No
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Install openssl file
                    openssl_install()
    """
    lnx_exec_command('yum -y install perl-core', timeout=10*60)
    copy_openssl()
    lnx_exec_command('unzip *.zip', timeout=60, cwd=OPENSSL_PATH_L)
    lnx_exec_command('chmod 777 *', timeout=60, cwd=f'{OPENSSL_PATH_L}openssl-master/')
    lnx_exec_command('./config --prefix=/usr/local/ssl', timeout=10*60, cwd=f'{OPENSSL_PATH_L}openssl-master/')
    _, out, err = lnx_exec_command('make', timeout=20*60, cwd=f'{OPENSSL_PATH_L}openssl-master/')
    check_error(err)
    _, out, err = lnx_exec_command('make test', timeout=20*60, cwd=f'{OPENSSL_PATH_L}openssl-master/')
    check_keyword(['Result: PASS'], out, 'Openssl test fail')
    check_error(err)
    _, out, err = lnx_exec_command('make install', timeout=20*60, cwd=f'{OPENSSL_PATH_L}openssl-master/')
    add_environment_to_file('PERL5LIB', f'export PERL5LIB=$PERL5LIB:{OPENSSL_PATH_L}openssl-master')
    add_environment_to_file('OPENSSL_ENGINES', 'export OPENSSL_ENGINES=/usr/lib64/engines-1.1')
    add_environment_to_file('LD_LIBRARY_PATH', 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib')


if __name__ == '__main__':
    openssl_install()



