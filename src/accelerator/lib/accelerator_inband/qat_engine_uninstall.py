from lnx_exec_with_check import lnx_exec_command
from constant import *
from log import logger
from check_error import check_error


def qat_engine_uninstall():
    """
          Purpose: Uninstall QAT Engine
          Args:
              No
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Uninstall QAT Engine file
                    qat_engine_uninstall()
    """
    _, out, err = lnx_exec_command('make uninstall', timeout=60, cwd=f'{QAT_ENGINE_PATH_L}QAT_Engine-master/')
    check_error(err)
    _, out, err = lnx_exec_command('make clean', timeout=60, cwd=f'{QAT_ENGINE_PATH_L}QAT_Engine-master/')
    check_error(err)
    _, out, err = lnx_exec_command('make distclean', timeout=60, cwd=f'{QAT_ENGINE_PATH_L}QAT_Engine-master/')
    check_error(err)


if __name__ == '__main__':
    qat_engine_uninstall()



