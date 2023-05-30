import time
from lnx_exec_with_check import lnx_exec_command
from log_keyword_check import check_keyword
from constant import *


def qat_stress():
    """
          Purpose: Run QAT stress overnight
          Args:
              No
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Run QAT stress overnight
                    qat_stress()
    """
    current_time = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
    lnx_exec_command('rm -rf qat*.log', timeout=60, cwd='/root/')
    lnx_exec_command(
        f'while [ $SECONDS -lt 300 ]; do {QAT_DRIVER_PATH_L}/build/cpa_sample_code runTests=63 signOfLife=1 | tee /root/qat-{current_time}.log; done ',
        timeout=50000)
    lnx_exec_command(f'cp /root/qat*.log {LOGS_L}')
    _, out, err = lnx_exec_command('cat /root/qat*.log')
    check_keyword(["Sample code completed successfully"], out, 'Run qat stress fail')


if __name__ == '__main__':
    qat_stress()



