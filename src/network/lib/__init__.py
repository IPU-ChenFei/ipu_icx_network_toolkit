import re
import os.path
import types
import time

from sys import exit
from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.infra.sut import get_sut_list, get_default_sut
from dtaf_core.lib.tklib.steps_lib.os_scene import *
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to
from dtaf_core.lib.tklib.steps_lib.bios_knob import set_bios_knobs_step
from dtaf_core.lib.tklib.steps_lib import cleanup, log_check
from dtaf_core.lib.tklib.steps_lib.uefi_scene import UefiShell
from dtaf_core.lib.tklib.basic.log import LogAll, logger

# from src.network.lib.tool.dhcp_server import setup_dhcp_server
from src.network.lib.network import val_os
from src.network.lib.network import muti_nic_config
from src.network.lib.config import nic_config

from tkconfig import bios_knob
from tkconfig.sut_tool.bhs_sut_tools import NW_WINDOWS_HEB_W
from tkconfig.sut_tool import bhs_sut_tools
from tkconfig import sut_tool

# from src.network.lib.mev import MEV, MEVOp, MEVConn
# from src.network.lib.utility import get_core_list, iperf3_data_conversion, get_bdf



