import os
#from exsi import *
from dtaf_core.lib.tklib.basic.log import logger
from dtaf_core.lib.tklib.basic.testcase import Case
from dtaf_core.lib.tklib.basic.const import *
from dtaf_core.lib.tklib.steps_lib.os_scene import OperationSystem
from dtaf_core.lib.tklib.basic.config import LOG_PATH
from src.virtualization.lib.rich_virtual import *
# from tkconfig import sut_tool
from dtaf_core.lib.tklib.auto_api import *

QATZIP_H = sut_tool('QATZIP_H')
QATZIP_SCRIPT_H = sut_tool('QATZIP_SCRIPT_H')
OPENSSL_H = sut_tool('OPENSSL_H')
QAT_ENGINE_H = sut_tool('QAT_ENGINE_H')
LINPACK_H = sut_tool('LINPACK_H')
QAT_DRIVER_H = sut_tool('QAT_DRIVER_H')
DLB_DRIVER_H = sut_tool('DLB_DRIVER_H')
DPDK_DRIVER_H =sut_tool('DPDK_DRIVER_H')
DSA_H = sut_tool('DSA_H')
STRESSAPPTEST_H = sut_tool('STRESSAPPTEST_H')
QAT_ASYM_H = sut_tool('QAT_ASYM_H')
QAT_SYM_H = sut_tool('QAT_SYM_H')
QAT_TEST_SCRIPT_H = sut_tool('QAT_TEST_SCRIPT_H')
PTU_H = sut_tool('PTU_H')
MLC_H = sut_tool('MLC_H')
SAMPLE_CODE_H = sut_tool('SAMPLE_CODE_H')
MEGA_CONF_H = sut_tool('MEGA_CONF_H')
MEGA_SCRIPT_H = sut_tool('MEGA_SCRIPT_H')
KERNEL_HEADER_H = sut_tool('KERNEL_HEADER_H')
KERNEL_DEVEL_H = sut_tool('KERNEL_DEVEL_H')
KERNEL_INTERNAL_H = sut_tool('KERNEL_INTERNAL_H')
PPEXPECT_H = sut_tool('PPEXPECT_H')
OVMF_H = sut_tool('OVMF_H')
PRIME95_H = sut_tool('PRIME95_H')
PRIME95_SCRIPT_H = sut_tool('PRIME95_SCRIPT_H')
TDX_SEAM_LOADER_H = sut_tool('TDX_SEAM_LOADER_H')
TDX_SEAM_MODULE_H = sut_tool('TDX_SEAM_MODULE_H')
SGX_H = sut_tool('SGX_H')
SGXHYDRA_H = sut_tool('SGXHYDRA_H')
SGXSDK_SCRIPT_H = sut_tool('SGXSDK_SCRIPT_H')
SRC_SCRIPT_H = sut_tool('SRC_SCRIPT_H')
IDXD_KTEST_MASTER_H = sut_tool('IDXD_KTEST_MASTER_H')
SPR_ACCE_RANDOM_CONFIG_H = sut_tool('SPR_ACCE_RANDOM_CONFIG_H')
SOCWATCH_H = sut_tool('SOCWATCH_H')
CPUID_H = sut_tool('CPUID_H')
SOCWATCH_SCRIPT_H = sut_tool('SOCWATCH_SCRIPT_H')
BASHRC_H = sut_tool('BASHRC_H')
MSR_tool_H = sut_tool('MSR_tool_H')
QAT_DRIVER_V_H = sut_tool('QAT_DRIVER_V_H')
DLB_DRIVER_V_H = sut_tool('DLB_DRIVER_V_H')
DSA_DRIVER_V_H = sut_tool('DSA_DRIVER_V_H')
IAX_WB_H = sut_tool('IAX_WB_H')
XMLCLI_H = sut_tool('XMLCLI_H')
EFIXMLCLI_H = sut_tool('EFIXMLCLI_H')


QAT_DRIVER_NAME = sut_tool('QAT_DRIVER_NAME')
DLB_DRIVER_NAME = sut_tool('DLB_DRIVER_NAME')
KERNEL_HEADER_NAME = sut_tool('KERNEL_HEADER_NAME')
KERNEL_DEVEL_NAME = sut_tool('KERNEL_DEVEL_NAME')
KERNEL_INTERNAL_NAME = sut_tool('KERNEL_INTERNAL_NAME')
DPDK_DRIVER_NAME = sut_tool('DPDK_DRIVER_NAME')
DSA_ACCEL_CONFIG_NAME = sut_tool('DSA_ACCEL_CONFIG_NAME')
IDXD_KTEST_MASTER_NAME = sut_tool('IDXD_KTEST_MASTER_NAME')
SPR_ACCE_RANDOM_CONFIG_NAME = sut_tool('SPR_ACCE_RANDOM_CONFIG_NAME')
IMAGE_NAME = sut_tool('IMAGE_NAME')
CLEAN_IMAGE_NAME = sut_tool('CLEAN_IMAGE_NAME')
IMAGE_NAME_DLB = sut_tool('IMAGE_NAME_DLB')
IMAGE_BASE_NAME = sut_tool('IMAGE_BASE_NAME')
SAMPLE_CODE_NAME  = sut_tool('SAMPLE_CODE_NAME')
MEGA_SCRIPT_NAME  = sut_tool('MEGA_SCRIPT_NAME')
PPEXPECT_NAME  = sut_tool('PPEXPECT_NAME')
TDX_SEAM_RPMS_PATH_L = sut_tool('TDX_SEAM_RPMS_PATH_L')
QATZIP_PATH_L = sut_tool('QATZIP_PATH_L')
QATZIP_SCRIPT_PATH_L = sut_tool('QATZIP_SCRIPT_PATH_L')
OPENSSL_PATH_L = sut_tool('OPENSSL_PATH_L')
QAT_ENGINE_PATH_L = sut_tool('QAT_ENGINE_PATH_L')
LINPACK_PATH_L = sut_tool('LINPACK_PATH_L')
QAT_DRIVER_PATH_L = sut_tool('QAT_DRIVER_PATH_L')
DLB_DRIVER_PATH_L = sut_tool('DLB_DRIVER_PATH_L')
DPDK_DRIVER_PATH_L = sut_tool('DPDK_DRIVER_PATH_L')
DSA_PATH_L = sut_tool('DSA_PATH_L')
STRESSAPPTEST_PATH_L = sut_tool('STRESSAPPTEST_PATH_L')
QAT_ASYM_PATH_L = sut_tool('QAT_ASYM_PATH_L')
QAT_SYM_PATH_L = sut_tool('QAT_SYM_PATH_L')
QAT_TEST_SCRIPT_PATH_L = sut_tool('QAT_TEST_SCRIPT_PATH_L')
PTU_PATH_L = sut_tool('PTU_PATH_L')
MLC_PATH_L = sut_tool('MLC_PATH_L')
SAMPLE_CODE_PATH_L = sut_tool('SAMPLE_CODE_PATH_L')
MEGA_CONF_PATH_L = sut_tool('MEGA_CONF_PATH_L')
MEGA_SCRIPT_PATH_L = sut_tool('MEGA_SCRIPT_PATH_L')
KERNEL_HEADER_PATH_L = sut_tool('KERNEL_HEADER_PATH_L')
KERNEL_DEVEL_PATH_L = sut_tool('KERNEL_DEVEL_PATH_L')
KERNEL_INTERNAL_PATH_L = sut_tool('KERNEL_INTERNAL_PATH_L')
PPEXPECT_MEGA_PATH_L = sut_tool('PPEXPECT_MEGA_PATH_L')
PPEXPECT_prime95_PATH_L = sut_tool('PPEXPECT_prime95_PATH_L')
PPEXPECT_SOCWATCH_PATH_L = sut_tool('PPEXPECT_SOCWATCH_PATH_L')
VM_PATH_L = sut_tool('VM_PATH_L')
ISO_PATH_L = sut_tool('ISO_PATH_L')
OVMF_PATH_L = sut_tool('OVMF_PATH_L')
PRIME95_PATH_L = sut_tool('PRIME95_PATH_L')
PRIME95_SCRIPT_PATH_L = sut_tool('PRIME95_SCRIPT_PATH_L')
TDX_SEAM_LOADER_PATH_L = sut_tool('TDX_SEAM_LOADER_PATH_L')
TDX_SEAM_MODULE_PATH_L = sut_tool('TDX_SEAM_MODULE_PATH_L')
PPEXPECT_SGXSDK_PATH_L = sut_tool('PPEXPECT_SGXSDK_PATH_L')
SGX_PATH_L = sut_tool('SGX_PATH_L')
SGXHYDRA_PATH_L = sut_tool('SGXHYDRA_PATH_L')
SGXSDK_SCRIPT_PATH_L = sut_tool('SGXSDK_SCRIPT_PATH_L')
SRC_SCRIPT_PATH_L = sut_tool('SRC_SCRIPT_PATH_L')
IDXD_KTEST_MASTER_PATH_L = sut_tool('IDXD_KTEST_MASTER_PATH_L')
SPR_ACCE_RANDOM_CONFIG_PATH_L = sut_tool('SPR_ACCE_RANDOM_CONFIG_PATH_L')
IMAGE_PATH_L = sut_tool('IMAGE_PATH_L')
TDX_SEAM_MODULE_RPM_PATH_L = sut_tool('TDX_SEAM_MODULE_RPM_PATH_L')
TDX_SEAM_MODULE_COMMON_PATH_L = sut_tool('TDX_SEAM_MODULE_COMMON_PATH_L')
TDX_SEAM_MODULE_NON_PRODUCTION_PATH_L = sut_tool('TDX_SEAM_MODULE_NON_PRODUCTION_PATH_L')
PPEXPECT_TDX_LOADER_PATH_L = sut_tool('PPEXPECT_TDX_LOADER_PATH_L')
SOCWATCH_PATH_L = sut_tool('SOCWATCH_PATH_L')
CPUID_PATH_L = sut_tool('CPUID_PATH_L')
SOCWATCH_SCRIPT_PATH_L = sut_tool('SOCWATCH_SCRIPT_PATH_L')
BASHRC_PATH_L = sut_tool('BASHRC_PATH_L')
MSR_TOOL_PATH_L = sut_tool('MSR_TOOL_PATH_L')
PPEXPECT_IAX_WB_PATH_L = sut_tool('PPEXPECT_IAX_WB_PATH_L')
IAX_WB_PATH_L = sut_tool('IAX_WB_PATH_L')
XMLCLI_TOOL_PATH_L = sut_tool('XMLCLI_TOOL_PATH_L')
EFIXMLCLI_TOOL_PATH_L = sut_tool('EFIXMLCLI_TOOL_PATH_L')
QAT_DRIVER_PATH_V = sut_tool('QAT_DRIVER_PATH_V')
DLB_DRIVER_PATH_V = sut_tool('DLB_DRIVER_PATH_V')
DSA_DRIVER_PATH_V = sut_tool('DSA_DRIVER_PATH_V')
ESXI_VM_TOOL_PATH_V = sut_tool('ESXI_VM_TOOL_PATH_V')



class Accelerator:
    BKC_FILES_DIRECTORY = r'C:\Users\Administrator\Desktop\Accelerator\BKC_files\\'
    QAT_DEVICE_NUM = 4
    DLB_DEVICE_NUM = 4
    DSA_DEVICE_NUM = 4
    IAX_DEVICE_NUM = 4
    CENTOS_INTEL_NEXT_KERNEL = '5.12.0'
    CENTOS_STREAM_KERNEL = '5.15.0'
    IFWI_VERSION = '0076.D27'
    DEVICE_ID = {
        'SPR': {
            'QAT_DEVICE_ID': '4940',
            'DLB_DEVICE_ID': '2710',
            'DSA_DEVICE_ID': '0b25',
            'IAX_DEVICE_ID': '0cfe',
            'QAT_VF_DEVICE_ID': '4941',
            'DLB_VF_DEVICE_ID': '2711',
            'DSA_MDEV_DEVICE_ID': '',
            'IAX_MDEV_DEVICE_ID': '',
            'QAT_MDEV_DEVICE_ID': '0da5',
            'DLB_MDEV_DEVICE_ID': '',
        },
        'GNR': {
            'QAT_DEVICE_ID': '4944',
            'DLB_DEVICE_ID': '2714',
            'DSA_DEVICE_ID': '0b25',
            'IAX_DEVICE_ID': '0cfe',
            'QAT_VF_DEVICE_ID': '4945',
            'DLB_VF_DEVICE_ID': '2715',
            'DSA_MDEV_DEVICE_ID': '',
            'IAX_MDEV_DEVICE_ID': '',
            'QAT_MDEV_DEVICE_ID': '0da5',
            'DLB_MDEV_DEVICE_ID': '',
        }
    }

    def __init__(self, sut):
        self.sut = sut
        self.Case = Case
        self.my_os = OperationSystem[OS.get_os_family(sut.default_os)]
        self.platform = self.sut.socket_name
        # self.platform = str(sut.cfg['defaults'].get('platform')).lower()
        # self.platform = sut.cfg["defaults"]["platform"]
        self.qat_id = Accelerator.DEVICE_ID[self.platform].get('QAT_DEVICE_ID')
        self.dlb_id = Accelerator.DEVICE_ID[self.platform].get('DLB_DEVICE_ID')
        self.dsa_id = Accelerator.DEVICE_ID[self.platform].get('DSA_DEVICE_ID')
        self.iax_id = Accelerator.DEVICE_ID[self.platform].get('IAX_DEVICE_ID')
        self.qat_vf_id = Accelerator.DEVICE_ID[self.platform].get('QAT_VF_DEVICE_ID')
        self.dlb_vf_id = Accelerator.DEVICE_ID[self.platform].get('DLB_VF_DEVICE_ID')
        self.qat_mdev_id = Accelerator.DEVICE_ID[self.platform].get('QAT_MDEV_DEVICE_ID')
        self.dlb_mdev_id = Accelerator.DEVICE_ID[self.platform].get('DLB_MDEV_DEVICE_ID')
        self.dsa_mdev_id = Accelerator.DEVICE_ID[self.platform].get('DSA_MDEV_DEVICE_ID')
        self.iax_mdev_id = Accelerator.DEVICE_ID[self.platform].get('IAX_MDEV_DEVICE_ID')
        self.qat_device_num = Accelerator.QAT_DEVICE_NUM
        self.dlb_device_num = Accelerator.DLB_DEVICE_NUM
        self.dsa_device_num = Accelerator.DSA_DEVICE_NUM
        self.iax_device_num = Accelerator.IAX_DEVICE_NUM

    # CentOS-APIs
###########################################################################################################

    def dsa_modify(self):
        # 1. current file abs path
        cur_path = os.path.abspath(__file__)
        # 2. get configureation path
        src_path = cur_path.split("src")[0]
        conf_path = os.path.join(src_path, "src", "configuration", "config", self.sut.cfg["platform"])
        # 3. sut_tools.py path
        # 4. open sut_tools.py
        # 5. search DSA_H line
        # 6. replace with new line
        # 7. close file
        pass

    def accel_config_check(self, device_num, acce_ip):
        """
             Purpose: Check accel-config list result
             Args:
                 device_num: The number of enabled device in work-queues
                 acce_ip: Which device need to check the device status, such as: 'DSA' or 'IAX'
             Returns:
                 No
             Raises:
                 RuntimeError: If any errors
             Example:
                 Simplest usage: Check accel-config list result
                     accel_config_check(device_num, 'IAX')
       """
        cpu_num = self.get_cpu_num()
        _, out, err = self.sut.execute_shell_cmd('accel-config list', timeout=60)
        if acce_ip == 'qat':
            if device_num == cpu_num * self.qat_device_num:
                # self.__check_all_device_wq(cpu_num, self.qat_device_num, out)
                self.__check_all_device_wq(out, device_num, acce_ip)
            else:
                self.__check_random_device_wq(out, device_num, acce_ip)
        elif acce_ip == 'dlb':
            if device_num == cpu_num * self.dlb_device_num:
                # self.__check_all_device_wq(cpu_num, self.dlb_device_num, out)
                self.__check_all_device_wq(out, device_num, acce_ip)
            else:
                self.__check_random_device_wq(out, device_num, acce_ip)
        elif acce_ip == 'dsa':
            if device_num == cpu_num * self.dsa_device_num:
                # self.__check_all_device_wq(cpu_num, self.dsa_device_num, out)
                self.__check_all_device_wq(out, device_num, acce_ip)
            else:
                self.__check_random_device_wq(out, device_num, acce_ip)
        elif acce_ip == 'iax':
            if device_num == cpu_num * self.iax_device_num:
                # self.__check_all_device_wq(cpu_num, self.iax_device_num, out)
                self.__check_all_device_wq(out, device_num, acce_ip)
            else:
                self.__check_random_device_wq(out, device_num, acce_ip)

    def accel_config_install(self):
        """
              Purpose: Install DSA SIOV accel_config
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Install DSA SIOV accel_config
                      accel_config_install()
        """
        ker_ver = self.kernel_version()
        if ker_ver <= self.CENTOS_INTEL_NEXT_KERNEL:
            self.modify_kernel_grub('intel_iommu=on,sm_on,iova_sl idxd.legacy_cdev_load=1 modprobe.blacklist=idxd_uacce', True)
            self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=DSA_PATH_L)
            self.sut.upload_to_remote(localpath=DSA_H, remotepath=DSA_PATH_L)
            _, out, err = self.sut.execute_shell_cmd('ls', timeout=60, cwd='/sys/bus/dsa/')
            self.check_keyword(['devices', 'drivers', 'drivers_autoprobe', 'drivers_probe', 'uevent'], out,
                               'all driver exist')
            self.check_keyword(['devices'], out, 'all driver exist')
            _, out, err = self.sut.execute_shell_cmd('ls |grep dsa', timeout=60, cwd='/sys/bus/dsa/devices/')
            # self.check_keyword(['dsa0', 'dsa10', 'dsa12', 'dsa14', 'dsa2', 'dsa4', 'dsa6', 'dsa8'], out, 'Not recognize all dsa device')
            self.check_keyword(['dsa'], out, 'Not recognize all dsa device')
            self.sut.execute_shell_cmd('unzip *.zip', timeout=20, cwd=DSA_PATH_L)
            _, out, err = self.sut.execute_shell_cmd('./autogen.sh', timeout=20 * 60, cwd=f'{DSA_PATH_L}*/')
            # self.__check_error(err)
            self.sut.execute_shell_cmd(
                "./configure CFLAGS='-g -O2' --prefix=/usr --sysconfdir=/etc --libdir=/usr/lib64 --enable-test=yes",
                timeout=60, cwd=f'{DSA_PATH_L}*/')
            # self.__check_error(err)
            _, out, err = self.sut.execute_shell_cmd('make', timeout=20 * 60, cwd=f'{DSA_PATH_L}*/')
            self.__check_error(err)
            _, out, err = self.sut.execute_shell_cmd('make check', timeout=40 * 60, cwd=f'{DSA_PATH_L}*/')
            self.__check_error(err)
            _, out, err = self.sut.execute_shell_cmd('make install', timeout=20 * 60, cwd=f'{DSA_PATH_L}*/')
            self.__check_error(err)
            _, out, err = self.sut.execute_shell_cmd('accel-config --list-cmds', timeout=5 * 60, cwd=f'{DSA_PATH_L}*/')
            self.check_keyword(
                ['version', 'list', 'load-config', 'save-config', 'help', 'disable-device', 'enable-device',
                 'disable-wq', 'enable-wq', 'config-device', 'config-group', 'config-wq', 'config-engine',
                 'create-mdev', 'remove-mdev'], out, 'accel-config show fail')
            _, out, err = self.sut.execute_shell_cmd('accel-config list -i', timeout=5 * 60, cwd=f'{DSA_PATH_L}*/')
            # self.check_keyword(['dsa0', 'dsa10', 'dsa12', 'dsa14', 'dsa2', 'dsa4', 'dsa6', 'dsa8'], out, 'Not all DSA device are detected')
            self.check_keyword(['dsa'], out, 'No DSA device are detected')
        else:
            self.modify_kernel_grub('intel_iommu=on,sm_on,iova_sl', True)
            self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=SPR_ACCE_RANDOM_CONFIG_PATH_L)
            self.sut.upload_to_remote(localpath=SPR_ACCE_RANDOM_CONFIG_H, remotepath=SPR_ACCE_RANDOM_CONFIG_PATH_L)
            self.sut.execute_shell_cmd('unzip *.zip', timeout=5 * 60, cwd=SPR_ACCE_RANDOM_CONFIG_PATH_L)


    def acce_random_test(self, command):
        """
             Purpose: Configure work-queues
             Args:
                 command: execute command
             Returns:
                 No
             Raises:
                 RuntimeError: If any errors
             Example:
                 Simplest usage: Configure work-queues
                     acce_random_test('Setup_Randomize_DSA_Conf.sh -au -F 1')
       """
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=SPR_ACCE_RANDOM_CONFIG_PATH_L)
        self.sut.upload_to_remote(localpath=SPR_ACCE_RANDOM_CONFIG_H, remotepath=SPR_ACCE_RANDOM_CONFIG_PATH_L)
        self.sut.execute_shell_cmd('unzip *.zip', timeout=5*60, cwd=SPR_ACCE_RANDOM_CONFIG_PATH_L)
        cpu_num = self.get_cpu_num()
        device_num = 0
        out = ''
        cmd_list = command.strip().split('_Conf')
        acce_ip = cmd_list[0].split('_')[2]   #'DSA', 'IAX'
        if acce_ip == 'QAT':
            device_num = self.qat_device_num
        elif acce_ip == 'DLB':
            device_num = self.dlb_device_num
        elif acce_ip == 'DSA':
            device_num = self.dsa_device_num
        elif acce_ip == 'IAX':
            device_num = self.iax_device_num
        comm_list = command.strip().split('-')
        if 'a' in comm_list[1]:
            out = self.__choose_run_folder(command, False)
            enabled_device_num = self.check_enabled_device_num(out)
            enabled_wq_num = self.__check_enabled_wq_num(out)
            if enabled_device_num != cpu_num * device_num:
                logger.error('Not all device detected')
                raise Exception('Not all device detected')
            else:
                self.check_keyword([f'enabled {enabled_device_num} device(s) out of {enabled_device_num}', f'enabled {enabled_wq_num} wq(s) out of {enabled_wq_num}'], out, 'Device random test fail')
        elif 'c' in comm_list[1] and 'a' not in comm_list[1]:
            out = self.__choose_run_folder(command, False)
            enabled_device_num = self.check_enabled_device_num(out)
            enabled_wq_num = self.__check_enabled_wq_num(out)
            self.check_keyword([f'enabled {enabled_device_num} device(s) out of {enabled_device_num}', f'enabled {enabled_wq_num} wq(s) out of {enabled_wq_num}'], out, 'Device random test fail')
        elif 'w' in comm_list[1] or 'b' in comm_list[1]:
            out = self.__choose_run_folder(command, True)
            self.check_keyword(['No errors found. Test pass'], out, 'Device random test fail')
        return out

    def add_environment_to_file(self, check_key, add_command):
        """
              Purpose: to check all keys in /root/.bashrc file, if not add environments variable to /root/.bashrc file
              Args:
                  check_key: the name of environments variable
                  add_command: add environments variable to /root/.bashrc file
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: check key 'end' in /root/.bashrc file
                        add_environment_to_file('end', 'end=$((SECONDS+110))')
        """
        _, out, err = self.sut.execute_shell_cmd('cat /root/.bashrc', timeout=60)
        if check_key not in out:
            self.sut.execute_shell_cmd(f"echo '{add_command}' >> /root/.bashrc", timeout=60)
            self.sut.execute_shell_cmd('source /root/.bashrc', timeout=60)


    def attach_mdev_to_vm(self, kvm, vm_name, mdev_uuid_list):

        logger.info(f"attach acc mdev to {vm_name}")
        self.sut.execute_shell_cmd('rm -rf xml', timeout=60, cwd=IMAGE_PATH_L)
        self.sut.execute_shell_cmd('mkdir xml', timeout=60, cwd=IMAGE_PATH_L)
        is_vm_running = kvm.is_vm_running(vm_name)
        if is_vm_running:
            kvm.shutdown_vm(vm_name)
        for mdev_uuid in mdev_uuid_list:
            xml_path = self.create_mdev_xml_on_sut(kvm.sut, vm_name, mdev_uuid)
            cmd = f'virsh attach-device {vm_name} {xml_path} --config'
            rcode, _, std_err = kvm.sut.execute_shell_cmd(cmd)
            if rcode != 0:
                raise Exception(std_err)
            if vm_name not in kvm.attached_device_list:
                kvm.attached_device_list[vm_name] = [xml_path]
            else:
                kvm.attached_device_list[vm_name] += [xml_path]


    def change_xmlcli_file(self):
        """
                Purpose: To install DSA driver
                Args:
                    No
                Returns:
                    No
                Raises:
                    RuntimeError: If any errors
                Example:
                    Simplest usage: change xmlcli file
                        change_xmlcli_file()
            """
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=XMLCLI_TOOL_PATH_L)
        self.sut.upload_to_remote(localpath=XMLCLI_H, remotepath=XMLCLI_TOOL_PATH_L)
        self.sut.execute_shell_cmd('unzip *.zip', timeout=60, cwd=XMLCLI_TOOL_PATH_L)
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=EFIXMLCLI_TOOL_PATH_L)
        self.sut.upload_to_remote(localpath=EFIXMLCLI_H, remotepath=EFIXMLCLI_TOOL_PATH_L)
        self.sut.execute_shell_cmd('unzip *.zip', timeout=60, cwd=EFIXMLCLI_TOOL_PATH_L)
        # self.sut.execute_shell_cmd('reboot', timeout=30 * 60)
        # self.Case.sleep(60)
        # self.Case.wait_and_expect(f'SUT in OS', 30 * 60, self.sut.check_system_in_os)
        self.my_os.warm_reset_cycle_step(self.sut)
        self.Case.sleep(60)

    def check_acce_device_status(self, acce_ip):
        """
              Purpose: Check all device in output file
              Args:
                  acce_ip : Which device need to check the device status, such as 'qat','dlb','dsa'
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Check all QAT device
                        check_acce_device_status('qat')
        """
        out = ''
        cpu_num = self.get_cpu_num()
        if acce_ip == 'qat':
            _, out, err = self.sut.execute_shell_cmd(f'lspci |grep {self.qat_id}', timeout=60)
            line_list = out.strip().split('\n')
            device_num = 0
            for line in line_list:
                if f'{self.qat_id}' in line:
                    device_num += 1
            if device_num != cpu_num * self.qat_device_num:
                logger.error('Not detect all device')
                raise Exception('Not detect all device')
        elif acce_ip == 'dlb':
            _, out, err = self.sut.execute_shell_cmd(f'lspci |grep {self.dlb_id}', timeout=60)
            line_list = out.strip().split('\n')
            device_num = 0
            for line in line_list:
                if f'{self.dlb_id}' in line:
                    device_num += 1
            if device_num != cpu_num * self.dlb_device_num:
                logger.error('Not detect all device')
                raise Exception('Not detect all device')
        elif acce_ip == 'dsa':
            _, out, err = self.sut.execute_shell_cmd(f'lspci |grep {self.dsa_id}', timeout=60)
            line_list = out.strip().split('\n')
            device_num = 0
            for line in line_list:
                if f'{self.dsa_id}' in line:
                    device_num += 1
            if device_num != cpu_num * self.dsa_device_num:
                logger.error('Not detect all device')
                raise Exception('Not detect all device')
        elif acce_ip == 'iax':
            _, out, err = self.sut.execute_shell_cmd(f'lspci |grep {self.iax_id }', timeout=60)
            line_list = out.strip().split('\n')
            device_num = 0
            for line in line_list:
                if f'{self.iax_id }' in line:
                    device_num += 1
            if device_num != cpu_num * self.iax_device_num:
                logger.error('Not detect all device')
                raise Exception('Not detect all device')

    def check_enabled_device_num(self, out):
        """
             Purpose: Check the number of enabled device in work-queues
             Args:
                 out: Configure work-queues result
             Returns:
                 No
             Raises:
                 RuntimeError: If any errors
             Example:
                 Simplest usage: Check the number of enabled device in work-queues
                     check_enabled_device_num(out)
       """
        line_list = out.strip().split('Enabling')
        device_list = line_list[1].split('enabled')
        device_word_list = device_list[1].strip().split(' ')
        return int(device_word_list[0])

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

    def check_python_environment(self):
        _, out, err = self.sut.execute_shell_cmd('ln -s /usr/bin/python3 /usr/bin/python | wc -l', timeout=60)
        if 'File exists' not in err:
            logger.error('*************************************************************')
            raise Exception('*************************************************************')
        else:
            pass

    def check_qat_service_status(self, is_vf=False):
        """
              Purpose: Check all QAT device status in output file
              Args:
                  vf: Check QAT vf status or pf status
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Check all QAT device status in output file
                        check_all_device_status(True)-->check qat vf status
                        check_all_device_status(False)-->check qat pf status
        """
        cpu_num = self.get_cpu_num()
        out = self.qat_service_status()
        str_list = out.strip().split('\n')
        status_num = 0
        if is_vf:
            for line in str_list:
                if 'state: up' in line:
                    status_num += 1
            if status_num != cpu_num*self.qat_device_num*17:
                logger.error('Not all QAT device status up or Not Recognize all QAT device')
                raise Exception('Not all QAT device status up or Not Recognize all QAT device')
        else:
            for line in str_list:
                if 'state: up' in line:
                    status_num += 1
            if status_num != cpu_num*self.qat_device_num:
                logger.error('Not all QAT device status up or Not Recognize all QAT device')
                raise Exception('Not all QAT device status up or Not Recognize all QAT device')

    def clear_qat_config_file(self, config_key):
        """
              Purpose: Clear QAT config files
              Args:
                  config_key : Which function (asym, mdev, shim) config files need to modify
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Clear QAT asymmetric encrypted config files
                        clear_qat_config_file('asym')
        """
        if config_key == 'mdev':
            self.__qat_mdev_config_clr()
        elif config_key == 'asym':
            self.__qat_asym_config_clr()
        elif config_key == 'shim':
            self.__qat_shim_config_clr()
        else:
            logger.error('Input correct config keyword')
            raise Exception('Input correct config keyword')

    def cpuid_check(self):
        """
             Purpose: Check SGX "cpuid" value
             Args:
                 No
             Returns:
                 No
             Raises:
                 RuntimeError: If any errors
             Example:
                 Simplest usage: Check SGX "cpuid 0x12" value
                     cpuid_check()
       """
        thread_num = self.__get_thread_num()
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=CPUID_PATH_L)
        self.sut.upload_to_remote(localpath=CPUID_H, remotepath=CPUID_PATH_L)
        self.sut.execute_shell_cmd('chmod 777 *', timeout=60, cwd=f'{CPUID_PATH_L}')
        self.sut.execute_shell_cmd('./cpuid -l 0x12 > cpuid_0x12.log', timeout=60, cwd=f'{CPUID_PATH_L}')
        self.sut.download_to_local(f'{CPUID_PATH_L}cpuid_0x12.log', os.path.join(LOG_PATH, 'Logs'))
        _, out, err = self.sut.execute_shell_cmd('cat cpuid_0x12.log', timeout=60, cwd=f'{CPUID_PATH_L}')
        line_list = out.strip().split('CPU')
        sgx_list = []
        for line in line_list:
            if line != '':
                sgx_list.append(line)
        for i in range(thread_num):
            l1 = sgx_list[i].split('\n')
            sgx1_line_list = l1[2].split('=')
            sgx2_line_list = l1[3].split('=')
            sgx1_value = sgx1_line_list[1].strip()
            sgx2_value = sgx2_line_list[1].strip()
            if sgx1_value != 'true' or sgx2_value != 'true':
                logger.error('SGX cpuid value is incorrect')
                raise Exception('SGX cpuid value is incorrect')

    def cpuid_check_uefi(self):
        """
             Purpose: Check SGX "cpuid" value
             Args:
                 No
             Returns:
                 No
             Raises:
                 RuntimeError: If any errors
             Example:
                 Simplest usage: Check SGX "cpuid 0x12" value
                     cpuid_check()
       """
        usb_device_id = self.__usb_device_detact()
        uefi_cmd = f'fs{usb_device_id}:\\cpuidd\\Cpuid.efi'
        out = self.sut.execute_uefi_cmd(uefi_cmd, timeout=60)
        self.check_keyword(['SGX1: 1', 'SGX2: 1'], out, 'SGX enable failed')
    # ##API 15
    # def create_dlb_mdev(self, dlb_device_index):
    #     """
    #           Purpose: Create DLB SRIOV config
    #           Args:
    #               dlb_dev: DLB device id number, device id number begin from 0
    #           Returns:
    #               No
    #           Raises:
    #               RuntimeError: If any errors
    #           Example:
    #               Simplest usage: Create DLB SRIOV config
    #                   creat_dlb_mdev(0)
    #     """
    #     self.add_environment_to_file('SYSFS_PATH', f'export SYSFS_PATH=/sys/class/dlb2/dlb{dlb_device_index}')
    #     self.add_environment_to_file('UUID1', "export UUID1=`uuidgen`")
    #     self.add_environment_to_file('MDEV_PATH', 'export MDEV_PATH=/sys/bus/mdev/devices/$UUID1/dlb2_mdev')
    #     self.sut.execute_shell_cmd('echo $UUID1 > $SYSFS_PATH/device/mdev_supported_types/dlb2-dlb/create ', timeout=60, cwd='/root')
    #     self.sut.execute_shell_cmd('echo 2048 > $MDEV_PATH/num_atomic_inflights', timeout=60, cwd='/root')
    #     self.sut.execute_shell_cmd('echo 4096 > $MDEV_PATH/num_dir_credits', timeout=60, cwd='/root')
    #     self.sut.execute_shell_cmd('echo 64 > $MDEV_PATH/num_dir_ports', timeout=60, cwd='/root')
    #     self.sut.execute_shell_cmd('echo 2048 > $MDEV_PATH/num_hist_list_entries', timeout=60, cwd='/root')
    #     self.sut.execute_shell_cmd('echo 8192 > $MDEV_PATH/num_ldb_credits', timeout=60, cwd='/root')
    #     self.sut.execute_shell_cmd('echo 64 > $MDEV_PATH/num_ldb_ports', timeout=60, cwd='/root')
    #     self.sut.execute_shell_cmd('echo 32 > $MDEV_PATH/num_ldb_queues', timeout=60, cwd='/root')
    #     self.sut.execute_shell_cmd('echo 32 > $MDEV_PATH/num_sched_domains', timeout=60, cwd='/root')
    #     self.sut.execute_shell_cmd('echo 16 > $MDEV_PATH/num_sn0_slots', timeout=60, cwd='/root')
    #     self.sut.execute_shell_cmd('echo 16 > $MDEV_PATH/num_sn1_slots', timeout=60, cwd='/root')

    def __create_dlb_mdev_egs(self, MDEV_PATH):
        self.sut.execute_shell_cmd(f'echo 2048 > {MDEV_PATH}/num_atomic_inflights', timeout=60, cwd='/root')
        self.sut.execute_shell_cmd(f'echo 4096 > {MDEV_PATH}/num_dir_credits', timeout=60, cwd='/root')
        self.sut.execute_shell_cmd(f'echo 64 > {MDEV_PATH}/num_dir_ports', timeout=60, cwd='/root')
        self.sut.execute_shell_cmd(f'echo 2048 >  {MDEV_PATH}/num_hist_list_entries', timeout=60, cwd='/root')
        self.sut.execute_shell_cmd(f'echo 8192 >  {MDEV_PATH}/num_ldb_credits', timeout=60, cwd='/root')
        self.sut.execute_shell_cmd(f'echo 64 >  {MDEV_PATH}/num_ldb_ports', timeout=60, cwd='/root')
        self.sut.execute_shell_cmd(f'echo 32 >  {MDEV_PATH}/num_ldb_queues', timeout=60, cwd='/root')
        self.sut.execute_shell_cmd(f'echo 32 >  {MDEV_PATH}/num_sched_domains', timeout=60, cwd='/root')
        self.sut.execute_shell_cmd(f'echo 16 >  {MDEV_PATH}/num_sn0_slots', timeout=60, cwd='/root')
        self.sut.execute_shell_cmd(f'echo 16 >  {MDEV_PATH}/num_sn1_slots', timeout=60, cwd='/root')

    def __create_dlb_mdev_bhs(self, MDEV_PATH):
        self.sut.execute_shell_cmd(f'echo 2048 > {MDEV_PATH}/num_atomic_inflights', timeout=60, cwd='/root')
        self.sut.execute_shell_cmd(f'echo 96 > {MDEV_PATH}/num_dir_ports', timeout=60, cwd='/root')
        self.sut.execute_shell_cmd(f'echo 2048 >  {MDEV_PATH}/num_hist_list_entries', timeout=60, cwd='/root')
        self.sut.execute_shell_cmd(f'echo 16384 >  {MDEV_PATH}/num_ldb_credits', timeout=60, cwd='/root')
        self.sut.execute_shell_cmd(f'echo 64 >  {MDEV_PATH}/num_ldb_ports', timeout=60, cwd='/root')
        self.sut.execute_shell_cmd(f'echo 32 >  {MDEV_PATH}/num_ldb_queues', timeout=60, cwd='/root')
        self.sut.execute_shell_cmd(f'echo 32 >  {MDEV_PATH}/num_sched_domains', timeout=60, cwd='/root')
        self.sut.execute_shell_cmd(f'echo 16 >  {MDEV_PATH}/num_sn0_slots', timeout=60, cwd='/root')
        self.sut.execute_shell_cmd(f'echo 16 >  {MDEV_PATH}/num_sn1_slots', timeout=60, cwd='/root')

    ##API 15
    def create_dlb_mdev(self, dlb_device_index):
        """
              Purpose: Create DLB SRIOV config
              Args:
                  dlb_dev: DLB device id number, device id number begin from 0
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Create DLB SRIOV config
                      creat_dlb_mdev(0)
        """
        self.add_environment_to_file('SYSFS_PATH', f'export SYSFS_PATH=/sys/class/dlb2/dlb{dlb_device_index}')
        self.sut.execute_shell_cmd('uuidgen > uuidgen.txt', timeout=60, cwd='/root/')
        _, out, err = self.sut.execute_shell_cmd('cat uuidgen.txt', timeout=60, cwd='/root/')
        line_list = out.strip().split('\n')
        uuidgen = line_list[0]
        MDEV_PATH = f'/sys/bus/mdev/devices/{uuidgen}/dlb2_mdev'
        self.sut.execute_shell_cmd(f'echo {uuidgen} > $SYSFS_PATH/device/mdev_supported_types/dlb2-dlb/create ',
                                   timeout=60, cwd='/root')
        self.__create_dlb_mdev_egs(MDEV_PATH)


    def create_mdev_xml_on_sut(self, sut, vm_name, mdev_uuid):
        xml_filename = f'pci_device_{vm_name}_{mdev_uuid}.xml'
        xml_content = self.get_mdev_xml_content(mdev_uuid)

        with open(xml_filename, "w") as xml_file:
            xml_file.write(xml_content)

        sut.upload_to_remote(localpath=xml_filename, remotepath=f"{sut_tool('IMAGE_PATH_L')}/xml")
        os.remove(xml_filename)

        return f"{sut_tool('IMAGE_PATH_L')}/xml/{xml_filename}"


    def delete_environment(self, check_key):
        """
              Purpose: to check and delete all keys in /root/.bashrc file, if already add environments variable delete it in /root/.bashrc file
              Args:
                  check_key: the name of environments variable
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: check if key 'end' in /root/.bashrc file and delete it
                        delete_environment('end')
        """
        _, out, err = self.sut.execute_shell_cmd('cat /root/.bashrc', timeout=60)
        if check_key in out:
            # self.sut.execute_shell_cmd(f'sed -i "s/.*{check_key}.*//g" /root/.bashrc', timeout=60)
            self.sut.execute_shell_cmd(f"sed '/{check_key}/d' /root/.bashrc > /root/.bashrc1", timeout=60)
            self.sut.execute_shell_cmd(f"mv -f /root/.bashrc1 /root/.bashrc", timeout=60)
            self.sut.execute_shell_cmd('source /root/.bashrc', timeout=60)

    def device_mode_test(self, acce_ip, is_random=False):
        """
             Purpose: Run acce_ip user mode test
             Args:
                 acce_ip: Which device need to check the device status, such as: 'DSA' or 'IAX'
                 is_random: Run value is random or not
             Returns:
                 No
             Raises:
                 RuntimeError: If any errors
             Example:
                 Simplest usage: Run acce_ip user mode test
                     device_mode_test('IAX', False)
       """
        _, out, err = self.sut.execute_shell_cmd(f'./Setup_Randomize_{acce_ip}_Conf.sh -r', timeout=5 * 60, cwd=f'{SPR_ACCE_RANDOM_CONFIG_PATH_L}*/')
        cpu_num = self.get_cpu_num()
        device_num = 0
        if acce_ip == 'QAT':
            device_num = self.qat_device_num * cpu_num * 8
        elif acce_ip == 'DLB':
            device_num = self.dlb_device_num * cpu_num * 8
        elif acce_ip == 'DSA':
            device_num = self.dsa_device_num * cpu_num * 8
        elif acce_ip == 'IAX':
            device_num = self.iax_device_num * cpu_num * 8
        device_wq = 0
        line_list = out.strip().split('\n')
        for line in line_list:
            if 'WQs:' in line:
                device_wq = line.strip().split(':')[1].strip()
        thread_num = int(device_wq) * 24
        print(device_wq)
        print(thread_num)
        if is_random:
            self.check_keyword([f'{thread_num} of {thread_num} tests passed'], out, 'Device mode test failed')
        else:
            if device_num != int(device_wq):
                logger.error('Not all WQ are detected')
                raise Exception('Not all WQ are detected')
            else:
                self.check_keyword([f'{thread_num} of {thread_num} tests passed'], out, 'Device mode test failed')

    def device_opcodes_stress(self, command, test_index):
        """
             Purpose: Run acce_ip test with available OpCodes
             Args:
                 command: execute command
                 test_index: Which OpCode need to run
             Returns:
                 No
             Raises:
                 RuntimeError: If any errors
             Example:
                 Simplest usage: Run acce_ip test with available OpCodes
                     device_opcodes_stress('Setup_Randomize_DSA_Conf.sh -o', 3)
       """
        _, out, err = self.sut.execute_shell_cmd(f'./{command} 0x{test_index}', timeout=60*60, cwd=f'{SPR_ACCE_RANDOM_CONFIG_PATH_L}*/')
        if test_index == 2:
            self.__check_error(err)
        else:
            line_list = out.strip().split('\n')
            actual_wq = 0
            total_wq = 0
            for line in line_list:
                if 'work queues' in line:
                    word_list = line.split('of')
                    actual_wq = word_list[0].strip()
                    total_wq = word_list[1].strip().split('work')[0].strip()
            self.check_keyword([f'{actual_wq} of {total_wq} work queues logged completion records'], out, 'Not all work queues logged completion records')

    def disable_device_conf(self, disable_num, acce_ip):
        """
             Purpose: Disable work-queues
             Args:
                 device_num: The number of enabled device in work-queues
                 acce_ip: Which device need to check the device status, such as: 'DSA' or 'IAX'
             Returns:
                 No
             Raises:
                 RuntimeError: If any errors
             Example:
                 Simplest usage: Disable work-queues
                     disable_device_conf(device_num, 'DSA')
       """
        Case.step('Disable dsa config')
        _, out, err = self.sut.execute_shell_cmd(f'./Setup_Randomize_{acce_ip}_Conf.sh -d', timeout=5*60, cwd=f'{SPR_ACCE_RANDOM_CONFIG_PATH_L}*/')
        line_list = out.strip().split('\n')
        dsa_disable_num = 0
        for line in line_list:
            if 'disabled 1 device(s) out of 1' in line:
                dsa_disable_num += 1
        if dsa_disable_num != int(disable_num):
            logger.error('Not all dsa device are disabled')
            raise Exception('Not all dsa device are disabled')

    def dlb_install(self, ch_makefile):
        """
              Purpose: To install DLB driver
              Args:
                  ch_makefile: If need to modify DLB make file
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Install DLB driver need modify Makefile
                      dlb_install(True)
        """
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=DLB_DRIVER_PATH_L)
        self.sut.upload_to_remote(localpath=DLB_DRIVER_H, remotepath=DLB_DRIVER_PATH_L)
        self.sut.execute_shell_cmd('unzip *.zip ', timeout=60, cwd=DLB_DRIVER_PATH_L)
        if ch_makefile:
            self.sut.execute_shell_cmd("sed -i 's/ccflags-y += -DCONFIG_INTEL_DLB2_SIOV/#  iccflags-y += -DCONFIG_INTEL_DLB2_SIOV/g' /home/BKCPkg/domains/accelerator/dlb/driver/dlb2/Makefile", timeout=60)
        _, out, err = self.sut.execute_shell_cmd('make', timeout=60, cwd=f'{DLB_DRIVER_PATH_L}driver/dlb2/')
        # self.__check_error(err)
        self.sut.execute_shell_cmd('rmmod dlb2', timeout=60, cwd=f'{DLB_DRIVER_PATH_L}driver/dlb2/')
        self.sut.execute_shell_cmd('insmod ./dlb2.ko', timeout=60, cwd=f'{DLB_DRIVER_PATH_L}driver/dlb2/')
        _, out, err = self.sut.execute_shell_cmd('lsmod | grep dlb2', timeout=60)
        self.check_keyword(['dlb2'], out, 'Issue - dlb driver install fail')
        self.sut.execute_shell_cmd('make', timeout=60, cwd=f'{DLB_DRIVER_PATH_L}libdlb/')
        self.__check_error(err)
        self.add_environment_to_file('LD_LIBRARY_PATH', 'export LD_LIBRARY_PATH=/home/BKCPkg/domains/accelerator/dlb/libdlb:$LD_LIBRARY_PATH')

    def dlb_stress(self):
        """
              Purpose: Run dlb stress overnight
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Run dlb stress overnight
                        dlb_stress()
        """
        self.sut.execute_shell_cmd('rm -rf dlb.log', timeout=60, cwd='/root/')
        # self.add_environment_to_file('end', 'end=$((SECONDS+300))')
        self.sut.execute_shell_cmd('while [ $SECONDS -lt 300 ]; do /home/BKCPkg/domains/accelerator/dlb/libdlb/examples/ldb_traffic -n 1024 ;done | tee /root/dlb.log',timeout=500000)
        _, out, err = self.sut.execute_shell_cmd('cat /root/dlb.log')
        self.check_keyword(['[tx_traffic()] Sent 1024 events', '[rx_traffic()] Received 1024 events'], out, 'Run DLB stress fail')
        self.sut.download_to_local(remotepath='/root/dlb.log', localpath=os.path.join(LOG_PATH, 'Logs'))
        self.delete_environment('end')

    def dlb_uninstall(self):
        """
             Purpose: to uninstall dlb driver
             Args:
                 No
             Returns:
                 No
             Raises:
                 RuntimeError: If any errors
             Example:
                 Simplest usage: uninstall dlb driver
                     dlb_uninstall()
        """
        self.sut.execute_shell_cmd('rmmod dlb2', timeout=60, cwd=f'{DLB_DRIVER_PATH_L}driver/dlb2/')

    def dmatest_check(self, acce_ip):
        """
             Purpose: Run dmatest
             Args:
                 acce_ip: Which device need to check the device status, such as: 'DSA' or 'IAX'
             Returns:
                 No
             Raises:
                 RuntimeError: If any errors
             Example:
                 Simplest usage: Run dmatest
                     dmatest_check(device_num, 'DSA')
       """
        ker_ver = self.kernel_version()
        if ker_ver <= self.CENTOS_INTEL_NEXT_KERNEL:
            _, out, err = self.sut.execute_shell_cmd(f'./Setup_Randomize_{acce_ip}_Conf.sh -x -i 1000 -j 10',
                                                     timeout=50 * 60, cwd=f'{SPR_ACCE_RANDOM_CONFIG_PATH_L}*/')
        else:
            _, out, err = self.sut.execute_shell_cmd(f'./Setup_Randomize_{acce_ip}_Conf.sh -i 1000 -j 10',
                                                     timeout=50 * 60, cwd=f'{SPR_ACCE_RANDOM_CONFIG_PATH_L}*/')
        line_list = out.strip().split('\n')
        total_thread = 0
        threads_passed = 0
        for line in line_list:
            if 'Total Threads' in line:
                word_list0 = line.split(' ')
                total_thread = word_list0[2]
            if 'Threads Passed' in line:
                word_list1 = line.split(' ')
                threads_passed = word_list1[2]
        if total_thread != threads_passed:
            logger.error('dmatest fail')
            raise Exception('dmatest fail')

    def dsa_wq_2g2q_user_1(self, dsa_device_index):
        """
              Purpose: Run DSA workqueues two groups two queues and user 1 test
              Args:
                  dsa_device_index: DSA device index, index begin from 0
              Returns:
                  None
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Run DSA workqueues two groups two queues and user 1 test
                      dsa_wq_2g2q_user_1('0')
        """
        ker_ver = self.kernel_version()
        if ker_ver <= self.CENTOS_INTEL_NEXT_KERNEL:
            res, out, err = self.sut.execute_shell_cmd('accel-config load-config -c ./2g2q_user_1.conf | wc -l', timeout=60, cwd=f'{DSA_PATH_L}*/test/configs/')
            if out != '0\n':
                logger.error('accel-config load-config fail')
                raise Exception('accel-config load-config fail')
            _, out, err = self.sut.execute_shell_cmd('accel-config list -i', timeout=60, cwd=f'{DSA_PATH_L}*/test/configs/')
            self.check_keyword(['"grouped_workqueues"', '"grouped_engines"'], out, 'Not recognized grouped_workqueues')
            _, out, err = self.sut.execute_shell_cmd(f'accel-config enable-device dsa{dsa_device_index}', timeout=60, cwd=f'{DSA_PATH_L}*/test/configs/')
            self.check_keyword(['enabled 1 device(s) out of 1'], err, 'Enable dsa device fail')
            _, out, err = self.sut.execute_shell_cmd(f'accel-config enable-wq dsa{dsa_device_index}/wq0.0 dsa{dsa_device_index}/wq0.1', timeout=60, cwd=f'{DSA_PATH_L}*/')
            self.check_keyword(['enabled 2 wq(s) out of 2'], err, 'Not all workqueues are enabled')
            _, out, err = self.sut.execute_shell_cmd('accel-config list -i', timeout=60, cwd=f'{DSA_PATH_L}*/')
            self.check_keyword(['"state":"enabled"'], out, 'Not recognized grouped_workqueues')
            _, out, err = self.sut.execute_shell_cmd(f'accel-config disable-wq dsa{dsa_device_index}/wq0.1 dsa{dsa_device_index}/wq0.0', timeout=60, cwd=f'{DSA_PATH_L}*/')
            self.check_keyword(['disabled 2 wq(s) out of 2'], err, 'Not all workqueues are disabled')
            _, out, err = self.sut.execute_shell_cmd(f'accel-config disable-device dsa{dsa_device_index}', timeout=60, cwd=f'{DSA_PATH_L}*/')
            self.check_keyword(['disabled 1 device(s) out of 1'], err, 'Disable dsa device fail')
            _, out, err = self.sut.execute_shell_cmd('accel-config list -i', timeout=60, cwd=f'{DSA_PATH_L}*/test/configs/')
            if 'grouped_workqueues' in out or '"grouped_engines"' in out:
                logger.error('disable workqueues fail')
                raise Exception('disable workqueues fail')
        else:
            DSA_path = '/usr/share/accel-config/test/configs'
            res, out, err = self.sut.execute_shell_cmd('accel-config load-config -c 2g2q_user_1.conf | wc -l', timeout=60, cwd=DSA_path)
            if out != '0\n':
                logger.error('accel-config load-config fail')
                raise Exception('accel-config load-config fail')
            _, out, err = self.sut.execute_shell_cmd('accel-config list -i', timeout=60, cwd=DSA_path)
            self.check_keyword(['"grouped_workqueues"', '"grouped_engines"'], out, 'Not recognized grouped_workqueues')
            _, out, err = self.sut.execute_shell_cmd(f'accel-config enable-device dsa{dsa_device_index}', timeout=60, cwd=DSA_path)
            self.check_keyword(['enabled 1 device(s) out of 1'], err, 'Enable dsa device fail')
            _, out, err = self.sut.execute_shell_cmd(f'accel-config enable-wq dsa{dsa_device_index}/wq0.0 dsa{dsa_device_index}/wq0.1', timeout=60, cwd=DSA_path)
            self.check_keyword(['enabled 2 wq(s) out of 2'], err, 'Not all workqueues are enabled')
            _, out, err = self.sut.execute_shell_cmd('accel-config list -i', timeout=60, cwd=DSA_path)
            self.check_keyword(['"state":"enabled"'], out, 'Not recognized grouped_workqueues')
            _, out, err = self.sut.execute_shell_cmd(f'accel-config disable-wq dsa{dsa_device_index}/wq0.1 dsa{dsa_device_index}/wq0.0', timeout=60, cwd=DSA_path)
            self.check_keyword(['disabled 2 wq(s) out of 2'], err, 'Not all workqueues are disabled')
            _, out, err = self.sut.execute_shell_cmd(f'accel-config disable-device dsa{dsa_device_index}', timeout=60, cwd=DSA_path)
            self.check_keyword(['disabled 1 device(s) out of 1'], err, 'Disable dsa device fail')
            _, out, err = self.sut.execute_shell_cmd('accel-config list -i', timeout=60, cwd=DSA_path)
            if 'grouped_workqueues' in out or '"grouped_engines"' in out:
                logger.error('disable workqueues fail')
                raise Exception('disable workqueues fail')

    # def dsa_wq_2g2q_user_1(self, dsa_device_index):
    #     """
    #           Purpose: Run DSA workqueues two groups two queues and user 1 test
    #           Args:
    #               dsa_device_index: DSA device index, index begin from 0
    #           Returns:
    #               None
    #           Raises:
    #               RuntimeError: If any errors
    #           Example:
    #               Simplest usage: Run DSA workqueues two groups two queues and user 1 test
    #                   dsa_wq_2g2q_user_1('0')
    #     """
    #     res, out, err = self.sut.execute_shell_cmd('accel-config load-config -c ./2g2q_user_1.conf | wc -l', timeout=60, cwd=f'{DSA_PATH_L}*/test/configs/')
    #     if out != '0\n':
    #         logger.error('accel-config load-config fail')
    #         raise Exception('accel-config load-config fail')
    #     _, out, err = self.sut.execute_shell_cmd('accel-config list -i', timeout=60, cwd=f'{DSA_PATH_L}*/test/configs/')
    #     self.check_keyword(['"grouped_workqueues"', '"grouped_engines"'], out, 'Not recognized grouped_workqueues')
    #     _, out, err = self.sut.execute_shell_cmd(f'accel-config enable-device dsa{dsa_device_index}', timeout=60, cwd=f'{DSA_PATH_L}*/test/configs/')
    #     self.check_keyword(['enabled 1 device(s) out of 1'], err, 'Enable dsa device fail')
    #     _, out, err = self.sut.execute_shell_cmd(f'accel-config enable-wq dsa{dsa_device_index}/wq0.0 dsa{dsa_device_index}/wq0.1', timeout=60, cwd=f'{DSA_PATH_L}*/')
    #     self.check_keyword(['enabled 2 wq(s) out of 2'], err, 'Not all workqueues are enabled')
    #     _, out, err = self.sut.execute_shell_cmd('accel-config list -i', timeout=60, cwd=f'{DSA_PATH_L}*/')
    #     self.check_keyword(['"state":"enabled"'], out, 'Not recognized grouped_workqueues')
    #     _, out, err = self.sut.execute_shell_cmd(f'accel-config disable-wq dsa{dsa_device_index}/wq0.1 dsa{dsa_device_index}/wq0.0', timeout=60, cwd=f'{DSA_PATH_L}*/')
    #     self.check_keyword(['disabled 2 wq(s) out of 2'], err, 'Not all workqueues are disabled')
    #     _, out, err = self.sut.execute_shell_cmd(f'accel-config disable-device dsa{dsa_device_index}', timeout=60, cwd=f'{DSA_PATH_L}*/')
    #     self.check_keyword(['disabled 1 device(s) out of 1'], err, 'Disable dsa device fail')
    #     _, out, err = self.sut.execute_shell_cmd('accel-config list -i', timeout=60, cwd=f'{DSA_PATH_L}*/test/configs/')
    #     if 'grouped_workqueues' in out or '"grouped_engines"' in out:
    #         logger.error('disable workqueues fail')
    #         raise Exception('disable workqueues fail')

    #
    # def fio_stress(self):
    #     """
    #           Purpose: Run fio stress overnight
    #           Args:
    #               No
    #           Returns:
    #               No
    #           Raises:
    #               RuntimeError: If any errors
    #           Example:
    #               Simplest usage: Run fio stress overnight
    #                     fio_stress()
    #     """
    #     self.sut.execute_shell_cmd('yum install -y fio', timeout=10*60)
    #     _, out, err = self.sut.execute_shell_cmd('fio --filename=/dev/sda --direct=1 --iodepth=1 --rw=randrw --rwmixread=70 --ioengine=libaio --bs=4k --size=300G --numjobs=50 --runtime=300 --group_reporting --name=randrw70read4k > /root/fio.log',
    #         timeout=300)
    #     self.__check_error(err)
    #     self.sut.download_to_local(remotepath='/root/fio.log', localpath=os.path.join(LOG_PATH, 'Logs'))
    #     self.sut.execute_shell_cmd('rm -rf fio.log', timeout=60, cwd='/root/')

    def fio_stress(self):
        """
              Purpose: Run fio stress overnight
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Run fio stress overnight
                        fio_stress()
        """
        self.sut.execute_shell_cmd('yum install -y fio', timeout=10*60)
        hdd_info = self.__grep_linux_fio_hdd()
        _, out, err = self.sut.execute_shell_cmd(f'fio --filename=/dev/{hdd_info} --direct=1 --iodepth=1 --rw=randrw --rwmixread=70 --ioengine=libaio --bs=4k --size=300G --numjobs=50 --runtime=300 --group_reporting --name=randrw70read4k > fio.log',
            timeout=300)
        self.__check_error(err)
        self.sut.download_to_local(remotepath='/root/fio.log', localpath=LOG_PATH)
        self.sut.execute_shell_cmd('/root/rm -rf fio.log', timeout=60)

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
        _, out, err = self.sut.execute_shell_cmd('lscpu', timeout=60)
        line_list = out.strip().split('\n')
        for line in line_list:
            word_list = line.split()
            if word_list[0] == 'Socket(s):':
                cpu_num = int(word_list[1])
                return cpu_num

    def get_dev_id(self, ip, pf, vf):
        """
              Purpose: Get single QAT device id
              Args:
                  ip: Which device need to check the device status, eg: 'qat','dlb','dsa'
                  pf: which device pf need to search, input number of the device
                        eg: 0,1...8,begin from 0
                  vf_num: which device vf number need to search
                        eg:1,2....16,begin from 1
              Returns:
                  Yes: device id  --> '0000:6d:00.0'
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Get single QAT device id
                        get_qat_dev_id('qat', 0, 0)
                        return --> '0000:6d:00.0'
        """
        cpu_num = self.get_cpu_num()
        out = ''
        if ip == 'qat':
            _, out, err = self.sut.execute_shell_cmd(f'lspci | grep {self.qat_id}', timeout=60)
            line_list = out.strip().split('\n')
            qat_device_list = []
            for line in line_list:
                str_list = line.split(' ')
                word_list = str_list[0].split(':')  # ['6b','00.0']
                qat_device_list.append(word_list[0])
            if pf > len(qat_device_list) or vf > 16:
                logger.error('the number of given PF exceeds the maximum PF get number')
                raise Exception('the number of given PF exceeds the maximum PF get number')
            else:
                quotient, remainder = divmod(vf, 8)
                dev_id = f'0000:{qat_device_list[pf]}:0{quotient}.{remainder}'  # [' 0000:6b:00.0'] or  [' 0000:6b:00.03']
                return dev_id
        elif ip == 'dsa':
            _, out, err = self.sut.execute_shell_cmd(f'lspci | grep {self.dsa_id}', timeout=60)
            line_list = out.strip().split('\n')
            device_list = []
            i = 0
            if i < cpu_num * self.dsa_device_num:
                for line in line_list:
                    str_list = line.split()  # ['6a:01.0', 'System'... ]
                    dev_id = '0000:' + str_list[i]   # '0000:6a:01.0'
                    device_list.append(dev_id)   # ['0000:6a:01.0','0000:6f:01.0']
                i += 1
            return device_list[pf]   # '0000:6a:01.0'

    def get_dlb_dev_id_list(self, pf, vf_num):
        """
              Purpose: Get list of DLB device ID
              Args:
                  pf: DLB PF device number
                  vf: How many DLB VF device need to create
              Returns:
                  Yes: DLB device ID list --> ['0000:6d:00.0','0000:72:00.0']
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: get DLB True device 0 and create 2 DLB Vietual device for Platform
                        get_dlb_dev_id_list(0, 2)
                        return ['0000:6d:00.1','0000:6d:00.2']
        """
        _, out, err = self.sut.execute_shell_cmd(f'lspci | grep {self.dlb_id}', timeout=60)
        line_list = out.strip().split('\n')
        dlb_list = []
        dev_id_list = []
        for line in line_list:
            str_list = line.split()  # ['6d:00.0', 'Co-processor:'...]
            words_list = str_list[0].split('.')  # ['6d:00', '0' , ....]
            if words_list[1] == '0':
                dlb_deviceid = '0000:' + str_list[0]  # '0000:6d:00.0''0000:72:00.0'
                dlb_deviceid = dlb_deviceid.split(':')
                dlb_list.append(dlb_deviceid[1])  # ['0000:6d:00.0','0000:72:00.0']
        quotient, remainder = divmod(vf_num, 8)
        if vf_num == 0:
            dev_id_list.append(f'0000:{dlb_list[pf]}:0{quotient}.{remainder}')   # ['0000:6d:00.0','0000:72:00.0']
        else:
            for i in range(1, vf_num + 1):
                if i < 8:
                    dev_id_list.append(f'0000:{dlb_list[pf]}:00.{i}')
                elif 7 < i < 16:
                    dev_id_list.append(f'0000:{dlb_list[pf]}:01.{i - 8}')
                else:
                    dev_id_list.append(f'0000:{dlb_list[pf]}:0{quotient}.{remainder}')  # ['0000:6d:00.1','0000:6d:00.2']
        return dev_id_list  # ['0000:6d:00.0','0000:72:00.0']


    def get_mdev_xml_content(self, mdev_uuid):
        content = '<hostdev mode="subsystem" type="mdev" managed="no" model="vfio-pci" display="off">\n'
        content += '    <source>\n'
        content += f'        <address uuid="{mdev_uuid}"/>\n'
        content += '    </source>\n'
        content += '</hostdev>\n\n'
        return content


    def get_qat_dev_id_list(self, pf, vf_num):
        """
              Purpose: Get list of QAT device ID
              Args:
                  pf: which QAT pf need to search, input number of the device
                        eg: 0,1...8,begin from 0
                  vf_num: which QAT vf number need to search
                        eg:1,2....16,begin from 1
              Returns:
                  Yes: QAT device id list
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Check all QAT device
                        get_qat_dev_id_list(0, 2)
                        return --> ['0000:6b:00.1', '0000:6b:00.2']
        """
        dev_list = []
        for i in range(1, vf_num+1):
            dev_id = self.get_dev_id('qat', pf, i)
            dev_list.append(dev_id)
        return dev_list


    def get_ifwi_version(self):
        _, out, err = self.sut.execute_shell_cmd('dmidecode -t 0 |grep -i "version"', timeout=60)
        line_list = out.strip().split('.')
        ifwi_ver = str(line_list[2]) + '.' + str(line_list[3])
        return ifwi_ver

    def init_bashrc(self):
        """
              Purpose: Clear /root/.bashrc environment
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Clear /root/.bashrc environment
                      init_bashrc()
        """
        self.sut.execute_shell_cmd('rm -rf /root/.bashrc', timeout=60)
        self.sut.upload_to_remote(localpath=BASHRC_H, remotepath=BASHRC_PATH_L)

    def install_socwatch(self):
        """
                 Purpose: Install socwatch tool
                 Args:
                     No
                 Returns:
                     No
                 Raises:
                     RuntimeError: If any errors
                 Example:
                     Simplest usage: Install socwatch tool
                         install_socwatch()
           """
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=SOCWATCH_PATH_L)
        self.sut.upload_to_remote(localpath=SOCWATCH_H, remotepath=SOCWATCH_PATH_L)
        self.sut.execute_shell_cmd('tar -zxvf *.tar.gz', timeout=60, cwd=SOCWATCH_PATH_L)
        _, out, err = self.sut.execute_shell_cmd('sh ./build_drivers.sh', timeout=60, cwd=f'{SOCWATCH_PATH_L}*/')
        # self.__check_error(err)
        res, out, err = self.sut.execute_shell_cmd('insmod drivers/socwatch2_14.ko | wc -l', timeout=60, cwd=f'{SOCWATCH_PATH_L}*/')
        if out != '0\n':
            logger.error('insmod socwatch.ko fail')
            raise Exception('insmod socwatch.ko fail')
        _, out, err = self.sut.execute_shell_cmd('source ./setup_socwatch_env.sh', timeout=60, cwd=f'{SOCWATCH_PATH_L}*/')
        self.check_keyword(['SOCWATCH_BASE_DIR', 'SOCPERF_BASE_DIR'], out, 'config environment fail')

    def install_accel_config_rich_vm(self, qemu):
        self.install_accel_config_deps_rich_vm(qemu)
        self.upload_dsa_tools_rich_vm(qemu)
        self.kernel_header_devel_rich_vm(qemu)
        self.kernel_header_internal_devel_rich_vm(qemu)
        exec_res = qemu.execute_rich_vm_cmd_parallel('accel-config --version')
        accel_config_install = 0
        for vm in exec_res:
            err = exec_res[vm][2]
            line_list = err.split('\n')
            if 'command not found' in line_list[0]:
                accel_config_install = 1
                break
        if accel_config_install:
            qemu.execute_rich_vm_cmd_parallel('unzip *.zip', cwd=f'{DSA_PATH_L}')
            qemu.execute_rich_vm_cmd_parallel('./autogen.sh', timeout=10 * 60, cwd=f'{DSA_PATH_L}*/')
            qemu.execute_rich_vm_cmd_parallel(
                "./configure CFLAGS='-g -O2' --prefix=/usr --sysconfdir=/etc --libdir=/usr/lib64 --enable-test=yes",
                timeout=10 * 60, cwd=f'{DSA_PATH_L}*/')
            qemu.execute_rich_vm_cmd_parallel('make', timeout=20 * 60, cwd=f'{DSA_PATH_L}*/')
            qemu.execute_rich_vm_cmd_parallel('make install', timeout=20 * 60, cwd=f'{DSA_PATH_L}*/')


    def install_accel_config_deps_rich_vm(self, qemu):
        exec_res = qemu.execute_rich_vm_cmd_parallel(f"yum groupinstall -y \'Development Tools\' --allowerasing", timeout=10*60)
        for vm in exec_res:
            res = exec_res[vm][0]
            Case.expect('yum install Development Tools pass', res == 0)

        exec_res1 =qemu.execute_rich_vm_cmd_parallel('yum install -y autoconf automake libtool pkgconf rpm-build rpmdevtools', timeout=10*60)
        for vm in exec_res1:
            res = exec_res1[vm][0]
            Case.expect('yum install Development Tools pass', res == 0)
        exec_res2 = qemu.execute_rich_vm_cmd_parallel('yum install -y asciidoc xmlto libuuid-devel json-c-devel kmod-devel libudev-devel', timeout=10*60)
        for vm in exec_res2:
            res = exec_res2[vm][0]
            Case.expect('yum install Development Tools pass', res == 0)

    def kernel_header_devel(self):
        """
              Purpose: Install kernel-header and kernel-devel package
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Install kernel-header and kernel-devel package
                      kernel_header_devel()
        """
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=KERNEL_HEADER_PATH_L)
        # self.sut.upload_to_remote(localpath=KERNEL_HEADER_H, remotepath=KERNEL_HEADER_PATH_L)
        self.sut.upload_to_remote(localpath=KERNEL_DEVEL_H, remotepath=KERNEL_DEVEL_PATH_L)
        self.sut.execute_shell_cmd('rpm -ivh *.rpm --force --nodeps', timeout=5*60, cwd=KERNEL_DEVEL_PATH_L)

    def linpack_stress(self):
        """
              Purpose: Run linpack stress overnight
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Run linpack stress overnight
                        linpack_stress()
        """
        self.sut.execute_shell_cmd('yum -y install docker', timeout=10*60)
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=LINPACK_PATH_L)
        self.sut.upload_to_remote(localpath=LINPACK_H, remotepath=LINPACK_PATH_L)
        self.sut.execute_shell_cmd('unzip *.zip', timeout=10 * 60, cwd=LINPACK_PATH_L)
        # self.add_environment_to_file('end', 'end=$((SECONDS+300))')
        self.sut.execute_shell_cmd('while [ $SECONDS -lt 300 ]; do /home/BKCPkg/domains/accelerator/linpack/pnpwls-master/linpack/run_linpack.sh avx3 ; done | tee /root/linpack.log',timeout=50000)
        _, out, err =self.sut.execute_shell_cmd('cat /root/linpack.log')
        self.check_keyword("1 tests completed and passed residual checks", out, 'Run Linpark stress fail')
        self.sut.download_to_local(remotepath='/root/linpack.log', localpath=os.path.join(LOG_PATH, 'Logs'))
        self.sut.execute_shell_cmd('rm -rf linpack.log', timeout=60, cwd='/root/')
        self.delete_environment('end')

    def mlc_stress(self):
        """
              Purpose: Run mlc stress overnight
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Run mlc stress overnight
                        mlc_stress()
        """
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=MLC_PATH_L)
        self.sut.upload_to_remote(localpath=MLC_H, remotepath=MLC_PATH_L)
        self.sut.execute_shell_cmd('tar -zxvf *.tgz', timeout=10 * 60, cwd=MLC_PATH_L)
        self.sut.execute_shell_cmd('chmod 777 *', timeout=60, cwd=f'{MLC_PATH_L}Linux/')
        _, out, err = self.sut.execute_shell_cmd('./mlc --loaded_latency -t5 -X -D8192 > mlc.log', timeout=50000, cwd=f'{MLC_PATH_L}Linux/')
        self.__check_error(err)
        self.sut.download_to_local(remotepath='/home/BKCPkg/domains/accelerator/mlc/Linux/mlc.log', localpath=os.path.join(LOG_PATH, 'Logs'))

    def modify_qat_config_file(self, config_key):
        """
              Purpose: Modify QAT config files
              Args:
                  config_key : Which function (asym, mdev, shim) config files need to modify
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Modify QAT asymmetric encrypted config files
                        modify_qat_config_file('asym')
        """
        if config_key == 'mdev':
            self.__qat_mdev_config()
        elif config_key == 'asym':
            self.__qat_asym_config()
        elif config_key == 'shim':
            self.__qat_shim_config()
        else:
            logger.error('Input correct config keyword')
            raise Exception('Input correct config keyword')

    def modify_kernel_grub(self, vm_function, add_or_remove=True):
        """
              Purpose: Modify kernel grub file
              Args:
                  vm_function: What config need to add/remove to grub file
                  add_or_remove: Is add or remove config file
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Add 'intel_iommu=on,sm_on iommu=on no5lvl' function to kernel grub file
                      modify_kernel_grub('intel_iommu=on,sm_on iommu=on no5lvl', True)
        """

        _, out, err = self.sut.execute_shell_cmd('uname -r', timeout=60)
        if add_or_remove:
            self.sut.execute_shell_cmd(f'grubby --update-kernel=/boot/vmlinuz-{out.strip()} --args="{vm_function}"', timeout=60)
            # self.sut.execute_shell_cmd('reboot', timeout=30 * 60)
            # self.Case.sleep(60)
            # self.Case.wait_and_expect(f'SUT in OS', 30 * 60, self.sut.check_system_in_os)
            self.my_os.warm_reset_cycle_step(self.sut)
            self.Case.sleep(60)
            _, out, _ = self.sut.execute_shell_cmd('cat /proc/cmdline')
            if vm_function not in out:
                logger.error('modify kernel file fail')
                raise Exception('modify kernel file fail')
        else:
            self.sut.execute_shell_cmd(f'grubby --update-kernel=/boot/vmlinuz-{out.strip()} --remove-args="{vm_function}"', timeout=60)
            # self.sut.execute_shell_cmd('reboot', timeout=30*60)
            # self.Case.sleep(60)
            # self.Case.wait_and_expect(f'SUT in OS', 30*60, self.sut.check_system_in_os)
            self.my_os.warm_reset_cycle_step(self.sut)
            self.Case.sleep(60)
            _, out, _ = self.sut.execute_shell_cmd('cat /proc/cmdline')
            if vm_function in out:
                logger.error('modify kernel file fail')
                raise Exception('modify kernel file fail')

    def modify_kernel_grub_rich_vm(self, qemu, vm_function, add_or_remove):
        """
              Purpose: Modify kernel grub file
              Args:
                  qemu: Call VM Class RichHypervisor
                  vm_function: What config need to add/remove to grub file
                  add_or_remove: Is add or remove config file
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Add 'intel_iommu=on,sm_on iommu=on no5lvl' function to kernel grub file in VM
                      modify_kernel_grub_rich_vm(qemu,'intel_iommu=on,sm_on iommu=on no5lvl', True)
        """
        exec_res = qemu.execute_rich_vm_cmd_parallel('uname -r', timeout=60)
        out=''
        for vm in exec_res:
            out = exec_res[vm][1]
            return out
        if add_or_remove:
            qemu.execute_rich_vm_cmd_parallel(f"grubby --update-kernel=/boot/vmlinuz-{out.strip()} --args='{vm_function}'",
                                timeout=60)
            qemu.execute_rich_vm_cmd_parallel('reboot', timeout=30 * 60)
            self.Case.sleep(2*60)
            exec_res = qemu.execute_rich_vm_cmd_parallel('cat /proc/cmdline')
            for vm in exec_res:
                out = exec_res[vm][1]
                if vm_function not in out:
                    logger.error('modify kernel file fail')
                    raise Exception('modify kernel file fail')
        else:
            qemu.execute_rich_vm_cmd_parallel(f"grubby --update-kernel=/boot/vmlinuz-{out.strip()} --remove-args='{vm_function}'", timeout=60)
            qemu.execute_rich_vm_cmd_parallel('reboot', timeout=30 * 60)
            self.Case.sleep(2*60)
            exec_res = qemu.execute_rich_vm_cmd_parallel('cat /proc/cmdline')
            for vm in exec_res:
                out = exec_res[vm][1]
                if vm_function in out:
                    logger.error('modify kernel file fail')
                    raise Exception('modify kernel file fail')


    def openssl_asymmetric(self):
        """
              Purpose: Run openssl asymmetric
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Run openssl asymmetric
                      openssl_asymmetric()
        """
        _, out, err = self.sut.execute_shell_cmd('openssl engine -t -c -v qatengine', timeout=60, cwd=f'{QAT_ENGINE_PATH_L}QAT_Engine-master/')
        self.check_keyword(['available'], out, 'run openssl engine fail')
        self.__qat_asym_config()
        self.check_qat_service_status()
        _, out, err = self.sut.execute_shell_cmd('openssl speed -engine qatengine -elapsed -async_jobs 72 rsa2048', timeout=60, cwd=f'{QAT_ENGINE_PATH_L}QAT_Engine-master/')
        # self.__check_error(err)
        self.sut.execute_shell_cmd('dos2unix QAT_Linux_OpenSSL_Speed_Test_Script_Asymmetric.sh', timeout=60, cwd=f'{QAT_ASYM_PATH_L}')
        self.sut.execute_shell_cmd('chmod 777 *', timeout=60, cwd=f'{QAT_ASYM_PATH_L}')
        _, out, err = self.sut.execute_shell_cmd('./QAT_Linux_OpenSSL_Speed_Test_Script_Asymmetric.sh', timeout=30*60, cwd=f'{QAT_ASYM_PATH_L}')
        # self.__check_error(err)

    def openssl_install(self):
        """
              Purpose: Install openssl file
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Install openssl file
                        openssl_install()
        """
        self.sut.execute_shell_cmd('yum -y install perl-core', timeout=10*60)
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=OPENSSL_PATH_L)
        self.sut.upload_to_remote(localpath=OPENSSL_H, remotepath=OPENSSL_PATH_L)
        self.sut.execute_shell_cmd('unzip *.zip', timeout=60, cwd=OPENSSL_PATH_L)
        _, out, err = self.sut.execute_shell_cmd(f'find {OPENSSL_PATH_L} -name "config"')
        name = os.path.split(out)
        self.sut.execute_shell_cmd(f'mv {name[0]} {OPENSSL_PATH_L}openssl-master/', timeout=60)
        # self.sut.execute_shell_cmd('mv openssl*/ openssl-master/', timeout=60, cwd=OPENSSL_PATH_L)
        self.sut.execute_shell_cmd('chmod 777 *', timeout=60, cwd=f'{OPENSSL_PATH_L}openssl-master/')
        self.sut.execute_shell_cmd('./config --prefix=/usr/local/ssl', timeout=10*60, cwd=f'{OPENSSL_PATH_L}openssl-master/')
        _, out, err = self.sut.execute_shell_cmd('make', timeout=20*60, cwd=f'{OPENSSL_PATH_L}openssl-master/')
        # self.__check_error(err)
        self.check_keyword('error', out, 'openssl make fail')
        _, out, err = self.sut.execute_shell_cmd('make test', timeout=20*60, cwd=f'{OPENSSL_PATH_L}openssl-master/')
        self.check_keyword(['Result: PASS'], out, 'Openssl test fail')
        self.__check_error(err)
        _, out, err = self.sut.execute_shell_cmd('make install', timeout=20*60, cwd=f'{OPENSSL_PATH_L}openssl-master/')
        # self.__check_error(err)
        self.add_environment_to_file('PERL5LIB', 'export PERL5LIB=$PERL5LIB:/home/BKCPkg/domains/accelerator/openssl/openssl-master')
        self.add_environment_to_file('OPENSSL_ENGINES', 'export OPENSSL_ENGINES=/usr/lib64/engines-1.1')
        self.add_environment_to_file('LD_LIBRARY_PATH', 'export LD_LIBRARY_PATH=$LD_LIBRARY_PATH:/usr/lib')

    def openssl_symmetric(self):
        """
              Purpose: Run openssl symmetric
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Run openssl symmetric
                      openssl_symmetric()
        """
        _, out, err = self.sut.execute_shell_cmd('openssl engine -t -c -v qatengine', timeout=10*60, cwd=f'{QAT_ENGINE_PATH_L}QAT_Engine-master/')
        self.check_keyword(['available'], out, 'run openssl engine fail')
        self.sut.execute_shell_cmd('dos2unix QAT_Linux_OpenSSL_Speed_Test_Script_Symmetric.sh', timeout=60, cwd=f'{QAT_SYM_PATH_L}')
        self.sut.execute_shell_cmd('chmod 777 *', timeout=60, cwd=f'{QAT_SYM_PATH_L}')
        _, out, err = self.sut.execute_shell_cmd('./QAT_Linux_OpenSSL_Speed_Test_Script_Symmetric.sh', timeout=30*60, cwd=f'{QAT_SYM_PATH_L}')
        # self.__check_error(err)

    def prime95_stress(self):
        """
              Purpose: Run prime95 stress overnight
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Run prime95 stress overnight
                      prime95_stress()
        """
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=PRIME95_PATH_L)
        self.sut.upload_to_remote(localpath=PRIME95_H, remotepath=PRIME95_PATH_L, timeout=10*60)
        self.sut.execute_shell_cmd('tar -zxvf *.tar.gz', timeout=10 * 60, cwd=PRIME95_PATH_L)
        self.sut.upload_to_remote(localpath=PPEXPECT_H, remotepath=PPEXPECT_prime95_PATH_L)
        self.sut.upload_to_remote(localpath=PRIME95_SCRIPT_H, remotepath=PRIME95_SCRIPT_PATH_L)
        ret, out, err = self.sut.execute_shell_cmd(f'python3 prime95.py run_prime95', timeout=7200*60, cwd=PRIME95_PATH_L)
        self.__check_error(err)
        self.sut.download_to_local(remotepath=f'{PRIME95_PATH_L}primeprime.log', localpath=os.path.join(LOG_PATH, 'Logs'))
        self.sut.download_to_local(remotepath=f'{PRIME95_PATH_L}prime95.log', localpath=os.path.join(LOG_PATH, 'Logs'))
        _, out, err = self.sut.execute_shell_cmd(f'cat {PRIME95_PATH_L}primeprime.log', timeout=60)
        self.__check_error(err)
        _, out, err = self.sut.execute_shell_cmd(f'cat {PRIME95_PATH_L}prime95.log', timeout=60)
        self.__check_error(err)

    def ptu_stress(self):
        """
              Purpose: Run ptu stress overnight
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Run ptu stress overnight
                        ptu_stress()
        """
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=PTU_PATH_L)
        self.sut.upload_to_remote(localpath=PTU_H, remotepath=PTU_PATH_L)
        self.sut.execute_shell_cmd('unzip *.zip', timeout=10 * 60, cwd=PTU_PATH_L)
        self.sut.execute_shell_cmd('chmod 777 *', timeout=60, cwd=f'{PTU_PATH_L}')
        try:
            _, out, err = self.sut.execute_shell_cmd('./ptu -ct 8 > ptu.log', timeout=300, cwd=f'{PTU_PATH_L}')
        except Exception:
            pass
        self.sut.download_to_local('/home/BKCPkg/domains/accelerator/ptu/ptu.log', os.path.join(LOG_PATH, 'Logs'))
        _, out, err = self.sut.execute_shell_cmd('cat ptu.log', timeout=60, cwd=f'{PTU_PATH_L}')
        if 'error' in out:
            logger.error('Run ptu stress fail')
            raise Exception('Run ptu stress fail')

    def qat_engine_install(self):
        """
              Purpose: Install QAT Engine file
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Install QAT Engine file
                        qat_engine_install()
        """
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=QAT_ENGINE_PATH_L)
        self.sut.upload_to_remote(localpath=QAT_ENGINE_H, remotepath=QAT_ENGINE_PATH_L)
        self.sut.execute_shell_cmd('unzip *.zip', timeout=60, cwd=QAT_ENGINE_PATH_L)
        _, out, err = self.sut.execute_shell_cmd(f'find {QAT_ENGINE_PATH_L} -name "autogen.sh"')
        name = os.path.split(out)
        self.sut.execute_shell_cmd(f'mv {name[0]} {QAT_ENGINE_PATH_L}QAT_Engine-master/', timeout=60)
        self.sut.execute_shell_cmd('chmod 777 *', timeout=60, cwd=f'{QAT_ENGINE_PATH_L}QAT_Engine-master/')
        self.sut.execute_shell_cmd('dos2unix *', timeout=60, cwd=f'{QAT_ENGINE_PATH_L}QAT_Engine-master/')
        _, out, err = self.sut.execute_shell_cmd('./autogen.sh', timeout=20*60, cwd=f'{QAT_ENGINE_PATH_L}QAT_Engine-master/')
        # self.__check_error(err)
        _, out, err = self.sut.execute_shell_cmd('./configure  --with-qat_hw_dir=/home/BKCPkg/domains/accelerator/QAT', timeout=20*60, cwd=f'{QAT_ENGINE_PATH_L}QAT_Engine-master/')
        self.__check_error(err)
        self.sut.execute_shell_cmd('sed -i "s/cpa_dc.h/dc\/cpa_dc.h/g" /home/BKCPkg/domains/accelerator/QAT/quickassist/lookaside/access_layer/include/icp_sal_user.h', timeout=60)
        _, out, err = self.sut.execute_shell_cmd('make install', timeout=20*60, cwd=f'{QAT_ENGINE_PATH_L}QAT_Engine-master/')
        self.__check_error(err)

    def qat_engine_uninstall(self):
        """
              Purpose: Uninstall QAT Engine
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Uninstall QAT Engine file
                        qat_engine_uninstall()
        """
        _, out, err = self.sut.execute_shell_cmd('make uninstall', timeout=60, cwd=f'{QAT_ENGINE_PATH_L}QAT_Engine-master/')
        self.__check_error(err)
        _, out, err = self.sut.execute_shell_cmd('make clean', timeout=60, cwd=f'{QAT_ENGINE_PATH_L}QAT_Engine-master/')
        self.__check_error(err)
        _, out, err = self.sut.execute_shell_cmd('make distclean', timeout=60, cwd=f'{QAT_ENGINE_PATH_L}QAT_Engine-master/')
        self.__check_error(err)

    def qat_install(self, is_siov=False):
        """
              Purpose: To install QAT driver
              Args:
                  is_siov: Install qat driver with siov or not
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Install QAT driver
                      qat_install(False)
        """
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=QAT_DRIVER_PATH_L)
        self.sut.upload_to_remote(localpath=QAT_DRIVER_H, remotepath=QAT_DRIVER_PATH_L)
        self.sut.execute_shell_cmd('unzip *.zip', timeout=60, cwd=QAT_DRIVER_PATH_L)
        self.sut.execute_shell_cmd('tar -zxvf *.tar.gz', timeout=60, cwd=QAT_DRIVER_PATH_L)
        if is_siov:
            self.sut.execute_shell_cmd('./configure --enable-icp-sriov=host', timeout=5*60, cwd=QAT_DRIVER_PATH_L)
        else:
            self.sut.execute_shell_cmd('./configure', timeout=5*60, cwd=QAT_DRIVER_PATH_L)
        _, out, err = self.sut.execute_shell_cmd('make install', timeout=5*60, cwd=QAT_DRIVER_PATH_L)
        # self.__check_error(err)
        _, out, err = self.sut.execute_shell_cmd('make samples-install', timeout=5*60, cwd=QAT_DRIVER_PATH_L)
        # self.__check_error(err)
        _, out, err = self.sut.execute_shell_cmd('lsmod | grep qat', timeout=60)
        self.__check_error(err)
        line_list = out.strip().split('\n')
        key_list = ['qat_4xxx', 'intel_qat']
        for kw in key_list:
            for line in line_list:
                item_list = line.split()
                if kw in item_list[0]:
                    break
            else:
                logger.error('Issue - QAT driver install failed')
                raise Exception('Issue - QAT driver install failed')

    def qat_service_restart(self):
        """
              Purpose: Check QAT restart status
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: run qat_service restart
                        qat_service_restart()
        """
        out = self.__qat_service_restart()
        self.check_keyword(['Stopping all devices', 'Starting all devices'], out, 'QAT service status down')

    def qat_service_status(self):
        """
              Purpose: Run QAT service status
              Args:
                  No
              Returns:
                  QAT service status result
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: run qat_service status
                        qat_service_status()
        """
        _, out, err = self.sut.execute_shell_cmd('service qat_service status', timeout=10*60)
        if "Unit qat_service.service could not be found" in err:
            _, out, err = self.sut.execute_shell_cmd('qat_service status', timeout=10*60)
            return out
        return out

    def qat_service_stop_start(self):
        """
             Purpose: Check QAT service stop and QAT service start function
             Args:
                 No
             Returns:
                 No
             Raises:
                 RuntimeError: If any errors
             Example:
                 Simplest usage: run qat_service stop and qat_service start
                       qat_service_stop_start()
       """
        cpu_num = self.get_cpu_num()
        _, out, err = self.sut.execute_shell_cmd('service qat_service stop', timeout=10*60)
        line_list = out.strip().split('\n')
        dev_num = 0
        for line in line_list:
            if 'Stopping device qat_dev' in line:
                dev_num += 1
        if dev_num != cpu_num * 16 * self.qat_device_num:
            logger.error('Not all QAT vf stopped')
            raise Exception('Not all QAT vf stopped')
        _, out, err = self.sut.execute_shell_cmd('service qat_service start', timeout=10*60)
        line_list = out.strip().split('\n')
        dev_num = 0
        for line in line_list:
            if 'state: up' in line:
                dev_num += 1
        if dev_num != cpu_num * self.qat_device_num:
            logger.error('Not all QAT pf status show up')
            raise Exception('Not all QAT pf status show up')

    def qat_stress(self):
        """
              Purpose: Run QAT stress overnight
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Run QAT stress overnight
                        qat_stress()
        """
        # self.add_environment_to_file('end', 'end=$((SECONDS+300))')
        self.sut.execute_shell_cmd('while [ $SECONDS -lt 300 ]; do /home/BKCPkg/domains/accelerator/QAT/build/cpa_sample_code runTests=63 signOfLife=1 | tee /root/qat.log; done ', timeout=50000)
        self.sut.download_to_local(remotepath='/root/qat.log', localpath=os.path.join(LOG_PATH, 'Logs'))
        _, out, err = self.sut.execute_shell_cmd('cat /root/qat.log')
        self.check_keyword(["Sample code completed successfully"], out, 'Run qat stress fail')
        self.sut.execute_shell_cmd('rm -rf qat.log', timeout=60, cwd='/root/')
        self.delete_environment('end')

    def qat_stv_mega_test(self):
        """
              Purpose: Run QAT mega test
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Run QAT mega test
                      qat_stv_mega_test()
        """
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=SAMPLE_CODE_PATH_L)
        self.sut.upload_to_remote(localpath=SAMPLE_CODE_H, remotepath=SAMPLE_CODE_PATH_L, timeout=10*60)
        self.sut.execute_shell_cmd('tar -zxvf *.tar.gz', timeout=10*60, cwd=SAMPLE_CODE_PATH_L)
        self.sut.execute_shell_cmd('./build.sh', timeout=10*60, cwd=SAMPLE_CODE_PATH_L)
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=MEGA_CONF_PATH_L)
        self.sut.upload_to_remote(localpath=MEGA_CONF_H, remotepath=MEGA_CONF_PATH_L)
        def __copy_mega_to_config():
            cpu_num = self.get_cpu_num()
            for i in range(cpu_num*self.qat_device_num):
                self.sut.execute_shell_cmd(f'cp /home/BKCPkg/domains/accelerator/mega_conf/mega.conf /etc/4xxx_dev{i}.conf', timeout=60)
        __copy_mega_to_config()
        self.sut.execute_shell_cmd('./build/adf_ctl restart', timeout=60, cwd=QAT_DRIVER_PATH_L)
        self.sut.upload_to_remote(localpath=PPEXPECT_H, remotepath=PPEXPECT_MEGA_PATH_L)
        self.sut.upload_to_remote(localpath=MEGA_SCRIPT_H, remotepath=MEGA_SCRIPT_PATH_L)
        ret, out, err = self.sut.execute_shell_cmd(f'python3 mega_script.py run_testcli', cwd=MEGA_SCRIPT_PATH_L)
        self.__check_error(err)
        self.sut.download_to_local(remotepath=f'{MEGA_SCRIPT_PATH_L}mega.log', localpath=os.path.join(LOG_PATH, 'Logs'))
        _, out, err = self.sut.execute_shell_cmd(f'cat {MEGA_SCRIPT_PATH_L}mega.log', timeout=60)
        mega_list = out.strip().split('\n')
        tms_pass_num = 0
        for line in mega_list:
            if 'TMS PASSED' in line:
                tms_pass_num += 1
        if tms_pass_num != 7:
            logger.error(err)
            raise Exception(err)

    def qat_vm_mega_install(self, qemu, vm_name):
        """
              Purpose: Run QAT mega test on guest
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Run QAT mega test
                      qat_vm_mega_install()
        """
        qemu.execute_vm_cmd(vm_name, f'pip3 install pexpect', timeout=5 * 60)
        qemu.execute_vm_cmd(vm_name, f'yum install -y epel-release readline-devel  lz4-devel python3 xxhash-devel', timeout=5 * 60)
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=SAMPLE_CODE_PATH_L)
        self.sut.upload_to_remote(localpath=SAMPLE_CODE_H, remotepath=SAMPLE_CODE_PATH_L, timeout=10 * 60)
        qemu.execute_vm_cmd(vm_name, f'mkdir -p {SAMPLE_CODE_PATH_L}', timeout=10 * 60)
        qemu.execute_vm_cmd(vm_name, f'rm -rf {SAMPLE_CODE_PATH_L}*', timeout=10 * 60)
        sut_file_dir = f'{SAMPLE_CODE_PATH_L}{SAMPLE_CODE_NAME}'
        vm_file_dir = f'{SAMPLE_CODE_PATH_L}{SAMPLE_CODE_NAME}'
        qemu.upload_to_vm(vm_name, sut_file_dir, vm_file_dir)
        qemu.execute_vm_cmd(vm_name, f'tar -zxf *.tar.gz', timeout=10 * 60, cwd=SAMPLE_CODE_PATH_L)
        qemu.execute_vm_cmd(vm_name, f'./build.sh', timeout=10 * 60, cwd=SAMPLE_CODE_PATH_L)
        self.sut.upload_to_remote(localpath=PPEXPECT_H, remotepath=PPEXPECT_MEGA_PATH_L)
        qemu.execute_vm_cmd(vm_name, f'mkdir -p {PPEXPECT_MEGA_PATH_L}', timeout=10 * 60)
        qemu.execute_vm_cmd(vm_name, f'rm -rf {PPEXPECT_MEGA_PATH_L}*', timeout=10 * 60)
        sut_file_dir = f'{PPEXPECT_MEGA_PATH_L}{PPEXPECT_NAME}'
        vm_file_dir = f'{PPEXPECT_MEGA_PATH_L}{PPEXPECT_NAME}'
        qemu.upload_to_vm(vm_name, sut_file_dir, vm_file_dir)
        self.sut.upload_to_remote(localpath=MEGA_SCRIPT_H, remotepath=MEGA_SCRIPT_PATH_L)
        sut_file_dir = f'{MEGA_SCRIPT_PATH_L}{MEGA_SCRIPT_NAME}'
        vm_file_dir = f'{MEGA_SCRIPT_PATH_L}{MEGA_SCRIPT_NAME}'
        qemu.upload_to_vm(vm_name, sut_file_dir, vm_file_dir)

    def qat_uninstall(self):
        """
              Purpose: To uninstall QAT driver
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Uninstall QAT driver
                      qat_uninstall()
        """
        _, out, err = self.sut.execute_shell_cmd("lsmod | grep 'qat\|usdm' | wc -l", timeout=60, cwd=QAT_DRIVER_PATH_L)
        if out != '':
            if out != '0\n':
                # self.sut.execute_shell_cmd('reboot', timeout=30*60)
                # self.Case.sleep(60)
                # self.Case.wait_and_expect(f'SUT in OS', 30*60, self.sut.check_system_in_os)
                self.my_os.warm_reset_cycle_step(self.sut)
                self.Case.sleep(60)
                self.sut.execute_shell_cmd('make uninstall', timeout=10*60, cwd=QAT_DRIVER_PATH_L)
                self.sut.execute_shell_cmd('make clean', timeout=60, cwd=QAT_DRIVER_PATH_L)
                self.sut.execute_shell_cmd('make distclean', timeout=60, cwd=QAT_DRIVER_PATH_L)
                _, out, err = self.sut.execute_shell_cmd("lsmod | grep 'qat\|usdm' | wc -l", timeout=60,
                                                         cwd=QAT_DRIVER_PATH_L)
                self.check_keyword(['0'], out, 'Issue - QAT driver still exist')
                self.__check_error(err)
            else:
                pass
        else:
            pass


    def qatzip_test(self):  #qatzip_script-->qatzip.sh
        """
              Purpose: Install QATZIP file and test QATZIP
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Install QATZIP file and test QATZIP
                        qatzip_test()
        """
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=QATZIP_SCRIPT_PATH_L)
        self.sut.upload_to_remote(localpath=QATZIP_SCRIPT_H, remotepath=QATZIP_SCRIPT_PATH_L)
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=QATZIP_PATH_L)
        self.sut.upload_to_remote(localpath=QATZIP_H, remotepath=QATZIP_PATH_L)
        self.sut.execute_shell_cmd('unzip *.zip', timeout=60, cwd=QATZIP_PATH_L)
        _, out, err = self.sut.execute_shell_cmd(f'find {QATZIP_PATH_L} -name "qatzip.spec.in"')
        name = os.path.split(out)
        self.sut.execute_shell_cmd(f'mv {name[0]} {QATZIP_PATH_L}QATzip-master/', timeout=60)
        # self.sut.execute_shell_cmd('mv qatzip*/qatzip*/ QATzip-master/', timeout=60, cwd=QATZIP_PATH_L)
        self.sut.execute_shell_cmd('cp *.conf /etc', timeout=60, cwd=f'{QATZIP_PATH_L}QATzip-master/config_file/c6xx/multiple_process_opt/')
        self.add_environment_to_file('ICP_ROOT', 'export ICP_ROOT=/home/BKCPkg/domains/accelerator/QAT/')
        self.add_environment_to_file('QATZIP_ROOT', 'export QATZIP_ROOT=/home/BKCPkg/domains/accelerator/QATzip-master/')
        self.sut.execute_shell_cmd('chmod 777 *', timeout=5 * 60, cwd=f'{QATZIP_PATH_L}QATzip-master/')
        self.sut.execute_shell_cmd('./configure', timeout=5*60, cwd=f'{QATZIP_PATH_L}QATzip-master/')
        ker_ver = self.kernel_version()
        if ker_ver <= self.CENTOS_INTEL_NEXT_KERNEL:
            self.sut.execute_shell_cmd('make clean', timeout=60, cwd=f'{QATZIP_PATH_L}QATzip-master/')
        _, out, err = self.sut.execute_shell_cmd('make all install', timeout=5*60, cwd=f'{QATZIP_PATH_L}QATzip-master/')
        self.__check_error(err)
        self.qat_service_restart()
        self.check_qat_service_status()
        self.sut.execute_shell_cmd('chmod 777 *', timeout=60, cwd=QATZIP_SCRIPT_PATH_L)
        self.sut.execute_shell_cmd('dos2unix qatzip.sh', timeout=60, cwd=QATZIP_SCRIPT_PATH_L)
        _, out, err = self.sut.execute_shell_cmd('sh qatzip.sh', timeout=10*60, cwd=QATZIP_SCRIPT_PATH_L)
        self.check_keyword(['Test finished'], out, 'QATZIP test fail')

    def rpm_install(self):
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
                      rpm_install()
        """
        rpm_list = ['openssl-devel', 'libcurl-devel', 'protobuf-devel', 'yum-utils.noarch', 'zlib-devel.x86_64',
                    'yasm systemd-devel', 'boost-devel.x86_64', 'libnl3-devel', 'gcc gcc-c++',
                    'libgudev.x86_64', 'libgudev-devel.x86_64', 'systemd*', 'boost-devel.x86_64', 'autoconf',
                    'automake', 'libtool', 'pkgconf', 'rpm-build', 'rpmdevtools', 'asciidoc', 'xmlto', 'libuuid-devel',
                    'json-c-devel', 'kmod-devel', 'libudev-devel', 'qemu*', 'abrt-cli', 'epel-release', 'autoconf',
                    'automake', 'libtool', 'pkgconf', 'rpm-build', 'rpmdevtools', 'asciidoc', 'xmlto', 'libuuid-devel',
                    'json-c-devel', 'kmod-devel', 'libudev-devel', 'msr-tools', 'epel-release', 'readline-devel',
                    'xxhash-devel', 'lz4-devel', 'qemu-kvm', 'python3-libvirt.x86_64']
        self.add_environment_to_file('http_proxy', 'export http_proxy=http://proxy-iind.intel.com:911')
        self.add_environment_to_file('HTTP_PROXY', 'export HTTP_PROXY=http://proxy-iind.intel.com:911')
        self.add_environment_to_file('https_proxy', 'export https_proxy=http://proxy-iind.intel.com:911')
        self.add_environment_to_file('HTTPS_PROXY', 'export HTTPS_PROXY=http://proxy-iind.intel.com:911')
        self.add_environment_to_file('no_proxy', "export no_proxy='localhost,127.0.0.1,intel.com,.intel.com'")
        self.sut.execute_shell_cmd('yum groupinstall -y "Development Tools" --allowerasing', timeout=100*60)
        self.sut.execute_shell_cmd('dnf update --nogpg --allowerasing -y', timeout=100 * 60)
        for rpm in rpm_list:
            self.sut.execute_shell_cmd(f'yum -y install {rpm}', timeout=60000)

    def run_dpdk(self):
        """
              Purpose: Install and Run DPDK test
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Install and Run DPDK test
                      run_dpdk()
        """
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=DLB_DRIVER_PATH_L)
        self.sut.upload_to_remote(localpath=DLB_DRIVER_H, remotepath=DLB_DRIVER_PATH_L)
        self.sut.execute_shell_cmd('unzip *.zip', timeout=60, cwd=DLB_DRIVER_PATH_L)
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=DPDK_DRIVER_PATH_L)
        self.sut.upload_to_remote(localpath=DPDK_DRIVER_H, remotepath=DPDK_DRIVER_PATH_L)
        # self.sut.execute_shell_cmd('unzip *.zip', timeout=60, cwd=DPDK_DRIVER_PATH_L)
        self.sut.execute_shell_cmd('tar xfJ *.tar.xz', timeout=60, cwd=DPDK_DRIVER_PATH_L)
        _, out, err = self.sut.execute_shell_cmd('patch -Np1 < /home/BKCPkg/domains/accelerator/dlb/dpdk/*.patch', timeout=60, cwd=f'{DPDK_DRIVER_PATH_L}*/')
        # self.check_keyword(['succeeded'], out, 'DPDK load patch fail')
        self.__check_error(err)
        self.add_environment_to_file('DPDK_DIR', 'export DPDK_DIR=/home/BKCPkg/domains/accelerator/dpdk_driver/*')
        self.add_environment_to_file('RTE_SDK', 'export RTE_SDK=$DPDK_DIR')
        self.add_environment_to_file('RTE_TARGET', 'export RTE_TARGET=installdir')
        self.sut.execute_shell_cmd('yum install -y meson', timeout=10*60)
        _, out, err = self.sut.execute_shell_cmd('meson setup --prefix $RTE_SDK/$RTE_TARGET builddir', timeout=10*60, cwd=f'{DPDK_DRIVER_PATH_L}*/')
        self.__check_error(err)
        self.sut.execute_shell_cmd('ninja -C builddir', timeout=10*60, cwd=f'{DPDK_DRIVER_PATH_L}*/')
        self.sut.execute_shell_cmd('mkdir -p /mnt/hugepages', timeout=60, cwd=f'{DPDK_DRIVER_PATH_L}*/')
        self.sut.execute_shell_cmd('mount -t hugetlbfs nodev /mnt/hugepages', timeout=60, cwd=f'{DPDK_DRIVER_PATH_L}*/')
        self.sut.execute_shell_cmd('echo 2048 > /proc/sys/vm/nr_hugepages', timeout=60, cwd=f'{DPDK_DRIVER_PATH_L}*/')

    # def run_fio_stress_async(self):
    #     """
    #
    #           Purpose: Run fio asynchronous stress overnight
    #           Args:
    #               No
    #           Returns:
    #               No
    #           Raises:
    #               RuntimeError: If any errors
    #           Example:
    #               Simplest usage: Run fio stress overnight
    #                     run_fio_stress_async()
    #     """
    #     self.sut.execute_shell_cmd('rm -rf fio_async.log', timeout=60, cwd='/root/')
    #     self.sut.execute_shell_cmd('yum install -y fio', timeout=10 * 60)
    #     _, out, err = self.sut.execute_shell_cmd_async(
    #         'fio --filename=/dev/sda --direct=1 --iodepth=1 --rw=randrw --rwmixread=70 --ioengine=libaio --bs=4k --size=300G --numjobs=50 --runtime=300 --group_reporting --name=randrw70read4k > /root/fio_async.log',
    #         timeout=300)

    def run_fio_stress_async(self):
        """

              Purpose: Run fio asynchronous stress overnight
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Run fio stress overnight
                        run_fio_stress_async()
        """
        self.sut.execute_shell_cmd('rm -rf fio_async.log', timeout=60, cwd='/root/')
        self.sut.execute_shell_cmd('yum install -y fio', timeout=60)
        hdd_info = self.__grep_linux_fio_hdd()
        _, out, err = self.sut.execute_shell_cmd_async(
            f'fio --filename=/dev/{hdd_info} --direct=1 --iodepth=1 --rw=randrw --rwmixread=70 --ioengine=libaio --bs=4k --size=300G --numjobs=50 --runtime=300 --group_reporting --name=randrw70read4k > fio_async.log',
            timeout=300)

    def run_linpack_stress_async(self):
        """
              Purpose: Run linpack asynchronous stress overnight
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Run linpack asynchronous stress overnight
                        run_linpack_stress_async()
        """
        self.sut.execute_shell_cmd('rm -rf linpack_async.log', timeout=60, cwd='/root/')
        self.sut.execute_shell_cmd('yum -y install docker', timeout=5 * 60)
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=LINPACK_PATH_L)
        self.sut.upload_to_remote(localpath=LINPACK_H, remotepath=LINPACK_PATH_L)
        self.sut.execute_shell_cmd('unzip *.zip', timeout=10 * 60, cwd=LINPACK_PATH_L)
        self.sut.execute_shell_cmd_async(
            'while [ $SECONDS -lt $((SECONDS+300)) ]; do /home/BKCPkg/domains/accelerator/linpack/pnpwls-master/linpack/run_linpack.sh avx3 ; done | tee /root/linpack_async.log',
            timeout=50000)

    def run_mlc_stress_async(self):
        """
              Purpose: Run mlc asynchronous stress overnight
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Run mlc asynchronous stress overnight
                        run_mlc_stress_async()
        """
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=MLC_PATH_L)
        self.sut.upload_to_remote(localpath=MLC_H, remotepath=MLC_PATH_L)
        self.sut.execute_shell_cmd('tar -zxvf *.tgz', timeout=10 * 60, cwd=MLC_PATH_L)
        self.sut.execute_shell_cmd('chmod 777 *', timeout=60, cwd=f'{MLC_PATH_L}Linux/')
        _, out, err = self.sut.execute_shell_cmd_async('./mlc --loaded_latency -t3 -X -D8192 > mlc_async.log', timeout=50000, cwd=f'{MLC_PATH_L}Linux/')

    def run_openssl(self, is_asym=False):  # -->True/False
        """
              Purpose: Run openssl symmetric or asymmetric
              Args:
                  is_asym: is openssl symmetric or asymmetric
              Returns:
                  None
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Run openssl symmetric
                      run_openssl(False)
        """
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=QAT_ASYM_PATH_L)
        self.sut.upload_to_remote(localpath=QAT_ASYM_H, remotepath=QAT_ASYM_PATH_L)
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=QAT_SYM_PATH_L)
        self.sut.upload_to_remote(localpath=QAT_SYM_H, remotepath=QAT_SYM_PATH_L)
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=QAT_TEST_SCRIPT_PATH_L)
        self.sut.upload_to_remote(localpath=QAT_TEST_SCRIPT_H, remotepath=QAT_TEST_SCRIPT_PATH_L)
        if is_asym:
            self.openssl_asymmetric()
        else:
            self.openssl_symmetric()

    def run_prime95_stress_async(self):
        """

              Purpose: Run prime95 asynchronous stress overnight
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Run prime95 asynchronous stress overnight
                      run_prime95_stress_async()
        """
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=PRIME95_PATH_L)
        self.sut.upload_to_remote(localpath=PRIME95_H, remotepath=PRIME95_PATH_L, timeout=10 * 60)
        self.sut.execute_shell_cmd('tar -zxvf *.tar.gz', timeout=10 * 60, cwd=PRIME95_PATH_L)
        self.sut.upload_to_remote(localpath=PPEXPECT_H, remotepath=PPEXPECT_prime95_PATH_L)
        self.sut.upload_to_remote(localpath=PRIME95_SCRIPT_H, remotepath=PRIME95_SCRIPT_PATH_L)
        self.sut.execute_shell_cmd_async(f'python3 prime95.py run_prime95', timeout=7200 * 60, cwd=PRIME95_PATH_L)

    def run_ptu_stress_async(self):
        """
              Purpose: Run ptu asynchronous stress overnight
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Run ptu asynchronous stress overnight
                        run_ptu_stress_async()
        """
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=PTU_PATH_L)
        self.sut.upload_to_remote(localpath=PTU_H, remotepath=PTU_PATH_L)
        self.sut.execute_shell_cmd('unzip *.zip', timeout=10*60, cwd=PTU_PATH_L)
        self.sut.execute_shell_cmd('chmod 777 *', timeout=60, cwd=f'{PTU_PATH_L}')
        try:
            _, out, err = self.sut.execute_shell_cmd_async('./ptu -ct 8 > ptu_async.log', timeout=300, cwd=f'{PTU_PATH_L}')
        except Exception:
            pass

    def run_qat_sample_code(self, qat_cpa_param=''):
        """
              Purpose: Run QAT cap_sample stress
              Args:
                  qat_cpa_param: Which cap_sample stress need to run
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: run cap_sample stress
                        run_qat_sample_code('')
                        run_qat_sample_code('signOfLife=1')
        """
        _, out, err = self.sut.execute_shell_cmd('./cpa_sample_code ' + qat_cpa_param, timeout=1000*60, cwd=f'{QAT_DRIVER_PATH_L}/build/')
        self.check_keyword(['Sample code completed successfully'], out, 'Issue - Run qat stress fail')

    def run_qat_stress_async(self):
        """
              Purpose: Run QAT asynchronous stress overnight
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Run QAT asynchronous stress overnight
                        run_qat_stress_async()
        """
        self.sut.execute_shell_cmd('rm -rf qat_async.log', timeout=60, cwd='/root/')
        self.sut.execute_shell_cmd_async('while [ $SECONDS -lt $((SECONDS+300)) ]; do /home/BKCPkg/domains/accelerator/QAT/build/cpa_sample_code runTests=63 signOfLife=1 ; done | tee /root/qat_async.log')

    def run_socwatch(self, log_num):
        """
              Purpose: Run socwatch tool
              Args:
                  Yes: log_num is which time run socwatch tool.
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Run socwatch tool
                      install_socwatch()
        """
        self.sut.upload_to_remote(localpath=PPEXPECT_H, remotepath=PPEXPECT_SOCWATCH_PATH_L)
        self.sut.upload_to_remote(localpath=SOCWATCH_SCRIPT_H, remotepath=SOCWATCH_SCRIPT_PATH_L)
        # ret, out, err = self.sut.execute_shell_cmd(f'python3 socwatch.py run_socwatch', timeout=10*60, cwd=SOCWATCH_SCRIPT_PATH_L)
        # self.__check_error(err)
        # self.sut.execute_shell_cmd(f'rm -rf /root/socwatch{log_num}.log')
        # self.sut.execute_shell_cmd(f'mv socwatch.log socwatch{log_num}.log', timeout=10 * 60, cwd='/root')
        # self.sut.download_to_local(f'/root/socwatch{log_num}.log', os.path.join(LOG_PATH, 'Logs'))
        # self.sut.execute_shell_cmd(f'rm -rf /root/runsocwatch{log_num}.log')
        # self.sut.execute_shell_cmd(f'mv {SOCWATCH_PATH_L}socwatch_chrome_linux_INTERNAL_v2021.2_x86_64/runsocwatch.log /root/runsocwatch{log_num}.log', timeout=10*60)
        # self.sut.download_to_local(f'/root/runsocwatch{log_num}.log', os.path.join(LOG_PATH, 'Logs'))
        # self.sut.execute_shell_cmd(f'rm -rf /root/SoCWatchOutput{log_num}.csv')
        # self.sut.execute_shell_cmd(f'mv {SOCWATCH_PATH_L}socwatch_chrome_linux_INTERNAL_v2021.2_x86_64/SoCWatchOutput.csv /root/SoCWatchOutput{log_num}.csv', timeout=10*60)
        # self.sut.download_to_local(f'/root/SoCWatchOutput{log_num}.csv', os.path.join(LOG_PATH, 'Logs'))
        # _, out, err = self.sut.execute_shell_cmd(f'cat SoCWatchOutput{log_num}.csv', timeout=60, cwd='/root')
        # self.__cc6_value_check(out)
        # self.__cpu_idle_value_check(out)

    def run_stressapptest_stress_async(self):
        """
              Purpose: Run stressapptest asynchronous stress overnight
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Run stressapptest asynchronous stress overnight
                        run_stressapptest_stress_async()
        """
        self.sut.execute_shell_cmd('rm -rf stressapptest_async_log', timeout=60, cwd='/root/')
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=STRESSAPPTEST_PATH_L)
        self.sut.upload_to_remote(localpath=STRESSAPPTEST_H, remotepath=STRESSAPPTEST_PATH_L)
        self.sut.execute_shell_cmd('unzip *.zip', timeout=10*60, cwd=STRESSAPPTEST_PATH_L)
        self.sut.execute_shell_cmd('./configure', timeout=10*60, cwd=f'{STRESSAPPTEST_PATH_L}stressapptest-master/')
        self.sut.execute_shell_cmd('make install', timeout=10*60, cwd=f'{STRESSAPPTEST_PATH_L}stressapptest-master/')
        self.sut.execute_shell_cmd_async('/home/BKCPkg/domains/accelerator/stressapptest/stressapptest-master/src/stressapptest -s 300 -M 256 -m 18 -W -l /root/stressapptest_async_log', timeout=50000)

    def save_check_mce_error(self):
        self.sut.execute_shell_cmd('rm -rf /root/mce.log', timeout=60)
        self.sut.execute_shell_cmd('abrt-cli list | grep mce | tee /root/mce.log', timeout=60)
        self.sut.download_to_local(remotepath='/root/mce.log', localpath=os.path.join(LOG_PATH, 'Logs'))
        rcode, out, err = self.sut.execute_shell_cmd('abrt-cli list | grep mce|wc -l', timeout=60)
        if int(out.strip()) != 0:
            logger.error(err)
            raise Exception(err)

    def save_check_dmesg_error(self):
        self.sut.execute_shell_cmd('rm -rf /root/dmesg.log', timeout=60)
        self.sut.execute_shell_cmd('dmesg | tee /root/dmesg.log', timeout=60)
        self.sut.download_to_local(remotepath='/root/dmesg.log', localpath=os.path.join(LOG_PATH, 'Logs'))
        rcode, out, err = self.sut.execute_shell_cmd('dmesg | grep "error" | wc -l', timeout=60)
        if int(out.strip()) != 0:
            logger.error(err)
            raise Exception(err)

    def sgx_install_and_test(self):
        """
             Purpose: Install SGX driver and run SGX SDK test
             Args:
                 No
             Returns:
                 No
             Raises:
                 RuntimeError: If any errors
             Example:
                 Simplest usage: Install SGX driver and run SGX SDK test
                     sgx_install_and_test()
       """
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=SGX_PATH_L)
        self.sut.upload_to_remote(localpath=SGX_H, remotepath=SGX_PATH_L)
        self.sut.execute_shell_cmd('unzip sgx*.zip', timeout=60, cwd=SGX_PATH_L)
        self.sut.execute_shell_cmd('tar -zxvf sgx*.tgz', timeout=60, cwd=f'{SGX_PATH_L}Installer/')
        self.sut.execute_shell_cmd(f'yum-config-manager --add-repo {SGX_PATH_L}Installer/sgx_rpm_local_repo', timeout=60)
        self.sut.execute_shell_cmd('yum --nogpgcheck install -y libsgx-epid libsgx-uae-service libsgx-launch libsgx-urts', timeout=10*60)
        self.sut.execute_shell_cmd('chmod 777 *', timeout=60, cwd=f'{SGX_PATH_L}sgx_test/')
        self.add_environment_to_file('LD_LIBRARY_PATH', 'export LD_LIBRARY_PATH=/home/BKCPkg/domains/accelerator/sgx/sgx_test')
        _, out, err = self.sut.execute_shell_cmd('./sgx_app -auto', timeout=60, cwd=f'{SGX_PATH_L}sgx_test/')
        self.check_keyword(['Success: 7   Fail: 0'], out, 'Execute SGX app test fail')
        self.sut.execute_shell_cmd('chmod 777 *', timeout=60, cwd=f'{SGX_PATH_L}Installer/')
        self.sut.upload_to_remote(localpath=PPEXPECT_H, remotepath=PPEXPECT_SGXSDK_PATH_L)
        self.sut.upload_to_remote(localpath=SGXSDK_SCRIPT_H, remotepath=SGXSDK_SCRIPT_PATH_L)
        ret, out, err = self.sut.execute_shell_cmd(f'python3 sgx_sdk.py run_sgxsdk', timeout=7200*60, cwd=SGXSDK_SCRIPT_PATH_L)
        self.__check_error(err)
        self.sut.download_to_local(remotepath=f'{SGXSDK_SCRIPT_PATH_L}sgx_sdk.log', localpath=os.path.join(LOG_PATH, 'Logs'))
        self.sut.download_to_local(remotepath=f'{SGXSDK_SCRIPT_PATH_L}Installer/sdk.log', localpath=os.path.join(LOG_PATH, 'Logs'))
        _, out, err = self.sut.execute_shell_cmd(f'cat {SGXSDK_SCRIPT_PATH_L}Installer/sdk.log', timeout=60)
        self.check_keyword(['Installation is successful!'], out, 'RUN SGX SDK fail')
        self.add_environment_to_file('source', 'source /home/BKCPkg/domains/accelerator/sgx/Installer/sgxsdk/environment')
        _, out, err = self.sut.execute_shell_cmd('source /home/BKCPkg/domains/accelerator/sgx/Installer/sgxsdk/environment', timeout=60, cwd=f'{SGX_PATH_L}Installer/')
        self.__check_error(err)

    def sgx_msr_value_check(self):
        """
             Purpose: Check SGX "rdmsr 0x3a" value
             Args:
                 No
             Returns:
                 No
             Raises:
                 RuntimeError: If any errors
             Example:
                 Simplest usage: Check SGX "rdmsr 0x3a" value
                     sgx_msr_value_check()
       """
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=MSR_TOOL_PATH_L)
        self.sut.upload_to_remote(localpath=MSR_tool_H, remotepath=MSR_TOOL_PATH_L)
        self.sut.execute_shell_cmd('rpm -ivh *.rpm --force --nodeps', timeout=60, cwd=MSR_TOOL_PATH_L)
        self.sut.execute_shell_cmd('yum install -y openssl-devel libcurl-devel protobuf-devel yum-utils.noarch epel-release msr-tools', timeout=10*60)
        _, out, err = self.sut.execute_shell_cmd('rdmsr 0x3a', timeout=60)
        x3a_value = '0x' + out
        x3a_bin_value = bin(int(x3a_value, 16))
        x3a_str_value = str(x3a_bin_value)[2:]
        x3a_list = []
        for num in x3a_str_value:
            x3a_list.append(num)
        x3a_list.reverse()
        if x3a_list[0] != '1' or x3a_list[17] != '1' or x3a_list[18] != '1' or x3a_list[20] != '1':
            logger.error('0x3a value is incorrect')
            raise Exception('0x3a value is incorrect')

    def sgx_sampleenclave_test(self):
        """
             Purpose: Run SGX sampleenclave test
             Args:
                 No
             Returns:
                 No
             Raises:
                 RuntimeError: If any errors
             Example:
                 Simplest usage: Run SGX sampleenclave test
                     sgx_sampleenclave_test()
       """
        _, out, err = self.sut.execute_shell_cmd('make', timeout=60, cwd=f'{SGX_PATH_L}Installer/sgxsdk/SampleCode/SampleEnclave/')
        self.check_keyword(['The project has been built in debug hardware mode'], out, 'Execute SGX app test fail')
        try:
            self.sut.execute_shell_cmd('./app > app.log', timeout=60, cwd=f'{SGX_PATH_L}Installer/sgxsdk/SampleCode/SampleEnclave/')
            self.__check_error(err)
        except Exception:
            pass
        self.sut.download_to_local(f'{SGX_PATH_L}Installer/sgxsdk/SampleCode/SampleEnclave/app.log', os.path.join(LOG_PATH, 'Logs'))
        _, out, err = self.sut.execute_shell_cmd(f'cat {SGX_PATH_L}Installer/sgxsdk/SampleCode/SampleEnclave/app.log', timeout=60)
        self.check_keyword(['SampleEnclave successfully returned'], out, 'Run SampleEnclave fail')

    def sgxhydra_test(self):
        """
             Purpose: Run sgxhydra test
             Args:
                 No
             Returns:
                 No
             Raises:
                 RuntimeError: If any errors
             Example:
                 Simplest usage: Run sgxhydra test
                     sgxhydra_test()
       """
        self.sut.upload_to_remote(localpath=SGXHYDRA_H, remotepath=SGXHYDRA_PATH_L)
        self.sut.execute_shell_cmd('unzip SGXHydra.zip', timeout=60, cwd=SGXHYDRA_PATH_L)
        self.sut.execute_shell_cmd('make SGX_PRERELEASE=1 SGX_DEBUG=0', timeout=60, cwd=f'{SGXHYDRA_PATH_L}SGXHydra/')
        _, out, err = self.sut.execute_shell_cmd('./SGXHydra 128 64 64 9', timeout=50000*60, cwd=f'{SGXHYDRA_PATH_L}SGXHydra/App/')
        self.check_keyword(['started', 'stopped'], out, 'run SGXHydra stress fail')

    def stressapptest_stress(self):
        """
              Purpose: Run stressapptest stress overnight
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Run stressapptest stress overnight
                        stressapptest_stress()
        """
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=STRESSAPPTEST_PATH_L)
        self.sut.upload_to_remote(localpath=STRESSAPPTEST_H, remotepath=STRESSAPPTEST_PATH_L)
        self.sut.execute_shell_cmd('unzip *.zip', timeout=10 * 60, cwd=STRESSAPPTEST_PATH_L)
        self.sut.execute_shell_cmd('./configure', timeout=10 * 60, cwd=f'{STRESSAPPTEST_PATH_L}stressapptest-master/')
        self.sut.execute_shell_cmd('make install', timeout=10 * 60, cwd=f'{STRESSAPPTEST_PATH_L}stressapptest-master/')
        self.sut.execute_shell_cmd(
            '/home/BKCPkg/domains/accelerator/stressapptest/stressapptest-master/src/stressapptest -s 300 -M 256 -m 18 -W -l /root/stressapptest_log',
            timeout=50000)
        _, out, err = self.sut.execute_shell_cmd('cat /root/stressapptest_log')
        self.check_keyword(["Status: PASS - please verify no corrected errors"], out, 'Run stressapptest stress fail')
        self.sut.download_to_local(remotepath='/root/stressapptest_log', localpath=os.path.join(LOG_PATH, 'Logs'))
        self.sut.execute_shell_cmd('rm -rf stressapptest_log', timeout=60, cwd='/root/')

    def kernel_version(self):
        _, out, err = self.sut.execute_shell_cmd('uname -r')
        line_list = out.strip().split('-')
        return line_list[0]

    def tdx_install(self):
        """
              Purpose: Install TDX driver and check TDX status
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Install TDX driver and check TDX status
                      tdx_install()
        """
        ker_ver = self.kernel_version()
        if ker_ver <= self.CENTOS_INTEL_NEXT_KERNEL:
            self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=MSR_TOOL_PATH_L)
            self.sut.upload_to_remote(localpath=MSR_tool_H, remotepath=MSR_TOOL_PATH_L)
            self.sut.execute_shell_cmd('rpm -ivh *.rpm --force --nodeps', timeout=60, cwd=MSR_TOOL_PATH_L)
            _, out, err = self.sut.execute_shell_cmd('rdmsr 0x1401 -f 11:11', timeout=60)
            self.check_keyword(['1'], out, 'TDX status show fail')
            self.sut.execute_shell_cmd('mkdir /usr/lib/firmware/intel-seam', timeout=60)
            self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=TDX_SEAM_LOADER_PATH_L)
            self.sut.upload_to_remote(localpath=TDX_SEAM_LOADER_H, remotepath=TDX_SEAM_LOADER_PATH_L)
            self.sut.execute_shell_cmd('unzip *.zip', timeout=60, cwd=TDX_SEAM_LOADER_PATH_L)
            self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=TDX_SEAM_MODULE_PATH_L)
            self.sut.upload_to_remote(localpath=TDX_SEAM_MODULE_H, remotepath=TDX_SEAM_MODULE_PATH_L)
            self.sut.execute_shell_cmd('unzip *.zip', timeout=60, cwd=TDX_SEAM_MODULE_PATH_L)
            self.sut.execute_shell_cmd('mv *.bin np-seamldr.acm', timeout=60, cwd=f'{TDX_SEAM_LOADER_PATH_L}*/')
            self.sut.execute_shell_cmd('cp np-seamldr.acm  /usr/lib/firmware/intel-seam/', timeout=60, cwd=f'{TDX_SEAM_LOADER_PATH_L}*/')
            self.sut.execute_shell_cmd('mv *.sigstruct libtdx.so.sigstruct', timeout=60, cwd=f'{TDX_SEAM_MODULE_PATH_L}*/')
            self.sut.execute_shell_cmd('cp libtdx.so.sigstruct  /usr/lib/firmware/intel-seam/', timeout=60, cwd=f'{TDX_SEAM_MODULE_PATH_L}*/')
            self.sut.execute_shell_cmd('mv *.so libtdx.so', timeout=60, cwd=f'{TDX_SEAM_MODULE_PATH_L}*/')
            self.sut.execute_shell_cmd('cp libtdx.so  /usr/lib/firmware/intel-seam/', timeout=60, cwd=f'{TDX_SEAM_MODULE_PATH_L}*/')
            self.sut.execute_shell_cmd('rm -rf np-seamldr.conf', timeout=60, cwd='/etc/dracut.conf.d/')
            self.sut.execute_shell_cmd('touch np-seamldr.conf', timeout=60, cwd='/etc/dracut.conf.d/')
            command = 'compress=cat'
            self.sut.execute_shell_cmd(f'echo {command} >> /etc/dracut.conf.d/np-seamldr.conf', timeout=60)
            self.sut.execute_shell_cmd('echo \'install_items+=" /usr/lib/firmware/intel-seam/libtdx.so /usr/lib/firmware/intel-seam/libtdx.so.sigstruct /usr/lib/firmware/intel-seam/np-seamldr.acm "\' >> /etc/dracut.conf.d/np-seamldr.conf', timeout=60)
            self.sut.execute_shell_cmd('chmod 777 *', timeout=60, cwd='/etc/dracut.conf.d/')
            self.sut.execute_shell_cmd('dracut --force', timeout=60, cwd='/etc/dracut.conf.d/')
            # self.sut.execute_shell_cmd('reboot', timeout=30 * 60)
            # self.Case.sleep(60)
            # self.Case.wait_and_expect(f'SUT in OS', 30 * 60, self.sut.check_system_in_os)
            self.my_os.warm_reset_cycle_step(self.sut)
            self.Case.sleep(60)
            _, out, err = self.sut.execute_shell_cmd('dmesg | grep -i "tdx init"', timeout=60, cwd='/etc/dracut.conf.d/')
            self.__check_error(err)
            self.check_keyword(['tdx: TDX initialized'], out, 'TDX initialized fail')
        else:
            self.sut.execute_shell_cmd(f'mkdir -p {TDX_SEAM_RPMS_PATH_L}', timeout=60)
            self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=TDX_SEAM_RPMS_PATH_L)
            self.sut.execute_shell_cmd(f'wget {TDX_SEAM_MODULE_RPM_PATH_L}', timeout=30 * 60, cwd=TDX_SEAM_RPMS_PATH_L)
            self.sut.execute_shell_cmd(f'wget {TDX_SEAM_MODULE_COMMON_PATH_L}', timeout=30 * 60, cwd=TDX_SEAM_RPMS_PATH_L)
            self.sut.execute_shell_cmd(f'wget {TDX_SEAM_MODULE_NON_PRODUCTION_PATH_L}', timeout=30 * 60, cwd=TDX_SEAM_RPMS_PATH_L)
            self.sut.execute_shell_cmd('rpm -ivh tdx-seam*.rpm --nodeps', timeout=60, cwd=TDX_SEAM_RPMS_PATH_L)
            self.modify_kernel_grub('tdx_host=on', True)
            _, out, err = self.sut.execute_shell_cmd('rdmsr 0x1401 -f 11:11', timeout=60)
            self.check_keyword(['1'], out, 'TDX status show fail')
            _, out, err = self.sut.execute_shell_cmd('dmesg | grep -i "tdx"', timeout=60, cwd='/etc/dracut.conf.d/')
            self.__check_error(err)
            self.check_keyword(['tdx: Successfully initialized TDX module'], out, 'TDX initialized fail')

    def upload_dsa_tools_rich_vm(self, qemu):
        qemu.execute_rich_vm_cmd_parallel(f'mkdir -p {SPR_ACCE_RANDOM_CONFIG_PATH_L}', timeout=60)
        qemu.execute_rich_vm_cmd_parallel(f'rm -rf {SPR_ACCE_RANDOM_CONFIG_PATH_L}*', timeout=60)
        sut_file_dir = f'{SPR_ACCE_RANDOM_CONFIG_PATH_L}{SPR_ACCE_RANDOM_CONFIG_NAME}'
        vm_file_dir = f'{SPR_ACCE_RANDOM_CONFIG_PATH_L}{SPR_ACCE_RANDOM_CONFIG_NAME}'
        qemu.upload_to_rich_vm(sut_file_dir, vm_file_dir)

        qemu.execute_rich_vm_cmd_parallel(f'mkdir -p {DSA_PATH_L}', timeout=60)
        qemu.execute_rich_vm_cmd_parallel(f'rm -rf {DSA_PATH_L}*', timeout=60)
        sut_file_dir1 = f'{DSA_PATH_L}{DSA_ACCEL_CONFIG_NAME}'
        vm_file_dir1 = f'{DSA_PATH_L}{DSA_ACCEL_CONFIG_NAME}'
        self.sut.upload_to_remote(localpath=DSA_H, remotepath=DSA_PATH_L)
        qemu.upload_to_rich_vm(sut_file_dir1, vm_file_dir1)

    # def tdx_install(self):
    #     """
    #           Purpose: Install TDX driver and check TDX status
    #           Args:
    #               No
    #           Returns:
    #               No
    #           Raises:
    #               RuntimeError: If any errors
    #           Example:
    #               Simplest usage: Install TDX driver and check TDX status
    #                   tdx_install()
    #     """
    #     self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=MSR_TOOL_PATH_L)
    #     self.sut.upload_to_remote(localpath=MSR_tool_H, remotepath=MSR_TOOL_PATH_L)
    #     self.sut.execute_shell_cmd('rpm -ivh *.rpm --force --nodeps', timeout=60, cwd=MSR_TOOL_PATH_L)
    #     _, out, err = self.sut.execute_shell_cmd('rdmsr 0x1401 -f 11:11', timeout=60)
    #     self.check_keyword(['1'], out, 'TDX status show fail')
    #     self.sut.execute_shell_cmd('mkdir /usr/lib/firmware/intel-seam', timeout=60)
    #     self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=TDX_SEAM_LOADER_PATH_L)
    #     self.sut.upload_to_remote(localpath=TDX_SEAM_LOADER_H, remotepath=TDX_SEAM_LOADER_PATH_L)
    #     self.sut.execute_shell_cmd('unzip *.zip', timeout=60, cwd=TDX_SEAM_LOADER_PATH_L)
    #     self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=TDX_SEAM_MODULE_PATH_L)
    #     self.sut.upload_to_remote(localpath=TDX_SEAM_MODULE_H, remotepath=TDX_SEAM_MODULE_PATH_L)
    #     self.sut.execute_shell_cmd('unzip *.zip', timeout=60, cwd=TDX_SEAM_MODULE_PATH_L)
    #     self.sut.execute_shell_cmd('mv *.bin np-seamldr.acm', timeout=60, cwd=f'{TDX_SEAM_LOADER_PATH_L}*/')
    #     self.sut.execute_shell_cmd('cp np-seamldr.acm  /usr/lib/firmware/intel-seam/', timeout=60, cwd=f'{TDX_SEAM_LOADER_PATH_L}*/')
    #     self.sut.execute_shell_cmd('mv *.sigstruct libtdx.so.sigstruct', timeout=60, cwd=f'{TDX_SEAM_MODULE_PATH_L}*/')
    #     self.sut.execute_shell_cmd('cp libtdx.so.sigstruct  /usr/lib/firmware/intel-seam/', timeout=60, cwd=f'{TDX_SEAM_MODULE_PATH_L}*/')
    #     self.sut.execute_shell_cmd('mv *.so libtdx.so', timeout=60, cwd=f'{TDX_SEAM_MODULE_PATH_L}*/')
    #     self.sut.execute_shell_cmd('cp libtdx.so  /usr/lib/firmware/intel-seam/', timeout=60, cwd=f'{TDX_SEAM_MODULE_PATH_L}*/')
    #     self.sut.execute_shell_cmd('rm -rf np-seamldr.conf', timeout=60, cwd='/etc/dracut.conf.d/')
    #     self.sut.execute_shell_cmd('touch np-seamldr.conf', timeout=60, cwd='/etc/dracut.conf.d/')
    #     command = 'compress=cat'
    #     self.sut.execute_shell_cmd(f'echo {command} >> /etc/dracut.conf.d/np-seamldr.conf', timeout=60)
    #     self.sut.execute_shell_cmd('echo \'install_items+=" /usr/lib/firmware/intel-seam/libtdx.so /usr/lib/firmware/intel-seam/libtdx.so.sigstruct /usr/lib/firmware/intel-seam/np-seamldr.acm "\' >> /etc/dracut.conf.d/np-seamldr.conf', timeout=60)
    #     self.sut.execute_shell_cmd('chmod 777 *', timeout=60, cwd='/etc/dracut.conf.d/')
    #     self.sut.execute_shell_cmd('dracut --force', timeout=60, cwd='/etc/dracut.conf.d/')
    #     # self.sut.execute_shell_cmd('reboot', timeout=30 * 60)
    #     # self.Case.sleep(60)
    #     # self.Case.wait_and_expect(f'SUT in OS', 30 * 60, self.sut.check_system_in_os)
    #     self.my_os.warm_reset_cycle_step(self.sut)
    #     self.Case.sleep(60)
    #     _, out, err = self.sut.execute_shell_cmd('dmesg | grep -i "tdx init"', timeout=60, cwd='/etc/dracut.conf.d/')
    #     self.__check_error(err)
    #     self.check_keyword(['tdx: TDX initialized'], out, 'TDX initialized fail')

    def __dlb_vf_set_egs(self, vf, dlb_pf_id, pci_id_list):
        for i in range(vf):
            self.sut.execute_shell_cmd(
                f'echo {int(2048 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_atomic_inflights',
                timeout=60)
            self.sut.execute_shell_cmd(
                f'echo {int(2048 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_dir_credits',
                timeout=60)
            self.sut.execute_shell_cmd(
                f'echo {int(64 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_dir_ports',
                timeout=60)
            self.sut.execute_shell_cmd(
                f'echo {int(2048 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_hist_list_entries',
                timeout=60)
            self.sut.execute_shell_cmd(
                f'echo {int(8192 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_ldb_credits',
                timeout=60)
            self.sut.execute_shell_cmd(
                f'echo {int(64 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_ldb_ports',
                timeout=60)
            self.sut.execute_shell_cmd(
                f'echo {int(32 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_ldb_queues',
                timeout=60)
            self.sut.execute_shell_cmd(
                f'echo {int(32 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_sched_domains',
                timeout=60)
            self.sut.execute_shell_cmd(
                f'echo {int(16 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_sn0_slots',
                timeout=60)
            self.sut.execute_shell_cmd(
                f'echo {int(16 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_sn1_slots',
                timeout=60)
            ret, out, err = self.sut.execute_shell_cmd(f'virsh nodedev-detach pci_{pci_id_list[i]}', timeout=60)
            if ret:
                logger.error('detached device fail')
                raise Exception('detached device fail')

    def __dlb_vf_set_bhs(self, vf, dlb_pf_id, pci_id_list):
        for i in range(vf):
            self.sut.execute_shell_cmd(
                f'echo {int(2048 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_atomic_inflights',
                timeout=60)
            self.sut.execute_shell_cmd(
                f'echo {int(96 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_dir_ports',
                timeout=60)
            self.sut.execute_shell_cmd(
                f'echo {int(2048 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_hist_list_entries',
                timeout=60)
            self.sut.execute_shell_cmd(
                f'echo {int(16384 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_ldb_credits',
                timeout=60)
            self.sut.execute_shell_cmd(
                f'echo {int(64 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_ldb_ports',
                timeout=60)
            self.sut.execute_shell_cmd(
                f'echo {int(32 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_ldb_queues',
                timeout=60)
            self.sut.execute_shell_cmd(
                f'echo {int(32 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_sched_domains',
                timeout=60)
            self.sut.execute_shell_cmd(
                f'echo {int(16 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_sn0_slots',
                timeout=60)
            self.sut.execute_shell_cmd(
                f'echo {int(16 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_sn1_slots',
                timeout=60)
            ret, out, err = self.sut.execute_shell_cmd(f'virsh nodedev-detach pci_{pci_id_list[i]}', timeout=60)
            if ret:
                logger.error('detached device fail')
                raise Exception('detached device fail')

    def __grep_linux_fio_hdd(self):
        # grep boot os hdd
        _, out, err = self.sut.execute_shell_cmd("df -h |grep -i '/boot/efi' |awk '{print $1}'", timeout=60)
        dev_list = []
        disk_line = out.split('/')
        disk_name = disk_line[2][:-2]
        dev_list.append(disk_name)

        # grep vm os hdd
        _, out, err = self.sut.execute_shell_cmd("fdisk -l |grep -i 'VMware VMFS'|awk '{print $1}'", timeout=60)
        disk_line = out.split()
        disk_num = 0
        for line in disk_line:
            if 'sd' in line:
                disk_num += 1
                line_name = line.split('/')
                disk_name = line_name[2][:-1]
                dev_list.append(disk_name)

            else:
                disk_num += 1
                line_name = line.split('/')
                disk_name = line_name[2][:-2]
                dev_list.append(disk_name)

        _, out, err = self.sut.execute_shell_cmd("fdisk -l |grep -i 'unknown'|awk '{print $1}'", timeout=60)
        disk_line = out.split()
        disk_num = 0
        for line in disk_line:
            if 'sd' in line:
                disk_num += 1
                line_name = line.split('/')
                disk_name = line_name[2][:-1]
                dev_list.append(disk_name)

            else:
                disk_num += 1
                line_name = line.split('/')
                disk_name = line_name[2][:-2]
                dev_list.append(disk_name)

        # grep all sut hdd
        _, out1, err = self.sut.execute_shell_cmd('ls /dev/sd?', timeout=60)
        _, out2, err = self.sut.execute_shell_cmd('ls /dev/nvme*n1', timeout=60)
        out = out1 + ' ' + out2

        disk_line = out.split()
        disk_num = 0
        all_dev_list = []
        for line in disk_line:
            disk_num += 1
            line_name = line.split('/')
            disk_name = line_name[2]
            all_dev_list.append(disk_name)

        # grep fio hdd name
        fio_list = []
        for list in all_dev_list:
            if list not in dev_list:
                fio_list.append(list)

        if fio_list == []:
            logger.error('please add another hdd to test')
            raise Exception('please add another hdd to test')
        else:
            return fio_list[0]

    def unbind_device(self, ip_pf_vf):   #begain is qat_0_1  dlb_0_0
        """
              Purpose: Unbind 'QAT', 'DLB', 'DSA' device
              Args:
                  ip_pf_vf_mdev :
                  1. If unbind QAT device, format is qat_0_1, pf 0 is QAT PF device 1,pf begin from device 1, device id from device 0-7, pf 0 -->device id;
                    vf 1 vf device 1, vf begin from virtual device 1, device id from device 00.1-02.0,vf 1-->device 00.1
                  2.If unbind DLB device, format is dlb_0_0, pf 0 is pf device 1,pf begin from true device 1, device id from device 0-7, pf 0 -->device id 1;
                    vf is number of vf device need created, vf 0 is don't create virtual device, vf 1 is create 1 virtual device, vf 16 is create 16 virtual device
                  3.If unbind DSA device, format is dsa_0_0, pf 0 is pf device 1,pf begin from true device 1, device id from device 0-7, pf 0 -->device id 1
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: unbind QAT pf device 0
                        unbind_device('qat_0_0')
        """
        ip, pf, vf = ip_pf_vf.split('_')
        pf = int(pf)
        vf = int(vf)
        if ip == 'qat':
            dev_id = self.get_dev_id(ip, pf, vf)
            unbind_path = self.__get_qat_unbind_path(dev_id)
            pci_id = self.__get_qat_pci_id(dev_id)
            self.sut.execute_shell_cmd('modprobe vfio')
            self.sut.execute_shell_cmd('modprobe vfio-pci')
            self.sut.execute_shell_cmd(f'echo {dev_id} > /sys/bus/pci/devices/{unbind_path}/driver/unbind', timeout=60)
            if vf == 0:
                self.sut.execute_shell_cmd(f'echo 8086 {self.qat_id} > /sys/bus/pci/drivers/vfio-pci/new_id', timeout=60)
            elif 0 < vf < 17:
                self.sut.execute_shell_cmd(f'echo 8086 {self.qat_vf_id} > /sys/bus/pci/drivers/vfio-pci/new_id', timeout=60)
            else:
                logger.error('Input an uncorrect vf number')
                raise Exception('Input an uncorrect vf number')
            self.sut.execute_shell_cmd(f'lspci -s {dev_id} -k', timeout=60)
            ret, out, err = self.sut.execute_shell_cmd(f'virsh nodedev-detach pci_{pci_id}', timeout=60)
            if ret:
                logger.error('detached device fail')
                raise Exception('detached device fail')
        elif ip == 'dlb':
            dev_id_list = self.get_dlb_dev_id_list(pf, vf)
            dlb_pf_id = self.__get_dlb_unbind_path(dev_id_list[0])
            pci_id_list = self.__get_dlb_pci_id_list(dev_id_list)
            self.sut.execute_shell_cmd('modprobe vfio')
            self.sut.execute_shell_cmd('modprobe vfio-pci')
            for i in range(vf):
                self.sut.execute_shell_cmd(f'echo {dev_id_list[i]} > /sys/bus/pci/drivers/dlb2/unbind', timeout=60)
            if vf == 0:
                self.sut.execute_shell_cmd(f'echo {dev_id_list[0]} > /sys/bus/pci/drivers/dlb2/unbind', timeout=60)
                self.sut.execute_shell_cmd(f'echo 8086 {self.dlb_id} > /sys/bus/pci/drivers/vfio-pci/new_id', timeout=60)
                self.sut.execute_shell_cmd(f'lspci -s {dev_id_list[0]} -k', timeout=60)
                ret, out, err = self.sut.execute_shell_cmd(f'virsh nodedev-detach pci_{pci_id_list[0]}', timeout=60)
                if ret:
                    logger.error('detached device fail')
                    raise Exception('detached device fail')
            elif 0 < vf < 17:
                self.sut.execute_shell_cmd(f'echo 8086 {self.dlb_vf_id} > /sys/bus/pci/drivers/vfio-pci/new_id', timeout=60)
                self.__dlb_vf_set_egs(vf, dlb_pf_id, pci_id_list)
            else:
                logger.error('Input an uncorrect vf number')
                raise Exception('Input an uncorrect vf number')
        elif ip == 'dsa':
            dev_id = self.get_dev_id(ip, pf, vf)
            self.sut.execute_shell_cmd(f'echo {dev_id} > /sys/bus/pci/devices/{dev_id}/driver/unbind', timeout=60)
            self.sut.execute_shell_cmd(f'echo 8086 {self.dsa_id} > /sys/bus/pci/drivers/vfio-pci/new_id', timeout=60)
            self.sut.execute_shell_cmd(f'lspci -s {dev_id} -k', timeout=60)

    # CentOS_VM-APIs
###############################################################################################

    def add_environment_to_file_vm(self, qemu, vm_name, check_key, add_command):
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
        _, out, err = qemu.execute_vm_cmd(vm_name, 'cat /root/.bashrc', timeout=60)
        if check_key not in out:
            qemu.execute_vm_cmd(vm_name, f"echo '{add_command}' >> /root/.bashrc", timeout=60)
            qemu.execute_vm_cmd(vm_name, 'source /root/.bashrc', timeout=60)

    def add_environment_to_file_rich_vm(self, qemu, check_key, add_command):
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
        exec_res = qemu.execute_rich_vm_cmd_parallel('cat /root/.bashrc', timeout=60)
        for vm in exec_res:
            out = exec_res[vm][1]
            if check_key not in out:
                qemu.execute_vm_cmd(vm, f"echo '{add_command}' >> /root/.bashrc", timeout=60)
                qemu.execute_vm_cmd(vm, 'source /root/.bashrc', timeout=60)

    def check_device_in_vm(self, qemu, vm_name, device_ip, vf_num, mdev=False):
        """
              Purpose: Check attached device in VM
              Args:
                  qemu: Call VM Class RichHypervisor
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
                      check_device_in_vm(qemu, vm_name, 'qat', 16)
        """
        _, out, err = qemu.execute_vm_cmd(vm_name, 'lspci')
        if not mdev:
            if not vf_num:
                if device_ip == 'qat':
                    self.check_keyword([f'Intel Corporation Device {self.qat_id}'], out, "Can't detact attached device")
                elif device_ip == 'dlb':
                    self.check_keyword([f'Intel Corporation Device {self.dlb_id}'], out, "Can't detact attached device")
                elif device_ip == 'dsa':
                    self.check_keyword([f'Intel Corporation Device {self.dsa_id}'], out, "Can't detact attached device")
            else:
                if device_ip == 'qat':
                    self.__check_device_in_vm(out, vf_num, f'Intel Corporation Device {self.qat_vf_id}')
                elif device_ip == 'dlb':
                    self.__check_device_in_vm(out, vf_num, f'Intel Corporation Device {self.dlb_vf_id}')
        else:
            if device_ip == 'qat':
                self.check_keyword([f'Intel Corporation Device {self.qat_mdev_id}'], out, "Can't detact attached device")

    def check_device_in_rich_vm(self, qemu, device_ip, vf_num, mdev=False):
        """
              Purpose: Check attached device in VM
              Args:
                  qemu: Call VM Class RichHypervisor
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
                      check_device_in_rich_vm(qemu, 'qat', 16)
        """
        logger.info(f'start check devices in every virtual machine')
        exec_res = qemu.execute_rich_vm_cmd_parallel('lspci')
        for vm in exec_res:
            out = exec_res[vm][1]
            if not mdev:
                if not vf_num:
                    if device_ip == 'qat':
                        self.check_keyword([f'Intel Corporation Device {self.qat_id}'], out, "Can't detact attached device")
                    elif device_ip == 'dlb':
                        self.check_keyword([f'Intel Corporation Device {self.dlb_id}'], out, "Can't detact attached device")
                    elif device_ip == 'dsa':
                        self.check_keyword([f'Intel Corporation Device {self.dsa_id}'], out, "Can't detact attached device")
                else:
                    if device_ip == 'qat':
                        self.__check_device_in_vm(out, vf_num, f'Intel Corporation Device {self.qat_vf_id}')
                    elif device_ip == 'dlb':
                        self.__check_device_in_vm(out, vf_num, f'Intel Corporation Device {self.dlb_vf_id}')
            else:
                if device_ip == 'qat':
                    self.check_keyword([f'Intel Corporation Device {self.qat_mdev_id}'], out, "Can't detact attached device")
        logger.info(f'check devices in every virtual machine successfully')

    def dlb_install_vm(self, qemu, vm_name, ch_makefile):
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
        qemu.execute_vm_cmd(vm_name, f'mkdir -p {DLB_DRIVER_PATH_L}', timeout=60)
        qemu.execute_vm_cmd(vm_name, f'rm -rf {DLB_DRIVER_PATH_L}*', timeout=60)
        sut_file_dir = f'{DLB_DRIVER_PATH_L}{DLB_DRIVER_NAME}'
        vm_file_dir = f'{DLB_DRIVER_PATH_L}{DLB_DRIVER_NAME}'
        qemu.upload_to_vm(vm_name, sut_file_dir, vm_file_dir)
        qemu.execute_vm_cmd(vm_name, f'unzip -o {DLB_DRIVER_NAME}', timeout=60, cwd=DLB_DRIVER_PATH_L)
        if ch_makefile:
            qemu.execute_vm_cmd(vm_name, "sed -i 's/ccflags-y += -DCONFIG_INTEL_DLB2_SIOV/#  iccflags-y += -DCONFIG_INTEL_DLB2_SIOV/g' /home/BKCPkg/domains/accelerator/dlb/driver/dlb2/Makefile", timeout=60)
        _, out, err = qemu.execute_vm_cmd(vm_name, 'make', timeout=60, cwd=f'{DLB_DRIVER_PATH_L}driver/dlb2/')
        # self.__check_error(err)
        qemu.execute_vm_cmd(vm_name, 'rmmod dlb2', timeout=60, cwd=f'{DLB_DRIVER_PATH_L}driver/dlb2/')
        qemu.execute_vm_cmd(vm_name, 'insmod ./dlb2.ko', timeout=60, cwd=f'{DLB_DRIVER_PATH_L}driver/dlb2/')
        _, out, err = qemu.execute_vm_cmd(vm_name, 'lsmod | grep dlb2', timeout=60)
        self.check_keyword(['dlb2'], out, 'Issue - dlb driver install fail')
        qemu.execute_vm_cmd(vm_name, 'make', timeout=60, cwd=f'{DLB_DRIVER_PATH_L}libdlb/')
        self.__check_error(err)
        self.add_environment_to_file_vm(qemu, vm_name, 'LD_LIBRARY_PATH', 'export LD_LIBRARY_PATH=/home/BKCPkg/domains/accelerator/dlb/libdlb:$LD_LIBRARY_PATH')


    def dlb_install_rich_vm(self, qemu, ch_makefile):
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
                      dlb_install_rich_vm(qemu, True)
        """
        logger.info(f'start dlb driver in every virtual machine')
        qemu.execute_rich_vm_cmd_parallel(f'mkdir -p {DLB_DRIVER_PATH_L}', timeout=60)
        qemu.execute_rich_vm_cmd_parallel(f'rm -rf {DLB_DRIVER_PATH_L}*', timeout=60)
        sut_file_dir = f'{DLB_DRIVER_PATH_L}{DLB_DRIVER_NAME}'
        vm_file_dir = f'{DLB_DRIVER_PATH_L}{DLB_DRIVER_NAME}'
        qemu.upload_to_rich_vm(sut_file_dir, vm_file_dir)
        logger.info(f'copy dlb driver to every virtual machine successfully')
        qemu.execute_rich_vm_cmd_parallel(f'unzip -o {DLB_DRIVER_NAME}', timeout=60, cwd=DLB_DRIVER_PATH_L)
        logger.info(f'unzip dlb driver in every virtual machine successfully')
        if ch_makefile:
            qemu.execute_rich_vm_cmd_parallel("sed -i 's/ccflags-y += -DCONFIG_INTEL_DLB2_SIOV/#  iccflags-y += -DCONFIG_INTEL_DLB2_SIOV/g' /home/BKCPkg/domains/accelerator/dlb/driver/dlb2/Makefile", timeout=60)
        qemu.execute_rich_vm_cmd_parallel('make', timeout=60, cwd=f'{DLB_DRIVER_PATH_L}driver/dlb2/')
        # self.__check_error(err)
        logger.info(f'install dlb driver in every virtual machine successfully')
        qemu.execute_rich_vm_cmd_parallel('rmmod dlb2', timeout=60, cwd=f'{DLB_DRIVER_PATH_L}driver/dlb2/')
        qemu.execute_rich_vm_cmd_parallel('insmod ./dlb2.ko', timeout=60, cwd=f'{DLB_DRIVER_PATH_L}driver/dlb2/')
        logger.info(f'insmod dlb driver in every virtual machine successfully')
        exec_res = qemu.execute_rich_vm_cmd_parallel('lsmod | grep dlb2', timeout=60)
        for vm in exec_res:
            out = exec_res[vm][1]
            self.check_keyword(['dlb2'], out, 'Issue - dlb driver install fail')
        exec_res = qemu.execute_rich_vm_cmd_parallel('make', timeout=60, cwd=f'{DLB_DRIVER_PATH_L}libdlb/')
        for vm in exec_res:
            err = exec_res[vm][2]
            self.__check_error(err)
        self.add_environment_to_file_rich_vm(qemu, 'LD_LIBRARY_PATH', 'export LD_LIBRARY_PATH=/home/BKCPkg/domains/accelerator/dlb/libdlb:$LD_LIBRARY_PATH')
        logger.info(f'dlb driver show in every virtual machine correct')

    def kernel_header_devel_vm(self, qemu, vm_name):
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
        qemu.execute_vm_cmd(vm_name, f'mkdir -p {KERNEL_HEADER_PATH_L}', timeout=60)
        qemu.execute_vm_cmd(vm_name, f'rm -rf {KERNEL_HEADER_PATH_L}*', timeout=60)
        # sut_file_dir = f'{KERNEL_HEADER_PATH_L}{KERNEL_HEADER_NAME}'
        # vm_file_dir = f'{KERNEL_HEADER_PATH_L}{KERNEL_HEADER_NAME}'
        # qemu.upload_to_vm(vm_name, sut_file_dir, vm_file_dir)
        sut_file_dir1 = f'{KERNEL_DEVEL_PATH_L}{KERNEL_DEVEL_NAME}'
        vm_file_dir1 = f'{KERNEL_DEVEL_PATH_L}{KERNEL_DEVEL_NAME}'
        qemu.upload_to_vm(vm_name, sut_file_dir1, vm_file_dir1)
        qemu.execute_vm_cmd(vm_name, 'rpm -ivh *.rpm --force --nodeps', timeout=5 * 60, cwd=KERNEL_DEVEL_PATH_L)

    def kernel_header_internal_devel_rich_vm(self, qemu):
        qemu.execute_rich_vm_cmd_parallel(f'mkdir -p {KERNEL_INTERNAL_PATH_L}', timeout=60)
        qemu.execute_rich_vm_cmd_parallel(f'rm -rf {KERNEL_INTERNAL_PATH_L}*', timeout=60)
        sut_file_dir = f'{KERNEL_INTERNAL_PATH_L}{KERNEL_INTERNAL_NAME}'
        vm_file_dir = f'{KERNEL_INTERNAL_PATH_L}{KERNEL_INTERNAL_NAME}'
        self.sut.upload_to_remote(localpath=KERNEL_INTERNAL_H, remotepath=KERNEL_INTERNAL_PATH_L)
        qemu.upload_to_rich_vm(sut_file_dir, vm_file_dir)
        qemu.execute_rich_vm_cmd_parallel('rpm -ivh *.rpm --force --nodeps', timeout=10 * 60,
                                          cwd=KERNEL_INTERNAL_PATH_L)


    def kvm_kernel_header_devel_vm(self, kvm, vm_name):
        """
              Purpose: Install kernel-header and kernel-devel package in VM
              Args:
                  kvm: Call VM Class
                  vm_name: Run command on which VM
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Install kernel-header and kernel-devel package in VM
                      kvm_kernel_header_devel_vm(kvm, vm_name)
        """
        kvm.execute_vm_cmd(vm_name, f'mkdir -p {KERNEL_HEADER_PATH_L}', timeout=60)
        kvm.execute_vm_cmd(vm_name, f'rm -rf {KERNEL_HEADER_PATH_L}*', timeout=60)
        sut_file_dir1 = f'{KERNEL_DEVEL_PATH_L}{KERNEL_DEVEL_NAME}'
        vm_file_dir1 = f'{KERNEL_DEVEL_PATH_L}{KERNEL_DEVEL_NAME}'
        kvm.upload_to_vm(vm_name, sut_file_dir1, vm_file_dir1)
        kvm.execute_vm_cmd(vm_name, 'rpm -ivh *.rpm --force --nodeps', timeout=5 * 60, cwd=KERNEL_DEVEL_PATH_L)

    def kvm_add_environment_to_file_vm(self, kvm, vm_name, check_key, add_command):
        """
              Purpose: to check all keys in VM /root/.bashrc file, if not add environments variable to /root/.bashrc file
              Args:
                  qemu: Call VM Class kvm
                  vm_name: Run command on which VM
                  check_key: the name of environments variable
                  add_command: add environments variable to VM /root/.bashrc file
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Add key 'end' to /root/.bashrc file
                        add_environment_to_file(kvm, vm_name, 'end', 'end=$((SECONDS+110))')
        """
        _, out, err = kvm.execute_vm_cmd(vm_name, 'cat /root/.bashrc', timeout=60)
        if check_key not in out:
            kvm.execute_vm_cmd(vm_name, f"echo '{add_command}' >> /root/.bashrc", timeout=60)
            kvm.execute_vm_cmd(vm_name, 'source /root/.bashrc', timeout=60)

    def kvm_qat_uninstall_vm(self, kvm, vm_name):
        """
              Purpose: To uninstall QAT driver
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Uninstall QAT driver
                     kvm_qat_uninstall_vm()
        """
        _, out, err = kvm.execute_vm_cmd(vm_name, "lsmod | grep 'qat\|usdm' | wc -l", timeout=60, cwd=QAT_DRIVER_PATH_L)
        if out != '':
            if out != '0\n':
                kvm.execute_vm_cmd(vm_name, 'reboot', timeout=30*60)
                self.Case.sleep(60)
                kvm.execute_vm_cmd(vm_name, 'make uninstall', timeout=10*60, cwd=QAT_DRIVER_PATH_L)
                kvm.execute_vm_cmd(vm_name, 'sleep 180', timeout=10 * 60, cwd=QAT_DRIVER_PATH_L)
                kvm.execute_vm_cmd(vm_name, 'make clean', timeout=60, cwd=QAT_DRIVER_PATH_L)
                kvm.execute_vm_cmd(vm_name, 'sleep 180', timeout=10 * 60, cwd=QAT_DRIVER_PATH_L)
                kvm.execute_vm_cmd(vm_name, 'make distclean', timeout=60, cwd=QAT_DRIVER_PATH_L)
                kvm.execute_vm_cmd(vm_name, 'sleep 180', timeout=10 * 60, cwd=QAT_DRIVER_PATH_L)
                _, out, err = kvm.execute_vm_cmd(vm_name, "lsmod | grep 'qat\|usdm' | wc -l", timeout=60,
                                                         cwd=QAT_DRIVER_PATH_L)
                self.check_keyword(['0'], out, 'Issue - QAT driver still exist')
                self.__check_error(err)
            else:
                pass
        else:
            pass

    def kvm_qat_install_vm(self, kvm, vm_name, execute_command, enable_siov=False):
        """
                      Purpose: To install QAT driver in VM
                      Args:
                          No
                      Returns:
                          No
                      Raises:
                          RuntimeError: If any errors
                      Example:
                          Simplest usage: install QAT driver
                              kvm_qat_install_vm()
                """
        kvm.execute_vm_cmd(vm_name, f'mkdir -p {QAT_DRIVER_PATH_L}', timeout=60)
        kvm.execute_vm_cmd(vm_name, f'rm -rf {QAT_DRIVER_PATH_L}*', timeout=60)
        sut_file_dir = f'{QAT_DRIVER_PATH_L}{QAT_DRIVER_NAME}'
        vm_file_dir = f'{QAT_DRIVER_PATH_L}{QAT_DRIVER_NAME}'
        kvm.upload_to_vm(vm_name, sut_file_dir, vm_file_dir)
        kvm.execute_vm_cmd(vm_name, f'unzip {QAT_DRIVER_NAME}', timeout=60, cwd=QAT_DRIVER_PATH_L)
        kvm.execute_vm_cmd(vm_name, 'tar -zxvf *.tar.gz', timeout=60, cwd=QAT_DRIVER_PATH_L)
        kvm.execute_vm_cmd(vm_name, execute_command, timeout=5 * 60, cwd=QAT_DRIVER_PATH_L)
        kvm.execute_vm_cmd(vm_name, 'sleep 60', timeout=5 * 60, cwd=QAT_DRIVER_PATH_L)
        _, out, err = kvm.execute_vm_cmd(vm_name, 'make install', timeout=5 * 60, cwd=QAT_DRIVER_PATH_L)
        kvm.execute_vm_cmd(vm_name, 'sleepp 120', timeout=5 * 60, cwd=QAT_DRIVER_PATH_L)
        _, out, err = kvm.execute_vm_cmd(vm_name, 'make samples-install', timeout=5 * 60, cwd=QAT_DRIVER_PATH_L)
        kvm.execute_vm_cmd(vm_name, 'sleep 120', timeout=5 * 60, cwd=QAT_DRIVER_PATH_L)
        _, out, err = kvm.execute_vm_cmd(vm_name, 'lsmod | grep qat', timeout=60)
        self.__check_error(err)
        if enable_siov:
            key_list = ['qat_vqat', 'intel_qat']
            self.check_keyword(key_list, out, 'Issue - QAT driver install failed')
        else:
            key_list = ['qat_4xxx', 'intel_qat']
            self.check_keyword(key_list, out, 'Issue - QAT driver install failed')

    def kvm_rpm_install_vm(self, kvm, vm_name):
        """
              Purpose: To install rpm packages in VM
              Args:
                  kvm: Call VM Class
                  vm_name: Run command on which VM
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Install rpm packages in VM
                      kvm_rpm_install_vm(kvm, vm_name)
        """

        rpm_list = [
            'zlib-devel.x86_64 yasm systemd-devel boost-devel.x86_64 openssl-devel libnl3-devel gcc gcc-c++ libgudev.x86_64 libgudev-devel.x86_64 systemd* abrt-cli boost-devel.x86_64']
        self.kvm_add_environment_to_file_vm(kvm, vm_name, 'http_proxy', 'export http_proxy=http://proxy-iind.intel.com:911')
        self.kvm_add_environment_to_file_vm(kvm, vm_name, 'HTTP_PROXY', 'export HTTP_PROXY=http://proxy-iind.intel.com:911')
        self.kvm_add_environment_to_file_vm(kvm, vm_name, 'https_proxy', 'export https_proxy=http://proxy-iind.intel.com:911')
        self.kvm_add_environment_to_file_vm(kvm, vm_name, 'HTTPS_PROXY', 'export HTTPS_PROXY=http://proxy-iind.intel.com:911')
        self.kvm_add_environment_to_file_vm(kvm, vm_name, 'no_proxy', "export no_proxy='localhost,127.0.0.1,intel.com,.intel.com'")
        for rpm in rpm_list:
            kvm.execute_vm_cmd(vm_name, f'yum -y install {rpm}', timeout=60000)

    def kvm_qat_vm_mega_install(self, kvm, vm_name):
        """
              Purpose: Run QAT mega test on guest
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Run QAT mega test
                      virsh_qat_vm_mega_install()
        """
        kvm.execute_vm_cmd(vm_name, f'pip3 install pexpect', timeout=5 * 60)
        kvm.execute_vm_cmd(vm_name, f'yum install -y epel-release readline-devel  lz4-devel python3 xxhash-devel',
                            timeout=5 * 60)
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=SAMPLE_CODE_PATH_L)
        self.sut.upload_to_remote(localpath=SAMPLE_CODE_H, remotepath=SAMPLE_CODE_PATH_L, timeout=10 * 60)
        kvm.execute_vm_cmd(vm_name, f'mkdir -p {SAMPLE_CODE_PATH_L}', timeout=10 * 60)
        kvm.execute_vm_cmd(vm_name, f'rm -rf {SAMPLE_CODE_PATH_L}*', timeout=10 * 60)
        sut_file_dir = f'{SAMPLE_CODE_PATH_L}{SAMPLE_CODE_NAME}'
        vm_file_dir = f'{SAMPLE_CODE_PATH_L}{SAMPLE_CODE_NAME}'
        kvm.upload_to_vm(vm_name, sut_file_dir, vm_file_dir)
        kvm.execute_vm_cmd(vm_name, f'tar -zxf *.tar.gz', timeout=10 * 60, cwd=SAMPLE_CODE_PATH_L)
        kvm.execute_vm_cmd(vm_name, f'sleep 120', timeout=10 * 60, cwd=SAMPLE_CODE_PATH_L)
        kvm.execute_vm_cmd(vm_name, f'./build.sh', timeout=10 * 60, cwd=SAMPLE_CODE_PATH_L)
        kvm.execute_vm_cmd(vm_name, f'sleep 120', timeout=10 * 60, cwd=SAMPLE_CODE_PATH_L)
        kvm.execute_vm_cmd(vm_name, f'rm -rf *', timeout=10 * 60, cwd=MEGA_CONF_PATH_L)
        self.sut.upload_to_remote(localpath=PPEXPECT_H, remotepath=PPEXPECT_MEGA_PATH_L)
        kvm.execute_vm_cmd(vm_name, f'mkdir -p {PPEXPECT_MEGA_PATH_L}', timeout=10 * 60)
        kvm.execute_vm_cmd(vm_name, f'rm -rf {PPEXPECT_MEGA_PATH_L}*', timeout=10 * 60)
        sut_file_dir = f'{PPEXPECT_MEGA_PATH_L}{PPEXPECT_NAME}'
        vm_file_dir = f'{PPEXPECT_MEGA_PATH_L}{PPEXPECT_NAME}'
        kvm.upload_to_vm(vm_name, sut_file_dir, vm_file_dir)
        self.sut.upload_to_remote(localpath=MEGA_SCRIPT_H, remotepath=MEGA_SCRIPT_PATH_L)
        sut_file_dir = f'{MEGA_SCRIPT_PATH_L}{MEGA_SCRIPT_NAME}'
        vm_file_dir = f'{MEGA_SCRIPT_PATH_L}{MEGA_SCRIPT_NAME}'
        kvm.upload_to_vm(vm_name, sut_file_dir, vm_file_dir)


    def kernel_header_devel_rich_vm(self, qemu):
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
        qemu.execute_rich_vm_cmd_parallel(f'mkdir -p {KERNEL_HEADER_PATH_L}', timeout=60)
        qemu.execute_rich_vm_cmd_parallel(f'rm -rf {KERNEL_HEADER_PATH_L}*', timeout=60)
        sut_file_dir1 = f'{KERNEL_DEVEL_PATH_L}{KERNEL_DEVEL_NAME}'
        vm_file_dir1 = f'{KERNEL_DEVEL_PATH_L}{KERNEL_DEVEL_NAME}'
        qemu.upload_to_rich_vm(sut_file_dir1, vm_file_dir1)
        qemu.execute_rich_vm_cmd_parallel('rpm -ivh *.rpm --force --nodeps', timeout=5 * 60, cwd=KERNEL_DEVEL_PATH_L)
        logger.info(f'install kernel_devel to every virtual machine successfully')

    def modify_kernel_grub_vm(self, qemu, vm_name, vm_function, add_or_remove):
        """
              Purpose: Modify kernel grub file
              Args:
                  qemu: Call VM Class RichHypervisor
                  vm_name: Run command on which VM
                  vm_function: What config need to add/remove to grub file
                  add_or_remove: Is add or remove config file
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Add 'intel_iommu=on,sm_on iommu=on no5lvl' function to kernel grub file in VM
                      modify_kernel_grub_vm(qemu, vm_name, 'intel_iommu=on,sm_on iommu=on no5lvl', True)
        """
        _, out, err = qemu.execute_vm_cmd(vm_name, 'uname -r', timeout=60)
        if add_or_remove:
            qemu.execute_vm_cmd(vm_name, f"grubby --update-kernel=/boot/vmlinuz-{out.strip()} --args='{vm_function}'",
                                timeout=60)
            qemu.execute_vm_cmd(vm_name, 'reboot', timeout=30 * 60)
            self.Case.sleep(2*60)
            _, out, _ = qemu.execute_vm_cmd(vm_name, 'cat /proc/cmdline')
            if vm_function not in out:
                logger.error('modify kernel file fail')
                raise Exception('modify kernel file fail')
        else:
            qemu.execute_vm_cmd(vm_name,
                f"grubby --update-kernel=/boot/vmlinuz-{out.strip()} --remove-args='{vm_function}'", timeout=60)
            qemu.execute_vm_cmd(vm_name, 'reboot', timeout=30 * 60)
            self.Case.sleep(2*60)
            _, out, _ = qemu.execute_vm_cmd(vm_name, 'cat /proc/cmdline')
            if vm_function in out:
                logger.error('modify kernel file fail')
                raise Exception('modify kernel file fail')

    def qat_install_vm(self, qemu, vm_name, execute_command, enable_siov=False):
        """
              Purpose: To install QAT driver in VM
              Args:
                  qemu: Call VM Class RichHypervisor
                  vm_name: Run command on which VM
                  enable_sriov: If enable sriov host function in VM
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: install QAT driver in VM
                      qat_install_vm(qemu, vm_name, False)
        """
        qemu.execute_vm_cmd(vm_name, f'mkdir -p {QAT_DRIVER_PATH_L}', timeout=60)
        qemu.execute_vm_cmd(vm_name, f'rm -rf {QAT_DRIVER_PATH_L}*', timeout=60)
        sut_file_dir = f'{QAT_DRIVER_PATH_L}{QAT_DRIVER_NAME}'
        vm_file_dir = f'{QAT_DRIVER_PATH_L}{QAT_DRIVER_NAME}'
        qemu.upload_to_vm(vm_name, sut_file_dir, vm_file_dir)
        qemu.execute_vm_cmd(vm_name, f'unzip {QAT_DRIVER_NAME}', timeout=60, cwd=QAT_DRIVER_PATH_L)
        qemu.execute_vm_cmd(vm_name, 'tar -zxvf *.tar.gz', timeout=60, cwd=QAT_DRIVER_PATH_L)
        qemu.execute_vm_cmd(vm_name, execute_command, timeout=5*60, cwd=QAT_DRIVER_PATH_L)
        _, out, err = qemu.execute_vm_cmd(vm_name, 'make install', timeout=5*60, cwd=QAT_DRIVER_PATH_L)
        _, out, err = qemu.execute_vm_cmd(vm_name, 'make samples-install', timeout=5*60, cwd=QAT_DRIVER_PATH_L)
        _, out, err = qemu.execute_vm_cmd(vm_name, 'lsmod | grep qat', timeout=60)
        self.__check_error(err)
        if enable_siov:
            key_list = ['qat_vqat', 'intel_qat']
            self.check_keyword(key_list, out, 'Issue - QAT driver install failed')
        else:
            key_list = ['qat_4xxx', 'intel_qat']
            self.check_keyword(key_list, out, 'Issue - QAT driver install failed')

    def qat_install_rich_vm(self, qemu, execute_command, enable_siov=False):
        """
              Purpose: To install QAT driver in VM
              Args:
                  qemu: Call VM Class RichHypervisor
                  vm_name: Run command on which VM
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
        qemu.execute_rich_vm_cmd_parallel(f'mkdir -p {QAT_DRIVER_PATH_L}', timeout=60)
        qemu.execute_rich_vm_cmd_parallel(f'rm -rf {QAT_DRIVER_PATH_L}*', timeout=60)
        sut_file_dir = f'{QAT_DRIVER_PATH_L}{QAT_DRIVER_NAME}'
        vm_file_dir = f'{QAT_DRIVER_PATH_L}{QAT_DRIVER_NAME}'
        qemu.upload_to_rich_vm(sut_file_dir, vm_file_dir)
        logger.info(f'copy qat driver to every virtual machine successfully')
        qemu.execute_rich_vm_cmd_parallel(f'unzip {QAT_DRIVER_NAME}', timeout=60, cwd=QAT_DRIVER_PATH_L)
        qemu.execute_rich_vm_cmd_parallel('tar -zxvf *.tar.gz', timeout=60, cwd=QAT_DRIVER_PATH_L)
        logger.info(f'qat driver successfully unzip in every virtual machine ')
        qemu.execute_rich_vm_cmd_parallel(execute_command, timeout=5*60, cwd=QAT_DRIVER_PATH_L)
        qemu.execute_rich_vm_cmd_parallel('make install', timeout=30*60, cwd=QAT_DRIVER_PATH_L)
        qemu.execute_rich_vm_cmd_parallel('make samples-install', timeout=15*60, cwd=QAT_DRIVER_PATH_L)
        logger.info(f'qat driver install successfully in every virtual machine')
        exec_res = qemu.execute_rich_vm_cmd_parallel('lsmod | grep qat', timeout=60)
        for vm in exec_res:
            out = exec_res[vm][1]
            err = exec_res[vm][2]
            self.__check_error(err)
            if enable_siov:
                key_list = ['qat_vqat', 'intel_qat']
                self.check_keyword(key_list, out, 'Issue - QAT driver install failed')
            else:
                key_list = ['qat_4xxx', 'intel_qat']
                self.check_keyword(key_list, out, 'Issue - QAT driver install failed')
        logger.info(f'qat driver show successfully in every virtual machine')

    def qat_uninstall_vm(self, qemu, vm_name):
        """
              Purpose: To uninstall QAT driver
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Uninstall QAT driver
                      qat_uninstall()
        """
        _, out, err = qemu.execute_vm_cmd(vm_name, "lsmod | grep 'qat\|usdm' | wc -l", timeout=60, cwd=QAT_DRIVER_PATH_L)
        if out != '':
            if out != '0\n':
                qemu.execute_vm_cmd(vm_name, 'reboot', timeout=30*60)
                self.Case.sleep(60)
                qemu.execute_vm_cmd(vm_name, 'make uninstall', timeout=10*60, cwd=QAT_DRIVER_PATH_L)
                qemu.execute_vm_cmd(vm_name, 'make clean', timeout=60, cwd=QAT_DRIVER_PATH_L)
                qemu.execute_vm_cmd(vm_name, 'make distclean', timeout=60, cwd=QAT_DRIVER_PATH_L)
                _, out, err = qemu.execute_vm_cmd(vm_name, "lsmod | grep 'qat\|usdm' | wc -l", timeout=60,
                                                         cwd=QAT_DRIVER_PATH_L)
                self.check_keyword(['0'], out, 'Issue - QAT driver still exist')
                self.__check_error(err)
            else:
                pass
        else:
            pass



    def run_dpdk_vm(self, qemu, vm_name):
        """
              Purpose: Install and Run DPDK test in VM
              Args:
                  qemu: Call VM Class RichHypervisor
                  vm_name: Run command on which VM
              Returns:
                  None
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Install and Run DPDK test in VM
                      run_dpdk_vm(qemu, vm_name)
        """
        qemu.execute_vm_cmd(vm_name, f'mkdir -p {DLB_DRIVER_PATH_L}', timeout=60)
        qemu.execute_vm_cmd(vm_name, f'rm -rf {DLB_DRIVER_PATH_L}*', timeout=60)
        sut_file_dir = f'{DLB_DRIVER_PATH_L}{DLB_DRIVER_NAME}'
        vm_file_dir = f'{DLB_DRIVER_PATH_L}{DLB_DRIVER_NAME}'
        qemu.upload_to_vm(vm_name, sut_file_dir, vm_file_dir)
        # qemu.execute_vm_cmd(vm_name, 'unzip *.zip', timeout=60, cwd=DLB_DRIVER_PATH_L)
        qemu.execute_vm_cmd(vm_name, 'rm -rf *', timeout=60, cwd=DPDK_DRIVER_PATH_L)
        self.sut.upload_to_remote(localpath=DPDK_DRIVER_H, remotepath=DPDK_DRIVER_PATH_L)
        qemu.execute_vm_cmd(vm_name, f'mkdir -p {DPDK_DRIVER_PATH_L}', timeout=60)
        qemu.execute_vm_cmd(vm_name, f'rm -rf {DPDK_DRIVER_PATH_L}*', timeout=60)
        sut_file_dir = f'{DPDK_DRIVER_PATH_L}{DPDK_DRIVER_NAME}'
        vm_file_dir = f'{DPDK_DRIVER_PATH_L}{DPDK_DRIVER_NAME}'
        qemu.upload_to_vm(vm_name, sut_file_dir, vm_file_dir)
        qemu.execute_vm_cmd(vm_name, 'unzip *.zip', timeout=60, cwd=DPDK_DRIVER_PATH_L)
        qemu.execute_vm_cmd(vm_name, 'tar xfJ *.tar.xz', timeout=60, cwd=DPDK_DRIVER_PATH_L)
        _, out, err = qemu.execute_vm_cmd(vm_name, 'patch -Np1 < /home/BKCPkg/domains/accelerator/dlb/dpdk/*.patch',
                                          timeout=60, cwd=f'{DPDK_DRIVER_PATH_L}*/')
        # self.check_keyword(['succeeded'], out, 'DPDK load patch fail')
        self.__check_error(err)
        self.add_environment_to_file_vm(qemu, vm_name, 'DPDK_DIR',
                                        'export DPDK_DIR=/home/BKCPkg/domains/accelerator/dpdk/*')
        self.add_environment_to_file_vm(qemu, vm_name, 'RTE_SDK', 'export RTE_SDK=$DPDK_DIR')
        self.add_environment_to_file_vm(qemu, vm_name, 'RTE_TARGET', 'export RTE_TARGET=installdir')
        qemu.execute_vm_cmd(vm_name, 'yum install -y meson', timeout=10 * 60)
        _, out, err = qemu.execute_vm_cmd(vm_name, 'meson setup --prefix $RTE_SDK/$RTE_TARGET builddir',
                                          timeout=10 * 60, cwd=f'{DPDK_DRIVER_PATH_L}*/')
        self.__check_error(err)
        qemu.execute_vm_cmd(vm_name, 'ninja -C builddir', timeout=10 * 60, cwd=f'{DPDK_DRIVER_PATH_L}*/')
        qemu.execute_vm_cmd(vm_name, 'mkdir -p /mnt/hugepages', timeout=60, cwd=f'{DPDK_DRIVER_PATH_L}*/')
        qemu.execute_vm_cmd(vm_name, 'mount -t hugetlbfs nodev /mnt/hugepages', timeout=60,
                            cwd=f'{DPDK_DRIVER_PATH_L}*/')
        qemu.execute_vm_cmd(vm_name, 'echo 2048 > /proc/sys/vm/nr_hugepages', timeout=60, cwd=f'{DPDK_DRIVER_PATH_L}*/')

    def rpm_install_vm(self, qemu, vm_name):
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
                      rpm_install_vm(qemu, vm_name)
        """

        rpm_list = [
            'zlib-devel.x86_64 yasm systemd-devel boost-devel.x86_64 openssl-devel libnl3-devel gcc gcc-c++ libgudev.x86_64 libgudev-devel.x86_64 systemd* abrt-cli boost-devel.x86_64']
        self.add_environment_to_file_vm(qemu, vm_name, 'http_proxy', 'export http_proxy=http://proxy-iind.intel.com:911')
        self.add_environment_to_file_vm(qemu, vm_name, 'HTTP_PROXY', 'export HTTP_PROXY=http://proxy-iind.intel.com:911')
        self.add_environment_to_file_vm(qemu, vm_name, 'https_proxy', 'export https_proxy=http://proxy-iind.intel.com:911')
        self.add_environment_to_file_vm(qemu, vm_name, 'HTTPS_PROXY', 'export HTTPS_PROXY=http://proxy-iind.intel.com:911')
        self.add_environment_to_file_vm(qemu, vm_name, 'no_proxy', "export no_proxy='localhost,127.0.0.1,intel.com,.intel.com'")
        for rpm in rpm_list:
            qemu.execute_vm_cmd(vm_name, f'yum -y install {rpm}', timeout=60000)
        qemu.execute_vm_cmd(vm_name, f'yum -y install make', timeout=60000)
        qemu.execute_vm_cmd(vm_name, f'yum -y install patch', timeout=60000)

    def rpm_install_rich_vm(self, qemu):
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
        self.add_environment_to_file_rich_vm(qemu, 'http_proxy', 'export http_proxy=http://proxy-iind.intel.com:911')
        self.add_environment_to_file_rich_vm(qemu, 'HTTP_PROXY', 'export HTTP_PROXY=http://proxy-iind.intel.com:911')
        self.add_environment_to_file_rich_vm(qemu, 'https_proxy', 'export https_proxy=http://proxy-iind.intel.com:911')
        self.add_environment_to_file_rich_vm(qemu, 'HTTPS_PROXY', 'export HTTPS_PROXY=http://proxy-iind.intel.com:911')
        self.add_environment_to_file_rich_vm(qemu, 'no_proxy', "export no_proxy='localhost,127.0.0.1,intel.com,.intel.com'")
        for rpm in rpm_list:
            qemu.execute_rich_vm_cmd_parallel(f'yum -y install {rpm}', timeout=60000)
        logger.info(f'yum install packages to every virtual machine successfully')
        qemu.execute_rich_vm_cmd_parallel(f'yum -y install make', timeout=60000)
        qemu.execute_rich_vm_cmd_parallel(f'yum -y install patch', timeout=60000)

    def run_qat_sample_code_vm(self, qemu, vm_name, qat_cpa_param=''):
        """
              Purpose: Run QAT cap_sample stress on VM
              Args:
                  qemu: Call VM Class RichHypervisor
                  vm_name: Run command on which VM
                  qat_cpa_param: Which cap_sample stress need to run
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: run cap_sample stress
                        run_qat_sample_code(qemu, vm_name, '')
                        run_qat_sample_code(qemu, vm_name, 'signOfLife=1')
        """
        _, out, err = qemu.execute_vm_cmd(vm_name, './cpa_sample_code ' + qat_cpa_param, timeout=10 * 60, cwd=f'{QAT_DRIVER_PATH_L}/build/')
        self.check_keyword(['Sample code completed successfully'], out, 'Issue - Run qat stress fail')

    def run_qat_sample_code_rich_vm(self, qemu, qat_cpa_param=''):
        """
              Purpose: Run QAT cap_sample stress on VM
              Args:
                  qemu: Call VM Class RichHypervisor
                  vm_name: Run command on which VM
                  qat_cpa_param: Which cap_sample stress need to run
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: run cap_sample stress
                        run_qat_sample_code_rich_vm(qemu, '')
                        run_qat_sample_code_rich_vm(qemu, 'signOfLife=1')
        """
        logger.info(f'start run qat stress in every virtual machine')
        exec_res = qemu.execute_rich_vm_cmd_parallel('./cpa_sample_code ' + qat_cpa_param, timeout=10 * 60, cwd=f'{QAT_DRIVER_PATH_L}/build/')
        for vm in exec_res:
            out = exec_res[vm][1]
            self.check_keyword(['Sample code completed successfully'], out, 'Issue - Run qat stress fail')
        logger.info(f'run qat stress in every virtual machine successfully')

    def run_qat_sample_code_vm_async(self, qemu, vm_name, qat_cpa_param=''):
        """
              Purpose: Run qat sample stress asynchronously in vm
              Args:
                  qemu: Call VM Class RichHypervisor
                  vm_name: Run command on which VM
                  qat_cpa_param: Which cap_sample stress need to run
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: run cap_sample stress
                        run_qat_sample_code(qemu, vm_name, '')
                        run_qat_sample_code(qemu, vm_name, 'signOfLife=1')
        """

        _, out, err = qemu.execute_vm_cmd_async(vm_name, './cpa_sample_code ' + qat_cpa_param, timeout=10 * 60, cwd=f'{QAT_DRIVER_PATH_L}/build/')
        self.check_keyword(['Sample code completed successfully'], out, 'Issue - Run qat stress fail')

    def run_qat_stress_vm_async(self, qemu, vm_name):
        """

              Purpose: Run QAT asynchronous stress overnight in VM
              Args:
                  qemu: Call VM Class RichHypervisor
                  vm_name: Run command on which VM
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Run QAT asynchronous stress overnight in VM
                        run_qat_stress_vm_async(qemu, vm_name)
        """
        qemu.execute_vm_cmd_async(vm_name, 'rm -rf qat_vm_async.log', timeout=60, cwd='/root/')
        qemu.execute_vm_cmd_async(vm_name,
                                  'while [ $SECONDS -lt 300 ]; do /home/BKCPkg/domains/accelerator/QAT/build/cpa_sample_code runTests=63 signOfLife=1 ; done | tee /root/qat_vm_async.log')


    def run_qat_stress_rich_vm_async(self, qemu):
        """

              Purpose: Run QAT asynchronous stress overnight in VM
              Args:
                  qemu: Call VM Class RichHypervisor
                  vm_name: Run command on which VM
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Run QAT asynchronous stress overnight in VM
                        run_qat_stress_vm_async(qemu, vm_name)
        """
        qemu.execute_rich_vm_cmd_parallel('rm -rf qat_vm_async.log', timeout=60, cwd='/root/')
        qemu.execute_rich_vm_cmd_parallel_async('while [ $SECONDS -lt 100 ]; do /home/BKCPkg/domains/accelerator/QAT/build/cpa_sample_code runTests=63 signOfLife=1 ; done | tee /root/qat_vm_async.log')

    # VMware-APIs
#################################################################################################

    def check_acce_device_esxi(self, acce_module_name, cpu_num, is_driver_installed=False):
        """
             Purpose: Check accelerator device status
             Args:
                 acce_module_name: this is accelerator device name, eg: 'qat', 'dlb', 'iadx'
                 is_driver_installed: check driver installed or not
             Returns:
                 No
             Raises:
                 RuntimeError: If any errors
             Example:
                 Simplest usage: Get CPU number in BIOS serial log
                     get_cpu_num_esxi()
       """
        if acce_module_name == 'qat':
            _, out, err = self.sut.execute_shell_cmd(f'lspci -p | grep 8086:{self.qat_id}', timeout=60)
            self.__detact_device_in_esxi(out, [f'{self.qat_id}', 'V'], 'qat', cpu_num)
            if is_driver_installed:
                self.__detact_device_in_esxi(out, [f'{self.qat_id}', 'V', 'qat'], 'qat', cpu_num)
        elif acce_module_name == 'dlb':
            _, out, err = self.sut.execute_shell_cmd(f'lspci -p | grep 8086:{self.dlb_id}', timeout=60)
            self.__detact_device_in_esxi(out, [f'{self.dlb_id}', 'V'], 'dlb', cpu_num)
            if is_driver_installed:
                self.__detact_device_in_esxi(out, [f'{self.dlb_id}', 'V', 'dlb'], 'dlb', cpu_num)
        elif acce_module_name == 'iadx':
            _, out, err = self.sut.execute_shell_cmd(f'lspci -p | grep 8086:{self.dsa_id}', timeout=60)
            self.__detact_device_in_esxi(out, [f'{self.dsa_id}', 'V'], 'dsa', cpu_num)
            if is_driver_installed:
                self.__detact_device_in_esxi(out, [f'{self.dsa_id}', 'V', 'iadx'], 'dsa', cpu_num)
        elif acce_module_name == 'iads':
            _, out, err = self.sut.execute_shell_cmd(f'lspci -p | grep 8086:{self.dsa_id}', timeout=60)
            self.__detact_device_in_esxi(out, [f'{self.dsa_id}', 'V'], 'dsa', cpu_num)
            if is_driver_installed:
                self.__detact_device_in_esxi(out, [f'{self.dsa_id}', 'V', 'iads'], 'dsa', cpu_num)
    def dsa_driver_install_esxi(self):
        """
              Purpose: To install DSA driver
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Install DSA driver
                      dsa_driver_install_esxi()
        """
        self.sut.execute_shell_cmd(f'mkdir -p {DSA_DRIVER_PATH_V}', timeout=60) #add by jin
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=DSA_DRIVER_PATH_V)
        self.sut.upload_to_remote(localpath=DSA_DRIVER_V_H, remotepath=DSA_DRIVER_PATH_V)
        self.sut.execute_shell_cmd('unzip -j *.zip', timeout=60, cwd=DSA_DRIVER_PATH_V)
        self.sut.execute_shell_cmd(f'tar -xvf *.tar', timeout=60, cwd=DSA_DRIVER_PATH_V) #add by jin
        self.sut.execute_shell_cmd('unzip VMW-esx-*.zip', timeout=60, cwd=DSA_DRIVER_PATH_V)
        _, out, err = self.sut.execute_shell_cmd(
            f'esxcli software vib install --maintenance-mode --no-sig-check -v {DSA_DRIVER_PATH_V}vib20/iads/INT*.vib',
            timeout=5 * 60)
        self.check_keyword(['Operation finished successfully'], out, 'DSA driver install fail')
        self.__load_driver()
        self.my_os.warm_reset_cycle_step(self.sut)
        self.Case.sleep(60)
        self.__check_acce_driver('iads')

    def dlb_driver_install_esxi(self, is_siov=False):
        """
              Purpose: To install dlb driver
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Install dlb driver
                      dlb_driver_install_esxi()
        """
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=DLB_DRIVER_PATH_V)
        self.sut.upload_to_remote(localpath=DLB_DRIVER_V_H, remotepath=DLB_DRIVER_PATH_V)
        self.sut.execute_shell_cmd('unzip *.zip', timeout=60, cwd=DLB_DRIVER_PATH_V)
        _, out, err = self.sut.execute_shell_cmd('ls  *.tar.gz', cwd='/home/BKCPkg/domains/accelerator/dlb', timeout=30)
        out = out.strip().split()
        line = []
        for i in out:
            line.append(i)
        for a in range(len(line)):
            if 'dvx' in line[a]:
                siov_tool = str(line[a])
            else:
                sriov_tool = str(line[a])
        if is_siov:
            # self.sut.execute_shell_cmd('tar -zxvf dlb_siov_*.tar.gz', timeout=60, cwd=DLB_DRIVER_PATH_V)
            self.sut.execute_shell_cmd(f'tar -zxvf {siov_tool}', timeout=60, cwd=DLB_DRIVER_PATH_V)
            self.Case.sleep(10)
            _, out, err = self.sut.execute_shell_cmd(
                f'esxcli software component apply --no-sig-check -d {DLB_DRIVER_PATH_V}INT-esx*.zip', timeout=5 * 60)
            self.check_keyword(['The update completed successfully', 'Reboot Required: true'], out,
                               'dlb driver install fail')
            self.my_os.warm_reset_cycle_step(self.sut)
            self.__check_acce_driver('dlb')
        else:
            # self.sut.execute_shell_cmd('tar -zxvf dlb_sriov_*.tar.gz', timeout=60, cwd=DLB_DRIVER_PATH_V)
            self.sut.execute_shell_cmd(f'tar -zxvf {sriov_tool}', timeout=60, cwd=DLB_DRIVER_PATH_V)
            _, out, err = self.sut.execute_shell_cmd(
                f'esxcli software component apply --no-sig-check -d {DLB_DRIVER_PATH_V}VMW*.zip', timeout=5 * 60)
            self.check_keyword(['The update completed successfully', 'Reboot Required: true'], out,
                               'dlb driver install fail')
            self.my_os.warm_reset_cycle_step(self.sut)
            self.Case.sleep(60)
            self.__check_acce_driver('dlb')

    def get_cpu_num_esxi(self):
        """
             Purpose: Get CPU number in BIOS serial log
             Args:
                 No
             Returns:
                 No
             Raises:
                 RuntimeError: If any errors
             Example:
                 Simplest usage: Get CPU number in BIOS serial log
                     get_cpu_num_esxi()
       """
        self.sut.execute_shell_cmd('reboot', timeout=30 * 60)
        # self.Case.wait_and_expect(f'SUT in OS', 10 * 60, self.sut.check_system_in_os)
        self.Case.sleep(8 * 60)
        bios_log = os.path.join(LOG_PATH, 'bios.log')
        with open(bios_log, 'r') as file:
            line_str = '\n'.join(file.readlines())
            file_list = line_str.split('Calculate Resource Allocation - END')
            cpu_info = file_list[0].split('CPU Resource Allocation')
            line_list = cpu_info[1].strip().split('\n')
            cpu_num = 0
            for line in line_list:
                if 'CPU' in line:
                    cpu_num += 1
            return cpu_num

    def qat_driver_install_esxi(self):
        """
              Purpose: To install QAT driver
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Install QAT driver
                      qat_driver_install_esxi
        """
        self.sut.execute_shell_cmd('rm -rf *', timeout=60, cwd=QAT_DRIVER_PATH_V)
        self.sut.upload_to_remote(localpath=QAT_DRIVER_V_H, remotepath=QAT_DRIVER_PATH_V)
        self.sut.execute_shell_cmd('unzip *.zip', timeout=60, cwd=QAT_DRIVER_PATH_V)
        # self.sut.execute_shell_cmd('tar -zxvf *.tar.gz', timeout=60, cwd=QAT_DRIVER_PATH_V)
        _, out, err = self.sut.execute_shell_cmd(f'esxcli software component apply --no-sig-check -d {QAT_DRIVER_PATH_V}qat-*/*.zip', timeout=5 * 60)
        self.check_keyword(['Installed: Intel-qat', 'Operation finished successfully'], out,
                           'QAT driver install fail')
        self.__load_driver()
        self.my_os.warm_reset_cycle_step(self.sut)
        self.Case.sleep(60)
        self.__check_acce_driver('qat')

    def uninstall_driver_esxi(self, acce_module_name):
        """
              Purpose: To uninstall accelerator device driver
              Args:
                  acce_module_name: this is accelerator device name, eg: 'qat', 'dlb', 'iadx'
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Uninstall accelerator device driver
                      uninstall_driver_esxi()
        """
        if acce_module_name == 'qat':
            _, out, err = self.sut.execute_shell_cmd(f'esxcfg-module -u {acce_module_name}', timeout=60)
            self.check_keyword([f'Module {acce_module_name} unloaded successfully'], out, 'uninstall driver fail')
            _, out, err = self.sut.execute_shell_cmd(
                f'esxcli software component remove -n Intel-{acce_module_name}', timeout=60)
            self.check_keyword([f'Components Removed: Intel-{acce_module_name}', 'Operation finished successfully'],
                               out, f'uninstall {acce_module_name} driver fail')
        if acce_module_name == 'dlb':
            _, out, err = self.sut.execute_shell_cmd(f'esxcfg-module -u {acce_module_name}', timeout=60)
            self.check_keyword([f'Module {acce_module_name} unloaded successfully'], out, 'uninstall driver fail')
            _, out, err = self.sut.execute_shell_cmd(
                f'esxcli software component remove -n Intel-{acce_module_name}', timeout=60)
            self.check_keyword([f'Components Removed: Intel-{acce_module_name}',
                                'The update completed successfully, but the system needs to be rebooted for the changes to be effective.'],
                               out, f'uninstall {acce_module_name} driver fail')
            self.my_os.warm_reset_cycle_step(self.sut)

        elif acce_module_name == 'iadx':
            _, out, err = self.sut.execute_shell_cmd(f'vmkload_mod --unload {acce_module_name}', timeout=60)
            self.check_keyword([f'Module {acce_module_name} successfully unloaded'], out, 'uninstall driver fail')
            _, out, err = self.sut.execute_shell_cmd(
                f'esxcli software vib remove --maintenance-mode -n {acce_module_name}', timeout=60)
            self.check_keyword(['Operation finished successfully'], out,
                               f'uninstall {acce_module_name} driver fail')
        elif acce_module_name == 'iads':
            _, out, err = self.sut.execute_shell_cmd(f'vmkload_mod --unload {acce_module_name}', timeout=60)
            self.check_keyword([f'Module {acce_module_name} successfully unloaded'], out, 'uninstall driver fail')
            _, out, err = self.sut.execute_shell_cmd(
                f'esxcli software vib remove --maintenance-mode -n {acce_module_name}', timeout=60)
            self.check_keyword(['Operation finished successfully'], out,
                               f'uninstall {acce_module_name} driver fail')

#############################################################################################################

    def __cc6_value_check(self, out):
        cpu_num = self.get_cpu_num()
        core_num = self.__get_core_num()
        line_list = out.strip().split('CC6')
        cc6_line_list = line_list[1].split('Core C-State Summary: Entry Counts')
        word_list = cc6_line_list[0].strip().split(',')
        value_list = []
        for word in word_list:
            value_list.append(word.strip())
        less_100_value_list = []
        for word in value_list:
            if word != '' and float(word) <= 100.00:
                less_100_value_list.append(word)
        cc6_num = 0
        for word in less_100_value_list:
            if float(word) >= 70:
                cc6_num += 1
        if cc6_num != cpu_num * core_num:
            logger.error('Not all core CC6 Residency value more than 70%')
            raise Exception('Not all core CC6 Residency value more than 70%')

    def __check_acce_driver(self, acce_module_name):
        _, out, err = self.sut.execute_shell_cmd(f'esxcfg-module -l | grep {acce_module_name}', timeout=60)
        self.check_keyword([f'{acce_module_name}'], out, f'detect {acce_module_name} driver fail')

    # def __check_all_device_wq(self, cpu_num, device_num, out):
    #     line_list = out.strip().split('\n')
    #     dsa_enable_num = 0
    #     for line in line_list:
    #         if '"state":"enabled"' in line:
    #             dsa_enable_num += 1
    #     if dsa_enable_num != cpu_num * device_num * 9:
    #         logger.error('Not all dsa grouped_workqueues are enabled')
    #         raise Exception('Not all dsa grouped_workqueues are enabled')


    def __check_all_device_wq(self, out, device_num, acce_ip):
        if '"state":"disabled"' in out:
            logger.error('Some disabled wq are showed')
            raise Exception('Some disabled wq are showed')
        enabled_device_num = 0
        line_list = out.strip().split('\n')
        for line in line_list:
            if f'"dev":"{acce_ip}' in line:
                enabled_device_num += 1
        if device_num != enabled_device_num:
            logger.error('Not all device are detected')
            raise Exception('Not all device are detected')


    def __check_enabled_wq_num(self, out):
        line_list = out.strip().split('Enabling')
        work_queues_list = line_list[2].split('enabled')
        queues_word_list = work_queues_list[1].strip().split(' ')
        return queues_word_list[0]

    def __check_error(self, err):
        if err != '':
            logger.error(err)
            raise Exception(err)

    def __check_device_in_vm(self, out, vf_num, check_key):
        dev_num = 0
        line_list = out.strip().split('\n')
        for line in line_list:
            if check_key in line:
                dev_num += 1
        if dev_num != vf_num:
            logger.error("Can't detact attached device")
            raise Exception("Can't detact attached device")

    def __check_random_device_wq(self, out, device_num, acce_ip):
        if '"state":"disabled"' in out:
            logger.error('Some disabled wq are showed')
            raise Exception('Some disabled wq are showed')
        enabled_device_num = 0
        line_list = out.strip().split('\n')
        for line in line_list:
            if f'"dev":"{acce_ip}' in line:
                enabled_device_num += 1
        if device_num != enabled_device_num:
            logger.error('Not all device are detected')
            raise Exception('Not all device are detected')

    def __choose_run_folder(self, command, is_reset_folder=False):
        if not is_reset_folder:
            self.sut.execute_shell_cmd('chmod 777 *', timeout=5 * 60, cwd=f'{SPR_ACCE_RANDOM_CONFIG_PATH_L}*/')
            _, out, err = self.sut.execute_shell_cmd(f'./{command}', timeout=5 * 60, cwd=f'{SPR_ACCE_RANDOM_CONFIG_PATH_L}*/')
        else:
            self.sut.execute_shell_cmd('chmod 777 *', timeout=5 * 60, cwd=f'{SPR_ACCE_RANDOM_CONFIG_PATH_L}*/accelerator_reset/')
            _, out, err = self.sut.execute_shell_cmd(f'./{command}', timeout=5 * 60, cwd=f'{SPR_ACCE_RANDOM_CONFIG_PATH_L}*/accelerator_reset/')
        return out

    def __cpu_idle_value_check(self, out):
        thread_num = self.__get_thread_num()
        line_list = out.strip().split('CPU Idle')
        cpu_idle_list = line_list[1].split('CPU P-State/Frequency Summary: Total Samples Received')
        cpu_idle_list = cpu_idle_list[0].strip().split(',')
        word_list = []
        for word in cpu_idle_list:
            word_list.append(word.strip())
        print(word_list)
        cpu_idle_value_less_100_list = []
        for word in word_list:
            if word != '' and float(word) <= 100.00:
                cpu_idle_value_less_100_list.append(word)
        cpu_idle_num = 0
        for word in cpu_idle_value_less_100_list:
            if float(word) >= 70:
                cpu_idle_num += 1
        if cpu_idle_num != thread_num:
            logger.error('Not all thread cpu idle value more than 70%')
            raise Exception('Not all thread cpu idle value more than 70%')

    def __detact_device_in_esxi(self, out, key_list, acce_ip, cpu_num):
        qat_line_list = out.strip().split('\n')
        for key in key_list:
            key_num = 0
            for line in qat_line_list:
                if key in line:
                    key_num += 1
            if acce_ip == 'qat':
                if key_num != cpu_num * self.qat_device_num:
                    logger.error('Not all device are recognized')
                    raise Exception('Not all device are recognized')
            elif acce_ip == 'dlb':
                if key_num != cpu_num * self.dlb_device_num:
                    logger.error('Not all device are recognized')
                    raise Exception('Not all device are recognized')
            elif acce_ip == 'dsa':
                if key_num != cpu_num * self.dsa_device_num:
                    logger.error('Not all device are recognized')
                    raise Exception('Not all device are recognized')

    def __get_core_num(self):
        """
              Purpose: Get current SUT core numbers
              Args:
                  No
              Returns:
                  Yes: return core numbers
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Get current SUT core numbers
                        __get_core_num()
        """
        _, out, err = self.sut.execute_shell_cmd('lscpu', timeout=60)
        line_list = out.strip().split('\n')
        for line in line_list:
            word_list = line.split()
            if word_list[0] == 'Core(s)':
                core_num = int(word_list[3])
                return core_num

    def __get_dlb_pci_id_list(self, dev_id_list):
        """
              Purpose: Modify the format of DLB device ID list
              Args:
                  dev_id_list : DLB device ID list --># ['0000:6d:00.1','0000:6d:00.2','0000:6d:00.3']
              Returns:
                  Yes  --> # '0000_6d_00_1''0000_6d_00_2''0000_6d_00_3'
              Example:
                  Simplest usage: Modify the format of DLB device ID list
                        __get_dlb_pci_id_list(['0000:6d:00.1','0000:6d:00.2','0000:6d:00.3'])
                        return '0000_6d_00_1''0000_6d_00_2''0000_6d_00_3'
        """
        dlb_pci_id_list = []
        for dev_id in dev_id_list:
            change_li = []
            word_list_split = dev_id.split(
                ':')  # [' 0000', '6d', '00.1'][' 0000', '6d', '00.2'][' 0000', '6d', '00.3']
            word_list_change = word_list_split[2].split('.')  # ['00', '1']['00', '2']['00', '3']
            change_li.append(word_list_split[0])  # [' 0000][' 0000'][' 0000']
            change_li.append(word_list_split[1])  # [' 0000', '6d'][' 0000', '6d'][' 0000', '6d']
            change_li.append(word_list_change[0])  # [' 0000', '6d','00'][' 0000', '6d','00'][' 0000', '6d', '00']
            change_li.append(
                word_list_change[1])  # [' 0000', '6d','00', '1'][' 0000', '6d','00', '2'][' 0000', '6d', '00', '3']
            i = 1
            while i < len(change_li):
                change_li.insert(i,
                                 '_')  # [' 0000', '_', '6d', '_', '00', '_', '1'][' 0000', '_', '6d', '_', '00', '_', '2'][' 0000', '_', '6d', '_', '00', '_', '3']
                i += 2
            change_str = ''.join(change_li)  # ' 0000_6d_00_1'' 0000_6d_00_2'' 0000_6d_00_3'
            change_str = change_str.strip()  # '0000_6d_00_1''0000_6d_00_2''0000_6d_00_3'
            dlb_pci_id_list.append(change_str)
        return dlb_pci_id_list

    def __get_dlb_unbind_path(self, dev_id):  # '0000:6d:00.1'
        """
              Purpose: Get True DLB device ID
              Args:
                  dev_id: DLB device ID, this is DLB True device ID or virtual DLB device ID
              Returns:
                  Yes  --> '0000:6d:00.0'
              Example:
                  Simplest usage: get DLB True device 0 and create 2 DLB Vietual device for Platform
                        __get_dlb_unbind_path('0000:6d:00.1')
                        return'0000:6d:00.0'
        """
        is_vf = dev_id.split(':')
        if is_vf[2] == '00.0':
            dlb_pf_id = dev_id  # '0000:6d:00.0'
        else:
            before_id = dev_id.split(".")
            dlb_pf_id = before_id[0] + '.0'  # '0000:6d:00.0'
        return dlb_pf_id  # '0000:6d:00.0'

    def __get_qat_pci_id(self, dev_id):
        """
              Purpose: Modify the format of QAT device ID
              Args:
                  dev_id : QAT device ID -->'0000:6d:00.0'
              Returns:
                  Yes  --> '0000_6b_00_1'
              Example:
                  Simplest usage: Modify the format of QAT device ID
                        __get_qat_pci_id(0000:6d:00.0)
                        return '0000_6b_00_1'
        """
        change_li = []
        word_list_split = dev_id.split(':')  # [' 0000', '6b', '00.1']
        word_list_change = word_list_split[2].split('.')  # ['00', '1']
        change_li.append(word_list_split[0])  # [' 0000]
        change_li.append(word_list_split[1])  # [' 0000', '6b']
        change_li.append(word_list_change[0])  # [' 0000', '6b','00']
        change_li.append(word_list_change[1])  # [' 0000', '6b','00', '1']
        i = 1
        while i < len(change_li):
            change_li.insert(i, '_')  # [' 0000', '_', '6b', '_', '00', '_', '1']
            i += 2
        change_str = ''.join(change_li)  # ' 0000_6b_00_1'
        change_str = change_str.strip()  # '0000_6b_00_1'
        return change_str

    def __get_qat_unbind_path(self, dev_id):
        """
              Purpose: Modify the format of QAT device ID
              Args:
                  dev_id : QAT device ID -->'0000:6d:00.0'
              Returns:
                  Yes  --> '0000\:6b\:00.0'
              Example:
                  Simplest usage: Modify the format of QAT device ID
                        __get_qat_unbind_path(0000:6d:00.0)
                        return '0000\:6b\:00.0'
        """
        word_split = dev_id.split(':')  # [' 0000', '6b', '00.0']
        i = 1
        while i < len(word_split):
            word_split.insert(i, '\\:')  # [' 0000', '\\:', '6b', '\\:', '00.0']
            i += 2
        change_word = "".join(word_split)  # ' 0000\:6b\:00.0'
        change_word = change_word.strip()  # '0000\:6b\:00.0'
        return change_word

    def __get_thread_num(self):
        """
              Purpose: Get current SUT core numbers
              Args:
                  No
              Returns:
                  Yes: return core numbers
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Get current SUT core numbers
                        __get_core_num()
        """
        _, out, err = self.sut.execute_shell_cmd('lscpu', timeout=60)
        line_list = out.strip().split('\n')
        for line in line_list:
            word_list = line.split()
            if word_list[0] == 'CPU(s):':
                thread_num = int(word_list[1])
                return thread_num

    def __load_driver(self):
        res, out, err = self.sut.execute_shell_cmd('kill -HUP $(cat /var/run/vmware/vmkdevmgr.pid)', timeout=5 * 60)
        if res != 0:
            logger.error('kill vmkdevmgr fail')
            raise Exception('kill vmkdevmgr fail')
        self.Case.sleep(30)

    def __qat_asym_config(self):
        """
              Purpose: Modify QAT asymmetric encrypted files config
              Args:
                  No
              Returns:
                  No
              Raises:
                  RuntimeError: If any errors
              Example:
                  Simplest usage: Modify QAT asym metric encrypted files config
                        __qat_asym_config()
        """
        cpu_num = self.get_cpu_num()
        for i in range(cpu_num*self.qat_device_num):
            self.sut.execute_shell_cmd(f'sed -i "s/ServicesEnabled.*/ServicesEnabled = asym;dc/g" /etc/4xxx_dev{i}.conf', timeout=60)
        self.qat_service_restart()

    def __qat_asym_config_clr(self):
        """
              Purpose: Clear QAT asymmetric encrypted config files
              Args:
                  No
              Returns:
                  No
              Example:
                  Simplest usage: Clear QAT asymmetric encrypted config files
                        __qat_asym_config_clr()
        """
        cpu_num = self.get_cpu_num()
        for i in range(cpu_num*self.qat_device_num):
            self.sut.execute_shell_cmd(f'sed -i "s/ServicesEnabled = asym;dc/ServicesEnabled = sym;dc/g" /etc/4xxx_dev{i}.conf', timeout=60)
        self.qat_service_restart()

    def __qat_mdev_config(self):
        """
              Purpose: Modify QAT SIOV config files
              Args:
                  No
              Returns:
                  No
              Example:
                  Simplest usage: Modify QAT SIOV config files
                        __qat_mdev_config()
        """
        cpu_num = self.get_cpu_num()
        for i in range(cpu_num*self.qat_device_num):
            self.sut.execute_shell_cmd(f'sed -i "s/NumberAdis = 0/NumberAdis = 16/g" /etc/4xxx_dev{i}.conf', timeout=60)
        self.qat_service_stop_start()

    def __qat_mdev_config_clr(self):
        """
              Purpose: Clear QAT SIOV config files
              Args:
                  No
              Returns:
                  No
              Example:
                  Simplest usage: Clear QAT SIOV config files
                        __qat_mdev_config_clr()
        """
        cpu_num = self.get_cpu_num()
        for i in range(cpu_num*self.qat_device_num):
            self.sut.execute_shell_cmd(f'sed -i "s/NumberAdis = 16/NumberAdis = 0/g" /etc/4xxx_dev{i}.conf', timeout=60)
        self.qat_service_restart()

    def __qat_service_restart(self):
        _, out, err = self.sut.execute_shell_cmd('service qat_service restart', timeout=10 * 60)
        if "Unit qat_service.service not found" in err:
            _, out, err = self.sut.execute_shell_cmd('qat_service restart', timeout=10 * 60)
            return out
        return out

    def __qat_shim_config(self):
        """
              Purpose: Modify QAT SSL config files
              Args:
                  No
              Returns:
                  No
              Example:
                  Simplest usage: Modify QAT SSL config files
                        __qat_shim_config()
        """
        cpu_num = self.get_cpu_num()
        for i in range(cpu_num*self.qat_device_num):
            self.sut.execute_shell_cmd(f'sed -i "s/\[SSL\]/\[SHIM\]/g" /etc/4xxx_dev{i}.conf', timeout=60)
            self.sut.execute_shell_cmd(f'sed -i "s/NumberCyInstances = 3/NumberCyInstances = 1/g" /etc/4xxx_dev{i}.conf',
                                  timeout=60)
            self.sut.execute_shell_cmd(f'sed -i "s/NumberDcInstances = 2/NumberDcInstances = 1/g" /etc/4xxx_dev{i}.conf',
                                  timeout=60)
            self.sut.execute_shell_cmd(f'sed -i "s/NumProcesses = 1/NumProcesses = 16/g" /etc/4xxx_dev{i}.conf', timeout=60)
            self.sut.execute_shell_cmd(f'sed -i "s/LimitDevAccess = 0/LimitDevAccess = 1/g" /etc/4xxx_dev{i}.conf',
                                  timeout=60)
        self.qat_service_restart()

    def __qat_shim_config_clr(self):
        """
              Purpose: Clear QAT SSL config files
              Args:
                  No
              Returns:
                  No
              Example:
                  Simplest usage: Clear QAT SSL config files
                        __qat_shim_config_clr()
        """
        cpu_num = self.get_cpu_num()
        for i in range(cpu_num*self.qat_device_num):
            self.sut.execute_shell_cmd(f'sed -i "s/\[SHIM\]/\[SSL\]/g" /etc/4xxx_dev{i}.conf', timeout=60)
            self.sut.execute_shell_cmd(f'sed -i "s/NumberCyInstances = 1/NumberCyInstances = 3/g" /etc/4xxx_dev{i}.conf',
                                  timeout=60)
            self.sut.execute_shell_cmd(f'sed -i "s/NumberDcInstances = 1/NumberDcInstances = 2/g" /etc/4xxx_dev{i}.conf',
                                  timeout=60)
            self.sut.execute_shell_cmd(f'sed -i "s/NumProcesses*/NumProcesses = 1/g" /etc/4xxx_dev{i}.conf', timeout=60)
            self.sut.execute_shell_cmd(f'sed -i "s/LimitDevAccess = 1/LimitDevAccess = 0/g" /etc/4xxx_dev{i}.conf',
                                  timeout=60)
        self.qat_service_restart()

    def __usb_device_detact(self):
        out = self.sut.execute_uefi_cmd('map -r', timeout=60)
        line_list = out.strip().split('FS')
        for line in line_list:
            if 'USB' in line:
                line.split(':')
                return line[0]





