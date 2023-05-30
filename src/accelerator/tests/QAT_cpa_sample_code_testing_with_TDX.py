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
    sut.execute_shell_cmd('ln -s /usr/bin/python3 /usr/bin/python', timeout=60)
    acce.init_bashrc()
    acce.kernel_header_devel()
    acce.rpm_install()

    # Step 1 - Install TDX driver
    Case.step('Install TDX driver')
    acce.tdx_install()

    # Step 2 - Check QAT device
    Case.step('Enable QAT SIOV function and Check QAT device')
    acce.modify_kernel_grub('intel_iommu=on,sm_on', True)
    acce.check_acce_device_status('qat')

    # Step 3 - QAT driver install and run qat sample
    Case.step('QAT driver install and run qat sample')
    acce.qat_uninstall()
    acce.qat_install(True)

    # Step 4 - QAT driver install and run qat sample
    Case.step('Check QAT service status and ')
    acce.check_qat_service_status(is_vf=True)
    acce.run_qat_sample_code('')

    # Step 5 - Uninstall seam module
    Case.step('Uninstall seam module')
    ker_ver = acce.kernel_version()
    if ker_ver <= acce.CENTOS_INTEL_NEXT_KERNEL:
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
