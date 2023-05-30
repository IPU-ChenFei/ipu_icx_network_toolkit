#!/usr/bin/env python
#################################################################################
# INTEL CONFIDENTIAL
# Copyright Intel Corporation All Rights Reserved.
#
# The source code contained or described herein and all documents related to
# the source code ("Material") are owned by Intel Corporation or its suppliers
# or licensors. Title to the Material remains with Intel Corporation or its
# suppliers and licensors. The Material may contain trade secrets and proprietary
# and confidential information of Intel Corporation and its suppliers and
# licensors, and is protected by worldwide copyright and trade secret laws and
# treaty provisions. No part of the Material may be used, copied, reproduced,
# modified, published, uploaded, posted, transmitted, distributed, or disclosed
# in any way without Intel's prior express written permission.
#
# No license under any patent, copyright, trade secret or other intellectual
# property right is granted to or conferred upon you by disclosure or delivery
# of the Materials, either expressly, by implication, inducement, estoppel or
# otherwise. Any license under such intellectual property rights must be express
# and approved by Intel in writing.
#################################################################################


class SGXConstants:
    """
    This class having all the Windows OS Constants
    """
    DMESG_CMD = r'dmesg'
    DMESG_CLEAR_CMD = r'dmesg -c'
    DMESG_SVN_CHECK_CMD = r'dmesg | grep -i sgx'
    GET_UCODE_LINUX_CMD = r'cat /proc/cpuinfo | grep -im 1 microcode'
    LIN_UCODE_UPGRADE_RELOAD = r'echo 1 > /sys/devices/system/cpu/microcode/reload'
    LIN_UCODE_DOWNGRADE_RELOAD = r'echo 2 > /sys/devices/system/cpu/microcode/reload'
    LIN_SVN_UPDATE = r'echo 1 > /sys/devices/system/cpu/microcode/svnupdate'
    LIN_UCODE_ROLLBACK = r'rm -f /lib/firmware/intel-ucode/*'
    REMOVE_HOST_KEYS = r'sudo rm /root/.ssh/known_hosts'
    SGX_LINUX_WORKLOAD = r'./app-workload'
    SGX_APP = r'./app'
    WIN_UCODE_DEF_DLL = r' C:\Windows\System32\mcupdate_GenuineIntel.dll'
    WIN_UCODE_COPY_TOOL = r'sfpcopy64.exe '
    LIN_UCODE_COPY_CMD = r'iucode_tool -K {} --overwrite'
    LIN_UCODE_COPY_MULTI_STEP_CMD = r'cp {} /lib/firmware/intel-ucode/'
    LIN_UCODE_PATCH_LINK_CMD = r'ln -s -f {} {}'
    LIN_SGX_VM_CMD = r"sudo /usr/libexec/qemu-kvm -accel kvm -smp 4,sockets=1 -m 4G -cpu host,+sgx-provisionkey -object memory-backend-epc,id=mem1,size=8M,prealloc=on -M sgx-epc.0.memdev=mem1,sgx-epc.0.node=0 -drive file=/home/enclave/SGX_rhel8_efi{}.qcow2,if=virtio,format=qcow2 -bios /home/enclave/OVMF-upstream.fd -net nic -net user,hostfwd=tcp::22{}-:22 -nographic"
    LIN_GEN_VM_CMD = r"sudo /usr/libexec/qemu-kvm -accel kvm -smp 4,sockets=1 -m 4G -cpu host -drive file=/home/enclave/SGX_rhel8_efi{}.qcow2,if=virtio,format=qcow2 -bios /home/enclave/OVMF-upstream.fd -net nic -net user,hostfwd=tcp::22{}-:22 -nographic"
    LIN_CHECK_VM_STATUS = r"sshpass -p 123456 ssh root@localhost -p 22{} uptime"
    LIN_GET_QEMU_PID = r'pgrep qemu'
    LIN_KILL_PID = r'sudo kill -9 {}'
    LIN_GET_WORKLOAD_PID = r'pgrep app-workload'
    LIN_READ_MSR = r'rdmsr {}'
    LIN_WRITE_MSR = r'wrmsr {} {}'
    LIN_CHECK_VM_SGX_STATUS = r"sshpass -p 123456 ssh root@localhost -p 22{} lscpu| grep sgx"
    
class PortAllocation:
    """
    This class having Port number details
    """
    SGX_VM_PORT = 21

class TimeDelay:
    """
    This class having TimeDelay
    """
    VM_STABLE_TIMEOUT = 10
    VM_CREATION_SLEEP_TIMEOUT = 50
    SYSTEM_TIMEOUT = 600
    REBOOT_OS_TIMEOUT = 800

class LinuxPath:
    """
    This class having LinuxPath
    """
    ROOT_PATH = "/root"
    LINUX_SGX_APP_PATH = "/home/enclave/ereport-new"
    LINUX_SGX_WORKLOAD_PATH = "/home/enclave/workload"
    LINUX_LOCAL_ATTEST_SGX_APP_PATH = "/home/local-attest"
    LINUX_UCODE_PATCH_PATH = "/lib/firmware/intel-ucode/"
