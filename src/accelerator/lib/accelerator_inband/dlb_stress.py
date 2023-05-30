import time
from lnx_exec_with_check import lnx_exec_command
from log_keyword_check import check_keyword
from constant import *


def dlb_stress():
    """
          Purpose: Run dlb stress overnight
          Args:
              No
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Run dlb stress overnight
                    dlb_stress()
    """
    current_time = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
    lnx_exec_command('rm -rf dlb*.log', timeout=60, cwd='/root/')
    lnx_exec_command(
        f'while [ $SECONDS -lt 30 ]; do /home/BKCPkg/domains/accelerator/dlb/libdlb/examples/ldb_traffic -n 1024 ;done | tee /root/dlb-{current_time}.log',
        timeout=500000)
    lnx_exec_command(f'cp /root/dlb*.log {LOGS_L}')
    _, out, err = lnx_exec_command('cat /root/dlb*.log')
    check_keyword(['[tx_traffic()] Sent 1024 events', '[rx_traffic()] Received 1024 events'], out, 'Run DLB stress fail')


if __name__ == '__main__':
    dlb_stress()



