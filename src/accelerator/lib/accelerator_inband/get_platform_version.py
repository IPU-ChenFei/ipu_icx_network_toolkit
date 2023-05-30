from lnx_exec_with_check import lnx_exec_command
from constant import vm_platform

def get_platform_version():
    """
          Purpose: get platform version
          Args:
              No
          Returns:
              version name
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage:
                    get_platform_version()
    """
    _,out,_ = lnx_exec_command('dmidecode |grep Version|grep -e EGS -e BHS')
    if 'EGS' in out:
        return 'EGS'
    elif 'BHS' in out:
        return 'BHS'
    else:
        return vm_platform