import sys
import argparse
from lnx_exec_with_check import lnx_exec_command


def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='to check and delete all keys in /root/.bashrc file, if already add environments variable delete it in /root/.bashrc file'
                    '--check_key <environment name>')
    parser.add_argument('-c', '--check_key', required=True, dest='check_key', action='store', help='environment name')
    ret = parser.parse_args(args)
    return ret


def delete_environment(check_key):
    """
          Purpose: to check and delete all keys in /root/.bashrc file, if already add environments variable delete it in /root/.bashrc file
          Args:
              check_key: the name of environments variable
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: check if key 'end' in /root/.bashrc file and delete it
                    delete_environmen('end')
    """
    _, out, err = lnx_exec_command('cat /root/.bashrc', timeout=60)
    if check_key in out:
        lnx_exec_command(f"sed '/{check_key}/d' /root/.bashrc > /root/.bashrc1", timeout=60)
        lnx_exec_command(f"mv -f /root/.bashrc1 /root/.bashrc", timeout=60)
        lnx_exec_command('source /root/.bashrc', timeout=60)


if __name__ == '__main__':
    args_parse = setup_argparse()
    delete_environment(args_parse.check_key)



