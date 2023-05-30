import sys
import argparse
from lnx_exec_with_check import lnx_exec_command
from log_keyword_check import check_keyword
from dmesg_check import dmesg_error_check
from constant import *
from log import logger

def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='Run accelerator random test, input the shell file name'
                    '--shell file name, like Guest_Mdev_Randomize_DSA_Conf'
                    '--unzip <copy and unzip original file or not>'
                    '--mode, mode of dsa test, random or all')
    parser.add_argument('-u', '--unzip', default="True", dest='unzip', action='store', help='copy and unzip original file')
    parser.add_argument('-s', '--shell', required=True, dest='shell', action='store', help='shell file name')
    parser.add_argument('-m', '--mode', required=True, dest='mode', action='store', help='mode of dsa test, random or all')
    ret = parser.parse_args(args)
    return ret


def get_log_folder_name():
    _, out, err = lnx_exec_command('ls -l|grep DSA_Test', cwd=f'{ACCE_RANDOM_CONFIG_TEST_PATH_L}/logs')
    line_list = out.strip().split('\n')
    for line in line_list:
        if line[0] == 'd':
            folder_name = line.split(' ')[-1]
            return folder_name
    else:
        raise Exception('no DSA test log found')


def check_dsa_test_log():
    folder_name = get_log_folder_name()
    _, out, err = lnx_exec_command('ls|grep wq', cwd=f'{ACCE_RANDOM_CONFIG_TEST_PATH_L}/logs/{folder_name}')
    file_list = out.strip().split('\n')
    for file in file_list:
        print(f'checking log in cat {ACCE_RANDOM_CONFIG_TEST_PATH_L}/logs/{folder_name}/{file}|grep compl[0]')
        _, out, err = lnx_exec_command(f'cat {ACCE_RANDOM_CONFIG_TEST_PATH_L}/logs/{folder_name}/{file}|grep compl', cwd=f'{ACCE_RANDOM_CONFIG_TEST_PATH_L}/logs/{folder_name}')
        check_keyword('0x0000000000000001',out,'completion record error')
    return

def wq_configuration(shell,mode):
    if mode == 'random':
        return_code, out, err = lnx_exec_command(f'./{shell} -c', timeout=60, cwd=ACCE_RANDOM_CONFIG_TEST_PATH_L)
    elif mode == 'all':
        return_code, out, err = lnx_exec_command(f'./{shell} -u', timeout=60, cwd=ACCE_RANDOM_CONFIG_TEST_PATH_L)
    else:
        raise Exception('mode should be all or random')
    if return_code !=0:
        logger.error(err)
        raise Exception('wq configuration failed')
    line_list = out.strip().split('\n')
    for line in line_list:
        if 'enabled' in line and 'wq(s) out of' in line:
            queues_num = line.strip().split(' ')[1]
            wq_total = line.strip().split(' ')[5]
            break
    else:
        raise Exception('wq configuration failed')
    if queues_num!= wq_total:
        raise Exception('wq configuration failed')
    else:
        return

def run_all_opcode(shell,mode):
    for opcode in ['0x0','0x2','0x3','0x4','0x5','0x6','0x9']:
        lnx_exec_command(f'rm -rf /logs/DSA_Test*', timeout=60, cwd=f'{ACCE_RANDOM_CONFIG_TEST_PATH_L}')
        wq_configuration(shell, mode)
        return_code, out, err = lnx_exec_command(f'./{shell} -o {opcode}', timeout=60, cwd=ACCE_RANDOM_CONFIG_TEST_PATH_L)
        if return_code !=0:
            logger.error(err)
            raise Exception('opcode test failed')
        # line_list = out.strip().split('\n')
        # for line in line_list:
        #     if 'work queues logged completion records' in line:
        #         queues_num = line.strip().split(' ')[0]
        #         wq_total = line.strip().split(' ')[2]
        #         break
        # else:
        #     raise Exception('opcode test failed')
        # if queues_num!= wq_total:
        #     raise Exception('opcode test failed')
        # else:
        check_dsa_test_log()


def copy_acce_random_config():
    lnx_exec_command(f'mkdir -p {ACCE_RANDOM_CONFIG_PATH_L}')
    lnx_exec_command('rm -rf *', timeout=60, cwd=f'{ACCE_RANDOM_CONFIG_PATH_L}')
    lnx_exec_command(f'mkdir -p {ACCE_RANDOM_CONFIG_PATH_L}')
    # self.sut.upload_to_remote(localpath=SPR_ACCE_RANDOM_CONFIG_H, remotepath=ACCE_RANDOM_CONFIG_PATH_L)
    lnx_exec_command(f'cp -r {ACCE_RANDOM_CONFIG_NAME} {ACCE_RANDOM_CONFIG_PATH_L}')

def dsa_test(shell,mode,unzip):
    """
         Purpose: Configure work-queues, run dsa test, check the log
         Args:
             command: execute command
         Returns:
             No
         Raises:
             RuntimeError: If any errors
         Example:
             Simplest usage: Configure work-queues
                 dsa_test('./Guest_Mdev_Randomize_DSA_Conf.sh -o 0x3')
   """
    if unzip == "True":
        copy_acce_random_config()
        lnx_exec_command('unzip *.zip', timeout=60, cwd=ACCE_RANDOM_CONFIG_PATH_L)
    lnx_exec_command('rm -rf logs', timeout=60, cwd=ACCE_RANDOM_CONFIG_TEST_PATH_L)
    run_all_opcode(shell,mode)
    dmesg_error_check('')
    lnx_exec_command(f'./{shell} -d', timeout=60, cwd=ACCE_RANDOM_CONFIG_TEST_PATH_L)




if __name__ == '__main__':
    args_parse = setup_argparse()
    dsa_test(args_parse.shell, args_parse.mode, args_parse.unzip)

