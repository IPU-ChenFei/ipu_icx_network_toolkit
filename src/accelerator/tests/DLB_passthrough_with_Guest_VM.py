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

    # Prepare steps - Enable VT-d in BIOS and install rpm package
    Case.prepare('boot to OS and enable VT-d  in BIOS')
    logger.info('')
    logger.info('---- Test Boot to Default os ----')
    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('knob_setting_sriov_common_xmlcli'))
    sut.execute_shell_cmd('ln -s /usr/bin/python3 /usr/bin/python', timeout=60)
    acce.init_bashrc()
    acce.rpm_install()
    acce.kernel_header_devel()

    # Step 1 - copy vm file and OVMF file to SUT
    Case.step('copy vm file and OVMF file to SUT')
    # sut.execute_shell_cmd(f'wget {VM_PATH_L}', timeout=30 * 60, cwd='/home/')
    # sut.execute_shell_cmd('xz -d *.img.xz', timeout=10 * 60, cwd='/home/')
    # sut.execute_shell_cmd('mv *.img.xz centos_basic.qcow2', timeout=10 * 60, cwd='/home/')
    sut.upload_to_remote(localpath=OVMF_H, remotepath=OVMF_PATH_L)
    file_name = f'{IMAGE_PATH_L}{IMAGE_NAME}'

    # Step 2 - Add function to grub file and clear abort log
    Case.step('Add function to grub file and clear abort log')
    acce.modify_kernel_grub('intel_iommu=on,sm_off', True)
    sut.execute_shell_cmd('abrt-auto-reporting enabled', timeout=60)
    sut.execute_shell_cmd('abrt-cli rm /var/spool/abrt/*', timeout=60)

    # Step 3 - Install sut environments
    Case.step('Install sut environments')
    sut.execute_shell_cmd('python -m pip install --upgrade pip --proxy=http://child-prc.intel.com:913', timeout=120)
    sut.execute_shell_cmd('python -m pip install --upgrade paramiko --proxy=http://child-prc.intel.com:913', timeout=180)
    sut.execute_shell_cmd(f'mkdir {SRC_SCRIPT_PATH_L}')
    sut.execute_shell_cmd(f'rm -rf {SRC_SCRIPT_PATH_L}*')
    sut.upload_to_remote(localpath=SRC_SCRIPT_H, remotepath=SRC_SCRIPT_PATH_L)
    sut.execute_shell_cmd('unzip *', timeout=5 * 60, cwd=f'{SRC_SCRIPT_PATH_L}')

    # Step 4 - Install DLB driver and check DLB device status
    Case.step('Install DLB driver and check DLB device status')
    acce.dlb_install(True)
    acce.check_acce_device_status('dlb')

    # Step 5 - Unbind QAT PF 0 and open vm
    Case.step('Unbind QAT PF 0 and open vm')
    dlb_dev_id = acce.get_dlb_dev_id_list(0, 0)
    acce.unbind_device('dlb_0_0')
    vm_name = 'vm'

    # Step 6 - Open VM and install kernel header and kernel devel file
    Case.step('Open VM and install kernel header and kernel devel file')
    qemu.kill_vm(vm_name)
    qemu.register_vm(vm_name, file_name)
    # qemu.create_vm_from_template(vm_name, file_name)
    qemu.attach_acce_dev_to_vm(vm_name, [dlb_dev_id[0]])
    qemu.start_vm(vm_name)
    acce.kernel_header_devel_vm(qemu, vm_name)

    # Step 7 - Install rpm package and check QAT device in vm
    Case.step('Install rpm package and check QAT device in vm')
    acce.rpm_install_vm(qemu, vm_name)
    acce.check_device_in_vm(qemu, vm_name, 'dlb', 0)
    qemu.execute_vm_cmd(vm_name, 'abrt-auto-reporting enabled && abrt-cli rm /var/spool/abrt/*')

    # Step 8 - Install DLB driver and run ldb_traffic stress
    Case.step('Install DLB driver and run ldb_traffic stress')
    acce.dlb_install_vm(qemu, vm_name, True)
    _, out, err = qemu.execute_vm_cmd(vm_name, './ldb_traffic -n 1024', timeout=60, cwd=f'{DLB_DRIVER_PATH_L}libdlb/examples')
    acce.check_keyword(['Received 1024 events'], out, 'execute dlb stress fail')

    # Step 9 - check mce error and shutdown vm
    Case.step('check mce error and shutdown vm')
    rcode, out, err = qemu.execute_vm_cmd(vm_name, 'abrt-cli list | grep mce|wc -l', timeout=60)
    if int(out) != 0:
        logger.error(err)
        raise Exception(err)
    qemu.shutdown_vm(vm_name)

    # Step 10 - Clear grub config
    Case.step('Clear grub config')
    acce.modify_kernel_grub('intel_iommu=on,sm_off', False)




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
