from src.virtualization.lib.tkinit import *

CASE_DESC = [
    'The system checks Posted Interrupts in KVM'
]


def find_lines(keyword, data, index=-1, insensitive=True):
    """
    similar with find_keyword(), the only difference is that return lines including keyword

    :param keyword: string obj
    :param data: string
    :param index: index of matched items
    :param insensitive: ignore case, by default it is True
    :return: str, tuple
    :raise: no exceptions there
    """
    flags = re.I if insensitive else 0

    r = []

    for line in data.splitlines():
        match = re.findall(keyword, line, flags=flags)
        if match:
            r.append(line)

    if index == -1:
        return r
    elif index not in range(1, len(r) + 1):
        return ''
    else:
        return r[index - 1]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    Case.prepare("boot to os")
    boot_to(sut, sut.default_os)

    Case.prepare("set vtd vmx bios")
    set_bios_knobs_step(sut, *bios_knob('knob_setting_virtual_common_xmlcli'))

    Case.prepare('check preconditions')
    Case.precondition(FilePrecondition(sut, 'kvm_unit_tests', sut_tool('VT_KVM_UNIT_TESTS_L')))
    Case.check_preconditions()

    Case.step("install kvm-unit-tests-master")
    err = sut.execute_shell_cmd(f"unzip -o {sut_tool('VT_KVM_UNIT_TESTS_L')}", cwd=sut_tool("VT_TOOLS_L"))[2]
    Case.expect("unzip kvm-master pass", err == '')
    ret = sut.execute_shell_cmd("./configure", cwd=sut_tool("VT_KVM_UNIT_TESTS_UNZIP_L"))[0]
    Case.expect("configure successfully", ret == 0)
    ret = sut.execute_shell_cmd("make standalone", cwd=sut_tool("VT_KVM_UNIT_TESTS_UNZIP_L"))[0]
    Case.expect("make standalone successfully", ret == 0)

    Case.step("run test vmx")
    out = sut.execute_shell_cmd("./tests/vmx", 60 * 2, cwd=sut_tool("VT_KVM_UNIT_TESTS_UNZIP_L"))[1]
    res = find_lines("Virtualize interrupt-delivery", out)
    Case.expect("show the result", res)
    count = 0
    for out1 in res:
        if out1[:4] == 'PASS':
            count = count + 1
        else:
            Case.expect(out1, False)
    Case.expect(f"All result is PASS {out1} : ", len(res) == count)


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
