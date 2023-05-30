
from src.network.lib import *
CASE_DESC = [
    'check Driver install/uninstall successful'
]


def install_uninstall(sut, tool, type):
    unzip_dir = tool.strip(".tar.gz")
    mod = unzip_dir.split("-")[0]

    Case.step("install driver")
    ret = sut.execute_shell_cmd("cp {} /usr/local/src".format(tool), cwd="/home/BKCPkg/domains/network/")
    Case.expect("copy file successful", ret[0] == 0)
    ret = sut.execute_shell_cmd("tar -zxf {}".format(tool), cwd="/usr/local/src")
    Case.expect("unzip file successful", ret[0] == 0)
    ret = sut.execute_shell_cmd("make install", cwd="/usr/local/src/{}/src/".format(unzip_dir), timeout=120)
    Case.expect("unzip file successful", ret[0] == 0)
    ret = sut.execute_shell_cmd("modprobe {}".format(mod))
    Case.expect("install driver successful", ret[0] == 0)
    ret = sut.execute_shell_cmd("lsmod |grep {}".format(mod))
    Case.expect("grep {} successful".format(mod), ret[0] == 0)
    ret = sut.execute_shell_cmd("lspci |grep -i {}".format(type))
    Case.expect("grep {} successful".format(type), ret[0] == 0)

    Case.step("check driver install successful")
    ret = sut.execute_shell_cmd("modinfo {}".format(mod))
    Case.expect("{} driver install successful".format(type), ret[0] == 0)

    Case.step("uninstall driver")
    ret = sut.execute_shell_cmd("rmmod {}".format(mod))
    sut.execute_shell_cmd("lsmod |grep {}".format(mod))
    Case.expect("driver uninstall successful", ret[0] == 0)

    Case.step("reinstall driver")
    sut.execute_shell_cmd("modprobe {}".format(mod))
    ret = sut.execute_shell_cmd("lsmod |grep {}".format(mod))
    Case.expect("grep {} successful".format(mod), ret[0] == 0)


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

    Case.step("install/uninstall driver")
    sut_pci_type = conn.port1.nic.id_in_os.get(sutos)
    install_uninstall(sut1, tool, sut_pci_type)
    install_uninstall(sut2, tool, sut_pci_type)


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