from log_keyword_check import check_keyword
from lnx_exec_with_check import lnx_exec_command
from constant import *


def qat_uninstall():
    """
          Purpose: To uninstall QAT driver
          Args:
              No
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Uninstall QAT driver
                  qat_uninstall()
    """
    _, out, err = lnx_exec_command("lsmod | grep 'qat\|usdm' | wc -l", timeout=60, cwd=QAT_DRIVER_PATH_L)
    if out != '':
        if out != '0\n':
            lnx_exec_command('make uninstall', timeout=10 * 60, cwd=QAT_DRIVER_PATH_L)
            lnx_exec_command('make clean', timeout=60, cwd=QAT_DRIVER_PATH_L)
            lnx_exec_command('make distclean', timeout=60, cwd=QAT_DRIVER_PATH_L)
            _, out, err = lnx_exec_command("lsmod | grep 'qat\|usdm' | wc -l", timeout=60, cwd=QAT_DRIVER_PATH_L)
            check_keyword(['0'], out, 'Issue - QAT driver still exist')
        else:
            pass
    else:
        pass


if __name__ == '__main__':
    qat_uninstall()



