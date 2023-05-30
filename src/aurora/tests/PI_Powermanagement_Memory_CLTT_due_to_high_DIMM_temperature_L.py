import time

# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.lib.toolkit.auto_api import *
from src.lib.toolkit.infra.xtp.itp import PythonsvSemiStructured
from src.lib.toolkit.steps_lib.cleanup import default_cleanup
from src.aurora.lib.aurora import MLC_PATH, MEMORY_MC_NUM, MEMORY_CH_NUM, PTU_PATH
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to

CASE_DESC = [
    'https://hsdes.intel.com/appstore/article/#/18016910216',
]


def restore_dimm_temp(itp, socket_index):
    itp.execute('unlock()')
    itp.execute(f'sv.socket{socket_index}.uncore.memss.mcs.chs.dimm_temp_th_0.temp_hi=0x55')
    itp.execute(f'sv.socket{socket_index}.uncore.memss.mcs.chs.dimm_temp_th_0.temp_mid=0x53')
    itp.execute(f'sv.socket{socket_index}.uncore.memss.mcs.chs.dimm_temp_th_0.temp_lo=0x52')
    # itp.execute(f'sv.socket{socket_index}.uncore.memss.mcs.chs.dimm_temp_th_1.temp_hi=0x55')
    # itp.execute(f'sv.socket{socket_index}.uncore.memss.mcs.chs.dimm_temp_th_1.temp_mid=0x53')
    # itp.execute(f'sv.socket{socket_index}.uncore.memss.mcs.chs.dimm_temp_th_1.temp_lo=0x52')


def get_dimm_temp(itp, socket_index):
    out = itp.execute(f'print(sv.socket{socket_index}.uncore.memss.mcs.chs.dimmtempstat_0.dimm_temp)')
    out = out.strip().split('\n')
    out = [int(item.split('-')[1].strip(), 16) for item in out]
    min_temp = min(out)

    return min_temp


def test_mem_cltt_event(sut, itp, socket_index, mc_index, ch_index):
    restore_dimm_temp(itp, socket_index)

    Case.step('Monitor the cpu using ptu tool')
    ret, _, _ = sut.execute_shell_cmd('./ptu -mon -t 600', 800, cwd=PTU_PATH)
    Case.expect('run ptu tool successfully', ret == 0)

    Case.step('read DIMM temperature')
    itp.execute(f'print(sv.socket{socket_index}.uncore.memss.mcs.chs.dimmtempstat_0.dimm_temp)')

    Case.step('run mlc stress test')
    ret, normal_bandwidth, _ = sut.execute_shell_cmd('./mlc --peak_injection_bandwidth -X -t30', 600, cwd=MLC_PATH)

    Case.step(f'test socket{socket_index} memory cltt')
    dimm_temp = get_dimm_temp(itp, socket_index)
    itp.execute(
        f'sv.socket{socket_index}.uncore.memss.mc{mc_index}.ch{ch_index}.dimm_temp_th_0.temp_lo={dimm_temp - 6}')
    itp.execute(
        f'sv.socket{socket_index}.uncore.memss.mc{mc_index}.ch{ch_index}.dimm_temp_th_0.temp_mid={dimm_temp - 4}')
    itp.execute(
        f'sv.socket{socket_index}.uncore.memss.mc{mc_index}.ch{ch_index}.dimm_temp_th_0.temp_hi={dimm_temp - 2}')
    ret, low_bandwidth, _ = sut.execute_shell_cmd('./mlc --peak_injection_bandwidth -X -t30', 400, cwd=MLC_PATH)

    normal_bandwidth = normal_bandwidth.strip().split('\n')[-5:]
    low_bandwidth = low_bandwidth.strip().split('\n')[-5:]
    for index in range(len(normal_bandwidth)):
        normal_item = float(normal_bandwidth[index].split(':\t')[1].strip())
        low_item = float(low_bandwidth[index].split(':\t')[1].strip())
        if (normal_item - low_item) / normal_item * 100 < 5:
            raise RuntimeError('memory CLTT is not working')


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    Case.prepare('Boot to Default os')
    boot_to(sut, sut.default_os)
    itp = PythonsvSemiStructured(sut.socket_name, globals(), locals())
    itp.execute('unlock()')

    for socket_index in range(sut.socket_num):
        for mc_index in range(MEMORY_MC_NUM):
            for ch_index in range(MEMORY_CH_NUM):
                test_mem_cltt_event(sut, itp, socket_index, mc_index, ch_index)
                time.sleep(30)

    restore_dimm_temp(itp, socket_index)


def clean_up(sut, my_os):
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
        clean_up(sut, my_os)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)
