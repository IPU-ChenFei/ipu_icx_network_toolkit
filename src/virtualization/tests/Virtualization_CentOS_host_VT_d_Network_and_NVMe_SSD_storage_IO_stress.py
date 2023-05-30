"""
Case Link: https://hsdes.intel.com/appstore/article/#/1509884014
"""
from src.virtualization.lib.tkinit import *

CASE_DESC = [
    'Purpose of this test case is to run the n/w and storage stress workload on CentOS Host.'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    sutos = ParameterParser.parse_parameter("sutos")
    conn = ParameterParser.parse_parameter("conn")
    valos = val_os(sutos)

    sut1 = sut
    sut2 = get_sut_list()[1]
    conn = nic_config(sut1, sut2, conn)

    Case.prepare("prepare steps")
    boot_to(sut1, sut1.default_os)
    Case.wait_and_expect('wait for restoring sut2 ssh connection', 60 * 5, sut2.check_system_in_os)

    Case.step("set ipv4")
    valos.ip_assign(conn)

    Case.step("run fio")
    res = sut1.execute_shell_cmd("ls -l /sys/class/block/")[1]
    res1 = log_check.find_lines("nvme1n1p1", res)
    res2 = log_check.find_lines("nvme1n1p2", res)
    Case.expect(f"{res1} {res2}", res1 and res2)
    fio_cmd = "fio -filename=/dev/nvme0n1p1-direct=1 -iodepth 1 -thread -rw=randread -ioengine=psync -bs=4k -size=10G " \
              "-numjobs=50 -runtime=180 -group_reporting -name=rand_100read_4k "
    sut1.execute_shell_cmd(fio_cmd)

    Case.step("running iperf3 on two suts")
    valos.iperf_stress(600, 'tcp', conn)


def clean_up(sut):
    pass
    # if Result.returncode != 0:
    #     cleanup.to_s5(sut)


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
