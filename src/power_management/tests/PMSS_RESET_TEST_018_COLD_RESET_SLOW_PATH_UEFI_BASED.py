from src.power_management.lib.tkinit import *

CASE_DESC = [
    'The objective of this test case is used to COLD RESET SLOW PATH - UEFI BASED',
    # list the name of those cases which are expected to be executed before this case
]


def test_steps(sut, my_os):
    Case.prepare('boot to UEFI')
    boot_to(sut, SUT_STATUS.S0.UEFI_SHELL)

    Case.step('CHANGE BIOS KNOBS --> Disable AttemptFastBoot and AttemptFastBootCold')
    itp = PythonsvSemiStructured(sut.socket_name, globals(), locals())
    itp.execute('unlock()')
    itp.execute("knobs = 'AttemptFastBoot=0x0,AttemptFastBootCold=0x0'")
    itp.execute("import pysvtools.xmlcli.XmlCli as cli")
    itp.execute("cli.clb.AuthenticateXmlCliApis = True")
    ret = itp.execute("cli.CvProgKnobs(knobs)")
    Case.expect('CHANGE BIOS KNOBS successful', 'Verify Passed' in ret)

    Case.step('Power cycle the platform and Boot back to UEFI')
    UefiShell.g3_cycle_step(sut)

    write_reg_value = '0x0000cafe'

    for i in range(1, 3):
        Case.step(f'Write to sticky and non sticky registers through ITP-{i}')
        itp.execute(f"{pysv_reg('biosscratchpad6_cfg')} = {write_reg_value}")
        itp.execute(f"{pysv_reg('biosnonstickyscratchpad6_cfg')} = {write_reg_value}")
        Case.sleep(5)

        Case.step(f"Issue Reboot via UEFI and Wait for system to boot back to UEFI-{i}")
        UefiShell.cold_reset_cycle_step(sut)

        Case.step(f'Check the BIOS log for subBootMode-{i}')
        bios_log_path = sut.get_bios_log()
        knob_line_in_bios_log = find_lines('subBootMode = ColdBoot', bios_log_path)[-1]
        Case.expect('subBootMode = ColdBoot', knob_line_in_bios_log == 'subBootMode = ColdBoot')

        Case.step(f'Check Punit MC status-{i}')
        check_punit_mc_status(sut, itp)

        Case.step(f'Check Sticky and non-sticky registers-{i}')
        ret1 = itp.execute(f"{pysv_reg('biosscratchpad6_cfg')}.show()")
        ret2 = itp.execute(f"{pysv_reg('biosnonstickyscratchpad6_cfg')}.show()")
        sticky_reg_ret = re.findall(r'0x\w+', ret1)
        non_sticky_reg_ret = re.findall(r'0x\w+', ret2)
        for reg_value in sticky_reg_ret:
            Case.expect('check sticky register right', reg_value != write_reg_value)
        for reg_value in non_sticky_reg_ret:
            Case.expect('check non-sticky register right', reg_value != write_reg_value)

    Case.step("exit itp link")
    itp.exit()


def clean_up(sut):
    cleanup.default_cleanup(sut)


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
