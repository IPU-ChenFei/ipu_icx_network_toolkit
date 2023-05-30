#!/usr/bin/env python


from src.dpmo.lib.bios_service import BiosService
from src.dpmo.lib.os_service import OsService
from src.dpmo.lib.power_service import PowerService
from src.dpmo.lib.test_report import *
from src.dpmo.lib.test_scenario import *


def print_help():
    # todo: print all required information for users
    DpmoCfg.show_dpmo_config()
    logger.info('after 30s, dpmo testing will be started ...')
    time.sleep(3)


class TestBase:
    def __init__(self):
        self.test_cls = None
        self.bios_service = BiosService()
        self.power_service = PowerService(sut)
        self.os_service = OsService(sut)
        self.monitor_service = MonitorService()
        self.test_report = TestReport()
        self.event_queue = EventQueue()

    def prepare(self):
        print_help()
        self.test_scenario = create_test_scenario(self.test_cls,
                                                  self.bios_service,
                                                  self.power_service,
                                                  self.os_service,
                                                  self.monitor_service,
                                                  self.test_report)

        # start running service
        self.bios_service.start()
        self.power_service.start()
        self.os_service.start()
        self.monitor_service.start()

    def cleanup(self):
        # stop running service
        self.bios_service.stop()
        self.power_service.stop()
        self.os_service.stop()
        self.monitor_service.stop()

    def test_entry(self):
        self.prepare()
        try:
            while True:
                event = self.event_queue.get_event()
                logger.info(f'Event: {event}')
                result = self._event_handler(event)
                if not result:
                    continue
                else:
                    return result
        finally:
            self.cleanup()
            self.test_report.print_table()

    def _event_handler(self, event):
        if event == Event.SUT_IN_G3:
            return self.test_scenario.sut_in_g3()
        elif event == Event.SUT_IN_S5:
            return self.test_scenario.sut_in_s5()
        elif event == Event.SUT_IN_S4:
            return self.test_scenario.sut_in_s4()
        elif event == Event.SUT_IN_S3:
            return self.test_scenario.sut_in_s3()
        elif event == Event.SUT_IN_S0:
            return self.test_scenario.sut_in_s0()
        elif event == Event.SUT_IN_OS:
            return self.test_scenario.sut_in_os()
        elif event == Event.SUT_IN_UEFI:
            return self.test_scenario.sut_in_uefi()
        elif event == Event.SUT_IN_TIMEOUT:
            return self.test_scenario.sut_in_timeout()
        elif event == Event.SUT_IN_AUTO_SLEEP:
            return self.test_scenario.sut_in_auto_sleep()
        elif event == Event.SUT_IN_AUTO_HIBERNATE:
            return self.test_scenario.sut_in_auto_hibernate()
        elif event == Event.SUT_IN_AUTO_SHUTDOWN:
            return self.test_scenario.sut_in_auto_shutdown()
        elif event == Event.SUT_IN_AUTO_RESET_S3:
            return self.test_scenario.sut_in_auto_reset_s3()
        elif event == Event.SUT_IN_AUTO_RESET_S4:
            return self.test_scenario.sut_in_auto_reset_s4()
        elif event == Event.SUT_IN_AUTO_RESET_S5:
            return self.test_scenario.sut_in_auto_reset_s5()
        else:
            logger.warning(f'Unhandled Event: {event}')
