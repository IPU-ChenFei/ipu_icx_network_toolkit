from src.power_management.lib.tkinit import *

CASE_DESC = [
    'The objective of this test case is used to WAKE ON LAN(S5)',
    # list the name of those cases which are expected to be executed before this case
]


def test_steps(sut, my_os):

    Case.prepare('boot to OS')
    boot_to(sut, sut.default_os)

    Case.step('CHANGE BIOS KNOBS --> Enable WakeOnLanS5 and WakeOnLanSupport knobs')
    itp = PythonsvSemiStructured(sut.socket_name, globals(), locals())
    itp.execute('unlock()')
    itp.execute("knobs = 'WakeOnLanSupport=0x1,WakeOnLanS5=0x1'")
    itp.execute("import pysvtools.xmlcli.XmlCli as cli")
    itp.execute("cli.clb.AuthenticateXmlCliApis = True")
    ret = itp.execute("cli.CvProgKnobs(knobs)")
    Case.expect('CHANGE BIOS KNOBS successful', 'Verify Passed' in ret)

    Case.step('Power Cycle the platform and Boot back to OS')
    my_os.g3_cycle_step(sut, gracefully=False)

    waketoolpath = 'c:\\'
    ethmac = sut.execute_shell_cmd(f'ifconfig enp1s0 |grep ether')[1].split()[1].replace(':', '-')
    ethbroadcast = sut.execute_shell_cmd(f'ifconfig enp1s0 |grep broadcast')[1].split()[-1]

    for i in range(1, 3):
        Case.step(f"Turn on WOL in ethtool (LINIUX ONLY)-{i}")
        sut.execute_shell_cmd(f'ethtool --change enp1s0 wol g')
        ret = sut.execute_shell_cmd(f'ethtool enp1s0 | grep -i wake-on')[1]
        Case.expect('wake-on status is g', 'Wake-on: g' in ret)

        Case.step(f'Shut down the system-{i}')
        my_os.shutdown(sut)
        Case.sleep(10)

        Case.step(f'Wake up the system using WOL tool from HOST-{i}')
        sut.execute_host_cmd(f'WakeMeOnLan.exe /wakeup {ethmac} 30000 {ethbroadcast}', cwd=waketoolpath)
        Case.wait_and_expect('system back to OS', 600, sut.check_system_in_os)

        Case.step(f'Check Punit MC status-{i}')
        check_punit_mc_status(sut, itp)

    Case.step("exit itp link")
    itp.exit()


def clean_up(sut):
    # TODO: restore bios setting or other step to eliminate impact on the next case regardless case pass or fail
    # sut.set_bios_knobs(*bios_knob('disable_wol_s5_xmlcli'))

    # TODO: replace default cleanup.to_S5 if necessary when case execution fail
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
