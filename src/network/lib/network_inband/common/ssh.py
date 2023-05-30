#!/usr/bin/env python
import re

import paramiko
import subprocess
import sys
import os
import traceback
import getpass
import stat
import socket
import time

from src.network.inband.common.log import log
from src.network.inband.common.log import DEFAULT_LOG_PATH


paramiko.util.log_to_file(os.path.join(DEFAULT_LOG_PATH, 'ssh.log'))
USEGSSAPI = False
DOGSSAPIKEYEXCHANGE = False
PORT = 22
CONNECT_TIMEOUT = 60
EXEC_TIMEOUT = 1800


class Result:
    exitcode = -sys.maxsize - 1
    stdout = ''
    stderr = ''


class SSHClient(object):
    def __init__(self,
                 hostname=None,
                 port=None,
                 username=None,
                 password=None,
                 family=None):
        """
        Initialize a ssh client to remote system

        :param hostname: remote hostname or ip address
        :param port: ssh port, default is 22
        :param username: remote login username
        :param password: remote login password
        :param family: remote system os family
        """
        if not hostname:
            self.hostname = input('Hostname: ')
        else:
            self.hostname = hostname
        if not port:
            self.port = PORT
        else:
            self.port = int(port)
        if not username:
            default_username = getpass.getuser()
            self.username = input('Username <%s>: ' % default_username)
        else:
            self.username = username
        if not password:
            if not (USEGSSAPI and DOGSSAPIKEYEXCHANGE):
                self.password = getpass.getpass('Password for <%s@%s>: ' % (username, hostname))
        else:
            self.password = password
        if not family:
            self.family = 'linux'
        else:
            self.family = family

        if self.hostname.find('@') >= 0:
            self.username, self.hostname = self.hostname.split('@')
        if self.hostname.find(':') >= 0:
            self.hostname, self.port = self.hostname.split(':')
            self.port = int(self.port)

        self.client = None
        self.result = Result()

        log.info('*****' * 25)
        log.info('*              SSH LOGIN ||HOSTNAME: %s, PORT: %s, USERNAME: %s, PASSWORD: *****||               *'
                    % (self.hostname, self.port, self.username))
        log.info('*****' * 25)


    def localhost(self):
        return socket.gethostname()

    def connect(self, timeout=CONNECT_TIMEOUT):
        try:
            self.client = paramiko.SSHClient()
            self.client.load_system_host_keys()
            # Set policy to use when connecting to servers without a known host key
            self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

            log.info('***** Connecting <%s> ...' % self.hostname)
            try:
                if not USEGSSAPI or (not USEGSSAPI and not DOGSSAPIKEYEXCHANGE):
                    self.client.connect(self.hostname,
                                        self.port,
                                        self.username,
                                        self.password,
                                        timeout=timeout)
                else:
                    self.client.connect(self.hostname,
                                        self.port,
                                        self.username,
                                        gss_auth=USEGSSAPI,
                                        gss_kex=DOGSSAPIKEYEXCHANGE,
                                        timeout=timeout)
            except Exception as ex:
                log.error('##### Exception: %s: %s' % (ex.__class__, ex))
                traceback.print_exc()
                return False
                # password = getpass.getpass('Password for %s@%s: ' % (self.username, self.hostname))
                # self.client.connect(self.hostname, self.port, self.username, password)
        except Exception as ex:
            log.error('##### Exception: %s: %s' % (ex.__class__, ex))
            traceback.print_exc()
            try:
                self.client.close()
            except:
                pass
            return False
        return True

    def execute(self, cmd, timeout=EXEC_TIMEOUT):
        """
        Return (exit-code, stdout-str, stderr-str)
        """
        log.info('[%s@%s]# %s' % (self.username, self.hostname, cmd))

        chan = self.client.get_transport().open_session()
        chan.exec_command(cmd)

        now = time.time()
        while time.time() - now < timeout:
            if chan.recv_ready():
                out = chan.recv(1024).decode()
                sys.stdout.write(out)
                self.result.stdout += out
            if chan.recv_stderr_ready():
                err = chan.recv_stderr(1024).decode()
                sys.stderr.write(err)
                self.result.stderr += err
            if chan.exit_status_ready():
                self.result.exitcode = chan.recv_exit_status()
                break
        else:
            log.error(f'timeout happened within: {timeout}s')
            self.result.returncode = -sys.maxsize - 2

        return self.result

    def disconnect(self):
        if self.client:
            try:
                self.client.close()
            except:
                pass

    def sftp(self, localpath=None, remotepath=None, upload=True, sync=False):
        """
        Upload/Download files between local and remote with SSH2

        :param remotepath: must be a directory-like string when uploading files
        :param localpath: must be a directory-like string when downloading files
        :param upload: true means upload, false means download
        :param sync: true means files will not be overwritten if the same size
        """
        _sftp = None

        def _progress(finish, total):
            sys.stdout.write('%s / %s\r' % (finish, total))
            sys.stdout.flush()

        def _stat(path):
            return _sftp.stat(path)

        def sig_equ(localpath, remotepath):
            try:
                l_st = os.stat(localpath)
                r_st = _stat(remotepath)
            except Exception as ex:
                log.error(ex)
                return False

            l_size = l_st.st_size
            r_size = r_st.st_size

            if not l_size == r_size:
                log.info('localsize:%s, remotesize:%s' % (l_size, r_size))
                return False
            return True

        def _is_dir(remotepath):
            try:
                _st = _stat(remotepath)
                return stat.S_ISDIR(_st.st_mode)
            except Exception as ex:
                log.error(ex)
                return False

        def _is_file(remotepath):
            try:
                _st = _stat(remotepath)
                return stat.S_ISREG(_st.st_mode) or stat.S_ISLNK(_st.st_mode)
            except Exception as ex:
                log.error(ex)
                return False

        _is_exist = lambda remotepath: _is_dir(remotepath) or _is_file(remotepath)
        _rpath_sep = '/' if self.family == 'linux' else '\\'

        def _upload(localpath, remotepath):
            if _is_file(remotepath):
                log.error('<%s:%s> must be a directory-like string' % (self.hostname, remotepath))
                return False

            log.info('##### UPLOADING: %s:%s --> %s:%s ...' % (self.localhost, localpath,
                                                               self.hostname, remotepath))
            if os.path.isfile(localpath):
                remotepath = remotepath.rstrip(_rpath_sep) + _rpath_sep + os.path.basename(localpath)
                if not (sync and sig_equ(localpath, remotepath)):
                    log.info('uploading %s:%s --> %s:%s' % (self.localhost, localpath,
                                                            self.hostname, remotepath))

                    _sftp.put(localpath, remotepath, _progress)
            elif os.path.isdir(localpath):
                for root, dirs, files in os.walk(localpath):
                    for fn in files:
                        src = os.path.join(root, fn)
                        suffix = src.split(localpath)[1]
                        dst = remotepath.rstrip(_rpath_sep) + _rpath_sep + suffix.lstrip(os.sep).replace(os.sep, _rpath_sep)
                        prefix = os.path.dirname(dst)
                        if not _is_dir(prefix):
                            # _sftp.mkdir(prefix)
                            self.execute('mkdir -p %s' % prefix)

                        if not (sync and sig_equ(src, dst)):
                            log.info('uploading %s:%s --> %s:%s' % (self.localhost, src,
                                                                    self.hostname, dst))
                            _sftp.put(src, dst, _progress)
            else:
                log.error('<%s:%s> is not valid' % (self.localhost, localpath))
                return False
            return True

        def _download(localpath, remotepath):
            if os.path.isfile(localpath):
                log.error('<%s:%s> must be a directory-like string' % (self.localhost, localpath))
                return False

            log.info('##### DOWNLOADING: %s:%s --> %s:%s ...' % (self.hostname, remotepath,
                                                                self.localhost, localpath))
            if _is_file(remotepath):
                localpath = os.path.join(localpath, os.path.basename(remotepath))
                if not (sync and sig_equ(localpath, remotepath)):
                    log.info('downloading %s:%s --> %s:%s' % (self.hostname, remotepath,
                                                              self.localhost, localpath))
                    _sftp.get(remotepath, localpath, _progress)
            elif _is_dir(remotepath):
                log.info('Prepare remote files, please wait ...')
                files = []
                dirs = []
                dirs.append(remotepath)
                while dirs:
                    nested = dirs.pop()
                    sftpattrs = _sftp.listdir_attr(nested)
                    for attr in sftpattrs:
                        filename = attr.filename
                        p = nested.rstrip(_rpath_sep) + _rpath_sep + filename
                        if _is_dir(p):
                            dirs.append(p)
                        else:
                            files.append(p)

                for file in files:
                    suffix = file.split(remotepath)[1]
                    dst = os.path.join(localpath.rstrip(os.sep), suffix.lstrip(_rpath_sep).replace(_rpath_sep, os.sep))
                    prefix = os.path.dirname(dst)
                    if not os.path.exists(prefix):
                        os.makedirs(prefix, 0o777)

                    if not (sync and sig_equ(dst, file)):
                        log.info('downloading %s:%s --> %s:%s' % (self.hostname, file,
                                                                  self.localhost, dst))
                        _sftp.get(file, dst, _progress)
            else:
                log.error('<%s:%s> is not valid' % (self.hostname, remotepath))
                return False
            return True

        # Main flow
        try:
            _sftp = paramiko.SFTPClient.from_transport(self.client.get_transport())
            _upload(localpath, remotepath) if upload else _download(localpath, remotepath)
            _sftp.close()

        except KeyboardInterrupt:
            log.warn('##### CTRL-C PRESSED by USER')
            return False

        except Exception as ex:
            log.error('##### Exception: %s: %s' % (ex.__class__, ex))
            traceback.print_exc()
            try:
                _sftp.close()
            except: pass
            return False
        return True


def exec_local(cmd, timeout=EXEC_TIMEOUT, powershell=False, waitfor_complete=True):
    """ Administrator permission required """
    if powershell:
        cmd = cmd.replace('\"', '\'')
        cmd = 'PowerShell -Command "& {' + cmd + '}"'

    if not waitfor_complete:
        if not os.name == 'nt':
            cmd = f'{cmd} &'
        else:
            cmd_async = 'cmd_async.bat'
            cmd = f'echo {cmd} > {cmd_async} & ' \
                  f'schtasks /create /f /sc onstart /tn _taskname /tr {cmd_async} & ' \
                  f'schtasks /run /tn _taskname & ' \
                  f'schtasks /delete /f /tn _taskname'
    print(cmd)
    result = Result()
    child = subprocess.Popen(cmd,
                             shell=True,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE
    )

    child.wait(timeout)
    result.exitcode = child.returncode

    stdout = child.stdout.readlines()
    for line in stdout:
        line = line.decode().strip('\r')
        result.stdout += line
        log.info(line.strip('\n'))

    stderr = child.stderr.readlines()
    for line in stderr:
        line = line.decode().strip('\r')
        result.stderr += line
        log.error(line.strip('\n'))

    return result


def exec_remote(cmd, timeout=EXEC_TIMEOUT, hostname=None, port=PORT, username=None, password=None, family=None, powershell=False, waitfor_complete=True):
    """ Administrator permission required """
    if powershell:
        cmd = cmd.replace('\"', '\'')
        cmd = 'PowerShell -Command "& {' + cmd + '}"'

    if not waitfor_complete:
        if family.lower() == 'linux':
            cmd = f'{cmd} &'
        elif family.lower() == 'windows':
            cmd_async = 'cmd_async.bat'
            cmd = f'echo {cmd} > {cmd_async} & ' \
                  f'schtasks /create /f /sc onstart /tn _taskname /tr {cmd_async} & ' \
                  f'schtasks /run /tn _taskname & ' \
                  f'schtasks /delete /f /tn _taskname'
        else:
            raise RuntimeError(f'family={family} not supported')

    ssh = None
    try:
        ssh = SSHClient(hostname=hostname, port=port, username=username, password=password, family=family)
        ssh.connect()
        return ssh.execute(cmd, timeout)
    finally:
        if ssh:
            ssh.disconnect()


def upload_to_remote(localpath, remotepath, hostname=None, port=PORT, username=None, password=None, family=None):
    ssh = None
    try:
        ssh = SSHClient(hostname=hostname, port=port, username=username, password=password, family=family)
        ssh.connect()
        return ssh.sftp(localpath, remotepath, upload=True, sync=True)
    finally:
        if ssh:
            ssh.disconnect()


def download_to_local(remotepath, localpath, hostname=None, port=PORT, username=None, password=None, family=None):
    ssh = None
    try:
        ssh = SSHClient(hostname=hostname, port=port, username=username, password=password, family=family)
        ssh.connect()
        return ssh.sftp(localpath, remotepath, upload=False, sync=True)
    finally:
        if ssh:
            ssh.disconnect()


def usage_demo():

    # rs = exec_local('netsh interface ipv4 show address "vEthernet (Default Switch)"', powershell=False)
    rs = exec_remote('netsh interface ipv6 show address "Ethernet0"', hostname='10.239.219.182', username='Administrator', password='xxx', family='windows',powershell=False)
    print('rs.exitcode:', rs.exitcode)
    print(rs.stdout)
    p = re.search('address (.*) Parameters', rs.stdout, re.I)
    print(not p)


if __name__ == '__main__':
    usage_demo()