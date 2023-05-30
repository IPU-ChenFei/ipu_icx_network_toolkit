import datetime
import logging
import os
import re
import subprocess
import sys
import time

"""
Script parameter sequence: vm_name, physical adapter name, vm_switch_name
"""


def get_logger():
    log_obj = logging.getLogger()
    formatter = logging.Formatter("%(asctime)s - %(pathname)s[line:%(lineno)d] - %(levelname)s: %(message)s")
    log_obj.setLevel(logging.DEBUG)

    file_handle = logging.FileHandler("vm_sut_w_{}.log".format(datetime.datetime.now().strftime("%Y%m%dZ%Hh%Mm%Ss")))
    stream_handle = logging.StreamHandler()
    file_handle.setFormatter(formatter)
    stream_handle.setFormatter(formatter)

    log_obj.addHandler(file_handle)
    log_obj.addHandler(stream_handle)

    return log_obj


log = get_logger()


def exec_command(cmd):
    log.info("Executing cmd: \n {}".format(cmd))
    ret = subprocess.Popen(cmd,
                           # shell=True,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    out, err = ret.communicate()

    if err.decode() != "":
        log.error(f"Failed to execute cmd: {cmd}\n "
                  f"error message: {err.decode()}\n")
        raise RuntimeError("Command execution failed! error: \n{}".format(err.decode()))
    return out.decode('utf-8').splitlines()


SILENT_CONTINUE = "$progressPreference = 'silentlyContinue'"
GET_HYPER_V_INSTALLED_CMD = "powershell.exe Get-Command *-VM"

NEW_VM_STR = "New-VM"
VM_STATE_STR = "Running"

GET_NETWORK_INTERFACE_NAME_CMD = "powershell.exe ip addr show | awk '/inet.*brd/{print $NF; exit}'"
SUT_ISO_IMAGE_LOCATION = "C:\\BKCPkg\\domains\\network\\"
CREATE_VM_FROM_TEMPLATE_CMD = "powershell.exe New-VM -Name {} -MemoryStartupBytes {}GB -VHDPath {}"
CREATE_VM_FROM_ISO_CMD = "powershell.exe \"New-VM -Name {} -MemoryStartupBytes {}GB -NewVHDPath {} " \
                         "-NewVHDSizeBytes {}GB | Add-VMDvdDrive -Path {} \""
GET_VM_CMD = "powershell.exe Get-VM -Name {}"
GET_VM_LIST_CMD = "powershell.exe Get-VM"
VERIFY_VM_STATE = "powershell.exe {}; Get-VM -Name {}"
START_VM_CMD = "powershell.exe Start-VM -Name {}"
REMOVE_VM_CMD = "powershell.exe Remove-VM -Name {} -Force"
GET_VM_VHDPATH_CMD = "powershell.exe Get-VMHardDiskDrive -VMName {}"
DELETE_VHD_CMD = "powershell.exe Del {}"
SHUTDOWN_VM_CMD = "powershell.exe Stop-VM -Name {} -Force"

GET_VM_Memory_CMD = "powershell.exe Get-VMMemory -VMName {}"
GET_CPU_NUM_CMD = "powershell.exe Get-VMProcessor {}"
MODIFY_VM_CPU_COMMAND = "powershell.exe {}; Set-VMProcessor -VMName {} -Count {}"
GET_NET_ADAPTER_CMD = 'powershell.exe {}; ("Get-NetAdapter -Name * -Physical).Name'.format(SILENT_CONTINUE)
GET_VM_NETWORK_ADAPTER_CMD = "powershell.exe Get-VMNetworkAdapter -VMName '{}'"
NEW_VM_SWITCH_CMD = "powershell.exe {}; New-VMSwitch -Name {} -NetAdapterName '{}'" \
                    " -AllowManagementOS $true"
NEW_VM_SWITCH_WITH_SRIOV_CMD = "powershell.exe New-VMSwitch {} -NetAdapterName '{}' -EnableIov 1"
ADD_VM_NETWORK_ADAPTER_CMD = "powershell.exe {}; Add-VMNetworkAdapter -VMName {} -Name '{}'" \
                             " -SwitchName {}"
REMOVE_VM_SWITCH_COMMAND = "powershell.exe {}; Remove-VMSwitch -Name {} -Force"


def create_vm(vm_name, vm_os, mem_size=4, disk_size=9, create_timeout=1600):
    """
    Create vm via ios image, still requires manual action
    """

    is_vm_created = get_vm(vm_name)
    log.info("get_vm: {}".format(is_vm_created))
    if is_vm_created is not None:
        log.error("VM {} already exist".format(vm_name))
        raise RuntimeError("VM {} already exists, please check the existing VM or user another name".format(vm_name))

    if vm_os in ("RedHat",):
        iso_file = SUT_ISO_IMAGE_LOCATION + "RHEL-8.3.0-20201009.2-x86_64-dvd1.iso"
    else:
        iso_file = SUT_ISO_IMAGE_LOCATION + "17763.1.180914-1434.rs5_release_SERVER_OEMRET_x64FRE_en-us.iso"
    if not os.path.exists(iso_file):
        log.error("ISO file not found")
        raise RuntimeError("Specified ISO image does not exist")

    log.info("Creating VM named {}".format(vm_name))
    vhd_path = SUT_ISO_IMAGE_LOCATION + vm_name + ".vhdx"

    print("Creating VM named {}\n using iso {}\n and vhd path {}".format(vm_name, iso_file, vhd_path))
    exec_command(CREATE_VM_FROM_ISO_CMD.format(vm_name, mem_size, vhd_path, disk_size, iso_file))

    ret = get_vm(vm_name)
    if ret is None:
        log.error("VM {} creation failed".format(vm_name))
        raise RuntimeError("VM creation failed")

    log.info("VM {} successfully created".format(vm_name))


def create_vm_from_template(vm_name, mem_size=4):
    """
    Create vm automatically from existing vhdx file template
    """

    check_vm = get_vm(vm_name)
    if check_vm is not None:
        log.error("VM {} already exist".format(vm_name))
        raise RuntimeError("VM {} already exists, please check the existing VM or user another name".format(vm_name))

    to_copy = SUT_ISO_IMAGE_LOCATION + 'WIN.vhdx'
    new_copy = SUT_ISO_IMAGE_LOCATION + vm_name + '.vhdx'
    copy_cmd = exec_command(r'powershell.exe Copy-Item {} {}'.format(to_copy, new_copy))
    # if "1 file(s) copied." not in "".join(copy_cmd):
    #     raise RuntimeError("template copy failed")

    temp_path = SUT_ISO_IMAGE_LOCATION + vm_name + ".vhdx"

    log.info("Creating VM {} from template {}".format(vm_name, temp_path))
    creation = exec_command(CREATE_VM_FROM_TEMPLATE_CMD.format(vm_name, mem_size, temp_path))

    if vm_name and "Operating normally" not in "".join(creation):
        raise RuntimeError("Failed to create VM {}".format(vm_name))
    log.info("VM {} created successfully".format(vm_name))


def get_vm(vm_name):
    """
    Query a vm, throws an exception if the queried vm does not exist
    """
    try:
        v_state = _get_vm_state(vm_name)
        v_cpu = _get_no_of_cpus(vm_name)
        v_mem = _get_vm_memory_info(vm_name)

        vm_dict = {"name": vm_name,
                   "state": v_state,
                   "cpu_num": v_cpu,
                   "memory_info": v_mem}
        log.info("Get VM: {}".format(vm_dict))
        return vm_dict

    except RuntimeError:
        log.error("Failed to get vm info or the vm does not exist")
        return None


def start_vm(vm_name):
    """
    Boot up a vm, skip if the vm is already on
    """
    try:
        vm_state = _get_vm_state(vm_name)
        if VM_STATE_STR not in "".join(vm_state):
            log.info("VM {} is now off, turning it on".format(vm_name))
            exec_command(START_VM_CMD.format(vm_name))
            log.info("VM {} started successfully".format(vm_name))
        # elif "already in the specified state" in v
    except Exception as ex:
        log.error("Failed to start the VM: {}".format(ex))
        raise ex


def shutdown_vm(vm_name):
    """
    Shutdown the specified vm
    """
    try:
        shutdown_ret = exec_command(SHUTDOWN_VM_CMD.format(vm_name))

        if len(shutdown_ret) == 0:
            log.info("VM {} successfully shutdown".format(vm_name))
    except RuntimeError:
        raise


def delete_vm(vm_name):
    """
    Destroy the specified vm and its vhdx file
    """
    try:
        vm_info = _get_vm_state(vm_name)
        if VM_STATE_STR in "".join(vm_info):
            log.info("VM {} is running, shutting it down now".format(vm_name))
            shutdown_vm(vm_name)
        vhd_path = _get_vm_vhd(vm_name)
        log.info("VHD path get: {}".format(vhd_path))

        remove_vm = exec_command(REMOVE_VM_CMD.format(vm_name))
        if len(remove_vm) == 0:
            log.info("VM {} successfully removed".format(vm_name))

        remove_vhd = exec_command(DELETE_VHD_CMD.format(vhd_path))
        if len(remove_vhd) == 0:
            log.info("VM {}'s vhd successfully removed".format(vm_name))
    except Exception as ex:
        raise ex


def add_vm_adapter_sriov(vm_name, physical_adapter, switch_name):
    """
    Add a virtual switch via sr-iov and a adapter along with it
    """
    log.info("Adding sriov adapter")
    adapter_info = exec_command(GET_NET_ADAPTER_CMD)
    log.info("Got adapter info: {}".format(adapter_info))

    if physical_adapter not in "".join(adapter_info):
        raise RuntimeError("Invalid adapter name")

    # shutdown the vm if vm is up
    vm_state = _get_vm_state(vm_name)
    if VM_STATE_STR in vm_state:
        shutdown_vm(vm_name)

    # add switch with SRIOV
    log.info("adding new switch")
    exec_command(NEW_VM_SWITCH_WITH_SRIOV_CMD.format(switch_name, physical_adapter))

    # add adapter
    log.info("adding new adapter")
    adapter_name = "adapter_for_{}".format(vm_name)
    exec_command(ADD_VM_NETWORK_ADAPTER_CMD.format(SILENT_CONTINUE, vm_name, adapter_name, switch_name))


def move_file_to_vm(vm_name, sut_path, vm_path):
    """
    Move a file from host to a specified path on vm
    """
    cmd = ("powershell.exe $account = 'administrator'\n"
           "$password = 'intel_123'\n"
           "$secpwd = convertTo-secureString $password -asplaintext -force\n"
           "$cred = new-object System.Management.Automation.PSCredential -argumentlist $account, $secpwd\n"
           "$session = New-PSSession -vmname {} -Credential $cred\n"
           "Copy-Item -ToSession $session -Path {} -Destination {}").format(vm_name, sut_path, vm_path)

    try:
        if not os.path.exists(sut_path):
            log.error("The sut file at {} to be copied is not found".format(sut_path))
            raise RuntimeError("Specified sut file does not exist")

        log.info("Copying file from sut {} to vm {}".format(sut_path, vm_path))
        exec_command(cmd)

    except RuntimeError as e:
        log.error("Failed to copy file!")
        raise e


def install_driver_on_vm(vm_name):
    """
    Install driver on vm
    """
    script = "C:\\Users\\Administrator\\Desktop\\PROWinx64.exe /qn /liew C:\\Users\\Administrator\\Desktop\\install.log"

    cmd = (f"powershell.exe $account = 'administrator'\n"
           f"$password = 'intel_123'\n"
           f"$secpwd = convertTo-secureString $password -asplaintext -force\n"
           f"$cred = new-object System.Management.Automation.PSCredential -argumentlist $account,$secpwd\n"
           f"Invoke-Command -VMName {vm_name} -Credential $cred -ScriptBlock {{ {script} }} \n")
    try:
        log.info("Installing NIC driver on vm")
        exec_command(cmd)
    except Exception as e:
        log.error("Driver installation on VM {} failed!".format(vm_name))
        raise e


def check_device_on_vm(vm_name):
    """
    Invoke adapter checking command to see if the adapter had been added successfully
    """
    query = "(get-NetAdapter -Name *).Name"

    cmd = (f"powershell.exe $account = 'administrator'\n"
           f"$password = 'intel_123'\n"
           f"$secpwd = convertTo-secureString $password -asplaintext -force\n"
           f"$cred = new-object System.Management.Automation.PSCredential -argumentlist $account,$secpwd\n"
           f"Invoke-Command -VMName {vm_name} -Credential $cred -ScriptBlock {{ {query} }} "
           )

    result = exec_command(cmd)
    log.debug("Queried VM adapter: {}".format(result))
    if len(result) < 2:
        raise RuntimeError("Failed to find the adapter in VM, the test may failed!")


# ===================================================
def _get_vm_state(vm_name):
    try:
        vm_info = exec_command(GET_VM_CMD.format(vm_name))
        if len(vm_info) == 0:
            raise RuntimeError("Failed to get the vm state")
        log.info("Got state info: {}".format(vm_info))

        state = None
        index = 0
        for line in vm_info:
            print(line)
            if line is not '' and '---' not in line:
                res = re.finditer(r"\S+", line)
                temp_index = 0
                for match in res:
                    if index == 0:
                        index += 1
                        break
                    if temp_index == 0:
                        temp_index += 1
                    else:
                        state = match.group()
                        break
        if state is None:
            raise RuntimeError("Failed to get the vm state")
        else:
            return state

    except RuntimeError:
        raise


def _get_no_of_cpus(vm_name):
    try:
        cpu_info = exec_command(GET_CPU_NUM_CMD.format(vm_name))
        if len(cpu_info) == 0:
            raise RuntimeError("Failed to get the vm cpu info")
        log.info("Got cpu info: {}".format(cpu_info))

        num = None
        index = 0
        for line in cpu_info:
            print(line)
            if line != '' and '---' not in line:
                res = re.finditer(r"\S+", line)
                temp_index = 0
                for match in res:
                    if index == 0:
                        index += 1
                        break
                    if temp_index == 0:
                        temp_index += 1
                    else:
                        num = match.group()
                        break
        if num is None:
            raise RuntimeError("Failed to get vm cpu number")
        else:
            return num

    except RuntimeError:
        raise


def _get_vm_memory_info(vm_name):
    mem_info = exec_command(GET_VM_Memory_CMD.format(vm_name))
    if len(mem_info) == 0:
        raise RuntimeError("Failed to get the vm cpu info")
    log.info("got memory info: {}".format(mem_info))

    val_list = []
    for line in mem_info:
        print(line)
        if line != '' and '---' not in line:
            res = re.finditer(r"\S+", line)
            for match in res:
                val_list.append(match.group())
    if len(val_list) == 0:
        raise RuntimeError("Failed to get vm memory info")
    index = int(len(val_list) / 2)
    info_dict = dict(zip(val_list[:index],
                         val_list[index:]))
    return info_dict


def _get_vm_vhd(vm_name):
    try:
        vhd_info = exec_command(GET_VM_VHDPATH_CMD.format(vm_name))
        log.info("Got VHD path:{}".format(vhd_info))

        vhd_path = None
        for line in vhd_info:
            print(line)
            if line != '' and '---' not in line:
                res = re.finditer(r"\S+", line)

                for match in res:
                    if ".vhdx" in match.group():
                        vhd_path = match.group()
                        break
        if vhd_path is None:
            raise RuntimeError("Failed to get vhd path")
        else:
            return vhd_path
    except Exception:
        raise


if __name__ == '__main__':
    log.info("=============Testing VM SR-IOV Windows==============")
    # create_vm("WIN1", "Windows")
    args = sys.argv
    vm_name = args[1]
    adapter = args[2]
    switch_name = args[3]

    create_vm_from_template(vm_name)
    get_vm(vm_name)
    add_vm_adapter_sriov(vm_name, adapter, switch_name)
    start_vm(vm_name)
    time.sleep(100)

    # Install driver (Optional
    # move_file_to_vm(vm_name, "C:\\BKCPkg\\Drivers\\network_adapter_driver\\PROWinx64.exe",
    #                         "C:\\Users\\Administrator\\Desktop")
    # install_driver_on_vm(vm_name)

    time.sleep(60)
    check_device_on_vm(vm_name)

    # shutdown_vm(vm_name)
    delete_vm(vm_name)
    exec_command(REMOVE_VM_SWITCH_COMMAND.format(SILENT_CONTINUE, switch_name))
