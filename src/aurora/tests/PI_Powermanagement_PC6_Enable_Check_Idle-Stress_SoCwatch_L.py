import os

# noinspection PyUnresolvedReferences
import set_toolkit_src_root

from src.aurora.lib.aurora import PTU_PATH, SOCWATCH_PATH, SocWatchLog
from src.lib.toolkit.auto_api import *
from src.lib.toolkit.steps_lib.bios_knob import set_bios_knobs_step
from src.lib.toolkit.steps_lib.cleanup import default_cleanup
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to

CASE_DESC = [
    'https://hsdes.intel.com/appstore/article/#/18014075677',
]

STRESS_TIME = 15


def run_stress(sut):
    Case.step('kill old process')
    sut.execute_shell_cmd('./killptu.sh', cwd=PTU_PATH)

    Case.step('start stress tool')
    sut.execute_shell_cmd_async('./ptu -ct 3', cwd=PTU_PATH)
    # wait for stress tool boot up
    Case.sleep(60)

    Case.step(f'run socwatch for {STRESS_TIME} min')
    sut.execute_shell_cmd(f'./socwatch --update-usage-consent no', timeout=30, cwd=SOCWATCH_PATH)
    sut.execute_shell_cmd(f'./socwatch --skip-usage-collection -m -f cpu-pstate -f cpu-cstate -t {STRESS_TIME * 60}',
                          timeout=STRESS_TIME * 60 * 1.5, cwd=SOCWATCH_PATH)


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    Case.prepare('Boot to Default os & Cstate Enable')
    boot_to(sut, sut.default_os)
    set_bios_knobs_step(sut, *bios_knob('enable_PM_CState_auto_xmlcli'), *bios_knob('enable_PM_monitor_mwait_xmlcli'),
                        *bios_knob('enable_PM_C6_report_xmlcli'))
    Case.sleep(120)
    sut.execute_shell_cmd('./killptu.sh', cwd=PTU_PATH)

    Case.step(f'run socwatch for {STRESS_TIME} min')
    sut.execute_shell_cmd(f'./socwatch --update-usage-consent no', timeout=30, cwd=SOCWATCH_PATH)
    sut.execute_shell_cmd(f'./socwatch --skip-usage-collection -m -f cpu-pstate -f cpu-cstate -t {STRESS_TIME * 60}',
                          timeout=STRESS_TIME * 60 * 1.5, cwd=SOCWATCH_PATH)

    Case.step('download log file and check log')
    sut.download_to_local(remotepath=f'{SOCWATCH_PATH}/SoCWatchOutput.csv',
                          localpath=os.path.join(LOG_PATH, 'cstate_enable_idle', 'SoCWatchOutput.csv'))
    log_data = SocWatchLog.get_cstate_cc6(os.path.join(LOG_PATH, 'cstate_enable_idle', 'SoCWatchOutput.csv'))
    logger.debug(f'get cstate cc6 data: {log_data}')
    for key, value in log_data.items():
        Case.expect(f'{key} cc6 value is {value}% > 85%', float(value) > 85)

    # run stress test to check CC0 value
    run_stress(sut)

    Case.step('download log file and check log')
    sut.download_to_local(remotepath=f'{SOCWATCH_PATH}/SoCWatchOutput.csv',
                          localpath=os.path.join(LOG_PATH, 'cstate_enable_stress', 'SoCWatchOutput.csv'))
    log_data = SocWatchLog.get_cstate_cc0(os.path.join(LOG_PATH, 'cstate_enable_stress', 'SoCWatchOutput.csv'))
    logger.debug(f'get cstate cc0 data: {log_data}')
    for key, value in log_data.items():
        Case.expect(f'{key} cc0 value is {value}% > 90%', float(value) > 90)

    Case.step('Cstate disable')
    set_bios_knobs_step(sut, *bios_knob('enable_PM_CState_C0_C1_state_xmlcli'),
                        *bios_knob('disable_PM_monitor_mwait_xmlcli'),
                        *bios_knob('disable_PM_C6_report_xmlcli'))
    # wait for OS stable
    Case.sleep(120)

    Case.step(f'run socwatch for 10 min')
    sut.execute_shell_cmd(f'./socwatch --update-usage-consent no', timeout=30, cwd=SOCWATCH_PATH)
    sut.execute_shell_cmd(f'./socwatch --skip-usage-collection -m -f cpu-pstate -f cpu-cstate -t {10 * 60}',
                          timeout=10 * 60 * 1.5, cwd=SOCWATCH_PATH)

    Case.step('download log file and check log')
    sut.download_to_local(remotepath=f'{SOCWATCH_PATH}/SoCWatchOutput.csv',
                          localpath=os.path.join(LOG_PATH, 'cstate_disable', 'SoCWatchOutput.csv'))
    log_data = SocWatchLog.get_cstate_cc1(os.path.join(LOG_PATH, 'cstate_disable', 'SoCWatchOutput.csv'))
    logger.debug(f'get cstate cc1 data: {log_data}')
    for key, value in log_data.items():
        Case.expect(f'{key} cc1 value is {value}% > 90%', float(value) > 90)


def clean_up(sut):
    sut.execute_shell_cmd('./killptu.sh', cwd=PTU_PATH)

    sut.restore_bios_defaults_xmlcli(sut.SUT_PLATFORM)

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
