import importlib
import os
import re
import time
import traceback
import sys
from argparse import ArgumentParser
import pexpect
from ppexpect import LinuxChildShell

"""
    use for expect common.
    
        eg: 
            python vm_connect.py -m console -vm rhel8.4 -cmd "ifconfig" -cmd "pwd" ..
             
            python vm_connect.py -m ssh -ip 192.168.1.2 -cmd "ifconfig" -cmd "pwd" .. 
            
            python vm_connect.py 
            -m "qemu-system-x86_64 -name guestvm1 -machine 
            q35 -enable-kvm -global kvm-apic.vapic=false -m 10240 -cpu host -drive format=raw,
            file=/home/images/centos-8.4.2105-embargo-coreserver-202110131506.img -bios /home/OVMF.fd -smp 16 -serial 
            mon:stdio -net nic,model=virtio -nic user,hostfwd=tcp::2222-:22 -nographic" 
            -acmd "login: & root" 
            -acmd "]# &  " .. 
            -acmd "password: & password" 
            -acmd "]# & start[10]" 
            -acmd "]# &  " .. 
             


"""
install_path = "/home"


def __dynamic_import(module):
    """
    dynamic import
    :param module:module name
    :return: module
    """
    return importlib.import_module(module)


class LinuxChildShellLog(LinuxChildShell):
    """
        addition logs print
    """

    def send(self, cmd):
        """
        Send cmd to child process and print cmd
        """
        print(f'Execute expect cmd >>> {cmd}')

        return self.child.sendline(cmd)

    def output(self):
        """
        Results from child process
        """
        res = self.child.before + self.child.after
        print(res.decode('utf-8'))
        return res


def __ssh_connect(ip):
    # type: (str) -> object
    cs = None
    try:
        print(f'+++++ ssh {ip} +++++ ')
        cs = LinuxChildShellLog(f'ssh {ip}')
        a = cs.expect(['password:', 'The authenticity of host'])
        if a == 0:
            cs.send('password')
            cs.expect("]#")
            print('connect successful !')
        if a == 1:
            print('this ip will be added to know_host files!')
            cs.send('yes')
            cs.expect('password:')
            cs.send('password')
            cs.expect("]#")

    except pexpect.EOF:
        traceback.print_exc()
    return cs


def __vm_console(vm_name):
    # type:(str) -> object

    try:
        print(f'+++++ virsh console {vm_name} +++++ ')
        cs = LinuxChildShellLog(f'virsh console {vm_name}')
        cs.expect("Escape character is")
        cs.send('\n')
        a = cs.expect(['login:', ']#'])
        if a == 0:
            cs.send('root\n')
            cs.expect('Password:')
            cs.send('password')

        cs.expect("]#")
        print(cs.output().decode("utf-8"))
        print('connect successful !')
    except pexpect.EOF:
        traceback.print_exc()
        cs.kill()
        print("connect failed")
        print("try vm run : "
              "systemctl enable serial-getty@ttyS0.service\r\n"
              "systemctl start serial-getty@ttyS0.service")
        sys.exit()
    return cs


def __wait_sleep(sec):
    # type:(int) -> None
    print("wait time sleep : [{}]".format(sec))
    time.sleep(sec)


def scp_file(args):
    print('============= SCP FILES============')
    print(type(args))
    print(args)
    ip = args[0]
    local_path = args[1]
    if len(args) <= 2:
        remote_path = install_path
    else:
        remote_path = args[2]
    cs = None
    try:
        print(f'+++++ scp -r {local_path} root@{ip}:{remote_path} +++++ ')
        cs = LinuxChildShellLog(f'scp -r {local_path} root@{ip}:{remote_path}')
        a = cs.expect(['password:', 'The authenticity of host'])
        if a == 0:
            cs.send('password')
            time.sleep(10)
            cs.output()
            print('connect successful !')
        if a == 1:
            print('this ip will be added to know_host files!')
            cs.send('yes')
            cs.expect('password:')
            cs.send('password')
            time.sleep(10)
            cs.output()
    except pexpect.EOF:
        traceback.print_exc()


def execute_commands(args):
    cs = None
    temp_file = None
    f_name = args.method.split(" ")[0] + ".log"
    if args.log_file is not None:
        f_name = args.log_file
    if args.method == 'console':
        cs = __vm_console(args.vm_name)
    elif args.method == 'ssh':
        cs = __ssh_connect(f'{args.ip}')
    else:
        cs = LinuxChildShellLog(args.method)
    try:
        temp_file = open(f_name, 'wb')

        cs.child.logfile = temp_file
        # answer cmd "login: & root"
        w_time = 1
        if args.acommands is not None:
            if str(args.acommands).find("&") == -1:
                print("answer commands format is not correct")
                sys.exit()

            for awcmd in args.acommands:
                # login: & root
                cmds = awcmd.split("&")
                cs.expect(cmds[0].strip())
                cmd = cmds[1].strip()
                # time handle
                if re.search(r"\[+", cmds[1].strip()) is not None:
                    p = re.compile(r'[[](.*?)[]]', re.S)
                    w_time = int(re.findall(p, cmds[1].strip())[0])
                    cmd = cmds[1].strip().split("[")[0]
                cs.send(cmd)
                __wait_sleep(w_time)
                cs.output()

        if args.commands is not None:
            # common cmd
            for cmd in args.commands:
                if re.search(r"\[+", cmd.strip()) is not None:
                    p = re.compile(r'[[](.*?)[]]', re.S)
                    w_time = int(re.findall(p, cmd.strip())[0])
                    cmd = cmd.strip().split("[")[0]
                cs.send(cmd.strip())
                __wait_sleep(w_time)
                cs.expect(']#')
                cs.output()
    except pexpect.EOF:
        traceback.print_exc()
    finally:
        print("connect close")
        temp_file.close()
        cs.kill()


if __name__ == '__main__':
    parser = ArgumentParser(epilog="Example:python vm_connect.py\n\r -m console/ssh")
    parser.add_argument("-m", "--method", dest='method', type=str, required=True, help='an method console or ssh')
    parser.add_argument('-execute_cmd', "--execute_cmd", default="execute_commands", dest='execute_cmd', type=str)
    parser.add_argument('-cmd', "--commands", dest='commands', type=str, action='append',
                        help='commands')
    parser.add_argument('-acmd', "--acommands", dest='acommands', type=str, action='append',
                        help='answer commands')
    parser.add_argument("-ip", "--ip", dest='ip', type=str, help='an vm_name str')
    parser.add_argument("-vm", "--vm_name", dest='vm_name', type=str, help='an vm_name str')
    parser.add_argument("-path", "--path", dest='path', type=str, help='an path str')
    parser.add_argument("-log_file", "--log_file", dest='log_file', default=None, type=str, help='an logfile str')

    args = parser.parse_args()
    print(args)
    file_name = os.path.basename(sys.argv[0]).split(".")[0]
    module = __dynamic_import(file_name)

    # python dpdk_expect.py method_name args path
    getattr(module, args.execute_cmd)(args)
