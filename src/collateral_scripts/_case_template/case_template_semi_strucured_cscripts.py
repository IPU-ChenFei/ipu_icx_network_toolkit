# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.lib.toolkit.auto_api import *
from src.lib.toolkit.infra.xtp.itp import CscriptsSemiStructured
from src.lib.toolkit.steps_lib import cleanup
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to

CASE_DESC = [
    # TODO: replace these with real case description for this case
    'it\'s a template for a general case based on CScripts',
    'the case is expected to work for multiple os, only test on Windows by now.',
    'start the test case via dflaunch commandline as: dflaunch case_template_semi_strucured_cscripts.py',
    'replace the description here for your case',
    # list the name of those cases which are expected to be executed before this case
    '<dependencies: if any>'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    # TODO: replace these with your own steps
    # Prepare steps - call predefined steps
    Case.prepare('boot to OS & launch cscripts')
    boot_to(sut, sut.default_os)

    # if cscripts is not in 'C:\cscripts', please pass the path to CscriptsSemiStructured
    cs = CscriptsSemiStructured(globals(), locals())
    # cs = CscriptsSemiStructured(globals(), locals(), cscripts_path='C:\\bhs_cscripts')
    Case.step('test cscripts command')
    cs.execute('coreinfo.steppingInfo()')
    cs.execute('coreinfo.showVTSupport()')
    cs.execute('halt()')
    cs.execute('go()')
    cs.execute('sv.refresh()')
    # itp.execute('error.check_sys_errors()')

    cs.exit()


def clean_up(sut):
    # TODO: restore bios setting or other step to eliminate impact on the next case regardless case pass or fail
    # set_bios_knobs_step(sut, *bios_knob('disable_wol_s5_xmlcli'))

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
