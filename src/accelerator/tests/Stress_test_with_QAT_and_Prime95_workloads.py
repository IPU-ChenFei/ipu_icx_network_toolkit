# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.accelerator.lib import *

CASE_DESC = [
    'clear abort log and check QAT device status',
    'Run cpa_sample_code',
    'Modify QAT asym file',
    'Run QAT cpa_sample_code with Prime95 stress'
]


def test_steps(sut, my_os):
    acce = Accelerator(sut)

    Case.prepare('boot to OS with vtd disable')
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

    # step 1 - clear abort log and check QAT device status
    Case.step('clear abort log and check QAT device status')
    acce.kernel_header_devel()
    acce.rpm_install()
    acce.qat_uninstall()
    acce.qat_install(False)
    sut.execute_shell_cmd('abrt-auto-reporting enabled', timeout=60)
    sut.execute_shell_cmd('abrt-cli rm /var/spool/abrt/*', timeout=60)
    acce.check_qat_service_status()

    # Step 2 - Run cpa_sample_code
    Case.step('Run cpa_sample_code')
    acce.run_qat_sample_code('')

    # Step 3 - Modify QAT asym file
    Case.step('Modify QAT asym file')
    acce.modify_qat_config_file('asym')
    acce.check_qat_service_status()

    # Step 4 - Run QAT cpa_sample_code with Prime95 stress
    Case.step('Run QAT cpa_sample_code with Prime95 stress')
    acce.run_qat_stress_async()
    acce.prime95_stress()

    # Step 12 - Save qat log
    Case.step('Save qat log')
    sut.download_to_local(remotepath='/root/qat_async.log', localpath=LOG_PATH)
    _, out, err = sut.execute_shell_cmd('cat /root/qat_async.log')
    acce.check_keyword(["Sample code completed successfully"], out, 'Run qat stress fail')

    # Step 12 - Check mce error
    Case.step('Check mce error')
    sut.execute_shell_cmd('rm -rf /root/abrt.log', timeout=60)
    sut.execute_shell_cmd('abrt-cli list | tee /root/abrt.log', timeout=60)
    sut.download_to_local(remotepath='/root/abrt.log', localpath=os.path.join(LOG_PATH, 'Logs'))
    _, out, err = sut.execute_shell_cmd('abrt-cli list | grep mce|wc -l', timeout=60)
    Case.expect('MCE not occurred', int(out) == 0)


    

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
