# noinspection PyUnresolvedReferences
from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to

from src.multisocket.lib.upi_degradation import UpiDegrade

CASE_DESC = [
    'BHS 4s SUT with fully connected 1 topology degradation case',
    'Validates that the SUT would enter the right degraded topology after certain UPI port(s) getting disabled'
    '<dependencies: if any>'
]

topology_full_2 = {
    "link_1": [("S0P3", "S3P2"), ("S1P3", "S2P2"), "TOPOLOGY_4S_Degradation_12"],
    "link_2": [("S0P2", "S2P3"), ("S1P2", "S3P3"), "TOPOLOGY_4S_Degradation_13"],
    "link_3": [("S0P0", "S1P0"), ("S1P0", "S0P0"), "TOPOLOGY_4S_Degradation_14"]
}


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    # Prepare steps - call predefined steps
    Case.prepare('boot to OS & launch itp')
    boot_to(sut, SUT_STATUS.S0.UEFI_SHELL)

    Case.step('Initialize degrade object and check UPI link details')
    full_1_degrade = UpiDegrade(sut, globals(), locals(), "cscripts")
    full_1_degrade.check_instance.check_upi_topology()
    full_1_degrade.check_instance.check_upi_link_speed(sut)
    full_1_degrade.check_instance.check_upi_s_clm()
    full_1_degrade.check_instance.check_upi_print_error()

    Case.step('Run degradation through itp')
    full_1_degrade.link_degrade_4s_full(topology_full_2)


def clean_up(sut):
    cleanup.default_cleanup(sut)


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
