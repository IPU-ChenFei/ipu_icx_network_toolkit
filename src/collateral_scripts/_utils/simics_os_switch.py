from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.basic.config import DEFAULT_SUT_CONFIG_FILE

AVAILABLE_PARAM = ('redhat', 'centos', 'fedora', 'vmware', 'windows')
DEFAULT_OS_BOOT = {
    'redhat': 'Red Hat Enterprise Linux',
    'centos': 'CentOS Linux',
    'vmware': 'VMware ESXi',
    'windows': 'Windows Boot Manager',
    'fedora': 'Fedora',
}

if __name__ == '__main__':
    new_os = ParameterParser.parse_parameter("new_os")
    assert new_os in AVAILABLE_PARAM

    filelist = ParameterParser.get_sut_config_list()
    if len(filelist) == 0:
        config_file = DEFAULT_SUT_CONFIG_FILE
    else:
        config_file = ParameterParser.sut_config_list[0]
    assert (os.path.exists(config_file))

    cfg = ConfigParser()
    cfg.read(config_file)
    cfg.set(section='defaults', option='default_os_boot', value=DEFAULT_OS_BOOT[new_os])
    with open(config_file, "w") as f:
        cfg.write(f)
