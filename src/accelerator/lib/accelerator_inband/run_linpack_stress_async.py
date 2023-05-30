import time
import sys
from lnx_exec_with_check import lnx_exec_command
from lnx_exec_with_check_async import lnx_exec_command_async
from log_keyword_check import check_keyword
from constant import *


def copy_linpack():
    lnx_exec_command(f'mkdir -p {LINPACK_PATH_L}')
    lnx_exec_command('rm -rf *', timeout=60, cwd=LINPACK_PATH_L)
    lnx_exec_command(f'cp -r {LINPACK_NAME} {LINPACK_PATH_L}')


def run_linpack_stress_async():
    """
          Purpose: Run linpack asynchronous stress overnight
          Args:
              No
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Run linpack asynchronous stress overnight
                    run_linpack_stress_async()
    """
    current_time = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
    lnx_exec_command('rm -rf linpack_async*.log', timeout=60, cwd='/root/')
    lnx_exec_command('yum -y install docker', timeout=5 * 60)
    copy_linpack()
    lnx_exec_command('unzip *.zip', timeout=10 * 60, cwd=LINPACK_PATH_L)
    lnx_exec_command_async(
        f'while [ $SECONDS -lt $((SECONDS+100)) ]; do {LINPACK_PATH_L}pnpwls-master/linpack/run_linpack.sh avx3 ; done | tee /root/linpack_async-{current_time}.log')
    lnx_exec_command('ls', timeout=60)


if __name__ == '__main__':
    run_linpack_stress_async()





