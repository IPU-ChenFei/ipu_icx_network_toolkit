#!/usr/bin/env python3
from src.lib.toolkit.auto_api import *
from src.lib.toolkit.infra.sut import *
from src.collateral_scripts._utils.default_os_switch import set_default_os
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to

if __name__ == '__main__':
    # param: --sut=sut1.ini --sut=sut2.ini --sut1_os={windows/rhel/centos} --sut2_os={windows/rhel/centos}
    user = ParameterParser.parse_embeded_parameters()
    sut_list = get_sut_list()
    file_list = ParameterParser.get_sut_config_list()
    sut1_os = ParameterParser.parse_parameter("sut1_os")
    sut2_os = ParameterParser.parse_parameter("sut2_os")
    os_list = [sut1_os, sut2_os]

    for index in range(len(sut_list)):
        Case.start(sut_list[index])

        if sut_list[index].get_power_status() == SUT_STATUS.S5:
            boot_to(sut_list[index], sut_list[index].default_os)
            
        if os_list[index].lower() == 'windows':
            to_os = 'windows'
        elif os_list[index].lower() == 'rhel':
            to_os = 'redhat'
        elif os_list[index].lower() == 'centos':
            to_os = 'centos'
        else:
            raise ValueError('No support platform')

        set_default_os(sut_list[index], to_os, file_list[index])

    Case.end()
