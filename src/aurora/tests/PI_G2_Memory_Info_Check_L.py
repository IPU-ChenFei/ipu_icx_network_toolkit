# noinspection PyUnresolvedReferences
import set_toolkit_src_root

from src.aurora.lib.aurora import MEMORY_NUM_PER_SOCKET, MEMORY_SIZE, SOCKET_NUM
from src.lib.toolkit.auto_api import *
from src.lib.toolkit.steps_lib.cleanup import default_cleanup
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to

CASE_DESC = [
    'https://hsdes.intel.com/appstore/article/#/18014074832'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    Case.prepare('Boot to Default os')
    boot_to(sut, sut.default_os)

    Case.step('get the MemTotal number in /proc/meminfo')
    ret, stdout, _ = sut.execute_shell_cmd("cat /proc/meminfo | grep MemTotal | awk -F ':' '{print $2}'")
    system_detected_mem = stdout.strip().split()
    system_detected_mem_total = int(system_detected_mem[0])
    logger.debug(f'system detected mem total is {system_detected_mem_total} {system_detected_mem[1]}')
    mem_config_total = SOCKET_NUM * MEMORY_NUM_PER_SOCKET * MEMORY_SIZE * 1024 * 1024
    logger.debug(f'mem config total is {mem_config_total} {system_detected_mem[1]}')
    Case.expect('mem config total approximates system detected mem total',
                (mem_config_total - system_detected_mem_total) / mem_config_total < 0.05)


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
