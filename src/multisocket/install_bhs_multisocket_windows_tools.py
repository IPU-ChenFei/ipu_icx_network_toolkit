import os

from dtaf_core.lib.tklib.basic.utility import execute_host_cmd

INSTALL_PACKAGE = ('install_mlc_w.py', 'install_stream_w.py', 'install_linpack_w.py', 'install_iwvss_w.py')

sut_app_path = str(__file__).split('src')
sut_app_path = os.path.join(sut_app_path[0], 'src', 'collateral_scripts', '_sutapp')

for install_script in INSTALL_PACKAGE:
    ret, _, _ = execute_host_cmd(f'python {install_script}', timeout=1200, cwd=sut_app_path)
    assert ret == 0, f'execute {install_script} failed'
