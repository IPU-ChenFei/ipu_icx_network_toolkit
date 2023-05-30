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
    ifwi_ver = acce.get_ifwi_version()
    if ifwi_ver >= acce.IFWI_VERSION:
        set_bios_knobs_step(sut, *bios_knob('knob_setting_pcstates_common_d_xmlcli'))
        check_bios_knobs_step(sut, *bios_knob('knob_setting_pcstates_common_d_xmlcli'))
    else:
        set_bios_knobs_step(sut, *bios_knob('knob_setting_pcstates_common_xmlcli'))
        check_bios_knobs_step(sut, *bios_knob('knob_setting_pcstates_common_xmlcli'))
    sut.execute_shell_cmd('ln -s /usr/bin/python3 /usr/bin/python', timeout=60)
    acce.kernel_header_devel()
    acce.init_bashrc()
    acce.rpm_install()

    # Step 2 - Clear abort log
    def clear_abort_log():
        Case.step('Clear abort log')
        sut.execute_shell_cmd('abrt-auto-reporting enabled', timeout=60)
        sut.execute_shell_cmd('abrt-cli rm /var/spool/abrt/*', timeout=60)

    # Step 3 - check mce error
    def check_mce_error():
        Case.step('check mce error')
        rcode, out, err = sut.execute_shell_cmd('abrt-cli list | grep mce|wc -l', timeout=60)
        if int(out) != 0:
            logger.error(err)
            raise Exception(err)

    # Step 4 - Clear abort log
    Case.step('Clear abort log')
    clear_abort_log()
    acce.qat_uninstall()

    # Step 5 - Install socwatch and run socwatch
    Case.step('Install socwatch and run socwatch')
    acce.install_socwatch()
    acce.run_socwatch(1)

    # Step 6 - check mce error and clear abort log
    Case.step('check mce error and clear abort log')
    check_mce_error()
    clear_abort_log()

    # Step 7 - Check QAT device
    Case.step('Check QAT device')
    acce.check_acce_device_status('qat')

    # Step 8 - QAT driver install and run qat samplecode test
    Case.step('QAT driver install and run qat samplecode test')
    acce.qat_install(False)
    acce.run_qat_sample_code('')

    # Step 9 - run socwatch and check mce error
    Case.step('run socwatch and check mce error')
    acce.run_socwatch(2)
    check_mce_error()
    clear_abort_log()

    # Step 10 - run dlb ldb traffic test and corrupt test
    Case.step('run dlb ldb traffic test and corrupt test')
    try:
        sut.execute_shell_cmd('./cpa_sample_code > cap_sample_corrupt.log', timeout=10, cwd=f'{QAT_DRIVER_PATH_L}/build/')
    except Exception:
        pass
    sut.download_to_local(f'{QAT_DRIVER_PATH_L}/build/cap_sample_corrupt.log', os.path.join(LOG_PATH, 'logs'))
    rcode, out, err = sut.execute_shell_cmd(f'cat {QAT_DRIVER_PATH_L}/build/cap_sample_corrupt.log')
    acce.check_keyword(['icp_sal_userStartMultiProcess("SSL") started'], out, 'run qat cap_sample fail')


    # Step 11 - run socwatch and check mce error
    Case.step('run socwatch and check mce error')
    acce.run_socwatch(3)
    check_mce_error()



    

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
