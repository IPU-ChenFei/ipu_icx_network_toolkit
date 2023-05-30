from src.virtualization.lib.tkinit import *

CASE_DESC = [
    '1. BIOS SettingEDKII Menu -- Socket Configuration -- Processor Configuration -- VMX -> Enable'
    'EDKII Menu -- Socket Configuration -- IIO Configuration - VTd -> Enable'
    'EDKII Menu -- Platform Configuration -- Miscellaneous Configuration -- SR-IOV Support -> Enable'
    '2. Connect an external Mellanox Ethernet Adapter that supports SR-IOV to SUT'
    '3. Driver Installation'
    'Latest Driver for the PCIe device installed on both SUT and the VM image'
    'Check vendor website for the latest driver.https://www.mellanox.com/products/adapter-software/ethernet/windows/winof-2'
    'For ConnectX-3 and ConnectX-3 Pro drivers download WinOF.For ConnectX-4 and onwards adapter cards drivers download WinOF-2.'
    '4. Install Hyper-V (Refer to \'Virtualization - Hyper-V - Install Hypervisor\')'
    '5. Create a VM with the vhdx disk file that contains the correct setup, such as OS, driver, etc.'
    'Create windows VM (Refer to \'Virtualization - Hyper-V - Guest OS Install & Config\')'
    '6. OnSUT, enable the IovEnableOverride Field in the Windows Registry:'
    'Open regedit.exe and browse to the following location: Computer\HKEY_LOCAL_MACHINE\SOFTWARE\Microsoft\WindowsNT\CurrentVersion\Virtualization'
    'Insert a registry key of type DWORD (32-bit): IovEnableOverride'
    'Set the value of that key to 1'
]


def test_steps(sut, my_os):
    Case.prepare('boot to OS')
    boot_to(sut, sut.default_os)
    hyperv = get_vmmanger(sut)

    Case.prepare("check preconditions")
    Case.precondition(VirtualMachinePrecondition(sut, 'windows1'))
    Case.precondition(FilePrecondition(sut, 'auto_poc\\', sut_tool('VT_AUTO_POC_W')))
    Case.precondition(NicPrecondition(sut, 'MLX NIC', 'Mell'))
    Case.check_preconditions()

    Case.step(' Enable SR-IOV')
    sut.execute_shell_cmd('Enable-NetAdapterSriov -InterfaceDescription *Mellanox*', powershell=True)
    sut.execute_shell_cmd('net stop vmms', powershell=True)
    sut.execute_shell_cmd('net start vmms', powershell=True)

    Case.step('Enable SR-IOV in the Virtual Machine Hardware Acceleration Settings')
    MELL_NIC = hyperv.get_netadapter_by_keyword(MELL_NIC_NAME)[0]
    hyperv.create_switch(MELL_NIC_SWITCH_NAME, False, MELL_NIC)
    hyperv.attach_nic_to_vm(WINDOWS_VM_NAME, MELL_NIC_SWITCH_NAME)
    sut.execute_shell_cmd(f'Set-VMNetworkAdapter -VMName {WINDOWS_VM_NAME} -IovWeight 10', powershell=True)
    hyperv.start_vm(WINDOWS_VM_NAME, 600)

    Case.step('Confirm that Virtual Function has been correctly enabled')
    code, out, err = hyperv.execute_vm_cmd(WINDOWS_VM_NAME, 'Get-NetAdapterSriovVf -InterfaceDescription *Mellanox*', powershell=True, timeout=60)
    Case.expect('return code == 0 and no error info', code == 0 and len(err.strip()) == 0)
    vm_ip = hyperv.get_vm_ip(WINDOWS_VM_NAME, MELL_NIC_SWITCH_NAME)
    hyperv.ping_vm(vm_ip)

    Case.step('Shutdown VM and remove VM switch network adapter')
    hyperv.shutdown_vm(WINDOWS_VM_NAME, 600)
    hyperv.detach_nic_from_vm(WINDOWS_VM_NAME, MELL_NIC_SWITCH_NAME)
    hyperv.delete_switch(MELL_NIC_SWITCH_NAME)
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