# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.infra.xtp.itp import PythonsvSemiStructured
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to

from src.multisocket.lib.multisocket import MultiSocket

CASE_DESC = [
    "Multisocket test for IO stability in G3/S5/warm reset cycles"
]


def test_steps(sut, my_os, globals_vars, local_vars):
    # type: (SUT, GenericOS) -> None
    cycle_number = ParameterParser.parse_parameter("cycle_number")
    power_cycle_type = ParameterParser.parse_parameter("power_cycle")
    assert power_cycle_type in ('G3', 'S5', 'WARM')

    config_path = r"C:\BKCPkg\multisocket_ofband\mltskt_config.txt"
    with open(config_path, "r") as r:
        config = r.readlines()
        pcie_list = config[2].split(":")[1]
        pcie_list = pcie_list.split(",")

    Case.prepare('boot to OS & launch itp')
    boot_to(sut, sut.default_os)
    itp = PythonsvSemiStructured(sut.socket_name, globals_vars, local_vars)

    Case.step('Check pcie status before cycle')
    pre_pcie_info = []
    for pcie_key in pcie_list:
        pre_pcie_info.append(MultiSocket.pcie_check(pcie_key.strip(), sut))

    if sut.default_os == SUT_PLATFORM.LINUX:
        Case.step('Check dmesg for Call Trace error')
        sut.execute_shell_cmd("dmesg")

        Case.step('Check clocksource for tsc output')
        _, out, _ = sut.execute_shell_cmd("cat /sys/devices/system/clocksource/clocksource0/current_clocksource")
        # if "tsc" not in out:
        #     raise RuntimeError("Clocksource check error, retrun missing tsc")

    Case.step("Check upi details before cycle")
    mltskt_check = MultiSocket("pythonsv", itp)
    mltskt_check.check_upi_topology()
    mltskt_check.check_upi_link_speed(sut)
    mltskt_check.check_upi_s_clm()
    mltskt_check.check_upi_print_error()

    for i in range(cycle_number):
        Case.step(f'========== {power_cycle_type} Cycle No.{i + 1}==========')
        if power_cycle_type == 'G3':
            my_os.g3_cycle_step(sut)
        elif power_cycle_type == 'S5':
            my_os.s5_cycle_step(sut)
        elif power_cycle_type == 'WARM':
            my_os.warm_reset_cycle_step(sut)

        Case.step(f'Check pcie status after cycle {i + 1}')
        pcie_order = 0
        for pcie_key in pcie_list:
            post_pcie_info = MultiSocket.pcie_check(pcie_key.strip(), sut)
            if pre_pcie_info[pcie_order] != post_pcie_info:
                raise RuntimeError(f"PCIE info differs during cycling {i + 1}")
            pcie_order += 1
        if pcie_order != len(pre_pcie_info):
            raise RuntimeError(f"PCIE info differs during cycling {i + 1}")

        if sut.default_os == SUT_PLATFORM.LINUX:
            Case.step('Check dmesg for Call Trace error')
            sut.execute_shell_cmd("dmesg")

            Case.step('Check clocksource for tsc output')
            _, out, _ = sut.execute_shell_cmd("cat /sys/devices/system/clocksource/clocksource0/current_clocksource")
            # if "tsc" not in out:
            #     raise RuntimeError("Clocksource check error, retrun missing tsc")

        Case.step(f"Check upi details after cycle {i + 1}")
        mltskt_check.check_upi_topology()
        mltskt_check.check_upi_link_speed(sut)
        mltskt_check.check_upi_s_clm()
        mltskt_check.check_upi_print_error()

    Case.step("exit itp link")
    itp.exit()


def clean_up(sut):
    pass
    # if Result.returncode != 0:
    #     cleanup.to_s5(sut)


def test_main(globals_vars, local_vars):
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
    #       default sut configure file
    #       which is defined in basic.config.DEFAULT_SUT_CONFIG_FILE will be loaded
    sut = get_default_sut()
    my_os = OperationSystem[OS.get_os_family(sut.default_os)]

    try:
        Case.start(sut, CASE_DESC)
        test_steps(sut, my_os, globals_vars, local_vars)

    except Exception as e:
        Result.get_exception(e, str(traceback.format_exc()))
    finally:
        Case.end()
        clean_up(sut)


if __name__ == '__main__':
    test_main(globals(), locals())
    exit(Result.returncode)
