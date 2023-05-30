import re

# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.infra.xtp.itp import PythonsvSemiStructured
from dtaf_core.lib.tklib.steps_lib import cleanup
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to
from dtaf_core.lib.tklib.steps_lib.uefi_scene import UefiShell
from src.multisocket.lib.multisocket import MultiSocket

CASE_DESC = [
    "Update S3M Firmware , check the update flow and version of S3M"
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    # latest ifwi bin file path in HOST
    ifwi_path = ParameterParser.parse_parameter("ifwi_path")
    # latest S3M version, must be hex value string
    latest_s3m_version = ParameterParser.parse_parameter("s3m_ver")
    # N-1 S3M zip file path in HOST
    pre_ver_s3m_path = ParameterParser.parse_parameter("pre_ver_s3m_path")
    pre_ver_s3m_ver = re.search(r'REVID(0x\d+)', pre_ver_s3m_path)
    if pre_ver_s3m_ver is None:
        raise ValueError('param pre_ver_s3m_path is wrong')
    pre_ver_s3m_ver = pre_ver_s3m_ver.group(1)

    # build S3M N-1 release with the latest ifwi by stitch tool
    pre_ver_ifwi_path = MultiSocket.build_ifwi_by_stitch(sut, ifwi_path, pre_ver_s3m_path, sut_tool('MS_STITCH_PATH'))
    logger.debug(f'get bin file {pre_ver_ifwi_path} of S3M N-1 release with the latest ifwi')

    Case.prepare('boot to uefi & launch itp')
    boot_to(sut, SUT_STATUS.S0.UEFI_SHELL)
    itp = PythonsvSemiStructured(sut.socket_name, globals(), locals())
    itp.execute("unlock()")

    Case.step('enable S3M provision')
    itp.execute('import pysvtools.xmlcli.XmlCli as cli')
    itp.execute('cli.clb._setCliAccess("itpii")')
    output = itp.execute('cli.CvProgKnobs("CFRS3mProvision=0x1, CFRPucodeProvision=0x1")')
    Case.expect('set bios knob successfully', 'Verify Passed' in output)
    UefiShell.reset_cycle_step(sut)

    Case.step('check S3M N version')
    s3m_version = MultiSocket.get_S3M_version(itp)
    Case.expect('S3M version is correct', s3m_version == latest_s3m_version)

    Case.step('AC off the system and flash the bios binary with S3M N-1 release')
    sut.ac_off()
    sut.wait_for_power_status(SUT_STATUS.G3, 60)
    # TODO: flash the bios binary with S3M N-1 release

    Case.step('AC on the system and boot to UEFI Shell')
    sut.ac_on()
    sut.wait_for_power_status(SUT_STATUS.S0, 60)
    sut.bios.enter_bios_setup()
    sut.bios.bios_setup_to_uefi_shell()

    Case.step('check S3M N-1 version')
    s3m_version = MultiSocket.get_S3M_version(itp)
    Case.expect('S3M N-1 version is correct', s3m_version == pre_ver_s3m_ver)

    Case.step('AC off the system and flash the bios binary with S3M N release')
    sut.ac_off()
    sut.wait_for_power_status(SUT_STATUS.G3, 60)
    # TODO: flash the bios binary with S3M N release

    Case.step('AC on the system and boot to UEFI Shell')
    sut.ac_on()
    sut.wait_for_power_status(SUT_STATUS.S0, 60)
    sut.bios.enter_bios_setup()
    sut.bios.bios_setup_to_uefi_shell()

    Case.step('check S3M N version')
    s3m_version = MultiSocket.get_S3M_version(itp)
    Case.expect('S3M N version is correct', s3m_version == latest_s3m_version)

    Case.step("exit itp link")
    itp.exit()


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
