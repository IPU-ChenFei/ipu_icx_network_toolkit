import time

# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.lib.toolkit.auto_api import *
from src.lib.toolkit.steps_lib.cleanup import default_cleanup
from src.aurora.lib.aurora import DMIDECODE_PATH, MEMORY_SIZE, kill_process
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to

CASE_DESC = [
    'https://hsdes.intel.com/appstore/article/#/18014075043'
]

STRESS_DURATION = 1800


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    Case.prepare('Boot to Default os')
    boot_to(sut, sut.default_os)
    Case.step('check memory size')
    ret, stdout, _ = sut.execute_shell_cmd("./dmidecode|grep -A5 'Memory Device'|grep Size|awk -F ':' '{print $2}'",
                                           cwd=DMIDECODE_PATH)
    for size in stdout.strip().split('\n'):
        if size.strip() == 'No Module Installed':
            continue
        size = size.strip().split()
        size = int(size[0])
        Case.expect('memory size is correct', size == MEMORY_SIZE)

    Case.step('allow single-threaded tests to use')
    ret, stdout, _ = sut.execute_shell_cmd("sysctl vm.zone_reclaim_mode=0")

    Case.step('check the MemFree number in /proc/meminfo')
    ret, stdout, _ = sut.execute_shell_cmd("cat /proc/meminfo | grep MemFree | awk '{print$2}'")
    mem_free1 = int(stdout.strip())

    Case.step('run dd for 30 minutes')
    sut.execute_shell_cmd_async('dd if=/dev/zero of=/temp')
    time.sleep(STRESS_DURATION)
    kill_process(sut, 'dd if=/dev/zero of=/temp')

    Case.step('check the MemFree in /proc/meminfo is changed to  a small number')
    ret, stdout, _ = sut.execute_shell_cmd("cat /proc/meminfo | grep MemFree | awk '{print$2}'")
    mem_free2 = int(stdout.strip())

    Case.expect('MemFree is changed to a small number', mem_free2 < mem_free1)


def clean_up(sut):
    default_cleanup(sut)


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
