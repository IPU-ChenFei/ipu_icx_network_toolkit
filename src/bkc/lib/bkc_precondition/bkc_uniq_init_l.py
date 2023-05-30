#!/usr/bin/env python

from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.basic.utility import ParameterParser
from dtaf_core.lib.tklib.infra.sut import get_default_sut
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to
from dtaf_core.lib.tklib.steps_lib.valtools.tools import *

CASE_DESC = [
    "Copy bkc uniq init file to Linux sut"
]


def test_steps(sut, sutos):
    tools = get_tool(sut)

    Case.prepare("boot to OS")
    boot_to(sut, sut.default_os)

    Case.step('Create log folder')
    nowTime = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    log_dir = rf'mkdir /root/sut_scripts/log_{nowTime}'
    sut.execute_shell_cmd(log_dir)
    remote_path = rf'/root/sut_scripts/log_{nowTime}'

    Case.step('Download and uncompress to SUT')
    tools.get('bkc_uniq_init_l').uncompress_to(method='zip')

    Case.step('Rename folder')
    folder_name = tools.get("bkc_uniq_init_l").filename.rstrip('.zip')
    cmd = f'mv {folder_name} bkc_uniq'
    sut.execute_shell_cmd(cmd, timeout=10 * 60, cwd=f'{tools.bkc_uniq_init_l.ipath}')

    Case.step('disable EIST in bios and reset ')
    set_bios_knobs_step(sut, *bios_knob("disable_SpeedStep_xmlcli"))
    sutos.warm_reset_cycle_step(sut)
    check_bios_knobs_step(sut, *bios_knob("disable_SpeedStep_xmlcli"))

    Case.step('Generate golden file')
    sut.execute_shell_cmd('chmod 777 * && ./bkc_uniq_generate_golden.sh', timeout=10 * 60, cwd=f'{tools.bkc_uniq_init_l.ipath}/bkc_uniq')

    Case.step('Save log files')
    sut.execute_shell_cmd(f'cp *_golden.txt {remote_path}', cwd=f'{tools.bkc_uniq_init_l.ipath}/bkc_uniq')
    sut.download_to_local(remotepath=remote_path, localpath=os.path.join(LOG_PATH, 'result'))

    Case.step('restore env')
    del_log = rf'rm -rf {remote_path}'
    sut.execute_shell_cmd(del_log)

def clean_up(sut):
    cleanup.default_cleanup(sut)
    # pass


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
