import os
import re
import xml.etree.ElementTree as ET
from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.steps_lib.os_scene import *
from tkconfig import sut_tool
from dtaf_core.lib.tklib.basic.const import SUT_PLATFORM


def set_vmd(bios_file_name, status='Enable', vmd_list=None, weight=4):
    """
    Purpose:
        This method is used to set vmd bios knobs through parsing the bios xml file get by xmlcli tool,
        Apply for wht, egs, bhs.
    Args:
        bios_file_name: a xml file which dumping with your SUT by xmlcli tool in current directory
            for example: 'wht_bios.xml', 'egs_bios.xml', 'bhs_bios.xml'
        status: Enable or Disable
            default --> Enable
        vmd_list: a list which contains the BIOS knobs name extension number on wht and egs,for bhs use default None.
            for example: vmd_list = [5, 11]
            default for all IOU port --> vmd_list = [1, 2, 4, 5, 7, 8, 10, 11]
            More info: If you want to enable socket 0 IOU 3, search it in bios knobs xml file,
            <!-- VMD Config for IOU 3 -->
            <knob type="scalar" setupType="oneof" name="VMDEnabled_4" varstoreIndex="00" prompt="Enable/Disable VMD"
            will find the name with extension number 4, then vmd_list parameter should vmd_list = [4]
        weight: port numbers in this IOU port.
            eg: 4 or 8
            More info: If you want to check how many ports in socket0 IOU3, search it in bios knobs xml file.
            check the count for prompt under IOU3 for [VMD port A, VMD port B, VMD port C...]
    Raises:
        AssertError: if failed
    Returns:
        A list which contains vmd knobs options and values
        for example: ['VMDEnabled_11', '0x1', 'VMDPortEnable_6', '0x1', ..., ...]
    Example:
        Usage example:
            for enable in ICX:
                set_vmd('wht_bios.xml', status='Enable', vmd_list = [5, 11], weight=4)
            for disable in EGS:
                set_vmd('wht_bios.xml', status='Disable', vmd_list = [5, 11], weight=8)
    """
    script_path = os.getcwd()
    os.chdir(os.path.dirname(__file__))
    # assert os.path.isfile(bios_file_name), 'platform bios file not exist in current directory'
    tree = ET.parse(bios_file_name)
    os.chdir(script_path)
    root = tree.getroot()
    change_list = set()
    bios_knob = []

    bios_file_list = ['wht_bios.xml', 'egs_bios.xml']
    if bios_file_name.lower() in bios_file_list:

        # enable IOU4 for socket0 and socket1
        # set_vmd_list = [5, 11]
        # assert vmd_list, 'vmd port setting list is empty.'
        if vmd_list is None:
            vmd_list = [5, 11]
            # vmd_list = [1, 2, 4, 5, 7, 8, 10, 11]
        set_vmd_list = vmd_list
        for bios_knobs in root:
            for knob in bios_knobs:
                if 'prompt' in knob.attrib.keys():
                    for i in set_vmd_list:
                        for j in range(i * weight, (i + 1) * weight):
                            find_list = [f'VMDEnabled_{i}', f'VMDEnabled_{i}_inst_2', f'VMDPortEnable_{j}', f'VMDPortEnable_{j}_inst_2']
                            if any(p == knob.attrib['name'] for p in find_list):
                                for options in knob:
                                    for option in options:
                                        if option.attrib['text'] == status:
                                            changed_knob = knob.attrib['name']
                                            changed_value = option.attrib['value']
                                            knob_and_value = (changed_knob, changed_value)
                                            change_list.add(knob_and_value)
        for i in change_list:
            if (i[0] + '_inst_2', i[1]) not in change_list:
                bios_knob.extend(i)

    elif bios_file_name.lower() == 'bhs_bios.xml':
        find_list = ['PcieHotPlugEnable']
        # socket number
        # TODO: hard code here temporarily
        for i in range(1):
            # PCI Express 4、5
            for j in range(4, 6):
                find_list.append(f'Socket_{i}_PciExpress_{j}_VMDEnabled')
                # port 0 ~ 7
                for k in range(8):
                    find_list.append(f'Socket_{i}_PciExpress_{j}_Port_{k}_VMDPortEnabled')
                    find_list.append(f'Socket_{i}_PciExpress_{j}_Port_{k}_PcieHotPlugOnPort')
        for bios_knobs in root:
            for knob in bios_knobs:
                if 'prompt' in knob.attrib.keys():
                    if any(p == knob.attrib['name'] for p in find_list):
                        for options in knob:
                            for option in options:
                                if option.attrib['text'] == status:
                                    changed_knob = knob.attrib['name']
                                    changed_value = option.attrib['value']
                                    knob_and_value = (changed_knob, changed_value)
                                    bios_knob.extend(knob_and_value)
    else:
        raise ValueError('invalid platform bios file')
    return bios_knob


# Below function is for windows VMD test cases
SUT_TOOLS_WINDOWS_STORAGE = sut_tool('SUT_TOOLS_WINDOWS_STORAGE')
SUT_TOOLS_LINUX_STORAGE = sut_tool('SUT_TOOLS_LINUX_STORAGE')

def split_wmic_get(sut,cmd, list_name):
    list_get = sut.execute_shell_cmd(cmd)[1].strip().split()
    list_name = []
    for i in list_get:
        if i == 'SerialNumber=' or i == '_00000001.':
            continue
        elif '=' not in i:
            list_name.append(i)
            continue
        list_name.append(i.split('=', 1)[1])
    return list_name


def SN_get_VROC(sut, cmd, list_new):
    # SUT_TOOLS_WINDOWS_STORAGE = sut_tool('SUT_TOOLS_WINDOWS_STORAGE')
    cmd_get = sut.execute_shell_cmd(cmd, cwd=SUT_TOOLS_WINDOWS_STORAGE)[1].strip().split()
    list_name = []
    list_new = []
    for i in cmd_get:
        list_name.append(i)
    for j in list_name:
        if j != 'Number:' and j != 'Serial':
            list_new.append(j)
    return list_new


def ID_get_VROC(sut, cmd, list_new):
    # SUT_TOOLS_WINDOWS_STORAGE = sut_tool('SUT_TOOLS_WINDOWS_STORAGE')
    cmd_get = str(sut.execute_shell_cmd(cmd, cwd=SUT_TOOLS_WINDOWS_STORAGE)[1].strip().split())
    list_new = re.findall(r'\d-\d-\d-\d', cmd_get)
    return list_new


def generate_dict(key_list, value_list):
    d = {x: y for x, y in zip(key_list, value_list)}
    return d


def get_raid_devices(sut):
    """
        Purpose:
            This method is used to get the SSD devices which can be used for RAID.
        Args:
            sut: SUT instance
        Returns:
            A list which contains SSD devices name.
            for example:
                in Linux: ['/dev/nvme1n1', '/dev/nvme3n1', '/dev/nvme4n1', '/dev/nvme6n1', ...]
                in Windows: ['3-0-0-0', '5-0-0-0', '6-0-0-0', '6-0-0-1', ...]
     """
    raid_devices_list = []
    if sut.default_os == SUT_PLATFORM.WINDOWS:
        cmd1 = 'wmic diskdrive get /value | find "SerialNumber"'
        SN1_list = split_wmic_get(sut, cmd1, 'SN1_list')
        cmd2 = 'wmic diskdrive get /value | find "Partitions"'
        partitions_list = split_wmic_get(sut, cmd2, 'partitions_list')
        dict_SN_partitions = generate_dict(SN1_list, partitions_list)
        last_key_list = []
        for key in dict_SN_partitions:
            if int(dict_SN_partitions[key]) == 0:
                last_key_list.append(key)

        cmd = 'IntelVROCCli.exe -I | find "Serial Number"'
        SN2_list = SN_get_VROC(sut, cmd, 'SN2_list')
        cmd = 'IntelVROCCli.exe -I | find "ID"'
        ID_list = ID_get_VROC(sut, cmd, 'ID_list')
        dict_SN_ID = generate_dict(SN2_list, ID_list)
        # last_id_list = []
        for key in last_key_list:
            raid_devices_list.append(dict_SN_ID[key])
        # return raid_devices_list
    else:
        get_devices_num = r'ls /dev/nvme*n1 | wc -l'
        devices_num = int(sut.execute_shell_cmd(get_devices_num)[1])

        for i in range(devices_num):
            cmd = f"cat /proc/partitions | grep nvme{i} | wc -l"
            ret = sut.execute_shell_cmd(cmd)[1]
            j = '/dev/nvme' + f'{i}' + 'n1'
            if int(ret) == 1:
                raid_devices_list.append(j)

    return raid_devices_list
