#!/usr/bin/env python

"""
This module suits for writing subshell scripts running on target system, just like dpdk pmd or generator
"""

import pexpect
import time


class LinuxChildShell(object):
    """
    Create a new child process to interactive with a program

    ::Dependencies
        1. pip install pexpect
        2. Python 3.3+, or Python 2.7

    ::Usage Demo
        print('+++++ CHILD PROCESS 1 +++++ (Demo child process for running cmds on a remote system)')
        cs = LinuxChildShell('ssh 10.239.174.182')
        cs.expect('password:')
        cs.send('intel@123')
        cs.expect(']#')
        print(cs.run(cmd='ping -c 5 localhost', exp=']#'))
        print(cs.run(cmd='ping localhost', exp='ttl=64'))
        cs.kill()

        print('+++++ CHILD PROCESS 2 +++++ (Another child process for running cmds on a remote system)')
        cs2 = LinuxChildShell('ssh 10.239.174.182')
        cs2.expect('password:')
        cs2.send('intel@123')
        cs2.expect(']#')
        print(cs2.run(cmd='ls /', exp=']#'))
        print(cs2.run(cmd='ping localhost', exp='icmp_seq=5'))
        cs2.kill()

        print('+++++ CHILD PROCESS 3 +++++ (Run long-run cmds with Ctrl-C)')
        cs3 = LinuxChildShell('ssh 10.239.174.182')
        cs3.expect('password:')
        cs3.send('intel@123')
        cs3.expect(']#')
        print(cs3.run(cmd='ping localhost', exp=']#', intr_timeout=5))
        print(cs3.run(cmd='ping localhost', exp=']#', intr_timeout=20))
        cs3.kill()
    """
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


if __name__ == '__main__':
    print('+++++ CHILD PROCESS 1 +++++ (Demo child process for running cmds on a remote system)')
    cs = LinuxChildShell('ssh 10.239.174.182')
    cs.expect('password:')
    cs.send('intel@123')
    cs.expect(']#')
    print(cs.run(cmd='ping -c 5 localhost', exp=']#'))
    print(cs.run(cmd='ping localhost', exp='ttl=64'))
    cs.kill()

    print('+++++ CHILD PROCESS 2 +++++ (Another child process for running cmds on a remote system)')
    cs2 = LinuxChildShell('ssh 10.239.174.182')
    cs2.expect('password:')
    cs2.send('intel@123')
    cs2.expect(']#')
    print(cs2.run(cmd='ls /', exp=']#'))
    print(cs2.run(cmd='ping localhost', exp='icmp_seq=5'))
    cs2.kill()

    print('+++++ CHILD PROCESS 3 +++++ (Run long-run cmds with Ctrl-C)')
    cs3 = LinuxChildShell('ssh 10.239.174.182')
    cs3.expect('password:')
    cs3.send('intel@123')
    cs3.expect(']#')
    print(cs3.run(cmd='ping localhost', exp=']#', intr_timeout=5))
    print(cs3.run(cmd='ping localhost', exp=']#', intr_timeout=20))
    cs3.kill()