import time
from threading import Thread
from src.accelerator.lib.accelerator import *
# from src.virtualization.lib.const import sut_tool


class KVM:
    CALLER_COMMAND_BASE = f"python {sut_tool('SRC_SCRIPT_PATH_L')}/src/caller.py --os-type LINUX "

    def __init__(self, sut):
        self.sut = sut
        self.attached_device_list = {}
        self.vm_list = []
        self.acce = Accelerator(sut)



    def attach_mdev_to_vm(self, vm_name, mdev_uuid_list):
        self.sut.execute_shell_cmd('rm -rf xml', timeout=60, cwd=IMAGE_PATH_L)
        self.sut.execute_shell_cmd('mkdir xml', timeout=60, cwd=IMAGE_PATH_L)
        is_vm_running = self.is_vm_running(vm_name)
        if is_vm_running:
            self.shutdown_vm(vm_name)
        for mdev_uuid in mdev_uuid_list:
            logger.info(f"attach device {mdev_uuid} to {vm_name}")
            xml_path = self.create_mdev_xml_on_sut(vm_name, mdev_uuid)
            cmd = f'virsh attach-device {vm_name} {xml_path} --config'
            rcode, _, std_err = self.sut.execute_shell_cmd(cmd)
            if rcode != 0:
                raise Exception(std_err)
            if vm_name not in self.attached_device_list:
                self.attached_device_list[vm_name] = [xml_path]
            else:
                self.attached_device_list[vm_name] += [xml_path]


    def attach_vf_to_vm(self, vm_name, vf_list):
        is_vm_running = self.is_vm_running(vm_name)
        self.sut.execute_shell_cmd('rm -rf xml', timeout=60, cwd=IMAGE_PATH_L)
        self.sut.execute_shell_cmd('mkdir xml', timeout=60, cwd=IMAGE_PATH_L)
        if is_vm_running:
            self.shutdown_vm(vm_name)
        for vf in vf_list:
            logger.info(f"attach device {vf} to {vm_name}")
            xml_path = self.create_VF_xml_on_sut(vm_name, vf)
            cmd = f'virsh attach-device {vm_name} {xml_path} --config'
            rcode, _, std_err = self.sut.execute_shell_cmd(cmd)
            if rcode != 0:
                raise Exception(std_err)

            if vm_name not in self.attached_device_list:
                self.attached_device_list[vm_name] = [xml_path]
            else:
                self.attached_device_list[vm_name] += [xml_path]

    def check_device_in_vm(self,vm_name, device_ip, vf_num, mdev=False):
        """
              Purpose: Check attached device in VM
              Args:
                  vm_name: Run command on which VM
                  device_ip: Which device need to check; eg: 'qat', 'blb', 'dsa'
                  vf_num: How many vf attached to VM
                  mdev: Is SIOV device
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Check attached device in VM
                      check_device_in_vm(vm_name, 'qat', 16)
        """
        _, out, err = qemu.execute_vm_cmd(vm_name, 'lspci')
        if not mdev:
            if not vf_num:
                if device_ip == 'qat':
                    self.acce.check_keyword([f'Intel Corporation Device {self.acce.qat_id}'], out, "Can't detact attached device")
                elif device_ip == 'dlb':
                    self.acce.check_keyword([f'Intel Corporation Device {self.acce.dlb_id}'], out, "Can't detact attached device")
                elif device_ip == 'dsa':
                    self.acce.check_keyword([f'Intel Corporation Device {self.acce.dsa_id}'], out, "Can't detact attached device")
            else:
                if device_ip == 'qat':
                    self.check_device_num_in_vm(out, vf_num, f'Intel Corporation Device {self.acce.qat_vf_id}')
                elif device_ip == 'dlb':
                    self.check_device_num_in_vm(out, vf_num, f'Intel Corporation Device {self.acce.dlb_vf_id}')
        else:
            if device_ip == 'qat':
                self.acce.check_keyword([f'Intel Corporation Device {self.acce.qat_mdev_id}'], out, "Can't detact attached device")

    def check_device_num_in_vm(self, out, vf_num, check_key):
        dev_num = 0
        line_list = out.strip().split('\n')
        for line in line_list:
            if check_key in line:
                dev_num += 1
        if dev_num != vf_num:
            logger.error("Can't detact attached device")
            raise Exception("Can't detact attached device")

    def create_VF_xml_on_sut(self, vm_name, vf):
        bus = '0x' + vf.split(':')[1]
        slot = '0x' + vf.split(':')[2].split('.')[0]
        function = '0x' +  vf.split(':')[2].split('.')[1]

        xml_filename = f'pci_device_{vm_name}_{bus}_{slot}_{function}.xml'
        xml_content = self.get_pci_xml_content(bus, slot, function)

        with open(xml_filename, "w") as xml_file:
            xml_file.write(xml_content)

        self.sut.upload_to_remote(localpath=xml_filename, remotepath=f"{sut_tool('IMAGE_PATH_L')}/xml")
        os.remove(xml_filename)

        return f"{sut_tool('IMAGE_PATH_L')}/xml/{xml_filename}"

    def create_mdev_xml_on_sut(self, vm_name, mdev_uuid):
        xml_filename = f'pci_device_{vm_name}_{mdev_uuid}.xml'
        xml_content = self.get_mdev_xml_content(mdev_uuid)

        with open(xml_filename, "w") as xml_file:
            xml_file.write(xml_content)

        self.sut.upload_to_remote(localpath=xml_filename, remotepath=f"{sut_tool('IMAGE_PATH_L')}/xml")
        os.remove(xml_filename)

        return f"{sut_tool('IMAGE_PATH_L')}/xml/{xml_filename}"

    def create_vm_from_template(self, vm_name, template=f'{IMAGE_PATH_L}{CLEAN_IMAGE_NAME}', ram_mb=16384, cpu_num=4, disk_dir=f'{IMAGE_PATH_L}', vnic_type='virtio', timeout=600):
        """
        Reference:
            None
        Purpose: to create a new VM from template
        Args:
            vm_name: the name of new VM
            template: the path of template file
            ram_mb: the memory going to be assigned to VM, in MB
            cpu_num: the cpu going to be assigned to VM
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
            if self.is_vm_exist(vm_name):
                if self.is_vm_running(vm_name):
                    self.shutdown_vm(vm_name)
                self.undefine_vm(vm_name)

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
        self.sut.execute_shell_cmd(f'virsh setvcpus {vm_name} --maximum {cpu_num} --config', timeout=120)
        self.sut.execute_shell_cmd(f'virsh setvcpus {vm_name} --count {cpu_num} --config', timeout=120)
        self.vm_list.append(vm_name)
        logger.info(f"create {vm_name} from {template} succeed")

    def copy_template_to_disk(self, vm_name, template, disk_dir):
        disk_path = f'{disk_dir}/{vm_name}.qcow2'
        cmd = f'cp {template} {disk_path}'
        logger.info(f'copying {template} to {disk_path}, wait a while please...\n')
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd, timeout=3000)
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
            Create a new virtual disk file at '/home' which name is 'temp.qcow2' and size is 10GB
                create_disk_file('/home/temp.qcow2', 10)
        """
        logger.info(f'create new disk file {disk_path} size={disk_size_gb}GB')

        cmd = f'qemu-img create -f qcow2 ' \
              f'-o size={disk_size_gb}G {disk_path}'
        rcode, _, std_err = self.sut.execute_shell_cmd(cmd=cmd)
        if rcode != 0:
            raise Exception(std_err)

    def check_device_in_vm(self, out, vf_num, check_key):
        dev_num = 0
        line_list = out.strip().split('\n')
        for line in line_list:
            if check_key in line:
                dev_num += 1
        if dev_num != vf_num:
            logger.error("Can't detact attached device")
            raise Exception("Can't detact attached device")

    def check_error(self, err):
        if err != '':
            logger.error(err)
            raise Exception(err)

    def execute_cmd(self, vm_name, vm_cmd, timeout, cwd='/root', is_async=False):
        vm_cmd = f'cd {cwd} && {vm_cmd}'
        cmd = f'python /home/BKCPkg/domains/virtualization/auto-poc/src/caller.py --os-type LINUX '
        cmd += '--command execute_vm_cmd '
        cmd += f'--vm-name {vm_name} '
        cmd += f'--timeout {timeout} '
        cmd += f'--vm-command "{vm_cmd}" '
        cmd += f'--ssh-port 22 '
        if is_async:
            rcode, std_out, std_err = self.sut.execute_shell_cmd_async(cmd, timeout=(timeout+60))
        else:
            rcode, std_out, std_err = self.sut.execute_shell_cmd(cmd, timeout=(timeout+60))
        out_line_list = std_out.strip().split('\n')
        std_out = '\n'.join(out_line_list[1:])
        return rcode, std_out, std_err

    def execute_vm_cmd(self, vm_name, cmd, timeout=30, cwd='/root'):
        cmd = cmd.replace("[[vm_name]]", vm_name)
        logger.info(f'<{vm_name}> execute command [{cmd}]')
        return self.execute_cmd(vm_name, cmd, timeout, cwd)

    def execute_vm_cmd_async(self, vm_name, cmd, timeout=30, cwd='/root'):
        cmd = cmd.replace("[[vm_name]]", vm_name)
        logger.info(f'<{vm_name}> execute command [{cmd}]')
        return self.execute_cmd(vm_name, cmd, timeout, cwd, is_async=True)

    def get_pci_xml_content(self, bus, slot, function):
        content = '<hostdev mode="subsystem" type="pci" managed="yes">\n'
        content += '    <driver name="vfio"/>\n'
        content += '    <source>\n'
        content += f'        <address domain="0x0000" bus="{bus}" slot="{slot}" function="{function}"/>\n'
        content += '    </source>\n'
        content += '</hostdev>\n\n'
        return content



    def get_mdev_xml_content(self, mdev_uuid):
        content = '<hostdev mode="subsystem" type="mdev" managed="no" model="vfio-pci" display="off">\n'
        content += '    <source>\n'
        content += f'        <address uuid="{mdev_uuid}"/>\n'
        content += '    </source>\n'
        content += '</hostdev>\n\n'
        return content



    def get_vm_external_ip(self, vm_name):
        vm_cmd = "ifconfig | grep \"inet 10.\" | grep -v i\"10.0\""
        rcode, std_out, std_err = self.execute_vm_cmd(vm_name, vm_cmd)
        if rcode != 0:
            raise Exception(std_err)

        if std_out.strip() == "":
            raise Exception(f"error: cannot find external IP from {vm_name}")

        return std_out.strip().split()[1]


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

    def is_upload_src_path_exist(self, src_path):
        if 'linux' in self.CALLER_COMMAND_BASE.lower():
            cmd = f'ls -l {src_path}'
            err_keyword = 'no such file or directory'
        else:
            cmd = f'dir {src_path}'
            err_keyword = 'File Not Found'
        _, _, std_err = self.sut.execute_shell_cmd(cmd)
        return err_keyword not in std_err


    def is_vm_autostart(self, vm_name):
        logger.info(f'check if {vm_name} start with Hypervisor')
        return self.__get_vm_info(vm_name)[VM_INFO.IS_AUTOSTART] == VM_INFO.ENABLE_AUTOSTART

    def is_vm_exist(self, vm_name):
        cmd = f'virsh list --all | grep {vm_name}'
        _, std_out, std_err = self.sut.execute_shell_cmd(cmd)
        if std_err.strip() != '':
            raise Exception(std_err)
        return vm_name in std_out

    def is_vm_running(self, vm_name):
        cmd = f'virsh list --name | grep {vm_name}'
        _, std_out, std_err = self.sut.execute_shell_cmd(cmd)
        if std_err.strip() != '':
            raise Exception(std_err)
        return vm_name in std_out



    def get_from_sut(self, vm_name, sut_path, vm_path):
        cmd = f'python /home/BKCPkg/domains/virtualization/auto-poc/src/caller.py --os-type LINUX '
        cmd += '--command upload_to_vm '
        cmd += f'--vm-name {vm_name} '
        cmd += f'--src-path {sut_path} '
        cmd += f'--dest-path {vm_path} '
        cmd += f'--ssh-port 22'

        rcode, _, std_err = self.sut.execute_shell_cmd(cmd, timeout=6000)
        if rcode != 0:
            raise Exception(std_err)


    def ping_vm(self, vm_ip, times=2):
        cmd = f'ping -c {times} {vm_ip}'
        _, std_out, _ = self.sut.execute_shell_cmd(cmd)
        return '100% packet loss' not in std_out

    def put_to_sut(self, vm_name, sut_path, vm_path):
        cmd = f'python /home/BKCPkg/domains/virtualization/auto-poc/src/caller.py --os-type LINUX '
        cmd += '--command download_from_vm '
        cmd += f'--vm-name {vm_name} '
        cmd += f'--src-path {vm_path} '
        cmd += f'--dest-path {sut_path} '
        cmd += f'--ssh-port 22'

        rcode, _, std_err = self.sut.execute_shell_cmd(cmd, timeout=6000)
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
        while (remain_time > 0) and (not self.__check_is_vm_in_os_by_log(vm_name)):
            logger.info(f"Waitting for {vm_name} boot into os...")
            remain_time -= 10

        if remain_time <= 0:
            raise Exception(f"error: cannot start {vm_name} with timeout {timeout}s, try logger timeout please")

        logger.info(f'start {vm_name} succeed')


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

    def __execute_vm_cmd_thread(self, exec_res, vm_name, cmd, timeout, cwd):
        rcode, std_out, std_err = self.execute_vm_cmd(vm_name, cmd, timeout, cwd)
        exec_res[vm_name] = [rcode, std_out, std_err]

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



class Rich_KVM(KVM):

    def __init__(self, sut):
        super().__init__(sut)
        self.vm_group_prefix = 'rich_vm_'


    def attach_acce_dev_to_vm_grouply(self, dev_list, dev_num_per_vm, BDF=True):
        logger.info(f'attach {dev_num_per_vm} accelerator devices to every virtual machine')
        cur_dev_index = 0
        if BDF:
            for vm in self.vm_list:
                self.attach_vf_to_vm(vm, dev_list[cur_dev_index: cur_dev_index + dev_num_per_vm])
                cur_dev_index += dev_num_per_vm
        else:
            for vm in self.vm_list:
                self.attach_mdev_to_vm(vm, dev_list[cur_dev_index: cur_dev_index + dev_num_per_vm])
                cur_dev_index += dev_num_per_vm

    def add_environment_to_file_rich_vm(self, check_key, add_command):
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
                        add_environment_to_file_rich_vm(qemu, 'end', 'end=$((SECONDS+110))')
        """
        exec_res = self.execute_rich_vm_cmd_parallel('cat /root/.bashrc', timeout=60)
        for vm in exec_res:
            out = exec_res[vm][1]
            if check_key not in out:
                self.execute_vm_cmd(vm, f"echo '{add_command}' >> /root/.bashrc", timeout=60)
                self.execute_vm_cmd(vm, 'source /root/.bashrc', timeout=60)



    def create_rich_vm(self, vm_num, template=f'{IMAGE_PATH_L}{CLEAN_IMAGE_NAME}', ram_mb=4096, cpu_num=4,
                       disk_dir=sut_tool('IMAGE_PATH_L'), vnic_type='virtio'):
        logger.info(f'create {vm_num} virtual machine from {template}')

        for i in range(vm_num):
            vm_name = self.vm_group_prefix + str(i)
            try:
                self.create_vm_from_template(vm_name, template, ram_mb, cpu_num, disk_dir, vnic_type)
            except Exception as e:
                logger.error(e.args[0])
                raise e

    def check_device_in_rich_vm(self, device_ip, vf_num, mdev=False):
        """
              Purpose: Check attached device in VM
              Args:
                  device_ip: Which device need to check; eg: 'qat', 'blb', 'dsa'
                  vf_num: How many vf attached to VM
                  mdev: Is SIOV device
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Check attached device in VM
                      check_device_in_rich_vm('qat', 16)
        """
        logger.info(f'start check devices in every virtual machine')
        exec_res = self.execute_rich_vm_cmd_parallel('lspci')
        for vm in exec_res:
            out = exec_res[vm][1]
            if not mdev:
                if not vf_num:
                    if device_ip == 'qat':
                        self.acce.check_keyword([f'Intel Corporation Device {self.acce.qat_id}'], out,
                                                "Can't detact attached device")
                    elif device_ip == 'dlb':
                        self.acce.check_keyword([f'Intel Corporation Device {self.acce.dlb_id}'], out,
                                                "Can't detact attached device")
                    elif device_ip == 'dsa':
                        self.acce.check_keyword([f'Intel Corporation Device {self.acce.dsa_id}'], out,
                                                "Can't detact attached device")
                else:
                    if device_ip == 'qat':
                        self.check_device_num_in_vm(out, vf_num, f'Intel Corporation Device {self.acce.qat_vf_id}')
                    elif device_ip == 'dlb':
                        self.check_device_num_in_vm(out, vf_num, f'Intel Corporation Device {self.acce.dlb_vf_id}')
            else:
                if device_ip == 'qat':
                    self.acce.check_keyword([f'Intel Corporation Device {self.acce.qat_mdev_id}'], out,
                                            "Can't detact attached device")
        logger.info(f'check devices in every virtual machine successfully')

    def dlb_install_rich_vm(self, ch_makefile):
        """
              Purpose: To install DLB driver in VM
              Args:
                  ch_makefile: if need to modify DLB make file
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Modify Makefile and install DLB driver
                      dlb_install_rich_vm(True)
        """
        logger.info(f'start dlb driver in every virtual machine')
        self.execute_rich_vm_cmd_parallel(f'mkdir -p {DLB_DRIVER_PATH_L}', timeout=60)
        self.execute_rich_vm_cmd_parallel(f'rm -rf {DLB_DRIVER_PATH_L}*', timeout=60)
        sut_file_dir = f'{DLB_DRIVER_PATH_L}{DLB_DRIVER_NAME}'
        vm_file_dir = f'{DLB_DRIVER_PATH_L}{DLB_DRIVER_NAME}'
        self.upload_to_rich_vm(sut_file_dir, vm_file_dir)
        logger.info(f'copy dlb driver to every virtual machine successfully')
        self.execute_rich_vm_cmd_parallel(f'unzip -o {DLB_DRIVER_NAME}', timeout=60, cwd=DLB_DRIVER_PATH_L)
        logger.info(f'unzip dlb driver in every virtual machine successfully')
        if ch_makefile:
            self.execute_rich_vm_cmd_parallel(
                "sed -i 's/ccflags-y += -DCONFIG_INTEL_DLB2_SIOV/#  iccflags-y += -DCONFIG_INTEL_DLB2_SIOV/g' /home/BKCPkg/domains/accelerator/dlb/driver/dlb2/Makefile",
                timeout=60)
        self.execute_rich_vm_cmd_parallel('make', timeout=60, cwd=f'{DLB_DRIVER_PATH_L}driver/dlb2/')
        # self.__check_error(err)
        logger.info(f'install dlb driver in every virtual machine successfully')
        self.execute_rich_vm_cmd_parallel('rmmod dlb2', timeout=60, cwd=f'{DLB_DRIVER_PATH_L}driver/dlb2/')
        self.execute_rich_vm_cmd_parallel('insmod ./dlb2.ko', timeout=60, cwd=f'{DLB_DRIVER_PATH_L}driver/dlb2/')
        logger.info(f'insmod dlb driver in every virtual machine successfully')
        exec_res = self.execute_rich_vm_cmd_parallel('lsmod | grep dlb2', timeout=60)
        for vm in exec_res:
            out = exec_res[vm][1]
            self.acce.check_keyword(['dlb2'], out, 'Issue - dlb driver install fail')
        exec_res = self.execute_rich_vm_cmd_parallel('make', timeout=60, cwd=f'{DLB_DRIVER_PATH_L}libdlb/')
        for vm in exec_res:
            err = exec_res[vm][2]
            self.check_error(err)
        self.add_environment_to_file_rich_vm('LD_LIBRARY_PATH',
                                             'export LD_LIBRARY_PATH=/home/BKCPkg/domains/accelerator/dlb/libdlb:$LD_LIBRARY_PATH')
        logger.info(f'dlb driver show in every virtual machine correct')

    def download_from_rich_vm(self, local_path, remote_path):
        vm_list = self.vm_list
        for vm in vm_list:
            logger.info(
                f'download file from virtual machine {vm}  to <{self.sut.sut_name}>:{local_path}')
            self.put_to_sut(vm, local_path, remote_path)

    def execute_rich_vm_cmd_parallel(self, cmd, timeout=60, cwd='/root', start_index=None, end_index=None):
        start_index = 0 if not start_index else start_index
        end_index = len(self.vm_list) if not end_index else end_index + 1
        logger.info(f'execute command [{cmd}] in virtual machine {start_index} to {end_index - 1}')

        vm_list = self.vm_list
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

        vm_list = list(self.vm_list)
        vm_list = vm_list[start_index:end_index]
        exec_res = {}
        logger.info(f'The virtual machine going to execute async`{cmd}`: {vm_list}')

        for vm in vm_list:
            exec_res[vm] = self.execute_vm_cmd_async(vm, cmd, timeout, cwd)

        return exec_res


    def kernel_header_devel_rich_vm(self):
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
                      kernel_header_devel_rich_vm(qemu)
        """
        logger.info(f'start install kernel_devel to every virtual machine')
        self.execute_rich_vm_cmd_parallel(f'mkdir -p {KERNEL_HEADER_PATH_L}', timeout=60)
        self.execute_rich_vm_cmd_parallel(f'rm -rf {KERNEL_HEADER_PATH_L}*', timeout=60)
        sut_file_dir1 = f'{KERNEL_DEVEL_PATH_L}{KERNEL_DEVEL_NAME}'
        vm_file_dir1 = f'{KERNEL_DEVEL_PATH_L}{KERNEL_DEVEL_NAME}'
        self.upload_to_rich_vm(sut_file_dir1, vm_file_dir1)
        self.execute_rich_vm_cmd_parallel('rpm -ivh *.rpm --force --nodeps', timeout=5 * 60, cwd=KERNEL_DEVEL_PATH_L)

    def qat_install_rich_vm(self, execute_command, enable_siov=False):
        """
              Purpose: To install QAT driver in VM
              Args:
                  execute_command : qat configuration flag
                  enable_sriov: If enable sriov host function in VM
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: install QAT driver in VM
                      qat_install_rich_vm(qemu, False)
        """
        logger.info(f'start install qat driver in every virtual machine')
        self.execute_rich_vm_cmd_parallel(f'mkdir -p {QAT_DRIVER_PATH_L}', timeout=60)
        self.execute_rich_vm_cmd_parallel(f'rm -rf {QAT_DRIVER_PATH_L}*', timeout=60)
        sut_file_dir = f'{QAT_DRIVER_PATH_L}{QAT_DRIVER_NAME}'
        vm_file_dir = f'{QAT_DRIVER_PATH_L}{QAT_DRIVER_NAME}'
        self.upload_to_rich_vm(sut_file_dir, vm_file_dir)
        logger.info(f'copy qat driver to every virtual machine successfully')
        self.execute_rich_vm_cmd_parallel(f'unzip {QAT_DRIVER_NAME}', timeout=60, cwd=QAT_DRIVER_PATH_L)
        self.execute_rich_vm_cmd_parallel('tar -zxvf *.tar.gz', timeout=60, cwd=QAT_DRIVER_PATH_L)
        logger.info(f'qat driver successfully unzip in every virtual machine ')
        self.execute_rich_vm_cmd_parallel(execute_command, timeout=5*60, cwd=QAT_DRIVER_PATH_L)
        self.execute_rich_vm_cmd_parallel('make install', timeout=30*60, cwd=QAT_DRIVER_PATH_L)
        self.execute_rich_vm_cmd_parallel('make samples-install', timeout=15*60, cwd=QAT_DRIVER_PATH_L)
        logger.info(f'qat driver install successfully in every virtual machine')
        exec_res = self.execute_rich_vm_cmd_parallel('lsmod | grep qat', timeout=60)
        for vm in exec_res:
            out = exec_res[vm][1].strip()
            err = exec_res[vm][2]
            self.check_error(err)
            if enable_siov:
                key_list = ['qat_vqat', 'intel_qat']
                self.acce.check_keyword(key_list, out, 'Issue - QAT driver install failed')
            else:
                key_list = ['qat_4xxx', 'intel_qat']
                self.acce.check_keyword(key_list, out, 'Issue - QAT driver install failed')
        logger.info(f'qat driver show successfully in every virtual machine')

    def rpm_install_rich_vm(self):
        """
              Purpose: To install rpm packages in VM
              Args:
                  qemu: Call VM Class RichHypervisor
                  vm_name: Run command on which VM
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Install rpm packages in VM
                      rpm_install_rich_vm(qemu)
        """
        logger.info(f'start yum install packages to every virtual machine')
        rpm_list = [
            'zlib-devel.x86_64 yasm systemd-devel boost-devel.x86_64 openssl-devel libnl3-devel gcc gcc-c++ libgudev.x86_64 libgudev-devel.x86_64 systemd* abrt-cli boost-devel.x86_64']
        self.add_environment_to_file_rich_vm('http_proxy', 'export http_proxy=http://proxy-iind.intel.com:911')
        self.add_environment_to_file_rich_vm('HTTP_PROXY', 'export HTTP_PROXY=http://proxy-iind.intel.com:911')
        self.add_environment_to_file_rich_vm('https_proxy', 'export https_proxy=http://proxy-iind.intel.com:911')
        self.add_environment_to_file_rich_vm('HTTPS_PROXY', 'export HTTPS_PROXY=http://proxy-iind.intel.com:911')
        self.add_environment_to_file_rich_vm('no_proxy', "export no_proxy='localhost,127.0.0.1,intel.com,.intel.com'")
        for rpm in rpm_list:
            self.execute_rich_vm_cmd_parallel(f'yum -y install {rpm}', timeout=60000)
        logger.info(f'yum install packages to every virtual machine successfully')
        self.execute_rich_vm_cmd_parallel(f'yum -y install make', timeout=60000)
        self.execute_rich_vm_cmd_parallel(f'yum -y install patch', timeout=60000)


    def run_qat_sample_code_rich_vm(self, qat_cpa_param=''):
        """
              Purpose: Run QAT cap_sample stress on VM
              Args:
                  qat_cpa_param: Which cap_sample stress need to run
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: run cap_sample stress
                        run_qat_sample_code_rich_vm()
                        run_qat_sample_code_rich_vm('signOfLife=1')
        """
        logger.info(f'start run qat stress in every virtual machine')
        exec_res = self.execute_rich_vm_cmd_parallel('./cpa_sample_code ' + qat_cpa_param, timeout=10 * 60, cwd=f'{QAT_DRIVER_PATH_L}/build/')
        for vm in exec_res:
            out = exec_res[vm][1]
            self.acce.check_keyword(['Sample code completed successfully'], out, 'Issue - Run qat stress fail')
        logger.info(f'run qat stress in every virtual machine successfully')

    def run_dlb_rich_vm(self, num=1024, ldb=True):
        if ldb:
            exec_res = self.execute_rich_vm_cmd_parallel(f'./ldb_traffic -n {num}', timeout=60 * 10,
                                                         cwd=f'{DLB_DRIVER_PATH_L}libdlb/examples')
            for vm in exec_res:
                out = exec_res[vm][1]
                self.acce.check_keyword([f'Received {num} events'], out, 'execute dlb stress fail')
        else:
            exec_res = self.execute_rich_vm_cmd_parallel(f'./dir_traffic -n {num}', timeout=60 * 10,
                                                        cwd=f'{DLB_DRIVER_PATH_L}libdlb/examples')
            for vm in exec_res:
                out = exec_res[vm][1]
                self.acce.check_keyword([f'Received {num} events'], out, 'execute dlb stress fail')

    def shutdown_rich_vm(self, start_index=None, end_index=None):
        start_index = 0 if not start_index else start_index
        end_index = len(self.vm_list) if not end_index else end_index + 1
        logger.info(f'shutdown virtual machine {start_index} to {end_index - 1}')

        vm_list = list(self.vm_list)
        for vm in vm_list[start_index:end_index]:
            self.shutdown_vm(vm)
        logger.info(f'shutdown virtual machine {start_index} to {end_index - 1} successfully')

    def start_rich_vm(self, start_index=None, end_index=None):
        start_index = 0 if not start_index else start_index
        end_index = len(self.vm_list) if not end_index else end_index + 1
        logger.info(f'start virtual machine {start_index} to {end_index - 1}')

        vm_list = self.vm_list
        for vm in vm_list:
            logger.info(f"starting virtual machine {vm}")
            self.start_vm(vm)
            logger.info(f"start virtual machine {vm} successfully")

    def undefine_rich_vm(self):
        logger.info(f'undefine all virtual machine')

        for vm_name in self.vm_list:
            self.undefine_vm(vm_name, True)

        logger.info(f'undefine all virtual machine successfully')

    def upload_to_rich_vm(self, local_path, remote_path):
        vm_list = self.vm_list
        for vm in vm_list:
            self.get_from_sut(vm, local_path, remote_path)


    def __execute_vm_cmd_thread(self, exec_res, vm_name, cmd, timeout, cwd):
        rcode, std_out, std_err = self.execute_vm_cmd(vm_name, cmd, timeout, cwd)
        exec_res[vm_name] = [rcode, std_out, std_err]