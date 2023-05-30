import time
from lnx_exec_with_check import lnx_exec_command, lnx_exec_command_async
from log import logger
from check_error import check_error


def run_fio_stress_async():
    """

          Purpose: Run fio asynchronous stress overnight
          Args:
              No
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Run fio stress overnight
                    run_fio_stress_async()
    """
    current_time = time.strftime('%Y%m%d%H%M', time.localtime(time.time()))
    lnx_exec_command('rm -rf fio_async*.log', timeout=60, cwd='/root/')
    lnx_exec_command('yum install -y fio', timeout=10 * 60)
    lnx_exec_command_async(
        f'fio --filename=/dev/sda --direct=1 --iodepth=1 --rw=randrw --rwmixread=70 --ioengine=libaio --bs=4k --size=300G --numjobs=50 --runtime=300 --group_reporting --name=randrw70read4k > /root/fio_async-{current_time}.log')

if __name__ == '__main__':
    run_fio_stress_async()



