# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.accelerator.lib import *

CASE_DESC = [
    'Check QAT device',
    'QAT driver install',
    'check cpa_sample_code file generate'
]


def test_steps(sut, my_os):
    acce = Accelerator(sut)

    Case.prepare('boot to OS with vtd disable')
    logger.info('')
    logger.info('---- Test Boot to Default os ----')
    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('knob_setting_sriov_disable_xmlcl'))
    sut.execute_shell_cmd('ln -s /usr/bin/python3 /usr/bin/python', timeout=60)
    acce.init_bashrc()
    acce.rpm_install()
    acce.kernel_header_devel()



    def get_qat_device_num():
        _, out, err = sut.execute_shell_cmd(f'lspci |grep {acce.qat_id}', timeout=60)
        line_list = out.strip().split('\n')
        device_num = 0
        for line in line_list:
            if f'{acce.qat_id}' in line:
                device_num += 1
        return device_num

    def set_bios_knob(command):
        ret = False
        (knobs_xmlcli_str, knobs_serial_list) = parse_knob_args(*bios_knob(command))
        while not ret:
            acce.change_xmlcli_file()
            try:
                set_bios_knobs_step(sut, *bios_knob(command))
            except Exception:
                pass
            ret = sut.check_bios_knobs_xmlcli(knobs_xmlcli_str, sut.SUT_PLATFORM)

    # step 1 - disable all QAT device
    Case.step('disable all QAT device')
    set_bios_knob('knob_setting_socket_disable_common_xmlcli')
    cpu_num = acce.get_cpu_num()
    device_num = get_qat_device_num()
    Case.expect('no qat device after disable all cpm', device_num == 0)

    # step 2 - enable all QAT device
    Case.step('enable all QAT device')
    set_bios_knob('knob_setting_socket_enable_common_xmlcli')
    device_num = get_qat_device_num()
    Case.expect('all qat device exist after enable all cpm', device_num == cpu_num * acce.QAT_DEVICE_NUM)

    # Step 3 - QAT driver install and check cpa_sample_code file generate
    Case.step('QAT driver install and check cpa_sample_code file generate')
    acce.qat_install(False)
    _, out, err = sut.execute_shell_cmd('ls |grep cpa', timeout=30, cwd=f'{QAT_DRIVER_PATH_L}/build')
    err_msg = 'Issue - cpa_sample_code file not generate'
    acce.check_keyword('cpa_sample_code', out, err_msg)
    acce.qat_uninstall()
    cpu_num = acce.get_cpu_num()
    pf_num = cpu_num * acce.QAT_DEVICE_NUM

    # step 4 - disable the one QAT device and keep others enable
    Case.step('disable the one QAT device and keep others enable')
    # set_bios_knobs_step(sut, *bios_knob('knob_setting_socket_enable_common_xmlcli'))
    for i in range(pf_num):
        set_bios_knob(f'knob_setting_Cpm_disable{i}')
        device_num = get_qat_device_num()
        Case.expect('one dlb device disappear after disable one bios hqm', device_num == cpu_num * acce.QAT_DEVICE_NUM - 1)
        acce.qat_install(False)
        _, out, err = sut.execute_shell_cmd('ls |grep cpa', timeout=30, cwd=f'{QAT_DRIVER_PATH_L}/build')
        err_msg = 'Issue - cpa_sample_code file not generate'
        acce.check_keyword('cpa_sample_code', out, err_msg)
        acce.qat_uninstall()
    set_bios_knob('knob_setting_socket_enable_common_xmlcli')
    device_num = get_qat_device_num()
    Case.expect('all qat device exist after enable all cpm', device_num == cpu_num * acce.QAT_DEVICE_NUM)

    # Step 5 - disable one cpu dlb device
    Case.step('disable one cpu dlb device')
    for i in range(cpu_num):
        set_bios_knob(f'knob_setting_socket{i}_disable_common_xmlcli')
        device_num = get_qat_device_num()
        Case.expect('cpu0 qat device disappear and cpu1 dlb device exist', device_num == cpu_num * acce.QAT_DEVICE_NUM / 2)
        acce.qat_install(False)
        _, out, err = sut.execute_shell_cmd('ls |grep cpa', timeout=30, cwd=f'{QAT_DRIVER_PATH_L}/build')
        err_msg = 'Issue - cpa_sample_code file not generate'
        acce.check_keyword('cpa_sample_code', out, err_msg)
        acce.qat_uninstall()
    set_bios_knob('knob_setting_socket_enable_common_xmlcli')
    device_num = get_qat_device_num()
    Case.expect('all qat device exist after enable all cpm', device_num == cpu_num * acce.QAT_DEVICE_NUM)
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
