import os
import sys
import traceback

parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
parent_dir += r'\src'
sys.path.insert(0, parent_dir)

from src.lib.toolkit.basic.testcase import *
from src.lib.toolkit.infra.sut import *
from src.lib.toolkit.basic.const import *
from datetime import datetime

CASE_DESC = [
    'check sut environment'
]


class SutCheck:

    def __init__(self, sut):
        self.sut = sut

    def localip(self):
        res = None
        if self.sut.SUT_PLATFORM == SUT_STATUS.S0.LINUX:
            cmd = 'ping -n 2 192.168.0.2'
            ret, out, err = self.sut.execute_host_cmd(cmd)
            if ret == 0:
                res = True
            else:
                res = False

        elif self.sut.SUT_PLATFORM == SUT_STATUS.S0.WINDOWS:
            cmd = 'ping -n 2 192.168.0.3'
            ret, out, err = self.sut.execute_host_cmd(cmd)
            if ret == 0:
                res = True
            else:
                res = False

        elif self.sut.SUT_PLATFORM == SUT_STATUS.S0.VMWARE:
            cmd = 'ping -n 2 192.168.0.4'
            ret, out, err = self.sut.execute_host_cmd(cmd)
            if ret == 0:
                res = True
            else:
                res = False

        if res:
            logger.info("PASS: Check sut local network driver link status.")
            return True
        else:
            logger.info("""
            FAIL: Check sut local network driver link status. 
            PROMPT:
            1.Check host and sut network cable physical connection.
            
            2.Check host(default 192.168.0.1) and sut(default 192.168.0.2/3/4) IP address configuration.
              Sut IP config reference different platform setup scripts. Scripts location as following:
              Host: 
                setup/host/env_ini_H.bat
              Sut:
                windows: setup/sut/windows/env_ini_L.sh
                linux:   setup/sut/linux/env_ini_W.bat
                
            3.Check local network driver link status.
              cmd: ifup <network name> (only linux platform need)
                     example: ifup enp1s0
                   ping <ip>
                     example: ping 192.168.0.2
            
            """)
            return False

    def sshd(self):
        res = None

        if self.sut.SUT_PLATFORM == SUT_STATUS.S0.LINUX or self.sut.SUT_PLATFORM == SUT_STATUS.S0.VMWARE:
            ret, out, err = self.sut.execute_shell_cmd('uname -a')
            if ret == 0:
                res = True
            else:
                res = False

        elif self.sut.SUT_PLATFORM == SUT_STATUS.S0.WINDOWS:
            ret, out, err = self.sut.execute_shell_cmd('dir')
            if ret == 0:
                res = True
            else:
                res = False

        if res:
            logger.info("PASS: Check sshd service status.")
            return True
        else:
            logger.info("""
            FAIL: Execute remote cmd by ssh fail.
            PROMPT:
            1.Check local network link status. refrence check item localip prompt.
            
            2.Check sut ssh service status.
              linux cmd: systemctl status sshd
                         systemctl restart sshd
              windows cmd: net start sshd
              
            3.Check ssh login username and password in your sut.ini file.
              linux default: root/password
              windows default: administrator/password
              
            """)
            return False

    def py3interpreter(self):
        res = None
        if self.sshd():
            if self.sut.SUT_PLATFORM == SUT_STATUS.S0.LINUX or self.sut.SUT_PLATFORM == SUT_STATUS.S0.VMWARE:
                ret, out, err = self.sut.execute_shell_cmd('test -f /usr/bin/python')
                if ret == 0:
                    res = True
                else:
                    res = False

            elif self.sut.SUT_PLATFORM == SUT_STATUS.S0.WINDOWS:
                cmd = 'dir C:\\Python36\\python.exe'
                ret, out, err = self.sut.execute_shell_cmd(cmd)
                if ret == 0:
                    res = True
                else:
                    res = False

        if res:
            logger.info("PASS: Check python3 interpreter is installed.")
            return True
        else:
            logger.info("""
            FAIL: Python3 interpreter is not installed.
            PROMPT:
            1.Get python3 interpreter install package. 
              Localtion: setup/sut/tools/pyton-3.6.8-amd64.exe
              
            2.Install python3 interpreter in the specified directory(C:\Python36).
              Windows platform:
                  GUI install: specify install path as 'C:\Python36 '
                               select checkbox 'Add Python 3.6 to PATH'.
                               select checkbox 'install for all users'.
                  CMD install: 
                  python-3.6.8-amd64.exe /passive InstallAllUsers=1 PrependPath=1 TargetDir=C:\Python36
              Linux platform: ln -s /usr/bin/python3 /usr/bin/python
                  
            
            """)
            return False

    def xmlclios(self):
        res = None

        if self.sshd():
            if self.sut.SUT_PLATFORM == SUT_STATUS.S0.LINUX or self.sut.SUT_PLATFORM == SUT_STATUS.S0.VMWARE:
                cmd = 'test -f /opt/APP/xmlcli/xmlcli_save_read_prog_knobs.py'
                ret, out, err = self.sut.execute_shell_cmd(cmd)
                if ret == 0:
                    res = True
                else:
                    res = False

            elif self.sut.SUT_PLATFORM == SUT_STATUS.S0.WINDOWS:
                cmd = 'dir C:\\BKCPkg\\xmlcli\\xmlcli_save_read_prog_knobs.py'
                ret, out, err = self.sut.execute_shell_cmd(cmd)
                if ret == 0:
                    res = True
                else:
                    res = False

            if res:
                logger.info("PASS: Check xmlcli tool is installed.")
                return True
            else:
                logger.info("""
                FAIL: xmlcli OS tool is not installed on OS
                PROMPT:
                1.Get xmlcli OS tool.
                  Location: setup/sut/tools/6.3_xmlcli_windows_linux_Python2-3.zip
                
                2.Copy xmlcli OS tool to specified directory on OS.
                  linux directory: /opt/APP/xmlcli/
                  window directory: C:\\BKCPkg\\xmlcli\\
                  linux uncompress cmd: unzip 6.3_xmlcli_windows_linux_Python2-3.zip
                
                """)
                return False

    def xmlcliefi(self):
        res = None

        if self.sshd():
            if self.sut.SUT_PLATFORM == SUT_STATUS.S0.LINUX or self.sut.SUT_PLATFORM == SUT_STATUS.S0.VMWARE:
                cmd = 'test -f /boot/efi/bkc_tool/XmlCliKnobs.efi'
                ret, out, err = self.sut.execute_shell_cmd(cmd)
                if ret == 0:
                    res = True
                else:
                    res = False

            elif self.sut.SUT_PLATFORM == SUT_STATUS.S0.WINDOWS:
                logger.warning("Warning: Windows SUT not support to check efi shell tools")
                return True

        if res:
            logger.info("PASS: Check xmlcli efi tool(XmlCliKnobs.efi) is installed.")
            return True
        else:
            logger.info("""
            FAIL: xmlcli efi tool(XmlCliKnobs.efi) is not installed.
            PROMPT:
            1.Get xmlcli efi tool(XmlCliKnobs.efi).
              Location: setup/sut/tools/XmlCliKnobs.efi
                
            2.Copy xmlcli OS tool to specified directory on OS.
              linux directory: /boot/efi/bkc_tool
              cmd: mkdir -p /boot/efi/bkc_tool
                   cp -a XmlCliKnobs.efi /boot/efi/bkc_tool
            
            """)
            return False

    def screen(self):
        res = None

        if self.sshd():
            if self.sut.SUT_PLATFORM == SUT_STATUS.S0.LINUX or self.sut.SUT_PLATFORM == SUT_STATUS.S0.VMWARE:
                cmd = 'rpm -qa screen|grep screen'
                ret, out, err = self.sut.execute_shell_cmd(cmd)
                if ret == 0:
                    res = True
                else:
                    res = False

            elif self.sut.SUT_PLATFORM == SUT_STATUS.S0.WINDOWS:
                logger.warning("Warning: Windows SUT not support to check screen rpm package")
                return True

        if res:
            logger.info("PASS: Check screen rpm package is installed.")
            return True
        else:
            logger.info("""
            FAIL: screen rpm package is not installed.
            PROMPT:
            1.Get screen rpm package and copy it to linux sut(Only linux need).
              Location: setup/sut/tools/screen-4.6.2-10.el8.x86_64.rpm
              
            2.Install screen rpm package.
              cmd: rpm -ivh screen-4.6.2-10.el8.x86_64.rpm
            
            """)
            return False

    def firewalld(self):
        res = None

        if self.sshd():
            if self.sut.SUT_PLATFORM == SUT_STATUS.S0.LINUX or self.sut.SUT_PLATFORM == SUT_STATUS.S0.VMWARE:
                cmd = "systemctl status firewalld|sed -n '3p'|awk '{print $2}'"
                ret, out, err = self.sut.execute_shell_cmd(cmd)
                if out.strip() == 'inactive':
                    res = True
                else:
                    res = False

            elif self.sut.SUT_PLATFORM == SUT_STATUS.S0.WINDOWS:
                cmd = 'netsh firewall show state'
                ret, out, err = self.sut.execute_shell_cmd(cmd)
                lines = out.split('\n')
                res = False
                for line in lines:
                    if 'Operational mode' in line:
                        value = line.split('=')[-1].strip()
                        if value == 'Disable':
                            res = True
                            break

            if res:
                logger.info("PASS: Check firewall service status is disabled.")
                return True
            else:
                logger.info(""""
                FAIL: Firewall service status is not disabled.
                PROMPT:
                1.Disable firewall service.
                  linux cmd: systemctl stop firewall
                             systemctl disable firewall
                             systemctl status firewall
                  windows cmd: netsh advfirewall set allprofiles state off
                               netsh firewall show state (check Operational mode is Disable)
                               
                """)
                return False

    def selinux(self):
        res = None

        if self.sshd():
            if self.sut.SUT_PLATFORM == SUT_STATUS.S0.LINUX or self.sut.SUT_PLATFORM == SUT_STATUS.S0.VMWARE:
                cmd = 'getenforce'
                ret, out, err = self.sut.execute_shell_cmd(cmd)
                if out.strip() == 'Disabled':
                    res = True
                else:
                    res = False

            elif self.sut.SUT_PLATFORM == SUT_STATUS.S0.WINDOWS:
                logger.warning(
                    "Warning: Windows SUT not support to check selinux state")
                return True

        if res:
            logger.info("PASS: Check linux selinux state is disabled.")
            return True
        else:
            logger.info("""
            FAIL: Linux selinux state is not disabled.
            PROMPT:
            1.Disable selinux service by modify config file.
              Config file: /etc/selinux/config
              cmd: vi /etc/selinux/config
                      SELINUX=disabled
                      
            2.Rebot system.
              cmd: reboot
            
            """)
            return False

    def cmdasync(self):
        res = None

        if self.sshd() and self.screen():
            if self.sut.SUT_PLATFORM == SUT_STATUS.S0.LINUX or self.sut.SUT_PLATFORM == SUT_STATUS.S0.VMWARE:
                cmd_async = 'sleep 8'
                ret_async = self.sut.execute_shell_cmd_async(cmd_async)
                cmd = 'ps aux|grep -v grep|grep SCREEN'
                ret, out, err = self.sut.execute_shell_cmd(cmd)
                if ret_async and ret == 0:
                    res = True
                else:
                    res = False

            elif self.sut.SUT_PLATFORM == SUT_STATUS.S0.WINDOWS:
                logger.warning("Warning: Windows SUT not support to check async cmd execution")
                return True

        if res:
            logger.info("PASS: Check cmd execution with async mode.")
            return True
        else:
            logger.info("""
            FAIL: Execution cmd with async mode failed.
            PROMPT:
            1.Check ssh service status. Reference check item sshd.
            
            2.Check wether screen rpm pakcage installed or not. Reference check item screen.
            
            """)
            return False

    def inisysdatetime(self):
        now = datetime.now()
        datestr_l = f'{now.year}-{now.month}-{now.day}'
        datestr_w = f'{now.month}-{now.day}-{now.year}'
        timestr = f'{now.hour}:{now.minute}:{now.second}'
        # print(datestr_l, datestr_w, timestr)
        res = None

        # check datetime
        if self.sut.SUT_PLATFORM == SUT_STATUS.S0.WINDOWS:
            cmd_g = 'echo %date:~10,4% %date:~4,2% %date:~7,2% %time:~0,2% %time:~3,2% %time:~6,2%'
        else:
            cmd_g = "date '+%Y %m %d %H %M'"

        ret, out, err = self.sut.execute_shell_cmd(cmd_g)

        isset = False
        if ret == 0:
            out = out.strip().split()
            # print(out)

            if int(now.year) != int(out[0]):
                isset = True

            if int(now.month) != int(out[1]):
                isset = True

            if int(now.day) != int(out[2]):
                isset = True

            if int(now.hour) != int(out[3]):
                isset = True

            if int(now.second) != int(out[4]):
                isset = True

        # setup datetime
        if isset:
            if self.sut.SUT_PLATFORM == SUT_STATUS.S0.WINDOWS:
                cmd_s = f'date {datestr_w} && time {timestr}'
                cmd_w = 'echo %date% %time%'
            else:
                cmd_s = f"date -s '{datestr_l} {timestr}' && date"
                cmd_w = "clock -w"

            ret, out, err = self.sut.execute_shell_cmd(cmd_s)
            if ret == 0:
                self.sut.execute_shell_cmd(cmd_w)
                logger.info("PASS: Setup system datetine done.")
                return True
            else:
                res = False

        # check system datetime pass
        else:
            res = True

        if res:
            logger.info("PASS: Check system datetime done.")
        else:
            logger.info("""
            FAIL: Check system datetime failed.
            PROMPT
            1.Check network driver link status. Reference check item sshd.
            
            2.set system datetime manualy.
              linux cmd: date -s "year-moth-day hout:minute:second"  example: date -s "2021-06-14 00:00:00"
                         clock -w
                         date '+%F %H:%M:S%'
              windows cmd: 
            
            """)


def test_steps(sut):
    sutchk = SutCheck(sut)

    # Step 1
    Case.step("check sshd service")
    Case.expect('sshd service correct', sutchk.sshd())

    # Step 2
    Case.step("check python3 interpreter")
    Case.expect('python3 interpreter correct', sutchk.py3interpreter())

    # Step 3
    Case.step("check xmlcli tool in OS")
    Case.expect('xmlcli tool in OS correct', sutchk.xmlclios())

    # Step 4
    Case.step("check xmlcli tool in uefi shell FS0 driver")
    Case.expect('xmlcli tool in uefi shell FS0 driver correct', sutchk.xmlcliefi())

    # Step 5
    Case.step("check linux screen rpm")
    Case.expect('linux screen rpm correct', sutchk.screen())

    # Step 6
    Case.step("check firewall service")
    Case.expect('firewall service correct', sutchk.firewalld())

    # Step 7
    Case.step("check linux selinux service")
    Case.expect('linux selinux service correct', sutchk.selinux())

    # Step 8
    Case.step("check async cmd mode in linux")
    Case.expect('async cmd mode in linux correct', sutchk.cmdasync())

    # Step 9
    Case.step("check system datetime")
    Case.expect('system datetime correct', sutchk.inisysdatetime())


def test_main():
    sut = get_default_sut()

    try:
        Case.start(sut, CASE_DESC)
        test_steps(sut)

    except Exception as e:
        Result.get_exception(e, str(traceback.format_exc()))
    finally:
        Case.end()


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)
