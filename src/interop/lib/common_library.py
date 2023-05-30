import os
import subprocess
import sys
import six
import time
import re

if six.PY2:
    from pathlib import Path
if six.PY3:
    from pathlib2 import Path

from dtaf_core.lib.dtaf_constants import ProductFamilies

from src.lib.common_content_lib import CommonContentLib
from src.lib.content_artifactory_utils import ContentArtifactoryUtils
from src.lib.content_configuration import ContentConfiguration
from src.lib.os_lib import WindowsCommonLib
from src.lib import content_exceptions
from src.lib.grub_util import GrubUtil
from src.lib.install_collateral import InstallCollateral
from src.interop.lib.accelerator_library import AcceleratorLibrary
from src.virtualization.virtualization_common import VirtualizationCommon


class CommonLibrary(object):
    REGEX_FOR_INTEL_IOMMU_ON_STR = r"intel_iommu=on,sm_on\siommu=on"
    COMMAND_TO_BIND_DEVICES = "echo 8086 {} > /sys/bus/pci/drivers/vfio-pci/new_id"
    COMMAND_TO_UNBIND_DEVICES = "echo {} > /sys/bus/pci/devices/{}\:{}\:{}.{}/driver/unbind"
    QAT_CODE = "4940"
    DLB_CODE = "2710"
    DSA_CODE = "0b25"
    IAX_CODE = "0cfe"
    TEST_CASE_CONTENT_PATH = r"/root/pv-dsa-iax-bkc-tests/spr-accelerators-random-config-and-test"
    ACC_DEVICES = ["qat", "dlb", "dsa", "iax"]
    ACC_DEVICE_CODE = ["4940", "2710", "0b25", "0cfe"]
    COPY_FILE_TO_VM_FROM_SUT = 'export SSHPASS=password;sshpass -e scp -o StrictHostKeyChecking=no -r root@{}:/root/{} {} && echo "Files copied"'
    CREATE_VM_CMD = r"/usr/libexec/qemu-kvm -name {} -machine q35 -enable-kvm -global kvm-apic.vapic=false -m 10240 " \
                    r"-cpu host -drive format=raw,file={} -bios /usr/share/qemu/OVMF.fd -smp 16 -nic user," \
                    r"hostfwd=tcp::{}-:22 -nographic "
    REGEX_VM_FAIL = "Connection refused"
    SSH_TO_PORT = 'ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o LogLevel=ERROR -p {} localhost "{}"'
    ROOT_EXE_CMD_ON_VM = "cd {} ; {}"
    ROOT = "/root/"
    QAT_BUILD_PATH = "/root/QAT/build/"
    ACCELERATOR_DEVICES_VM = []
    VFI_DEVICES = "-device vfio-pci,host={}"
    CLONED_PATH = "/home/images/{}.img"
    REGEX_FOR_FISHER_TOOL_SUCCESS = r"I: fisher: stats: PASS = "
    IAX_CONFIG_FILE_COMMAND = "./Setup_Randomize_IAX_Conf.sh"
    REGEX_FOR_INTEL_IOMMU_ON_STR_VM = r"intel_iommu=on,sm_on iommu=on no5lvl --update-kernel=ALL"
    WORKLOAD_CYCLE_CMD = "fisher --workload=\"{}\" --injection-type=ddr5_patrol_scrub_correctable_injection " \
                         "--cycles={} --remote-host={} --remote-port={}"

    WORKLOAD_RUNTIME_CMD = 'fisher --workload={} --injection-type=ddr5_patrol_scrub_correctable_injection ' \
                           '--runtime={} --remote-host={} --remote-port={}'
    ACCEL_RANDOM_CONFIG_PATH = r"/root/accel-random-config-and-test/{}"
    devices_list = ['-device intel-iommu,caching-mode=on,dma-drain=on,x-scalable-mode="modern",device-iotlb=on,aw-bits=48 ']
    device_string = '-device vfio-pci,sysfsdev=/sys/bus/mdev/devices/{}'

    def __init__(self, log, os_obj, cfg_opts, arguments=None):

        self._log = log
        self._os = os_obj
        self.sut_os = self._os.os_type
        self._cfg = cfg_opts
        self._common_content_lib = CommonContentLib(self._log, self._os, self._cfg)
        self._common_content_configuration = ContentConfiguration(self._log)
        self._install_collateral = InstallCollateral(self._log, self._os, cfg_opts)  # ....
        self.run_time = self._common_content_configuration.get_workload_time()  # ..
        self.PTU_WORKLOAD_COMMAND = "./ptu -y -ct 3 -cpu 0xFE -t {0}".format(self.run_time)
        self.MLC_WORKLOAD_COMMAND = "./mlc --loaded_latency -t{0} -X -D8192 ".format(self.run_time)
        self._command_timeout = self._common_content_configuration.get_command_timeout()
        self._os_time_out_in_sec = self._common_content_configuration.os_full_ac_cycle_time_out()
        self._reboot_time_out = self._common_content_configuration.get_reboot_timeout()
        self.sut_ras_tools_path = None
        self.sut_viral_injector_path = None
        self.dpdk_file_path = self._common_content_configuration.get_dpdk_file()
        self.dpdk_file_name = os.path.split(self.dpdk_file_path)[-1].strip()
        self.dpdk_patch_file_name = self._common_content_configuration.get_dpdk_patch_file()
        self.rdt_file_path = self._common_content_configuration.get_rdt_file()
        self.kernel_rpm_file_name = self._common_content_configuration.get_kernel_rpm_file()
        self.qat_file_path = self._common_content_configuration.get_qat_file()
        self.hqm_file_path = self._common_content_configuration.get_hqm_file()
        self.accel_file_path = self._common_content_configuration.get_idx_file()
        self.spr_file_path = self._common_content_configuration.get_spr_file()
        self._ldb_traffic_data = self._common_content_configuration.get_hqm_ldb_traffic_data()
        self._platform = self._common_content_lib.get_platform_family()
        self._os_lib = WindowsCommonLib(self._log, os_obj)
        self._artifactory_obj = ContentArtifactoryUtils(self._log, self._os, self._common_content_lib, cfg_opts)
        self._grub_obj = GrubUtil(self._log, self._common_content_configuration, self._common_content_lib)
        self._accelerator_lib = AcceleratorLibrary(log, os_obj, cfg_opts)
        self._vm_common = VirtualizationCommon(log, arguments, cfg_opts)
        self.num_of_cycles = self._common_content_configuration.memory_number_of_cycle()
        self.fisher_port_number = self._common_content_configuration.get_fisher_port_number_for_err_injection()
        self.REGEX_FOR_DLB_WORKLOAD_SUCCESS = r"Success"
        self.REGEX_FOR_QAT_WORKLOAD_SUCCESS = r"Sample\scode\scompleted\ssuccessfully."

    def update_kernel_args_and_reboot(self, list_of_args):
        """
        This method is to update the grub config file by using kernel

        :param list_of_args: list of the arguments want to update like intel iommu configuration

        """
        self._log.info('Inside update_kernel_args_and_reboot method')
        result_data = self._common_content_lib.execute_sut_cmd(
            "cat /proc/cmdline",
            "Verifying kernel Parameters grub config file",
            self._command_timeout)

        self._log.debug("Kernel Command Line Parameters:\n{}".format(result_data))

        if re.findall(self.REGEX_FOR_INTEL_IOMMU_ON_STR, "".join(result_data)):
            self._log.info("Kernel Parameters Already Set.")
        else:
            self._log.info("Setting the Kernel Parameters'{}'".format(" ".join(list_of_args)))
            result_data = self._common_content_lib.execute_sut_cmd(
                "grubby --update-kernel=ALL --args='{}'".format(" ".join(list_of_args)),
                "updating grub config file",
                self._command_timeout)
            self._log.debug("Updated the grub config file with stdout:\n{}".format(result_data))
            # rebooting the system
            self._common_content_lib.perform_os_reboot(self._reboot_time_out)

    def run_ptu_workload_on_host(self):
        """
             This function runs PTU  workload on host.
             :param : None
             :Runs the PTU workload for given RUN_TIME
             :return: None
        """

        try:
            self._log.info("Running PTU workload ...")

            ptu_workload = self._common_content_lib.execute_sut_cmd(self.PTU_WORKLOAD_COMMAND,
                                                                    "Running ptu work load",
                                                                    self._command_timeout,
                                                                    cmd_path="/root/ptu/")
            self._log.info(f"Ran PTU workload for {self.run_time} seconds...")

        except Exception as ex:
            log_error = "Error in running PTU workload Test"
            self._log.error(log_error)
            RuntimeError(ex)

    def run_mlc_workload_on_host(self):
        """
                    This function runs MLC  workload on host.
                    :param : None
                    :Runs the MLC workload for given RUN_TIME
                    :return: None
               """
        try:
            self._log.info("Running MLC workload ...")

            mlc_workload = self._common_content_lib.execute_sut_cmd(self.MLC_WORKLOAD_COMMAND,
                                                                    "Running MLC work load",
                                                                    self._command_timeout,
                                                                    cmd_path="/root/mlc_v3/Linux")
            self._log.info(f"Ran MLC workload for {self.run_time} seconds...")

        except Exception as ex:
            log_error = "error in MLC workload"
            self._log.error(log_error)
            RuntimeError(ex)

    def run_fio_workload_on_host(self):
        """
                :param: None
                :Runs the fio workload
                """
        try:

            self._log.info("Running FIO stress-workload ...")
            self._common_content_lib.execute_sut_cmd('yum install -y fio', "Installing", self._command_timeout,
                                                     cmd_path="/root/")
            # hdd_info = self.grep_linux_fio_hdd()
            hdd_info = self.grep_linux_fio_hdd()
            avail_engines = self._common_content_lib.execute_sut_cmd("fio --enghelp", "Available engines",
                                                                     self._command_timeout,
                                                                     cmd_path='/root/')

            command = self._common_content_lib.execute_sut_cmd(f'fio --filename=/dev/{hdd_info} --direct=1 '
                                                               f'--iodepth=1 --rw=randrw --rwmixread=70 '
                                                               f'--ioengine=posixaio --bs=4k --size=700G --numjobs=50 '
                                                               f'--runtime={self.run_time} --group_reporting '
                                                               f'--name=randrw70read4k --output=sde.txt',

                                                               "Installing",
                                                               self._command_timeout,
                                                               cmd_path="/root/")

            self._log.info(f"Ran FIO stress-workload for {self.run_time} seconds ...")

        except Exception as ex:

            log_error = "error in fio workload"
            self._log.error(log_error)
            RuntimeError(ex)

    def grep_linux_fio_hdd(self):
        os_installed_place = self._common_content_lib.execute_sut_cmd("df -h |grep -i '/boot/efi' |awk '{print $1}'",
                                                                      "Debugging", self._command_timeout,
                                                                      cmd_path="/root/")

        hdd_name = os_installed_place[5:]

        if 'sd' in hdd_name:

            out = self._common_content_lib.execute_sut_cmd('ls /dev/sd?', "SsD harddisk", self._command_timeout,
                                                           cmd_path="/root/")

        else:
            out = self._common_content_lib.execute_sut_cmd('ls /dev/nvme*n1', "NVM harddisk", self._command_timeout,
                                                           cmd_path="/root/")

        disk_line = out.split()

        '''
        for i in disk_line:
            if i in os_installed_place:
                disk_line.remove(i)
         '''
        disk_line = [i for i in disk_line if i not in os_installed_place]

        if not disk_line:
            log_error = "please add another hdd to test"
            self._log.error(log_error)
        else:
            disk_num = 0
            all_dev_list = []
            for line in disk_line:
                disk_num += 1
                line_name = line.split('/')
                disk_name = line_name[2]
                all_dev_list.append(disk_name)

            return all_dev_list[0]

    def execute_ssh_on_vm(self, cmd, command_string, port_number, timeout, path=None):
        """
        This method is used to execute the ssh commands and get the output
        :param cmd: command to be executed
        :param command_string: command being executed
        :param port_number: port number of the VM
        :timeout: command timeout
        """
        self._log.info("Executing {}".format(command_string))
        command_to_execute = self._os.execute(self.SSH_TO_PORT.format(port_number, cmd), timeout, path)
        return command_to_execute.stdout

    def unbind_devices(self, device):
        """
        This method is used to unbind devices from the SUT
        :param device: what device to be unbind, ex: qat, dsa, iax
        :return:
        """
        dbdf_list = None
        regex_unbind_verificarion = "Kernel driver in use: vfio-pci"
        if device == "QAT" or device == "qat":
            dbdf_list = self._vm_common.get_vf_device_dbdf_by_devid(devid=self.ACC_DEVICE_CODE[0],
                                                                    common_content_object=self._common_content_lib)
            bind_command = self.COMMAND_TO_BIND_DEVICES.format(self.ACC_DEVICE_CODE[0])
        elif device == "DLB" or device == "dlb":
            dbdf_list = self._vm_common.get_vf_device_dbdf_by_devid(devid=self.ACC_DEVICE_CODE[1],
                                                                    common_content_object=self._common_content_lib)
            bind_command = self.COMMAND_TO_BIND_DEVICES.format(self.ACC_DEVICE_CODE[1])
        elif device == "DSA" or device == "dsa":
            dbdf_list = self._vm_common.get_vf_device_dbdf_by_devid(devid=self.ACC_DEVICE_CODE[2],
                                                                    common_content_object=self._common_content_lib)
            bind_command = self.COMMAND_TO_BIND_DEVICES.format(self.ACC_DEVICE_CODE[2])
        elif device == "IAX" or device == "iax":
            dbdf_list = self._vm_common.get_vf_device_dbdf_by_devid(devid=self.ACC_DEVICE_CODE[3],
                                                                    common_content_object=self._common_content_lib)
            bind_command = self.COMMAND_TO_BIND_DEVICES.format(self.ACC_DEVICE_CODE[3])

        dbdf_device = dbdf_list[0]
        domain_value = dbdf_device.split(":")[0]
        bus_value = dbdf_device.split(":")[1]
        slot_value = dbdf_device.split(":")[2].split(".")[0]
        function_value = dbdf_device.split(":")[2].split(".")[1]
        unbind_command = self.COMMAND_TO_UNBIND_DEVICES.format(dbdf_device, domain_value, bus_value, slot_value,
                                                               function_value)
        self._vm_common.load_vfio_driver()
        self._common_content_lib.execute_sut_cmd(unbind_command, unbind_command, self._command_timeout)
        try:
            self._common_content_lib.execute_sut_cmd(bind_command, bind_command, self._command_timeout)
        except BaseException as e:
            self._vm_common.load_vfio_driver()
            self._common_content_lib.execute_sut_cmd(bind_command, bind_command, self._command_timeout)
        lspci_cmd = "lspci -s {} -k".format(dbdf_device)
        unbind_out = self._common_content_lib.execute_sut_cmd(lspci_cmd, lspci_cmd, self._command_timeout)
        if not re.findall(regex_unbind_verificarion, unbind_out.strip()):
            raise content_exceptions.TestError("{} not unbinded as expected".format(device))

    def spr_qat_installation(self, port_number, qat_folder_path, configure_spr_cmd=None):
        """
        This function execute SPR QAT Tool installation

        :param: qat_folder_path get the QAT folder path
        """
        if configure_spr_cmd:
            configure_cmd = configure_spr_cmd
        else:
            configure_cmd = r"./configure && make uninstall"
        cmd_to_install_dev_tools = 'echo y | yum group install "Development Tools"'
        make_cmd = "make all"
        make_install = "make install"
        make_samples_install = "make samples-install"
        find_cpa_sample_code_file = "./cpa_sample_code"
        qat_dependency_packages = "dnf install -y zlib-devel libnl3-devel boost-devel systemd-devel yasm lz4-devel " \
                                  "elfutils-libelf-devel yasm openssl-devel readline-devel kernel-spr-bkc-pc-devel"
        spr_work_around_cmd = ["export EXTRA_CXXFLAGS=-Wno-stringop-truncation",
                               "echo '/usr/local/lib' | sudo tee -a /etc/ld.so.conf", "mkdir -p /etc/default",
                               "mkdir -p /etc/udev/rules.d/", "mkdir -p /etc/ld.so.conf.d"]

        self._log.info("QAT Installtion in SPR platfrom")
        # Configuring the work around for SPR platform
        for cmd_item in spr_work_around_cmd:
            self._log.info("Executing work around command '{}' for QAT installation".format(cmd_item))
            self.execute_ssh_on_vm(cmd_item, cmd_item, port_number, self._command_timeout)

        self.execute_ssh_on_vm(cmd_to_install_dev_tools, "install development tools", port_number,
                               self._command_timeout)
        # Installing dependency packates
        command_result = self.execute_ssh_on_vm(qat_dependency_packages,
                                                "Dependency package installation", port_number,
                                                self._command_timeout)
        self._log.debug("Dependency packages are installed sucessfully {}".format(command_result))

        # Configuring the QAT Tool if installed already uninstall
        configure_command = self.execute_ssh_on_vm(self.ROOT_EXE_CMD_ON_VM.format(qat_folder_path, configure_cmd),
                                                   "run configure command", port_number,
                                                   self._command_timeout)

        self._log.debug("Configuring and Uninstall QAT Tool successfully if already installed {}".format
                        (configure_command))
        command_result_make = self.execute_ssh_on_vm(self.ROOT_EXE_CMD_ON_VM.format(qat_folder_path, make_cmd),
                                                     "run make command", port_number,
                                                     self._command_timeout)
        self._log.debug("Make installation for QAT Team {}".format(command_result_make))

        # make install  the QAT Tool
        command_result_make_install = self.execute_ssh_on_vm(self.ROOT_EXE_CMD_ON_VM.format(qat_folder_path,
                                                                                            make_install),
                                                             "run make install command",
                                                             port_number, self._command_timeout)
        self._log.debug("Install the QAT Tool in SUT {}".format(command_result_make_install))
        # make install samples the QAT Tool
        command_result_make_samples = self.execute_ssh_on_vm(self.ROOT_EXE_CMD_ON_VM.format(qat_folder_path,
                                                                                            make_samples_install),
                                                             "run make sample-install command", port_number,
                                                             self._command_timeout)
        self._log.debug("Install the Samples Tool with QAT {}".format(command_result_make_samples))

        # find cpa_sample_code file from the build folder
        cpa_sample_file = self.execute_ssh_on_vm(self.QAT_BUILD_PATH + find_cpa_sample_code_file,
                                                 "find the cpa_sample_code file in build path",
                                                 port_number, self._command_timeout)
        self._log.debug("Found cpa_sample_code file from build folder {} ".format(cpa_sample_file))
        if not cpa_sample_file:
            raise content_exceptions.TestFail("cpa_sample code file not found from build folder")
        self._log.info("QAT Tool installed successfully")

    def install_qat_on_vm(self, port_number, configure_spr_cmd=None):
        """
        This method installs QAT on sut by running below commands:
        1. tar -xvf ./QAT1.7.L.4.9.0-00008.tar.gz
        2. ./configure
        3. make
        4. make install
        :return: None
        """
        self._log.info("Installing QAT")
        qat_file_path = self._common_content_configuration.get_qat_file()
        cmd_to_install_dep_pack = "echo y | yum install -y elfutils-libelf-devel libudev-devel"
        cmd_to_install_dev_tools = 'yum groupinstall -y "Development Tools"'
        root_path_vm = "/root/"
        qat_folder_name = "QAT"
        configure_cmd = "./configure"
        make_command = "make"
        make_install_cmd = "make install"
        zip_file_path_vm = '/root/QAT/'

        install_dev_tools = self.execute_ssh_on_vm(cmd_to_install_dev_tools, "Install development tools", port_number,
                                                   self._command_timeout)
        self._log.debug("Installation of dependency packages is done successfully with output '{}'"
                        .format(install_dev_tools))
        qat_host_path = self._artifactory_obj.download_tool_to_automation_tool_folder(qat_file_path)
        self._common_content_lib.copy_zip_file_to_linux_sut(qat_folder_name, qat_host_path)
        self.create_folders_in_vm(qat_folder_name, qat_file_path, port_number)
        self.execute_ssh_on_vm("yum install sshpass", "install sshpass in VM", port_number,
                               self._command_timeout)
        host_ip_add = self._common_content_lib.execute_sut_cmd("hostname -i", "getting ip for hostname",
                                                               self._command_timeout)
        copy_cmd = self.COPY_FILE_TO_VM_FROM_SUT.format(host_ip_add.strip(), qat_folder_name, root_path_vm)
        # copying file to Linux SUT in root from host
        self.execute_ssh_on_vm(copy_cmd, "copy QAT to VM", port_number, self._command_timeout)
        self._log.info("QAT file is extracted and copied to SUT path {}".format(zip_file_path_vm))
        # Install QAT tool in EGS Platform
        command_result = self.execute_ssh_on_vm(cmd_to_install_dep_pack, "Install require tools", port_number,
                                                self._command_timeout)
        self._log.debug("Installation of dependency packages is done successfully with output '{}'"
                        .format(command_result))
        if self._platform == ProductFamilies.SPR:
            self.spr_qat_installation(port_number, zip_file_path_vm, configure_spr_cmd=configure_spr_cmd)
        else:
            # Installing QAT Tool for other platforms
            # Installing Development tools
            command_result = self.execute_ssh_on_vm(cmd_to_install_dev_tools, "Install development tools", port_number,
                                                    self._command_timeout)
            self._log.debug("Installation of 'Development Tools' is done successfully with output '{}'"
                            .format(command_result))
            # Configuring the QAT Tool
            command_result = self.execute_ssh_on_vm(zip_file_path_vm + configure_cmd, "run configure command",
                                                    port_number, self._command_timeout)
            self._log.debug("Configuring the QAT Tool file successfully {}".format(command_result))
            # make and compiling the files in QAT Tool folder
            command_result = self.execute_ssh_on_vm(make_command, "run make command", port_number,
                                                    self._command_timeout, zip_file_path_vm)
            self._log.debug("make and compiling the files QAT Tool folder {}".format(command_result))
            # make install command
            command_result = self.execute_ssh_on_vm(make_install_cmd, "run make Install command", port_number,
                                                    self._command_timeout, zip_file_path_vm)
            self._log.debug("Installation of QAT is done successfully {}".format(command_result))

    def create_folders_in_vm(self, sut_folder_name, host_zip_file_path, port_number, dont_delete=None):
        """
        copy zip file to Linux SUT and unzip

        :param : sut_folder_name : name of the folder in SUT
        :param : host_zip_file_path : name of the zip file in Host
        :return: The extracted folder path in SUT
        """
        if dont_delete is None:
            self.execute_ssh_on_vm("rm -rf {}".format(sut_folder_name), "Deleting {} folder in VM".format
            (sut_folder_name), port_number, self._command_timeout, self.ROOT)

            self.execute_ssh_on_vm("mkdir -p {}".format(sut_folder_name), "Creating {} folder in VM".format
            (sut_folder_name), port_number, self._command_timeout, self.ROOT)
        else:
            sut_folder_name_find = self.execute_ssh_on_vm \
                ("find / -type d -samefile {}".format(sut_folder_name), "find the sut folder path", port_number,
                 self._command_timeout, self.ROOT)
            self._log.debug("find sut folder path {} result {}".format(sut_folder_name, sut_folder_name_find))
            if sut_folder_name_find == "" or \
                    len(re.findall(r'.*No such file or directory.*', sut_folder_name_find, re.IGNORECASE)) > 0:
                self.execute_ssh_on_vm("mkdir -p '{}'".format(sut_folder_name), "To Create a folder", port_number,
                                       self._command_timeout, self.ROOT)

    def create_qemu_vm(self, vm_name, port_number, accelerator_device=None):
        """
        This method is used to create the VM using .img file
        :return:
        """
        self._log.info("Getting Accelerator device for creating VM")
        if accelerator_device is not None:
            devices = " ".join([str(dev) for dev in accelerator_device])
            create_vm = self.CREATE_VM_CMD.format(vm_name, self.CLONED_PATH.format(vm_name), port_number) + devices
        else:
            create_vm = self.CREATE_VM_CMD.format(vm_name, self.CLONED_PATH.format(vm_name), port_number)
        self._os.execute_async(create_vm)
        time.sleep(10)
        verify_vm = self.execute_ssh_on_vm("ls", "verify vm launch ", port_number, self._command_timeout)
        if re.findall(self.REGEX_VM_FAIL, verify_vm.strip()):
            raise content_exceptions.TestFail("Failed to launch VM with error {}".format(verify_vm.strip()))

    def verify_vm_functionality(self, vm_name, port_number):
        """
        This Method is used to check VM funcationality
        :param vm_name: Name of the VM
        :param port_number: Port Number of the VM
        :return: None
        """
        ls_cmd = self.execute_ssh_on_vm("ls", "verify vm cmd", port_number, self._command_timeout)
        if re.findall(self.REGEX_VM_FAIL, ls_cmd.strip()):
            self.start_vm(vm_name, port_number)
        ls_cmd = self.execute_ssh_on_vm("ls", "verify vm cmd", port_number, self._command_timeout)
        if re.findall(self.REGEX_VM_FAIL, ls_cmd.strip()):
            self._log.info("{} VM not started".format(vm_name))
            raise content_exceptions.TestFail("Failed to start {} VM".format(vm_name))
        self._log.info("Successfully started {} VM".format(vm_name))

    def start_vm(self, vm_name, port_number):
        """
        This Method is used to start the VM
        """
        self.CREATE_VM_CMD.format(vm_name, self.CLONED_PATH.format(vm_name), port_number)
        self._log.info("Successfully started {} VM".format(vm_name))

    def perform_reboot_on_vm(self, vm_name, port_number):
        """
        Performing reboot on the VM
        """
        self.execute_ssh_on_vm("reboot", "performing reboot", port_number, self._command_timeout)
        time.sleep(10)
        ls_cmd = self.execute_ssh_on_vm("ls", "verify vm cmd", port_number, self._command_timeout)
        if re.findall(self.REGEX_VM_FAIL, ls_cmd.strip()):
            self._log.info("{} VM not started".format(vm_name))
            raise content_exceptions.TestFail("Failed to start {} VM".format(vm_name))
        self._log.info("Successfully started {} VM".format(vm_name))

    def update_kernel_args_and_reboot_on_vm(self, vm_name, list_of_args, port_number):
        """
        This method is to update the grub config file by using kernel

        :param list_of_args: list of the arguments want to update like intel iommu configuration
        :param port_number: port  number for VM

        """
        self._log.info('Inside update_kernel_args_and_reboot method')
        result_data = self.execute_ssh_on_vm("cat /proc/cmdline",
                                             "Verifying kernel Parameters grub config file",
                                             port_number, self._command_timeout)

        self._log.debug("Kernel Command Line Parameters:\n{}".format(result_data))

        if re.findall(self.REGEX_FOR_INTEL_IOMMU_ON_STR_VM, "".join(result_data)):
            self._log.info("Kernel Parameters Already Set.")
        else:
            self._log.info("Setting the Kernel Parameters'{}'".format(" ".join(list_of_args)))
            result_data = self.execute_ssh_on_vm(
                "grubby --update-kernel=ALL --args='{}'".format(" ".join(list_of_args)),
                "updating grub config file", port_number, self._command_timeout)
            self._log.debug("Updated the grub config file with stdout:\n{}".format(result_data))
            # rebooting the system
            self.execute_ssh_on_vm("shutdown now", "shutting down VM", port_number, self._command_timeout)

    def install_hqm_driver_on_vm(self, port_number):
        """
        HQM Driver Installation
        1. Copy the .txz file to sut and extract it
        2. Use make command to compile in dlb folder
        3. Use make command to compile in libdlb folder
        4. insmod the dlb2.ko file
        raise: contents_exception.TestFail if dlb2.ko kernel file not available
        """
        dpdk_patch_file_name = self._common_content_configuration.get_dpdk_patch_file()
        self._log.info("Install HQM Driver on the VM")
        hqm_file_name = self._common_content_configuration.get_hqm_file()
        dpdk_file_name = self._common_content_configuration.get_dpdk_file()
        hqm_folder_name = "HQM"
        dpdk_name, version = self._install_collateral.get_name_version(dpdk_file_name)
        dpdk_full_folder_name = dpdk_name + '-' + 'stable' + '-' + version
        dpdk_folder_name = "HQM/dpdk"
        make_command = " make"
        find_dlb_dir_path = "find $(pwd) -type d -name 'dlb2' 2>/dev/null | grep 'driver/dlb2'"
        grep_dlb_driver = "lsmod | grep dlb"
        expected_dlb_val = "dlb2"
        insmod_cmd = " insmod dlb2.ko"
        patch_cmd = "cd /root/HQM/dpdk/{};patch -Np1 < /root/HQM/dpdk/{};".format(dpdk_full_folder_name,
                                                                                  dpdk_patch_file_name)
        export_cmd = "cd /root/HQM/dpdk/{};" \
                     "echo y | yum install -y meson;" \
                     "export DPDK_DIR=/root/HQM/dpdk/{}/;" \
                     "export RTE_SDK=$DPDK_DIR;" \
                     "export RTE_TARGET=installdir;".format(dpdk_full_folder_name.strip(),
                                                            dpdk_full_folder_name.strip())
        # "meson setup --prefix $RTE_SDK/$RTE_TARGET builddir;" \
        # "ninja -C builddir "
        hqm_host_file_path = (self._artifactory_obj.download_tool_to_automation_tool_folder(hqm_file_name)).strip()
        dpdk_host_file_path = (self._artifactory_obj.download_tool_to_automation_tool_folder(dpdk_file_name)).strip()
        self.execute_ssh_on_vm("whoami;sync;", "executing sync command", port_number, self._command_timeout,
                               path=self.ROOT)
        # Remove HQM file if it already exists.
        self.execute_ssh_on_vm("find / -type f -name HQM 2>/dev/null -exec rm {} \;", "Removing the HQM file",
                               port_number, self._command_timeout, self.ROOT)
        self.execute_ssh_on_vm("find / -type d -name HQM 2>/dev/null -exec rm -r {} \;", "Removing the HQM file",
                               port_number, self._command_timeout, self.ROOT)
        self.execute_ssh_on_vm("mkdir -p '{}'".format(hqm_folder_name), "To Create a HQM folder",
                               port_number, self._command_timeout, self.ROOT)
        # Copy the HQM file to SUT
        sut_folder_path = self._common_content_lib.copy_zip_file_to_linux_sut(hqm_folder_name, hqm_host_file_path,
                                                                              dont_delete="True")
        sut_folder_path = sut_folder_path.strip()
        # Copy the dpdk file to SUT
        dpdk_folder_path = self._common_content_lib.copy_zip_file_to_linux_sut(dpdk_folder_name, dpdk_host_file_path,
                                                                               dont_delete="True")
        dpdk_folder_path = dpdk_folder_path.strip()
        #self.create_folders_in_vm(sut_folder_path, hqm_host_file_path, port_number)
        host_ip_add = self._common_content_lib.execute_sut_cmd("hostname -I", "getting ip for hostname",
                                                               self._command_timeout)
        copy_cmd = self.COPY_FILE_TO_VM_FROM_SUT.format(host_ip_add.strip(), hqm_folder_name, self.ROOT)
        # copying file to Linux SUT in root from host
        self.execute_ssh_on_vm(copy_cmd, "Copy HQM folder to VM from Host", port_number, self._command_timeout)
        self._log.debug("HQM file is extracted and copied to VM")
        hqm_driver_kernel_file_path = self.execute_ssh_on_vm(find_dlb_dir_path, "find the dlb2 kernel file",
                                                             port_number, self._command_timeout)
        self.execute_ssh_on_vm(self.ROOT_EXE_CMD_ON_VM.format(hqm_driver_kernel_file_path.strip(), make_command),
                               "running make command", port_number, self._command_timeout)
        self.execute_ssh_on_vm(self.ROOT_EXE_CMD_ON_VM.format(hqm_driver_kernel_file_path.strip(), insmod_cmd),
                               "running insmod command", port_number, self._command_timeout)
        lsmod_out = self.execute_ssh_on_vm(grep_dlb_driver, "get running devices", port_number, self._command_timeout)
        if expected_dlb_val not in lsmod_out.strip():
            raise content_exceptions.TestFail('Expected output not in output,insmod failure')
        self._log.debug("dlb driver output {}".format(lsmod_out))
        '''
        self._common_content_lib.copy_zip_file_to_linux_sut(self.ROOT, dpdk_host_file_path, dont_delete=True)
        copy_cmd = self.COPY_FILE_TO_VM_FROM_SUT.format(host_ip_add.strip(), dpdk_full_folder_name, self.ROOT)
        self.execute_ssh_on_vm(copy_cmd, "install sshpass in VM", port_number, self._command_timeout)

        # execute patch cmd
        hqm_driver_dpdk_path = self.execute_ssh_on_vm(patch_cmd, "executing patch command", port_number,
                                                      self._command_timeout, dpdk_folder_path)
        hqm_driver_dpdk_path = hqm_driver_dpdk_path.strip()
        self._log.debug("HQM drivers dlb path {}".format(hqm_driver_dpdk_path))
        '''
        # export cmd
        hqm_driver_dpdk_path = self.execute_ssh_on_vm(export_cmd, "executing export command", port_number,
                                                      self._command_timeout, dpdk_folder_path)
        hqm_driver_dpdk_path = hqm_driver_dpdk_path.strip()
        self._log.debug("HQM drivers dlb path {}".format(hqm_driver_dpdk_path))
        self.execute_ssh_on_vm("sync", "executing sync command", port_number, self._command_timeout, self.ROOT)
        cmd_output2 = self.execute_ssh_on_vm("{} {}".format(insmod_cmd, hqm_driver_kernel_file_path.strip()),
                                             "insmod the dlb2 driver", port_number, self._command_timeout)
        self._log.debug(cmd_output2)
        # grep dlb driver file
        hqm_driver_kernel = self.execute_ssh_on_vm(grep_dlb_driver, "grep the dlb2 kernel file",
                                                   port_number, self._command_timeout, sut_folder_path)
        self._log.debug("dpdk file is extracted and copied to dpdk path in HQM {}".format(dpdk_folder_path))
        self._log.info("dpdk installed successfully")

    def execute_cpa_sample(self, port_number, cpa_sample_code, run_time=None):
        """
        This Method is used to to run sample code on QAT in VM
        """
        if (run_time != None):
            self._log.info("Running QAT workload...")
            cnt = 0
            com_time = time.perf_counter() + self.run_time
            while time.perf_counter() < com_time:
                cnt += 1
                qat_test = self.execute_ssh_on_vm(self.ROOT_EXE_CMD_ON_VM.format(self.QAT_BUILD_PATH, cpa_sample_code),
                                                  "find the cpa_sample_code file in build path", port_number,
                                                  self._command_timeout)
                time.sleep(1)
                if re.findall(self.REGEX_FOR_QAT_WORKLOAD_SUCCESS, "".join(qat_test)):
                    self._log.info("QAT workload run Successfully in loop: {}".format(cnt))
                else:
                    self._log.error("QAT workload Failed in loop: {}".format(cnt))
            self._log.info(f"Ran QAT stress-workload for {self.run_time} seconds ")

        else:
            print('In execute cpa sample code method: ',
                  self.ROOT_EXE_CMD_ON_VM.format(self.QAT_BUILD_PATH, cpa_sample_code))
            cpa_sample_file = self.execute_ssh_on_vm(
                self.ROOT_EXE_CMD_ON_VM.format(self.QAT_BUILD_PATH, cpa_sample_code),
                "find the cpa_sample_code file in build path", port_number,
                self._command_timeout)
            print("Output of cpa_sample_code execution: ", cpa_sample_file)
            self._log.debug("Executing cpa_sample_code file from build folder {} ".format(cpa_sample_file))
            if not cpa_sample_file:
                raise content_exceptions.TestFail("cpa_sample code file not found from build folder")
            self._log.info("CPA sample run successful")

    def execute_dlb(self, port_number, run_time=None):
        """
        This method is used to run dlb workload
        """
        huge_pages_dir = "/mnt/hugepages"
        mount_point_huge_pages = "mount -t hugetlbfs nodev {}".format(huge_pages_dir)
        kernel_mm_hugepages = "echo 2048 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages"
        build_app_path = "find $(pwd) -type d -name 'app' 2>/dev/null | grep 'builddir/app'"
        dlb_execution_cmd = "./dpdk-test-eventdev --vdev=dlb2_event -- --test=order_queue --plcores=3 --wlcore=4,5" \
                            " --nb_flows=64 --nb_pkts=100000000;"

        self.execute_ssh_on_vm("mkdir -p " + huge_pages_dir, huge_pages_dir, port_number,
                               self._command_timeout)

        defg = self.execute_ssh_on_vm(mount_point_huge_pages, mount_point_huge_pages, port_number,
                                      self._command_timeout)
        self.execute_ssh_on_vm(kernel_mm_hugepages, kernel_mm_hugepages, port_number,
                               self._command_timeout)
        build_path = self.execute_ssh_on_vm(build_app_path, build_app_path, port_number,
                                            self._command_timeout)
        if (run_time != None):
            cnt = 0
            com_time = time.perf_counter() + self.run_time
            while time.perf_counter() < com_time:
                cnt += 1
                dlb_test = self.execute_ssh_on_vm(self.ROOT_EXE_CMD_ON_VM.format(build_path.strip(),
                                                                                 dlb_execution_cmd),
                                                  self.ROOT_EXE_CMD_ON_VM.format(build_path.strip(), dlb_execution_cmd),
                                                  port_number, self._command_timeout)
                time.sleep(1)
                if re.findall(self.REGEX_FOR_DLB_WORKLOAD_SUCCESS, "".join(dlb_test)):
                    self._log.info("DLB workload run Successfully in loop: {}".format(cnt))
                else:
                    self._log.error("DLB workload Failed in loop: {}".format(cnt))
            self._log.info(f"Ran DLB workload for {self.run_time} seconds ...")

        else:
            dlb_exe_output = self.execute_ssh_on_vm(self.ROOT_EXE_CMD_ON_VM.format(build_path.strip(),
                                                                                   dlb_execution_cmd),
                                                    self.ROOT_EXE_CMD_ON_VM.format(build_path.strip(),
                                                                                   dlb_execution_cmd),
                                                    port_number, self._command_timeout)
            print('dlb_exe_output', dlb_exe_output)
            self._log.debug("Execution Output for DLB: {}".format(dlb_exe_output))

    def get_vfio_devices_vm(self, accel_devices, required_length=None):
        """
        This Method is used to get the Devices for attaching to VM
        :param accel_devices: type of devices
        :param required_length: len of devices
        """
        for acc in accel_devices:
            device_list = self._vm_common.get_vf_device_dbdf_by_devid(acc)
            for dev in device_list[:required_length]:
                self.ACCELERATOR_DEVICES_VM.append(self.VFI_DEVICES.format(dev[5:]))
        return self.ACCELERATOR_DEVICES_VM

    def run_dsa_workload_on_vm(self, device_type, port_number):
        """
        This function runs dsa workload on VM.

        :param : vm_os_obj : VM OS object

        :return: None
        """
        self._log.info("Running DMA test")
        configure_wq = "./Guest_Passthrough_Randomize_{}_Conf.sh -kcD".format(device_type)
        cmd_output = self.execute_ssh_on_vm(self.ACCEL_RANDOM_CONFIG_PATH.format(configure_wq),
                                            self.ACCEL_RANDOM_CONFIG_PATH.format(configure_wq), port_number,
                                            self._command_timeout)
        self._log.info("Configuring workqueues {}".format(cmd_output))
        cmd_dma = "./Guest_Passthrough_Randomize_{}_Conf.sh -i 100 -j 2".format(device_type)
        cmd_output = self.execute_ssh_on_vm(self.ACCEL_RANDOM_CONFIG_PATH.format(cmd_dma),
                                            self.ACCEL_RANDOM_CONFIG_PATH.format(cmd_dma), port_number,
                                            self._command_timeout)
        self._log.info("Running DSA workload on vm and output is {}".format(cmd_output))
        cmd_check_error = "journalctl --dmesg | grep error"
        cmd_opt = self.execute_ssh_on_vm(cmd_check_error, cmd_check_error, port_number,
                                         self._command_timeout)
        if len(cmd_opt) == 0:
            self._log.info("No errors found")
        else:
            raise RuntimeError("Errors found after running workload")

    def run_mdev_workload_on_vm(self, device_type, config_cmd, wq_cmd, port_number):
        """
        This function runs IAX workload on VM.
        :param : vm_os_obj : VM OS object
        :return: None
        """
        self._log.info("Running DMA test")
        configure_wq = "./Guest_Mdev_Randomize_{}_Conf.sh {}".format(device_type, config_cmd)
        cmd_output = self.execute_ssh_on_vm(self.ACCEL_RANDOM_CONFIG_PATH.format(configure_wq),
                                            self.ACCEL_RANDOM_CONFIG_PATH.format(configure_wq), port_number,
                                            self._command_timeout)
        self._log.info("Configuring workqueues {}".format(cmd_output))
        cmd_dma = "./Guest_Mdev_Randomize_{}_Conf.sh {}".format(device_type, wq_cmd)
        cmd_output = self.execute_ssh_on_vm(self.ACCEL_RANDOM_CONFIG_PATH.format(cmd_dma),
                                            self.ACCEL_RANDOM_CONFIG_PATH.format(cmd_dma), port_number,
                                            self._command_timeout)
        self._log.info("Running DSA workload on vm and output is {}".format(cmd_output))
        cmd_check_error = "journalctl --dmesg | grep error"
        cmd_opt = self.execute_ssh_on_vm(cmd_check_error, cmd_check_error, port_number,
                                         self._command_timeout)
        if len(cmd_opt) == 0:
            self._log.info("No errors found")
        else:
            raise RuntimeError("Errors found after running workload")

    def run_dsa_iax_workload_on_vm(self, device_type, config_cmd, wq_cmd, port_number, run_time=None):
        """
        This function runs IAX and DSA workload on VM.
        :param : vm_os_obj : VM OS object
        :return: None
        """
        configure_wq = "./Guest_Mdev_Randomize_{}_Conf.sh {}".format(device_type, config_cmd)

        if (run_time !=None):
            cnt = 0
            com_time = time.perf_counter() + self.run_time
            while time.perf_counter() < com_time:
                cnt += 1
                cmd_output = self.execute_ssh_on_vm(self.ACCEL_RANDOM_CONFIG_PATH.format(configure_wq),
                                                    self.ACCEL_RANDOM_CONFIG_PATH.format(configure_wq), port_number,
                                                    self._command_timeout)
                self._log.info("Configuring workqueues {}".format(cmd_output))
                cmd_dma = "./Guest_Mdev_Randomize_{}_Conf.sh {}".format(device_type, wq_cmd)
                cmd_output = self.execute_ssh_on_vm(self.ACCEL_RANDOM_CONFIG_PATH.format(cmd_dma),
                                                    self.ACCEL_RANDOM_CONFIG_PATH.format(cmd_dma), port_number,
                                                    self._command_timeout)
                self._log.info("Running DSA workload on vm and output is {}".format(cmd_output))
                cmd_check_error = "journalctl --dmesg | grep error"
                cmd_opt = self.execute_ssh_on_vm(cmd_check_error, cmd_check_error, port_number,
                                                 self._command_timeout)
                if len(cmd_opt) == 0:
                    self._log.info("Workload passed in loop {}".format(cnt))
                else:
                    self._log.info("Errors found after running workload in loop {}".format(cnt))

        else:
            cmd_output = self.execute_ssh_on_vm(self.ACCEL_RANDOM_CONFIG_PATH.format(configure_wq),
                                                self.ACCEL_RANDOM_CONFIG_PATH.format(configure_wq), port_number,
                                                self._command_timeout)
            self._log.info("Configuring workqueues {}".format(cmd_output))
            cmd_dma = "./Guest_Mdev_Randomize_{}_Conf.sh {}".format(device_type, wq_cmd)
            cmd_output = self.execute_ssh_on_vm(self.ACCEL_RANDOM_CONFIG_PATH.format(cmd_dma),
                                                self.ACCEL_RANDOM_CONFIG_PATH.format(cmd_dma), port_number,
                                                self._command_timeout)
            self._log.info("Running DSA workload on vm and output is {}".format(cmd_output))
            cmd_check_error = "journalctl --dmesg | grep error"
            cmd_opt = self.execute_ssh_on_vm(cmd_check_error, cmd_check_error, port_number,
                                             self._command_timeout)
            if len(cmd_opt) == 0:
                self._log.info("Workload passed")
            else:
                raise RuntimeError("Errors found after running workload")

    def load_mdev_vfio_driver(self):
        """
        This method is used for loading the mdev devices in Host
        """
        mdev_cmd = "modprobe mdev"
        self._vm_common.load_vfio_driver()
        self._common_content_lib.execute_sut_cmd(mdev_cmd, mdev_cmd, self._command_timeout)

    def get_uuid(self, type_of_device):
        """
        Get the UUID for for the particular device
        :return: single UUID
        """
        if type_of_device == "IAX":
            accel_config_cmd = "./Setup_Randomize_IAX_Conf.sh -maD -F 1 -w 15"
            uuid_cmd = "accel-config create-mdev iax1 1dwq"
        elif type_of_device == 'DSA':
            accel_config_cmd = "./Setup_Randomize_DSA_Conf.sh -maD -F 1 -w 15"
            uuid_cmd = "accel-config create-mdev dsa0 1dwq"

        self.load_mdev_vfio_driver()
        enable_wq = self._os.execute(accel_config_cmd, self._command_timeout,
                                     self.ACCEL_RANDOM_CONFIG_PATH.format(""))
        self._log.debug(enable_wq.stdout)
        uuid = self._os.execute(uuid_cmd, self._command_timeout, self.ACCEL_RANDOM_CONFIG_PATH.format(""))
        uuid = uuid.stdout.split(":")[1].strip()
        return uuid

    def run_fisher_tool_on_vm(self, port_number, type_of_error, workload):
        """
        This method is used to install and run_fisher_tools fisher tool on VM
        :param port_number: port number of VM
        :param workload: workload to be run_fisher_tools on VM
        :param type_of_error: config of the workload to be run_fisher_tools
        """
        workload_command = None
        self._log.info("Running Fisher tool...")
        if workload == 'DLB':
            dpdk_file_name = os.path.split(self.dpdk_file_path)[-1].strip()
            dpdk_name, version = self._install_collateral.get_name_version(dpdk_file_name)
            dpdk_full_folder_name = dpdk_name + '-' + 'stable' + '-' + version
            workload_command = "/root/HQM/dpdk/{}/builddir/app/./dpdk-test-eventdev -c 0xf --vdev=dlb2_event -- " \
                               "--test=order_queue --plcores=1 --wlcore=2,3 --nb_flows=64".format(dpdk_full_folder_name)
        elif workload == 'DSA':
            workload_command = "./Guest_Mdev_Randomize_DSA_Conf.sh -o 0x3"
        elif workload == 'IAX':
            workload_command = "./Guest_Mdev_Randomize_IAX_Conf.sh -r"
        elif workload == 'QAT':
            workload_command ="/root/QAT/build/./cpa_sample_code"

        self._log.info('Workload command: {}'.format(workload_command))

        fisher_workload = f"'{workload_command}'"

        if self.run_time < 60:
            fisher_tool_run_time = "{}s".format(int(self.run_time))
        elif self.run_time < 3600:
            fisher_tool_run_time = "{}m".format(int(self.run_time/60))
        else:
            fisher_tool_run_time = "{}h".format(int(self.run_time/3600))

        if type_of_error == "correctable":
            fisher_command = self.WORKLOAD_RUNTIME_CMD.format(fisher_workload, fisher_tool_run_time,
                                                              self._common_content_lib.get_host_ip(),
                                                              port_number)
        else:
            self._log.info("not yet implemented for uncorrectable injection")

        self._log.info('Fisher command: {}'.format(fisher_command))

        if (workload == 'DSA') or (workload == 'IAX'):
            self._log.info("Running DSA/IAX workload inside 'accel-random-config-and-test'")
            run_fisher_tools = self.execute_ssh_on_vm(self.ROOT_EXE_CMD_ON_VM.format(self.ACCEL_RANDOM_CONFIG_PATH
                                                                                     .format(""),
                                                                                     fisher_command),
                                                      fisher_command, port_number, self._command_timeout)
            fisher_output = self.execute_ssh_on_vm("cat {}".format(self.ACCEL_RANDOM_CONFIG_PATH.format("fisher_*")),
                                               "reading fisher output", port_number, self._command_timeout)
        elif (workload == 'DLB') or (workload == 'QAT'):
            self._log.info("Running DLB/QAT workload in 'root'")
            run_fisher_tools = self.execute_ssh_on_vm(self.ROOT_EXE_CMD_ON_VM.format(self.ROOT
                                                                                     .format(""),
                                                                                     fisher_command),
                                                      fisher_command, port_number, self._command_timeout)
            fisher_output = self.execute_ssh_on_vm("cat {}".format(self.ROOT.format("fisher_*")),
                                               "reading fisher output", port_number, self._command_timeout)

        self._log.info(fisher_output)

        if type_of_error =="uncorrectable":
            REGEX_FISHER= "{}{} - FAIL = 0".format(self.REGEX_FOR_FISHER_TOOL_SUCCESS, self.num_of_cycles)
        else:
            cur_num_of_cycles = len(re.findall(self.REGEX_FOR_FISHER_TOOL_SUCCESS, fisher_output)) - 1
            REGEX_FISHER= "{}{} - FAIL = 0".format(self.REGEX_FOR_FISHER_TOOL_SUCCESS, cur_num_of_cycles)

        if re.findall(REGEX_FISHER, fisher_output):
            self._log.info("The error injection ran successfully for the given workload.")
        else:
            raise content_exceptions.TestFail("Error injection could not occur through fisher tool.")

    def get_qat_uuid(self):
        '''
        # Method returns the qat uuid
        '''
        qat_uuid_cmd = "/root/QAT/build/./vqat_ctl create 0000:6b:00.0 sym | cut -d'=' -f2"
        qat_uuid = self._common_content_lib.execute_sut_cmd(qat_uuid_cmd, qat_uuid_cmd, self._command_timeout,
                                                            self.ROOT)
        return qat_uuid.strip()

    def get_iax_uuid(self):
        '''
        # Method returns the iax uuid
        '''
        iax_uuid_cmd = "accel-config create-mdev dsa$((2*1)) 1dwq | cut -d':' -f2"
        iax_uuid = self._common_content_lib.execute_sut_cmd(iax_uuid_cmd, iax_uuid_cmd, self._command_timeout,
                                                            self.ROOT)
        return iax_uuid.strip()

    def get_dsa_uuid(self):
        '''
        # Method returns the dsa uuid
        '''
        dsa_uuid_cmd = "accel-config create-mdev iax$(((2*1)+1)) 1dwq | cut -d':' -f2"
        dsa_uuid = self._common_content_lib.execute_sut_cmd(dsa_uuid_cmd, dsa_uuid_cmd, self._command_timeout,
                                                            self.ROOT)
        print('dsa_uuid', dsa_uuid)
        return dsa_uuid.strip()

    def get_dlb_uuid(self):
        '''
        # Method returns the dlb uuid
          Check if insmod command has inserted dlb2 folder in /sys/class/ directory
          If not , below commands will not work
        '''
        dlb_uuid_cmd = 'export SYSFS_PATH=/sys/class/dlb2/dlb0;export UUID=$(uuidgen);echo "$UUID";'
        dlb_uuid = self._common_content_lib.execute_sut_cmd(dlb_uuid_cmd, dlb_uuid_cmd, self._command_timeout,
                                                            self.ROOT)
        MEM_DIV_CMD = "export MDEV_PATH=/sys/bus/mdev/devices/{0}/dlb2_mdev/;echo {0} > /sys/class/dlb2/dlb0/device/mdev_supported_types/dlb2-dlb/create;" \
                      "echo 128 > $MDEV_PATH/num_atomic_inflights;echo 256 > $MDEV_PATH/num_dir_credits;echo 4 > $MDEV_PATH/num_dir_ports;echo 128 > $MDEV_PATH/num_hist_list_entries;" \
                      "echo 512 > $MDEV_PATH/num_ldb_credits;echo 4 > $MDEV_PATH/num_ldb_ports;echo 2 > $MDEV_PATH/num_ldb_queues;echo 2 > $MDEV_PATH/num_sched_domains;" \
                      "echo 1 > $MDEV_PATH/num_sn0_slots;echo 1 > $MDEV_PATH/num_sn1_slots;".format(dlb_uuid.strip())

        self._common_content_lib.execute_sut_cmd(MEM_DIV_CMD, MEM_DIV_CMD, self._command_timeout, self.ROOT)
        return dlb_uuid.strip()

    def check_interrupt_from_driver_in_VM(self, port_number, workload, type_of_check):
        if workload == 'QAT':
            cmd = "cat /proc/interrupts | grep -i qat | fold -w 150 > {}.txt".format(type_of_check)
        elif workload == 'DLB':
            cmd = "cat /proc/interrupts | grep -i dlb | fold -w 150 > {}.txt".format(type_of_check)
        elif workload == 'DSA':
            cmd = "cat /proc/interrupts | grep -i idxd | fold -w 150 > {}.txt".format(type_of_check)
        elif workload == 'IAX':
            cmd = "cat /proc/interrupts | grep -i idxd | fold -w 150 > {}.txt".format(type_of_check)

        self.execute_ssh_on_vm(cmd, cmd, port_number, self._command_timeout, self.ROOT)

        if type_of_check == 'post':
            cmd = 'diff pre.txt post.txt'
            cmd_output = self.execute_ssh_on_vm(cmd, cmd, port_number, self._command_timeout, self.ROOT)
            rm_cmd = 'rm -rf pre.txt post.txt'
            self.execute_ssh_on_vm(rm_cmd, rm_cmd, port_number, self._command_timeout, self.ROOT)
            if not cmd_output:
                raise content_exceptions.TestFail("Interrupts found from {} driver in VM.".format(workload))
