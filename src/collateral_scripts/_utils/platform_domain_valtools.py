#!/usr/bin/env python
import getpass
import shutil
import sys
import os
import re
import subprocess


def find_real_domain(domain):
    """
    The "real domain" means "domain" class is configured in this module with format: DomainSetup
    """
    tag = 'Setup'
    modules = sys.modules[__name__].__dict__.keys()

    domains = []
    for m in modules:
        if m.endswith(tag) and not m.startswith('_'):
            domains.append(m)

    domains = [d.split(tag)[0].lower() for d in domains]

    for d in domains:
        if domain.lower().startswith(d):
            return d

    print(f'ERROR: not found a defined domain class in this module that matches <{domain}>')


class _Utils:
    @classmethod
    def parse_parameter(cls, param):
        """
        Parameter format should be like: --name=value
        Space is not permitted in multiple values, but instead with comma
        """
        args = sys.argv[1:]
        for arg in args:
            if arg.startswith(f'--{param}='):
                return arg[len(f'--{param}='):]
        return ''

    @classmethod
    def win_os(cls):
        return os.name == 'nt'

    @classmethod
    def exec_local(cls, cmd, timeout=None, cwd=None, powershell=False, waitfor_complete=True, show_cmd=True):
        """ Administrator permission required """
        class _Result:
            exitcode = -sys.maxsize - 1
            stdout = ''
            stderr = ''

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
        if show_cmd:
            print(cmd)
        result = _Result()
        child = subprocess.Popen(cmd,
                                 shell=True,
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 cwd=cwd
                                 )
        out, err = child.communicate(timeout=timeout)
        result.exitcode = child.returncode
        result.stdout = out.decode(encoding='utf-8')
        result.stderr = err.decode(encoding='utf-8')
        print(result.stdout)
        return result

    @classmethod
    def check_md5(cls, file):
        if cls.win_os():
            cmd = f'(Get-FileHash {file} -Algorithm md5).hash'
        else:
            cmd = f"md5sum {file}|awk '{{print $1}}'"

        rs = _Utils.exec_local(cmd)
        return rs.stdout

    @classmethod
    def file_copy(cls, src, dst):
        if not _Utils.win_os():
            if not os.path.exists(src):
                raise RuntimeError(f'{src} not exist')

        if not os.path.exists(dst):
            os.makedirs(dst)
            try:
                if os.path.isfile(src):
                    shutil.copy(src, dst)
                else:
                    shutil.copytree(src, dst)
            except shutil.Error:
                raise
            print(f'File Transfer: {src} -> {dst}')
        else:
            if not cls.check_md5(src) == cls.check_md5(dst):
                try:
                    if os.path.isfile(src):
                        shutil.copy(src, dst)
                    else:
                        shutil.copytree(src, dst)
                except shutil.Error:
                    raise
                print(f'File Transfer: {src} -> {dst}')


class _FileDownload:
    def __init__(self, fileserver, username, password, domain):
        self.fileserver = fileserver
        self.username = username
        self.password = password
        self.domain = domain
        self.mount_point = self._mount()

    def _mount(self):
        """
        Mount sharefolder, return a local mount point
        """
        if _Utils.win_os():
            mount_point = self.fileserver
            cmd = f'net use {self.fileserver} "{self.password}" /user:"{self.username}"'
        else:
            mount_point = '/mnt'
            cmd = r"mount -t cifs -o username={},password='{}' {} {}".format(
                self.username, self.password, self.fileserver, mount_point
            )
        ret = _Utils.exec_local(cmd, timeout=30, show_cmd=False)

        if not ret.exitcode == 0 and ret.stderr == '':
            print(f'Mount fileserver {mount_point} failed, will try again ...')
            self.username = "ccr\\" + self.username
            ret = _Utils.exec_local(cmd, timeout=30, show_cmd=False)
            if not ret.exitcode == 0 and ret.stderr == '':
                print(f'Mount fileserver {mount_point} failed again ...')
                return ''
        print(f'Mount fileserver {mount_point} successfully!')
        return mount_point

    def download(self):
        if not self.mount_point:
            return False

        osfolder = 'windows' if _Utils.win_os() else 'linux'
        ospath = 'C:\\BKCPkg\\domains' if _Utils.win_os() else '/home/BKCPkg/domains'

        for domain in self.domain:
            source = os.path.join(self.mount_point, domain, osfolder)
            destination = os.path.join(ospath, find_real_domain(domain))

            print('Download tools will spend several minutes, please wait patiently...')
            copy_cmd = f'xcopy {source} {destination} /E /Y' if _Utils.win_os() else f'cp -r {source}/* {destination}'
            if not os.path.exists(destination):
                os.makedirs(destination)
            ret = _Utils.exec_local(copy_cmd)
            if ret.exitcode == 0 and ret.stderr == '':
                print('Download tools successfully!')
                return True
            else:
                print(f'Download tools from {source} to {destination} failed ...')
                return False


class _GeneralSetup:
    def __init__(self, platform, domain):
        self.platform = platform
        self.domain = domain
        self.path = os.path.join('C:\\BKCPkg\\domains' if _Utils.win_os() else '/home/BKCPkg/domains',
                                 self.__class__.__name__.split('Setup')[0].lower())
        if not os.path.exists(self.path):
            raise RuntimeError(f'Domain tools should be downloaded/copied to {self.path} firstly')

    def unzip_file(self, srcfile, dstdir):
        if _Utils.win_os():
            expand_cmd = f'Expand-Archive -Force -Path {srcfile} -DestinationPath {dstdir}'
        else:
            if srcfile.endswith('zip'):
                expand_cmd = f'unzip -o {srcfile} -d {dstdir}'
            else:
                expand_cmd = f'tar -zxvf {srcfile} -C {dstdir}'

        if _Utils.win_os():
            ret = _Utils.exec_local(expand_cmd, timeout=30, powershell=True)
        else:
            ret = _Utils.exec_local(expand_cmd, timeout=30)
        if ret.exitcode == 0:
            return True
        else:
            print(ret.stderr)
            return False

    def find_file(self, par, folder):
        """ Return matched file in specific folder, re regex supported """
        for root, dirs, files in os.walk(folder):
            for file in files:
                if re.search(par, file):
                    file_path = os.path.join(root, file)
                    return file_path
        else:
            return ''

    def yum_repo(self):
        if not _Utils.win_os():
            ret = _Utils.exec_local("cat /etc/redhat-release")
            if 'CentOS' in ret.stdout:
                key = 'centos'
            else:
                key = 'rhel8'
            ret = _Utils.exec_local("cat /etc/redhat-release | awk '{print $6}'")
            version = float(ret.stdout.strip())
            yum_repo = f"""
[{key}-base]
name={key} base
baseurl=http://linux-ftp.jf.intel.com/pub/ISO/redhat/redhat-rhel/RHEL-{version}.0-GA/BaseOS/x86_64/os/
enabled=1
keepcache=0
gpgcheck=0

[{key}-optional]
name={key} optional
baseurl=http://linux-ftp.jf.intel.com/pub/ISO/redhat/redhat-rhel/RHEL-{version}.0-GA/CRB/x86_64/os/
enabled=1
keepcache=0
gpgcheck=0

[{key}-appstream]
name={key} appstream
baseurl=http://linux-ftp.jf.intel.com/pub/ISO/redhat/redhat-rhel/RHEL-{version}.0-GA/AppStream/x86_64/os/
enabled=1
keepcache=0
gpgcheck=0
"""
            ret = _Utils.exec_local(f'rm -rf /etc/yum.repos.d/*')
            if ret.exitcode == 0 and ret.stderr == '':
                print('Remove all yum repo file successfully!')
            try:
                with open(f'/etc/yum.repos.d/intel-{key}.repo', 'w') as f:
                    f.write(yum_repo)
            except Exception as ex:
                print(ex)
                print('Set intel yum repos failed ...')
            print('Set intel yum repos successfully!')

    def setup(self):
        """ Common setup process """
        self.yum_repo()


class NetworkSetup(_GeneralSetup):
    def __init__(self, platform, domain):
        super().__init__(platform, domain)

    def _setup_windows_iperf_install(self):
        file = self.find_file('iperf-.*-win64.zip', self.path)
        if file:
            self.unzip_file(file, self.path)
            os.rename(os.path.join(self.path, os.path.basename(file).rstrip('.zip')), os.path.join(self.path, 'iperf3'))
            if self.find_file('iperf3.exe', os.path.join(self.path, 'iperf3')):
                print('Install iperf3 successfully!')
            else:
                print('Install iperf3 failed ...')
        else:
            print('Not found iperf3 tool, please download tool to local and try again')
            return False

    def _setup_windows_700_driver(self):
        unziptool = os.path.join(self.path, 'unzip.exe')
        if not os.path.exists(unziptool):
            print('Not found unzip.exe tool, please download tool to local and try again')

        file = self.find_file(r'700Series_NVMUpdatePackage_v\d+_\d+_Windows.zip', self.path)
        if not file:
            print('Not found 700series tool, please download tool to local and try again')
            return False
        else:
            dstpath = os.path.join(self.path, os.path.basename(file).strip('.zip'))
            if self.unzip_file(file, dstpath):
                file = self.find_file(r'700Series_NVMUpdatePackage_v\d+_\d+_Windows\.exe', self.path)
                ret = _Utils.exec_local(f'{unziptool} {file}', cwd=dstpath)
                print(ret.stdout)
                if ret.exitcode == 0 and ret.stderr == '':
                    print('Install windows 700series driver successfully!')
                    return True
                else:
                    print('Install windows 700series driver failed ...')
                    return False
            else:
                print('Unzip windows 700series driver failed ...')

    def _setup_windows_e810_driver(self):
        unziptool = os.path.join(self.path, 'unzip.exe')
        if not os.path.exists(unziptool):
            print('Not found unzip.exe tool, please download tool to local and try again')

        file = self.find_file(r'E810_NVMUpdatePackage_v\d+_\d+_Windows\.zip', self.path)
        if not file:
            print('Not found E810 tool, please download tool to local and try again')
        else:
            dstpath = os.path.join(self.path, os.path.basename(file).strip('.zip'))
            if self.unzip_file(file, dstpath):
                file = self.find_file(r'E810_NVMUpdatePackage_v\d+_\d+_Windows\.exe', self.path)
                ret = _Utils.exec_local(f'{unziptool} {file}', cwd=dstpath)
                print(ret.stdout)
                if ret.exitcode == 0 and ret.stderr == '':
                    print('Install windows E810 driver successfully!')
                    return True
                else:
                    print('Install windows E810 driver failed ...')
                    return False
            else:
                print('Unzip windows E810 driver failed ...')

    def _setup_windows_mlx_driver(self):
        winmft = r"C:\Program Files\Mellanox\WinMFT"
        winof = r"C:\\Program Files\Mellanox\MLNX_WinOF2"
        tools = [r'MLNX_WinOF2-.*_All_x64\.exe', r'WinMFT_x64_.*\.exe']
        for tool in tools:
            file = self.find_file(tool, self.path)
            if not file:
                print(f'Not found tool, please download tool to local and try again')
            else:
                _Utils.exec_local(f'{file} /S')
        flag = True
        if not os.path.exists(winof):
            flag = False
            print('Install Mellanox WinOF2 tool failed ...')
        if not os.path.exists(winmft):
            flag = False
            print('Install Mellanox WinMFT tool failed ...')
        if flag:
            print('Install Mellanox driver successfully!')

    def _setup_linux_pxe_server(self, ip=None):
        print('Start to setup linux pxe server ...')
        servers = ['dhcp-server', 'tftp-server', 'vsftpd', 'syslinux']
        for server in servers:
            ret = _Utils.exec_local(f'yum install -y {server}')
            if ret.exitcode == 0 and ret.stderr == '':
                print('Setup essential servers done!')
            else:
                print('Setup essential servers failed ...')

        dhcp_conf = """
# DHCP Server Configuration file
# see /usr/share/doc/dhcp-server/dhcpd.conf.example
# see dhcpd.conf(5) man page
#

default-lease-time 600;
max-lease-time 7200;
ignore client-updates;
allow booting;
allow bootp;
allow unknown-clients;


# Initial Boot Files for PXE Clients
# Note: filename may change for different Linux OSes, such as shim.efi, pxelinux.0, ...
filename "grubx64.efi";
#next-server 0.0.0.0;


# Possible Subnets
"""
        for i in range(1, 21):
            ip_conf = """
subnet 192.168.{0}.0 netmask 255.255.255.0
{{
  range 192.168.{0}.100 192.168.{0}.200;
}}          
""".format(str(i))
            dhcp_conf += ip_conf

        try:
            with open(f'/etc/dhcp/dhcpd.conf', 'w') as f:
                f.write(dhcp_conf)
        except Exception as ex:
            print(ex)
            print('Writing dhcp server configuration file failed ...')

        if ip:
            ret = _Utils.exec_local(f'echo "next-server {ip};" >> /etc/dhcp/dhcpd.conf')
            if not (ret.exitcode == 0 and ret.stderr == ''):
                print('Add ip to dhcp server configuration file failed ...')
                return False

        command = 'systemctl restart dhcpd.service &' \
                  ' cp -rf -v /usr/share/syslinux/* /var/lib/tftpboot &' \
                  ' cp -rf -v /boot/efi/EFI/redhat/*.efi /var/lib/tftpboot &' \
                  ' chmod 777 /var/lib/tftpboot/* &' \
                  ' systemctl restart tftp.service'
        ret = _Utils.exec_local(command)
        if not (ret.exitcode == 0 and ret.stderr == ''):
            print('Setup FTP server and TFTP server failed ...')
            return False
        print('Setup linux pxe server successfully!')
        return True

    def _setup_linux_ilvss_driver(self):
        ilvss_dir = os.path.join(self.path, 'ilvss')
        file = self.find_file('ilvss-.*tar.gz', ilvss_dir)
        if file:
            print(file, ilvss_dir)
            if self.unzip_file(file, ilvss_dir):
                dstpath = os.path.join(ilvss_dir, os.path.basename(file).rstrip('.tar.gz'))
                print("dst: " + dstpath)
                ret = os.system(f'cd {dstpath} && ./install --nodeps')
                if ret == 0:
                    print('Install ilvss successfully!')
                    ret = _Utils.exec_local(f'cp {ilvss_dir}/license.key {dstpath} && date -s "2021-09-01 00:00:00"')
                    if not (ret.exitcode == 0 and ret.stderr == ''):
                        print('Fail to modify license key and datetime ...')
                else:
                    print('Install ilvss failed ...')
            else:
                print('Fail to unzip ilvss tool ...')
        else:
            print('Not found ilvss tool, please download to local and try again')

    def _setup_linux_iperf3_driver(self):
        file = self.find_file(r'iperf3-.*fc24\.x86_64.rpm', self.path)
        if file:
            ret = _Utils.exec_local(f'rpm -ivh {file} --force --nodeps')
            if ret.exitcode == 0 and ret.stderr == '':
                print('Install iperf3 successfully!')
            else:
                print('Install iperf3 failed ...')
        else:
            print('Not found iperf3 rpm package, please download to local and try again')

    def _setup_linux_mlx_driver(self):
        ret = _Utils.exec_local('yum install gcc-gfortran tcsh kernel-modules-extra tk')
        if not (ret.exitcode == 0 and ret.stderr == ''):
            return False
        file = self.find_file('MLNX_OFED_LINUX-.*-x86_64.tgz', self.path)
        if file:
            if self.unzip_file(file, self.path):
                dstpath = os.path.join(self.path, os.path.basename(file).rstrip('.tar.gz'))
                ret = _Utils.exec_local('chmod 777 ./* && ./mlnxofedinstall', cwd=dstpath)
                if ret.exitcode == 0 and ret.stderr == '':
                    print('Install mellanox driver successfully!')
                    ret = _Utils.exec_local('rmmod rpcrdma & rmmod ib_srpt & rmmod ib_isert && rmmod ii40iw')
                    if ret.exitcode == 0 and ret.stderr == '':
                        print('remove module successfully!')
                    else:
                        print('Fail to remove module, please check if your server insert mellanox card!')
                else:
                    ret = os.system(f'cd {dstpath} && ./mlnxofedinstall')
                    print(ret)
                    print('Install mellanox driver failed ...')
            else:
                print('Fail to unzip mellanox driver tool ...')
        else:
            print('Not found mellanox driver tool, please download to local and try again')

    def _setup_linux_vm_driver(self):
        vm_driver = [r'kernel-modules-extra-.*el8.x86_64\.rpm', r'python3-pexpect-.*el8.noarch\.rpm', r'python3-ptyprocess-.*.el8.noarch\.rpm']
        for driver in vm_driver:
            file = self.find_file(driver, self.path)
            if file:
                ret = _Utils.exec_local(f'rpm -ivh {file} --force --nodeps')
                if ret.exitcode == 0 and ret.stderr == '':
                    print(f'Install vm driver {os.path.basename(file)} successfully!')
                else:
                    print(f'Install vm driver {os.path.basename(file)} failed!')
                    return False
            else:
                print(f'Not found {driver} rpm package, please download to local and try again')
        print('Install vm driver done!')
        return True

    def _setup_linux_fio_driver(self):
        file = self.find_file('fio-.*x86_64.rpm', self.path)
        if file:
            ret = _Utils.exec_local(f'rpm -ivh {file} --force --nodeps')
            if ret.exitcode == 0 and ret.stderr == '':
                print('Install fio successfully!')
                return True
            else:
                print('Install fio failed ...')
        print('Will install fio via yum')
        ret = _Utils.exec_local('yum install fio')
        if ret.exitcode == 0 and ret.stderr == '':
            print('Install fio successfully!')
            return True
        else:
            print('Install fio failed ...')
            return False

    def setup(self):
        super().setup()

        # Tools Setup for BHS platform
        if self.platform == 'bhs':
            if _Utils.win_os():
                self._setup_windows_iperf_install()
            else:
                self._setup_linux_pxe_server()

        # Tools Setup for EGS platform
        if self.platform == 'egs':
            if _Utils.win_os():
                self._setup_windows_iperf_install()
                self._setup_windows_e810_driver()
                self._setup_windows_700_driver()
                self._setup_windows_mlx_driver()
            else:
                self._setup_linux_pxe_server()
                self._setup_linux_iperf3_driver()
                self._setup_linux_ilvss_driver()
                self._setup_linux_fio_driver()
                self._setup_linux_mlx_driver()
                self._setup_linux_vm_driver()


class StorageSetup(_GeneralSetup):
    def __init__(self, platform, domain):
        super().__init__(platform, domain)

    def _setup_windows_demo_tools(self):
        pass

    def _setup_linux_demo_tools(self):
        pass

    def setup(self):
        super().setup()

        # Tools Setup for BHS platform
        if self.platform == 'bhs':
            if _Utils.win_os():
                self._setup_windows_demo_tools()
            else:
                self._setup_linux_demo_tools()

        # Tools Setup for EGS platform
        if self.platform == 'egs':
            if _Utils.win_os():
                self._setup_windows_demo_tools()
            else:
                self._setup_linux_demo_tools()


class VirutalizationSetup(_GeneralSetup):
    def __init__(self, platform, domain):
        super().__init__(platform, domain)

    def _setup_windows_demo_tools(self):
        pass

    def _setup_linux_demo_tools(self):
        pass

    def setup(self):
        super().setup()

        # Tools Setup for BHS platform
        if self.platform == 'bhs':
            if _Utils.win_os():
                self._setup_windows_demo_tools()
            else:
                self._setup_linux_demo_tools()

        # Tools Setup for EGS platform
        if self.platform == 'egs':
            if _Utils.win_os():
                self._setup_windows_demo_tools()
            else:
                self._setup_linux_demo_tools()


class AcceleratorSetup(_GeneralSetup):
    def __init__(self, platform, domain):
        super().__init__(platform, domain)

    def _setup_windows_demo_tools(self):
        pass

    def _setup_linux_demo_tools(self):
        pass

    def setup(self):
        super().setup()

        # Tools Setup for BHS platform
        if self.platform == 'bhs':
            if _Utils.win_os():
                self._setup_windows_demo_tools()
            else:
                self._setup_linux_demo_tools()

        # Tools Setup for EGS platform
        if self.platform == 'egs':
            if _Utils.win_os():
                self._setup_windows_demo_tools()
            else:
                self._setup_linux_demo_tools()


class MultisocketSetup(_GeneralSetup):
    def __init__(self, platform, domain):
        super().__init__(platform, domain)

    def _setup_windows_demo_tools(self):
        pass

    def _setup_linux_demo_tools(self):
        pass

    def setup(self):
        super().setup()

        # Tools Setup for BHS platform
        if self.platform == 'bhs':
            if _Utils.win_os():
                self._setup_windows_demo_tools()
            else:
                self._setup_linux_demo_tools()

        # Tools Setup for EGS platform
        if self.platform == 'egs':
            if _Utils.win_os():
                self._setup_windows_demo_tools()
            else:
                self._setup_linux_demo_tools()


def help():
    r"""
    Description:
    ============

    Python platform_domain_valtools.py --platform=bhs --domain=network[,virtualization] --fileserver=xxx --cred=true
        --platform: The platform is used for customizing domain tools installation <required parameter>
        --domain: Multiple domains must be separated by a comma (without space)    <required parameter>
            -> domain param is used for downloading tools from "fileserver/domain/sutos" to "pre-defined domain path in steps_lib.config.sut_tools"
            -> domain param must start with valid "domain name", which is also used in your script tool path
            -> domain param related "setup class" must be defined if any extra tools installation required
        --fileserver: The fileserver that maintain test tools, by default, it is: \\ccr\ec\proj\DPG\PV\test_case_tool
        --cred: The account for accessing fileserver, by default use internal faceless account
            -> in case faceless account is outdated, then you can use your own account
        --skipdownload: If skipdownload='true', then will ignore tools download actions from fileserver, by default, it is 'false'
        --skipinstall: If skipinstall='true', then will ignore pre-defined tools setup actions, by default, it is 'false'

    As a DEFAULT behavior, this script just copy domain specific tools to sut tools folder, if any special installation
    process required, make sure you have customized the `DomainSetup` class before running it (take NetworkSetup class as an example)


    Usage Demo:
    ===========

    1. download network tools from fileserver, and run pre-defined installation process
        > Python platform_domain_valtools.py --platform=bhs --domain=network
    2. download network tools from fileserver, and ignore pre-defined installation process
        > Python platform_domain_valtools.py --platform=bhs --domain=network --skipinstall=true
    3. ignore download actions, only run pre-defined installation process
        > Python platform_domain_valtools.py --platform=bhs --domain=network --skipdownload=true
    """
    print(help.__doc__)


def main():
    platform = _Utils.parse_parameter('platform')
    domain = _Utils.parse_parameter('domain').split(',')

    assert platform, '--platform is required'
    assert domain, '--domain is required'

    skipdownload = _Utils.parse_parameter('skipdownload')
    if skipdownload.lower() == 'true':
        skipdownload = True
    else:
        skipdownload = False

    skipinstall = _Utils.parse_parameter('skipinstall')
    if skipinstall.lower() == 'true':
        skipinstall = True
    else:
        skipinstall = False

    if not skipdownload:
        fileserver = _Utils.parse_parameter('fileserver')
        if not fileserver:
            fileserver = r'\\shsfls0001.ccr.corp.intel.com\PV\test_case_tool' if _Utils.win_os() else r'\\\\shsfls0001.ccr.corp.intel.com\\PV\\test_case_tool'

        cred = _Utils.parse_parameter('cred')
        if cred.lower() == 'true':
            cred = True
        else:
            cred = True

        if cred:
            print(f'input your username & password for accessing fileserver: {fileserver}')
            username = input('username: ')
            password = getpass.getpass(prompt='password: ')
        else:
            raise RuntimeError('Required: --cred=true in commandline')

        tools = _FileDownload(fileserver, username, password, domain)
        if not tools.download():
            sys.exit()

    if not skipinstall:
        for dm in domain:
            dm = find_real_domain(dm)
            dm = dm.capitalize()
            cls = getattr(sys.modules[__name__], f'{dm}Setup')
            cls(platform, domain).setup()


if __name__ == '__main__':
    help()
    main()
