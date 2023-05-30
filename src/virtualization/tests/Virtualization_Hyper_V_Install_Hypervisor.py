from src.virtualization.lib.tkinit import *

CASE_DESC = [
    # TODO
    'Install Hypervisor'

]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    # Prepare steps - Enable VTD and VMX in BIOS


    boot_to_with_bios_knobs(sut, sut.default_os, 'VTdSupport', '0x1', "ProcessorVmxEnable", "0x1")

    # Step 1
    Case.step('check hyperv install status')
    ret, out, err = sut.execute_shell_cmd('Get-WindowsFeature -Name "Hyper*"', timeout=60, powershell=True)
    (code, stdout, stderr) = sut.execute_shell_cmd('Get-WindowsFeature -Name "Hyper*"', timeout=60, powershell=True)
    Case.expect('return code == 0 and no error info', code == 0 and len(stderr.strip()) == 0)
    res = out.splitlines()[3]

    if res.split(r' ')[-1] == 'Installed':
        logger.info('hyperv install success !')
    else:
        logger.info('hyperv not install !')
        sut.execute_shell_cmd('Install-WindowsFeature -Name Hyper-V -IncludeManagementTools -Restart',
                                          timeout=600, powershell=True)
        Case.wait_and_expect('wait for restoring sut ssh connection', 60 * 5, sut.check_system_in_os)

    # Step 2
    Case.step('check hyperv install success')
    ret, out, err = sut.execute_shell_cmd('Get-WindowsFeature -Name "Hyper*"', timeout=60, powershell=True)
    res = out.splitlines()[3]
    Case.expect('HyperV has been installed', 'Installed' in res)


def clean_up(sut):
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