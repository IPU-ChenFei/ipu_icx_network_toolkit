import subprocess
import datetime
import os
import re
import threading
import time
from shutil import copyfile

from dtaf_core.drivers.driver_factory import DriverFactory
from dtaf_core.lib.configuration import ConfigurationHelper
from dtaf_core.lib.exceptions import InvalidParameterError
from dtaf_core.providers.console_log import ConsoleLogProvider

from dtaf_core.lib.tklib.basic.log import LogAll, get_com_logger
from dtaf_core.lib.tklib.basic.utility import remove_terminal_sequences, get_tag_value
from dtaf_core.lib.tklib.infra.logs.dtaf_log import dtaf_logger


def gen_wait_and_expect_func(sleep_time, func,  *args):
    ret = func(*args)
    time.sleep(sleep_time)
    return ret


def get_ether_name(exec_func, nic_id, nic_port_index):
    bdf = get_bdf(exec_func, nic_id, nic_port_index)
    _, ether_name, std_err = exec_func(f'ls /sys/bus/pci/devices/{bdf}/net')
    if ether_name == '':
        raise RuntimeError(f'can not get ether name for {std_err}')
    ether_name = str(ether_name).replace('\n', '')
    return ether_name


def get_bdf(exec_func, nic_id, nic_port_index):
    _, nics, _ = exec_func(f'lspci | grep -i {nic_id}')
    if nics == '':
        raise RuntimeError(f"can not find any nic according to id {nic_id}")
    nics = str(nics)[:-1].split('\n')

    if nic_port_index == -1:
        nic_info = [nic.strip().split(' ') for nic in nics]
        bdf = [info[0] for info in nic_info]
        for i in range(len(bdf)):
            if len(bdf[i].split(":")) == 2:
                bdf[i] = "0000:" + bdf[i]
    else:
        nic_info = nics[nic_port_index].strip().split(' ')
        bdf = nic_info[0]
        if len(bdf.split(":")) == 2:
            bdf = "0000:" + bdf
    return bdf


def get_ip(exec_func, net_interface, mode='ipv4'):
    """
        Acquire IPV4 address
        :param exec_func: function name. Optional: [sut.execute_shell_cmd, MEV.execute_imc_cmd, vm.execute_vm_cmd]
        :param net_interface: Ethernet interface name
        :param mode: 'ipv4' or 'ipv6'
        :return: String: IPV4 address
        :raise AttributeError if couldn't get the address.
    """
    _, ifcfg, _ = exec_func(f"ifconfig {net_interface}")
    if mode == 'ipv4':
        return re.search(r'((2[0-5]|1[0-9]|[0-9])?[0-9]\.){3}((2[0-5]|1[0-9]|[0-9])?[0-9])', ifcfg, re.I).group()
    elif mode == 'ipv6':
        pat = '[a-fA-F-0-9]{4}'
        return re.search(rf'{pat}::{pat}:{pat}:{pat}:{pat}', ifcfg, re.I).group()
    else:
        raise RuntimeError("Unsupported Mode")


def ping_to_peer(exec_func, dst_ip, src_ip=None, mode='ipv4'):
    """
    Ping to specific IP address with given function name
    :param exec_func: function name. Optional: [sut.execute_shell_cmd, MEV.execute_imc_cmd, vm.execute_vm_cmd]
    :param dst_ip: destination IP address to ping to
    :param src_ip: source IP to ping from
    :param mode: 'ipv4' or 'ipv6'
    :return: Bool, True if ping is successfully, and vase vice
    """
    _, out, _ = exec_func(f'ping -{mode[-1]} -c 20 -I {src_ip} {dst_ip}', timeout=60)
    loss_data = re.search(r'(\d+)% packet loss', out).group(1)
    # if loss percentage larger than 20%, check fail
    if int(loss_data) > 20:
        return False
    else:
        return True


def execute_host_cmd(cmd, timeout=10, cwd=None, env=None):
    """
    default windows shell is cmd.
    returncode: execute successfully:0(zero), execute failed: not zero
    """
    child = subprocess.Popen(cmd,
                             shell=True,
                             stdin=subprocess.PIPE,
                             stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE,
                             cwd=cwd,
                             env=env)

    out, err = child.communicate(timeout=timeout)
    returncode = child.returncode
    return returncode, out.decode(encoding='utf-8'), err.decode(encoding='utf-8')


def iperf3_data_conversion(number, old_unit, new_unit):
    UNIT = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y', 'B')

    old_unit_index = UNIT.index(old_unit.upper())
    new_unit_index = UNIT.index(new_unit.upper())

    return number * (1024 ** (old_unit_index - new_unit_index))


def get_core_list(sut):
    """
    return: cores under socket 1. [start1, end1, start2, end2]
    """
    core_list = []
    _, out, _ = sut.execute_shell_cmd("cat /sys/devices/system/node/node1/cpulist")
    cpu_list = out.strip('\n').split(',')
    for item in cpu_list:
        cores = item.split('-')
        core_list.extend(int(core) for core in cores)
    return core_list


class BaseConsoleLogProvider2(ConsoleLogProvider):
    """
    Base Class that record all output data into log file.
    """

    def __init__(self, console_log_cfg, name):
        """
        Create a new ConsoleLogPrvd object.
        :param self._console_log_cfg: xml.etree.ElementTree.Element of configuration options for execution environment
        :param logger: Logger object to use for output messages
        """
        file_name = "{}_timestamp.log".format(name)
        com_port = get_tag_value(console_log_cfg, 'port')
        file_path = LogAll.register(f'{name} log with timestamp', file_name)
        comlogger = get_com_logger(com_port, file_path)

        super(BaseConsoleLogProvider2, self).__init__(console_log_cfg, dtaf_logger)
        self.buffer_name = 'console_buffer'
        self.keyword_buffer = None
        self.runtime_buffer = None
        self.runtime_lock = threading.Lock()
        self.buffer_size = 4 * 1024 * 1024
        self.lock = threading.Lock()
        self.repo = ""
        if console_log_cfg.find('.//com'):
            self.drv_opts = ConfigurationHelper.get_driver_config(provider=console_log_cfg, driver_name='com')
        elif console_log_cfg.find('.//sol'):
            self.drv_opts = ConfigurationHelper.get_driver_config(provider=console_log_cfg, driver_name='sol')
        elif console_log_cfg.find('.//wsol'):
            self.drv_opts = ConfigurationHelper.get_driver_config(provider=console_log_cfg, driver_name='wsol')
        else:
            raise InvalidParameterError('Driver {com, sol, wsol} lost for ConsolelogProvider')

        self.log_file = LogAll.register(f'{name} log without timestamp', f'{name}.log')
        self.log_path = os.path.dirname(self.log_file)
        if not os.path.exists(self.log_path):
            os.makedirs(self.log_path)
        self.log_name = os.path.basename(self.log_file)

        self.console_log = open(self.log_file, 'a+', encoding='utf-8')
        self.console_logger = comlogger

        self.serial = DriverFactory.create(self.drv_opts, dtaf_logger)
        self.serial.register(self.buffer_name, self.buffer_size)

        self.log_thread = threading.Thread(target=self._log_thread)
        self.log_thread.setDaemon(True)
        self.log_thread.start()

    def __enter__(self):
        return super(BaseConsoleLogProvider2, self).__enter__()

    def __exit__(self, exc_type, exc_val, exc_tb):
        try:
            self.lock.acquire()
            if self.console_log:
                self.console_log.close()
            if self.repo:
                for handler in self._log.root.handlers:
                    dest_file = os.path.join(self.repo, os.path.basename(handler.baseFilename))
                    copyfile(handler.baseFilename, dest_file)
                copyfile(self.log_file, os.path.join(self.repo, self.log_name))
        except Exception as ex:
            print(ex)
        finally:
            self.lock.release()
            self.serial._release_resource()
        super(BaseConsoleLogProvider2, self).__exit__(exc_type, exc_val, exc_tb)

    def inject_line(self, line):
        # type: (str) -> None
        """
        Insert a separate line into serial log file.

        :param line: data line, any sequence that can be converted into string
        :return: None
        """
        line = str(line) if line else ''
        self.lock.acquire()
        try:
            self.console_logger.info(line)
            self.console_log.write('\n' + line + '\n')
            self.console_log.flush()
        finally:
            self.lock.release()

    def _log_thread(self):
        self._logline = ''
        while True:
            self.lock.acquire()
            try:
                data = self.serial.read_from(self.buffer_name)
                if not data:
                    # sleep(): release GIL so that it can be used for other threads
                    time.sleep(0)
                    continue
                else:
                    self._logline += data
                    if not self.console_log.closed:
                        if '\n' in self._logline:
                            dl = self._logline.split('\n')
                            for i in range(len(dl) - 1):
                                self.console_logger.info(remove_terminal_sequences(dl[i]) + '\n')
                                self.console_log.write(remove_terminal_sequences(dl[i]) + '\n')
                            self.console_log.flush()
                            self._logline = dl[-1]
            finally:
                self.lock.release()

        # Handle the rest data
        if self.conself.console_log:
            self.self.console_log.write(remove_terminal_sequences(self._logline))
            self.console_log.flush()
        if self.console_logger:
            self.console_logger.info(remove_terminal_sequences(self._logline))

    def read(self):
        """
        read data from console
        :return: data buffer received from console
        """
        try:
            self.runtime_lock.acquire()
            if self.runtime_buffer is None:
                self.runtime_buffer = r"runtime_buffer"
                self.serial.register(self.runtime_buffer, self.buffer_size)
        finally:
            self.runtime_lock.release()
        return self.serial.read_from(self.runtime_buffer)

    def write(self, buf):
        """
        write data to console
        """
        try:
            self.runtime_lock.acquire()
            if self.runtime_buffer is None:
                self.runtime_buffer = r"runtime_buffer"
                self.serial.register(self.runtime_buffer, self.buffer_size)
        finally:
            self.runtime_lock.release()
        return self.serial.write(buf) == len(buf)

    def make_repo(self, path):
        self.repo = path
        if path and not os.path.exists(self.repo):
            os.makedirs(self.repo)

    def redirect(self, log_file):
        try:
            self.log_file = log_file
            self.lock.acquire()
            self.runtime_lock.acquire()
            if self.console_log:
                self.console_log.close()
            self.console_log = open(self.log_file, 'a+', encoding='utf-8')
        finally:
            self.runtime_lock.release()
            self.lock.release()

    def search_for_keyword(self, pattern, timeout):
        # type:(str,int)-> bool
        """
        The API will search the data in console for the keyword. It will
        return if the specified pattern detected or timeout

        :param pattern:
        :param timeout:
        :return: True/False
        :raise DriverIOError:if fail to read data
        """
        try:
            self.runtime_lock.acquire()
            if self.keyword_buffer is None:
                self.keyword_buffer = r"keyword_buffer"
                self.serial.register(self.keyword_buffer, self.buffer_size)
        finally:
            self.runtime_lock.release()
        start_time = datetime.datetime.now()
        data = ''
        while (datetime.datetime.now() - start_time).seconds < timeout:
            content = self.serial.search_data(self.keyword_buffer)
            data += content
            if re.search(pattern, data):
                return True
        return False


