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
    Case.prepare('Enable VT-d in BIOS and install rpm package')
    logger.info('')
    logger.info('---- Test Boot to Default os ----')
    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('knob_setting_sriov_common_xmlcli'))
    sut.execute_shell_cmd('ln -s /usr/bin/python3 /usr/bin/python', timeout=60)
    acce.rpm_install()
    acce.kernel_header_devel()
    acce.init_bashrc()

    # Step 1 - copy vm file and OVMF file to SUT
    Case.step('copy vm file and OVMF file to SUT')
    # sut.execute_shell_cmd(f'wget {VM_PATH_L}', timeout=30 * 60, cwd='/home/')
    # sut.execute_shell_cmd('xz -d *.img.xz', timeout=10 * 60, cwd='/home/')
    # sut.execute_shell_cmd('cp centos_basic.qcow2 centos.qcow2', timeout=10 * 60, cwd='/home/')
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

    # Step 4 - Check QAT device status and install QAT driver
    Case.step('Check QAT device status and install QAT driver')
    acce.check_acce_device_status('qat')
    acce.qat_uninstall()
    acce.qat_install(False)
    acce.check_qat_service_status()

    # Step 5 - Install DLB driver and check DLB device status
    Case.step('Install DLB driver and check DLB device status')
    acce.dlb_uninstall()
    acce.dlb_install(True)
    acce.check_acce_device_status('dlb')
    cpu_num = acce.get_cpu_num()
    pf_num = cpu_num * acce.QAT_DEVICE_NUM

    # Step 6 - Unbind QAT PF 0
    Case.step('Unbind QAT PF 0')
    for pf in range(pf_num):
        acce.unbind_device(f'qat_{pf}_0')

    # Step 7 - Unbind dlb PF 0 and open vm
    Case.step('Unbind dlb PF 0 and open vm')
    for pf in range(pf_num):
        acce.unbind_device(f'dlb_{pf}_0')

    # Step 8 - get device list
    Case.step('get device list')
    dev_list = []
    for pf in range(pf_num):
        qat_dev_id = acce.get_dev_id('qat', pf, 0)
        print(qat_dev_id)
        dlb_dev_id = acce.get_dlb_dev_id_list(pf, 0)
        print(dlb_dev_id)
        dev_list.append(qat_dev_id)
        dev_list.append(dlb_dev_id[0])
    print(dev_list)

    # Step 9 - Create vm and attach device list to vm, open vm
    Case.step('Create vm and attach device list to vm, open vm')
    qemu.create_rich_vm(pf_num, file_name)
    qemu.attach_acce_dev_to_vm_grouply(dev_list, 2)
    qemu.start_rich_vm()

    # Step 10 - Install rpm package and kernel files
    Case.step('Install rpm package and kernel files')
    qemu.execute_rich_vm_cmd_parallel('abrt-auto-reporting enabled && abrt-cli rm /var/spool/abrt/*')
    acce.kernel_header_devel_rich_vm(qemu)
    acce.rpm_install_rich_vm(qemu)

    # Step 11 - Check QAT and DLB device in vm
    Case.step('Check qat and dlb device in vm')
    acce.check_device_in_rich_vm(qemu, 'qat', 0)
    acce.check_device_in_rich_vm(qemu, 'dlb', 0)

    # Step 12 - Install QAT driver and run qat sanmple code stress
    Case.step('Install QAT driver and run qat sanmple code stress')
    acce.qat_install_rich_vm(qemu, './configure')
    acce.run_qat_sample_code_rich_vm(qemu, 'signOfLife=1')

    # Step 13 - Install DLB driver and run ldb_traffic stress
    Case.step('Install DLB driver and run ldb_traffic stress')
    acce.dlb_install_rich_vm(qemu, True)
    exec_res = qemu.execute_rich_vm_cmd_parallel('./ldb_traffic -n 1024', timeout=60, cwd=f'{DLB_DRIVER_PATH_L}libdlb/examples')
    for vm in exec_res:
        out = exec_res[vm][1]
        acce.check_keyword(['Received 1024 events'], out, 'execute dlb stress fail')

    # Step 14 - check mce error and shutdown vm
    Case.step('check mce error and shutdown vm')
    exec_res = qemu.execute_rich_vm_cmd_parallel('abrt-cli list | grep mce|wc -l', timeout=60)
    for vm in exec_res:
        code = exec_res[vm][0]
        # out = exec_res[vm][1]
        err = exec_res[vm][2]
        if code != 0:
            logger.error(err)
            raise Exception(err)
    qemu.shutdown_rich_vm()
    qemu.undefine_rich_vm()

    # Step 16 - Clear grub config
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
