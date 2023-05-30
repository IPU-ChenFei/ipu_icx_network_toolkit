#!/usr/bin/env python
import os
from src.dtaf_core.lib.tklib.basic.utility import execute_host_cmd


SUT_APP_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '../collateral_scripts/_sutapp'))


execute_host_cmd(f'python install_iperf3_l.py', timeout=600, cwd=SUT_APP_PATH)
execute_host_cmd(f'python install_pxeserver_l.py', timeout=600, cwd=SUT_APP_PATH)
