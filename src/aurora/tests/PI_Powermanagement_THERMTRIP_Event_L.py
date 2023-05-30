# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.lib.toolkit.auto_api import *
from src.lib.toolkit.infra.xtp.itp import PythonsvSemiStructured
from src.lib.toolkit.steps_lib.cleanup import default_cleanup
from src.aurora.lib.aurora import PTU_PATH
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to

CASE_DESC = [
    'https://hsdes.intel.com/appstore/article/#/18016910205'
]


def check_thermtrip_event(sut, itp, socket_index):
    Case.step('Monitor the cpu using ptu tool')
    ret, _, _ = sut.execute_shell_cmd('./ptu -mon -t 600', 800, cwd=PTU_PATH)
    Case.expect('run ptu tool successfully', ret == 0)

    Case.step('run ptu stress for 10 min after 2 min idle')
    Case.sleep(2 * 60)
    ret, _, _ = sut.execute_shell_cmd('./ptu -ct 3 -t 600', 800, cwd=PTU_PATH)
    Case.expect('run ptu tool successfully', ret == 0)

    Case.step('trigger thermtrip through')
    itp.execute('unlock()')
    itp.execute('sls()')
    if socket_index == 0:
        itp.execute('sv.socket0.taps.core_dts_d00.dtscfgfuse.dtscfg_cri_cattripcode_0=0x3f')
    elif socket_index == 1:
        itp.execute('sv.socket1.taps.core_dts_d00.dtscfgfuse.dtscfg_cri_cattripcode_0=0x3f')
    else:
        raise ValueError('Invalid socket index')
    Case.sleep(60)
    Case.expect('system shutdown', sut.get_power_status() == SUT_STATUS.S5)
    sut.dc_on()
    Case.wait_and_expect('wait for OS boot to OS', 30 * 60, sut.check_system_in_os)


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    Case.prepare('Boot to Default os')
    boot_to(sut, sut.default_os)
    itp = PythonsvSemiStructured(sut.socket_name, globals(), locals())

    check_thermtrip_event(sut, itp, socket_index=0)
    Case.sleep(120)
    check_thermtrip_event(sut, itp, socket_index=1)


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
