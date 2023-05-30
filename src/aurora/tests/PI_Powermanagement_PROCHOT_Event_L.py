# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.lib.toolkit.auto_api import *
from src.lib.toolkit.infra.xtp.itp import PythonsvSemiStructured
from src.lib.toolkit.steps_lib.cleanup import default_cleanup
from src.aurora.lib.aurora import PTU_PATH
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to

CASE_DESC = [
    'https://hsdes.intel.com/appstore/article/#/18016910207'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    Case.prepare('Boot to Default os')
    boot_to(sut, sut.default_os)
    itp = PythonsvSemiStructured(sut.socket_name, globals(), locals())

    Case.step('Monitor the cpu using ptu tool')
    ret, _, _ = sut.execute_shell_cmd('./ptu -mon -t 600', 800, cwd=PTU_PATH)
    Case.expect('run ptu tool successfully', ret == 0)

    Case.step('run ptu stress for 10 min after 2 min idle')
    Case.sleep(2 * 60)
    ret, _, _ = sut.execute_shell_cmd('./ptu -ct 3 -t 600', 800, cwd=PTU_PATH)
    Case.expect('run ptu tool successfully', ret == 0)

    Case.step('Check the status before triggering PROCHOT')
    itp.execute('unlock()')
    itp.execute('sls()')
    socket0_prochot = itp.execute('print(sv.socket0.uncore.punit.package_therm_status.prochot_status)')
    socket1_prochot = itp.execute('print(sv.socket1.uncore.punit.package_therm_status.prochot_status)')
    Case.expect('prochot_status all should be 0x0', socket0_prochot == '0x0' and socket1_prochot == '0x0')

    Case.step('Trigger the PROCHOT')
    itp.execute('sv.socket0.uncore.pcodeio_map.io_hw_signals_override.prochot_hw_inject=1')
    itp.execute('sv.socket1.uncore.pcodeio_map.io_hw_signals_override.prochot_hw_inject=1')

    Case.step('Check the status of PROCHOT for socket 0 and Socket 1')
    socket0_prochot = itp.execute('print(sv.socket0.uncore.punit.package_therm_status.prochot_status)')
    socket1_prochot = itp.execute('print(sv.socket1.uncore.punit.package_therm_status.prochot_status)')
    Case.expect('prochot_status all should be 0x0', socket0_prochot == '0x1' and socket1_prochot == '0x1')

    Case.step('Restore setting')
    itp.execute('sv.socket0.uncore.pcodeio_map.io_hw_signals_override.prochot_hw_inject=0')
    itp.execute('sv.socket1.uncore.pcodeio_map.io_hw_signals_override.prochot_hw_inject=0')
    socket0_prochot = itp.execute('print(sv.socket0.uncore.punit.package_therm_status.prochot_status)')
    socket1_prochot = itp.execute('print(sv.socket1.uncore.punit.package_therm_status.prochot_status)')
    Case.expect('prochot_status all should be 0x0', socket0_prochot == '0x0' and socket1_prochot == '0x0')


def clean_up(sut):
    default_cleanup(sut)


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
