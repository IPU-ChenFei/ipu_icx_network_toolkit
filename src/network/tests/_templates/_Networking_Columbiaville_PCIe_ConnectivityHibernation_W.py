
from src.network.lib import *

CASE_DESC = [
    """
    This case is used to check the networking connectivity after Hibernate SUT.
    Connect sut1 network port to sut2 network port cable.
    Copy PSTools to SUT
   """
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    sutos = ParameterParser.parse_parameter("sutos")
    conn = ParameterParser.parse_parameter("conn")
    valos = val_os(sutos)

    sut1 = sut
    sut2 = get_sut_list()[1]
    conn = nic_config(sut1, sut2, conn)

    Case.prepare("prepare steps")
    boot_to(sut1, sut1.default_os)
    Case.wait_and_expect('wait for restoring sut2 ssh connection', 60 * 5, sut2.check_system_in_os)

    Case.step("set ipv4")
    valos.ip_assign(conn)

    Case.step('Enable ACPI Sx State Control')
    set_bios_knobs_step(sut1, *bios_knob("enable_AcpiS3S4_xmlcli"))
    my_os.warm_reset_cycle_step(sut1)

    Case.step('set hypervisorlaunchtype')
    ret = sut1.execute_shell_cmd('bcdedit /set hypervisorlaunchtype off')[0]
    Case.expect('set successfully', ret == 0)
    my_os.warm_reset_cycle_step(sut1)

    Case.step('Run hibernate three times')
    for i in range(3):
        Case.step('Enable hibernate on SUT1')
        ret = sut1.execute_shell_cmd(f'powercfg.exe /hibernate on', 30, powershell=True)[0]
        Case.expect("Enable hibernate on SUT1 successfully", ret == 0)
        Case.step('Hibernate SUT1')
        sut1.execute_shell_cmd('psshutdown.exe -accepteula -h', 60, cwd=NW_WINDOWS_HEB_W)
        Case.sleep(60)
        sut1.ac_off()
        Case.sleep(10)
        sut1.ac_on()
        Case.wait_and_expect('wait for restoring sut1 ssh connection', 60 * 8, sut1.check_system_in_os)
        sut1.execute_shell_cmd(valos.ping.format(conn.port2.ip), timeout=30)


def clean_up(sut):
    from dtaf_core.lib.tklib.steps_lib import cleanup
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
