import os, re
import subprocess
import argparse
import sys

def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='--cmd <command to be executed>'
					)
    parser.add_argument('-c', '--cmd', required=True, default=None, dest='cmd', action='store', help='command to be executed')
    ret = parser.parse_args(args)
    return ret
	
def lnx_exec_command(cmd, cwd=None, timeout=60):
    """
          Purpose: execute command and return 
          Args:
    """
    sub = subprocess.Popen(cmd,
                           shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE,
                           encoding='utf-8',
                           cwd=cwd)
    if sub.returncode is None:
        return_code = 0
    else:
        return_code = sub.returncode
    outs, errs = sub.communicate()
    print(outs) # print out to framework
    print(errs)
    return return_code, outs, errs


			
def keyword_check(key_word, data):
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
    for line in data.splitlines():
        if(re.findall(key_word,line)):
            return True
        else:
            return False

def test_main():
    args_parse = setup_argparse()
    _, out, _ = lnx_exec_command(cmd = args_parse.cmd)
    res = keyword_check('error', out)
    if res == True:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == '__main__':
	test_main()