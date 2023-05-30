import sys
import argparse
from lnx_exec_with_check import lnx_exec_command
from vm_copy import *
from vm_execute import *

def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='copy api from host to guest vm, and add necessary path'
                    '--port <the host port mapping to vm>')
    parser.add_argument('-p', '--port', default='', dest='port', action='store', help='the host port list mapping to vm,separated by ,')
    parser.add_argument('-n', '--num', default='', dest='num', action='store', help='the number of port to launch if port not specified by -p')
    parser.add_argument('-u', '--user', default='root', dest='user', action='store', help='the user name of vm')
    parser.add_argument('-w', '--password', default='password', dest='password', action='store',
                        help='the password of vm')
    ret = parser.parse_args(args)
    return ret
'''
def vm_config(ip,port,username,password):
    remote_exec_cmd(ip, port, username, password, 'mkdir -p /home')
    remote_exec_cmd(ip, port, username, password, 'mkdir -p /home/BKCPkg')
    remote_exec_cmd(ip, port, username, password, 'mkdir -p /home/BKCPkg/accelerator_inband')
    vm_copy('/home/BKCPkg/accelerator_inband', '/home/BKCPkg/', port, username, password,ip)
    remote_exec_cmd(port, username, password, 'rm -rf $HOME/.bashrc',ip)
    vm_copy('/root/.bashrc', '/root/.bashrc', ip, port, username, password)
    remote_exec_cmd(port, username, password, 'cd ~ && source ~/.bashrc',ip)

'''
def vm_config_parallel(portlist_str, portnum, user, password, ip='localhost'):
    #if portlist_str == '':
    #    _, out, err = lnx_exec_command('cat /home/logs/port.log', timeout=60)
    #    portlist = out.strip().split('\n')
    #    portlist_str = ','.join(portlist)
    #vm_exec_cmd_parallel(portlist_str, user, password, 'mkdir -p /home',ip)
    #vm_exec_cmd_parallel(portlist_str, user, password, 'mkdir -p /home/BKCPkg',ip)
    lnx_exec_command('pip3 install paramiko setuptools_rust paramiko scp', timeout=100 * 60)
    vm_exec_cmd_parallel(portlist_str, portnum, user, password, 'mkdir -p /home/BKCPkg/accelerator_inband',ignore_err='True')
    vm_exec_cmd_parallel(portlist_str, portnum, user, password, 'mkdir -p /home/acce_tools',ignore_err='True')
    vm_copy_parallel('/home/BKCPkg/accelerator_inband', '/home/BKCPkg/', portlist_str, portnum, user, password)
    vm_exec_cmd_parallel(portlist_str, portnum, user, password, 'rm -rf $HOME/.bashrc')
    vm_copy_parallel('/root/.bashrc', '/root/.bashrc', portlist_str, portnum, user, password)
    vm_exec_cmd_parallel(portlist_str, portnum, user, password, 'cd ~ && source ~/.bashrc',ip)
    return

if __name__ == '__main__':
    args_parse = setup_argparse()
    vm_config_parallel(args_parse.port,args_parse.num,args_parse.user,args_parse.password)


