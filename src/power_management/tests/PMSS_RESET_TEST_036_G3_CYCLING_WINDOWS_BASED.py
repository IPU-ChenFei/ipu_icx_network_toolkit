from src.power_management.lib.tkinit import *

CASE_DESC = [
    " PMSS_RESET_TEST_036 - G3 CYCLING - WINDOWS BASED "
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    # Step1
    Case.prepare('boot to OS & launch itp')
    boot_to(sut, sut.default_os)
    itp = PythonsvSemiStructured(sut.socket_name, globals(), locals())
    itp.execute("unlock()")

    itp.execute("knobs = 'AttemptFastBoot=0x0,AttemptFastBootCold=0x0'")
    itp.execute("import pysvtools.xmlcli.XmlCli as cli")
    itp.execute("cli.clb.AuthenticateXmlCliApis = True")
    ret = itp.execute("cli.CvProgKnobs(knobs)")
    Case.expect('change bios knob successful', 'Verify Passed' in ret)

    for i in range(0, 2):
        Case.step(f'G3 cycle the platform and Boot back to OS - {i + 1}')
        my_os.g3_cycle_step(sut)
        Case.wait_and_expect('system back to OS', 10*60, sut.check_system_in_os)

        Case.step(f'Check the BIOS log-{i + 1}')
        bios_log_path = sut.get_bios_log()
        knob_line_in_bios_log = find_lines('subBootMode = ColdBoot', bios_log_path)[-1]
        Case.expect('knob in bios log is as expect', knob_line_in_bios_log == 'subBootMode = ColdBoot')

        Case.step(f"Check Punit MC status-{i + 1}")
        check_punit_mc_status(sut, itp)

    Case.step("exit itp link")
    itp.exit()


def clean_up(sut):
    # if Result.returncode != 0:
    #     cleanup.to_s5(sut)
    pass


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
