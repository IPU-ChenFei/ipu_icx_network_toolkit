import logging
import subprocess
import time
import datetime
import os


daemon_json_txt = ['{',
                  '\'\"registry-mirrors\":[\"https://registry.docker-cn.com\",\"http://hub-mirror.c.163.com\",\"https://docker,mirrors.ustc.edu.cn\",\"https://peee6w651.mirror.aliyuncs.com\"],\'',
                  '\'\"data-root\":\"/docker\",\'',
                  '\'\"insecure-registries\":[\"beethoven.sh.intel.com:5999\",\"amr-registry.caas.intel.com\",\"10.112.249.57\"]\'',
                  '}']


ssh_config_txt = ['StrictHostKeyChecking no',
                  'UserKnownHostsFIle /dev/null']


def get_logger():
    log_obj = logging.getLogger()
    formatter = logging.Formatter("%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    log_obj.setLevel(logging.DEBUG)

    file_handle = logging.FileHandler("docker_installation_{}.log".format(datetime.datetime.now().strftime("%Y%m%dZ%Hh%Mm%Ss")))
    stream_handle = logging.StreamHandler()
    file_handle.setFormatter(formatter)
    stream_handle.setFormatter(formatter)

    log_obj.addHandler(file_handle)
    log_obj.addHandler(stream_handle)

    return log_obj


log = get_logger()


def exec_command(cmd):
    log.debug("Executing cmd: {}".format(cmd))
    ret = subprocess.Popen(cmd,
                           shell=True,
                           stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    ret_code = ret.returncode
    out, err = ret.communicate()

    if err.decode() != "":
        log.warning(f"return code: {ret_code}\n")
        log.warning(f"Failed to execute cmd: {cmd}\n "
                    f"error message: {err.decode()}\n")
        # raise RuntimeError("Command execution failed! error: \n{}".format(err.decode()))
    return ret_code, out.decode('utf-8')


def install_sshpass():
    exec_command("wget http://sourceforge.net/projects/sshpass/files/latest/download "
                 "-O sshpass.tar.gz --no-check-certificate")
    exec_command("cd /root && tar -xvf sshpass.tar.gz")
    _, o = exec_command("cd /root && ls")
    ls = o.split("\n")
    sshpass_folder = ""

    for f in ls:
        if "sshpass-" in f:
            sshpass_folder = "/root/" + f.strip()
    exec_command(f"cd {sshpass_folder} && ./configure")
    exec_command(f"cd {sshpass_folder} && make install")

    ret, out = exec_command("sshpass -V")
    assert "This program is free software" in out


if __name__ == "__main__":
    check_install = os.system("docker -v")
    if check_install != 0:
        install_sshpass()

        yum_install_seq = [
            "yum install -y yum-utils",
            "yum install -y device-mapper-persistent-data",
            "yum install -y lvm2",
            "yum-config-manager --add-repo http://mirrors.aliyun.com/docker-ce/linux/centos/docker-ce.repo",
            "yum install -y --allowerasing docker-ce"
        ]
        for cmd in yum_install_seq:
            ret, out = exec_command(cmd)

        for txt in ssh_config_txt:
            exec_command(f'echo {txt} >> /etc/ssh/ssh_config')

        # start docker service from os level
        time.sleep(15)
        daemon_ret = os.system("systemctl daemon-reload")
        assert daemon_ret == 0

        enable_ret = os.system("systemctl enable docker")
        assert enable_ret == 0

        time.sleep(15)
        fail = 0
        for i in range(3):
            docker_ret = os.system("systemctl start docker")
            if docker_ret != 0:
                fail += 1
            else:
                break
        assert fail < 3

        exec_command("touch /etc/docker/daemon.json")
        for txt in daemon_json_txt:
            exec_command(f'echo {txt} >> /etc/docker/daemon.json')

        exec_command("docker login -u guest -p Passw0rd 10.112.249.57")
        exec_command("docker pull 10.112.249.57/multisocket/stresstools:latest")
        exec_command("docker network create --subnet=172.100.0.0/24 docker-br0")

        exec_command("docker run -itd --name=stresstools-latest -p 2222:22 --privileged "
                     "--net=docker-br0 --ip=172.100.0.2 "
                     "10.112.249.57/multisocket/stresstools:latest /sbin/init")

    else:
        ret = os.system("docker start stresstools-latest")
        print(ret)
        assert ret == 0 or ret is None
