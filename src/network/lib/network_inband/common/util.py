#!/usr/bin/env python

from configparser import ConfigParser
import sys
import os
import re

from src.network.inband.common.log import log


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
            log.error(ex)
            return False

    @classmethod
    def read_cfg(cls, section, option, config=None):

        config = config if config else os.environ['CFG']
        path = os.path.abspath(config)
        if not os.path.exists(config):
            return ''
        try:
            parser = cls.NormalConfigParser()
            parser.read(config)
            return parser.get(section, option)
        except Exception as ex:
            log.error(ex)
            return ''

    @classmethod
    def read_cfg_tuple_to_list(cls, section, option, config=None):
        tuple_value = cls.read_cfg(section, option, config)
        return tuple_value.strip('()').replace(' ', '').replace('\n', '').split(',')


def parse_parameter(param):
    """
    Parameter format should be like: --name=value
    Space is not permitted in multiple values, but instead with comma
    """
    args = sys.argv[1:]
    for arg in args:
        if arg.startswith(f'--{param}='):
            return arg[len(f'--{param}='):]
    return ''


def check_output(pattern, string, error=None, minimal_matches=None):
    rs = re.findall(pattern, string, re.I)
    if not re:
        if error:
            raise RuntimeError(error)
        else:
            raise RuntimeError(f'cannot find {pattern} in {string}')
    else:
        if len(rs) < int(minimal_matches):
            if error:
                raise RuntimeError(error)
            else:
                raise RuntimeError(f'cannot find {pattern} in {string} with minimal_matches={minimal_matches}')


def check_condition(condition, error=None):
    if not condition:
        if error:
            raise RuntimeError(error)
        else:
            raise RuntimeError(f'{condition} is not true')