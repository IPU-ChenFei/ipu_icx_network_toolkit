# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.lib.toolkit.auto_api import *
from src.lib.toolkit.infra.xtp.itp import PythonsvSemiStructured
from src.lib.toolkit.steps_lib.bios_knob import set_bios_knobs_step, restore_bios_defaults_xmlcli_step
from src.lib.toolkit.steps_lib.cleanup import default_cleanup
from src.aurora.lib.aurora import DMIDECODE_PATH, MEMORY_SIZE, MLC_PATH
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to

CASE_DESC = [
    'https://hsdes.intel.com/appstore/article/#/1509819385'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    Case.prepare('Boot to Default os')
    boot_to(sut, sut.default_os)
    set_bios_knobs_step(sut, *bios_knob('disable_snc_xmlci'), *bios_knob('enable_UMA_Based_clustering_hemi_xmlci'))
    itp = PythonsvSemiStructured(sut.socket_name, globals(), locals())

    Case.step('check memory size')
    ret, stdout, _ = sut.execute_shell_cmd("./dmidecode|grep -A5 'Memory Device'|grep Size|awk -F ':' '{print $2}'",
                                           cwd=DMIDECODE_PATH)
    for size in stdout.strip().split('\n'):
        size = size.strip().split()
        size = int(size[0])
        Case.expect('memory size is correct', size == MEMORY_SIZE)

    Case.step('Verify Hemi mode is enabled')
    itp.execute('unlock()')
    out = itp.execute('print(sv.sockets.uncore.cha.cha0.ms2idi0.snc_config)')
    out = out.strip().split('\n')
    for snc_config in out:
        snc_config = snc_config.split('-')[1]
        snc_config = int(snc_config.strip(), 16)
        Case.expect('snc config must equal 0x6', snc_config == 0x6)

    Case.step('run mlc stress')
    ret, _, _ = sut.execute_shell_cmd("./mlc --peak_injection_bandwidth -Z -t3600", timeout=3600 * 5,
                                      cwd=MLC_PATH)
    Case.expect('run mlc without error', ret == 0)


def clean_up(sut):
    restore_bios_defaults_xmlcli_step(sut, sut.SUT_PLATFORM)

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
