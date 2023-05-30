# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.accelerator.lib import *

CASE_DESC = [
    'clear abort log and check QAT device status',
    'Run cpa_sample_code',
    'Modify QAT asym file',
    'Run QAT cpa_sample_code with StressApptest workloads'
]


def test_steps(sut, my_os):
    acce = Accelerator(sut)
    qemu = RichHypervisor(sut)

    Case.prepare('boot to OS and enable VT-d  in BIOS')
    logger.info('')
    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('knob_setting_sriov_common_xmlcli'))
    sut.execute_shell_cmd('ln -s /usr/bin/python3 /usr/bin/python', timeout=60)
    acce.init_bashrc()
    acce.rpm_install()
    acce.kernel_header_devel()

    # Step 1 - clear abort log and check dlb device status
    Case.step('clear abort log and check dlb device status')
    acce.modify_kernel_grub("intel_iommu=on,sm_off", True)
    sut.execute_shell_cmd('abrt-auto-reporting enabled', timeout=60)
    sut.execute_shell_cmd('abrt-cli rm /var/spool/abrt/*', timeout=60)

    # Step 2 - Install DLB driver and check DLB device status
    Case.step('Install DLB driver and check DLB device status')
    acce.dlb_install(True)
    acce.check_acce_device_status('dlb')

    # Step 3 - Creation of VF
    Case.step('Unbind dlb PF 0 and open vm')
    dlb_dev_id = acce.get_dlb_dev_id_list(0, 1)
    sut.execute_shell_cmd(f'echo 1 > /sys/class/dlb2/dlb0/device/sriov_numvfs')
    acce.unbind_device(f'dlb_0_1')
    vm_name = 'vm'

    # Step 4 - copy vm file and OVMF file to SUT
    Case.step('copy vm file and OVMF file to SUT')
    sut.upload_to_remote(localpath=OVMF_H, remotepath=OVMF_PATH_L)
    file_name = f'{IMAGE_PATH_L}{IMAGE_NAME}'

    # Step 5 - Install sut environments
    Case.step('Install sut environments')
    sut.execute_shell_cmd('python -m pip install --upgrade pip --proxy=http://child-prc.intel.com:913', timeout=120)
    sut.execute_shell_cmd('python -m pip install --upgrade paramiko --proxy=http://child-prc.intel.com:913', timeout=180)
    sut.execute_shell_cmd(f'mkdir {SRC_SCRIPT_PATH_L}')
    sut.execute_shell_cmd(f'rm -rf {SRC_SCRIPT_PATH_L}*')
    sut.upload_to_remote(localpath=SRC_SCRIPT_H, remotepath=SRC_SCRIPT_PATH_L)
    sut.execute_shell_cmd('unzip *', timeout=5 * 60, cwd=f'{SRC_SCRIPT_PATH_L}')

    # Step 6 - Open VM and Install and clear abort log
    Case.step('Open VM and Install and clear abort log ')
    qemu.create_vm_from_template(vm_name, file_name)
    qemu.attach_acce_dev_to_vm(vm_name, [dlb_dev_id[0]])
    qemu.start_vm(vm_name)
    
    # Step 7 - Install rpm package and kernel files
    acce.kernel_header_devel_vm(qemu, vm_name)
    acce.rpm_install_vm(qemu, vm_name)
    qemu.execute_vm_cmd(vm_name, 'abrt-auto-reporting enabled && abrt-cli rm /var/spool/abrt/*')
    
    # Step 8 - Check QAT and DLB device in vm
    Case.step('Check qat and dlb device in vm')
    acce.check_device_in_vm(qemu, vm_name, 'dlb', 1)

    # Step 7 - run qat sanmple code stress
    Case.step('run qat sanmple code stress')
    acce.dlb_install_vm(qemu, vm_name, True)
    _, out, err = qemu.execute_vm_cmd(vm_name, './ldb_traffic -n 1024', timeout=60,
                                      cwd=f'{DLB_DRIVER_PATH_L}libdlb/examples')
    acce.check_keyword(['Received 1024 events'], out, 'execute dlb stress fail')

    # Step 8 - check mce error and shutdown vm
    Case.step('check mce error and shutdown vm')
    rcode, out, err = qemu.execute_vm_cmd(vm_name, 'abrt-cli list | grep mce|wc -l', timeout=60)
    if int(out) != 0:
        logger.error(err)
        raise Exception(err)
    qemu.shutdown_vm(vm_name)
    qemu.undefine_vm(vm_name, True)

    

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
