import traceback
import argparse
import sys
import os


def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='execute command with output checking'
                    '--cmd <command> : command to execute'
                    '--mode <check mode>     : "no", "keyword", "string", "kv'
                    '--dir <dir to execute>     : /root'
                    '--timeout execute timeout>     : 60'
                    '--list <checking string>   '
                )
    parser.add_argument('-c', '--cmd', required=True, dest='cmd', action='store', help='command to execute')
    parser.add_argument('-t', '--timeout', default='60', dest='timeout', action='store', help='execute timeout')
    parser.add_argument('-d', '--dir', default='/root/', dest='dir', action='store', help='dir to execute')
    parser.add_argument('-m', '--mode', default=None, dest='mode', action='store', help='mode for checking')
    parser.add_argument('-l', '--list', default=None, dest='list', action='store', help='checking string')
    parser.add_argument('--last-line', action='store_true',  help='only check last line')
    ret = parser.parse_args(args)
    return ret


LOG_PREFIX="CMD result checking pass: Mode:"
def result_checking(out, mode, input):
    if mode == "no":
        return 0
    elif mode == "string":
        if input.strip() in out:
            print(LOG_PREFIX, mode, input)
            return 0
        else:
            return -1
    elif mode == "kv":
        input_list = input.split(",")
        if len(input_list) == 2:
            key = input_list[0]
            v = input_list[1]
            out_lines = out.splitlines()
            for line in out_lines:
                if key in line and v not in line:
                    return -1
                if key in line:
                    print(LOG_PREFIX, mode, line)
            return 0
        else:
            return -1
    elif mode == "keyword":
        key_list = input.split(",")
        for key in key_list:
            if key.strip() not in out:
                print('error, not found keyword')
                return -1
        return 0
    elif mode == "no_found":
        key_list = input.split(",")
        for key in key_list:
            if key.strip() in out:
                print('error, found no_found')
                return -1
        return 0
    return 0


