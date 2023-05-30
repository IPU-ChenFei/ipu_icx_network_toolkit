from lnx_exec_with_check import lnx_exec_command
import sys
import argparse
from constant import *


def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='Get device id list'
                    '--pf <device pf number>'
                    '--vf <device vf number>')
    parser.add_argument('-p', '--pf', required=True, dest='pf', action='store', help='device pf number')
    parser.add_argument('-v', '--vf_num', required=True, dest='vf_num', action='store', help='device vf number')
    ret = parser.parse_args(args)
    return ret


def get_dlb_dev_id_list(pf, vf_num):
    """
          Purpose: Get list of DLB device ID
          Args:
              pf: DLB PF device number
              vf: How many DLB VF device need to create
          Returns:
              Yes: DLB device ID list --> ['0000:6d:00.0','0000:72:00.0']
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: get DLB True device 0 and create 2 DLB Vietual device for Platform
                    get_dlb_dev_id_list(0, 2)
                    return ['0000:6d:00.1','0000:6d:00.2']
    """
    pf = int(pf)
    vf_num = int(vf_num)
    _, out, err = lnx_exec_command(f'lspci | grep {dlb_id}', timeout=60)
    line_list = out.strip().split('\n')
    dlb_list = []
    dev_id_list = []
    for line in line_list:
        str_list = line.split()  # ['6d:00.0', 'Co-processor:'...]
        words_list = str_list[0].split('.')  # ['6d:00', '0' , ....]
        if words_list[1] == '0':
            dlb_deviceid = '0000:' + str_list[0]  # '0000:6d:00.0''0000:72:00.0'
            dlb_deviceid = dlb_deviceid.split(':')
            dlb_list.append(dlb_deviceid[1])  # ['0000:6d:00.0','0000:72:00.0']
    quotient, remainder = divmod(vf_num, 8)
    if vf_num == 0:
        dev_id_list.append(f'0000:{dlb_list[pf]}:0{quotient}.{remainder}')  # ['0000:6d:00.0','0000:72:00.0']
    else:
        for i in range(1, vf_num + 1):
            if i < 8:
                dev_id_list.append(f'0000:{dlb_list[pf]}:00.{i}')
            elif 7 < i < 16:
                dev_id_list.append(f'0000:{dlb_list[pf]}:01.{i - 8}')
            else:
                dev_id_list.append(f'0000:{dlb_list[pf]}:0{quotient}.{remainder}')  # ['0000:6d:00.1','0000:6d:00.2']
    # return dev_id_list  # ['0000:6d:00.0','0000:72:00.0']
    lnx_exec_command('mkdir -p /home/logs/')
    lnx_exec_command('rm -rf /home/logs/dlb_list.log')
    lnx_exec_command(f'echo {dev_id_list} > /home/logs/dlb_list.log')


if __name__ == '__main__':
    args_parse = setup_argparse()
    get_dlb_dev_id_list(args_parse.pf, args_parse.vf_num)



