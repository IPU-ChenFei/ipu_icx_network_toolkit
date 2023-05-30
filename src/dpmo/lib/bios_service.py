#!/usr/bin/env python

from src.dpmo.lib.power_service import *
from dtaf_core.lib.tklib.infra.bios.bios import init_bios
from dtaf_core.lib.tklib.basic.log import logger


class BiosService(threading.Thread):
    def __init__(self):
        super().__init__(daemon=True)
        self.bios = init_bios()  # todo: create bios obj
        # self.uefi = None    # todo: create uefi obj
        self.__uefi_detect = False
        self.is_stop = False
        self.event_queue = EventQueue()
        self.power_service = PowerService(sut)
        self.__uefi_init = False

    @property
    def uefi_init(self):
        return self.__uefi_init

    @uefi_init.setter
    def uefi_init(self, value):
        self.__uefi_init = value

    @property
    def uefi_detect(self):
        return self.__uefi_detect

    @uefi_detect.setter
    def uefi_detect(self, value):
        self.__uefi_detect = value

    def reset(self):
        if DpmoCfg.uart_write_block:
            self.bios.uefi_reboot()
            # self.uefi.reset()  # todo:

    def shutdown(self, timeout):
        if DpmoCfg.uart_write_block:
            # self.uefi.shutdown()  # todo:
            self.bios.uefi_shutdown()
        if not self.power_service.wait_for_power(POWER_STATE_S5, timeout):
            logger.error(f'fail to wait for power: {POWER_STATE_S5}')
            return False
        logger.info(f'successfully do the power transition: {POWER_STATE_S0} -> {POWER_STATE_S5}')
        return True

    def sleep(self):
        raise NotImplementedError

    def hibernate(self):
        raise NotImplementedError

    def set_boot_to_os(self):
        if DpmoCfg.uart_write_block:
            # self.uefi.execute(DpmoCfg.os_boot_entry)
            self.bios.uefi_shell_execute(DpmoCfg.os_boot_entry)

    def wait_for_uefi(self, timeout=600):
        start = time.time()
        while time.time() - start <= timeout:
            if self.in_uefi(timeout=5):
                return True
            else:
                continue
        logger.error(f"Fail to enter uefi shell within {timeout}s")
        return False
        # return self.uefi.wait_for_uefi()  # todo: check sut boot to uefi, no blocking checking

    def in_uefi(self, timeout):
        # todo: run uefi cmd to check if it's really in uefi within timeout
        # todo: mostly used for checking after timeout happened or environment initialization
        start = time.time()
        while time.time() - start <= timeout:
            # if self.uefi.in_uefi():
            if self.bios.in_uefi():
                return True
            time.sleep(1)
        # else:
        #     raise RuntimeError(f'not in uefi within: {timeout}')

    def idle(self, timeout):
        logger.info(f'idle {timeout}s ...')
        time.sleep(timeout)

    def save_log(self, filename):
        self.bios.bios_log.redirect(filename)

    def stop(self):
        logger.info('stop bios service ...')
        self.is_stop = True
        self.join(60)
        if self.is_alive():
            self.stop()

    def run(self):
        logger.info('bios service is running ...')
        while not self.is_stop:
            if self.uefi_init:
                ready = self.in_uefi(60)
                if ready:
                    self.uefi_init = False
                    self.uefi_detect = False
                    self.event_queue.put_event(Event.SUT_IN_UEFI)

            if self.uefi_detect:

                ready = self.wait_for_uefi()
                if ready:
                    self.uefi_detect = False
                    self.event_queue.put_event(Event.SUT_IN_UEFI)
