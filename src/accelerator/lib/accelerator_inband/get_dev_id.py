from lnx_exec_with_check import lnx_exec_command
import sys
import argparse
from constant import *
from log import logger
from get_cpu_num import get_cpu_num


def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='Get device id'
                    '--id <accelerator type> {dsa, iax, qat, dlb}'
                    '--pf <device pf number>'
                    '--vf <device vf number>')
    parser.add_argument('-i', '--ip', required=True, dest='ip', action='store', help='accelerator type')
    parser.add_argument('-p', '--pf', required=True, dest='pf', action='store', help='device pf number')
    parser.add_argument('-v', '--vf', required=True, dest='vf', action='store', help='device vf number')
    ret = parser.parse_args(args)
    return ret


def get_dev_id(ip, pf, vf):
    """
          Purpose: Get single QAT device id
          Args:
              ip: Which device need to check the device status, eg: 'qat','dlb','dsa'
              pf: which device pf need to search, input number of the device
                    eg: 0,1...8,begin from 0
              vf_num: which device vf number need to search
                    eg:1,2....16,begin from 1
          Returns:
              Yes: device id  --> '0000:6d:00.0'
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Get single QAT device id
                    get_qat_dev_id('qat', 0, 0)
                    return --> '0000:6d:00.0'
    """
    pf = int(pf)
    vf = int(vf)
    get_cpu_num()
    cpu_num = int((lnx_exec_command('cat /home/logs/cpu_num.log')[1]).strip())
    if ip == 'qat':
        _, out, err = lnx_exec_command(f'lspci | grep {qat_id}', timeout=60)
        line_list = out.strip().split('\n')
        qat_device_list = []
        for line in line_list:
            str_list = line.split(' ')
            word_list = str_list[0].split(':')  # ['6b','00.0']
            qat_device_list.append(word_list[0])
        if pf > len(qat_device_list) or vf > 16:
            logger.error('the number of given PF exceeds the maximum PF get number')
            raise Exception('the number of given PF exceeds the maximum PF get number')
        else:
            quotient, remainder = divmod(vf, 8)
            dev_id = f'0000:{qat_device_list[pf]}:0{quotient}.{remainder}'  # [' 0000:6b:00.0'] or  [' 0000:6b:00.03']
            # return dev_id
            lnx_exec_command('mkdir -p /home/logs/')
            lnx_exec_command('rm -rf /home/logs/dev_id.log')
            lnx_exec_command(f'echo {dev_id} > /home/logs/dev_id.log')
    elif ip == 'dsa':
        _, out, err = lnx_exec_command(f'lspci | grep {dsa_id}', timeout=60)
        line_list = out.strip().split('\n')
        device_list = []
        i = 0
        if i < cpu_num * dsa_device_num:
            for line in line_list:
                str_list = line.split()  # ['6a:01.0', 'System'... ]
                dev_id = '0000:' + str_list[i]  # '0000:6a:01.0'
                device_list.append(dev_id)  # ['0000:6a:01.0','0000:6f:01.0']
            i += 1
        # return device_list[pf]    # return dev_list
        lnx_exec_command('mkdir -p /home/logs/')
        lnx_exec_command('rm -rf /home/logs/dev_id.log')
        lnx_exec_command(f'echo {device_list[pf]} > /home/logs/dev_id.log')


if __name__ == '__main__':
    args_parse = setup_argparse()
    get_dev_id(args_parse.ip, args_parse.pf, args_parse.vf)


