from src.virtualization.lib.tkinit import *

CASE_DESC = [
    # TODO
    'it\'s a case template',
    'replace the description here for your case',
    # list the name of those cases which are expected to be executed before this case
    '<dependencies: if any>'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    # Prepare steps - Enable VTD and VMX in BIOS
    Case.prepare("boot to Windows")
    hyperv = get_vmmanger(sut)
    boot_to_with_bios_knobs(sut, sut.default_os, 'VTdSupport', '0x1', "ProcessorVmxEnable", "0x1")

    Case.prepare("check preconditions")
    Case.precondition(VirtualMachinePrecondition(sut, 'windows1'))
    Case.precondition(FilePrecondition(sut, 'auto_poc\\', sut_tool('VT_AUTO_POC_W')))
    Case.precondition(NicPrecondition(sut, 'MLX NIC', 'Mell'))
    Case.check_preconditions()

    Case.step('Create New Virtual Switch on Hyper-V')
    MELL_NIC = hyperv.get_netadapter_by_keyword(MELL_NIC_NAME)[0]
    hyperv.create_switch(MELL_NIC_SWITCH_NAME, True, MELL_NIC)

    Case.step('Add-VMNetworkAdapter')
    if hyperv.is_vm_running(WINDOWS_VM_NAME):
        hyperv.shutdown_vm(WINDOWS_VM_NAME)
    hyperv.attach_nic_to_vm(WINDOWS_VM_NAME, MELL_NIC_SWITCH_NAME)
    hyperv.start_vm(WINDOWS_VM_NAME, 600)

    Case.step('VM ping SUT')
    vm_ip = hyperv.get_vm_ip(WINDOWS_VM_NAME, MELL_NIC_SWITCH_NAME)
    hyperv.ping_vm(vm_ip)

    Case.step('Remove VMSwitch and VMNetworkAdapter')
    hyperv.shutdown_vm(WINDOWS_VM_NAME, 600)
    hyperv.detach_nic_from_vm(WINDOWS_VM_NAME, MELL_NIC_SWITCH_NAME)
    hyperv.delete_switch(MELL_NIC_SWITCH_NAME)


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