import argparse
import sys
from log import logger


def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='Check if execute command with error'
                    '--error <Error message>')
    parser.add_argument('-e', '--error', required=True, dest='error', action='store',
                        help='Error message')
    ret = parser.parse_args(args)
    return ret


def check_error(err):
    if err != '':
        logger.error(err)
        raise Exception(err)


if __name__ == '__main__':
    args_parse = setup_argparse()
    check_error(args_parse.error)


