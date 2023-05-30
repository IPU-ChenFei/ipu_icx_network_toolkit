from importlib import import_module
from dtaf_core.lib.tklib.basic.utility import get_config_item


CONFIG_PATH_TEMPLATE = r'tkconfig.{type}.{file_name}'


def bios_knob(knob):
    """
    Get bios knob settings from script level

    Demo Usage:
        from src.configuration.config import bios_knob
        s = bios_knob('enable_wol_knob_setting')
        print(s)    # ('WakeOnLanSupport', '0x1', 'WakeOnLanS5', '0x1')

    Args:
        knob: The knob item which defined in bios module level

    Returns: The knob definition or AttrubuteError if no such attribute found in bios module
    """
    config = get_config_item('platform_configuration', 'bios_knob')
    file_name = config.strip()
    if file_name.endswith('.py'):
        file_name = file_name.replace('.py', '')

    module = import_module(CONFIG_PATH_TEMPLATE.format(type="bios", file_name=file_name))

    return getattr(module, knob)


def sut_tool(name):
    """
    Get sut tools config from script level

    Demo Usage:
        from src.configuration.config import sut_tool
        t = sut_tool('SUT_TOOLS_LINUX_FIO')

    Args:
        name: The tool name you defined in sut_tools.py

    Returns: The tool definition or AttrubuteError if no such attribute found in sut_tools module
    """
    config = get_config_item('platform_configuration', 'sut_tools')
    file_name = config.strip()
    if file_name.endswith('.py'):
        file_name = file_name.replace('.py', '')

    module = import_module(CONFIG_PATH_TEMPLATE.format(type="sut_tool", file_name=file_name))

    return getattr(module, name)


def pysv_reg(name):
    """
    Get pythonsv register definition from script level

    Demo Usage:
        from src.configuration.config import pysv_reg
        s = pysv_reg('biosscratchpad6_cfg')

    Args:
        name: The name which defined in pysv_reg.py

    Returns: The reg definition or AttrubuteError if no such attribute found in pysv_reg module
    """
    config = get_config_item('platform_configuration', 'pysv_reg')
    file_name = config.strip()
    if file_name.endswith('.py'):
        file_name = file_name.replace('.py', '')

    module = import_module(CONFIG_PATH_TEMPLATE.format(type="pysv", file_name=file_name))

    return getattr(module, name)
