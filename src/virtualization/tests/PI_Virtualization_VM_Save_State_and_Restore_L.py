"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509883842
 @Author:
 @Prerequisite:
    1. HW Configuration
    2. SW Configuration
        1. SUT Python package
            1. Updated pip
            2. Paramiko
        2. Tools
        3. Files
            1. /BKCPkg/domains/virtualization/auto-poc copy from
               \\ccr\ec\proj\DPG\PV\test_case_tool\virtualization\auto-poc.zip and **unzip it**
     3. Virtual Machine
        1. A Linux virtual machine named "rhel1"
"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    "VMM allows a VM to be saved to disk and resumed after the platform goes through a power-cycle. Verify that they "
    "function as expected "
]


def test_steps(sut, my_os):
    # type:(SUT, GenericOS) -> None

    Case.prepare("boot to os with BIOS config")
    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob("enable_vmx_xmlcli"), *bios_knob("enable_vtd_xmlcli"))

    Case.prepare('check preconditions')
    Case.precondition(VirtualMachinePrecondition(sut, 'rhel1'))
    Case.precondition(FilePrecondition(sut, 'auto_poc/', sut_tool('VT_AUTO_POC_L')))
    Case.check_preconditions()

    kvm = get_vmmanger(sut)
    state_file_name = f"{sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION')}/state_{int(time.time())}"
    Case.step("Get VM IP")
    kvm.start_vm(RHEL_VM_NAME)
    vm_ip_list = kvm.get_vm_ip_list(RHEL_VM_NAME)
    vm_ip = vm_ip_list[0] if vm_ip_list != [] else ''
    Case.expect(f'get {RHEL_VM_NAME} IP succeed', vm_ip_list != [])

    Case.step("Stores the state of the domain on the hard disk of the host system and terminates the qemu process")
    kvm.save_vm_state(RHEL_VM_NAME, state_file_name)

    Case.step("Start VM")
    kvm.start_vm(RHEL_VM_NAME)

    Case.step("Ping to VM has no problem")
    is_succeed = kvm.ping_vm(vm_ip)
    Case.expect("ping successfully", is_succeed)

    Case.step("Shutdown VM")
    kvm.shutdown_vm(RHEL_VM_NAME)

    Case.step("restore VM Image")
    kvm.restore_vm_state(RHEL_VM_NAME, state_file_name)

    Case.step("wait 10sPing to VM has no problem")
    Case.step(10)
    # is_succeed = kvm.ping_vm(vm_ip, times=30)
    code, std_out, err = sut.execute_shell_cmd(f"ping -c 4 {vm_ip}")
    Case.expect("ping successfully", '100% packet loss' not in std_out)

    Case.step(f"Restore VM {RHEL_VM_NAME}")
    kvm.shutdown_vm(RHEL_VM_NAME, timeout=3 * 60)
    sut.execute_shell_cmd("rm -f state*", cwd=sut_tool("SUT_TOOLS_LINUX_VIRTUALIZATION"))
    kvm.undefine_vm(RHEL_VM_NAME)
    kvm.create_vm_from_template(RHEL_VM_NAME, KVM_RHEL_TEMPLATE)


def clean_up(sut):
    if Result.returncode != 0:
        pass


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
