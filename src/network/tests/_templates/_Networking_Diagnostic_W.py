
from src.network.lib import *
CASE_DESC = [
    'connect sut1 network port to sut2 network port cable',
    'Verify operating status of NIC(s) via software tool.'
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

    Case.step("set onboard nic ipv4 address")
    valos.ip_assign(conn)

    Case.step("Hardware test")
    sut_pci_type = conn.port1.nic.id_in_os.get(sutos)
    ret = sut1.execute_shell_cmd("Import-Module IntelNetCmdlets", powershell=True)[2]
    Case.expect('Import module successfully', ret == '')
    _, stdout, stderr = sut1.execute_shell_cmd("Get-IntelNetAdapter", powershell=True)
    Case.expect('Get-IntelNetAdapter successfully', stdout and stderr == '')
    nic_list = []
    for line in stdout.splitlines():
        ret = re.search(r"(?=\s).*{}.*\s(?=Eth)".format(sut_pci_type), line)
        if ret:
            str = ret.group(0).strip()
            nic_list.append(str)
    for nic in nic_list:
        test_count = 0
        test_pass = False

        while test_count < 5:
            logger.debug(f'-----start No.{test_count + 1} test-----')

            _, stdout, stderr = sut1.execute_shell_cmd('Test-IntelNetDiagnostics -Name "{}" -Test All'.format(nic),
                                                       powershell=True, timeout=600)
            Case.expect('run Test-IntelNetDiagnostics successfully', stdout != '' and stderr == '')
            test_items = re.findall(r"AdapterName[\s\S]*?ResultCode.*", stdout)

            test_items_all_pass = True
            for test_item in test_items:
                # ignore test item 'Connection Status' for it must set dhcp mode
                if 'Connection Status' in test_item:
                    continue
                if 'Failed' in test_item:
                    test_items_all_pass = False
                    break

            if not test_items_all_pass:
                logger.debug(f'-----No.{test_count + 1} failed, sleep 30 sec to start next test-----')
                test_count += 1
                time.sleep(30)
            else:
                logger.debug(f'-----No.{test_count + 1} pass-----')
                test_pass = True
                break

        if not test_pass:
            raise Exception('LOM Diagnostic failed for Harddware|Cable')


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
