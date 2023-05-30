import traceback

from dtaf_core.lib.tklib.basic.const import OS
from dtaf_core.lib.tklib.basic.log import logger
from dtaf_core.lib.tklib.basic.testcase import Result, Case
from dtaf_core.lib.tklib.basic.utility import ParameterParser
from dtaf_core.lib.tklib.infra.sut import get_default_sut
from dtaf_core.lib.tklib.steps_lib.os_scene import OperationSystem

CASE_DESC = [
    'Mock BKC test case to verify 0-click flow without impacting SUT'
]


def test_steps(sut, my_os):
    try:
        Case.prepare('Prepare to run test case')
        Case.step('step 1, 2, 3, ..., N')
    except Exception as e:
        logger.info(e)
        raise ValueError('device check fail')
    finally:
        Case.step('Final step')


def clean_up(sut):
    pass


def test_main():
    user_parameters = ParameterParser.parse_embeded_parameters()

    sut = get_default_sut()
    my_os = OperationSystem[OS.get_os_family(sut.default_os)]

    try:
        Case.start(sut, CASE_DESC)
        test_steps(sut, my_os)

    except Exception as e:
        Result.get_exception(e, str(traceback.format_exc()))
    finally:
        Case.step('Final step cannot Case.end()')
#        Case.end()

    if Result.returncode != 0:
        clean_up(sut)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)
