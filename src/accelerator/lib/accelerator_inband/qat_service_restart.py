from lnx_exec_with_check import lnx_exec_command
from log_keyword_check import check_keyword


def __qat_service_restart():
    _, out, err = lnx_exec_command('service qat_service restart', timeout=10 * 60)
    if "Unit qat_service.service not found" in err:
        _, out, err = lnx_exec_command('qat_service restart', timeout=10 * 60)
        return out
    return out


def qat_service_restart():
    """
          Purpose: Check QAT restart status
          Args:
              No
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: run qat_service restart
                    qat_service_restart()
    """
    out = __qat_service_restart()
    check_keyword(['Stopping all devices', 'Starting all devices'], out, 'QAT service status down')


if __name__ == '__main__':
    qat_service_restart()



