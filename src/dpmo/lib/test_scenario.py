#!/usr/bin/env python

import inspect
from functools import wraps

from dtaf_core.lib.tklib.infra.debug.debug import dpmo_check, customized_check, Debug

from src.dpmo.lib.monitor_service import *
from src.dpmo.lib.power_service import sut


# from src.lib.toolkit.infra.sut import get_default_sut


def func_name():
    return inspect.currentframe().f_back.f_code.co_name


def sut_status(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        name = func.__name__
        logger.info(f'sut status: {name}')
        return func(*args, **kwargs)

    return wrapper


TEST_PASS = 1
TEST_FAIL = -1


class TestScenario:
    def __init__(self, bios_service, power_service, os_service, monitor_service, test_report):
        self.power_service = power_service
        self.os_service = os_service
        self.bios_service = bios_service
        self.monitor_service = monitor_service
        self.test_report = test_report
        self.current_cycle = 0
        self.target_cycle = DpmoCfg.target_running_cycles

    # Power scenarios
    @sut_status
    def sut_in_g3(self):
        pass

    @sut_status
    def sut_in_s5(self):
        pass

    @sut_status
    def sut_in_s4(self):
        pass

    @sut_status
    def sut_in_s3(self):
        pass

    @sut_status
    def sut_in_s0(self):
        self.power_service.power_detect = True
        if DpmoCfg.os_boot_target == 'os':
            self.os_service.os_detect = True
        else:
            self.bios_service.uefi_detect = True

    # Environment scenarios
    @sut_status
    def sut_in_os(self):
        pass

    @sut_status
    def sut_in_uefi(self):
        pass

    @sut_status
    def sut_in_auto_sleep(self):
        if DpmoCfg.stop_when_auto_sleep:
            return TEST_FAIL
        else:
            self.power_service.dc_on_from_s3_to_s0(DpmoCfg.power_transition_max_waiting_time)
            self.power_service.power_detect = True
            self.power_service.s0_detect = True

    @sut_status
    def sut_in_auto_hibernate(self):
        if DpmoCfg.stop_when_auto_sleep:
            return TEST_FAIL
        else:
            self.power_service.dc_on_from_s4_to_s0(DpmoCfg.power_transition_max_waiting_time)
            self.power_service.power_detect = True
            self.power_service.s0_detect = True

    @sut_status
    def sut_in_auto_shutdown(self):
        if DpmoCfg.stop_when_auto_sleep:
            return TEST_FAIL
        else:
            self.power_service.dc_on_from_s5_to_s0(DpmoCfg.power_transition_max_waiting_time)
            self.power_service.power_detect = True
            self.power_service.s0_detect = True

    @sut_status
    def sut_in_auto_reset_s3(self):
        if DpmoCfg.stop_when_auto_reset_s3:
            return TEST_FAIL
        else:
            self.power_service.power_detect = True
            self.power_service.s0_detect = True

    @sut_status
    def sut_in_auto_reset_s4(self):
        if DpmoCfg.stop_when_auto_reset_s4:
            return TEST_FAIL
        else:
            self.power_service.power_detect = True
            self.power_service.s0_detect = True

    @sut_status
    def sut_in_auto_reset_s5(self):
        if DpmoCfg.stop_when_auto_reset_s5:
            return TEST_FAIL
        else:
            self.power_service.power_detect = True
            self.power_service.s0_detect = True

    @sut_status
    def sut_in_timeout(self):
        if DpmoCfg.stop_when_cycle_timeout:
            return TEST_FAIL
        else:
            # clean internal variable
            self.power_service.power_detect = False

            if DpmoCfg.enable_fail_safe_mode:
                self.power_service.ac_off(DpmoCfg.power_transition_max_waiting_time)
                self.power_service.ac_on(DpmoCfg.power_transition_max_waiting_time)
                self.power_service.power_detect = True
                self.power_service.s0_detect = True
            else:
                # only enable timeout handler in s0 (check if really in os/uefi)
                # mostly it is caused by os/uefi communication error
                if DpmoCfg.os_boot_target == 'os':
                    self.os_service.os_init = True
                else:
                    self.bios_service.uefi_init = True

    def _start_new_cycle(self):
        # start a new cycle here
        if self.current_cycle >= self.target_cycle:
            logger.info(f'TEST PASS: test finished with {self.target_cycle} cycles ...')
            return TEST_PASS
        self.current_cycle += 1
        logger.info(f'IN CYCLE: {self.current_cycle} ...')
        self.monitor_service.start_time = time.time()
        self.bios_service.save_log(os.path.join(f'{DpmoCfg.bios_log}', f'bios_{self.current_cycle}.log'))


class G3General(TestScenario):
    # Flow: G3 -> AC ON -> OS/UEFI -> Shutdown -> S5 -> AC OFF -> G3 -> ...
    def sut_in_g3(self):
        super().sut_in_g3()
        self.power_service.idle(DpmoCfg.ac_off_to_g3_sleep_time)
        if self._start_new_cycle(): return TEST_PASS
        self.power_service.ac_on_from_g3_to_s0(DpmoCfg.power_transition_max_waiting_time)
        self.power_service.power_detect = True
        self.power_service.s0_detect = True

    def sut_in_s5(self):
        super().sut_in_s5()
        self.power_service.ac_off_from_s5_to_g3(DpmoCfg.power_transition_max_waiting_time)
        self.power_service.power_detect = True

    def sut_in_s4(self):
        super().sut_in_s4()
        return TEST_FAIL

    def sut_in_s3(self):
        super().sut_in_s3()
        return TEST_FAIL

    def sut_in_os(self):
        # super().sut_in_os()
        self.os_service.idle(DpmoCfg.os_dile_time)
        dpmo_check(sut, self.current_cycle)
        customized_check(sut, self.current_cycle)
        self.os_service.shutdown(DpmoCfg.power_transition_max_waiting_time)
        self.power_service.power_detect = True
        self.power_service.s5_detect = True

    def sut_in_uefi(self):
        super().sut_in_uefi()
        self.bios_service.idle(DpmoCfg.os_dile_time)
        # dpmo_check(sut, self.current_cycle)
        # customized_check(sut, self.current_cycle)
        self.bios_service.shutdown(DpmoCfg.power_transition_max_waiting_time)
        self.power_service.power_detect = True
        self.power_service.s5_detect = True


class G3DcOn(G3General):
    # Flow: G3 -> AC ON -> S5 -> DC ON -> OS/UEFI -> Shutdown -> S5 -> AC OFF -> G3 -> ...
    def sut_in_g3(self):
        # super().sut_in_g3()
        self.power_service.idle(DpmoCfg.ac_off_to_g3_sleep_time)
        if self._start_new_cycle(): return TEST_PASS
        self.power_service.ac_on_from_g3_to_s0(DpmoCfg.power_transition_max_waiting_time)
        self.power_service.power_detect = True
        self.power_service.s0_detect = True


class G3Surprise(G3General):
    # Flow: G3 -> AC ON -> OS/UEFI -> AC OFF -> G3 -> ...
    def sut_in_os(self):
        # super().sut_in_os()
        self.os_service.idle(DpmoCfg.os_dile_time)
        # todo: plug information check here, fill in result table
        dpmo_check(sut, self.current_cycle)
        customized_check(sut, self.current_cycle)
        self.power_service.ac_off_from_s0_to_g3(DpmoCfg.power_transition_max_waiting_time)

    def sut_in_uefi(self):
        super().sut_in_uefi()
        self.bios_service.idle(DpmoCfg.os_dile_time)
        # todo: plug information check here, fill in result table
        # dpmo_check(sut, self.current_cycle)
        # customized_check(sut, self.current_cycle)
        self.power_service.ac_off_from_s0_to_g3(DpmoCfg.power_transition_max_waiting_time)


class G3SurpriseDcOn(G3Surprise):
    # Flow: G3 -> AC ON -> OS/UEFI -> Shutdown -> S5 -> DC ON -> OS/UEFI -> AC OFF -> G3 -> ...
    def sut_in_s5(self):
        # super().sut_in_s5()
        self.power_service.dc_on_from_s5_to_s0(DpmoCfg.power_transition_max_waiting_time)
        self.power_service.power_detect = True
        self.power_service.s0_detect = True


class S5General(TestScenario):
    # Flow: S5 -> DC ON -> OS/UEFI -> Shutdown -> S5 -> ...
    def sut_in_g3(self):
        super().sut_in_g3()
        return TEST_FAIL

    def sut_in_s5(self):
        super().sut_in_s5()
        if self._start_new_cycle(): return TEST_PASS
        self.power_service.dc_on_from_s5_to_s0(DpmoCfg.power_transition_max_waiting_time)
        self.power_service.power_detect = True
        self.power_service.s0_detect = True

    def sut_in_s4(self):
        super().sut_in_s4()
        return TEST_FAIL

    def sut_in_s3(self):
        super().sut_in_s3()
        return TEST_FAIL

    def sut_in_os(self):
        # super().sut_in_os()
        self.os_service.idle(DpmoCfg.os_dile_time)
        # todo: plug information check here, fill in result table
        dpmo_check(sut, self.current_cycle)
        customized_check(sut, self.current_cycle)
        self.os_service.shutdown(DpmoCfg.power_transition_max_waiting_time)
        self.power_service.power_detect = True
        self.power_service.s5_detect = True

    def sut_in_uefi(self):
        super().sut_in_uefi()
        self.bios_service.idle(DpmoCfg.os_dile_time)
        # todo: plug information check here, fill in result table
        # dpmo_check(sut, self.current_cycle)
        # customized_check(sut, self.current_cycle)
        self.power_service.ac_off_from_s0_to_g3(DpmoCfg.power_transition_max_waiting_time)


class S3General(TestScenario):
    # Flow: S3 -> DC ON -> OS/UEFI -> Sleep -> S3 -> ...
    def sut_in_g3(self):
        super().sut_in_g3()
        return TEST_FAIL

    def sut_in_s5(self):
        super().sut_in_s5()
        return TEST_FAIL

    def sut_in_s4(self):
        super().sut_in_s4()
        return TEST_FAIL

    def sut_in_s3(self):
        super().sut_in_s3()
        if self._start_new_cycle(): return TEST_PASS
        self.power_service.dc_on_from_s3_to_s0(DpmoCfg.power_transition_max_waiting_time)
        self.power_service.power_detect = True
        self.power_service.s0_detect = True

    def sut_in_os(self):
        super().sut_in_os()
        self.os_service.idle(DpmoCfg.os_dile_time)
        # todo: plug information check here, fill in result table
        dpmo_check(sut, self.current_cycle)
        customized_check(sut, self.current_cycle)
        self.os_service.sleep(DpmoCfg.power_transition_max_waiting_time)
        self.power_service.power_detect = True
        self.power_service.s5_detect = False

    def sut_in_uefi(self):
        super().sut_in_uefi()
        self.bios_service.idle(DpmoCfg.os_dile_time)
        # todo: plug information check here, fill in result table
        # dpmo_check(sut, self.current_cycle)
        # customized_check(sut, self.current_cycle)
        self.power_service.ac_off_from_s0_to_g3(DpmoCfg.power_transition_max_waiting_time)
        self.power_service.power_detect = True
        self.power_service.s5_detect = False


class ResetGeneral(TestScenario):
    # Flow: OS/UEFI -> Reset -> OS/UEFI -> ...
    def sut_in_g3(self):
        super().sut_in_g3()
        return TEST_FAIL

    def sut_in_s5(self):
        super().sut_in_s5()
        return TEST_FAIL

    def sut_in_s4(self):
        super().sut_in_s4()
        return TEST_FAIL

    def sut_in_s3(self):
        super().sut_in_s3()
        return TEST_FAIL

    def sut_in_os(self):
        super().sut_in_os()
        self.os_service.idle(DpmoCfg.os_dile_time)
        if self._start_new_cycle(): return TEST_PASS
        # todo: plug information check here, fill in result table
        dpmo_check(sut, self.current_cycle)
        customized_check(sut, self.current_cycle)
        self.os_service.reset()
        self.os_service.os_detect = True
        self.power_service.power_detect = True
        self.power_service.s0_detect = True

    def sut_in_uefi(self):
        super().sut_in_uefi()
        self.bios_service.idle(DpmoCfg.os_dile_time)
        # todo: plug information check here, fill in result table
        # dpmo_check(sut, self.current_cycle)
        # customized_check(sut, self.current_cycle)
        self.bios_service.reset(DpmoCfg.power_transition_max_waiting_time)
        self.bios_service.uefi_detect = True
        self.power_service.power_detect = True
        self.power_service.s0_detect = True


class ResetUefi2Os(ResetGeneral):
    # Flow: OS -> Reset -> UEFI -> Continue -> OS -> ...
    def sut_in_g3(self):
        super().sut_in_g3()
        return TEST_FAIL

    def sut_in_s5(self):
        super().sut_in_s5()
        return TEST_FAIL

    def sut_in_s4(self):
        super().sut_in_s4()
        return TEST_FAIL

    def sut_in_s3(self):
        super().sut_in_s3()
        return TEST_FAIL

    def sut_in_os(self):
        # super().sut_in_os()
        self.os_service.idle(DpmoCfg.os_dile_time)
        if self._start_new_cycle(): return TEST_PASS
        # todo: plug information check here, fill in result table
        dpmo_check(sut, self.current_cycle)
        customized_check(sut, self.current_cycle)
        # self.os_service.set_boot_to_uefi()
        self.os_service.bootfirst()
        self.os_service.reset()
        self.bios_service.uefi_detect = True

        # self.power_service.power_detect = True
        # self.power_service.s0_detect = True

    def sut_in_uefi(self):
        # super().sut_in_uefi()
        self.bios_service.idle(DpmoCfg.os_dile_time)
        self.bios_service.set_boot_to_os()
        self.os_service.os_detect = True
        self.power_service.power_detect = True
        self.power_service.s0_detect = True


def create_test_scenario(cls, bios_service, power_service, os_service, monitor_service, test_report):
    if cls == 'G3General': return G3General(bios_service, power_service, os_service, monitor_service, test_report)
    if cls == 'G3DcOn': return G3DcOn(bios_service, power_service, os_service, monitor_service, test_report)
    if cls == 'G3Surprise': return G3Surprise(bios_service, power_service, os_service, monitor_service, test_report)
    if cls == 'G3SurpriseDcOn': return G3SurpriseDcOn(bios_service, power_service, os_service, monitor_service,
                                                      test_report)
    if cls == 'S5General': return S5General(bios_service, power_service, os_service, monitor_service, test_report)
    if cls == 'GeneralS3': return S3General(bios_service, power_service, os_service, monitor_service, test_report)
    if cls == 'ResetGeneral': return ResetGeneral(bios_service, power_service, os_service, monitor_service, test_report)
    if cls == 'Uefi2OsReset': return ResetUefi2Os(bios_service, power_service, os_service, monitor_service, test_report)


def get_report_dict():
    debug = Debug(sut)
    x_dict = getattr(debug, "dpmo_check_result")
    # r_json = [{"record_windows_system_cfg_1": True},
    #           {"record_windows_event_log1": True},
    #           {"record_windows_system_cfg2": False},
    #           {"record_windows_event_log2": True}]
    r_dict = {}
    for k, v in sut.dpmo_check.items():
        if v is True:
            r_list = []
            for x in x_dict:
                for k1, v1 in x.items():
                    if k in k1 and v1 == True:
                        r_list.append(int(k1.replace(k, "")))
            r_dict[k] = r_list

    return r_dict
