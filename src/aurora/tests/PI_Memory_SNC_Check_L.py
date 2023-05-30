# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.lib.toolkit.auto_api import *
from src.lib.toolkit.infra.xtp.itp import PythonsvSemiStructured
from src.lib.toolkit.steps_lib.cleanup import default_cleanup
from src.aurora.lib.aurora import MLC_PATH, set_snc_via_redfish
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to

CASE_DESC = [
    'https://hsdes.intel.com/appstore/article/#/18016909612'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    Case.prepare('Boot to Default os')
    boot_to(sut, sut.default_os)
    itp = PythonsvSemiStructured(sut.socket_name, globals(), locals())

    for i in range(2):
        Case.step('set SNC mode')
        # work around for Aurora, SNC can only be set by BMC, not bios
        if i == 0:
            set_snc_via_redfish(sut, 'snc2')
        elif i == 1:
            set_snc_via_redfish(sut, 'snc4')
        my_os.warm_reset_cycle_step(sut)
        Case.sleep(60)

        Case.step('Make sure that the numbers of nodes are as expected. This is generally the number of sockets')
        itp.execute('unlock()')
        itp.execute('sls()')
        out = itp.execute('print(sv.sockets.uncore.upi.upi0.ktilk_snc_config)')
        out = out.strip().split('\n')
        for snc_config in out:
            snc_config = snc_config.split('-')[1]
            snc_config = int(snc_config.strip(), 16)

            if i == 0:
                Case.expect('snc 2 config must equal 0x000007', snc_config == 0x000007)
            elif i == 1:
                Case.expect('snc 4 config must equal 0x00000f', snc_config == 0x00000f)

        Case.step('Run mlc stress and SUT should not break during stress')
        ret, _, _ = sut.execute_shell_cmd("./mlc --peak_injection_bandwidth -Z -t3600", timeout=3600 * 5,
                                          cwd=MLC_PATH)
        Case.expect('run mlc without error', ret == 0)


def clean_up(sut):
    set_snc_via_redfish(sut, 'no')

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
