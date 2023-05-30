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

    # Prepare steps - call predefined steps
    Case.prepare('Enable VT-d in BIOS and install rpm package')
    logger.info('')
    logger.info('---- Test Boot to Default os ----')
    boot_to(sut, sut.default_os)
    ker_ver = acce.kernel_version()
    if ker_ver <= acce.CENTOS_INTEL_NEXT_KERNEL:
        set_bios_knobs_step(sut, *bios_knob('knob_setting_tdx_common_xmlcli'))
        check_bios_knobs_step(sut, *bios_knob('knob_setting_tdx_common_xmlcli'))
    else:
        set_bios_knobs_step(sut, *bios_knob('knob_setting_tdx15_common_xmlcli'))
        check_bios_knobs_step(sut, *bios_knob('knob_setting_tdx15_common_xmlcli'))
    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('knob_setting_dsa_sriov_common_xmlcli'))
    sut.execute_shell_cmd('ln -s /usr/bin/python3 /usr/bin/python', timeout=60)
    sut.execute_shell_cmd('dmesg -C')
    acce.init_bashrc()
    acce.kernel_header_devel()
    acce.rpm_install()

    # Step 1 - Install TDX driver
    Case.step('Install TDX driver')
    acce.tdx_install()

    # Step 2 - Modify Grub file add SIOV function
    Case.step('Modify Grub file add SIOV function')
    acce.modify_kernel_grub('intel_iommu=on,sm_on', True)

    # Step 3 - Check DSA device
    Case.step('Check DSA device')
    acce.check_acce_device_status('dsa')
    _, out, err = sut.execute_shell_cmd('lsmod | grep idxd', timeout=60)
    acce.check_keyword(['idxd_mdev', 'idxd', 'vfio_pci', 'irqbypass'], out, 'DSA driver check fail')
    _, out, err = sut.execute_shell_cmd('dmesg | grep idxd', timeout=60)
    cpu_num = acce.get_cpu_num()
    line_list = out.strip().split('\n')
    dsa_device_num = 0
    for line in line_list:
        if 'Intel(R) Accelerator Device (v100)' in line:
            dsa_device_num += 1
    if dsa_device_num != cpu_num*acce.dsa_device_num*2:
        logger.error('Not all idxd device detected')
        raise Exception('Not all idxd device detected')

    # Step 4 - Accel-config install and accel-config test
    Case.step('Accel-config install and accel-config test')
    acce.accel_config_install()
    _, out, err = sut.execute_shell_cmd('accel-config test', timeout=60, cwd='/usr/share/accel-config/test/configs')
    acce.check_keyword(['SUCCESS'], out, 'Accel-config test fail')

    # Step 5 - Uninstall seam module
    Case.step('Uninstall seam module')
    ker_ver = acce.kernel_version()
    if ker_ver > acce.CENTOS_INTEL_NEXT_KERNEL:
        sut.execute_shell_cmd(f'ls {TDX_SEAM_RPMS_PATH_L} > /root/tdx_seam_module.txt')
        _, out, err = sut.execute_shell_cmd('cat /root/tdx_seam_module.txt')
        seam_module_list = out.strip().split('.rpm')
        for seam_module in seam_module_list:
            sut.execute_shell_cmd(f'rpm -e {seam_module}')

    # Step 6 - delete grub environment
    Case.step('delete grub environment')
    acce.modify_kernel_grub('tdx_host=on intel_iommu=on,sm_on', True)




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
    # sut = get_default_sut()
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
