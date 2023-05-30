import time
from lnx_exec_with_check import lnx_exec_command
from log_keyword_check import check_keyword
from constant import *


def copy_stressapptest():
    lnx_exec_command(f'mkdir -p {STRESSAPPTEST_PATH_L}')
    lnx_exec_command('rm -rf *', timeout=60, cwd=STRESSAPPTEST_PATH_L)
    lnx_exec_command(f'cp -r {STRESSAPPTEST_NAME} {STRESSAPPTEST_PATH_L}')


def stressapptest_stress():
    """
          Purpose: Run stressapptest stress overnight
          Args:
              No
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Run stressapptest stress overnight
                    stressapptest_stress()
    """
    current_time = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
    lnx_exec_command('rm -rf stressapptest*.log', timeout=60, cwd='/root/')
    copy_stressapptest()
    lnx_exec_command('unzip *.zip', timeout=10 * 60, cwd=STRESSAPPTEST_PATH_L)
    lnx_exec_command('./configure', timeout=10 * 60, cwd=f'{STRESSAPPTEST_PATH_L}stressapptest-master/')
    lnx_exec_command('make install', timeout=10 * 60, cwd=f'{STRESSAPPTEST_PATH_L}stressapptest-master/')
    lnx_exec_command(
        f'{STRESSAPPTEST_PATH_L}stressapptest-master/src/stressapptest -s 100 -M 256 -m 18 -W -l /root/stressapptest-{current_time}.log',
        timeout=50000)
    lnx_exec_command(f'cp /root/stressapptest*.log {LOGS_L}')
    _, out, err = lnx_exec_command('cat /root/stressapptest*.log')
    check_keyword(["Status: PASS - please verify no corrected errors"], out, 'Run stressapptest stress fail')


if __name__ == '__main__':
    stressapptest_stress()



