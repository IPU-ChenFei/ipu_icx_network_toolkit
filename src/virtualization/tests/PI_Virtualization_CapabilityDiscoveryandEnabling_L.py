"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509889311
 @Author:Liu, JianjunX
 @Prerequisite:
    1. SW Configuration
        1. QEMU is installed:

        2. Tools
            acpica-unix-20190509.tar.gz
            cpuid
            cpuid2
"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    "Capability Discovery and Enabling: \r\n"
    "CPU Virtualization: \r\n"
    "VT-x capability presence in CPUID  (CPUID.1:ECX.VMX[bit 5] = 1) of all the logical processors. \r\n"
    "IO Virtualization: \r\n"
    "Presence of ACPI DMAR table \r\n"
    "VT-d2 IOMMU hardware presence @ the addresses indicated in the ACPI DMAR table \r\n"
    "Dependency analysis: \r\n"
    "If x2APIC CPU capability is enabled in the BIOS Setup ,  VT-d2 with extended interrupt remap capability must be "
    "present and enabled. \r\n "
    "CPUID.(EAX=1):ECX.21 = 1) indicates x2APIC capability presence. \r\n"
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

    Case.prepare('check preconditions')
    Case.precondition(FilePrecondition(sut, 'acpica_unix.tar.gz', sut_tool('VT_ACPICA_UNIX_L')))
    Case.precondition(FilePrecondition(sut, 'cpuid', sut_tool('VT_CPUID_L')))
    Case.precondition(FilePrecondition(sut, 'cpuid2', sut_tool('VT_CPUID2_L')))
    Case.check_preconditions()

    tool_name_tar = sut_tool('VT_ACPICA_UNIX_L')

    tool_name = tool_name_tar.split("/")[-1].split(".tar.gz")[0]
    tool_name_acp = f"{sut_tool('VT_TOOLS_L')}/{tool_name}"

    _, out, _ = sut.execute_shell_cmd(r"grubby --info=ALL | grep -i kernel=\"")
    kernel_418 = log_check.find_lines("4.18", out)[0][8:-1]
    # BIOS

    set_bios_knobs_step(sut, *bios_knob('knob_setting_virtual_common_xmlcli'), *bios_knob('enable_X2apic_xmlcli'))

    Case.step("set 4.18kernel to test")
    _, out, _ = sut.execute_shell_cmd(r"grubby --default-kernel")
    kernel_512 = out.strip()
    res = log_check.find_keyword(kernel_418, out)
    if res == "":
        code, out, err = sut.execute_shell_cmd(f"grubby --set-default={kernel_418}")
        Case.expect('set default success', code == 0)
        my_os.warm_reset_cycle_step(sut)

    Case.step("x2APIC CPU capability is enabled in the BIOS Setup")
    _, out, _ = sut.execute_shell_cmd('journalctl | grep -i x2apic', timeout=60 * 3)
    res = find_lines("DMAR-IR: Enabled", out)
    Case.expect(res, len(res) != 0)
    find_lines("x2apic enabled", out)
    Case.expect(res, len(res) != 0)

    Case.step("CPUID.(EAX=1):ECX.21 = 1) indicates x2APIC capability presence.")
    sut.execute_shell_cmd("chmod +777 cpuid2 ", cwd=sut_tool('VT_TOOLS_L'))
    _, out, _ = sut.execute_shell_cmd("./cpuid2 1 0", cwd=sut_tool('VT_TOOLS_L'))
    # check the bit 21 of ECX should be 1
    res = log_check.find_lines("ECX: ", out)
    # ECX: 7ffefbff
    res = res[0].split(':')
    res = bin(int(res[-1].strip(), 16))[2:]
    result = res[-22]
    Case.expect(f"check the bit 21 of ECX should be 1 [{res[1]}]", int(result) == 1)

    Case.step("boot into OS and lauch command  ")
    _, out, _ = sut.execute_shell_cmd("virt-host-validate")
    # All configuration except Checking for secure guest support is pass
    res = log_check.find_lines("ERROR", out)
    Case.expect("All configuration except Checking for secure guest support is pass", len(res) == 0)

    Case.step(
        "Checking VT-x capability presence in  CPUID  (CPUID.1:ECX.VMX[bit 5] = 1) of all the logical processors.")
    sut.execute_shell_cmd("chmod +x cpuid", cwd=sut_tool('VT_TOOLS_L'))
    _, out1, _ = sut.execute_shell_cmd("cat /proc/cpuinfo | grep processor | wc -l",
                                       cwd=sut_tool('VT_TOOLS_L'))

    _, out2, _ = sut.execute_shell_cmd("./cpuid | egrep --color -iw  'vmx' | wc -l",
                                       cwd=sut_tool('VT_TOOLS_L'))
    Case.expect("two command output number is the same", out1 == out2)

    Case.step("build acpica")
    sut.execute_shell_cmd(f"tar -xzf {tool_name_tar}", cwd=sut_tool('VT_TOOLS_L'))
    sut.execute_shell_cmd("make clean && make ", timeout=60 * 2, cwd=tool_name_acp)

    Case.step("Check Presence of ACPI DMAR tablev")
    "cd /root/virtualization/tools/acpica-unix-20190509/generate/unix/bin"
    tool_name_bin = f"{tool_name_acp}/generate/unix/bin"
    sut.execute_shell_cmd("chmod +x acpidump ", cwd=tool_name_bin)
    sut.execute_shell_cmd("chmod +x acpixtract ", cwd=tool_name_bin)
    sut.execute_shell_cmd("chmod +x iasl ", cwd=tool_name_bin)

    sut.execute_shell_cmd("rm -rf ACPI_table.out", timeout=60 * 2, cwd=tool_name_bin)
    sut.execute_shell_cmd("./acpidump -o ACPI_table.out", timeout=60 * 2, cwd=tool_name_bin)
    sut.execute_shell_cmd("./acpixtract -a ACPI_table.out", cwd=tool_name_bin)
    sut.execute_shell_cmd("./iasl -d dmar.dat", cwd=tool_name_bin)

    _, out, _ = sut.execute_shell_cmd("cat dmar.dsl", cwd=tool_name_bin)
    res = find_lines("DMA Remapping table", out)
    Case.expect(f"the DMAR table: {res}", len(res) != 0)

    Case.step("VT-d2 IOMMU hardware presence @ the addresses indicated in the ACPI DMAR table")
    _, out, _ = sut.execute_shell_cmd("dmesg | grep -i DMAR | grep -i IOMMU")
    res = log_check.find_lines("DMAR: IOMMU enabled", out)
    Case.expect(f"result DMAR : {res}", len(res) != 0)
    log_check.find_lines("IOMMU", out)
    Case.expect(f"result DMAR : {res}", len(res) != 0)

    Case.step("restore set 5.12kernel to sut")
    code, out, err = sut.execute_shell_cmd(f"grubby --set-default={kernel_512}")
    Case.expect('set default success', code == 0)
    my_os.warm_reset_cycle_step(sut)


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
