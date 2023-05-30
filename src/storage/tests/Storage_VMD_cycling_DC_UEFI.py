import set_toolkit_src_root
import datetime
from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.steps_lib import cleanup
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to, boot_to_with_bios_knobs
from dtaf_core.lib.tklib.infra.sut import *
from dtaf_core.lib.tklib.steps_lib.uefi_scene import *
import re


CASE_DESC = [
    # TODO: replace these with real case description for this case
    'This testcase is to verify DC cycling_UEFI after enabling VMD.',
    # list the name of those cases which are expected to be executed before this case
    '<dependencies: if any>',
    'Storage_VMD_enable.py'
]


def test_steps(sut, my_os):
    Case.prepare('Boot to uefi shell')
    boot_to(sut, SUT_STATUS.S0.UEFI_SHELL)

    log_path = os.path.join(LOG_PATH, 'result')
    os.system(rf'mkdir {log_path}')
    src_str = ''
    cycles = ParameterParser.parse_parameter("cycles")
    if cycles == '':
        cycles = 6
    else:
        cycles = int(cycles)

    for i in range(1, cycles):
        Case.step(f"show devices {i} cycle result : ")
        src_list = sut.execute_uefi_cmd("devices", 60).split('\n')
        src_list.pop()
        temp_str = ''.join(src_list)

        with open(log_path + f'\\devices-{i}.txt', 'a+') as f1:
            f1.write(temp_str)

        with open(log_path + f'\\devices-{i}.txt', 'r') as f2:
            devices_str = f2.read()

        pat = 'PciRoot.*NVMe.*|INTEL SSD.*'
        ssd_list = re.findall(pat, devices_str)
        ssd_num = len(ssd_list)

        with open(log_path + f'\\ssd_info.txt', 'a+') as f3:
            f3.write(str(ssd_list))
            f3.write('\n\n')

        if 1 == i:
            ssd_num_src = ssd_num
        else:
            Case.expect('devices check success', ssd_num_src == ssd_num)

        UefiShell.s5_cycle_step(sut)
        time.sleep(10)


def clean_up(sut):
    # TODO: restore bios setting or other step to eliminate impact on the next case regardless case pass or fail
    # sut.set_bios_knobs(*bios_knob('disable_wol_s5_xmlcli'))

    # TODO: replace default cleanup.to_S5 if necessary when case execution fail
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
