import os
import re
import sys
import subprocess
import set_toolkit_src_root
import time
from datetime import datetime
from dtaf_core.lib.tklib.auto_api import *
from dtaf_core.lib.tklib.basic.config import LOG_PATH
from dtaf_core.lib.tklib.basic.utility import ParameterParser
from dtaf_core.lib.tklib.steps_lib.prepare.boot_to import boot_to



# def exec_cmd(cmd, timeout=30, cwd=None):
#     child = subprocess.Popen(cmd,
#                              shell=True,
#                              stdin=subprocess.PIPE,
#                              stdout=subprocess.PIPE,
#                              stderr=subprocess.PIPE,
#                              cwd=cwd
#                              )
#     out, err = child.communicate(timeout=timeout)
#     exitcode = child.returncode
#     stdout = out.decode(encoding='utf-8')
#     stderr = err.decode(encoding='utf-8')
#     print(stdout)
#     return exitcode, stdout, stderr


def get_device_info(sut):
    get_cmd = 'wmic diskdrive get /value | find "{}"'
    dev_dict = {}

    # def test_steps(sut, my_os):
    #     Case.prepare('case prepare description')
    #     boot_to(sut, sut.default_os)

    # get partitions
    ret, out, _ = sut.execute_shell_cmd(get_cmd.format("Partitions"))
    if not ret == 0:
        return False
    par_idx = []
    for idx, par in enumerate(out.splitlines()):
        if re.match("^Partitions=0$", par):
            par_idx.append(idx)

    # get index
    ret, out, _ = sut.execute_shell_cmd(get_cmd.format("Index"))
    if not ret == 0:
        return False
    index_dict = {}
    for idx, num in enumerate(out.splitlines()):
        if idx in par_idx:
            index = re.match("^Index=(\d+)$", num).group(1)
            index_dict[idx] = index

    # get Model
    ret, out, _ = sut.execute_shell_cmd(get_cmd.format("Model"))
    if not ret == 0:
        return False
    for key, val in index_dict.items():
        for idx, model in enumerate(out.splitlines()):
            if key == idx:
                value = re.match("Model=(.*)", model).group(1)
                dev_dict[val] = value
                break

    # get FirmwareRevision
    ret, out, _ = sut.execute_shell_cmd(get_cmd.format("FirmwareRevision"))
    if not ret == 0:
        return False
    for key, val in index_dict.items():
        for idx, fw in enumerate(out.splitlines()):
            if key == idx:
                value = re.match("FirmwareRevision=(.*)", fw).group(1)
                dev_dict[val] = dev_dict[val] + " " + value
                break
    return dev_dict


def modify_cfg_file(dev_data, cfg_file, stress_time):
    if not os.path.isfile(cfg_file):
        print(f"Not found config file {cfg_file}")
        return False
    if not isinstance(dev_data, dict):
        print("device info should be like dictionary type")
        return False

    # dev_data = {
    #     "4": "INTEL SSDPF21Q400GB L0310009",
    #     "5": "INTEL SSDPF21Q400GB L0310009",
    #     "6": "INTEL SSDPF21Q400GB L0310009",
    #     "7": "INTEL SSDPF21Q400GB L0310009"
    # }

    try:
        with open(cfg_file, 'r') as f1, open("%s.bak" % cfg_file, 'w') as f2:
            for line in f1:
                dev_key = list(dev_data.keys())
                # if re.match('\t(\d+):.*"\((.*)"', line):
                if re.match('\t(\d+):.*"(.*)"', line):
                    ret = re.sub('\t\d+:', '\t%s:' % dev_key[0], line)
                    # line = re.sub('"\((.*)"', '"\(%s"' % dev_data[dev_key[0]], ret)
                    line = re.sub('"(.*)"', '"%s"' % dev_data[dev_key[0]], ret)
                    dev_data.pop(dev_key[0])
                f2.write(line)
        os.remove(cfg_file)
        os.rename("%s.bak" % cfg_file, cfg_file)

        time_list = stress_time.split(',')
        hour = time_list[0]
        minute = time_list[1]
        repl = f'\t{hour}' + ' ' * 10 + f'{minute}' + ' ' * 10 + '00\n'

        with open(cfg_file, 'r') as f1, open("%s.bak" % cfg_file, 'w') as f2:
            content = f1.readlines()
            for line in content:
                pattern = re.compile('\d+\s+\d+\s+\d+$')
                if pattern.findall(line):
                    f2.write(repl)
                else:
                    f2.write(line)
        os.remove(cfg_file)
        os.rename("%s.bak" % cfg_file, cfg_file)
    except Exception as ex:
        print(ex)
        return False





if __name__ == '__main__':
    cfg_file = sys.argv[1]
    dev_data = get_device_info()
    if not modify_cfg_file(dev_data, cfg_file):
        exit(1)
