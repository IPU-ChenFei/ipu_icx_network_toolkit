#from src.lib.toolkit.auto_api import *
#from sys import exit
#from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to
#from src.mev.lib.mev import MEV, MEVOp
from src.network.lib import *

CASE_DESC = [
    # TODO
    'Mev System Concurrency Lan Vf Vm Nvme Pf Dynamic Ints Ate Enabled',
    # list the name of those cases which are expected to be executed before this case
    '<dependencies: if any>'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    mev = MEV(sut)
    try:
        # Prepare steps - call predefined steps
        boot_to(sut, sut.default_os)
        mev.general_bring_up()

        # Step1 - Create 2 VMs
        Case.step('Create 2 VMs')
        mev.create_vms(vm_num=2, mem_sz=2048, cpu_num=2, hugepage=False)

        # Step2 - Generate rules for vm0 and vm1
        Case.step('Generate rules for vm0 and vm1')
        components = [mev.xhc]
        components.extend(mev.vm_list)
        MEVOp.generate_rules(mev, components)

        Case.expect('ping vm0 to vm1 successfully.',
                    MEVOp.ping_to_each(mev.vm_list, mode='ipv4'))

        # Step3 - ssh to vm each
        Case.step('ssh to vm each')
        ret, _, _ = mev.vm_list[0].execute_shell_cmd(f"sshpass -p password ssh -q root@{mev.vm_list[1].ip_v4} -o "
                                                     f"'StrictHostKeyChecking=no' -o 'UserKnownHostsFile /dev/null' 'ls'")
        Case.expect('vm0 ssh to vm1 successfully.', ret == 0)

        ret, _, _ = mev.vm_list[1].execute_shell_cmd(f"sshpass -p password ssh -q root@{mev.vm_list[0].ip_v4} -o "
                                                     f"'StrictHostKeyChecking=no' -o 'UserKnownHostsFile /dev/null' 'ls'")
        Case.expect('vm1 ssh to vm0 successfully.', ret == 0)

    except Exception as e:
        raise e
    finally:
        MEVOp.clean_up(mev)


def clean_up(sut):
    from steps_lib import cleanup
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
