# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.lib.toolkit.auto_api import *
from src.lib.toolkit.steps_lib.bios_knob import set_bios_knobs_step, restore_bios_defaults_xmlcli_step
from src.lib.toolkit.steps_lib.cleanup import default_cleanup
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to

CASE_DESC = [
    'https://hsdes.intel.com/appstore/article/#/18014074404'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    Case.prepare('Boot to Default os')
    boot_to(sut, sut.default_os)

    # Case.step('check memory frequency 4000')
    # set_bios_knobs_step(sut, *bios_knob('enable_MemoryFrequency4000_xmlcli'))
    # ret, stdout, _ = sut.execute_shell_cmd(
    #     "dmidecode -t 17|grep 'Configured Memory Speed'|awk -F ':' '{print $2}'|awk -F ' ' '{print $1}'")
    # stdout = stdout.strip().split('\n')
    # for frequency in stdout:
    #     frequency = int(frequency.strip())
    #     Case.expect('Configure d Memory Speed = 4000 MT/S', frequency == 4000)

    Case.step('check memory frequency 4400')
    set_bios_knobs_step(sut, *bios_knob('enable_MemoryFrequency4400_xmlcli'))
    ret, stdout, _ = sut.execute_shell_cmd(
        "dmidecode -t 17|grep 'Configured Memory Speed'|awk -F ':' '{print $2}'|awk -F ' ' '{print $1}'")
    stdout = stdout.strip().split('\n')
    for frequency in stdout:
        Case.expect(' Configured Memory Speed = 4400 MT/S', int(frequency.strip()) == 4400)

    Case.step('check memory frequency 4800')
    set_bios_knobs_step(sut, *bios_knob('enable_MemoryFrequency4800_xmlcli'))
    ret, stdout, _ = sut.execute_shell_cmd(
        "dmidecode -t 17|grep 'Configured Memory Speed'|awk -F ':' '{print $2}'|awk -F ' ' '{print $1}'")
    stdout = stdout.strip().split('\n')
    for frequency in stdout:
        Case.expect(' Configured Memory Speed = 4800 MT/S', int(frequency.strip()) == 4800)


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
