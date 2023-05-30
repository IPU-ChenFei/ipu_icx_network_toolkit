import sys
import argparse
from lnx_exec_with_check import lnx_exec_command
from constant import *
import time
import paramiko
from resource_config_login import port_gen
import re
import _thread
import threading

def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='copy file from host to guest vm'
					'--ip <the ip of the vm>'
					'--port <the host port mapping to vm>'
                    '--user<the user name of vm>'
					'--password <the password of vm>'
					'--cmd <the command to be executed>')
    parser.add_argument('-p', '--port', default='', dest='port', action='store', help='the host port list mapping to vm,separated by ,')
    parser.add_argument('-u', '--user', default='root', dest='user', action='store', help='the user name of vm')
    parser.add_argument('-w', '--password', default='password', dest='password', action='store', help='the password of vm')
    parser.add_argument('-c', '--cmd', required=True, dest='cmd', action='store', help='the cmd to be executed')
    parser.add_argument('-n', '--num', default='', dest='num', action='store', help='the number of port to launch if port not specified by -p')
    parser.add_argument('-i', '--ignore_err', default='False', dest='ignore_err', action='store', help='ignore the error of execution in vm')
    ret = parser.parse_args(args)
    return ret
	
def remote_exec_cmd(remote_port, remote_un, remote_pwd, cmd, remote_ip, ignore_err='False'):
    """
    Function to execute the cmd in remote machine and returns the output
    :param remote_ip: IP of the Remote machine
    :type remote_ip: string
    :param remote_port: User port of Jump Host(Test Pilot)
    :type remote_port: string
    :param remote_pwd: Password of the Jump Host
    :type remote_pwd: String
    :param cmd: cmd to be executed on the remote machine
    :type: cmd: String
    :return: Output of the executed string
    :rtype:str if the cmd prints the output, else returns -1
    """
    try:
        remote_obj = paramiko.SSHClient()
        remote_obj.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        remote_obj.connect(remote_ip, remote_port,username=remote_un, password=remote_pwd)
        stdin, stdout, stderr = remote_obj.exec_command(cmd)
        if cmd == 'reboot' or cmd == 'shutdown now' or ignore_err != 'False':
            time.sleep(20)
            return 0
        out = stdout.read().decode('UTF-8')
        print('execute in '+ str(remote_port), out)
        if stdout.channel.recv_exit_status() !=0:
            print('Could not connect with the remote machine {} or could not execute the cmd {}'.format(remote_port, cmd))
            return -1
    except:
        print('Could not connect with the remote machine {} or could not execute the cmd {}'.format(remote_port, cmd))
        return -1

    if out != '':
        print('Returning the output, after executing the cmd {}'.format(cmd))
        return out

    elif out == '':
        print('Command execution returned nothing.. Checking for status of cmd execution..')
        stdin, stdout, stderr = remote_obj.exec_command('echo $?')
        null_out = int(stdout.read().decode('UTF-8'))

        if null_out == 0:
            print('The cmd {} executed successfully in the machine {}'.format(cmd, remote_ip))
            return 0
        else:
            print('Could not execute the command {} in {}'.format(cmd, remote_ip))
            return -1
    return out


class TaskThread(threading.Thread):

    def __init__(self, func, args=()):
        super(TaskThread, self).__init__()
        self.func = func
        self.args = args

    def run(self):
        print("start func {}".format(self.func.__name__))
        self.result = self.func(*self.args)

    def get_result(self):
        try:
            return self.result
        except Exception as ex:
            print(ex)
            return "ERROR"


def vm_exec_cmd_parallel(remote_portlist_str, remote_portnum, remote_un, remote_pwd, cmd, ignore_err='False', remote_ip='localhost'):
    """
    Function to execute the cmd in remote machine and returns the output
    :param remote_portlist: User port list of Jump Host(Test Pilot)
    :type remote_portlist: string
    :param remote_pwd: Password of the Jump Host
    :type remote_pwd: String
    :param cmd: cmd to be executed on the remote machine
    :type: cmd: String
    :return: Output of the executed string
    :rtype:str if the cmd prints the output, else returns -1
    """
    if remote_portlist_str != '':
        remote_portlist = remote_portlist_str.strip().split(',')
    else:
        if remote_portnum!= '':
            port_gen(int(remote_portnum),False)
        _, out, err = lnx_exec_command('cat /home/logs/port.log', timeout=60)
        return_code, out, err = lnx_exec_command('cat /home/logs/port.log', timeout=60)
        if return_code:
            raise Exception('no port specify')
        remote_portlist = out.strip().split('\n')
    ts = []
    for remote_port in remote_portlist:
        try:
            t = TaskThread(remote_exec_cmd, args=(remote_port, remote_un, remote_pwd, cmd, remote_ip, ignore_err))
            #t = threading.Thread(target=remote_exec_cmd, args=(remote_port, remote_un, remote_pwd, cmd, remote_ip, ignore_err,))
            t.start()
            ts.append(t)
        except:
            print("Error: unable to start thread")
    for t in ts:
        t.join()
        if t.get_result() == -1:
            raise Exception(f'Execution of "{cmd}" in VM(s) failed')
    return
	
if __name__ == '__main__':
    args_parse = setup_argparse()
    vm_exec_cmd_parallel(args_parse.port, args_parse.num, args_parse.user, args_parse.password, args_parse.cmd,args_parse.ignore_err)