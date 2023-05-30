# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.accelerator.lib import *

CASE_DESC = [
    'clear abort log and check QAT device status',
    'Run cpa_sample_code stress',
    'Run mega test',
    'Run Prime95 stress'
]


def test_steps(sut, my_os):
    acce = Accelerator(sut)

    Case.prepare('boot to OS with vtd disable')
    logger.info('')
    boot_to(sut, sut.default_os)
    ifwi_ver = acce.get_ifwi_version()
    if ifwi_ver >= acce.IFWI_VERSION:
        set_bios_knobs_step(sut, *bios_knob('knob_setting_vtd_common_xmlcli'))
        check_bios_knobs_step(sut, *bios_knob('knob_setting_vtd_common_xmlcli'))
    else:
        set_bios_knobs_step(sut, *bios_knob('disable_vtd_xmlcli'))
        check_bios_knobs_step(sut, *bios_knob('disable_vtd_xmlcli'))
    sut.execute_shell_cmd('ln -s /usr/bin/python3 /usr/bin/python', timeout=60)
    acce.init_bashrc()
    sut.execute_shell_cmd(
        'yum -y install https://dl.fedoraproject.org/pub/epel/epel-release-latest-8.noarch.rpm --nogpgcheck',
        timeout=10 * 60)
    sut.execute_shell_cmd('yum -y install epel-release readline-devel  xxhash-devel  lz4-devel', timeout=10 * 60)

    # step 1 - clear abort log and check QAT device status
    Case.step('clear abort log and check QAT device status')
    acce.kernel_header_devel()
    acce.rpm_install()
    acce.qat_uninstall()
    acce.qat_install(False)
    sut.execute_shell_cmd('abrt-auto-reporting enabled', timeout=60)
    sut.execute_shell_cmd('abrt-cli rm /var/spool/abrt/*', timeout=60)
    acce.check_qat_service_status()

    # Step 2 - Run QAT cpa_sample_code
    Case.step('Run QAT cpa_sample_code')
    acce.qat_stress()

    # Step 3 - Run mega test
    Case.step('Run mega test')
    acce.qat_stv_mega_test()

    # Step 4 - Run Prime95 stress
    Case.step('Run Prime95 stress')
    acce.prime95_stress()


    

    acce.check_python_environment()


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
