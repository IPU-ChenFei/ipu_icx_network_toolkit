import abc
import re
import datetime
import time
# from src.lib.toolkit.auto_api import *
from dtaf_core.lib.tklib.auto_api import *
from xml.etree import ElementTree as ET
# from src.lib.toolkit.basic.testcase import Case
from dtaf_core.lib.tklib.basic.testcase import Case
# from src.lib.toolkit.infra.sut import get_default_sut
from dtaf_core.lib.tklib.infra.sut import get_default_sut
from dtaf_core.drivers.driver_factory import DriverFactory
from dtaf_core.drivers.internal.simics_driver import SimicsDriver
from dtaf_core.drivers.internal.console.console import Channel
from dtaf_core.lib.configuration import ConfigurationHelper
# from src.lib.toolkit.infra.logs.dtaf_log import dtaf_logger
from dtaf_core.lib.tklib.infra.logs.dtaf_log import dtaf_logger
# from src.lib.toolkit.infra.dtaf_config import update_simics_config
from dtaf_core.lib.tklib.infra.dtaf_config import update_simics_config


class OSInstaller:
    def __init__(self, sut):
        self.sut = sut
        self.remote_path = None
        self.local_path = None
        self.script = None
        os_info = self.sut.cfg[self.sut.cfg['defaults']['default_os_boot']]
        self.usr = os_info['user']
        self.pwd = os_info['password']
        self.cfg = ET.fromstring(f"""
        <dc>
            <driver>
                <simics>
                    <mode>
                        <real-time>True</real-time>
                    </mode>
                    <serial_port>2122</serial_port>
                    <host>
                        <name>10.148.205.212</name>
                        <port>22</port>
                        <username>xxxxxx</username>
                        <password>xxxxxx</password>
                    </host>
                    <os>centos_stream</os>
                    <service_port>2123</service_port>
                    <app>/nfs/site/disks/simcloud_users/czhao/workarea/projects/gnr-6.0/2021ww35.3/simics</app>
                    <project>/nfs/site/disks/simcloud_users/czhao/workarea/projects/gnr-6.0/2021ww35.3</project>
                    <script>/nfs/site/disks/simcloud_users/czhao/workarea/projects/gnr-6.0/2021ww35.3/targets/birchstream/birchstream-ap.simics</script>
                </simics>
            </driver>
            <timeout>
                <power_on>5</power_on>
                <power_off>20</power_off>
            </timeout>
        </dc>
        """)
        update_simics_config(self.cfg, sut.cfg['simics'])

    @abc.abstractmethod
    def init_env(self):
        pass

    @abc.abstractmethod
    def run_script(self):
        pass

    def copy_setup_script(self):
        self.execute_simics_cmd(f'matic0.run "mkdir {self.local_path}"')
        self.execute_simics_cmd(rf'matic0.upload-dir from="{self.remote_path}"'
                                rf' to="{self.local_path}" -verbose', timeout=120)

    def execute_simics_cmd(self, cmd, until_pat=r"([\s\S]+running>)+", timeout=30):
        driver_cfg = ConfigurationHelper.get_driver_config(provider=self.cfg, driver_name=r"simics")
        with DriverFactory.create(cfg_opts=driver_cfg, logger=dtaf_logger) as sw:  # type: SimicsDriver
            sw.register("run_cmd")
            simics = sw.SimicsChannel  # type: Channel
            ret = simics.execute_until(f"{cmd}\r\n", until_pat, timeout)
            sw.unregister("run_cmd")
        assert (ret and "run command fail")
        return ret

    def save_craff(self):
        cur_day = datetime.date.today()
        self.execute_simics_cmd("stop", until_pat=r"simics>")
        self.execute_simics_cmd(f"birchstream.nvme.nvme_disk_image.save -save-craff "
                                f"{self.sut.cfg['simics']['simics_project']}/"
                                f"{self.sut.default_os_boot}_{cur_day.strftime('%Y%m%d')}.craff"
                                , until_pat=r"simics>", timeout=600)

    def run(self):
        Case.step(f"Start {self.sut.SUT_PLATFORM} OS Installer.")
        self.init_env()
        Case.step(f"Target OS detected. Start Copy setup script.")
        self.copy_setup_script()
        time.sleep(60)
        Case.step(f"Run setup script.")
        self.run_script()
        Case.step(f"Tool installed. Save OS craff to current project folder.")
        my_os = OperationSystem[OS.get_os_family(self.sut.default_os)]
        my_os.warm_reset_cycle_step(self.sut)
        self.save_craff()


class LINUXInstaller(OSInstaller):
    def __init__(self, sut):
        super().__init__(sut)
        self.local_path = '/root/setup'
        self.remote_path = '/nfs/site/disks/simcloud_zijianhu_002/sut/linux'
        self.script = "os_initial_linux.sh"

    def init_env(self):
        self.execute_simics_cmd("start-agent-manager")
        self.execute_simics_cmd("agent_manager.connect-to-agent")
        driver_cfg = ConfigurationHelper.get_driver_config(provider=self.cfg, driver_name=r"simics")
        with DriverFactory.create(cfg_opts=driver_cfg, logger=dtaf_logger) as sw:  # type: SimicsDriver
            sw.register("wait_for_os")
            data = ""
            serial = sw.SerialChannel  # type: Channel
            while True:
                d = serial.read_from()
                if d:
                    data += d
                    if re.search("embargo login:", data):
                        break
            serial.execute_until("root\r\n", "root@embargo", timeout=30)
            serial.execute_until(f"echo '{self.pwd}' | passwd --stdin {self.usr}\r\n", "root@embargo", timeout=30)
            serial.execute_until("simics-agent &\r\n\r\n", "root@embargo", timeout=30)
            sw.unregister("wait_for_os")

    def run_script(self):
        now = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        self.sut.execute_shell_cmd(f'date -s "{now}"')
        self.sut.execute_shell_cmd(f"chmod +x {self.script}", cwd='/root/setup/linux')
        self.sut.execute_shell_cmd(f"dos2unix {self.script}", cwd='/root/setup/linux')
        ret, _, _ = self.sut.execute_shell_cmd(f"./{self.script}", timeout=3600, cwd='/root/setup/linux')
        Case.expect("Install tools successfully.", ret == 0)


class WINDOWSInstaller(OSInstaller):
    def __init__(self, sut):
        super().__init__(sut)
        self.remote_path = '/nfs/site/disks/simcloud_zijianhu_002/sut/windows'
        self.local_path = 'C:\\\\setup'
        self.script = "os_initial_win.bat"

    def init_env(self):
        self.execute_simics_cmd("start-agent-manager")
        self.execute_simics_cmd("agent_manager.connect-to-agent")
        while True:
            self.execute_simics_cmd("stop", until_pat=r"simics>")
            ret = self.execute_simics_cmd("agent_manager.status", until_pat=r"([\s\S]+simics>)+")
            pat = re.compile(r"Simics Agents\s*:\s*([1-9]+)")
            if re.findall(pat, ret):
                self.execute_simics_cmd("run")
                break
            self.execute_simics_cmd("run")
            time.sleep(60)
        self.execute_simics_cmd(f'matic0.run "net user {self.usr} {self.pwd}"')

    def run_script(self):
        now = time.strftime("%m/%d/%Y %H:%M:%S", time.localtime())
        day, tick = now.split(" ")
        self.sut.execute_shell_cmd(f'date {day}')
        self.sut.execute_shell_cmd(f'time {tick}')
        ret, _, _ = self.sut.execute_shell_cmd(f"{self.script}", timeout=3600, cwd="C:\\setup\\windows")
        Case.expect("Install tools successfully.", ret == 0)


class VMWAREInstaller(OSInstaller):
    def __init__(self, sut):
        super().__init__(sut)

    def init_env(self):
        pass

    def copy_setup_script(self):
        pass

    def run_script(self):
        now = time.localtime()
        self.sut.execute_shell_cmd(f'esxcli system time set -y {now.tm_year} -M {now.tm_mon} -d {now.tm_mday}'
                                   f'-H {now.tm_hour} -m {now.tm_min} -s {now.tm_sec}')
        self.sut.execute_shell_cmd("esxcli network firewall set --enabled false", timeout=60)


if __name__ == '__main__':
    sut = get_default_sut()
    Case.start(sut, [f'Simics {sut.default_os_boot} OS Installer'])
    sut.ac_on()
    installer = eval(f"{sut.SUT_PLATFORM}Installer(sut)")
    installer.run()
    sut.ac_off()
    Case.end()
