
from src.network.lib import *
CASE_DESC = [
    'connect sut1 network port to sut2 network port cable',
    'Mellanox firmware update'
]


def __fw_update(sut, my_os, bin_file, path):
    stdout = sut.execute_shell_cmd('mst status')[1]
    logger.info(f'query NIC info:\n{stdout}')
    devs = re.findall(r'mt[\d\w]+', stdout)
    Case.expect("find mellanox card", len(devs) > 0)
    bin_ver = bin_file.split('-')[3].replace('_', '.')

    update = False
    for dev in devs:
        _, stdout, _ = sut.execute_shell_cmd(f'flint -d {dev} q', timeout=30, cwd=path)
        logger.info(f'current device info is:\n{stdout}')
        dev_fw_version = re.search(r'(?!FW Version:\s+)\d[\d\.]+', stdout).group()

        if bin_ver == dev_fw_version:
            logger.info(f'device {dev} has latest firmware image, no update happen')
        else:
            logger.info(f'update device {dev} with image file {bin_file}')
            logger.info(f'update fw version from {dev_fw_version} to {bin_ver}')
            ret_code, stdout, stderr = sut.execute_shell_cmd(f'flint_ext.exe -y -d {dev} -i {bin_file} burn',
                                                             timeout=60 * 10, cwd=path)
            logger.info(f'burn firmware bin file result is:{ret_code}')
            logger.info(f'burn firmware bin file process info is:\n{stdout}')
            logger.debug(f'burn firmware bin file process err is:\n{stderr}')

            if ret_code != 0:
                sut.execute_shell_cmd("flint_ext.exe -y -d {} -i {} -allow_psid_change burn".format(dev, bin_file),
                                      timeout=60 * 10,
                                      cwd=path)
            ret_code, stdout, stderr = sut.execute_shell_cmd('mlxfwmanager.exe', timeout=60 * 30, cwd=path)
            logger.info('update fw return code = {}'.format(ret_code))
            logger.info('update fw process log:{}'.format(stdout))
            logger.debug('update fw stderr:{}'.format(stderr))
            ret_code, stdout, stderr = sut.execute_shell_cmd('type update.log', cwd=path)
            logger.info('update fw result log:{}'.format(stdout))
            if stdout.find(bin_ver):
                logger.info("fw is update successful")
                update = True

    if update:
        my_os.warm_reset_cycle_step(sut)


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
    valos.switch_infiniband_mode(sut1, "ETH", "windows")
    valos.switch_infiniband_mode(sut2, "ETH", "windows")

    Case.step("set ipv4")
    valos.ip_assign(conn)

    Case.step("unzip tools")
    ret = valos.unzip7z_tools(sut1, tool, "FWUpdate")
    Case.expect("unzip sut1 firmware update tool", ret)
    ret = valos.unzip7z_tools(sut2, tool, "FWUpdate")
    Case.expect("unzip sut2 firmware update tool", ret)
    binfile = "{}.bin".format(tool.strip(".zip"))

    Case.step("update server firmware")
    path = os.path.join(valos.tool_path, "FWUpdate")
    __fw_update(sut1, my_os, binfile, path)
    Case.wait_and_expect('wait for restoring sut2 ssh connection', 60 * 5, sut2.check_system_in_os)
    __fw_update(sut2, my_os, binfile, path)


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
