#from src.lib.toolkit.auto_api import *
#from sys import exit
#from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to
#from src.mev.lib.mev import MEVOp, MEVConn
from src.network.lib import *
#from src.mev.lib.utility import get_core_list, iperf3_data_conversion
#from src.lib.toolkit.infra.sut import get_sut_list
#from src.configuration.tkconfig.sut_tool.egs_sut_tools import SUT_TOOLS_LINUX_MEV
#from tkconfig import sut_tool

#import os
#import re


CASE_DESC = [
    'LAN Netperf TCP_STREAM Throughput',
    # list the name of those cases which are expected to be executed before this case
    '<dependencies: sut <=> sut >'
]


def neper_test(conn: MEVConn, direction, queue, rx, tx, num_thread, duration=3600):
    MEVOp.perf_prepare(conn, direction, queue, rx, tx)

    server = conn.port1.xhc
    client = conn.port2.xhc
    sut1 = server.sut
    sut2 = client.sut
    core_list1 = get_core_list(sut1)
    core_list2 = get_core_list(sut2)

    log_folder_name = 'neper_' + direction + '_log'
    remote_folder_path = '/root/' + log_folder_name
    server_cmd = {
        'unidirectional': f'taskset -c {core_list1[2]}-{core_list1[2] + num_thread}'
                          f' ./tcp_stream --nolog -T {num_thread} -F 200 -B 81920 -l {duration}',
        'bidirectional': f'taskset -c {core_list1[2]}-{core_list1[2] + 15}'
                         f' ./tcp_stream --nolog -T {num_thread} -F 200 -B 81920 -l {duration} -w'
    }

    client_cmd = {
        'unidirectional': f'taskset -c {core_list2[2]}-{core_list2[2] + 15}'
                          f'./tcp_stream --nolog -c -H {server.ip_v4} -T {num_thread} -F 200 -B 81920 -l {duration}',
        'bidirectional': f'taskset -c {core_list2[2]}-{core_list2[2] + 15}'
                         f' ./tcp_stream --nolog -c -H {server.ip_v4} -T {num_thread} -F 200 -B 81920 -l {duration} -r'
    }

    Case.step(f'-----------kill all neper server process-----------')
    _, stdout, _ = sut1.execute_shell_cmd(rf'ps -e | grep tcp_steam', 30)
    if stdout != '':
        sut1.execute_shell_cmd(f'kill -9 $(pidof tcp_steam)')

    # create new log folder for running perf in sut
    exit_code, stdout, stderr = sut1.execute_shell_cmd(f'mkdir {remote_folder_path}')
    if exit_code == 1 and 'exist' in stderr:
        OperationSystem[OS.get_os_family(sut1.default_os)].remove_folder(sut1, remote_folder_path)
        sut1.execute_shell_cmd(f'mkdir {remote_folder_path}')
    exit_code, stdout, stderr = sut2.execute_shell_cmd(f'mkdir {remote_folder_path}')
    if exit_code == 1 and 'exist' in stderr:
        OperationSystem[OS.get_os_family(sut2.default_os)].remove_folder(sut2, remote_folder_path)
        sut2.execute_shell_cmd(f'mkdir {remote_folder_path}')

    # start to run perf test
    Case.step(f'-----------start {direction} neper server on sut1-----------')
    log_file = f'{remote_folder_path}/server.txt'
    sut1.execute_shell_cmd_async(f'{server_cmd[direction]} > {log_file}',
                                 timeout=30, cwd=f'{SUT_TOOLS_LINUX_MEV}/neper_master')

    logger.info(f'-----------start {direction} neper client on sut2-----------')
    log_file = f'{remote_folder_path}/client.txt'
    sut2.execute_shell_cmd_async(f'{client_cmd[direction]} > {log_file}',
                                 timeout=30, cwd=f'{SUT_TOOLS_LINUX_MEV}/neper_master')

    # wait for finish transfer
    if duration >= 60 * 5:
        sleep_time = duration + 90
    else:
        sleep_time = duration * 1.2
    Case.sleep(sleep_time)

    # download log file to check result
    sut1.download_to_local(remote_folder_path, LOG_PATH)
    sut2.download_to_local(remote_folder_path, LOG_PATH)

    # calc sum of transfer and bandwith
    with open(f'{os.path.join(LOG_PATH, log_folder_name)}\\server.txt', 'r') as fs:
        data = fs.read()
        bandwidth_l = float(re.findall(r'local_throughput=([0-9]*)', data)[0])
        bandwidth_r = float(re.findall(r'remote_throughput=([0-9]*)', data)[0])
        bandwidth = bandwidth_l + bandwidth_r
        bandwidth_unit = 'bit/s'

    bandwidth = iperf3_data_conversion(bandwidth, bandwidth_unit[0], 'G')

    logger.info(f'neper total bandwidth = {bandwidth} Gbits/sec')

    criterion = {
        'unidirectional': 200 * 0.9,
        'bidirectional': 400 * 0.9,
    }

    Case.expect(f'test neper {direction} stress pass', bandwidth > criterion[direction])


def test_steps(sut_list, my_os):
    sut1, sut2 = sut_list
    conn = MEVConn(sut1, sut2)
    mev1 = conn.port1
    mev2 = conn.port2
    try:
        # Boot server and client. Connect them.
        boot_to(sut1, sut1.default_os)
        boot_to(sut2, sut2.default_os)

        conn.bring_up()
        conn.connect()
        # pass traffic between sut1 and sut2
        mev1.pass_xhc_traffic()
        mev2.pass_xhc_traffic()

        # Neper performance test and throughput
        Case.step('Run neper performace test and check throughput')
        neper_test(conn, direction='unidirectional', queue=16, rx=1024, tx=1024, num_thread=20, duration=3600)
        neper_test(conn, direction='bidirectional', queue=16, rx=1024, tx=1024, num_thread=20, duration=3600)
    except Exception as e:
        raise e
    finally:
        MEVOp.clean_up(conn)


def clean_up(sut):
    pass


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
    sut_list = get_sut_list()
    sut = sut_list[0]
    my_os = OperationSystem[OS.get_os_family(sut.default_os)]

    try:
        Case.start(sut, CASE_DESC)
        test_steps(sut_list, my_os)

    except Exception as e:
        Result.get_exception(e, str(traceback.format_exc()))
    finally:
        Case.end()
        clean_up(sut)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)
