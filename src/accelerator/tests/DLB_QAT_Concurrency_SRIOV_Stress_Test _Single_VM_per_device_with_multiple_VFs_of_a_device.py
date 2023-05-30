# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.accelerator.lib import *
from src.accelerator.lib.rich_virtual_virsh import *


CASE_DESC = [
    'Check QAT device',
    'QAT driver install',
    'check cpa_sample_code file generate'
]


def test_steps(sut, my_os):
    acce = Accelerator(sut)
    kvm = Rich_KVM(sut)
    qat_all_vf_list = []
    cpu_num = acce.get_cpu_num()
    vf_per_device = 16
    vf_per_vm = 16
    qat_pf_num = cpu_num * acce.QAT_DEVICE_NUM
    dlb_pf_num = cpu_num * acce.DLB_DEVICE_NUM
    dlb_all_vf_list = []

    # Prepare steps - Enable VT-d in BIOS and install rpm package
    Case.prepare('boot to OS and enable VT-d  in BIOS')
    logger.info('')
    logger.info('---- Test Boot to Default os ----')
    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('knob_setting_sriov_common_xmlcli'))
    sut.execute_shell_cmd('ln -s /usr/bin/python3 /usr/bin/python', timeout=60)
    acce.rpm_install()
    acce.kernel_header_devel()
    acce.init_bashrc()

    # Step 1 - copy OVMF file to SUT
    Case.step('copy vm file and OVMF file to SUT')
    sut.upload_to_remote(localpath=OVMF_H, remotepath=OVMF_PATH_L)

    # Step 2 - Add SRIOV function to grub file and clear abort log
    Case.step('Add SRIOV function to grub file and clear abort log')
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
    acce.qat_install(True)
    acce.check_qat_service_status(True)

    # Step 5 - Install DLB driver and check DLB device status
    Case.step('Install DLB driver and check DLB device status')
    acce.dlb_uninstall()
    acce.dlb_install(True)
    acce.check_acce_device_status('dlb')

   #Step 6 - Unbind all QAT and DLB VF from host
    for pf in range(0, qat_pf_num):
        qat_vf_list = acce.get_qat_dev_id_list(pf, vf_per_device)
        acce.unbind_device(f'qat_{pf}_{vf_per_device}')
        qat_all_vf_list.extend(qat_vf_list)

    sut.execute_shell_cmd('modprobe vfio')
    sut.execute_shell_cmd('modprobe vfio-pci')
    for pf in range(dlb_pf_num):
        sut.execute_shell_cmd(f'echo {vf_per_device} > /sys/class/dlb2/dlb{pf}/device/sriov_numvfs')
    for pf in range(dlb_pf_num):
        acce.unbind_device(f'dlb_{pf}_{vf_per_device}')

    for pf in range(0, dlb_pf_num):
        dlb_vf_list = acce.get_dlb_dev_id_list(pf, vf_per_device)
        dlb_all_vf_list.extend(dlb_vf_list)

    # Step 7 - Create vms and attach devices to vm
    kvm.create_rich_vm(qat_pf_num)
    kvm.attach_acce_dev_to_vm_grouply(qat_all_vf_list, vf_per_vm)
    kvm.attach_acce_dev_to_vm_grouply(dlb_all_vf_list, vf_per_vm)
    kvm.start_rich_vm()

    # Step 8 - Check QAT and DLB device in vm
    Case.step('Check qat and dlb device in vm')
    kvm.check_device_in_rich_vm('qat', vf_per_vm)
    kvm.check_device_in_rich_vm('dlb', vf_per_vm)

    # Step 9 - Install rpm package and kernel files
    Case.step('Install rpm package and kernel files')
    kvm.kernel_header_devel_rich_vm()
    kvm.rpm_install_rich_vm()
    kvm.execute_rich_vm_cmd_parallel('abrt-auto-reporting enabled && abrt-cli rm /var/spool/abrt/*')

    # Step 10 - Install driver and run sample codes
    kvm.qat_install_rich_vm('./configure --enable-icp-sriov=guest')
    kvm.run_qat_sample_code_rich_vm('signOfLife=1')
    kvm.dlb_install_rich_vm(True)
    kvm.run_dlb_rich_vm()

    # Step 11 - run parallel QAT and DLB
    exec_res = kvm.execute_rich_vm_cmd_parallel(f'{QAT_DRIVER_PATH_L}/build//cpa_sample_code signOfLife=1 && ./ldb_traffic -n 100000000', timeout=60 * 10, cwd=f'{DLB_DRIVER_PATH_L}libdlb/examples')
    for vm in exec_res:
        out = exec_res[vm][1]
        key_list = ['Received 100000000 events', 'Sample code completed successfully']
        acce.check_keyword(key_list, out, 'Issue - Run qat stress fail')
    logger.info(f'run qat and dlb stress in every virtual machine successfully')

    # Step 12 - check mce error and shutdown vm
    Case.step('check mce error and shutdown vm')
    exec_res = kvm.execute_rich_vm_cmd_parallel('abrt-cli list | grep mce|wc -l', timeout=60)
    for vm in exec_res:
        code = exec_res[vm][0]
        # out = exec_res[vm][1]
        err = exec_res[vm][2]
        if code != 0:
            logger.error(err)
            raise Exception(err)
    kvm.shutdown_rich_vm()
    kvm.undefine_rich_vm()

    # Step 13 - Clear grub config
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
