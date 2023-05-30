import os

# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.lib.toolkit.auto_api import *
from src.lib.toolkit.steps_lib.bios_knob import set_bios_knobs_step, restore_bios_defaults_xmlcli_step
from src.lib.toolkit.steps_lib.cleanup import default_cleanup
from src.aurora.lib.aurora import PTU_PATH, ptu_mon_log_check
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to

CASE_DESC = [
    'https://hsdes.intel.com/appstore/article/#/18014075558'
]


def idle_check_callback(c0_residency, c1_residency, c6_residency):
    pass


def stress_check_callback(c0_residency, c1_residency, c6_residency):
    Case.expect('C0 residency > 100%', float(c0_residency) > 90)


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    Case.prepare('Boot to Default os')
    boot_to(sut, sut.default_os)
    set_bios_knobs_step(sut, *bios_knob('enable_processor_HWP_out_of_band_xmlcli'))
    Case.sleep(120)

    Case.step('Check C6 residency in idle mode')
    ret, _, _ = sut.execute_shell_cmd('./ptu -mon -filter 0x0F -l 2 -t 60 -log -logdir . -logname idle', 90,
                                      cwd=PTU_PATH)
    Case.expect('run ptu tool successfully', ret == 0)
    sut.download_to_local(remotepath=f'{PTU_PATH}/idle_ptumon.txt')
    sut.download_to_local(remotepath=f'{PTU_PATH}/idle_ptumsg.txt')
    ptu_mon_log_check(os.path.join(LOG_PATH, 'idle_ptumon.txt'), idle_check_callback)

    Case.step('Check C1 residency in stress mode')
    Case.sleep(60)
    ret, _, _ = sut.execute_shell_cmd('./ptu -ct 3 -mon -filter 0x0F -l 2 -t 900 -log -logdir . -logname stress', 1200,
                                      cwd=PTU_PATH)
    Case.expect('run ptu tool successfully', ret == 0)
    sut.download_to_local(remotepath=f'{PTU_PATH}/stress_ptumon.txt')
    sut.download_to_local(remotepath=f'{PTU_PATH}/stress_ptumsg.txt')
    ptu_mon_log_check(os.path.join(LOG_PATH, 'stress_ptumon.txt'), stress_check_callback, 5 * 60)


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
