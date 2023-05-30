#!/usr/bin/env python3
# noinspection PyUnresolvedReferences
import time
from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.infra.sut import *
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to
from dtaf_core.lib.tklib.steps_lib.uefi_scene import BIOS_Menu, UefiShell
from dtaf_core.lib.tklib.basic.utility import get_config_item
import xml.etree.ElementTree as ET


BASE_PATH = r"C:\Automation\tkconfig"


def __update_xml_file(config_file, to_default_os_boot):
    inipath = os.path.abspath(config_file)
    xml_config_path = os.path.join(BASE_PATH, get_config_item('defaults', 'sys_config', inipath))
    xml_obj = ET.parse(xml_config_path)
    root = xml_obj.getroot()
    suts = root.findall('.//sut_os')

    current_sut = None
    for sut in suts:
        if sut.attrib['id'] == to_default_os_boot:
            current_sut = sut
            break
    user = pwd = ip = port = ''

    for tag in current_sut.iter('credentials'):
        user = tag.attrib['user']
        pwd = tag.attrib['password']
    for tag in current_sut.iter('ipv4'):
        ip = tag.text
        print(ip)
    for tag in current_sut.iter('port'):
        port = tag.text

    bios_prvd = root.find('.//xmlcli')
    username = bios_prvd.find('user')
    username.text = user
    password = bios_prvd.find('password')
    password.text = pwd
    ipv4 = bios_prvd.find('ip')
    ipv4.text = ip
    comport = bios_prvd.find('port')
    comport.text = port

    sut_os_path = bios_prvd.find('sutospath')
    if to_default_os_boot.strip() == 'Windows Boot Manager':
        sut_os_path.text = 'C:\\BKCPkg\\xmlcli\\'
    elif to_default_os_boot.strip() == 'VMware ESXi':
        sut_os_path.text = '/var/tmp/xmlcli/'
    else:
        sut_os_path.text = '/opt/APP/xmlcli/'
    xml_obj.write(xml_config_path, 'utf-8', True)


def os_type_convert(os_list):
    boot_os = {'redhat': 'Red Hat Enterprise Linux',
               'windows': 'Windows Boot Manager',
               'centos': 'CentOS Linux',
               'vmware': 'VMware ESXi'}
    if boot_os.get(os_list.lower()):
        to_os = boot_os[os_list.lower()]
    else:
        raise ValueError('No support platform')
    return to_os


def __set_default_boot_dev(sut, dev):
    logger.info('<{}> set_default_boot_dev {} '.format(sut.sut_name, dev))
    sut.bios.set_default_boot_dev(dev)
    sut.bios.back_to_bios_setup(level=2)


def __update_config(config_file, to_os):
    assert (os.path.exists(config_file))
    assert (os.path.isfile(config_file))
    cfg = ConfigParser()
    cfg.read(config_file)
    cfg.set(section='defaults', option='default_os_boot', value=to_os)
    with open(config_file, "w") as f:
        cfg.write(f)


def set_server_default_os(sut, to_default_os_boot, config_file=DEFAULT_SUT_CONFIG_FILE):
    # type: (SUT, str, str) -> None
    """
    to_default_os_boot: available value for default_os_boot, e.g. "redhat", "windows", "centos", "vmware"
    """
    logger.info('Switching from UEFI')
    boot_to(sut, SUT_STATUS.S0.UEFI_SHELL)
    sut.set_bios_bootorder_xmlcli(to_default_os_boot, SUT_STATUS.S0.UEFI_SHELL)
    UefiShell.exit_to_bios_menu(sut)
    __update_config(config_file, to_default_os_boot)
    __update_xml_file(config_file, to_default_os_boot)
    sut = get_sut(config_file)
    BIOS_Menu.continue_to_os(sut)


def set_client_default_os(sut, to_default_os_boot, config_file=DEFAULT_SUT_CONFIG_FILE):
    # type: (SUT, str, str) -> None
    """
    to_default_os_boot: available value for default_os_boot, e.g. "redhat", "windows", "centos", "vmware"
    """

    logger.info('Switching from OS')
    boot_to(sut, sut.default_os)
    sut.set_bios_bootorder_xmlcli(to_default_os_boot, sut.default_os)

    if sut.SUT_PLATFORM in SUT_STATUS.S0.LINUX_FAMILY:
        sut.execute_shell_cmd('shutdown -r now')
    if sut.SUT_PLATFORM == SUT_STATUS.S0.WINDOWS:
        sut.execute_shell_cmd('shutdown /r /t 0')
    if sut.SUT_PLATFORM == SUT_STATUS.S0.VMWARE:
        sut.execute_shell_cmd('reboot -f')

    __update_config(config_file, to_default_os_boot)
    __update_xml_file(config_file, to_default_os_boot)
    sut = get_sut(config_file)
    time.sleep(30)
    sut.check_system_in_os(method='in')


if __name__ == '__main__':
    """
    Usage Demo:
        --sut=sut.ini --sut1_os={windows/redhat/centos/vmware}
        --sut=network_server.ini --sut=network_client.ini --sut1_os={windows/redhat/centos/vmware} --sut2_os={windows/redhat/centos/vmware}
        --sut=network_server.ini --sut1_os={windows/redhat/centos/vmware}
        --sut=network_client.ini --sut2_os={windows/redhat/centos/vmware}
    """

    user = ParameterParser.parse_embeded_parameters()
    sut_list = []
    file_list = []
    filelist = ParameterParser.get_sut_config_list()
    for file in filelist:
        if os.path.exists(file) and os.path.isfile(file):
            s = get_sut(file)
            sut_list.append(s)
            file_list.append(file)
        else:
            sut_cfg = os.path.join(BASE_PATH, 'sut', file)
            if not os.path.exists(sut_cfg):
                logger.error(f"Fail to find config file <{sut_cfg}>")
                exit(-1)
            else:
                s = get_sut(sut_cfg)
                sut_list.append(s)
                file_list.append(sut_cfg)

    sut1_os = ParameterParser.parse_parameter("sut1_os")
    sut2_os = ParameterParser.parse_parameter("sut2_os")
    os_list = [sut1_os, sut2_os]

    Case.start(sut_list[0])
    if sut1_os != '':
        to_os = os_type_convert(os_list[0])
        set_server_default_os(sut_list[0], to_os, file_list[0])
    if sut2_os != '':
        to_os = os_type_convert(os_list[len(os_list)-1])
        set_client_default_os(sut_list[len(sut_list)-1], to_os, file_list[len(file_list)-1])
    Case.end()
