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

    # Step 1 - Clear the abort logs
    Case.step('Clear the abort logs')
    sut.execute_shell_cmd('abrt-auto-reporting enabled && abrt-cli rm /var/spool/abrt/*')

    # Step 2 - install dlb
    Case.step('install dlb')
    acce.dlb_install(True)

    # Step 3 - Run ldb_traffic example on the PF
    Case.step('Run ldb_traffic example on the PF')
    dlb_tool_path = f'{DLB_DRIVER_PATH_L}/libdlb/examples'
    _, out, _ = sut.execute_shell_cmd('./ldb_traffic -n 1024', cwd=dlb_tool_path, timeout=180)
    acce.check_keyword('Received 1024 events', out, 'Issue - Traffic move through the PF with some errors.')

    # Step 4 - Run Prime95 for 12 hrs
    Case.step('Run Prime95 for 12 hrs')
    acce.run_prime95_stress_async()

    # Step 5 - Run DLB workload for 12 hrs
    Case.step('Run DLB workload for 12 hrs')
    acce.dlb_stress()

    # Step 6 - Save Prime95 log
    Case.step('Save Prime95 log')
    Case.sleep(5*60)
    sut.download_to_local(remotepath=f'{PRIME95_PATH_L}primeprime.log', localpath=LOG_PATH)
    sut.download_to_local(remotepath=f'{PRIME95_PATH_L}prime95.log', localpath=LOG_PATH)
    std, out, err = sut.execute_shell_cmd(f'cat {PRIME95_PATH_L}primeprime.log', timeout=60)
    if std != 0:
        logger.error(err)
        raise Exception(err)
    std, out, err = sut.execute_shell_cmd(f'cat {PRIME95_PATH_L}prime95.log', timeout=60)
    if std != 0:
        logger.error(err)
        raise Exception(err)

    # Step 7 -  Check mce log
    Case.step('Check mce log')
    sut.execute_shell_cmd('rm -rf /root/abrt.log', timeout=60)
    sut.execute_shell_cmd('abrt-cli list | tee /root/abrt.log', timeout=60)
    sut.download_to_local(remotepath='/root/abrt.log', localpath=os.path.join(LOG_PATH, 'Logs'))
    _, out, _ = sut.execute_shell_cmd('abrt-cli list |grep mce |wc -l')
    acce.check_keyword('0', out, 'Issue - some hardware errors occurred')

    # Step 8 - uninstall DLB driver
    Case.step('uninstall DLB driver')
    acce.dlb_uninstall()




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
