# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from src.lib.toolkit.auto_api import *
from src.lib.toolkit.basic.utility import get_xml_driver
from src.lib.toolkit.infra.bmc.bmc import RedfishController
from src.lib.toolkit.steps_lib.cleanup import default_cleanup
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to

CASE_DESC = [
    'https://hsdes.intel.com/appstore/article/#/18014075536',
    'Check cpu temperature after system being idle for 15 min'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None

    Case.prepare('boot to os')
    boot_to(sut, sut.default_os)

    Case.step('keep system idle for 15 minutes')
    Case.sleep(900)

    Case.step('check cpu temperature')
    redfish_cfg = get_xml_driver('physical_control')
    redfish_cfg = redfish_cfg.find('./redfish')
    redfish_inst = RedfishController(redfish_cfg.find('./ip').text, redfish_cfg.find('./username').text,
                                     redfish_cfg.find('./password').text)
    ret = redfish_inst.redfish_get('/redfish/v1/Chassis/Baseboard/Thermal')
    logger.debug(f'query thermal via redfish: {ret}')
    checked_count = 0
    check_items = ('DTS_CPU1', 'DTS_CPU2', 'Die_CPU1', 'Die_CPU2')
    for data in ret['Temperatures']:
        if data["MemberId"] in check_items:
            logger.debug(f'current temperature of {data["MemberId"]} is {data["ReadingCelsius"]}')
            Case.expect('temperature lower than 50', data["ReadingCelsius"] < 50)
            checked_count += 1
    Case.expect('all items have been checked', checked_count == len(check_items))


def clean_up(sut):
    default_cleanup(sut)


def test_main():
    # ParameterParser parses all the embed parameters
    # --help to see all allowed parameters
    user_parameters = ParameterParser.parse_embeded_parameters()
    # add your parameter parsers with list user_parameters

    # if you would like to hardcode to disable clearcmos
    # ParameterParser.bypass_clearcmos = True

    # if commandline provide sut description file by --sut <sut ini file>
    #       generate sut instance from given json file
    #       if multiple files have been provided in command line, only the 1st will take effect for get_default_sut
    #       to get multiple sut, call function get_sut_list instead
    # otherwise
    #       default sut configure file will be loaded
    #       which is defined in basic.config.DEFAULT_SUT_CONFIG_FILE
    sut = get_default_sut()
    my_os = OperationSystem[OS.get_os_family(sut.default_os)]

    try:
        Case.start(default_sut=sut, desc_lines=CASE_DESC)
        test_steps(sut, my_os)

    except Exception as e:
        Result.get_exception(e, str(traceback.format_exc()))
    finally:
        Case.end()
        clean_up(sut)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)
