import argparse
import os
import sys
from lnx_exec_with_check import lnx_exec_command
from log_keyword_check import check_keyword
from constant import *

def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description='copy file from host to guest vm'
                    '--device <the device name>'
                    '--mode <the mode of execution>'	
                    '--time <the maximum execution time>')
    parser.add_argument('-d', '--device', required=True, dest='device', action='store', help='the device name')
    parser.add_argument('-m', '--mode', required=True, dest='mode', action='store', help='the mode of execution')
    parser.add_argument('-t', '--time', default='43200', dest='time', action='store', help='the maximum execution time')
    ret = parser.parse_args(args)
    return ret

def check_rmmod_insmod(time):
    _, out, err = lnx_exec_command('lsmod | grep dlb2', timeout=time)
    check_keyword(['dlb2'], out, 'dlb2 not detected')
    lnx_exec_command('rmmod dlb2', timeout=time)
    lnx_exec_command(f'insmod {Accelerator_REMOTE_TOOL_PATH}/dlb/driver/dlb2/dlb2.ko', timeout=time)

def guest_exec(device, mode, time):
    time = float(time)
    if device == 'dlb':
        if mode == 'ldb' or mode == 'all':
            check_rmmod_insmod(time)
            _, out, err = lnx_exec_command('LD_LIBRARY_PATH=$PWD ./examples/ldb_traffic -n 1000000 | tee /root/dlb_op.log',
                                           timeout=time,cwd=f'{Accelerator_REMOTE_TOOL_PATH}/dlb/libdlb')
        if mode == 'ordered' or mode == 'all':
            check_rmmod_insmod(time)
            lnx_exec_command('mkdir -p / mnt / hugepages', timeout=time)
            lnx_exec_command('mount -t hugetlbfs nodev /mnt/hugepages', timeout=time)
            lnx_exec_command('echo 2048 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages', timeout=time)
            _, out, err = lnx_exec_command('./dpdk-test-eventdev -c 0x0f --vdev=dlb2_event -- --test=order_queue --plcores=1 --wlcore=2,3 --nb_flows=64 --nb_pkts=100000000', timeout=time, cwd=f'{Accelerator_REMOTE_TOOL_PATH}/dpdk_driver/dpdk-stable-20.11.3/builddir/app')
            check_keyword(['Success'], out, 'dpdk test not succeeds')
        if mode == 'perf' or mode == 'all':
            check_rmmod_insmod(time)
            lnx_exec_command('mkdir -p / mnt / hugepages', timeout=time)
            lnx_exec_command('mount -t hugetlbfs nodev /mnt/hugepages', timeout=time)
            lnx_exec_command('echo 2048 > /sys/kernel/mm/hugepages/hugepages-2048kB/nr_hugepages', timeout=time)
            _, out, err = lnx_exec_command('./dpdk-test-eventdev -c 0x0f --vdev=dlb2_event -- --test=perf_queue --plcores=1 --wlcore=2,3 --nb_flows=64 --stlist=o --nb_pkts=100000000', timeout=time, cwd=f'{Accelerator_REMOTE_TOOL_PATH}/dpdk_driver/dpdk-stable-20.11.3/builddir/app')
            check_keyword(['Success'], out, 'dpdk test not succeeds')
    return

if __name__ == '__main__':
    args_parse = setup_argparse()
    guest_exec(args_parse.device, args_parse.mode, args_parse.time)


