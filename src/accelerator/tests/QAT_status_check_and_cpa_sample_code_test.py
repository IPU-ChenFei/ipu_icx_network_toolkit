import set_toolkit_src_root
from src.accelerator.lib import *

CASE_DESC = [
    'QAT Status Test',
    'Cpa_sample_code Test',
]


def check_qat_device(sut):
    acce = Accelerator(sut)
    cpu_num = acce.get_cpu_num()
    _, out, err = sut.execute_shell_cmd(f'lspci -vnd 8086:{acce.qat_id}|grep 8086:{acce.qat_id}', timeout=60)
    line_list = out.strip().split('\n')
    device_num = 0
    for line in line_list:
        if f'8086:{acce.qat_id}' in line:
            device_num += 1
    if device_num != cpu_num * acce.qat_device_num:
        logger.error('Not detect all device')
        raise Exception('Not detect all device')


def test_steps(sut, my_os):
    acce = Accelerator(sut)

    Case.prepare('disable VTD and boot to OS')
    logger.info('')
    boot_to(sut, sut.default_os)
    ifwi_ver = acce.get_ifwi_version()
    if ifwi_ver >= acce.IFWI_VERSION:
        set_bios_knobs_step(sut, *bios_knob('knob_setting_vtd_common_xmlcli'))
        check_bios_knobs_step(sut, *bios_knob('knob_setting_vtd_common_xmlcli'))
    else:
        set_bios_knobs_step(sut, *bios_knob('disable_vtd_xmlcli'))
        check_bios_knobs_step(sut, *bios_knob('disable_vtd_xmlcli'))
    sut.execute_shell_cmd('ln -s /usr/bin/python3 /usr/bin/python', timeout=60)
    acce.init_bashrc()

    # Step 1 - install QAT Driver
    Case.step('install QAT Driver')
    acce.kernel_header_devel()
    acce.rpm_install()
    acce.qat_uninstall()
    acce.qat_install(False)

    # Step 2 - Check QAT Status
    Case.step('Check QAT Status')
    acce.qat_service_restart()
    acce.check_qat_service_status()

    # Step 3 - Verify QAT device has been enumerated
    Case.step('Verify QAT device has been enumerated')
    check_qat_device(sut)

    # Step 4 - Check the service status after reboot
    Case.step('Check the service status after reboot')
    my_os.warm_reset_cycle_step(sut)
    time.sleep(60)
    acce.check_qat_service_status()

    # Step 5 - run and check sample code
    Case.step('run and check sample code')
    acce.run_qat_sample_code(' ')
    acce.run_qat_sample_code('signOfLife=1')
    acce.run_qat_sample_code('cySymLoops=50')
    acce.run_qat_sample_code('runTests=32')

    # Step 6 - Enable asym
    Case.step('Enable asym')
    acce.modify_qat_config_file('asym')
    acce.qat_service_restart()
    acce.qat_service_status()

    # Step 7 - run and check cpa sample code asymloops
    Case.step('run and check cpa sample code asymloops')
    acce.run_qat_sample_code('cyAsymLoops=50')




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
