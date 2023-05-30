import os
import re
import sys
import argparse
import platform
import requests
import subprocess
import urllib3
import shutil

from winreg import *
from bs4 import BeautifulSoup

urllib3.disable_warnings()


OS_TYPE = platform.system().lower()
DEFAULT_OS = 'windows'
REG_ENV = r"SYSTEM\CurrentControlSet\Control\Session Manager\Environment"


class EnvSetup(object):
    repo = f'https://ubit-artifactory-sh.intel.com/artifactory/validationtools-sh-local/env/host/{OS_TYPE}/'
    host_tool_path = os.path.join(os.getcwd(), "tools")
    src_root_path = r'C:\Python36\Lib\site-packages' if OS_TYPE == DEFAULT_OS else '/usr/lib64/python3.6/site-packages'

    @classmethod
    def host_env_setup(cls, install_only=False, proxy='', version=None):
        if not cls.dtaf_core_version_check(version):
            return False
        if not cls.set_root_path():
            return False
        if not install_only:
            if not cls.download_tools_from_artifactory():
                return False
        if not cls.host_setting():
            return False
        if not cls.install_tools(proxy):
            return False
        cls.comm_prompt()
        return True

    @classmethod
    def dtaf_core_version_check(cls, version):
        default_version = None
        cfg_path = os.path.join(os.getcwd(), 'requirements.txt')
        if os.path.exists(cfg_path):
            with open(cfg_path, 'r') as f1:
                content = f1.readlines()
            for line in content:
                default_version = re.findall('@(.*)#', line)[0]
        if version:
            print(f'Install dtaf_core lib with specific version <{version.strip()}>')
            input('Press <Enter> to continue:')
            try:
                with open(cfg_path, 'w') as f2:
                    for line in content:
                        ret = re.sub('@.*#', f'@{version.strip()}#', line)
                        f2.write(ret)
                return True
            except IOError:
                return False
        else:
            print(f'Install dtaf_core lib with default version <{default_version}>')
            input('Press <Enter> to continue:')
            return True

    @classmethod
    def set_root_path(cls):
        if OS_TYPE == DEFAULT_OS:
            root_path = "C:\\Automation\\"
            src_config = os.path.abspath(os.path.join(os.getcwd(), "../../../configuration/tkconfig"))
            if not os.path.exists(src_config):
                print(f'Not found <{src_config}>!')
                return False
            if not os.path.exists(root_path):
                os.makedirs(root_path)
                try:
                    shutil.copytree(src_config, os.path.join(root_path, 'tkconfig'))
                except Exception as ex:
                    print(ex)
                    return False
            else:
                if not os.path.exists(os.path.join(root_path, 'tkconfig')):
                    try:
                        shutil.copytree(src_config, os.path.join(root_path, 'tkconfig'))
                    except Exception as ex:
                        print(ex)
                        return False
            try:
                path = RegTools.read_reg(HKEY_LOCAL_MACHINE, REG_ENV, name="PYTHONPATH")
                if root_path not in path[1]:
                    root_path = root_path + ';' + path[1]
                    RegTools.write_reg(HKEY_LOCAL_MACHINE, REG_ENV, type=REG_SZ, name="PYTHONPATH", value=root_path)
            except Exception:
                print('Add system variable PYTHONPATH')
                RegTools.write_reg(HKEY_LOCAL_MACHINE, REG_ENV, REG_SZ, name="PYTHONPATH", value=root_path)
        print('Set local configuration successfully!')
        return True

    @classmethod
    def download_tools_from_artifactory(cls):
        if not os.path.isdir(cls.host_tool_path):
            os.mkdir(cls.host_tool_path)

        response = requests.get(cls.repo, verify=False)
        cont = response.content.decode('utf-8')
        tools = []
        if response.status_code == 200:
            soup = BeautifulSoup(cont, 'html.parser')
            for item in soup.find_all('a'):
                if item.text.endswith('.zip'):
                    tools.append(item.text)
        else:
            return False
        for tool in tools:
            if not cls._download(cls.repo, tool, cls.host_tool_path):
                print(f'Fail to download tool {tool}')
                return False

            if not cls._unzip_tool(os.path.join(cls.host_tool_path, tool), cls.host_tool_path):
                print(f'Fail to unzip tool {tool}')
                return False
            print(f'Download and unzip tool {tool} done!')
        return True

    @classmethod
    def _download(cls, repo, file, path):
        url = repo + file
        response = requests.get(url, verify=False)
        if response.status_code == 200:
            with open(os.path.join(path, file), 'ab') as f:
                f.write(response.content)
            return True
        else:
            return False

    @classmethod
    def _unzip_tool(cls, srcfile, dstdir):
        if OS_TYPE == DEFAULT_OS:
            expand_cmd = f'Expand-Archive -Force -Path {srcfile} -DestinationPath {dstdir}'
            ret = execute_host_cmd(expand_cmd, timeout=60, powershell=True)[0]
        else:
            if srcfile.endswith('zip'):
                expand_cmd = f'unzip -o {srcfile} -d {dstdir}'
            else:
                expand_cmd = f'tar -zxvf {srcfile} -C {dstdir}'
            ret = execute_host_cmd(expand_cmd)[0]
        if not ret == 0:
            print(f'Fail to execute command {expand_cmd}')
            return False
        os.remove(os.path.join(dstdir, srcfile))
        return True

    @classmethod
    def host_setting(cls):
        print("Start to set host dc and firewall ...")

        if OS_TYPE == DEFAULT_OS:
            try:
                val_list = ["monitor-timeout-ac", "monitor-timeout-dc", "disk-timeout-ac", "disk-timeout-dc",
                            "standby-timeout-ac",
                            "disk-timeout-dc", "hibernate-timeout-ac", "hibernate-timeout-dc"]

                ret = execute_host_cmd("netsh advfirewall set allprofiles state off")[0]
                if not ret == 0:
                    print('Fail to disable firewall')
                print('Disable firewall done!')

                for item in val_list:
                    execute_host_cmd("powercfg /CHANGE {} 0".format(item))
                print('Setting powercfg done!')

                with open(r'C:\Windows\System32\WindowsPowerShell\v1.0\profile.ps1', 'w') as f:
                    f.write('$ProgressPreference = "SilentlyContinue"')

                ret = execute_host_cmd("Set-ExecutionPolicy -ExecutionPolicy Bypass", powershell=True)[0]
                if not ret == 0:
                    print('Fail to set powershell execution policy')

                print("Host setting done!\n")

            except Exception as ex:
                print(ex)
                return False
        return True

    @classmethod
    def install_tools(cls, proxy):
        print("Start to install tools ...")
        if proxy:
            proxy = proxy.replace(',', ' ') if ',' in proxy else proxy
        else:
            proxy = ''

        if OS_TYPE == DEFAULT_OS:
            install_cmd = f'install.bat {proxy}'
            ret, out, err = execute_host_cmd(install_cmd, timeout=3600, cwd=os.path.join(cls.host_tool_path, '..'))
            print(out)
            if not ret == 0:
                print("Fail to execute install.bat to install tools")
                return False
            if err:
                print("Install tools occured some error as below, you can ignore it and continue to setup ...")
                print(err)

        else:
            if not execute_host_cmd(f'dos2unix ./install.sh & source ./install.sh {proxy}',
                                    cwd=os.path.join(cls.host_tool_path, '..'))[0] == 0:
                print("Fail to install tools")
                return False
        print('Install tools done!\n')
        return True

    @classmethod
    def comm_prompt(cls):
        prompt = """
---------------------------------------------------------------------------
|                               PROMPTION                                 |
---------------------------------------------------------------------------
| Don't forget to check your ssh communication network port, if use dhcp, |
| make sure it works fine; if use back-to-back connection to sut, make    |
| sure the internal static ip  address is assigned, such as 192.168.1.x   |
---------------------------------------------------------------------------
"""
        print(prompt)


def execute_host_cmd(cmd, timeout=10, cwd=None, powershell=False):
    if OS_TYPE == DEFAULT_OS:
        if powershell:
            cmd = f"C:\\WINDOWS\\system32\\WindowsPowerShell\\v1.0\\powershell.exe {cmd}"
        child = subprocess.Popen(cmd,
                                 shell=True,
                                 stdin=subprocess.PIPE,
                                 stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE,
                                 cwd=cwd)
        out, err = child.communicate(timeout=timeout)
        returncode = child.returncode
        return returncode, out.decode(encoding='utf-8'), err.decode(encoding='utf-8')

    else:
        sub = subprocess.Popen(cmd,
                               shell=True,
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               encoding='utf-8',
                               cwd=cwd)
        return_code = sub.returncode
        outs, errs = sub.communicate()
        return return_code, outs, errs


class RegTools(object):

    @staticmethod
    def connect_reg(computer_name, key):
        """
        hkey = connect_reg(computer_name, key) - Establishes a connection to a predefined registry handle on another computer.
        computer_name is the name of the remote computer, of the form \\computername.
        If None, the local computer is used.
        key is the predefined handle to connect to.
        The return value is the handle of the opened key.
        If the function fails, a WindowsError exception is raised.
        """
        return ConnectRegistry(computer_name, key)

    @staticmethod
    def write_reg(rootkey, subkey, type, name, value, CreateKey=CreateKey):
        hkey = CreateKey(rootkey, subkey)
        SetValueEx(hkey, name, 0, type, value)
        CloseKey(hkey)

    @staticmethod
    def read_reg(rootkey, subkey, name):
        hkey = OpenKey(rootkey, subkey)
        (value, type) = QueryValueEx(hkey, name)
        hkey.Close()
        return name, value, type

    @staticmethod
    def delete_reg(rootkey, subkey, name, OpenKey=OpenKey):
        hkey = OpenKey(rootkey, subkey, 0, KEY_ALL_ACCESS)
        DeleteValue(hkey, name)


def run(args):
    if not args.dtaf_ver:
        args.dtaf_ver = None
    if args.install:
        ret = EnvSetup.host_env_setup(install_only=True, proxy=args.proxy, version=args.dtaf_ver)
    else:
        ret = EnvSetup.host_env_setup(proxy=args.proxy, version=args.dtaf_ver)
    return ret


def get_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--install', action='store_true', help='Setup host automation environment')
    parser.add_argument('-p', '--proxy', type=str, help='Set http_proxy and https_proxy')
    parser.add_argument('-v', '--dtaf_ver', type=str, help='Using specific dtaf-core version')
    parser.set_defaults(func=run)
    try:
        ret = parser.parse_args()

    except Exception as ex:
        print(ex)
        return False

    return ret


def main():
    arguments = get_parser()
    if arguments and arguments.func(arguments):
        sys.exit(0)
    sys.exit(1)


if __name__ == '__main__':
    main()