#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from dtaf_core.lib.tklib.infra.sut import *
from dtaf_core.lib.tklib.basic.const import CMD_EXEC_WEIGHT
from dtaf_core.lib.tklib.steps_lib.valtools.tools import *
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to
from tkconfig import sut_tool
    
class VlToolMenu():
    def __init__(self) -> None:
        self._sut = None
        self._tools = None

    def sut(self):
        if self._sut is None:
            self._sut = get_default_sut()
        return self._sut

    def upload(self, file, target):
        self.sut().upload_to_remote(file, target)

    def download(self, rfile, target):
        self.sut().download_to_local(rfile, target)

    def get_all_tools(self):
        tool = get_tool(None)
        return vars(tool).keys()

    def install_tool_to_sut(self, package):
        sut = self.sut()
        tools = get_tool(sut)
        toolpkg = tools.get(package)
        filext = toolpkg.filename.split('.')[-1]
        method = filext if filext in ['tgz', 'zip', "gz", "bz2"] else 'copy'
        sutos = OperationSystem[OS.get_os_family(sut.default_os)]
        assert (issubclass(sutos, GenericOS))
        boot_to(sut, sut.default_os)
        toolpkg.uncompress_to(method=method)
        return
        if package == 'mlc_l':
            # uninstall
            sutos.remove_folder(sut, toolpkg.ipath)
            sutos.execute_cmd(sut, sutos.mkdir_cmd % toolpkg.ipath)

            # install
            toolpkg.uncompress_to(method='tgz')

            sutos.execute_cmd(sut, f'{toolpkg.ipath}/Linux/mlc --peak_injection_bandwidth -Z -t60', timeout=10*60)

        elif package == 'prim95_l':
            # uninstall
            sutos.remove_folder(sut, toolpkg.ipath)
            sutos.execute_cmd(sut, sutos.mkdir_cmd % toolpkg.ipath)

            # install
            toolpkg.uncompress_to(method='gz')

            # check
            sutos.execute_cmd(sut, 'prim95 -v')

        elif package == 'iperf3_l':
            # uninstall
            sutos.execute_cmd(sut, 'rpm -e iperf3', no_check=True)
            toolpkg.uncompress_to(method='copy')

            # install
            sut.execute_shell_cmd(f'rpm -ivh {toolpkg.ipath}/{toolpkg.filename} --force --nodeps', timeout=10 * 60, cwd=sut_tool('SUT_TOOLS_LINUX_NETWORK'))

            # check
            sutos.execute_cmd(sut, 'iperf3 -v')

        elif package == 'iperf3_w':
            toolpkg.uncompress_to(method='zip')

            # install
            # create symbolic link to target file/directory if some version number are included inside uncompressed path
            suttool_win_network = sut_tool('SUT_TOOLS_WINDOWS_NETWORK')
            sutos.execute_cmd(sut, rf'mklink /D {suttool_win_network}\iperf3, {toolpkg.ipath}\{os.path.basename(toolpkg.ipath)}', timeout=30)

            # check
            sutos.execute_cmd(sut, rf'{suttool_win_network}\iperf3\iperf3.exe -v', timeout=30)

        elif package == 'pxeserver_l':
            toolpkg.uncompress_to(method='copy')

            # install
            sut.execute_shell_cmd(f'dos2unix {toolpkg.filename} && sh {toolpkg.filename}', timeout=10 * 60, cwd=sut_tool('SUT_TOOLS_LINUX_NETWORK'))

        elif package == 'stressapp_l':
            # uninstall
            sutos.remove_folder(sut, toolpkg.ipath)
            sutos.execute_cmd(sut, sutos.mkdir_cmd % toolpkg.ipath)

            # install
            toolpkg.uncompress_to(method='zip', install_path='$HOME')
            sut.execute_shell_cmd('./configure', timeout=10 * 60, cwd=toolpkg.ipath)
            sut.execute_shell_cmd('make install', timeout=10 * 60, cwd=toolpkg.ipath)

            # check
            sutos.execute_cmd(sut, f'{toolpkg.ipath}/src/stressapptest-v1.3.5 -s 60 -M -m -W', timeout=10*60)
