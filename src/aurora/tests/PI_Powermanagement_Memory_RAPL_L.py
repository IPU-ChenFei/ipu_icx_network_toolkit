import re

# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.lib.toolkit.auto_api import *
from src.lib.toolkit.steps_lib.cleanup import default_cleanup
from src.aurora.lib.aurora import PMUTIL_BIN_PATH, MLC_PATH, kill_process
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to

CASE_DESC = [
    'https://hsdes.intel.com/appstore/article/#/18016910039, Test case steps are not clear',
    'Suggust to refer: https://hsdes.intel.com/appstore/article/#/18014889242'
]


def is_mlc_tool_alive(sut):
    _, stdout, _ = sut.execute_shell_cmd(f'ps aux | grep mlc | grep -v grep', 30)
    if stdout != '':
        return True
    else:
        return False


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    Case.prepare('Boot to Default os')
    boot_to(sut, sut.default_os)

    Case.step('get and check DRAM TDP and DRAM MAX PWR')
    ret, stdout, stderr = sut.execute_shell_cmd('./pmutil_bin -i', cwd=PMUTIL_BIN_PATH)
    dram_tdp = re.findall(r'DRAM\d TDP: (\d+)W', stdout)
    dram_max_pwr = re.findall(r'DRAM\d Max_pwr: (\d+)W', stdout)
    for index in range(len(dram_tdp)):
        logger.debug(f'Dram{index} TDP is {dram_tdp[index]}W')
        logger.debug(f'Dram{index} max power is {dram_max_pwr[index]}W')
        Case.expect('Dram TDP is lower than Dram max power', int(dram_tdp[index]) < int(dram_max_pwr[index]))

    Case.step('set DRAM PL & enable DRAM PBM')
    ret, _, _ = sut.execute_shell_cmd('./pmutil_bin -set_dram_pl 32', cwd=PMUTIL_BIN_PATH)
    Case.expect('set dram pl successfully', ret == 0)
    ret, stdout, _ = sut.execute_shell_cmd('./pmutil_bin -dram_pbm_status', cwd=PMUTIL_BIN_PATH)
    if 'enable: 0' in stdout:
        ret, _, _ = sut.execute_shell_cmd('./pmutil_bin -dram_pbm_toggle', cwd=PMUTIL_BIN_PATH)
        Case.expect('enable Dram PBM successfully', ret == 0)
    else:
        logger.debug('Dram PBM is already enabled')

    Case.step('run mlc stress')
    kill_process(sut, 'mlc')
    sut.execute_shell_cmd_async('./mlc --loaded_latency -W5 -d0 -t600', cwd=MLC_PATH)
    Case.sleep(60)

    Case.step('check Dram power')
    ret, dram0_perf, stderr = sut.execute_shell_cmd('./pmutil_bin -S 0 -dram_perf', cwd=PMUTIL_BIN_PATH)
    dram0_old_perf = dram0_perf.strip().split(' ')[2]
    ret, dram1_perf, stderr = sut.execute_shell_cmd('./pmutil_bin -S 1 -dram_perf', cwd=PMUTIL_BIN_PATH)
    dram1_old_perf = dram1_perf.strip().split(' ')[2]
    while is_mlc_tool_alive(sut):
        ret, dram0_perf, stderr = sut.execute_shell_cmd('./pmutil_bin -S 0 -dram_perf', cwd=PMUTIL_BIN_PATH)
        dram0_new_perf = dram0_perf.strip().split(' ')[2]
        ret, dram1_perf, stderr = sut.execute_shell_cmd('./pmutil_bin -S 1 -dram_perf', cwd=PMUTIL_BIN_PATH)
        dram1_new_perf = dram1_perf.strip().split(' ')[2]

        logger.debug(f'dram0 new perf is {dram0_new_perf} and dram0 old perf is {dram0_old_perf}')
        Case.expect('dram0 new perf is larger than dram0 old perf', int(dram0_new_perf, 16) > int(dram0_old_perf, 16))
        logger.debug(f'dram1 new perf is {dram1_new_perf} and dram1 old perf is {dram1_old_perf}')
        Case.expect('dram1 new perf is larger than dram1 old perf', int(dram1_new_perf, 16) > int(dram1_old_perf, 16))

        dram0_old_perf = dram0_new_perf
        dram1_old_perf = dram1_new_perf


def clean_up(sut):
    sut.execute_shell_cmd('./pmutil_bin -set_dram_pl 0', cwd=PMUTIL_BIN_PATH)
    ret, stdout, _ = sut.execute_shell_cmd('./pmutil_bin -dram_pbm_status', cwd=PMUTIL_BIN_PATH)
    if 'enable: 1' in stdout:
        sut.execute_shell_cmd('./pmutil_bin -dram_pbm_toggle', cwd=PMUTIL_BIN_PATH)
    kill_process(sut, 'mlc')

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
