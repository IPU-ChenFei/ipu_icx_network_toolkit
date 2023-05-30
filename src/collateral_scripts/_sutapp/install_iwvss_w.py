import os.path

from dtaf_core.lib.tklib.auto_api import *

CASE_DESC = [
    "install iwvss to sut (windows)"
]


def test_steps(sut, my_os):
    Case.prepare("boot to OS")
    boot_to(sut, sut.default_os)

    Case.step('deploy and install')
    tools = get_tool(sut)
    tool_instance = tools.get('iwvss_2.9.2_w')
    tool_folder = tool_instance.filename.replace('.zip', '')
    tool_parent_path = tool_instance.uncompress_to(method='zip')
    tool_path = os.path.join(tool_parent_path, tool_folder)
    sut.execute_shell_cmd('"iwVSS 2.9.2.exe" /S', cwd=tool_path)
    my_os.warm_reset_cycle_step(sut)

    Case.step('deploy license key')
    tools.get('ixvss_license_key_2024').uncompress_to(method='copy', install_path='C:\\iwVSS')


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
