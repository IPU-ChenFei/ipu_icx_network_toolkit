import sys
import argparse
from lnx_exec_with_check import lnx_exec_command
from log_keyword_check import check_keyword
from get_cpu_num import get_cpu_num
from constant import *
from log import logger


def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='Run accelerator random test, input the command need to be executed'
                    '--cmd <execute command> {Setup_Randomize_DSA_Conf.sh -c -F 1}'
                    '--unzip <copy and unzip original file or not>'
                    '--mode <the mode of execution, guest or host>'
                    '--num <if the mode is guest, the number of device in the guest>')
    parser.add_argument('-c', '--cmd', required=True, dest='cmd', action='store', help='execute command')
    parser.add_argument('-u', '--unzip', default="True", dest='unzip', action='store', help='copy and unzip original file')
    parser.add_argument('-m', '--mode', default='host', dest='mode', action='store', help='the mode of execution, guest or host')
    parser.add_argument('-n', '--num', default='1', dest='num', action='store', help='if the mode is guest, the number of device in the guest')
    ret = parser.parse_args(args)
    return ret


def get_folder_name(variable_path):
    _, out, err = lnx_exec_command('ls -l', cwd=variable_path)
    line_list = out.strip().split('\n')
    for line in line_list:
        if line[0] == 'd':
            file_name = line.split(' ')[-1]
            return file_name


def __choose_run_folder(command, is_reset_folder=False):
    folder_name = get_folder_name(ACCE_RANDOM_CONFIG_PATH_L)
    if not is_reset_folder:
        _, out, err = lnx_exec_command(f'./{command}', timeout=5 * 60, cwd=f'{ACCE_RANDOM_CONFIG_PATH_L}{folder_name}/')
    else:
        _, out, err = lnx_exec_command(f'./{command}', timeout=5 * 60, cwd=f'{ACCE_RANDOM_CONFIG_PATH_L}{folder_name}/accelerator_reset/')
    return out


def __check_enabled_wq_num(out):
    line_list = out.strip().split('\n')
    for line in line_list:
        if 'enabled' in line and 'wq(s) out of' in line:
            queues_num = line.strip().split(' ')[1]
            return queues_num
    else:
        line_list = out.strip().split('Enabling')
        work_queues_list = line_list[2].split('enabled')
        queues_word_list = work_queues_list[1].strip().split(' ')
    return queues_word_list[0]


def check_enabled_device_num(out):
    """
         Purpose: Check the number of enabled device in work-queues
         Args:
             out: Configure work-queues result
         Returns:
             No
         Raises:
             RuntimeError: If any errors
         Example:
             Simplest usage: Check the number of enabled device in work-queues
                 check_enabled_device_num(out)
   """
    line_list = out.strip().split('Enabling')
    device_list = line_list[1].split('enabled')
    device_word_list = device_list[1].strip().split(' ')
    enabled_num = device_word_list[0]
    lnx_exec_command('mkdir -p /home/logs/')
    lnx_exec_command('rm -rf /home/logs/enabled_num.log')
    lnx_exec_command(f'echo {enabled_num} > /home/logs/enabled_num.log') # return int(device_word_list[0])


def copy_acce_random_config():
    lnx_exec_command(f'mkdir -p {ACCE_RANDOM_CONFIG_PATH_L}')
    lnx_exec_command('rm -rf *', timeout=60, cwd=f'{ACCE_RANDOM_CONFIG_PATH_L}')
    lnx_exec_command(f'mkdir -p {ACCE_RANDOM_CONFIG_PATH_L}')
    # self.sut.upload_to_remote(localpath=SPR_ACCE_RANDOM_CONFIG_H, remotepath=ACCE_RANDOM_CONFIG_PATH_L)
    lnx_exec_command(f'cp -r {ACCE_RANDOM_CONFIG_NAME} {ACCE_RANDOM_CONFIG_PATH_L}')


def acce_random_test(command,mode,num,unzip):
    """
         Purpose: Configure work-queues
         Args:
             command: execute command
         Returns:
             No
         Raises:
             RuntimeError: If any errors
         Example:
             Simplest usage: Configure work-queues
                 acce_random_test('Setup_Randomize_DSA_Conf.sh -au -F 1')
   """
    lnx_exec_command(f'lspci -i {qat_id}')
    if unzip == "True":
        copy_acce_random_config()
        lnx_exec_command('unzip *.zip', timeout=60, cwd=ACCE_RANDOM_CONFIG_PATH_L)
    get_cpu_num()
    cpu_num = int((lnx_exec_command('cat /home/logs/cpu_num.log')[1]).strip())
    device_num = 0
    cmd_list = command.strip().split('_Conf')
    if cmd_list[0].split('_')[0] == 'Setup' or cmd_list[0].split('_')[0] == './Setup':
        acce_ip = cmd_list[0].split('_')[2]   #'DSA', 'IAX'
    elif cmd_list[0].split('_')[0] == 'Guest' or cmd_list[0].split('_')[0] == './Guest':
        acce_ip = cmd_list[0].split('_')[3]
    else:
        acce_ip = cmd_list[0].split('_')[2]
    if mode == 'host':
        if acce_ip == 'QAT':
            device_num = QAT_DEVICE_NUM
        elif acce_ip == 'DLB':
            device_num = DLB_DEVICE_NUM
        elif acce_ip == 'DSA':
            device_num = DSA_DEVICE_NUM
        elif acce_ip == 'IAX':
            device_num = IAX_DEVICE_NUM
    else:
        cpu_num = 1
        device_num = int(num)
    comm_list = command.strip().split('-')
    if 'a' in comm_list[1]:
        out = __choose_run_folder(command, False)
        check_enabled_device_num(out)
        enabled_device_num = int((lnx_exec_command('cat /home/logs/enabled_num.log')[1]).strip())
        enabled_wq_num = __check_enabled_wq_num(out)
        if enabled_device_num != cpu_num * device_num:
            logger.error('Not all device detected')
            raise Exception('Not all device detected')
        else:
            check_keyword([f'enabled {enabled_device_num} device(s) out of {enabled_device_num}', f'enabled {enabled_wq_num} wq(s) out of {enabled_wq_num}'], out, 'Device random test fail')
    elif 'c' in comm_list[1] and 'a' not in comm_list[1]:
        out = __choose_run_folder(command, False)
        check_enabled_device_num(out)
        enabled_device_num = int((lnx_exec_command('cat /home/logs/enabled_num.log')[1]).strip())
        enabled_wq_num = __check_enabled_wq_num(out)
        if cmd_list[0].split('_')[0] == 'Setup' or cmd_list[0].split('_')[0] == './Setup':
            check_keyword([f'enabled {enabled_device_num} device(s) out of {enabled_device_num}', f'enabled {enabled_wq_num} wq(s) out of {enabled_wq_num}'], out, 'Device random test fail')
        elif cmd_list[0].split('_')[0] == 'Guest' or cmd_list[0].split('_')[0] == './Guest':
            check_keyword([f'enabled {enabled_wq_num} wq(s) out of {enabled_wq_num}'], out, 'Device random test fail')
    elif 'w' in comm_list[1] or 'b' in comm_list[1]:
        out = __choose_run_folder(command, True)
        check_keyword(['No errors found. Test pass'], out, 'Device random test fail')
    elif 'r' in comm_list[1]:
        out = __choose_run_folder(command, False)
        line_list = out.strip().split('\n')
        for line in line_list:
            if 'tests passed' in line:
                if line.split(' ')[0] != line.split(' ')[2]:
                    raise Exception('Not all tests passed')
    elif 'k' in comm_list[1]:
        out = __choose_run_folder(command, False)
        check_enabled_device_num(out)
        enabled_device_num = int((lnx_exec_command('cat /home/logs/enabled_num.log')[1]).strip())
        enabled_wq_num = __check_enabled_wq_num(out)
        if enabled_device_num != cpu_num * device_num:
            logger.error('Not all device detected')
            raise Exception('Not all device detected')
        else:
            check_keyword([f'enabled {enabled_wq_num} wq(s) out of {enabled_wq_num}'], out,
                          'Device random test fail')


if __name__ == '__main__':
    args_parse = setup_argparse()
    acce_random_test(args_parse.cmd,args_parse.mode,args_parse.num,args_parse.unzip)
 
