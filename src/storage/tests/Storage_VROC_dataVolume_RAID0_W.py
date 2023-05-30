import set_toolkit_src_root
import re
from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.infra.sut import *
# from src.configuration.config.wht.sut_tools import *
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to
from src.storage.lib.storage import *

CASE_DESC = [
    'This testcase is to verify create data volume RAID0 in Win OS.',
    # list the name of those cases which are expected to be executed before this case
    '<dependencies: if any>',
    'Storage_VMD_enable.py'
]


def test_steps(sut, my_os):
    Case.prepare('boot to OS')
    boot_to(sut, sut.default_os)

    Case.step('Search the formatted drive ID ')
    cmd = 'wmic diskdrive get /value | find "SerialNumber"'
    SN1_list = split_wmic_get(sut, cmd, 'SN1_list')
    cmd = 'wmic diskdrive get /value | find "Partitions"'
    partitions_list = split_wmic_get(sut, cmd, 'partitions_list')
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
    last_id_list = []
    for key in last_key_list:
        last_id_list.append(dict_SN_ID[key])

    Case.step('create data volume RAID0')
    create_raid_cmd = rf'intelvroccli.exe -C -l 0 -n TestRAID0 --span {last_id_list[0]} {last_id_list[1]} -s 128 -z 120'
    check_raid_info_cmd = r'.\intelvroccli.exe -I -v | tee raid_info.txt'
    stderr = []
    try:
        ret_code, stdout1, stderr1 = sut.execute_shell_cmd(create_raid_cmd, cwd=SUT_TOOLS_WINDOWS_STORAGE)
        stderr.append(stderr1)
        stdout2 = sut.execute_shell_cmd(check_raid_info_cmd, cwd=SUT_TOOLS_WINDOWS_STORAGE, powershell=True)[1]
        Case.expect('create RAID0 success', ret_code == 0 and 'TestRAID0' in stdout2)
    except Exception as e:
        logger.info(e)
        logger.info(stderr[0])
        raise ValueError('create RAID0 fail')

    finally:
        Case.step('remove RAID volume')
        delete_raid_cmd = r'intelvroccli.exe -M -D TestRAID0'
        sut.execute_shell_cmd(delete_raid_cmd, cwd=SUT_TOOLS_WINDOWS_STORAGE)

        Case.step('save log files')
        sut.download_to_local(remotepath=rf'{SUT_TOOLS_WINDOWS_STORAGE}\raid_info.txt',
                              localpath=os.path.join(LOG_PATH, 'result'))

        Case.step('restore env')
        del_log = rf'del {SUT_TOOLS_WINDOWS_STORAGE}\raid_info.txt'
        sut.execute_shell_cmd(del_log)


def clean_up(sut):
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

    try:
        Case.start(sut, CASE_DESC)
        test_steps(sut, my_os)

    except Exception as e:
        Result.get_exception(e, str(traceback.format_exc()))
    finally:
        Case.end()

    if Result.returncode != 0:
        clean_up(sut)


if __name__ == '__main__':
    test_main()
    exit(Result.returncode)
