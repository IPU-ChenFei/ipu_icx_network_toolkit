import os
import sys

parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
parent_dir += r'\src'
sys.path.insert(0, parent_dir)

from src.lib.toolkit.basic.testcase import *
from src.lib.toolkit.infra.sut import *
import os

CASE_DESC = [
    'check host environment'
]


class HostCheck:

    def __init__(self, sut):
        self.sut = sut

    def py3interpreter(self, file):
        if os.path.exists(file):
            logger.info("PASS: Check python3 interpreter is installed.")
            return True
        else:
            logger.info("""
            
            FAIL: Python3 interpreter is not installed.
            PROMPT:
            1.Pls install python3 interpreter with default path and select ADD PAHT checkbox.
            
            2.Check python interpreter installed successfully.
              cmd: python -h
              
            3.Check python related path is added to system environment variable PATH.
              example: C:\\Python36
                       C:\\Python36\\Scripts
              cmd: set
            
            """)
            return False

    def localip(self):
        ip = '192.168.0.1'
        cmd = f'ping -n 2 {ip}'
        ret, out, err = self.sut.execute_host_cmd(cmd)
        if ret == 0:
            logger.info("PASS: Check local network link status.")
            return True
        else:
            logger.info("""
            
            FAIL: local network link status is down.
            PROMPT:
            1.Pls set ip address(192.168.0.1) on you network driver manualy.
            
            2.Execute cmd to check local network link status.
              cmd: ping 192.168.0.1
              
            """)
            return False

    def internetip(self):
        cmd = 'nslookup www.intel.com'
        ret, out, err = self.sut.execute_host_cmd(cmd)
        tmpstr = 'e11.dsca.akamaiedge.net'
        if tmpstr in out:
            logger.info("PASS: Check internet network link status.")
            return True
        else:
            logger.info("""

            FAIL: Internet network link status is down.
            PROMPT:
            1.Pls check your network driver physical connection.
            
            2.Makesure that network driver could get IP automaticly
            
            2.Execute cmd to check intelnet ip link status.
              cmd: nslookup www.intel.com 

            """)
            return False

    def vcpp2015u3(self, file):
        if os.path.exists(file):
            logger.info("PASS: VC++ 2015 buildtools is installed.")
            return True
        else:
            logger.info("""

            FAIL: VC++2015 buildtools is not installed.
            PROMPT:
            Pls install vc++2015 buildtools by launch VisualCppBuildTools_Full.exe in
            the directory 'setup/host/tools/vcpp2015u3'. 

            """)
            return False

    def dtafcore(self):
        cwd = 'C:\\Python36'
        name = "python.exe"
        file = os.path.join(cwd, name)
        if self.py3interpreter(file):
            cmd = 'pip show dtaf-core'
            ret, out, err = self.sut.execute_host_cmd(cmd, cwd=cwd)
            if ret == 0:
                logger.info("PASS: Check dtaf-core is installed.")
                return True
            else:
                logger.info("""

                FAIL: Dtaf-core is not installed.
                PROMPT:
                1.Create a file named 'pip.ini' in the directory 'C:\\Users\\%USERNAME%\\pip'
                  '%USERNAME%' is the username which you used to login in Windows OS.
                  Example: C:\\Users\\Administrator\\pip\\pip.ini

                2.Edit the file 'C:\\Users\\%USERNAME%\\pip\\pip.ini'
                  [global]
                  index-url = https://af01p-png.devtools.intel.com/artifactory/api/pypi/dtaf-framework-release-png-local/simple
                  extra-index-url = https://pypi.org/simple
                  proxy=http://child-prc.intel.com:911

                3.Check internet network link is up.

                4.Install dtaf-core with pip tool.
                  cmd: pip install dtaf-core

                5.Check dtaf-core is installed or not.
                  cmd: pip show dtaf-core

                """)
                return False

    def dtafcorerequirements(self):
        pass

    def frmwkrequires(self):
        cwd = 'C:\\Python36'
        name = "python.exe"
        file = os.path.join(cwd, name)
        if self.py3interpreter(file):
            pkgs = ['pyqt5, pywin32']
            for pkg in pkgs:
                cmd = f'pip show {pkg}'
                ret, out, err = self.sut.execute_host_cmd(cmd, cwd=cwd)
                if ret != 0:
                    logger.info(f"""
    
                    FAIL: Check automation framework requirements. 
                          [{pkg}] not installed.
                    PROMPT:
                    1.Check internet network link is up.
    
                    2.Install requirement.
                      cmd: pip install {pkg} --proxy http://child-prc.intel.com:911
    
                    3.Check {pkg} pacakge is installed or not.
                      cmd: pip show {pkg} 
    
                    """)

                    return False

            logger.info("PASS: Automation framework requirements are installed.")
            return True


def test_steps(sut):
    hostchk = HostCheck(sut)

    # Step 1
    Case.step("check python3 interpreter")
    py3_file = 'C:\Python36\python.exe'
    Case.expect('python3 interpreter correct', hostchk.py3interpreter(py3_file))

    # Step 2
    Case.step("check vcpp2015u3 build tools")
    vcpp_file = 'C:\\Program Files (x86)\\Microsoft Visual C++ Build Tools\\vcbuildtools.bat'
    Case.expect('vcpp2015u3 build tools correct', hostchk.vcpp2015u3(vcpp_file))

    # Step 3
    Case.step("check dtaf-core")
    Case.expect('dtaf-core correct', hostchk.dtafcore())

    # Step 4
    Case.step("check frmwkrequires")
    Case.expect('frmwkrequires correct', hostchk.frmwkrequires())

    # Step 5
    # Case.step('check power control')
    # hostchk.powerctl()


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
