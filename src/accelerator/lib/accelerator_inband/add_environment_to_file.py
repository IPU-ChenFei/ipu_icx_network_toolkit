import sys
import argparse
from lnx_exec_with_check import lnx_exec_command


def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='to check all keys in /root/.bashrc file, if not add environments variable to /root/.bashrc file'
                    '--check_key <environment name>'
                    '--add_command <added environment>')
    parser.add_argument('-c', '--check_key', required=True, dest='check_key', action='store', help='environment name')
    parser.add_argument('-c', '--add_command', required=True, dest='add_command', action='store',
                        help='added environment')
    ret = parser.parse_args(args)
    return ret


def add_environment_to_file(check_key, add_command):
    """
          Purpose: to check all keys in /root/.bashrc file, if not add environments variable to /root/.bashrc file
          Args:
              check_key: the name of environments variable
              add_command: add environments variable to /root/.bashrc file
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: check key 'end' in /root/.bashrc file
                    add_environment_to_file('end', 'end=$((SECONDS+110))')
    """
    _, out, err = lnx_exec_command('cat /root/.bashrc', timeout=60)
    if check_key not in out:
        lnx_exec_command(f"echo '{add_command}' >> /root/.bashrc", timeout=60)
        lnx_exec_command('source /root/.bashrc', timeout=60)


if __name__ == '__main__':
    args_parse = setup_argparse()
    add_environment_to_file(args_parse.check_key, args_parse.add_command)



