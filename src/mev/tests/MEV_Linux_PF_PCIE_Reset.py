from src.lib.toolkit.auto_api import *
from sys import exit
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to
from src.mev.lib.mev import MEV, MEVOp

CASE_DESC = [
    # TODO
    'PCIe_reset',
    # list the name of those cases which are expected to be executed before this case
    '<dependencies: if any>'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    mev = MEV(sut)
    try:
        # Test 1 PF PCIe Reset no VFs

        # Step1 - Get IP from DHCP for XHC & PCIe Reset
        boot_to(sut, sut.default_os)
        mev.general_bring_up()
        Case.step('Get IP from DHCP for XHC and ping from XHC to DHCP server')
        mev.pass_xhc_traffic()
        Case.expect('ping to DHCP client successfully.', MEVOp.ping_to_dhcp(mev.xhc, mode='ipv4'))
        sut.execute_shell_cmd('dmesg -C')
        Case.step('PCIe reset on the PF device')
        ret, _, _ = sut.execute_shell_cmd(f'echo 1 > /sys/class/net/{mev.xhc.eth_name}/device/reset')
        Case.expect('PF reset successfully', ret == 0)
        return_code_1, stdout_1, _ = sut.execute_shell_cmd('dmesg', 30)
        Case.expect('check dmesg have not error mesg', 'error' not in stdout_1)

        # Step 2 - Get IP from DHCP for XHC
        Case.step('Get IP from DHCP for XHC and ping from XHC'
                  ' to DHCP server after PCIe reset,and check dmesg with no error')
        mev.pass_xhc_traffic()
        Case.expect('ping to DHCP client successfully.', MEVOp.ping_to_dhcp(mev.xhc, mode='ipv4'))

        # Test 2 PF PCIe Reset with VFs
        # Step1 - Reboot OS & Create 2 VMs
        Case.step('Create 2 VMs')
        mev.create_vms(vm_num=2, mem_sz=2048, cpu_num=2, hugepage=False)

        # Step2 - ping between vms and DHCP
        Case.step('Get IP from DHCP')
        mev.pass_vf_traffic(mev.vm_list[0])
        Case.expect('ping to each other successfully.',
                    MEVOp.ping_to_dhcp(mev.vm_list[0], mode='ipv4'))
        mev.pass_vf_traffic(mev.vm_list[1])
        Case.expect('ping to each other successfully.',
                    MEVOp.ping_to_dhcp(mev.vm_list[1], mode='ipv4'))

        # Step4 - Reset on one of the VF device on VM and redo the step 3
        sut.execute_shell_cmd('dmesg -C')
        Case.step('Reset on one of the VF device on VM')
        for vm in mev.vm_list:
            ret, _, _ = vm.execute_shell_cmd(f'echo 1 > /sys/class/net/{vm.eth_name}/device/reset')
            Case.expect('VF reset successfully', ret == 0)
            return_code_2, stdout_2, _ = sut.execute_shell_cmd('dmesg', 30)
            Case.expect('check dmesg have not error mesg', 'error' not in stdout_2)

            mev.pass_vf_traffic(vm)
            Case.step('Ping between each VMs and DHCP')
            Case.expect('ping to each other successfully.',
                        MEVOp.ping_to_dhcp(vm, mode='ipv4'))

        # Test 3 PF PCIe Reset with VFs
        # Step1 - Reboot OS & ping DHCP
        Case.step('Get IP from DHCP for XHC and ping from XHC to DHCP server')
        mev.pass_xhc_traffic()
        Case.expect('ping to DHCP client successfully.', MEVOp.ping_to_dhcp(mev.xhc, mode='ipv4'))

        # Step3 - PCIe reset on the PF device
        Case.step('PCIe Reset on the PF Device')
        sut.execute_shell_cmd('dmesg -C')
        ret_4, _, _ = sut.execute_shell_cmd(f'echo 1 > /sys/class/net/{mev.xhc.eth_name}/device/reset')
        Case.expect('check cmd', ret_4 == 0)
        return_code_5, stdout_5, _ = sut.execute_shell_cmd('dmesg', 30)
        Case.expect('check dmesg have not error mesg', 'error' not in stdout_5)

        # Step4 - redo the ping and check demsg with no error
        Case.step('Get IP from DHCP for XHC and ping from XHC to DHCP server')
        mev.pass_xhc_traffic()
        Case.expect('ping to DHCP client successfully.', MEVOp.ping_to_dhcp(mev.xhc, mode='ipv4'))

    except Exception as e:
        raise e
    finally:
        MEVOp.clean_up(mev)


def clean_up(sut):
    pass


def test_main():
    # ParameterParser parses all the embed parameters
    # --help to see all allowed parameters
    user_parameters = ParameterParser.parse_embeded_parameters()
    # add your parameter parsers with list user_parameters

    # if you would like to hardcode to disable clearcmos
    # ParameterParser.bypass_clearcmos = True

    # if commandline provide sut description file by --sut <json file>
    #       generate sut instance from given json file
    #       if multiple files have been provided in command line, only the 1st will take effect for get_default_sut
    #       to get multiple sut, call function get_sut_list instead
    # otherwise
    #       default sut configure file will be loaded
    #       which is defined in basic.config.DEFAULT_SUT_CONFIG_FILE
    sut = get_default_sut()
    my_os = OperationSystem[OS.get_os_family(sut.default_os)]

    try:
        Case.start(sut, CASE_DESC)
        test_steps(sut, my_os)

    except Exception as e:
        Result.get_exception(e, str(traceback.format_exc()))
    finally:
        Case.end()
        clean_up(sut)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)
