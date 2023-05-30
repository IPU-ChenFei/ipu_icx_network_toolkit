# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.infra.xtp.itp import PythonsvSemiStructured
from dtaf_core.lib.tklib.steps_lib import cleanup
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to

from src.multisocket.lib.multisocket import MultiSocket

CASE_DESC = [
    "Use ilvss to run stress test and monitor system status"
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    execution_time = int(ParameterParser.parse_parameter("execution_time")) / 60
    package = ParameterParser.parse_parameter("package")
    pc = ParameterParser.parse_parameter("pc")
    stress_timeout = execution_time + 30

    Case.prepare('boot to OS & launch itp')
    boot_to(sut, sut.default_os)
    itp = PythonsvSemiStructured(sut.socket_name, globals(), locals())
    itp.execute("unlock()")

    Case.step('Check Socket Number and clear event log')
    MultiSocket.check_socket_num_win(sut, sut.socket_num)
    sut.execute_shell_cmd("Clear-EventLog system", powershell=True)

    Case.step("Check UPI link details")
    MultiSocket.check_upi_topology(itp)
    MultiSocket.check_upi_link_speed(itp, sut)
    MultiSocket.check_upi_s_clm(itp)
    MultiSocket.check_upi_print_error(itp)

    Case.step("Run iwvss tool")
    # kill old task if it exist
    _, stdout, _ = sut.execute_shell_cmd('tasklist /FI \"IMAGENAME eq t.exe\"', 30)
    if 't.exe' in stdout:
        sut.execute_shell_cmd('taskkill /F /IM t.exe', 30)

    sut.execute_shell_cmd(
        f"t.exe /pkg {package} /reconfig /pc {pc} /flow Mem /run /minutes {int(execution_time)} /rr iwvss.log",
        cwd=r"C:\iwVSS", timeout=int(stress_timeout * 60))

    # Set idle for 12h
    Case.sleep(43200, 60 * 5)

    Case.step("Check event log for error")
    ret, out, err = sut.execute_shell_cmd("powershell.exe Get-Eventlog system -EntryType error")
    if ret != 1 or "No matches found" not in err:
        raise RuntimeError("Error found after executing iwvss stress")

    Case.step("exit itp link")
    itp.exit()


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
