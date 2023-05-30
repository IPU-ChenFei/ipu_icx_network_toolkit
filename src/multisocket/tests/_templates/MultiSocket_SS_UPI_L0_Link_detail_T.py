# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.infra.xtp.itp import PythonsvSemiStructured
from dtaf_core.lib.tklib.steps_lib import cleanup
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to

from src.multisocket.lib.multisocket import MultiSocket

CASE_DESC = [
    'System boot to OS successfully without any hang or unexpected errors',
    'Check UPI Link Topology, LinkSpeed, B/W and UPI link Error via ITP by pythonsv'
]


def test_steps(sut, my_os, globals_vars, local_vars):
    # type: (SUT, GenericOS) -> None
    Case.prepare('boot to OS & launch itp')
    boot_to(sut, sut.default_os)
    itp = PythonsvSemiStructured(sut.socket_name, globals_vars, local_vars)
    itp.execute('unlock()')

    Case.step("Check UPI link detail")
    MultiSocket.check_upi_topology(itp)
    MultiSocket.check_upi_link_speed(itp, sut)
    MultiSocket.check_upi_s_clm(itp)
    MultiSocket.check_upi_print_error(itp)

    Case.step("exit itp link")
    itp.exit()


def clean_up(sut):
    cleanup.default_cleanup(sut)


def test_main(globals_vars, local_vars):
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
        test_steps(sut, my_os, globals_vars, local_vars)

    except Exception as e:
        Result.get_exception(e, str(traceback.format_exc()))
    finally:
        Case.end()
        clean_up(sut)


if __name__ == '__main__':
    test_main(globals(), locals())
    exit(Result.returncode)
