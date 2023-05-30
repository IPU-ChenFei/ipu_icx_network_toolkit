from src.lib.toolkit.auto_api import *
from sys import exit
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to
from src.mev.lib.mev import MEV, MEVOp

CASE_DESC = [
    # TODO preparation operation
    'Maximum_VF_Generation',
    # list the name of those cases which are expected to be executed before this case
    '<dependencies: if any>'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    mev = MEV(sut)
    try:
        boot_to(sut, sut.default_os)
        mev.general_bring_up()

        # Step2 - Create 1023 VFs
        Case.step(f'Create 1023 VFs')

        def count_vf_num(num):
            _, out, _ = mev.execute_imc_cmd(f'/usr/bin/cplane/cli_client | grep -i "is_vf: yes" | wc -l')
            return int(out.strip('\n')) == num

        ret, _, _ = sut.execute_shell_cmd(f'echo 1020 > /sys/class/net/{mev.xhc.eth_name}/device/sriov_numvfs'
                                          , timeout=120)
        Case.expect('create vf successfully', ret == 0)
        sut.execute_shell_cmd('modprobe iavf')
        Case.wait_and_expect('All VFs are shown to OS.', 20 * 60, count_vf_num, 1011)
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
