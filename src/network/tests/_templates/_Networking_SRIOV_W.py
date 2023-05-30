
from src.network.lib import *
CASE_DESC = [
    'connect sut1 network port to sut2 network port cable',
    'check the networking VF setup functionality for SR-IOV'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    sutos = ParameterParser.parse_parameter("sutos")
    conn = ParameterParser.parse_parameter("conn")
    valos = val_os(sutos)

    sut1 = sut
    sut2 = get_sut_list()[1]
    conn = nic_config(sut1, sut2, conn)

    Case.prepare("prepare steps")
    boot_to(sut1, sut1.default_os)
    Case.wait_and_expect('wait for restoring sut2 ssh connection', 60 * 5, sut2.check_system_in_os)

    Case.step("set ipv4")
    valos.ip_assign(conn)

    Case.step("set BIOS")
    set_bios_knobs_step(sut1, *bios_knob('enable_vtd_xmlcli'))

    Case.step("set SRIOV enable")
    sut_pci_type = conn.port1.nic.id_in_os.get(sutos)
    _, stdout, _ = sut1.execute_shell_cmd('wmic path win32_networkadapter get Description,NetConnectionID,NetEnabled')
    ret = re.search(r".*{}.*(Ethernet \d+)\s+TRUE".format(sut_pci_type), stdout)
    nic_id = ret.group(1)
    ret, out, err = sut1.execute_shell_cmd('BCDEdit /set hypervisorlaunchtype auto')
    ret = sut1.execute_shell_cmd('Set-NetAdapterAdvancedProperty -Name "{}" -DisplayName "SR-IOV" -DisplayValue "Enabled"'.format(nic_id), powershell=True)
    Case.expect('enable sriov', ret[2] == '')

    Case.step("enable Hyper-V")
    vm_setup(sut1, my_os=my_os)
    try:
        ret, out, err = sut1.execute_shell_cmd('python C:\\BKCPkg\\domains\\network\\vm_sut_w.py "vm3" \"{}\" "123"'.format(nic_id), timeout=600)
        if ret != 0:
            raise Exception(err)
    except Exception as e:
        ret, out, err = sut1.execute_shell_cmd('Stop-VM -Name * -Force', timeout=600, powershell=True)
        ret, out, err = sut1.execute_shell_cmd('Remove-VM -Name * -Force', timeout=600, powershell=True)
        ret, out, err = sut1.execute_shell_cmd('Remove-VMSwitch -Name * -Force', timeout=600, powershell=True)
        raise Exception(err)
    finally:
        ret, out, err = sut1.execute_shell_cmd('Stop-VM -Name * -Force', timeout=600, powershell=True)
        ret, out, err = sut1.execute_shell_cmd('Remove-VM -Name * -Force', timeout=600, powershell=True)
        ret, out, err = sut1.execute_shell_cmd('Remove-VMSwitch -Name * -Force', timeout=600, powershell=True)
    


def clean_up(sut):
    from dtaf_core.lib.tklib.steps_lib import cleanup
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