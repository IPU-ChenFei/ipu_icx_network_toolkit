import importlib
import re
import time
import traceback
import sys
import pexpect

from ppexpect import LinuxChildShell
install_path = "/home"
SGX_path = f"/home/BKCPkg/domains/virtualization/tools/SGX"
sut_install_sgx = f'{SGX_path}/install_sgx.log'
SGX_BIN = "sgx_linux_x64_sdk_2.15.100.3.bin"


class LinuxChildShellLog(LinuxChildShell):
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


def __dynamic_import(module):
    """
    dynamic import
    :param module:module name
    :return: module
    """
    return importlib.import_module(module)


def __ssh_connect(ip):
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


def install_sgx(args):
    global temp_file, cs
    try:
        ip = args[0]

        print(f'+++++ start_vm +++++ ')
        cs = __ssh_connect(f'{ip}')
        temp_file = open(f'{sut_install_sgx}', 'wb')

        cs.child.logfile = temp_file

        cs.send(f'cd {SGX_path}')
        cs.expect(']#')

        cs.send(f"chmod +x {SGX_BIN}")
        cs.expect(']#')

        cs.send(f'./{SGX_BIN}')
        cs.expect('] :')
        cs.send("yes\n")
        time.sleep(10)
        cs.expect(']#')
        cs.output()

    except pexpect.EOF:
        traceback.print_exc()
    finally:
        temp_file.close()
        cs.kill()


if __name__ == '__main__':

    if len(sys.argv) >= 3:
        print(len(sys.argv))
        module = __dynamic_import('sgx_install')
        # python dpdk_expect.py method_name args path
        getattr(module, sys.argv[1])(sys.argv[2:])
    else:
        print('args value no correct')
        print('python sgx_install.py install ip')
        sys.exit()
