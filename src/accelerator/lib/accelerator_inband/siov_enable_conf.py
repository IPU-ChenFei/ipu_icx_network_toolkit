import sys
import argparse
from lnx_exec_with_check import lnx_exec_command
from log_keyword_check import check_keyword
from get_cpu_num import get_cpu_num

def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='revise configuration file number of adis parameter '
                    '--siov <number of Adis>'
                    '--number <the number of devices to confugure>'
                    '--all_sym <assign all ADIs to sym or half sym and half dc>')
    parser.add_argument('-s', '--siov', required=True, dest='siov', action='store', help='number of Adis')
    parser.add_argument('-n', '--number', default='all', dest='number', action='store', help='the number of devices to confugure')
    parser.add_argument('-a', '--all_sym', default='True', dest='all_sym', action='store', help='assign all ADI to sym or half sym and half dc')
    ret = parser.parse_args(args)
    return ret

def siov_enable_conf(siov_num, number, all_sym):
    if number == 'all':
        get_cpu_num()
        cpu_num = int((lnx_exec_command('cat /home/logs/cpu_num.log')[1]).strip())
        device_number = 4 * cpu_num
    else:
        device_number = number
    for i in range(device_number):
        lnx_exec_command(f"cd /etc/ && sed -i 's/NumberAdis.*/NumberAdis = {siov_num}/g' /etc/4xxx_dev{i}.conf", timeout=10 * 60)
        if all_sym == "True":
            lnx_exec_command(f"cd /etc/ && sed -i 's/NumberCyInstances.*/NumberCyInstances = 0/g' /etc/4xxx_dev{i}.conf", timeout=10 * 60)
            lnx_exec_command(f"cd /etc/ && sed -i 's/NumberDcInstances.*/NumberDcInstances = 0/g' /etc/4xxx_dev{i}.conf", timeout=10 * 60)
            lnx_exec_command(f"cd /etc/ && sed -i 's/NumberCyInstances.*/NumberCyInstances = 0/g' /etc/4xxx_dev{i}.conf", timeout=10 * 60)
            lnx_exec_command(f"cd /etc/ && sed -i 's/NumberDcInstances.*/NumberDcInstances = 0/g' /etc/4xxx_dev{i}.conf", timeout=10 * 60)
    return

if __name__ == '__main__':
    args_parse = setup_argparse()
    siov_enable_conf(args_parse.siov, args_parse.number, args_parse.all_sym)



