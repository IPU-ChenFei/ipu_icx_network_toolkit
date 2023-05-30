import time
from lnx_exec_with_check import lnx_exec_command
from constant import *
from log import logger
from check_error import check_error


def fio_stress():
    """
          Purpose: Run fio stress overnight
          Args:
              No
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Run fio stress overnight
                    fio_stress()
    """
    current_time = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
    lnx_exec_command('rm -rf fio*.log', timeout=60, cwd='/root/')
    lnx_exec_command('yum install -y fio', timeout=10 * 60)
    _, out, err = lnx_exec_command(
        f'fio --filename=/dev/sda --direct=1 --iodepth=1 --rw=randrw --rwmixread=70 --ioengine=libaio --bs=4k --size=300G --numjobs=50 --runtime=100 --group_reporting --name=randrw70read4k > /root/fio-{current_time}.log',
        timeout=300)
    lnx_exec_command(f'cp /root/fio*.log {LOGS_L}')
    check_error(err)


if __name__ == '__main__':
    fio_stress()



