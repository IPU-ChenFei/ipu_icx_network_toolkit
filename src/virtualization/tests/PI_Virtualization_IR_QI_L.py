"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509883448
 @Author:Liu, JianjunX
 @Prerequisite:
    1. SW Configuration
        1. QEMU is installed:
            yum -y install qemu-kvm virt-install virt-manager
        2. Tools
            kvm-unit-tests-master.zip
"""

from src.virtualization.lib.tkinit import *

CASE_DESC = [
    "The system checks Interrupt Remapping & Queued Invalidation"
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    Case.prepare("boot to os")
    boot_to(sut, sut.default_os)
    # BIOS
    set_bios_knobs_step(sut, *bios_knob('knob_setting_virtual_common_xmlcli'))


    Case.prepare('check preconditions')
    Case.precondition(FilePrecondition(sut, 'kvm_unit_tests', sut_tool('VT_KVM_UNIT_TESTS_L')))
    Case.check_preconditions()

    tool_name_zip = sut_tool('VT_KVM_UNIT_TESTS_L')
    tool_name_cd = f"{sut_tool('VT_TOOLS_L')}/kvm-unit-tests-master/"

    Case.prepare(f"yum install ")
    sut.execute_shell_cmd("yum -y install qemu-kvm virt-install virt-manager")

    Case.step(f"Download : {tool_name_zip}")
    sut.execute_shell_cmd(f"ls | grep -i {tool_name_zip}", cwd=sut_tool('VT_TOOLS_L'))
    sut.execute_shell_cmd(f'unzip -o {tool_name_zip}', timeout=60, cwd=sut_tool('VT_TOOLS_L'))

    Case.step(f"install {tool_name_zip} ./configure")
    sut.execute_shell_cmd('./configure', cwd=tool_name_cd)

    Case.step("make standalone")
    sut.execute_shell_cmd('make standalone', cwd=tool_name_cd)

    Case.step("./tests/intel_iommu")
    _, out, _ = sut.execute_shell_cmd("./tests/intel_iommu", cwd=tool_name_cd)
    # The successful code need to the last line of log has string "PASS intel_iommu "
    res = log_check.find_lines("PASS", out)
    result = log_check.find_keyword("intel_iommu ", res[-1])
    Case.expect(f"The successful code need to the last line of log has string {res[-1]}", result != 0)


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
