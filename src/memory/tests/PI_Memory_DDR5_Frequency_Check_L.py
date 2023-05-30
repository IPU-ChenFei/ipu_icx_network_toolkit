import set_toolkit_src_root
from src.memory.lib.memory import *
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to
from dtaf_core.lib.tklib.steps_lib.uefi_scene import *
from dtaf_core.lib.tklib.steps_lib.bios_knob import *

CASE_DESC = [
    'Verify if the POR frequency of memory under Linux behaviors as the same as it is set in BIOS.',
    # list the name of those cases which are expected to be executed before this case
]


def test_steps(sut, my_os):
    freq_list = ParameterParser.parse_parameter("freq_list")
    if freq_list == '':
        freq_list = [2666, 2933]
    else:
        freq_list = freq_list.split(',')
        freq_list = [int(i) for i in freq_list]

    Case.prepare('case prepare description')
    boot_to(sut, sut.default_os)
    # boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob(f'mem_freq_{freq_list[0]}_xmlcli'))

    clear_system_log(sut)

    log_dir = create_log_dir(sut)

    try:
        for freq in freq_list:
            my_os.reset_to_uefi_shell(sut)

            Case.step('change mem freq')
            sut.set_bios_knobs_xmlcli('='.join(bios_knob(f'mem_freq_{freq}_xmlcli')), SUT_STATUS.S0.UEFI_SHELL)
            # set_bios_knobs_step(sut, *bios_knob(f'mem_freq_{freq}_xmlcli'))
            UefiShell.reset_to_os(sut)
            Case.expect(f'mem freq has been changed to {freq} successfully',
                        sut.check_bios_knobs_xmlcli('='.join(bios_knob(f'mem_freq_{freq}_xmlcli')),
                                                    SUT_STATUS.S0.LINUX))

            Case.step('check mem quantities')
            list_freq_cmd = r'dmidecode -t 17 | tee mem_info.txt | grep "Configured Memory Speed" | grep -v "Un*" | grep -Eo "[0-9]{4}"'
            freq_list = sut.execute_shell_cmd(list_freq_cmd, cwd=log_dir)[1].strip().split('\n')
            get_mem_num = 'dmidecode -t 17 | grep -E -v "No|Vo" | grep "Size" | wc -l'
            dimm_info_check(sut, get_mem_num, 'hw_dimm_number')

            Case.step(f'check {freq} mem freq value')
            freq_set = set(freq_list)
            Case.expect('correct frequency of physical memory', len(freq_set) == 1 and int(freq_list[0]) == freq)

        check_system_log(sut, log_dir)

    finally:
        save_log_files(sut, log_dir)
        restore_env(sut, log_dir)
        restore_bios_defaults_xmlcli_step(sut, SUT_STATUS.S0.LINUX)


def clean_up(sut):
    # TODO: restore bios setting or other step to eliminate impact on the next case regardless case pass or fail
    # sut.set_bios_knobs(*bios_knob('disable_wol_s5_xmlcli'))

    # TODO: replace default cleanup.to_S5 if necessary when case execution fail
    # if Result.returncode != 0:
    #     cleanup.to_s5(sut)
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
