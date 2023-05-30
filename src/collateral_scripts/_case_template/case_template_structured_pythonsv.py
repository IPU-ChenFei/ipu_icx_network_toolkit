# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.lib.toolkit.auto_api import *
from src.lib.toolkit.steps_lib import cleanup
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to, boot_to_with_bios_knobs
from src.lib.toolkit.infra.xtp.itp import PythonsvStructured
from src.lib.toolkit.steps_lib import bios_knob

CASE_DESC = [
    # TODO
    'it\'s a template for a general case case',
    'the case is expected to work for multiple os like Windoes/Linux/VMWare',
    'replace the description here for your case',
    # list the name of those cases which are expected to be executed before this case
    '<dependencies: if any>'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    # TODO, replace these with your own steps
    # Prepare steps - call predefined steps
    # boot_to(sut, sut.default_os)
    # equals
    boot_to_with_bios_knobs(sut, sut.default_os, *bios_knob('knob_setting_security_common_xmlcli'))

    itp = PythonsvStructured()

    # Step 1 - call predefined steps
    Case.step('Check PythonSv')
    print("ITP connected: {}".format(itp.is_itp_connected()))
    print(itp.search_by_type('uncore', keyword='pcu', search_type='registers'))
    print(itp.search_reg('uncore', keyword='io_pcu_bios_spare2_cfg'))
    print(itp.search_reg_bitfield('uncore', keyword='bios_spare'))
    print(itp.get_addr('uncore', reg_path='pcodeio_map.io_pcu_bios_spare2_cfg'))
    # print(itp.get_field_value('uncore', reg_path='pcodeio_map.io_pcu_bios_spare2_cfg', field='bios_spare'))


def clean_up(sut):
    # TODO: by default, use cleanup.default_cleanup() for all scripts, for special purpose, call other function in cleanup module
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
