import set_toolkit_src_root
import datetime
from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to, boot_to_with_bios_knobs
from dtaf_core.lib.tklib.infra.sut import *

CASE_DESC = [
    # TODO: replace these with real case description for this case
    'it is a template for a general case',
    'this testcase is to verify AC cycling_Linux OS with enable VMD'
    'replace the description here for your case',
    # list the name of those cases which are expected to be executed before this case
    '<dependencies: if any>'
]


def test_steps(sut, my_os):
    # TODO: replace these with your own steps
    # Prepare steps - call predefined steps
    Case.prepare('boot to OS')
    boot_to(sut, sut.default_os)

    Case.step('Create log folder')
    nowTime = datetime.datetime.now().strftime('%Y%m%d-%H%M%S')
    log_dir = rf'mkdir /root/log_{nowTime}'
    sut.execute_shell_cmd(log_dir)
    remote_path = rf'/root/log_{nowTime}'
    show_device_info = rf'fdisk -l |tee device.txt |grep -o "Disk /dev/nvme.*n1" |tee devices_info.txt'
    smartctl_cmd = rf'ls /dev/nvme*n1 |xargs -n 1 smartctl -a > smartctl.txt'

    Case.step('Get SSD devices list')
    sut.execute_shell_cmd(show_device_info, cwd=remote_path)
    sut.execute_shell_cmd(smartctl_cmd, cwd=remote_path)

    Case.step('Show SSD devices detail info')
    get_ssdinfo_cmd = r"lspci | grep -i nvme | awk '{print $1}' | xargs -n 1 lspci -vvv -s | tee nvme.txt"
    sut.execute_shell_cmd(get_ssdinfo_cmd, cwd=remote_path)
    sut.execute_shell_cmd(get_ssdinfo_cmd, cwd='/root')

    Case.step('Check if all nvme devices width is x4')
    get_nvme_count_cmd = r"lspci | grep -i nvme | wc -l"
    nvme_count = sut.execute_shell_cmd(get_nvme_count_cmd)[1].strip()
    get_widthx4_cmd = r"cat /root/nvme.txt | grep -i width | wc -l"
    widthx4 = sut.execute_shell_cmd(get_widthx4_cmd)[1].strip()
    try:
        if int(widthx4) == int(nvme_count) * 2:
            logger.info('All nvme devices link cap and sta width is x4')
        else:
            raise TimeoutError
    except Exception as e:
        logger.info(e)
        raise ValueError('nvme devices width incorrect')
    finally:
        Case.step('save log files')
        sut.download_to_local(remotepath=remote_path, localpath=os.path.join(LOG_PATH, 'result'))

        Case.step('restore env')
        del_log = rf'rm -rf {remote_path}'
        sut.execute_shell_cmd(del_log)

def clean_up(sut):
    # TODO: restore bios setting or other step to eliminate impact on the next case regardless case pass or fail
    # sut.set_bios_knobs(*bios_knob('disable_wol_s5_xmlcli'))

    # TODO: replace default cleanup.to_S5 if necessary when case execution fail
    # if Result.returncode != 0:
    #     cleanup.to_s5(sut)
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
    # my_os = OperationSystem[sut.default_os]

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
