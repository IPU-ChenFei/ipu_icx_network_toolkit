import csv
import os

# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.lib.toolkit.auto_api import *
from src.lib.toolkit.steps_lib.bios_knob import set_bios_knobs_step, restore_bios_defaults_xmlcli_step
from src.lib.toolkit.steps_lib.cleanup import default_cleanup
from src.aurora.lib.aurora import PTU_PATH, SOCWATCH_PATH, SocWatchLog
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to

CASE_DESC = [
    'https://hsdes.intel.com/appstore/article/#/18014074402'
]

STRESS_DURATION_MIN = 15


def run_stress(sut):
    Case.step('kill old process')
    sut.execute_shell_cmd('./killptu.sh', cwd=PTU_PATH)

    Case.step('start stress tool')
    sut.execute_shell_cmd_async('./ptu -ct 3', cwd=PTU_PATH)
    # wait for stress tool boot up
    Case.sleep(60)

    Case.step(f'run socwatch for {STRESS_DURATION_MIN} min')
    sut.execute_shell_cmd(f'./socwatch --update-usage-consent no', timeout=30, cwd=SOCWATCH_PATH)
    sut.execute_shell_cmd(
        f'./socwatch --skip-usage-collection -m -f cpu-pstate -f cpu-cstate -t {STRESS_DURATION_MIN * 60}',
        timeout=STRESS_DURATION_MIN * 60 * 1.5, cwd=SOCWATCH_PATH)


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    Case.prepare('Boot to Default os')
    boot_to(sut, sut.default_os)
    set_bios_knobs_step(sut, *bios_knob('enable_PM_Turbo_mode_xmlcli'))
    Case.sleep(120)

    run_stress(sut)

    Case.step('download log file and check log')
    sut.download_to_local(remotepath=f'{SOCWATCH_PATH}/SoCWatchOutput.csv',
                          localpath=os.path.join(LOG_PATH, 'enable', 'SoCWatchOutput.csv'))
    log_data = SocWatchLog.get_pstate_p0(os.path.join(LOG_PATH, 'enable', 'SoCWatchOutput.csv'))
    logger.debug(f'get pstate p0 data: {log_data}')
    for key, value in log_data.items():
        total_residency = 0
        for residency in value:
            total_residency += float(residency)

        Case.expect(f'{key} P0 value is {total_residency} > 90%', total_residency > 90)

    Case.step('disable Turbo mode')
    set_bios_knobs_step(sut, *bios_knob('disable_PM_Turbo_mode_xmlcli'))
    # wait for OS stable
    Case.sleep(120)

    run_stress(sut)

    Case.step('download log file and check log')
    sut.download_to_local(remotepath=f'{SOCWATCH_PATH}/SoCWatchOutput.csv',
                          localpath=os.path.join(LOG_PATH, 'disable', 'SoCWatchOutput.csv'))

    log_p0_data = SocWatchLog.get_pstate_p0(os.path.join(LOG_PATH, 'disable', 'SoCWatchOutput.csv'))
    logger.debug(f'get pstate p0 data: {log_p0_data}')
    for key, value in log_p0_data.items():
        total_residency = 0
        for residency in value:
            total_residency += float(residency)

        Case.expect(f'{key} P0 value is {total_residency} < 10%', total_residency < 10)

    log_p1_data = SocWatchLog.get_pstate_p1(os.path.join(LOG_PATH, 'disable', 'SoCWatchOutput.csv'))
    logger.debug(f'get pstate p1 data: {log_p1_data}')
    for key, value in log_p1_data.items():
        Case.expect(f'{key} P1 value is {value} > 90%', float(value) > 90)


def clean_up(sut):
    sut.execute_shell_cmd('./killptu.sh', cwd=PTU_PATH)
    
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
