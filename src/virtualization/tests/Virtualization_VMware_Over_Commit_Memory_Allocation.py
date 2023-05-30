"""
 @Case Link:https://hsdes.intel.com/appstore/article/#/1509885971
 @Author:YanXu
 @Prerequisite:
    1. HW Configuration
    2. SW Configuration
        1. SUT Python package
        2. Tools
            1.install epel-release
            2.install stress
        3. Files
    3. Virtual Machine
        1. Set up a Centos VM
"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    "Test that all the memory in the system can be allocated and to test ESX's ability to overcommit a certain amount of memory."
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    boot_to(sut, sut.default_os)

    esxi = get_vmmanger(sut)

    if esxi.is_vm_running(RHEL_VM_NAME):
        esxi.shutdown_vm(RHEL_VM_NAME)

    Case.step('Assign the virtual machine with more memory than the system has and power on the VM')
    code, out, err = sut.execute_shell_cmd("esxcli hardware memory get")
    mem_bytes = log_check.scan_format("Physical Memory: %d", out)[0]
    mem_GB = int(mem_bytes / 1024 / 1024 / 1024)
    # TODO: vm_memory = int(mem_GB - 50)
    vm_memory = 200
    vm_bytes = int(mem_GB/2 - 2)
    vm2_bytes = int(mem_GB/2 - 3)
    vm_time = '5m'
    vm2_time = '10m'
    log_5m = 'log_5_m.txt'
    log_10m = 'log_10_m.txt'
    ret, set_vm_result, err = esxi.execute_host_cmd_esxi(f'Get-VM {RHEL_VM_NAME} | Set-VM -MemoryGB {vm_memory} -Confirm:$false')
    Case.expect('Each CLI exec successfully and returns a zero return code', ret == 0)

    esxi.start_vm(RHEL_VM_NAME)

    Case.step("Check that memory balloon hasn't taken place before stress")
    _, vm_stat, _ = esxi.execute_vm_cmd(RHEL_VM_NAME, 'vmware-toolbox-cmd stat balloon')
    vm_speed = log_check.find_lines("0 MB", vm_stat)
    Case.expect('The returned value is 0 MB', vm_speed)

    Case.step('Begin to memory stress the virtual machine')
    esxi.execute_vm_cmd_async(RHEL_VM_NAME, f'stress --vm 2 --vm-bytes {vm_bytes}G --timeout {vm_time}', timeout=5 * 60)
    ret, res, err = esxi.execute_vm_cmd(RHEL_VM_NAME, f'./check_ballon.sh {log_5m}', timeout=5 * 60)
    stress_log = log_check.find_lines("0 MB", res)
    Case.expect('stress test successfully', not stress_log)
    _, cat_result, _ = esxi.execute_vm_cmd(RHEL_VM_NAME, f'cat {log_5m}')
    Case.expect('test pass', '0 MB' not in cat_result)

    Case.step('Allow the system to stress for a few hours to ensure that the balloon driver is properly working')
    esxi.execute_vm_cmd_async(RHEL_VM_NAME, f'stress --vm 2 --vm-bytes {vm2_bytes}G --timeout {vm2_time}', timeout=10 * 60)
    ret, res, err = esxi.execute_vm_cmd(RHEL_VM_NAME, f'./check_ballon.sh {log_10m}', timeout=10 * 60)
    stress_log2 = log_check.find_lines("0 MB", res)
    Case.expect('stress test successfully', not stress_log2)
    _, cat_result_log, _ = esxi.execute_vm_cmd(RHEL_VM_NAME, f'cat {log_10m}')
    Case.expect('test pass', '0 MB' not in cat_result_log)

    esxi.shutdown_vm(RHEL_VM_NAME)
    esxi.execute_host_cmd_esxi(f'Get-VM {RHEL_VM_NAME} | Set-VM -MemoryGB 4 -Confirm:$false')


def clean_up(sut):
    esxi = get_vmmanger(sut)
    if Result.returncode != 0:
        esxi.execute_host_cmd_esxi(f'Get-VM {RHEL_VM_NAME} | Set-VM -MemoryGB 4 -Confirm:$false')
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
