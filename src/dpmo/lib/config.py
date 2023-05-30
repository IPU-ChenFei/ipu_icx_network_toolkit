#!/usr/bin/env python

from configparser import ConfigParser
from dtaf_core.lib.tklib.basic.log import logger
from dtaf_core.lib.tklib.basic.config import LOG_PATH
import os


class CFGParser:
    class NormalConfigParser(ConfigParser):
        def __init__(self, defaults=None):
            ConfigParser.__init__(self, defaults=defaults)

        def optionxform(self, optionstr):
            return optionstr

    @classmethod
    def init_cfg(cls, config):
        os.environ['CFG'] = config

    @classmethod
    def write_cfg(cls, section, option, value, config=None):
        config = config if config else os.environ['CFG']
        if not os.path.exists(config):
            return False
        try:
            parser = cls.NormalConfigParser()
            parser.read(config)
            if not parser.has_section(section):
                parser.add_section(section)
            value = value if value else ''
            parser.set(section, option, value)
            with open(config, 'r+') as fp:
                parser.write(fp)
            return True
        except Exception as ex:
            logger.error(ex)
            return False

    @classmethod
    def read_cfg(cls, section, option, config=None):
        config = config if config else os.environ['CFG']
        if not os.path.exists(config):
            return ''
        try:
            parser = cls.NormalConfigParser()
            parser.read(config)
            return parser.get(section, option)
        except Exception as ex:
            logger.error(ex)
            return ''


config = os.path.join(os.pardir, 'dpmo.ini')
CFGParser.init_cfg(config)


class DpmoCfg:
    # dpmo.ini
    os_dile_time = float(CFGParser.read_cfg('dpmo', 'os_idle_time'))
    one_cycle_max_time = float(CFGParser.read_cfg('dpmo', 'one_cycle_max_time'))
    target_running_cycles = int(CFGParser.read_cfg('dpmo', 'target_running_cycles'))
    power_transition_max_waiting_time = float(CFGParser.read_cfg('dpmo', 'power_transition_max_waiting_time'))
    ac_off_to_g3_sleep_time = float(CFGParser.read_cfg('dpmo', 'ac_off_to_g3_sleep_time'))
    consistent_power_state_checking_time = float(CFGParser.read_cfg('dpmo', 'consistent_power_state_checking_time'))
    time_consuming_warning_limit_between_cycles = \
        float(CFGParser.read_cfg('dpmo', 'time_consuming_warning_limit_between_cycles'))
    time_consuming_warning_limit_between_power_on_and_bios_output = \
        float(CFGParser.read_cfg('dpmo', 'time_consuming_warning_limit_between_power_on_and_bios_output'))
    os_boot_target = CFGParser.read_cfg('dpmo', 'os_boot_target')
    enable_ssh_conn = bool(CFGParser.read_cfg('dpmo', 'enable_ssh_conn'))
    uart_write_block = bool(CFGParser.read_cfg('dpmo', 'uart_write_block'))
    os_boot_entry = CFGParser.read_cfg('dpmo', 'os_boot_entry')
    stop_when_cycle_timeout = bool(CFGParser.read_cfg('dpmo', 'stop_when_cycle_timeout'))
    enable_fail_safe_mode = bool(CFGParser.read_cfg('dpmo', 'enable_fail_safe_mode'))
    stop_when_auto_sleep = bool(CFGParser.read_cfg('dpmo', 'stop_when_auto_sleep'))
    stop_when_auto_hibernate = bool(CFGParser.read_cfg('dpmo', 'stop_when_auto_hibernate'))
    stop_when_auto_shutdown = bool(CFGParser.read_cfg('dpmo', 'stop_when_auto_shutdown'))
    stop_when_auto_reset_s3 = bool(CFGParser.read_cfg('dpmo', 'stop_when_auto_reset_s3'))
    stop_when_auto_reset_s4 = bool(CFGParser.read_cfg('dpmo', 'stop_when_auto_reset_s4'))
    stop_when_auto_reset_s5 = bool(CFGParser.read_cfg('dpmo', 'stop_when_auto_reset_s5'))

    # debug.ini/[dpmo_check]
    # todo: get all check_ items from [dpmo_check] section
    dpmo_check_list = []

    # log path
    bios_log = os.path.join(LOG_PATH, 'bios')
    if not os.path.exists(bios_log):
        os.makedirs(bios_log)

    @classmethod
    def show_dpmo_config(cls):
        logger.info(f'========== DPMO Configuration OPTION ({config}) ==========')
        for m in dir(cls):
            if not (m.startswith('__') or callable(getattr(cls, m))):
                logger.info(f'{m}: {getattr(cls, m)}')
