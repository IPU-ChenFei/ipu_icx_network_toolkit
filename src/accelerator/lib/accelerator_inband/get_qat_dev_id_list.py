from lnx_exec_with_check import lnx_exec_command
import sys
import argparse
from get_dev_id import get_dev_id


def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='Get device id list'
                    '--pf <device pf number>'
                    '--vf_num <device vf number>')
    parser.add_argument('-p', '--pf', required=True, dest='pf', action='store', help='device pf number')
    parser.add_argument('-v', '--vf_num', required=True, dest='vf_num', action='store', help='device vf number')
    ret = parser.parse_args(args)
    return ret


def get_qat_dev_id_list(pf, vf_num):
    """
          Purpose: Get list of QAT device ID
          Args:
              pf: which QAT pf need to search, input number of the device
                    eg: 0,1...8,begin from 0
              vf_num: which QAT vf number need to search
                    eg:1,2....16,begin from 1
          Returns:
              Yes: QAT device id list
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: Check all QAT device
                    get_qat_dev_id_list(0, 2)
                    return --> ['0000:6b:00.1', '0000:6b:00.2']
    """
    pf = int(pf)
    vf_num = int(vf_num)
    dev_list = []
    for i in range(1, vf_num + 1):
        get_dev_id('qat', pf, i)
        dev_id = (lnx_exec_command('cat /home/logs/dev_id.log')[1]).strip()
        dev_list.append(dev_id)
    # return dev_list
    lnx_exec_command('mkdir -p /home/logs/')
    lnx_exec_command('rm -rf /home/logs/qat_dev_id_list.log')
    lnx_exec_command(f'echo {dev_list} > /home/logs/qat_dev_id_list.log')


if __name__ == '__main__':
    args_parse = setup_argparse()
    get_qat_dev_id_list(args_parse.pf, args_parse.vf_num)



