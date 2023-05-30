import time
# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.accelerator.lib import *


CASE_DESC = [
    'clear the abort logs',
    'run cpa_sample_code',
    'cold reset while run cpa_sample_code'
    'check mce error if occur'
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

    # step 1 - clear the abort logs
    Case.step('clear the abort logs')
    acce.kernel_header_devel()
    acce.rpm_install()
    acce.qat_uninstall()
    acce.qat_install(False)
    sut.execute_shell_cmd('abrt-auto-reporting enabled', timeout=60)
    sut.execute_shell_cmd('abrt-cli rm /var/spool/abrt/*', timeout=60)

    # Step 2 - check QAT device status and run cpa_sample_code
    Case.step('check QAT device status and run cpa_sample_code')
    for i in range(2):
        if i < 2:
            acce.check_qat_service_status()
            acce.run_qat_sample_code('')
            sut.execute_shell_cmd_async('./cpa_sample_code', timeout=10*60, cwd=f'{QAT_DRIVER_PATH_L}/build/')
            time.sleep(20)
            my_os.cold_reset_cycle_step(sut)
            time.sleep(60)
            sut.execute_shell_cmd('rm -rf /root/abrt.log', timeout=60)
            sut.execute_shell_cmd('abrt-cli list | tee /root/abrt.log', timeout=60)
            sut.download_to_local(remotepath='/root/abrt.log', localpath=os.path.join(LOG_PATH, 'Logs'))
            _, out, err = sut.execute_shell_cmd('abrt-cli list | grep mce|wc -l', timeout=60)
            Case.expect('MCE not occurred', int(out) == 0)




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
