from src.network.lib.dpdk.dpdk_common import *
from src.network.lib import *
CASE_DESC = [
    """
    This purpose of this case is to verify DPDK installation process
    """
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    tool = ParameterParser.parse_parameter("tool")

    Case.prepare("prepare steps")
    boot_to(sut, sut.default_os)

    Case.step("untar dpdk")
    ret = sut.execute_shell_cmd("tar -xvf {}".format(tool),
                                cwd=bhs_sut_tools.SUT_TOOLS_LINUX_NETWORK)[0]
    Case.expect("untar sut dpdk tool", ret == 0)

    Case.step("dpdk installation")
    install_dpdk(sut)

    Case.step("check folders")
    ret = sut.execute_shell_cmd("ls", cwd=bhs_sut_tools.NW_DPDK_INSTALL_L)[1]
    file_name = ['app', 'compile_commands.json', 'drivers', 'build.ninja']
    for index in range(len(file_name)):
        value_key = log_check.find_keyword(file_name[index], ret)
        Case.expect(f"{value_key} file exist", value_key != '')

    Case.step("check dpdk version")
    res = sut.execute_shell_cmd(r"./dpdk-testpmd -v", cwd=bhs_sut_tools.NW_VERSION_CHECK_L)[2]
    ver = re.search(r'\d+(\.\d+)+', tool).group()
    ret = log_check.find_lines(ver, res)
    Case.expect(f"dpdk version is {ret}", ret)



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
