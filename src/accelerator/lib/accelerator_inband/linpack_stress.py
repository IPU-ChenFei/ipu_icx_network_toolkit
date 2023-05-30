import time
from lnx_exec_with_check import lnx_exec_command
from log_keyword_check import check_keyword
from constant import *


def copy_linpack():
    lnx_exec_command(f'mkdir -p {LINPACK_PATH_L}')
    lnx_exec_command('rm -rf *', timeout=60, cwd=LINPACK_PATH_L)
    lnx_exec_command(f'cp -r {LINPACK_NAME} {LINPACK_PATH_L}')


def linpack_stress():
    """
          Purpose: Run linpack stress overnight
          Args:
              No
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Run linpack stress overnight
                    linpack_stress()
    """
    current_time = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
    lnx_exec_command('rm -rf linpack*.log', timeout=60, cwd='/root/')
    lnx_exec_command('yum -y install docker', timeout=10 * 60)
    copy_linpack()
    lnx_exec_command('unzip *.zip', timeout=10 * 60, cwd=LINPACK_PATH_L)
    lnx_exec_command(
        f'while [ $SECONDS -lt 300 ]; do /home/BKCPkg/domains/accelerator/linpack/pnpwls-master/linpack/run_linpack.sh avx3 ; done | tee /root/linpack-{current_time}.log',
        timeout=30*60)
    lnx_exec_command(f'cp /root/linpack*.log {LOGS_L}')
    _, out, err = lnx_exec_command('cat /root/linpack*.log')
    check_keyword("1 tests completed and passed residual checks", out, 'Run Linpark stress fail')


if __name__ == '__main__':
    linpack_stress()





