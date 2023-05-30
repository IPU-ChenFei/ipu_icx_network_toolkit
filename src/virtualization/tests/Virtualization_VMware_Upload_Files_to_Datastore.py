"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/15010211464
 @Author:QiBo
 @Prerequisite:
    1. HW Configuration
    2. SW Configuration
        Install Power CLI on local Windows host
        Install-Module VMware.PowerCLI -Force
        1. SUT Python package
            1. Updated pip
            2. Paramiko
        2. Tools
        3. Files
            test.iso

"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    "This case purpose to upload files to datastore. e.g. the ISO of Centos"
]


def test_steps(sut, my_os):
    # type:(SUT, GenericOS) -> None

    Case.prepare('boot to uefi shell')
    boot_to(sut, SUT_STATUS.S0.UEFI_SHELL)
    set_bios_knobs_step(sut, *bios_knob('knob_setting_virtual_common_xmlcli'))
    UefiShell.reset_to_os(sut)
    Case.wait_and_expect(f'OS for system back to the os', 15 * 10 * 60, sut.check_system_in_os)
    Case.sleep(60)

    server_ip = sut.supported_os[sut.default_os].ip

    Case.step('Upload the file')
    esxi = get_vmmanger(sut)
    datastore_name = "datastore1"
    sut.execute_host_cmd(r"echo 0 > c:\test.iso", powershell=True)
    ret, res, err = esxi.execute_host_cmd_esxi(f'\"New-PSDrive -Location (Get-Datastore {datastore_name})'
                                               f' -Name isostore -PSProvider VimDatastore -Root \\ \";'
                                               f' -Name isostore -PSProvider -Confirm:$false VimDatastore -Root \\ \";'
                                               r'"Copy-DatastoreItem -Item c:\test.iso -Destination isostore:"')
    Case.expect("copy pass", ret == 0)
    vm_ip = log_check.find_keyword(server_ip, res)
    Case.expect(f"upload {res} pass", vm_ip)
    
    Case.step("Check the file")
    childitem_path = r"vmstore:\ha-datacenter\datastore1\test.iso"
    ret, res, err = esxi.execute_host_cmd_esxi(f"Get-ChildItem -Path {childitem_path} | Format-List")
    res1 = log_check.find_keyword('test.iso', res)
    Case.expect(f"check {res1} iso pass", res1)


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
