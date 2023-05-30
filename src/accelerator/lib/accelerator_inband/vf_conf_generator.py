#!/usr/bin/python3

import sys
import os

Genaral = '''[GENERAL]
ServicesEnabled = {0}
ConfigVersion = 2

CyNumConcurrentSymRequests = 512
CyNumConcurrentAsymRequests = 64
statsGeneral = 1
statsDh = 1
statsDrbg = 1
statsDsa = 1
statsEcc = 1
statsKeyGen = 1
statsDc = 1
statsLn = 1
statsPrime = 1
statsRsa = 1
statsSym = 1
StorageEnabled = 0
PkeServiceDisabled = 0
AutoResetOnError = 0
SVMEnabled = 1
ATEnabled = {1}
ATMode = {2}

[KERNEL]
NumberCyInstances = 0
NumberDcInstances = 0

[SIOV]
NumberAdis = 0
'''


SSL_head = '''
[SSL]
NumberCyInstances = {0}
NumberDcInstances = {1}
NumProcesses = 1
LimitDevAccess = 0
'''

Cy_instance = '''
Cy{0}Name = "SSL{0}"
Cy{0}IsPolled = 1
Cy{0}CoreAffinity = {1}
'''

Dc_instance = '''
Dc{0}Name = "Dc{0}"
Dc{0}IsPolled = 1
Dc{0}CoreAffinity = {1}
'''

# default node 0 PF number
NUMA0_device_number = 4

def help():
    print("*******************************************************************************************************")
    print("* ")
    print("* Usage: ")
    print("*     python vf_conf_generator.py replace_svm service AT_Mode pf_number vf_number instance cores/cross ")
    print("* ")
    print("*     replace_svm: ")
    print("*         whether to replace libsvm_s.so, 0: no replace, 1: replace ")
    print("*     service: ")
    print("*         ServiceEnable settings in conf file, include dc, sym, asym or sym,dc ")
    print("*     AT_Mode: ")
    print("*         AT settings in conf file, include off, on and prefetch ")
    print("*     pf_number: ")
    print("*         number of PF in use, if 0, use all pf. ")
    print("*     vf_number: ")
    print("*         number of VF map to PF, if 0, use all vf. ")
    print("*     instance: ")
    print("*         instance number on conf file, if include two type service, set instance on ")
    print("*         format cy_instance,dc_instance, like 2,2 ")
    print("*     cores/cross: ")
    print("*         cores in use or whether use cross cores. like 0-27 or 0-27,56-83, can be omit.")
    print("*         if 1, use cross cores, like PF on node 0 use cores on node 1. ")
    print("*         if 0, use cores as normal. ")
    print("* ")
    print("* Example: ")
    print("*     performance:")
    print("*         different core of different VF instance")
    print("*         python vf_conf_generator.py 0 dc prefetch 4 4 2 0-15,56-71")
    print("*     PFs:")
    print("*         set cores")
    print("*         python vf_conf_generator.py 0 asym on 4 2 4 0-15,16-31")
    print("*     functional:")
    print("*         assign different core to different VFs, depends on BIOS setting")
    print("*         python vf_conf_generator.py 0 sym on 0 0 2")
    print("* ")
    print("*******************************************************************************************************")


def replace_svm():
    '''
    replace usdm with svm, include usdm under /usr/local/lib and driver directory
    '''
    status = os.system('yes | cp -f {}/libsvm_s.so /usr/local/lib/libusdm_drv_s.so'.format('/'.join(sys.argv[0].split('/')[:-1])))
    status += os.system('yes | cp -f {0}/libsvm_s.so {0}/../../../driver/build/libusdm_drv_s.so'.format('/'.join(sys.argv[0].split('/')[:-1])))
    if status != 0:
        print('copy svm lib failed.')


def clear_settings(service):
    '''
    Set all instance to 0. And set AT settings to default.
    '''
    status = []

    if not os.path.exists("/etc/4xxxvf_dev0.conf"):
        return None

    # set service
    status.append(os.system('sed -i "s/ServicesEnabled.*/ServicesEnabled = {}/g" /etc/4xxxvf_dev*.conf'.format(service)))

    # set instance number to 0
    status.append(os.system('sed -i "s/NumberCyInstances.*/NumberCyInstances = 0/g" /etc/4xxxvf_dev*.conf'))
    status.append(os.system('sed -i "s/NumberDcInstances.*/NumberDcInstances = 0/g" /etc/4xxxvf_dev*.conf'))

    # clear Cy and Dc instance
    status.append(os.system('sed -i "s/Cy[0-9]*Name.*//g" /etc/4xxxvf_dev*.conf'))
    status.append(os.system('sed -i "s/Cy[0-9]*IsPolled.*//g" /etc/4xxxvf_dev*.conf'))
    status.append(os.system('sed -i "s/Cy[0-9]*CoreAffinity.*//g" /etc/4xxxvf_dev*.conf'))
    status.append(os.system('sed -i "s/Dc[0-9]*Name.*//g" /etc/4xxxvf_dev*.conf'))
    status.append(os.system('sed -i "s/Dc[0-9]*IsPolled.*//g" /etc/4xxxvf_dev*.conf'))
    status.append(os.system('sed -i "s/Dc[0-9]*CoreAffinity.*//g" /etc/4xxxvf_dev*.conf'))

    status.append(os.system('sed -i "s/ATEnabled.*/ATEnabled = 0/g" /etc/4xxxvf_dev*.conf'))
    status.append(os.system('sed -i "s/ATMode.*/ATMode = streaming/g" /etc/4xxxvf_dev*.conf'))

    if len(list(set(status))) > 1:
        print('clear instance failed.')


def get_numa_cores(pfs, cross):
    '''
    Get cpu cores
    '''
    node_cores = {}

    cores_output = os.popen('numactl --hardware | grep cpus')
    cores_str_list = cores_output.readlines()
    if cross:
        for pf in range(pfs):
            if pf < NUMA0_device_number:
                node_cores[pf] = cores_str_list[1].split(':')[1].strip().split(' ')
            else:
                node_cores[pf] = cores_str_list[0].split(':')[1].strip().split(' ')
    else:
        for pf in range(pfs):
            if pf < NUMA0_device_number:
                node_cores[pf] = cores_str_list[0].split(':')[1].strip().split(' ')
            else:
                node_cores[pf] = cores_str_list[1].split(':')[1].strip().split(' ')
    return node_cores


def parse_cores_opt(pfs, vfs, instances, cores_str):
    '''
    Parse cores option if provide, include pfs, functional and performance test mode.
    You can set cores range on different node, separate by comma, like 0-7,52-59.
    while pf number < 4 and cores number equal half of total instance number,
    set cores on pfs mode.
    '''
    total_core_number = pfs * vfs * instances
    cores = { }
    for pf in range(pfs):
        cores[pf] = []

    if ',' in cores_str:
        cores_str_list = cores_str.split(',')
        cores_range_0 = [int(core_index) for core_index in cores_str_list[0].split('-')]
        cores_range_1 = [int(core_index) for core_index in cores_str_list[1].split('-')]
        if (cores_range_0[1] - cores_range_0[0]) + 1 <= int(total_core_number / 4):
            for pf in range(pfs):
                if pf < 2:
                    cores[pf] = [i for i in range(cores_range_0[0], cores_range_0[1] + 1)]
                else:
                    cores[pf] = [i for i in range(cores_range_1[0], cores_range_1[1] + 1)]
        else:
            if pfs <= NUMA0_device_number:
                for pf in range(pfs):
                    cores[pf] = [i for i in range(cores_range_0[0], cores_range_0[1] + 1)] + [j for j in range(cores_range_1[0], cores_range_1[1] + 1)]
            else:
                for pf in range(pfs):
                    if pf < NUMA0_device_number:
                        cores[pf] = [i for i in range(cores_range_0[0], cores_range_0[1] + 1)]
                    else:
                        cores[pf] = [i for i in range(cores_range_1[0], cores_range_1[1] + 1)]
    else:
        cores_range = [int(core_index) for core_index in cores_str.split('-')]
        if (cores_range[1] - cores_range[0] + 1) <= int(total_core_number / 2):
            cores_range_0 = [cores_range[0] , int((cores_range[1] - cores_range[0] + 1) / 2) + cores_range[0] - 1]
            cores_range_1 = [int((cores_range[1] - cores_range[0] + 1) / 2) + cores_range[0], cores_range[1]]
            for pf in range(pfs):
                if pf < 2:
                    cores[pf] = [i for i in range(cores_range_0[0], cores_range_0[1] + 1)]
                else:
                    cores[pf] = [i for i in range(cores_range_1[0], cores_range_1[1] + 1)]
        else:
            if pfs <= NUMA0_device_number:
                for pf in range(pfs):
                    cores[pf] = [i for i in range(cores_range[0], cores_range[1] + 1)]
            else:
                cores_range_0 = [cores_range[0], (cores_range[0] + cores_range[1] + 1) / 2]
                cores_range_1 = [(cores_range[0] + cores_range[1] + 1) / 2, cores_range[1]]
                for pf in range(pfs):
                    if pf < NUMA0_device_number:
                        cores[pf] = [i for i in range(cores_range_0[0], cores_range_0[1])]
                    else:
                        cores[pf] = [i for i in range(cores_range_1[0], cores_range_1[1] + 1)]
    return cores


def get_pf_number():
    '''
    Get PF number
    '''
    # output = os.popen('ls -l /sys/kernel/debug/ | grep _4xxx_ | wc -l')
    output = os.popen('lspci -d:4940 | wc -l')
    PF_number = int(output.read().strip('\n'))
    return PF_number


def override_conf(service, AT_Enable, AT_Mode='streaming', pf_number=0, vf_number=0, instance=0, cores=None):
    '''
    Generate content of conf file.
    '''
    vf_conf_file_pattern = '/etc/4xxxvf_dev{}.conf'
    cy_instance_number = 0
    dc_instance_number = 0

    general_section = Genaral.format(service, AT_Enable, AT_Mode)

    ssl_section = ''
    if service == 'sym' or service == 'asym' or service == 'cy':
        ssl_section = SSL_head.format(instance, 0)
        cy_instance_number = int(instance)
    elif service == 'dc':
        ssl_section = SSL_head.format(0, instance)
        dc_instance_number = int(instance)
    else:
        cy_instance_number = int(instance.split(',')[0])
        dc_instance_number = int(instance.split(',')[1])
        ssl_section = SSL_head.format(cy_instance_number, dc_instance_number)

    instance_section = ''

    for pf in range(pf_number):
        for vf in range(vf_number):
            with open(vf_conf_file_pattern.format(pf * 16 + vf), 'w') as vf_conf:
                vf_conf.write(general_section)
                vf_conf.write(ssl_section)
                for inst in range(cy_instance_number):
                    if pf < NUMA0_device_number:
                        instance_section += Cy_instance.format(inst, cores[pf][(pf * vf_number * cy_instance_number + vf * cy_instance_number + inst) % len(cores[pf])])
                    else:
                        instance_section += Cy_instance.format(inst, cores[pf][((pf - NUMA0_device_number) * vf_number * cy_instance_number + vf * cy_instance_number + inst) % len(cores[pf])])

                for inst in range(dc_instance_number):
                    if pf < NUMA0_device_number:
                        instance_section += Dc_instance.format(inst, cores[pf][(pf * vf_number * dc_instance_number + vf * dc_instance_number + inst) % len(cores[pf])])
                    else:
                        instance_section += Dc_instance.format(inst, cores[pf][((pf - NUMA0_device_number) * vf_number * dc_instance_number + vf * dc_instance_number + inst) % len(cores[pf])])

                vf_conf.write(instance_section)
                instance_section = ''


if __name__ == '__main__':
    opts = os.sys.argv[1:]
    if len(opts) < 6 or len(opts) > 7:
        help()
    else:
        print("Generating...")
        if int(opts[0]) != 0:
            replace_svm()

        service = opts[1].replace(',', ';')

        NUMA_output = os.popen("lspci -vmm -d:4940 | grep NUMANode | awk -F \" \" '{print $2}'")
        NUMA0_device_number = len([node for node in NUMA_output.readlines() if int(node.strip()) == 0])

        AT_Enable = 0
        AT_Mode = 'streaming'
        if opts[2] == 'on':
            AT_Enable = 1
            AT_Mode = 'streaming'
        elif opts[2] == 'off':
            AT_Enable = 0
            AT_Mode = 'streaming'
        else:
            AT_Enable = 1
            AT_Mode = 'prefetch'

        pf_number = 0
        if int(opts[3]) == 0 or int(opts[3]) > 8:
            pf_number = get_pf_number()
        else:
            pf_number = int(opts[3])

        vf_number = 0
        if int(opts[4]) == 0 or int(opts[4]) > 16:
            vf_number = 16
        else:
            vf_number = int(opts[4])

        instances = max([int(inst) for inst in opts[5].split(',')])

        cores = []
        if len(opts) == 7 and opts[6].find('-') > 0:
            cores = parse_cores_opt(pf_number, vf_number, instances, opts[6])
        elif len(opts) == 7 and opts[6].find('-') == -1:
            cores = get_numa_cores(pf_number, int(opts[6]))
        else:
            cores = get_numa_cores(pf_number, 0)

        clear_settings(service)
        override_conf(service, AT_Enable, AT_Mode, pf_number, vf_number, opts[5], cores)
