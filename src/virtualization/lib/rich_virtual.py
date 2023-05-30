import time
from threading import Thread
# from src.virtualization.lib.const import sut_tool
from src.virtualization.lib.virtualization import logger


class QemuVM:
    def __init__(self, vm_name, disk_path, add_by_host=True, is_sriov=True, is_uuid=False, bios='/home/OVMF.fd'):
        self.vm_name = vm_name
        self.disk_path = disk_path
        self.ssh_port = 2222
        self.add_by_host = add_by_host
        self.is_sriov = is_sriov
        self.bios = bios
        self.dev_list = []
        self.is_uuid = is_uuid

    def os_kernel(self, sut):
        _, out, err = sut.execute_shell_cmd('uname -r')
        line_list = out.strip().split('-')
        if line_list[0] <= '5.12.0':
            qemu_cmd = 'qemu-system-x86_64'
        else:
            qemu_cmd = '/usr/libexec/qemu-kvm'
        return qemu_cmd


    # def start(self, sut, ssh_port):
    #     if self.is_sriov:
    #         cmd = f'qemu-system-x86_64 -name {self.vm_name} -machine q35 -accel kvm '
    #         cmd += '-m 10240 -cpu host '
    #         cmd += f'-drive format=raw,file={self.disk_path} -bios {self.bios} '
    #         cmd += '-smp 4 -monitor pty -net nic,model=virtio '
    #         cmd += f'-nic user,hostfwd=tcp::{ssh_port}-:22 -nographic '
    #     else:
    #         cmd = f'qemu-system-x86_64 -name {self.vm_name} -machine q35 '
    #         cmd += f'-enable-kvm -global kvm-apic.vapic=false -m 10240 -cpu host '
    #         cmd += f'-drive format=raw,file={self.disk_path} -bios {self.bios} '
    #         cmd += '-device intel-iommu,caching-mode=on,dma-drain=on,x-scalable-mode=""modern"",'
    #         cmd += 'device-iotlb=on,aw-bits=48 -smp 16 -serial mon:stdio '
    #         cmd += f'-net nic,model=virtio -nic user,hostfwd=tcp::{ssh_port}-:22 '
    #         cmd += '-nographic '
    #     cmd += self.__get_attach_dev_cmd(sut)
    #     rcode, _, std_err = sut.execute_shell_cmd_async(cmd, timeout=6000)
    #     if rcode != 0:
    #         raise Exception(std_err)


    def start(self, sut, ssh_port):
        qemu_cmd = self.os_kernel(sut)
        if self.is_sriov:
            cmd = f'{qemu_cmd} -name {self.vm_name} -machine q35 -accel kvm '
            cmd += '-m 10240 -cpu host '
            cmd += f'-drive format=raw,file={self.disk_path} -bios {self.bios} '
            cmd += '-smp 4 -monitor pty -net nic,model=virtio '
            cmd += f'-nic user,hostfwd=tcp::{ssh_port}-:22 -nographic '
        else:
            cmd = f'{qemu_cmd} -name {self.vm_name} -machine q35 '
            cmd += f'-enable-kvm -global kvm-apic.vapic=false -m 10240 -cpu host '
            cmd += f'-drive format=raw,file={self.disk_path} -bios {self.bios} '
            cmd += '-device intel-iommu,caching-mode=on,dma-drain=on,x-scalable-mode=""modern"",'
            cmd += 'device-iotlb=on,aw-bits=48 -smp 16 -serial mon:stdio '
            cmd += f'-net nic,model=virtio -nic user,hostfwd=tcp::{ssh_port}-:22 '
            cmd += '-nographic '
        if self.is_uuid:
            cmd += self.__get_attach_uuid_cmd(sut)
        else:
            cmd += self.__get_attach_dev_cmd(sut)
        rcode, _, std_err = sut.execute_shell_cmd_async(cmd, timeout=6000)
        if rcode != 0:
            raise Exception(std_err)

    def __get_attach_dev_cmd(self, sut):
        if not self.dev_list:
            return ''

        cmd = ''
        if self.is_sriov:
            for dev in self.dev_list:
                cmd += f'-device vfio-pci,host={dev} '
        else:
            for dev in self.dev_list:
                cmd += f'-device vfio-pci,host={dev} ' if self.add_by_host else self.__get_dev_path(sut, dev)

        return cmd

    def __get_dev_path(self, sut, dev):
        dev_parts = dev.split(':')
        func_id = dev_parts[-1].split('.')
        dev_parts.pop(-1)
        dev_parts += func_id

        dev_dir = f'/sys/devices/pci0000:{dev_parts[-3]}/{dev}'
        std_out = sut.execute_shell_cmd(f'ls {dev_dir} | grep -')[1]
        dev_path = f'{dev_dir}/{std_out.strip()}'

        return f'-device vfio-pci,sysfsdev={dev_path} '

    def __get_attach_uuid_cmd(self, sut):
        if not self.dev_list:
            return ''
        cmd = ''
        for dev in self.dev_list:
            cmd += f'-device vfio-pci,sysfsdev=/sys/bus/mdev/devices/{dev} '

        return cmd

    def execute_cmd(self, sut, vm_cmd, timeout, cwd='/root', is_async=False):
        vm_cmd = f'cd {cwd} && {vm_cmd}'
        cmd = f'python /home/BKCPkg/domains/virtualization/auto-poc/src/caller.py --os-type LINUX '
        cmd += '--command execute_vm_cmd '
        cmd += f'--vm-name {self.vm_name} '
        cmd += f'--timeout {timeout} '
        cmd += f'--vm-command "{vm_cmd}" '
        cmd += f'--ssh-port {self.ssh_port} '
        if is_async:
            rcode, std_out, std_err = sut.execute_shell_cmd_async(cmd, timeout=(timeout+60))
        else:
            rcode, std_out, std_err = sut.execute_shell_cmd(cmd, timeout=(timeout+60))
        out_line_list = std_out.strip().split('\n')
        std_out = '\n'.join(out_line_list[1:])
        return rcode, std_out, std_err

    def attach_device(self, dev_list):
        self.dev_list += dev_list

    def clear_device(self):
        self.dev_list = []

    def get_from_sut(self, sut, sut_path, vm_path):
        cmd = f'python /home/BKCPkg/domains/virtualization/auto-poc/src/caller.py --os-type LINUX '
        cmd += '--command upload_to_vm '
        cmd += f'--vm-name {self.vm_name} '
        cmd += f'--src-path {sut_path} '
        cmd += f'--dest-path {vm_path} '
        cmd += f'--ssh-port {self.ssh_port}'

        rcode, _, std_err = sut.execute_shell_cmd(cmd, timeout=6000)
        if rcode != 0:
            raise Exception(std_err)

    def put_to_sut(self, sut, sut_path, vm_path):
        cmd = f'python /home/BKCPkg/domains/virtualization/auto-poc/src/caller.py --os-type LINUX '
        cmd += '--command download_from_vm '
        cmd += f'--vm-name {self.vm_name} '
        cmd += f'--src-path {vm_path} '
        cmd += f'--dest-path {sut_path} '
        cmd += f'--ssh-port {self.ssh_port}'

        rcode, _, std_err = sut.execute_shell_cmd(cmd, timeout=6000)
        if rcode != 0:
            raise Exception(std_err)


class QemuHypervisor:
    def __init__(self, sut):
        self.sut = sut
        self.vm_list = {}

    def attach_acce_dev_to_vm(self, vm_name, dev_list):
        self.vm_list[vm_name].attach_device(dev_list)

    def create_vm_from_template(self, vm_name, template, add_by_host=True, is_sriov=True, is_uuid=False, disk_dir='/home', bios='/home/OVMF.fd'):
        logger.info(f'create new virtual machine {vm_name}')

        disk_path = f'{disk_dir}/{vm_name}.qcow2'
        self.sut.execute_shell_cmd(f'cp {template} {disk_path}', timeout=600)

        vm = QemuVM(vm_name, disk_path, add_by_host, is_sriov, is_uuid, bios=bios)
        self.vm_list[vm_name] = vm

    def create_exist_vm(self, vm_name):
        logger.info(f'create an exsit virtual machine {vm_name}')
        vm = QemuVM(vm_name, '')
        vm.ssh_port = 2222
        self.vm_list[vm_name] = vm

    def create_vm_debug(self, vm_name, add_by_host=True, is_sriov=True, disk_dir='/home', bios='/home/OVMF.fd'):
        logger.info(f'Debug: create new virtual machine {vm_name}')
        disk_path = f'{disk_dir}/{vm_name}.qcow2'
        vm = QemuVM(vm_name, disk_path, add_by_host, is_sriov, bios)
        self.vm_list[vm_name] = vm

    def detach_all_acce_dev_from_vm(self, vm_name):
        self.vm_list[vm_name].clear_device()

    def download_from_vm(self, vm_name, local_path, remote_path):
        local_path = local_path.replace("[[vm_name]]", vm_name)
        remote_path = remote_path.replace("[[vm_name]]", vm_name)
        logger.info(f'download file from <{vm_name}>:{remote_path} to <{self.sut.sut_name}:{local_path}')
        self.vm_list[vm_name].put_to_sut(self.sut, local_path, remote_path)

    def execute_vm_cmd(self, vm_name, cmd, timeout=30, cwd='/root'):
        cmd = cmd.replace("[[vm_name]]", vm_name)
        logger.info(f'<{vm_name}> execute command [{cmd}]')
        return self.vm_list[vm_name].execute_cmd(self.sut, cmd, timeout, cwd)

    def execute_vm_cmd_async(self, vm_name, cmd, timeout=30, cwd='/root'):
        logger.info(f'<{vm_name}> execute command [{cmd}] async')
        return self.vm_list[vm_name].execute_cmd(self.sut, cmd, timeout, cwd, is_async=True)

    def is_vm_running(self, vm_name):
        if vm_name not in self.vm_list:
            return False

        disk_path = self.vm_list[vm_name].disk_path
        cmd = f"lsof | grep qemu-system-x86_64 | grep {disk_path} | wc -l"
        _, std_out, _ = self.sut.execute_shell_cmd(cmd)
        return std_out.strip() == "1"

    def kill_vm(self, vm_name):
        if vm_name not in self.vm_list:
            return
        if not self.is_vm_running(vm_name):
            return

        logger.info(f"try to kill {vm_name}")
        disk_path = self.vm_list[vm_name].disk_path
        cmd = f"lsof | grep qemu-system-x86_64 | grep {disk_path}"
        _, std_out, _ = self.sut.execute_shell_cmd(cmd)
        pid = std_out.split()[1]

        cmd = f"kill {pid}"
        self.sut.execute_shell_cmd(cmd)

    def register_vm(self, vm_name, disk_path, add_by_host=True, is_sriov=True, bios='/home/OVMF.fd'):
        logger.info(f'register virtual machine {vm_name}')
        vm = QemuVM(vm_name, disk_path, add_by_host, is_sriov, bios=bios)
        self.vm_list[vm_name] = vm

    def shutdown_vm(self, vm_name):
        self.execute_vm_cmd(vm_name, 'poweroff')
        time.sleep(30)

    def start_vm(self, vm_name):
        logger.info(f'Starting virtual machine {vm_name}')

        ssh_port = self.__get_free_port()
        self.sut.execute_shell_cmd(f"ssh-keygen -R [localhost]:{ssh_port}")
        self.vm_list[vm_name].start(self.sut, ssh_port)
        self.vm_list[vm_name].ssh_port = ssh_port

        remain_try_times = 200
        while not self.try_to_connect(vm_name) and remain_try_times > 0:
            time.sleep(3)
            remain_try_times -= 1
            logger.info(f'watting for {vm_name} boot into OS...')

        if remain_try_times <= 0:
            logger.error(f'error: start {vm_name} failed because SSH connection cannot be established')

    def start_vm_debug(self, vm_name, ssh_port):
        logger.info(f'Starting virtual machine {vm_name} for debug')

        self.vm_list[vm_name].start(self.sut, ssh_port)
        while not self.try_to_connect(vm_name):
            time.sleep(3)
            logger.info(f'watting for {vm_name} boot into OS...')

    # def start_vm_debug(self, vm_name):
    #     logger.info(f'Starting virtual machine {vm_name} for debug')
    #
    #     ssh_port = self.__get_free_port()
    #     self.sut.execute_shell_cmd(f"ssh-keygen -R [localhost]:{ssh_port}")
    #     self.vm_list[vm_name].start(self.sut, ssh_port)
    #     self.vm_list[vm_name].ssh_port = ssh_port
    #
    #     remain_try_times = 200
    #     while not self.try_to_connect(vm_name) and remain_try_times > 0:
    #         time.sleep(3)
    #         remain_try_times -= 1
    #         logger.info(f'watting for {vm_name} boot into OS...')
    #     if remain_try_times <= 0:
    #         logger.error(f'error: start {vm_name} failed because SSH connection cannot be established')

    def undefine_vm(self, vm_name, remove_img=False):
        if remove_img:
            rcode, _, std_err = self.sut.execute_shell_cmd(f'rm -f {self.vm_list[vm_name].disk_path}', timeout=60)
            if rcode != 0:
                raise Exception(std_err)
        self.vm_list.pop(vm_name)

    def upload_to_vm(self, vm_name, local_path, remote_path):
        local_path = local_path.replace("[[vm_name]]", vm_name)
        remote_path = remote_path.replace("[[vm_name]]", vm_name)
        logger.info(f'upload file from <{self.sut.sut_name}:{local_path} to <{vm_name}>:{remote_path}')
        self.vm_list[vm_name].get_from_sut(self.sut, local_path, remote_path)

    def try_to_connect(self, vm_name):
        ssh_port = self.vm_list[vm_name].ssh_port
        cmd = f'python /home/BKCPkg/domains/virtualization/auto-poc/src/caller.py --os-type LINUX '
        cmd += f'--command connect_test --ssh-port {ssh_port} '
        rcode, _, err = self.sut.execute_shell_cmd(cmd)
        return rcode == 0

    def __get_free_port(self):
        port_start = 2222
        port_end = 3333

        for port in range(port_start, port_end + 2):
            _, out, _ = self.sut.execute_shell_cmd(f'lsof -i:{port}')
            if out.strip() == '':
                return port

        err_msg = 'error: cannot find free port between 2222 and 3333'
        logger.error(err_msg)
        raise Exception(err_msg)


class RichHypervisor(QemuHypervisor):
    def __init__(self, sut):
        super().__init__(sut)
        self.vm_group_prefix = 'rich_vm_'

    def attach_acce_dev_to_vm_grouply(self, dev_list, dev_num_per_vm):
        logger.info(f'attach {dev_num_per_vm} accelerator devices to every virtual machine')
        cur_dev_index = 0

        for vm in self.vm_list.keys():
            self.attach_acce_dev_to_vm(vm, dev_list[cur_dev_index: cur_dev_index + dev_num_per_vm])
            cur_dev_index += dev_num_per_vm

    def create_rich_vm(self, vm_num, template, add_by_host=True, is_sriov=True, is_uuid=False, disk_dir='/home'):
        logger.info(f'create {vm_num} virtual machine from {template}')

        for i in range(vm_num):
            vm_name = self.vm_group_prefix + str(i)
            try:
                self.create_vm_from_template(vm_name, template, add_by_host, is_sriov, is_uuid, disk_dir)
            except Exception as e:
                logger.error(e.args[0])
                raise e

    def create_rich_vm_debug(self, vm_num, add_by_host=True, is_sriov=True, disk_dir='/home'):
        logger.info(f'debug {vm_num} virtual machine')

        for i in range(vm_num):
            vm_name = self.vm_group_prefix + str(i)
            try:
                self.create_vm_debug(vm_name, add_by_host, is_sriov, disk_dir)
            except Exception as e:
                logger.error(e.args[0])
                raise e

    def download_from_rich_vm(self, local_path, remote_path, start_index=None, end_index=None):
        start_index = 0 if not start_index else start_index
        end_index = len(self.vm_list) if not end_index else end_index + 1
        logger.info(
            f'download file from virtual machine {start_index} to {end_index-1} to <{self.sut.sut_name}>:{local_path}')

        vm_list = list(self.vm_list.keys())
        for vm in vm_list[start_index:end_index]:
            self.download_from_vm(vm, local_path, remote_path)

    def __execute_vm_cmd_thread(self, exec_res, vm_name, cmd, timeout, cwd):
        rcode, std_out, std_err = self.execute_vm_cmd(vm_name, cmd, timeout, cwd)
        exec_res[vm_name] = [rcode, std_out, std_err]

    def execute_rich_vm_cmd_parallel(self, cmd, timeout=60, cwd='/root', start_index=None, end_index=None):
        start_index = 0 if not start_index else start_index
        end_index = len(self.vm_list) if not end_index else end_index + 1
        logger.info(f'execute command [{cmd}] in virtual machine {start_index} to {end_index - 1}')

        vm_list = list(self.vm_list.keys())
        vm_list = vm_list[start_index:end_index]
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

    def execute_rich_vm_cmd_parallel_async(self, cmd, timeout=60, cwd='/root', start_index=None, end_index=None):
        # only for Linux virtual machine
        # cmd += " &"
        # return self.execute_rich_vm_cmd_parallel(cmd, timeout, cwd, start_index, end_index)
        start_index = 0 if not start_index else start_index
        end_index = len(self.vm_list) if not end_index else end_index + 1
        logger.info(f'execute async command [{cmd}] in virtual machine {start_index} to {end_index - 1}')

        vm_list = list(self.vm_list.keys())
        vm_list = vm_list[start_index:end_index]
        exec_res = {}
        logger.info(f'The virtual machine going to execute async`{cmd}`: {vm_list}')

        for vm in vm_list:
            exec_res[vm] = self.execute_vm_cmd_async(vm, cmd, timeout, cwd)

        return exec_res

    def start_rich_vm(self, start_index=None, end_index=None):
        start_index = 0 if not start_index else start_index
        end_index = len(self.vm_list) if not end_index else end_index + 1
        logger.info(f'start virtual machine {start_index} to {end_index - 1}')

        vm_list = list(self.vm_list.keys())
        for vm in vm_list[start_index:end_index]:
            logger.info(f"starting virtual machine {vm}")
            self.start_vm(vm)
            logger.info(f"start virtual machine {vm} successfully")

    def start_rich_vm_debug(self, start_index=None, end_index=None, ssh_port_list=None):
        start_index = 0 if not start_index else start_index
        end_index = len(self.vm_list) if not end_index else end_index + 1
        logger.info(f'start virtual machine {start_index} to {end_index - 1}')

        vm_list = list(self.vm_list.keys())
        for i, vm in enumerate(vm_list[start_index:end_index]):
            self.start_vm_debug(vm, ssh_port_list[i])

    def shutdown_rich_vm(self, start_index=None, end_index=None):
        start_index = 0 if not start_index else start_index
        end_index = len(self.vm_list) if not end_index else end_index + 1
        logger.info(f'shutdown virtual machine {start_index} to {end_index - 1}')

        vm_list = list(self.vm_list.keys())
        for vm in vm_list[start_index:end_index]:
            self.shutdown_vm(vm)
        logger.info(f'shutdown virtual machine {start_index} to {end_index - 1} successfully')

    def undefine_rich_vm(self):
        logger.info(f'undefine all virtual machine')

        vm_name_list = []
        for name in self.vm_list.keys():
            vm_name_list.append(name)
        for name in vm_name_list:
            self.undefine_vm(name, True)

        logger.info(f'undefine all virtual machine successfully')

    def upload_to_rich_vm(self, local_path, remote_path, start_index=None, end_index=None):
        start_index = 0 if not start_index else start_index
        end_index = len(self.vm_list) if not end_index else end_index + 1
        logger.info(
            f'upload file from <{self.sut.sut_name}>:{local_path} to virtual machine {start_index} to {end_index - 1}')

        vm_list = list(self.vm_list.keys())
        for vm in vm_list[start_index:end_index]:
            self.upload_to_vm(vm, local_path, remote_path)
