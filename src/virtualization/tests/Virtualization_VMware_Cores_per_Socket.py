"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509886002
 @Author:QiBo
 @Prerequisite:
    1. HW Configuration
    2. SW Configuration
        Create a centos VM
        1. SUT Python package

        2. Tools
        3. Files
        4. virtual machine
            linux_vm_name = 'rhel1'
"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    "VMwaremulticore virtual CPU support lets you control the number of cores per virtual CPU in a virtual machine. "
    "This capability lets operating systems with socket restrictions use more of the host CPU's cores. "
]


def test_steps(sut, my_os):
    # type:(SUT, GenericOS) -> None

    Case.prepare('boot to OS')
    boot_to(sut, sut.default_os)

    Case.prepare('check preconditions')
    Case.precondition(VirtualMachinePrecondition(sut, 'rhel1'))
    Case.check_preconditions()

    cpu_number_assigned = 4
    core_num = 4

    Case.step("Set sockets and cores for the Virtual Machine")
    esxi = get_vmmanger(sut)
    esxi.execute_host_cmd_esxi(f"Get-VM {RHEL_VM_NAME}")
    esxi.shutdown_vm(RHEL_VM_NAME)
    ret, res, err = esxi.execute_host_cmd_esxi(
        f"Set-VM -VM {RHEL_VM_NAME} -NumCpu {cpu_number_assigned} -CoresPerSocket {core_num} -confirm:$false")
    Case.expect("set vm pass", ret == 0)

    Case.step("Check the results of the settings")
    esxi.execute_host_cmd_esxi('\"$result = @();'
                               '$vms = Get-view -ViewType VirtualMachine;'
                               'foreach ($vm in $vms) {'
                               '$obj = new-object psobject;'
                               '\"$obj | Add-Member -MemberType NoteProperty -Name name -Value $vm.Name;'
                               '$obj | Add-Member -MemberType NoteProperty -Name CPUSocket -Value $vm.config.hardware.NumCPU;'
                               '$obj | Add-Member -MemberType NoteProperty -Name Corepersocket -Value $vm.config.hardware.NumCoresPerSocket;\"'
                               '$result += $obj;'
                               '};'
                               '$result;\"')
    esxi.start_vm(RHEL_VM_NAME)
    vm_ip = esxi.get_vm_ip(RHEL_VM_NAME)
    Case.expect(f"Get {vm_ip} pass", vm_ip)

    Case.step("Use command line to check whether the information of Core(s) per socket and CPU")
    ret, res, err = esxi.execute_vm_cmd(RHEL_VM_NAME, "lscpu")
    cpu_number = log_check.scan_format("CPU(s):%d", res)[0]
    core_number = log_check.scan_format("Core(s) per socket: %d", res)[0]
    Case.expect(f"check {cpu_number} pass", cpu_number_assigned == cpu_number and core_number == core_num)


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
