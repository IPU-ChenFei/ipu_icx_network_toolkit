"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509883685
 @Author: Liu, JianjunX
 @Prerequisite:
    1. HW Configuration
    2. SW Configuration
        1. Install Power CLI on local Windows host
            Install-Module VMware.PowerCLI -Force
        2. Create a windows VM
        2. Tools
        3. Files
        4. virtual machine
            win_vm_name = 'win2019h1-1'


"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    'Verify virtualization Linux OS is workable after reboot.'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    Case.prepare("boot to os")
    boot_to(sut, SUT_STATUS.S0.UEFI_SHELL)
    set_bios_knobs_step(sut, *bios_knob('knob_setting_virtual_common_xmlcli'))
    UefiShell.reset_to_os(sut)

    Case.wait_and_expect(f'OS for system back to os', 15 * 10 * 60, sut.check_system_in_os)
    Case.sleep(60)

    Case.prepare('check preconditions')
    Case.precondition(VirtualMachinePrecondition(sut, 'windows1', True))
    Case.check_preconditions()

    esxi = get_vmmanger(sut)

    Case.step("Start Virtual Machine:")
    esxi.start_vm(WINDOWS_VM_NAME)

    Case.step("Get the IP Address of Virtual Machine:")
    win_ip = esxi.get_vm_ip(WINDOWS_VM_NAME)
    Case.expect("get the vm ip successful ", True)
    Case.step("Use command to create AutoAdminLogon:")
    code, out, err = esxi.execute_vm_cmd(WINDOWS_VM_NAME, r"powershell;REG ADD "
                                                  r"HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\'Windows NT'\CurrentVersion"
                                                  r"\Winlogon /v AutoAdminLogon /t REG_SZ /d 1 /f")
    Case.expect("AutoAdminLogon successful", err == "")

    Case.step("Use command to export securityconfig.cfg")
    code, out, err = esxi.execute_vm_cmd(WINDOWS_VM_NAME, r"powershell -Command secedit /export /cfg C:\securityconfig.cfg")
    Case.expect("The task has completed successfully.", err == "")

    Case.step("Use the command to change the contents of the file:")
    cmd = r"(gc C:\\securityconfig.cfg) -Replace 'PasswordComplexity = 1','PasswordComplexity = 0' > " \
          r"C:\\securityconfigupdate.cfg "
    cmd = 'C:\\WINDOWS\\system32\\WindowsPowerShell\\v1.0\\powershell.exe "& {' + cmd + ' }"'
    code, out, err = esxi.execute_vm_cmd(WINDOWS_VM_NAME, cmd)
    Case.expect("change the contents of the file is successful ! ", err == "")

    Case.step("Use the command to update securitypolicy:")
    code, out, err = esxi.execute_vm_cmd(WINDOWS_VM_NAME, r"powershell -command secedit /configure /db "
                                                  r"C:\Windows\security\new.sdb /cfg C:\securityconfigupdate.cfg "
                                                  r"/areas SECURITYPOLICY")
    Case.expect("Get the Passthrough devices successful!", err == "")

    os.mkdir(os.path.join(LOG_PATH, 'result'))
    result = f"{os.path.join(LOG_PATH, 'result')}\scerv.log"
    esxi.download_from_vm(WINDOWS_VM_NAME, host_path=result,
                          vm_path=r"C:\WINDOWS\security\logs\scesrv.log")
    with open(result, "r") as f:
        res = f.read().replace("\x00", '')
    result = log_check.find_keyword("error", res)
    Case.expect("The task has completed successfully.", result == "")

    for index in range(1, 6):
        Case.step(f"restart vm cycle [{index}]")
        Case.step('Restart the Virtual Machine:')
        esxi.reboot_vm(WINDOWS_VM_NAME)
        Case.sleep(60 * 2)
        Case.step("Get the IP Address of Virtual Machine:")
        win_ip = esxi.get_vm_ip(WINDOWS_VM_NAME)
        Case.expect("get the vm ip successful ", win_ip != "")


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
