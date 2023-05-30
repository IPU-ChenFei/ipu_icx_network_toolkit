"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509884624
 @Author:YanXu
 @Prerequisite:
    1. HW Configuration
    2. SW Configuration
        1. SUT Python package
        2. Tools
        3. Files
    3. Virtual Machine
        1. Create a windows VM
"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    "Test that the VMware Tools are installed properly on a Windows guest."
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    Case.prepare("boot to os")
    boot_to(sut, sut.default_os)
    Case.sleep(60)

    Case.prepare('check preconditions')
    Case.precondition(VirtualMachinePrecondition(sut, 'windows1'))
    Case.check_preconditions()

    esxi = get_vmmanger(sut)

    if not esxi.is_vm_running(WINDOWS_VM_NAME):
        esxi.start_vm(WINDOWS_VM_NAME)

    Case.step('Check the date of VM:')
    esxi.execute_vm_cmd(WINDOWS_VM_NAME, "echo %date%")

    Case.step('Check the date of the server:')
    sut.execute_shell_cmd('date')

    Case.step('Set a new time for server:')
    old_sut_date = sut.execute_shell_cmd('esxcli system time get')[1]
    old_sut_year = int(old_sut_date.split('-')[0])
    _, _, std_err = sut.execute_shell_cmd(f'esxcli system time set -y {old_sut_year + 1}')
    Case.expect('The time will be set successfully', std_err.strip() == "")

    Case.step('Check if the time of server has been changed:')
    _, date_result, _ = sut.execute_shell_cmd('date')
    new_sut_year = int(date_result.split()[-1])
    Case.expect('The SUT time has been changed', new_sut_year == old_sut_year + 1)

    Case.step('Check the status of VMware tool :')
    _, timesync_status, _ = esxi.execute_vm_cmd(WINDOWS_VM_NAME, "VMwareToolboxCmd.exe timesync status", cwd=r'"C:\Program Files\VMware\VMware Tools\"')
    if "Disable" in timesync_status:
        Case.step('Enable timesync funtion of VMware tool:')
        _, ena_status, _ = esxi.execute_vm_cmd(WINDOWS_VM_NAME, "VMwareToolboxCmd.exe timesync enable", cwd=r'"C:\Program Files\VMware\VMware Tools\"')
        Case.expect('Enable timesync funtion of VMware tool ,success', 'Enable' in ena_status)
        Case.sleep(60)
    Case.step('Check the date of VM:')
    res, new_vm_date, err = esxi.execute_vm_cmd(WINDOWS_VM_NAME, "echo %date%")
    new_vm_year = int(new_vm_date.split("/")[-1])
    Case.expect('VMware Tools are installed successfully', new_vm_year == new_sut_year)

    Case.step("restore")
    _, _, std_err = sut.execute_shell_cmd(f'esxcli system time set -y {old_sut_year}')

    esxi.execute_vm_cmd(WINDOWS_VM_NAME, "VMwareToolboxCmd.exe timesync disable", cwd=r'"C:\Program Files\VMware\VMware Tools\"')
    esxi.execute_vm_cmd(WINDOWS_VM_NAME, "VMwareToolboxCmd.exe timesync enable",
                                           cwd=r'"C:\Program Files\VMware\VMware Tools\"')
    Case.sleep(60)
    esxi.execute_vm_cmd(WINDOWS_VM_NAME, "echo %date%")
    esxi.execute_vm_cmd(WINDOWS_VM_NAME, "VMwareToolboxCmd.exe timesync disable", cwd=r'"C:\Program Files\VMware\VMware Tools\"')


def clean_up(sut):
    if Result.returncode != 0:
        old_sut_date = sut.execute_host_cmd('echo %date%')[1]
        old_sut_year = int(old_sut_date.split('/')[-1])
        sut.execute_shell_cmd(f'esxcli system time set -y {old_sut_year}')
        esxi = get_vmmanger(sut)
        esxi.execute_vm_cmd(WINDOWS_VM_NAME, "VMwareToolboxCmd.exe timesync disable",
                            cwd=r'"C:\Program Files\VMware\VMware Tools\"')
        esxi.execute_vm_cmd(WINDOWS_VM_NAME, "VMwareToolboxCmd.exe timesync enable",
                            cwd=r'"C:\Program Files\VMware\VMware Tools\"')
        Case.sleep(60)
        esxi.execute_vm_cmd(WINDOWS_VM_NAME, "echo %date%")
        esxi.execute_vm_cmd(WINDOWS_VM_NAME, "VMwareToolboxCmd.exe timesync disable",
                            cwd=r'"C:\Program Files\VMware\VMware Tools\"')

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