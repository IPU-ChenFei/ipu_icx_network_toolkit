import re

# noinspection PyUnresolvedReferences
import set_toolkit_src_root
from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.infra.xtp.itp import PythonsvSemiStructured
from dtaf_core.lib.tklib.steps_lib import cleanup
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to

CASE_DESC = [
    "Check S3M Firmware Status by Bios Menu and pythonsv via ITP"
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    # test params: --svn_bkc=0x1 --s3m_bkc=0x16 --pcode_bkc=0x1d0000b0
    svn_bkc = ParameterParser.parse_parameter("svn_bkc")
    s3m_bkc = ParameterParser.parse_parameter("s3m_bkc")
    pcode_bkc = ParameterParser.parse_parameter("pcode_bkc")

    Case.prepare('boot to uefi & launch itp')
    boot_to(sut, SUT_STATUS.S0.UEFI_SHELL)
    itp = PythonsvSemiStructured(sut.socket_name, globals(), locals())
    itp.execute("unlock()")

    Case.step('check S3M firmware and Pcode')
    itp.execute("import s3m.debugger.ad as ad")

    ret = itp.execute("ad.s3mfw_region_info()")
    svn_values = re.findall(r'SVN:\s(0x\d+)', ret)
    for svn in svn_values:
        Case.expect('SVN version is the same as BKC candidate version', svn == svn_bkc)
    revid_values = re.findall(r'REVID:\s(0x\d+)', ret)
    Case.expect('the highest REVID is S3M. Must be the same as BKC candidate.', max(revid_values) == s3m_bkc)

    ret = itp.execute("ad.pcode_region_info()")
    svn_values = re.findall(r'SVN:\s(0x\d+)', ret)
    for svn in svn_values:
        Case.expect('SVN version is the same as BKC candidate version', svn == svn_bkc)
    revid_values = re.findall(r'REVID:\s(0x\S+)', ret)
    Case.expect('the highest REVID is Pcode. Must be the same as BKC candidate.', max(revid_values) == pcode_bkc)

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
