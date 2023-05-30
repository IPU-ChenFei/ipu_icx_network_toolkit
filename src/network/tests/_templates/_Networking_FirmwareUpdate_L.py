
from src.network.lib import *
CASE_DESC = [
    'connect sut1 mellanox nic port to sut2 mellanox nic port cable',
    'set sut1 as a server and sut2 as a client',
    'Mellanox firmware update'
]


def __fm_update(sut, bin_file, path):
    bin_ver = bin_file.split('-')[3].replace('_', '.')
    retcode = sut.execute_shell_cmd('mst start')[0]
    Case.expect("mst start", retcode == 0)
    dev = sut.execute_shell_cmd("mst status |grep -i mt | awk -F ' ' '{print $1}'")[1].strip()

    _, stdout, _ = sut.execute_shell_cmd(f'flint -d {dev} q', timeout=30)
    logger.info(f'current device info is:\n{stdout}')
    dev_fw_version = re.search(r'(?!FW Version:\s+)\d[\d\.]+', stdout).group()

    if bin_ver == dev_fw_version:
        logger.info(f'device {dev} has latest firmware image, no update happen')
    else:
        logger.info(f'update device {dev} with image file {bin_file}')
        logger.info(f'update fw version from {dev_fw_version} to {bin_ver}')
        ret_code, stdout, stderr = sut.execute_shell_cmd("flint -d {} -i {} -y burn".format(dev.strip(), bin_file),
                                                         cwd=path, timeout=60 * 5)[0]
        logger.info(f'burn firmware bin file result is:{ret_code}')
        logger.info(f'burn firmware bin file process info is:\n{stdout}')
        logger.debug(f'burn firmware bin file process err is:\n{stderr}')

        Case.expect("update firmware", retcode == 0)
        sut.execute_shell_cmd("shutdown -r now")
        Case.wait_and_expect('wait for OS down', 60, not_in_os, sut)
        Case.wait_and_expect('wait for restoring sut ssh connection', 60 * 5, sut.check_system_in_os)
        stdout = sut.execute_shell_cmd("ibstat |grep -i Firmware | awk -F ' ' '{print $3}'")[1]
        Case.expect("check firmware version is latest", stdout.splitlines()[0].strip() == bin_ver)


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    sutos = ParameterParser.parse_parameter("sutos")
    conn = ParameterParser.parse_parameter("conn")
    tool = ParameterParser.parse_parameter("tool")
    valos = val_os(sutos)

    sut1 = sut
    sut2 = get_sut_list()[1]
    conn = nic_config(sut1, sut2, conn)

    Case.prepare("prepare steps")
    boot_to(sut1, sut1.default_os)
    Case.wait_and_expect('wait for restoring sut2 ssh connection', 60 * 5, sut2.check_system_in_os)

    Case.step("Change sut1 and sut2 network interface mode to ETH mode")
    valos.switch_infiniband_mode(sut1, "ETH")
    valos.switch_infiniband_mode(sut2, "ETH")

    Case.step("set mellanox card ipv4")
    valos.ip_assign(conn)

    Case.step("unzip tools")
    ret = valos.unzip_tools(sut1, tool, "FWUpdate")
    Case.expect("unzip sut1 firmware update tool", ret)
    ret = valos.unzip_tools(sut2, tool, "FWUpdate")
    Case.expect("unzip sut2 firmware update tool", ret)
    binfile = "{}.bin".format(tool.strip(".zip"))

    Case.step("update mellanox firmware")
    path = "{}/FWUpdate".format(valos.tool_path)
    __fm_update(sut1, binfile, path)
    Case.wait_and_expect('wait for restoring sut2 ssh connection', 60 * 5, sut2.check_system_in_os)
    __fm_update(sut2, binfile, path)


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