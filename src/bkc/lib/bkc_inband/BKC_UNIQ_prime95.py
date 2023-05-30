
# from steps_lib.domains.network.tool.ppexpect import LinuxChildShell
import time
import os
import pexpect

class LinuxChildShell(object):
    def __init__(self, prog):
        self.child = pexpect.spawn(prog)

    def expect(self, exp=None):
        """
        Expected termination flag in child process
        """
        return self.child.expect(exp if exp else pexpect.EOF)

    def send(self, cmd):
        """
        Send cmd to child process
        """
        return self.child.sendline(cmd)

    def output(self):
        """
        Results from child process
        """
        return self.child.before + self.child.after

    def run(self, cmd, exp=None, intr_timeout=None):
        """
        Run command in child process, and return the results

        Noted:
            If execute the long-run command, and even this API returns,
            the child process is still there, which may block the following executions,
            so, the long-run command should be the last run() call for a specific instance

            But if you want to run long-run command with specific timeout, and then stop it,
            just specify intr_timeout=xxx, that's it

        :param cmd: command in child process
        :param exp:
            1. the delimiter that marks the expected output,
               where you think the output is enough for current execution
            2. if exp == None, then it defaults to "child process complete",
               but most of time, in interactive program, the child process always alive,
               then you will see the TIMEOUT error
        :param intr_timeout: cmd execution timeout
        :return: output from child process
        """
        self.send(cmd)

        if not intr_timeout:
            self.expect(exp)
        else:
            intr_timeout = int(intr_timeout)
            time.sleep(intr_timeout)
            self.child.sendcontrol('c')
            self.expect(exp)
        return self.output()

    def kill(self):
        """
        Kill child process
        """
        return self.child.terminate(force=True)


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


def __ssh_connect(ip):
    cs = None
    try:
        print(f'+++++ ssh {ip} +++++ ')
        cs = LinuxChildShellLog(f'ssh {ip}')
        a = cs.expect(['password:', 'The authenticity of host'])
        if a == 0:
            cs.send('password')
            cs.expect(']#')
            print('connect successful !')
        if a == 1:
            print('this ip will be added to know_host files!')
            cs.send('yes')
            cs.expect('password:')
            cs.send('password')
            cs.expect(']#')

    except pexpect.EOF:
        traceback.print_exc()
    return cs

#caculate number of  physical cores 
cores_per_socket = os.popen("lscpu |grep 'Core(s) per socket' |awk '{print $4}'").read().strip()
sockets = os.popen(" lscpu |grep 'Socket(s):' |awk '{print $2}'").read().strip()
phy_cores_num = int(cores_per_socket)*int(sockets)

print(f"System has {phy_cores_num} cores in total !")

prime95 = '/opt/prime95/prime95.log'

path = '/opt/prime95/'
def run_prime95():
    cs = __ssh_connect('localhost')
    cs.send(f'cd {path}')
    temp_file = open(f'{prime95}', 'wb')
    cs.child.logfile = temp_file
    if os.path.exists(f"{path}/local.txt"):
        os.system(f"rm -rf {path}/local.txt ")
    if os.path.exists(f"{path}/prime.txt"):
        print("-------------- exist !")
        os.system(f"rm -rf {path}/prime.txt ")
    cs.send('./mprime -dm| tee prime95.log')
    cs.expect(':')
    cs.send('N')
    cs.expect(':')
    time.sleep(1)
    cs.send(f'{phy_cores_num}')
    time.sleep(1)
    cs.expect('\): ')
    cs.send('Y')
    cs.expect(':')
    time.sleep(1)
    cs.send('4')
    cs.expect(':')
    time.sleep(1)
    cs.send('N')
    cs.expect(':')
    time.sleep(1)
    cs.send('N')
    cs.expect(':')
    time.sleep(1)
    cs.send('Y')
    cs.expect(':')

    time.sleep(240*60)
    cs.output()
    temp_file.close()
    cs.kill()

    check_log = os.popen(f'cat {path}prime95.log |grep  -v "NOTE: if you fail the blend test"|grep -iE "Error|Fail|Failed"').read().strip()
    if len(check_log) == 0:
        print("Prime95 Test PASS!")
        os.system(f"echo 'Prime95 Test PASS!' >> {path}prime95.log")
    else:
        print("Prime95 Test FAIL!")
        os.system(f"echo 'Prime95 Test FAIL!' >> {path}prime95.log")
        raise

if __name__ == '__main__':
    run_prime95()
