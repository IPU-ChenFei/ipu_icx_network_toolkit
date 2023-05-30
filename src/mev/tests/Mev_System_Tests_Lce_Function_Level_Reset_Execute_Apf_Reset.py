from src.lib.toolkit.auto_api import *
from sys import exit
from src.lib.toolkit.steps_lib.prepare.boot_to import boot_to
from src.mev.lib.mev import MEV, MEVOp
from src.mev.lib.utility import get_bdf

CASE_DESC = [
    # TODO
    'case name here',
    # list the name of those cases which are expected to be executed before this case
    '<dependencies: if any>'
]


def test_steps(sut, my_os):
    # type: (SUT, GenericOS) -> None
    mev = MEV(sut)
    try:
        # TODO, replace these with your own steps
        # Prepare steps - call predefined steps
        boot_to(sut, sut.default_os)

        MEVOp.lce_common_prepare_step(mev)

        Case.step('load lce related drivers')
        mev.execute_acc_cmd('modprobe qat_lce_cpfxx', timeout=60)
        Case.sleep(10)

        Case.step("run lce test on ACC")
        _, out, _ = mev.execute_acc_cmd(r"lspci -D -d :1456 | cut -f1 -d \" \" ")
        cpfdev = out.strip('\n')
        _, out, _ = mev.execute_acc_cmd("cat /proc/sys/kernel/random/uuid")
        mdev_uuid = out.strip("\n")

        mev.execute_acc_cmd(f"echo {mdev_uuid} >"
                            f" /sys/bus/pci/devices/{cpfdev}/mdev_supported_types/lce_cpfxx-mdev/create")
        mev.execute_acc_cmd("echo 0 > enable", cwd=f"/sys/bus/mdev/devices/{mdev_uuid}")
        mev.execute_acc_cmd("echo 2 > dma_queue_pairs", cwd=f"/sys/bus/mdev/devices/{mdev_uuid}")
        mev.execute_acc_cmd("echo 2 > cy_queue_pairs", cwd=f"/sys/bus/mdev/devices/{mdev_uuid}")
        mev.execute_acc_cmd("echo 2 > dc_queue_pairs", cwd=f"/sys/bus/mdev/devices/{mdev_uuid}")
        mev.execute_acc_cmd("echo 1 > enable", cwd=f"/sys/bus/mdev/devices/{mdev_uuid}")

        Case.step('load lce_apfxx driver on sut')
        sut.execute_shell_cmd('dmesg -C')
        sut.execute_shell_cmd('modprobe qat_lce_apfxx')

        Case.step(' Enable lce_flr on device on SUT')
        bdf = get_bdf(sut.execute_shell_cmd, 1455, 0)
        ret, _, _ = sut.execute_shell_cmd(f' echo 1 > /sys/bus/pci/devices/{bdf}/lce_flr')
        Case.expect('LCE flr successfully.', ret == 0)

        ret_, stdout, _ = sut.execute_shell_cmd('dmesg')
        Case.expect('Check no error', 'error' not in stdout)

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
