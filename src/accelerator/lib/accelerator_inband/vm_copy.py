import argparse
import os
import sys
from lnx_exec_with_check import lnx_exec_command
import paramiko
from scp import SCPClient
from resource_config_login import port_gen
import threading

def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='copy file from host to guest vm'
                    '--source <source file path in host>'
                    '--destination <destination file path in guest vm>'	
                    '--port <the host port mapping to vm>'
                    '--user <the user name of vm>'
                    '--password <the password of vm>')
    parser.add_argument('-s', '--src', required=True, dest='src', action='store', help='the path of source file')
    parser.add_argument('-d', '--des', required=True, dest='des', action='store', help='the path of destination file')
    parser.add_argument('-p', '--port', default='', dest='port', action='store', help='the host port list mapping to vm,separated by ,')
    parser.add_argument('-n', '--num', default='', dest='num', action='store', help='the number of port to launch if port and -p')
    parser.add_argument('-u', '--user', default='root', dest='user', action='store', help='the user name of vm')
    parser.add_argument('-w', '--password', default='password', dest='password', action='store', help='the password of vm')
    ret = parser.parse_args(args)
    return ret


def scp_local_to_remote(ssh_instance, src_path, dst_path):
    """Function to copy local file to remote destination

        :param ssh_instance: return value from ssh_connect(,,)
        :type ssh_instance: hex integer
        :param src_path: Local source directory path
        :type src_path: string e.g. '/root/home/user'
        :param dst_path: Remote destination directory path
        :type dst_path: string e.g. '/root/home/user'
        :return: 0 on success
        :rtype: integer
    """
    # SCPCLient takes a paramiko transport as an argument
    scp = SCPClient(ssh_instance.get_transport())
    if os.path.isfile(src_path) == True:
        scp.put(src_path, dst_path)
    # Uploading the 'test' directory with its content in the
    # '/home/user/dump' remote directory
    else:
        scp.put(src_path, recursive=True, remote_path=dst_path)
    print('SCP Local to Remote is Successful. Local_path: {}, Remote_path: {}'.format(src_path, dst_path))
    scp.close()
    return 0


def vm_copy(src_path, des_path, hostport, username='root', password='password',ip='localhost'):
    ssh_instance = paramiko.SSHClient()
    ssh_instance.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh_instance.connect(ip, hostport, username, password)
    scp_local_to_remote(ssh_instance, src_path, des_path)

def vm_copy_parallel(src_path, des_path, portlist_str, portnum, user, password,ip='localhost'):
    if portlist_str != '':
        portlist = portlist_str.strip().split(',')
    else:
        if portnum!= '':
            port_gen(int(portnum),False)
        return_code, out, err = lnx_exec_command('cat /home/logs/port.log', timeout=60)
        if return_code:
            raise Exception('no port specify')
        portlist = out.strip().split('\n')
    ts = []
    for port in portlist:
        try:
            t = threading.Thread(target=vm_copy, args=(src_path, des_path, port, user, password,))
            t.start()
            ts.append(t)
        except:
            print("Error: unable to start thread")
    for t in ts:
        t.join()
    return

if __name__ == '__main__':
    args_parse = setup_argparse()
    vm_copy_parallel(args_parse.src, args_parse.des, args_parse.port, args_parse.num, args_parse.user, args_parse.password)


