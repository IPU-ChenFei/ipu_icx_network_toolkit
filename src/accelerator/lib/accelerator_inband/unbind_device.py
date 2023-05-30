from lnx_exec_with_check import lnx_exec_command
import sys
import argparse
from get_dev_id import get_dev_id
from get_dlb_dev_id_list import get_dlb_dev_id_list
from constant import *
from log import logger


def setup_argparse():
    args = sys.argv[1:]
    parser = argparse.ArgumentParser(
        description="Unbind 'QAT', 'DLB', 'DSA', 'IAX' device"
                    '--ip_pf_vf <accelerator type_pf number_vf number> {qat_0_0, dlb_0_1}')
    parser.add_argument('-v', '--ip_pf_vf', required=True, dest='ip_pf_vf', action='store',
                        help='accelerator type_pf number_vf number')
    ret = parser.parse_args(args)
    return ret


def __get_qat_unbind_path(dev_id):
    """
          Purpose: Modify the format of QAT device ID
          Args:
              dev_id : QAT device ID -->'0000:6d:00.0'
          Returns:
              Yes  --> '0000\:6b\:00.0'
          Example:
              Simplest usage: Modify the format of QAT device ID
                    __get_qat_unbind_path(0000:6d:00.0)
                    return '0000\:6b\:00.0'
    """
    word_split = dev_id.split(':')  # [' 0000', '6b', '00.0']
    i = 1
    while i < len(word_split):
        word_split.insert(i, '\\:')  # [' 0000', '\\:', '6b', '\\:', '00.0']
        i += 2
    change_word = "".join(word_split)  # ' 0000\:6b\:00.0'
    change_word = change_word.strip()  # '0000\:6b\:00.0'
    return change_word


def __get_qat_pci_id(dev_id):
    """
          Purpose: Modify the format of QAT device ID
          Args:
              dev_id : QAT device ID -->'0000:6d:00.0'
          Returns:
              Yes  --> '0000_6b_00_1'
          Example:
              Simplest usage: Modify the format of QAT device ID
                    __get_qat_pci_id(0000:6d:00.0)
                    return '0000_6b_00_1'
    """
    change_li = []
    word_list_split = dev_id.split(':')  # [' 0000', '6b', '00.1']
    word_list_change = word_list_split[2].split('.')  # ['00', '1']
    change_li.append(word_list_split[0])  # [' 0000]
    change_li.append(word_list_split[1])  # [' 0000', '6b']
    change_li.append(word_list_change[0])  # [' 0000', '6b','00']
    change_li.append(word_list_change[1])  # [' 0000', '6b','00', '1']
    i = 1
    while i < len(change_li):
        change_li.insert(i, '_')  # [' 0000', '_', '6b', '_', '00', '_', '1']
        i += 2
    change_str = ''.join(change_li)  # ' 0000_6b_00_1'
    change_str = change_str.strip()  # '0000_6b_00_1'
    return change_str


def __get_dlb_unbind_path(dev_id):  # '0000:6d:00.1'
    """
          Purpose: Get True DLB device ID
          Args:
              dev_id: DLB device ID, this is DLB True device ID or virtual DLB device ID
          Returns:
              Yes  --> '0000:6d:00.0'
          Example:
              Simplest usage: get DLB True device 0 and create 2 DLB Vietual device for Platform
                    __get_dlb_unbind_path('0000:6d:00.1')
                    return'0000:6d:00.0'
    """
    is_vf = dev_id.split(':')
    if is_vf[2] == '00.0':
        dlb_pf_id = dev_id  # '0000:6d:00.0'
    else:
        before_id = dev_id.split(".")
        dlb_pf_id = before_id[0] + '.0'  # '0000:6d:00.0'
    return dlb_pf_id  # '0000:6d:00.0'


def __get_dlb_pci_id_list(dev_id_list):
    """
          Purpose: Modify the format of DLB device ID list
          Args:
              dev_id_list : DLB device ID list --># ['0000:6d:00.1','0000:6d:00.2','0000:6d:00.3']
          Returns:
              Yes  --> # '0000_6d_00_1''0000_6d_00_2''0000_6d_00_3'
          Example:
              Simplest usage: Modify the format of DLB device ID list
                    __get_dlb_pci_id_list(['0000:6d:00.1','0000:6d:00.2','0000:6d:00.3'])
                    return '0000_6d_00_1''0000_6d_00_2''0000_6d_00_3'
    """
    dlb_pci_id_list = []
    for dev_id in dev_id_list:
        change_li = []
        word_list_split = dev_id.split(
            ':')  # [' 0000', '6d', '00.1'][' 0000', '6d', '00.2'][' 0000', '6d', '00.3']
        word_list_change = word_list_split[2].split('.')  # ['00', '1']['00', '2']['00', '3']
        change_li.append(word_list_split[0])  # [' 0000][' 0000'][' 0000']
        change_li.append(word_list_split[1])  # [' 0000', '6d'][' 0000', '6d'][' 0000', '6d']
        change_li.append(word_list_change[0])  # [' 0000', '6d','00'][' 0000', '6d','00'][' 0000', '6d', '00']
        change_li.append(
            word_list_change[1])  # [' 0000', '6d','00', '1'][' 0000', '6d','00', '2'][' 0000', '6d', '00', '3']
        i = 1
        while i < len(change_li):
            change_li.insert(i,
                             '_')  # [' 0000', '_', '6d', '_', '00', '_', '1'][' 0000', '_', '6d', '_', '00', '_', '2'][' 0000', '_', '6d', '_', '00', '_', '3']
            i += 2
        change_str = ''.join(change_li)  # ' 0000_6d_00_1'' 0000_6d_00_2'' 0000_6d_00_3'
        change_str = change_str.strip()  # '0000_6d_00_1''0000_6d_00_2''0000_6d_00_3'
        dlb_pci_id_list.append(change_str)
    return dlb_pci_id_list


def __dlb_vf_set_egs(vf, dlb_pf_id, pci_id_list):
    for i in range(vf):
        lnx_exec_command(
            f'echo {int(2048 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_atomic_inflights',
            timeout=60)
        lnx_exec_command(
            f'echo {int(2048 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_dir_credits',
            timeout=60)
        lnx_exec_command(
            f'echo {int(64 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_dir_ports',
            timeout=60)
        lnx_exec_command(
            f'echo {int(2048 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_hist_list_entries',
            timeout=60)
        lnx_exec_command(
            f'echo {int(8192 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_ldb_credits',
            timeout=60)
        lnx_exec_command(
            f'echo {int(64 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_ldb_ports',
            timeout=60)
        lnx_exec_command(
            f'echo {int(32 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_ldb_queues',
            timeout=60)
        lnx_exec_command(
            f'echo {int(32 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_sched_domains',
            timeout=60)
        lnx_exec_command(
            f'echo {int(16 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_sn0_slots',
            timeout=60)
        lnx_exec_command(
            f'echo {int(16 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_sn1_slots',
            timeout=60)
        lnx_exec_command(f'virsh nodedev-detach pci_{pci_id_list[i]}', timeout=60)

def __dlb_vf_set_bhs(vf, dlb_pf_id, pci_id_list):
    for i in range(vf):
        lnx_exec_command(
            f'echo {int(2048 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_atomic_inflights',
            timeout=60)
        lnx_exec_command(
            f'echo {int(96 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_dir_ports',
            timeout=60)
        lnx_exec_command(
            f'echo {int(2048 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_hist_list_entries',
            timeout=60)
        lnx_exec_command(
            f'echo {int(16384 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_ldb_credits',
            timeout=60)
        lnx_exec_command(
            f'echo {int(64 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_ldb_ports',
            timeout=60)
        lnx_exec_command(
            f'echo {int(32 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_ldb_queues',
            timeout=60)
        lnx_exec_command(
            f'echo {int(32 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_sched_domains',
            timeout=60)
        lnx_exec_command(
            f'echo {int(16 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_sn0_slots',
            timeout=60)
        lnx_exec_command(
            f'echo {int(16 / vf)} > /sys/bus/pci/devices/{dlb_pf_id}/vf{i}_resources/num_sn1_slots',
            timeout=60)
        lnx_exec_command(f'virsh nodedev-detach pci_{pci_id_list[i]}', timeout=60)



def unbind_device(ip_pf_vf):  # begain is qat_0_1  dlb_0_0
    """
          Purpose: Unbind 'QAT', 'DLB', 'DSA', 'IAX' device
          Args:
              ip_pf_vf_mdev :
              1. If unbind QAT device, format is qat_0_1, pf 0 is QAT PF device 1,pf begin from device 1, device id from device 0-7, pf 0 -->device id;
                vf 1 vf device 1, vf begin from virtual device 1, device id from device 00.1-02.0,vf 1-->device 00.1
              2.If unbind DLB device, format is dlb_0_0, pf 0 is pf device 1,pf begin from true device 1, device id from device 0-7, pf 0 -->device id 1;
                vf is number of vf device need created, vf 0 is don't create virtual device, vf 1 is create 1 virtual device, vf 16 is create 16 virtual device
              3.If unbind DSA device, format is dsa_0_0, pf 0 is pf device 1,pf begin from true device 1, device id from device 0-7, pf 0 -->device id 1
          Returns:
              No
          Raises:
              RuntimeError: If any errors
          Example:
              Simplest usage: unbind QAT pf device 0
                    unbind_device('qat_0_0')
    """
    ip, pf, vf = ip_pf_vf.split('_')
    pf = int(pf)
    vf = int(vf)
    if ip == 'qat':
        get_dev_id(ip, pf, vf)
        dev_id_str = (lnx_exec_command('cat /home/logs/dev_id.log')[1]).strip()
        dev_id_str = dev_id_str.strip('[]')
        dev_id = dev_id_str
        unbind_path = __get_qat_unbind_path(dev_id)
        pci_id = __get_qat_pci_id(dev_id)
        lnx_exec_command(f'echo {dev_id} > /sys/bus/pci/devices/{unbind_path}/driver/unbind', timeout=60)
        if vf == 0:
            lnx_exec_command(f'echo 8086 {qat_id} > /sys/bus/pci/drivers/vfio-pci/new_id', timeout=60)
        elif 0 < vf < 17:
            lnx_exec_command(f'echo 8086 {qat_vf_id} > /sys/bus/pci/drivers/vfio-pci/new_id', timeout=60)
        else:
            logger.error('Input an uncorrect vf number')
            raise Exception('Input an uncorrect vf number')
        lnx_exec_command(f'lspci -s {dev_id} -k', timeout=60)
        lnx_exec_command(f'virsh nodedev-detach pci_{pci_id}', timeout=60)
    elif ip == 'dlb':
        dev_id_list = []
        get_dlb_dev_id_list(pf, vf)
        dev_list = (lnx_exec_command('cat /home/logs/dlb_list.log')[1]).strip()
        dev_list = dev_list.strip('[]')
        dev_id_list=dev_list.split(',')
        dlb_pf_id = __get_dlb_unbind_path(dev_id_list[0])
        pci_id_list = __get_dlb_pci_id_list(dev_id_list)
        for i in range(vf):
            print(dev_id_list,i)
            lnx_exec_command(f'echo {dev_id_list[i]} > /sys/bus/pci/drivers/dlb2/unbind', timeout=60)
        if vf == 0:
            lnx_exec_command(f'echo {dev_id_list[0]} > /sys/bus/pci/drivers/dlb2/unbind', timeout=60)
            lnx_exec_command(f'echo 8086 {dlb_id} > /sys/bus/pci/drivers/vfio-pci/new_id', timeout=60)
            lnx_exec_command(f'lspci -s {dev_id_list[0]} -k', timeout=60)
            lnx_exec_command(f'virsh nodedev-detach pci_{pci_id_list[0]}', timeout=60)
        elif 0 < vf < 17:
            lnx_exec_command(f'echo 8086 {dlb_vf_id} > /sys/bus/pci/drivers/vfio-pci/new_id', timeout=60)
            __dlb_vf_set_egs(vf, dlb_pf_id, pci_id_list)
        else:
            logger.error('Input an uncorrect vf number')
            raise Exception('Input an uncorrect vf number')
    elif ip == 'dsa':
        get_dev_id(ip, pf, vf)
        dev_id = (lnx_exec_command('cat /home/logs/dev_id.log')[1]).strip()
        lnx_exec_command(f'echo {dev_id} > /sys/bus/pci/devices/{dev_id}/driver/unbind', timeout=60)
        lnx_exec_command(f'echo 8086 {dsa_id} > /sys/bus/pci/drivers/vfio-pci/new_id', timeout=60)
        lnx_exec_command(f'lspci -s {dev_id} -k', timeout=60)


if __name__ == '__main__':
    args_parse = setup_argparse()
    unbind_device(args_parse.ip_pf_vf)