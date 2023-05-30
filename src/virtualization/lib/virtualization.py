import os.path
import re
import time
import traceback

import requests
import atexit
from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect

from src.virtualization.lib.tools.pchelper import *
from src.virtualization.lib.util import *
from src.virtualization.lib.const import *


class Hypervisor:
    CALLER_COMMAND_BASE = ''

    def __init__(self, sut):
        # type: (SUT) -> None
        self.sut = sut
        self.vm_list = {}

    def is_upload_src_path_exist(self, src_path):
        if 'linux' in self.CALLER_COMMAND_BASE.lower():
            cmd = f'ls -l {src_path}'
            err_keyword = 'no such file or directory'
        else:
            cmd = f'dir {src_path}'
            err_keyword = 'File Not Found'
        _, _, std_err = self.sut.execute_shell_cmd(cmd)
        return err_keyword not in std_err

    def copy_template_to_disk(self, vm_name, template, disk_dir):
        if 'linux' in self.CALLER_COMMAND_BASE.lower():
            disk_path = f'{disk_dir}/{vm_name}.qcow2'
            cmd = f'cp {template} {disk_path}'
        else:
            disk_path = f'{disk_dir}\\{vm_name}.vhdx'
            cmd = f'copy {template} {disk_path}'

        logger.info(f'copying {template} to {disk_path}, wait a while please...\n')
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd, timeout=3000)
        if rcode != 0:
            raise Exception(std_err)

    def __is_vm_os_linux(self, vm_name):
        return "rhel" in vm_name or "cent" in vm_name

    def __check_is_vm_in_os_by_log(self, vm_name):
        try:
            _, pre_log, std_err = self.__execute_vm_cmd(vm_name, "journalctl -n 1 --no-pager", timeout=10)
            if std_err != "":
                logger.info(f"Ignored execute command error in {vm_name}: {std_err}")
                time.sleep(10)
                return False
            time.sleep(10)
            cur_log = self.__execute_vm_cmd(vm_name, "journalctl -n 1 --no-pager", timeout=10)[1]
            if "Startup finished" in cur_log:
                logger.info("VM log satisfied")
                return True
            if pre_log.strip().split(":")[-1] == cur_log.strip().split(":")[-1]:
                logger.info("VM log satisfied")
                return True
            return False
        except Exception:
            logger.info(f"Ignore timeout error for check if {vm_name} has been boot to os")
            return False

    def create_vm_snapshot(self, vm_name, snap_name):
        """
        Reference:
            None
        Purpose: to create a snapshot of VM
        Args:
            vm_name: the name of new VM
            snap_name: the name of snapshot
        Returns:
            None
        Raises:
            RuntimeError: If any errors
        Example:
            Create a new snapshot for VM 'RHEL1', the snapshot named 's1'
                create_vm_snapshot('RHEL1', 's1')
        """
        raise NotImplemented

    def delete_vm_snapshot(self, vm_name, snap_name):
        """
        Reference:
            None
        Purpose: to delete the sanpshot of VM
        Args:
            vm_name: the name of new VM
            snap_name: the name of snapshot going to be deleted
        Returns:
            None
        Raises:
            RuntimeError: If any errors
        Example:
            Delete the RHEL1's snapshot named 's1'
                delete_vm_snapshot('RHEL1', 's1')
        """
        raise NotImplemented

    def download_from_vm(self, vm_name, src_path, dest_path):
        """
        Reference:
            None
        Purpose: to download file from VM
        Args:
            vm_name: the name of VM
            src_path: the remote file path in VM
            dest_path: the local file path in SUT
        Returns:
            None
        Raises:
            RuntimeError: If any errors
        Example:
            Usage: download '/home/test.txt' in VM 'RHEL1' to '/root/test.txt' in SUT
                download_from_vm('RHEL1', '/home/test.txt', '/root/test.txt')
        """
        logger.info(f"download file from <{vm_name}>:{src_path} to <{self.sut.sut_name}>:{dest_path}")

        if not self.is_vm_running(vm_name):
            raise Exception(f'download file from virtual machine failed: {vm_name} is not running')

        cmd = self.CALLER_COMMAND_BASE
        cmd += '--command download_from_vm '
        cmd += f'--vm-name {vm_name} '
        cmd += f'--src-path {src_path} '
        cmd += f'--dest-path {dest_path} '
        cmd += f'--ssh-port 22 '

        rcode, _, std_err = self.sut.execute_shell_cmd(cmd=cmd, timeout=600)
        if rcode != 0:
            raise Exception(std_err)

    def execute_vm_cmd(self, vm_name, vm_cmd, cwd=".", timeout=30, powershell=False):
        """
        Reference:
            None
        Purpose: to execute a command in virtual machine
        Args:
            vm_name: the name of VM
            vm_cmd: the command going to be executed in VM, e.g. ls -al
            cwd: the command running path
            timeout: the timeout that wait for the command respond
            powershell: if this parameter was set to True, command will be ran in powershell
        Returns:
            code: the command executed result code
            out: the stdout after command executed
            err: the stderr after command executed
        Raises:
            RuntimeError: If any errors
        Example:
            Execute command 'ls -al /root/Documents/test.txt' in VM 'RHEL1'
                code, out, err = execute_vm_cmd('RHEL1', 'ls -al /root/Documents/test.txt')
        """
        logger.info(f'<{vm_name}> execute cmd [cmd: {vm_cmd} timeout: {timeout}]')

        if not self.is_vm_running(vm_name):
            raise Exception(f'execute command in virtual machine failed: {vm_name} is not running')

        if powershell:
            vm_cmd = f'cd {cwd}; {vm_cmd}'
        else:
            vm_cmd = f'cd {cwd} && {vm_cmd}'

        if powershell:
            vm_cmd = 'PowerShell -Command "& { ' + vm_cmd + ' }"'

        vm_cmd = vm_cmd.replace('"', '@@')
        return self.__execute_vm_cmd(vm_name, vm_cmd, timeout)

    def execute_vm_cmd_async(self, vm_name, vm_cmd, cwd=".", timeout=30, powershell=False):
        """
        Reference:
            None

        Purpose: to execute a command in virtual machine async

        Args:
            vm_name: the name of VM
            vm_cmd: the command going to be executed in VM, e.g. ls -al
            cwd: the command running path
            timeout: the timeout that wait for the command respond
            powershell: if this parameter was set to True, command will be ran in powershell

        Returns:
            code: the command executed result code
            out: the stdout after command executed
            err: the stderr after command executed

        Raises:
            RuntimeError: If any errors

        Example:
            Execute command 'ls -al /root/Documents/test.txt' in VM 'RHEL1'
                code, out, err = execute_vm_cmd_async('RHEL1', 'ls -al /root/Documents/test.txt')
        """
        logger.info(f'<{vm_name}> execute cmd [cmd: {vm_cmd} timeout: {timeout}]')

        if not self.is_vm_running(vm_name):
            raise Exception(f'execute command in virtual machine failed: {vm_name} is not running')

        if self.__is_vm_os_linux(vm_name):
            vm_cmd = f'cd {cwd} && {vm_cmd}'

        if powershell:
            vm_cmd = f'cd {cwd}; {vm_cmd}'
        else:
            vm_cmd = f'cd {cwd} && {vm_cmd}'

        if powershell:
            vm_cmd = 'PowerShell -Command "& { ' + vm_cmd + ' }"'

        vm_cmd = vm_cmd.replace('"', '@@')
        return self.__execute_vm_cmd_async(vm_name, vm_cmd, timeout)


    def __execute_vm_cmd(self, vm_name, vm_cmd, timeout):
        cmd = self.CALLER_COMMAND_BASE
        cmd += '--command execute_vm_cmd '
        cmd += f'--vm-name {vm_name} '
        cmd += f'--timeout {timeout} '
        cmd += f'--vm-command \"{vm_cmd}\" '
        cmd += f'--ssh-port 22'

        rcode, std_out, std_err = self.sut.execute_shell_cmd(cmd, timeout=(timeout + 60))
        std_out = '\n'.join(std_out.split('\n')[1:])
        return rcode, std_out, std_err

    def __execute_vm_cmd_async(self, vm_name, vm_cmd, timeout):
        cmd = self.CALLER_COMMAND_BASE
        cmd += '--command execute_vm_cmd '
        cmd += f'--vm-name {vm_name} '
        cmd += f'--timeout {timeout} '
        cmd += f'--vm-command \"{vm_cmd}\" '
        cmd += f'--ssh-port 22'

        rcode, std_out, std_err = self.sut.execute_shell_cmd_async(cmd, timeout=(timeout + 60))
        std_out = '\n'.join(std_out.split('\n')[1:])
        return rcode, std_out, std_err

    def get_vm_disk_list(self, vm_name):
        """
        Reference:
            None
        Purpose: to get the virtual disk list of VM
        Args:
            vm_name: the name of new VM
        Returns:
            a list of disk in VM, e.g. [vda, vdb, sda, sdb]
        Raises:
            RuntimeError: If any errors
        Example:
            Get the virtual disk list of RHEL1
                disk_list = get_vm_disk_list('RHEL1')
        """
        raise NotImplemented

    def get_vm_ip_list(self, vm_name):
        """
        Reference:
            None
        Purpose: to get the list of VM IP addresses
        Args:
        Returns:
            a list which contains all the IP addresses of VM
        Raises:
            RuntimeError: If any errors
        Example:
            Get all the IP address of 'RHEL1'
                ip_list = get_vm_ip_list('RHEL1')
        """
        raise NotImplemented

    def get_vm_list(self):
        """
        Reference:
            None
        Purpose: to get the list of existing VM
        Args:
        Returns:
            a list which contains all the name of existing VM
        Raises:
            RuntimeError: If any errors
        Example:
            Get all the VM names (running and not running)
                vm_list = get_vm_list()
        """
        raise NotImplemented

    def get_vm_memory(self, vm_name):
        """
        Reference:
            None
        Purpose: to get the memory of VM
        Args:
            vm_name: the name of VM
        Returns:
            the value of VM memory in MB
        Raises:
            RuntimeError: If any errors
        Example:
            get the memory of RHEL1
                mem = get_vm_memory('RHEL1')
        """
        raise NotImplemented

    def get_vm_snapshot_list(self, vm_name):
        """
        Reference:
            None
        Purpose: to get the snapshot list of VM
        Args:
            vm_name: the name of VM
        Returns:
            the list of snapshot
        Raises:
            RuntimeError: If any errors
        Example:
            get the snapshot list of RHEL1
                snap_list = get_vm_snapshot_list('RHEL1')
        """
        raise NotImplemented

    def iperf_stress(self, duration, proto='tcp', *conn):
        """
        Run iperf stress with duration seconds, and check results meet connection requirements
        Recommend to use script on SUT OS for completing this
        Need to run 4 iperf threads for getting the correct tcp throughput (especially for high speed/rate connection)
        Args:
            duration: stress time, unit is second
            proto: tcp/udp
            *conn: interface.NicPortConnection object
        Returns:
            None
        Raises:
            RuntimeError: If any errors
        """
        MAX_PROCESS_NUM = 4
        DEFAULT_PORT_NO = 5201

        if proto != 'tcp':
            raise RuntimeError('iperf_stress only support tcp test')

        for conn_inst in conn:
            port1 = conn_inst.port1
            port2 = conn_inst.port2
            sut1 = port1.sut
            sut2 = port2.sut

            log_folder_name = 'iperf_test'
            if sut2.default_os == SUT_PLATFORM.WINDOWS:
                remote_folder_path = sut_tool('SUT_TOOLS_WINDOWS_VIRTUALIZATION') + '\\iperf3\\' + log_folder_name
                cmd = f"{sut_tool('SUT_TOOLS_WINDOWS_VIRTUALIZATION')}\\iperf3\\iperf3.exe"
            else:
                remote_folder_path = sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION') + '/' + log_folder_name
                cmd = 'iperf3'

            logger.info(f'-----------kill all iperf3 server process on sut1-----------')
            if sut1.default_os == SUT_PLATFORM.WINDOWS:
                _, stdout, _ = sut1.execute_shell_cmd('tasklist /FI \"IMAGENAME eq iperf3.exe\"', 30)
                if 'iperf3.exe' in stdout:
                    sut1.execute_shell_cmd('taskkill /F /IM iperf3.exe', 30)
            else:
                _, stdout, _ = sut1.execute_shell_cmd(f'ps -e | grep iperf3', 30)
                if stdout != '':
                    sut1.execute_shell_cmd('kill -9 $(pidof iperf3)')

            # create new log folder for running iperf3 in sut
            exit_code, stdout, stderr = sut1.execute_shell_cmd(f'mkdir {remote_folder_path}')
            if exit_code == 1 and 'exist' in stderr:
                OperationSystem[sut1.default_os].remove_folder(sut1, remote_folder_path)
                sut1.execute_shell_cmd(f'mkdir {remote_folder_path}')
            exit_code, stdout, stderr = sut2.execute_shell_cmd(f'mkdir {remote_folder_path}')
            if exit_code == 1 and 'exist' in stderr:
                OperationSystem[sut2.default_os].remove_folder(sut2, remote_folder_path)
                sut2.execute_shell_cmd(f'mkdir {remote_folder_path}')

            logger.info(f'-----------start iperf3 server on sut1-----------')
            for i in range(MAX_PROCESS_NUM):
                port_no = DEFAULT_PORT_NO + i
                # --one-off flag mean iperf3 server will stop service after one client test
                if sut1.default_os == SUT_PLATFORM.WINDOWS:
                    log_file = f'{remote_folder_path}\\server_{port_no}.txt'
                else:
                    log_file = f'{remote_folder_path}/server_{port_no}.txt'
                sut1.execute_shell_cmd_async(f'{cmd} -s --one-off -p {port_no} > {log_file}')

            logger.info('-----------start iperf3 client on sut2-----------')
            for i in range(MAX_PROCESS_NUM):
                port_no = DEFAULT_PORT_NO + i
                if sut2.default_os == SUT_PLATFORM.WINDOWS:
                    log_file = f'{remote_folder_path}\\client_{port_no}.txt'
                else:
                    log_file = f'{remote_folder_path}/client_{port_no}.txt'
                sut2.execute_shell_cmd_async(f'{cmd} -c {port1.ip} -p {port_no} -t {duration} > {log_file}')

            # wait for iperf3 finish transfer
            if duration >= 60 * 5:
                sleep_time = duration + 90
            else:
                sleep_time = duration * 1.2
            logger.info(f'-----------sleep {sleep_time} sec to wait for iperf3 finish transfer-----------')
            time.sleep(sleep_time)

            # download log file to check result
            sut1.download_to_local(remote_folder_path, LOG_PATH)
            sut2.download_to_local(remote_folder_path, LOG_PATH)

            # calc sum of transfer and bandwith
            transfer = 0
            bandwidth = 0
            for root, dirs, files in os.walk(os.path.join(LOG_PATH, log_folder_name)):
                for file in files:
                    if file.startswith('client_') and file.endswith('.txt'):
                        log_file = os.path.join(root, file)
                        with open(log_file, 'r') as fs:
                            data = fs.read()
                            receiver_str = re.search(r'.*sec(.*/sec).*receiver', data).group(1)
                            receiver_data = re.split(r'\s+', receiver_str.strip())
                            transfer += float(receiver_data[0])
                            bandwidth += float(receiver_data[2])

            transfer_unit = receiver_data[1]
            bandwidth_unit = receiver_data[3]

            logger.debug(f'iperf total transfer = {transfer} {transfer_unit}')
            logger.debug(f'iperf total bandwidth = {bandwidth} {bandwidth_unit}')

            # convert data to unified unit
            transfer = self.__iperf3_data_conversion(transfer, transfer_unit[0], bandwidth_unit[0])

            logger.debug(f'check transfer > bandwidth / 8 * duration * 0.9 with unit {bandwidth_unit[0]}Bytes')

            if transfer > bandwidth / 8 * duration * 0.9:
                logger.info(
                    f'test iperf3 stress from {port1.nic.type.family} with {port1.ip} to {port2.nic.type.family} with {port2.ip} pass')
            else:
                raise RuntimeError(
                    f'test iperf3 stress from {port1.nic.type.family} with {port1.ip} to {port2.nic.type.family} with {port2.ip} fail')

    def __iperf3_data_conversion(self, number, old_unit, new_unit):
        UNIT = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y', 'B')

        old_unit_index = UNIT.index(old_unit.upper())
        new_unit_index = UNIT.index(new_unit.upper())

        return number * (1024 ** (old_unit_index - new_unit_index))

    def is_vm_autostart(self, vm_name):
        """
        Reference:
            None
        Purpose: to check if the VM is autostart with hypervisor
        Args:
            vm_name: the name of VM
        Returns:
            True: start with hypervisor
            False: not start with hypervisor
        Raises:
            RuntimeError: If any errors
        Example:
            To check if RHEL1 autostart with hypervisor
                is_auto = is_vm_autostart('RHEL1')
        """
        raise NotImplemented

    def is_vm_exist(self, vm_name):
        """
        Reference:
            None
        Purpose: to check if the VM is already existed
        Args:
            vm_name: the name of VM
        Returns:
            True: VM existed
            False: VM not existed
        Raises:
            RuntimeError: If any errors
        Example:
            To check if RHEL1 existed
                is_existed = is_vm_exist('RHEL1')
        """
        return vm_name in self.get_vm_list()

    def is_vm_running(self, vm_name):
        """
        Reference:
            None
        Purpose: to check if the VM is running, note that this function will return False if VM not existed
        Args:
            vm_name: the name of VM
        Returns:
            True: the VM is running
            False: the VM is not running
        Raises:
            RuntimeError: If any errors
        Example:
            To check if RHEL1 is running
                is_running = is_vm_running('RHEL1')
        """
        raise NotImplemented

    def ping_vm(self, vm_ip, times=2):
        """
        Reference:
            None
        Purpose: to Ping VM 2 times to check the connection, Note
        Args:
            vm_ip: the IP address of VM
        Returns:
            True: this IP can be ping succeed
            False: this IP cannot be ping succeed
        Raises:
            RuntimeError: If any errors
        Example:
            Ping '192.168.0.3' 2 times:
                res = ping_vm('192.168.0.3')
        """
        raise NotImplemented

    def reboot_vm(self, vm_name, timeout=600):
        """
        Reference:
            None
        Purpose: to reboot the VM
        Args:
            vm_name: the name of VM
            timeout: stop trying to reboot this VM after timeout
        Returns:
            None
        Raises:
            RuntimeError: If any errors
        Example:
            Reboot the VM 'RHEL1' in 120s
                reboot_vm('RHEL1', 120)
        """
        logger.info(f'reboot virtual machine {vm_name}')

        if not self.is_vm_running(vm_name):
            logger.error(f'reboot virtual machine failed: {vm_name} is not running')
            return

        cmd = self.CALLER_COMMAND_BASE
        cmd += '--command reboot_vm '
        cmd += f'--vm-name {vm_name} '
        cmd += f'--timeout {timeout} '

        rcode, _, std_err = self.sut.execute_shell_cmd(cmd, timeout=(timeout + 60))
        if rcode != 0:
            raise Exception(std_err)
        time.sleep(30)

    def restore_vm_snapshot(self, vm_name, snap_name):
        """
        Reference:
            None
        Purpose: to restore the snapshot to VM
        Args:
            vm_name: the name of VM
            snap_name: the name of snapshot
        Returns:
            None
        Raises:
            RuntimeError: If any errors
        Example:
            Restore the snapshot 's1' to 'RHEL1'
                restore_vm_snapshot('RHEL1', 's1')
        """
        raise NotImplemented

    def set_vm_autostart(self, vm_name):
        """
        Reference:
            None
        Purpose: to set the VM start with hypervisor
        Args:
            vm_name: the name of VM
        Returns:
            None
        Raises:
            RuntimeError: If any errors
        Example:
            Set 'RHEL1' start with hypervisor
                set_vm_autostart('RHEL1')
        """
        raise NotImplemented

    def set_vm_memory(self, vm_name, ram_mb):
        """
        Reference:
            None
        Purpose: to set the memory of VM
        Args:
            vm_name: the name of VM
            ram_mb: the new memory of VM
        Returns:
            None
        Raises:
            RuntimeError: If any errors
        Example:
            Set 'RHEL1' memory to 1024MB
                set_vm_memory('RHEL1', 1024)
        """
        raise NotImplemented

    def set_vm_unautostart(self, vm_name):
        """
        Reference:
            None
        Purpose:
        Args:
            vm_name: the name of VM
        Returns:
            None
        Raises:
            RuntimeError: If any errors
        Example:
            Set 'RHEL1' not start with hypervisor
                set_vm_unautostart('RHEL1')
        """
        raise NotImplemented

    def shutdown_vm(self, vm_name, timeout=60):
        """
        Reference:
            None
        Purpose: to shutdown the VM
        Args:
            vm_name: the name of VM
            timeout: Stop trying to shutdown this VM after timeout
        Returns:
            None
        Raises:
            RuntimeError: If any errors
        Example:
            Shutdown the VM 'RHEL1' in 60s
                shutdown_vm('RHEL1', 60)
        """
        # logger.info(f'shutdown the virtual machine {vm_name}')
        #
        # if not self.is_vm_running(vm_name):
        #     logger.error(f'shutdown virtual machine failed: {vm_name} is not running')
        #     return
        #
        # cmd = self.CALLER_COMMAND_BASE
        # cmd += '--command shutdown_vm '
        # cmd += f'--vm-name {vm_name} '
        # cmd += f'--timeout {timeout}'
        #
        # logger.info(f'shutdown {vm_name}')
        # rcode, _, std_err = self.sut.execute_shell_cmd(cmd, timeout=(timeout + 60))
        # if rcode != 0:
        #     raise Exception(std_err)
        # logger.info(f'shutdown {vm_name} succeed')
        raise NotImplemented

    def start_vm(self, vm_name, timeout=420):
        """
        Reference:
            None
        Purpose: to start the VM
        Args:
            vm_name: the name of VM
            timeout: stop trying start the VM after timeout
        Returns:
            None
        Raises:
            RuntimeError: If any errors
        Example:
            Start VM 'RHEL1' in 600s
                start_vm('RHEL1', 600)
        """
        logger.info(f'start the virtual machine {vm_name}')

        if self.is_vm_running(vm_name):
            logger.error(f'start virtual machine failed: {vm_name} is already started')
            return

        cmd = self.CALLER_COMMAND_BASE
        cmd += '--command start_vm '
        cmd += f'--vm-name {vm_name} '
        cmd += f'--timeout {timeout}'

        logger.info(f'starting {vm_name}...')
        clock_start = time.time()
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd=cmd, timeout=(timeout + 60))
        clock_end = time.time()
        if rcode != 0 and "could not initialize" in std_err:
            raise Exception(std_err)

        remain_time = timeout - (clock_end - clock_start)
        if self.__is_vm_os_linux(vm_name):
            while (remain_time > 0) and (not self.__check_is_vm_in_os_by_log(vm_name)):
                logger.info(f"Waitting for {vm_name} boot into os...")
                remain_time -= 10

        if remain_time <= 0:
            raise Exception(f"error: cannot start {vm_name} with timeout {timeout}s, try logger timeout please")

        logger.info(f'start {vm_name} succeed')

    def undefine_vm(self, vm_name, timeout=600):
        """
        Reference:
            None
        Purpose: to undefine a VM, and delete the disk file of VM
        Args:
            vm_name: the name of VM
            timeout: stop undefine VM and raise exception after timeout
        Returns:
            None
        Raises:
            RuntimeError: If any errors
        Examples:
            Undefine the VM 'RHEL1'
                undefine_vm('RHEL1')
        """
        raise NotImplemented

    def upload_to_vm(self, vm_name, src_path, dest_path):
        """
        Reference:
            None
        Purpose: to upload file to VM from SUT
        Args:
            vm_name: the name of VM
            src_path: the local file path in SUT, e.g. /root/Document/src/test.txt
            dest_path: the remote file path in virtual machine, e.g. /root/Document/dest/test.txt
        Returns:
            None
        Raises:
            RuntimeError: If any errors
        Example:
            Upload '/home/test.txt' in SUT 'RHEL1' to '/root/test.txt' in RHEL1
                upload_from_vm('RHEL1', '/home/test.txt', '/root/test.txt')
        """
        logger.info(f'upload file from <{self.sut.sut_name}>:{src_path} to <{vm_name}>:{dest_path}')

        if not self.is_vm_running(vm_name):
            raise Exception(f'download file from virtual machine failed: {vm_name} is not running')

        if not self.is_upload_src_path_exist(src_path):
            raise Exception(f'error: {src_path} do not exist on SUT, check it please')

        cmd = self.CALLER_COMMAND_BASE
        cmd += '--command upload_to_vm '
        cmd += f'--vm-name {vm_name} '
        cmd += f'--src-path {src_path} '
        cmd += f'--dest-path {dest_path} '
        cmd += '--ssh-port 22 '

        rcode, _, std_err = self.sut.execute_shell_cmd(cmd=cmd, timeout=600)
        if rcode == 13:
            raise Exception("error: this API is only used for file transport, not folder, check it please")
        if rcode != 0:
            raise Exception(std_err)

    def wait_for_vm_shutoff(self, vm_name, timeout):
        remain_time = timeout
        while remain_time > 0 and self.is_vm_running(vm_name):
            logger.info(f'waiting for {vm_name} shut off...')
            time.sleep(10)
            remain_time -= 10
        if remain_time <= 0:
            raise Exception(f'error: cannot shutdown {vm_name} in {timeout}s, try longer timeout please')
        time.sleep(30)

    def wait_and_expect(self, desc, timeout, function, *args):
        """
        call check function every one second repeatedly until check function return True
        raise exceptions when check function always return False after time out
        Args:
            desc: Step information description
            timeout: timeout in second
            function: func name
            args: args will be passed to function
        Raises:
            exceptions if error happened
        Returns:
            None
        """
        timeout = int(timeout * CMD_EXEC_WEIGHT)

        cnt = 0
        dur_time = 0
        start_time = time.time()
        logger.info('Wait [{}] for [{}] second'.format(desc, timeout))
        while dur_time < timeout:
            cnt += 1
            dur_time = time.time() - start_time
            try:
                if function(*args):
                    logger.info(">>> Wait and Expected [{}] pass {}/{}".format(desc, dur_time, timeout))
                    return
            except Exception:
                err_msg = traceback.format_exc()
                if "VMwareTools" in err_msg:
                    logger.debug("waitting for VMwareTools start...")
                else:
                    logger.debug(err_msg)
                    logger.debug('wait for next retry')
            if cnt % 30 == 0:
                logger.info('wait and expect {} time remain {}'.format(desc, timeout - dur_time))
            time.sleep(30)

        logger.debug('>>> Wait and expect Timeout [timeout={}]'.format(timeout))
        err = 'Failed at Wait and Expect [{}] timeout {}s'.format(desc, timeout)
        raise TimeoutError(err)


class KVM(Hypervisor):
    CALLER_COMMAND_BASE = f"python {sut_tool('VT_AUTO_POC_L')}/src/caller.py --os-type LINUX "

    def __init__(self, sut):
        super().__init__(sut)
        self.attached_device_list = {}

    def attach_disk_to_vm(self, vm_name, disk_path, disk_name):
        """
        Reference:
            None
        Purpose: to attach a virtual disk to VM, the virtual disk should be created before this action
        Args:
            vm_name: target VM
            disk_path: the virtual disk path
            disk_name: the virtual disk name in VM, e.g. 'vdb'
        Returns:
            None
        Raises:
            RuntimeError: If any errors
        Example:
            Attach the virtual disk file '/home/temp.qcow2' to 'RHEL1' as disk 'vdb'
                attach_disk_to_vm('RHEL1', '/home/temp.qcow2', 'vdb')
        """
        logger.info(f'<HOST> attach disk {disk_path} to {vm_name}')

        is_vm_running = self.is_vm_running(vm_name)
        if is_vm_running:
            self.shutdown_vm(vm_name)

        cmd = f'virsh attach-disk {vm_name} '
        cmd += f'--source {disk_path} --target {disk_name} --persistent '
        rcode, std_out, std_err = self.sut.execute_shell_cmd(cmd=cmd)
        if rcode != 0:
            raise Exception(std_err)

        if is_vm_running:
            self.start_vm(vm_name)

    def attach_nic_to_vm(self, vm_name, bus, slot, function):

        logger.info(f"attach NIC[{bus}:{slot}:{function}] to {vm_name}")

        is_vm_running = self.is_vm_running(vm_name)
        if is_vm_running:
            self.shutdown_vm(vm_name)

        xml_path = create_nic_xml_on_sut(self.sut, vm_name, bus, slot, function)
        cmd = f'virsh attach-device {vm_name} {xml_path} --config'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd)
        if rcode != 0:
            raise Exception(std_err)

        if is_vm_running:
            self.start_vm(vm_name)

        if vm_name not in self.attached_device_list:
            self.attached_device_list[vm_name] = [xml_path]
        else:
            self.attached_device_list[vm_name] += [xml_path]

    def create_vm_from_template(self, vm_name, template, ram_mb=4096,
                                disk_dir=sut_tool('VT_IMGS_L'),
                                vnic_type='virtio', timeout=600):
        """
        Reference:
            None
        Purpose: to create a new VM from template
        Args:
            vm_name: the name of new VM
            template: the path of template file
            ram_mb: the memory going to be assigned to VM, in MB
            disk_dir: the directory that the virtual disk file of new VM going to be placed
            vnic_type: the virtual NIC type, virtio or e1000
            timeout: it will raise exception after timeout
        Returns:
            None
        Raises:
            RuntimeError: If any errors
        Example:
            Create a new VM named 'RHEL-NEW' from template '/hoem/imgs/RHEL0.qcow2', assign 2048MB memory to it
            and put the virtual disk size to '/root/imgs'
                create_vm_from_template('RHEL-NEW', '/home/imgs/RHEL0.qcow2', 2048, '/root/imgs')
        """
        if self.is_vm_exist(vm_name):
            raise Exception(f'create virtual machine failed: {vm_name} already exist')

        logger.info('create new virtual machine from template')
        logger.info("=======================================================")
        logger.info(f"\tName: {vm_name}")
        logger.info(f"\tTemplate Path: {template}")
        logger.info(f"\tMemory: {ram_mb}MB")
        logger.info(f"\tDiks Storage directory: {disk_dir}")
        logger.info("=======================================================")

        self.copy_template_to_disk(vm_name, template, disk_dir)

        cmd = self.CALLER_COMMAND_BASE
        cmd += '--command create_vm_from_template '
        cmd += f'--new-vm-name {vm_name} '
        cmd += f'--template {template} '
        cmd += f'--memory {ram_mb} '
        cmd += f'--disk-dir {disk_dir} '
        cmd += f'--vnic-type {vnic_type} '
        cmd += f'--timeout {timeout}'

        rcode, _, std_err = self.sut.execute_shell_cmd(cmd=cmd, timeout=(timeout + 60))
        if rcode != 0:
            raise Exception(std_err)

        self.shutdown_vm(vm_name, timeout)
        logger.info(f"create {vm_name} from {template} succeed")

    def create_disk_file(self, disk_path, disk_size_gb):
        """
        Reference:
            None
        Purpose: to create a new virtual disk file
        Args:
            disk_path: the file path (contains name) of virtual disk
            disk_size_gb: the file size of virtual disk
        Returns:
            None
        Raises:
            RuntimeError: If any errors
        Example:
            Create a new virtual disk file at '/home' which name is 'temp.qcow2' and size is 10GB
                create_disk_file('/home/temp.qcow2', 10)
        """
        logger.info(f'create new disk file {disk_path} size={disk_size_gb}GB')

        cmd = f'qemu-img create -f qcow2 ' \
              f'-o size={disk_size_gb}G {disk_path}'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd=cmd)
        if rcode != 0:
            raise Exception(std_err)

    def create_vm_snapshot(self, vm_name, snap_name):
        logger.info(f'create new snapshot {snap_name} for {vm_name}')

        ts = time.localtime()
        snap_date = f'{ts.tm_year}/{ts.tm_mon}/{ts.tm_mday}'
        snap_time = f'{ts.tm_hour}:{ts.tm_min}:{ts.tm_sec}'
        cmd = f'virsh snapshot-create-as '
        cmd += f'--domain {vm_name} '
        cmd += f'--name {snap_name} '
        cmd += f'--description "{vm_name} snapshot at {snap_date} {snap_time}" '

        rcode, _, std_err = self.sut.execute_shell_cmd(cmd)
        if rcode != 0:
            raise Exception(std_err)

    def delete_vm_snapshot(self, vm_name, snap_name):
        logger.info(f'delete snapshot {snap_name} for {vm_name}')
        cmd = f'virsh snapshot-delete {vm_name} {snap_name}'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd)
        if rcode != 0:
            raise Exception(std_err)

    def detach_disk_from_vm(self, vm_name, disk_name):
        """
        Reference:
            None
        Purpose: to detach the virtual disk file from VM
        Args:
            vm_name: the name of new VM
            disk_name: the virtual disk name in VM going to be detached, e.g. 'vdb'
        Returns:
            None
        Raises:
            RuntimeError: If any errors
        Example:
            Detach virtual disk 'vdb' from 'RHEL1'
                detach_disk_from_vm('RHEL1', 'vdb')
        """
        logger.info(f'detach {disk_name} from {vm_name}')

        is_vm_running = self.is_vm_running(vm_name)
        if is_vm_running:
            self.shutdown_vm(vm_name)

        cmd = f'virsh detach-disk {vm_name} --target {disk_name} --persistent'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd)
        if rcode != 0:
            raise Exception(std_err)

        if is_vm_running:
            self.start_vm(vm_name)

    def detach_nic_from_vm(self, vm_name, bus, slot, function):
        logger.info(f'detach NIC[{bus}:{slot}:{function}] froms {vm_name}')

        xml_path = create_nic_xml_on_sut(self.sut, vm_name, bus, slot, function)
        if xml_path not in self.attached_device_list[vm_name]:
            raise Exception(f'error: cannot detach a device which was not attached to {vm_name}')

        is_vm_running = self.is_vm_running(vm_name)
        if is_vm_running:
            self.shutdown_vm(vm_name)

        cmd = f'virsh detach-device {vm_name} {xml_path} --config'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd)
        if rcode != 0:
            raise Exception(std_err)
        self.sut.execute_shell_cmd(f"rm -f {xml_path}")

        if is_vm_running:
            self.start_vm(vm_name)

    def get_vm_external_ip(self, vm_name):
        vm_cmd = "ifconfig | grep \"inet 10.\" | grep -v i\"10.0\""
        rcode, std_out, std_err = self.execute_vm_cmd(vm_name, vm_cmd)
        if rcode != 0:
            raise Exception(std_err)

        if std_out.strip() == "":
            raise Exception(f"error: cannot find external IP from {vm_name}")

        return std_out.strip().split()[1]

    def get_vm_disk_list(self, vm_name):
        logger.info(f'get the disk list of {vm_name}')

        is_vm_running = self.is_vm_running(vm_name)
        if is_vm_running:
            self.shutdown_vm(vm_name)

        cmd = f"virsh domblklist {vm_name} |sed -n '3,10p' | awk '{{print $1}}'"
        rcode, std_out, std_err = self.sut.execute_shell_cmd(cmd)
        if rcode != 0:
            raise Exception(std_err)

        return std_out.strip().split('\n')

    def get_vm_ip_list(self, vm_name):
        cmd = f"virsh domifaddr {vm_name} | sed -n '3,10p' | awk '{{print $4}}'"
        rcode, std_out, std_err = self.sut.execute_shell_cmd(cmd)
        if rcode != 0:
            raise Exception(std_err)

        ip_list = []
        ip_lines = std_out.strip().split('\n')
        for line in ip_lines:
            ip_list.append(line[:-3])

        return ip_list

    def get_vm_list(self):
        logger.info(f'get the virtual machine list')
        cmd = 'virsh list --all --name'
        rcode, std_out, std_err = self.sut.execute_shell_cmd(cmd)
        if rcode != 0:
            raise Exception(std_err)
        return std_out.strip().split('\n')

    def get_vm_memory(self, vm_name):
        logger.info(f'get {vm_name}\'s memory')
        memory_string = self.__get_vm_info(vm_name)[VM_INFO.MAX_MEMORY]
        return int(int(memory_string.split()[0]) / 1024)

    def get_vm_snapshot_list(self, vm_name):
        logger.info(f'get {vm_name}\'s snapshot status')

        cmd = f'virsh snapshot-list --domain {vm_name} --tree'
        rcode, std_out, std_err = self.sut.execute_shell_cmd(cmd)
        if rcode != 0:
            raise Exception(std_err)

        return std_out.strip().split('\n')

    def is_vm_autostart(self, vm_name):
        logger.info(f'check if {vm_name} start with Hypervisor')
        return self.__get_vm_info(vm_name)[VM_INFO.IS_AUTOSTART] == VM_INFO.ENABLE_AUTOSTART

    def is_vm_exist(self, vm_name):
        return super().is_vm_exist(vm_name)

    def is_vm_running(self, vm_name):
        cmd = f'virsh list --name | grep {vm_name}'
        _, std_out, std_err = self.sut.execute_shell_cmd(cmd)
        if std_err.strip() != '':
            raise Exception(std_err)
        return vm_name in std_out

    def ping_vm(self, vm_ip, times=2):
        cmd = f'ping -c {times} {vm_ip}'
        _, std_out, _ = self.sut.execute_shell_cmd(cmd)
        return '100% packet loss' not in std_out

    def restore_vm_snapshot(self, vm_name, snap_name):
        logger.info(f'restore snapshot {snap_name} to {vm_name}')

        cmd = f'virsh snapshot-revert --domain {vm_name} --snapshotname {snap_name}'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd)
        if rcode != 0:
            raise Exception(std_err)

    def restore_vm_state(self, vm_name, img_path):
        """
        Reference:
            None
        Purpose: to restore a VM from a save state file
        Args:
            vm_name: the name of VM
            img_path: the image file path which saved VM state
        Returns:
            None
        Raises:
            RuntimeError: If any errors
        Example:
            Restore the 'RHEL1' state from '/root/state0.qcow2'
                restore_vm_state('RHEL1', '/root/state0.qcow2')
        """
        logger.info(f'restore the state {img_path} to {vm_name}')
        cmd = f'virsh restore {img_path} --bypass-cache --running'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd)
        if rcode != 0:
            raise Exception(std_err)

    def resume_vm(self, vm_name):
        """
        Reference:
            None
        Purpose: to move a VM out of the suspended state
        Args:
            vm_name: the name of VM
        Returns:
            None
        Raises:
            RuntimeError: If any errors
        Example:
            Resume 'RHEL1'
                resume_vm('RHEL1')
        """
        logger.info(f'resume {vm_name}')
        cmd = f'virsh resume {vm_name}'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd)
        if rcode != 0:
            raise Exception(std_err)

    def save_vm_state(self, vm_name, img_path):
        """
        Reference:
            None
        Purpose: to save a running VM (RAM, but not disk state) to a state file so that it can be restored later
                 this API will make VM shutdown
        Args:
            vm_name: the name of VM
        Returns:
            None
        Raises:
            RuntimeError: If any errors
        Example:
            Save 'RHEL1' state to '/root/state0.qcow2'
                save_vm_state('RHEL1', '/root/state0.qcow2')
        """
        logger.info(f'save {vm_name} state to {img_path}')
        cmd = f'virsh save --bypass-cache {vm_name} {img_path} --running'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd)
        if rcode != 0:
            raise Exception(std_err)

    def set_vm_autostart(self, vm_name):
        logger.info(f'set {vm_name} start with KVM')

        cmd = f'virsh autostart {vm_name}'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd)
        if rcode != 0:
            raise Exception(std_err)

    def set_vm_memory(self, vm_name, ram_mb):
        logger.info(f'set {vm_name}\'s max memory to {ram_mb}MB')

        old_vm_state = self.is_vm_running(vm_name)
        if old_vm_state:
            self.shutdown_vm(vm_name)

        cmd = f'virsh setmaxmem {vm_name} {ram_mb * 1024} --config'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd)
        if rcode != 0:
            raise Exception(std_err)

        if old_vm_state:
            self.start_vm(vm_name)

    def set_vm_unautostart(self, vm_name):
        logger.info(f'set {vm_name} not start with Hypervisor')

        cmd = f'virsh autostart --disable {vm_name}'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd)
        if rcode != 0:
            raise Exception(std_err)

    def shutdown_vm(self, vm_name, timeout=120):
        logger.info(f'try to shutdown {vm_name}')

        cmd = f'virsh shutdown {vm_name}'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd)
        if rcode != 0:
            raise Exception(std_err)

        remain_time = timeout
        while remain_time > 0 and self.is_vm_running(vm_name):
            logger.info(f'waiting for {vm_name} shut off...')
            self.sut.execute_shell_cmd(cmd)
            time.sleep(30)
            remain_time -= 30
        if remain_time <= 0:
            raise Exception(f'error: cannot shutdown {vm_name} in {timeout}s, try longer timeout please')
        time.sleep(10)

        logger.info(f'shutdown {vm_name} succeed')

    def suspend_vm(self, vm_name):
        """
        Reference:
            None
        Purpose: to suspend a running VM
        Args:
            vm_name: the name of VM
        Returns:
            None
        Raises:
            RuntimeError: If any errors
        Example:
            Suspend 'RHEL1'
                suspend_vm('RHEL1')
        """
        logger.info(f'suspend {vm_name}')
        cmd = f'virsh suspend {vm_name}'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd)
        if rcode != 0:
            raise Exception(std_err)

    def undefine_vm(self, vm_name, timeout=600):
        logger.info(f'undefine {vm_name}')

        if self.is_vm_running(vm_name):
            self.shutdown_vm(vm_name)

        cmd = f'virsh undefine {vm_name} --remove-all-storage'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd, timeout)
        if rcode != 0:
            raise Exception(std_err)

    def __get_vm_info(self, vm_name):
        logger.info(f'get {vm_name} information dict')

        cmd = f'virsh dominfo {vm_name}'
        rcode, std_out, std_err = self.sut.execute_shell_cmd(cmd)
        if rcode != 0:
            raise Exception(std_err)

        info = {}
        lines = std_out.strip().split('\n')
        for line in lines:
            key, val = line.strip().split(':', 1)
            info[key] = val.strip()
        return info


def split_results(line_list):
    results = []
    item = []
    for line in line_list:
        if line != "":
            item.append(line)
        else:
            results.append('\n'.join(item))
            item = []
    results.append('\n'.join(item))
    return results


class HyperV(Hypervisor):
    CALLER_COMMAND_BASE = f"python {sut_tool('VT_AUTO_POC_W')}\\src\\caller.py --os-type WINDOWS "

    def attach_physical_disk_to_vm(self, vm_name, disk_id):
        """
        Reference:
            None
        Purpose: to attach a virtual disk to VM, the virtual disk should be created before this action
        Args:
            vm_name: target VM
            disk_id: the virtual disk id
            index: if there are more than 1 disk were found with keyword, which one will be attach to VM
        Returns:
            None
        Raises:
            RuntimeError: If any errors
        Example:
            Attach physical disk with Number=1 to 'RHEL1'
                attach_disk_to_vm('RHEL1', 1)
        """
        logger.info(f'<HOST> attach disk {disk_id} to {vm_name}')
        is_vm_running = False
        if self.is_vm_running(vm_name):
            is_vm_running = True
            self.shutdown_vm(vm_name)

        cmd = f'Set-Disk -Number {disk_id} -IsOffline $true; '
        self.sut.execute_shell_cmd(cmd, timeout=60, powershell=True)

        cmd = f"Get-Disk {disk_id} | Add-VMHardDiskDrive -VMName {vm_name}"
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd, timeout=60, powershell=True)
        if rcode != 0:
            raise Exception(std_err)

        if is_vm_running:
            self.start_vm(vm_name)

    def attach_nic_to_vm(self, vm_name, switch_name):
        """
        Reference:
            None
        Purpose: to attach a virtual NIC to VM
        Args:
            vm_name: target VM
            switch_name: the virtual switch name
        Returns:
            None
        Raises:
            RuntimeError: If any errors
        Example:
            Attach the virtual NIC to 'RHEL1' which virtual swich is 'Default'
                attach_nic_to_vm('RHEL1', 'Default')
        """
        logger.info(f'attach virtual network adapter to {vm_name}')
        cmd = f'Add-VMNetworkAdapter -Name {switch_name} -VMName {vm_name} -SwitchName {switch_name}'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd, powershell=True)
        if rcode != 0:
            raise Exception(std_err)

    def create_disk_file(self, disk_path, disk_size_gb):
        """
        Reference:
            None
        Purpose: to create a new virtual disk file
        Args:
            disk_path: the file path (contains name) of virtual disk
            disk_size_gb: the file size of virtual disk
        Returns:
            None
        Raises:
            RuntimeError: If any errors
        Example:
            Create a new virtual disk file at 'C:\imgs\' which name is 'temp.vhdx' and size is 10GB
                create_disk_file('C:\\imgs\\temp.vhdx', 10)
        """
        logger.info(f'create new disk file {disk_path} size={disk_size_gb}GB')

        cmd = f'New-VHD -Path {disk_path} -SizeBytes {disk_size_gb}GB'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd=cmd, powershell=True)
        if rcode != 0:
            raise Exception(std_err)

    def create_switch(self, switch_name, is_internal=False, interface_desc='', iov=False):
        """
        Reference:
            None
        Purpose: to create a new virtual switch, only available on Hyper-V
        Args:
            switch_name: new virtual switch name
            is_internal: virtual switch type, True means create a internal switch, False means external switch,
                         no private switch supported
            interface_desc: if a external switch going to be created, this parameter should be set,
                            you can get this information from powershell command 'GetNetAdapter -Name *'
            iov: enable IOV or not
        Returns:
            None
        Raises:
            RuntimeError: If any errors
        Example:
            Create a external switch 'DEFAULT' from host net adapter 'Intel(R) Ethernet Network Adapter X710-T2L'
                create_switch('DEFAULT', False, 'Intel(R) Ethernet Network Adapter X710-T2L')
            Create a internal switch 'DEFAULT'
                create_switch('DEFAULT')
        """
        if not is_internal and interface_desc == '':
            raise Exception(f'error: cannot create external virtual switch without host net adapter')

        if is_internal:
            info_msg = f'create new internal virtual switch [{switch_name}]'
        else:
            info_msg = f'create new external virtual switch [{switch_name}] '
            info_msg += f'from host net adapter {interface_desc}'
        logger.info(info_msg)

        cmd = f'New-VMSwitch -Name {switch_name} '
        cmd += f'-SwitchType Internal ' if is_internal else ''
        cmd += f'-NetAdapterInterfaceDescription "{interface_desc}" ' if not is_internal else ''
        cmd += f'-EnableIov ${iov} '

        rcode, _, std_err = self.sut.execute_shell_cmd(cmd, powershell=True)
        if rcode != 0:
            raise Exception(std_err)

    def create_vm_from_template(self, vm_name, template, ram_mb=2048, disk_dir=sut_tool('VT_IMGS_W'),
                                switch_name='ExternalSwitch', timeout=600):
        """
        Reference:
            None
        Purpose: to create a new VM from template
        Args:
            vm_name: the name of new VM
            template: the path of template file
            ram_mb: the memory going to be assigned to VM, in MB
            disk_dir: the directory that the virtual disk file of new VM going to be placed
            switch_name: the switch going to be attach to VM when create it
            timeout: it will raise exception after timeout
        Returns:
            None
        Raises:
            RuntimeError: If any errors
        Example:
            Create a new VM named 'RHEL-NEW' from template 'C:\\RHEL0.vhdx', assign 2048MB memory to it
            and put the virtual disk size to 'C:\\imgs'
                create_vm_from_template('RHEL-NEW', 'C:\\RHEL0.vhdx', 2048, 'C:\\imgs', 'Default Switch')
        """
        if self.is_vm_exist(vm_name):
            raise Exception(f'create virtual machine failed: {vm_name} already exist')

        logger.info('create new virtual machine from template')
        logger.info("=======================================================")
        logger.info(f"\tName: {vm_name}")
        logger.info(f"\tTemplate Path: {template}")
        logger.info(f"\tMemory: {ram_mb}MB")
        logger.info(f"\tDiks Storage directory: {disk_dir}")
        logger.info("=======================================================")

        self.copy_template_to_disk(vm_name, template, disk_dir)

        cmd = self.CALLER_COMMAND_BASE
        cmd += '--command create_vm_from_template '
        cmd += f'--new-vm-name {vm_name} '
        cmd += f'--template {template} '
        cmd += f'--memory {ram_mb} '
        cmd += f'--disk-dir {disk_dir} '
        cmd += f'--switch-name \"{switch_name}\" '
        cmd += f'--timeout {timeout}'

        rcode, _, std_err = self.sut.execute_shell_cmd(cmd=cmd, timeout=(timeout + 60))
        if rcode != 0:
            raise Exception(std_err)

    def create_vm_snapshot(self, vm_name, snap_name):
        logger.info(f'create snapshot {snap_name} from virtual machine {vm_name}')
        cmd = f'Checkpoint-VM -Name {vm_name} -SnapshotName {snap_name}'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd, powershell=True)
        if rcode != 0:
            raise Exception(std_err)

    def delete_vm_snapshot(self, vm_name, snap_name):
        logger.info(f'delete snapshot {snap_name} of virtual machine {vm_name}')
        cmd = f'Remove-VMCheckpoint -VMName {vm_name} -Name {snap_name}'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd, powershell=True)
        if rcode != 0:
            raise Exception(std_err)

    def delete_switch(self, switch_name):
        """
        Reference:
            None
        Purpose: to delete the virtual switch, only for Hyper-V
        Args:
            switch_name: the virtual switch going to be deleted
        Returns:
            None
        Raises:
            RuntimeError: If any errors
        Example:
            Delete the switch 'Default'
                delete_switch('Default')
        """
        logger.info(f'delete virtual switch [{switch_name}] from Hyper-V')
        cmd = f'Remove-VMSwitch "{switch_name}" -Force'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd, powershell=True)
        if rcode != 0:
            raise Exception(std_err)

    def detach_physical_disk_from_vm(self, vm_name, disk_id):
        """
        Reference:
            None
        Purpose: to detach the physical disk file from VM
        Args:
            vm_name: the name of new VM
            disk_id: the physical disk id
        Returns:
            None
        Raises:
            RuntimeError: If any errors
        Example:
            Detach physical disk which id is 1 from 'RHEL1'
                detach_disk_from_vm('RHEL1', 1)
        """
        logger.info(f'detach virtual disk {disk_id} from {vm_name}')

        is_vm_running = self.is_vm_running(vm_name)
        if is_vm_running:
            self.shutdown_vm(vm_name)

        ctl_num, ctl_loc = self.get_vm_disk_location_by_id(vm_name, disk_id)
        cmd = f"Remove-VMHardDiskDrive -VMName {vm_name} "
        cmd += f"-ControllerType SCSI -ControllerNumber {ctl_num} -ControllerLocation {ctl_loc}"
        rcode, std_out, std_err = self.sut.execute_shell_cmd(cmd, powershell=True)
        if rcode != 0:
            raise Exception(std_err)

        cmd = f"Set-Disk -Number {disk_id} -IsOffline $false"
        rcode, std_out, std_err = self.sut.execute_shell_cmd(cmd, powershell=True)
        if rcode != 0:
            raise Exception(std_err)

        if is_vm_running:
            self.start_vm(vm_name)

    def detach_nic_from_vm(self, vm_name, switch_name):
        """
        Reference:
            None
        Purpose: to detach a virtual NIC to VM
        Args:
            vm_name: target VM
            switch_name: the virtual switch name
        Returns:
            None
        Raises:
            RuntimeError: If any errors
        Example:
            Detach the virtual NIC to 'RHEL1' which virtual switch is 'Default'
                detach_nic_to_vm('RHEL1', 'Default')
        """
        logger.info(f'detach virtual network adapter from virtual machine')

        cmd = f"Get-VMNetworkAdapter -VMName {vm_name} | Select-Object -ExpandProperty SwitchName"
        rcode, std_out, std_err = self.sut.execute_shell_cmd(cmd, powershell=True)
        if rcode != 0:
            raise Exception(std_err)
        target_i = -1
        for i, name in enumerate(std_out.strip().splitlines()):
            if name.strip() == switch_name:
                target_i = i
                break
        if target_i == -1:
            raise Exception(f"error: cannot found network adapter which swtich is {switch_name} from {vm_name}")

        cmd = f'$nics=Get-VMNetworkAdapter -VMName {vm_name};$nics[{target_i}] | Remove-VMNetworkAdapter'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd, powershell=True)
        if rcode != 0:
            raise Exception(std_err)

    def __find_item_with_twice_search(self, first_cmd, keyword, second_cmd):
        _, out, _ = self.sut.execute_shell_cmd(first_cmd, powershell=True)
        line_list = out.strip().splitlines()
        results = split_results(line_list)
        target_i = -1
        for i in range(len(results)):
            if keyword in results[i]:
                target_i = i
                break
        if target_i == -1:
            raise Exception(f"error: cannot find {keyword} with command {first_cmd} which output is\n{out}")

        _, out, _ = self.sut.execute_shell_cmd(second_cmd, powershell=True)
        line_list = out.strip().splitlines()
        result = split_results(line_list)
        target_item = result[target_i]
        target_item_value = target_item.split(" : ")[1].strip()
        return target_item_value

    def get_disk_id_by_keyword(self, keyword):
        cmd = f"wmic diskdrive get /value"
        _, out, _ = self.sut.execute_shell_cmd(cmd, powershell=True)
        disk_infos = self.get_disk_info_blocks(out.strip())

        target_disk_id_list = []
        for disk in disk_infos:
            if keyword in disk["Model"]:
                if int(disk["Partitions"]) >= 3:
                    raise Exception(f"error: looks like the disk with keyword [{keyword}] is an OS HD because "
                                    f"it's partition more than 3, double-check it please")
                target_disk_id_list.append(int(disk["Index"]))
        return target_disk_id_list

    def get_disk_info_blocks(self, std_out):
        disk_infos = []
        out_lines = std_out.split("\n")
        if out_lines[1].strip() == "":
            out_lines = std_out.split("\n\n")
        i = 0
        while i < len(out_lines):
            if "Availability" in out_lines[i]:
                disk_info = {}
                while i < len(out_lines) and out_lines[i].strip() != "":
                    key, val = out_lines[i].strip().split("=")
                    disk_info[key] = val
                    i += 1

                disk_infos.append(disk_info)
            i += 1
        return disk_infos

    def get_vm_disk_location_by_id(self, vm_name, disk_id):
        # this API is to get the disk location of VM with the disk id on *SUT*
        cmd = f"Get-VMHardDiskDrive -VMName {vm_name} | select ControllerNumber, ControllerLocation, DiskNumber |"
        cmd += f"Where-Object {{$_.DiskNumber -match {disk_id}}}"
        _, std_out, _ = self.sut.execute_shell_cmd(cmd, powershell=True)
        out_lines = std_out.strip().splitlines()
        if len(out_lines) <= 2:
            raise Exception(f"error: cannot get disk location of {vm_name} with disk_id={disk_id}")
        disk_line = out_lines[2]
        return int(disk_line.split()[0]), int(disk_line.split()[1])

    def get_netadapter_by_keyword(self, keyword):
        cmd = 'Get-NetAdapter | select InterfaceDescription, Status '
        cmd += f'| findstr "{keyword}" '
        cmd += f'| findstr "Up"'
        _, std_out, _ = self.sut.execute_shell_cmd(cmd, powershell=True)
        interface_lines = std_out.splitlines()

        interfaces = []
        for lines in interface_lines:
            interfaces.append(" ".join(lines.split()[:-1]))
        return interfaces

    def get_vm_disk_list(self, vm_name):
        cmd = f'Get-VMHardDiskDrive -VMName {vm_name} | Select-Object -ExpandProperty Path'
        rcode, std_out, std_err = self.sut.execute_shell_cmd(cmd, powershell=True)
        if rcode != 0:
            raise Exception(std_err)

        return std_out.strip().split('\n')

    def get_vm_ip(self, vm_name, nic_keyword):
        """
        Reference:
            None
        Purpose: to get the VM ip with the keyword of NIC
        Args:
            vm_name: target VM
            nic_keyword: the keyword of NIC, if the keyword is not unique in the description of virtual switch,
                         you may get some error, for example:
                         'X710-T2l' is better than 'X710' because there is one description contains 'X710-T1L'
        Returns:
            the VM ip which bind to the virtual switch created with target NIC
        Raises:
            RuntimeError: If any errors
        Example:
            Get the 'rhel1' ip which use X710
                vm_ip = get_vm_ip('rhel1', 'X710')
        """
        first_cmd = f"Get-VMSwitch | fl -Property Name, NetAdapterInterfaceDescription"
        second_cmd = f"Get-VMSwitch | fl -Property Name"
        switch_name = self.__find_item_with_twice_search(first_cmd, nic_keyword, second_cmd)

        first_cmd = f"Get-VM -Name {vm_name} | Get-VMNetworkAdapter | fl -Property SwitchName, IPAddresses"
        second_cmd = f"Get-VM -Name {vm_name} | Get-VMNetworkAdapter | fl -Property IPAddresses"
        ip_mac_pair = self.__find_item_with_twice_search(first_cmd, switch_name, second_cmd)

        return ip_mac_pair[1:-1].split(",")[0]

    def get_vm_ip_list(self, vm_name):
        cmd = f'Get-VM -Name {vm_name} | Get-VMNetworkAdapter | Select IPAddresses | findstr :'
        rcode, std_out, std_err = self.sut.execute_shell_cmd(cmd, powershell=True)
        if rcode != 0:
            raise Exception(std_err)

        ip_list = []
        std_out = std_out[1:-1]
        ip_addr = std_out.split(',')[0]
        # TODO: ...

    def get_vm_list(self):
        return list(self.__get_vm_info_total())

    def get_vm_memory(self, vm_name):
        cmd = f'Get-VMMemory {vm_name} | findstr {vm_name}'
        rcode, std_out, std_err = self.sut.execute_shell_cmd(cmd, powershell=True)
        if rcode != 0:
            raise Exception(std_err)
        return int(std_out.strip().split()[3])

    def get_vm_snapshot_list(self, vm_name):
        cmd = f'Get-VMSnapshot -VMName {vm_name} | findstr rhel1'
        rcode, std_out, std_err = self.sut.execute_shell_cmd(cmd, powershell=True)
        if rcode != 0:
            raise Exception(std_err)

        if std_out.strip() == '':
            return []

        snap_list = []
        line_list = std_out.strip().split('\n')
        for line in line_list:
            snap_list.append(line.strip().split()[1])
        return snap_list

    def is_vm_autostart(self, vm_name):
        cmd = f'Get-VM  -VMName {vm_name} |  Select-Object  VMname,AutomaticStartAction | findstr {vm_name}'
        rcode, std_out, std_err = self.sut.execute_shell_cmd(cmd, powershell=True)
        if rcode != 0:
            raise Exception(std_err)
        return std_out.strip().split()[1] == 'Start'

    def is_vm_exist(self, vm_name):
        return vm_name in self.get_vm_list()

    def is_vm_running(self, vm_name):
        vm_info = self.__get_vm_info_total()[vm_name]
        return vm_info[1] == 'Running'

    def ping_vm(self, vm_ip, times=2):
        cmd = f'ping /n {times} {vm_ip}'
        _, std_out, _ = self.sut.execute_shell_cmd(cmd, powershell=True)
        return '0% loss' in std_out

    def restore_vm_snapshot(self, vm_name, snap_name):
        logger.info(f'restore snapshot {snap_name} to virtual machine {vm_name}')
        cmd = f'Restore-VMSnapshot -VMName {vm_name} -Name {snap_name} -Force'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd, powershell=True)
        if rcode != 0:
            raise Exception(std_err)

    def set_vm_autostart(self, vm_name):
        logger.info(f'set virtual machine {vm_name} start with Hypervisor')
        cmd = f'Get-VM -VMname {vm_name} | Set-VM -AutomaticStartAction Start'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd, powershell=True)
        if rcode != 0:
            raise Exception(std_err)

    def set_vm_memory(self, vm_name, ram_mb):
        logger.info(f'set the memory of {vm_name} to {ram_mb}MB')
        if not self.is_vm_running(vm_name):
            raise Exception('error: cannot modify the memory when VM is running')

        cmd = f'Set-VMMemory {vm_name} -StartupBytes {ram_mb}MB'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd, powershell=True)
        if rcode != 0:
            raise Exception(std_err)

    def set_vm_unautostart(self, vm_name):
        logger.info(f'set virtual machine {vm_name} not start with Hypervisor')
        cmd = f'Get-VM -VMname {vm_name} | Set-VM -AutomaticStartAction StartIfRunning'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd, powershell=True)
        if rcode != 0:
            raise Exception(std_err)

    def shutdown_vm(self, vm_name, timeout=120):
        logger.info(f'try to shutdown {vm_name}')

        cmd = f'Stop-VM -Name {vm_name}'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd, powershell=True, timeout=timeout)
        if rcode != 0:
            raise Exception(std_err)
        self.wait_for_vm_shutoff(vm_name, timeout)
        logger.info(f'shutdown {vm_name} succeed')

    def undefine_vm(self, vm_name, timeout=600):
        logger.info(f'undefine {vm_name}')
        cmd = f'Get-VM -VMName {vm_name} | Select-Object -Property VMId | Get-VHD'
        rcode, std_out, std_err = self.sut.execute_shell_cmd(cmd, powershell=True)
        disk_path_line = std_out.strip().split('\n')[1]
        disk_path = disk_path_line.split()[2]

        cmd = f'Remove-VM -Name {vm_name} -Force'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd, timeout, powershell=True)
        if rcode != 0:
            raise Exception(std_err)

        cmd = f'del {disk_path}'
        self.sut.execute_shell_cmd(cmd, powershell=True)

    def __get_vm_info_total(self):
        rcode, std_out, std_err = self.sut.execute_shell_cmd('Get-VM', powershell=True)
        if rcode != 0:
            raise Exception(std_err)

        line_list = std_out.strip().split('\n')[2:]
        vm_info = {}
        for line in line_list:
            items = line.split()
            name, state, cpu_usage, memory = items[:4]
            vm_info[name] = [name, state, int(cpu_usage), int(memory)]

        return vm_info


def get_datastore(path):
    path_items = path.split('/')
    for item in path_items:
        if 'datastore' in item:
            return item
    raise Exception(f"error: cannot find keyword 'datastore' in {path}")


def get_datastore_relative_path(path):
    path_items = path.split('/')
    target = -1
    for i in range(len(path_items)):
        if 'datastore' in path_items[i]:
            target = i
            break
    if target == -1:
        raise Exception(f"error: cannot find keyword 'datastore' in {path}")
    return "/".join(path_items[target + 1:]) if path_items[-1] != '' else "/".join(path_items[target + 1:-1])


def get_vm_credit(vm_os_type):
    if "lin" in vm_os_type.lower():
        user = "root"
        pwd = "password"
    elif "win" in vm_os_type.lower():
        user = "administrator"
        pwd = "intel@123"
    elif "vsp" in vm_os_type.lower():
        user = "root"
        pwd = "Intel@123"
    return vim.vm.guest.NamePasswordAuthentication(username=user, password=pwd)


def get_vm_obj(vm_name, service_instance):
    esxi_content = service_instance.RetrieveContent()

    vm = get_obj(esxi_content, [vim.VirtualMachine], vm_name)
    if not vm:
        raise Exception(f"error: cannot locate the virtual machine {vm_name}")

    tools_status = vm.guest.toolsStatus
    if tools_status in ('toolsNotInstalled', 'toolsNotRunning'):
        raise Exception(f"error: VMwareTools is needed for execute command in virtual machine")

    return vm


def is_default_cmd(cmd):
    cur_dir = os.path.dirname(__file__)
    with open(f"{cur_dir}\\tools\\bin_cmds.txt", "r") as file:
        content = file.read()
    cmd_list = content.splitlines()
    return cmd in cmd_list


def wait_for_execute_vm_finish(vm, creds, res, profile_manager, timeout):
    remain_time = timeout
    rcode = profile_manager.ListProcessesInGuest(vm, creds, [res]).pop().exitCode
    while remain_time > 0 and not str(rcode).isdigit():
        remain_time -= 1
        time.sleep(1)
        rcode = profile_manager.ListProcessesInGuest(vm, creds, [res]).pop().exitCode

    if remain_time <= 0:
        raise TimeoutError("error: execute command in virtual machine timeout")

    return rcode


class ESXi(Hypervisor):
    def __init__(self, sut) -> None:
        super().__init__(sut)
        self.CMD_CONNECT_TO_ESXI = f'Connect-VIServer -Server {self.sut.ssh_sutos._ip} ' + \
                                   f'-Protocol https -User {self.sut.ssh_sutos._user} ' + \
                                   f'-Password {self.sut.ssh_sutos._password} ' +\
                                   f'-Port {os_web_port}'

    def create_vm_from_template(self, vm_name, host_template, timeout=60*15):
        """
        Reference:
            None
        Purpose: to create a new VM from template
        Args:
            vm_name: the name of new VM
            host_template: the path of template file, you can copy template from:
                        \\ccr\ec\proj\DPG\PV\test_case_tool\virtualization\VMware\imgs\ and **unzip it**
                        C:\BKCPkg\domains\virtualization\imgs\rhel1\rhel1.ovf
            timeout: it will raise exception after timeout
        Returns:
            None
        Raises:
            RuntimeError: If any errors
        Example:
            Create a new VM named 'RHEL-NEW' from template 'rhel0' which is stored in datastore1, assign 2048MB memory,
            and put new vm image in datastore1
                create_vm_from_template('RHEL-NEW', '/vmfs/volumes/datastore1/rhel0', 2048)
        """
        if self.is_vm_exist(vm_name):
            raise Exception(f"error: {vm_name} already existed, unregister it before create")
        logger.info('create new virtual machine from template')
        logger.info("=======================================================")
        logger.info(f"\tName: {vm_name}")
        logger.info(f"\tHost Template Path: {host_template}")
        logger.info("=======================================================")
        timeout = int(timeout * CMD_EXEC_WEIGHT)
        cmd = "$vmHost = Get-VMHost -Name '{}';" \
              "Import-vApp -Name {} -Source '{}' -VMHost $vmHost".format(self.sut.ssh_sutos._ip,
                                                                         vm_name,
                                                                         host_template)
        logger.info(f"<{self.sut.cfg['defaults']['name']}> execute host command {cmd} in PowerCLI")
        host_cmd = f"{self.CMD_CONNECT_TO_ESXI}; {cmd}"
        return self.sut.execute_host_cmd(cmd=host_cmd, timeout=timeout, powershell=True)        #

    def __register_new_vm(self, vm_name, template, ram_mb):
        vmx_datastore = get_datastore(template)
        vmx_filepath = get_datastore_relative_path(template)

        cmd = f"rm -rf /vmfs/volumes/{vmx_datastore}/{vm_name}"
        self.sut.execute_shell_cmd(cmd)

        cmd = f"ls {template}"
        _, out, _ = self.sut.execute_shell_cmd(cmd)
        filenames = out.strip().split()
        template_vmdk_file = ''
        for name in filenames:
            if 'flat' not in name:
                template_vmdk_file = name

        cmd = f"New-VM "
        cmd += f"-Name {vm_name} "
        cmd += f"-DiskPath '[{vmx_datastore}] {vmx_filepath}/{template_vmdk_file}' "
        cmd += f"-MemoryMB {ram_mb} "
        cmd += f"-Datastore {vmx_datastore}"
        rcode, _, err = self.execute_host_cmd_esxi(cmd)
        if rcode != 0:
            raise Exception(err)

    def __set_controller(self, vm_name, vm_os_type):
        ctr_type = "ParaVirtual" if vm_os_type == "linux" else "VirtualLsiLogicSAS"
        cmd = f"Get-ScsiController -VM {vm_name} | Set-ScsiController -Type {ctr_type}"
        rcode, _, err = self.execute_host_cmd_esxi(cmd)
        if rcode != 0:
            raise Exception(err)

    def __set_guest_os_type(self, vm_name, template, vm_os_type):
        datastore = get_datastore(template)
        guest_os_type = "centos8-64" if vm_os_type == "linux" else "windows2019srvNext-64"
        vmx_file_path = f"/vmfs/volumes/{datastore}/{vm_name}/{vm_name}.vmx"
        cmd = f"sed -i 's/guestOS = \"winXPPro\"/guestOS = \"{guest_os_type}\"/g' {vmx_file_path}"
        rcode, _, err = self.sut.execute_shell_cmd(cmd)
        if rcode != 0:
            raise Exception(err)

    def __set_network_adapter(self, vm_name, vm_os_type):
        vm_adpather_type = "Vmxnet3" if vm_os_type == "linux" else "e1000e"
        cmd = f"Get-VM {vm_name} | Get-NetworkAdapter | Set-NetworkAdapter -Type {vm_adpather_type} -confirm:$false"
        rcode, _, err = self.execute_host_cmd_esxi(cmd)
        if rcode != 0:
            raise Exception(err)

    def __set_firmware(self, vm_name):
        cmd = f"$vm = Get-VM {vm_name}; "
        cmd += "$spec = New-Object VMware.Vim.VirtualMachineConfigSpec;"
        cmd += "$spec.Firmware = [VMware.Vim.GuestOsDescriptorFirmwareType]::efi;"
        cmd += "$vm.ExtensionData.ReconfigVM($spec)"
        rcode, _, err = self.execute_host_cmd_esxi(cmd)
        if rcode != 0:
            raise Exception(err)

    def __copy_image(self, vm_name, template, disk_dir):
        logger.info(f'copying from {template} to {disk_dir}...')

        template = template if list(template)[-1] != '/' else "".join(list(template)[:-1])
        disk_dir = disk_dir if list(disk_dir)[-1] != '/' else "".join(list(disk_dir)[:-1])

        # remove old directory
        cmd = f'rm -rf {disk_dir}/{vm_name}'
        self.sut.execute_shell_cmd(cmd)

        cmd = f'cp -r {template} {disk_dir}/{vm_name}'
        self.sut.execute_shell_cmd(cmd, 600)

    def __rename_copied_template_files(self, vm_name, disk_dir):
        virtualization_path = os.path.dirname(__file__)
        scripts_path = os.path.join(virtualization_path, "tools", "rename_copied_template_files.py")
        self.sut.upload_to_remote(scripts_path, "/vmfs/")

        cmd = f"python /vmfs/rename_copied_template_files.py --vm-name {vm_name} --disk-dir {disk_dir}/{vm_name}/"
        self.sut.execute_shell_cmd(cmd, 600)

    def download_from_vm(self, vm_name, host_path, vm_path):
        logger.info(f'download file from <{vm_name}>:{vm_path} to <{self.sut.cfg["defaults"]["name"]}>:{host_path}')

        service_instance = self.get_esxi_connection()
        vm = get_vm_obj(vm_name, service_instance)
        creds = get_vm_credit(self.get_vm_os_type(vm_name))
        fti = service_instance.RetrieveContent().guestOperationsManager.fileManager.InitiateFileTransferFromGuest(vm,
                                                                                                                  creds,
                                                                                                                  vm_path)
        fti.url = fti.url.replace("*", self.sut.ssh_sutos._ip)
        fti.url = fti.url.replace(":443", f":{os_web_port}")
        requests.packages.urllib3.disable_warnings()
        resp = requests.get(fti.url, verify=False)
        with open(host_path, 'wb') as f:
            f.write(resp.content)

    def is_enable(self):
        try:
            ret, stdout, stderr = self.execute_host_cmd_esxi('echo 1')
        except Exception:
            return False

        if ret == 0 and stderr is None:
            return True
        else:
            return False

    def execute_host_cmd_esxi(self, cmd, cwd=".", timeout=30):
        timeout = int(timeout * CMD_EXEC_WEIGHT)
        logger.info(f"<{self.sut.cfg['defaults']['name']}> execute host command {cmd} in PowerCLI")
        host_cmd = f"{self.CMD_CONNECT_TO_ESXI}; {cmd}"
        return self.sut.execute_host_cmd(cmd=host_cmd, cwd=cwd, timeout=timeout, powershell=True)

    def execute_vm_cmd(self, vm_name, vm_cmd, cwd=".", timeout=30, powershell=False):
        timeout = int(timeout * CMD_EXEC_WEIGHT)
        logger.info(f'<{vm_name}> execute cmd [cmd: {vm_cmd} timeout: {timeout}]')
        return self.__execute_vm_cmd(vm_name, vm_cmd, cwd, timeout, powershell, False)

    def execute_vm_cmd_async(self, vm_name, vm_cmd, cwd=".", timeout=30, powershell=False):
        timeout = int(timeout * CMD_EXEC_WEIGHT)
        logger.info(f'<{vm_name}> execute async cmd [cmd: {vm_cmd}]')
        return self.__execute_vm_cmd(vm_name, vm_cmd, cwd, timeout, powershell, True)

    def __execute_vm_cmd(self, vm_name, vm_cmd, cwd=".", timeout=30, powershell=False, is_async=False):
        service_instance = self.get_esxi_connection()
        vm = get_vm_obj(vm_name, service_instance)
        creds = get_vm_credit(self.get_vm_os_type(vm_name))

        profile_manager = service_instance.RetrieveContent().guestOperationsManager.processManager
        cmd, param = self.__get_program_and_param(vm_name, vm_cmd, cwd, is_async)
        program_spec = vim.vm.guest.ProcessManager.ProgramSpec(programPath=cmd, arguments=param)

        res = profile_manager.StartProgramInGuest(vm, creds, program_spec)
        if is_async:
            return None, None, None
        rcode = wait_for_execute_vm_finish(vm, creds, res, profile_manager, timeout)
        if vm_name == "Vsphere":
            return rcode, None, None

        std_out, std_err = self.__get_vm_cmd_log(vm_name)
        logger.info(f"<{vm_name}> execute cmd out: {std_out}")
        logger.info(f"<{vm_name}> execute cmd err: {std_err}")
        logger.info(f"<{vm_name}> execute cmd code: {rcode}")
        return rcode, std_out, std_err

    def __get_program_and_param(self, vm_name, vm_cmd, cwd, is_async=False):
        if "Vsphere" == vm_name:
            return "/bin/bash", "shell"

        vm_cmd = f"cd {cwd} && {vm_cmd}"
        if "lin" in self.get_vm_os_type(vm_name):
            vm_cmd = vm_cmd if not is_async else vm_cmd + " &"
            log_path = "/root/"
            cmd = "/bin/bash"
            param = f"-c \"{vm_cmd}\""
        elif "win" in self.get_vm_os_type(vm_name):
            vm_cmd = vm_cmd if not is_async else "start " + vm_cmd
            log_path = "C:\\"
            cmd = "C:\\Windows\\System32\\cmd.exe"
            param = f"/c \"{vm_cmd}\""

        param = f"{param} 1> {log_path}stdout.log 2> {log_path}stderr.log"
        return cmd, param

    def get_esxi_connection(self):
        os_cfg = self.sut.ssh_sutos
        try:
            service_instance = SmartConnect(host=os_cfg._ip, user=os_cfg._user, pwd=os_cfg._password,
                                            port=os_web_port, disableSslCertValidation=True)
            atexit.register(Disconnect, service_instance)
        except IOError as io_error:
            raise io_error

        if not service_instance:
            raise Exception("error: cannot connect to ESXi with supplied credentials, check sut.ini please")

        return service_instance

    def __get_vm_cmd_log(self, vm_name):
        log_path = "/root/" if "lin" in self.get_vm_os_type(vm_name) else "C:\\"
        self.download_from_vm(vm_name, host_path="C:\\BKCPkg\\stdout.log", vm_path=f"{log_path}stdout.log")
        self.download_from_vm(vm_name, host_path="C:\\BKCPkg\\stderr.log", vm_path=f"{log_path}stderr.log")
        with open("C:\\BKCPkg\\stdout.log", "r") as file:
            std_out = file.read()
        with open("C:\\BKCPkg\\stderr.log", "r") as file:
            std_err = file.read()
        return std_out, std_err

    def get_vm_id(self, vm_name):
        cmd = f'vim-cmd vmsvc/getallvms | awk \'' + '{' + 'print $1, $2}\''
        _, out, _ = self.sut.execute_shell_cmd(cmd)
        output_lines = out.strip().splitlines()[1:]
        for line in output_lines:
            id, name = line.strip().split()
            if name == vm_name:
                return id
        raise Exception(f"cannot find {vm_name}, check name please")

    def get_vm_list(self):
        logger.info(f'get the virtual machine list')

        cmd = 'vim-cmd vmsvc/getallvms | awk \'' + '{' + 'print $2}\''
        rcode, std_out, std_err = self.sut.execute_shell_cmd(cmd)
        if rcode != 0:
            raise Exception(std_err)

        return std_out.strip().splitlines()[1:]

    def get_vm_ip(self, vm_name):
        vm_id = self.get_vm_id(vm_name)
        cmd = f"vim-cmd vmsvc/get.summary {vm_id} | grep ipAddress | awk -F '[\\t\",]' '" + "{" + "print $2}'"
        for i in range(3):
            _, std_out, _ = self.sut.execute_shell_cmd(cmd)
            if std_out.strip() != "":
                break
            logger.info(f'[{vm_name}] wait 30 try again get')
            time.sleep(30)
        return std_out.strip()

    def get_vm_ip_list(self, vm_name):
        cmd = "ifconfig | grep inet | grep -v inet6"
        rcode, stdout, stderr = self.execute_vm_cmd(vm_name, cmd)
        if rcode != 0:
            raise Exception(stderr)
        outlines = stdout.strip().splitlines()

        iplist = []
        for line in outlines:
            ip = line.split()[1]
            if "10" == ip.split('.')[0]:
                iplist.append(ip)
        return iplist

    def get_vm_os_type(self, vm_name):
        if vm_name == "Vsphere":
            return "Vsphere"
        if "rhel" in vm_name:
            return "linux"
        if "cent" in vm_name:
            return "linux"
        if "win" in vm_name:
            return "windows"

        raise Exception(f"error: cannot recognize the OS type of {vm_name}")

    def is_vm_running(self, vm_name):
        vm_id = self.get_vm_id(vm_name)
        cmd = f'vim-cmd vmsvc/power.getstate {vm_id}'
        rcode, std_out, std_err = self.sut.execute_shell_cmd(cmd)
        if rcode != 0:
            raise Exception(std_err)
        return 'off' not in std_out

    def __modify_vmx_file_for_new_vm(self, vm_name, disk_dir):
        cmd = f"cat {disk_dir}/*.vmx | grep displayName"
        _, std_out, _ = self.sut.execute_shell_cmd(cmd)
        old_name = std_out.strip().split("\"")[-2]

        cmd = f"sed -i 's/displayName = \"{old_name}\"/displayName = \"{vm_name}\"/g' {disk_dir}/*.vmx > {disk_dir}/*.vmx"
        self.sut.execute_shell_cmd(cmd)

    def set_vm_memory(self, vm_name, ram_mb):
        logger.info(f'set {vm_name}\'s max memory to {ram_mb}')

        cmd = f'Get-VM ${vm_name} | Set-VM -MemoryMB {ram_mb} -Confirm:$false'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd, powershell=True)
        if rcode != 0:
            raise Exception(std_err)

    def start_vm(self, vm_name, timeout=600):
        logger.info(f'start the virtual machine {vm_name}')

        if self.is_vm_running(vm_name):
            logger.error(f'start virtual machine failed: {vm_name} is already started')
            return

        vm_id = self.get_vm_id(vm_name)
        cmd = f'vim-cmd vmsvc/power.on {vm_id}'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd=cmd, timeout=(timeout + 60))
        if rcode != 0:
            raise Exception(std_err)

        self.wait_and_expect(f'waiting form {vm_name} boot into OS...', timeout, self.execute_vm_cmd, vm_name, 'echo live')

    def shutdown_vm(self, vm_name, timeout=60):
        logger.info(f'shutdown the virtual machine {vm_name}')

        if not self.is_vm_running(vm_name):
            logger.error(f'shutdown virtual machine failed: {vm_name} is not running')
            return

        vm_id = self.get_vm_id(vm_name)
        cmd = f'vim-cmd vmsvc/power.off {vm_id}'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd, timeout=(timeout + 60))
        if rcode != 0:
            raise Exception(std_err)

    def suspend_vm(self, vm_name):
        logger.info(f'reboot virtual machine {vm_name}')

        if not self.is_vm_running(vm_name):
            logger.error(f'reboot virtual machine failed: {vm_name} is not running')
            return

        vm_id = self.get_vm_id(vm_name)
        cmd = f'vim-cmd vmsvc/power.suspend {vm_id}'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd)
        if rcode != 0:
            raise Exception(std_err)

    def reboot_vm(self, vm_name, timeout=600):
        logger.info(f'reboot virtual machine {vm_name}')

        if not self.is_vm_running(vm_name):
            raise Exception(f'reboot virtual machine failed: {vm_name} is not running')

        vm_id = self.get_vm_id(vm_name)
        cmd = f'vim-cmd vmsvc/power.reboot {vm_id}'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd, timeout=(timeout + 60))
        if rcode != 0:
            raise Exception(std_err)
        self.wait_and_expect(f'waiting form {vm_name} boot into OS...', timeout, self.execute_vm_cmd, vm_name, 'echo live')

    def resume_vm(self, vm_name):
        logger.info(f'reboot virtual machine {vm_name}')

        vm_id = self.get_vm_id(vm_name)
        cmd = f'vim-cmd vmsvc/power.suspendResume {vm_id}'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd)
        if rcode != 0:
            raise Exception(std_err)

    def undefine_vm(self, vm_name, timeout=600):
        logger.info(f'undefine {vm_name}')

        if self.is_vm_running(vm_name):
            self.shutdown_vm(vm_name)

        vm_id = self.get_vm_id(vm_name)
        cmd = f'vim-cmd vmsvc/unregister {vm_id}'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd)
        if rcode != 0:
            raise Exception(std_err)

    def upload_to_vm(self, vm_name, host_path, vm_path):
        logger.info(f'upload file from <{self.sut.cfg["defaults"]["name"]}>:{host_path} to <{vm_name}>:{vm_path}')

        service_instance = self.get_esxi_connection()
        vm = get_vm_obj(vm_name, service_instance)
        creds = get_vm_credit(self.get_vm_os_type(vm_name))

        with open(host_path, "rb") as file:
            data_to_send = file.read()

        file_attribute = vim.vm.guest.FileManager.FileAttributes()
        url = service_instance.RetrieveContent().guestOperationsManager.fileManager. \
            InitiateFileTransferToGuest(vm, creds, vm_path,
                                        file_attribute,
                                        len(data_to_send), True)
        url = re.sub(r"^https://\*:", "https://" + self.sut.ssh_sutos._ip + ":", url)
        url = url.replace(":443", f":{os_web_port}")
        resp = requests.put(url, data=data_to_send, verify=False)

        if resp.status_code != 200:
            raise Exception("error while uploading file")


def get_vmmanger(sut):
    vmmanger = {
        SUT_STATUS.S0.LINUX: KVM,
        SUT_STATUS.S0.WINDOWS: HyperV,
        SUT_STATUS.S0.VMWARE: ESXi,
    }
    return vmmanger[OS.get_os_family(sut.default_os)](sut)
