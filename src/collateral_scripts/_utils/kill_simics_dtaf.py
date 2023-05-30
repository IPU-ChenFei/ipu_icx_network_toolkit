# from src.lib.toolkit.basic.testcase import Case
# from src.lib.toolkit.infra.simics.simics_launcher import SimicsLauncher
# from src.lib.toolkit.infra.sut import *
from dtaf_core.lib.tklib.basic.testcase import Case
from dtaf_core.lib.tklib.infra.simics.simics_launcher import SimicsLauncher
from dtaf_core.lib.tklib.infra.sut import get_default_sut


if __name__ == '__main__':
    sut = get_default_sut()
    Case.start(sut)
    # if SimicsLauncher.is_running():
    SimicsLauncher.kill_simics()
    Case.end()
