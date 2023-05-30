"""
 @Case Link: https://hsdes.intel.com/appstore/article/#/1509883741
 @Author:Liu, JianjunX
 @Prerequisite:
    1. HW Configuration
        1. Plug an Intel Ethernet Controller X710 into SUT
    2. SW Configuration
        1. Install Power CLI on local Windows host
            Install-Module VMware.PowerCLI -Force
        2.  Create a centos VM
            Refer to 'Virtualization - VMware - Virtual Machine Guest OS (Centos) Installation'
        2. Tools
        3. Files
        4. virtual machine
            linux_vm_name = 'rhel1'
"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    'Verify SRIOV VF adapter can be generated for working'
]


def get_dhcp_pf_ids(esxi, nics):
    """
    Get the IDS of the specified network card type and connect the network cable
    return: list
    """
    pci_ids = []
    pf_ids = []
    code, out, err = esxi.execute_host_cmd_esxi(
        "Get-VMHostNetworkAdapter -Physical| Where-Object {$_.FullDuplex -match 'True'} | fl")
    out = log_check.find_lines("PciId              :", out)
    for id in out:
        temp = id.replace("PciId              : ", "")
        pci_ids.append(temp)
    nics = str(nics)[:-1].split('\n')
    for nic in nics:
        nic = nic.strip().split(' ')[0]
        if any(nic in s for s in pci_ids):
            pf_ids.append(nic)
    return pf_ids


def dhcp_ip_assgin(esxi, vm_name):
    rcode, std_out, std_err = esxi.execute_vm_cmd(vm_name, "lspci |grep -i 'Virtual Function'")
    nics = str(std_out)[:-1].split('\n')
    target_nic = nics[0].strip().split(' ')
    bdf = target_nic[0].strip()
    _, ether_name, std_err = esxi.execute_vm_cmd(vm_name, f'ls /sys/bus/pci/devices/0000:{bdf}/net')
    ether_name = ether_name.strip()
    esxi.execute_vm_cmd(vm_name, f"mkdir -p {sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION')}")
    cur_path = os.path.abspath(__file__)
    project_path_virtual = f"{cur_path.split('src')[0]}\\src\\virtualization\\lib"
    ifcfg_template = f"{project_path_virtual}\\tools\\ifcfg-template"
    esxi.upload_to_vm(vm_name, ifcfg_template, f"{sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION')}/ifcfg-ens192")

    Case.step("Copy the information of the default NIC to the NIC we added:")
    new_ethr = f"/etc/sysconfig/network-scripts/ifcfg-{ether_name}"
    code, out, err = esxi.execute_vm_cmd(vm_name, f"cp -rf {sut_tool('SUT_TOOLS_LINUX_VIRTUALIZATION')}/ifcfg-ens192"
                                 f" {new_ethr}")
    Case.expect("The information will be copied successfully", err == "")
    out = ""
    Case.step("Change NAME and DEVICE to <NIC_Num>, and delete UUID number:")
    code, out, err = esxi.execute_vm_cmd(vm_name, f"sed -i '/UUID/d' {new_ethr}")
    Case.expect("delete UUID successful! ", err == "")
    code, out, err = esxi.execute_vm_cmd(vm_name, r'sed -i "s/NAME.*$/NAME={}/g" {}'.format(ether_name,new_ethr))
    Case.expect("update NAME value successful! ", err == "")
    code, out, err = esxi.execute_vm_cmd(vm_name, r'sed -i "s/DEVICE.*$/DEVICE={}/g" {}'.format(ether_name,new_ethr))
    Case.expect("update DEVICE value successful! ", err == "")
    code, out, err = esxi.execute_vm_cmd(vm_name, f"cat {new_ethr }")
    Case.expect("Change and save the file.", err == "")
    Case.step("Reload the NIC and  check the information:")
    code, out, err = esxi.execute_vm_cmd(vm_name, "nmcli c reload")
    Case.expect("reload network successful! ", err == "")

    for i in range(10):
        _, out, std_err = esxi.execute_vm_cmd(vm_name, f"ifconfig {ether_name}")
        if len(log_check.find_lines("inet ", out)) != 0:
            out = log_check.scan_format("inet %s", out)[0]
            break
        Case.sleep(5)
    Case.expect(f"ip addr: {out}", out!="")
    return out


def enable_SRIOV(esxi, dev_id, server_ip, num=1):
    cmd = '$spec=New-Object VMware.Vim.HostSriovConfig;' \
          '$spec.SriovEnabled="$true";' \
          f'$spec.NumVirtualFunction="{num}";' \
          f'$spec.Id=\\"{dev_id}\\";' \
          f'$spec.ApplyNow="$true";' \
          f'$esx=Get-VMHost {server_ip};' \
          f'$ptMgr=Get-View -Id $esx.ExtensionData.ConfigManager.PciPassthruSystem;' \
          f'$ptMgr.UpdatePassthruConfig($spec);echo $spec'
    rcode, std_out, std_err = esxi.execute_host_cmd_esxi(cmd, timeout=60 * 2)
    return rcode, std_out, std_err


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    Case.prepare("boot to uefi shell")
    boot_to(sut, SUT_STATUS.S0.UEFI_SHELL)
    set_bios_knobs_step(sut, *bios_knob('knob_setting_virtual_common_xmlcli'))
    UefiShell.reset_to_os(sut)

    Case.wait_and_expect(f'OS for system back to os', 15 * 10 * 60, sut.check_system_in_os)
    Case.sleep(60)

    Case.prepare('check preconditions')
    Case.precondition(VirtualMachinePrecondition(sut, 'rhel1'))
    Case.check_preconditions()

    server_ip = sut.supported_os[sut.default_os].ip
    Case.step('Connect to server:')
    esxi = get_vmmanger(sut)
    Case.step('Enabling SR-IOV :')

    _, devs, err = sut.execute_shell_cmd(f"lspci | grep {X710_NIC_TYPE}")
    pf_ids = get_dhcp_pf_ids(esxi, devs)
    Case.expect("get NIC success", devs != "")
    PF_ID = pf_ids[0]
    rcode, std_out, std_err = enable_SRIOV(esxi, PF_ID, server_ip)
    Case.expect(f"Enable SRIOV {PF_ID}", std_err is None)

    Case.step("Use the following command to obtain the SR-IOV device bus number:")
    ret, res, err = esxi.execute_host_cmd_esxi(
        f"Get-PassthroughDevice -VMHost {server_ip} -Type Pci | "
        f'Where-Object {{$_.Name -match \\"{X710_NIC_TYPE}\\"}} | '
        r"Format-Custom -Property ExtensionData -Depth 2")
    Case.expect(f"The devicename and {PF_ID} in the output result should be the device of virtual functions.",
                err is None)

    Case.step("Add a new SR-IOV network adapter:")
    code, out, err = esxi.execute_host_cmd_esxi(f'$nic = Get-NetworkAdapter -VM {RHEL_VM_NAME} |'
                                                r' Where-Object{$_.Name -match \"SR-IOV\"};'
                                                r'Remove-NetworkAdapter -NetworkAdapter $nic -Confirm:$false')
    Case.expect('remove all SR-IOV devices success!', code == 0)
    code, out, err = esxi.execute_host_cmd_esxi(
        f"New-NetworkAdapter -VM {RHEL_VM_NAME} -type SriovEthernetCard -NetworkName 'VM Network' -PhysicalFunction '{PF_ID}'")
    Case.expect("Add SR-IOV network adapter success", err is None)

    Case.step("Start Virtual Machine:")
    esxi.start_vm(RHEL_VM_NAME)

    Case.step("Get the IP Address of Virtual Machine:")
    vm_ip = esxi.get_vm_ip(RHEL_VM_NAME)
    Case.expect("get the vm ip successful ", vm_ip != '')

    Case.step("Check the PCI device:")
    _, out, err = esxi.execute_vm_cmd(RHEL_VM_NAME, r'lspci | grep -i \\"Virtual Function\\"')
    Case.expect("NIC can be displayed normally", out != "")

    Case.step("Check the NIC device number:")
    dhcp_ip_assgin(esxi, RHEL_VM_NAME)

    Case.step("restore vm env")
    esxi.shutdown_vm(RHEL_VM_NAME)
    code, out, err = esxi.execute_host_cmd_esxi(f'$nic = Get-NetworkAdapter -VM {RHEL_VM_NAME} |'
                                                r' Where-Object{$_.Name -match \"SR-IOV\"};'
                                                r'Remove-NetworkAdapter -NetworkAdapter $nic -Confirm:$false')
    Case.expect('remove all SR-IOV devices success!', code == 0)


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
