import time
from lnx_exec_with_check import lnx_exec_command, lnx_exec_command_async
from log_keyword_check import check_keyword
from constant import *


def copy_stressapptest():
    lnx_exec_command(f'mkdir -p {STRESSAPPTEST_PATH_L}')
    lnx_exec_command('rm -rf *', timeout=60, cwd=STRESSAPPTEST_PATH_L)
    lnx_exec_command(f'cp -r {STRESSAPPTEST_NAME} {STRESSAPPTEST_PATH_L}')


def run_stressapptest_stress_async():
    """
          Purpose: Run stressapptest asynchronous stress overnight
          Args:
              No
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Run stressapptest asynchronous stress overnight
                    run_stressapptest_stress_async()
    """
    current_time = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
    lnx_exec_command('rm -rf stressapptest_async*_log', timeout=60, cwd='/root/')
    copy_stressapptest()
    lnx_exec_command('unzip *.zip', timeout=10*60, cwd=STRESSAPPTEST_PATH_L)
    lnx_exec_command('./configure', timeout=10*60, cwd=f'{STRESSAPPTEST_PATH_L}stressapptest-master/')
    lnx_exec_command('make install', timeout=10*60, cwd=f'{STRESSAPPTEST_PATH_L}stressapptest-master/')
    lnx_exec_command_async(f'{STRESSAPPTEST_PATH_L}stressapptest-master/src/stressapptest -s 300 -M 256 -m 18 -W -l /root/stressapptest_async-{current_time}_log')


if __name__ == '__main__':
    run_stressapptest_stress_async()



