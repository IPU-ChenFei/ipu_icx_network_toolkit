import os.path
import re
import time
import requests
import atexit
from pyVmomi import vim
from pyVim.connect import SmartConnect, Disconnect
import os
from src.lib.toolkit.basic.config import os_web_port
from src.lib.toolkit.basic.const import CMD_EXEC_WEIGHT
from src.lib.toolkit.auto_api import *
from src.accelerator.lib.accelerator import *


class VIRTUAL_MACHINE_OS:
    RHEL = 'RHEL'
    CENTOS = 'CENTOS'
    WINDOWS = 'WINDOWS'


class VM_INFO:
    ID = 'Id'
    NAME = 'Name'
    UUID = 'UUID'
    OS_TYPE = 'OS Type'
    STATE = 'State'
    CPU_NUM = 'CPU(s)'
    MAX_MEMORY = 'Max memory'
    USED_MEMORY = 'Used memory'
    IS_PERSISTENT = 'Persistent'
    IS_AUTOSTART = 'Autostart'
    ENABLE_AUTOSTART = 'enable'
    DISABLE_AUTOSTART = 'disable'


TEMP_NIC_FILENAME = 'temp_nic.xml'
TEMP_PCI_FILENAME = 'temp_pci.xml'

############################### Virtual Machine Constants ##############################################################
NEW_IMG_PATH = "/var/lib/libvirt/images/qemu.qcow2"
KVM_RHEL_TEMPLATE = f"{sut_tool('VT_IMGS_L')}/rhel0.qcow2"
KVM_WINDOWS_TEMPLATE = f"{sut_tool('VT_IMGS_L')}/windows0.qcow2"
QEMU_CENT_TEMPLATE = f"{sut_tool('VT_IMGS_L')}/cent0.img"
HYPERV_RHEL_TEMPLATE = f"{sut_tool('VT_IMGS_W')}\\rhel0.vhdx"
HYPERV_WINDOWS_TEMPLATE = f"{sut_tool('VT_IMGS_W')}\\windows0.vhdx"
HYPERV_CENTOS_TEMPLATE = f"{sut_tool('VT_IMGS_W')}\\centos0.vhdx"
ESXI_CENTOS_TEMPLATE_PATH = sut_tool('ESXI_CENTOS_TEMPLATE_PATH_V')
ESXI_CENTOS_TEMPLATE_NAME = sut_tool('ESXI_CENTOS_TEMPLATE_NAME')
ESXI_RHEL_TEMPLATE = f"{ESXI_CENTOS_TEMPLATE_PATH}rhel_acce"
ESXI_CENTOS_TEMPLATE = f"{ESXI_CENTOS_TEMPLATE_PATH}{ESXI_CENTOS_TEMPLATE_NAME}"
ESXI_WINDOWS_TEMPLATE = f"{ESXI_CENTOS_TEMPLATE_PATH}windows_acce"

DEFAULT_MEMORY = 2048
DEFAULT_SWITCH_NAME = "ExternalSwitch"

VM_TEMPLATES = {
    SUT_STATUS.S0.LINUX: {
        VIRTUAL_MACHINE_OS.RHEL: KVM_RHEL_TEMPLATE,
        VIRTUAL_MACHINE_OS.WINDOWS: KVM_WINDOWS_TEMPLATE,
        VIRTUAL_MACHINE_OS.CENTOS: QEMU_CENT_TEMPLATE
    },
    SUT_STATUS.S0.WINDOWS: {
        VIRTUAL_MACHINE_OS.RHEL: HYPERV_RHEL_TEMPLATE,
        VIRTUAL_MACHINE_OS.WINDOWS: HYPERV_WINDOWS_TEMPLATE,
        VIRTUAL_MACHINE_OS.CENTOS: HYPERV_CENTOS_TEMPLATE
    },
    SUT_STATUS.S0.VMWARE: {
        VIRTUAL_MACHINE_OS.RHEL: ESXI_RHEL_TEMPLATE,
        VIRTUAL_MACHINE_OS.CENTOS: ESXI_CENTOS_TEMPLATE,
        VIRTUAL_MACHINE_OS.WINDOWS: ESXI_CENTOS_TEMPLATE
    }
}


############################### Precondition items #####################################################################
class VTPRE:
    VM_RHEL1 = {"type": "vm", "name": "rhel1"}
    VM_RHEL2 = {"type": "vm", "name": "rhel2"}
    VM_WINDOWS1 = {"type": "vm", "name": "windows1"}
    VM_WINDOWS2 = {"type": "vm", "name": "windows2"}
    VM_CENTOS1 = {"type": "vm", "name": "centos1"}
    VM_VSPHERE = {"type": "vm", "name": "Vsphere"}
    NIC_X710 = {"type": "dev", "name": "X710 NIC", "subtype": "nic", "keyword": "X710"}
    NIC_MLX = {"type": "dev", "name": "MLX NIC", "subtype": "nic", "keyword": "Mell"}
    USB = {"type": "dev", "name": "U-Disk", "subtype": "disk", }
    SSD = {"type": "dev", "name": "NVME SSD", "subtype": "disk", "keyword": "NVME"}


def search_for_obj(content, vim_type, name, folder=None, recurse=True):
    """
    Search the managed object for the name and type specified
    Sample Usage:
    get_obj(content, [vim.Datastore], "Datastore Name")
    """
    if folder is None:
        folder = content.rootFolder

    obj = None
    container = content.viewManager.CreateContainerView(folder, vim_type, recurse)

    for managed_object_ref in container.view:
        if managed_object_ref.name == name:
            obj = managed_object_ref
            break
    container.Destroy()
    return obj


def get_obj(content, vim_type, name, folder=None, recurse=True):
    """
    Retrieves the managed object for the name and type specified
    Throws an exception if of not found.
    Sample Usage:
    get_obj(content, [vim.Datastore], "Datastore Name")
    """
    obj = search_for_obj(content, vim_type, name, folder, recurse)
    if not obj:
        raise RuntimeError("Managed Object " + name + " not found.")
    return obj


class Hypervisor:
    CALLER_COMMAND_BASE = ''

    def __init__(self, sut):
        # type: (SUT) -> None
        self.sut = sut
        self.vm_list = {}
        self.acce = Accelerator(sut)

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

    def __check_is_vm_in_os_by_echo(self, vm_name):
        try:
            rcode, _, _ = self.__execute_vm_cmd(vm_name, "echo", timeout=10)
            return True
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

    def start_vm(self, vm_name, timeout=300):
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
        while (remain_time > 0) and (not self.__check_is_vm_in_os_by_echo(vm_name)):
            logger.info(f"Waitting for {vm_name} boot into os...")
            time.sleep(10)
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
            raise Exception(f'error: {src_path} do not exist, check it please')

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
    print(tools_status)
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
        self.vm_list = []
        self.CMD_CONNECT_TO_ESXI = f'Connect-VIServer -Server {self.sut.ssh_sutos._ip} ' + \
                                   f'-Protocol https -User {self.sut.ssh_sutos._user} ' + \
                                   f'-Password {self.sut.ssh_sutos._password} ' + \
                                   f'-Port {os_web_port}'

    def create_vm_from_template(self, vm_name, template, ram_mb=2048, vm_os_type="linux", timeout=6000):
        """
        Reference:
            None
        Purpose: to create a new VM from template
        Args:
            vm_name: the name of new VM
            template: the path of template file, you can copy template from:
                        \\ccr\ec\proj\DPG\PV\test_case_tool\virtualization\VMware\imgs\ and **unzip it**
            ram_mb: the memory going to be assigned to VM, in MB
            vm_os_type: the OS type of VM
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
            self.undefine_vm(vm_name)
            self.remove_vm_files(vm_name)

        logger.info('create new virtual machine from template')
        logger.info("=======================================================")
        logger.info(f"\tName: {vm_name}")
        logger.info(f"\tTemplate Path: {template}")
        logger.info(f"\tMemory: {ram_mb}MB")
        logger.info("=======================================================")

        linux_keyword = ['cent', 'lin', 'redhat', 'rhle']
        for keyword in linux_keyword:
            if keyword in vm_os_type.lower():
                vm_os_type = 'linux'
                break
        if 'win' in vm_os_type.lower():
            vm_os_type = 'windows'
        new_vm_template = self.__create_new_vm_img(template, vm_name)
        self.__register_new_vm(vm_name, new_vm_template, ram_mb)
        self.__set_controller(vm_name, vm_os_type)
        self.__set_firmware(vm_name)
        self.__set_guest_os_type(vm_name, new_vm_template, vm_os_type)

        self.start_vm(vm_name)
        self.shutdown_vm(vm_name)
        self.__set_network_adapter(vm_name, vm_os_type)
        self.vm_list.append(vm_name)

    def remove_vm_files(self, vm_name):
        self.sut.execute_shell_cmd(f'rm -rf {vm_name}', cwd=f"{ESXI_CENTOS_TEMPLATE_PATH}")

    def __create_new_vm_img(self, template, vm_name):
        # vmx_datastore = get_datastore(template)
        self.sut.execute_shell_cmd(f'rm -rf {template}_copy')
        self.sut.execute_shell_cmd(f'mkdir -p {template}_copy')
        new_vm_template = f'{template}_copy'
        self.sut.execute_shell_cmd(f'\cp {template}/* {new_vm_template}/', timeout=60 * 10)
        return new_vm_template

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
            if 'flat' not in name and '.vmdk' in name:
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
            service_instance = SmartConnectNoSSL(host=os_cfg._ip, user=os_cfg._user, pwd=os_cfg._password)
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

        self.wait_and_expect(f'waiting form {vm_name} boot into OS...', timeout, self.execute_vm_cmd, vm_name,
                             'echo live')

    def reset_vm(self, vm_name, timeout=600):
        logger.info(f'reboot virtual machine {vm_name}')

        if not self.is_vm_running(vm_name):
            raise Exception(f'reboot virtual machine failed: {vm_name} is not running')

        vm_id = self.get_vm_id(vm_name)
        cmd = f'vim-cmd vmsvc/power.reset {vm_id}'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd, timeout=(timeout + 60))
        if rcode != 0:
            raise Exception(std_err)
        time.sleep(30)
        self.wait_and_expect(f'waiting form {vm_name} boot into OS...', timeout, self.execute_vm_cmd, vm_name,
                             'echo live')


    def warm_reboot_vm(self, vm_name, timeout=600):
        logger.info(f'reboot virtual machine {vm_name}')
        try:
            self.execute_vm_cmd_async(vm_name, 'systemctl reboot')
        finally:
            time.sleep(30)
            self.wait_and_expect(f'waiting form {vm_name} boot into OS...', timeout, self.execute_vm_cmd, vm_name,
                                 'echo live')

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

    def suspend_vm(self, vm_name, timeout=600):
        logger.info(f'reboot virtual machine {vm_name}')

        if not self.is_vm_running(vm_name):
            logger.error(f'reboot virtual machine failed: {vm_name} is not running')
            return

        vm_id = self.get_vm_id(vm_name)
        cmd = f'vim-cmd vmsvc/power.suspend {vm_id}'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd)
        if rcode != 0:
            raise Exception(std_err)
        time.sleep(60)

    def reboot_vm(self, vm_name, timeout=600):
        logger.info(f'reboot virtual machine {vm_name}')

        if not self.is_vm_running(vm_name):
            raise Exception(f'reboot virtual machine failed: {vm_name} is not running')

        vm_id = self.get_vm_id(vm_name)
        cmd = f'vim-cmd vmsvc/power.reboot {vm_id}'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd, timeout=(timeout + 60))
        if rcode != 0:
            raise Exception(std_err)
        self.wait_and_expect(f'waiting form {vm_name} boot into OS...', timeout, self.execute_vm_cmd, vm_name,
                             'echo live')

    def resume_vm(self, vm_name, timeout=600):
        logger.info(f'reboot virtual machine {vm_name}')

        vm_id = self.get_vm_id(vm_name)
        cmd = f'vim-cmd vmsvc/power.on {vm_id}'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd, timeout=(timeout + 60))
        if rcode != 0:
            raise Exception(std_err)
        self.wait_and_expect(f'waiting form {vm_name} boot into OS...', timeout, self.execute_vm_cmd, vm_name,
                             'echo live')

    def undefine_vm(self, vm_name, timeout=600):
        logger.info(f'undefine {vm_name}')

        if self.is_vm_running(vm_name):
            self.shutdown_vm(vm_name)

        vm_id = self.get_vm_id(vm_name)
        cmd = f'vim-cmd vmsvc/unregister {vm_id}'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd)
        if rcode != 0:
            raise Exception(std_err)

    def upload_to_vm_from_host(self, vm_name, host_path, vm_path):
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

    def modify_vmx_attribute(self, vm_name, exp):
        att = exp.split('=')[0].strip(' ')
        val = exp.split('=')[1].strip('"').strip(' ').strip('"')
        _, out, _ = self.sut.execute_shell_cmd(
            f"cat {ESXI_CENTOS_TEMPLATE_PATH}{vm_name}/{vm_name}.vmx | grep -e '{att} =' -e '{att}='")
        if out == '':
            self.sut.execute_shell_cmd(
                f'cd {ESXI_CENTOS_TEMPLATE_PATH}{vm_name} && echo {att} = \\"{val}\\" >> {vm_name}.vmx')
        else:
            self.sut.execute_shell_cmd(
                f'cd {ESXI_CENTOS_TEMPLATE_PATH}{vm_name} && sed -i \'s/{att} =.*/{att} = \\"{val}\\"/g\' {vm_name}.vmx')

    def passthrough_conf(self, device, vm_name):
        if device == 'dsa':
            self.modify_vmx_attribute(vm_name, 'pciPassthru0.present = "TRUE"')
            self.modify_vmx_attribute(vm_name, 'pciPassthru0.virtualDev = "dvx"')
            self.modify_vmx_attribute(vm_name, 'pciPassthru0.dvx.deviceClass = "com.intel.dsa"')
            self.modify_vmx_attribute(vm_name, 'pciPassthru0.dvx.config.profile_id = "1"')

    def passthrough_memory_conf(self, memsize, vm_name):
        self.modify_vmx_attribute(vm_name, f'memSize = "{memsize}"')
        self.modify_vmx_attribute(vm_name, f'sched.mem.min = "{memsize}"')
        self.modify_vmx_attribute(vm_name, f'sched.mem.minSize = "{memsize}"')
        self.modify_vmx_attribute(vm_name, 'sched.mem.shares = "normal"')
        self.modify_vmx_attribute(vm_name, 'sched.mem.pin = "TRUE"')

    def get_pf_bus_id_list(self, ip):
        """
              Purpose: Get single QAT device id
              Args:
                  ip: Which device need to check the device status, eg: 'qat','dlb','dsa','iax'
              Returns:
                  Yes: device id list  --> ['0000:6d:00.0',...]
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Get single QAT device id
                        get_pf_dev_id('qat')
                        return --> ['0000:6d:00.0',...]
        """
        cpu_num = self.get_cpu_num()
        device_list = []
        if ip == 'qat':
            device_id = self.acce.qat_id
            device_num = self.acce.qat_device_num
        elif ip == 'dlb':
            device_id = self.acce.dlb_id
            device_num = self.acce.dlb_device_num
        elif ip == 'dsa':
            device_id = self.acce.dsa_id
            device_num = self.acce.dsa_device_num
        elif ip == 'iax':
            device_id = self.acce.iax_id
            device_num = self.acce.iax_device_num
        _, out, err = self.sut.execute_shell_cmd(f'lspci -p | grep {device_id}', timeout=60)
        line_list = out.strip().split('\n')
        for line in line_list:
            str_list = line.split(' ')
            word_list = str_list[0]
            device_list.append(word_list)
        if len(device_list) == cpu_num * device_num:
            return device_list
        else:
            logger.error('the number of  PF number is not right')
            raise Exception('the number of  PF number is not right')

    def get_vf_from_pf(self, ip, pf, vf_num):
        if ip == 'qat':
            vf_device_id = self.acce.qat_vf_id
        elif ip == 'dlb':
            vf_device_id = self.acce.dlb_vf_id
        _, out, err = self.sut.execute_shell_cmd(f'lspci -p | grep {vf_device_id}', timeout=60)
        line_list = out.split('\n')
        bus = pf.split(':')[1]
        num = 0
        vf_list = []
        for line in line_list:
            if bus in line:
                num += 1
                vf_device = line.split(' ')[0]
                vf_list.append(vf_device)
        if num == vf_num:
            return vf_list
        else:
            logger.error(f'Can not get all vf from device {pf}')
            raise Exception(f'Can not get all vf from device {pf}')

    # def get_vf_passthrough_id_from_pf(self, ip, pf, vf_num):
    #     if ip == 'qat':
    #         vf_device_id = self.acce.qat_vf_id
    #     elif ip == 'dlb':
    #         vf_device_id = self.acce.dlb_vf_id
    #     _, out, err = self.sut.execute_shell_cmd(f'lspci -p | grep {vf_device_id}', timeout=60)
    #     line_list = out.split('\n')
    #     bus = pf.split(':')[1]
    #     num = 0
    #     pcipassthough_id_list = []
    #     for line in line_list:
    #         if bus in line:
    #             num += 1
    #             key_word = line.split(' ')[-1]
    #             vf_bus = key_word.split('.')[1]
    #             key_word_1 = line.split(' ')[0]
    #             vf_devcie_function = key_word_1.split(':')[-1]
    #             pcipassthough_id = f'00000:{vf_bus}:{vf_devcie_function}'
    #             pcipassthough_id_list.append(pcipassthough_id)
    #     if num == vf_num and ip == 'qat':
    #         return pcipassthough_id_list
    #     elif num == vf_num and ip == 'dlb':
    #         pcipassthough_id_list[0], pcipassthough_id_list[2] = pcipassthough_id_list[2], pcipassthough_id_list[0]
    #         return pcipassthough_id_list
    #     else:
    #         logger.error(f'Can not get all vf from device {pf}')
    #         raise Exception(f'Can not get all vf from device {pf}')

    def get_all_vf_passthrough_id_from_multi_pf(self, ip, pf_list, vf_num):
        device_list_all = []
        for pf in pf_list:
            vf_list = self.get_vf_passthough_id_from_pf(ip, pf, vf_num)
            device_list_all.extend(vf_list)
        return device_list_all

    def get_cpu_num(self):
        """
              Purpose: Get current SUT CPU numbers
              Args:
                  No
              Returns:
                  Yes: return cpu numbers
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Get current SUT CPU numbers
                        get_cpu_num()
        """
        _, out, err = self.sut.execute_shell_cmd('esxcli hardware cpu global get |grep Packages', timeout=60)
        line_list = out.strip().split('\n')
        cpu_num = int(line_list[0][-1])
        return cpu_num

    def create_vf(self, ip, pf_num, vf_num):
        """
            Create VF form pf and return vf list
            Args:
                  ip: dlb or qat
                  pf_num: the order of pf 0,1,2,3...
                  vf_num: how many vf you want create on this pf

        """
        pf_id_list = self.get_pf_bus_id_list(ip)
        pf_bus_id = pf_id_list[pf_num]
        _, out, err = self.sut.execute_shell_cmd(f'esxcli hardware pci sriov maxvfs set -d {pf_bus_id} -v {vf_num} -a',
                                                 timeout=60)
        if err != '':
            logger.error(err)
            raise Exception(f"Create vf from device {pf_bus_id} failed")
        vf_id_list = self.get_vf_from_pf(ip, pf_bus_id, vf_num)
        if ip == 'dlb':
            vf_id_list[0], vf_id_list[2] = vf_id_list[2], vf_id_list[0]
        for vf in vf_id_list:
            self.enable_vf_passthrough(vf)
        return vf_id_list

    def enable_vf_passthrough(self, vf_id):
        _, out, err = self.sut.execute_shell_cmd(f'esxcli hardware pci pcipassthru set -d {vf_id} -e=true -a',
                                                 timeout=60)
        if err != '':
            logger.error(err)
            raise Exception(f"Enable through vf from device {vf_id} failed")

    def create_vf_from_multi_pf(self, pf_list, vf_num):
        for pf in pf_list:
            self.create_vf(pf, vf_num)

    def get_all_vfs_from_multi_pf(self, ip, pf_list, vf_num):
        device_list_all = []
        for pf in pf_list:
            vf_list = self.get_vf_from_pf(ip, pf, vf_num)
            device_list_all.extend(vf_list)
        return device_list_all

    def attach_mdev_to_guest(self, vm_name, ip_name, pci_num=0, profile_id=1):
        self.modify_vmx_attribute(vm_name, f'pciPassthru{pci_num}.present = \"TRUE\"')
        self.modify_vmx_attribute(vm_name, f'pciPassthru{pci_num}.virtualDev = \"dvx\"')
        self.modify_vmx_attribute(vm_name, f'pciPassthru{pci_num}.dvx.deviceClass = \"com.intel.{ip_name}\"')
        self.modify_vmx_attribute(vm_name, f'pciPassthru{pci_num}.dvx.config.profile_id = \"{profile_id}\"')

    def attach_vf_to_guest(self, vm_name, ip, vf, num=0):
        if ip == 'qat':
            device_id = self.acce.qat_vf_id
        elif ip == 'dlb':
            device_id = self.acce.dlb_vf_id
        else:
            raise Exception('ip should be qat or dlb')
        vf_bus = vf.split(':')[1]
        vf_bus_passthroug_id = int(f'0x{vf_bus}', 16)
        vf_devcie_function = vf.split(':')[-1]
        passthrough_id = f'00000:{vf_bus_passthroug_id}:{vf_devcie_function}'
        self.modify_vmx_attribute(vm_name, f'pciPassthru{num}.present = \"TRUE\"')
        self.modify_vmx_attribute(vm_name, f'pciPassthru{num}.id = \"{passthrough_id}\"')
        self.modify_vmx_attribute(vm_name, f'pciPassthru{num}.deviceId = \"0x{device_id}\"')
        self.modify_vmx_attribute(vm_name, f'pciPassthru{num}.vendorId = \"0x8086\"')
        self.modify_vmx_attribute(vm_name, f'pciPassthru{num}.systemId  = \"BYPASS\"')

    def attach_vf_list_to_guest(self, vm_name, ip, vf_list, num=0):
        for passthrough_id in vf_list:
            self.attach_vf_to_guest(vm_name, ip, passthrough_id, num)
            num += 1

    def attach_mdevs_to_guest(self, vm_name, ip_name, mdev_num):
        num = 0
        while num < mdev_num:
            self.attach_mdev_to_guest(vm_name, ip_name, num)
            num += 1

    def attach_vqat_to_guest(self, vm_name, vqat_function, pci_num=0):
        self.sut.execute_shell_cmd(
            f"cd {ESXI_CENTOS_TEMPLATE_PATH}{vm_name} && echo 'pciPassthru{pci_num}.present = \"TRUE\"' >> {vm_name}.vmx")
        self.sut.execute_shell_cmd(
            f"cd {ESXI_CENTOS_TEMPLATE_PATH}{vm_name} && echo 'pciPassthru{pci_num}.virtualDev = \"dvx\"' >> {vm_name}.vmx")
        self.sut.execute_shell_cmd(
            f"cd {ESXI_CENTOS_TEMPLATE_PATH}{vm_name} && echo 'pciPassthru{pci_num}.dvx.deviceClass = \"com.intel.{vqat_function}\"' >> {vm_name}.vmx")

    def attach_vqats_to_guest(self, vm_name, vqat_function, mdev_num):
        num = 0
        while num < mdev_num:
            self.attach_vqat_to_guest(vm_name, vqat_function, num)
            num += 1

    def add_environment_to_file_vm(self, vm_name, var_name, var_cmd):
        """
              Purpose: to check all keys in VM /root/.bashrc file, if not add environments variable to /root/.bashrc file
              Args:
                  qemu: Call VM Class RichHypervisor
                  vm_name: Run command on which VM
                  check_key: the name of environments variable
                  add_command: add environments variable to VM /root/.bashrc file
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Add key 'end' to /root/.bashrc file
                        add_environment_to_file(qemu, vm_name, 'end', 'end=$((SECONDS+110))')
        """
        _, out, err = self.execute_vm_cmd(vm_name, 'cat /root/.bashrc', timeout=60)
        if var_name not in out:
            self.execute_vm_cmd(vm_name, f"echo '{var_cmd}' >> /root/.bashrc", timeout=60)
            self.execute_vm_cmd(vm_name, 'source /root/.bashrc', timeout=60)

    def qat_dependency_install_vm(self, vm_name):
        """
              Purpose: To install rpm packages
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Install rpm packages
                      rpm_install_vm()
        """
        rpm_list = ['yasm', 'systemd-devel', 'boost-devel.x86_64', 'openssl-devel', 'libnl3-devel', 'gcc', 'gcc-c++',
                    'libgudev.x86_64', 'libgudev-devel.x86_64', 'systemd*']
        self.add_environment_to_file_vm(vm_name, 'http_proxy', 'export http_proxy="http://proxy-dmz.intel.com:911"')
        self.add_environment_to_file_vm(vm_name, 'HTTP_PROXY', 'export HTTP_PROXY="http://proxy-dmz.intel.com:911"')
        self.add_environment_to_file_vm(vm_name, 'https_proxy', 'export https_proxy="http://proxy-dmz.intel.com:912"')
        self.add_environment_to_file_vm(vm_name, 'HTTPS_PROXY', 'export HTTPS_PROXY="http://proxy-dmz.intel.com:912"')
        self.add_environment_to_file_vm(vm_name, 'no_proxy',
                                        'export no_proxy="120.0.0.1,localhost,intel.com"')
        # self.execute_vm_cmd(vm_name, 'yum groupinstall -y "Development Tools" --allowerasing', timeout=100 * 60)
        # self.execute_vm_cmd(vm_name, 'dnf update --nogpg --allowerasing -y', timeout=100 * 60)
        for rpm in rpm_list:
            self.execute_vm_cmd(vm_name, f'yum -y install {rpm}', timeout=60000)

    def __check_error(self, err):
        if err != '':
            logger.error(err)
            raise Exception(err)

    def check_keyword(self, key_list, out, err_msg):
        """
              Purpose: to check all keys in out file, if not return error messages
              Args:
                  key_list: All keys need to check
                  out: command execute out put file
                  err_msg: if there is one key doesn't in out file, return an error message
              Returns:
                  Yes
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: check all keys "dsa_list" in out file
                        _, out, err = self.sut.execute_shell_cmd('accel-config list -i', timeout=60)
                        dsa_list = ['dsa10', 'dsa12', 'dsa14', 'dsa2', 'dsa4', 'dsa6', 'dsa8']
                        err_msg = 'Issue - Not All DSA device recognized'
                        check_keyword(dsa_list, out, err_msg)
        """
        for key in key_list:
            if key not in out:
                logger.error(err_msg)
                raise Exception(err_msg)

    def qat_install_vm(self, vm_name, execute_command, enable_siov=False):
        """
              Purpose: To install QAT driver in VM
              Args:
                  vm_name: Run command on which VM
                  enable_sriov: If enable sriov host function in VM
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: install QAT driver in VM
                      qat_install_vm(vm_name, './configure --enable-icp-sriov=guest',False)
        """

        self.execute_vm_cmd(vm_name, f'mkdir -p {QAT_DRIVER_PATH_L}', timeout=60)
        self.execute_vm_cmd(vm_name, f'rm -rf {QAT_DRIVER_PATH_L}*', timeout=60)
        host_file_dir = f'{QAT_DRIVER_H}'
        vm_file_dir = f'{QAT_DRIVER_PATH_L}{QAT_DRIVER_NAME}'
        self.upload_to_vm_from_host(vm_name, host_file_dir, vm_file_dir)
        self.execute_vm_cmd(vm_name, f'unzip {QAT_DRIVER_NAME}', timeout=60, cwd=QAT_DRIVER_PATH_L)
        self.execute_vm_cmd(vm_name, 'tar -zxvf *.tar.gz', timeout=60, cwd=QAT_DRIVER_PATH_L)
        self.execute_vm_cmd(vm_name, execute_command, timeout=5 * 60, cwd=QAT_DRIVER_PATH_L)
        _, out, err = self.execute_vm_cmd(vm_name, 'make install', timeout=5 * 60, cwd=QAT_DRIVER_PATH_L)
        _, out, err = self.execute_vm_cmd(vm_name, 'make samples-install', timeout=5 * 60, cwd=QAT_DRIVER_PATH_L)
        _, out, err = self.execute_vm_cmd(vm_name, 'lsmod | grep qat', timeout=60)
        self.__check_error(err)
        if enable_siov:
            key_list = ['intel_qat']
            self.check_keyword(key_list, out, 'Issue - QAT driver install failed')
        else:
            key_list = ['intel_qat']
            self.check_keyword(key_list, out, 'Issue - QAT driver install failed')

    def define_vm(self, vm_name):
        _, out, err = self.sut.execute_shell_cmd(
            f'vim-cmd solo/registervm {ESXI_CENTOS_TEMPLATE_PATH}{vm_name}/{vm_name}.vmx')
        self.__check_error(err)

    def kernel_header_devel_vm(self, vm_name):
        """
              Purpose: Install kernel-header and kernel-devel package in VM
              Args:
                  qemu: Call VM Class RichHypervisor
                  vm_name: Run command on which VM
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Install kernel-header and kernel-devel package in VM
                      kernel_header_devel_vm(qemu, vm_name)
        """
        self.execute_vm_cmd(vm_name, f'mkdir -p {KERNEL_HEADER_PATH_L}', timeout=60)
        self.execute_vm_cmd(vm_name, f'rm -rf {KERNEL_HEADER_PATH_L}*', timeout=60)
        host_file_dir1 = f'{KERNEL_DEVEL_H}'
        vm_file_dir1 = f'{KERNEL_DEVEL_PATH_L}{KERNEL_DEVEL_NAME}'
        self.upload_to_vm_from_host(vm_name, host_file_dir1, vm_file_dir1)
        self.execute_vm_cmd(vm_name, 'rpm -ivh *.rpm --force --nodeps', timeout=5 * 60, cwd=KERNEL_DEVEL_PATH_L)

    def kernel_header_internal_devel(self, vm_name):
        self.execute_vm_cmd(vm_name, f'mkdir -p {KERNEL_INTERNAL_PATH_L}', timeout=60)
        self.execute_vm_cmd(vm_name, f'rm -rf {KERNEL_INTERNAL_PATH_L}*', timeout=60)
        host_file_dir1 = f'{KERNEL_INTERNAL_H}'
        vm_file_dir = f'{KERNEL_INTERNAL_PATH_L}{KERNEL_INTERNAL_NAME}'
        self.sut.upload_to_remote(localpath=KERNEL_INTERNAL_H, remotepath=KERNEL_INTERNAL_PATH_L)
        self.upload_to_vm_from_host(vm_name, host_file_dir1, vm_file_dir)
        self.execute_vm_cmd(vm_name, 'rpm -ivh *.rpm --force --nodeps', timeout=10 * 60,
                                          cwd=KERNEL_INTERNAL_PATH_L)

    def dlb_install_vm(self, vm_name):
        """
              Purpose: To install DLB driver in VM
              Args:
                  qemu: Call VM Class RichHypervisor
                  vm_name: Run command on which VM
                  ch_makefile: if need to modify DLB make file
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Modify Makefile and install DLB driver
                      dlb_install(qemu, vm_name, True)
        """
        self.execute_vm_cmd(vm_name, f'mkdir -p {DLB_DRIVER_PATH_L}', timeout=60)
        self.execute_vm_cmd(vm_name, f'rm -rf {DLB_DRIVER_PATH_L}*', timeout=60)
        host_file_dir = f'{DLB_DRIVER_H}'
        vm_file_dir = f'{DLB_DRIVER_PATH_L}{DLB_DRIVER_NAME}'
        self.upload_to_vm_from_host(vm_name, host_file_dir, vm_file_dir)
        self.execute_vm_cmd(vm_name, f'unzip -o {DLB_DRIVER_NAME}', timeout=60, cwd=DLB_DRIVER_PATH_L)
        # if ch_makefile:
        #     qemu.execute_vm_cmd(vm_name, "sed -i 's/ccflags-y += -DCONFIG_INTEL_DLB2_SIOV/#  iccflags-y += -DCONFIG_INTEL_DLB2_SIOV/g' /home/BKCPkg/domains/accelerator/dlb/driver/dlb2/Makefile", timeout=60)
        _, out, err = self.execute_vm_cmd(vm_name, 'make', timeout=60, cwd=f'{DLB_DRIVER_PATH_L}dlb/driver/dlb2/')
        # self.__check_error(err)
        self.execute_vm_cmd(vm_name, 'rmmod dlb2', timeout=60, cwd=f'{DLB_DRIVER_PATH_L}dlb/driver/dlb2/')
        self.execute_vm_cmd(vm_name, 'insmod ./dlb2.ko', timeout=60, cwd=f'{DLB_DRIVER_PATH_L}dlb/driver/dlb2/')
        _, out, err = self.execute_vm_cmd(vm_name, 'lsmod | grep dlb2', timeout=60)
        self.check_keyword(['dlb2'], out, 'Issue - dlb driver install fail')
        self.execute_vm_cmd(vm_name, 'make', timeout=60, cwd=f'{DLB_DRIVER_PATH_L}dlb/libdlb/')
        self.__check_error(err)
        self.add_environment_to_file_vm(vm_name, 'LD_LIBRARY_PATH',
                                        'export LD_LIBRARY_PATH=/home/BKCPkg/domains/accelerator/dlb/dlb/libdlb')

    def wq_configuration_dmatest(self,vm_name, ip_name='dsa',config = True):
        _, out, _ = self.execute_vm_cmd(vm_name, 'dmesg -C')
        if ip_name == 'dsa':
            if config:
                ret_code,out,err = self.execute_vm_cmd(vm_name, f'sudo accel-config config-wq dsa0/wq0.0 --type kernel -n dmaengine')
                if ret_code != 0:
                    raise Exception(err)
                ret_code,out,err = self.execute_vm_cmd(vm_name, f'sudo accel-config enable-wq dsa0/wq0.0')
                if ret_code != 0:
                    raise Exception(err)
            ret_code,out,err = self.execute_vm_cmd(vm_name, 'modprobe dmatest')
            if ret_code != 0:
                raise Exception(err)
            ret_code,out,err = self.execute_vm_cmd(vm_name, 'echo 1000 > /sys/module/dmatest/parameters/iterations')
            if ret_code != 0:
                raise Exception(err)
            ret_code,out,err = self.execute_vm_cmd(vm_name, 'echo "" > /sys/module/dmatest/parameters/channel')
            if ret_code != 0:
                raise Exception(err)
            ret_code,out,err = self.execute_vm_cmd(vm_name, 'echo 1 > /sys/module/dmatest/parameters/run')
            if ret_code != 0:
                raise Exception(err)

        elif (ip_name == 'iaa') or (ip_name == 'iax'):
            if config:
                ret_code,out,err = self.execute_vm_cmd(vm_name, f'sudo accel-config config-wq {ip_name}0/wq0.0 --type kernel')
                if ret_code != 0:
                    raise Exception(err)
                ret_code,out,err = self.execute_vm_cmd(vm_name, f'sudo accel-config config-wq {ip_name}0/wq0.0 -n dmaengine')
                if ret_code != 0:
                    raise Exception(err)
                ret_code,out,err = self.execute_vm_cmd(vm_name, f'sudo accel-config config-wq {ip_name}0/wq0.0 -d dmaengine')
                if ret_code != 0:
                    raise Exception(err)

                ret_code, out, err = self.execute_vm_cmd(vm_name, f'sudo accel-config enable-wq {ip_name}0/wq0.0')
                if ret_code != 0:
                    raise Exception(err)
            ret_code,out,err = self.execute_vm_cmd(vm_name, 'modprobe dmatest')
            if ret_code != 0:
                raise Exception(err)
            ret_code,out,err = self.execute_vm_cmd(vm_name, 'echo 1 > /sys/module/dmatest/parameters/noverify')
            if ret_code != 0:
                raise Exception(err)
            ret_code,out,err = self.execute_vm_cmd(vm_name, 'echo 10 > /sys/module/dmatest/parameters/iterations')
            if ret_code != 0:
                raise Exception(err)
            ret_code,out,err = self.execute_vm_cmd(vm_name, 'echo "" > /sys/module/dmatest/parameters/channel')
            if ret_code != 0:
                raise Exception(err)
            ret_code,out,err = self.execute_vm_cmd(vm_name, 'echo 1 > /sys/module/dmatest/parameters/run')
            if ret_code != 0:
                raise Exception(err)
        else:
            raise Exception('ip should be iax,iaa or dsa')
        time.sleep(60)
        _, out, _ = self.execute_vm_cmd(vm_name, 'dmesg')
        if ('error' in out) or ('Error' in out) or ('ERROR' in out):
            raise Exception('dmesg shows error')
        return


    def clone_new_vm(self, vm_name, template_path=ESXI_CENTOS_TEMPLATE, vm_os_type="linux"):
        if self.is_vm_exist(vm_name):
            self.undefine_vm(vm_name)
            self.remove_vm_files(vm_name)

        logger.info('create new virtual machine from template')
        logger.info("=======================================================")
        logger.info(f"\tName: {vm_name}")
        logger.info(f"\tTemplate Path: {template_path}")
        # logger.info(f"\tMemory: {ram_mb}MB")
        logger.info("=======================================================")

        linux_keyword = ['cent', 'lin', 'redhat', 'rhle']
        for keyword in linux_keyword:
            if keyword in vm_os_type.lower():
                vm_os_type = 'linux'
                break
        if 'win' in vm_os_type.lower():
            vm_os_type = 'windows'
        self.create_new_vm_from_exsit(vm_name, template_path)
        # self.__set_controller(vm_name, vm_os_type)
        # self.__set_firmware(vm_name)
        # self.__set_guest_os_type(vm_name, new_vm_template, vm_os_type)
        # self.start_vm(vm_name)
        # self.shutdown_vm(vm_name)
        # self.__set_network_adapter(vm_name, vm_os_type)
        self.vm_list.append(vm_name)


    def create_new_vm_from_exsit(self, vm_name, template_path):
        vmx_datastore = get_datastore(template_path)
        template_guest_name = self.get_template_name(template_path)
        new_vm_path = f'/vmfs/volumes/{vmx_datastore}/{vm_name}'
        self.sut.execute_shell_cmd(f'rm -rf {new_vm_path}')
        self.sut.execute_shell_cmd(f'mkdir -p {new_vm_path}')
        self.sut.execute_shell_cmd(f'\cp -f {template_path}/{template_guest_name}.vmx {new_vm_path}/{vm_name}.vmx',
                                   timeout=60 * 10)
        self.sut.execute_shell_cmd(f'\cp -f {template_path}/{template_guest_name}.nvram {new_vm_path}/{vm_name}.nvram',
                                   timeout=60 * 10)
        self.sut.execute_shell_cmd(f'\cp -f {template_path}/{template_guest_name}.vmsd {new_vm_path}/{vm_name}.vmsd',
                                   timeout=60 * 10)
        self.sut.execute_shell_cmd(f'\cp -f {template_path}/{template_guest_name}.nvram {new_vm_path}/{vm_name}.nvram',
                                   timeout=60 * 10)
        self.sut.execute_shell_cmd(
            f'\cp -f {template_path}/{template_guest_name}-flat.vmdk {new_vm_path}/{vm_name}-flat.vmdk',
            timeout=60 * 10)
        self.sut.execute_shell_cmd(f'\cp -f {template_path}/{template_guest_name}.vmdk {new_vm_path}/{vm_name}.vmdk',
                                   timeout=60 * 10)
        cmd = f'sed -i \'/sched.swap.derivedName/d\' {new_vm_path}/{vm_name}.vmx'
        self.sut.execute_shell_cmd(cmd, timeout=60)
        cmd = f'sed -i \'/uuid.location/d\' {new_vm_path}{vm_name}.vmx'
        self.sut.execute_shell_cmd(cmd, timeout=60)
        cmd = f'sed -i \'/uuid.bios/d\' {new_vm_path}/{vm_name}.vmx'
        self.sut.execute_shell_cmd(cmd, timeout=60)
        cmd = f'sed -i \'/extendedConfigFile/d\' {new_vm_path}/{vm_name}.vmx'
        self.sut.execute_shell_cmd(cmd, timeout=60)
        cmd = f'sed -i \'s/{template_guest_name}/{vm_name}/g\' {new_vm_path}/{vm_name}.vmx'
        self.sut.execute_shell_cmd(cmd, timeout=60)
        cmd = f'sed -i \'s/{template_guest_name}/{vm_name}/g\' {new_vm_path}/{vm_name}.vmdk'
        self.sut.execute_shell_cmd(cmd, timeout=60)
        cmd = f'vim-cmd solo/registervm  {new_vm_path}/{vm_name}.vmx'
        self.sut.execute_shell_cmd(cmd, timeout=60)


    def get_template_name(self, template_path):
            path_items = template_path.split('/')
            template_name = path_items[-1]
            return template_name


    def config_dlb_vdev(self, vdev_num):
        cpu_num = self.get_cpu_num()
        device_num = self.acce.dlb_device_num
        dlb_device_num = cpu_num * device_num
        cmd = 'esxcli system module parameters set -m dlb -a -p provision_scale_factor='
        num = 0
        while num < dlb_device_num:
            cmd = cmd + f'{vdev_num}'
            if num < dlb_device_num - 1:
                cmd = cmd + ','
            num += 1
        _, out, err = self.sut.execute_shell_cmd(cmd, timeout=60)
        self.__check_error(err)
        _, out, err = self.sut.execute_shell_cmd('esxcfg-module -u dlb', timeout=60)
        self.__check_error(err)
        _, out, err = self.sut.execute_shell_cmd('kill -HUP $(cat /var/run/vmware/vmkdevmgr.pid)', timeout=60)
        self.__check_error(err)



class ESXi_Rich(ESXi):
    def __init__(self, sut) -> None:
        super().__init__(sut)
        self.vm_list_rich = []

    def clone_new_vm_rich(self,vm_num,template=f'{ESXI_CENTOS_TEMPLATE}'):
        logger.info(f'clone {vm_num} virtual machine from {template}')
        for i in range(vm_num):
            vm_name = f'centos_acce{i}'
            self.vm_list_rich.append(vm_name)
        try:
            for vm_name in self.vm_list_rich:
                self.clone_new_vm(vm_name, template)
        except Exception as e:
            logger.error(e.args[0])
            raise e
        return self.vm_list_rich


    def create_rich_vm(self,vm_num,template=f'{ESXI_CENTOS_TEMPLATE}', ram_mb=2048, vm_os_type="linux"):
        logger.info(f'create {vm_num} virtual machine from {template}')
        for i in range(vm_num):
            vm_name = f'centos_acce{i}'
            self.vm_list_rich.append(vm_name)
        try:
            for vm_name in self.vm_list_rich:
                self.create_vm_from_template(vm_name, template, ram_mb, vm_os_type,timeout=6000)
        except Exception as e:
            logger.error(e.args[0])
            raise e
        return self.vm_list_rich

    def rich_vm_operation(self,func,vm_list=[]):
        if vm_list == []:
            vm_list = self.vm_list_rich
        logger.info(f'perform func in all virtual machine')
        if len(vm_list)==0:
            raise Exception('no vm to perform func ')
        for vm_name in vm_list:
            func(vm_name, True)

        logger.info(f'perform func in all virtual machine successfully')
        return

    def undefine_rich_vm(self,vm_list=[]):
        if vm_list == []:
            vm_list = self.vm_list_rich
        logger.info(f'undefine all virtual machine')
        if len(vm_list)==0:
            raise Exception('no vm to undefine')
        for vm_name in vm_list:
            self.undefine_vm(vm_name, True)
        logger.info(f'undefine all virtual machine successfully')
        return

    def define_rich_vm(self,vm_list=[]):
        if vm_list == []:
            vm_list = self.vm_list_rich
        logger.info(f'define all virtual machine')
        if len(vm_list)==0:
            raise Exception('no vm to define')
        for vm_name in vm_list:
            self.define_vm(vm_name)
            time.sleep(30)

    def start_rich_vm(self,vm_list=[]):
        if vm_list == []:
            vm_list = self.vm_list_rich
        logger.info(f'start all virtual machine')
        if len(vm_list)==0:
            raise Exception('no vm to start')
        for vm_name in vm_list:
            self.start_vm(vm_name)
            time.sleep(30)

    def qat_dependency_install_rich_vm(self,vm_list=[]):
        if vm_list == []:
            vm_list = self.vm_list_rich
        logger.info(f'qat dependency install in all virtual machine')
        if len(vm_list)==0:
            raise Exception('no vm to install qat dependency')
        for vm_name in vm_list:
            self.qat_dependency_install_vm(vm_name)

    def qat_install_rich_vm(self, cmd, enable_siov=False, vm_list=[]):
        if vm_list == []:
            vm_list = self.vm_list_rich
        logger.info(f'qat install in all virtual machine')
        if len(vm_list) == 0:
            raise Exception('no vm to install qat')
        for vm_name in vm_list:
            self.qat_install_vm(vm_name, cmd, enable_siov)

    def __execute_vm_cmd_thread(self, exec_res, vm_name, cmd, timeout, cwd):
        rcode, std_out, std_err = self.execute_vm_cmd(vm_name, cmd, cwd,timeout)
        exec_res[vm_name] = [rcode, std_out, std_err]

    def execute_rich_vm_cmd_parallel(self, cmd, vm_list=[], timeout=60, cwd='/root', start_index=None, end_index=None):
        if vm_list == []:
            vm_list = self.vm_list_rich
        start_index = 0 if not start_index else start_index
        end_index = len(vm_list) if not end_index else end_index + 1
        logger.info(f'execute command [{cmd}] in virtual machine {start_index} to {end_index - 1}')

        # if vm_list == []:
        #     vm_list = self.vm_list_rich
        th_list = []
        exec_res = {}
        logger.info(f'The virtual machine going to execute `{cmd}`: {vm_list}')

        for i in range(len(vm_list)):
            th = Thread(target=self.__execute_vm_cmd_thread, args=[exec_res, vm_list[i], cmd, timeout, cwd])
            th_list.append(th)
            th.start()
            time.sleep(2)
        for th in th_list:
            th.join(timeout=timeout)

        return exec_res

    def create_multi_device_vf(self, ip, ip_device_num, vf_num_per_pf):
        num = 0
        vf_list_list = []
        while num < ip_device_num:
            vf_id_list = self.create_vf(ip, num, vf_num_per_pf)
            vf_list_list.append(vf_id_list)
            num += 1

        return vf_list_list

    def attach_vfs_rich_vm(self, ip, vf_list_list, vm_list=[], num=0):
        if vm_list == []:
            vm_list = self.vm_list_rich
        if len(vm_list) != len(vf_list_list):
            raise Exception('no enough vm or vf for test')
        i = 0
        for vm_name in vm_list:
            self.attach_vf_list_to_guest(vm_name, ip, vf_list_list[i], num)
            i += 1

    def attach_mdev_rich_vm(self, ip_name, mdev_num_per_vm,  pci_passthroug_num=0, profile_id=1, vm_list=[]):
        if vm_list == []:
            vm_list = self.vm_list_rich
        for vm_name in vm_list:
            i = 0
            while i < mdev_num_per_vm:
                self.attach_mdev_to_guest(vm_name, ip_name, pci_passthroug_num+i, profile_id)
                i += 1

    def enable_siov_support(self):
        future_list = ('DVX', 'DCF', 'HWvFuture')
        i = 0
        for future in future_list:
            cmd = f'feature-state-util -s "{future}"'
            _, out, _ = self.sut.execute_shell_cmd(cmd)
            if 'enabled' not in out:
                self.sut.execute_shell_cmd(f'feature-state-util -e "{future}')
                i +=1
        cmd = "esxcli system settings kernel list | grep iovPasidMode | awk '{print $4}'"
        _, out, _ = self.sut.execute_shell_cmd(cmd)
        if 'Ture' not in out:
            cmd = "esxcli system settings kernel set --setting=iovPasidMode --value=TRUE"
            self.sut.execute_shell_cmd(cmd)
            i += 1
        if i != 0:
            self.acce.my_os.warm_reset_cycle_step(self.sut)

    def dlb_instll_rich_vm(self, vm_list=[]):
        if vm_list == []:
            vm_list = self.vm_list_rich
        logger.info(f'dlb install in all virtual machine')
        if len(vm_list) == 0:
            raise Exception('no vm to install dlb')
        for vm_name in vm_list:
            self.kernel_header_devel_vm(vm_name)
            self.dlb_install_vm(vm_name)

    def check_device_in_rich_vm(self, esxi, ip, device_num, mdev=False, vm_list=[]):
        if vm_list == []:
            vm_list = self.vm_list_rich
        for vm_name in vm_list:
            self.acce.check_device_in_vm(esxi, vm_name, ip, device_num, mdev)

    def passthrough_memory_conf_rich_vm(self, memsize, vm_list=[]):
        if vm_list == []:
            vm_list = self.vm_list_rich
        for vm_name in vm_list:
            self.passthrough_memory_conf(memsize, vm_name)