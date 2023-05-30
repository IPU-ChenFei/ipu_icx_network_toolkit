from src.power_management.lib.tkinit import *

CASE_DESC = [
    "To verify the platform stability Run AC Power Cycle - VMWARE OS"
]


def test_steps(sut, my_os):
    Case.prepare('boot to OS & launch itp')
    boot_to(sut, sut.default_os)
    itp = PythonsvSemiStructured(sut.socket_name, globals(), locals())
    itp.execute('unlock()')
    itp.execute("knobs = 'AttemptFastBoot=0x0,AttemptFastBootCold=0x0'")
    itp.execute("import pysvtools.xmlcli.XmlCli as cli")
    itp.execute("cli.clb.AuthenticateXmlCliApis = True")
    ret = itp.execute("cli.CvProgKnobs(knobs)")
    Case.expect('change bios knob successful', 'Verify Passed' in ret)

    for i in range(1, 3):
        Case.step(f'G3 cycle the platform and Boot back to OS-{i}')
        my_os.g3_cycle_step(sut)

        Case.step(f'Check the BIOS log-{i}')
        bios_log_path = sut.get_bios_log()
        knob_line_in_bios_log = find_lines('subBootMode = ColdBoot', bios_log_path)[-1]
        Case.expect('knob in bios log is as expect', knob_line_in_bios_log == 'subBootMode = ColdBoot')

        Case.step(f'Check Punit MC status-{i}')
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
