import sys
import argparse
from lnx_exec_with_check import lnx_exec_command
import os
from constant import *


def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='add the only folder under the path to the system environment variable'
                    '--name <system environment variable name>'
                    '--path <value of the system environment variable which should be a path>')
    parser.add_argument('-n', '--name', required=True, dest='name', action='store', help='environment variable name')
    parser.add_argument('-p', '--path', required=True, dest='path', action='store',
                        help='variable path')
    ret = parser.parse_args(args)
    return ret


def add_path_to_environment(variable_name, variable_path):
    """
          Purpose: add the only folder under the path to the system environment variable and name it as variable name
          Args:
              variable_path: system environment variable name
              variable_name: value of the system environment variable which should be a path
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: check key 'end' in /root/.bashrc file
                    add_path_to_environment('SCRIPT', '')
    """
    _, out, err = lnx_exec_command('ll', cwd=variable_path)
    line_list = out.strip().split('\n')
    for line in line_list:
        if line[0] == 'd':
            file_name = line.split(' ')[-1]
            lnx_exec_command('echo export ' + variable_name + '=' + variable_path + '/' + file_name + '>> $HOME/.bashrc', timeout=60)
            break


if __name__ == '__main__':
    args_parse = setup_argparse()
    add_path_to_environment(args_parse.name, args_parse.path)



