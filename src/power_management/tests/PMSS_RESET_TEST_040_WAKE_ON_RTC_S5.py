from src.power_management.lib.tkinit import *

CASE_DESC = [
    "to verify the platform stability with WAKE ON RTC (S5) Test - to wake up system from S5 using RTC."
]


def test_steps(sut, my_os):

    Case.prepare('boot to OS & launch itp')
    boot_to(sut, sut.default_os)
    itp = PythonsvSemiStructured(sut.socket_name, globals(), locals())
    itp.execute('unlock()')

    for i in range(1, 3):
        Case.step(f'Execute command in OS -{i}')
        ret = sut.execute_shell_cmd("timedatectl | grep -i rtc")[1]
        timedate = re.findall('[\d]+:[\d]+:[\d]+', ret)[0].split(':')
        wakeh = int(timedate[0])
        wakem = int(timedate[1]) + 15
        if wakem >= 60:
            wakem = wakem - 60
            wakeh = wakeh + 1
        if wakeh >= 24:
            wakeh = wakeh - 24
        wakehour = hex(wakeh)
        wakeminute = hex(wakem)

        Case.step(f"Enable and set wake on time -{i}")
        itp.execute(f"knobs = 'WakeOnRTCS4S5=0x1,RTCWakeupTimeHour={wakehour},RTCWakeupTimeMinute={wakeminute},RTCWakeupTimeSecond=0x0'")
        itp.execute("import pysvtools.xmlcli.XmlCli as cli")
        itp.execute("cli.clb.AuthenticateXmlCliApis = True")
        ret = itp.execute("cli.CvProgKnobs(knobs)")
        Case.expect('successful', 'Verify Passed' in ret)

        Case.step(f'Power cycle the platform and Boot back to OS -{i}')
        my_os.g3_cycle_step(sut, gracefully=False)
        # itp.execute("sv.sockets.io0.uncore.s3m.main_acpi.ibl_acpi1.pm1_en_sts.rtc_en")
        # itp.execute("sv.sockets.io0.uncore.s3m.main_acpi.ibl_acpi1.pm1_cnt.sci_en=0x1")
        # itp.execute("sv.sockets.io0.uncore.s3m.main_acpi.ibl_acpi1.pm1_cnt.sci_en")
        
        Case.step(f'Trigger graceful shutdown from OS -{i}')
        my_os.shutdown(sut)
        Case.wait_and_expect('system wake up to OS', 1200, sut.check_system_in_os)

        Case.step(f'Check Punit MC status-{i}')
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

