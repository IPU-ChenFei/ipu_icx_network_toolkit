#from src.lib.toolkit.auto_api import *
#from sys import exit
#from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to
#from src.mev.lib.mev import MEVOp, MEVConn
#from src.mev.lib.utility import get_core_list, iperf3_data_conversion
#from src.lib.toolkit.infra.sut import get_sut_list
#from src.configuration.config.sut_tool.egs_sut_tools import SUT_TOOLS_LINUX_MEV
#import os
#import re
from src.network.lib import *

CASE_DESC = [
    # TODO  iperf implementation
    'case name here',
    # list the name of those cases which are expected to be executed before this case
    '<dependencies: if any>'
]


def iperf_test(conn: MEVConn, direction, queue, rx, tx, num_thread, duration=3600):
    MEVOp.perf_prepare(conn, direction, queue, rx, tx)

    server = conn.port1.xhc
    client = conn.port2.xhc
    sut1 = server.sut
    sut2 = client.sut
    core_list1 = get_core_list(sut1)
    core_list2 = get_core_list(sut2)

    log_folder_name = 'iperf_' + direction + '_log'
    remote_folder_path = '/root/' + log_folder_name

    server_cmd = f'taskset -c {core_list1[2]}-{core_list1[2] + num_thread} iperf -B {server.ip_v4} -p 5201 -s -i 2'

    client_cmd = f'taskset -c {core_list2[2]}-{core_list2[2] + num_thread} ' \
                 f'iperf -c {client.ip_v4} -p 5201 -P {num_thread} -t {duration} -i 2'

    Case.step(f'-----------kill all iperf server process-----------')
    _, stdout, _ = sut1.execute_shell_cmd(rf'ps -e | grep iperf', 30)
    if stdout != '':
        sut1.execute_shell_cmd(f'kill -9 $(pidof iperf)')

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
    if direction == 'unidirectional':
        Case.step(f'-----------start {direction} iperf server on sut1-----------')
        log_file = f'{remote_folder_path}/server.txt'
        sut1.execute_shell_cmd_async(f'{server_cmd[direction]} > {log_file}', timeout=30)

        logger.info(f'-----------start {direction} iperf client on sut2-----------')
        log_file = f'{remote_folder_path}/client.txt'
        sut2.execute_shell_cmd_async(f'{client_cmd[direction]} > {log_file}', timeout=30)
    else:
        Case.step(f'-----------start {direction} iperf server on sut1 and sut2-----------')
        log_file = f'{remote_folder_path}/server.txt'
        sut1.execute_shell_cmd_async(f'{server_cmd[direction]} > {log_file}', timeout=30)
        sut2.execute_shell_cmd_async(f'{server_cmd[direction]} > {log_file}', timeout=30)

        logger.info(f'-----------start {direction} iperf client on sut2 and sut1-----------')
        log_file = f'{remote_folder_path}/client.txt'
        sut2.execute_shell_cmd_async(f'{client_cmd[direction]} > {log_file}', timeout=30)
        sut1.execute_shell_cmd_async(f'{client_cmd[direction]} > {log_file}', timeout=30)

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
    with open(f'{os.path.join(LOG_PATH, log_folder_name)}\\client.txt', 'r') as fs:
        data = fs.read()
        receiver_str = re.findall(r'[SUM].*sec(.*/sec).*', data)[0]
        receiver_data = re.split(r'\s+', receiver_str.strip())
        bandwidth = float(receiver_data[2])
        bandwidth_unit = receiver_data[3]

    bandwidth = iperf3_data_conversion(bandwidth, bandwidth_unit[0], 'G')

    logger.info(f'iperf total bandwidth = {bandwidth} Gbits/sec')

    criterion = {
        'unidirectional': 200 * 0.9,
        'bidirectional': 400 * 0.9,
    }

    Case.expect(f'test iperf {direction} stress pass', bandwidth > criterion[direction])


def test_steps(sut_list, my_os):
    sut1, sut2 = sut_list
    conn = MEVConn(sut1, sut2)
    mev1 = conn.port1
    mev2 = conn.port2
    try:
        boot_to(sut1, sut1.default_os)
        boot_to(sut2, sut2.default_os)

        conn.bring_up()
        conn.connect()

        # Step1 - Pass all traffic for XHC
        Case.step('Pass all traffic for XHC')
        mev1.pass_xhc_traffic()
        mev2.pass_xhc_traffic()

        # Step2 - Run TCP stress with MEV
        Case.step('start ipef performance test')
        iperf_test(conn, direction='unidirectional', queue=16, rx=1024, tx=1024, num_thread=20, duration=3600)
        iperf_test(conn, direction='bidirectional', queue=16, rx=1024, tx=1024, num_thread=20, duration=3600)

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
