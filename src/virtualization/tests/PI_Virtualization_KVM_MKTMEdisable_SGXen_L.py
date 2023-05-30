from src.virtualization.lib.tkinit import *

CASE_DESC = [
    "Verify virtual OS(Linux and Windows) basic functionality through KVM console"
]


def test_steps(sut, my_os):
    # type:(SUT, GenericOS) -> None

    Case.prepare("boot to os")
    boot_to(sut, sut.default_os)

    Case.prepare('check preconditions')
    Case.precondition(FilePrecondition(sut, 'cent0.img', sut_tool('VT_QEMU_CENT_TEMPLATE_L')))
    Case.precondition(FilePrecondition(sut, 'auto_poc/', sut_tool('VT_AUTO_POC_L')))
    Case.check_preconditions()

    # BIOS
    # Case.prepare('set BIOS knob')
    Case.step("Select a Linux system, it should have created a virtual machine with KVM.")
    qemuhypervisor = QemuHypervisor(sut)
    qemuhypervisor.create_vm_from_template(RHEL_VM_NAME, QEMU_CENT_TEMPLATE, bios=VT_OVMF_L)
    Case.expect("Automation will use a pre-script generated VM image", True)

    Case.step("set BIOS knob Enable SGX")
    set_bios_knobs_step(sut, *bios_knob('enable_sgx_setting_xmlcli'))

    Case.step("Launch VM")
    qemuhypervisor.start_vm(RHEL_VM_NAME)
    code, out, err = qemuhypervisor.execute_vm_cmd(RHEL_VM_NAME, 'ls')
    Case.expect("The virtual machine should be able to launch up success.and able to ssh to VM", code == 0)

    qemuhypervisor.shutdown_vm(RHEL_VM_NAME)
    # qemuhypervisor.undefine_vm(RHEL_VM_NAME, True)

    set_bios_knobs_step(sut, *bios_knob('disable_sgx_setting_xmlcli'))


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
