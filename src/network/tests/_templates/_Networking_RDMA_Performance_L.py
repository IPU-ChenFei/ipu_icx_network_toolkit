
from src.network.lib import *
CASE_DESC = [
    'connect sut1 mellanox nic port to sut2 mellanox nic port cable',
    'set Mellanox card to IB mode',
    'check mellanox RDMA Performance'
]


def compare_value(content, standard_val, type):
    for line in content.splitlines():
        ret = re.search("\d+\s+\d+\s+", line)
        if ret:
            if type == "BW":
                read_val = line.split()[3]
                Case.expect("compare ib read bw value", float(read_val) > standard_val)
            else:
                read_val = line.split()[5]
                Case.expect("compare ib read lat value", float(read_val) < standard_val)


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    sutos = ParameterParser.parse_parameter("sutos")
    conn = ParameterParser.parse_parameter("conn")
    IB_READ_BW = 6200.0 * 0.9
    IB_SEND_BW = 11000.0 * 0.9
    IB_WRITE_BW = 11000.0 * 0.9
    READ_LAT = 2.0
    SEND_LAT = 1.5
    WRITE_LAT = 1.5
    valos = val_os(sutos)

    sut1 = sut
    sut2 = get_sut_list()[1]
    conn = nic_config(sut1, sut2, conn)

    Case.prepare("prepare steps")
    boot_to(sut1, sut1.default_os)
    Case.wait_and_expect('wait for restoring sut2 ssh connection', 60 * 5, sut2.check_system_in_os)

    Case.step("add sut1 & sut2 mellanox driver")
    path = "/etc/sysconfig/network-scripts"
    cmd = 'dos2unix ifcfg* & ' \
          'dracut --add-drivers "mlx4_en mlx4_ib mlx5_ib" -f & ' \
          '/etc/init.d/openibd start & ' \
          'chkconfig --add openibd'
    retcode = sut1.execute_shell_cmd(cmd, cwd=path)[0]
    Case.expect("add mellanox driver for sut1", retcode == 0)
    retcode = sut2.execute_shell_cmd(cmd, cwd=path)[0]
    Case.expect("add mellanox driver for sut2", retcode == 0)

    Case.step("reboot SUT1 and SUT2")
    sut2.execute_shell_cmd("shutdown -r now")
    Case.wait_and_expect('wait for OS down', 60, not_in_os, sut2)
    my_os.warm_reset_cycle_step(sut1)
    Case.wait_and_expect('wait for restoring  sut ssh connection', 60 * 5, sut2.check_system_in_os)

    Case.step("Change sut1 and sut2 network interface mode to IB mode")
    valos.switch_infiniband_mode(sut1, "IB")
    valos.switch_infiniband_mode(sut2, "IB")

    Case.step("set mellanox card ip")
    valos.ip_assign(conn)

    Case.step("check runall test result")
    sut2.execute_shell_cmd_async("ib_read_bw -F", cwd="/usr/bin", timeout=60)
    rbw = sut1.execute_shell_cmd("ib_read_bw -F {}".format(conn.port2.ip), cwd="/usr/bin")
    Case.expect("execute ib read bw", rbw[0] == 0)
    compare_value(rbw[1], IB_READ_BW, "BW")

    sut2.execute_shell_cmd_async("ib_send_bw -F", cwd="/usr/bin", timeout=60)
    sbw = sut1.execute_shell_cmd("ib_send_bw -F {}".format(conn.port2.ip), cwd="/usr/bin")
    Case.expect("execute ib send bw", sbw[0] == 0)
    compare_value(sbw[1], IB_SEND_BW, "BW")

    sut2.execute_shell_cmd_async("ib_write_bw -F", cwd="/usr/bin", timeout=60)
    wbw = sut1.execute_shell_cmd("ib_write_bw -F {}".format(conn.port2.ip), cwd="/usr/bin")
    Case.expect("execute ib write bw", wbw[0] == 0)
    compare_value(wbw[1], IB_WRITE_BW, "BW")

    sut2.execute_shell_cmd_async("ib_read_lat -F", cwd="/usr/bin", timeout=60)
    rlat = sut1.execute_shell_cmd("ib_read_lat -F {}".format(conn.port2.ip), cwd="/usr/bin")
    Case.expect("execute ib read lat", rlat[0] == 0)
    compare_value(rlat[1], READ_LAT, "LAT")

    sut2.execute_shell_cmd_async("ib_send_lat -F", cwd="/usr/bin", timeout=60)
    slat = sut1.execute_shell_cmd("ib_send_lat -F {}".format(conn.port2.ip), cwd="/usr/bin")
    Case.expect("execute ib send lat", slat[0] == 0)
    compare_value(slat[1], SEND_LAT, "LAT")

    sut2.execute_shell_cmd_async("ib_write_lat -F", cwd="/usr/bin", timeout=60)
    wlat = sut1.execute_shell_cmd("ib_write_lat -F {}".format(conn.port2.ip), cwd="/usr/bin")
    Case.expect("execute ib write lat", wlat[0] == 0)
    compare_value(wlat[1], WRITE_LAT, "LAT")

    sut2.execute_shell_cmd_async("ib_read_bw -F -b", cwd="/usr/bin", timeout=60)
    rbw = sut1.execute_shell_cmd("ib_read_bw -F -b {}".format(conn.port2.ip), cwd="/usr/bin")
    Case.expect("execute ib read bw", rbw[0] == 0)
    compare_value(rbw[1], IB_READ_BW, "BW")

    sut2.execute_shell_cmd_async("ib_send_bw -F -b", cwd="/usr/bin", timeout=60)
    sbw = sut1.execute_shell_cmd("ib_send_bw -F -b {}".format(conn.port2.ip), cwd="/usr/bin")
    Case.expect("execute ib send bw", sbw[0] == 0)
    compare_value(sbw[1], IB_READ_BW, "BW")

    sut2.execute_shell_cmd_async("ib_write_bw -F -b", cwd="/usr/bin", timeout=60)
    wbw = sut1.execute_shell_cmd("ib_write_bw -F -b {}".format(conn.port2.ip), cwd="/usr/bin")
    Case.expect("execute ib write bw", wbw[0] == 0)
    compare_value(wbw[1], IB_READ_BW, "BW")

    Case.step("restore SUT1 and SUT2 network interface back to ETH mode")
    valos.switch_infiniband_mode(sut1, "ETH")
    valos.switch_infiniband_mode(sut2, "ETH")


def clean_up(sut):
    from dtaf_core.lib.tklib.steps_lib import cleanup
    if Result.returncode != 0:
        cleanup.to_s5(sut)


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
