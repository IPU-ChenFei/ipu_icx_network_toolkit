import time
from lnx_exec_with_check import lnx_exec_command, lnx_exec_command_async
from constant import *


def run_qat_stress_async():
    """
          Purpose: Run QAT asynchronous stress overnight
          Args:
              No
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Run QAT asynchronous stress overnight
                    run_qat_stress_async()
    """
    current_time = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
    lnx_exec_command('rm -rf qat_async*.log', timeout=60, cwd='/root/')
    lnx_exec_command_async(
        f'while [ $SECONDS -lt $((SECONDS+100)) ]; do {QAT_DRIVER_PATH_L}build/cpa_sample_code runTests=63 signOfLife=1 ; done | tee /root/qat_async-{current_time}.log')


if __name__ == '__main__':
    run_qat_stress_async()



