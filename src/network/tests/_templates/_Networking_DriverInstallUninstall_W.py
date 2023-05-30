
from src.network.lib import *
CASE_DESC = [
    'check Driver install/uninstall successful'
]


def install_uninstall(sut, path, type):
    _, stdout, _ = sut.execute_shell_cmd("get-wmiobject win32_pnpsigneddriver | select devicename, driverprovidername, infname | where {$_.devicename -like 'Intel*%s*'} | where {$_.driverprovidername -like 'Intel*'}" % type, powershell=True)
    for line in stdout.splitlines():
        if line.endswith(".inf"):
            ret = line.split()[-1]
            retcode = sut.execute_shell_cmd('pnputil /delete-driver "{}" /uninstall /force'.format(ret), timeout=60)[0]
            Case.sleep(10)
            #Case.expect("delete inf file <{}>".format(ret), ret == 3010)
            #if ret == 3010:
            break

    sut.execute_shell_cmd("shutdown /r /t 0")
    Case.sleep(10)
    Case.wait_and_expect('wait for restoring sut1 ssh connection', 60 * 5, sut.check_system_in_os)

    Case.step("install network driver")
    retcode = sut.execute_shell_cmd('pnputil /add-driver "*.inf" /install', cwd=path, timeout=180)
    Case.sleep(10)
    sut.execute_shell_cmd("shutdown /r /t 0")
    Case.sleep(10)
    Case.wait_and_expect('wait for restoring sut1 ssh connection', 60 * 5, sut.check_system_in_os)


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    sutos = ParameterParser.parse_parameter("sutos")
    conn = ParameterParser.parse_parameter("conn")
    tool = ParameterParser.parse_parameter("tool")
    valos = val_os(sutos)

    sut1 = sut
    sut2 = get_sut_list()[1]
    conn = nic_config(sut1, sut2, conn)

    Case.prepare("prepare steps")
    boot_to(sut1, sut1.default_os)
    Case.wait_and_expect('wait for restoring sut2 ssh connection', 60 * 5, sut2.check_system_in_os)

    Case.step("set ipv4")
    valos.ip_assign(conn)

    # Case.step("unzip tools")
    # updatepath = tool.split("x64.zip")[0]

    # ret = valos.unzip7z_tools(sut1, tool, "{}update".format(updatepath), flag=True)
    # ret = valos.unzip7z_tools(sut2, tool, "{}update".format(updatepath), flag=True)


    Case.step("install/uninstall driver")
    sut_pci_type = conn.port1.nic.id_in_os.get(sutos)
    if sut_pci_type == "I210":
        flag = "PRO1000"
    elif sut_pci_type == "E810":
        flag = "PROCGB"
    elif sut_pci_type == "I350":
        flag = "PRO1000"
    elif sut_pci_type == 'Ethernet Converged Network Adapter X710':
        flag = "PRO40GB"
    elif sut_pci_type == 'X710-T':
        flag = "PRO40GB"
    #tool_path = tool.split(".zip")[0]
    path = r"C:\driver\driver\{}\Winx64\NDIS68".format(tool)
    #path = r"{}\{}Upgrade7".format(valos.tool_path, flag)
    install_uninstall(sut1, path, sut_pci_type)
    Case.wait_and_expect('wait for restoring sut2 ssh connection', 60 * 5, sut2.check_system_in_os)
    install_uninstall(sut2, path, sut_pci_type)


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