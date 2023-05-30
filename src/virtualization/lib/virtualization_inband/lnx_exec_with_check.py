import subprocess
import sys
import os
from cmd_check_utlis import setup_argparse, result_checking
from log import logger
from threading import Timer


# def kill_command(process):
#     process.kill()


# def lnx_exec_command(cmd, cwd=None, timeout=60, is_silent=False):
#     print("LNX Execute: " + cmd + "\n", flush=True)

#     sub = subprocess.Popen(cmd,
#                            shell=True,
#                            stdout=subprocess.PIPE,
#                            stderr=subprocess.PIPE,
#                            encoding='utf-8',
#                            cwd=cwd)

#     timer = Timer(timeout, kill_command, [sub])
#     timer.start()
#     stdout, stderr = sub.communicate()
#     if not timer.is_alive():
#         raise Exception(f"error: execute command [{cmd}] timeout within {timeout}s")
#     timer.cancel()
#     res = sub.returncode, stdout, stderr

#     if not is_silent:
#         logger.info(f'SUT execute cmd: {cmd}')
#         logger.info(f'SUT execute stdout: {stdout}')
#         logger.info(f'SUT execute stderr: {stderr}')

#     return res

def lnx_exec_command(cmd, cwd=None, timeout=300):
    # timeout = float(timeout)
    print("LNX Execute: " + cmd + "\n", flush=True)

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
    if timeout is None:
        outs, errs = sub.communicate()
    else:
        outs, errs = sub.communicate(timeout=timeout)

    res = return_code, outs, errs
    logger.info(f'SUT execute cmd: {cmd}')
    logger.info(f'SUT execute stdout: {outs}')
    # haibo_start
    if return_code:
        logger.error(f'SUT execute stderr: {errs}')
    # haibo_end

    return res




def lnx_exec_command_async(cmd, cwd=None, timeout=None):
    cmd = '{} &'.format(cmd)
    os.system(cmd)
    logger.info(f'SUT execute cmd: {cmd}')


if __name__ == '__main__':
    args_parse = setup_argparse()
    return_code, out, err = lnx_exec_command(cmd=args_parse.cmd, cwd=args_parse.dir, timeout=int(args_parse.timeout))
    if return_code:
        sys.exit(return_code)
    else:
        ret = result_checking(out, args_parse.mode, args_parse.list)
        sys.exit(ret)
