from src.network.lib import *
CASE_DESC=[
    'connect sut1 nic port to sut2 nic port cable',
    'set sut1 as a server and sut2 as a client',
    'update server and client firmware'
]


def __firmware_update(sut, path, mac):
    ret_code, stdout, stderr = sut.execute_shell_cmd('nvmupdatew64e.exe -u -m {} -l -o update.log -c nvmupdate.cfg'.format(mac), timeout=60 * 30, cwd=path)
    if ret_code == 1:
        repeattime = 5
        for i in range(repeattime):
            repeattime = repeattime + 1
            ret_code, stdout, stderr = sut.execute_shell_cmd(
                'nvmupdatew64e.exe -u -m {} -l -o update.log -c nvmupdate.cfg'.format(mac), timeout=60 * 30, cwd=path)
            if ret_code == 0:
                repeattime = 0
    Case.expect("execute command to update firmware successful", ret_code == 0)
    logger.info('update fw return code = {}'.format(ret_code))
    logger.info('update fw process log:{}'.format(stdout))
    logger.debug('update fw stderr:{}'.format(stderr))
    ret_code, stdout, stderr = sut.execute_shell_cmd('type update.log', cwd=path)
    logger.info('update fw result log:{}'.format(stdout))
    if stdout.find('Reboot is required to complete the update process') > -1:
        Windows.reset_cycle_step(sut)


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

    Case.step("set ipv4")
    valos.ip_assign(conn)

    Case.step("unzip update file")
    flag = tool.split("_")[0]
    tool_path = r"{0}\{1}Upgrade\{1}\Winx64".format(valos.tool_path, flag)
    ret = valos.unzip_tools(sut1, tool, "{}Upgrade".format(flag), flag=True)
    Case.expect("unzip sut1 update tool", ret)
    valos.unzip_tools(sut2, tool, "{}Upgrade".format(flag), flag=True)
    Case.expect("unzip sut2 update tool", ret)

    Case.step("update server firmware in sut1")
    mac = valos.get_mac_address(sut1, conn.port1.nic.id_in_os.get(sutos), 0)
    __firmware_update(sut1, tool_path, mac.replace('-', ''))
    Case.wait_and_expect('wait for restoring sut2 ssh connection', 60 * 5, sut2.check_system_in_os)

    Case.step("update client firmware in sut2")
    mac2 = valos.get_mac_address(sut2, conn.port1.nic.id_in_os.get(sutos), 0)
    __firmware_update(sut2, tool_path, mac2.replace('-', ''))


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