import re
import subprocess
import sys
import argparse

def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='check whether the data meets the requirement'
		            '--cmd <command to be executed>'
                    '--able <enable or disable> : True/False'
					)
    parser.add_argument('-c', '--cmd', required=True, default=None, dest='cmd', action='store', help='command to be executed')
    parser.add_argument('-a', '--able',required=True, default=None, dest='able', action='store', help='enable or disable')
    ret = parser.parse_args(args)
    return ret

def lnx_exec_command(cmd, cwd=None, timeout=60):
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
	
def enable_disable_check(able, data):
    """
          Purpose: check x out of x enable/disable
          Args:
              able: True /False, Enable or disable
			  data: data to be checked
          Returns:
              whether the input data meets the requirement
          Example:
              Simplest usage: enable_disable_check(True, wq(s), data)
    """
    line_list = data.strip().split('\n')
    if able == 'True':
        status = 'enabled'
    else:
        status = 'disabled'
    regexp = status + '(\d+) (.*) out of (\d+)'
    for line in line_list:
        matchObj = re.match(regexp, line)
        print(line)
        print(matchObj)
        if matchObj:
            if matchObj.group(0) != matchObj.group(2):
                return False
    else:
        return True
	

if __name__ == '__main__':
    args_parse = setup_argparse()
    _, out, _ = lnx_exec_command(cmd = args_parse.cmd)
    ret= enable_disable_check(able = args_parse.able, data = out)
    if ret:
        print('pass')
        sys.exit(0)
    else:
        print('fail')
        sys.exit(1)