import set_toolkit_src_root
import datetime
from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.steps_lib import cleanup
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to, boot_to_with_bios_knobs
from dtaf_core.lib.tklib.infra.sut import *


# TODO: import your domain knobs define or define it here
#   Finally optimize import (shortcut key is 'Ctrl + Alt + O') before submitting code
# from dtaf_core.lib.tklib.steps_lib.config import bios_knob

CASE_DESC = [
    # TODO: replace these with real case description for this case
    'This testcase is to verify Reboot cycling_Win OS.',
    '<dependencies: if any>',
    'Storage_VMD_enable.py'
]


def test_steps(sut, my_os):

    Case.prepare('boot to OS')
    boot_to(sut, sut.default_os)

    Case.step('Create log folder')
    nowTime = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    log_dir = f'mkdir C:\\log_{nowTime}'
    sut.execute_shell_cmd(log_dir)
    remote_path = f'C:\\log_{nowTime}'

    cycles = ParameterParser.parse_parameter("cycles")
    if cycles == '':
        cycles = 6
    else:
        cycles = int(cycles)

    try:
        for i in range(1, cycles):
            show_device_info = rf'wmic diskdrive list brief | tee device_info{i}.log'
            device_info = set(
                sut.execute_shell_cmd(show_device_info, timeout=60, cwd=remote_path, powershell=True)[1].strip().split('\n'))
            device_info_count = len(device_info)
            if 1 == i:
                device_set_count = device_info_count
            else:
                Case.expect('device check success', device_set_count == device_info_count)
            my_os.warm_reset_cycle_step(sut)
    except Exception as e:
        logger.info(e)
        raise ValueError('device check fail')
    finally:
        Case.step('save log files')
        sut.download_to_local(remotepath=remote_path, localpath=os.path.join(LOG_PATH, 'result'))

        Case.step('restore env')
        sut.execute_shell_cmd(f'rd /s /q {remote_path}')


def clean_up(sut):
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

    if Result.returncode != 0:
        clean_up(sut)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)
