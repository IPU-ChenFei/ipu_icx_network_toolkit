import sys
from lnx_exec_with_check import lnx_exec_command


def get_cpu_num():
    """
          Purpose: Get current SUT CPU numbers
          Args:
              No
          Returns:
              Yes: return cpu numbers
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Get current SUT CPU numbers
                    get_cpu_num()
    """
    _, out, err = lnx_exec_command('lscpu')
    line_list = out.strip().split('\n')
    for line in line_list:
        word_list = line.split()
        if word_list[0] == 'Socket(s):':
            cpu_num = int(word_list[1])
            lnx_exec_command('mkdir -p /home/logs/')
            lnx_exec_command('rm -rf /home/logs/cpu_num.log')
            lnx_exec_command(f'echo {cpu_num} > /home/logs/cpu_num.log')


if __name__ == '__main__':
    get_cpu_num()
