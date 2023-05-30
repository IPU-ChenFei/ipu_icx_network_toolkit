# # from src.lib.toolkit.basic.testcase import Case
# from src.lib.toolkit.infra.sut import *
from dtaf_core.lib.tklib.basic.testcase import Case
from dtaf_core.lib.tklib.infra.sut import *

if __name__ == '__main__':
    sut = get_default_sut()
    Case.start(sut)
    sut.clear_cmos()
    Case.end()
