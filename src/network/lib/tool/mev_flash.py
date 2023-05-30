from src.lib.toolkit.auto_api import *
from sys import exit
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to
from src.mev.lib.mev import MEV, MEVOp
from src.configuration.config.sut_tool.egs_sut_tools import SUT_IMAGE_LINUX_MEV

CASE_DESC = [
    # TODO
    'PCI Express - Endpoint LTSSM Testing',
    # list the name of those cases which are expected to be executed before this case
    '<dependencies: if any>'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    mev = MEV(sut, acc_port=3, imc_port=5)
    try:
        # Prepare steps - call predefined steps
        boot_to(sut, sut.default_os)
        MEVOp.flash_ssd_image(mev, f'{SUT_IMAGE_LINUX_MEV}/a0_3335/mev/images/nvme-image-ci.release.3335-mev-hw-a0.bin')
        MEVOp.flash_spi_image(sut, f'{SUT_IMAGE_LINUX_MEV}/a0_3335/imc/images/board_id/60004/'
                                   f'nvm-image-ci.release.3335-mev-hw-a0-imc/nvm-image_60004.bin')

    except Exception as e:
        raise e
    finally:
        MEVOp.clean_up(mev)


def clean_up(sut):
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
        clean_up(sut)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)
