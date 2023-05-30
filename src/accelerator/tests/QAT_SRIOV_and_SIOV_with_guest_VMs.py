# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.accelerator.lib import *


CASE_DESC = [
    'Check QAT device',
    'QAT driver install',
    'check cpa_sample_code file generate'
]


def test_steps(sut, my_os):
    acce = Accelerator(sut)
    qemu = RichHypervisor(sut)

    # Prepare steps - call predefined steps
    Case.prepare('boot to OS and enable VT-d  in BIOS')
    logger.info('')
    logger.info('---- Test Boot to Default os ----')
    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('knob_setting_sriov_common_xmlcli'))
    sut.execute_shell_cmd('ln -s /usr/bin/python3 /usr/bin/python', timeout=60)
    acce.rpm_install()
    acce.kernel_header_devel()
    acce.init_bashrc()

    # Step 1
    Case.step('copy vm file and OVMF file to SUT')
    # sut.execute_shell_cmd(f'wget {VM_PATH_L}', timeout=30 * 60, cwd='/home/')
    # sut.execute_shell_cmd('xz -d *.img.xz', timeout=10 * 60, cwd='/home/')
    # sut.execute_shell_cmd('cp centos_basic.qcow2 centos.qcow2', timeout=10 * 60, cwd='/home/')
    sut.upload_to_remote(localpath=OVMF_H, remotepath=OVMF_PATH_L)
    file_name = f'{IMAGE_PATH_L}{IMAGE_NAME}'

    # Step 2
    Case.step('Add SRIOV function to grub file and clear abort log')
    acce.modify_kernel_grub('intel_iommu=on,sm_off', True)
    sut.execute_shell_cmd('abrt-auto-reporting enabled', timeout=60)
    sut.execute_shell_cmd('abrt-cli rm /var/spool/abrt/*', timeout=60)

    # step 3
    Case.step('Install sut environments')
    sut.execute_shell_cmd('python -m pip install --upgrade pip --proxy=http://child-prc.intel.com:913', timeout=120)
    sut.execute_shell_cmd('python -m pip install --upgrade paramiko --proxy=http://child-prc.intel.com:913', timeout=180)
    sut.execute_shell_cmd(f'mkdir {SRC_SCRIPT_PATH_L}')
    sut.execute_shell_cmd(f'rm -rf {SRC_SCRIPT_PATH_L}*')
    sut.upload_to_remote(localpath=SRC_SCRIPT_H, remotepath=SRC_SCRIPT_PATH_L)
    sut.execute_shell_cmd('unzip *', timeout=60*5, cwd=SRC_SCRIPT_PATH_L)

    # Step 4
    Case.step('Check QAT device status and install QAT driver')
    acce.check_acce_device_status('qat')
    acce.qat_uninstall()
    acce.qat_install(True)
    acce.check_qat_service_status(True)

    vm_name = 'vm'

    # Step 5
    def choose_qat_device(num):
        Case.step('Unbind QAT VF 1')
        qat_dev_id = acce.get_dev_id('qat', 0, num)
        print(qat_dev_id)
        acce.unbind_device(f'qat_0_{num}')
        return qat_dev_id

    qat_dev_id = choose_qat_device(1)

    # Step 6
    Case.step('Open VM and install kernel header and kernel devel file')
    qemu.create_vm_from_template(vm_name, file_name)
    # qemu.create_qemu_vm_debug(vm_name)
    qemu.attach_acce_dev_to_vm(vm_name, [qat_dev_id])
    # qemu.start_qemu_vm_debug(vm_name, ssh_port='2222')
    qemu.start_vm(vm_name)

    # Step 7
    Case.step('Install rpm package and kernel packages')
    acce.kernel_header_devel_vm(qemu, vm_name)
    acce.rpm_install_vm(qemu, vm_name)
    qemu.execute_vm_cmd(vm_name, 'abrt-auto-reporting enabled && abrt-cli rm /var/spool/abrt/*')

    # Step 8
    Case.step('Check QAT device in vm')
    acce.check_device_in_vm(qemu, vm_name, 'qat', 1)

    # Step 9
    Case.step('Install QAT driver and run qat sanmple code stress')
    acce.qat_install_vm(qemu, vm_name, './configure --enable-icp-sriov=guest')
    acce.run_qat_sample_code_vm(qemu, vm_name, '')

    # Step 10
    Case.step('check mce error and shutdown vm')
    rcode, out, err = qemu.execute_vm_cmd(vm_name, 'abrt-cli list | grep mce|wc -l', timeout=60)
    if int(out) != 0:
        logger.error(err)
        raise Exception(err)
    qemu.shutdown_vm(vm_name)
    qemu.undefine_vm(vm_name, True)

    # Step 11
    Case.step('re-install QAT driver and re-config SIOV grub config')
    acce.qat_uninstall()
    acce.modify_kernel_grub('intel_iommu=on,sm_off', False)
    acce.modify_kernel_grub('intel_iommu=on,sm_on', True)
    acce.qat_install(True)
    acce.check_qat_service_status(True)

    # Step 12
    Case.step('Modify QAT config file and show VQAT device')
    acce.modify_qat_config_file('mdev')
    _, out, err = sut.execute_shell_cmd('./build/vqat_ctl show', timeout=60, cwd=f'{QAT_DRIVER_PATH_L}')
    cpu_num = acce.get_cpu_num()
    line_list = out.strip().split('BDF:')
    line_list.pop(0)
    sym_device_num = 0
    dc_device_num = 0
    for line in line_list:
        str_list = line.strip().split('\n')
        sym_name = str_list[1].strip().split(':')
        sym_num = int(sym_name[1].strip())
        if sym_num == 8:
            sym_device_num += 1
        dc_name = str_list[3].strip().split(':')
        dc_num = int(dc_name[1].strip())
        if dc_num == 8:
            dc_device_num += 1
    print(sym_device_num)
    print(dc_device_num)
    if sym_device_num != cpu_num * acce.qat_device_num and dc_device_num != cpu_num * acce.qat_device_num:
        logger.error('Not all device get available sym and available dc value')
        raise Exception('Not all device get available sym and available dc value')
    sut.execute_shell_cmd('./build/vqat_ctl –help', timeout=60, cwd=QAT_DRIVER_PATH_L)

    # Step 13
    Case.step('Enable SIOV on QAT PF')
    get_qat_dev_id_00 = acce.get_dev_id('qat', 0, 0)
    print(get_qat_dev_id_00)
    def get_device_uuid(out):
        device_uuid = ''
        line_list = out.strip().split('\n')
        for line in line_list:
            str_list = line.split(',')
            dev_name = str_list[1].split('=')
            device_uuid = dev_name[1].strip()
        return device_uuid
    _, out, err = sut.execute_shell_cmd(f'./build/vqat_ctl create {get_qat_dev_id_00} sym', timeout=60,
                                        cwd=QAT_DRIVER_PATH_L)
    acce.check_keyword(['VQAT-sym created successfully'], out, 'VQAT-sym create fail')
    sym_uuid = get_device_uuid(out)
    print(sym_uuid)
    _, out, err = sut.execute_shell_cmd('./build/vqat_ctl show', timeout=60, cwd=QAT_DRIVER_PATH_L)
    sym_num = 0
    line_list = out.strip().split('BDF:')
    for line in line_list:
        str_list = line.strip().split('\n')
        if str_list[0] == f'{get_qat_dev_id_00}':
            sym_name = str_list[1].strip().split(':')
            sym_num = int(sym_name[1].strip())
    if sym_num != 7:
        logger.error('VQAT set unsuccessful')
        raise Exception('VQAT set unsuccessful')

    vm_name = 'vm'

    # Step 14
    Case.step('create and start vm')
    qemu.create_vm_from_template(vm_name, file_name, add_by_host=False, is_sriov=False)
    # qemu.create_qemu_vm_debug(vm_name, add_by_host=False, is_sriov=False)
    qemu.attach_acce_dev_to_vm(vm_name, [get_qat_dev_id_00])
    qemu.start_vm(vm_name)
    # qemu.start_qemu_vm_debug(vm_name, ssh_port='2222')

    # Step 15
    Case.step('Install rpm package and kernel packages')
    acce.kernel_header_devel_vm(qemu, vm_name)
    acce.rpm_install_vm(qemu, vm_name)
    qemu.execute_vm_cmd(vm_name, 'abrt-auto-reporting enabled && abrt-cli rm /var/spool/abrt/*')

    # Step 16
    Case.step('check QAT device and install QAT driver')
    rcode, out, err = qemu.execute_vm_cmd(vm_name, "lspci -v -d 8086:0da5 -vmm | grep -E 'SDevice | 0000'")
    acce.check_keyword(['SDevice', 'Device 0000'], out, 'QAT SW installed fail')
    acce.check_device_in_vm(qemu, vm_name, 'qat', 0, mdev=True)
    acce.qat_install_vm(qemu, vm_name, './configure --enable-icp-sriov=guest', enable_siov=True)

    # Step 17
    Case.step('run qat sample code stress with SIOV device')
    rcode, out, err = qemu.execute_vm_cmd(vm_name, './build/adf_ctl qat_dev0 up', cwd=f'{QAT_DRIVER_PATH_L}')
    acce.check_keyword(['Starting device qat_dev0'], out, 'qat_dev0 down')
    rcode, out, err = qemu.execute_vm_cmd(vm_name, 'adf_ctl status')
    acce.check_keyword(['state: up'], out, 'qat_dev0 down')
    acce.run_qat_sample_code_vm(qemu, vm_name, 'signOfLife=1 runTests=63')

    # Step 18
    Case.step('check mce error and shutdown vm')
    rcode, out, err = qemu.execute_vm_cmd(vm_name, 'abrt-cli list | grep mce|wc -l', timeout=60)
    if int(out) != 0:
        logger.error(err)
        raise Exception(err)
    qemu.shutdown_vm(vm_name)
    qemu.undefine_vm(vm_name, True)

    # Step 19
    Case.step('Remove vm file and clear grub config')
    acce.modify_kernel_grub('intel_iommu=on,sm_on', False)


    

    acce.check_python_environment()


def clean_up(sut):
    pass
    # if Result.returncode != 0:
    #     cleanup.to_s5(sut)


def test_main():
    # ParameterParser parses all the embed parameters
    # --help to see all allowed parameters
    user_parameters = ParameterParser.parse_embeded_parameters()
    # add your parameter parsers with list user_parameters

    # if you would like to hardcode to disable clearcmos
    # ParameterParser.bypass_clearcmos = True

    # if commandline provide sut description file by --sut <json file>
    #       generate sut instance from given json file
    #       if multiple files have been provided in command line, only the 1st will take effect for get_default_sut
    #       to get multiple sut, call function get_sut_list instead
    # otherwise
    #       default sut configure file will be loaded
    #       which is defined in basic.config.DEFAULT_SUT_CONFIG_FILE
    sut = get_default_sut()
    my_os = OperationSystem[OS.get_os_family(sut.default_os)]

    try:
        Case.start(sut, CASE_DESC)
        test_steps(sut, my_os)

    except Exception as e:
        Result.get_exception(e, str(traceback.format_exc()))
    finally:
        Case.end()
        clean_up(sut)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)
