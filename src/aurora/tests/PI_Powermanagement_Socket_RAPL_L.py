import re

# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.lib.toolkit.auto_api import *
from src.lib.toolkit.steps_lib.cleanup import default_cleanup
from src.aurora.lib.aurora import PMUTIL_BIN_PATH, kill_process, MLC_PATH
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to

CASE_DESC = [
    'https://hsdes.intel.com/appstore/article/#/18016910041, Test case steps are not clear',
    'Suggest to refer: https://hsdes.intel.com/appstore/article/#/18014889199'
]

STRESS_DURATION = 3600


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
    socket_tdp = re.findall(r'Socket\d TDP: (\d+)W', stdout)
    socket_max_pkg_pwr = re.findall(r'Socket\d Max_pkg_pwr: (\d+)W', stdout)
    socket_min_pkg_pwr = re.findall(r'Socket\d Min_pkg_pwr: (\d+)W', stdout)
    socket_pl1 = re.findall(r'Socket\d PL1: (\d+)W', stdout)
    socket_pl2 = re.findall(r'Socket\d PL2: (\d+)W', stdout)

    for index in range(len(socket_tdp)):
        logger.debug(f'socket{index} TDP is {socket_tdp[index]}W')
        logger.debug(f'socket{index} max package power is {socket_max_pkg_pwr[index]}W')
        logger.debug(f'socket{index} min package power is {socket_min_pkg_pwr[index]}W')
        logger.debug(f'socket{index} power limit1 is {socket_pl1[index]}W')
        logger.debug(f'socket{index} power limit2 is {socket_pl2[index]}W')
        Case.expect(f'socket{index} TDP is larger than socket{index} min package power',
                    int(socket_tdp[index]) > int(socket_min_pkg_pwr[index]))
        Case.expect(f'socket{index} TDP is smaller than socket{index} max package power',
                    int(socket_tdp[index]) < int(socket_max_pkg_pwr[index]))
        Case.expect(f'socket{index} power limit2 equal socket{index} power limit1 * 1.2',
                    int(socket_pl2[index]) == int(socket_pl1[index]) * 1.2)

    Case.step('run mlc stress')
    kill_process(sut, 'mlc')
    sut.execute_shell_cmd_async(f'./mlc --loaded_latency -W5 -d0 -t{STRESS_DURATION}', cwd=MLC_PATH)

    Case.step('check socket power, clip reason and perf status')
    _, socket0_perf, _ = sut.execute_shell_cmd('./pmutil_bin -S 0 -rapl_perf', cwd=PMUTIL_BIN_PATH)
    socket0_old_perf = socket0_perf.strip().split(' ')[2]
    _, socket1_perf, _ = sut.execute_shell_cmd('./pmutil_bin -S 1 -rapl_perf', cwd=PMUTIL_BIN_PATH)
    socket1_old_perf = socket1_perf.strip().split(' ')[2]
    while is_mlc_tool_alive(sut):
        # check socket power
        ret, stdout, stderr = sut.execute_shell_cmd('./pmutil_bin -power_dump', cwd=PMUTIL_BIN_PATH)
        power = stdout.split(',')
        cur_pkg0_power = power[0].split()[2]
        cur_pkg1_power = power[2].split()[2]
        Case.expect(
            f'current socket0 package power {cur_pkg0_power} is smaller than PL2 {socket_pl2[0]}',
            int(socket_pl2[0]) > float(cur_pkg0_power))
        Case.expect(
            f'current socket1 package power {cur_pkg1_power} is smaller than PL2 {socket_pl2[1]}',
            int(socket_pl2[1]) > float(cur_pkg1_power))

        # check perf status
        _, socket0_perf, _ = sut.execute_shell_cmd('./pmutil_bin -S 0 -rapl_perf', cwd=PMUTIL_BIN_PATH)
        socket0_new_perf = socket0_perf.strip().split(' ')[2]
        _, socket1_perf, _ = sut.execute_shell_cmd('./pmutil_bin -S 1 -rapl_perf', cwd=PMUTIL_BIN_PATH)
        socket1_new_perf = socket1_perf.strip().split(' ')[2]
        Case.expect(f'socket0 new perf {socket0_new_perf} is larger than dram0 old perf {socket0_old_perf}',
                    int(socket0_new_perf, 16) > int(socket0_old_perf, 16))
        Case.expect(f'socket1 new perf {socket1_new_perf} is larger than dram1 old perf {socket1_old_perf}',
                    int(socket1_new_perf, 16) > int(socket1_old_perf, 16))
        socket0_old_perf = socket0_new_perf
        socket1_old_perf = socket1_new_perf

    Case.step('set power limit1 to package min power')
    Case.sleep(120)
    sut.execute_shell_cmd(f'./pmutil_bin -set_pl1 {socket_min_pkg_pwr[index]}', cwd=PMUTIL_BIN_PATH)
    ret, stdout, stderr = sut.execute_shell_cmd('./pmutil_bin -i', cwd=PMUTIL_BIN_PATH)
    socket_pl1_new = re.findall(r'Socket\d PL1: (\d+)W', stdout)
    Case.expect('current PL1 equal package min power',
                socket_pl1_new[0] == socket_min_pkg_pwr[0] and socket_pl1_new[0] == socket_min_pkg_pwr[1])

    Case.step('run mlc stress')
    kill_process(sut, 'mlc')
    sut.execute_shell_cmd_async(f'./mlc --loaded_latency -W5 -d0 -t{STRESS_DURATION}', cwd=MLC_PATH)

    Case.step('check socket power, clip reason and perf status')
    _, socket0_perf, _ = sut.execute_shell_cmd('./pmutil_bin -S 0 -rapl_perf', cwd=PMUTIL_BIN_PATH)
    socket0_old_perf = socket0_perf.strip().split(' ')[2]
    _, socket1_perf, _ = sut.execute_shell_cmd('./pmutil_bin -S 1 -rapl_perf', cwd=PMUTIL_BIN_PATH)
    socket1_old_perf = socket1_perf.strip().split(' ')[2]
    while is_mlc_tool_alive(sut):
        # check socket power
        ret, stdout, stderr = sut.execute_shell_cmd('./pmutil_bin -power_dump', cwd=PMUTIL_BIN_PATH)
        power = stdout.split(',')
        cur_pkg0_power = power[0].split()[2]
        cur_pkg1_power = power[2].split()[2]
        Case.expect(
            f'current socket0 package power {cur_pkg0_power} is close to socket0 power limit1 {socket_pl1_new[0]}',
            int(socket_pl1_new[0]) + 30 > float(cur_pkg0_power) > int(socket_pl1_new[0]) - 30)
        Case.expect(
            f'current socket1 package power {cur_pkg1_power} is close to socket1 power limit1 {socket_pl1_new[1]}',
            int(socket_pl1_new[1]) + 30 > float(cur_pkg1_power) > int(socket_pl1_new[1]) - 30)

        # check clip reason
        ret, stdout, stderr = sut.execute_shell_cmd('./pmutil_bin -C', cwd=PMUTIL_BIN_PATH)
        Case.expect(f'clip reason is CLIPPED_PBM or CLIPPED_AVX', 'CLIPPED_PBM' in stdout or 'CLIPPED_AVX' in stdout)

        # check perf status
        _, socket0_perf, _ = sut.execute_shell_cmd('./pmutil_bin -S 0 -rapl_perf', cwd=PMUTIL_BIN_PATH)
        socket0_new_perf = socket0_perf.strip().split(' ')[2]
        _, socket1_perf, _ = sut.execute_shell_cmd('./pmutil_bin -S 1 -rapl_perf', cwd=PMUTIL_BIN_PATH)
        socket1_new_perf = socket1_perf.strip().split(' ')[2]
        Case.expect(f'socket0 new perf {socket0_new_perf} is larger than dram0 old perf {socket0_old_perf}',
                    int(socket0_new_perf, 16) > int(socket0_old_perf, 16))
        Case.expect(f'socket1 new perf {socket1_new_perf} is larger than dram1 old perf {socket1_old_perf}',
                    int(socket1_new_perf, 16) > int(socket1_old_perf, 16))
        socket0_old_perf = socket0_new_perf
        socket1_old_perf = socket1_new_perf

    Case.step('restore PL1 setting')
    sut.execute_shell_cmd(f'./pmutil_bin -set_pl1 {socket_pl1[0]}', cwd=PMUTIL_BIN_PATH)

    Case.step('set power limit2 to package min power')
    Case.sleep(120)
    sut.execute_shell_cmd(f'./pmutil_bin -set_pl2 {socket_min_pkg_pwr[index]}', cwd=PMUTIL_BIN_PATH)
    ret, stdout, stderr = sut.execute_shell_cmd('./pmutil_bin -i', cwd=PMUTIL_BIN_PATH)
    socket_pl2_new = re.findall(r'Socket\d PL2: (\d+)W', stdout)
    Case.expect('current PL2 equal package min power',
                socket_pl2_new[0] == socket_min_pkg_pwr[0] and socket_pl2_new[1] == socket_min_pkg_pwr[1])

    Case.step('run mlc stress')
    kill_process(sut, 'mlc')
    sut.execute_shell_cmd_async(f'./mlc --loaded_latency -W5 -d0 -t{STRESS_DURATION}', cwd=MLC_PATH)

    Case.step('check socket power, clip reason and perf status')
    _, socket0_perf, _ = sut.execute_shell_cmd('./pmutil_bin -S 0 -rapl_perf', cwd=PMUTIL_BIN_PATH)
    socket0_old_perf = socket0_perf.strip().split(' ')[2]
    _, socket1_perf, _ = sut.execute_shell_cmd('./pmutil_bin -S 1 -rapl_perf', cwd=PMUTIL_BIN_PATH)
    socket1_old_perf = socket1_perf.strip().split(' ')[2]
    while is_mlc_tool_alive(sut):
        # check socket power
        ret, stdout, stderr = sut.execute_shell_cmd('./pmutil_bin -power_dump', cwd=PMUTIL_BIN_PATH)
        power = stdout.split(',')
        cur_pkg0_power = power[0].split()[2]
        cur_pkg1_power = power[2].split()[2]
        Case.expect(
            f'current socket0 package power {cur_pkg0_power} is close to socket0 power limit2 {socket_pl2_new[0]}',
            int(socket_pl2_new[0]) + 30 > float(cur_pkg0_power) > int(socket_pl2_new[0]) - 30)
        Case.expect(
            f'current socket1 package power {cur_pkg1_power} is close to socket1 power limit2 {socket_pl2_new[1]}',
            int(socket_pl2_new[1]) + 30 > float(cur_pkg1_power) > int(socket_pl2_new[1]) - 30)

        # check clip reason
        ret, stdout, stderr = sut.execute_shell_cmd('./pmutil_bin -C', cwd=PMUTIL_BIN_PATH)
        Case.expect(f'clip reason is CLIPPED_PBM or CLIPPED_AVX', 'CLIPPED_PBM' in stdout or 'CLIPPED_AVX' in stdout)

        # check perf status
        _, socket0_perf, _ = sut.execute_shell_cmd('./pmutil_bin -S 0 -rapl_perf', cwd=PMUTIL_BIN_PATH)
        socket0_new_perf = socket0_perf.strip().split(' ')[2]
        _, socket1_perf, _ = sut.execute_shell_cmd('./pmutil_bin -S 1 -rapl_perf', cwd=PMUTIL_BIN_PATH)
        socket1_new_perf = socket1_perf.strip().split(' ')[2]
        Case.expect(f'socket0 new perf {socket0_new_perf} is larger than dram0 old perf {socket0_old_perf}',
                    int(socket0_new_perf, 16) > int(socket0_old_perf, 16))
        Case.expect(f'socket1 new perf {socket1_new_perf} is larger than dram1 old perf {socket1_old_perf}',
                    int(socket1_new_perf, 16) > int(socket1_old_perf, 16))
        socket0_old_perf = socket0_new_perf
        socket1_old_perf = socket1_new_perf

    Case.step('restore PL2 setting')
    sut.execute_shell_cmd(f'./pmutil_bin -set_pl2 {socket_pl2[0]}', cwd=PMUTIL_BIN_PATH)


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
