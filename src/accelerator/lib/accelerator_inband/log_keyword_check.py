import argparse
import sys
from log import logger


def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='Check if all keyword can be detect on output'
                    '--key_list <The list of keyword need to be checked>'
                    '--out <The result of last command>'
                    '--err_message <Error message>')
    parser.add_argument('-k', '--key_list', required=True, dest='key_list', action='store',
                        help='keyword list')
    parser.add_argument('-o', '--out', required=True, dest='out', action='store', 
                        help='The result of last command')
    parser.add_argument('-e', '--err_message', required=True, dest='err_message', action='store',
                        help='Error message')
    ret = parser.parse_args(args)
    return ret


def check_keyword(key_list, out, err_message):
    """
          Purpose: check whether there is any keyword in the data
          Args:
              Keyword to be checked.
              The data that should contain the keyword.
          Returns:
              Yes: the data contain the keyword
              No: Otherwise
          Raises:
              RuntimeError: If any errors
          Example:
              keyword_checking('error', data)
    """
    for key in key_list:
        if key not in out:
            logger.error(err_message)
            raise Exception(err_message)


if __name__ == '__main__':
    args_parse = setup_argparse()
    check_keyword(args_parse.key_list, args_parse.out, args_parse.err_message)


