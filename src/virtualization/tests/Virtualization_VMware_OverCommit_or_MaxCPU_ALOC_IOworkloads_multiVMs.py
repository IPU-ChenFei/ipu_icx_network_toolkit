"""
 @Case Link:https://hsdes.intel.com/appstore/article/#/1509885966
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
        1. Set up 2 Centos VMs
"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    "Test case is similar to 'Virtualization - VMware - Over Commit Memory Allocation'"
    "Need to overcommit CPUs to Guest VM and run the IO workloads."
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    Case.prepare("boot to os")
    boot_to(sut, sut.default_os)
    Case.sleep(60)

    Case.prepare('check preconditions')
    Case.precondition(VirtualMachinePrecondition(sut, 'Vsphere'))
    Case.precondition(VirtualMachinePrecondition(sut, 'rhel2'))
    Case.check_preconditions()

    stress_run_time = 1

    esxi = get_vmmanger(sut)
    if esxi.is_vm_running(RHEL_VM_NAME):
        esxi.shutdown_vm(RHEL_VM_NAME)

    if esxi.is_vm_running(RHEL_VM_NAME2):
        esxi.shutdown_vm(RHEL_VM_NAME2)

    _, cpu_num, _ = sut.execute_shell_cmd("cat /proc/cpuinfo | grep 'process' | sort | uniq | wc -l")
    num = math.ceil(int(cpu_num)/2)

    Case.step('Assign more CPUs to the virtual machines than total available CPUs on SUT')
    recode, _, _ = esxi.execute_host_cmd_esxi(f'Get-VM {RHEL_VM_NAME} | Set-VM -NumCpu {num} -Confirm:$false')
    Case.expect('Each CLI exec successfully and returns a zero return code', recode == 0)
    recode, _, _ = esxi.execute_host_cmd_esxi(f'Get-VM {RHEL_VM_NAME2} | Set-VM -NumCpu {num} -Confirm:$false')
    Case.expect('Each CLI exec successfully and returns a zero return code', recode == 0)

    esxi.start_vm(RHEL_VM_NAME)
    esxi.start_vm(RHEL_VM_NAME2)

    Case.step('Run stress tests in 2 VMs with all assigned CPU simultaneously')
    vm1_res, _, _ = esxi.execute_vm_cmd_async(RHEL_VM_NAME, f'stress --cpu {num} --io 16 --timeout {stress_run_time}m',
                                              timeout=10 * 60)
    Case.expect('streee success', vm1_res is None)
    vm2_res, _, _ = esxi.execute_vm_cmd_async(RHEL_VM_NAME2, f'stress --cpu {num} --io 16 --timeout {stress_run_time}m',
                                              timeout=10 * 60)
    Case.expect('streee success', vm2_res is None)
    Case.sleep(stress_run_time + 60)
    result_path = os.path.join(LOG_PATH, 'result')
    os.mkdir(result_path)
    vm1_stress = f"{result_path}\\vm1_stress.log"
    esxi.download_from_vm(RHEL_VM_NAME, vm1_stress, '/root/stdout.log')
    vm2_stress = f"{result_path}\\vm2_stress.log"
    esxi.download_from_vm(RHEL_VM_NAME, vm2_stress, '/root/stdout.log')
    code, out, err = esxi.execute_vm_cmd(RHEL_VM_NAME, 'cat /root/stdout.log')
    result = log_check.find_lines("completed", out)
    Case.expect("run completed", result != "")
    code, out, err = esxi.execute_vm_cmd(RHEL_VM_NAME2, 'cat /root/stdout.log')
    result = log_check.find_lines("completed", out)
    Case.expect("run completed", result != "")

    if esxi.is_vm_running(RHEL_VM_NAME):
        esxi.shutdown_vm(RHEL_VM_NAME)
    if esxi.is_vm_running(RHEL_VM_NAME2):
        esxi.shutdown_vm(RHEL_VM_NAME2)

    Case.step('Restore VM CPU settings')
    recode, _, _ = esxi.execute_host_cmd_esxi(f'Get-VM {RHEL_VM_NAME} | Set-VM -NumCpu 2 -Confirm:$false')
    Case.expect('Each CLI exec successfully and returns a zero return code', recode == 0)
    recode, _, _ = esxi.execute_host_cmd_esxi(f'Get-VM {RHEL_VM_NAME2} | Set-VM -NumCpu 2 -Confirm:$false')
    Case.expect('Each CLI exec successfully and returns a zero return code', recode == 0)


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