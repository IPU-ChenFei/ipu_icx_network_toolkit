# !/usr/bin/env python

from src.dpmo.lib.power_service import *
from dtaf_core.lib.tklib.basic.const import OS
from dtaf_core.lib.tklib.steps_lib.os_scene import OperationSystem
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to
from dtaf_core.lib.tklib.basic.log import logger


class OsService(threading.Thread):
    def __init__(self, sut):
        super().__init__(daemon=True)
        self.is_stop = False
        self.os = OperationSystem[OS.get_os_family(sut.default_os)]  # todo: initial os obj
        self.__os_detect = False
        self.event_queue = EventQueue()
        self.power_service = PowerService(sut)
        self.__os_init = True
        self.sut = sut

    @property
    def os_init(self):
        return self.__os_init

    @os_init.setter
    def os_init(self, value):
        self.__os_init = value

    @property
    def os_detect(self):
        return self.__os_detect

    @os_detect.setter
    def os_detect(self, value):
        self.__os_detect = value

    def reset(self):
        if DpmoCfg.enable_ssh_conn:
            self.sut.execute_shell_cmd("shutdown -r now")
            # self.sut.wait_for_power_status(POWER_STATE_S5, timeout=300)
            # self.os.reset_cycle_step(self.sut)
            # self.os.reset()  # todo:

    def shutdown(self, timeout):
        if DpmoCfg.enable_ssh_conn:
            self.os.shutdown(self.sut)  # todo:
        if not self.power_service.wait_for_power(POWER_STATE_S5, timeout):
            logger.error(f'fail to wait for power: {POWER_STATE_S5}')
            return False
        logger.info(f'successfully do the power transition: {POWER_STATE_S0} -> {POWER_STATE_S5}')
        return True

    def bootfirst(self):
        self.sut.execute_shell_cmd("efibootmgr --bootorder 0001")

    def sleep(self, timeout):
        if DpmoCfg.enable_ssh_conn:
            self.os.shutdown()  # todo:
        if not self.power_service.wait_for_power(POWER_STATE_S5, timeout):
            logger.error(f'fail to wait for power: {POWER_STATE_S5}')
            return False
        logger.info(f'successfully do the power transition: {POWER_STATE_S0} -> {POWER_STATE_S5}')
        return True

    def hibernate(self, timeout):
        if DpmoCfg.enable_ssh_conn:
            self.os.hibernate()  # todo:
        if not self.power_service.wait_for_power(POWER_STATE_S4, timeout):
            logger.error(f'fail to wait for power: {POWER_STATE_S4}')
            return False
        logger.info(f'successfully do the power transition: {POWER_STATE_S0} -> {POWER_STATE_S4}')
        return True

    def set_boot_to_uefi(self):
        if DpmoCfg.enable_ssh_conn:
            # todo: api implementation for setting default boot option here
            boot_to(self.sut, SUT_STATUS.S0.UEFI_SHELL)

    def wait_for_os(self):
        return self.sut.check_system_in_os(method='in')  # todo: check sut boot to os, no block checking

    def in_os(self, timeout):
        # todo: ping sut to check if it's really in os within timeout
        # todo: mostly used for checking after timeout happened or environment initialization
        start = time.time()
        while time.time() - start <= timeout:
            if self.sut.check_system_in_os():
                return True
            time.sleep(1)
        else:
            raise RuntimeError(f'not in os within: {timeout}')

    def idle(self, timeout):
        logger.info(f'idle {timeout}s ...')
        time.sleep(timeout)

    def stop(self):
        logger.info('stop os service ...')
        self.is_stop = True
        self.join(60)
        if self.is_alive():
            self.stop()

    def run(self):
        logger.info('os service is running ...')
        while not self.is_stop:
            if self.os_init:
                ready = self.in_os(60)
                if ready:
                    self.os_init = False
                    self.os_detect = False
                    self.event_queue.put_event(Event.SUT_IN_OS)

            if self.os_detect:
                ready = self.wait_for_os()
                if ready:
                    self.os_detect = False
                    self.event_queue.put_event(Event.SUT_IN_OS)
