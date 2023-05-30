from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.basic.config import DEFAULT_SUT_CONFIG_FILE

TOPOLOGY = ('TOPOLOGY_4S_Fully_Connected_1', 'TOPOLOGY_4S_Fully_Connected_2', 'TOPOLOGY_4S_Fully_Connected_3',
            'TOPOLOGY_4S_Fully_Connected_4', 'TOPOLOGY_4S_Fully_Connected_5', 'TOPOLOGY_4S_Ring_1',
            'TOPOLOGY_4S_Ring_2', 'TOPOLOGY_4S_Ring_3')

SIMICS_CONFIG_MAPPING = {
    ('TOPOLOGY_4S_Fully_Connected_1', 'CentOS Linux'): 'BHS-GNR-SP_config_bmod_centos_base_4Sconfig1.simics',
    ('TOPOLOGY_4S_Fully_Connected_2', 'CentOS Linux'): 'BHS-GNR-SP_config_bmod_centos_base_4Sconfig2.simics',
    ('TOPOLOGY_4S_Fully_Connected_3', 'CentOS Linux'): 'BHS-GNR-SP_config_bmod_centos_base_4Sconfig3.simics',
    ('TOPOLOGY_4S_Fully_Connected_4', 'CentOS Linux'): 'BHS-GNR-SP_config_bmod_centos_base_4Sconfig4.simics',
    ('TOPOLOGY_4S_Fully_Connected_5', 'CentOS Linux'): 'BHS-GNR-SP_config_bmod_centos_base_4Sconfig5.simics',
    ('TOPOLOGY_4S_Ring_1', 'CentOS Linux'): 'BHS-GNR-SP_config_bmod_centos_base_4Sconfig6.simics',
    ('TOPOLOGY_4S_Ring_2', 'CentOS Linux'): 'BHS-GNR-SP_config_bmod_centos_base_4Sconfig7.simics',
    ('TOPOLOGY_4S_Ring_3', 'CentOS Linux'): 'BHS-GNR-SP_config_bmod_centos_base_4Sconfig8.simics',

    ('TOPOLOGY_4S_Fully_Connected_1', 'Windows Boot Manager'): 'BHS-GNR-SP_config_bmod_win_2022_base_4Sconfig1.simics',
    ('TOPOLOGY_4S_Fully_Connected_2', 'Windows Boot Manager'): 'BHS-GNR-SP_config_bmod_win_2022_base_4Sconfig2.simics',
    ('TOPOLOGY_4S_Fully_Connected_3', 'Windows Boot Manager'): 'BHS-GNR-SP_config_bmod_win_2022_base_4Sconfig3.simics',
    ('TOPOLOGY_4S_Fully_Connected_4', 'Windows Boot Manager'): 'BHS-GNR-SP_config_bmod_win_2022_base_4Sconfig4.simics',
    ('TOPOLOGY_4S_Fully_Connected_5', 'Windows Boot Manager'): 'BHS-GNR-SP_config_bmod_win_2022_base_4Sconfig5.simics',
    ('TOPOLOGY_4S_Ring_1', 'Windows Boot Manager'): 'BHS-GNR-SP_config_bmod_win_2022_base_4Sconfig6.simics',
    ('TOPOLOGY_4S_Ring_2', 'Windows Boot Manager'): 'BHS-GNR-SP_config_bmod_win_2022_base_4Sconfig7.simics',
    ('TOPOLOGY_4S_Ring_3', 'Windows Boot Manager'): 'BHS-GNR-SP_config_bmod_win_2022_base_4Sconfig8.simics',

    ('TOPOLOGY_4S_Fully_Connected_1', 'VMware ESXi'): 'BHS-GNR-SP_config_bmod_esxi800_base_4Sconfig1.simics',
    ('TOPOLOGY_4S_Fully_Connected_2', 'VMware ESXi'): 'BHS-GNR-SP_config_bmod_esxi800_base_4Sconfig2.simics',
    ('TOPOLOGY_4S_Fully_Connected_3', 'VMware ESXi'): 'BHS-GNR-SP_config_bmod_esxi800_base_4Sconfig3.simics',
    ('TOPOLOGY_4S_Fully_Connected_4', 'VMware ESXi'): 'BHS-GNR-SP_config_bmod_esxi800_base_4Sconfig4.simics',
    ('TOPOLOGY_4S_Fully_Connected_5', 'VMware ESXi'): 'BHS-GNR-SP_config_bmod_esxi800_base_4Sconfig5.simics',
    ('TOPOLOGY_4S_Ring_1', 'VMware ESXi'): 'BHS-GNR-SP_config_bmod_esxi800_base_4Sconfig6.simics',
    ('TOPOLOGY_4S_Ring_2', 'VMware ESXi'): 'BHS-GNR-SP_config_bmod_esxi800_base_4Sconfig7.simics',
    ('TOPOLOGY_4S_Ring_3', 'VMware ESXi'): 'BHS-GNR-SP_config_bmod_esxi800_base_4Sconfig8.simics',
}

if __name__ == '__main__':
    topology = ParameterParser.parse_parameter("topology")
    assert topology in TOPOLOGY

    filelist = ParameterParser.get_sut_config_list()
    if len(filelist) == 0:
        config_file = DEFAULT_SUT_CONFIG_FILE
    else:
        config_file = ParameterParser.sut_config_list[0]
    assert (os.path.exists(config_file))

    # get current value of default_os_boot and simics_script
    sut_cfg = ConfigParser()
    sut_cfg.read(config_file)
    default_os_boot_cfg = sut_cfg.get(section='defaults', option='default_os_boot')

    sys_config_file_path = get_config_item('defaults', 'sys_config')
    xml_obj = ET.parse(sys_config_file_path)
    root = xml_obj.getroot()
    simics_scripts = root.findall('.//simics/script')

    for simics_script in simics_scripts:
        new_simics_script = SIMICS_CONFIG_MAPPING.get((topology, default_os_boot_cfg))
        new_simics_script_cfg = simics_script.text.split('/')
        new_simics_script_cfg[-1] = new_simics_script
        simics_script.text = '/'.join(new_simics_script_cfg)

    xml_obj.write(sys_config_file_path, 'utf-8', True)

    # change topology setting in mltskt_config.ini
    with open(r'C:\BKCPkg\multisocket_ofband\mltskt_config.ini', "r") as f:
        content = f.read()
    content = re.sub(r'Topology:\s*.+', f'Topology: {topology}', content)
    with open(r'C:\BKCPkg\multisocket_ofband\mltskt_config.ini', "w") as f:
        f.write(content)
