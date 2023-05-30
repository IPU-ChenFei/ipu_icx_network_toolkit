
from src.network.lib import *
CASE_DESC = [
    'connect sut1 network port to sut2 network port cable',
    'set ipv4 for Mellanox nic',
    'running iwvss or fio stress test by param config'
]

def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    sutos = ParameterParser.parse_parameter("sutos")
    stress = ParameterParser.parse_parameter("stress")

    sut1 = sut
    sut2 = get_sut_list()[1]

    valos = val_os(sutos)
    conns = muti_nic_config(sut1, sut2)
    Case.prepare('prepare steps')
    boot_to(sut1, sut1.default_os)
    Case.wait_and_expect('wait for restoring sut2 ssh connection', 60 * 5, sut2.check_system_in_os)

    #Case.step('Change sut1 and sut2 network interface mode to ETH mode')
    #valos.switch_infiniband_mode(sut1, "ETH")
    #valos.switch_infiniband_mode(sut2, "ETH")

    #Case.step('set mellanox card ipv4')

    valos.ip_assign(*conns)
    if stress == 'fio':
        Case.step('run fio test')
        valos.fio_stress(*conns)
    else:
        Case.step('run ixvss test')
        pkg = ParameterParser.parse_parameter("tool")
        conf = ParameterParser.parse_parameter("conf")
        flow = ParameterParser.parse_parameter("flow")

        valos.ixvss_stress(10, pkg, conf, flow, *conns)


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
