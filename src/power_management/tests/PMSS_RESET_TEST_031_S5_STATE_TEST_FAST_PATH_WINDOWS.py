from src.power_management.lib.tkinit import *

CASE_DESC = [
    " PMSS_RESET_TEST_031 - S5 STATE TEST - FAST PATH - WINDOWS "
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    # Step1
    Case.prepare('boot to OS & launch itp')
    boot_to(sut, sut.default_os)
    itp = PythonsvSemiStructured(sut.socket_name, globals(), locals())
    itp.execute("unlock()")

    # Step2
    Case.step('CHANGE BIOS KNOBS')
    itp.execute("knobs = 'AttemptFastBoot=0x1,AttemptFastBootCold=0x1'")
    itp.execute("import pysvtools.xmlcli.XmlCli as cli")
    itp.execute("cli.clb.AuthenticateXmlCliApis = True")
    ret = itp.execute("cli.CvProgKnobs(knobs)")
    Case.expect('CHANGE BIOS KNOBS successful', 'Verify Passed' in ret)

    Case.step("Power Cycle the platform and Boot back to OS (Windows)")
    my_os.g3_cycle_step(sut, gracefully=False)

    write_reg_value = '0x0000cafe'

    for i in range(0, 2):
        Case.step(f"Write to sticky and non sticky registers - {i+1}")
        itp.execute(f"{pysv_reg('biosscratchpad6_cfg')} = {write_reg_value}")
        itp.execute(f"{pysv_reg('biosnonstickyscratchpad6_cfg')} = {write_reg_value}")
        Case.sleep(5)

        Case.step(f"ShutDown OS and Check State - {i+1}")
        cmd = 'shutdown -s -t 10 '
        sut.execute_shell_cmd(cmd, timeout=120, powershell=True)
        # itp.execute("sv.socket0.io0.uncore.s3m.uarch.s3m_acpi_pm.evt_sts.show()")
        Case.expect('system status is S5', sut.wait_for_power_status(SUT_STATUS.S5, 60))

        Case.step(f"Boot back to OS (Windows)- {i+1}")
        itp.execute("itp.pulsehook(0,1,True,25000000)")
        Case.wait_and_expect('system back to OS', 10*60, sut.check_system_in_os)

        Case.step(f"Check the BIOS log for subBootMode = ColdBootFast-{i+1}")
        bios_log_path = sut.get_bios_log()
        knob_line_in_bios_log = find_lines('subBootMode = ColdBootFast', bios_log_path)[-1]
        Case.expect('knob in bios log is as expect', knob_line_in_bios_log == 'subBootMode = ColdBootFast')

        Case.step(f"Check Sticky and non-sticky registers-{i+1}")
        itp.execute("sv.refresh()")
        ret1 = itp.execute(f"{pysv_reg('biosscratchpad6_cfg')}.show()")
        ret2 = itp.execute(f"{pysv_reg('biosnonstickyscratchpad6_cfg')}.show()")
        sticky_reg_ret = re.findall(r'0x\w+', ret1)
        non_sticky_reg_ret = re.findall(r'0x\w+', ret2)
        for reg_value in sticky_reg_ret:
            Case.expect('check sticky register right', reg_value != write_reg_value)
        for reg_value in non_sticky_reg_ret:
            Case.expect('check non-sticky register right', reg_value != write_reg_value)

        Case.step(f"Check Punit MC status-{i+1}")
        check_punit_mc_status(sut, itp)

    Case.step("exit itp link")
    itp.exit()


def clean_up(sut):
    if Result.returncode != 0:
        cleanup.to_s5(sut)


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
