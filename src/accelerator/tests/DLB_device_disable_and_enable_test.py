# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.accelerator.lib import *


CASE_DESC = [
    'check dlb device when bios all hqm disable',
    'check dlb device when bios all hqm enable',
    'disable the first DLB device and keep others enable',
    'disable one cpu dlb device'
]


def test_steps(sut, my_os):
    acce = Accelerator(sut)
    Case.prepare('Boot to OS with bios hqm disable')
    logger.info('')
    logger.info('---- Boot to OS with bios hqm disable ----')
    boot_to(sut, sut.default_os)
    sut.execute_shell_cmd('ln -s /usr/bin/python3 /usr/bin/python', timeout=60)
    acce.init_bashrc()
    acce.rpm_install()
    acce.kernel_header_devel()

    # Step 1 - check dlb device when bios all hqm disable
    Case.step('check dlb device when bios all hqm disable')
    (knobs_xmlcli_str, knobs_serial_list) = parse_knob_args(*bios_knob('knob_setting_hqm_disable_common_xmlcli'))
    try:
        acce.change_xmlcli_file()
        boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('knob_setting_hqm_disable_common_xmlcli'))
    except Exception:
        pass
    ret = sut.check_bios_knobs_xmlcli(knobs_xmlcli_str, sut.SUT_PLATFORM)
    while not ret:
        acce.change_xmlcli_file()
        try:
            set_bios_knobs_step(sut, *bios_knob('knob_setting_hqm_disable_common_xmlcli'))
        except Exception:
            pass
        ret = sut.check_bios_knobs_xmlcli(knobs_xmlcli_str, sut.SUT_PLATFORM)


    def get_dlb_device_num():
        _, out, err = sut.execute_shell_cmd(f'lspci |grep {acce.dlb_id}', timeout=60)
        line_list = out.strip().split('\n')
        device_num = 0
        for line in line_list:
            if f'{acce.dlb_id}' in line:
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

    # Step 1 - check dlb device when bios all hqm disable
    Case.step('check dlb device when bios all hqm disable')
    cpu_num = acce.get_cpu_num()
    pf_num = cpu_num * acce.DLB_DEVICE_NUM
    device_num = get_dlb_device_num()
    Case.expect('no dlb device after disable all hqm', device_num == 0)

    # Step 2 - check dlb device when bios all hqm enable
    Case.step('check dlb device when bios all hqm enable')
    set_bios_knob('knob_setting_hqm_enable_common_xmlcli')

    device_num = get_dlb_device_num()
    Case.expect('all dlb device exist after enable all hqm', device_num == cpu_num * acce.DLB_DEVICE_NUM)
    acce.dlb_install(True)
    ret, out, _ = sut.execute_shell_cmd('./ldb_traffic -n 1024', cwd=f'{DLB_DRIVER_PATH_L}/libdlb/examples', timeout=180)
    acce.check_keyword('Received 1024 events', out, 'Issue - Traffic move through the PF with some errors.')
    acce.dlb_uninstall()

    # Step 3 - disable the first DLB device and keep others enable
    Case.step('disable the first DLB device and keep others enable')
    for i in range(pf_num):
        set_bios_knob(f'knob_setting_hqm_disable{i}')
        device_num = get_dlb_device_num()
        Case.expect('one dlb device disappear after disable one bios hqm', device_num == cpu_num * acce.DLB_DEVICE_NUM - 1)
        acce.dlb_install(True)
        ret, out, _ = sut.execute_shell_cmd('./ldb_traffic -n 1024', cwd=f'{DLB_DRIVER_PATH_L}/libdlb/examples/',
                                            timeout=180)
        acce.check_keyword('Received 1024 events', out, 'Issue - Traffic move through the PF with some errors.')
        acce.dlb_uninstall()
    set_bios_knob('knob_setting_hqm_enable_common_xmlcli')

    # Step 4 - disable one cpu dlb device
    Case.step('disable one cpu dlb device')
    for i in range(cpu_num):
        set_bios_knob(f'knob_setting_hqm_disablecpu{i}_common_xmlcli')
        # set_bios_knobs_step(sut, *bios_knob(f'knob_setting_hqm_disablecpu{i}_common_xmlcli'))
        device_num = get_dlb_device_num()
        Case.expect('cpu0 dlb device disappear and cpu1 dlb device exist', device_num == cpu_num * acce.DLB_DEVICE_NUM / 2)
        acce.dlb_install(True)
        ret, out, _ = sut.execute_shell_cmd('./ldb_traffic -n 1024', cwd=f'{DLB_DRIVER_PATH_L}/libdlb/examples',
                                            timeout=180)
        acce.check_keyword('Received 1024 events', out, 'Issue - Traffic move through the PF with some errors.')
        acce.dlb_uninstall()
    set_bios_knob('knob_setting_hqm_enable_common_xmlcli')
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
        # clean_up(sut)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)
