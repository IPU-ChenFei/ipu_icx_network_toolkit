#!/usr/bin/env python

import threading
import time

from dtaf_core.lib.tklib.basic.const import SUT_STATUS
from dtaf_core.lib.tklib.infra.sut import get_default_sut

from src.dpmo.lib.config import *
from src.dpmo.lib.event import *

sut = get_default_sut()
POWER_STATE_S0 = SUT_STATUS.S0
POWER_STATE_S3 = SUT_STATUS.S3
POWER_STATE_S4 = SUT_STATUS.S4
POWER_STATE_S5 = SUT_STATUS.S5
POWER_STATE_G3 = SUT_STATUS.G3
POWER_STATE_UNKNOWN = SUT_STATUS.UNKNOWN


class PowerService(threading.Thread):
    def __init__(self, sut):
        super().__init__(daemon=True)
        self.sut = sut

        self.is_stop = False
        self.__power_init = True
        self.__power_detect = True
        self.event_queue = EventQueue()
        self.__s0_detect = True
        self.__s3_detect = False
        self.__s4_detect = False
        self.__s5_detect = False
        self.__s3_is_detected = False
        self.__s4_is_detected = False
        self.__s5_is_detected = False
        self.__last_power_state = None
        self.__last_change_time = None

    @property
    def s3_is_detected(self):
        return self.__s3_is_detected

    @s3_is_detected.setter
    def s3_is_detected(self, value):
        self.__s3_is_detected = value

    @property
    def s4_is_detected(self):
        return self.__s4_is_detected

    @s4_is_detected.setter
    def s4_is_detected(self, value):
        self.__s4_is_detected = value

    @property
    def s5_is_detected(self):
        return self.__s5_is_detected

    @s5_is_detected.setter
    def s5_is_detected(self, value):
        self.__s5_is_detected = value

    @property
    def last_power_state(self):
        return self.__last_power_state

    @last_power_state.setter
    def last_power_state(self, value):
        self.__last_power_state = value

    @property
    def last_change_time(self):
        return self.__last_change_time

    @last_change_time.setter
    def last_change_time(self, value):
        self.__last_change_time = value

    @property
    def s0_detect(self):
        return self.__s0_detect

    @s0_detect.setter
    def s0_detect(self, value):
        self.__s0_detect = value

    @property
    def s3_detect(self):
        return self.__s3_detect

    @s3_detect.setter
    def s3_detect(self, value):
        self.__s3_detect = value

    @property
    def s4_detect(self):
        return self.__s4_detect

    @s4_detect.setter
    def s4_detect(self, value):
        self.__s4_detect = value

    @property
    def s5_detect(self):
        return self.__s5_detect

    @s5_detect.setter
    def s5_detect(self, value):
        self.__s5_detect = value

    @property
    def power_detect(self):
        return self.__power_detect

    @power_detect.setter
    def power_detect(self, value):
        self.__power_detect = value

    @property
    def power_init(self):
        return self.__power_init

    @power_init.setter
    def power_init(self, value):
        self.__power_init = value

    def wait_for_power(self, state, timeout):  # todo:
        return self.sut.wait_for_power_status(state, timeout)

    def ac_off(self, timeout):
        # todo: doing ac off action here
        self.sut.ac_off()
        if not self.wait_for_power(POWER_STATE_G3, timeout):
            logger.error(f'fail to wait for power: {POWER_STATE_G3}')
            return False
        logger.info(f'successfully do the power transition: Unknown -> {POWER_STATE_G3}')
        return True

    def ac_on(self, timeout):
        self.sut.ac_on()
        # todo: doing ac on action here
        if not self.wait_for_power(POWER_STATE_S0, timeout):
            logger.error(f'fail to wait for power: {POWER_STATE_S0}')
            return False
        logger.info(f'successfully do the power transition: {POWER_STATE_G3} -> {POWER_STATE_S0}')
        return True

    def get_power_state(self):  # todo: try many times to get power states
        pwst = self.sut.get_power_status()  # default to try many times to get power states
        logger.info(f'current power state: {pwst}')

        return pwst

    def ac_on_from_g3_to_s0(self, timeout):
        state = self.get_power_state()
        if not state == POWER_STATE_G3:
            logger.error(f'current state is not in: {POWER_STATE_G3}')
            return False
        self.sut.ac_on()
        # todo: doing ac on action here

        if not self.wait_for_power(POWER_STATE_S0, timeout):
            logger.error(f'fail to wait for power: {POWER_STATE_S0}')
            return False
        logger.info(f'successfully do the power transition: {POWER_STATE_G3} -> {POWER_STATE_S0}')
        return True

    def ac_on_from_g3_to_s5(self, timeout):
        state = self.get_power_state()
        if not state == POWER_STATE_G3:
            logger.error(f'current state is not in: {POWER_STATE_G3}')
            return False
        self.sut.ac_on()
        # todo: doing ac on action here

        if not self.wait_for_power(POWER_STATE_S5, timeout):
            logger.error(f'fail to wait for power: {POWER_STATE_S5}')
            return False
        logger.info(f'successfully do the power transition: {POWER_STATE_G3} -> {POWER_STATE_S5}')
        return True

    def ac_off_from_s5_to_g3(self, timeout):
        state = self.get_power_state()
        if not state == POWER_STATE_S5:
            logger.error(f'current state is not in: {POWER_STATE_S5}')
            return False
        self.sut.ac_off()
        # todo: doing ac off action here

        if not self.wait_for_power(POWER_STATE_G3, timeout):
            logger.error(f'fail to wait for power: {POWER_STATE_G3}')
            return False
        logger.info(f'successfully do the power transition: {POWER_STATE_S5} -> {POWER_STATE_G3}')
        return True

    def ac_off_from_s0_to_g3(self, timeout):
        state = self.get_power_state()
        if not state == POWER_STATE_S0:
            logger.error(f'current state is not in: {POWER_STATE_S0}')
            return False
        self.sut.ac_off()
        # todo: doing ac off action here

        if not self.wait_for_power(POWER_STATE_G3, timeout):
            logger.error(f'fail to wait for power: {POWER_STATE_G3}')
            return False
        logger.info(f'successfully do the power transition: {POWER_STATE_S0} -> {POWER_STATE_G3}')
        return True

    def dc_on_from_s5_to_s0(self, timeout):
        # state = self.get_power_state()
        # if not state == POWER_STATE_G3:
        #     logger.error(f'current state is not in: {POWER_STATE_G3}')
        #     return False
        self.sut.dc_on()
        # todo: doing dc on action here

        if not self.wait_for_power(POWER_STATE_S0, timeout):
            logger.error(f'fail to wait for power: {POWER_STATE_S0}')
            return False
        logger.info(f'successfully do the power transition: {POWER_STATE_S5} -> {POWER_STATE_S0}')
        return True

    def dc_on_from_s3_to_s0(self, timeout):
        state = self.get_power_state()
        if not state == POWER_STATE_S3:
            logger.error(f'current state is not in: {POWER_STATE_S3}')
            return False
        self.sut.dc_on()
        # todo: doing dc on action here

        if not self.wait_for_power(POWER_STATE_S0, timeout):
            logger.error(f'fail to wait for power: {POWER_STATE_S0}')
            return False
        logger.info(f'successfully do the power transition: {POWER_STATE_S3} -> {POWER_STATE_S0}')
        return True

    def dc_on_from_s4_to_s0(self, timeout):
        state = self.get_power_state()
        if not state == POWER_STATE_S4:
            logger.error(f'current state is not in: {POWER_STATE_S4}')
            return False
        self.sut.dc_on()
        # todo: doing dc on action here

        if not self.wait_for_power(POWER_STATE_S0, timeout):
            logger.error(f'fail to wait for power: {POWER_STATE_S0}')
            return False
        logger.info(f'successfully do the power transition: {POWER_STATE_S4} -> {POWER_STATE_S0}')
        return True

    def dc_off_from_s0_to_s5(self, timeout):
        state = self.get_power_state()
        if not state == POWER_STATE_S0:
            logger.error(f'current state is not in: {POWER_STATE_S0}')
            return False
        self.sut.dc_off()
        # todo: doing dc off action here

        if not self.wait_for_power(POWER_STATE_S5, timeout):
            logger.error(f'fail to wait for power: {POWER_STATE_S5}')
            return False
        logger.info(f'successfully do the power transition: {POWER_STATE_S0} -> {POWER_STATE_S5}')
        return True

    def detect_stable_power(self, state, timeout):
        # check power stability during timeout
        start_time = time.time()
        while time.time() - start_time <= timeout:
            current_state = self.get_power_state()
            if current_state != state:
                return False
        return True

    def idle(self, timeout):
        logger.info(f'idle {timeout}s ...')
        time.sleep(timeout)

    def stop(self):
        logger.info('stop power service ...')
        self.is_stop = True
        self.join(60)
        if self.is_alive():
            self.stop()

    def run(self):
        logger.info('power service is running ...')
        while not self.is_stop:
            state = self.get_power_state()
            time.sleep(0.5)

            # <<< state s0: only used for environment initialization >>>
            if state == POWER_STATE_S0 and self.s0_detect:
                self.event_queue.put_event(Event.SUT_IN_S0)
                self.s0_detect = False

            # unknown state
            if state == POWER_STATE_UNKNOWN:
                raise RuntimeError(f'cannot detect power state correctly, state={state}')

            # unstable state
            if self.power_detect:
                if state == self.last_power_state:
                    if time.time() - self.last_change_time > DpmoCfg.consistent_power_state_checking_time:
                        if state == POWER_STATE_S3:
                            self.power_detect = False
                            if self.s3_detect:
                                self.event_queue.put_event(Event.SUT_IN_S3)

                            else:
                                self.event_queue.put_event(Event.SUT_IN_AUTO_SLEEP)

                        if state == POWER_STATE_S4:
                            self.power_detect = False
                            if self.s4_detect:
                                self.event_queue.put_event(Event.SUT_IN_S4)
                            else:
                                self.event_queue.put_event(Event.SUT_IN_AUTO_HIBERNATE)
                        if state == POWER_STATE_S5:
                            self.power_detect = False
                            if self.s5_detect:
                                self.event_queue.put_event(Event.SUT_IN_S5)

                            else:
                                self.event_queue.put_event(Event.SUT_IN_AUTO_SHUTDOWN)
                        if state == POWER_STATE_G3:
                            self.power_detect = False
                            self.event_queue.put_event(Event.SUT_IN_G3)

                else:
                    # current state is: s0, and previous state is: s5
                    if state == POWER_STATE_S5:
                        self.s5_is_detected = True
                    else:
                        if state == POWER_STATE_S0 and self.s5_is_detected:
                            self.s5_is_detected = False
                            self.event_queue.put_event(Event.SUT_IN_AUTO_RESET_S5)

                    # current state is: s0, and previous state is: s3
                    if state == POWER_STATE_S3:
                        self.s3_is_detected = True
                    else:
                        if state == POWER_STATE_S0 and self.s3_is_detected:
                            self.s3_is_detected = False
                            self.event_queue.put_event(Event.SUT_IN_AUTO_RESET_S3)

                    # current state is: s0, and previous state is: s4
                    if state == POWER_STATE_S4:
                        self.s4_is_detected = True
                    else:
                        if state == POWER_STATE_S0 and self.s4_is_detected:
                            self.s4_is_detected = False
                            self.event_queue.put_event(Event.SUT_IN_AUTO_RESET_S4)

                    # if power state changed, update below variable
                    self.last_change_time = time.time()
                    self.last_power_state = state
            else:
                # clean internal variable
                self.s3_is_detected = False
                self.s4_is_detected = False
                self.s5_is_detected = False
                self.last_power_state = None
                self.last_change_time = None

#
# def main():
#     ps = PowerService()
#     ps.start()
#     logger.info('============================')
#     logger.info(ps.event_queue.get_event())
#
#
# if __name__ == '__main__':
#     main()
