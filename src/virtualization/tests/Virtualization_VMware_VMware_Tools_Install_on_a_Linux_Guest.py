"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509885942
 @Author:YanXu
 @Prerequisite:
    1. HW Configuration
    2. SW Configuration
        1. SUT Python package
        2. Tools
        3. Files
    3. Virtual Machine
        1. Create a centos VM
"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    "Test that the VMware Tools are installed properly on a Linux guest"
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    Case.prepare("boot to os")
    boot_to(sut, sut.default_os)
    Case.sleep(60)

    Case.prepare('check preconditions')
    Case.precondition(VirtualMachinePrecondition(sut, 'rhel1'))
    Case.check_preconditions()

    esxi = get_vmmanger(sut)

    if not esxi.is_vm_running(RHEL_VM_NAME):
        esxi.start_vm(RHEL_VM_NAME)

    Case.step('Get the ip of VM:')
    esxi.get_vm_ip(RHEL_VM_NAME)

    Case.step('Check the status of time synchronization:')
    _, status, _ = esxi.execute_vm_cmd(RHEL_VM_NAME, 'vmware-toolbox-cmd timesync status')
    if 'Disabled' in status:
        Case.expect('Time synchronization has been disabled', 'Disabled' in status)

        Case.step('Enable the time synchronization:')
        _, set_enable, _ = esxi.execute_vm_cmd(RHEL_VM_NAME, 'vmware-toolbox-cmd timesync enable')
        Case.expect('Enable the time synchronization successfully', "Enabled" in set_enable)

    Case.step('Check the date of VM:')
    esxi.execute_vm_cmd(RHEL_VM_NAME, 'date -R')[1]

    Case.step('Set a new time for server:')
    old_sut_date = sut.execute_shell_cmd('esxcli system time get')[1]
    old_sut_year = int(old_sut_date.split('-')[0])
    _, _, std_err = sut.execute_shell_cmd(f'esxcli system time set -y {old_sut_year + 1}')
    Case.expect('The time will be set successfully', std_err.strip() == "")

    esxi.reboot_vm(RHEL_VM_NAME)
    Case.sleep(60)

    Case.step('Check if the time has been changed:')
    _, date_result, _ = sut.execute_shell_cmd('date')
    new_sut_year = int(date_result.split()[-1])
    Case.expect('The SUT time has been changed', new_sut_year == old_sut_year + 1)

    Case.step('Check if the time of VM is synchronized:')
    _, vm_date_result, _ = esxi.execute_vm_cmd(RHEL_VM_NAME, 'date -R')
    new_vm_year = int(vm_date_result.split()[3])
    Case.expect('VMware Tools are installed properly on a Linux guest', new_vm_year == new_sut_year)
    esxi.execute_vm_cmd(RHEL_VM_NAME, 'vmware-toolbox-cmd  timesync disable')

    _, _, std_err = sut.execute_shell_cmd(f'esxcli system time set -y {old_sut_year}')
    Case.expect('The time will be set successfully', std_err.strip() == "")


def clean_up(sut):
    if Result.returncode != 0:
        old_sut_date = sut.execute_host_cmd('echo %date%')[1]
        old_sut_year = int(old_sut_date.split('/')[-1])
        sut.execute_shell_cmd(f'esxcli system time set -y {old_sut_year}')
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