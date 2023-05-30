from src.virtualization.lib.tkinit import *

CASE_DESC = [
    'Configuration:1.BIOS Setting:EDKII Menu -- Socket Configuration -- Processor Configuration -- VMX -> Enable '
    'EDKII Menu -- Socket Configuration -- IIO Configuration ?Intel@ VT for Directed I/O(VT-d) -- Intel@ VT for Directed I/O -> Enable',
    '2.Install Hyper-V (Refer to Virtualization - Hyper-V - Install Hypervisor)'
    '3. Connect an external Ethernet Network Adapter to SUT'
    '4.Create a windows VM(Refer to Virtualization - Hyper-V - Guest OS Install & Config)'
]


def get_x710_nic_interface_list(sut):
    cmd = 'Get-PnpDevice -PresentOnly|Select FriendlyName | Where-Object{$_.friendlyName -match "X710"}'
    output = sut.execute_shell_cmd(cmd, powershell=True)[1].strip()
    return output.splitlines()[2:]


def test_steps(sut, my_os):
    Case.prepare('boot to OS')
    boot_to(sut, sut.default_os)

    Case.prepare("check preconditions")
    Case.precondition(VirtualMachinePrecondition(sut, 'windows1'))
    Case.precondition(FilePrecondition(sut, 'auto_poc\\', sut_tool('VT_AUTO_POC_W')))
    Case.precondition(NicPrecondition(sut, 'X710', '710'))
    Case.check_preconditions()

    Case.step(' Enable SR-IOV')
    hyperv = get_vmmanger(sut)
    nic_interface = get_x710_nic_interface_list(sut)[1]
    sut.execute_shell_cmd(f'Enable-NetAdapterSriov -InterfaceDescription "{nic_interface}"', powershell=True)
    sut.execute_shell_cmd('net stop vmms', powershell=True)
    sut.execute_shell_cmd('net start vmms', powershell=True)

    Case.step('Create VM and Start VM')
    hyperv.start_vm(WINDOWS_VM_NAME, 600)
    cmd = rf'Set-NetFirewallProfile -Profile Domain,Public,Private -Enabled False'
    (code, stdout, stderr) = hyperv.execute_vm_cmd(WINDOWS_VM_NAME, cmd, powershell=True, timeout=60)
    Case.expect('return code == 0 and no error info', code == 0 and len(stderr.strip()) == 0)
    hyperv.shutdown_vm(WINDOWS_VM_NAME)

    Case.step('Passthrough network to VM')
    hyperv.create_switch(NIC_SWITCH_NAME, interface_desc=nic_interface)
    hyperv.attach_nic_to_vm(WINDOWS_VM_NAME, NIC_SWITCH_NAME)
    sut.execute_shell_cmd(cmd=f'Set-VMNetworkAdapter -VMName {WINDOWS_VM_NAME} -IovWeight 10', powershell=True)

    Case.step('Confirm that Virtual Function has been correctly enabled')
    hyperv.start_vm(WINDOWS_VM_NAME, 600)

    code, out, err = hyperv.execute_vm_cmd(WINDOWS_VM_NAME, 'Get-NetAdapter', powershell=True, timeout=60)
    Case.expect('return code == 0 and no error info', code == 0 and len(err.strip()) == 0)

    Case.step('ping IP')
    vm_ip = hyperv.get_vm_ip(WINDOWS_VM_NAME, NIC_SWITCH_NAME)
    hyperv.ping_vm(vm_ip)

    Case.step('Shutdown VM and remove VM switch network adapter')
    hyperv.shutdown_vm(WINDOWS_VM_NAME, 600)
    hyperv.detach_nic_from_vm(WINDOWS_VM_NAME, NIC_SWITCH_NAME)
    hyperv.delete_switch(NIC_SWITCH_NAME)
    my_os.warm_reset_cycle_step(sut)


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