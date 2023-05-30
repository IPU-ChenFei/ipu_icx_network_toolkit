# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.accelerator.lib import *


CASE_DESC = [
    'check the system under extreme conditions',
    'monitors system resources such as Memory, processor, network',
    'checks the ability of the system to recover back to normal status',
    'checks whether the system displays appropriate error messages while under stress'
]


def test_steps(sut, my_os):
    sut.execute_shell_cmd('ln -s /usr/bin/python3 /usr/bin/python', timeout=60)
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
    acce.init_bashrc()

    # Step 1 - install QAT Driver
    Case.step('install QAT Driver')
    acce.kernel_header_devel()
    acce.rpm_install()
    acce.qat_uninstall()
    acce.qat_install(False)

    # Step 2 - Check QAT Status
    Case.step('Check QAT Status')
    acce.check_qat_service_status()

    # Step 3 - run and check sample code
    Case.step('run and check sample code')
    acce.run_qat_sample_code(' ')

    # Step 4 - Enable asym
    Case.step('Enable asym')
    acce.modify_qat_config_file('asym')
    acce.qat_service_restart()
    acce.qat_service_status()

    # Step 5 - Run QAT cpa_sample_code with parameters for 12 hrs
    Case.step('Run QAT cpa_sample_code with parameters for 12 hrs')
    acce.run_qat_stress_async()

    # Step 6 - Run StressApp for 12 hrs
    Case.step('Run StressApp for 12 hrs')
    acce.linpack_stress()

    # Step 11 - Save qat log
    Case.step('Save qat log')
    Case.sleep(5 * 60)
    sut.download_to_local(remotepath='/root/qat_async.log', localpath=LOG_PATH)
    _, out, err = sut.execute_shell_cmd('cat /root/qat_async.log')
    acce.check_keyword(["Sample code completed successfully"], out, 'Run qat stress fail')


    # Step 7 -  Check mce log
    Case.step('Check mce log')
    sut.execute_shell_cmd('rm -rf /root/abrt.log', timeout=60)
    sut.execute_shell_cmd('abrt-cli list | tee /root/abrt.log', timeout=60)
    sut.download_to_local(remotepath='/root/abrt.log', localpath=os.path.join(LOG_PATH, 'Logs'))
    _, out, _ = sut.execute_shell_cmd('abrt-cli list |grep mce |wc -l')
    acce.check_keyword('0', out, 'Issue - some hardware errors occurred')


    

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
