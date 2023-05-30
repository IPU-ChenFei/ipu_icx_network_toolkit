import time
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
    acce.rpm_install()
    acce.kernel_header_devel()
    acce.init_bashrc()

    # Step 1 - copy vm file and OVMF file to SUT
    Case.step('copy vm file and OVMF file to SUT')
    # sut.execute_shell_cmd(f'wget {VM_PATH_L}', timeout=30 * 60, cwd='/home/')
    # sut.execute_shell_cmd('xz -d *.img.xz', timeout=10 * 60, cwd='/home/')
    # sut.execute_shell_cmd('mv *.img.xz centos_basic.qcow2', timeout=10 * 60, cwd='/home/')
    sut.upload_to_remote(localpath=OVMF_H, remotepath=OVMF_PATH_L)
    file_name = f'{IMAGE_PATH_L}{IMAGE_NAME}'

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

    vm_name = 'vm'

    # Step 6 - Unbind QAT VF 1
    def choose_qat_device(num):
        Case.step('Unbind QAT VF 1')
        qat_dev_id = acce.get_dev_id('qat', 0, num)
        print(qat_dev_id)
        acce.unbind_device(f'qat_0_{num}')
        return qat_dev_id

    qat_dev_id = choose_qat_device(1)

    # Step 7 - Unbind QAT PF 0 and open vm
    def choose_dlb_device(num):
        Case.step('Unbind QAT PF 0 and open vm')
        dlb_dev_id = acce.get_dlb_dev_id_list(num, 1)
        sut.execute_shell_cmd('modprobe vfio')
        sut.execute_shell_cmd('modprobe vfio-pci')
        sut.execute_shell_cmd(f'echo 1 > /sys/class/dlb2/dlb{num}/device/sriov_numvfs')
        acce.unbind_device(f'dlb_{num}_1')
        return dlb_dev_id

    dlb_dev_id = choose_dlb_device(0)

    # Step 8 - get device list
    Case.step('get device list')
    dev_list = []
    dev_list.append(qat_dev_id)
    dev_list.append(dlb_dev_id[0])
    print(dev_list)

    # Step 9 - Open VM and install kernel header and kernel devel file
    Case.step('Open VM and install kernel header and kernel devel file')
    qemu.create_vm_from_template(vm_name, file_name)
    qemu.attach_acce_dev_to_vm(vm_name, dev_list)
    qemu.start_vm(vm_name)

    # Step 10 - Install rpm package and kernel packages
    Case.step('Install rpm package and kernel packages')
    qemu.execute_vm_cmd(vm_name, 'abrt-auto-reporting enabled && abrt-cli rm /var/spool/abrt/*')
    acce.kernel_header_devel_vm(qemu, vm_name)
    acce.rpm_install_vm(qemu, vm_name)

    # Step 11 - Check QAT and DLB device in vm
    Case.step('Check QAT and DLB device in vm')
    acce.check_device_in_vm(qemu, vm_name, 'qat', 1)
    acce.check_device_in_vm(qemu, vm_name, 'dlb', 1)

    # Step 12 - Install QAT driver and run qat sanmple code stress
    Case.step('Install QAT driver and run qat sanmple code stress')
    acce.qat_install_vm(qemu, vm_name, './configure --enable-icp-sriov=guest')
    acce.run_qat_sample_code_vm(qemu, vm_name, '')
    acce.run_qat_stress_vm_async(qemu, vm_name)

    # Step 13 - Install DLB driver and run ldb_traffic stress
    Case.step('Install DLB driver and run ldb_traffic stress')
    acce.dlb_install_vm(qemu, vm_name, True)
    _, out, err = qemu.execute_vm_cmd(vm_name, './ldb_traffic -n 1024', timeout=60,
                                      cwd=f'{DLB_DRIVER_PATH_L}libdlb/examples/')
    acce.check_keyword(['Received 1024 events'], out, 'execute dlb stress fail')
    # acce.dlb_stress_vm(qemu, vm_name)

    # Step 14 - Copy qat async log to SUT
    Case.step('Copy qat async log to SUT')
    time.sleep(200)
    _, out, err = qemu.execute_vm_cmd(vm_name, 'cat /root/qat_vm_async.log')
    acce.check_keyword(["Sample code completed successfully"], out, 'Run qat stress fail')
    vm_file_path = '/root/qat_vm_async.log'
    sut_file_path = '/root/qat_vm_async.log'
    qemu.download_from_vm(vm_name, sut_file_path, vm_file_path)

    # Step 15 - check mce error and shutdown vm
    Case.step('check mce error and shutdown vm')
    rcode, out, err = qemu.execute_vm_cmd(vm_name, 'abrt-cli list | grep mce|wc -l', timeout=60)
    if int(out) != 0:
        logger.error(err)
        raise Exception(err)
    qemu.shutdown_vm(vm_name)
    qemu.undefine_vm(vm_name, True)

    # Step 16 - Copy qat async log to host folder
    Case.step('Copy qat async log to host folder')
    sut.download_to_local(remotepath='/root/qat_vm_async.log', localpath=LOG_PATH)
    sut.execute_shell_cmd('rm -rf qat_async.log', timeout=60, cwd='/root/')

    # Step 17 - Clear grub config
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
