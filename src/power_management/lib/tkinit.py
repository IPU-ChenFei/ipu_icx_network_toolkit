import time
import set_toolkit_src_root
from tkconfig import pysv
from src.power_management.lib.pm_reset import check_punit_mc_status
from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.infra.xtp.itp import PythonsvSemiStructured
from dtaf_core.lib.tklib.steps_lib import cleanup
from dtaf_core.lib.tklib.steps_lib.log_check import *
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to
from dtaf_core.lib.tklib.steps_lib.uefi_scene import *
from dtaf_core.lib.tklib.basic.utility import get_xml_prvd, get_tag_attr
# from dtaf_core.lib.tklib.validationlanguage.python_code import case