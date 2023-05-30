"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509883889
 @Author:
 @Prerequisite:
    1. HW Configuration
    2. SW Configuration
        1. SUT Python package
            1. Updated pip
            2. Paramiko
        2. Tools
            msr-tools-1.3.zip
"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    "PI_Virtualization_VT-X_Enabling_L"
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


def binary_convert(binary, bit):
    res = bin(int(binary, 16))[2:]
    result = res[-(bit + 1)]
    return res, int(result)


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    method = ParameterParser.parse_parameter("method")
    Case.prepare("boot to os")
    boot_to(sut, sut.default_os)
    # BIOS
    if method == "enable":
        set_bios_knobs_step(sut,
                            *bios_knob('knob_setting_virtual_common_xmlcli'),
                            *bios_knob('enable_smx_xmlcli'),
                            *bios_knob('enable_txt_xmlcli'))
    elif method == "disable":
        set_bios_knobs_step(sut,
                            *bios_knob('knob_setting_virtual_common_xmlcli'),
                            *bios_knob('disable_smx_xmlcli'),
                            *bios_knob('disable_txt_xmlcli'))
    #

    Case.prepare('check preconditions')
    Case.precondition(FilePrecondition(sut, 'msr_tools.zip', sut_tool('VT_MSR_TOOLS_L')))
    Case.check_preconditions()

    tool_name_msr_zip = sut_tool("VT_MSR_TOOLS_L")
    tool_name_master = f"{sut_tool('VT_TOOLS_L')}/msr-tools-master/"

    Case.step("install MSR tool onto the DUT")
    if sut.is_simics:
        sut.upload_to_remote(localpath=os.path.join(sut_tool('SUT_TOOLS_WINDOWS_VIRTUALIZATION'), tool_name_msr_zip),
                             remotepath=sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION'))
    sut.execute_shell_cmd(f"ls | grep -i {tool_name_msr_zip}", cwd=sut_tool('VT_TOOLS_L'))
    sut.execute_shell_cmd(f'unzip -o {tool_name_msr_zip}', timeout=60, cwd=sut_tool('VT_TOOLS_L'))
    sut.execute_shell_cmd('make', cwd=tool_name_master)
    code, out, err = sut.execute_shell_cmd('modprobe msr', cwd=tool_name_master)
    Case.expect("the CLI exec successfully and returns a zero return code.", code == 0)

    Case.step("IA32_FEATURE_CONTROL MSR Lock bit 0 is set by BIOS")
    _, out, _ = sut.execute_shell_cmd('./rdmsr -x  0x3a', cwd=tool_name_master)
    res, result = binary_convert(out, 0)
    Case.expect(f"expetced to have bit 0 as 1 {out} (convert the result into Binary) {res} === {result}", result == 1)

    if method == "enable":
        Case.step("If TXT is enabled,  then IA32_FEATURE_CONTROL MSR bit 1 must be set by BIOS.")
        _, out, _ = sut.execute_shell_cmd("./rdmsr -x  0x3a", cwd=tool_name_master)
        res, result = binary_convert(out, 1)
        Case.expect(f"expetced to have bit 1 as 1 {res} === {result}", result == 1)

    elif method == "disable":
        Case.step("If TXT is disabled, then IA32_FEATURE_CONTROL MSR bit 2 must be set by BIOS.")
        _, out, _ = sut.execute_shell_cmd("./rdmsr -x  0x3a", cwd=tool_name_master)
        res, result = binary_convert(out, 2)
        Case.expect(f"expetced to have bit 2 as 1 {res} === {result}", result == 1)

    Case.step("If x2APIC CPU mode is enabled (IA32_APIC_BASE_MSR bit 10 = 1), check the out value's bit 10")
    _, out, _ = sut.execute_shell_cmd("./rdmsr -x 0x1B", cwd=tool_name_master)
    res, result = binary_convert(out, 10)
    Case.expect(f"expetced to have bit 10 as 1 {res} === {result}", result == 1)

    Case.step("VT-d2 with interrupt remapping must be enabled")
    _, out, _ = sut.execute_shell_cmd("journalctl | grep -i x2apic",timeout=60*3, cwd=tool_name_master)
    #
    res = find_lines("x2apic enabled", out)
    Case.expect(f"The successful code need to the last line of log has string {res}", result != 0)


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