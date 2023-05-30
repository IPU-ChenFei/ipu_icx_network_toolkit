#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
from dtaf_core.lib.tklib.infra.sut import *
from dtaf_core.lib.tklib.basic.const import *
from dtaf_core.lib.tklib.basic.testcase import *
from dtaf_core.lib.tklib.basic.log import *
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to
from dtaf_core.lib.tklib.steps_lib.uefi_scene import UefiShell
from dtaf_core.lib.tklib.steps_lib.vl.vltcd import *
from src.lib.validationlanguage.src_translator.const import *
from src.lib.validationlanguage.src_translator.trans_h2l import HlsTranslator
from src.lib.validationlanguage.src_translator.trans_l2p import PythonTransaltor
from src.lib.validationlanguage.src_translator.translator import *

CASE_DESC =  [
    'test for hls gui',
]

class VlTestCase:
    Linux = os_scene.Linux
    Windows = os_scene.Windows
    ESXi = os_scene.Vmware
    UEFI = "UEFI SHELL"
    OS = 'OS'
    def __init__(self, outtext, biostext, _global, _local) -> None:
        self.globals = _global
        self.locals = _local
        self.__sut = None
        self.__loghandler = logging.StreamHandler(stream=outtext)
        self.__loghandler.setLevel(logging.INFO)
        self.outtext = outtext
        self.biostext = biostext
        self.show_bios_log = False
        logger.addHandler(self.__loghandler)
        self.h2l = HlsTranslator()
        self.l2p = PythonTransaltor()
        self.environment = None # OS, UEFI_SHELL
        self.os = None
        self.itplib = 'pythonsv'
        self._itp = None

    # def __del__(self) -> None:
    #     logger.removeHandler(self.__loghandler)
    #     if self.__sut is not None:
    #         Case.end()

    def toggle_bios_log(self, on = True):
        if self.show_bios_log == on:
            return

        self.show_bios_log = on
        if self.__sut is None:
            return

        if self.show_bios_log:
            self.__sut.bios.bios_log.console_log.close()
            self.__sut.bios.bios_log.console_log = self.biostext
            self.__sut.bios.bios_log.console_log.closed = False
        else:
            self.__sut.bios.bios_log.console_log = open(self.__sut.bios.bios_log.log_file, 'a+', encoding='utf-8')

    def sut(self):
        if self.__sut is None:
            self.__sut = get_default_sut()
            if self.show_bios_log:
                if self.__sut.bios.bios_log.console_log is not None:
                    self.__sut.bios.bios_log.console_log.close()
                self.__sut.bios.bios_log.console_log = self.biostext
                self.__sut.bios.bios_log.console_log.closed = False
            Case.start(default_sut=self.__sut, desc_lines=CASE_DESC)
            if Case.prepare('boot to OS'):
                boot_to(self.__sut, self.__sut.default_os)
                self.environment = self.OS
                self.os = OS.get_os_family(self.__sut.default_os)
        return self.__sut

    def itp(self):
        if self._itp is None:
            if self.itplib == 'pythonsv':
                sut = self.sut()
                from dtaf_core.lib.tklib.infra.xtp.itp import PythonsvSemiStructured
                self._itp = PythonsvSemiStructured(sut.socket_name, self.globals, self.locals)
            elif self.itplib == 'cscripts' or self.itplib == 'cscript':
                from dtaf_core.lib.tklib.infra.xtp.itp import CscriptsSemiStructured
                self._itp = CscriptsSemiStructured(self.globals, self.locals)
        return self._itp

    def __power_cycle_cmd_wa(self, cmd):
        try:
            res = self.sut().execute_shell_cmd(cmd)
            return res
        except Exception as e:
            # TODO DTAF shall not raise OsCommandException when timeout
            logger.debug('ignore timeout issue, as SSH service may get down before DTAF function return')
            logger.debug(OperationSystem[self.sut().SUT_PLATFORM].s5_cmd)
            err_info = str(traceback.format_exc())
            logger.debug(err_info)

    def cold_reset(self, timeout=10 * 60):
        if self.environment == self.UEFI:
            cmd = 'reset -c'
            logger.info('<Uefi> reboot with cmd: {}'.format(cmd))
            self.sut().bios.uefi_shell.execute(cmd)
            time.sleep(60)
        elif self.environment == self.OS:
            self.sut().sutos.shutdown(self.sut(), timeout)
            logger.info(f'[{self.sut().sutos.OS}][Cold Reset Cycle] Press power button and boot back to OS')
            self.sut().press_power_button_short()
            Case.expect('wait for system back to S0', self.sut().wait_for_power_status(SUT_STATUS.S0, timeout))
            Case.wait_and_expect(f'wait for system back to {self.sut().sutos.OS}', 15 * timeout, self.sut().check_system_in_os)
        else:
            logger.error(f'invalid environment={self.environment}')
            assert(False)

    def warm_reset(self, timeout=10 * 60):
        sut = self.sut()
        if self.environment == self.UEFI:
            cmd = 'reset -w'
            logger.info('<Uefi> reboot with cmd: {}'.format(cmd))
            sut.bios.uefi_shell.execute(cmd)
            time.sleep(10)
        elif self.environment == self.OS:
            cmd = OperationSystem[OS.get_os_family(sut.default_os)].wr_cmd
            assert (cmd is not None and "Warm Reset is not implemented for this OS")
            self.__power_cycle_cmd_wa(cmd)
            time.sleep(10)
            Case.wait_and_expect('wait for OS down', timeout, not_in_os, sut)
            Case.snapshot('after_os_down')
        else:
            logger.error(f'invalid environment={self.environment}')
            assert(False)

    def reset(self, method=None, timeout=10 * 60):
        if method.upper() == 'COLD':
            self.cold_reset(timeout)
        else:
            self.warm_reset(timeout)

    def unpack_cmd(self, text, patterns):
        for p in patterns:
            if text.startswith(p):
                px, _, cmd = text.partition(',')
                pre, tail = self.unpack_cmd(cmd.strip(), patterns)
                pre += px,
                return (pre, tail)
        return ((), text)

    def parse_equation_value(self, equations, key):
        for e in equations:
            if e.startswith(f'{key}='):
                return e.partition('=')[2]
        return None

    def execute_cmd(self, cmd):
        sut = self.sut()
        sutos = OperationSystem[OS.get_os_family(sut.default_os)]
        hostos = HostOs()
        tools = get_tool(sut)
        bmc = get_bmc_info()

        pre, ucmd = self.unpack_cmd(cmd, ['nocheck', 'timeout='])
        fcmd = eval('f"""' + ucmd + '"""')

        timeout=self.parse_equation_value(pre, 'timeout')
        no_check='nocheck' in pre
        if timeout is None:
            sutos.execute_cmd(sut, fcmd, no_check=no_check)
        else:
            timeout = int(timeout)
            sutos.execute_cmd(sut, fcmd, timeout, no_check)

    def execute_itp_cmd(self, cmd):
        sut = self.sut()
        hostos = HostOs()
        tools = get_tool(sut)
        bmc = get_bmc_info()

        itp = self.itp()
        if itp is None:
            return

        fcmd = eval('f"""' + cmd + '"""')
        itp.execute(fcmd)

    def execute_host_cmd(self, cmd):
        sut = self.sut()
        hostos = HostOs()
        tools = get_tool(sut)
        bmc = get_bmc_info()

        pre, ucmd = self.unpack_cmd(cmd, ['nocheck', 'timeout='])
        fcmd = eval('f"""' + ucmd + '"""')
        timeout=self.parse_equation_value(pre, 'timeout')

        if timeout is None:
            res = sut.execute_host_cmd(fcmd)
        else:
            res = sut.execute_host_cmd(fcmd, timeout=timeout)
        retval, stdout, errout = res

        no_check='nocheck' in pre
        if no_check:
            retval = None
        else:
            Case.expect("host command exit with zero", retval == 0)

    def wait(self, seconds):
        self.sut()
        Case.sleep(seconds)

    def execute_high_level(self, cmd):
        steps = self.h2l.translate_lines([cmd])
        self.execute_low_blocks(steps)

    def switch_ac(self, statte):
        sut = self.sut()
        if statte.upper() == 'ON':
            sut.ac_on()
        elif statte.upper() == 'OFF':
            sut.ac_off()

    def switch_dc(self, state):
        sut = self.sut()
        if state.upper() == 'ON':
            sut.dc_on()
        elif state.upper() == 'OFF':
            sut.dc_off()

    def wait_for(self, target):
        sut = self.sut()
        if target.upper() == 'OS':
            Case.wait_and_expect("wait for entering OS ", 60*60, sut.check_system_in_os)
        elif target.upper() == 'UEFI SHELL':
            sut.bios.enter_bios_setup()
            sut.bios.bios_setup_to_uefi_shell()
            Case.expect('in UEFI Shell', sut.bios.in_uefi())
            self.environment = "UEFI SHELL"
        elif target.upper() == 'S0':
            sut.wait_for_power_status(SUT_STATUS.S0, 30*60)
        elif target.upper() == 'S5':
            sut.wait_for_power_status(SUT_STATUS.S5, 30*60)

    def check_environment(self, target):
        sut = self.sut()
        if target.upper() == 'UEFI SHELL':
            Case.expect(f'system in UEFI SHELL', not sut.check_system_in_os() and sut.bios.in_uefi())
        elif target.upper() == 'OS':
            Case.expect(f'system in OS', sut.check_system_in_os())

    def check_powerstate(self, target):
        sut = self.sut()
        if target.upper() == 'S0':
            Case.expect(f'system power in S0', sut.get_power_status() ==SUT_STATUS.S0)
        elif target.upper() == 'S5':
            Case.expect(f'system power in S5', sut.get_power_status() ==SUT_STATUS.S5)
        elif target.upper() == 'G3':
            Case.expect(f'system power in G3', sut.get_power_status() ==SUT_STATUS.G3)

    def set_bios_knobs(self, biosknobs):
        sut = self.sut()
        set_cli = sut.xmlcli_uefi.check_bios_knobs(biosknobs)
        if not set_cli:
            sut.xmlcli_uefi.set_bios_knobs(biosknobs)
            UefiShell.reset_cycle_step(sut)
            Case.expect("double check bios knobs", sut.xmlcli_uefi.check_bios_knobs(biosknobs))

    def clear_cmos(self):
        sut = self.sut()
        sut.clear_cmos()

    def unpack_repeat(self, steps, indent):
        blocks = []
        for i in range(len(steps)):
            cmd = steps[i]
            fop, _, val = cmd.partition(':')
            op = fop.strip()
            idt = fop.index(fop.strip())
            if op == 'End' and indent == idt:
                break
            blocks.append(cmd)
        return blocks

    def execute_low_blocks(self, steps):
        i = 0
        while i < len(steps):
            cmd = steps[i]
            fop, _, val = cmd.partition(':')
            op = fop.strip()
            indent = fop.index(fop.strip())
            if op.strip() == 'Repeat':
                repeat = int(val.strip())
                if i + 1 >= len(steps):
                    break
                blocks = self.unpack_repeat(steps[i + 1:], indent)
                for j in range(0, repeat):
                    self.execute_low_blocks(blocks)
                i += len(blocks) + 2
                continue
            self.execute_low_level(cmd.strip())
            i += 1

    def execute_low_level(self, cmd):
        self.sut()
        op, _, val = cmd.partition(':')
        if op in self.l2p.translators.keys():
            val = val.strip()
            if op == 'Check Environment':
                self.check_environment(val)
            elif op == 'Check Power State':
                self.check_powerstate(val)
            elif op == 'Reset':
                self.reset(val)
            elif op == 'Execute Command':
                self.execute_cmd(val)
            elif op == 'Execute Host Command':
                self.execute_host_cmd(val)
            elif op == 'Execute ITP Command':
                self.execute_itp_cmd(val)
            elif op == 'Wait':
                self.wait(int(val))
            elif op == 'Wait for':
                self.wait_for(val)
            elif op == 'Switch DC':
                self.switch_dc(val)
            elif op == 'Set BIOS knob':
                self.set_bios_knobs(val)
            elif op == 'Switch AC':
                self.switch_ac(val)
            elif op == 'Clear CMOS':
                self.clear_cmos()
            else:
                # op == 'PREPARE' or op == 'STEP' or op == 'Repeat' or op == 'Log':
                self.outtext.write(f'not implemented for {op}, cmd = {cmd}')
            return

        if is_assign_line(cmd):
            ret = parse_assignment_line(cmd)
            if ret is None:
                return
            name, value = ret
            if value.startswith('\'') or value.startswith('"'):
                value = eval(value)
            if name == 'ItpLib':
                self.itplib = value
            elif name == 'OS':
                self.os = value
            elif name == 'Environment':
                self.environment = value
            else:
                self.outtext.write(f'ERROR: unknown assignment{cmd}\n')
            return

        # comments or unknown line
        self.outtext.write(cmd + '\n')
