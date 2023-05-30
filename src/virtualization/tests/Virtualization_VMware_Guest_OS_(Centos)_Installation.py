"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509884614
 @Author:QiBo
 @Prerequisite:
    1. HW Configuration
    2. SW Configuration
        1. SUT Python package
            1. Updated pip
            2. Paramiko
        2. Tools
        3. Files
"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    "Verify the installation and running the set of supported guest operating systems in virtual machines"
    "Need to upload the Centos ISO to Datastore"
]


def test_steps(sut, my_os):
    # type:(SUT, GenericOS) -> None

    Case.prepare('boot to OS')
    boot_to(sut,sut.default_os)
    # boot_to(sut, SUT_STATUS.S0.UEFI_SHELL)
    # set_bios_knobs_step(sut, *bios_knob('knob_setting_virtual_common_xmlcli'))
    # UefiShell.reset_to_os(sut)
    # Case.wait_and_expect(f'OS for system back to os', 15 * 10 * 60, sut.check_system_in_os)
    Case.sleep(60)

    Case.step("Create a new virtual machine:")
    esxi = get_vmmanger(sut)
    code, out, err = esxi.create_vm_from_template(RHEL_VM_NAME3, sut_tool("VT_RHEL_TEMPLATE_H"))
    Case.expect("create vm success", err == "")
    esxi.undefine_vm(vm_name)


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
        # clean_up(sut)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)
