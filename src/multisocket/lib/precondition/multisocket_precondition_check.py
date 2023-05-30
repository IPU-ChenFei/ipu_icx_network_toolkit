from dtaf_core.lib.tklib.auto_api import *

CASE_DESC = [
    "multisocket pre-condition check"
]


def test_steps(sut, sutos):
    assert (issubclass(sutos, GenericOS))
    Case.prepare("boot to OS")
    boot_to(sut, sut.default_os)

    Case.step('pre-condition check')
    if OS.get_os_family(sut.default_os) in SUT_STATUS.S0.LINUX_FAMILY:
        # TODO
        pass

    if OS.get_os_family(sut.default_os) == SUT_STATUS.S0.WINDOWS:
        tools = get_tool(sut)

        # Check mlc_w
        tool_path = os.path.join(tools.get('mlc_w').ipath, tools.get('mlc_w').filename.replace('.zip', ''))
        Case.precondition(CommandPrecondition(sut, "mlc_w", os.path.join(tool_path, "mlc_internal.exe --help")))
        Case.precondition(FilePrecondition(sut, "mlc_w", os.path.join(tool_path, "config_4s.txt")))
        Case.precondition(FilePrecondition(sut, "mlc_w", os.path.join(tool_path, "config_8s.txt")))

        # Check linpack_w
        tool_path = os.path.join(tools.get('linpack_w').ipath, tools.get('linpack_w').filename.replace('.zip', ''))
        Case.precondition(FilePrecondition(sut, "linpack_w", tool_path))

        # Check stream_w
        tool_path = os.path.join(tools.get('stream_w').ipath, tools.get('stream_w').filename.replace('.zip', ''))
        Case.precondition(FilePrecondition(sut, "stream_w", os.path.join(tool_path, "wstream.exe")))

        # Check iwvss
        Case.precondition(FilePrecondition(sut, "iwvss", r"C:\iwVss\t.exe"))

    Case.check_preconditions()


def clean_up(sut):
    pass


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
