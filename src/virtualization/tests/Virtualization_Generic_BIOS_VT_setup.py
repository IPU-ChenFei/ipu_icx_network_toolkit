from src.virtualization.lib.tkinit import *

CASE_DESC = [
    'This test case will guide the tester through configuring VT features in the setup menu (BIOS)'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    Case.prepare("set vtd vmx bios")
    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('knob_setting_virtual_common_xmlcli'))
    Case.wait_and_expect('wait for restoring sut ssh connection', 60 * 5, sut.check_system_in_os)


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
